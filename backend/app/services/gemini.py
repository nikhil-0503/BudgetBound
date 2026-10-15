import os
import json
import logging
import httpx
import re
import time
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
from datetime import datetime

# Load .env before reading env vars (singleton is created at import time)
load_dotenv(override=True)  # Force reload from .env file

logger = logging.getLogger(__name__)

# Import model discovery service
from app.services.groq_model_discovery import get_available_model

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Capture at module load
FALLBACK_MODEL_OVERRIDE = os.getenv("GROQ_MODEL")  # Allow manual override via env var
GROQ_MODEL = FALLBACK_MODEL_OVERRIDE or "llama-3.3-70b-versatile"

# These cover common Indian trip destinations immediately.  Other places are
# resolved through Nominatim below; importantly, we never fabricate a point
# from the spelling of a destination.
KNOWN_DESTINATION_COORDINATES = {
    "agra": (27.1767, 78.0081), "amritsar": (31.6340, 74.8723),
    "bangalore": (12.9716, 77.5946), "bengaluru": (12.9716, 77.5946),
    "bhopal": (23.2599, 77.4126), "chennai": (13.0827, 80.2707),
    "coorg": (12.3375, 75.8069), "darjeeling": (27.0410, 88.2663),
    "delhi": (28.6139, 77.2090), "goa": (15.2993, 74.1240),
    "hyderabad": (17.3850, 78.4867), "jaipur": (26.9124, 75.7873),
    "jaisalmer": (26.9157, 70.9083), "jodhpur": (26.2389, 73.0243),
    "kochi": (9.9312, 76.2673), "kozhikode": (11.2588, 75.7804),
    "leh": (34.1526, 77.5771), "manali": (32.2432, 77.1892),
    "mumbai": (19.0760, 72.8777), "mysore": (12.2958, 76.6394),
    "mysuru": (12.2958, 76.6394), "nainital": (29.3803, 79.4636),
    "ooty": (11.4102, 76.6950), "puducherry": (11.9416, 79.8083),
    "pondicherry": (11.9416, 79.8083), "rishikesh": (30.0869, 78.2676),
    "shimla": (31.1048, 77.1734), "srinagar": (34.0837, 74.7973),
    "udaipur": (24.5854, 73.7125), "varanasi": (25.3176, 82.9739),
}


class GroqTravelService:
    """
    Groq-powered travel itinerary generator with automatic model discovery.
    Falls back gracefully to template generation if the API key is absent or the call fails.
    
    Features:
    - Automatic model discovery and selection
    - Bounded retry logic for transient failures
    - Detection of token-limit exhaustion and empty responses
    - Comprehensive diagnostic logging
    - Safe error handling and observability
    """
    
    # Class-level cache for initialization diagnostics
    _init_logged = False
    _model_cache: Optional[Tuple[Optional[str], Optional[str]]] = None  # (model_id, reason)
    _last_model_check = 0
    _model_check_interval = 300  # Re-check model availability every 5 minutes

    def __init__(self):
        self.api_key = GROQ_API_KEY
        self._fallback_reason = None
        self._selected_model = None
        self._model_discovery_error = None
        self._request_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "token_exhaustion_count": 0,
            "empty_response_count": 0,
            "fallback_activations": 0
        }
        
        # Discover model on first init
        self._refresh_model_selection()
        
        # Log initialization ONCE per process
        if not GroqTravelService._init_logged:
            GroqTravelService._init_logged = True
            import sys
            
            if self.api_key:
                key_preview = self.api_key[:10] + "..." if len(self.api_key) > 10 else "***"
                
                if self._selected_model:
                    msg = f"✓ Groq AI service initialized: model={self._selected_model}, key={key_preview}"
                    logger.info(msg)
                    print(f"DEBUG: {msg}", file=sys.stderr)
                else:
                    reason = self._model_discovery_error or "Model discovery failed"
                    msg = f"⚠ Groq API key configured but no model available: {reason}. Using fallback generator."
                    logger.warning(msg)
                    print(f"DEBUG: {msg}", file=sys.stderr)
            else:
                msg = "✗ Groq API key not configured - using fallback generator for all requests"
                logger.warning(msg)
                print(f"DEBUG: {msg}", file=sys.stderr)

    def _refresh_model_selection(self):
        """Refresh model selection with caching."""
        now = time.time()
        
        # Use cached model if available and within TTL
        if GroqTravelService._model_cache and (now - GroqTravelService._last_model_check) < GroqTravelService._model_check_interval:
            self._selected_model, self._model_discovery_error = GroqTravelService._model_cache
            return
        
        # Check for manual override
        if FALLBACK_MODEL_OVERRIDE:
            logger.info(f"Using manually configured model: {FALLBACK_MODEL_OVERRIDE}")
            self._selected_model = FALLBACK_MODEL_OVERRIDE
            self._model_discovery_error = None
            GroqTravelService._model_cache = (self._selected_model, None)
            GroqTravelService._last_model_check = now
            return
        
        # Discover available models
        model_id, discovery_error = get_available_model()
        self._selected_model = model_id
        self._model_discovery_error = discovery_error
        GroqTravelService._model_cache = (model_id, discovery_error)
        GroqTravelService._last_model_check = now

    @property
    def is_available(self) -> bool:
        """Check if Groq service is available (has API key and selected model)"""
        if not self.api_key:
            if not self._fallback_reason:
                self._fallback_reason = "GROQ_API_KEY not configured"
            return False
        
        if not self._selected_model:
            if not self._fallback_reason:
                self._fallback_reason = self._model_discovery_error or "No compatible Groq model available"
            return False
        
        return True

    def _chat(
        self,
        prompt: str,
        max_retries: int = 3,
        response_schema: Optional[dict] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Send a single-turn chat message with automatic retries and model discovery.
        
        Args:
            prompt: The user prompt
            max_retries: Number of retries on failure
            response_schema: Optional JSON schema for structured output (Groq json_schema mode)
        
        Returns:
            Tuple of (content, error_reason) where error_reason is non-None if request failed
        """
        self._request_stats["total_requests"] += 1
        
        if not self.is_available:
            error = f"Groq not available: {self._fallback_reason}"
            self._request_stats["failed_requests"] += 1
            return None, error
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        # First attempt: try with schema if provided
        use_schema = response_schema is not None
        schema_unsupported = False
        
        for attempt in range(max_retries):
            payload = {
                "model": self._selected_model,
                "messages": [{
                    "role": "user",
                    "content": prompt
                }],
            }
            
            # Add structured output schema if provided and model supports it
            if use_schema and not schema_unsupported:
                payload["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "structured_response",
                        "schema": response_schema,
                        "strict": True  # Enforce strict schema validation
                    }
                }
                logger.debug("Using strict JSON schema mode for Groq API")
            
            try:
                with httpx.Client(timeout=60.0) as client:
                    response = client.post(
                        GROQ_API_URL,
                        headers=headers,
                        json=payload,
                    )
                    
                    if response.status_code != 200:
                        error_msg = f"HTTP {response.status_code}"
                        try:
                            error_data = response.json()
                            if "error" in error_data and "message" in error_data["error"]:
                                error_msg = error_data["error"]["message"]
                        except:
                            pass
                        
                        logger.warning(f"Groq API error (attempt {attempt + 1}/{max_retries}): {error_msg}")
                        
                        # Handle HTTP 429 (rate limit) - always retry with backoff
                        if response.status_code == 429:
                            logger.warning(f"Rate limited (HTTP 429). Waiting before retry...")
                            if attempt < max_retries - 1:
                                # Longer backoff for rate limits
                                wait_time = 1.0 * (attempt + 1)
                                logger.info(f"Retrying Groq API in {wait_time}s...")
                                time.sleep(wait_time)
                                continue
                            else:
                                self._request_stats["failed_requests"] += 1
                                return None, error_msg
                        
                        # If model doesn't support json_schema, retry without schema
                        if use_schema and "json_schema" in error_msg.lower() and not schema_unsupported:
                            logger.info(f"Model {self._selected_model} does not support json_schema, retrying without schema...")
                            schema_unsupported = True
                            if attempt < max_retries - 1:
                                continue
                            else:
                                # Last attempt failed, retry without schema
                                use_schema = False
                                continue
                        
                        # Don't retry model decommissioning errors
                        if "decommissioned" in error_msg.lower():
                            self._request_stats["failed_requests"] += 1
                            return None, error_msg
                        
                        if attempt < max_retries - 1:
                            wait_time = 0.5 * (attempt + 1)
                            logger.info(f"Retrying Groq API in {wait_time}s...")
                            time.sleep(wait_time)
                            continue
                        
                        self._request_stats["failed_requests"] += 1
                        return None, error_msg
                    
                    response_json = response.json()
                    finish_reason = response_json.get("choices", [{}])[0].get("finish_reason")
                    content = response_json.get("choices", [{}])[0].get("message", {}).get("content", "")
                    usage = response_json.get("usage", {})
                    
                    # Log token usage and completion details
                    logger.debug(
                        f"Groq response: model={self._selected_model}, "
                        f"finish_reason={finish_reason}, "
                        f"content_len={len(content) if content else 0}, "
                        f"tokens_used={usage.get('total_tokens', 0)}, "
                        f"schema_mode={'yes' if payload.get('response_format') else 'no'}"
                    )
                    
                    # Detect token exhaustion
                    if finish_reason == "length":
                        self._request_stats["token_exhaustion_count"] += 1
                        error_msg = "Token limit reached: model response incomplete"
                        logger.warning(error_msg)
                        self._request_stats["failed_requests"] += 1
                        return None, error_msg
                    
                    # Empty content rejection
                    if not content or len(content.strip()) == 0:
                        self._request_stats["empty_response_count"] += 1
                        logger.warning(
                            f"Groq returned empty content (finish_reason={finish_reason}). "
                            f"Tokens used: {usage.get('total_tokens', 0)}"
                        )
                        
                        if attempt < max_retries - 1:
                            wait_time = 0.5 * (attempt + 1)
                            logger.info(f"Retrying after empty response...")
                            time.sleep(wait_time)
                            continue
                        
                        self._request_stats["failed_requests"] += 1
                        return None, "Groq returned empty response"
                    
                    # Success
                    self._request_stats["successful_requests"] += 1
                    logger.debug(f"Groq request successful on attempt {attempt + 1}")
                    return content, None
            
            except (httpx.ConnectError, httpx.NetworkError, httpx.RemoteProtocolError, OSError) as err:
                if attempt < max_retries - 1:
                    wait_time = 0.5 * (attempt + 1)
                    logger.info(f"Retrying Groq API after network error (attempt {attempt + 1}/{max_retries}): {err}")
                    time.sleep(wait_time)
                    continue
                
                self._request_stats["failed_requests"] += 1
                return None, f"Network error: {str(err)}"
            
            except Exception as e:
                logger.exception("Unexpected error during Groq API call")
                if attempt < max_retries - 1:
                    wait_time = 0.5 * (attempt + 1)
                    time.sleep(wait_time)
                    continue
                
                self._request_stats["failed_requests"] += 1
                return None, f"Unexpected error: {str(e)}"
        
        self._request_stats["failed_requests"] += 1
        return None, f"Failed after {max_retries} attempts"

    def generate_itinerary(
        self,
        destination_name: str,
        state: str,
        category: str,
        attractions: List[str],
        travel_type: str,
        days: int,
        comfort_score: int,
        avg_food_cost: float,
        avg_activity_cost: float,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Ask the LLM to generate a day-by-day itinerary in JSON format.
        Returns None if unavailable or on any error so the caller can fall back.
        """
        if not self.is_available:
            return None

        comfort_label = (
            "budget traveler (prefer free / cheap activities)"
            if comfort_score < 30
            else "mid-range comfort (mix of paid attractions and free sights)"
            if comfort_score <= 70
            else "luxury traveler (premium experiences, fine dining, private tours)"
        )

        attractions_str = ", ".join(attractions[:10]) if attractions else "local landmarks"

        prompt = f"""You are a master Indian travel guide. Generate a vivid, detailed, day-by-day itinerary for the following trip.

Trip details:
- Destination: {destination_name}, {state}
- Destination category: {category}
- Travel type preference: {travel_type}
- Duration: EXACTLY {days} days
- Comfort level: {comfort_label} (score {comfort_score}/100)
- Known attractions: {attractions_str}
- Average food cost per meal: INR {avg_food_cost:.0f}
- Average activity/entry cost: INR {avg_activity_cost:.0f}

Rules:
1. Generate EXACTLY {days} days in the array (day_number 1 through {days}).
2. Day 1 Morning must start with arrival/check-in.
3. The last day (Day {days}) must end with check-out and departure back home.
4. Every activity title MUST be unique, vivid, and action-oriented - tailored to {travel_type} (e.g. "Sunrise photography trek", "Sampling local thali at heritage cafe"). NEVER repeat generic titles like "Sightseeing".
5. Use known attractions naturally across the days.
6. Provide estimated cost in INR for each activity (0 for free activities).

Return ONLY a valid JSON array matching this exact structure with {days} days (no conversational text):
[
  {{
    "day_number": 1,
    "description": "Engaging 1-sentence day summary...",
    "activities": [
      {{"time": "Morning", "title": "Arrival in {destination_name} & Hotel Check-in", "cost": 0.0}},
      {{"time": "Afternoon", "title": "Specific afternoon activity name", "cost": 300.0}},
      {{"time": "Evening", "title": "Specific evening activity name", "cost": 150.0}}
    ]
  }}
]"""

        try:
            raw = self._chat(prompt).strip()

            # Helper for robust JSON array extraction
            def extract_json_array(text: str) -> Optional[List[Any]]:
                text = text.strip()
                if "```" in text:
                    for part in text.split("```"):
                        part_str = part.strip()
                        if part_str.startswith("json"):
                            part_str = part_str[4:].strip()
                        if part_str.startswith("[") and part_str.endswith("]"):
                            try:
                                res = json.loads(part_str)
                                if isinstance(res, list):
                                    return res
                            except Exception:
                                pass
                start_idx = text.find("[")
                end_idx = text.rfind("]")
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    try:
                        res = json.loads(text[start_idx:end_idx + 1])
                        if isinstance(res, list):
                            return res
                    except Exception:
                        pass
                return None

            itinerary = extract_json_array(raw)

            if not isinstance(itinerary, list) or len(itinerary) == 0:
                logger.warning("LLM output could not be parsed as a valid JSON array. Falling back.")
                return None

            # Adjust days count if slightly mismatched
            if len(itinerary) > days:
                itinerary = itinerary[:days]

            # Sanitise cost fields to float and validate day structure
            for idx, day in enumerate(itinerary, start=1):
                day["day_number"] = idx
                if not isinstance(day.get("activities"), list):
                    day["activities"] = []
                for act in day.get("activities", []):
                    try:
                        act["cost"] = float(act.get("cost", 0.0))
                    except Exception:
                        act["cost"] = 0.0

            logger.info("AI itinerary successfully generated for %s (%d days)", destination_name, len(itinerary))
            return itinerary

        except httpx.HTTPStatusError as e:
            logger.warning("Groq API error %s: %s - falling back.", e.response.status_code, e.response.text)
            return None
        except Exception as e:
            logger.warning("AI itinerary generation failed: %s - falling back to templates.", e)
            return None

    async def chat_assistant(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Interactive travel chat companion.
        Formats responses to be clean, conversational, and helpful.
        """
        if not self.is_available:
            raise NotImplementedError(
                "AI service not configured. Add GROQ_API_KEY to your .env file."
            )

        system = (
            "You are BudgetBound's AI travel companion specialised in Indian destinations. "
            "Help users plan budget-conscious trips, suggest destinations, explain costs, "
            "and answer any travel-related questions. Keep responses conversational and practical. "
            "\n\nResponse Style:\n"
            "- Write in a friendly, conversational tone as if giving travel advice to a friend\n"
            "- Organize information into clear paragraphs, not bullet lists or templates\n"
            "- Start with a brief overview, then go into details naturally\n"
            "- Include specific recommendations with prices in rupees (₹)\n"
            "- End with practical tips or next steps\n"
            "- Avoid rigid templates - write naturally flowing prose\n"
            "- Keep sentences short but connect them logically\n"
            "- NEVER use bullet points, dashes, or markdown tables\n"
            "- NEVER create a 'snapshot' or summary table at the end\n"
            "- Write like a travel blogger, not a tour guide brochure"
        )
        groq_messages = [{"role": "system", "content": system}]
        for msg in messages:
            groq_messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {"model": GROQ_MODEL, "messages": groq_messages}
            response = httpx.post(GROQ_API_URL, headers=headers, json=payload, timeout=30.0)
            response.raise_for_status()
            reply = response.json()["choices"][0]["message"]["content"]
            
            # Clean up the response
            reply = reply.strip()
            
            # Remove markdown code blocks if present
            if reply.startswith("```"):
                lines = reply.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                reply = "\n".join(lines).strip()
            
            # Remove markdown tables entirely
            lines = reply.split("\n")
            cleaned_lines = []
            
            for line in lines:
                # Skip table separator rows
                if line.strip().startswith("|") and all(c in "|- " for c in line):
                    continue
                # Skip table data rows
                elif line.strip().startswith("|"):
                    cells = [cell.strip() for cell in line.split("|")[1:-1] if cell.strip()]
                    # Skip if it's just separators
                    if cells and not all(c in "-:" for c in "".join(cells)):
                        # Convert to prose - skip this row as it will be rewritten in prose form
                        continue
                # Remove bullet points and dashes at start of lines (convert to prose)
                elif line.strip().startswith(("• ", "- ", "* ")):
                    # Remove the bullet but keep the content, integrate into prose
                    content = line.strip()[2:].strip()
                    if content:
                        cleaned_lines.append(content)
                    else:
                        cleaned_lines.append(line)
                else:
                    cleaned_lines.append(line)
            
            reply = "\n".join(cleaned_lines).strip()
            
            # Clean up excessive whitespace
            reply = re.sub(r'\n{3,}', '\n\n', reply)  # Max 2 line breaks
            reply = re.sub(r' {2,}', ' ', reply)  # Max 1 space between words
            
            return {"reply": reply}
        except httpx.HTTPStatusError as e:
            logger.error("Groq chat error %s: %s", e.response.status_code, e.response.text)
            raise RuntimeError(f"AI service error: {e.response.status_code}") from e
        except Exception as e:
            logger.error("Groq chat failed: %s", e)
            raise RuntimeError(f"AI service error: {e}") from e

    async def generate_personalized_plan(self, keywords: str, budget: float, days: int, special: str) -> Dict[str, Any]:
        """
        Generate a customized travel plan using strict structured outputs.
        
        Process:
        1. Extract structured requirements from user input
        2. Generate LLM response with JSON schema enforcement
        3. Validate output against structural and financial criteria
        4. Score itinerary quality
        5. Return result with metadata
        
        Falls back to rule-based generator if LLM unavailable or schema validation fails.
        """
        from app.services.requirement_extractor import extract_requirements, format_requirements_for_prompt
        from app.services.personalized_plan_validator import PersonalizedPlanValidator
        from app.schemas import PersonalizedPlanResponse
        from app.services.financial_validator import FinancialValidator
        
        if not self.is_available:
            return self._fallback_personalized_plan(keywords, budget, days, special)
        
        # Extract structured requirements from user input
        requirements = extract_requirements(special or "")
        requirements_formatted = format_requirements_for_prompt(special or "")
        
        logger.info(
            f"Generating personalized plan with structured output: destination={keywords}, budget={budget}, days={days}, "
            f"requirements_extracted={len(requirements)}"
        )

        # Build enhanced prompt
        prompt = self._build_personalized_plan_prompt(
            destination=keywords,
            budget=budget,
            days=days,
            requirements=requirements,
            requirements_formatted=requirements_formatted
        )
        
        try:
            # Get JSON schema for strict structured output
            response_schema = PersonalizedPlanResponse.json_schema_for_groq()
            
            # Call LLM with structured output enforcement
            content, chat_error = self._chat(prompt, response_schema=response_schema)
            
            if chat_error:
                logger.warning(f"LLM request failed: {chat_error}. Using fallback.")
                self._request_stats["fallback_activations"] += 1
                return self._fallback_personalized_plan(keywords, budget, days, special)
            
            if not content:
                logger.warning("LLM returned no content. Using fallback.")
                self._request_stats["fallback_activations"] += 1
                return self._fallback_personalized_plan(keywords, budget, days, special)
            
            raw = content.strip()
            logger.debug(f"Raw LLM response (first 300 chars): {raw[:300]}")
            
            # Parse JSON - should be valid due to schema enforcement
            try:
                data = json.loads(raw)
                logger.info("Successfully parsed structured output JSON")
            except json.JSONDecodeError as json_err:
                # This should not happen with strict schema mode, but handle gracefully
                logger.error(f"Structured output JSON parse failed (unexpected): {json_err}")
                self._request_stats["fallback_activations"] += 1
                return self._fallback_personalized_plan(keywords, budget, days, special)
            
            # Validate financial correctness
            financial_validator = FinancialValidator(budget, days)
            
            budget_breakdown = data.get("budget_breakdown", {})
            days_array = data.get("days", [])
            estimated_total = data.get("estimated_total_cost", 0)
            
            financial_result = financial_validator.validate_itinerary(
                days_array,
                budget_breakdown.get("accommodation_per_night", 0),
                budget_breakdown.get("food_per_day", 0),
                budget_breakdown.get("activities_per_day", 0),
                budget_breakdown.get("transport", 0),
                budget_breakdown.get("contingency", 0),
                estimated_total
            )
            
            logger.info(
                f"Financial validation: valid={financial_result['is_valid']}, "
                f"total={financial_result['estimated_total_cost']}, "
                f"remaining={financial_result['remaining_budget']}, "
                f"errors={len(financial_result['errors'])}"
            )
            
            if financial_result["errors"]:
                logger.warning(f"Financial validation errors: {financial_result['errors']}")
            
            # Only fail if budget compliance is violated (exceeds budget) - warnings are acceptable
            if financial_result.get("overspend") is not None and financial_result.get("overspend", 0) > budget * 0.05:
                logger.warning(f"LLM exceeded budget by more than 5%. Using fallback.")
                self._request_stats["fallback_activations"] += 1
                return self._fallback_personalized_plan(keywords, budget, days, special)
            
            # Create response object from validated data
            try:
                response = PersonalizedPlanResponse(**data)
                response.data_source = "llm"
                response.validation_warnings = financial_result.get("warnings", [])
                if financial_result.get("remaining_budget") is not None:
                    response.remaining_budget = financial_result["remaining_budget"]
                
                # Calculate quality scores using validator
                validator = PersonalizedPlanValidator(response)
                validation_result = validator.validate()
                response.semantic_score = validation_result.semantic_score
                response.feasibility_score = validation_result.feasibility_score
                response.requirement_coverage_score = validation_result.requirement_coverage_score
                
                logger.info(f"Successfully generated LLM-based plan for {keywords} with scores: semantic={validation_result.semantic_score}, feasibility={validation_result.feasibility_score}, coverage={validation_result.requirement_coverage_score}")
                return response.dict()
                
            except Exception as e:
                logger.error(f"Failed to instantiate PersonalizedPlanResponse: {e}")
                self._request_stats["fallback_activations"] += 1
                return self._fallback_personalized_plan(keywords, budget, days, special)
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}. Using fallback.")
            self._request_stats["fallback_activations"] += 1
            return self._fallback_personalized_plan(keywords, budget, days, special)
        except Exception as e:
            logger.exception(f"Error generating personalized plan via LLM: {e}")
            self._request_stats["fallback_activations"] += 1
            return self._fallback_personalized_plan(keywords, budget, days, special)
    
    
    def _build_personalized_plan_prompt(
        self,
        destination: str,
        budget: float,
        days: int,
        requirements: List[Any],
        requirements_formatted: str
    ) -> str:
        """Build an enhanced prompt for personalized plan generation."""
        return f"""You are an expert travel planner specializing in global destinations. Generate a highly detailed, practical, destination-specific travel itinerary that satisfies all user requirements.

DESTINATION & TRIP SCOPE:
- Destination: {destination}
- Total Budget: Rs. {budget:.0f}
- Duration: EXACTLY {days} days
- {requirements_formatted if requirements_formatted else 'No specific requirements'}

ITINERARY REQUIREMENTS (NON-NEGOTIABLE):
1. Generate EXACTLY {days} days numbered 1 through {days}. NO MORE, NO LESS.
2. Day 1 MUST include Arrival/Hotel Check-in (morning activity, cost = 0).
3. Day {days} MUST include Check-out/Departure (evening activity, cost = 0 or minimal).
4. Every activity MUST be SPECIFIC to {destination}:
   - Use REAL, verifiable place names (neighborhoods, landmarks, actual restaurants)
   - Provide specific dish names or activity details
   - NO generic placeholders like "local lunch", "shopping", "explore", "orientation tour"
5. Activity titles MUST be:
   - Unique across all {days} days (no repetition)
   - Descriptive and action-oriented (e.g., "Morning ferry ride on Hooghly River to Dakshineswar Temple")
   - NOT formatted as "DAY 01 - Day 1" (avoid redundant heading styles)
6. Activities must vary meaningfully by day (different themes, locations, experiences).
7. Activity timing must be logical (morning → afternoon → evening per day).

ACTIVITY STRUCTURE (per activity):
- Time of day: Morning, Afternoon, or Evening
- Start time: e.g., "08:00 AM" (realistic for destination)
- Title: Specific, unique to destination, action-oriented
- Description: 1-2 sentences explaining the experience
- Cost: Non-negative number in INR (0 for free activities)
- Duration: e.g., "2-3 hours"
- Location: Specific neighborhood, street, or landmark name

BUDGET ALLOCATION GUIDANCE:
- Accommodation: ~30-40% of total budget (per night)
- Food & dining: ~15-20% (per day, higher if user prefers food)
- Activities & entry fees: ~15-20% (per day)
- Transport & transfers: ~20-30% (for entire trip)
- Contingency & reserves: ~5-10% (for entire trip)

REQUIREMENT FULFILLMENT:
{self._format_requirement_instructions(requirements)}

COST RECONCILIATION:
- Sum of daily activity costs must align with estimated_total_cost / {days}
- All costs must be realistic and non-negative
- Daily totals: sum of all 3 activities (morning + afternoon + evening)
- Trip total: sum of all daily costs + trip-level expenses

RESPONSE FORMAT (Return ONLY valid JSON, no markdown, no explanations):
{{
  "plan_name": "Customized {days}-day trip to {destination}",
  "destination": "{destination}",
  "num_days": {days},
  "estimated_total_cost": <float: realistic estimate 80-95% of budget>,
  "budget_limit": {budget},
  "summary": "<2-3 sentence overview highlighting destination and satisfied requirements>",
  "budget_breakdown": {{
    "accommodation_per_night": <float>,
    "food_per_day": <float>,
    "activities_per_day": <float>,
    "transport": <float>,
    "contingency": <float>
  }},
  "days": [
    {{
      "day_number": 1,
      "title": "Day 1 - <specific, unique day title>",
      "description": "<1-2 sentence overview of the day>",
      "activities": [
        {{
          "time": "Morning",
          "start_time": "08:00 AM",
          "title": "<specific activity, not generic>",
          "description": "<1-2 sentences>",
          "cost": <number>,
          "duration": "<e.g., 2-3 hours>",
          "location": "<specific place name>"
        }}
      ]
    }}
  ]
}}

EXAMPLES OF GOOD vs BAD TITLES:
✓ GOOD: "Morning ferry ride on Hooghly River & breakfast at Sonalika (Hilsa fish curry)"
✗ BAD: "Local breakfast & river tour"
✓ GOOD: "Heritage walk through Fort area & Leopold Cafe for lunch"
✗ BAD: "Explore heritage & local lunch"
"""
    
    def _format_requirement_instructions(self, requirements: List[Any]) -> str:
        """Format requirement instructions for the prompt with specific activity examples."""
        if not requirements:
            return "No specific requirements."
        
        from app.services.requirement_extractor import RequirementExtractor
        
        mandatory_reqs = [r for r in requirements if r.mandatory]
        optional_reqs = [r for r in requirements if not r.mandatory]
        
        extractor = RequirementExtractor()
        activity_hints = extractor.get_activity_hints(requirements)
        
        lines = []
        if mandatory_reqs:
            lines.append("MANDATORY requirements (MUST be explicitly included):")
            for req in mandatory_reqs:
                req_name = req.value.replace("_", " ").title()
                lines.append(f"  • {req_name} ({req.category}): Include specific activities/dining that satisfy this.")
                
                # Add specific activity hints for cuisine requirements
                if req.category == "cuisine" and req.value in activity_hints:
                    hints = activity_hints.get(req.value, [])
                    if hints:
                        lines.append(f"    Examples: {', '.join(hints[:3])}")
        
        if optional_reqs:
            lines.append("OPTIONAL preferences (include if feasible within budget/time):")
            for req in optional_reqs:
                req_name = req.value.replace("_", " ").title()
                lines.append(f"  • {req_name} ({req.category})")
        
        return "\n".join(lines)
    
    def _repair_json(self, text: str) -> str:
        """
        Attempt to repair malformed JSON from LLM output.
        Handles: unterminated strings, missing closing braces, smart quotes, truncation.
        """
        import re
        
        # Replace smart quotes with regular quotes
        text = text.replace(''', "'").replace(''', "'").replace('"', '"').replace('"', '"')
        
        # Find last opening brace that might indicate truncation
        last_close_brace = max(text.rfind('}'), text.rfind(']'))
        last_open_brace = max(text.rfind('{'), text.rfind('['))
        
        # If there are unclosed braces, try to close them
        if last_open_brace > last_close_brace:
            # Text is likely truncated - try to find the last valid structure
            # Look for the last complete object/array element
            text = text[:last_close_brace + 1] if last_close_brace > 0 else text
        
        # Remove trailing commas before ] or }
        text = re.sub(r',(\s*[\]}])', r'\1', text)
        
        # Ensure all opening braces have closing braces
        open_braces = text.count('{') - text.count('}')
        if open_braces > 0:
            text += '}' * open_braces
        
        open_brackets = text.count('[') - text.count(']')
        if open_brackets > 0:
            text += ']' * open_brackets
        
        return text

    def _normalize_schema(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize LLM response schema to our standard format.
        Different models may return slightly different field names.
        """
        normalized = dict(data)
        
        # Normalize top-level fields
        field_mappings = {
            "estimated_total_budget": "estimated_total_cost",
            "total_estimated_budget": "estimated_total_cost",
            "budget": "estimated_total_cost",
        }
        for old_field, new_field in field_mappings.items():
            if old_field in normalized and new_field not in normalized:
                normalized[new_field] = normalized.pop(old_field)
        
        # Handle days array normalization
        if "days" in normalized:
            days_list = normalized.get("days", [])
            for day in days_list:
                # Normalize activity field names
                if "activities" in day:
                    for activity in day.get("activities", []):
                        # Handle time_span → time
                        if "time_span" in activity and "time" not in activity:
                            activity["time"] = activity.pop("time_span")
                        
                        # Handle start_time variations
                        if "start_time" not in activity and "time" in activity:
                            # Try to extract time if it's in title
                            activity["start_time"] = ""
        
        # Normalize budget breakdown field names
        # Try to construct if missing
        if "budget_breakdown" not in normalized:
            breakdown = {}
            
            # First try budget_allocations
            if "budget_allocations" in normalized:
                allocations = normalized.pop("budget_allocations")
                if isinstance(allocations, dict):
                    mapping = {
                        "accommodation": "accommodation_per_night",
                        "food": "food_per_day",
                        "activities": "activities_per_day",
                        "tours & activities": "activities_per_day",
                        "local transportation": "transport",
                        "transportation": "transport",
                        "miscellaneous": "contingency",
                    }
                    for src_key, dst_key in mapping.items():
                        if src_key in allocations:
                            breakdown[dst_key] = allocations[src_key]
            
            # If still empty, estimate from estimated_total_cost
            if not breakdown and "estimated_total_cost" in normalized:
                total_cost = normalized.get("estimated_total_cost", 0)
                num_days = normalized.get("num_days", 1)
                breakdown = {
                    "accommodation_per_night": total_cost * 0.35 / max(1, num_days),
                    "food_per_day": total_cost * 0.18 / max(1, num_days),
                    "activities_per_day": total_cost * 0.18 / max(1, num_days),
                    "transport": total_cost * 0.25,
                    "contingency": total_cost * 0.04,
                }
            
            normalized["budget_breakdown"] = breakdown
        
        return normalized

    def _normalize_llm_response(
        self,
        data: Dict[str, Any],
        keywords: str,
        budget: float,
        days: int,
        requirements: List[Any]
    ) -> "PersonalizedPlanResponse":
        """Normalize LLM response into PersonalizedPlanResponse object."""
        from app.schemas import PersonalizedPlanResponse, PersonalizedPlanDay, PersonalizedPlanActivity, BudgetBreakdown
        from datetime import datetime
        
        # Validate and fix day count
        llm_days = data.get("days", [])
        if len(llm_days) != days:
            logger.warning(f"LLM returned {len(llm_days)} days, padding/trimming to {days}")
            if len(llm_days) < days:
                for i in range(len(llm_days) + 1, days + 1):
                    llm_days.append({
                        "day_number": i,
                        "title": f"Day {i} - Continued Exploration",
                        "description": f"Additional exploration of {keywords}",
                        "activities": []
                    })
            else:
                llm_days = llm_days[:days]
        
        # Normalize activities and costs
        all_costs = []
        for day in llm_days:
            day["activities"] = day.get("activities", [])
            for activity in day["activities"]:
                # Parse cost
                cost = activity.get("cost", 0.0)
                if isinstance(cost, str):
                    try:
                        cost = float(re.sub(r'[^\d.]', '', cost) or 0.0)
                    except:
                        cost = 0.0
                else:
                    try:
                        cost = float(cost)
                    except:
                        cost = 0.0
                
                # Ensure non-negative
                cost = max(0.0, cost)
                activity["cost"] = cost
                all_costs.append(cost)
        
        # Validate and reconcile total cost
        estimated_total = data.get("estimated_total_cost", sum(all_costs))
        try:
            estimated_total = float(estimated_total)
        except:
            estimated_total = sum(all_costs)
        
        # Clamp to budget if exceeds
        if estimated_total > budget:
            logger.warning(f"Estimated total ({estimated_total}) exceeds budget ({budget}), clamping")
            estimated_total = budget * 0.95
        
        # Normalize breakdown
        breakdown = data.get("budget_breakdown", {})
        try:
            accommodation_per_night = float(breakdown.get("accommodation_per_night", budget * 0.35 / days))
            food_per_day = float(breakdown.get("food_per_day", budget * 0.18 / days))
            activities_per_day = float(breakdown.get("activities_per_day", budget * 0.18 / days))
            transport = float(breakdown.get("transport", budget * 0.25))
            contingency = float(breakdown.get("contingency", budget * 0.04))
        except:
            accommodation_per_night = budget * 0.35 / days
            food_per_day = budget * 0.18 / days
            activities_per_day = budget * 0.18 / days
            transport = budget * 0.25
            contingency = budget * 0.04
        
        # Reconcile breakdown to match estimated total
        breakdown_total = (accommodation_per_night * days) + (food_per_day * days) + (activities_per_day * days) + transport + contingency
        if breakdown_total > 0 and abs(breakdown_total - estimated_total) > 1.0:
            scale = estimated_total / breakdown_total
            accommodation_per_night *= scale
            food_per_day *= scale
            activities_per_day *= scale
            transport *= scale
            contingency *= scale
        
        # Create normalized response
        days_list = []
        for day_data in llm_days:
            activities_list = []
            day_cost = 0.0
            
            for activity_data in day_data.get("activities", []):
                activity = PersonalizedPlanActivity(
                    time=activity_data.get("time", "Morning"),
                    start_time=activity_data.get("start_time", ""),
                    title=activity_data.get("title", ""),
                    description=activity_data.get("description", ""),
                    cost=float(activity_data.get("cost", 0.0)),
                    duration=activity_data.get("duration", ""),
                    location=activity_data.get("location", keywords),
                    fulfills_requirements=[]
                )
                activities_list.append(activity)
                day_cost += activity.cost
            
            day = PersonalizedPlanDay(
                day_number=day_data.get("day_number", 1),
                title=day_data.get("title", f"Day {day_data.get('day_number', 1)}"),
                description=day_data.get("description", ""),
                activities=activities_list,
                total_cost=round(day_cost, 2)
            )
            days_list.append(day)
        
        response = PersonalizedPlanResponse(
            plan_name=data.get("plan_name", f"Customized {days}-day trip to {keywords}"),
            destination=keywords,
            num_days=days,
            estimated_total_cost=round(estimated_total, 2),
            budget_limit=budget,
            summary=data.get("summary", ""),
            budget_breakdown=BudgetBreakdown(
                accommodation_per_night=round(accommodation_per_night, 2),
                food_per_day=round(food_per_day, 2),
                activities_per_day=round(activities_per_day, 2),
                transport=round(transport, 2),
                contingency=round(contingency, 2)
            ),
            days=days_list,
            remaining_budget=round(max(0, budget - estimated_total), 2),
            requirements_extracted=requirements,
            generation_timestamp=datetime.utcnow()
        )
        
        return response

    def _fallback_personalized_plan(self, keywords: str, budget: float, days: int, special: str) -> Dict[str, Any]:
        """
        Fallback personalized plan generator with destination-agnostic day themes.
        Generates meaningful, varied day themes for ANY destination without hard-coding.
        Uses a rule-based algorithm that infers destination type and creates contextual activities.
        
        ALGORITHM:
        - Day 1: Always "Arrival & {destination} Introduction"
        - Mid-days: Vary themes from a destination-agnostic pool: Heritage, Nature, Markets, Culture, 
                    Adventure, Cuisine, Arts, Leisure, Exploration, Local Life, Outdoor, Discovery
        - Last day: Always "Leisure & Departure Prep"
        - Themes are rotated to ensure 4+ unique themes for 4-day trip
        - Restaurant types are inferred from destination keyword patterns
        - Activity titles are parameterized and never generic (no "Local lunch", "Main attraction")
        - USER PREFERENCES are injected into activity titles and descriptions
        
        BUDGET MODEL:
        - budget_limit: User's maximum spending limit (input)
        - Base allocations (before preference adjustments):
          * accommodation: 35% of budget
          * food: 18% of budget
          * activities: 18% of budget
          * transport: 25% of budget
          * contingency: 4% of budget
        - Preference multipliers adjust food+activities allocations only
        - estimated_total_cost = sum of all allocated categories (INCLUDES contingency)
        - remaining_budget = budget_limit - estimated_total_cost
        - Daily costs are derived from per-day allocations
        - All category allocations must be non-negative
        """
        from app.services.requirement_extractor import RequirementExtractor
        
        dest = keywords if keywords else "India"
        
        # Extract requirements from special preferences
        extractor = RequirementExtractor()
        requirements = extractor.extract(special or "")
        activity_hints = extractor.get_activity_hints(requirements)
        
        # Parse user preferences
        preferences_text = special.lower() if special else ""
        has_food_pref = "delicious food" in preferences_text or "food" in preferences_text or "cuisine" in preferences_text
        has_fancy_pref = "fancy" in preferences_text or "luxury" in preferences_text or "premium" in preferences_text
        
        # Build cuisine-specific descriptors and activity titles from requirements
        cuisine_hint = None
        cuisine_activities = []
        for req in requirements:
            if req.category == "cuisine":
                cuisine_hint = req.value.replace("_", " ").title()
                cuisine_activities = activity_hints.get("cuisine", [])
                break
        
        # Allocate budget with preference adjustments
        # Base allocations
        accommodation_per_night_base = budget * 0.35 / max(days, 1)
        food_per_day_base = budget * 0.18 / max(days, 1)
        activities_per_day_base = budget * 0.18 / max(days, 1)
        transport_base = budget * 0.25
        contingency_base = budget * 0.04
        
        # Apply preference multipliers ONLY to food+activities, not to accommodation/transport
        cost_multiplier = 1.2 if (has_food_pref or has_fancy_pref) else 1.0
        
        # However, we must ensure total doesn't exceed budget
        # Calculate what the totals would be with multiplier
        estimated_with_multiplier = (
            (accommodation_per_night_base * days) +
            (food_per_day_base * days * cost_multiplier) +
            (activities_per_day_base * days * cost_multiplier) +
            transport_base +
            contingency_base
        )
        
        # If multiplier would exceed budget, scale it down
        if estimated_with_multiplier > budget:
            # Calculate max allowed multiplier
            base_total = (accommodation_per_night_base * days) + (food_per_day_base * days) + (activities_per_day_base * days) + transport_base + contingency_base
            unaffected_total = (accommodation_per_night_base * days) + transport_base + contingency_base
            affected_base = base_total - unaffected_total
            
            if affected_base > 0:
                max_multiplier = (budget - unaffected_total) / affected_base
                cost_multiplier = min(1.2, max(1.0, max_multiplier))
            else:
                cost_multiplier = 1.0
        
        # Final allocations
        accommodation_per_night = accommodation_per_night_base
        food_per_day = food_per_day_base * cost_multiplier
        activities_per_day = activities_per_day_base * cost_multiplier
        transport = transport_base
        contingency = contingency_base
        
        # Ensure no negative values
        food_per_day = max(0.0, food_per_day)
        activities_per_day = max(0.0, activities_per_day)
        
        # Calculate estimated total with adjusted values
        estimated_total = (accommodation_per_night * days) + (food_per_day * days) + (activities_per_day * days) + transport + contingency
        
        # Ensure estimated total doesn't exceed budget
        if estimated_total > budget:
            # Scale contingency down to fit within budget
            contingency = max(0.0, budget - ((accommodation_per_night * days) + (food_per_day * days) + (activities_per_day * days) + transport))
            estimated_total = (accommodation_per_night * days) + (food_per_day * days) + (activities_per_day * days) + transport + contingency
        
        # Destination-agnostic theme generation algorithm
        # Infer destination keywords to generate contextual themes
        destination_lower = dest.lower()
        
        # Keyword patterns for destination type classification
        beach_keywords = ["beach", "coast", "island", "sea", "ocean", "goa", "andaman", "lakshadweep", "zanzibar", "maldives", "caribbean", "pacific", "mediterranean"]
        mountain_keywords = ["mountain", "hill", "himalaya", "alps", "andes", "himalayan", "range", "peak", "manali", "shimla", "darjeeling", "leh", "ladakh"]
        temple_keywords = ["temple", "pilgrimage", "spiritual", "sacred", "shrine", "varanasi", "mathura", "vrindavan", "tirupati", "agra", "kathmandu"]
        heritage_keywords = ["heritage", "palace", "fort", "mughal", "historic", "ancient", "monument", "rajasthan", "delhi", "agra", "jaipur", "udaipur", "jodhpur"]
        urban_keywords = ["city", "metro", "mumbai", "delhi", "bangalore", "kolkata", "hyderabad", "pune", "urban", "metro", "york", "london", "paris"]
        nature_keywords = ["wildlife", "safari", "jungle", "forest", "national park", "botanical", "garden", "reserve", "tiger", "leopard"]
        cultural_keywords = ["culture", "art", "museum", "gallery", "craft", "artisan", "workshop", "traditional", "local"]
        food_keywords = ["food", "cuisine", "gastronomic", "culinary", "cooking", "chef", "restaurant"]
        
        # Classify destination based on keywords
        def has_keyword_match(text, keywords):
            return any(kw in text for kw in keywords)
        
        is_beach = has_keyword_match(destination_lower, beach_keywords)
        is_mountain = has_keyword_match(destination_lower, mountain_keywords)
        is_temple = has_keyword_match(destination_lower, temple_keywords)
        is_heritage = has_keyword_match(destination_lower, heritage_keywords)
        is_urban = has_keyword_match(destination_lower, urban_keywords)
        is_nature = has_keyword_match(destination_lower, nature_keywords)
        is_cultural = has_keyword_match(destination_lower, cultural_keywords)
        
        # Generate destination-agnostic restaurant types based on classification
        if is_beach:
            restaurant_types = ["Seafood restaurant", "Beach shack", "Coastal cafe", "Fish market restaurant", "Beachfront bistro", "Island cuisine restaurant"]
        elif is_mountain:
            restaurant_types = ["Mountain lodge restaurant", "Local home kitchen", "Highland cafe", "Traditional mountain cuisine", "Trekker's lodge restaurant", "Village eatery"]
        elif is_temple or is_cultural:
            restaurant_types = ["Temple area restaurant", "Local cuisine cafe", "Traditional family restaurant", "Spiritual retreat kitchen", "Cultural cuisine restaurant", "Street food stand"]
        elif is_heritage or is_urban:
            restaurant_types = ["Heritage restaurant", "City restaurant", "Local bistro", "Contemporary restaurant", "Upscale urban eatery", "Fusion cafe"]
        else:
            restaurant_types = ["District restaurant", "Market area cafe", "Neighborhood bistro", "Downtown dining", "Market area restaurant"]
        
        # If user has cuisine preference, inject it into restaurant types
        if cuisine_hint and cuisine_activities:
            restaurant_types = [
                f"{cuisine_hint} Restaurant",
                f"{cuisine_hint} Eatery",
                f"Local {cuisine_hint} Restaurant",
            ] + restaurant_types[:3]
        
        # Generate 5 primary day themes (will be truncated/expanded as needed)
        # Day themes are: (theme_title, activity_area, activity_focus)
        theme_pool = [
            ("Heritage & Landmarks", "Heritage district", "Historic sites"),
            ("Nature & Outdoor Exploration", "Natural areas", "Parks & nature reserves"),
            ("Markets & Local Commerce", "Market district", "Bazaars & shopping"),
            ("Cultural Immersion", "Cultural center", "Local traditions"),
            ("Adventure & Activities", "Adventure zones", "Outdoor sports"),
            ("Culinary Discovery", "Food district", "Local cuisine"),
            ("Arts & Museums", "Arts district", "Galleries & studios"),
            ("Leisure & Relaxation", "Resort areas", "Spa & wellness"),
            ("Local Life & Communities", "Residential areas", "Village/neighborhood"),
            ("Exploration & Discovery", "Less-known areas", "Hidden gems"),
            ("Outdoor Recreation", "Recreation zones", "Sports & activities"),
            ("Historical Deep Dive", "Historical sites", "Monuments & archaeology"),
        ]
        
        # Customize theme pool based on destination type
        if is_beach:
            theme_pool = [
                ("Beach & Coastal Welcome", "Beach areas", "Coastal shoreline"),
                ("Water Sports & Activities", "Beach resorts", "Watersports center"),
                ("Beach Culture & Local Life", "Beach villages", "Fishing communities"),
                ("Diving & Snorkeling", "Dive sites", "Marine exploration"),
                ("Sunset Leisure & Relaxation", "Beach sunset spots", "Evening relaxation"),
            ]
        elif is_mountain:
            theme_pool = [
                ("Mountain & Valley Introduction", "Mountain base", "Highland landscape"),
                ("Trekking & Highland Exploration", "Mountain trails", "Peak views"),
                ("Local Village Culture", "Mountain villages", "Rural traditions"),
                ("Adventure Sports", "Adventure zones", "Climbing & sports"),
                ("Scenic Views & Nature Walks", "Mountain vistas", "Easy hiking"),
            ]
        elif is_temple:
            theme_pool = [
                ("Temple Visit & Spiritual Welcome", "Main temple", "Sacred rituals"),
                ("Pilgrimage Circuit", "Temple district", "Holy sites"),
                ("Local Devotional Culture", "Temple areas", "Religious life"),
                ("Spiritual Practices & Meditation", "Meditation centers", "Inner peace"),
                ("Temple Town Exploration", "Temple surroundings", "Pilgrimage town"),
            ]
        # Otherwise use generic theme pool for urban/unknown destinations
        
        # If user has cuisine preference, inject food-focused theme
        if cuisine_hint:
            theme_pool = [
                (f"{cuisine_hint} Culinary Experience", "Food district", f"{cuisine_hint} restaurants & markets"),
            ] + theme_pool[:4]
        
        # Select unique themes for the trip (always start with Arrival, end with Departure)
        # For mid-days, cycle through theme pool to ensure variety
        selected_themes = []
        used_themes = set()
        
        for i in range(days):
            if i == 0:
                # First day: always arrival introduction
                selected_themes.append((f"Arrival & {dest} Introduction", dest, "Main arrival area"))
            elif i == days - 1:
                # Last day: always departure prep
                selected_themes.append((f"Leisure & Departure Preparation", dest, "Favorite spots"))
            else:
                # Mid-days: cycle through theme pool, skipping duplicates
                theme_index = (i - 1) % len(theme_pool)
                theme = theme_pool[theme_index]
                # Avoid exact duplicates by rotating if needed
                rotation = 0
                while theme[0] in used_themes and rotation < len(theme_pool):
                    theme_index = (theme_index + 1) % len(theme_pool)
                    theme = theme_pool[theme_index]
                    rotation += 1
                used_themes.add(theme[0])
                selected_themes.append(theme)
        
        day_themes = selected_themes
        
        # Generate restaurant names (5+ entries, indexed by day number)
        # Ensure we have enough types for any trip duration
        food_restaurants = {}
        for day_num in range(1, max(days, 5) + 1):
            idx = (day_num - 1) % len(restaurant_types)
            rest_type = restaurant_types[idx]
            food_restaurants[day_num] = rest_type
        
        # Limit to requested days
        day_themes = day_themes[:days]
        
        # Ensure we have enough themes
        while len(day_themes) < days:
            day_themes.append((f"Day {len(day_themes)+1} - Additional Exploration", dest, "Local area"))
        
        # Build days with varied activities per theme
        days_list = []
        for i, (theme_title, theme_area, theme_focus) in enumerate(day_themes):
            day_num = i + 1
            restaurant_name = food_restaurants.get(day_num, "Local restaurant")
            
            # Generate 3 distinct activities per day based on theme
            # Activity titles are ALWAYS specific to destination and never generic
            if day_num == 1:
                # First day: arrival and orientation
                # INJECT CUISINE PREFERENCE if available
                if cuisine_hint and cuisine_activities:
                    activity_titles = [
                        f"Arrival at {dest} & Hotel Check-in",
                        f"{theme_area} exploration & local {cuisine_hint} lunch",
                        f"Welcome dinner at {restaurant_name}"
                    ]
                    descriptions = [
                        "Welcome to your destination. Settle into your accommodation and freshen up.",
                        f"Get acquainted with {theme_area} while tasting authentic {cuisine_hint} cuisine for lunch.",
                        f"Relax and enjoy your first meal in {dest} at a local {restaurant_name}."
                    ]
                else:
                    activity_titles = [
                        f"Arrival at {dest} & Hotel Check-in",
                        f"{theme_area} exploration & orientation",
                        f"Welcome dinner at {restaurant_name}"
                    ]
                    descriptions = [
                        "Welcome to your destination. Settle into your accommodation and freshen up.",
                        f"Get acquainted with {theme_area} and its key attractions and neighborhoods.",
                        f"Relax and enjoy your first meal in {dest} at a local {restaurant_name}."
                    ]
            elif day_num == days:
                # Last day: leisure and departure
                activity_titles = [
                    f"Relaxed morning in {dest}",
                    f"Final exploration of {theme_area}",
                    f"Check-out & departure from {dest}"
                ]
                descriptions = [
                    f"Enjoy a relaxed final morning in {dest}. Take time to revisit favorite spots or rest.",
                    f"Explore any remaining attractions in {theme_area} or shop for souvenirs.",
                    "Check out and head to transport for departure."
                ]
            else:
                # Mid-journey days with varied activities based on theme
                # INJECT CUISINE PREFERENCE into activity titles if available
                if cuisine_hint and i % 2 == 1:  # Alternate with regular themes
                    activity_titles = [
                        f"Breakfast at a local {cuisine_hint} restaurant",
                        f"Mid-day {cuisine_hint} dining experience" if cuisine_activities else f"Main activities: {theme_focus}",
                        f"Evening {cuisine_hint} dinner at {restaurant_name}"
                    ]
                    descriptions = [
                        f"Start your day with authentic {cuisine_hint} breakfast and explore local flavors.",
                        f"Experience the highlights of {cuisine_hint} cuisine and culinary traditions in {dest}.",
                        f"Unwind with authentic {cuisine_hint} dinner at a highly-rated {restaurant_name}."
                    ]
                else:
                    activity_titles = [
                        f"{theme_focus} (Part 1): Morning exploration",
                        f"Main activities: {theme_focus}",
                        f"{theme_focus} (Part 2): Evening experience"
                    ]
                    descriptions = [
                        f"Start your day with a hearty breakfast and begin exploring {theme_focus}.",
                        f"Experience the highlights of {theme_area}. Dive deep into {theme_focus.lower()}.",
                        f"Unwind with a relaxing time in {theme_area}. Enjoy dinner at {restaurant_name}."
                    ]
            
            # Daily combined food+activities budget (already includes preference multiplier)
            daily_food_activities = food_per_day + activities_per_day
            
            activities = []
            if day_num == 1:
                activities = [
                    {
                        "time": "Morning",
                        "start_time": "08:00 AM",
                        "title": activity_titles[0],
                        "description": descriptions[0],
                        "cost": 0.0,
                        "duration": "2-3 hours",
                        "location": f"Airport/Station → {theme_area}"
                    },
                    {
                        "time": "Afternoon",
                        "start_time": "01:00 PM",
                        "title": activity_titles[1],
                        "description": descriptions[1],
                        "cost": round(daily_food_activities * 0.40, 2),
                        "duration": "3-4 hours",
                        "location": theme_area
                    },
                    {
                        "time": "Evening",
                        "start_time": "06:00 PM",
                        "title": activity_titles[2],
                        "description": descriptions[2],
                        "cost": round(daily_food_activities * 0.35, 2),
                        "duration": "2-3 hours",
                        "location": restaurant_name
                    }
                ]
            elif day_num == days:
                activities = [
                    {
                        "time": "Morning",
                        "start_time": "08:00 AM",
                        "title": activity_titles[0],
                        "description": descriptions[0],
                        "cost": round(daily_food_activities * 0.25, 2),
                        "duration": "2-3 hours",
                        "location": theme_area
                    },
                    {
                        "time": "Afternoon",
                        "start_time": "01:00 PM",
                        "title": activity_titles[1],
                        "description": descriptions[1],
                        "cost": round(daily_food_activities * 0.30, 2),
                        "duration": "3 hours",
                        "location": theme_area
                    },
                    {
                        "time": "Evening",
                        "start_time": "05:00 PM",
                        "title": activity_titles[2],
                        "description": descriptions[2],
                        "cost": 0.0,
                        "duration": "2-3 hours",
                        "location": f"{theme_area} → Airport/Station"
                    }
                ]
            else:
                # Mid-journey days with varied activities
                activities = [
                    {
                        "time": "Morning",
                        "start_time": "08:00 AM",
                        "title": activity_titles[0],
                        "description": descriptions[0],
                        "cost": round(daily_food_activities * 0.25, 2),
                        "duration": "2-3 hours",
                        "location": theme_area
                    },
                    {
                        "time": "Afternoon",
                        "start_time": "01:00 PM",
                        "title": activity_titles[1],
                        "description": descriptions[1],
                        "cost": round(daily_food_activities * 0.45, 2),
                        "duration": "4 hours",
                        "location": theme_focus
                    },
                    {
                        "time": "Evening",
                        "start_time": "06:00 PM",
                        "title": activity_titles[2],
                        "description": descriptions[2],
                        "cost": round(daily_food_activities * 0.30, 2),
                        "duration": "3-4 hours",
                        "location": restaurant_name
                    }
                ]
            
            day_cost = sum(act.get("cost", 0.0) for act in activities)
            
            days_list.append({
                "day_number": day_num,
                "title": f"Day {day_num} - {theme_title}",
                "description": f"Experience {theme_title.lower()} in {dest}. Immerse yourself in local culture and attractions.{' Savor diverse culinary experiences.' if has_food_pref else ''}",
                "activities": activities,
                "total_cost": round(day_cost, 2)
            })
        
        # Calculate estimated total directly from allocations (already multiplier-adjusted)
        # This ensures reconciliation matches our budget model exactly
        estimated_total = round((accommodation_per_night * days) + (food_per_day * days) + (activities_per_day * days) + transport + contingency, 2)
        
        remaining_budget = round(max(0, budget - estimated_total), 2)
        
        # Build breakdown using calculated allocations directly (not from residuals)
        breakdown = {
            "accommodation_per_night": round(accommodation_per_night, 2),
            "food_per_day": round(food_per_day, 2),
            "activities_per_day": round(activities_per_day, 2),
            "transport": round(transport, 2),
            "contingency": round(contingency, 2)
        }
        
        return {
            "plan_name": f"Customized trip to {dest}" + (" for food lovers" if has_food_pref else "") + (" with premium comfort" if has_fancy_pref else ""),
            "destination": dest,
            "num_days": days,
            "estimated_total_cost": estimated_total,
            "budget_limit": budget,
            "summary": f"A thoughtfully designed {days}-day itinerary in {dest}. " + 
                      (f"Special focus: {special}. This itinerary emphasizes culinary experiences and local flavors at every opportunity." if has_food_pref else "Balanced mix of cultural sites, local experiences, and relaxation.") if special else "",
            "budget_breakdown": breakdown,
            "days": days_list,
            "remaining_budget": remaining_budget,
            # Quality scores for fallback: conservative but reasonable
            "semantic_score": 70.0,  # 70% - fallback generates generic but coherent plans
            "feasibility_score": 85.0,  # 85% - structural soundness is good
            "requirement_coverage_score": (100.0 if (has_food_pref and cuisine_hint) else 50.0),  # 100% if food pref is met, 50% otherwise
            "data_source": "fallback"
        }

    async def regenerate_trip(self, trip: Any, instruction: str) -> Dict[str, Any]:
        """
        Ask the LLM to modify an existing trip plan based on instructions.
        """
        if not self.is_available:
            return self._fallback_regenerate_trip(trip, instruction)

        old_allocation = {
            "transport_cost": trip.budget_allocation.transport_cost if trip.budget_allocation else 0.0,
            "hotel_cost": trip.budget_allocation.hotel_cost if trip.budget_allocation else 0.0,
            "food_cost": trip.budget_allocation.food_cost if trip.budget_allocation else 0.0,
            "activities_cost": trip.budget_allocation.activities_cost if trip.budget_allocation else 0.0,
            "local_transport_cost": trip.budget_allocation.local_transport_cost if trip.budget_allocation else 0.0,
            "taxes_fees_cost": trip.budget_allocation.taxes_fees_cost if trip.budget_allocation else 0.0,
            "emergency_reserve": trip.budget_allocation.emergency_reserve if trip.budget_allocation else 0.0,
            "total_estimated_cost": trip.total_estimated_cost
        }
        
        old_itinerary = [
            {
                "day_number": day.day_number,
                "description": day.description,
                "activities": day.activities
            } for day in sorted(trip.itineraries, key=lambda x: x.day_number)
        ]

        prompt = f"""You are an expert travel planner. Please optimize or modify this existing trip itinerary and budget details based on the user instruction.

Trip Details:
Destination: {trip.destination.name}, {trip.destination.state}
Budget: INR {trip.budget:.0f}
Duration: {trip.days} days
Travelers Count: {trip.travelers_count}
Travel Type: {trip.travel_type}
Comfort Score: {trip.comfort_score}/100
Current Selected Transport: {trip.transport_mode}
Current Selected Hotel Tier: {trip.hotel_tier}

Current Budget Allocation:
{json.dumps(old_allocation, indent=2)}

Current Daily Itinerary:
{json.dumps(old_itinerary, indent=2)}

User Instruction: {instruction}

Return ONLY a valid JSON object matching the following structure (no markdown code blocks, no explanation, just raw JSON):
{{
  "costs": {{
    "transport_mode": "Flight or Train",
    "hotel_tier": "Budget or Mid or Luxury",
    "transport_cost": 5000.0,
    "hotel_cost": 6000.0,
    "food_cost": 3000.0,
    "activities_cost": 2000.0,
    "local_transport_cost": 1500.0,
    "taxes_fees_cost": 800.0,
    "emergency_reserve": 1000.0,
    "total_estimated_cost": 19300.0
  }},
  "itineraries": [
    {{
      "day_number": 1,
      "description": "Day summary",
      "activities": [
        {{"time": "Morning", "title": "Activity name", "cost": 0.0}},
        {{"time": "Afternoon", "title": "Activity name", "cost": 500.0}},
        {{"time": "Evening", "title": "Activity name", "cost": 200.0}}
      ]
    }}
  ]
}}
"""
        try:
            raw = self._chat(prompt).strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()
            data = json.loads(raw)
            return data
        except Exception as e:
            logger.warning("Error regenerating trip plan via LLM: %s. Using fallback.", e)
            return self._fallback_regenerate_trip(trip, instruction)

    def _fallback_regenerate_trip(self, trip: Any, instruction: str) -> Dict[str, Any]:
        factor = 0.8 if any(kw in instruction.lower() for kw in ["save", "cheap", "lower", "budget", "reduce", "less"]) else 1.0
        
        old_alloc = trip.budget_allocation
        transport_cost = (old_alloc.transport_cost if old_alloc else 3000.0) * factor
        hotel_cost = (old_alloc.hotel_cost if old_alloc else 4000.0) * factor
        food_cost = (old_alloc.food_cost if old_alloc else 2000.0) * factor
        activities_cost = (old_alloc.activities_cost if old_alloc else 1500.0) * factor
        local_transport_cost = (old_alloc.local_transport_cost if old_alloc else 1000.0) * factor
        taxes_fees_cost = (old_alloc.taxes_fees_cost if old_alloc else 500.0) * factor
        emergency_reserve = (old_alloc.emergency_reserve if old_alloc else 1000.0) * factor
        
        total_cost = transport_cost + hotel_cost + food_cost + activities_cost + local_transport_cost + taxes_fees_cost + emergency_reserve
        
        itineraries = [
            {
                "day_number": day.day_number,
                "description": day.description or f"Enjoy a relaxed day around {trip.destination.name}.",
                "activities": [
                    {
                        "time": act.get("time", "Morning"),
                        "title": f"Modified: {act.get('title')}" if factor < 1.0 else act.get("title"),
                        "cost": round(act.get("cost", 0.0) * factor, 2)
                    } for act in (day.activities or [])
                ]
            } for day in sorted(trip.itineraries, key=lambda x: x.day_number)
        ]
        
        return {
            "costs": {
                "transport_mode": "Train" if factor < 1.0 else trip.transport_mode,
                "hotel_tier": "Budget" if factor < 1.0 else trip.hotel_tier,
                "transport_cost": round(transport_cost, 2),
                "hotel_cost": round(hotel_cost, 2),
                "food_cost": round(food_cost, 2),
                "activities_cost": round(activities_cost, 2),
                "local_transport_cost": round(local_transport_cost, 2),
                "taxes_fees_cost": round(taxes_fees_cost, 2),
                "emergency_reserve": round(emergency_reserve, 2),
                "total_estimated_cost": round(total_cost, 2)
            },
            "itineraries": itineraries
        }

    async def explain_itinerary(self, trip: Any) -> Dict[str, Any]:
        """
        Produce a structured explanation of budget allocation grounded in actual decision data.
        
        This completely replaces the old LLM-generated Markdown approach with:
        1. Decision metadata extracted from calculate_costs logic
        2. Validated financial reconciliation
        3. Real alternatives (not fabricated)
        4. Optional LLM-powered summarization (cannot override facts)
        """
        from app.services import explainability
        from app.schemas import ExplainabilityResponse, TripMetadata, FinancialSummary
        
        logger.info(f"Building structured explainability for trip {trip.id}")
        
        alloc = trip.budget_allocation
        if not alloc:
            logger.warning(f"Trip {trip.id} has no budget allocation; cannot explain")
            return {"error": "Trip has no budget allocation data"}
        
        try:
            # 1. Assemble trip metadata
            trip_metadata = TripMetadata(
                destination_name=trip.destination.name,
                destination_state=trip.destination.state,
                trip_duration_days=trip.days,
                traveler_count=trip.travelers_count,
                comfort_score=trip.comfort_score,
                travel_type=trip.travel_type,
                starting_city=None,  # Could be loaded from user preferences if available
                destination_category=trip.destination.category
            )
            
            # 2. Build cost explanations (fully grounded in actual logic)
            cost_explanations = explainability.assemble_cost_explanations(
                trip=trip,
                costs_dict={
                    "transport_mode": trip.transport_mode,
                    "transport_cost": alloc.transport_cost,
                    "hotel_tier": trip.hotel_tier,
                    "hotel_cost": alloc.hotel_cost,
                    "food_cost": alloc.food_cost,
                    "activities_cost": alloc.activities_cost,
                    "local_transport_cost": alloc.local_transport_cost,
                    "taxes_fees_cost": alloc.taxes_fees_cost,
                    "emergency_reserve": alloc.emergency_reserve,
                    "total_estimated_cost": trip.total_estimated_cost,
                },
                budget=trip.budget,
                days=trip.days,
                travelers=trip.travelers_count,
                comfort_score=trip.comfort_score,
                travel_type=trip.travel_type,
                starting_city=None,
                destination=trip.destination
            )
            
            # 3. Calculate financial summary
            subtotal = (alloc.transport_cost + alloc.hotel_cost + alloc.food_cost + 
                       alloc.activities_cost + alloc.local_transport_cost + alloc.taxes_fees_cost)
            total_with_contingency = subtotal + alloc.emergency_reserve
            
            financial_summary = FinancialSummary(
                total_budget=trip.budget,
                total_estimated_cost=trip.total_estimated_cost,
                remaining_budget=round(trip.budget - trip.total_estimated_cost, 2),
                contingency_included=True,
                contingency_amount=alloc.emergency_reserve,
                contingency_percentage=round(alloc.emergency_reserve / subtotal * 100.0, 1) if subtotal > 0 else 0.0
            )
            
            # 4. Optional AI summarization (must be grounded in facts)
            ai_summary = None
            if self.is_available:
                try:
                    ai_summary = await self._generate_summary_from_facts(
                        trip=trip,
                        cost_explanations=cost_explanations,
                        financial_summary=financial_summary
                    )
                except Exception as e:
                    logger.warning(f"AI summary generation failed: {e}. Continuing without.")
            
            # 5. Build recommendations (only include if real alternatives exist)
            recommendations = []
            # Example: If comfort score is high but budget is tight, suggest downgrade
            if trip.comfort_score > 70 and financial_summary.remaining_budget < 5000:
                recommendations.append({
                    "action": "Consider reducing comfort level",
                    "savings_potential": round(financial_summary.remaining_budget + 10000, 2),
                    "trade_offs": ["Fewer premium activities", "Mid-range instead of luxury accommodation"],
                    "implementation": "Reduce comfort score to 60 and replan"
                })
            
            # 6. Assemble response
            response_data = {
                "trip_id": trip.id,
                "trip_metadata": trip_metadata.dict(),
                "financial_summary": financial_summary.dict(),
                "cost_explanations": [exp for exp in cost_explanations],
                "ai_summary": ai_summary,
                "recommendations": recommendations,
                "has_alternative_prices": True,
                "missing_decision_data": [],
                "data_source": "calculated"
            }
            
            logger.info(f"Successfully built explainability for trip {trip.id}")
            return response_data
            
        except Exception as e:
            logger.exception(f"Error building structured explainability: {e}")
            # Fallback to basic deterministic explanation
            return self._fallback_structured_explain(trip)
    
    async def _generate_summary_from_facts(
        self,
        trip: Any,
        cost_explanations: List[Dict],
        financial_summary: Dict
    ) -> Optional[str]:
        """
        Use LLM to generate a summary that is grounded in verified facts.
        
        The LLM cannot:
        - Invent cost values
        - Claim unsupported decision factors influenced the choice
        - Make unsupported financial recommendations
        """
        # Build fact-based prompt
        facts = f"""
Trip to {trip.destination.name}:
- Budget: ₹{trip.budget:,.0f}
- Estimated cost: ₹{trip.total_estimated_cost:,.0f}
- Comfort score: {trip.comfort_score}/100
- Duration: {trip.days} days
- Travelers: {trip.travelers_count}

Key allocations:
- Accommodation ({trip.hotel_tier}): ₹{financial_summary.get('allocations', {}).get('Accommodation', 0):,.0f}
- Transport ({trip.transport_mode}): ₹{financial_summary.get('allocations', {}).get('Inter-city Transport', 0):,.0f}
- Food: ₹{financial_summary.get('allocations', {}).get('Food & Dining', 0):,.0f}
- Contingency: ₹{financial_summary['contingency_amount']:,.0f} ({financial_summary['contingency_percentage']:.1f}%)

Financial status: {financial_summary['remaining_budget']:,.0f} remaining after estimated costs
"""
        
        prompt = f"""Summarize this trip's budget allocation in 2-3 sentences.
        
{facts}

Be specific with numbers and reasoning. Do not invent costs or suggest unsupported changes."""
        
        try:
            summary = self._chat(prompt).strip()
            return summary if len(summary) < 500 else summary[:500] + "..."
        except Exception as e:
            logger.warning(f"LLM summary generation failed: {e}")
            return None
    
    def _fallback_structured_explain(self, trip: Any) -> Dict[str, Any]:
        """
        Deterministic fallback explanation when LLM is unavailable or fails.
        
        Returns the same structured format as explain_itinerary().
        """
        from app.schemas import TripMetadata, FinancialSummary
        
        alloc = trip.budget_allocation
        if not alloc:
            return {"error": "No budget allocation data available"}
        
        try:
            trip_metadata = TripMetadata(
                destination_name=trip.destination.name,
                destination_state=trip.destination.state,
                trip_duration_days=trip.days,
                traveler_count=trip.travelers_count,
                comfort_score=trip.comfort_score,
                travel_type=trip.travel_type,
                destination_category=trip.destination.category
            )
            
            financial_summary = FinancialSummary(
                total_budget=trip.budget,
                total_estimated_cost=trip.total_estimated_cost,
                remaining_budget=round(trip.budget - trip.total_estimated_cost, 2),
                contingency_included=True,
                contingency_amount=alloc.emergency_reserve,
                contingency_percentage=round(alloc.emergency_reserve / (trip.total_estimated_cost - alloc.emergency_reserve) * 100.0, 1) if trip.total_estimated_cost > alloc.emergency_reserve else 0.0
            )
            
            # Simple cost explanations for each category
            cost_explanations = [
                {
                    "category": "Accommodation",
                    "selected_option": f"{trip.hotel_tier} Hotel",
                    "selected_cost": alloc.hotel_cost,
                    "estimated_cost": alloc.hotel_cost,
                    "allocation_percentage": round(alloc.hotel_cost / trip.budget * 100, 1),
                    "decision_factors": [f"Comfort score: {trip.comfort_score}/100", f"Duration: {trip.days} days"],
                    "alternatives": None,
                    "explanation": f"Based on comfort score {trip.comfort_score}/100, selected {trip.hotel_tier} tier accommodation."
                },
                {
                    "category": "Inter-city Transportation",
                    "selected_option": trip.transport_mode,
                    "selected_cost": alloc.transport_cost,
                    "estimated_cost": alloc.transport_cost,
                    "allocation_percentage": round(alloc.transport_cost / trip.budget * 100, 1),
                    "decision_factors": [f"Comfort score: {trip.comfort_score}/100"],
                    "alternatives": None,
                    "explanation": f"{trip.transport_mode} selected based on comfort preferences ({trip.comfort_score}/100)."
                },
                {
                    "category": "Food & Dining",
                    "selected_option": f"₹{alloc.food_cost / trip.days:,.0f}/day per person",
                    "selected_cost": alloc.food_cost,
                    "estimated_cost": alloc.food_cost,
                    "allocation_percentage": round(alloc.food_cost / trip.budget * 100, 1),
                    "decision_factors": [f"Days: {trip.days}", f"Travelers: {trip.travelers_count}"],
                    "alternatives": None,
                    "explanation": f"Daily food budget of ₹{alloc.food_cost / trip.days / trip.travelers_count:,.0f} per person based on destination and comfort level."
                },
                {
                    "category": "Activities & Admissions",
                    "selected_option": f"Activities & entry fees",
                    "selected_cost": alloc.activities_cost,
                    "estimated_cost": alloc.activities_cost,
                    "allocation_percentage": round(alloc.activities_cost / trip.budget * 100, 1),
                    "decision_factors": [f"Comfort score: {trip.comfort_score}/100"],
                    "alternatives": None,
                    "explanation": f"Activity budget allocated based on comfort level and trip duration."
                },
                {
                    "category": "Local Transportation",
                    "selected_option": "Local transit",
                    "selected_cost": alloc.local_transport_cost,
                    "estimated_cost": alloc.local_transport_cost,
                    "allocation_percentage": round(alloc.local_transport_cost / trip.budget * 100, 1),
                    "decision_factors": [f"Days: {trip.days}"],
                    "alternatives": None,
                    "explanation": f"Local transport budget for {trip.days} days of destination travel."
                },
                {
                    "category": "Taxes & Fees",
                    "selected_option": "Service tax & fees",
                    "selected_cost": alloc.taxes_fees_cost,
                    "estimated_cost": alloc.taxes_fees_cost,
                    "allocation_percentage": round(alloc.taxes_fees_cost / trip.budget * 100, 1),
                    "decision_factors": [],
                    "alternatives": None,
                    "explanation": "GST and service charges on accommodation, transport, and activities."
                },
                {
                    "category": "Contingency & Emergency Reserve",
                    "selected_option": f"{financial_summary.contingency_percentage:.1f}% buffer",
                    "selected_cost": alloc.emergency_reserve,
                    "estimated_cost": alloc.emergency_reserve,
                    "allocation_percentage": round(alloc.emergency_reserve / trip.budget * 100, 1),
                    "decision_factors": ["Standard travel contingency"],
                    "alternatives": None,
                    "explanation": "Emergency reserve for unexpected expenses and price variations."
                }
            ]
            
            return {
                "trip_id": trip.id,
                "trip_metadata": trip_metadata.dict(),
                "financial_summary": financial_summary.dict(),
                "cost_explanations": cost_explanations,
                "ai_summary": None,
                "recommendations": [],
                "has_alternative_prices": False,
                "missing_decision_data": ["Alternative pricing not calculated in fallback mode"],
                "data_source": "fallback"
            }
        except Exception as e:
            logger.exception(f"Fallback explanation also failed: {e}")
            return {"error": f"Cannot generate explanation: {str(e)}"}


    async def generate_multistop_plan(
        self,
        stops: List[Dict[str, Any]],
        budget: float,
        special: str,
    ) -> Dict[str, Any]:
        """
        Generate a multi-stop travel plan covering several destinations in sequence.
        Each stop is { destination: str, days: int }.
        Returns a structured JSON with per-leg itineraries and cost breakdown.
        """
        from app.services.multistop_calculator import MultiStopCostCalculator, MultiStopItineraryValidator
        
        logger.info(f"generate_multistop_plan: Starting with {len(stops)} stops, budget={budget}")
        
        if not self.is_available:
            logger.info("AI service unavailable, using fallback")
            data = self._fallback_multistop_plan(stops, budget, special)
            logger.info("Fallback plan generated, resolving coordinates...")
            data = await self._with_resolved_stop_coordinates(data, stops)
            logger.info("Coordinates resolved")
            # Apply calculator to ensure valid structure
            calculator = MultiStopCostCalculator(budget, stops)
            allocations = calculator.allocate_budget()
            self._apply_calculator_allocations(data, allocations, stops)
            return data

        stops_desc = "\n".join(
            [f"  - Stop {i+1}: {s['destination']} for {s['days']} day(s)" for i, s in enumerate(stops)]
        )
        total_days = sum(s['days'] for s in stops)
        stop_destinations = " → ".join(s['destination'] for s in stops)
        
        # Calculate budget allocations for reference in prompt
        calculator = MultiStopCostCalculator(budget, stops)
        allocations = calculator.allocate_budget()
        
        # Build preference injection
        preference_instruction = ""
        if special:
            preference_instruction = f"\nIMPORTANT: User has special requests/dietary needs: {special}\nEnsure ALL food recommendations and activity suggestions honor this. Every meal suggestion must align with these preferences."

        prompt = f"""You are an expert Indian travel planner. Generate a highly detailed, destination-specific multi-stop trip plan for these consecutive destinations:
{stops_desc}

Trip Info:
- Total Budget: INR {budget:.0f}
- Total Duration: {total_days} days
- Budget Allocation Guide (reference only - ensure costs fit within total):
  - Per night accommodation: ₹{allocations['stops'][0]['allocation']['accommodation_per_night']:.0f}
  - Per day food: ₹{allocations['stops'][0]['allocation']['food_per_day']:.0f}
  - Per day activities: ₹{allocations['stops'][0]['allocation']['activities_per_day']:.0f}
  - Per day local transport: ₹{allocations['stops'][0]['allocation']['local_transport_per_day']:.0f}{preference_instruction}

CRITICAL RULES FOR DESTINATION SPECIFICITY:
1. For EACH destination, research and use ACTUAL local attractions, restaurants, and experiences - NOT generic templates like "Old Quarter Walk", "Bazaar & Handicraft", "Scenic Viewpoint".
2. Activities MUST be vivid, specific, and action-oriented. Examples:
   - Good: "Sunrise hike to Arunachaleswara Temple via jungle trail"
   - Bad: "Visit historical temple"
3. Every activity MUST include destination-specific insider knowledge in the 'notes' field.

STRUCTURAL RULES:
1. For EACH leg (stop), generate EXACTLY the specified number of days.
2. Day 1 of each leg must start with arrival / transit from previous stop.
3. Last day of EVERY leg (except the final one) must end with transit to the next stop.
4. Final leg must end with check-out and return home.
5. Budget per leg should be proportional to its days. DO NOT allocate equal budget per stop regardless of duration.
6. All activity costs must be realistic INR values based on destination cost of living.
7. Every activity title must be VIVID and SPECIFIC - never use generic terms like "Sightseeing", "Lunch", "Shopping", "Relaxation".
8. Each activity MUST include a 1-sentence 'notes' field with insider tips, best times, or local recommendations.
9. Each leg MUST include:
   a. 'highlights' - a list of 3-4 SPECIFIC must-see attractions for that destination (not generic).
   b. 'must_try_food' - a list of 2-3 SPECIFIC iconic local dishes or street foods (use REAL local names where possible).
   c. 'travel_to_next' - object with 'mode' (Train/Bus/Flight/Road), 'duration' (e.g. '4 hrs'), 'approx_cost' (INR). Omit ONLY for the final leg.
   d. 'best_time_tip' - one sentence tip about the best time of day or season for this destination.
   e. 'coordinates' - object with 'lat' and 'lng' float values (approx geographic center of the destination).
10. The root JSON object MUST include a 'packing_list' array with 8-10 specific items relevant to this entire route and season.
11. Add 'global_day_range' to each leg: [start_day, end_day] counting across all stops (e.g., Stop 1: [1,2], Stop 2: [3,5], Stop 3: [6,7]).

Return ONLY a valid JSON object (no markdown, no explanation):
{{
  "trip_name": "{stop_destinations} Multi-Stop Journey",
  "total_estimated_cost": {budget:.0f},
  "packing_list": ["Comfortable trekking shoes", "Light cotton clothing", "Sunscreen (SPF 50)", "Power bank"],
  "legs": [
    {{
      "destination": "First City",
      "days": 2,
      "estimated_cost": 18000.0,
      "global_day_range": [1, 2],
      "best_time_tip": "Visit early morning to avoid crowds at the main temples.",
      "coordinates": {{"lat": 28.6139, "lng": 77.2090}},
      "highlights": ["Specific Attraction Name 1", "Specific Attraction Name 2", "Specific Attraction Name 3"],
      "must_try_food": ["Local Dish Name 1", "Street Food Name 2"],
      "travel_to_next": {{"mode": "Train", "duration": "3 hrs", "approx_cost": 400}},
      "itinerary": [
        {{
          "day_number": 1,
          "description": "Engaging day summary with specific activities",
          "activities": [
            {{"time": "Morning",   "title": "Specific arrival/transit activity",    "cost": 0.0,   "notes": "Insider tip about this activity."}},
            {{"time": "Afternoon", "title": "Specific vivid afternoon activity",  "cost": 400.0, "notes": "Why this is special; local recommendation."}}
          ]
        }}
      ]
    }}
  ]
}}
"""
        try:
            raw = self._chat(prompt).strip()
            if "```" in raw:
                parts = raw.split("```")
                for part in parts:
                    p = part.strip()
                    if p.startswith("json"):
                        p = p[4:].strip()
                    if p.startswith("{"):
                        raw = p
                        break
            data = json.loads(raw)
            
            # Normalise numeric fields
            data["total_estimated_cost"] = float(data.get("total_estimated_cost", 0))
            for leg in data.get("legs", []):
                leg["estimated_cost"] = float(leg.get("estimated_cost", 0))
                if "global_day_range" not in leg:
                    leg["global_day_range"] = None  # Will be set by calculator
                for day in leg.get("itinerary", []):
                    for act in day.get("activities", []):
                        act["cost"] = float(act.get("cost", 0))
            
            # Validate itinerary
            logger.info("Validating LLM itinerary...")
            validator = MultiStopItineraryValidator()
            validation = validator.validate(data, stops)
            if not validation["is_valid"]:
                logger.warning("LLM itinerary validation errors: %s", validation["errors"])
                # Fall back if critical errors
                data = self._fallback_multistop_plan(stops, budget, special)
            else:
                # Apply global day ranges if not present
                self._apply_calculator_allocations(data, allocations, stops)
            
            logger.info("Resolving coordinates for LLM itinerary...")
            return await self._with_resolved_stop_coordinates(data, stops)
        except Exception as e:
            logger.exception("Error generating multistop plan via LLM: %s. Using fallback.", e)
            logger.info("Generating fallback plan...")
            data = self._fallback_multistop_plan(stops, budget, special)
            logger.info("Fallback plan generated, resolving coordinates...")
            data = await self._with_resolved_stop_coordinates(data, stops)
            logger.info("Coordinates resolved")
            # Apply calculator to ensure valid structure
            calculator = MultiStopCostCalculator(budget, stops)
            allocations = calculator.allocate_budget()
            self._apply_calculator_allocations(data, allocations, stops)
            logger.info("Fallback plan complete")
            return data
    
    def _apply_calculator_allocations(self, itinerary: Dict[str, Any], allocations: Dict[str, Any], stops: List[Dict[str, Any]]) -> None:
        """Apply budget calculator results to itinerary (adds global day ranges and adjusted costs if needed)."""
        legs = itinerary.get("legs", [])
        for idx, leg in enumerate(legs):
            if idx < len(allocations["stops"]):
                calc_stop = allocations["stops"][idx]
                leg["global_day_range"] = calc_stop["global_day_range"]

    @staticmethod
    def _normalise_destination(destination: str) -> str:
        return " ".join("".join(
            character if character.isalnum() else " " for character in destination.lower()
        ).split())

    async def _resolve_destination_coordinates(self, destination: str) -> Optional[Dict[str, float]]:
        """Return an actual map position, or no position when it cannot be verified."""
        normalized = self._normalise_destination(destination)
        for name, (lat, lng) in KNOWN_DESTINATION_COORDINATES.items():
            if normalized == name or normalized.startswith(f"{name} "):
                return {"lat": lat, "lng": lng}

        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                response = await client.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={"q": f"{destination}, India", "format": "jsonv2", "limit": 1},
                    headers={"User-Agent": "BudgetBound/1.0 (trip map coordinate lookup)"},
                )
                response.raise_for_status()
                results = response.json()
            if results:
                return {"lat": float(results[0]["lat"]), "lng": float(results[0]["lon"])}
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
            logger.info("Could not geocode multi-stop destination %r: %s", destination, error)
        return None

    async def _with_resolved_stop_coordinates(
        self, data: Dict[str, Any], stops: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Use the submitted stop names as the source of truth for map pins.

        AI-provided coordinates can be hallucinated, so they must not determine
        where a route is drawn.  A stop with no verified result intentionally
        has no pin rather than a misleading one.
        """
        import asyncio
        
        legs = data.get("legs", [])
        
        # Resolve coordinates concurrently with timeout protection
        async def resolve_with_timeout(destination: str, timeout: int = 5) -> Optional[Dict[str, float]]:
            try:
                return await asyncio.wait_for(
                    self._resolve_destination_coordinates(destination),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.warning("Coordinate resolution timeout for %r", destination)
                return None
            except Exception as e:
                logger.warning("Coordinate resolution error for %r: %s", destination, e)
                return None
        
        # Create concurrent tasks for all stops
        tasks = [
            resolve_with_timeout(stop["destination"]) 
            for stop in stops[:len(legs)]
        ]
        coordinates_list = await asyncio.gather(*tasks, return_exceptions=False)
        
        for index, stop in enumerate(stops):
            if index >= len(legs):
                break
            legs[index]["destination"] = stop["destination"]
            legs[index]["coordinates"] = coordinates_list[index] if index < len(coordinates_list) else None
        
        return data

    def _fallback_multistop_plan(self, stops: List[Dict[str, Any]], budget: float, special: str) -> Dict[str, Any]:
        """
        Generate fallback multi-stop plan using:
        - Destination-specific activities from destination_database
        - Real transfer options from transfer_service
        - Preference application (vegetarian/non-veg, adventure level, etc.)
        - Deterministic cost calculator for reconciliation
        """
        from app.services.multistop_calculator import MultiStopCostCalculator
        from app.services.destination_database import get_activities_for_destination, get_restaurants_for_destination, get_must_try_food
        from app.services.transfer_service import estimate_transfer
        
        # Parse preferences
        special_lower = (special or "").lower()
        is_vegetarian = "vegetarian" in special_lower or "veg" in special_lower
        is_non_veg = "non-vegetarian" in special_lower or "non-veg" in special_lower or "meat" in special_lower or "fish" in special_lower
        is_adventure = "adventure" in special_lower or "trekking" in special_lower or "hiking" in special_lower
        is_budget = "budget" in special_lower or "cheap" in special_lower
        is_luxury = "luxury" in special_lower or "premium" in special_lower
        
        total_days = sum(s["days"] for s in stops)
        stop_destinations = " → ".join(s["destination"] for s in stops)
        calculator = MultiStopCostCalculator(budget, stops)
        allocations = calculator.allocate_budget()
        
        legs = []
        current_global_day = 1
        
        for i, s in enumerate(stops):
            dest = s["destination"]
            days = s["days"]
            is_last = i == len(stops) - 1
            next_dest = stops[i + 1]["destination"] if not is_last else None
            
            # Get this stop's allocation
            stop_alloc = allocations["stops"][i]
            stop_total = stop_alloc["stop_total"]
            global_day_range = stop_alloc["global_day_range"]
            
            # Get destination-specific data
            dest_activities = get_activities_for_destination(dest, vegetarian_only=is_vegetarian, count=4)
            dest_restaurants = get_restaurants_for_destination(dest, vegetarian_only=is_vegetarian)
            dest_must_try = get_must_try_food(dest, vegetarian=is_vegetarian)
            
            # Get transfer options if not last stop
            transfer_info = None
            if not is_last:
                transfer_info = estimate_transfer(dest, next_dest)
            
            # Build destination-specific itinerary
            itinerary_days = []
            activities_per_day = []  # Track which activities for which day
            
            for d in range(days):
                day_num = d + 1
                global_day_num = current_global_day + d
                activities = []
                
                if d == 0:
                    # First day: arrival
                    activities.append({
                        "time": "Morning",
                        "title": f"Arrive in {dest} & check into accommodation",
                        "cost": 0.0,
                        "notes": f"Settle in, freshen up, and explore your immediate neighborhood. Rest after travel if needed."
                    })
                    
                    if days == 1:
                        # Single-day stop: pack more activities
                        if dest_activities:
                            act = dest_activities[0]
                            activities.append({
                                "time": "Afternoon",
                                "title": act.title,
                                "cost": round(stop_alloc["allocation"]["activities_per_day"] * 0.4, 0),
                                "notes": act.description[:100] + "..."  # Truncate for brevity
                            })
                        
                        if dest_restaurants:
                            rest = dest_restaurants[0]
                            activities.append({
                                "time": "Evening",
                                "title": f"Dinner at {rest.name}",
                                "cost": round(stop_alloc["allocation"]["food_per_day"] * 0.6, 0),
                                "notes": f"Try {', '.join(rest.specialties[:2])}. Cuisine: {rest.cuisine}"
                            })
                    else:
                        # Multi-day: ease in on first day
                        activities.append({
                            "time": "Afternoon",
                            "title": f"Explore {dest}'s main neighborhood & local market",
                            "cost": round(stop_alloc["allocation"]["activities_per_day"] * 0.3, 0),
                            "notes": f"Get oriented and find your rhythm in the city."
                        })
                        
                        if dest_restaurants:
                            rest = dest_restaurants[0]
                            activities.append({
                                "time": "Evening",
                                "title": f"Dinner at local restaurant",
                                "cost": round(stop_alloc["allocation"]["food_per_day"] * 0.4, 0),
                                "notes": f"Try a signature regional dish: {rest.specialties[0] if rest.specialties else 'local cuisine'}"
                            })
                
                elif d == days - 1 and not is_last:
                    # Last day before transit: prepare for departure
                    if dest_activities and len(dest_activities) > 1:
                        act = dest_activities[1]
                        activities.append({
                            "time": "Morning",
                            "title": f"Final activity: {act.title}",
                            "cost": round(stop_alloc["allocation"]["activities_per_day"] * 0.4, 0),
                            "notes": act.description[:80] + "..."
                        })
                    
                    activities.append({
                        "time": "Afternoon",
                        "title": f"Lunch & prepare for transit to {next_dest}",
                        "cost": round(stop_alloc["allocation"]["food_per_day"] * 0.5, 0),
                        "notes": f"Leisurely meal before heading to transit."
                    })
                    
                    if transfer_info:
                        activities.append({
                            "time": "Evening",
                            "title": f"Travel from {dest} to {next_dest} ({transfer_info['mode'].title()})",
                            "cost": round(float(stop_alloc["allocation"]["inter_city_transport"] or 0), 0),
                            "notes": f"{transfer_info['mode'].title()}, {transfer_info['duration_display']}. {transfer_info['notes']}"
                        })
                
                elif d == days - 1 and is_last:
                    # Last day of entire trip
                    activities.append({
                        "time": "Morning",
                        "title": f"Final morning in {dest}",
                        "cost": round(stop_alloc["allocation"]["activities_per_day"] * 0.3, 0),
                        "notes": f"Final exploration or revisit favorite spot."
                    })
                    
                    activities.append({
                        "time": "Afternoon",
                        "title": f"Check out & depart {dest}",
                        "cost": 0.0,
                        "notes": f"Head to station/airport for return journey home."
                    })
                
                else:
                    # Middle days: varied activities
                    if dest_activities and (d % len(dest_activities)) < len(dest_activities):
                        act = dest_activities[d % len(dest_activities)]
                        activities.append({
                            "time": "Morning",
                            "title": act.title,
                            "cost": round(stop_alloc["allocation"]["activities_per_day"] * 0.4, 0),
                            "notes": act.description[:100] + "..."
                        })
                    
                    if dest_restaurants and (d % len(dest_restaurants)) < len(dest_restaurants):
                        rest = dest_restaurants[d % len(dest_restaurants)]
                        activities.append({
                            "time": "Afternoon",
                            "title": f"Lunch & local dining",
                            "cost": round(stop_alloc["allocation"]["food_per_day"] * 0.5, 0),
                            "notes": f"Try {rest.cuisine} cuisine at {rest.name[:30]}"
                        })
                    else:
                        activities.append({
                            "time": "Afternoon",
                            "title": f"Lunch & exploration",
                            "cost": round(stop_alloc["allocation"]["food_per_day"] * 0.5, 0),
                            "notes": f"Experience local dining and culture."
                        })
                    
                    if len(dest_activities) > 2:
                        act = dest_activities[(d + 1) % len(dest_activities)]
                        activities.append({
                            "time": "Evening",
                            "title": f"Evening activity: {act.title}",
                            "cost": round(stop_alloc["allocation"]["activities_per_day"] * 0.3, 0),
                            "notes": act.description[:80] + "..."
                        })
                
                itinerary_days.append({
                    "day_number": day_num,
                    "global_day_number": global_day_num,
                    "description": f"Day {global_day_num} - {dest}" + (" (Arrival)" if d == 0 else (" (Departure)" if d == days - 1 and not is_last else "")),
                    "activities": activities
                })
            
            # Build leg with destination-specific content
            highlights = []
            if dest_activities:
                highlights = [a.title for a in dest_activities[:3]]
            
            leg = {
                "destination": dest,
                "days": days,
                "estimated_cost": stop_total,
                "global_day_range": global_day_range,
                "coordinates": None,  # Will be filled by _with_resolved_stop_coordinates
                "best_time_tip": f"Early mornings are ideal for exploring {dest} before crowds arrive.",
                "highlights": highlights or [f"Key attraction in {dest}", f"Local market", f"Cultural experience"],
                "must_try_food": dest_must_try or [f"Regional specialty", f"Street food"],
                "itinerary": itinerary_days
            }
            
            if not is_last and next_dest and transfer_info:
                leg["travel_to_next"] = {
                    "mode": transfer_info["mode"].title(),
                    "duration": transfer_info["duration_display"],
                    "approx_cost": round(transfer_info["cost_per_person"], 0),
                    "frequency": transfer_info["frequency"],
                    "notes": transfer_info["notes"]
                }
            
            legs.append(leg)
            current_global_day += days
        
        return {
            "trip_name": f"{stop_destinations} Multi-Stop Journey",
            "total_estimated_cost": float(allocations["grand_total"]),
            "budget_breakdown": allocations["category_breakdown"],
            "packing_list": [
                "Comfortable walking shoes / sneakers",
                "Light layers for varying temperatures",
                "Sunscreen and sunglasses",
                "Reusable water bottle",
                "Universal power adapter & power bank",
                "Basic first-aid kit",
                "Travel documents folder",
                "Lightweight backpack",
                "Quick-dry towel",
                "Portable charger"
            ],
            "legs": legs,
            "data_source": "fallback",  # Indicate this is fallback-generated
        }


gemini_service = GroqTravelService()
