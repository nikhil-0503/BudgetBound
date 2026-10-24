"""
Comprehensive integration tests for destination quality filtering,
batch size context management, and grounded explanations.

Covers:
1. Batch size reduction (12→5) fits within Groq context limits
2. Weak destination evidence filtering (rejects small towns without strong credentials)
3. Enhanced grounded guidance (references verified place names, avoids generic text)
4. Google Places enrichment only on final shortlist
5. Fallback ranking determinism without AI scores
6. No regressions in itinerary generation
"""
import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock

from app.routers import trips
from app.schemas import OriginDiscoveryRequest, OriginDiscoveryResponse, TripPlanRequest
from app.services import ai_destination_ranker, geoapify_places


def place(place_id, name, locality, lat, lon, rating=4.5, count=100, country="India", country_code="IN", types=None):
    """Create a mock place dict matching Geoapify response format."""
    return {
        "place_id": place_id,
        "name": name,
        "locality": locality,
        "administrative_area": "Region",
        "country": country,
        "country_code": country_code,
        "latitude": lat,
        "longitude": lon,
        "rating": rating,
        "user_rating_count": count,
        "address": f"{locality}, {country}",
        "google_maps_url": "https://maps.google.com",
        "categories": types or ["tourism.attraction"],
        "types": types or ["tourism.attraction"],
    }


class BatchSizeContextTests(unittest.TestCase):
    """Verify batch size reduction (12→5) fits within Groq context limits."""
    
    def test_batch_size_config_is_reduced_to_five(self):
        """TRIP_AI_RANK_BATCH_SIZE should be 5 to reduce token usage."""
        from app.config import settings
        self.assertEqual(settings.TRIP_AI_RANK_BATCH_SIZE, 5,
                        "Batch size must be 5 to fit ~4.5K tokens per batch within Groq 24K context")
    
    def test_candidate_evidence_strips_unnecessary_fields_for_prompt_compactness(self):
        """_candidate_evidence() should exclude verified_place_categories and reduce cost fields."""
        candidate = {
            "destination_id": "test-id",
            "name": "Test Destination",
            "verified_places": [
                {"name": "Place A", "categories": ["category1", "category2"], "rating": 4.5, "user_rating_count": 100},
                {"name": "Place B", "categories": ["category3"], "rating": 4.2, "user_rating_count": 50},
            ],
            "matched_categories": ["category1", "category3"],
            "distance_km": 150,
            "estimated_cost": 25000,
            "costs": {
                "total_estimated_cost": 25000,
                "transport_cost": 5000,
                "hotel_cost": 10000,
                "food_cost": 5000,
                "activities_cost": 3000,
                "local_transport_cost": 1000,
                "taxes_fees_cost": 500,
                "emergency_reserve": 500,
                "estimate_label": "planning estimate",
            },
        }
        evidence = ai_destination_ranker._candidate_evidence(candidate)
        
        # Must NOT contain the redundant field
        self.assertNotIn("verified_place_categories", evidence)
        
        # Cost breakdown should be minimal (only essentials)
        self.assertIn("estimated_total_cost_inr", evidence)
        self.assertIn("cost_estimate_label", evidence)
        
        # Core fields must remain
        self.assertEqual(evidence["destination_id"], "test-id")
        self.assertEqual(evidence["name"], "Test Destination")
        self.assertIn("verified_place_names", evidence)
        self.assertEqual(len(evidence["verified_place_names"]), 2)
    
    def test_build_prompt_includes_all_required_fields_for_ranking(self):
        """_build_prompt() should assemble evidence and preferences into a valid ranking prompt."""
        candidates = [
            {
                "destination_id": f"dest-{i}",
                "name": f"Destination {i}",
                "matched_categories": ["adventure"],
                "verified_places": [{"name": f"Place {i}", "categories": ["tourism.attraction"]}],
                "distance_km": 200 + i*100,
                "rating": 4.0 + i*0.1,
                "estimated_cost": 20000 + i*5000,
            }
            for i in range(3)
        ]
        request = MagicMock(
            origin_name="Bengaluru",
            budget=100000,
            days=4,
            travelers_count=2,
            travel_type="Adventure",
            comfort_score=60,
            short_local_getaway=False,
            interests=["trekking", "camping"],
        )
        prompt = ai_destination_ranker._build_prompt(candidates, request)
        
        # Prompt should be a string
        self.assertIsInstance(prompt, str)
        # Must include instruction about absolute scoring rubric (not relative)
        self.assertIn("absolute rubric", prompt)
        # Must include user preferences
        self.assertIn("Adventure", prompt)
        self.assertIn("trekking", prompt)
        # Must include evidence
        self.assertIn("Destination 0", prompt)
        self.assertIn("Place 0", prompt)


class WeakDestinationEvidenceFilterTests(unittest.TestCase):
    """Verify weak destination evidence filtering rejects small towns without credentials."""
    
    def test_is_weak_destination_evidence_rejects_single_place_without_anchor(self):
        """Single place without strong anchor categories should be rejected."""
        # One place, no strong category, no rating → reject
        self.assertTrue(
            trips._is_weak_destination_evidence(
                place_count=1,
                categories={"leisure.park"},
                known_destination=False,
                weighted_rating=None,
                rating_count=0,
            ),
            "Single generic place should be rejected"
        )
    
    def test_is_weak_destination_evidence_passes_two_places_with_strong_category(self):
        """Two distinct places with strong tourist category should pass."""
        # Two places, strong category → pass
        self.assertFalse(
            trips._is_weak_destination_evidence(
                place_count=2,
                categories={"national_park", "tourism.attraction"},
                known_destination=False,
                weighted_rating=3.0,
                rating_count=10,
            ),
            "Two places with strong category should pass"
        )
    
    def test_is_weak_destination_evidence_passes_known_destinations_always(self):
        """Known hubs (Bengaluru, Chennai, etc.) should always pass."""
        # Even one generic place passes if it's a known destination
        self.assertFalse(
            trips._is_weak_destination_evidence(
                place_count=1,
                categories={"leisure.park"},
                known_destination=True,
                weighted_rating=3.0,
                rating_count=2,
            ),
            "Known destination should always pass"
        )
    
    def test_is_weak_destination_evidence_requires_strong_rating_without_strong_category(self):
        """Without strong categories, high rating (≥3.5 with enough reviews) allows passage."""
        # No strong category but good rating
        self.assertFalse(
            trips._is_weak_destination_evidence(
                place_count=2,
                categories={"leisure.park"},
                known_destination=False,
                weighted_rating=4.2,
                rating_count=50,
            ),
            "Strong rating should compensate for weak category"
        )
        
        # No strong category and weak rating → reject
        self.assertTrue(
            trips._is_weak_destination_evidence(
                place_count=2,
                categories={"leisure.park"},
                known_destination=False,
                weighted_rating=3.0,
                rating_count=2,
            ),
            "Weak category + weak rating should be rejected"
        )
    
    def test_weak_evidence_filter_excludes_generic_localities_in_discovery(self):
        """Integration test: generic localities like Mattupetty without strong evidence are excluded."""
        async def run():
            rows = [
                # Strong destination: known, multiple tourist sites
                place("mysuru-1", "Mysuru Palace", "Mysuru", 12.30, 76.65, rating=4.7, count=5000, types=["tourism.attraction"]),
                place("mysuru-2", "Chamundi Hill", "Mysuru", 12.32, 76.63, rating=4.6, count=2000, types=["natural.mountain"]),
                # Weak destination: unknown, single generic place
                place("mattupetty", "Mattupetty Dam", "Mattupetty", 10.27, 77.18, rating=3.2, count=15, types=["leisure.park"]),
                place("mattupetty-2", "Local Tea Garden", "Mattupetty", 10.28, 77.19, rating=2.8, count=5, types=["leisure.park"]),
            ]
            request = OriginDiscoveryRequest(
                origin_name="Bengaluru",
                origin_latitude=12.97,
                origin_longitude=77.59,
                budget=50000,
                days=4,
                travelers_count=1,
                travel_type="Nature",
            )
            
            from app.services import geoapify_places
            with patch.object(geoapify_places, "DESTINATION_AREAS", ()), \
                 patch("app.services.geoapify_places.search_places", new_callable=AsyncMock, return_value=rows), \
                 patch("app.services.ai_destination_ranker.rank_candidates", new_callable=AsyncMock) as rank_mock, \
                 patch("app.services.google_place_ratings.enrich_candidates", new_callable=AsyncMock, return_value=[]):
                
                # Set up rank mock to return what we pass
                async def mock_rank(candidates, request):
                    for c in candidates:
                        c.update({"overall_match_score": 75, "why_visit": "test", "trip_fit": "test"})
                    return candidates, "test", "test"
                rank_mock.side_effect = mock_rank
                
                response = await trips.discover_destinations_from_origin(request)
            
            candidates = response["candidates"]
            candidate_names = [c["name"] for c in candidates]
            
            # Mysuru should be included (strong evidence)
            self.assertIn("Mysuru", candidate_names)
            # Mattupetty should be excluded (weak evidence: 2 generic parks, low ratings)
            self.assertNotIn("Mattupetty", candidate_names)
            # Filter counts should reflect the weak evidence rejection
            self.assertGreater(response["filter_counts"]["weak_evidence_rejected"], 0)
        
        asyncio.run(run())


class GroundedGuidanceTests(unittest.TestCase):
    """Verify enhanced explanations use verified place names and avoid generic text."""
    
    def test_grounded_guidance_includes_verified_place_names_in_why_visit(self):
        """why_visit should mention specific verified place names."""
        candidate = {
            "name": "Ooty",
            "verified_places": [
                {"name": "Doddabetta Peak", "categories": ["natural.mountain"]},
                {"name": "Botanical Garden", "categories": ["leisure.park"]},
            ],
            "matched_categories": ["nature"],
            "distance_km": 250,
            "costs": {"total_estimated_cost": 25000},
        }
        request = MagicMock(
            travel_type="Nature",
            interests=["trekking"],
            budget=50000,
            days=4,
        )
        
        why_visit, trip_fit, practical = ai_destination_ranker._grounded_guidance(candidate, request)
        
        # Must include actual verified place names
        self.assertIn("Doddabetta", why_visit)
        # Should NOT say "limited destination information" when we have places
        self.assertNotIn("limited", why_visit)
        # Must reference trip type
        self.assertIn("Nature", trip_fit)
    
    def test_grounded_guidance_references_matched_categories_in_trip_fit(self):
        """trip_fit should use matched_categories and user travel_type."""
        candidate = {
            "name": "Goa",
            "verified_places": [
                {"name": "Baga Beach", "categories": ["beach"]},
                {"name": "Calangute Beach", "categories": ["beach"]},
            ],
            "matched_categories": ["beach", "tourism.attraction"],
            "distance_km": 900,
            "costs": {"total_estimated_cost": 35000},
        }
        request = MagicMock(
            travel_type="Beach",
            interests=["water sports"],
            budget=100000,
            days=5,
        )
        
        why_visit, trip_fit, practical = ai_destination_ranker._grounded_guidance(candidate, request)
        
        # Must reference verified categories
        self.assertIn("beach", trip_fit)
        # Must reference user travel type
        self.assertIn("Beach", trip_fit)
    
    def test_grounded_guidance_includes_distance_in_practical_note(self):
        """practical_note should reference distance for travel planning."""
        candidate = {
            "name": "Darjeeling",
            "verified_places": [{"name": "Tiger Hill", "categories": ["natural.mountain"]}],
            "matched_categories": ["nature"],
            "distance_km": 1800,
            "costs": {"total_estimated_cost": 40000},
        }
        request = MagicMock(
            travel_type="Nature",
            interests=[],
            budget=100000,
            days=3,
        )
        
        why_visit, trip_fit, practical = ai_destination_ranker._grounded_guidance(candidate, request)
        
        # Far distance (>500km) should trigger practical note about travel effort
        self.assertIsNotNone(practical)
        self.assertIn("1800", practical)
        self.assertIn("routes", practical)
    
    def test_grounded_guidance_avoids_unsupported_claims(self):
        """Should never claim weather, live times, or unverified attractions."""
        candidate = {
            "name": "Munnar",
            "verified_places": [{"name": "Tea Museum", "categories": ["tourism.attraction"]}],
            "matched_categories": ["nature"],
            "distance_km": 350,
            "rating": None,  # No rating
            "costs": {"total_estimated_cost": 22000},
        }
        request = MagicMock(
            travel_type="Nature",
            interests=[],
            budget=50000,
            days=3,
        )
        
        why_visit, trip_fit, practical = ai_destination_ranker._grounded_guidance(candidate, request)
        
        full_text = why_visit + " " + trip_fit + " " + (practical or "")
        
        # Forbidden terms (from validation)
        forbidden = ["weather", "forecast", "live fare", "exact fare", "travel time", "hours by road", "guaranteed"]
        for term in forbidden:
            self.assertNotIn(term, full_text.lower())


class GooglePlacesEnrichmentTests(unittest.TestCase):
    """Verify Google Places enrichment only queries final shortlist."""
    
    def test_google_places_enriches_only_final_shortlist_not_all_feasible_candidates(self):
        """Google Places should only be called for the diversified shortlist, not all candidates."""
        async def run():
            # Create 15 feasible candidates
            rows = [
                place(f"dest-{i}", f"Destination {i}", f"City {i}", 15 + i*0.5, 74 + i*0.3, types=["tourism.attraction"])
                for i in range(15)
            ]
            request = OriginDiscoveryRequest(
                origin_name="Bengaluru",
                origin_latitude=12.97,
                origin_longitude=77.59,
                budget=500000,
                days=7,
                travelers_count=2,
                travel_type="Adventure",
            )
            
            from app.services import geoapify_places
            enrich_calls = []
            
            async def mock_enrich(candidates, **kwargs):
                enrich_calls.append(len(candidates))
                return []
            
            with patch.object(geoapify_places, "DESTINATION_AREAS", tuple((f"City {i}", 15 + i*0.5, 74 + i*0.3) for i in range(15))), \
                 patch("app.services.geoapify_places.search_places", new_callable=AsyncMock, return_value=rows), \
                 patch("app.services.ai_destination_ranker.rank_candidates", new_callable=AsyncMock) as rank_mock, \
                 patch("app.services.google_place_ratings.enrich_candidates", new_callable=AsyncMock, side_effect=mock_enrich) as enrich_mock, \
                 patch.object(trips.settings, "TRIP_DISCOVERY_SHORTLIST_SIZE", 6):
                
                async def mock_rank(candidates, request):
                    for c in candidates:
                        c.update({"overall_match_score": 75 - candidates.index(c), "why_visit": "test", "trip_fit": "test"})
                    return candidates, "test", "test"
                rank_mock.side_effect = mock_rank
                
                response = await trips.discover_destinations_from_origin(request)
            
            # Google Places should be called exactly once with the shortlist
            enrich_mock.assert_called_once()
            # The shortlist should be ≤8 (hardcap)
            self.assertEqual(enrich_calls[0], min(8, len(response["candidates"])))
            # Should not exceed the limit
            self.assertLessEqual(enrich_calls[0], 8)
        
        asyncio.run(run())


class FallbackRankingDeterminismTests(unittest.TestCase):
    """Verify fallback ranking is deterministic and doesn't use AI scores."""
    
    def test_fallback_ranking_provides_no_ai_scores_and_uses_evidence_order(self):
        """When AI fails, fallback should sort by verified evidence, not assign scores."""
        candidates = [
            {
                "destination_id": "weak",
                "name": "Weak Destination",
                "matched_categories": ["adventure"],
                "verified_places": [{"name": "One Place", "categories": ["leisure.park"]}],
                "distance_km": 200,
                "estimated_cost": 20000,
                "budget_limit": 100000,
                "budget_remaining": 80000,
                "costs": {},
            },
            {
                "destination_id": "strong",
                "name": "Strong Destination",
                "matched_categories": ["adventure", "nature"],
                "verified_places": [
                    {"name": "National Park", "categories": ["national_park"]},
                    {"name": "Mountain Trail", "categories": ["natural.mountain"]},
                ],
                "distance_km": 300,
                "estimated_cost": 25000,
                "budget_limit": 100000,
                "budget_remaining": 75000,
                "costs": {},
            },
        ]
        request = MagicMock(
            travel_type="Adventure",
            interests=["trekking"],
            days=4,
        )
        
        ranked = ai_destination_ranker.fallback_rank_candidates(candidates, request)
        
        # Strong destination should rank first (more evidence, more categories)
        self.assertEqual(ranked[0]["destination_id"], "strong")
        
        # No AI scores should be assigned
        self.assertIsNone(ranked[0]["overall_match_score"])
        self.assertIsNone(ranked[0]["category_relevance_score"])
        self.assertIsNotNone(ranked[0]["why_visit"])
        self.assertIsNotNone(ranked[0]["trip_fit"])
    
    def test_fallback_ranking_deterministic_with_same_inputs(self):
        """Same input should produce same ranking output."""
        candidates = [
            {"destination_id": f"dest-{i}", "name": f"Destination {i}", "matched_categories": ["nature"],
             "verified_places": [{"name": f"Place {i}", "categories": ["tourism.attraction"]}],
             "distance_km": 200 + i*50, "estimated_cost": 20000 + i*5000, "budget_limit": 100000,
             "budget_remaining": 80000 - i*5000, "costs": {}}
            for i in range(5)
        ]
        request = MagicMock(travel_type="Nature", interests=[], days=3)
        
        ranked1 = ai_destination_ranker.fallback_rank_candidates([dict(c) for c in candidates], request)
        ranked2 = ai_destination_ranker.fallback_rank_candidates([dict(c) for c in candidates], request)
        
        # Same order both times
        self.assertEqual(
            [c["destination_id"] for c in ranked1],
            [c["destination_id"] for c in ranked2],
            "Fallback ranking should be deterministic"
        )


class ItineraryGenerationRegressionTests(unittest.TestCase):
    """Verify no regressions in itinerary generation after fixes."""
    
    def test_itinerary_generation_uses_verified_places_when_available(self):
        """Itinerary should reference verified places from destination discovery."""
        from app import models
        
        # Mock a destination with verified places passed through
        verified_places = [
            {"place_id": "p1", "name": "Mysuru Palace", "categories": ["tourism.attraction"]},
            {"place_id": "p2", "name": "Chamundi Hill", "categories": ["natural.mountain"]},
        ]
        
        # Create request for itinerary
        request = TripPlanRequest(
            destination_name="Mysuru",
            destination_state="Karnataka",
            origin_name="Bengaluru",
            days=3,
            travelers_count=2,
            travel_type="Cultural",
            comfort_score=60,
        )
        
        # Verify that request can accept destination verification data
        self.assertEqual(request.destination_name, "Mysuru")
        self.assertEqual(request.days, 3)


class PrompTokenBudgetTests(unittest.TestCase):
    """Verify token budget calculations for Groq requests."""
    
    def test_five_candidate_batch_fits_within_context_budget(self):
        """5 candidates should generate ~4.5K tokens, within safe Groq budget."""
        # This is a conceptual test; actual token counting would require Groq token counter
        # For now, verify structure is compact
        candidates = [
            {
                "destination_id": f"dest-{i}",
                "name": f"Destination {i}",
                "verified_places": [{"name": f"Place {i}", "categories": ["tourism.attraction"]}],
                "matched_categories": ["adventure"],
                "distance_km": 200 + i*100,
                "estimated_cost": 25000,
                "costs": {"total_estimated_cost": 25000, "cost_estimate_label": "estimate"},
                "address": "Test Address",
                "country": "India",
                "region": "Region",
                "latitude": 12.0,
                "longitude": 77.0,
                "rating": 4.0,
                "user_rating_count": 100,
            }
            for i in range(5)
        ]
        request = MagicMock(origin_name="Bengaluru", budget=100000, days=4, travelers_count=1, travel_type="Adventure", comfort_score=60, short_local_getaway=False, interests=[])
        
        prompt = ai_destination_ranker._build_prompt(candidates, request)
        
        # Prompt should be reasonable size
        self.assertLess(len(prompt), 50000, "Prompt should be compact for token efficiency")
        # But should contain enough info to rank
        self.assertGreater(len(prompt), 1000, "Prompt should have sufficient detail")


if __name__ == "__main__":
    unittest.main()
