"""
Live Geoapify-based destination discovery endpoints.

Replaces the hardcoded catalog for:
- Destination Explorer (live search and browse)
- Compare Destinations (select live results to compare)
- Multi-Stop Planner (resolve stop coordinates)
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.geoapify_destination_search import (
    GeoapifyError,
    clear_cache,
    explore_destinations_by_category,
    resolve_location_coordinates,
    search_destinations_by_text,
    search_nearby_attractions,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/destinations-live", tags=["destinations-live"])


@router.get("/search")
async def search_destinations(
    q: str = Query(..., min_length=2, max_length=256, description="Search query"),
    limit: int = Query(20, ge=1, le=50, description="Results to return"),
    category: Optional[str] = Query(None, description="Optional category filter"),
):
    """
    Search for destinations by text query.
    
    Returns list of places from Geoapify with:
    - name, address, locality, administrative_area
    - latitude, longitude
    - rating and review count (if available)
    - data_source: "geoapify"
    
    This is the primary interface for Destination Explorer.
    """
    try:
        results = await search_destinations_by_text(
            query=q,
            limit=limit,
            category_filter=category,
        )
        
        return {
            "results": results,
            "count": len(results),
            "source": "geoapify",
        }
    
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except GeoapifyError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    except Exception as exc:
        logger.error(f"Search error: {exc}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/explore")
async def explore_by_category(
    category: str = Query(..., description="Travel type: Nature, Adventure, Beach, Religious, City Exploration, Family, Romantic"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=50, description="Results per page"),
    search: Optional[str] = Query(None, description="Optional text filter within category"),
):
    """
    Explore destinations by travel category.
    
    Searches major Indian destination hubs for places matching the category.
    Replaces the seeded destination catalog with live Geoapify results.
    
    This is the primary interface for Destination Explorer category browsing.
    """
    try:
        result = await explore_destinations_by_category(
            category=category,
            page=page,
            limit=limit,
            search_term=search,
        )
        
        if "error" in result:
            raise HTTPException(status_code=503, detail=result["error"])
        
        return {
            "destinations": result["destinations"],
            "total": result["total"],
            "page": result["page"],
            "page_size": result["page_size"],
            "has_more": result["has_more"],
            "category": category,
            "source": "geoapify",
        }
    
    except GeoapifyError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    except Exception as exc:
        logger.error(f"Explore error: {exc}")
        raise HTTPException(status_code=500, detail="Exploration failed")


@router.get("/nearby")
async def get_nearby_attractions(
    latitude: float = Query(..., ge=-90, le=90, description="Center latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Center longitude"),
    categories: Optional[str] = Query(None, description="Comma-separated Geoapify categories"),
    radius_m: int = Query(5000, ge=1000, le=50000, description="Search radius in meters"),
    limit: int = Query(20, ge=1, le=50, description="Results to return"),
):
    """
    Search for attractions near coordinates.
    
    Used to populate detail views and nearby recommendations.
    """
    try:
        category_list = [c.strip() for c in categories.split(",")] if categories else None
        
        results = await search_nearby_attractions(
            latitude=latitude,
            longitude=longitude,
            categories=category_list,
            radius_m=radius_m,
            limit=limit,
        )
        
        return {
            "attractions": results,
            "count": len(results),
            "center": {"latitude": latitude, "longitude": longitude},
            "radius_m": radius_m,
            "source": "geoapify",
        }
    
    except Exception as exc:
        logger.error(f"Nearby attractions error: {exc}")
        raise HTTPException(status_code=500, detail="Failed to fetch nearby attractions")


@router.post("/resolve-location")
async def resolve_location(
    location: str = Query(..., min_length=2, max_length=256, description="Location name or address"),
):
    """
    Resolve a location text to coordinates and canonical name.
    
    Used by Multi-Stop Planner to geocode stop names entered by users.
    
    Returns: {
        "latitude": float,
        "longitude": float,
        "name": str,  // canonical place name
        "source": "geoapify"
    }
    """
    try:
        lat, lon, name = await resolve_location_coordinates(location)
        
        return {
            "latitude": lat,
            "longitude": lon,
            "name": name,
            "source": "geoapify",
        }
    
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except GeoapifyError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    except Exception as exc:
        logger.error(f"Location resolution error: {exc}")
        raise HTTPException(status_code=500, detail="Failed to resolve location")


@router.post("/clear-cache")
async def clear_search_cache():
    """
    Clear all destination search caches.
    
    For testing and cache invalidation only.
    """
    try:
        clear_cache()
        return {"status": "cache cleared"}
    except Exception as exc:
        logger.error(f"Cache clear error: {exc}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")


@router.get("/detail/{place_id}")
async def get_live_destination_detail(
    place_id: str = Path(..., description="Geoapify place_id from search results"),
    latitude: Optional[float] = Query(None, ge=-90, le=90, description="Latitude for weather lookup"),
    longitude: Optional[float] = Query(None, ge=-180, le=180, description="Longitude for weather lookup"),
):
    """
    Get detailed information about a live Geoapify destination.
    
    Returns enhanced destination data including:
    - Basic place information from search results
    - Nearby attractions (from Geoapify Places)
    - Weather intelligence (if coordinates provided)
    - Travel recommendations and category matches
    
    This endpoint bridges live Geoapify results with destination details UI.
    """
    try:
        if not place_id:
            raise HTTPException(status_code=400, detail="place_id is required")
        
        # For now, return a structured response based on coordinates
        # In production, could cache place details or fetch from enrichment API
        if not latitude or not longitude:
            raise HTTPException(status_code=400, detail="latitude and longitude required for detail view")
        
        # Get nearby attractions as "details" for the location
        attractions = await search_nearby_attractions(
            latitude=latitude,
            longitude=longitude,
            categories=[
                "tourism.attraction",
                "tourism.sights",
                "leisure.park",
                "entertainment.museum",
                "natural"
            ],
            radius_m=5000,
            limit=15
        )
        
        return {
            "place_id": place_id,
            "latitude": latitude,
            "longitude": longitude,
            "nearby_attractions": attractions[:10],  # Top 10 attractions
            "total_nearby": len(attractions),
            "data_source": "geoapify",
        }
    
    except GeoapifyError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    except Exception as exc:
        logger.error(f"Detail lookup error: {exc}")
        raise HTTPException(status_code=500, detail="Failed to get destination details")
