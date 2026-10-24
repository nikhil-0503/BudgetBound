"""Google Places API (New) client. API keys are backend-only."""
import logging
from typing import Any

import httpx

from app.config import settings
from app.services.weather import validate_coordinates

logger = logging.getLogger(__name__)
TEXT_URL = "https://places.googleapis.com/v1/places:searchText"
NEARBY_URL = "https://places.googleapis.com/v1/places:searchNearby"
FIELD_MASK = ",".join((
    "places.id", "places.displayName", "places.formattedAddress", "places.location",
    "places.primaryType", "places.types", "places.rating", "places.userRatingCount",
    "places.priceLevel", "places.googleMapsUri", "places.websiteUri",
    "places.regularOpeningHours", "places.reviews", "places.addressComponents",
))


def _address_component(item: dict[str, Any], component_type: str, field: str):
    components = item.get("addressComponents")
    if not isinstance(components, list):
        return None
    for component in components:
        if not isinstance(component, dict) or not isinstance(component.get("types"), list):
            continue
        if component_type in component["types"]:
            value = component.get(field)
            return value.strip() if isinstance(value, str) and value.strip() else None
    return None


def is_destination_in_india(candidate: dict[str, Any]) -> bool:
    """Accept only candidates with an explicit Indian ISO code and valid coordinates."""
    code = candidate.get("country_code")
    if not isinstance(code, str) or code.strip().upper() != "IN":
        return False
    try:
        lat, lon = float(candidate.get("latitude")), float(candidate.get("longitude"))
        validate_coordinates(lat, lon)
    except (TypeError, ValueError):
        return False
    return True


class PlacesError(Exception):
    pass


def normalize_place(item: dict[str, Any]) -> dict[str, Any] | None:
    place_id = item.get("id")
    name = (item.get("displayName") or {}).get("text")
    point = item.get("location") or {}
    lat, lng = point.get("latitude"), point.get("longitude")
    if not place_id or not name or lat is None or lng is None:
        return None
    try:
        lat, lng = float(lat), float(lng)
        validate_coordinates(lat, lng)
    except (TypeError, ValueError):
        return None
    return {
        "place_id": place_id,
        "name": name,
        "address": item.get("formattedAddress"),
        "locality": _address_component(item, "locality", "longText"),
        "administrative_area": _address_component(item, "administrative_area_level_2", "longText"),
        "country": _address_component(item, "country", "longText"),
        "country_code": (_address_component(item, "country", "shortText") or "").upper() or None,
        "latitude": lat,
        "longitude": lng,
        "primary_type": item.get("primaryType"),
        "types": item.get("types", []),
        "rating": item.get("rating"),
        "user_rating_count": item.get("userRatingCount"),
        "price_level": item.get("priceLevel"),
        "google_maps_url": item.get("googleMapsUri"),
        "website_url": item.get("websiteUri"),
        "opening_hours": item.get("regularOpeningHours"),
        "reviews": [
            {"rating": review.get("rating"), "text": (review.get("text") or {}).get("text"), "publish_time": review.get("publishTime"), "google_maps_url": review.get("googleMapsUri"), "author_name": (review.get("authorAttribution") or {}).get("displayName"), "author_url": (review.get("authorAttribution") or {}).get("uri"), "visit_date": review.get("visitDate")}
            for review in item.get("reviews", [])[:3]
        ],
        "data_source": "google_places",
    }


async def _request(url: str, body: dict[str, Any], *, country_code: str | None = None, diagnostics: dict[str, int] | None = None) -> list[dict[str, Any]]:
    if not settings.GOOGLE_MAPS_API_KEY:
        raise PlacesError("Google Places is not configured. Set GOOGLE_MAPS_API_KEY on the backend.")
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(settings.GOOGLE_PLACES_TIMEOUT_SECONDS, connect=4.0)) as client:
            response = await client.post(url, json=body, headers={"X-Goog-Api-Key": settings.GOOGLE_MAPS_API_KEY, "X-Goog-FieldMask": FIELD_MASK})
        if response.status_code in (401, 403):
            raise PlacesError("Google Places rejected the API key or its permissions.")
        if response.status_code == 429:
            raise PlacesError("Google Places quota or rate limit was reached.")
        response.raise_for_status()
        raw = response.json()
        entries = raw.get("places", [])
        if not isinstance(entries, list):
            raise PlacesError("Google Places returned an invalid response.")
        if diagnostics is not None:
            diagnostics["received"] = diagnostics.get("received", 0) + len(entries)
        deduplicated = {}
        for entry in entries:
            place = normalize_place(entry)
            if place and diagnostics is not None:
                diagnostics["normalized"] = diagnostics.get("normalized", 0) + 1
            if country_code and not is_destination_in_india(place or {}):
                if diagnostics is not None:
                    diagnostics["country_rejected"] = diagnostics.get("country_rejected", 0) + 1
                continue
            if place:
                deduplicated[place["place_id"]] = place
        if diagnostics is not None:
            diagnostics["deduplicated"] = diagnostics.get("deduplicated", 0) + len(deduplicated)
        return list(deduplicated.values())
    except PlacesError:
        raise
    except httpx.TimeoutException as exc:
        logger.warning("Google Places timed out")
        raise PlacesError("Google Places request timed out.") from exc
    except httpx.HTTPStatusError as exc:
        logger.warning("Google Places returned HTTP %s", exc.response.status_code)
        raise PlacesError("Google Places returned an upstream error.") from exc
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        logger.warning("Google Places response was unavailable or malformed")
        raise PlacesError("Google Places data is temporarily unavailable.") from exc


async def text_search(query: str, *, page_size: int = 8, region_code: str | None = None, country_code: str | None = None, diagnostics: dict[str, int] | None = None) -> list[dict[str, Any]]:
    body = {"textQuery": query, "pageSize": min(max(page_size, 1), 20), "languageCode": "en"}
    if region_code:
        body["regionCode"] = region_code.strip().upper()
    return await _request(TEXT_URL, body, country_code=country_code, diagnostics=diagnostics)


async def nearby_search(latitude: float, longitude: float, included_types: list[str], *, radius: float = 12000, page_size: int = 10, country_code: str | None = None) -> list[dict[str, Any]]:
    validate_coordinates(latitude, longitude)
    types = [t for t in included_types if t in {"tourist_attraction", "museum", "park", "art_gallery", "restaurant", "beach", "historical_landmark"}]
    body = {"includedTypes": types or ["tourist_attraction"], "maxResultCount": min(max(page_size, 1), 20), "locationRestriction": {"circle": {"center": {"latitude": latitude, "longitude": longitude}, "radius": min(max(radius, 1), 50000)}}}
    return await _request(NEARBY_URL, body, country_code=country_code)
