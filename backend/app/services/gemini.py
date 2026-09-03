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
        """Send a single-turn chat message with automatic retries for transient socket resets."""
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
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with httpx.Client(timeout=30.0) as client:
                    response = client.post(
                        GROQ_API_URL,
                        headers=headers,
                        json=payload,
                    )
                    response.raise_for_status()
                    return response.json()["choices"][0]["message"]["content"]
            except (httpx.ConnectError, httpx.NetworkError, httpx.RemoteProtocolError, OSError) as err:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(0.2 * (attempt + 1))
                    logger.info("Retrying Groq API connection after transient socket reset (attempt %d/%d): %s", attempt + 1, max_retries, err)
                    continue
                raise err

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
4. Every activity title MUST be unique, vivid, and action-oriented — tailored to {travel_type} (e.g. "Sunrise photography trek", "Sampling local thali at heritage cafe"). NEVER repeat generic titles like "Sightseeing".
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
        if not self.is_available:
            return await self._with_resolved_stop_coordinates(
                self._fallback_multistop_plan(stops, budget, special), stops
            )

        stops_desc = "\n".join(
            [f"  - Stop {i+1}: {s['destination']} for {s['days']} day(s)" for i, s in enumerate(stops)]
        )
        total_days = sum(s['days'] for s in stops)
        stop_destinations = " → ".join(s['destination'] for s in stops)

        prompt = f"""You are an expert Indian travel planner. Generate a highly detailed multi-stop trip plan for these consecutive destinations:
{stops_desc}

Trip Info:
- Total Budget: INR {budget:.0f}
- Total Duration: {total_days} days
- Special Requests / Dietary: {special or 'None'}

Rules:
1. For EACH leg (stop), generate EXACTLY the specified number of days.
2. Day 1 of each leg must start with arrival / transit from previous stop.
3. Last day of EVERY leg (except the final one) must end with transit to the next stop.
4. Final leg must end with check-out and return home.
5. Budget per leg should be proportional to its days.
6. All activity costs must be realistic INR values.
7. Every activity title must be vivid, specific, and action-oriented — never "Sightseeing" or "Lunch".
8. Each activity MUST include a 1-sentence 'notes' field with insider tips, timings, or why it is special.
9. Each leg MUST include:
   a. 'highlights' — a list of 3-4 must-see/must-do attractions for that destination.
   b. 'must_try_food' — a list of 2-3 iconic local dishes or street foods.
   c. 'travel_to_next' — object with 'mode' (Train/Bus/Flight/Road), 'duration' (e.g. '4 hrs'), 'approx_cost' (INR). Omit only for the final leg.
   d. 'best_time_tip' — one sentence tip about the best time of day or season for this destination.
   e. 'coordinates' — object with 'lat' and 'lng' float values (approx geographic coordinates of the city).
10. The root JSON object MUST include a 'packing_list' array containing 8-10 specific categorised string items to pack for this entire journey.

Return ONLY a valid JSON object (no markdown, no explanation):
{{
  "trip_name": "{stop_destinations} Multi-Stop Journey",
  "total_estimated_cost": 45000.0,
  "packing_list": ["Comfortable trekking shoes", "Light cotton clothing", "Sunscreen (SPF 50)", "Power bank"],
  "legs": [
    {{
      "destination": "First City",
      "days": 2,
      "estimated_cost": 18000.0,
      "best_time_tip": "Visit early morning to avoid crowds at the main temples.",
      "coordinates": {{"lat": 28.6139, "lng": 77.2090}},
      "highlights": ["Highlight 1", "Highlight 2", "Highlight 3"],
      "must_try_food": ["Local Dish 1", "Street Food 2"],
      "travel_to_next": {{"mode": "Train", "duration": "3 hrs", "approx_cost": 400}},
      "itinerary": [
        {{
          "day_number": 1,
          "description": "Engaging one-sentence day summary",
          "activities": [
            {{"time": "Morning",   "title": "Arrival & Hotel Check-in",          "cost": 0.0,   "notes": "Check in early to freshen up before the day begins."}},
            {{"time": "Afternoon", "title": "Specific vivid afternoon activity",  "cost": 400.0, "notes": "Insider tip or why this is worth visiting."}},
            {{"time": "Evening",   "title": "Specific vivid evening activity",    "cost": 200.0, "notes": "Best enjoyed at sunset with a local guide."}}
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
                for day in leg.get("itinerary", []):
                    for act in day.get("activities", []):
                        act["cost"] = float(act.get("cost", 0))
            return await self._with_resolved_stop_coordinates(data, stops)
        except Exception as e:
            logger.warning("Error generating multistop plan via LLM: %s. Using fallback.", e)
            return await self._with_resolved_stop_coordinates(
                self._fallback_multistop_plan(stops, budget, special), stops
            )

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
        legs = data.get("legs", [])
        for index, stop in enumerate(stops):
            if index >= len(legs):
                break
            coordinates = await self._resolve_destination_coordinates(stop["destination"])
            legs[index]["destination"] = stop["destination"]
            legs[index]["coordinates"] = coordinates
        return data

    def _fallback_multistop_plan(self, stops: List[Dict[str, Any]], budget: float, special: str) -> Dict[str, Any]:
        total_days = sum(s["days"] for s in stops)
        stop_destinations = " → ".join(s["destination"] for s in stops)
        legs = []
        for i, s in enumerate(stops):
            dest = s["destination"]
            leg_cost = round((s["days"] / max(total_days, 1)) * budget * 0.85, 2)
            is_last = i == len(stops) - 1
            next_dest = stops[i + 1]["destination"] if not is_last else None

            legs.append({
                "destination": dest,
                "days": s["days"],
                "estimated_cost": leg_cost,
                # Coordinates are filled from the real stop name before this
                # response is returned to the client.
                "coordinates": None,
                "best_time_tip": f"Early mornings are the best time to explore {dest}'s popular spots before the crowds arrive.",
                "highlights": [
                    f"Old Quarter & Heritage Walk in {dest}",
                    f"Local Bazaar & Handicraft Market",
                    f"Scenic Viewpoint / Waterfront",
                ],
                "must_try_food": [
                    f"Signature regional thali of {dest}",
                    f"Popular street snack from the local market",
                ],
                **({
                    "travel_to_next": {
                        "mode": "Train",
                        "duration": "3-4 hrs",
                        "approx_cost": round(leg_cost * 0.08, 0)
                    }
                } if next_dest else {}),
                "itinerary": [
                    {
                        "day_number": d + 1,
                        "description": f"{'Arrival day' if d == 0 else 'Explore'} {dest} highlights — Day {d + 1}",
                        "activities": [
                            {
                                "time": "Morning",
                                "title": f"Arrive & check-in at {dest}" if d == 0 else f"Morning heritage walk through {dest}'s old quarter",
                                "cost": 0.0,
                                "notes": f"{'Freshen up and orient yourself around the local neighbourhood.' if d == 0 else 'Start early to catch the market vendors setting up stalls.'}"
                            },
                            {
                                "time": "Afternoon",
                                "title": f"Local sightseeing & regional lunch in {dest}",
                                "cost": round(leg_cost / (s["days"] * 3), 2),
                                "notes": "Try the regional thali at a well-reviewed local eatery for an authentic taste."
                            },
                            {
                                "time": "Evening",
                                "title": f"Sunset stroll & cultural dinner in {dest}",
                                "cost": round(leg_cost / (s["days"] * 4), 2),
                                "notes": "Evenings are lively — look for street performances or local music near the main square."
                            },
                        ]
                    } for d in range(s["days"])
                ]
            })
        return {
            "trip_name": f"{stop_destinations} Multi-Stop Journey",
            "total_estimated_cost": round(budget * 0.85, 2),
            "packing_list": [
                "Universal Power Adapter & High Capacity Power Bank",
                "Comfortable walking shoes/sneakers",
                "Basic First-Aid Kit & personal medications",
                "Light layers for variable evening temperatures",
                "Reusable water bottle (stay hydrated!)",
                "Government ID & Travel Documents folder"
            ],
            "legs": legs,
        }


gemini_service = GroqTravelService()
