"""Verified, request-scoped Google Places rating enrichment for destination cards."""
import asyncio
import logging
import re
import time
import threading
from collections import OrderedDict
from html import unescape
from difflib import SequenceMatcher
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)
TEXT_URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = ",".join((
    "places.id", "places.displayName", "places.adrFormatAddress",
    "places.location", "places.rating", "places.userRatingCount",
    "places.googleMapsUri",
))
MAX_MATCH_DISTANCE_KM = 30.0
RATING_CACHE_TTL_SECONDS = 6 * 60 * 60
RATING_CACHE_MAX_ENTRIES = 2000
RATING_REQUEST_INTERVAL_SECONDS = 0.15
_rating_cache: OrderedDict[tuple, tuple[float, dict[str, Any]]] = OrderedDict()
_cache_lock = threading.Lock()
_throttle_lock = threading.Lock()
_next_request_at = 0.0

# Daily quota exhaustion tracking
_quota_exhausted_today = False
_quota_exhaustion_lock = threading.Lock()
_quota_reset_at = 0.0  # Timestamp when quota will be reset (next UTC midnight)


class GoogleRatingError(Exception):
    def __init__(self, message: str, status_code: int = 503, diagnostic_code: str = "provider_error"):
        super().__init__(message)
        self.status_code = status_code
        self.diagnostic_code = diagnostic_code


def configuration_status() -> str:
    """Safe configuration diagnostic; never returns the credential value."""
    return "configured" if (settings.GOOGLE_MAPS_API_KEY or "").strip() else "missing_key"


def _text(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    from math import asin, cos, radians, sin, sqrt
    a1, a2 = radians(lat1), radians(lat2)
    dlat, dlon = radians(lat2-lat1), radians(lon2-lon1)
    hav = sin(dlat/2)**2 + cos(a1)*cos(a2)*sin(dlon/2)**2
    return 6371 * 2 * asin(sqrt(hav))


def _match_score(candidate: dict[str, Any], place: dict[str, Any]) -> float:
    candidate_name = _text(candidate.get("name"))
    google_name = _text((place.get("displayName") or {}).get("text"))
    if not candidate_name or not google_name:
        return 0.0
    return SequenceMatcher(None, candidate_name, google_name).ratio()


def normalize_matching_result(candidate: dict[str, Any], item: dict[str, Any]) -> dict[str, Any] | None:
    """Return rating metadata only for a same-named, Indian, nearby city result."""
    location = item.get("location") or {}
    address = item.get("adrFormatAddress") or item.get("formattedAddress")
    name = (item.get("displayName") or {}).get("text")
    try:
        lat, lon = float(location["latitude"]), float(location["longitude"])
        candidate_lat = float(candidate["latitude"])
        candidate_lon = float(candidate["longitude"])
    except (KeyError, TypeError, ValueError):
        return None
    if not isinstance(address, str) or "india" not in unescape(re.sub(r"<[^>]+>", " ", address)).casefold():
        return None
    region = _text(candidate.get("region"))
    address_text = _text(unescape(re.sub(r"<[^>]+>", " ", address)))
    if region and region not in address_text:
        return None
    if not item.get("id"):
        return None
    if _match_score(candidate, item) < 0.70:
        return None
    if _distance_km(candidate_lat, candidate_lon, lat, lon) > MAX_MATCH_DISTANCE_KM:
        return None

    rating = item.get("rating")
    try:
        rating = float(rating) if isinstance(rating, (int, float)) and not isinstance(rating, bool) else None
    except (TypeError, ValueError):
        rating = None
    if rating is not None and not 1 <= rating <= 5:
        rating = None
    count = item.get("userRatingCount")
    try:
        count = int(count) if isinstance(count, int) and not isinstance(count, bool) else None
    except (TypeError, ValueError):
        count = None
    if count is not None and count < 0:
        count = None
    return {
        "rating": rating,
        "user_rating_count": count,
        "google_place_id": item.get("id"),
        "google_maps_uri": item.get("googleMapsUri"),
        "rating_source": "google_places",
    }


async def _search_candidate_uncached(candidate: dict[str, Any]) -> dict[str, Any] | None:
    """Search for the city itself, and reject ambiguous/non-Indian mismatches."""
    # Short-circuit if daily quota is exhausted
    if _is_quota_exhausted():
        logger.debug("google_places_ratings skipping_request quota_exhausted=true")
        raise GoogleRatingError("Google Places daily quota is exhausted. Ratings will resume at tomorrow's UTC midnight.", 503, "quota_exceeded")
    
    api_key = settings.GOOGLE_MAPS_API_KEY
    if not api_key or not api_key.strip():
        raise GoogleRatingError("Google Places ratings are not configured on the backend.")
    name, region = candidate.get("name"), candidate.get("region")
    if not name:
        return None
    query = f"{name}{', ' + region if region else ''}, India"
    body = {
        "textQuery": query,
        "pageSize": 5,
        "languageCode": "en",
        "regionCode": "IN",
        "locationBias": {"circle": {"center": {
            "latitude": candidate["latitude"],
            "longitude": candidate["longitude"],
        }, "radius": 30_000}},
    }
    try:
        timeout = max(1.0, float(settings.GOOGLE_PLACES_TIMEOUT_SECONDS))
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=min(timeout, 4.0))) as client:
            response = await client.post(TEXT_URL, json=body, headers={
                "X-Goog-Api-Key": api_key,
                "X-Goog-FieldMask": FIELD_MASK,
            })
        if response.status_code in (401, 403, 429):
            try:
                raw_error = response.json()
                error_payload = raw_error.get("error", {}) if isinstance(raw_error, dict) else {}
                if not isinstance(error_payload, dict):
                    error_payload = {}
            except (ValueError, AttributeError, TypeError):
                error_payload = {}
            google_status = str(error_payload.get("status", "")).upper()
            raw_google_message = str(error_payload.get("message", ""))
            google_message = raw_google_message.casefold()
            safe_message = re.sub(r"(?i)(key|token|authorization|bearer)\s*[:=]?\s*\S+|https?://\S+", "[redacted]", raw_google_message)[:240]
            logger.warning("google_places_ratings provider_error http_status=%d api_status=%s message=%s", response.status_code, google_status or "none", safe_message or "none")
            if response.status_code == 401 or google_status == "API_KEY_INVALID" or "api key not valid" in google_message or "invalid api key" in google_message:
                raise GoogleRatingError("Google Places rejected the backend key. Verify GOOGLE_MAPS_API_KEY and its restrictions.", 503, "invalid_key")
            if response.status_code == 429 or "quota" in google_status or "quota" in google_message or "rate" in google_message:
                transient_limit = "rate limit" in google_message or "too many requests" in google_message
                is_quota = "quota" in google_status or "quota" in google_message or (google_status == "RESOURCE_EXHAUSTED" and not transient_limit)
                code = "quota_exceeded" if is_quota else "rate_limited"
                message = "Google Places rating quota was exhausted. Check the project's Places quota and billing." if is_quota else "Google Places rate limited the ratings lookup. Retry after a short delay."
                
                # Mark quota as exhausted if confirmed
                if is_quota:
                    _mark_quota_exhausted()
                
                raise GoogleRatingError(message, 503, code)
            if "billing" in google_message:
                raise GoogleRatingError("Google Places billing is not active for this project. Check billing before retrying.", 503, "billing_error")
            if google_status in {"SERVICE_DISABLED", "API_DISABLED"} or "has not been used" in google_message or "not enabled" in google_message:
                raise GoogleRatingError("Places API (New) is not enabled for this Google Cloud project. Enable it and retry.", 503, "api_disabled")
            raise GoogleRatingError("Google Places denied the request. Check Places API (New), billing, and key restrictions for this backend.", 503, "permission_denied")
        if response.status_code == 400:
            try:
                raw_error = response.json()
                error_payload = raw_error.get("error", {}) if isinstance(raw_error, dict) else {}
                message = str(error_payload.get("message", "")).casefold() if isinstance(error_payload, dict) else ""
            except (ValueError, AttributeError, TypeError):
                message = ""
            if "field mask" in message or "fieldmask" in message:
                raise GoogleRatingError("Google Places rejected the field mask. Review the requested Places API (New) fields.", 502, "invalid_field_mask")
            raise GoogleRatingError("Google Places rejected the rating search parameters.", 502, "invalid_request")
        if response.status_code >= 500:
            logger.warning("google_places_ratings provider_error http_status=%d api_status=none message=provider_unavailable", response.status_code)
            raise GoogleRatingError("Google Places ratings are temporarily unavailable.", 503)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise GoogleRatingError("Google Places returned an invalid rating response.", 502, "invalid_response")
        results = payload.get("places", [])
        if not isinstance(results, list):
            raise GoogleRatingError("Google Places returned an invalid rating response.", 502, "invalid_response")
    except GoogleRatingError:
        raise
    except httpx.TimeoutException as exc:
        logger.warning("Google Places rating lookup timed out")
        raise GoogleRatingError("Google Places rating lookup timed out.") from exc
    except httpx.HTTPStatusError as exc:
        logger.warning("Google Places rating lookup returned HTTP %s", exc.response.status_code)
        raise GoogleRatingError("Google Places rejected the rating request.", 502) from exc
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        logger.warning("Google Places rating response unavailable or malformed (%s)", type(exc).__name__)
        raise GoogleRatingError("Google Places ratings are temporarily unavailable.") from exc

    matches: list[tuple[float, float, dict[str, Any]]] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        normalized = normalize_matching_result(candidate, item)
        if normalized is None:
            continue
        location = item.get("location") or {}
        distance = _distance_km(float(candidate["latitude"]), float(candidate["longitude"]), float(location["latitude"]), float(location["longitude"]))
        matches.append((_match_score(candidate, item), distance, normalized))
    matches.sort(key=lambda row: (-row[0], row[1], str(row[2].get("google_place_id"))))
    if not matches:
        return None
    if len(matches) > 1:
        first, second = matches[0], matches[1]
        # If two similarly named places are effectively equidistant, do not
        # attach one city's rating to a different city record.
        if first[0] - second[0] < 0.08 and abs(first[1] - second[1]) < 5.0:
            logger.info("Google Places rating match was ambiguous for a destination candidate")
            return None
    return matches[0][2]


def _cache_key(candidate: dict[str, Any]) -> tuple:
    try:
        lat, lon = round(float(candidate["latitude"]), 3), round(float(candidate["longitude"]), 3)
    except (KeyError, TypeError, ValueError):
        lat = lon = None
    return (_text(candidate.get("name")), _text(candidate.get("region")), lat, lon)


def clear_rating_cache() -> None:
    """Clear the process-local cache (also used to isolate tests)."""
    with _cache_lock:
        _rating_cache.clear()


def _is_quota_exhausted() -> bool:
    """Check if today's daily quota is exhausted and hasn't been reset."""
    global _quota_exhausted_today, _quota_reset_at
    now = time.monotonic()
    with _quota_exhaustion_lock:
        if _quota_reset_at > 0 and now >= _quota_reset_at:
            # Reset flag at next UTC midnight (or after configured TTL)
            _quota_exhausted_today = False
            _quota_reset_at = 0.0
        return _quota_exhausted_today


def _mark_quota_exhausted() -> None:
    """Mark quota as exhausted for the day; reset it at midnight UTC."""
    global _quota_exhausted_today, _quota_reset_at
    with _quota_exhaustion_lock:
        _quota_exhausted_today = True
        # Set reset to tomorrow at UTC midnight
        import datetime
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        tomorrow_midnight = (now_utc + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        _quota_reset_at = time.monotonic() + (tomorrow_midnight - now_utc).total_seconds()
        logger.warning("google_places_ratings quota_exhausted=true reset_at_utc_midnight")


def clear_rating_cache() -> None:
    """Clear the process-local cache (also used to isolate tests)."""
    with _cache_lock:
        _rating_cache.clear()


def _cached_rating(candidate: dict[str, Any]) -> dict[str, Any] | None:
    now = time.monotonic()
    key = _cache_key(candidate)
    with _cache_lock:
        cached = _rating_cache.get(key)
        if cached is None:
            return None
        expires_at, value = cached
        if expires_at <= now:
            _rating_cache.pop(key, None)
            return None
        _rating_cache.move_to_end(key)
        return dict(value)


def _store_rating(candidate: dict[str, Any], result: dict[str, Any]) -> None:
    now = time.monotonic()
    key = _cache_key(candidate)
    with _cache_lock:
        _rating_cache[key] = (now + RATING_CACHE_TTL_SECONDS, dict(result))
        _rating_cache.move_to_end(key)
        while len(_rating_cache) > RATING_CACHE_MAX_ENTRIES:
            _rating_cache.popitem(last=False)


async def _throttle_request() -> None:
    global _next_request_at
    now = time.monotonic()
    with _throttle_lock:
        delay = max(0.0, _next_request_at - now)
        _next_request_at = max(now, _next_request_at) + RATING_REQUEST_INTERVAL_SECONDS
    if delay:
        await asyncio.sleep(delay)


async def search_candidate(candidate: dict[str, Any]) -> dict[str, Any] | None:
    """Look up a candidate with positive-result caching and bounded transient retries."""
    cached = _cached_rating(candidate)
    if cached is not None:
        return cached
    for attempt in range(3):
        await _throttle_request()
        try:
            result = await _search_candidate_uncached(candidate)
            if result is not None:
                _store_rating(candidate, result)
            return result
        except GoogleRatingError as exc:
            if exc.diagnostic_code != "rate_limited" or attempt >= 2:
                raise
            await asyncio.sleep(0.25 * (2 ** attempt))
    return None


async def enrich_candidates(candidates: list[dict[str, Any]], *, limit: int = 8, concurrency: int = 4) -> list[str]:
    """Enrich a ranked shortlist in parallel; errors never remove a candidate."""
    configured = configuration_status() == "configured"
    for candidate in candidates:
        candidate.update({"rating": None, "user_rating_count": None, "google_place_id": None,
                          "google_maps_uri": None, "rating_source": "unavailable",
                          "rating_unavailable_reason": "Rating lookup has not been configured." if not configured else "No verified Google match found."})
    if not configured:
        if candidates and limit > 0:
            logger.info("google_places_ratings status=key_missing")
        return ["Google Places ratings are not configured. Set GOOGLE_MAPS_API_KEY in the backend environment."] if candidates and limit > 0 else []
    shortlist = candidates[:max(0, limit)]
    semaphore = asyncio.Semaphore(min(2, max(1, concurrency)))

    async def enrich(candidate: dict[str, Any]):
        async with semaphore:
            return await search_candidate(candidate)

    results = await asyncio.gather(*(enrich(candidate) for candidate in shortlist), return_exceptions=True)
    issues: list[str] = []
    seen_google_place_ids: set[str] = set()
    for candidate, result in zip(shortlist, results):
        if isinstance(result, GoogleRatingError):
            logger.warning("google_places_ratings status=%s", result.diagnostic_code)
            issues.append(str(result))
            candidate["rating_unavailable_reason"] = str(result)
            continue
        if isinstance(result, BaseException):
            logger.error("Google Places rating lookup failed unexpectedly (%s)", type(result).__name__)
            issues.append("Google Places ratings are temporarily unavailable.")
            candidate["rating_unavailable_reason"] = "Google Places ratings are temporarily unavailable."
            continue
        if result:
            google_place_id = result.get("google_place_id")
            # A single Google Place must not be attributed to multiple distinct
            # Geoapify city candidates in the same discovery response.
            if google_place_id and google_place_id in seen_google_place_ids:
                continue
            if google_place_id:
                seen_google_place_ids.add(google_place_id)
            candidate.update(result)
            if result.get("rating") is None:
                candidate["rating_unavailable_reason"] = "The verified Google place does not provide a rating."
        elif configured:
            logger.info("google_places_ratings status=no_match")
            candidate["rating_unavailable_reason"] = "No sufficiently close, unambiguous Google match was found."
    for candidate in candidates[max(0, limit):]:
        if configured:
            candidate["rating_unavailable_reason"] = "Rating lookup was limited to the discovery shortlist."
    return list(dict.fromkeys(issues))
