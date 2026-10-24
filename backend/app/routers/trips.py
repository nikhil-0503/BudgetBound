import io
import logging
import asyncio
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status, Query
# pyrefly: ignore [missing-import]
from fastapi.responses import StreamingResponse, Response
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from typing import List, Optional
import datetime
import math
import re

from app import models, schemas, auth
from app.database import get_db
from app.services.pdf_generator import generate_premium_trip_pdf
from app.services.gemini import gemini_service
from app.services.weather import get_forecast, WeatherServiceError, resolve_location
from app.services.google_places import nearby_search, PlacesError
from app.config import settings

# ReportLab imports for PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

router = APIRouter(prefix="/api/trips", tags=["Trips"])
logger = logging.getLogger(__name__)


def _place_queries(name: str, interests: list[str], cuisines: list[str], travel_type: str):
    queries = [f"top tourist attractions in {name}"]
    if travel_type.lower() in ("nature", "adventure", "beach"):
        queries.append(f"{travel_type} outdoor attractions in {name}")
    if interests:
        queries.append(f"{', '.join(interests)} attractions in {name}")
    if cuisines:
        queries.append(f"restaurants in {name} serving {', '.join(cuisines)} cuisine")
    else:
        queries.append(f"popular restaurants in {name}")
    return list(dict.fromkeys(queries))[:4]


async def _discover_live_places(name: str, interests: list[str], cuisines: list[str], travel_type: str, latitude=None, longitude=None, country_code: str | None = None):
    from app.services.google_places import text_search
    places, failures = {}, []
    for query in _place_queries(name, interests, cuisines, travel_type):
        try:
            for place in await text_search(query, page_size=7, region_code=country_code, country_code=country_code):
                places[place["place_id"]] = place
        except PlacesError as exc:
            failures.append(str(exc))
    if latitude is not None and longitude is not None:
        try:
            nearby = await nearby_search(latitude, longitude, ["tourist_attraction", "museum", "park", "restaurant"], page_size=12, country_code=country_code)
            for place in nearby:
                places[place["place_id"]] = place
        except PlacesError as exc:
            failures.append(str(exc))
    return list(places.values()), failures


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    a1, a2 = math.radians(lat1), math.radians(lat2)
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    hav = math.sin(dlat/2)**2 + math.cos(a1)*math.cos(a2)*math.sin(dlon/2)**2
    return 2 * radius * math.asin(math.sqrt(hav))


def _is_low_quality_destination_record(place: dict) -> bool:
    """Reject route labels and generic access/locality records as tourist evidence."""
    name = " ".join(str(place.get("name") or "").casefold().split())
    locality = " ".join(str(place.get("locality") or "").casefold().split())
    if not name or re.match(r"^(?:nh|sh|ah|mdr|odr)\s*[- ]?\d+[a-z]?$", name):
        return True
    if re.search(r"\b(?:road|street|highway|bypass|railway station|bus stand|junction)\b", name):
        return True
    if name in {"viewpoint", "view point", "scenic viewpoint", "viewing point", "unnamed viewpoint"}:
        return True
    categories = place.get("categories") or place.get("types") or []
    if name == locality and any(token == "highway" or token == "place" or token.startswith("place.") for token in categories):
        return True
    return False


def _is_weak_destination_evidence(place_count: int, categories: set[str], known_destination: bool, weighted_rating: float | None, rating_count: int) -> bool:
    """Reject small towns with weak tourist evidence unless recognized or anchor-anchored.
    
    Returns True if the destination should be rejected due to weak evidence.
    """
    # Known destinations (recognized hubs) always pass; their breadth is established.
    if known_destination:
        return False
    
    # Require at least 2 distinct places unless there's a strong anchor or rating.
    if place_count < 2:
        # Single attraction may pass if it's highly-rated or a major anchor (handled upstream)
        return True
    
    # For 2+ places, require verified tourist categories or good ratings.
    strong_categories = {
        "national_park", "protected_area", "mountain", "beach", "waterfall",
        "tourist_attraction", "museum", "zoo", "aquarium", "theme_park",
        "activity_park", "temple", "mosque", "church", "historical_site",
    }
    has_strong_category = any(
        category.casefold() in strong_categories or any(
            category.casefold().startswith(prefix + ".")
            for prefix in strong_categories
        )
        for category in categories
    )
    
    # If no strong categories and weak rating, reject.
    if not has_strong_category:
        if weighted_rating is None or weighted_rating < 3.5 or rating_count < 3:
            return True
    
    return False


def _keep_verified_itinerary_activities(itineraries: list[dict], verified_places: list[dict]) -> list[dict]:
    """Keep sightseeing references only when they resolve to a verified place in the selected destination."""
    for day in itineraries:
        valid_activities = []
        for activity in day.get("activities", []):
            title = str(activity.get("title", ""))
            logistics = any(word in title.casefold() for word in ("arrival", "check-in", "check out", "departure", "transfer"))
            matched = next((place for place in verified_places if place["name"].casefold() in title.casefold()), None)
            if logistics or matched:
                if matched:
                    activity["title"] = matched["name"]
                    activity["place_id"] = matched.get("place_id")
                    activity["latitude"] = matched.get("latitude")
                    activity["longitude"] = matched.get("longitude")
                valid_activities.append(activity)
        day["activities"] = valid_activities
    return itineraries


async def _discover_geoapify_destination_places(name: str, travel_type: str, latitude: float, longitude: float):
    """Fetch verified Indian attractions around a selected destination city."""
    from app.services import geoapify_places
    categories = geoapify_places.category_values(travel_type)
    rows = await geoapify_places.search_places(latitude=latitude, longitude=longitude, radius_m=30_000, categories=categories, limit=40)
    return [place for place in rows if geoapify_places.is_destination_in_india(place)], []


def _comfort_cost_factors(comfort_score: int) -> dict[str, float]:
    """Map comfort 0–100 linearly to modest spend adjustments, applied once per cost category."""
    comfort = min(100, max(0, comfort_score)) / 100
    return {
        "transport": 0.8 + 0.4 * comfort,
        "lodging": 0.8 + 0.4 * comfort,
        "food": 0.8 + 0.4 * comfort,
        "activities": 0.8 + 0.4 * comfort,
        "local_transport": 0.8 + 0.4 * comfort,
    }


def _origin_candidate_cost(distance_km: float, request: schemas.OriginDiscoveryRequest | schemas.TripPlanRequest) -> dict:
    """Return a deterministic INR estimate for the whole party and trip."""
    travelers, days = request.travelers_count, request.days
    factors = _comfort_cost_factors(request.comfort_score)
    nights = max(days - 1, 0)
    # Straight-line distance is converted to approximate road distance once.
    route_km = distance_km * 1.25
    rate = settings.TRIP_ESTIMATE_INTERCITY_PER_KM_INR * factors["transport"] * (2.2 if route_km > 500 else 1.0)
    # A fixed access baseline plus a distance component avoids giving unrelated
    # destinations identical transport estimates on the old ₹500 floor.
    transport = (500.0 + route_km * rate) * travelers
    lodging = 1800.0 * nights * travelers * factors["lodging"]
    food = 900.0 * days * travelers * factors["food"]
    activities = 500.0 * days * travelers * factors["activities"]
    local = 250.0 * days * travelers * factors["local_transport"]
    taxes = round((lodging + food + activities) * 0.05, 2)
    contingency = round((transport + lodging + food + activities + local + taxes) * 0.08, 2)
    total = round(transport + lodging + food + activities + local + taxes + contingency, 2)
    return {"transport_mode": "Comfort-adjusted intercity estimate", "hotel_tier": "Comfort-adjusted lodging estimate", "transport_cost": round(transport, 2), "hotel_cost": round(lodging, 2), "accommodation_nights": nights, "food_cost": round(food, 2), "food_travelers": travelers, "activities_cost": round(activities, 2), "local_transport_cost": round(local, 2), "taxes_fees_cost": taxes, "emergency_reserve": contingency, "total_estimated_cost": total, "comfort_factors": factors, "shared_cost_assumptions": "Lodging, meals, activities, and local transport use the same per-person planning assumptions across destinations; the intercity estimate changes with origin-to-destination straight-line distance.", "estimate_label": "Planning estimate, not a fare or accommodation quote"}


def _select_origin_candidates_for_ai(candidates: list[dict], limit: int) -> list[dict]:
    """Order every verified feasible candidate so batching ranks the best evidence first."""
    del limit  # The limit is per model request; ranker batching does not drop candidates.
    return sorted(candidates, key=lambda item: (
        -int(item.get("evidence_count") or len(item.get("verified_places") or [])),
        -len(item.get("verified_places") or []),
        -len(item.get("matched_categories") or []),
        float(item.get("estimated_cost", float("inf"))),
        -int(bool(item.get("address"))),
        float(item.get("distance_km", float("inf"))),
        str(item.get("destination_id", "")),
    ))


def _rank_origin_fallback(candidates: list[dict]) -> list[dict]:
    """Explicit fallback: sort feasible destinations by estimated cost and distance."""
    from app.services.ai_destination_ranker import fallback_rank_candidates
    return fallback_rank_candidates(candidates)


def _select_diverse_shortlist(ranked: list[dict], requested_size: int = 6) -> list[dict]:
    """Choose a compact, geographically varied set after all eligibility and ranking steps."""
    size = min(8, max(1, int(requested_size)), len(ranked)) if ranked else 0
    if not size:
        return []
    remaining = list(ranked)
    chosen: list[dict] = []
    regions: dict[str, int] = {}
    distance_bands: dict[str, int] = {}
    original_rank = {str(item.get("destination_id")): index for index, item in enumerate(ranked)}
    while remaining and len(chosen) < size:
        def selection_value(item: dict) -> tuple[float, int]:
            region = " ".join(str(item.get("region") or "unknown").casefold().split())
            distance = float(item.get("distance_km") or 0)
            band = "near" if distance < 250 else "mid" if distance < 700 else "far"
            model_score = item.get("overall_match_score")
            base = float(model_score) if isinstance(model_score, (int, float)) else 100.0 - original_rank[str(item.get("destination_id"))] * 2
            diversity_penalty = min(regions.get(region, 0), 2) * 12 + min(distance_bands.get(band, 0), 2) * 4
            proximity_penalty = 0.0
            for previous in chosen:
                try:
                    separation = _distance_km(float(item["latitude"]), float(item["longitude"]), float(previous["latitude"]), float(previous["longitude"]))
                    if separation < 40:
                        proximity_penalty = max(proximity_penalty, 30.0)
                except (KeyError, TypeError, ValueError):
                    continue
            try:
                budget = float(item.get("budget_limit") or 0)
                cost = float(item.get("estimated_cost") or budget)
                affordability_bonus = min(3.0, max(0.0, (budget - cost) / budget * 3)) if budget > 0 else 0.0
            except (TypeError, ValueError, ZeroDivisionError):
                affordability_bonus = 0.0
            return base - diversity_penalty - proximity_penalty + affordability_bonus, -original_rank[str(item.get("destination_id"))]
        best = max(remaining, key=selection_value)
        chosen.append(best)
        remaining.remove(best)
        region = " ".join(str(best.get("region") or "unknown").casefold().split())
        distance = float(best.get("distance_km") or 0)
        band = "near" if distance < 250 else "mid" if distance < 700 else "far"
        regions[region] = regions.get(region, 0) + 1
        distance_bands[band] = distance_bands.get(band, 0) + 1
    return chosen


async def _verified_origin_coordinates(name: str, latitude=None, longitude=None, address: str | None = None) -> tuple[float, float, str]:
    """Resolve or verify an origin while keeping internal coordinates lat/lon."""
    if (latitude is None) != (longitude is None):
        raise HTTPException(status_code=422, detail="Provide both starting-location coordinates, or leave both blank to resolve the selected city.")
    resolved_reference = None
    label = address or name
    if latitude is None:
        try:
            latitude, longitude, resolved = await resolve_location(name)
            resolved_reference = (float(latitude), float(longitude))
            label = address or resolved or name
        except WeatherServiceError as exc:
            raise HTTPException(status_code=422, detail="Could not resolve the starting location. Choose a valid starting city or map point.") from exc
    try:
        latitude, longitude = float(latitude), float(longitude)
        from app.services.weather import validate_coordinates
        validate_coordinates(latitude, longitude)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail="Starting location coordinates are invalid.") from exc

    from app.services import geoapify_places
    reference = geoapify_places.origin_reference(name)
    if reference is None:
        reference = resolved_reference
        if reference is None:
            try:
                ref_lat, ref_lon, _ = await resolve_location(name)
                reference = (float(ref_lat), float(ref_lon))
            except WeatherServiceError as exc:
                raise HTTPException(status_code=422, detail="Could not verify that the starting coordinates match the selected location. Re-select the location or enter a more specific city.") from exc
    if _distance_km(latitude, longitude, reference[0], reference[1]) > 75:
        raise HTTPException(status_code=422, detail="Starting coordinates do not match the selected city. Re-select the location so its name and map pin agree.")
    return latitude, longitude, label


@router.post("/discover-from-origin", response_model=schemas.OriginDiscoveryResponse)
async def discover_destinations_from_origin(req: schemas.OriginDiscoveryRequest):
    """Discover and rank destination cities from an origin, with no destination preselection."""
    origin_lat, origin_lon, origin_label = await _verified_origin_coordinates(
        req.origin_name, req.origin_latitude, req.origin_longitude, req.origin_address,
    )
    from app.services import geoapify_places

    try:
        search_categories = geoapify_places.category_values(req.travel_type)
    except geoapify_places.GeoapifyError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    # Include local getaway coverage and a bounded grid of destination hubs
    # across India. Geoapify searches places in areas; it does not discover
    # destinations or route reachability by itself.
    search_areas = [(f"selected_origin:{req.origin_name}", origin_lat, origin_lon, 100_000)]
    search_areas.extend((name, lat, lon, 60_000) for name, lat, lon in geoapify_places.DESTINATION_AREAS)
    raw_places: dict[str, dict] = {}
    failures: list[geoapify_places.GeoapifyError] = []
    places_diagnostics: dict[str, int] = {}
    successful_area_searches = 0
    semaphore = asyncio.Semaphore(5)

    async def search_area(area):
        area_name, lat, lon, radius = area
        async with semaphore:
            try:
                result = await geoapify_places.search_places(latitude=lat, longitude=lon, radius_m=radius, categories=search_categories, limit=40, diagnostics=places_diagnostics)
                if area_name.startswith("selected_origin:"):
                    logger.info("origin_discovery area=selected_origin status=success places=%d", len(result))
                else:
                    logger.info("origin_discovery area=%s center_latitude=%.5f center_longitude=%.5f status=success places=%d", area_name, lat, lon, len(result))
                return result
            except geoapify_places.GeoapifyError as exc:
                if area_name.startswith("selected_origin:"):
                    logger.warning("origin_discovery area=selected_origin status=provider_error http_status=%d", exc.status_code)
                else:
                    logger.warning("origin_discovery area=%s center_latitude=%.5f center_longitude=%.5f status=provider_error http_status=%d", area_name, lat, lon, exc.status_code)
                raise

    results = await asyncio.gather(*(search_area(area) for area in search_areas), return_exceptions=True)
    for result in results:
        if isinstance(result, geoapify_places.GeoapifyError):
            failures.append(result)
        elif isinstance(result, BaseException):
            logger.error("origin_discovery provider=geoapify unexpected search failure type=%s", type(result).__name__)
            failures.append(geoapify_places.GeoapifyError("Geoapify Places search failed unexpectedly."))
        else:
            successful_area_searches += 1
            for place in result:
                raw_places[place["place_id"]] = place
    if not raw_places and failures and successful_area_searches == 0:
        first_error = failures[0]
        logger.error("origin_discovery stage=places provider=geoapify status=provider_error search_areas=%d failed_searches=%d error_status=%d", len(search_areas), len(failures), first_error.status_code)
        raise HTTPException(status_code=first_error.status_code, detail=str(first_error))

    origin_tokens = {geoapify_places.canonical_locality(part) for part in (req.origin_name, origin_label) if part}
    clusters: dict[str, dict] = {}
    country_verified_places = [place for place in raw_places.values() if geoapify_places.is_destination_in_india(place)]
    verified_places = [place for place in country_verified_places if not _is_low_quality_destination_record(place)]
    logger.info("origin_discovery stage=quality received=%d normalized=%d deduplicated=%d country_rejected=%d low_quality_rejected=%d retained=%d failures=%d", places_diagnostics.get("received", len(raw_places)), places_diagnostics.get("normalized", len(raw_places)), places_diagnostics.get("deduplicated", len(raw_places)), places_diagnostics.get("country_rejected", max(0, len(raw_places)-len(country_verified_places))), len(country_verified_places)-len(verified_places), len(verified_places), len(failures))
    after_origin = 0
    for place in verified_places:
        city = place.get("locality")
        if not city or not place.get("country"):
            continue
        city_norm = geoapify_places.canonical_locality(city)
        country_norm = " ".join(place["country"].casefold().split())
        if city_norm in origin_tokens:
            continue
        after_origin += 1
        # Group city aliases and same-name aliases within a state together.
        region = geoapify_places.canonical_administrative_area(str(place.get("administrative_area") or ""))
        key = f"{city_norm}|{region}|{country_norm}"
        cluster = clusters.setdefault(key, {"name": geoapify_places.display_locality(city), "address": place.get("address"), "region": place.get("administrative_area"), "country": place["country"], "country_code": "IN", "latitude_values": [], "longitude_values": [], "places": [], "matched_categories": set(), "rating_values": [], "rating_count": 0})
        cluster["latitude_values"].append(place["latitude"])
        cluster["longitude_values"].append(place["longitude"])
        cluster["places"].append(place)
        cluster["matched_categories"].update(geoapify_places.matched_trip_categories(place.get("categories") or place.get("types") or []))
        if place.get("rating") is not None:
            cluster["rating_values"].append((float(place["rating"]), int(place.get("user_rating_count") or 0)))
            cluster["rating_count"] += int(place.get("user_rating_count") or 0)

    logger.info("origin_discovery stage=origin_exclusion accepted_places=%d after_origin=%d excluded=%d", len(verified_places), after_origin, len(verified_places)-after_origin)
    candidates = []
    min_km = settings.TRIP_MIN_LOCAL_GETAWAY_KM if req.short_local_getaway else settings.TRIP_MIN_DESTINATION_DISTANCE_KM
    destination_areas = {geoapify_places.canonical_locality(name) for name, _, _ in geoapify_places.DESTINATION_AREAS}
    destination_areas.update({"bengaluru", "hyderabad", "chennai", "mumbai", "kolkata", "delhi"})
    credible_place_prefixes = (
        "national_park", "natural.protected_area", "natural.mountain", "natural.water", "natural.coastal",
        "beach", "tourism.attraction", "tourism.sights", "entertainment.museum", "entertainment.zoo",
        "entertainment.aquarium", "entertainment.theme_park", "entertainment.activity_park",
        "religion.place_of_worship", "leisure.park", "natural",
    )
    single_place_destination_prefixes = (
        "national_park", "natural.protected_area", "natural.mountain", "natural.water.whitewater",
        "beach", "tourism.attraction", "tourism.sights", "entertainment.museum", "entertainment.zoo",
        "entertainment.aquarium", "entertainment.theme_park", "entertainment.activity_park",
        "religion.place_of_worship",
    )
    credible_rejected = 0
    weak_evidence_rejected = 0
    credible_survivors = 0
    for cluster in clusters.values():
        lat = sum(cluster["latitude_values"]) / len(cluster["latitude_values"])
        lon = sum(cluster["longitude_values"]) / len(cluster["longitude_values"])
        unique_evidence = {}
        seen_place_ids: set[str] = set()
        seen_name_locations: set[tuple[str, float, float]] = set()
        for place in cluster["places"]:
            place_id = str(place.get("place_id") or "")
            name_key = geoapify_places.normalized_locality(place.get("name") or "")
            identity_key = (name_key, round(float(place.get("latitude") or 0), 3), round(float(place.get("longitude") or 0), 3))
            if place_id and place_id in seen_place_ids or identity_key in seen_name_locations:
                continue
            if place_id:
                seen_place_ids.add(place_id)
            seen_name_locations.add(identity_key)
            unique_evidence[place_id or "|".join(map(str, identity_key))] = place
        evidence_names = {geoapify_places.normalized_locality(place.get("name") or "") for place in unique_evidence.values()}
        def evidence_order(place):
            place_categories = place.get("categories") or place.get("types") or []
            category_match = req.travel_type in geoapify_places.matched_trip_categories(place_categories)
            anchor_match = any(
                value == prefix or value.startswith(prefix + ".")
                for value in place_categories for prefix in single_place_destination_prefixes
            )
            specificity = max((str(value).count(".") for value in place_categories), default=0)
            return (-int(category_match), -int(anchor_match), -specificity, str(place.get("name", "")).casefold())

        ordered_evidence = sorted(unique_evidence.values(), key=evidence_order)
        strong_anchor = any(
            category == prefix or category.startswith(prefix + ".")
            for place in unique_evidence.values()
            for category in (place.get("categories") or place.get("types") or [])
            for prefix in credible_place_prefixes
        )
        single_place_anchor = next((
            place for place in ordered_evidence
            if any(
                category == prefix or category.startswith(prefix + ".")
                for category in (place.get("categories") or place.get("types") or [])
                for prefix in single_place_destination_prefixes
            )
        ), None)
        known_destination = geoapify_places.canonical_locality(cluster["name"]) in destination_areas
        # A recognized hub needs relevant category evidence. Unknown
        # localities need either multiple distinct attractions or one named,
        # strong tourist destination; a generic park/amenity is insufficient.
        if not strong_anchor or (not known_destination and len(evidence_names) < 2 and single_place_anchor is None):
            credible_rejected += 1
            continue
        credible_survivors += 1
        distance = round(_distance_km(origin_lat, origin_lon, lat, lon), 1)
        if distance < min_km:
            logger.info("origin_discovery candidate name=%s country_code=IN distance_km=%.1f budget=%.2f rejection_reason=distance_below_minimum", cluster["name"], distance, req.budget)
            continue
        ratings = [(float(place["rating"]), int(place.get("user_rating_count") or 0)) for place in unique_evidence.values() if place.get("rating") is not None]
        weighted_rating = round(sum(r * max(n,1) for r,n in ratings) / sum(max(n,1) for _,n in ratings), 1) if ratings else None
        rating_count = sum(int(place.get("user_rating_count") or 0) for place in unique_evidence.values())
        categories = sorted({category for place in unique_evidence.values() for category in geoapify_places.matched_trip_categories(place.get("categories") or place.get("types") or [])})
        # Apply weak destination evidence filter: reject small towns without strong tourist credentials
        if _is_weak_destination_evidence(len(evidence_names), set(categories), known_destination, weighted_rating, rating_count):
            logger.info("origin_discovery candidate name=%s country_code=IN distance_km=%.1f budget=%.2f rejection_reason=weak_destination_evidence place_count=%d rating=%s rating_count=%d known_destination=%s", cluster["name"], distance, req.budget, len(evidence_names), weighted_rating or "none", rating_count, known_destination)
            weak_evidence_rejected += 1
            continue
        fit_categories = [category for category in categories if category.casefold() == req.travel_type.casefold()]
        if fit_categories:
            categories = fit_categories + [c for c in categories if c not in fit_categories]
        candidate_places = list(unique_evidence.values())
        sorted_places = sorted(candidate_places, key=evidence_order)
        destination_name = cluster["name"] if known_destination or len(evidence_names) > 1 or single_place_anchor is None else single_place_anchor["name"]
        candidates.append({"destination_id": sorted_places[0]["place_id"], "name": destination_name, "description": None, "destination_highlights": [p["name"] for p in sorted_places[:4]], "address": cluster["address"], "region": cluster["region"], "country": cluster["country"], "country_code": "IN", "latitude": lat, "longitude": lon, "distance_km": distance, "estimated_travel_hours": None, "travel_time_type": "straight-line distance; live routing unavailable", "rating": None, "user_rating_count": None, "matched_categories": categories, "verified_places": [{"place_id": p["place_id"], "name": p["name"], "address": p["address"], "categories": p.get("categories") or p.get("types") or [], "rating": p["rating"], "user_rating_count": p["user_rating_count"], "google_maps_url": None, "map_url": p.get("map_url")} for p in sorted_places[:4]], "data_source": "geoapify", "evidence_count": len(evidence_names)})
    after_distance = len(candidates)
    category_candidates = [candidate for candidate in candidates if req.travel_type.casefold() in {value.casefold() for value in candidate["matched_categories"]}]
    logger.info("origin_discovery stage=distance before=%d after=%d minimum_km=%.1f local_getaways=%s", len(clusters), after_distance, min_km, req.short_local_getaway)
    logger.info("origin_discovery stage=category before=%d after=%d category=%s", after_distance, len(category_candidates), req.travel_type)
    for candidate in candidates:
        if req.travel_type.casefold() not in {value.casefold() for value in candidate["matched_categories"]}:
            logger.info("origin_discovery candidate name=%s country_code=IN distance_km=%.1f budget=%.2f rejection_reason=category_mismatch categories=%s", candidate["name"], candidate["distance_km"], req.budget, ",".join(candidate["matched_categories"]))
    budget_candidates = []
    estimate_failures = 0
    over_budget = []
    for candidate in category_candidates:
        try:
            cost = _origin_candidate_cost(candidate["distance_km"], req)
        except (ArithmeticError, TypeError, ValueError) as exc:
            estimate_failures += 1
            logger.exception("origin_discovery candidate name=%s country_code=IN budget=%.2f rejection_reason=estimate_failed error=%s", candidate["name"], req.budget, type(exc).__name__)
            continue
        candidate["costs"] = cost
        candidate["estimated_cost"] = cost["total_estimated_cost"]
        candidate["budget_remaining"] = round(req.budget - cost["total_estimated_cost"], 2)
        candidate["budget_limit"] = req.budget
        candidate["under_budget"] = True
        rejection = "within_budget" if cost["total_estimated_cost"] <= req.budget else "estimated_total_exceeds_budget"
        logger.info("origin_discovery candidate_cost name=%s country_code=IN transport=%.2f accommodation=%.2f accommodation_nights=%d food=%.2f food_travelers=%d activities=%.2f local_transport=%.2f taxes=%.2f contingency=%.2f estimated_total=%.2f budget=%.2f rejection_reason=%s estimate_source=deterministic_assumptions", candidate["name"], cost["transport_cost"], cost["hotel_cost"], cost["accommodation_nights"], cost["food_cost"], cost["food_travelers"], cost["activities_cost"], cost["local_transport_cost"], cost["taxes_fees_cost"], cost["emergency_reserve"], cost["total_estimated_cost"], req.budget, rejection)
        if rejection == "within_budget":
            budget_candidates.append(candidate)
        else:
            over_budget.append((candidate, cost))
    logger.info("origin_discovery stage=budget before=%d after=%d budget=%.2f comfort=%d", len(category_candidates), len(budget_candidates), req.budget, req.comfort_score)
    ai_batch_size = min(max(1, int(settings.TRIP_AI_RANK_BATCH_SIZE)), 20)
    ai_candidates = _select_origin_candidates_for_ai(budget_candidates, ai_batch_size)
    logger.info("origin_discovery stage=ai_batch feasible=%d selected=%d per_request_batch_size=%d", len(budget_candidates), len(ai_candidates), ai_batch_size)
    from app.services import ai_destination_ranker
    ranking_source = "ai"
    ranking_mode = "not_applicable"
    ranking_fallback_detail = None
    try:
        ranked, ranking_mode, ranking_model = await ai_destination_ranker.rank_candidates(ai_candidates, req)
        logger.info("origin_discovery stage=ranking source=ai mode=%s model=%s final=%d", ranking_mode, ranking_model, len(ranked))
    except ai_destination_ranker.AIRankingError as exc:
        ranking_source = "fallback"
        ranking_mode = "verified_evidence_fallback"
        ranking_fallback_detail = str(exc)
        ranked = ai_destination_ranker.fallback_rank_candidates(ai_candidates, req)
        logger.warning("origin_discovery stage=ranking source=fallback failure_stage=rank_request exception=%s model=%s final=%d", type(exc).__name__, getattr(ai_destination_ranker.gemini_service, "_selected_model", None) or "none", len(ranked))
    except Exception as exc:
        ranking_source = "fallback"
        ranking_mode = "verified_evidence_fallback"
        ranking_fallback_detail = f"Unexpected ranking error ({type(exc).__name__}). Check backend logs and retry."
        ranked = ai_destination_ranker.fallback_rank_candidates(ai_candidates, req)
        logger.error("origin_discovery stage=ranking source=fallback failure_stage=unexpected exception=%s model=%s final=%d", type(exc).__name__, getattr(ai_destination_ranker.gemini_service, "_selected_model", None) or "none", len(ranked))
    examined_candidate_count = len(ranked)
    shortlist_limit = min(8, max(1, int(settings.TRIP_DISCOVERY_SHORTLIST_SIZE)))
    ranked = _select_diverse_shortlist(ranked, shortlist_limit)
    logger.info("origin_discovery stage=shortlist examined=%d selected=%d configured_limit=%d", examined_candidate_count, len(ranked), shortlist_limit)
    if ranking_source == "fallback":
        for candidate in ranked:
            candidate["explanation"] = " ".join(filter(None, (candidate["why_visit"], candidate["trip_fit"], candidate["practical_note"])))
    else:
        for candidate in ranked:
            if not candidate.get("why_visit") or not candidate.get("trip_fit"):
                candidate["why_visit"], candidate["trip_fit"], candidate["practical_note"] = ai_destination_ranker._grounded_guidance(candidate, req)
    # Query Google only for the final, diversified shortlist. Ratings never
    # determine candidate eligibility or block itinerary discovery.
    from app.services import foursquare_place_ratings
    try:
        rating_issues = await foursquare_place_ratings.enrich_candidates(
            ranked,
            limit=min(len(ranked), max(0, settings.TRIP_FOURSQUARE_RATING_ENRICH_LIMIT)),
            concurrency=max(1, settings.TRIP_FOURSQUARE_RATING_CONCURRENCY),
        )
    except Exception as exc:
        logger.warning("origin_discovery stage=ratings status=optional_provider_error error_type=%s", type(exc).__name__)
        rating_issues = ["Foursquare ratings are unavailable; destinations are shown without ratings."]
    warnings = []
    if rating_issues:
        warnings.append(f"Some candidate ratings could not be loaded: {rating_issues[0]}")
    if ranking_source == "fallback":
        warnings.append(f"AI personalization is unavailable. Destinations use verified evidence and trip-fit fallback ranking; no AI match scores were assigned. {ranking_fallback_detail or 'Retry for personalized ranking.'}")
    if ranked and len(ranked) < shortlist_limit:
        warnings.append(f"Showing {len(ranked)} destination(s); only this many passed the destination, category, and budget checks.")
    if failures:
        warnings.append(f"Partial results: {len(failures)} Geoapify destination-area search(es) failed; successful area results are retained. {failures[0]}")
    if not raw_places:
        if places_diagnostics.get("country_rejected", 0):
            warnings.append("Geoapify returned candidates, but none had verifiable Indian country metadata.")
        else:
            warnings.append("Geoapify returned no matching places in the searched destination areas.")
    if raw_places and not verified_places:
        warnings.append("Geoapify returned no destinations with verified Indian country metadata.")
    elif verified_places and not after_origin:
        warnings.append("Indian destinations were found, but they were the starting city or lacked a destination-city address.")
    elif after_origin and not candidates and not credible_survivors:
        warnings.append("Geoapify returned Indian localities, but their place evidence was too limited to verify them as travel destinations. Try a broader trip category or retry later.")
    elif after_origin and not candidates:
        warnings.append("Indian destinations were found, but all were closer than the configured minimum distance. Enable nearby getaways to include destinations at the 20 km minimum.")
    elif candidates and not category_candidates:
        warnings.append(f"Indian destinations were found within the distance limit, but Geoapify category metadata did not verify a {req.travel_type} match.")
    elif category_candidates and not budget_candidates and estimate_failures:
        warnings.append("A complete cost estimate could not be produced for one or more matching destinations, so affordability could not be confirmed. Cost estimates use planning assumptions, not live fares.")
    elif category_candidates and not budget_candidates and over_budget:
        cheapest_candidate, cheapest_cost = min(over_budget, key=lambda item: item[1]["total_estimated_cost"])
        overage = cheapest_cost["total_estimated_cost"] - req.budget
        warnings.append(f"All validated planning estimates exceed the budget. Cheapest: {cheapest_candidate['name']} at an estimated ₹{cheapest_cost['total_estimated_cost']:,.0f}, which is ₹{overage:,.0f} over budget. Estimates are not live fares.")
    search_status = "partial_api_error" if failures and raw_places else ("empty_search" if not raw_places and not places_diagnostics.get("country_rejected", 0) else "all_country_filtered" if not raw_places else "candidates")
    if search_status == "candidates" and not verified_places:
        search_status = "all_country_filtered"
    elif search_status == "candidates" and not after_origin:
        search_status = "origin_filtered"
    elif search_status == "candidates" and not credible_survivors:
        search_status = "quality_filtered"
    elif search_status == "candidates" and not candidates:
        search_status = "distance_filtered"
    elif search_status == "candidates" and not category_candidates:
        search_status = "category_filtered"
    elif search_status == "candidates" and not budget_candidates:
        search_status = "budget_filtered"
    filter_counts = {"received": places_diagnostics.get("received", len(raw_places)), "normalized": places_diagnostics.get("normalized", len(raw_places)), "country_rejected": places_diagnostics.get("country_rejected", max(0, len(raw_places)-len(country_verified_places))), "verified_country": len(country_verified_places), "low_quality_records_rejected": len(country_verified_places)-len(verified_places), "after_origin": after_origin, "locality_clusters": len(clusters), "credible_candidates": credible_survivors, "low_quality_localities_rejected": credible_rejected, "weak_evidence_rejected": weak_evidence_rejected, "distance_survivors": after_distance, "category_survivors": len(category_candidates), "budget_survivors": len(budget_candidates), "ai_batch": len(ai_candidates), "ai_batch_size": ai_batch_size, "estimate_failures": estimate_failures, "ranked": examined_candidate_count, "shortlisted": len(ranked)}
    return {"origin": {"name": origin_label, "latitude": origin_lat, "longitude": origin_lon}, "candidates": ranked, "candidate_count": len(ranked), "examined_candidate_count": examined_candidate_count, "shortlist_limit": shortlist_limit, "data_source": "geoapify" if ranked else ("geoapify_empty" if successful_area_searches else "unavailable"), "partial_results": bool(failures and successful_area_searches), "warnings": warnings, "budget_feasible": bool(ranked), "estimate_label": "All costs are deterministic planning estimates, not live quotes.", "search_status": search_status, "filter_counts": filter_counts, "ranking_source": ranking_source if ranked else "not_applicable", "ranking_mode": ranking_mode if ranked else None}

import uuid

def calculate_weather_intelligence(dest, month: int = None):
    if month is None:
        month = datetime.datetime.now().month
        
    best_season_str = dest.best_season or "October to March"
    
    # 1. Check is_in_best_season
    months_map = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
    }
    s = best_season_str.lower()
    words = []
    for m in months_map.keys():
        if m in s:
            words.append((s.find(m), months_map[m]))
    words.sort()
    
    in_best = True
    if len(words) >= 2:
        start_m = words[0][1]
        end_m = words[-1][1]
        if start_m <= end_m:
            in_best = start_m <= month <= end_m
        else:
            in_best = month >= start_m or month <= end_m
    elif len(words) == 1:
        in_best = month == words[0][1]

    # 2. Determine season name
    if month in [12, 1, 2]:
        season = "Winter"
    elif month in [3, 4, 5]:
        season = "Summer"
    elif month in [6, 7, 8, 9]:
        season = "Monsoon"
    else:
        season = "Post-Monsoon"

    # 3. Determine weather details based on season & category
    cat = (dest.category or "").lower()
    
    if season == "Winter":
        if "nature" in cat or "hills" in cat or "trek" in cat:
            temp = "5°C – 15°C"
            crowd = "High"
            rain = "5% - 10%"
        else:
            temp = "18°C – 26°C"
            crowd = "High"
            rain = "0% - 5%"
    elif season == "Summer":
        if "nature" in cat or "hills" in cat or "trek" in cat:
            temp = "15°C – 22°C"
            crowd = "High"
            rain = "5% - 15%"
        else:
            temp = "32°C – 42°C"
            crowd = "Low"
            rain = "0% - 10%"
    elif season == "Monsoon":
        if "nature" in cat or "hills" in cat or "trek" in cat:
            temp = "18°C – 24°C"
            crowd = "Low"
            rain = "85% - 98%"
        else:
            temp = "26°C – 32°C"
            crowd = "Medium"
            rain = "70% - 90%"
    else: # Post-Monsoon
        temp = "22°C – 28°C"
        crowd = "Medium"
        rain = "10% - 25%"

    # 4. Rating
    if in_best:
        rating = "Excellent" if season in ["Winter", "Post-Monsoon"] else "Good"
    else:
        if season == "Monsoon" and "beach" in cat:
            rating = "Avoid"
        elif season == "Summer" and ("city" in cat or "religious" in cat or "historic" in cat):
            rating = "Fair"
        else:
            rating = "Fair"

    # 5. Recommendation
    if rating == "Excellent":
        rec = "Perfect time to visit! Enjoy best sightseeing views, clear skies, and fully open outdoor trails."
    elif rating == "Good":
        rec = "Great conditions for travel. Sightseeing and activities are fully functional. Crowd is moderate."
    elif rating == "Fair":
        if season == "Summer":
            rec = "Warm weather. Best for morning/evening sightseeing. Stay hydrated and pack light clothes."
        else:
            rec = "Moderate weather with occasional showers. Good for relaxed, budget travel."
    else: # Avoid
        rec = "Off-season. Severe rain and high beach tides. Water sports and beach shacks are closed."

    if season == "Monsoon" and rating != "Avoid":
        rec = "Excellent for lush greenery and active waterfalls. Beautiful landscapes, but carry rain protection."

    return {
        "current_season": season,
        "best_season": best_season_str,
        "season_rating": rating,
        "crowd_level": crowd,
        "temperature_range": temp,
        "rain_probability": rain,
        "recommendation": rec
    }

def calculate_carbon_footprint(transport_mode: str, transport_cost: float):
    # Determine CO2 based on mode
    # Flight: 0.14 kg CO2 per km. Cost per km average = 6.0 INR -> 0.023 kg per INR.
    # Train: 0.015 kg CO2 per km. Cost per km average = 1.5 INR -> 0.010 kg per INR.
    if transport_mode == "Flight":
        co2 = round(transport_cost * 0.042, 1)
        score = 30 if co2 >= 100 else 65
        rating = "High Impact" if co2 >= 100 else "Moderate"
        alt_savings = round(co2 * 0.90, 1)  # Train would save 90%
    else:
        co2 = round(transport_cost * 0.012, 1)
        score = 92
        rating = "Eco Friendly"
        # Flight would cost 10x
        alt_savings = round(co2 * 9.0, 1)  # Train saves X vs flight
        
    return {
        "transport_mode": transport_mode,
        "co2_emissions": co2,
        "carbon_rating": rating,
        "eco_score": score,
        "alternative_savings": alt_savings
    }

def generate_default_packing_list(category: str, season: str, duration: int, comfort: int) -> List[str]:
    items = [
        "Toothbrush & Paste",
        "Government ID Card",
        "Phone Chargers",
        "Cash & Debit Cards",
        "First-aid medical kit"
    ]
    
    # Category
    cat_lower = category.lower()
    if "beach" in cat_lower:
        items.extend(["Swimwear", "Sunscreen SPF 50+", "Beach Slippers", "Sun Hat", "Sunglasses"])
    elif "nature" in cat_lower or "adventure" in cat_lower or "trek" in cat_lower:
        items.extend(["Trekking Shoes", "Windcheater Jacket", "Reusable Water Bottle", "High Capacity Power Bank", "Hand Sanitizer"])
    elif "religious" in cat_lower or "temple" in cat_lower:
        items.extend(["Traditional Clothing", "Comfortable Slip-on Shoes", "Scarf / Shawl", "Sanitizer Wipes"])
    else: # City/Solo/Family/Others
        items.extend(["Comfortable Sneakers", "Travel Pillow", "Small Backpack"])
        
    # Season
    season_lower = season.lower()
    if "monsoon" in season_lower:
        items.extend(["Umbrella", "Waterproof Bag Cover", "Ziplock bags for electronics"])
    elif "winter" in season_lower:
        items.extend(["Heavy Warm Sweater", "Thermals", "Lip Balm & Cold Cream"])
    elif "summer" in season_lower:
        items.extend(["Light Cotton T-shirts", "Sunglasses", "Cap / Visor", "Deodorant"])
        
    # Duration
    if duration >= 5:
        items.extend(["Laundry Bag", "Extra pair of socks", "Travel-size detergent"])
        
    # Comfort Level
    if comfort < 30:
        items.extend(["Quick-dry Travel Towel", "Waterproof pouch", "Sleeping sheet liner"])
    elif comfort > 75:
        items.extend(["Eye sleeping mask", "Noise-cancelling headphones"])
        
    # Unique items
    return list(dict.fromkeys(items))

def get_region(text: str) -> str:
    t = text.lower().strip()
    
    north = ["delhi", "gurgaon", "noida", "chandigarh", "amritsar", "srinagar", "jaipur", "dehradun", "lucknow", "punjab", "haryana", "uttarakhand", "himachal", "jammu", "kashmir", "uttar pradesh", "rajasthan", "ladakh", "shimla", "manali", "rishikesh", "auli", "spiti", "kedarnath", "haridwar", "nainital"]
    south = ["bangalore", "bengaluru", "chennai", "hyderabad", "kochi", "madurai", "tirupati", "coimbatore", "karnataka", "kerala", "tamil nadu", "andhra", "telangana", "pondicherry", "munnar", "coorg", "ooty", "wayanad", "alleppey", "kodaikanal", "araku", "kovalam", "varkala", "rameshwaram"]
    west = ["mumbai", "pune", "ahmedabad", "goa", "alibaug", "maharashtra", "gujarat", "daman", "shirdi", "gokarna", "mount abu"]
    east = ["kolkata", "darjeeling", "puri", "bhubaneswar", "guwahati", "west bengal", "odisha", "sikkim", "arunachal", "andaman", "nicobar", "tawang", "yumthang", "havelock"]
    
    for item in north:
        if item in t:
            return "North"
    for item in south:
        if item in t:
            return "South"
    for item in west:
        if item in t:
            return "West"
    for item in east:
        if item in t:
            return "East"
            
    return "Unknown"

def calculate_costs(dest: models.Destination, days: int, travelers: int, comfort_score: int, starting_city: str = ""):
    # 1. Transport Mode & Cost (influenced by starting city region)
    start_region = get_region(starting_city)
    dest_region = get_region(dest.state)

    # Expanded regional multiplier matrix — geographically calibrated haul distances.
    # Multiplier is applied to the base cost BEFORE flooring so cheap destinations
    # still reflect regional distance differences.
    multiplier = 1.0
    if start_region != "Unknown" and dest_region != "Unknown":
        if start_region == dest_region:
            multiplier = 0.45   # same region — short haul, heavy discount
        else:
            # Long haul: North↔South (Delhi↔Chennai ~2200km), East↔West (Kolkata↔Mumbai ~2000km)
            long_haul = (
                {start_region, dest_region} == {"North", "South"} or
                {start_region, dest_region} == {"East", "West"}
            )
            # Medium-long: North↔West (Delhi↔Goa ~1900km), North↔East (Delhi↔Kolkata ~1500km)
            medium_long = (
                {start_region, dest_region} == {"North", "West"} or
                {start_region, dest_region} == {"North", "East"}
            )
            # Medium: South↔West (Chennai↔Goa ~1000km), South↔East (Chennai↔Kolkata ~1700km)
            medium = (
                {start_region, dest_region} == {"South", "West"} or
                {start_region, dest_region} == {"South", "East"}
            )
            if long_haul:
                multiplier = 1.45   # Delhi↔Chennai, Kolkata↔Goa — farthest routes
            elif medium_long:
                multiplier = 1.25   # Delhi↔Goa, Delhi↔Kolkata
            elif medium:
                multiplier = 1.05   # Chennai↔Goa, Chennai↔Kolkata — shorter routes
            else:
                multiplier = 1.0    # fallback for any unmatched pair

    comfort_factors = _comfort_cost_factors(comfort_score)
    # Keep mode and cost independent of arbitrary comfort thresholds. Destination
    # average travel cost remains the anchor; the continuous factor is applied once.
    transport_mode = "Comfort-adjusted intercity estimate"
    transport_cost = max(600.0, dest.avg_travel_cost * multiplier) * travelers * comfort_factors["transport"]

    # 2. Hotel Tier & Cost
    hotel_tier = "Comfort-adjusted"
    hotel_cost_per_night = dest.avg_hotel_cost * comfort_factors["lodging"]
    hotel_cost = hotel_cost_per_night * max(days - 1, 0) * travelers

    # 3. Food Cost
    food_factor = comfort_factors["food"]
    food_cost = dest.avg_food_cost * days * travelers * food_factor

    # 4. Activities Cost
    activities_per_day = 2
    activity_factor = comfort_factors["activities"]
    activities_cost = dest.avg_activity_cost * travelers * max(days - 1, 0) * activities_per_day * activity_factor

    # 5. Local Transport Cost
    local_transport_cost = 400.0 * days * travelers * comfort_factors["local_transport"]

    # 6. Taxes & Fees (12% of subtotal parts)
    taxes_fees_cost = (transport_cost + hotel_cost + activities_cost) * 0.12

    # Subtotal
    subtotal = transport_cost + hotel_cost + food_cost + activities_cost + local_transport_cost + taxes_fees_cost

    # Emergency Reserve (8% of subtotal)
    emergency_reserve = subtotal * 0.08

    total_cost = subtotal + emergency_reserve

    return {
        "transport_mode": transport_mode,
        "hotel_tier": hotel_tier,
        "transport_cost": round(transport_cost, 2),
        "hotel_cost": round(hotel_cost, 2),
        "food_cost": round(food_cost, 2),
        "activities_cost": round(activities_cost, 2),
        "local_transport_cost": round(local_transport_cost, 2),
        "taxes_fees_cost": round(taxes_fees_cost, 2),
        "emergency_reserve": round(emergency_reserve, 2),
        "total_estimated_cost": round(total_cost, 2),
        "accommodation_nights": max(days - 1, 0),
    }

def calculate_score_breakdown(
    dest: models.Destination,
    costs: dict,
    budget: float,
    days: int,
    travel_type: str,
    comfort_score: int
) -> dict:
    # 1. Budget Fit (35%) — still the primary driver but comfort gets more room
    total_cost = costs["total_estimated_cost"]
    diff = abs(budget - total_cost) / budget
    if total_cost <= budget:
        budget_fit = 1.0 - diff  # closer to budget limit means higher resource utilisation
    else:
        budget_fit = max(0.0, 1.0 - diff * 4.0)  # heavy penalty if over budget

    # 2. Category Match (25%) — unchanged
    main_match = 1.0 if dest.category.lower() == travel_type.lower() else 0.0
    sub_score = 0.0
    t_type = travel_type.lower()
    if "nature" in t_type:
        sub_score = getattr(dest, "nature_score", 0.0) or 0.0
    elif "adventure" in t_type:
        sub_score = getattr(dest, "adventure_score", 0.0) or 0.0
    elif "family" in t_type:
        sub_score = getattr(dest, "family_score", 0.0) or 0.0
    elif "romantic" in t_type:
        sub_score = getattr(dest, "romantic_score", 0.0) or 0.0
    elif "religious" in t_type:
        sub_score = getattr(dest, "religious_score", 0.0) or 0.0
    elif "beach" in t_type:
        sub_score = getattr(dest, "beach_score", 0.0) or 0.0
    elif "city" in t_type:
        sub_score = getattr(dest, "city_score", 0.0) or 0.0
    elif "solo" in t_type:
        sub_score = getattr(dest, "solo_score", 0.0) or 0.0

    cat_match = 0.6 * main_match + 0.4 * (sub_score / 100.0)

    # 3. Rating Match (12%) — slightly reduced to make room for comfort
    rating_match = (dest.rating or 4.0) / 5.0

    # 4. Comfort Match (20%) — doubled from 10% so slider meaningfully reorders results.
    # A destination whose comfort_level is far from the user's comfort_score is penalised.
    comfort_match = 1.0 - abs(comfort_score - (dest.comfort_level or 50)) / 100.0

    # 5. Duration Suitability (8%) — minor factor
    rec_dur = dest.recommended_duration or 4
    duration_suitability = max(0.0, 1.0 - abs(days - rec_dur) / 5.0)

    # Weights: 35 + 25 + 12 + 20 + 8 = 100%
    weighted_score = (
        0.35 * budget_fit +
        0.25 * cat_match +
        0.12 * rating_match +
        0.20 * comfort_match +
        0.08 * duration_suitability
    ) * 100.0
    
    # Generate explanations
    # Each explanation includes the actual computed score so every destination
    # produces a different, specific explanation rather than generic template text.
    explanations = []

    # 1. Budget fit explanation
    budget_fit_pct = round(budget_fit * 100, 1)
    estimated_cost = costs["total_estimated_cost"]
    savings_amt = round(budget - estimated_cost, 0)
    if budget_fit >= 0.90:
        explanations.append(
            f"Excellent budget fit ({budget_fit_pct}%) — estimated cost ₹{estimated_cost:,.0f} leaves ₹{savings_amt:,.0f} unspent."
        )
    elif budget_fit >= 0.75:
        explanations.append(
            f"Good budget fit ({budget_fit_pct}%) — estimated ₹{estimated_cost:,.0f} uses most of your ₹{budget:,.0f} budget efficiently."
        )
    elif budget_fit >= 0.50:
        explanations.append(
            f"Moderate budget fit ({budget_fit_pct}%) — estimated ₹{estimated_cost:,.0f} is close to your ₹{budget:,.0f} budget limit."
        )
    else:
        explanations.append(
            f"Low budget fit ({budget_fit_pct}%) — estimated ₹{estimated_cost:,.0f} against ₹{budget:,.0f} budget. Consider adjusting days or comfort."
        )

    # 2. Travel type / category match explanation
    type_pct = round(cat_match * 100, 1)
    dest_cat = dest.category
    if cat_match >= 0.80:
        explanations.append(
            f"Strong {travel_type} match ({type_pct}%) — {dest.name} is categorised as {dest_cat} and scores highly for your travel style."
        )
    elif cat_match >= 0.55:
        explanations.append(
            f"Good {travel_type} alignment ({type_pct}%) — {dest.name} is a {dest_cat} destination with relevant attractions for your style."
        )
    else:
        explanations.append(
            f"Partial {travel_type} match ({type_pct}%) — {dest.name} is primarily a {dest_cat} destination but has activities that suit your interests."
        )

    # 3. Comfort match explanation
    comfort_match_pct = round(comfort_match * 100, 1)
    dest_comfort = dest.comfort_level or 50
    gap = abs(comfort_score - dest_comfort)
    if comfort_match >= 0.90:
        explanations.append(
            f"Comfort alignment is excellent ({comfort_match_pct}%) — your comfort preference ({comfort_score}/100) closely matches this destination's standard ({dest_comfort}/100)."
        )
    elif comfort_match >= 0.75:
        explanations.append(
            f"Good comfort match ({comfort_match_pct}%) — your preference ({comfort_score}/100) is {gap} points from the destination comfort level ({dest_comfort}/100)."
        )
    else:
        explanations.append(
            f"Comfort mismatch ({comfort_match_pct}%) — your preference is {comfort_score}/100 but this destination is rated {dest_comfort}/100. Adjust comfort score for better fits."
        )

    # 4. Rating explanation
    rating_val = dest.rating or 4.0
    if rating_val >= 4.5:
        explanations.append(
            f"Top-rated destination — {dest.name} holds a {rating_val}/5.0 visitor rating, placing it in the top tier of all destinations."
        )
    elif rating_val >= 4.0:
        explanations.append(
            f"Highly rated — {dest.name} has a strong {rating_val}/5.0 visitor rating based on traveler feedback."
        )
    else:
        explanations.append(
            f"Moderately rated — {dest.name} has a {rating_val}/5.0 visitor rating. Fewer reviews or a niche appeal destination."
        )

    # 5. Duration suitability explanation
    dur_pct = round(duration_suitability * 100, 1)
    if duration_suitability >= 0.90:
        explanations.append(
            f"Ideal trip length — your {days}-day plan perfectly matches the recommended {rec_dur}-day itinerary for {dest.name} ({dur_pct}% suitability)."
        )
    elif days < rec_dur:
        explanations.append(
            f"Short trip alert ({dur_pct}%) — {dest.name} is best explored in {rec_dur} days; your {days}-day plan may miss some key attractions."
        )
    else:
        explanations.append(
            f"Extended stay ({dur_pct}%) — {dest.name} is ideally visited in {rec_dur} days; your {days}-day plan gives extra relaxation time."
        )

    return {
        "value_score": round(weighted_score, 2),
        "budget_compatibility": round(budget_fit * 100, 1),
        "trip_type_match": round(cat_match * 100, 1),
        "comfort_match": round(comfort_match * 100, 1),
        "destination_rating": round(rating_match * 100, 1),
        "duration_suitability": round(duration_suitability * 100, 1),
        "explanations": explanations
    }

def calculate_weighted_score(
    dest: models.Destination,
    costs: dict,
    budget: float,
    days: int,
    travel_type: str,
    comfort_score: int
) -> float:
    breakdown = calculate_score_breakdown(dest, costs, budget, days, travel_type, comfort_score)
    return breakdown["value_score"]


def generate_itinerary_days(dest: models.Destination, days: int, comfort_score: int, travel_type: str = "", weather_context=None, verified_places=None):
    # --- Try AI service first ---
    attractions = dest.attractions if isinstance(dest.attractions, list) and len(dest.attractions) > 0 else []
    if not attractions:
        attractions = [f"{dest.name} Town Center", "Scenic Viewpoint", "Local Market", "Historical Landmark", "Cultural Center"]

    ai_result = gemini_service.generate_itinerary(
        destination_name=dest.name,
        state=dest.state,
        category=dest.category,
        attractions=attractions,
        travel_type=travel_type or dest.category,
        days=days,
        comfort_score=comfort_score,
        avg_food_cost=dest.avg_food_cost,
        avg_activity_cost=dest.avg_activity_cost,
        weather_context=weather_context,
        verified_places=verified_places,
    )
    if ai_result is not None and len(ai_result) >= days:
        return ai_result[:days]

    # --- Rich & Dynamic Fallback Itinerary Generator ---
    cat_lower = (travel_type or dest.category or "").lower()
    
    templates_by_category = {
        "nature": {
            "Morning": [
                "Early morning sunrise trek & nature trail walk at {attraction}",
                "Morning birdwatching & landscape photography session near {attraction}",
                "Scenic mountain valley walk & pine forest exploration at {attraction}",
                "Fresh morning air walk & flora sanctuary tour near {attraction}"
            ],
            "Afternoon": [
                "Authentic regional lunch & forest trail exploration near {attraction}",
                "Lakeside picnic, boat ride & leisure walk at {attraction}",
                "Alpine meadow walk & mountain stream viewpoint at {attraction}",
                "Visiting eco-park & local tea gardens near {attraction}"
            ],
            "Evening": [
                "Golden hour sunset photography at {attraction}",
                "Cozy evening walk through local hill bazaar & herbal tea tasting",
                "Sunset viewpoint relaxation & twilight valley panorama at {attraction}",
                "Evening bonfire gathering & stargazing experience"
            ]
        },
        "beach": {
            "Morning": [
                "Sunrise coastal walk & morning beach leisure at {attraction}",
                "Water sports (banana boat / jet ski) & beach volleyball at {attraction}",
                "Coastal morning boat ride & marine life spotting near {attraction}",
                "Early morning sea breeze walk & cliffside view at {attraction}"
            ],
            "Afternoon": [
                "Fresh seafood lunch at beach shacks & shaded relaxation at {attraction}",
                "Exploring historic coastal fort & maritime museum near {attraction}",
                "Beach hammock leisure, fresh coconut sampling & swimming at {attraction}",
                "Coastal village walk & local shell handicrafts browsing near {attraction}"
            ],
            "Evening": [
                "Sunset view at {attraction} beach with acoustic music",
                "Evening beachside promenade walk & night market street food sampling",
                "Seaside diner dinner under string lights with ocean wave soundscape",
                "Sunset beach walk & local souvenir shopping at seaside stalls"
            ]
        },
        "adventure": {
            "Morning": [
                "Thrilling adventure sport (ziplining/river rafting) at {attraction}",
                "Early morning hill trek & ridge trail navigation to {attraction}",
                "Rock climbing & outdoor wilderness adventure activity near {attraction}",
                "High-rope obstacle course & canopy walk at {attraction}"
            ],
            "Afternoon": [
                "Outdoor camp lunch & wilderness navigation near {attraction}",
                "Off-road ATV trail ride / mountain biking near {attraction}",
                "River crossing activity & waterfall trail exploration at {attraction}",
                "Guided canyon exploration & valley photo tour near {attraction}"
            ],
            "Evening": [
                "Sunset ridge view & campfire gathering with fellow travelers",
                "Evening rustic BBQ dinner & outdoor storytelling at adventure camp",
                "Stargazing & night trail walk around camping ridge near {attraction}",
                "Leisurely evening walk through local adventure hub bazaar"
            ]
        },
        "religious": {
            "Morning": [
                "Morning spiritual prayer, temple architecture tour & darshan at {attraction}",
                "Sacred river ghat sunrise walk & peaceful morning chanting near {attraction}",
                "Guided heritage pilgrimage walk & ancient temple history tour at {attraction}",
                "Morning meditation session & spiritual heritage walk near {attraction}"
            ],
            "Afternoon": [
                "Traditional satvik / regional thali lunch at heritage eatery near {attraction}",
                "Visiting sacred ashram gardens & spiritual library near {attraction}",
                "Exploring ancient stone carvings & holy water tanks at {attraction}",
                "Visiting local religious handicraft stalls & brassware bazaars"
            ],
            "Evening": [
                "Mesmerizing evening Aarti ceremony & lamp offering at {attraction}",
                "Sunset spiritual stroll along sacred riverbanks / temple square",
                "Peaceful evening bhajan performance & Prasad distribution",
                "Evening bazaar walk sampling traditional sweets & devotional goods"
            ]
        },
        "cultural": {
            "Morning": [
                "Guided heritage walking tour & architectural study at {attraction}",
                "Visiting royal palace corridors & museum galleries at {attraction}",
                "Morning artisan workshop tour & traditional handicraft study near {attraction}",
                "Exploring ancient fort ramparts & panoramic city view at {attraction}"
            ],
            "Afternoon": [
                "Authentic royal heritage thali lunch & local spice market tour",
                "Visiting textile museum & artisan weaver village near {attraction}",
                "Exploring historic Haveli courtyards & folk art galleries at {attraction}",
                "Visiting heritage monument complex & guided history lecture at {attraction}"
            ],
            "Evening": [
                "Vibrant traditional folk dance & puppet show performance at {attraction}",
                "Evening night market stroll sampling regional street food & spices",
                "Heritage rooftop dinner overlooking illuminated palace / fort",
                "Sunset view from historic bastion & handicraft souvenir browsing"
            ]
        }
    }

    default_templates = {
        "Morning": [
            "Guided morning sightseeing walk & landmark tour at {attraction}",
            "Morning photo walk & exploring city gardens near {attraction}",
            "Breakfast at iconic local eatery & historic square visit at {attraction}",
            "Morning panorama viewpoint & scenic heritage walk at {attraction}"
        ],
        "Afternoon": [
            "Regional specialty lunch & local museum gallery tour near {attraction}",
            "Shopping for local specialties & artisan bazaars near {attraction}",
            "Exploring historic corridors & cultural exhibits at {attraction}",
            "Relaxed afternoon park stroll & café coffee break near {attraction}"
        ],
        "Evening": [
            "Sunset viewpoint walk & twilight photo session at {attraction}",
            "Evening night market street food walk & souvenir shopping",
            "Leisurely dinner at popular local restaurant featuring live music",
            "Evening promenade stroll & illuminated city landmark view at {attraction}"
        ]
    }

    matched_pool = default_templates
    for key, pool in templates_by_category.items():
        if key in cat_lower:
            matched_pool = pool
            break

    itineraries = []
    attr_count = len(attractions)
    used_titles = set()

    for day in range(1, days + 1):
        day_activities = []
        if day == 1:
            day_activities.append({
                "time": "Morning",
                "title": f"Arrival in {dest.name}, hotel check-in & welcome drink",
                "cost": 0.0
            })
            day_activities.append({
                "time": "Afternoon",
                "title": f"Settle in & introductory lunch at local diner in {dest.name}",
                "cost": round(dest.avg_food_cost * 0.4, 2)
            })
            attr_first = attractions[0]
            day_activities.append({
                "time": "Evening",
                "title": f"Gentle orientation stroll & sunset view at {attr_first}",
                "cost": 0.0
            })
            description = f"Welcome to {dest.name}! Check in to your lodging, unpack, and enjoy a relaxed orientation walk."
        elif day == days:
            day_activities.append({
                "time": "Morning",
                "title": f"Early morning photo walk & souvenir shopping at local {dest.name} bazaars",
                "cost": round(dest.avg_activity_cost * 0.5, 2)
            })
            day_activities.append({
                "time": "Afternoon",
                "title": f"Pack bags, hotel check-out & farewell regional lunch",
                "cost": round(dest.avg_food_cost * 0.4, 2)
            })
            day_activities.append({
                "time": "Evening",
                "title": f"Transfer to transit hub & departure back home from {dest.name}",
                "cost": 0.0
            })
            description = f"Final day in {dest.name}. Pick up authentic local souvenirs, check out, and head home with fond memories."
        else:
            activities_per_day = 2
            times = ["Morning", "Afternoon", "Evening"]

            for i in range(activities_per_day):
                time_slot = times[i % 3]
                attr_idx = ((day - 2) * 3 + i) % attr_count
                attr_name = attractions[attr_idx]

                slot_templates = matched_pool.get(time_slot, default_templates[time_slot])
                template_str = slot_templates[(day + i) % len(slot_templates)]
                title = template_str.format(attraction=attr_name)

                retry_count = 0
                while title in used_titles and retry_count < 5:
                    retry_count += 1
                    alt_attr = attractions[(attr_idx + retry_count) % attr_count]
                    alt_template = slot_templates[(day + i + retry_count) % len(slot_templates)]
                    title = alt_template.format(attraction=alt_attr)

                used_titles.add(title)

                comfort_factor = _comfort_cost_factors(comfort_score)["activities"]
                act_cost = round(dest.avg_activity_cost * comfort_factor, 2)

                day_activities.append({
                    "time": time_slot,
                    "title": title,
                    "cost": act_cost
                })

            day_themes = [
                f"Discovering the famous landmarks and hidden gems of {dest.name}.",
                f"Immersing in the local culture, cuisine, and scenery of {dest.name}.",
                f"A full day of exploration, photography, and regional flavors around {dest.name}.",
                f"Uncovering historical heritage and scenic landscapes in {dest.name}."
            ]
            description = day_themes[(day - 2) % len(day_themes)]

        itineraries.append({
            "day_number": day,
            "activities": day_activities,
            "description": description
        })

    return itineraries


@router.post("/discover")
async def discover_trip_places(payload: dict, db: Session = Depends(get_db)):
    name = str(payload.get("destination_name", "")).strip()
    if len(name) < 2:
        raise HTTPException(status_code=422, detail="Choose a destination before searching for places.")
    lat, lon = payload.get("latitude"), payload.get("longitude")
    from app.services.geoapify_places import GeoapifyError
    try:
        if lat is None or lon is None:
            lat, lon, resolved_name = await resolve_location(name)
            name = name if not resolved_name else name
        lat, lon = float(lat), float(lon)
        if str(payload.get("destination_country_code") or "").strip().upper() == "IN":
            places, failures = await _discover_geoapify_destination_places(name, str(payload.get("travel_type", "Nature")), lat, lon)
            provider = "geoapify"
        else:
            places, failures = await _discover_live_places(name, payload.get("interests", []), payload.get("cuisine_preferences", []), str(payload.get("travel_type", "")), lat, lon)
            provider = "google_places"
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail="Destination coordinates are invalid.") from exc
    except WeatherServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except GeoapifyError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    result = {"destination": {"name": name, "address": payload.get("destination_address"), "latitude": lat, "longitude": lon}, "places": places, "data_source": provider if places else ("unavailable" if failures else f"{provider}_empty"), "fallback_used": False, "weather": None, "weather_data_source": "unavailable", "errors": []}
    if failures:
        result["errors"].append(f"Some {provider} searches failed; successful results are retained.")
    try:
        result["weather"] = await get_forecast(lat, lon, min(max(int(payload.get("days", 7)), 1), 16), name)
        result["weather_data_source"] = "open_meteo"
    except (WeatherServiceError, ValueError) as exc:
        result["errors"].append(str(exc))
    # A legitimate empty search is not an API failure and never triggers database fallback.
    if not places and failures and provider == "google_places":
        existing = db.query(models.Destination).filter(models.Destination.name.ilike(f"%{name}%")).first()
        if existing:
            result["places"] = [{"place_id": None, "name": item, "address": None, "latitude": None, "longitude": None, "rating": None, "user_rating_count": None, "price_level": None, "data_source": "database_fallback"} for item in (existing.attractions or [])]
            result["data_source"] = "database_fallback"
            result["fallback_used"] = True
            result["fallback_notice"] = "Google Places was unavailable. These attractions come from older BudgetBound destination data."
        else:
            result["data_source"] = "unavailable"
    return result


async def generate_dynamic_trip_plan(req: schemas.TripPlanRequest, db: Session):
    if req.destination_country_code and req.destination_country_code.strip().upper() != "IN":
        raise HTTPException(status_code=422, detail="The selected destination is outside the supported country list.")
    if req.destination_country_code and req.destination_country_code.strip().upper() == "IN":
        from app.services.geoapify_places import GeoapifyError
        try:
            places, failures = await _discover_geoapify_destination_places(req.destination_name or "", req.travel_type, float(req.latitude), float(req.longitude))
        except GeoapifyError as exc:
            raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
        source = "geoapify"
    else:
        places, failures = await _discover_live_places(req.destination_name or "", req.interests, req.cuisine_preferences, req.travel_type, req.latitude, req.longitude, req.destination_country_code)
        source = "google_places"
    fallback = False
    destination_db = None
    if not places and failures and not req.destination_country_code:
        destination_db = db.query(models.Destination).filter(models.Destination.name.ilike(f"%{req.destination_name}%")).first()
        if destination_db:
            fallback = True
            source = "database_fallback"
            places = [{"place_id": None, "name": name, "address": None, "latitude": None, "longitude": None, "rating": None, "user_rating_count": None, "price_level": None, "data_source": "database_fallback"} for name in (destination_db.attractions or [])]
    if not places:
        if req.destination_country_code:
            raise HTTPException(status_code=503 if failures else 404, detail=("Geoapify Places is unavailable; no Google or database fallback was used for this verified Indian destination." if failures else "Geoapify returned no verified Indian attractions for this destination."))
        raise HTTPException(status_code=503 if failures else 404, detail=("Google Places is unavailable and no matching database fallback exists." if failures else "No places matched these preferences. Try a broader search."))
    if fallback and destination_db:
        dest = destination_db
        cost_factors = calculate_costs(dest, req.days, req.travelers_count, req.comfort_score, req.starting_city)
        cost_factors["estimate_label"] = "Database fallback estimate; not a live quote"
    elif req.destination_country_code and req.destination_country_code.strip().upper() == "IN":
        origin_lat, origin_lon, _ = await _verified_origin_coordinates(
            req.starting_city, req.origin_latitude, req.origin_longitude,
        )
        try:
            from app.services.weather import validate_coordinates
            validate_coordinates(float(origin_lat), float(origin_lon))
            validate_coordinates(float(req.latitude), float(req.longitude))
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=422, detail="Starting or destination coordinates are invalid.") from exc
        trip_distance = round(_distance_km(float(origin_lat), float(origin_lon), float(req.latitude), float(req.longitude)), 1)
        cost_factors = _origin_candidate_cost(trip_distance, req)
        if cost_factors["total_estimated_cost"] > req.budget:
            raise HTTPException(status_code=422, detail=f"Estimated trip cost ₹{cost_factors['total_estimated_cost']:,.0f} exceeds your maximum budget ₹{req.budget:,.0f}. Adjust the budget or trip details.")
        from types import SimpleNamespace
        dest = SimpleNamespace(name=req.destination_name, state=req.destination_address or "", category=req.travel_type, attractions=[p["name"] for p in places], avg_food_cost=cost_factors["food_cost"] / max(req.days * req.travelers_count, 1), avg_activity_cost=cost_factors["activities_cost"] / max(req.days * req.travelers_count, 1), best_season="Not assessed", description="Geoapify destination data", rating=0.0)
    else:
        # Transparent configurable estimate ratios; independent of seeded destination prices.
        nightly = float(__import__("os").getenv("TRIP_ESTIMATE_LODGING_PER_PERSON_NIGHT", "1800"))
        food_daily = float(__import__("os").getenv("TRIP_ESTIMATE_FOOD_PER_PERSON_DAY", "900"))
        transport = float(__import__("os").getenv("TRIP_ESTIMATE_TRANSPORT_PER_PERSON", "3500"))
        activities = float(__import__("os").getenv("TRIP_ESTIMATE_ACTIVITIES_PER_PERSON_DAY", "500"))
        lodging_total, food_total = nightly * req.days * req.travelers_count, food_daily * req.days * req.travelers_count
        activity_total = activities * req.days * req.travelers_count
        local = 250 * req.days * req.travelers_count
        reserve = req.budget * 0.08
        total = round(lodging_total + food_total + activity_total + transport * req.travelers_count + local + reserve, 2)
        cost_factors = {"transport_mode": "Estimated transport", "hotel_tier": "Estimated lodging", "transport_cost": transport * req.travelers_count, "hotel_cost": lodging_total, "food_cost": food_total, "activities_cost": activity_total, "local_transport_cost": local, "taxes_fees_cost": 0.0, "emergency_reserve": reserve, "total_estimated_cost": total, "estimate_label": "Configurable planning estimate; not a live market quote"}
        if total > req.budget:
            raise HTTPException(status_code=422, detail=f"Estimated trip cost ₹{total:,.0f} exceeds your maximum budget ₹{req.budget:,.0f}. Adjust the budget or trip details.")
        from types import SimpleNamespace
        dest = SimpleNamespace(name=req.destination_name, state=req.destination_address or "", category=req.travel_type, attractions=[p["name"] for p in places], avg_food_cost=food_daily, avg_activity_cost=activities, best_season="Not assessed", description="Live Google Places destination", rating=0.0)
    try:
        forecast = await get_forecast(req.latitude, req.longitude, min(req.days, 16), req.destination_name)
        weather_context = {"timezone": forecast.get("timezone"), "daily": forecast.get("daily")}
    except (WeatherServiceError, ValueError):
        weather_context = None
    attractions = [p["name"] for p in places if p.get("data_source") == source]
    if not attractions:
        attractions = [p["name"] for p in places]
    itineraries = gemini_service.generate_itinerary(
        destination_name=dest.name, state=dest.state, category=dest.category, attractions=attractions,
        travel_type=req.travel_type, days=req.days, comfort_score=req.comfort_score,
        avg_food_cost=cost_factors["food_cost"] / max(req.days * req.travelers_count, 1),
        avg_activity_cost=cost_factors["activities_cost"] / max(req.days * req.travelers_count, 1),
        weather_context=weather_context, verified_places=places,
        budget_limit=req.budget, travelers_count=req.travelers_count,
        user_preferences=[*req.interests, *req.cuisine_preferences, *([req.accessibility] if req.accessibility else [])],
    )
    
    itinerary_source = "groq"
    
    # If Groq fails, generate deterministic fallback itinerary
    if not itineraries or len(itineraries) != req.days:
        logger.warning("Groq itinerary unavailable/incomplete status=%s provider_error=%s model=%s finish_reason=%s expected_days=%d actual_days=%s; using fallback", gemini_service._last_http_status, gemini_service._last_provider_error, gemini_service._selected_model, gemini_service._last_finish_reason, req.days, len(itineraries) if itineraries else 0)
        # Generate deterministic fallback itinerary
        itineraries = generate_itinerary_days(dest, req.days, req.comfort_score, req.travel_type, weather_context, places)
        itinerary_source = "fallback_deterministic"
        
        if not itineraries or len(itineraries) != req.days:
            # Should not happen, but fail safely
            logger.error("Fallback itinerary generation failed expected_days=%d actual_days=%s", req.days, len(itineraries) if itineraries else 0)
            raise HTTPException(status_code=503, detail="Itinerary generation failed. Try again in a few moments.")
    
    try:
        validated_days = [schemas.ItineraryBase.model_validate(day).model_dump() for day in itineraries]
        if [day["day_number"] for day in validated_days] != list(range(1, req.days + 1)):
            raise ValueError("Itinerary day sequence is invalid")
        itineraries = validated_days
    except Exception as exc:
        logger.error("Itinerary schema validation failed status=%s provider_error=%s model=%s source=%s validation_failure=%s", gemini_service._last_http_status, gemini_service._last_provider_error, gemini_service._selected_model, itinerary_source, exc)
        raise HTTPException(status_code=502, detail="The generated itinerary was incomplete or malformed. Please retry.") from exc
    # Keep only supplied places as sightseeing activities, while permitting logistics and meals.
    itineraries = _keep_verified_itinerary_activities(itineraries, places)
    planned_activities = [a for day in itineraries for a in day.get("activities", []) if a.get("place_id")]
    activity_pool = float(cost_factors["activities_cost"])
    if planned_activities:
        per_item = round(activity_pool / len(planned_activities), 2)
        assigned = 0.0
        for index, activity in enumerate(planned_activities):
            amount = round(activity_pool - assigned, 2) if index == len(planned_activities) - 1 else per_item
            activity["cost"] = amount
            activity["cost_type"] = "estimate"
            assigned += amount
    for day in itineraries:
        for activity in day.get("activities", []):
            if not activity.get("place_id"):
                activity["cost"] = 0.0
                activity["cost_type"] = "not_priced"
    
    # Add weather intelligence for discovered destinations
    weather_intelligence = calculate_weather_intelligence(dest, None)
    
    return {"destination": {"id": destination_db.id if destination_db else None, "name": dest.name, "state": dest.state, "description": dest.description, "rating": dest.rating or 0, "category": dest.category, "best_season": dest.best_season, "attractions": attractions, "latitude": req.latitude, "longitude": req.longitude, "address": req.destination_address, "google_place_id": req.google_place_id, "geoapify_place_id": req.geoapify_place_id, "country_code": req.destination_country_code, "places": places, "data_source": source, "fallback_used": fallback, "weather_intelligence": weather_intelligence}, "costs": cost_factors, "savings": round(req.budget-cost_factors["total_estimated_cost"],2), "value_score": 0, "under_budget": cost_factors["total_estimated_cost"] <= req.budget, "itineraries": itineraries, "itinerary_source": itinerary_source, "budget": req.budget, "days": req.days, "travelers_count": req.travelers_count, "comfort_score": req.comfort_score, "travel_type": req.travel_type, "data_source": source, "weather_data_source": "open_meteo" if weather_context else "unavailable", "weather_personalization_available": bool(weather_context), "breakdown": {"budget_compatibility": 85, "trip_type_match": 90, "comfort_match": 80, "destination_rating": 75, "duration_suitability": 85, "explanations": ["Destination matches your budget and travel preferences based on verified evidence and trip fit analysis."]}, "carbon_footprint": calculate_carbon_footprint(cost_factors.get("transport_mode", "Estimated transport"), cost_factors.get("transport_cost", 0))}

@router.post("/plan")
async def generate_trip_plan(req: schemas.TripPlanRequest, db: Session = Depends(get_db)):
    if req.destination_name and req.latitude is not None and req.longitude is not None:
        return await generate_dynamic_trip_plan(req, db)
    # Fetch either the selected destination or the full catalog to rank dynamically
    query = db.query(models.Destination)
    if req.destination_id is not None:
        query = query.filter(models.Destination.id == req.destination_id)

    destinations = query.all()
    if not destinations:
        if req.destination_id is not None:
            raise HTTPException(status_code=404, detail="Selected destination not found in database.")
        raise HTTPException(status_code=404, detail="No destinations found in database. Seed database first.")

    matched_plans = []
    for dest in destinations:
        costs = calculate_costs(dest, req.days, req.travelers_count, req.comfort_score, req.starting_city)
        score = calculate_weighted_score(dest, costs, req.budget, req.days, req.travel_type, req.comfort_score)
        under_budget = costs["total_estimated_cost"] <= req.budget

        matched_plans.append({
            "destination": dest,
            "costs": costs,
            "value_score": score,
            "savings": round(req.budget - costs["total_estimated_cost"], 2),
            "under_budget": under_budget
        })

    # --- Strict budget enforcement ---
    if req.destination_id is not None:
        # A specific destination was requested — check if it fits the budget
        selected_plan = matched_plans[0]
        if not selected_plan["under_budget"]:
            est = round(selected_plan["costs"]["total_estimated_cost"], 2)
            dest_obj = selected_plan["destination"]
            
            # Try to find viable alternatives (different day counts)
            alternatives = []
            for alt_days in [req.days - 1, req.days - 2, req.days + 1, req.days + 2]:
                if alt_days > 0 and alt_days <= 30:
                    alt_costs = calculate_costs(dest_obj, alt_days, req.travelers_count, req.comfort_score, req.starting_city)
                    if alt_costs["total_estimated_cost"] <= req.budget:
                        alternatives.append({
                            "days": alt_days,
                            "cost": round(alt_costs["total_estimated_cost"], 2),
                            "savings": round(req.budget - alt_costs["total_estimated_cost"], 2)
                        })
            
            # Sort by days (prefer closest to original request)
            alternatives.sort(key=lambda x: abs(x["days"] - req.days))
            
            alt_msg = ""
            if alternatives:
                best_alt = alternatives[0]
                alt_msg = f" However, {best_alt['days']} days would work (estimated ₹{best_alt['cost']:,.0f}). Consider {best_alt['days']} days instead."
            
            raise HTTPException(
                status_code=422,
                detail=(
                    f"'{dest_obj.name}' for {req.days} days exceeds your budget of ₹{req.budget:,.0f} "
                    f"(estimated ₹{est:,.0f}).{alt_msg} "
                    f"Or try: increasing budget, reducing comfort level, or choosing another destination."
                )
            )
    else:
        # Full catalog mode — only consider under-budget destinations
        under_budget_plans = [p for p in matched_plans if p["under_budget"]]

        if not under_budget_plans:
            # No destination fits — find the closest one for a helpful message
            matched_plans.sort(key=lambda x: x["costs"]["total_estimated_cost"])
            cheapest = matched_plans[0]
            cheapest_cost = round(cheapest["costs"]["total_estimated_cost"], 2)
            
            # Try alternative days for cheapest destination
            alt_days_msg = ""
            for alt_days in [req.days - 1, req.days - 2]:
                if alt_days > 0:
                    alt_costs = calculate_costs(cheapest["destination"], alt_days, req.travelers_count, req.comfort_score, req.starting_city)
                    if alt_costs["total_estimated_cost"] <= req.budget:
                        alt_days_msg = f" Try {alt_days} days (₹{alt_costs['total_estimated_cost']:,.0f}) or "
                        break
            
            raise HTTPException(
                status_code=422,
                detail=(
                    f"No destination fits your budget of ₹{req.budget:,.0f} for {req.days} days. "
                    f"Most affordable: {cheapest['destination'].name} (₹{cheapest_cost:,.0f}). "
                    f"{alt_days_msg}try: increasing budget, reducing trip duration, or lowering comfort level."
                )
            )

        # Sort under-budget destinations by value score (best fit first)
        under_budget_plans.sort(key=lambda x: x["value_score"], reverse=True)
        selected_plan = under_budget_plans[0]

    # --- Generate all plan components ---
    dest = selected_plan["destination"]

    # 1. Daily itinerary
    weather_context = None
    if req.latitude is not None and req.longitude is not None:
        try:
            forecast = await get_forecast(req.latitude, req.longitude, min(req.days, 16), dest.name)
            weather_context = {"timezone": forecast.get("timezone"), "daily": forecast["daily"]}
        except (WeatherServiceError, ValueError) as exc:
            logger.warning("Weather context unavailable for itinerary: %s", exc)
    itineraries = generate_itinerary_days(dest, req.days, req.comfort_score, req.travel_type, weather_context)

    # 2. Weather intelligence
    dest.weather_intelligence = calculate_weather_intelligence(dest, None)

    # 3. Carbon footprint
    carbon_intel = calculate_carbon_footprint(
        selected_plan["costs"]["transport_mode"],
        selected_plan["costs"]["transport_cost"]
    )

    # 4. Score breakdown (explainability) — MUST be computed before return
    breakdown = calculate_score_breakdown(
        dest,
        selected_plan["costs"],
        req.budget,
        req.days,
        req.travel_type,
        req.comfort_score
    )

    return {
        "destination": dest,
        "costs": selected_plan["costs"],
        "savings": selected_plan["savings"],
        "value_score": selected_plan["value_score"],
        "under_budget": selected_plan["under_budget"],
        "itineraries": itineraries,
        "budget": req.budget,
        "days": req.days,
        "travelers_count": req.travelers_count,
        "comfort_score": req.comfort_score,
        "travel_type": req.travel_type,
        "data_source": "seeded",
        "breakdown": breakdown,
        "carbon_footprint": carbon_intel
    }

@router.post("/", response_model=schemas.TripOut)
def save_trip(
    trip_data: dict, # Accepts raw dict representing output of /plan
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Existing catalog trips keep their destination FK; external places use a dedicated record.
    destination_data = trip_data["destination"]
    dest_id = destination_data.get("id")
    custom_dest_id = None
    geoapify_place_id = destination_data.get("geoapify_place_id")
    data_source = trip_data.get("data_source", "seeded")  # Default: seeded, google_places, or geoapify
    
    if not dest_id:
        lat, lon = destination_data.get("latitude"), destination_data.get("longitude")
        if lat is None or lon is None:
            raise HTTPException(status_code=422, detail="Custom destination coordinates are required to save this trip.")
        custom_dest = models.CustomDestination(
            name=destination_data["name"], 
            address=destination_data.get("address"), 
            latitude=float(lat), 
            longitude=float(lon),
            google_place_id=destination_data.get("google_place_id"), 
            geoapify_place_id=geoapify_place_id,
            data_source=data_source,  # Now supports "google_places" or "geoapify"
            category=trip_data.get("travel_type")
        )
        db.add(custom_dest)
        db.flush()
        custom_dest_id = custom_dest.id
    costs = trip_data["costs"]
    if not dest_id:
        expected_total = sum(float(costs.get(field, 0) or 0) for field in ("transport_cost", "hotel_cost", "food_cost", "activities_cost", "local_transport_cost", "taxes_fees_cost", "emergency_reserve"))
        submitted_total = float(costs.get("total_estimated_cost", 0))
        submitted_budget = float(trip_data.get("budget", 0))
        if submitted_budget <= 0 or submitted_total > submitted_budget or abs(expected_total - submitted_total) > 0.02:
            db.rollback()
            raise HTTPException(status_code=422, detail="Trip estimate is invalid or exceeds the maximum budget.")

    # Create Trip with geoapify_place_id and data_source
    db_trip = models.Trip(
        user_id=current_user.id,
        destination_id=dest_id,
        custom_destination_id=custom_dest_id,
        geoapify_place_id=geoapify_place_id if data_source == "geoapify" else None,
        data_source=data_source if not dest_id else "seeded",  # Mark live destinations appropriately
        budget=trip_data["budget"],
        days=trip_data["days"],
        travelers_count=trip_data["travelers_count"],
        travel_type=trip_data["travel_type"],
        comfort_score=trip_data["comfort_score"],
        total_estimated_cost=costs["total_estimated_cost"],
        hotel_tier=costs.get("hotel_tier", "Estimated"),
        transport_mode=costs.get("transport_mode", "Estimated"),
        status=trip_data.get("status", "Planned"),
        start_date=trip_data.get("start_date"),
        is_public=False,
        share_token=uuid.uuid4().hex
    )
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)

    # Save Budget Allocation
    db_allocation = models.BudgetAllocation(
        trip_id=db_trip.id,
        transport_cost=costs["transport_cost"],
        hotel_cost=costs["hotel_cost"],
        food_cost=costs["food_cost"],
        activities_cost=costs["activities_cost"],
        local_transport_cost=costs["local_transport_cost"],
        taxes_fees_cost=costs["taxes_fees_cost"],
        emergency_reserve=costs["emergency_reserve"]
    )
    db.add(db_allocation)

    # Save Itinerary days
    for it_day in trip_data["itineraries"]:
        db_itinerary = models.Itinerary(
            trip_id=db_trip.id,
            day_number=it_day["day_number"],
            activities=it_day["activities"],
            description=it_day.get("description", "")
        )
        db.add(db_itinerary)

    db.commit()
    db.refresh(db_trip)

    # Generate default checklist items
    month_val = None
    if db_trip.start_date:
        try:
            month_val = int(db_trip.start_date.split("-")[1])
        except Exception:
            pass

    dest = db.query(models.Destination).filter(models.Destination.id == db_trip.destination_id).first() if db_trip.destination_id else None
    season_name = calculate_weather_intelligence(dest, month_val)["current_season"] if dest else "Unknown"

    default_packing_items = generate_default_packing_list(
        category=dest.category if dest else db_trip.travel_type,
        season=season_name,
        duration=db_trip.days,
        comfort=db_trip.comfort_score
    )

    for item_name in default_packing_items:
        db_item = models.PackingItem(
            trip_id=db_trip.id,
            name=item_name,
            checked=False
        )
        db.add(db_item)

    db.commit()
    db.refresh(db_trip)

    # Log Trip creation notification
    saved_destination_name = dest.name if dest else destination_data["name"]
    notif_msg = f"Your trip to {saved_destination_name} has been planned successfully."
    if db_trip.start_date:
        notif_msg = f"Your trip to {saved_destination_name} starts on {db_trip.start_date}."
    db.add(models.Notification(
        user_id=current_user.id,
        type="Upcoming Trip",
        message=notif_msg
    ))
    db.commit()
    
    # Reload with relationships
    from sqlalchemy.orm import joinedload
    db_trip = db.query(models.Trip).options(
        joinedload(models.Trip.destination),
        joinedload(models.Trip.itineraries),
        joinedload(models.Trip.budget_allocation),
        joinedload(models.Trip.packing_items)
    ).filter(models.Trip.id == db_trip.id).first()
    
    return _serialize_trip(db_trip)


def _serialize_trip(trip):
    """Convert SQLAlchemy Trip model to JSON-serializable dict.
    
    Manually converts Trip fields to dict, ensuring nested SQLAlchemy objects
    (especially Destination) are properly serialized.
    """
    # Manually convert to dict to avoid Pydantic trying to serialize SQLAlchemy objects
    data = {
        "id": trip.id,
        "user_id": trip.user_id,
        "destination_id": trip.destination_id,
        "budget": trip.budget,
        "days": trip.days,
        "travelers_count": trip.travelers_count,
        "travel_type": trip.travel_type,
        "comfort_score": trip.comfort_score,
        "total_estimated_cost": trip.total_estimated_cost,
        "hotel_tier": trip.hotel_tier,
        "transport_mode": trip.transport_mode,
        "created_at": trip.created_at,
        "status": trip.status,
        "start_date": trip.start_date,
        "actual_spending": getattr(trip, "actual_spending", 0.0),
        "savings": getattr(trip, "savings", 0.0),
        "is_public": trip.is_public,
        "share_token": trip.share_token,
        "custom_destination_id": trip.custom_destination_id,
        "data_source": trip.data_source,
        "geoapify_place_id": trip.geoapify_place_id,
    }
    
    # Serialize itineraries
    data["itineraries"] = [
        {
            "id": it.id,
            "trip_id": it.trip_id,
            "day_number": it.day_number,
            "activities": it.activities,
            "description": it.description
        }
        for it in (trip.itineraries or [])
    ]
    
    # Serialize budget allocation
    if trip.budget_allocation:
        data["budget_allocation"] = {
            "id": trip.budget_allocation.id,
            "trip_id": trip.budget_allocation.trip_id,
            "transport_cost": trip.budget_allocation.transport_cost,
            "hotel_cost": trip.budget_allocation.hotel_cost,
            "food_cost": trip.budget_allocation.food_cost,
            "activities_cost": trip.budget_allocation.activities_cost,
            "emergency_reserve": trip.budget_allocation.emergency_reserve,
            "local_transport_cost": trip.budget_allocation.local_transport_cost,
            "taxes_fees_cost": trip.budget_allocation.taxes_fees_cost,
        }
    else:
        data["budget_allocation"] = None
    
    # Serialize packing items
    data["packing_items"] = [
        {
            "id": pi.id,
            "trip_id": pi.trip_id,
            "name": pi.name,
            "checked": pi.checked
        }
        for pi in (trip.packing_items or [])
    ]
    
    # Serialize documents
    data["documents"] = [
        {
            "id": doc.id,
            "trip_id": doc.trip_id,
            "category": doc.category,
            "filename": doc.filename,
            "filepath": doc.filepath,
            "filesize": doc.filesize,
            "uploaded_at": doc.uploaded_at
        }
        for doc in (trip.documents or [])
    ]
    
    # Serialize carbon footprint
    if hasattr(trip, "carbon_footprint") and trip.carbon_footprint:
        cf = trip.carbon_footprint
        # Handle both legacy format (co2_kg, offset_url) and current format (co2_emissions, etc.)
        if isinstance(cf, dict):
            if "co2_emissions" in cf:
                # Current format from calculate_carbon_footprint()
                data["carbon_footprint"] = {
                    "transport_mode": cf.get("transport_mode", trip.transport_mode or "Unknown"),
                    "co2_emissions": cf.get("co2_emissions", 0.0),
                    "carbon_rating": cf.get("carbon_rating", "Not assessed"),
                    "eco_score": cf.get("eco_score", 50),
                    "alternative_savings": cf.get("alternative_savings", 0.0)
                }
            else:
                # Legacy format - convert to new schema with defaults
                data["carbon_footprint"] = {
                    "transport_mode": trip.transport_mode or "Unknown",
                    "co2_emissions": cf.get("co2_kg", 0.0),
                    "carbon_rating": "Not assessed",
                    "eco_score": 50,
                    "alternative_savings": 0.0
                }
        else:
            data["carbon_footprint"] = None
    else:
        data["carbon_footprint"] = None
    
    # Handle custom destination
    custom = getattr(trip, "custom_destination", None)
    if custom:
        data["destination"] = {
            "id": None,
            "name": custom.name,
            "state": custom.address or "",
            "avg_travel_cost": 0,
            "avg_hotel_cost": 0,
            "avg_food_cost": 0,
            "avg_activity_cost": 0,
            "rating": 0,
            "category": trip.travel_type,
            "best_season": "Not assessed",
            "description": "Custom destination",
            "attractions": [],
            "latitude": custom.latitude,
            "longitude": custom.longitude,
            "address": custom.address,
            "google_place_id": custom.google_place_id,
            "geoapify_place_id": custom.geoapify_place_id,
            "data_source": custom.data_source
        }
        data["data_source"] = custom.data_source
    # Handle standard destination
    elif trip.destination:
        data["destination"] = {
            "id": trip.destination.id,
            "name": trip.destination.name,
            "state": trip.destination.state,
            "avg_travel_cost": trip.destination.avg_travel_cost,
            "avg_hotel_cost": trip.destination.avg_hotel_cost,
            "avg_food_cost": trip.destination.avg_food_cost,
            "avg_activity_cost": trip.destination.avg_activity_cost,
            "rating": trip.destination.rating,
            "category": trip.destination.category,
            "best_season": trip.destination.best_season,
            "description": trip.destination.description,
            "attractions": trip.destination.attractions,
            "budget_tier": trip.destination.budget_tier,
            "recommended_duration": trip.destination.recommended_duration,
            "comfort_level": trip.destination.comfort_level,
            "adventure_score": trip.destination.adventure_score,
            "nature_score": trip.destination.nature_score,
            "family_score": trip.destination.family_score,
            "romantic_score": trip.destination.romantic_score,
            "religious_score": trip.destination.religious_score,
            "beach_score": trip.destination.beach_score,
            "city_score": trip.destination.city_score,
            "solo_score": trip.destination.solo_score,
        }
        # Add weather_intelligence if present
        if hasattr(trip.destination, "weather_intelligence"):
            data["destination"]["weather_intelligence"] = trip.destination.weather_intelligence
    # Handle null destination
    else:
        data["destination"] = {
            "id": None,
            "name": "Unknown destination",
            "state": "",
            "avg_travel_cost": 0,
            "avg_hotel_cost": 0,
            "avg_food_cost": 0,
            "avg_activity_cost": 0,
            "rating": 0,
            "category": trip.travel_type or "Other",
            "best_season": "Not assessed",
            "description": "Destination not found",
            "attractions": []
        }
    
    return data

def auto_update_trip_status(trip: models.Trip, db: Session):
    if not trip.status:
        trip.status = "Planned"
        db.commit()
        db.refresh(trip)
        
    if trip.status in ["Planned", "In Progress"] and trip.start_date:
        try:
            start_dt = datetime.datetime.strptime(trip.start_date, "%Y-%m-%d").date()
            today = datetime.date.today()
            end_dt = start_dt + datetime.timedelta(days=trip.days)
            
            new_status = trip.status
            if today >= end_dt:
                new_status = "Completed"
            elif today >= start_dt:
                new_status = "In Progress"
                
            if new_status != trip.status:
                trip.status = new_status
                db.commit()
                db.refresh(trip)
        except Exception:
            pass

def attach_trip_intelligence(t: models.Trip, db: Session):
    auto_update_trip_status(t, db)
    actual_spent = sum([e.amount for e in t.expenses])
    t.actual_spending = round(actual_spent, 2)
    # Savings = money left if you stick to the estimated cost (projected savings)
    # NOT actual remaining budget after spending
    t.savings = round(max(0.0, t.budget - t.total_estimated_cost), 2)
    
    month_val = None
    if t.start_date:
        try:
            month_val = int(t.start_date.split("-")[1])
        except Exception:
            pass
    
    # Add null-check before accessing destination attributes
    if t.destination:
        t.destination.weather_intelligence = calculate_weather_intelligence(t.destination, month_val)
    
    cost_val = t.budget_allocation.transport_cost if t.budget_allocation else (t.total_estimated_cost * 0.25)
    t.carbon_footprint = calculate_carbon_footprint(t.transport_mode, cost_val)

@router.get("/", response_model=List[schemas.TripOut])
def get_user_trips(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    from sqlalchemy.orm import joinedload
    trips = db.query(models.Trip).options(
        joinedload(models.Trip.destination),
        joinedload(models.Trip.custom_destination),
        joinedload(models.Trip.itineraries),
        joinedload(models.Trip.budget_allocation),
        joinedload(models.Trip.packing_items)
    ).filter(models.Trip.user_id == current_user.id).order_by(models.Trip.created_at.desc()).all()
    for t in trips:
        if t.destination_id:
            attach_trip_intelligence(t, db)
    return [_serialize_trip(t) for t in trips]

@router.get("/{trip_id}", response_model=schemas.TripOut)
def get_trip_details(
    trip_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    from sqlalchemy.orm import joinedload
    trip = db.query(models.Trip).options(
        joinedload(models.Trip.destination),
        joinedload(models.Trip.custom_destination),
        joinedload(models.Trip.itineraries),
        joinedload(models.Trip.budget_allocation),
        joinedload(models.Trip.packing_items)
    ).filter(
        models.Trip.id == trip_id,
        models.Trip.user_id == current_user.id
    ).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    if trip.destination_id:
        attach_trip_intelligence(trip, db)
    return _serialize_trip(trip)

@router.put("/{trip_id}", response_model=schemas.TripOut)
def update_trip(
    trip_id: int,
    payload: dict,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    trip = db.query(models.Trip).filter(
        models.Trip.id == trip_id,
        models.Trip.user_id == current_user.id
    ).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    if "budget" in payload:
        trip.budget = float(payload["budget"])
    if "days" in payload:
        trip.days = int(payload["days"])
    if "travelers_count" in payload:
        trip.travelers_count = int(payload["travelers_count"])
    if "travel_type" in payload:
        trip.travel_type = payload["travel_type"]
    if "comfort_score" in payload:
        trip.comfort_score = int(payload["comfort_score"])
    if "status" in payload:
        trip.status = payload["status"]
    if "start_date" in payload:
        trip.start_date = payload["start_date"]
        
    db.commit()
    db.refresh(trip)
    
    if trip.destination_id:
        attach_trip_intelligence(trip, db)
    return _serialize_trip(trip)

@router.patch("/{trip_id}/status", response_model=schemas.TripOut)
def update_trip_status_endpoint(
    trip_id: int,
    payload: dict,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    trip = db.query(models.Trip).filter(
        models.Trip.id == trip_id,
        models.Trip.user_id == current_user.id
    ).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    status_val = payload.get("status")
    if not status_val:
        raise HTTPException(status_code=400, detail="Status value is required")
        
    valid_statuses = ["Draft", "Planned", "In Progress", "Completed", "Cancelled"]
    if status_val not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status value. Must be one of {valid_statuses}")
        
    trip.status = status_val
    db.commit()
    db.refresh(trip)
    
    attach_trip_intelligence(trip, db)
    return trip

@router.post("/{trip_id}/duplicate", response_model=schemas.TripOut)
def duplicate_trip(
    trip_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    orig = db.query(models.Trip).filter(
        models.Trip.id == trip_id,
        models.Trip.user_id == current_user.id
    ).first()
    if not orig:
        raise HTTPException(status_code=404, detail="Trip to duplicate not found")
        
    dup_trip = models.Trip(
        user_id=current_user.id,
        destination_id=orig.destination_id,
        budget=orig.budget,
        days=orig.days,
        travelers_count=orig.travelers_count,
        travel_type=orig.travel_type,
        comfort_score=orig.comfort_score,
        total_estimated_cost=orig.total_estimated_cost,
        hotel_tier=orig.hotel_tier,
        transport_mode=orig.transport_mode,
        status="Draft",
        start_date=orig.start_date,
        is_public=False,
        share_token=uuid.uuid4().hex
    )
    db.add(dup_trip)
    db.commit()
    db.refresh(dup_trip)
    
    if orig.budget_allocation:
        dup_alloc = models.BudgetAllocation(
            trip_id=dup_trip.id,
            transport_cost=orig.budget_allocation.transport_cost,
            hotel_cost=orig.budget_allocation.hotel_cost,
            food_cost=orig.budget_allocation.food_cost,
            activities_cost=orig.budget_allocation.activities_cost,
            local_transport_cost=orig.budget_allocation.local_transport_cost,
            taxes_fees_cost=orig.budget_allocation.taxes_fees_cost,
            emergency_reserve=orig.budget_allocation.emergency_reserve
        )
        db.add(dup_alloc)
        
    for it in orig.itineraries:
        dup_it = models.Itinerary(
            trip_id=dup_trip.id,
            day_number=it.day_number,
            activities=it.activities,
            description=it.description
        )
        db.add(dup_it)
        
    # Duplicate packing checklist
    for item in orig.packing_items:
        dup_item = models.PackingItem(
            trip_id=dup_trip.id,
            name=item.name,
            checked=item.checked
        )
        db.add(dup_item)
        
    db.commit()
    db.refresh(dup_trip)
    
    attach_trip_intelligence(dup_trip, db)
    return dup_trip

@router.delete("/{trip_id}", status_code=204)
def delete_trip(
    trip_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    trip = db.query(models.Trip).filter(
        models.Trip.id == trip_id,
        models.Trip.user_id == current_user.id
    ).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    db.delete(trip)
    db.commit()
    return None

@router.get("/{trip_id}/checklist", response_model=List[schemas.PackingItemOut])
def get_trip_checklist(
    trip_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id, models.Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip.packing_items

@router.post("/{trip_id}/checklist", response_model=schemas.PackingItemOut)
def add_checklist_item(

    trip_id: int,
    payload: dict,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):

    trip = db.query(models.Trip).filter(
        models.Trip.id == trip_id,
        models.Trip.user_id == current_user.id
    ).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    # Update costs
    costs = payload.get("costs")
    if costs:
        trip.total_estimated_cost = costs.get("total_estimated_cost", trip.total_estimated_cost)
        trip.hotel_tier = costs.get("hotel_tier", trip.hotel_tier)
        trip.transport_mode = costs.get("transport_mode", trip.transport_mode)
        
        # Update allocation
        alloc = trip.budget_allocation
        if alloc:
            alloc.transport_cost = costs.get("transport_cost", alloc.transport_cost)
            alloc.hotel_cost = costs.get("hotel_cost", alloc.hotel_cost)
            alloc.food_cost = costs.get("food_cost", alloc.food_cost)
            alloc.activities_cost = costs.get("activities_cost", alloc.activities_cost)
            alloc.local_transport_cost = costs.get("local_transport_cost", alloc.local_transport_cost)
            alloc.taxes_fees_cost = costs.get("taxes_fees_cost", alloc.taxes_fees_cost)
            alloc.emergency_reserve = costs.get("emergency_reserve", alloc.emergency_reserve)
            
    # Update itinerary
    itinerary_days = payload.get("itineraries")
    if itinerary_days:
        # Delete old itinerary days
        db.query(models.Itinerary).filter(models.Itinerary.trip_id == trip.id).delete()
        
        # Insert new itinerary days
        for it_day in itinerary_days:
            db_itinerary = models.Itinerary(
                trip_id=trip.id,
                day_number=it_day["day_number"],
                activities=it_day["activities"],
                description=it_day.get("description", "")
            )
            db.add(db_itinerary)
            
    db.commit()
    return {"status": "success", "message": "Trip updated successfully"}

    trip = db.query(models.Trip).filter(models.Trip.id == trip_id, models.Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    name = payload.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Item name is required")
        
    db_item = models.PackingItem(
        trip_id=trip_id,
        name=name,
        checked=False
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.put("/{trip_id}/checklist/{item_id}", response_model=schemas.PackingItemOut)
def toggle_checklist_item(
    trip_id: int,
    item_id: int,
    payload: dict,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id, models.Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    item = db.query(models.PackingItem).filter(models.PackingItem.id == item_id, models.PackingItem.trip_id == trip_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Packing item not found")
        
    if "checked" in payload:
        item.checked = bool(payload["checked"])
    if "name" in payload:
        item.name = payload["name"]
        
    db.commit()
    db.refresh(item)

    # Check for checklist completion notification
    all_items = db.query(models.PackingItem).filter(models.PackingItem.trip_id == trip_id).all()
    if all_items:
        total_items = len(all_items)
        packed_items = sum([1 for pi in all_items if pi.checked])
        if packed_items == total_items:
            trip_dest_name = trip.destination.name if trip.destination else trip.custom_destination.name
            comp_msg = f"Congratulations! Your packing checklist for trip to {trip_dest_name} is 100% complete."
            exists = db.query(models.Notification).filter(
                models.Notification.user_id == current_user.id,
                models.Notification.message == comp_msg
            ).first()
            if not exists:
                db.add(models.Notification(
                    user_id=current_user.id,
                    type="Checklist Completed",
                    message=comp_msg
                ))
                db.commit()
        elif packed_items == 1:
            # Packing started
            trip_dest_name = trip.destination.name if trip.destination else trip.custom_destination.name
            start_msg = f"Packing checklist for your trip to {trip_dest_name} has been initiated."
            exists = db.query(models.Notification).filter(
                models.Notification.user_id == current_user.id,
                models.Notification.message == start_msg
            ).first()
            if not exists:
                db.add(models.Notification(
                    user_id=current_user.id,
                    type="Packing Reminder",
                    message=start_msg
                ))
                db.commit()
    return item

@router.delete("/{trip_id}/checklist/{item_id}", status_code=204)
def delete_checklist_item(
    trip_id: int,
    item_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id, models.Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    item = db.query(models.PackingItem).filter(models.PackingItem.id == item_id, models.PackingItem.trip_id == trip_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Packing item not found")
        
    db.delete(item)
    db.commit()
    return None

@router.post("/{trip_id}/share/toggle", response_model=schemas.TripOut)
def toggle_trip_share(
    trip_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id, models.Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    trip.is_public = not trip.is_public
    if not trip.share_token:
        trip.share_token = uuid.uuid4().hex
        
    db.commit()
    db.refresh(trip)
    
    # Log public share setting updates
    if trip.is_public:
        trip_dest_name = trip.destination.name if trip.destination else trip.custom_destination.name
        share_msg = f"Your travel plan to {trip_dest_name} is now public and shared successfully."
        db.add(models.Notification(
            user_id=current_user.id,
            type="Trip Shared Successfully",
            message=share_msg
        ))
        db.commit()
        
    attach_trip_intelligence(trip, db)
    return trip

@router.get("/share/{share_token}", response_model=schemas.TripOut)
def get_shared_trip_details(
    share_token: str,
    db: Session = Depends(get_db)
):
    trip = db.query(models.Trip).filter(
        models.Trip.share_token == share_token,
        models.Trip.is_public == True
    ).first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Shared trip not found or this trip is set to private.")
        
    # Auto-update status
    if trip.status in ["Planned", "In Progress"] and trip.start_date:
        try:
            start_dt = datetime.datetime.strptime(trip.start_date, "%Y-%m-%d").date()
            today = datetime.date.today()
            end_dt = start_dt + datetime.timedelta(days=trip.days)
            
            new_status = trip.status
            if today >= end_dt:
                new_status = "Completed"
            elif today >= start_dt:
                new_status = "In Progress"
                
            if new_status != trip.status:
                trip.status = new_status
                db.commit()
                db.refresh(trip)
        except Exception:
            pass
    
    # Calculate spending/savings
    actual_spent = sum([e.amount for e in trip.expenses])
    trip.actual_spending = round(actual_spent, 2)
    # Savings = money left if you stick to the estimated cost (projected savings)
    trip.savings = round(max(0.0, trip.budget - trip.total_estimated_cost), 2)
    
    # Calculate weather intelligence
    month_val = None
    if trip.start_date:
        try:
            month_val = int(trip.start_date.split("-")[1])
        except Exception:
            pass
    if trip.destination:
        trip.destination.weather_intelligence = calculate_weather_intelligence(trip.destination, month_val)
    
    # Calculate carbon footprint
    cost_val = trip.budget_allocation.transport_cost if trip.budget_allocation else (trip.total_estimated_cost * 0.25)
    trip.carbon_footprint = calculate_carbon_footprint(trip.transport_mode, cost_val)
    
    return trip



@router.get("/reverse/search", response_model=List[schemas.DestinationSearchScore])
def reverse_travel_search(
    budget: float = Query(...),
    days: int = Query(...),
    travel_type: str = Query(...),
    travelers_count: int = Query(1),
    starting_city: Optional[str] = Query("Your City"),
    comfort_score: Optional[int] = Query(50),
    db: Session = Depends(get_db)
):
    # Fetch all destinations
    destinations = db.query(models.Destination).all()
    if not destinations:
        raise HTTPException(
            status_code=404,
            detail="Destination dataset is empty. Please seed the database first."
        )

    comfort = comfort_score or 50
    city = starting_city or ""

    all_scored = []
    for dest in destinations:
        costs = calculate_costs(dest, days, travelers_count, comfort, city)
        est_cost = costs["total_estimated_cost"]
        score = calculate_weighted_score(dest, costs, budget, days, travel_type, comfort)
        budget_fit_pct = round((est_cost / budget) * 100, 1)
        breakdown = calculate_score_breakdown(dest, costs, budget, days, travel_type, comfort)
        all_scored.append({
            "destination": dest,
            "estimated_cost": est_cost,
            "budget_fit": budget_fit_pct,
            "rating": dest.rating,
            "value_score": score,
            "breakdown": breakdown
        })

    # --- HARD BUDGET CONSTRAINT ---
    # Step 1: Keep only destinations whose estimated cost is within budget.
    under_budget = [s for s in all_scored if s["estimated_cost"] <= budget]

    # Step 2: If nothing fits, return a 422 with the cheapest available option.
    if not under_budget:
        all_scored.sort(key=lambda x: x["estimated_cost"])
        cheapest = all_scored[0]
        cheapest_cost = round(cheapest["estimated_cost"], 0)
        raise HTTPException(
            status_code=422,
            detail=(
                f"No destination found within your selected budget of ₹{budget:,.0f}. "
                f"The most affordable option is {cheapest['destination'].name} "
                f"at approximately ₹{cheapest_cost:,.0f}. "
                f"Try increasing your budget, reducing trip duration, or lowering comfort score."
            )
        )

    # Step 3: Rank the under-budget destinations by value_score.
    under_budget.sort(key=lambda x: x["value_score"], reverse=True)
    return under_budget[:8]

@router.post("/{trip_id}/optimize", response_model=schemas.OptimizationResponse)
def optimize_trip(
    trip_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    trip = db.query(models.Trip).filter(
        models.Trip.id == trip_id,
        models.Trip.user_id == current_user.id
    ).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    dest = trip.destination
    alloc = trip.budget_allocation
    if not alloc:
        raise HTTPException(status_code=400, detail="Trip does not have budget allocation")

    options = []

    # Option 1: Reduce Hotel Cost (Switch hotel tier down)
    if trip.hotel_tier == "Luxury":
        # New hotel cost at Mid-range
        new_hotel_cost = dest.avg_hotel_cost * 1.0 * trip.days
        diff = alloc.hotel_cost - new_hotel_cost
        if diff > 100:
            options.append(
                schemas.OptimizationOption(
                    action_key="reduce_hotel",
                    label="Downgrade Hotel to Mid-Range",
                    cost_difference=-diff,
                    description="Switch accommodation from luxury resort to a highly rated 3-star hotel.",
                    new_allocation=schemas.BudgetAllocationBase(
                        transport_cost=alloc.transport_cost,
                        hotel_cost=new_hotel_cost,
                        food_cost=alloc.food_cost,
                        activities_cost=alloc.activities_cost,
                        local_transport_cost=alloc.local_transport_cost,
                        taxes_fees_cost=alloc.taxes_fees_cost * 0.9, # reduced taxes
                        emergency_reserve=alloc.emergency_reserve * 0.95,
                        emergency_reserve_cost=alloc.emergency_reserve * 0.95 # legacy helper support
                    )
                )
            )
    elif trip.hotel_tier == "Mid-Range":
        # New hotel cost at Budget
        new_hotel_cost = dest.avg_hotel_cost * 0.65 * trip.days
        diff = alloc.hotel_cost - new_hotel_cost
        if diff > 100:
            options.append(
                schemas.OptimizationOption(
                    action_key="reduce_hotel",
                    label="Switch to Budget Hotel / Homestay",
                    cost_difference=-diff,
                    description="Opt for cozy local homestays or premium hostels instead of mid-tier hotels.",
                    new_allocation=schemas.BudgetAllocationBase(
                        transport_cost=alloc.transport_cost,
                        hotel_cost=new_hotel_cost,
                        food_cost=alloc.food_cost,
                        activities_cost=alloc.activities_cost,
                        local_transport_cost=alloc.local_transport_cost,
                        taxes_fees_cost=alloc.taxes_fees_cost * 0.85,
                        emergency_reserve=alloc.emergency_reserve * 0.92
                    )
                )
            )

    # Option 2: Switch flight to train (Reduce Travel Cost)
    if trip.transport_mode == "Flight":
        new_train_cost = max(1000.0, dest.avg_travel_cost * 0.4) * trip.travelers_count
        diff = alloc.transport_cost - new_train_cost
        if diff > 100:
            options.append(
                schemas.OptimizationOption(
                    action_key="reduce_travel",
                    label="Switch Transport from Flight to Train",
                    cost_difference=-diff,
                    description="Travel by AC Sleeper trains instead of flights. Adds travel time but heavily cuts costs.",
                    new_allocation=schemas.BudgetAllocationBase(
                        transport_cost=new_train_cost,
                        hotel_cost=alloc.hotel_cost,
                        food_cost=alloc.food_cost,
                        activities_cost=alloc.activities_cost,
                        local_transport_cost=alloc.local_transport_cost,
                        taxes_fees_cost=alloc.taxes_fees_cost * 0.7,
                        emergency_reserve=alloc.emergency_reserve * 0.9
                    )
                )
            )

    # Option 3: Increase Comfort (Upgrade hotel if they have lots of savings)
    current_savings = trip.budget - trip.total_estimated_cost
    if current_savings > 3000.0:
        if trip.hotel_tier == "Budget":
            new_hotel_cost = dest.avg_hotel_cost * 1.0 * trip.days
            diff = new_hotel_cost - alloc.hotel_cost
            options.append(
                schemas.OptimizationOption(
                    action_key="increase_comfort",
                    label="Upgrade Hotel to Mid-Range",
                    cost_difference=diff,
                    description="Upgrade your accommodation for better services, private pool and complimentary breakfast.",
                    new_allocation=schemas.BudgetAllocationBase(
                        transport_cost=alloc.transport_cost,
                        hotel_cost=new_hotel_cost,
                        food_cost=alloc.food_cost * 1.1, # slightly better meals
                        activities_cost=alloc.activities_cost,
                        local_transport_cost=alloc.local_transport_cost,
                        taxes_fees_cost=alloc.taxes_fees_cost * 1.15,
                        emergency_reserve=alloc.emergency_reserve * 1.05
                    )
                )
            )
        elif trip.hotel_tier == "Mid-Range":
            new_hotel_cost = dest.avg_hotel_cost * 1.85 * trip.days
            diff = new_hotel_cost - alloc.hotel_cost
            options.append(
                schemas.OptimizationOption(
                    action_key="increase_comfort",
                    label="Upgrade Hotel to Premium Luxury Resort",
                    cost_difference=diff,
                    description="Immerse in luxury. Premium room upgrades, spa sessions, and infinity pools.",
                    new_allocation=schemas.BudgetAllocationBase(
                        transport_cost=alloc.transport_cost,
                        hotel_cost=new_hotel_cost,
                        food_cost=alloc.food_cost * 1.3,
                        activities_cost=alloc.activities_cost,
                        local_transport_cost=alloc.local_transport_cost,
                        taxes_fees_cost=alloc.taxes_fees_cost * 1.35,
                        emergency_reserve=alloc.emergency_reserve * 1.2
                    )
                )
            )

    # Option 4: Cut down activities
    if alloc.activities_cost > 1000.0:
        new_act = alloc.activities_cost * 0.5
        diff = alloc.activities_cost - new_act
        options.append(
            schemas.OptimizationOption(
                action_key="reduce_activities",
                label="Streamline Activities Schedule",
                cost_difference=-diff,
                description="Reduce pre-booked activities by 50%. Focus on free natural sights and self-guided exploration.",
                new_allocation=schemas.BudgetAllocationBase(
                    transport_cost=alloc.transport_cost,
                    hotel_cost=alloc.hotel_cost,
                    food_cost=alloc.food_cost,
                    activities_cost=new_act,
                    local_transport_cost=alloc.local_transport_cost,
                    taxes_fees_cost=alloc.taxes_fees_cost * 0.95,
                    emergency_reserve=alloc.emergency_reserve * 0.95
                )
            )
        )

    # Format current allocations to match BaseSchema
    current_alloc = schemas.BudgetAllocationBase(
        transport_cost=alloc.transport_cost,
        hotel_cost=alloc.hotel_cost,
        food_cost=alloc.food_cost,
        activities_cost=alloc.activities_cost,
        emergency_reserve=alloc.emergency_reserve,
        local_transport_cost=alloc.local_transport_cost,
        taxes_fees_cost=alloc.taxes_fees_cost
    )

    return {
        "current_cost": trip.total_estimated_cost,
        "budget": trip.budget,
        "allocations": current_alloc,
        "options": options
    }

@router.post("/{trip_id}/optimize/apply")
def apply_optimization(
    trip_id: int,
    payload: dict,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    trip = db.query(models.Trip).filter(
        models.Trip.id == trip_id,
        models.Trip.user_id == current_user.id
    ).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    alloc = trip.budget_allocation
    if not alloc:
        raise HTTPException(status_code=400, detail="Budget allocation not found")

    dest = trip.destination
    action_key = payload.get("action_key")

    if action_key == "reduce_hotel":
        if trip.hotel_tier == "Luxury":
            trip.hotel_tier = "Mid-Range"
            alloc.hotel_cost = dest.avg_hotel_cost * 1.0 * trip.days
        elif trip.hotel_tier == "Mid-Range":
            trip.hotel_tier = "Budget"
            alloc.hotel_cost = dest.avg_hotel_cost * 0.65 * trip.days
        alloc.taxes_fees_cost *= 0.9
        alloc.emergency_reserve *= 0.95
    elif action_key == "reduce_travel":
        if trip.transport_mode == "Flight":
            trip.transport_mode = "Train"
            alloc.transport_cost = max(1000.0, dest.avg_travel_cost * 0.4) * trip.travelers_count
        alloc.taxes_fees_cost *= 0.75
        alloc.emergency_reserve *= 0.9
    elif action_key == "increase_comfort":
        if trip.hotel_tier == "Budget":
            trip.hotel_tier = "Mid-Range"
            alloc.hotel_cost = dest.avg_hotel_cost * 1.0 * trip.days
            alloc.food_cost *= 1.1
        elif trip.hotel_tier == "Mid-Range":
            trip.hotel_tier = "Luxury"
            alloc.hotel_cost = dest.avg_hotel_cost * 1.85 * trip.days
            alloc.food_cost *= 1.3
        alloc.taxes_fees_cost *= 1.2
        alloc.emergency_reserve *= 1.15
    elif action_key == "reduce_activities":
        alloc.activities_cost *= 0.5
        alloc.taxes_fees_cost *= 0.95
        alloc.emergency_reserve *= 0.95

    trip.total_estimated_cost = round(
        alloc.transport_cost + alloc.hotel_cost + alloc.food_cost +
        alloc.activities_cost + alloc.local_transport_cost +
        alloc.taxes_fees_cost + alloc.emergency_reserve,
        2
    )

    db.commit()
    return {
        "status": "success",
        "message": "Optimization applied successfully",
        "new_cost": trip.total_estimated_cost
    }

@router.get("/{trip_id}/pdf")
def download_trip_pdf(
    trip_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Download trip itinerary as premium branded PDF."""
    try:
        trip = db.query(models.Trip).filter(
            models.Trip.id == trip_id,
            models.Trip.user_id == current_user.id
        ).first()
        
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")

        # Generate premium PDF
        pdf_bytes = generate_premium_trip_pdf(trip, current_user)
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=budgetbound_{(trip.destination.name if trip.destination else trip.custom_destination.name).replace(' ', '_').lower()}.pdf"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"PDF Generation Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.put("/{trip_id}/allocations", response_model=schemas.TripOut)
def update_trip_allocations(
    trip_id: int,
    payload: dict,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    trip = db.query(models.Trip).filter(
        models.Trip.id == trip_id,
        models.Trip.user_id == current_user.id
    ).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    alloc = trip.budget_allocation
    if not alloc:
        raise HTTPException(status_code=400, detail="Trip does not have budget allocation")

    # Categories from allocation editor
    alloc.transport_cost = float(payload.get("transport_cost", alloc.transport_cost))
    alloc.hotel_cost = float(payload.get("hotel_cost", alloc.hotel_cost))
    alloc.food_cost = float(payload.get("food_cost", alloc.food_cost))
    alloc.activities_cost = float(payload.get("activities_cost", alloc.activities_cost))
    alloc.emergency_reserve = float(payload.get("emergency_reserve", alloc.emergency_reserve))
    
    # Reset helper columns to 0.0 if custom edit is applied
    alloc.local_transport_cost = float(payload.get("local_transport_cost", 0.0))
    alloc.taxes_fees_cost = float(payload.get("taxes_fees_cost", 0.0))

    # Recalculate trip total estimated cost
    trip.total_estimated_cost = round(
        alloc.transport_cost + alloc.hotel_cost + alloc.food_cost +
        alloc.activities_cost + alloc.emergency_reserve +
        alloc.local_transport_cost + alloc.taxes_fees_cost,
        2
    )

    db.commit()
    db.refresh(trip)
    return trip

@router.post("/{trip_id}/allocations/reset", response_model=schemas.TripOut)
def reset_trip_allocations(
    trip_id: int,
    payload: Optional[dict] = None,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    trip = db.query(models.Trip).filter(
        models.Trip.id == trip_id,
        models.Trip.user_id == current_user.id
    ).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    alloc = trip.budget_allocation
    if not alloc:
        raise HTTPException(status_code=400, detail="Trip does not have budget allocation")

    starting_city = ""
    if payload:
        starting_city = payload.get("starting_city", "")

    # Re-calculate default costs
    dest = trip.destination
    costs = calculate_costs(
        dest=dest,
        days=trip.days,
        travelers=trip.travelers_count,
        comfort_score=trip.comfort_score,
        starting_city=starting_city
    )

    # Apply default values
    alloc.transport_cost = costs["transport_cost"]
    alloc.hotel_cost = costs["hotel_cost"]
    alloc.food_cost = costs["food_cost"]
    alloc.activities_cost = costs["activities_cost"]
    alloc.local_transport_cost = costs["local_transport_cost"]
    alloc.taxes_fees_cost = costs["taxes_fees_cost"]
    alloc.emergency_reserve = costs["emergency_reserve"]

    trip.total_estimated_cost = costs["total_estimated_cost"]

    db.commit()
    db.refresh(trip)
    return trip

# ==========================================
# MULTI-STOP TRIP ENDPOINTS
# ==========================================

@router.post("/multistop", response_model=schemas.MultiStopTripOut)
def save_multistop_trip(
    req: schemas.MultiStopTripCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Saves an AI-generated multi-stop trip to the user's account.
    Stores the raw JSON result deeply so it can be rehydrated directly on the frontend.
    """
    print(f"DEBUG: Saving multistop trip - name={req.trip_name}, budget={req.total_budget}")
    
    new_ms_trip = models.MultiStopTrip(
        user_id=current_user.id,
        trip_name=req.trip_name,
        total_budget=req.total_budget,
        total_days=req.total_days,
        destinations_str=req.destinations_str,
        raw_json=req.raw_json
    )
    db.add(new_ms_trip)
    
    # Optional: could create a notification
    notif = models.Notification(
        user_id=current_user.id,
        type="Trip Saved",
        message=f"Your multi-stop journey '{req.trip_name}' has been securely saved."
    )
    db.add(notif)
    db.commit()
    db.refresh(new_ms_trip)
    
    print(f"DEBUG: Multistop trip saved with id={new_ms_trip.id}")
    return new_ms_trip


@router.get("/multistop", response_model=List[schemas.MultiStopTripOut])
def get_user_multistop_trips(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns all dynamically saved multi-stop trips for the authenticated user.
    """
    trips = db.query(models.MultiStopTrip).filter(models.MultiStopTrip.user_id == current_user.id).order_by(models.MultiStopTrip.created_at.desc()).all()
    return trips

@router.delete("/multistop/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_multistop_trip(
    trip_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    ms_trip = db.query(models.MultiStopTrip).filter(
        models.MultiStopTrip.id == trip_id,
        models.MultiStopTrip.user_id == current_user.id
    ).first()
    
    if not ms_trip:
        raise HTTPException(status_code=404, detail="Multi-stop trip not found")
        
    db.delete(ms_trip)
    db.commit()
    return None

