import os
import json
import logging
import httpx
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load .env before reading env vars (singleton is created at import time)
load_dotenv()

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
# Free model on Groq — change via GROQ_MODEL env var if needed
GROQ_MODEL = os.getenv("GROQ_MODEL", "gemma2-9b-it")


class GroqTravelService:
    """
    Groq-powered travel itinerary generator.
    Falls back silently to template generation if the API key is absent or the call fails.
    """

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if self.api_key:
            logger.info("Groq AI service initialised with model %s", GROQ_MODEL)
        else:
            logger.warning(
                "GROQ_API_KEY not set — AI itinerary generation disabled, using templates."
            )

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    def _chat(self, prompt: str) -> str:
        """Send a single-turn chat message and return the response text."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": GROQ_MODEL,
            "messages": [{
                "role": "user",
                "content": prompt
            }],
        }
        response = httpx.post(
            GROQ_API_URL,
            headers=headers,
            json=payload,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

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

        prompt = f"""You are a professional Indian travel planner. Generate a detailed day-by-day itinerary for the following trip.

Trip details:
- Destination: {destination_name}, {state}
- Destination category: {category}
- Travel type preference: {travel_type}
- Duration: {days} days
- Comfort level: {comfort_label} (score {comfort_score}/100)
- Known attractions: {attractions_str}
- Average food cost per meal: INR {avg_food_cost:.0f}
- Average activity/entry cost: INR {avg_activity_cost:.0f}

Rules:
1. Day 1 must start with "Arrival & Hotel Check-in" (cost 0) in the Morning slot.
2. The last day must end with departure. Include souvenir shopping and check-out.
3. Middle days should include 3 time slots: Morning, Afternoon, Evening.
4. Activity titles must be specific and vivid — tailored to the travel type ({travel_type}) and comfort level.
5. Each activity must have an estimated cost in INR (use 0 for free activities).
6. Use the known attractions naturally — don't just list them mechanically.
7. Keep descriptions engaging but concise (1-2 sentences per day).

Return ONLY a valid JSON array with this exact schema (no markdown, no explanation):
[
  {{
    "day_number": 1,
    "description": "Brief day summary...",
    "activities": [
      {{"time": "Morning", "title": "Activity name", "cost": 0.0}},
      {{"time": "Afternoon", "title": "Activity name", "cost": 500.0}},
      {{"time": "Evening", "title": "Activity name", "cost": 200.0}}
    ]
  }}
]"""

        try:
            raw = self._chat(prompt).strip()

            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            itinerary = json.loads(raw)

            # Basic validation — ensure it's a list with the right number of days
            if not isinstance(itinerary, list) or len(itinerary) != days:
                logger.warning(
                    "LLM returned %d days but expected %d. Falling back to templates.",
                    len(itinerary) if isinstance(itinerary, list) else 0,
                    days,
                )
                return None

            # Sanitise cost fields to float
            for day in itinerary:
                for act in day.get("activities", []):
                    act["cost"] = float(act.get("cost", 0.0))

            logger.info("AI itinerary generated for %s (%d days)", destination_name, days)
            return itinerary

        except httpx.HTTPStatusError as e:
            logger.warning("Groq API error %s: %s — falling back.", e.response.status_code, e.response.text)
            return None
        except Exception as e:
            logger.warning("AI itinerary generation failed: %s — falling back to templates.", e)
            return None

    async def chat_assistant(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Interactive travel chat companion.
        """
        if not self.is_available:
            raise NotImplementedError(
                "AI service not configured. Add GROQ_API_KEY to your .env file."
            )

        system = (
            "You are BudgetBound's AI travel companion specialised in Indian destinations. "
            "Help users plan budget-conscious trips, suggest destinations, explain costs, "
            "and answer any travel-related questions. Keep responses concise and practical."
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
            return {"reply": reply.strip()}
        except httpx.HTTPStatusError as e:
            logger.error("Groq chat error %s: %s", e.response.status_code, e.response.text)
            raise RuntimeError(f"AI service error: {e.response.status_code}") from e
        except Exception as e:
            logger.error("Groq chat failed: %s", e)
            raise RuntimeError(f"AI service error: {e}") from e


gemini_service = GroqTravelService()
