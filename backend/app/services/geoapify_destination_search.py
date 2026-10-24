"""
Live Geoapify destination discovery service for Destination Explorer,
Compare Destinations, and Multi-Stop Planner.

Provides:
- Text-based place search and geocoding
- Destination discovery by category
- Coordinates resolution for stop names
- Result normalization and deduplication
- Caching for repeated searches
- Error handling and fallback strategies
"""

import asyncio
import hashlib
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx

from app.config import settings
from app.services.geoapify_places import (
    GeoapifyError,
    is_destination_in_india,
    normalize_place,
    validate_configuration,
)
from app.services.weather import validate_coordinates

logger = logging.getLogger(__name__)

# Cache storage for search results (in production, use Redis)
_search_cache: dict[str, tuple[list[dict[str, Any]], datetime]] = {}
CACHE_TTL_SECONDS = 3600  # 1 hour cache

GEOCODING_URL = "https://api.geoapify.com/v1/geocode/search"
REVERSE_GEOCODING_URL = "https://api.geoapify.com/v1/geocode/reverse"
PLACES_URL = "https://api.geoapify.com/v2/places"


def _cache_key(search_type: str, query: str, filters: dict[str, Any] | None = None) -> str:
    """Generate cache key from search parameters."""
    parts = [search_type, query.strip().lower()]
    if filters:
        for key in sorted(filters.keys()):
            parts.append(f"{key}:{filters[key]}")
    key_str = "|".join(str(p) for p in parts)
    return hashlib.md5(key_str.encode()).hexdigest()


def _get_cached(cache_key: str) -> list[dict[str, Any]] | None:
    """Retrieve from cache if fresh."""
    if cache_key in _search_cache:
        results, timestamp = _search_cache[cache_key]
        if datetime.utcnow() - timestamp < timedelta(seconds=CACHE_TTL_SECONDS):
            logger.debug(f"Cache hit for {cache_key}")
            return results
        else:
            del _search_cache[cache_key]
    return None


def _set_cached(cache_key: str, results: list[dict[str, Any]]) -> None:
    """Store in cache."""
    _search_cache[cache_key] = (results, datetime.utcnow())
    logger.debug(f"Cached {len(results)} results for {cache_key}")


async def search_destinations_by_text(
    query: str,
    limit: int = 20,
    category_filter: str | None = None,
) -> list[dict[str, Any]]:
    """
    Search for destinations by text query.
    
    Returns list of normalized place objects with:
    - place_id, name, address, locality, administrative_area
    - latitude, longitude, types/categories
    - rating, user_rating_count (if available)
    - data_source: "geoapify"
    
    Args:
        query: Search text (city name, attraction, etc.)
        limit: Max results to return (1-50)
        category_filter: Optional Geoapify category to filter results
        
    Raises:
        GeoapifyError: If Geoapify is unavailable or API key is invalid
        ValueError: If query is invalid
    """
    validate_configuration()
    
    query = query.strip()
    if not query or len(query) < 2:
        raise ValueError("Search query must be at least 2 characters")
    
    if len(query) > 256:
        raise ValueError("Search query too long (max 256 characters)")
    
    limit = max(1, min(int(limit), 50))
    
    # Check cache
    cache_key = _cache_key("text_search", query, {"category": category_filter, "limit": limit})
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached
    
    api_key = settings.GEOAPIFY_API_KEY.strip()
    
    params: dict[str, str | int] = {
        "apiKey": api_key,
        "text": query,
        "limit": limit,
        "lang": "en",
        "type": "city",  # Prioritize city-level results
        "countrycode": "in",  # Restrict to India
    }
    
    if category_filter:
        params["type"] = "amenity"  # Switch to amenities for category search
    
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(settings.GEOAPIFY_TIMEOUT_SECONDS, connect=4.0)
        ) as client:
            response = await client.get(GEOCODING_URL, params=params)
        
        code = response.status_code
        
        if code == 401 or code == 403:
            raise GeoapifyError(
                "Geoapify API key invalid or access denied",
                status_code=503
            )
        if code == 429:
            raise GeoapifyError(
                "Geoapify rate limit exceeded. Please try again later.",
                status_code=429
            )
        if code >= 500:
            raise GeoapifyError(
                "Geoapify is temporarily unavailable",
                status_code=503
            )
        
        response.raise_for_status()
        body = response.json()
        
        results_raw = body.get("results", [])
        if not isinstance(results_raw, list):
            raise GeoapifyError("Invalid Geoapify response format", status_code=502)
        
        # Normalize results
        normalized = []
        for item in results_raw:
            if not isinstance(item, dict):
                continue
            
            # Convert Geoapify geocoding result to place format
            place = {
                "place_id": item.get("place_id") or str(item.get("address_line1", "")),
                "name": item.get("address_line1") or item.get("name") or "",
                "address": item.get("formatted", ""),
                "locality": item.get("city") or item.get("town") or "",
                "administrative_area": item.get("state"),
                "latitude": float(item.get("lat", 0)),
                "longitude": float(item.get("lon", 0)),
                "country": item.get("country"),
                "country_code": item.get("country_code"),
                "types": [item.get("result_type", "city")],
                "categories": item.get("categories", []) if isinstance(item.get("categories"), list) else [],
                "rating": None,  # Geocoding results don't include ratings
                "user_rating_count": None,
                "data_source": "geoapify",
            }
            
            # Validate it's actually in India
            if is_destination_in_india(place):
                normalized.append(place)
        
        # Cache before returning
        _set_cached(cache_key, normalized)
        
        return normalized
        
    except GeoapifyError:
        raise
    except httpx.TimeoutException:
        logger.warning("Geoapify geocoding request timed out")
        raise GeoapifyError(
            "Search request timed out. Please try again.",
            status_code=503
        )
    except Exception as exc:
        logger.error(f"Geoapify geocoding error: {exc}")
        raise GeoapifyError(
            "Failed to search destinations",
            status_code=503
        )


async def resolve_location_coordinates(
    location_text: str,
) -> tuple[float, float, str]:
    """
    Resolve a location text to coordinates and canonical name.
    
    Used by Multi-Stop Planner to geocode stop names.
    
    Args:
        location_text: Place name or address string
        
    Returns:
        (latitude, longitude, canonical_name)
        
    Raises:
        GeoapifyError: If location cannot be resolved or API fails
    """
    validate_configuration()
    
    location_text = location_text.strip()
    if not location_text or len(location_text) < 2:
        raise GeoapifyError(
            "Location name must be at least 2 characters",
            status_code=400
        )
    
    # Try cache
    cache_key = _cache_key("geocode", location_text)
    cached = _get_cached(cache_key)
    if cached:
        if cached:
            place = cached[0]
            result = (place["latitude"], place["longitude"], place["name"])
            return result
    
    api_key = settings.GEOAPIFY_API_KEY.strip()
    
    params = {
        "apiKey": api_key,
        "text": location_text,
        "countrycode": "in",
        "limit": 1,
        "lang": "en",
    }
    
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(settings.GEOAPIFY_TIMEOUT_SECONDS, connect=4.0)
        ) as client:
            response = await client.get(GEOCODING_URL, params=params)
        
        if response.status_code >= 400:
            raise GeoapifyError(
                f"Could not resolve location: {location_text}",
                status_code=422
            )
        
        body = response.json()
        results = body.get("results", [])
        
        if not results:
            raise GeoapifyError(
                f"Location not found: {location_text}",
                status_code=404
            )
        
        top = results[0]
        lat = float(top.get("lat", 0))
        lon = float(top.get("lon", 0))
        name = top.get("address_line1") or location_text
        
        validate_coordinates(lat, lon)
        
        # Cache the result
        place = {
            "place_id": location_text,
            "name": name,
            "latitude": lat,
            "longitude": lon,
            "address": top.get("formatted", ""),
            "data_source": "geoapify",
        }
        _set_cached(cache_key, [place])
        
        return (lat, lon, name)
        
    except GeoapifyError:
        raise
    except Exception as exc:
        logger.error(f"Location resolution error: {exc}")
        raise GeoapifyError(
            f"Failed to resolve location: {location_text}",
            status_code=503
        )


async def search_nearby_attractions(
    latitude: float,
    longitude: float,
    categories: list[str] | None = None,
    radius_m: int = 5000,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Search for attractions near coordinates.
    
    Used to populate nearby places in destination detail views.
    
    Args:
        latitude: Center latitude
        longitude: Center longitude
        categories: Optional list of Geoapify categories to filter
        radius_m: Search radius in meters (default 5km)
        limit: Max results to return
        
    Returns:
        List of normalized place objects
        
    Raises:
        GeoapifyError: If API fails
    """
    validate_configuration()
    validate_coordinates(latitude, longitude)
    
    limit = max(1, min(int(limit), 50))
    radius_m = max(1000, min(int(radius_m), 50000))
    
    api_key = settings.GEOAPIFY_API_KEY.strip()
    
    # Default categories if none specified
    if not categories:
        categories = [
            "tourism.attraction",
            "tourism.sights",
            "leisure.park",
            "natural",
        ]
    
    params = {
        "apiKey": api_key,
        "categories": ",".join(categories[:5]),  # Limit to 5 categories
        "filter": f"circle:{longitude},{latitude},{int(radius_m)}",
        "bias": f"proximity:{longitude},{latitude}",
        "limit": limit,
        "lang": "en",
    }
    
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(settings.GEOAPIFY_TIMEOUT_SECONDS, connect=4.0)
        ) as client:
            response = await client.get(PLACES_URL, params=params)
        
        if response.status_code >= 400:
            logger.warning(f"Geoapify nearby search failed: {response.status_code}")
            return []
        
        body = response.json()
        features = body.get("features", [])
        
        normalized = []
        for feature in features:
            if place := normalize_place(feature):
                if is_destination_in_india(place):
                    normalized.append(place)
        
        return normalized
        
    except Exception as exc:
        logger.error(f"Nearby attractions search error: {exc}")
        return []  # Return empty list instead of raising


async def explore_destinations_by_category(
    category: str,
    page: int = 1,
    limit: int = 20,
    search_term: str | None = None,
) -> dict[str, Any]:
    """
    Explore destinations by travel type category.
    
    Searches across major Indian destination hubs for places
    matching the travel category.
    
    Args:
        category: Travel type (Nature, Adventure, Beach, etc.)
        page: Page number (1-indexed)
        limit: Results per page
        search_term: Optional additional text filter
        
    Returns:
        {
            "destinations": [normalized place objects],
            "total": int,
            "page": int,
            "page_size": int,
            "has_more": bool,
        }
    """
    validate_configuration()
    
    limit = max(1, min(int(limit), 50))
    page = max(1, int(page))
    
    # Map travel categories to Geoapify categories
    category_map = {
        "Nature": ["natural", "leisure.park", "national_park"],
        "Adventure": ["natural.mountain", "camping", "tourism.attraction.viewpoint"],
        "Beach": ["beach", "natural.coastal"],
        "Religious": ["religion.place_of_worship", "tourism.sights.place_of_worship"],
        "City Exploration": ["tourism.attraction", "tourism.sights", "entertainment.museum"],
        "Family": ["entertainment.zoo", "entertainment.theme_park", "leisure.park"],
        "Romantic": ["beach", "tourism.attraction.viewpoint", "leisure.park"],
    }
    
    geoapify_categories = category_map.get(category, ["tourism.attraction"])
    
    # Expanded geographic destination hubs for broader coverage
    # Organized by region: South, North, East, West, Central, Northeast
    destination_hubs = [
        # South India - Beach & Nature
        ("Goa", 15.2993, 74.1240),
        ("Kochi", 9.9312, 76.2673),
        ("Thekkady", 9.5181, 77.2099),
        ("Pondicherry", 11.9416, 79.8083),
        ("Kanyakumari", 8.0883, 77.5385),
        
        # South India - Hill Stations
        ("Munnar", 10.0889, 77.0595),
        ("Ooty", 11.4102, 76.6950),
        ("Coorg", 12.3381, 75.7237),
        ("Kodaikanal", 10.2381, 77.4892),
        
        # North India - Mountain & Adventure
        ("Manali", 32.2396, 77.1887),
        ("Shimla", 31.1048, 77.1734),
        ("Nainital", 29.3803, 79.4636),
        ("Leh", 34.1526, 77.5771),
        ("Rishikesh", 30.0869, 78.2676),
        
        # North India - Golden Triangle & Plains
        ("Jaipur", 26.9124, 75.7873),
        ("Agra", 27.1767, 78.0081),
        ("Delhi", 28.6139, 77.2090),
        ("Mathura", 27.4924, 77.6737),
        
        # East India - Holy & Cultural
        ("Varanasi", 25.3176, 82.9739),
        ("Bodh Gaya", 24.4972, 84.9788),
        ("Kolkata", 22.5726, 88.3639),
        
        # Northeast India - Scenic & Adventure
        ("Darjeeling", 27.0410, 88.2663),
        ("Guwahati", 26.1445, 91.7362),
        ("Shillong", 25.5788, 91.8933),
        ("Imphal", 24.8170, 94.9061),
        
        # West India - Urban & Coastal
        ("Mumbai", 19.0760, 72.8777),
        ("Pune", 18.5204, 73.8567),
        ("Ahmedabad", 23.0225, 72.5714),
        ("Rajkot", 22.3039, 70.8022),
        
        # West India - Desert & Culture
        ("Jaisalmer", 26.9124, 70.9207),
        ("Udaipur", 24.5854, 73.7125),
        ("Pushkar", 26.4923, 74.5511),
        
        # Central India - Historical & Nature
        ("Indore", 22.7196, 75.8577),
        ("Bhopal", 23.1815, 79.9864),
        ("Jabalpur", 23.1815, 79.9864),
        ("Khajuraho", 24.8318, 79.9199),
        
        # Islands
        ("Port Blair", 11.6234, 92.7265),
        ("Lakshadweep", 10.5667, 72.7417),
    ]
    
    all_places = []
    
    # Search each hub in parallel with expanded result limits
    tasks = [
        search_nearby_attractions(
            lat, lon,
            categories=geoapify_categories,
            radius_m=10000,  # Increased from 8km to 10km radius per hub
            limit=100,  # Increased from 50 to 100 results per hub
        )
        for name, lat, lon in destination_hubs
    ]
    
    try:
        results = await asyncio.gather(*tasks, return_exceptions=False)
        for result in results:
            if isinstance(result, list):
                all_places.extend(result)
    except Exception as exc:
        logger.error(f"Error exploring destinations: {exc}")
        return {
            "destinations": [],
            "total": 0,
            "page": page,
            "page_size": limit,
            "has_more": False,
            "error": str(exc),
        }
    
    # Deduplicate by place_id
    deduped = {p["place_id"]: p for p in all_places}
    
    # Optional text filter
    if search_term:
        search_term_lower = search_term.lower()
        deduped = {
            pid: p for pid, p in deduped.items()
            if search_term_lower in p.get("name", "").lower()
            or search_term_lower in p.get("address", "").lower()
        }
    
    # Sort by rating if available
    sorted_places = sorted(
        deduped.values(),
        key=lambda x: (
            x.get("rating") or 0,
            x.get("user_rating_count") or 0,
        ),
        reverse=True,
    )
    
    # Paginate
    total = len(sorted_places)
    start = (page - 1) * limit
    end = start + limit
    paginated = sorted_places[start:end]
    
    return {
        "destinations": paginated,
        "total": total,
        "page": page,
        "page_size": limit,
        "has_more": end < total,
    }


def clear_cache() -> None:
    """Clear all search caches. Useful for testing."""
    global _search_cache
    _search_cache.clear()
    logger.info("Search cache cleared")
