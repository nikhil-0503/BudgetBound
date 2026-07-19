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

    async def generate_personalized_plan(self, keywords: str, budget: float, days: int, special: str) -> Dict[str, Any]:
        """
        Ask the LLM to generate a customized travel plan based on user preferences.
        """
        if not self.is_available:
            return self._fallback_personalized_plan(keywords, budget, days, special)

        prompt = f"""You are a professional travel planner. Please generate a customized travel plan for a trip matching these preferences:
Destination Keywords/Location: {keywords}
Budget Limit: INR {budget:.0f}
Duration: {days} days
Special Requests/Dietary/Accommodation: {special or 'None'}

Return ONLY a valid JSON object matching the following structure (no markdown code blocks, no explanation, just raw JSON):
{{
  "plan_name": "Trip to {keywords if keywords else 'Destination'}",
  "destination": "{keywords if keywords else 'Destination'}",
  "estimated_cost": {budget * 0.8:.1f},
  "summary": "Short overview of the trip design...",
  "days": [
    {{
      "day_number": 1,
      "description": "Day summary",
      "activities": [
        {{"time": "Morning", "title": "Arrival & Check-in", "cost": 0.0}},
        {{"time": "Afternoon", "title": "Local sightseeing", "cost": 300.0}},
        {{"time": "Evening", "title": "Dinner at local diner", "cost": 250.0}}
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
            logger.warning("Error generating personalized plan via LLM: %s. Using fallback.", e)
            return self._fallback_personalized_plan(keywords, budget, days, special)

    def _fallback_personalized_plan(self, keywords: str, budget: float, days: int, special: str) -> Dict[str, Any]:
        dest = keywords if keywords else "India"
        return {
            "plan_name": f"Custom Trip to {dest}",
            "destination": dest,
            "estimated_cost": round(budget * 0.85, 2),
            "summary": f"A customized package designed around {dest} with custom requests: '{special or 'none'}'.",
            "days": [
                {
                    "day_number": i,
                    "description": f"Explore the local attractions and custom spots in {dest}.",
                    "activities": [
                        {"time": "Morning", "title": f"Visit historical spots in {dest}", "cost": 150.0},
                        {"time": "Afternoon", "title": f"Local lunch & marketplace walk", "cost": 500.0},
                        {"time": "Evening", "title": f"Relaxing leisure walk & local dinner", "cost": 300.0}
                    ]
                } for i in range(1, days + 1)
            ]
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
        Produce a markdown explanation explaining the trip's budget allocation choices.
        """
        if not self.is_available:
            return {"explanation": self._fallback_explain(trip)}

        alloc = trip.budget_allocation
        costs_summary = f"""- Budget: INR {trip.budget}
- Total Estimated Cost: INR {trip.total_estimated_cost}
- Transport Mode: {trip.transport_mode} (Cost: INR {alloc.transport_cost if alloc else 0})
- Hotel Tier: {trip.hotel_tier} (Cost: INR {alloc.hotel_cost if alloc else 0})
- Food Cost: INR {alloc.food_cost if alloc else 0}
- Activity Entry Cost: INR {alloc.activities_cost if alloc else 0}
- Local Commuting Cost: INR {alloc.local_transport_cost if alloc else 0}
- Taxes & Fees: INR {alloc.taxes_fees_cost if alloc else 0}
- Emergency Reserves: INR {alloc.emergency_reserve if alloc else 0}
"""

        itinerary_summary = "\n".join([
            f"Day {day.day_number}: {day.description or 'Sightseeing'} (Activities count: {len(day.activities or [])})"
            for day in sorted(trip.itineraries, key=lambda x: x.day_number)
        ])

        prompt = f"""You are a helpful travel planning consultant. Please analyze this trip details and budget allocation, then write a comprehensive, readable explanation in markdown.

Trip Details:
Destination: {trip.destination.name}, {trip.destination.state}
Travel Type: {trip.travel_type}
Comfort Score Selected: {trip.comfort_score}/100

Budget Allocation:
{costs_summary}

Itinerary Overview:
{itinerary_summary}

Write a detailed budget analysis report in Markdown. Include:
1. An overview of the budget allocation (whether it's well-proportioned or top-heavy).
2. Why specific transport modes and lodging tiers were selected based on the Comfort Score.
3. Recommendations for where they can cut back to save money, and where they should consider spending more.
4. Tips for managing emergency buffers and dining expenses at {trip.destination.name}.

Write in a friendly, professional tone. Return ONLY the markdown text (do not wrap in markdown json fields, etc.).
"""
        try:
            reply = self._chat(prompt).strip()
            return {"explanation": reply}
        except Exception as e:
            logger.warning("Error generating budget explanation via LLM: %s. Using fallback.", e)
            return {"explanation": self._fallback_explain(trip)}

    def _fallback_explain(self, trip: Any) -> str:
        alloc = trip.budget_allocation
        return f"""### Budget Explanation Report for **{trip.destination.name}**

This report breaks down your **INR {trip.budget:,.2f}** budget and the estimated cost of **INR {trip.total_estimated_cost:,.2f}**.

#### 1. Accommodation ({trip.hotel_tier} Tier)
- Lodging cost makes up **INR {alloc.hotel_cost if alloc else 0:,.2f}**. 
- Selected tier is based on comfort level **{trip.comfort_score}/100**.

#### 2. Transport ({trip.transport_mode})
- Transit cost is estimated at **INR {alloc.transport_cost if alloc else 0:,.2f}**.

#### 3. Dining & Outer buffers
- Food expenses total **INR {alloc.food_cost if alloc else 0:,.2f}** over {trip.days} days.
- Local commuting: **INR {alloc.local_transport_cost if alloc else 0:,.2f}**.
- Activities & Admissions: **INR {alloc.activities_cost if alloc else 0:,.2f}**.
- Emergency Reserves: **INR {alloc.emergency_reserve if alloc else 0:,.2f}**.

#### 📝 Recommendations to Save Money
* **Transport**: Opt for sleeper trains or overnight buses instead of flights to reduce the transport bill.
* **Accommodation**: Look into budget homestays, hostels, or guesthouses.
"""


gemini_service = GroqTravelService()
