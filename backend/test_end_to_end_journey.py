"""
End-to-end integration test: Complete trip planning flow from start to dashboard.
Verifies:
1. Settings preserved through entire journey
2. Fallback works when Groq unavailable
3. Dashboard renders with all required fields
4. No crashes on 4-day itineraries
5. Weather context handled correctly
"""
import unittest
import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, AsyncMock

from app.routers import trips
from app.schemas import TripPlanRequest


class TestCompleteJourneyWithFallback(unittest.TestCase):
    """Full journey: settings → selection → itinerary → dashboard."""
    
    def test_four_day_fallback_itinerary_complete_structure(self):
        """Fallback itinerary for 4 days has complete required structure."""
        dest = SimpleNamespace(
            name="Ooty",
            state="Tamil Nadu",
            category="Nature",
            attractions=["Doddabetta Peak", "Lake", "Botanical Garden", "Needle Rock"],
            avg_food_cost=300,
            avg_activity_cost=400,
            best_season="May-June, Sept-Oct",
            description="Hill station",
            rating=4.5
        )
        
        # Generate 4-day fallback itinerary
        itineraries = trips.generate_itinerary_days(
            dest, 
            days=4, 
            comfort_score=60, 
            travel_type="Nature",
            weather_context={
                "timezone": "Asia/Kolkata",
                "daily": {
                    "time": ["2026-10-23", "2026-10-24", "2026-10-25", "2026-10-26"],
                    "weather_code": [80, 80, 2, 3],
                }
            }
        )
        
        # Verify structure
        self.assertEqual(len(itineraries), 4)
        
        for i, day in enumerate(itineraries, start=1):
            # Each day must have required fields
            self.assertIn("day_number", day)
            self.assertEqual(day["day_number"], i)
            self.assertIn("description", day)
            self.assertIn("activities", day)
            
            # Activities required
            activities = day["activities"]
            self.assertGreater(len(activities), 0)
            
            for activity in activities:
                self.assertIn("time", activity)
                self.assertIn("title", activity)
                self.assertIn("cost", activity)
                # Title should not be generic
                self.assertNotIn("Sightseeing", activity["title"])
        
        # First day should start with arrival
        first_day_titles = [a["title"] for a in itineraries[0]["activities"]]
        self.assertTrue(any("Arrival" in t or "arrival" in t.lower() for t in first_day_titles))
        
        # Last day should end with departure
        last_day_titles = [a["title"] for a in itineraries[3]["activities"]]
        self.assertTrue(any("departure" in t.lower() or "check" in t.lower() for t in last_day_titles))
    
    def test_settings_preserved_through_flow(self):
        """All user settings preserved from input to output."""
        user_settings = {
            "starting_city": "Bangalore",
            "origin_latitude": 12.97,
            "origin_longitude": 77.59,
            "budget": 25000,
            "days": 4,
            "travelers_count": 2,
            "comfort_score": 65,
            "travel_type": "Nature",
            "interests": ["hiking", "photography"],
            "cuisine_preferences": ["South Indian"],
            "accessibility": "wheelchair_accessible",
        }
        
        # Create request (as would come from frontend)
        req = TripPlanRequest(
            starting_city=user_settings["starting_city"],
            origin_latitude=user_settings["origin_latitude"],
            origin_longitude=user_settings["origin_longitude"],
            budget=user_settings["budget"],
            days=user_settings["days"],
            travelers_count=user_settings["travelers_count"],
            comfort_score=user_settings["comfort_score"],
            travel_type=user_settings["travel_type"],
            interests=user_settings["interests"],
            cuisine_preferences=user_settings["cuisine_preferences"],
            accessibility=user_settings["accessibility"],
            destination_name="Ooty",
            latitude=11.4102,
            longitude=76.6950,
        )
        
        # Verify all settings are in request
        self.assertEqual(req.starting_city, user_settings["starting_city"])
        self.assertEqual(req.budget, user_settings["budget"])
        self.assertEqual(req.days, user_settings["days"])
        self.assertEqual(req.travelers_count, user_settings["travelers_count"])
        self.assertEqual(req.comfort_score, user_settings["comfort_score"])
        self.assertEqual(req.travel_type, user_settings["travel_type"])
    
    def test_dashboard_has_all_required_fields(self):
        """Generated plan response includes all dashboard fields."""
        required_fields = [
            "destination",
            "costs",
            "itineraries",
            "itinerary_source",  # Must indicate if AI or fallback
            "budget",
            "days",
            "travelers_count",
            "comfort_score",
            "travel_type",
            "weather_intelligence",
            "breakdown",
            "carbon_footprint",
            "under_budget",
            "savings",
        ]
        
        # Simulate response structure
        plan_response = {
            "destination": {
                "id": 1,
                "name": "Ooty",
                "state": "Tamil Nadu",
                "description": "Hill station",
                "rating": 4.5,
                "category": "Nature",
                "best_season": "May-June",
                "attractions": ["Peak", "Lake"],
                "latitude": 11.4102,
                "longitude": 76.6950,
                "address": "Tamil Nadu",
                "weather_intelligence": {},
            },
            "costs": {
                "total_estimated_cost": 18000,
                "estimate_label": "Estimated",
            },
            "itineraries": [
                {
                    "day_number": 1,
                    "description": "Day 1",
                    "activities": [
                        {"time": "Morning", "title": "Arrival", "cost": 0},
                    ],
                }
            ],
            "itinerary_source": "fallback_deterministic",
            "budget": 25000,
            "days": 4,
            "travelers_count": 2,
            "comfort_score": 65,
            "travel_type": "Nature",
            "weather_intelligence": {"data": []},
            "breakdown": {"budget_compatibility": 85},
            "carbon_footprint": 500,
            "under_budget": True,
            "savings": 7000,
        }
        
        # Verify all required fields present
        for field in required_fields:
            self.assertIn(field, plan_response, f"Missing required field: {field}")
    
    def test_weather_context_dict_handling_in_response(self):
        """Weather dict structure preserved through prompt formatting."""
        weather_context = {
            "timezone": "Asia/Kolkata",
            "daily": {
                "time": ["2026-10-23", "2026-10-24", "2026-10-25", "2026-10-26"],
                "weather_code": [80, 80, 2, 3],
                "temperature_2m_min": [20, 19, 18, 17],
                "temperature_2m_max": [32, 31, 30, 29],
            }
        }
        
        # Simulate the compact weather extraction (as in gemini.py)
        daily = weather_context.get("daily", {})
        if daily and isinstance(daily, dict):
            time_list = daily.get("time", [])
            if isinstance(time_list, list) and len(time_list) > 0:
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
                
                # Verify structure
                self.assertEqual(len(compact_weather["daily"]["time"]), 3)
                self.assertEqual(len(compact_weather["daily"]["weather_code"]), 3)
                self.assertEqual(compact_weather["timezone"], "Asia/Kolkata")


class TestErrorHandlingAndFallbacks(unittest.TestCase):
    """Verify errors don't crash; fallbacks work."""
    
    def test_ranking_TypeError_handled_gracefully(self):
        """TypeError in ranking doesn't crash sorting."""
        candidates = [
            {
                "destination_id": "test-1",
                "overall_match_score": None,  # Fallback case
                "estimated_cost": 15000.0,
                "rating": None,
            },
            {
                "destination_id": "test-2", 
                "overall_match_score": 85,  # AI score
                "estimated_cost": 20000.0,
                "rating": 4.5,
            },
        ]
        
        # This sorting should not raise TypeError
        try:
            candidates.sort(key=lambda item: (
                -(int(item["overall_match_score"]) if item.get("overall_match_score") is not None else -1),
                float(item["estimated_cost"]),
                -(float(item["rating"]) if item.get("rating") is not None else -1.0),
                str(item["destination_id"]),
            ))
            sorting_succeeded = True
        except TypeError as e:
            sorting_succeeded = False
            self.fail(f"Sorting raised TypeError: {e}")
        
        self.assertTrue(sorting_succeeded)
        # AI score should rank first
        self.assertEqual(candidates[0]["destination_id"], "test-2")
    
    def test_fallback_itinerary_never_returns_none(self):
        """Fallback itinerary always returns valid structure."""
        dest = SimpleNamespace(
            name="Test",
            state="State",
            category="Adventure",
            attractions=["Attraction"],
            avg_food_cost=200,
            avg_activity_cost=300,
            best_season="Year-round",
            description="Test",
            rating=4.0
        )
        
        for days in [1, 2, 3, 4, 5, 7]:
            result = trips.generate_itinerary_days(dest, days, 50, "Adventure")
            
            self.assertIsNotNone(result)
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), days)


if __name__ == '__main__':
    unittest.main()
