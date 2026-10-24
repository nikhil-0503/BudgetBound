import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from app.routers import trips
from app.schemas import OriginDiscoveryRequest, OriginDiscoveryResponse


def place(place_id, name, locality, lat, lon, rating=4.5, count=100, country="India", country_code="IN", types=None):
    return {"place_id": place_id, "name": name, "locality": locality, "administrative_area": "Region", "country": country, "country_code": country_code, "latitude": lat, "longitude": lon, "rating": rating, "user_rating_count": count, "address": f"{locality}, {country}", "google_maps_url": "https://maps.google.com", "types": types or ["natural.mountain", "national_park"]}


class OriginDiscoveryTests(unittest.TestCase):
    def setUp(self):
        # Discovery tests exercise Geoapify but never make live Google requests.
        self.discovery_events = []
        async def fake_enrich(_candidates, **_kwargs):
            self.discovery_events.append("ratings")
            return []
        self.rating_patch = patch("app.services.google_place_ratings.enrich_candidates", new_callable=AsyncMock, side_effect=fake_enrich)
        self.rating_mock = self.rating_patch.start()
        async def fake_rank(candidates, request):
            self.discovery_events.append("ranking")
            for candidate in candidates:
                candidate.update({"value_score": 75, "overall_match_score": 75, "category_relevance_score": 80,
                                  "interest_match_score": 70, "comfort_suitability_score": 75,
                                  "duration_suitability_score": 80, "destination_quality_score": 65,
                                  "breakdown": {}, "match_reasons": ["Matches the requested category"],
                                  "tradeoffs": [], "explanation": "Matches the requested category."})
            return candidates, "json_prompt_validated", "unit-test-model"
        self.rank_patch = patch("app.services.ai_destination_ranker.rank_candidates", new_callable=AsyncMock, side_effect=fake_rank)
        self.rank_mock = self.rank_patch.start()

    def tearDown(self):
        self.rating_patch.stop()
        self.rank_patch.stop()

    def test_selected_bengaluru_origin_coordinates_are_separate_from_grid_centers_and_origin_is_excluded(self):
        async def run():
            rows = [
                place("origin-poi", "Bengaluru Park", "Bengaluru", 12.97, 77.59),
                place("mysuru-poi", "Mysuru Hill Park", "Mysuru", 12.30, 76.65),
            ]
            request = OriginDiscoveryRequest(origin_name="Bengaluru", origin_latitude=12.97, origin_longitude=77.59, budget=20000, days=4, travel_type="Adventure")
            from app.services import geoapify_places
            with patch.object(geoapify_places, "DESTINATION_AREAS", (("Puri", 19.8135, 85.8312),)), patch("app.services.geoapify_places.search_places", new_callable=AsyncMock, return_value=rows) as search:
                response = await trips.discover_destinations_from_origin(request)
            calls = [call.kwargs for call in search.await_args_list]
            self.assertTrue(any(call["latitude"] == 12.97 and call["longitude"] == 77.59 and call["radius_m"] == 100000 for call in calls))
            self.assertTrue(any(call["latitude"] == 19.8135 and call["longitude"] == 85.8312 and call["radius_m"] == 60000 for call in calls))
            self.assertTrue(all(call["categories"] == geoapify_places.category_values("Adventure") for call in calls))
            self.assertEqual(response["origin"]["latitude"], 12.97)
            self.assertEqual(response["origin"]["longitude"], 77.59)
            self.assertNotIn("Bengaluru", [candidate["name"] for candidate in response["candidates"]])
        asyncio.run(run())

    def test_swapped_or_inconsistent_origin_coordinates_are_rejected_before_geoapify(self):
        from fastapi import HTTPException
        async def check(request):
            with patch("app.services.geoapify_places.search_places", new_callable=AsyncMock) as search:
                with self.assertRaises(HTTPException) as caught:
                    await trips.discover_destinations_from_origin(request)
                search.assert_not_awaited()
            self.assertEqual(caught.exception.status_code, 422)
        asyncio.run(check(OriginDiscoveryRequest(origin_name="Bengaluru", origin_latitude=77.59, origin_longitude=12.97, budget=20000, days=4)))
        asyncio.run(check(OriginDiscoveryRequest(origin_name="Bengaluru", origin_latitude=17.385, origin_longitude=78.4867, budget=20000, days=4)))

    def test_failed_origin_geocoding_does_not_substitute_a_default_location(self):
        from fastapi import HTTPException
        from app.services.weather import WeatherServiceError
        request = OriginDiscoveryRequest(origin_name="Unresolvable starting place", budget=20000, days=4)
        async def run():
            with patch("app.routers.trips.resolve_location", new_callable=AsyncMock, side_effect=WeatherServiceError("unavailable")), \
                 patch("app.services.geoapify_places.search_places", new_callable=AsyncMock) as search:
                with self.assertRaises(HTTPException) as caught:
                    await trips.discover_destinations_from_origin(request)
            self.assertEqual(caught.exception.status_code, 422)
            search.assert_not_awaited()
        asyncio.run(run())

    def test_partial_coordinate_pairs_are_rejected_by_request_schema(self):
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            OriginDiscoveryRequest(origin_name="Bengaluru", origin_latitude=12.97, budget=20000, days=4)
        for latitude, longitude in ((float("nan"), 77.59), (12.97, float("inf")), (91, 77.59), (12.97, 181)):
            with self.assertRaises(ValidationError):
                OriginDiscoveryRequest(origin_name="Bengaluru", origin_latitude=latitude, origin_longitude=longitude, budget=20000, days=4)

    def test_ai_preselection_orders_strong_evidence_and_does_not_drop_feasible_candidates(self):
        candidates = [
            {"destination_id": "weak", "evidence_count": 1, "verified_places": [{"name": "One"}], "matched_categories": ["Adventure"], "estimated_cost": 5000, "distance_km": 100},
            {"destination_id": "strong", "evidence_count": 6, "verified_places": [{"name": "A"}, {"name": "B"}, {"name": "C"}], "matched_categories": ["Adventure", "Nature"], "estimated_cost": 9000, "distance_km": 200},
        ]
        ordered = trips._select_origin_candidates_for_ai(candidates, limit=1)
        self.assertEqual([item["destination_id"] for item in ordered], ["strong", "weak"])

    def test_routes_and_generic_road_records_are_excluded_from_destination_evidence(self):
        for name in ("SH79", "Railway Station Road", "NH 44", "Old Bypass"):
            self.assertTrue(trips._is_low_quality_destination_record({"name": name, "locality": "Majjigepura"}), name)
        self.assertFalse(trips._is_low_quality_destination_record({"name": "Mysuru Palace", "locality": "Mysuru", "categories": ["tourism.attraction"]}))

    def test_shortlist_is_hard_capped_at_eight_and_does_not_pad_short_results(self):
        many = [{"destination_id": str(index), "name": f"Destination {index}", "region": f"Region {index}", "distance_km": 100 + index} for index in range(12)]
        few = many[:3]
        self.assertEqual(len(trips._select_diverse_shortlist(many, 20)), 8)
        self.assertEqual(len(trips._select_diverse_shortlist(few, 6)), 3)

    def test_estimates_use_destination_distance_and_trip_inputs_with_shared_assumptions_documented(self):
        short = OriginDiscoveryRequest(origin_name="Bengaluru", budget=50000, days=3, travelers_count=1, comfort_score=30)
        long = OriginDiscoveryRequest(origin_name="Bengaluru", budget=50000, days=5, travelers_count=3, comfort_score=80)
        near_cost = trips._origin_candidate_cost(120, short)
        far_cost = trips._origin_candidate_cost(900, short)
        group_cost = trips._origin_candidate_cost(120, long)
        self.assertLess(near_cost["total_estimated_cost"], far_cost["total_estimated_cost"])
        self.assertNotEqual(near_cost["total_estimated_cost"], group_cost["total_estimated_cost"])
        self.assertIn("same per-person planning assumptions", near_cost["shared_cost_assumptions"])
        self.assertIn("not a fare", near_cost["estimate_label"])

    def test_discovery_returns_diverse_shortlist_after_ranking_and_enriches_only_those_candidates(self):
        async def run():
            locations = [
                ("Mysuru", 12.30, 76.65), ("Ooty", 11.41, 76.69), ("Goa", 15.30, 74.12),
                ("Jaipur", 26.91, 75.78), ("Varanasi", 25.32, 82.97), ("Puri", 19.81, 85.83),
                ("Darjeeling", 27.04, 88.27), ("Munnar", 10.09, 77.06), ("Kochi", 9.93, 76.27),
                ("Mumbai", 19.08, 72.88),
            ]
            rows = [place(f"poi-{index}", f"{city} nature park", city, lat, lon) for index, (city, lat, lon) in enumerate(locations)]
            request = OriginDiscoveryRequest(origin_name="Bengaluru", origin_latitude=12.97, origin_longitude=77.59, budget=200000, days=4, travelers_count=2, travel_type="Nature")
            from app.services import geoapify_places
            with patch.object(geoapify_places, "DESTINATION_AREAS", tuple((city, lat, lon) for city, lat, lon in locations)), \
                 patch.object(trips.settings, "TRIP_DISCOVERY_SHORTLIST_SIZE", 6), \
                 patch.object(trips.settings, "TRIP_GOOGLE_RATING_ENRICH_LIMIT", 8), \
                 patch("app.services.geoapify_places.search_places", new_callable=AsyncMock, return_value=rows):
                response = await trips.discover_destinations_from_origin(request)
            OriginDiscoveryResponse.model_validate(response)
            self.assertEqual(response["candidate_count"], 6)
            self.assertEqual(len(response["candidates"]), 6)
            self.assertGreater(response["examined_candidate_count"], len(response["candidates"]))
            self.assertEqual(response["filter_counts"]["shortlisted"], 6)
            self.assertEqual(self.discovery_events, ["ranking", "ratings"])
            enriched_ids = {item["destination_id"] for item in self.rating_mock.await_args.args[0]}
            returned_ids = {item["destination_id"] for item in response["candidates"]}
            self.assertEqual(enriched_ids, returned_ids)
            self.assertTrue(all(item["why_visit"] and item["trip_fit"] for item in response["candidates"]))
        asyncio.run(run())

    def test_google_rating_fields_survive_discovery_response_schema_without_blocking_selection(self):
        async def run():
            rows = [place("geo-ooty", "Ooty hill trek", "Ooty", 11.41, 76.69)]
            async def enrich(candidates, **_kwargs):
                self.discovery_events.append("ratings")
                candidates[0].update({"rating": 4.5, "user_rating_count": 2341, "google_place_id": "g-ooty", "rating_source": "google_places", "google_maps_uri": "https://maps.google.com/ooty"})
                return []
            request = OriginDiscoveryRequest(origin_name="Bengaluru", origin_latitude=12.97, origin_longitude=77.59, budget=50000, days=4, travel_type="Adventure")
            with patch("app.services.geoapify_places.search_places", new_callable=AsyncMock, return_value=rows), patch("app.services.google_place_ratings.enrich_candidates", new_callable=AsyncMock, side_effect=enrich):
                response = await trips.discover_destinations_from_origin(request)
            candidate = OriginDiscoveryResponse.model_validate(response).candidates[0]
            self.assertEqual(candidate.rating, 4.5)
            self.assertEqual(candidate.user_rating_count, 2341)
            self.assertEqual(candidate.google_place_id, "g-ooty")
            self.assertEqual(self.discovery_events, ["ranking", "ratings"])
            self.assertEqual(candidate.destination_id, "geo-ooty")
        asyncio.run(run())

    def test_unavailable_google_ratings_do_not_remove_a_selectable_destination(self):
        async def run():
            rows = [place("geo-ooty", "Ooty hill trek", "Ooty", 11.41, 76.69)]
            request = OriginDiscoveryRequest(origin_name="Bengaluru", origin_latitude=12.97, origin_longitude=77.59, budget=50000, days=4, travel_type="Adventure")
            with patch("app.services.geoapify_places.search_places", new_callable=AsyncMock, return_value=rows), \
                 patch("app.services.google_place_ratings.enrich_candidates", new_callable=AsyncMock, side_effect=RuntimeError("provider unavailable")):
                response = await trips.discover_destinations_from_origin(request)
            self.assertEqual(len(response["candidates"]), 1)
            self.assertEqual(response["candidates"][0]["destination_id"], "geo-ooty")
            self.assertIsNone(response["candidates"][0]["rating"])
            self.assertTrue(any("shown without ratings" in warning for warning in response["warnings"]))
        asyncio.run(run())

    def test_aliases_group_duplicate_cities_and_single_generic_locality_is_rejected(self):
        async def run():
            rows = [
                place("mysore-one", "Mysore Museum", "Mysore", 12.30, 76.65, types=["entertainment.museum"]),
                place("mysuru-two", "Mysuru Heritage Fort", "Mysuru", 12.31, 76.66, types=["tourism.sights.fort"]),
                place("locality", "Local park", "Anandnagar", 12.5, 77.0, types=["leisure.park"]),
            ]
            request = OriginDiscoveryRequest(origin_name="Bengaluru", origin_latitude=12.97, origin_longitude=77.59, budget=20000, days=4, travel_type="City Exploration")
            from app.services import geoapify_places
            with patch.object(geoapify_places, "DESTINATION_AREAS", ()), patch("app.services.geoapify_places.search_places", new_callable=AsyncMock, return_value=rows):
                response = await trips.discover_destinations_from_origin(request)
            self.assertEqual(len(response["candidates"]), 1)
            self.assertEqual(response["candidates"][0]["name"], "Mysuru")
            self.assertEqual(response["filter_counts"]["low_quality_localities_rejected"], 1)
        asyncio.run(run())

    def test_reusable_india_validator_requires_iso_code_and_valid_coordinates(self):
        from app.services.geoapify_places import is_destination_in_india
        self.assertTrue(is_destination_in_india(place("in", "Ooty", "Ooty", 11.4, 76.7)))
        for country, code in (("Pakistan", "PK"), ("Nepal", "NP"), ("Bangladesh", "BD"), ("Sri Lanka", "LK")):
            self.assertFalse(is_destination_in_india(place(code, country, country, 20, 80, country=country, country_code=code)))
        self.assertFalse(is_destination_in_india(place("missing", "Unknown", "Unknown", 20, 80, country_code=None)))
        self.assertFalse(is_destination_in_india(place("malformed", "Unknown", "Unknown", 20, 80, country_code="I-N")))
        self.assertFalse(is_destination_in_india(place("bad-coords", "Unknown", "Unknown", 91, 80)))

    def test_mixed_indian_and_foreign_places_filters_foreign_before_ranking_even_when_highly_rated(self):
        async def run():
            rows = [place("india", "Adventure park", "Mysuru", 12.3, 76.65), place("pak", "Pakistan adventure", "Lahore", 31.5, 74.3, 5.0, 100000, "Pakistan", "PK"), place("nepal", "Nepal trek", "Pokhara", 28.2, 83.9, 5.0, 100000, "Nepal", "NP")]
            request = OriginDiscoveryRequest(origin_name="Bengaluru", origin_latitude=12.97, origin_longitude=77.59, budget=20000, days=4, travelers_count=1, travel_type="Adventure")
            with patch("app.services.geoapify_places.search_places", AsyncMock(return_value=rows)):
                response = await trips.discover_destinations_from_origin(request)
            OriginDiscoveryResponse.model_validate(response)
            self.assertTrue(response["candidates"])
            self.assertEqual({candidate["country_code"] for candidate in response["candidates"]}, {"IN"})
            self.assertEqual([candidate["name"] for candidate in response["candidates"]], ["Mysuru"])
            self.assertFalse(any("Pakistan" in str(candidate) or "Lahore" in str(candidate) for candidate in response["candidates"]))
        asyncio.run(run())

    def test_budget_increase_does_not_weaken_country_filter(self):
        async def run():
            rows = [place("pak", "Pakistan trek", "Lahore", 31.5, 74.3, country="Pakistan", country_code="PK")]
            for budget in (20000, 2000000):
                request = OriginDiscoveryRequest(origin_name="Bengaluru", origin_latitude=12.97, origin_longitude=77.59, budget=budget, days=4, travelers_count=1, travel_type="Adventure")
                with patch("app.services.geoapify_places.search_places", AsyncMock(return_value=rows)):
                    response = await trips.discover_destinations_from_origin(request)
                self.assertEqual(response["candidates"], [])
                self.assertEqual(response["data_source"], "geoapify_empty")
        asyncio.run(run())

    def test_unverified_country_result_is_honestly_empty(self):
        async def run():
            rows = [place("unknown", "Unknown destination", "Somewhere", 20, 80, country="", country_code=None)]
            request = OriginDiscoveryRequest(origin_name="Bengaluru", origin_latitude=12.97, origin_longitude=77.59, budget=20000, days=4)
            with patch("app.services.geoapify_places.search_places", AsyncMock(return_value=rows)):
                response = await trips.discover_destinations_from_origin(request)
            self.assertEqual(response["candidates"], [])
            self.assertTrue(any("verified Indian country metadata" in message for message in response["warnings"]))
        asyncio.run(run())

    def test_origin_excluded_candidates_ranked_and_under_budget(self):
        async def run():
            result_places = [place("a", "Local cafe", "Chennai", 13.08, 80.27), place("b", "Hill viewpoint", "Ooty", 11.41, 76.69), place("c", "Fort", "Mysuru", 12.30, 76.65)]
            mock_search = AsyncMock(return_value=result_places)
            request = OriginDiscoveryRequest(origin_name="Chennai", origin_latitude=13.08, origin_longitude=80.27, budget=100000, days=4, travelers_count=2, travel_type="Nature", comfort_score=50)
            with patch("app.services.geoapify_places.search_places", mock_search):
                response = await trips.discover_destinations_from_origin(request)
            self.assertEqual(response["origin"]["name"], "Chennai")
            self.assertTrue(response["candidates"])
            names = {candidate["name"] for candidate in response["candidates"]}
            self.assertNotIn("Chennai", names)
            self.assertTrue(names.intersection({"Ooty", "Mysuru"}))
            self.assertTrue(all(item["costs"]["total_estimated_cost"] <= request.budget for item in response["candidates"]))
            self.assertTrue(all(item["costs"]["transport_cost"] > 0 for item in response["candidates"]))
        asyncio.run(run())

    def test_ai_failure_returns_explicit_unscored_fallback_without_dropping_feasible_candidate(self):
        async def run():
            request = OriginDiscoveryRequest(origin_name="Bengaluru", origin_latitude=12.97, origin_longitude=77.59, budget=20000, days=4, travelers_count=1, travel_type="Adventure")
            rows = [place("mysuru", "Verified adventure park", "Mysuru", 12.30, 76.65)]
            from app.services.ai_destination_ranker import AIRankingError
            with patch("app.services.geoapify_places.search_places", AsyncMock(return_value=rows)), \
                 patch("app.services.ai_destination_ranker.rank_candidates", new_callable=AsyncMock, side_effect=AIRankingError("Groq unavailable")):
                response = await trips.discover_destinations_from_origin(request)
            self.assertEqual(response["ranking_source"], "fallback")
            self.assertEqual(response["ranking_mode"], "verified_evidence_fallback")
            self.assertEqual(len(response["candidates"]), 1)
            self.assertIsNone(response["candidates"][0]["value_score"])
            self.assertIsNone(response["candidates"][0]["overall_match_score"])
            self.assertTrue(any("no AI match scores were assigned" in warning for warning in response["warnings"]))
        asyncio.run(run())

    def test_no_affordable_destination_is_not_returned(self):
        async def run():
            mock_search = AsyncMock(return_value=[place("x", "Hill point", "Ooty", 11.41, 76.69)])
            request = OriginDiscoveryRequest(origin_name="Delhi", origin_latitude=28.61, origin_longitude=77.20, budget=1000, days=5, travelers_count=4)
            with patch("app.services.geoapify_places.search_places", mock_search):
                response = await trips.discover_destinations_from_origin(request)
            self.assertEqual(response["candidates"], [])
            self.assertFalse(response["budget_feasible"])
            self.assertTrue(any("exceed the budget" in warning for warning in response["warnings"]))
        asyncio.run(run())

    def test_short_local_getaway_uses_configured_lower_threshold(self):
        request = OriginDiscoveryRequest(origin_name="Chennai", origin_latitude=13.08, origin_longitude=80.27, budget=100000, days=2, travelers_count=1, short_local_getaway=True)
        candidate = {"name": "Nearby town", "distance_km": 25, "estimated_cost": 9000, "budget_limit": request.budget, "rating": None, "destination_id": "nearby"}
        self.assertEqual(len(trips._rank_origin_fallback([candidate])), 1)
        self.assertIsNone(candidate["value_score"])
        far_cost = trips._origin_candidate_cost(25, request)
        self.assertLess(far_cost["total_estimated_cost"], request.budget)

    def test_comfort_cost_is_continuous_and_budget_filter_matches_displayed_cost(self):
        candidate = {"name": "Mysuru", "distance_km": 140, "matched_categories": ["Adventure"], "rating": 4.5}
        low = OriginDiscoveryRequest(origin_name="Bengaluru", budget=25000, days=4, travelers_count=1, travel_type="Adventure", comfort_score=11)
        middle = low.model_copy(update={"comfort_score": 50})
        high = low.model_copy(update={"comfort_score": 83})
        low_cost = trips._origin_candidate_cost(candidate["distance_km"], low)
        middle_cost = trips._origin_candidate_cost(candidate["distance_km"], middle)
        high_cost = trips._origin_candidate_cost(candidate["distance_km"], high)
        self.assertLess(low_cost["total_estimated_cost"], middle_cost["total_estimated_cost"])
        self.assertLess(middle_cost["total_estimated_cost"], high_cost["total_estimated_cost"])
        self.assertLess(low_cost["total_estimated_cost"], high_cost["total_estimated_cost"])
        self.assertEqual(low_cost["total_estimated_cost"] <= low.budget, high_cost["total_estimated_cost"] <= high.budget)
        self.assertLess(low_cost["total_estimated_cost"], high_cost["total_estimated_cost"])

    def test_bengaluru_twenty_thousand_example_uses_comfort_adjusted_hard_budget(self):
        async def run():
            rows = [place("mysuru-adventure", "Mysuru adventure park", "Mysuru", 12.30, 76.65, types=["natural.mountain", "national_park"])]
            for comfort in (11, 50, 83):
                request = OriginDiscoveryRequest(origin_name="Bengaluru", origin_latitude=12.97, origin_longitude=77.59, budget=20000, days=4, travelers_count=1, travel_type="Adventure", comfort_score=comfort)
                with patch("app.services.geoapify_places.search_places", AsyncMock(return_value=rows)):
                    response = await trips.discover_destinations_from_origin(request)
                self.assertEqual(len(response["candidates"]), 1)
                candidate = response["candidates"][0]
                self.assertEqual(candidate["estimated_cost"], candidate["costs"]["total_estimated_cost"])
                self.assertLessEqual(candidate["estimated_cost"], request.budget)
                self.assertEqual(candidate["costs"]["accommodation_nights"], 3)
                self.assertNotIn("Premium", candidate["costs"]["hotel_tier"])
                self.assertNotIn("Premium", candidate["costs"]["transport_mode"])
        asyncio.run(run())

    def test_cost_units_multipliers_and_contingency_are_applied_once(self):
        one = OriginDiscoveryRequest(origin_name="Bengaluru", budget=200000, days=4, travelers_count=1, comfort_score=50)
        two = one.model_copy(update={"travelers_count": 2})
        five_days = one.model_copy(update={"days": 5})
        estimate = trips._origin_candidate_cost(140, one)
        two_estimate = trips._origin_candidate_cost(140, two)
        five_day_estimate = trips._origin_candidate_cost(140, five_days)
        self.assertEqual(estimate["accommodation_nights"], 3)
        self.assertEqual(estimate["hotel_cost"], 1800 * 3)
        self.assertEqual(estimate["food_cost"], 900 * 4)
        self.assertEqual(two_estimate["hotel_cost"], estimate["hotel_cost"] * 2)
        self.assertEqual(two_estimate["food_cost"], estimate["food_cost"] * 2)
        self.assertEqual(five_day_estimate["accommodation_nights"], 4)
        self.assertEqual(five_day_estimate["food_cost"], estimate["food_cost"] * 1.25)
        pre_reserve = sum(estimate[key] for key in ("transport_cost", "hotel_cost", "food_cost", "activities_cost", "local_transport_cost", "taxes_fees_cost"))
        self.assertEqual(estimate["emergency_reserve"], round(pre_reserve * 0.08, 2))
        self.assertEqual(estimate["total_estimated_cost"], round(pre_reserve + estimate["emergency_reserve"], 2))

    def test_genuinely_over_budget_empty_state_shows_cheapest_validated_estimate(self):
        async def run():
            rows = [place("far-adventure", "Far adventure park", "Jaipur", 26.91, 75.79, types=["natural.mountain"])]
            request = OriginDiscoveryRequest(origin_name="Bengaluru", origin_latitude=12.97, origin_longitude=77.59, budget=1000, days=4, travelers_count=1, travel_type="Adventure", comfort_score=50)
            with patch("app.services.geoapify_places.search_places", AsyncMock(return_value=rows)):
                response = await trips.discover_destinations_from_origin(request)
            self.assertEqual(response["candidates"], [])
            self.assertEqual(response["search_status"], "budget_filtered")
            self.assertTrue(any("Cheapest: Jaipur" in warning and "over budget" in warning for warning in response["warnings"]))
        asyncio.run(run())

    def test_category_empty_state_uses_geoapify_categories_not_query_label(self):
        async def run():
            rows = [place("x", "Museum", "Mysuru", 12.3, 76.65, types=["entertainment.museum"])]
            request = OriginDiscoveryRequest(origin_name="Bengaluru", origin_latitude=12.97, origin_longitude=77.59, budget=20000, days=4, travel_type="Adventure")
            with patch("app.services.geoapify_places.search_places", AsyncMock(return_value=rows)):
                response = await trips.discover_destinations_from_origin(request)
            self.assertEqual(response["candidates"], [])
            self.assertTrue(any("did not verify a Adventure match" in warning for warning in response["warnings"]))
        asyncio.run(run())

    def test_nearby_getaway_toggle_obeys_20km_and_50km_thresholds(self):
        async def run():
            near = place("near", "Nearby park", "Hosur", 12.83, 77.80)
            rows = [near]
            for enabled, expected in ((False, []), (True, ["Hosur"])):
                request = OriginDiscoveryRequest(origin_name="Bengaluru", origin_latitude=12.97, origin_longitude=77.59, budget=20000, days=4, travel_type="Nature", short_local_getaway=enabled)
                with patch("app.services.geoapify_places.search_places", AsyncMock(return_value=rows)):
                    response = await trips.discover_destinations_from_origin(request)
                self.assertEqual(bool(response["candidates"]), bool(expected))
                if enabled:
                    self.assertEqual(response["candidates"][0]["name"], "Nearby park")
        asyncio.run(run())

    def test_itinerary_keeps_only_sightseeing_references_from_verified_place_set(self):
        verified = [{"place_id": "in-1", "name": "Mysuru Palace", "latitude": 12.3, "longitude": 76.6}]
        days = [{"day_number": 1, "activities": [
            {"title": "Explore Mysuru Palace", "time": "Morning", "cost": 0},
            {"title": "Visit Lahore Fort", "time": "Afternoon", "cost": 0},
            {"title": "Arrival and check-in", "time": "Evening", "cost": 0},
        ]}]
        result = trips._keep_verified_itinerary_activities(days, verified)
        self.assertEqual([activity["title"] for activity in result[0]["activities"]], ["Mysuru Palace", "Arrival and check-in"])
        self.assertEqual(result[0]["activities"][0]["place_id"], "in-1")

    def test_explicit_itinerary_generation_reuses_discovery_cost_and_verified_places(self):
        from unittest.mock import MagicMock
        from app.schemas import TripPlanRequest
        from types import SimpleNamespace
        async def run():
            candidate_place = place("poi-1", "Mysuru Palace", "Mysuru", 12.30, 76.65, types=["natural.mountain", "national_park"])
            request = TripPlanRequest(starting_city="Bengaluru", origin_latitude=12.97, origin_longitude=77.59, budget=20000, days=4, travelers_count=1, travel_type="Adventure", comfort_score=11, destination_name="Mysuru", destination_address="Karnataka, India", latitude=12.30, longitude=76.65, geoapify_place_id="poi-1", destination_country_code="IN")
            generated = [{"day_number": day, "description": "A planned day", "activities": [{"time": "Morning", "title": "Mysuru Palace", "cost": 100}]} for day in range(1, 5)]
            with patch("app.routers.trips._discover_geoapify_destination_places", AsyncMock(return_value=([candidate_place], []))) as geo_search, patch("app.routers.trips._discover_live_places", AsyncMock()) as google_search, patch("app.routers.trips.get_forecast", AsyncMock(return_value={"timezone": "Asia/Kolkata", "daily": []})), patch.object(trips.gemini_service, "generate_itinerary", return_value=generated) as generate:
                response = await trips.generate_dynamic_trip_plan(request, MagicMock())
            discovery_req = OriginDiscoveryRequest(origin_name="Bengaluru", origin_latitude=12.97, origin_longitude=77.59, budget=20000, days=4, travelers_count=1, travel_type="Adventure", comfort_score=11)
            expected_distance = round(trips._distance_km(12.97, 77.59, 12.30, 76.65), 1)
            expected_cost = trips._origin_candidate_cost(expected_distance, discovery_req)["total_estimated_cost"]
            self.assertEqual(response["costs"]["total_estimated_cost"], expected_cost)
            self.assertEqual(response["destination"]["country_code"], "IN")
            self.assertEqual(response["destination"]["geoapify_place_id"], "poi-1")
            self.assertEqual(response["itineraries"][0]["activities"][0]["place_id"], "poi-1")
            generate.assert_called_once()
            geo_search.assert_awaited_once()
            google_search.assert_not_awaited()
        asyncio.run(run())

    def test_foreign_selected_destination_is_rejected_without_database_or_places_lookup(self):
        from fastapi import HTTPException
        from unittest.mock import MagicMock
        from app.schemas import TripPlanRequest
        request = TripPlanRequest(starting_city="Bengaluru", budget=20000, days=4, travel_type="Adventure", destination_name="Lahore", latitude=31.5, longitude=74.3, google_place_id="foreign", destination_country_code="PK")
        async def run():
            with patch("app.routers.trips._discover_geoapify_destination_places", AsyncMock()) as places:
                with self.assertRaises(HTTPException) as caught:
                    await trips.generate_dynamic_trip_plan(request, MagicMock())
            self.assertEqual(caught.exception.status_code, 422)
            places.assert_not_awaited()
        asyncio.run(run())

    def test_delhi_origin_needs_no_destination_selection_and_partial_results_survive(self):
        from app.services.geoapify_places import GeoapifyError
        # An upstream category failure is represented by PlacesError and must not discard successful search data.
        async def run_partial():
            mock_search = AsyncMock(side_effect=[[place("x", "City landmark", "Jaipur", 26.91, 75.79, types=["entertainment.museum", "tourism.sights.fort"])], GeoapifyError("quota")])
            request = OriginDiscoveryRequest(origin_name="Delhi", origin_latitude=28.61, origin_longitude=77.20, budget=100000, days=3, travelers_count=1, travel_type="City Exploration")
            from app.services import geoapify_places
            with patch.object(geoapify_places, "DESTINATION_AREAS", (("Jaipur", 26.91, 75.79),)), patch("app.services.geoapify_places.search_places", mock_search):
                response = await trips.discover_destinations_from_origin(request)
            self.assertTrue(response["candidates"])
            self.assertTrue(response["partial_results"])
        asyncio.run(run_partial())

    def test_empty_places_and_api_unavailable_are_distinct(self):
        from fastapi import HTTPException
        from app.services.geoapify_places import GeoapifyError
        request = OriginDiscoveryRequest(origin_name="Delhi", origin_latitude=28.61, origin_longitude=77.20, budget=100000, days=3)
        async def run_empty():
            with patch("app.services.geoapify_places.search_places", AsyncMock(return_value=[])):
                response = await trips.discover_destinations_from_origin(request)
            self.assertEqual(response["data_source"], "geoapify_empty")
            self.assertEqual(response["candidates"], [])
        async def run_failed():
            with patch("app.services.geoapify_places.search_places", AsyncMock(side_effect=GeoapifyError("invalid key"))):
                with self.assertRaises(HTTPException) as caught:
                    await trips.discover_destinations_from_origin(request)
            self.assertEqual(caught.exception.status_code, 503)
        asyncio.run(run_empty()); asyncio.run(run_failed())


if __name__ == "__main__":
    unittest.main()
