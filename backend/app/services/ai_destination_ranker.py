"""Evidence-grounded AI ranking for already feasible origin-discovery cities."""
import asyncio
import json
import logging
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, ValidationError

from app.services.gemini import gemini_service
from app.config import settings

logger = logging.getLogger(__name__)


def _safe_diagnostic(value: Any) -> str:
    message = str(value or "")
    message = re.sub(r"(?i)bearer\s+\S+|gsk_[a-z0-9_-]+|sk-[a-z0-9_-]+|https?://\S+", "[redacted]", message)
    message = re.sub(r"(?i)(api[_ -]?key|authorization|token)\s*[:=]\s*\S+", r"\1=[redacted]", message)
    return message.splitlines()[0][:240]

# Current Groq strict JSON Schema support list (checked against Groq docs).
STRICT_JSON_SCHEMA_MODELS = {
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "qwen/qwen3.8-27b",
    "meta-models/muse-spark-open",
}


class CandidateMatchScore(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    destination_id: StrictStr = Field(min_length=1)
    category_relevance_score: StrictInt = Field(ge=0, le=100)
    interest_match_score: StrictInt = Field(ge=0, le=100)
    comfort_suitability_score: StrictInt = Field(ge=0, le=100)
    duration_suitability_score: StrictInt = Field(ge=0, le=100)
    destination_quality_score: StrictInt = Field(ge=0, le=100)
    overall_match_score: StrictInt = Field(ge=0, le=100)
    match_reasons: list[StrictStr] = Field(max_length=4)
    tradeoffs: list[StrictStr] = Field(max_length=4)
    why_visit: StrictStr = Field(min_length=1, max_length=320)
    trip_fit: StrictStr = Field(min_length=1, max_length=320)
    practical_note: StrictStr | None = Field(max_length=240)


class CandidateRanking(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    rankings: list[CandidateMatchScore] = Field(min_length=1)


class AIRankingError(Exception):
    """An AI response was unavailable or could not be trusted for ranking."""


STRICT_RANKING_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "rankings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "destination_id": {"type": "string"},
                    "category_relevance_score": {"type": "integer"},
                    "interest_match_score": {"type": "integer"},
                    "comfort_suitability_score": {"type": "integer"},
                    "duration_suitability_score": {"type": "integer"},
                    "destination_quality_score": {"type": "integer"},
                    "overall_match_score": {"type": "integer"},
                    "match_reasons": {"type": "array", "items": {"type": "string"}},
                    "tradeoffs": {"type": "array", "items": {"type": "string"}},
                    "why_visit": {"type": "string"},
                    "trip_fit": {"type": "string"},
                    "practical_note": {"type": ["string", "null"]},
                },
                "required": [
                    "destination_id", "category_relevance_score", "interest_match_score",
                    "comfort_suitability_score", "duration_suitability_score",
                    "destination_quality_score", "overall_match_score", "match_reasons", "tradeoffs",
                    "why_visit", "trip_fit", "practical_note",
                ],
                "additionalProperties": False,
            },
        },
    },
    "required": ["rankings"],
    "additionalProperties": False,
}


def _candidate_evidence(candidate: dict[str, Any], candidate_index: int) -> dict[str, Any]:
    """Keep the prompt compact by including only fields that affect ranking decisions.
    Use compact sequential IDs to avoid model confusion."""
    costs = candidate.get("costs") or {}
    places = candidate.get("verified_places") or []
    
    # Build concise place evidence
    place_names = []
    for p in places[:8]:  # Limit to top 8 places
        if isinstance(p, dict) and p.get("name"):
            place_names.append(str(p.get("name")))
    
    return {
        "destination_id": f"dest_{candidate_index}",  # Compact, deterministic ID
        "canonical_id": candidate.get("destination_id"),  # Preserve original for backend mapping
        "name": candidate.get("name"),
        "description": candidate.get("description", "")[:200],  # Truncate long descriptions
        "verified_place_names": place_names,
        "distance_from_origin_km": round(candidate.get("distance_km") or 0, 1),
        "google_rating": candidate.get("rating"),
        "estimated_total_cost_inr": round(costs.get("total_estimated_cost") or 0, 0),
    }


def _build_prompt(candidates: list[dict[str, Any]], request: Any) -> str:
    preferences = {
        "starting_location": request.origin_name,
        "budget_inr_hard_limit": request.budget,
        "duration_days": request.days,
        "traveler_count": request.travelers_count,
        "trip_category": request.travel_type,
        "comfort_score_0_to_100": request.comfort_score,
        "additional_interests": request.interests or [],
    }
    evidence = [_candidate_evidence(candidate, i) for i, candidate in enumerate(candidates)]
    
    # Build compact ID reference list
    id_list = ", ".join(f"dest_{i}" for i in range(len(candidates)))
    
    return (
        "Rank only these destinations by match to the user's trip. Use ONLY IDs: " + id_list + ". "
        "Score 0-100 per dimension: category_relevance_score, interest_match_score, comfort_suitability_score, "
        "duration_suitability_score, destination_quality_score. overall_match_score is your holistic judgment. "
        "Return one score per provided destination_id, exactly once. "
        "Provide brief why_visit and trip_fit fields. Reasons must reference only supplied place names or verified data. "
        "No invented prices, weather, travel times, or ratings beyond supplied data. "
        "If explanation cannot be written safely, use empty reasons array; backend will fill from verified fields.\n\n"
        "User preferences and constraints:\n" + json.dumps(preferences, ensure_ascii=False, separators=(",", ":")) +
        "\n\nDestinations (return each ID exactly once):\n" + json.dumps(evidence, ensure_ascii=False, separators=(",", ":"))
    )


def _validate_grounded_text(scores: CandidateMatchScore, candidate: dict[str, Any], request: Any) -> None:
    raw_text = " ".join(scores.match_reasons + scores.tradeoffs + [scores.why_visit, scores.trip_fit, scores.practical_note or ""])
    text = raw_text.casefold()
    forbidden = ("weather", "forecast", "live fare", "exact fare", "travel time", "hours by road", "guaranteed")
    if any(term in text for term in forbidden):
        raise AIRankingError("The ranking explanation included information that was not supplied.")
    if candidate.get("rating") is None and re.search(r"\b\d(?:\.\d)?\s*(?:/5|stars?|rating)\b", text):
        raise AIRankingError("The ranking explanation claimed a rating that is unavailable.")
    supplied_places = {
        str(item.get("name", "")).casefold()
        for item in candidate.get("verified_places", [])
        if isinstance(item, dict) and item.get("name")
    }
    # Do not accept a named landmark that does not occur in the verified-place evidence.
    supplied_place_names = supplied_places | {
        str(candidate.get(key, "")).casefold()
        for key in ("name", "region", "country")
        if candidate.get(key)
    }
    supplied_place_names.update(str(category).casefold() for category in candidate.get("matched_categories", []))
    supplied_place_names.update({"google maps", str(request.origin_name).casefold()})
    supplied_place_names.update(str(interest).casefold() for interest in request.interests or [])
    for phrase in re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b", raw_text):
        normalized_phrase = phrase.casefold()
        words = normalized_phrase.split()
        if words and words[0] in {"visit", "explore", "discover", "verified", "experience", "enjoy", "consider", "see"}:
            normalized_phrase = " ".join(words[1:])
        if normalized_phrase not in supplied_place_names and normalized_phrase not in {"geoapify", "google maps"}:
            raise AIRankingError("The ranking explanation referenced an unverified place name.")
    costs = candidate.get("costs") or {}
    supplied_numbers = {
        float(value) for value in (
            request.budget, request.days, request.travelers_count, request.comfort_score,
            candidate.get("distance_km"), candidate.get("estimated_cost"),
            candidate.get("budget_remaining"), candidate.get("rating"),
            candidate.get("user_rating_count"), *(costs.get(key) for key in (
                "transport_cost", "hotel_cost", "food_cost", "activities_cost",
                "local_transport_cost", "taxes_fees_cost", "emergency_reserve", "total_estimated_cost",
            )),
        )
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    }
    for number in re.findall(r"(?<![A-Za-z])\d[\d,]*(?:\.\d+)?", raw_text):
        try:
            value = float(number.replace(",", ""))
        except ValueError:
            continue
        if value not in supplied_numbers:
            raise AIRankingError("The ranking explanation included an unsupported numeric claim.")
    if not any(str(place.get("name", "")).casefold() in scores.why_visit.casefold()
               for place in candidate.get("verified_places", []) if isinstance(place, dict) and place.get("name")):
        raise AIRankingError("The visit explanation did not use a verified destination highlight.")
    fit_terms = [str(getattr(request, "travel_type", "") or "").casefold()]
    fit_terms.extend(str(value).casefold() for value in getattr(request, "interests", []) or [])
    if not any(term and term in scores.trip_fit.casefold() for term in fit_terms):
        raise AIRankingError("The trip-fit explanation did not use a supplied travel preference.")
    fit_text = scores.trip_fit.casefold()
    if str(getattr(request, "days", "")) not in fit_text or "comfort" not in fit_text or "budget" not in fit_text:
        raise AIRankingError("The trip-fit explanation omitted a current trip setting.")


def _grounded_explanation(candidate: dict[str, Any], request: Any) -> tuple[list[str], list[str]]:
    """Create safe replacement text entirely from verified candidate fields."""
    name = str(candidate.get("name") or "This destination")
    parts = []
    categories = [str(value) for value in candidate.get("matched_categories", []) if value]
    if categories:
        parts.append(f"{name} has verified place categories: {', '.join(categories[:3])}.")
    else:
        parts.append(f"{name} is a verified Indian destination in {candidate.get('region') or 'India'}.")
    cost = (candidate.get("costs") or {}).get("total_estimated_cost", candidate.get("estimated_cost"))
    if isinstance(cost, (int, float)) and not isinstance(cost, bool):
        budget = getattr(request, "budget", None)
        if isinstance(budget, (int, float)) and cost <= budget:
            parts.append("Its planning estimate is within the supplied budget.")
    places = [str(place.get("name")) for place in candidate.get("verified_places", [])
              if isinstance(place, dict) and place.get("name")]
    if places:
        parts.append(f"Verified places include {', '.join(places[:2])}.")
    return parts[:3], []


def _grounded_guidance(candidate: dict[str, Any], request: Any) -> tuple[str, str, str | None]:
    """Build concise destination guidance grounded in verified provider fields and trip settings."""
    places = [place for place in candidate.get("verified_places", []) if isinstance(place, dict) and place.get("name")]
    place_names = [str(place["name"]) for place in places[:3]]
    place_names_str = ", ".join(place_names) if place_names else ""
    
    # Build why_visit using verified place names and categories.
    highlights = []
    for place in places[:2]:
        categories = [str(value) for value in place.get("categories", []) if value]
        highlight = str(place["name"])
        if categories:
            highlight += f" ({', '.join(categories[:1])})"
        highlights.append(highlight)
    
    if highlights:
        why_visit = f"Key places include {', '.join(highlights)} in {candidate.get('name')}."
    elif place_names_str:
        why_visit = f"Verified places in {candidate.get('name')} include {place_names_str}."
    elif candidate.get("description"):
        why_visit = str(candidate["description"])[:320]
    else:
        why_visit = f"Verified destination details for {candidate.get('name')} are limited; check local sources for current activities."
    
    # Build trip_fit using travel type, verified categories, and matching interests.
    trip_type = str(getattr(request, "travel_type", "") or "").casefold()
    matched_categories = [str(c) for c in candidate.get("matched_categories", []) if c]
    fit_parts = []
    
    if trip_type and matched_categories:
        category_str = ", ".join(matched_categories[:2]) if len(matched_categories) > 1 else matched_categories[0]
        fit_parts.append(f"Verified {category_str} places align with your {trip_type} preference.")
    elif trip_type:
        fit_parts.append(f"This destination is tagged for {trip_type} travel.")
    
    # Check if interests match verified place evidence.
    interests = [str(value).strip() for value in getattr(request, "interests", []) or [] if str(value).strip()]
    evidence = " ".join(place_names).casefold()
    if interests:
        matching_interests = [i for i in interests if i.casefold() in evidence]
        if matching_interests:
            fit_parts.append(f"Listed places also match your interest in {matching_interests[0]}.")
    
    trip_fit = " ".join(fit_parts) if fit_parts else f"Destination is feasible for your {trip_type} trip."
    
    # Build practical_note: travel effort and budget context.
    practical = None
    distance = candidate.get("distance_km")
    days = getattr(request, "days", 0)
    
    if isinstance(distance, (int, float)) and distance >= 500:
        practical = f"At {distance:.0f}km straight-line distance, check current routes for travel time."
    elif isinstance(distance, (int, float)) and distance <= 150 and days <= 2:
        practical = f"At {distance:.0f}km, this is nearby; verify routes for day-trip feasibility."
    
    # Add budget context if applicable.
    cost = (candidate.get("costs") or {}).get("total_estimated_cost", candidate.get("estimated_cost"))
    budget = getattr(request, "budget", None)
    if isinstance(cost, (int, float)) and isinstance(budget, (int, float)) and cost <= budget:
        remaining = budget - cost
        if remaining > 0 and not practical:
            practical = f"Estimated cost ₹{cost:,.0f} leaves ₹{remaining:,.0f} for contingencies."
    
    return (why_visit[:320], trip_fit[:320], practical)


def _provider_diagnostic() -> str:
    status = getattr(gemini_service, "_last_http_status", None)
    provider_error = str(getattr(gemini_service, "_last_provider_error", "") or "").casefold()
    if status in (401, 403):
        return "Groq rejected its backend credentials or model permissions. Check GROQ_API_KEY and the project's model access."
    if status == 429:
        return "Groq destination ranking hit a rate or quota limit. Wait and retry, or check the Groq project limits."
    if status == 400:
        return "Groq rejected the configured model or ranking request. Check GROQ_MODEL availability and structured-output support."
    if status in (413, 422) or "token limit" in provider_error or "context length" in provider_error:
        return "Groq could not fit this ranking batch in the model context. Reduce TRIP_AI_RANK_BATCH_SIZE or choose a model with a larger context."
    if status and status >= 500:
        return "Groq is temporarily unavailable. Retry destination discovery."
    if "timed out" in provider_error or "timeout" in provider_error:
        return "Groq destination ranking timed out. Retry destination discovery."
    if "network" in provider_error or "connection" in provider_error:
        return "The backend could not connect to Groq. Check backend network access and retry."
    return "Groq destination ranking failed. Check the backend diagnostic log and retry."


async def _rank_batch(candidates: list[dict[str, Any]], request: Any) -> tuple[list[dict[str, Any]], str, str]:
    """Call Groq for one bounded batch and validate its complete response."""
    if not candidates:
        return [], "not_applicable", "none"
    if not gemini_service.is_available:
        if not getattr(gemini_service, "api_key", None):
            raise AIRankingError("Groq destination ranking is not configured. Set GROQ_API_KEY in the backend environment.")
        raise AIRankingError("No compatible Groq model is available. Check GROQ_MODEL and confirm the model is enabled for this project.")

    model = str(gemini_service._selected_model or "")
    strict_mode = model in STRICT_JSON_SCHEMA_MODELS
    schema = STRICT_RANKING_SCHEMA if strict_mode else None
    prompt = _build_prompt(candidates, request)
    
    # Create mapping from compact IDs to canonical candidates
    id_to_candidate = {f"dest_{i}": candidate for i, candidate in enumerate(candidates)}
    
    def call_chat(prompt_text: str):
        return gemini_service._chat(prompt_text, 1, schema, strict_mode, 2000, request_timeout=30)

    try:
        content, error = await asyncio.wait_for(asyncio.to_thread(call_chat, prompt), timeout=35)
    except asyncio.TimeoutError as exc:
        logger.warning("origin_discovery stage=ranking provider=groq failure_stage=client_timeout exception=TimeoutError model=%s http_status=none", model)
        raise AIRankingError("Groq destination ranking timed out. Retry destination discovery.") from exc
    if error or not content:
        status = getattr(gemini_service, "_last_http_status", None)
        safe_error = _safe_diagnostic(error or "empty response")
        logger.warning("origin_discovery stage=ranking provider=groq failure_stage=provider_request exception=ProviderError model=%s http_status=%s error=%s", model, status if status is not None else "none", safe_error)
        raise AIRankingError(_provider_diagnostic())

    try:
        parsed = CandidateRanking.model_validate_json(content)
    except (ValidationError, ValueError) as exc:
        safe_error = _safe_diagnostic(exc)
        logger.warning("origin_discovery stage=ranking provider=groq failure_stage=schema_validation exception=%s model=%s http_status=%s error=%s", type(exc).__name__, model, getattr(gemini_service, "_last_http_status", None) or "none", safe_error)
        correction = prompt + "\n\nReturn only valid JSON matching the exact schema. Every supplied ID (dest_0, dest_1, etc.) must appear exactly once. No other IDs."
        try:
            retry_content, retry_error = await asyncio.wait_for(asyncio.to_thread(call_chat, correction), timeout=35)
            if retry_error or not retry_content:
                raise ValueError(retry_error or "empty correction response")
            parsed = CandidateRanking.model_validate_json(retry_content)
        except (asyncio.TimeoutError, ValidationError, ValueError) as retry_exc:
            logger.warning("origin_discovery stage=ranking provider=groq failure_stage=corrective_retry exception=%s model=%s http_status=%s", type(retry_exc).__name__, model, getattr(gemini_service, "_last_http_status", None) or "none")
            # Fall back to deterministic ranking; no second retry
            logger.info("origin_discovery stage=ranking_fallback reason=corrective_retry_failed using_deterministic=true")
            raise AIRankingError("Groq returned invalid destination ranking after one corrective retry. Using deterministic ranking.") from retry_exc

    expected = set(id_to_candidate.keys())
    returned = [row.destination_id for row in parsed.rankings]
    if len(returned) != len(set(returned)) or set(returned) != expected:
        logger.warning("origin_discovery stage=ranking provider=groq failure_stage=candidate_id_validation exception=CandidateIDValidationError model=%s http_status=%s returned_ids=%s expected_ids=%s", model, getattr(gemini_service, "_last_http_status", None) or "none", returned, list(expected))
        # Do NOT attempt second retry; use deterministic fallback
        logger.info("origin_discovery stage=ranking_fallback reason=invalid_candidate_ids using_deterministic=true")
        raise AIRankingError("Groq returned invalid destination IDs. Using deterministic ranking.")

    candidate_by_id = id_to_candidate
    for row in parsed.rankings:
        try:
            _validate_grounded_text(row, candidate_by_id[row.destination_id], request)
        except AIRankingError as exc:
            logger.info("origin_discovery stage=ranking explanation=repaired reason=%s", str(exc))
            row.match_reasons, row.tradeoffs = _grounded_explanation(candidate_by_id[row.destination_id], request)
            row.why_visit, row.trip_fit, row.practical_note = _grounded_guidance(candidate_by_id[row.destination_id], request)
        if not row.why_visit or not row.trip_fit:
            row.why_visit, row.trip_fit, row.practical_note = _grounded_guidance(candidate_by_id[row.destination_id], request)

    parsed_by_id = {row.destination_id: row for row in parsed.rankings}
    for candidate in candidates:
        # Map from compact ID back to original candidate
        for compact_id, cand in id_to_candidate.items():
            if cand is candidate:
                row = parsed_by_id[compact_id]
                break
        else:
            continue
        candidate.update({
            "value_score": row.overall_match_score,
            "overall_match_score": row.overall_match_score,
            "category_relevance_score": row.category_relevance_score,
            "interest_match_score": row.interest_match_score,
            "comfort_suitability_score": row.comfort_suitability_score,
            "duration_suitability_score": row.duration_suitability_score,
            "destination_quality_score": row.destination_quality_score,
            "breakdown": {
                "category_relevance": row.category_relevance_score,
                "interest_match": row.interest_match_score,
                "comfort_suitability": row.comfort_suitability_score,
                "duration_suitability": row.duration_suitability_score,
                "destination_quality": row.destination_quality_score,
            },
            "match_reasons": row.match_reasons,
            "tradeoffs": row.tradeoffs,
            "explanation": " ".join(row.match_reasons),
            "why_visit": row.why_visit,
            "trip_fit": row.trip_fit,
            "practical_note": row.practical_note,
        })
    # Rank ties with stable deterministic facts only; no hidden weighted formula.
    # Handle None scores (from fallback) gracefully
    candidates.sort(key=lambda item: (
        -(int(item["overall_match_score"]) if item.get("overall_match_score") is not None else -1),
        float(item["estimated_cost"]),
        -(float(item["rating"]) if item.get("rating") is not None else -1.0),
        str(item["destination_id"]),
    ))
    return candidates, "strict_json_schema" if strict_mode else "json_prompt_validated", model


async def rank_candidates(candidates: list[dict[str, Any]], request: Any) -> tuple[list[dict[str, Any]], str, str]:
    """Rank all feasible candidates sequentially in bounded prompts.

    A failure in any batch rejects the complete AI ranking so callers can use
    one truthful deterministic fallback order without mixed or partial scores.
    """
    if not candidates:
        return [], "not_applicable", "none"
    batch_size = min(max(1, int(settings.TRIP_AI_RANK_BATCH_SIZE)), 20)
    ranked_all: list[dict[str, Any]] = []
    modes: list[str] = []
    selected_models: list[str] = []
    for offset in range(0, len(candidates), batch_size):
        batch = [dict(candidate) for candidate in candidates[offset:offset + batch_size]]
        ranked, mode, model = await _rank_batch(batch, request)
        ranked_all.extend(ranked)
        modes.append(mode)
        selected_models.append(model)
        logger.info("origin_discovery stage=ranking_batch completed=%d total=%d size=%d model=%s", min(offset + len(batch), len(candidates)), len(candidates), len(batch), model)
    ranked_all.sort(key=lambda item: (
        -(int(item["overall_match_score"]) if item.get("overall_match_score") is not None else -1),
        float(item["estimated_cost"]),
        str(item["destination_id"]),
    ))
    # Copy validated fields back only after every batch has succeeded.
    scored_by_id = {item["destination_id"]: item for item in ranked_all}
    for original in candidates:
        original.update(scored_by_id[original["destination_id"]])
    mode = modes[0] if len(set(modes)) == 1 else "mixed_validated_batches"
    if len(modes) > 1:
        mode = f"batched_{mode}"
    return ranked_all, mode, selected_models[0] if len(set(selected_models)) == 1 else "multiple"


def fallback_rank_candidates(candidates: list[dict[str, Any]], request: Any | None = None) -> list[dict[str, Any]]:
    """Deterministically rank verified quality, user fit, distance, and affordability."""
    for candidate in candidates:
        if request is not None:
            candidate["why_visit"], candidate["trip_fit"], candidate["practical_note"] = _grounded_guidance(candidate, request)
        candidate.update({
            "value_score": None,
            "overall_match_score": None,
            "category_relevance_score": None,
            "interest_match_score": None,
            "comfort_suitability_score": None,
            "duration_suitability_score": None,
            "destination_quality_score": None,
            "breakdown": {},
            "match_reasons": [],
            "tradeoffs": [],
            "explanation": "Shown in fallback order using verified destination details and trip fit; no AI match score was assigned.",
        })
    requested_category = str(getattr(request, "travel_type", "") or "").casefold()
    interests = {str(value).casefold() for value in getattr(request, "interests", []) or []}
    days = max(1, int(getattr(request, "days", 1) or 1))
    def fallback_key(item: dict[str, Any]):
        categories = {str(value).casefold() for value in item.get("matched_categories", [])}
        places = item.get("verified_places") or []
        evidence_text = " ".join(
            str(place.get("name", "")) + " " + " ".join(place.get("categories") or [])
            for place in places if isinstance(place, dict)
        ).casefold()
        category_fit = int(requested_category in categories) if requested_category else 0
        interest_fit = sum(1 for interest in interests if interest and interest in evidence_text)
        quality = min(4, len({str(place.get("place_id") or place.get("name", "")).casefold() for place in places if isinstance(place, dict) and place.get("name")}))
        distance = max(0.0, float(item.get("distance_km") or 0))
        duration_fit = 1 if distance <= 250 * days else 0
        budget = max(1.0, float(item.get("budget_limit") or 1))
        cost = max(0.0, float(item.get("estimated_cost") or budget))
        affordability = (budget - cost) / budget
        return (-category_fit, -interest_fit, -quality, -duration_fit, -affordability, distance, str(item["destination_id"]))
    return sorted(candidates, key=fallback_key)
