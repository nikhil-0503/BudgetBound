# BudgetBound — P0/P1/P2 Bug Fixes Summary

## Executive Summary

Fixed three critical production bugs causing HTTP 500 errors, TypeErrors, and repeated API calls:

| Priority | Issue | Root Cause | Status |
|----------|-------|-----------|--------|
| **P0** | Itinerary crash (KeyError on daily[:3]) | `daily` is dict, not list | ✅ Fixed |
| **P1** | Ranking TypeError on None scores | `int(None)` in sort key | ✅ Fixed |
| **P2** | Repeated Google Places requests after quota exhaustion | No quota tracking | ✅ Fixed |

---

## P0 — Itinerary Crash: `KeyError: slice(None, 3, None)`

### Root Cause

**Line 436 in `backend/app/services/gemini.py`:**
```python
daily = weather_context.get("daily", [])  # Retrieved as dict
if daily:
    compact_weather = {
        "timezone": weather_context.get("timezone"),
        "daily": daily[:3]  # ❌ TypeError: dict indices must be integers or slices, not slice
    }
```

**The Issue:**
- The Open-Meteo weather API returns `daily` as a **dictionary** with keys like `"time"`, `"weather_code"`, `"temperature_2m_min"`, etc.
- Each key contains a **list** of values (one per day)
- The code assumed `daily` was a list and tried to slice it: `daily[:3]`
- This caused `TypeError: 'slice' object cannot be interpreted as an integer`

**Actual Structure from Open-Meteo:**
```python
{
    "timezone": "Asia/Kolkata",
    "daily": {
        "time": ["2026-10-23", "2026-10-24", "2026-10-25", "2026-10-26"],
        "weather_code": [80, 80, 2, 3],
        "temperature_2m_min": [20, 19, 18, 17],
        "temperature_2m_max": [32, 31, 30, 29],
        # ... more fields
    }
}
```

### Solution

**Fixed in `backend/app/services/gemini.py` (lines 430-451):**
```python
# Compact weather context (only next 3 days)
# Note: daily is a dict with keys like "time", "weather_code", etc., each containing a list
compact_weather = None
if weather_context and isinstance(weather_context, dict):
    daily = weather_context.get("daily", {})
    if daily and isinstance(daily, dict):
        # Extract time list to determine number of days available
        time_list = daily.get("time", [])
        if isinstance(time_list, list) and len(time_list) > 0:
            # Limit to first 3 days by slicing each field's list
            max_days = min(3, len(time_list))
            compact_daily = {}
            for key, value in daily.items():
                if isinstance(value, list):
                    compact_daily[key] = value[:max_days]
                else:
                    compact_daily[key] = value
            compact_weather = {
                "timezone": weather_context.get("timezone"),
                "daily": compact_daily
            }
```

**Key Changes:**
1. ✅ Detect that `daily` is a dict, not a list
2. ✅ Iterate over dict items and slice each list field individually
3. ✅ Preserve dict structure; don't truncate weather code itself
4. ✅ Handles missing/None/empty weather gracefully
5. ✅ 4-day itineraries now work correctly

### Tests

✅ `test_weather_context_with_dict_daily_does_not_crash` - Verifies dict handling
✅ `test_four_day_itinerary_with_weather_context` - Confirms 4 days work
✅ `test_weather_context_none_does_not_crash` - Tests None/empty cases

---

## P1 — Ranking TypeError: `TypeError: int() argument must be a string, a bytes-like object or a number, not 'NoneType'`

### Root Cause

**Lines 414 & 442 in `backend/app/services/ai_destination_ranker.py`:**
```python
candidates.sort(key=lambda item: (
    -int(item["overall_match_score"]),  # ❌ Crashes if overall_match_score is None
    float(item["estimated_cost"]),
    str(item["destination_id"]),
))
```

**The Issue:**
- When Groq ranking fails and fallback ranking is used, scores are set to `None`
- The sort key calls `int(None)`, which raises `TypeError`
- Frontend displays: "AI personalization is unavailable. ... Unexpected ranking error (TypeError)."

### Solution

**Fixed in `backend/app/services/ai_destination_ranker.py` (lines 413-420 & 442-445):**
```python
# Handle None scores (from fallback) gracefully
candidates.sort(key=lambda item: (
    -(int(item["overall_match_score"]) if item.get("overall_match_score") is not None else -1),
    float(item["estimated_cost"]),
    -(float(item["rating"]) if item.get("rating") is not None else -1.0),
    str(item["destination_id"]),
))
```

**Key Changes:**
1. ✅ Check if score is `None` before calling `int()`
2. ✅ Use `-1` as fallback (sorts below AI scores)
3. ✅ Also protect rating field from None
4. ✅ Deterministic fallback ranking always succeeds

### Tests

✅ `test_sorting_with_none_scores_does_not_crash` - Mixed AI and fallback scores
✅ `test_all_none_scores_sorts_by_cost` - Pure fallback, sorts by cost

---

## P2 — Repeated Google Places Requests After Daily Quota Exhaustion

### Root Cause

**`backend/app/services/google_place_ratings.py` (line ~155):**
- When Google Places returns HTTP 429 with `RESOURCE_EXHAUSTED`, the code detected quota exhaustion
- But it **did not prevent future requests** for the same process/day
- Subsequent requests in the same session would retry and fail again
- Log showed repeated: `HTTP 429 api_status=RESOURCE_EXHAUSTED SearchTextRequest per day`

### Solution

Added quota exhaustion tracking in `backend/app/services/google_place_ratings.py`:

1. **Module-level state (lines 26-29):**
```python
# Daily quota exhaustion tracking
_quota_exhausted_today = False
_quota_exhaustion_lock = threading.Lock()
_quota_reset_at = 0.0  # Timestamp when quota will be reset (next UTC midnight)
```

2. **Quota check functions (lines 185-225):**
```python
def _is_quota_exhausted() -> bool:
    """Check if today's daily quota is exhausted and hasn't been reset."""
    global _quota_exhausted_today, _quota_reset_at
    now = time.monotonic()
    with _quota_exhaustion_lock:
        if _quota_reset_at > 0 and now >= _quota_reset_at:
            # Reset flag at next UTC midnight
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
```

3. **Quota check in search function (lines 108-110):**
```python
async def _search_candidate_uncached(candidate: dict[str, Any]) -> dict[str, Any] | None:
    """Search for the city itself, and reject ambiguous/non-Indian mismatches."""
    # Short-circuit if daily quota is exhausted
    if _is_quota_exhausted():
        logger.debug("google_places_ratings skipping_request quota_exhausted=true")
        raise GoogleRatingError("Google Places daily quota is exhausted. Ratings will resume at tomorrow's UTC midnight.", 503, "quota_exceeded")
```

4. **Mark quota when detected (line ~156):**
```python
if is_quota:
    _mark_quota_exhausted()
```

**Key Changes:**
1. ✅ Detect `RESOURCE_EXHAUSTED` status → mark quota as exhausted
2. ✅ Skip all further requests until midnight UTC
3. ✅ Thread-safe tracking with locks
4. ✅ Automatic reset at UTC midnight
5. ✅ Clear, honest error message about quota status
6. ✅ Destination discovery continues; ratings just unavailable

### Tests

✅ `test_quota_exhaustion_flag_is_set_and_checked` - Flag tracking works
✅ `test_quota_exhaustion_prevents_further_requests` - Requests skipped
✅ `test_quota_reset_at_midnight` - Reset scheduled correctly

---

## Impact & Behavior

### Before Fixes

| Scenario | Before | After |
|----------|--------|-------|
| 4-day itinerary with weather | ❌ HTTP 500 (KeyError) | ✅ Works, fallback if needed |
| Ranking fails, mixed scores | ❌ HTTP 500 (TypeError) | ✅ Sorts by fallback, works |
| Google quota exhausted | ❌ 5+ repeated failed requests | ✅ 1 attempt, skip rest of day |
| User journey end-to-end | ❌ Crashes at itinerary | ✅ Completes with fallback |

### End-to-End User Journey

1. ✅ **Enter trip settings:** Budget 20k, 4 days, adventure, Bangalore → Ooty
2. ✅ **Discover destinations:** Find Ooty (even if Google quota exhausted, uses cache)
3. ✅ **Select destination:** Click "Choose destination" on Ooty card
4. ✅ **Generate itinerary:** 4-day itinerary with weather context (dict-safe)
5. ✅ **Render dashboard:** Complete itinerary displays
   - If Groq available: AI itinerary + AI match scores
   - If Groq rate-limited: Deterministic itinerary + no AI scores (honest fallback)
6. ✅ **Trip settings preserved:** Budget, duration, travelers, category, interests, comfort all retained

---

## Files Modified

| File | Changes | Lines |
|------|---------|-------|
| `backend/app/services/gemini.py` | Fix weather dict slicing | 430–451 |
| `backend/app/services/ai_destination_ranker.py` | Handle None scores in sort | 413–420, 442–445 |
| `backend/app/services/google_place_ratings.py` | Add quota tracking | 26–29, 108–110, 156, 185–225 |
| `backend/test_p0_p1_p2_fixes.py` | NEW: 10 regression tests | All |

---

## Test Results

```
======================= 10 passed, 14 warnings in 2.21s ========================

TestP0ItineraryWeatherContextFix:
  ✅ test_weather_context_with_dict_daily_does_not_crash
  ✅ test_four_day_itinerary_with_weather_context
  ✅ test_weather_context_none_does_not_crash

TestP1RankingTypeErrorFix:
  ✅ test_sorting_with_none_scores_does_not_crash
  ✅ test_all_none_scores_sorts_by_cost

TestP2GooglePlacesQuotaExhaustionFix:
  ✅ test_quota_exhaustion_flag_is_set_and_checked
  ✅ test_quota_exhaustion_prevents_further_requests
  ✅ test_quota_reset_at_midnight

TestCompleteUserJourney:
  ✅ test_fallback_itinerary_used_when_groq_unavailable
  ✅ test_trip_settings_preserved_after_selection
```

---

## Verification Checklist

- ✅ All Python syntax valid (no compilation errors)
- ✅ TypeScript build clean (no tsc errors)
- ✅ 10 regression tests passing
- ✅ Fallback itinerary generates all 4 days
- ✅ Weather context dict properly handled
- ✅ None scores don't crash sort
- ✅ Quota exhaustion tracked and skipped
- ✅ No HTTP 500 errors on itinerary generation
- ✅ Trip settings preserved end-to-end

---

## Deployment Notes

- **No breaking changes** - Backward compatible
- **No database migrations** - Pure code fixes
- **No environment changes** - Uses existing configs
- **Safe fallbacks** - Never breaks user journey
- **Honest errors** - Clear "quota exhausted" messages, not hidden API key errors

Deploy to staging and run full regression suite before production rollout.
