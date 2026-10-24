"""Foursquare Places rating enrichment for Geoapify-discovered destinations."""
import asyncio
import logging
import re
import time
import threading
from collections import OrderedDict
from datetime import datetime, timezone
from difflib import SequenceMatcher
from math import asin, cos, radians, sin, sqrt
from typing import Any

import httpx
from app.config import settings

logger = logging.getLogger(__name__)
SEARCH_URL = "https://places-api.foursquare.com/places/search"
API_VERSION = "2025-06-17"
FIELDS = "fsq_place_id,name,location,latitude,longitude,categories,rating,stats,website,link"
MAX_MATCH_DISTANCE_KM = 2.0
CACHE_TTL_SECONDS = int(getattr(settings, "FOURSQUARE_RATING_CACHE_TTL_SECONDS", 21600))
_cache: OrderedDict[tuple, tuple[float, dict[str, Any]]] = OrderedDict()
_cache_lock = threading.Lock()
_inflight: dict[tuple, asyncio.Task] = {}

class FoursquareRatingError(Exception):
    def __init__(self, message: str, status_code: int = 503, diagnostic_code: str = "provider_unavailable"):
        super().__init__(message)
        self.status_code, self.diagnostic_code = status_code, diagnostic_code

def configuration_status() -> str:
    return "configured" if (settings.FOURSQUARE_API_KEY or "").strip() else "missing_key"

def _text(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()

def _distance_km(a: float, b: float, c: float, d: float) -> float:
    p1, p2 = radians(a), radians(c)
    x, y = radians(c-a), radians(d-b)
    return 6371 * 2 * asin(sqrt(sin(x/2)**2 + cos(p1)*cos(p2)*sin(y/2)**2))

def normalize_match(candidate: dict[str, Any], item: dict[str, Any]) -> dict[str, Any] | None:
    name = item.get("name")
    fsq_id = item.get("fsq_place_id")
    loc = item.get("location") or {}
    try:
        lat = float(item.get("latitude", loc.get("latitude")))
        lon = float(item.get("longitude", loc.get("longitude")))
        clat, clon = float(candidate["latitude"]), float(candidate["longitude"])
    except (KeyError, TypeError, ValueError):
        return None
    score = SequenceMatcher(None, _text(candidate.get("name")), _text(name)).ratio()
    distance = _distance_km(clat, clon, lat, lon)
    if not fsq_id or not name or score < 0.78 or distance > MAX_MATCH_DISTANCE_KM:
        return None
    rating = item.get("rating")
    if isinstance(rating, bool) or not isinstance(rating, (int, float)) or not 0 <= rating <= 10:
        rating = None
    stats = item.get("stats") or {}
    count = stats.get("total_ratings") if isinstance(stats, dict) else None
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        count = None
    return {"provider":"foursquare", "place_name":name, "rating":rating, "rating_scale":10,
            "review_count":count, "rating_url":item.get("link") or item.get("website"),
            "retrieved_at":datetime.now(timezone.utc).isoformat(), "status":"available" if rating is not None else "rating_unavailable",
            "fsq_place_id":fsq_id, "rating_source":"foursquare", "user_rating_count":count}

async def _lookup(candidate: dict[str, Any]) -> dict[str, Any] | None:
    key = (settings.FOURSQUARE_API_KEY or "").strip()
    if not key:
        raise FoursquareRatingError("Foursquare ratings are not configured on the backend.", 503, "missing_credentials")
    if not candidate.get("name"):
        return None
    params = {"query":candidate["name"], "ll":f"{candidate['latitude']},{candidate['longitude']}", "radius":5000, "limit":10, "fields":FIELDS}
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(max(1, float(settings.FOURSQUARE_TIMEOUT_SECONDS)), connect=4)) as client:
            response = await client.get(SEARCH_URL, params=params, headers={"Authorization":f"Bearer {key}", "X-Places-Api-Version":API_VERSION, "Accept":"application/json"})
        if response.status_code in (401,403):
            raise FoursquareRatingError("Foursquare rejected the backend credentials or access plan.", 503, "invalid_credentials")
        if response.status_code == 404:
            return None
        if response.status_code == 429:
            raise FoursquareRatingError("Foursquare rating quota or rate limit was reached.",503,"quota_exceeded")
        if response.status_code >= 500:
            raise FoursquareRatingError("Foursquare ratings are temporarily unavailable.",503,"provider_unavailable")
        response.raise_for_status()
        payload=response.json()
        results=payload.get("results",[]) if isinstance(payload,dict) else []
        if not isinstance(results,list):
            raise FoursquareRatingError("Foursquare returned an invalid response.",502,"invalid_response")
    except FoursquareRatingError:
        raise
    except httpx.TimeoutException as exc:
        raise FoursquareRatingError("Foursquare rating lookup timed out.",503,"timeout") from exc
    except (httpx.HTTPError,ValueError,TypeError) as exc:
        raise FoursquareRatingError("Foursquare ratings are temporarily unavailable.",503,"provider_unavailable") from exc
    matches=[]
    for item in results:
        if not isinstance(item,dict): continue
        match=normalize_match(candidate,item)
        if match:
            dist=_distance_km(float(candidate["latitude"]),float(candidate["longitude"]),float(item.get("latitude",(item.get("location") or {}).get("latitude"))),float(item.get("longitude",(item.get("location") or {}).get("longitude"))))
            score=SequenceMatcher(None,_text(candidate.get("name")),_text(item.get("name"))).ratio()
            matches.append((score,dist,match))
    matches.sort(key=lambda x:(-x[0],x[1]))
    if not matches: return None
    if len(matches)>1 and matches[0][0]-matches[1][0]<0.05 and abs(matches[0][1]-matches[1][1])<0.1: return None
    return matches[0][2]

def _key(candidate):
    return (_text(candidate.get("name")), round(float(candidate.get("latitude",0)),3),round(float(candidate.get("longitude",0)),3))

def clear_rating_cache():
    with _cache_lock: _cache.clear()

async def search_candidate(candidate):
    ck=_key(candidate); now=time.monotonic()
    with _cache_lock:
        cached=_cache.get(ck)
        if cached and cached[0]>now: return dict(cached[1])
        if cached: _cache.pop(ck,None)
        task=_inflight.get(ck)
        if task is None:
            task=asyncio.create_task(_lookup(candidate)); _inflight[ck]=task
    try:
        result=await task
        if result:
            with _cache_lock:
                _cache[ck]=(time.monotonic()+CACHE_TTL_SECONDS,dict(result))
                while len(_cache)>2000: _cache.popitem(last=False)
        return result
    finally:
        with _cache_lock:
            if _inflight.get(ck) is task: _inflight.pop(ck,None)

async def enrich_candidates(candidates: list[dict[str,Any]], *, limit=8, concurrency=3):
    for c in candidates:
        c.update({"rating":None,"user_rating_count":None,"fsq_place_id":None,"rating_url":None,"rating_source":"unavailable","provider":"foursquare","place_name":None,"rating_scale":10,"review_count":None,"retrieved_at":None,"status":"no_match","rating_unavailable_reason":"No sufficiently close Foursquare match found."})
    if configuration_status()!="configured":
        for c in candidates: c.update(status="missing_credentials",rating_unavailable_reason="Foursquare ratings are not configured.")
        return ["Foursquare ratings are not configured; destinations are shown without ratings."] if candidates and limit else []
    sem=asyncio.Semaphore(max(1,concurrency)); shortlist=candidates[:max(0,limit)]
    async def run(c):
        async with sem: return await search_candidate(c)
    results=await asyncio.gather(*(run(c) for c in shortlist),return_exceptions=True)
    issues=[]; seen=set()
    for c,r in zip(shortlist,results):
        if isinstance(r,BaseException):
            c["status"]=getattr(r,"diagnostic_code","provider_unavailable"); c["rating_unavailable_reason"]=str(r); issues.append(str(r)); continue
        if r is None: continue
        if r["fsq_place_id"] in seen: c.update(status="no_match",rating_unavailable_reason="Foursquare match was already assigned to another discovery result."); continue
        seen.add(r["fsq_place_id"]); c.update(r); c["rating_unavailable_reason"]=None
    return issues
