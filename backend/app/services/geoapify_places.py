"""Geoapify Places API client used by budget-first origin discovery."""
import logging
import math
from typing import Any

import httpx

from app.config import settings
from app.services.weather import validate_coordinates

logger = logging.getLogger(__name__)
PLACES_URL = "https://api.geoapify.com/v2/places"

# Geoapify's category hierarchy is distinct from Google Places types.
CATEGORY_MAP: dict[str, tuple[str, ...]] = {
    "Nature": ("national_park", "natural", "leisure.park"),
    # Adventure deliberately excludes generic sports facilities and attractions.
    "Adventure": ("national_park", "natural.mountain", "natural.water.whitewater", "natural.protected_area", "camping", "tourism.attraction.viewpoint"),
    "Family": ("entertainment.zoo", "entertainment.aquarium", "entertainment.theme_park", "entertainment.water_park"),
    "Religious": ("religion.place_of_worship", "tourism.sights.place_of_worship", "tourism.sights.monastery"),
    "Beach": ("beach", "natural.coastal"),
    "City Exploration": ("tourism.attraction", "tourism.sights", "entertainment.museum", "building.historic"),
    "Romantic": ("beach", "natural.water", "tourism.attraction.viewpoint", "leisure.park"),
    "Solo": ("tourism.attraction", "tourism.sights", "natural", "entertainment.museum", "leisure.park"),
}

# Stable reference points used only to validate coordinates supplied by the
# location picker. Internal coordinates are always (latitude, longitude).
ORIGIN_REFERENCES: dict[str, tuple[float, float]] = {
    "delhi": (28.6139, 77.2090), "new delhi": (28.6139, 77.2090),
    "jaipur": (26.9124, 75.7873), "agra": (27.1767, 78.0081),
    "dehradun": (30.3165, 78.0322), "manali": (32.2396, 77.1887),
    "srinagar": (34.0837, 74.7973), "varanasi": (25.3176, 82.9739),
    "kolkata": (22.5726, 88.3639), "darjeeling": (27.0410, 88.2663),
    "guwahati": (26.1445, 91.7362), "shillong": (25.5788, 91.8933),
    "mumbai": (19.0760, 72.8777), "goa": (15.2993, 74.1240),
    "pune": (18.5204, 73.8567), "ahmedabad": (23.0225, 72.5714),
    "bengaluru": (12.9716, 77.5946), "bangalore": (12.9716, 77.5946),
    "mysuru": (12.2958, 76.6394), "mysore": (12.2958, 76.6394),
    "ooty": (11.4102, 76.6950), "kochi": (9.9312, 76.2673),
    "munnar": (10.0889, 77.0595), "chennai": (13.0827, 80.2707),
    "madurai": (9.9252, 78.1198), "hyderabad": (17.3850, 78.4867),
    "visakhapatnam": (17.6868, 83.2185), "bhubaneswar": (20.2961, 85.8245),
    "puri": (19.8135, 85.8312), "port blair": (11.6234, 92.7265),
    "gurgaon": (28.4595, 77.0266), "gurugram": (28.4595, 77.0266),
    "pondicherry": (11.9416, 79.8083), "puducherry": (11.9416, 79.8083),
    "coimbatore": (11.0168, 76.9558), "indore": (22.7196, 75.8577),
    "lucknow": (26.8467, 80.9462), "rishikesh": (30.0869, 78.2676),
    "nainital": (29.3803, 79.4636), "shimla": (31.1048, 77.1734),
}
ORIGIN_ALIASES = {"bombay": "mumbai", "calcutta": "kolkata", "madras": "chennai", "gurgaon": "gurugram", "mysore": "mysuru", "bangalore": "bengaluru", "pondicherry": "puducherry"}
CITY_ALIASES = ORIGIN_ALIASES | {"new delhi": "delhi", "vizag": "visakhapatnam", "cochin": "kochi", "trivandrum": "thiruvananthapuram", "banaras": "varanasi"}
PREFERRED_LOCALITY_NAMES = {
    "bengaluru": "Bengaluru", "mysuru": "Mysuru", "mumbai": "Mumbai", "kolkata": "Kolkata",
    "chennai": "Chennai", "gurugram": "Gurugram", "puducherry": "Puducherry",
    "visakhapatnam": "Visakhapatnam", "kochi": "Kochi", "thiruvananthapuram": "Thiruvananthapuram",
    "varanasi": "Varanasi", "delhi": "Delhi",
}
ADMINISTRATIVE_AREA_ALIASES = {
    "national capital territory of delhi": "delhi", "nct of delhi": "delhi",
    "orissa": "odisha", "uttaranchal": "uttarakhand",
}


def normalized_locality(value: str) -> str:
    import re
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", str(value or "").casefold()).split())


def canonical_locality(value: str) -> str:
    normalized = normalized_locality(value)
    return CITY_ALIASES.get(normalized, normalized)


def display_locality(value: str) -> str:
    canonical = canonical_locality(value)
    return PREFERRED_LOCALITY_NAMES.get(canonical, canonical.title())


def canonical_administrative_area(value: str) -> str:
    normalized = normalized_locality(value)
    return ADMINISTRATIVE_AREA_ALIASES.get(normalized, normalized)


def origin_reference(name: str) -> tuple[float, float] | None:
    normalized = normalized_locality(name).split(",", 1)[0].strip()
    normalized = ORIGIN_ALIASES.get(normalized, normalized)
    return ORIGIN_REFERENCES.get(normalized)

# A bounded coverage grid of established Indian destination hubs. Each 60 km
# circle discovers POIs/cities around that hub; origin remains a separate query
# so nearby getaways can still appear. This is broad discovery, not a claim that
# every Indian destination or route is exhaustively covered.
DESTINATION_AREAS: tuple[tuple[str, float, float], ...] = (
    ("Delhi", 28.6139, 77.2090), ("Jaipur", 26.9124, 75.7873), ("Agra", 27.1767, 78.0081),
    ("Dehradun", 30.3165, 78.0322), ("Manali", 32.2396, 77.1887), ("Srinagar", 34.0837, 74.7973),
    ("Varanasi", 25.3176, 82.9739), ("Khajuraho", 24.8318, 79.9199), ("Kolkata", 22.5726, 88.3639),
    ("Darjeeling", 27.0410, 88.2663), ("Guwahati", 26.1445, 91.7362), ("Shillong", 25.5788, 91.8933),
    ("Mumbai", 19.0760, 72.8777), ("Goa", 15.2993, 74.1240), ("Pune", 18.5204, 73.8567),
    ("Ahmedabad", 23.0225, 72.5714), ("Bengaluru", 12.9716, 77.5946), ("Mysuru", 12.2958, 76.6394),
    ("Ooty", 11.4102, 76.6950), ("Kochi", 9.9312, 76.2673), ("Munnar", 10.0889, 77.0595),
    ("Chennai", 13.0827, 80.2707), ("Madurai", 9.9252, 78.1198), ("Hyderabad", 17.3850, 78.4867),
    ("Visakhapatnam", 17.6868, 83.2185), ("Bhubaneswar", 20.2961, 85.8245), ("Puri", 19.8135, 85.8312),
    ("Port Blair", 11.6234, 92.7265),
)


class GeoapifyError(Exception):
    def __init__(self, message: str, *, status_code: int = 503):
        super().__init__(message)
        self.status_code = status_code


def category_values(category: str) -> tuple[str, ...]:
    values = CATEGORY_MAP.get(category.casefold().title())
    if not values:
        raise GeoapifyError("Unsupported trip category. Choose one of the available planner categories.", status_code=400)
    return values


def validate_configuration() -> None:
    if not (settings.GEOAPIFY_API_KEY or "").strip():
        raise GeoapifyError("Geoapify is not configured. Set GEOAPIFY_API_KEY in the backend environment.")


def matched_trip_categories(place_categories: list[str] | tuple[str, ...] | set[str]) -> set[str]:
    normalized = {str(value).casefold() for value in place_categories}
    return {
        category
        for category, mapped in CATEGORY_MAP.items()
        if any(value.casefold() in normalized or any(found.startswith(value.casefold() + ".") for found in normalized) for value in mapped)
    }


def _properties(feature: dict[str, Any]) -> dict[str, Any]:
    properties = feature.get("properties")
    return properties if isinstance(properties, dict) else {}


def _coordinates_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    a1, a2 = math.radians(lat1), math.radians(lat2)
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    hav = math.sin(dlat/2) ** 2 + math.cos(a1) * math.cos(a2) * math.sin(dlon/2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(hav))


def normalize_place(feature: dict[str, Any]) -> dict[str, Any] | None:
    """Normalize GeoJSON feature properties without inferring unavailable ratings."""
    props = _properties(feature)
    geometry = feature.get("geometry") if isinstance(feature.get("geometry"), dict) else {}
    coordinates = geometry.get("coordinates") if isinstance(geometry.get("coordinates"), (list, tuple)) else []
    place_id = props.get("place_id") or feature.get("id")
    name = props.get("name") or props.get("address_line1")
    try:
        raw_lon = props.get("lon") if props.get("lon") is not None else coordinates[0]
        raw_lat = props.get("lat") if props.get("lat") is not None else coordinates[1]
        lon, lat = float(raw_lon), float(raw_lat)
        validate_coordinates(lat, lon)
        if len(coordinates) >= 2 and props.get("lat") is not None and props.get("lon") is not None:
            geometry_lon, geometry_lat = float(coordinates[0]), float(coordinates[1])
            validate_coordinates(geometry_lat, geometry_lon)
            if _coordinates_distance_km(lat, lon, geometry_lat, geometry_lon) > 1.0:
                return None
    except (IndexError, TypeError, ValueError):
        return None
    if not place_id or not name:
        return None
    cats = props.get("categories")
    if isinstance(cats, str):
        cats = [cats]
    if not isinstance(cats, list):
        cats = []
    country_code = props.get("country_code")
    rating = props.get("rating")
    try:
        rating = float(rating) if isinstance(rating, (int, float)) and not isinstance(rating, bool) else None
    except (TypeError, ValueError):
        rating = None
    if rating is not None and (not math.isfinite(rating) or not 1 <= rating <= 5):
        rating = None
    review_count = props.get("review_count")
    if not isinstance(review_count, int) or isinstance(review_count, bool) or review_count < 0:
        review_count = None
    return {
        "place_id": str(place_id),
        "name": str(name),
        "address": props.get("formatted") or ", ".join(str(v) for v in (props.get("address_line1"), props.get("address_line2")) if v) or None,
        "country": props.get("country"),
        "country_code": str(country_code).upper() if country_code else None,
        "locality": props.get("city") or props.get("town") or props.get("village") or props.get("municipality"),
        "administrative_area": props.get("state") or props.get("county"),
        "latitude": lat,
        "longitude": lon,
        "types": cats,
        "categories": cats,
        "primary_type": cats[0] if cats else None,
        "rating": rating,
        "user_rating_count": review_count,
        "google_maps_url": None,
        "map_url": props.get("place_url") or props.get("url") or None,
        "data_source": "geoapify",
    }


def is_destination_in_india(candidate: dict[str, Any]) -> bool:
    if str(candidate.get("country_code") or "").strip().casefold() != "in":
        return False
    country = " ".join(str(candidate.get("country") or "").casefold().split())
    if country not in {"india", "republic of india"}:
        return False
    try:
        validate_coordinates(float(candidate.get("latitude")), float(candidate.get("longitude")))
    except (TypeError, ValueError):
        return False
    lat, lon = float(candidate["latitude"]), float(candidate["longitude"])
    # A claimed IN code alone is insufficient if coordinates land abroad.
    return 6.0 <= lat <= 38.0 and 67.0 <= lon <= 98.0


async def search_places(*, latitude: float, longitude: float, radius_m: int, categories: tuple[str, ...] | list[str], limit: int = 40, diagnostics: dict[str, int] | None = None) -> list[dict[str, Any]]:
    """Query one bounded area. Spatial filter uses Geoapify's lon,lat ordering."""
    validate_configuration()
    api_key = settings.GEOAPIFY_API_KEY.strip()
    validate_coordinates(latitude, longitude)
    safe_categories = tuple(dict.fromkeys(categories))
    supported = {item for values in CATEGORY_MAP.values() for item in values} | {"natural", "tourism", "camping", "beach", "leisure.park", "national_park"}
    if not safe_categories or any(not isinstance(value, str) or value not in supported for value in safe_categories):
        raise GeoapifyError("Geoapify category configuration is invalid.", status_code=400)
    params = {
        "apiKey": api_key,
        "categories": ",".join(safe_categories),
        "filter": f"circle:{longitude},{latitude},{int(radius_m)}",
        "bias": f"proximity:{longitude},{latitude}",
        "limit": min(max(int(limit), 1), 100),
        "lang": "en",
    }
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(settings.GEOAPIFY_TIMEOUT_SECONDS, connect=4.0)) as client:
            response = await client.get(PLACES_URL, params=params)
        code = response.status_code
        if code in (401, 403):
            raise GeoapifyError("Geoapify rejected the API key or its restrictions. Check GEOAPIFY_API_KEY and its Places API permissions.", status_code=503)
        if code == 400:
            raise GeoapifyError("Geoapify rejected the categories or geographic search parameters. Check the configured category mapping.", status_code=502)
        if code == 429:
            raise GeoapifyError("Geoapify rate limit or quota exceeded. Retry later or check the project quota.", status_code=429)
        if code >= 500:
            raise GeoapifyError("Geoapify Places is temporarily unavailable. Retry later.", status_code=503)
        if 400 <= code < 500:
            raise GeoapifyError("Geoapify rejected the Places request. Check the categories and geographic parameters.", status_code=502)
        response.raise_for_status()
        body = response.json()
        features = body.get("features", []) if isinstance(body, dict) else None
        if not isinstance(features, list):
            raise GeoapifyError("Geoapify returned an invalid Places response.", status_code=502)
        if diagnostics is not None:
            diagnostics["received"] = diagnostics.get("received", 0) + len(features)
        normalized = [place for feature in features if isinstance(feature, dict) if (place := normalize_place(feature)) is not None]
        if diagnostics is not None:
            diagnostics["normalized"] = diagnostics.get("normalized", 0) + len(normalized)
        deduped = {place["place_id"]: place for place in normalized}
        if diagnostics is not None:
            diagnostics["country_rejected"] = diagnostics.get("country_rejected", 0) + sum(not is_destination_in_india(place) for place in deduped.values())
            diagnostics["deduplicated"] = diagnostics.get("deduplicated", 0) + len(deduped)
        return list(deduped.values())
    except GeoapifyError:
        raise
    except httpx.TimeoutException as exc:
        logger.warning("Geoapify Places request timed out")
        raise GeoapifyError("Geoapify Places request timed out. Retry later.") from exc
    except httpx.HTTPStatusError as exc:
        code = exc.response.status_code
        logger.warning("Geoapify Places returned HTTP %s", code)
        raise GeoapifyError("Geoapify Places returned an upstream error.", status_code=503) from exc
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        logger.warning("Geoapify Places response was unavailable or malformed")
        raise GeoapifyError("Geoapify Places data is temporarily unavailable.") from exc
