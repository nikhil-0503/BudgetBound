import asyncio
import json
import unittest
from unittest.mock import MagicMock, PropertyMock, patch

from app.schemas import OriginDiscoveryRequest
from app.services import ai_destination_ranker as ranker
from app.services.gemini import GroqTravelService, gemini_service


def destination(destination_id, name, categories, place_names, cost, rating=None, count=None):
    return {
        "destination_id": destination_id,
        "name": name,
        "address": f"{name}, India",
        "region": "Karnataka",
        "country": "India",
        "country_code": "IN",
        "latitude": 12.0,
        "longitude": 76.0,
        "distance_km": 140,
        "matched_categories": categories,
        "verified_places": [{"name": label} for label in place_names],
        "rating": rating,
        "user_rating_count": count,
        "costs": {
            "transport_cost": 1500,
            "hotel_cost": 4000,
            "food_cost": 2000,
            "activities_cost": 1000,
            "local_transport_cost": 500,
            "taxes_fees_cost": 300,
            "emergency_reserve": 700,
            "total_estimated_cost": cost,
            "estimate_label": "Planning estimate, not a quote",
        },
        "estimated_cost": cost,
        "budget_remaining": 20000-cost,
        "budget_limit": 20000,
        "under_budget": True,
        "data_source": "geoapify",
    }


def score_row(destination_id, overall, *, category=70, interest=70, comfort=70, duration=70, quality=70, reason="Matches the supplied verified categories.", tradeoffs=None):
    highlights = {"geo-mysuru": "Mysuru Hill Trek", "geo-kochi": "Kochi Food Market", "geo-third": "Ooty mountain trail"}
    return {
        "destination_id": destination_id,
        "category_relevance_score": category,
        "interest_match_score": interest,
        "comfort_suitability_score": comfort,
        "duration_suitability_score": duration,
        "destination_quality_score": quality,
        "overall_match_score": overall,
        "match_reasons": [reason],
        "tradeoffs": tradeoffs or [],
        "why_visit": f"Verified destination listings include {highlights.get(destination_id, 'the listed destination')}.",
        "trip_fit": "This matches the Adventure category for your trip.",
        "practical_note": None,
    }


def response_json(*rows):
    return json.dumps({"rankings": list(rows)})


class AIDestinationRankerTests(unittest.TestCase):
    def setUp(self):
        self.request = OriginDiscoveryRequest(
            origin_name="Bengaluru", budget=20000, days=4, travelers_count=2,
            travel_type="Adventure", comfort_score=67, interests=["wildlife", "trekking"],
        )
        self.outdoors = destination("geo-mysuru", "Mysuru", ["Adventure", "Nature"], ["Mysuru Hill Trek"], 12000, 4.6, 900)
        self.food_city = destination("geo-kochi", "Kochi", ["City Exploration"], ["Kochi Food Market"], 11000)

    def _mock_chat(self, rows, model="qwen/qwen3.8-27b", error=None):
        chat = MagicMock(return_value=(None, error) if error else (response_json(*rows), None))
        return chat, patch.object(GroqTravelService, "is_available", new_callable=PropertyMock, return_value=True), patch.object(gemini_service, "_selected_model", model), patch.object(gemini_service, "_chat", chat)

    def test_adventure_and_food_preferences_can_change_rankings_from_supplied_evidence(self):
        async def run():
            calls = []

            def contextual_chat(prompt, *args, **kwargs):
                preferences = json.loads(prompt.split("User preferences and constraints:\n", 1)[1].split("\n\nFeasible destination evidence:", 1)[0])
                calls.append(preferences)
                if preferences["additional_interests"] == ["food"]:
                    return response_json(score_row("geo-kochi", 95, interest=100, reason="Matches your food interest in a verified food market."), score_row("geo-mysuru", 50)), None
                return response_json(score_row("geo-mysuru", 93, interest=90, reason="Matches your Adventure category and a verified trekking place."), score_row("geo-kochi", 40)), None

            with patch.object(GroqTravelService, "is_available", new_callable=PropertyMock, return_value=True), \
                 patch.object(gemini_service, "_selected_model", "qwen/qwen3.8-27b"), \
                 patch.object(gemini_service, "_chat", side_effect=contextual_chat):
                adventure, _, _ = await ranker.rank_candidates([dict(self.outdoors), dict(self.food_city)], self.request)
                food_request = self.request.model_copy(update={"travel_type": "City Exploration", "interests": ["food"]})
                food, _, _ = await ranker.rank_candidates([dict(self.outdoors), dict(self.food_city)], food_request)
            self.assertEqual(adventure[0]["destination_id"], "geo-mysuru")
            self.assertEqual(food[0]["destination_id"], "geo-kochi")
            self.assertEqual(calls[0]["comfort_score_0_to_100"], 67)
            self.assertEqual(calls[0]["traveler_count"], 2)
        asyncio.run(run())

    def test_prompt_includes_candidate_identity_places_google_data_and_full_cost_breakdown(self):
        prompt = ranker._build_prompt([self.outdoors], self.request)
        self.assertIn("geo-mysuru", prompt)
        self.assertIn("Mysuru Hill Trek", prompt)
        self.assertIn('"google_rating":4.6', prompt)
        self.assertIn('"google_rating_count":900', prompt)
        self.assertIn("taxes_fees_cost", prompt)
        self.assertIn('"budget_inr_hard_limit":20000.0', prompt)
        self.assertIn("Budget is already a hard gate", prompt)

    def test_valid_scores_are_pydantic_validated_and_sorted_with_deterministic_tie_breakers(self):
        async def run():
            rows = [score_row("geo-kochi", 88), score_row("geo-mysuru", 88)]
            chat, available, model, chat_patch = self._mock_chat(rows)
            with available, model, chat_patch:
                ranked, mode, selected = await ranker.rank_candidates([dict(self.outdoors), dict(self.food_city)], self.request)
            self.assertEqual([item["destination_id"] for item in ranked], ["geo-kochi", "geo-mysuru"])
            self.assertEqual(mode, "strict_json_schema")
            self.assertEqual(selected, "qwen/qwen3.8-27b")
            self.assertEqual(ranked[0]["value_score"], ranked[0]["overall_match_score"])
            self.assertEqual(chat.call_args.args[2], ranker.STRICT_RANKING_SCHEMA)
            self.assertTrue(chat.call_args.args[3])
        asyncio.run(run())

    def test_unsupported_strict_model_uses_json_prompt_then_pydantic_validation(self):
        async def run():
            chat, available, model, chat_patch = self._mock_chat([score_row("geo-mysuru", 80)], model="llama-compatible-model")
            with available, model, chat_patch:
                ranked, mode, selected = await ranker.rank_candidates([dict(self.outdoors)], self.request)
            self.assertEqual(mode, "json_prompt_validated")
            self.assertEqual(selected, "llama-compatible-model")
            self.assertIsNone(chat.call_args.args[2])
            self.assertFalse(chat.call_args.args[3])
            self.assertEqual(ranked[0]["overall_match_score"], 80)
        asyncio.run(run())

    def test_invalid_scores_unknown_duplicate_missing_ids_and_unsupported_place_claims_are_rejected(self):
        invalid = [
            [score_row("geo-mysuru", 101), score_row("geo-kochi", 60)],
            [score_row("geo-mysuru", 80), score_row("geo-mysuru", 70)],
            [score_row("unknown", 80), score_row("geo-kochi", 70)],
            [score_row("geo-mysuru", 80)],
            [score_row("geo-mysuru", 80, reason="Visit the Taj Mahal for culture."), score_row("geo-kochi", 70)],
        ]
        for rows in invalid[:4]:
            async def run(rows=rows):
                chat, available, model, chat_patch = self._mock_chat(rows)
                with available, model, chat_patch:
                    with self.assertRaises(ranker.AIRankingError):
                        await ranker.rank_candidates([dict(self.outdoors), dict(self.food_city)], self.request)
            asyncio.run(run())
        async def repair_unverified_attraction():
            chat, available, model, chat_patch = self._mock_chat(invalid[4])
            with available, model, chat_patch:
                ranked, _, _ = await ranker.rank_candidates([dict(self.outdoors), dict(self.food_city)], self.request)
            self.assertEqual(len(ranked), 2)
            self.assertNotIn("Taj Mahal", " ".join(reason for item in ranked for reason in item["match_reasons"]))
        asyncio.run(repair_unverified_attraction())

    def test_invalid_explanation_is_repaired_without_discarding_valid_scores(self):
        async def run():
            candidate = dict(self.food_city)
            candidate.update({"rating": None, "user_rating_count": None, "region": None, "address": None})
            chat, available, model, chat_patch = self._mock_chat([score_row("geo-kochi", 80, reason="A 4.8 rating makes this a top choice.")])
            with available, model, chat_patch:
                ranked, _, _ = await ranker.rank_candidates([candidate], self.request)
            self.assertEqual(ranked[0]["overall_match_score"], 80)
            self.assertNotIn("4.8", ranked[0]["explanation"])
            self.assertIn("verified place categories", ranked[0]["explanation"])
        asyncio.run(run())

    def test_new_or_malformed_destination_id_is_rejected(self):
        async def run():
            chat, available, model, chat_patch = self._mock_chat([score_row("new-destination", 80)])
            with available, model, chat_patch:
                with self.assertRaisesRegex(ranker.AIRankingError, "invalid destination IDs"):
                    await ranker.rank_candidates([dict(self.food_city)], self.request)
        asyncio.run(run())

    def test_provider_timeout_rate_limit_malformed_and_missing_model_fail_without_fake_scores(self):
        async def run():
            for response in ((None, "HTTP 429 rate limited"), (None, "Groq request timed out"), ("not json", None), ("{}", None)):
                chat = MagicMock(return_value=response)
                with patch.object(GroqTravelService, "is_available", new_callable=PropertyMock, return_value=True), \
                     patch.object(gemini_service, "_selected_model", "qwen/qwen3.8-27b"), \
                     patch.object(gemini_service, "_chat", chat):
                    with self.assertRaises(ranker.AIRankingError):
                        await ranker.rank_candidates([dict(self.outdoors)], self.request)
            with patch.object(GroqTravelService, "is_available", new_callable=PropertyMock, return_value=False), patch.object(gemini_service, "api_key", ""):
                with self.assertRaisesRegex(ranker.AIRankingError, "not configured"):
                    await ranker.rank_candidates([dict(self.outdoors)], self.request)
        asyncio.run(run())

    def test_malformed_response_gets_one_corrective_retry_then_succeeds(self):
        async def run():
            valid = response_json(score_row("geo-mysuru", 81))
            chat = MagicMock(side_effect=[("not json", None), (valid, None)])
            with patch.object(GroqTravelService, "is_available", new_callable=PropertyMock, return_value=True), \
                 patch.object(gemini_service, "_selected_model", "qwen/qwen3.8-27b"), \
                 patch.object(gemini_service, "_chat", chat):
                ranked, _, _ = await ranker.rank_candidates([dict(self.outdoors)], self.request)
            self.assertEqual(chat.call_count, 2)
            self.assertIn("previous response failed schema validation", chat.call_args.args[0])
            self.assertEqual(ranked[0]["overall_match_score"], 81)
        asyncio.run(run())

    def test_fallback_has_no_ai_scores_and_uses_grounded_destination_guidance(self):
        candidate = dict(self.outdoors)
        ranked = ranker.fallback_rank_candidates([candidate], self.request)
        self.assertIsNone(ranked[0]["overall_match_score"])
        self.assertIn("Mysuru Hill Trek", ranked[0]["why_visit"])
        self.assertIn("Adventure", ranked[0]["trip_fit"])
        self.assertIn("no AI match score", ranked[0]["explanation"])

    def test_all_feasible_candidates_are_ranked_in_bounded_batches(self):
        async def run():
            candidates = [dict(self.outdoors), dict(self.food_city), destination("geo-third", "Ooty", ["Adventure"], ["Ooty mountain trail"], 9000)]
            def chat_for_each_batch(prompt, *_args, **_kwargs):
                evidence_text = prompt.split("Feasible destination evidence:\n", 1)[1]
                evidence = json.loads(evidence_text)
                rows = [score_row(item["destination_id"], 50 + index, reason="Matches supplied verified evidence.") for index, item in enumerate(evidence)]
                return response_json(*rows), None
            with patch.object(ranker.settings, "TRIP_AI_RANK_BATCH_SIZE", 2), \
                 patch.object(GroqTravelService, "is_available", new_callable=PropertyMock, return_value=True), \
                 patch.object(gemini_service, "_selected_model", "qwen/qwen3.8-27b"), \
                 patch.object(gemini_service, "_chat", side_effect=chat_for_each_batch) as chat:
                ranked, mode, _ = await ranker.rank_candidates(candidates, self.request)
            self.assertEqual(chat.call_count, 2)
            self.assertEqual({item["destination_id"] for item in ranked}, {"geo-mysuru", "geo-kochi", "geo-third"})
            self.assertEqual(mode, "batched_strict_json_schema")
            self.assertEqual(chat.call_args.args[4], 2400)
            self.assertEqual(chat.call_args.kwargs["request_timeout"], 30)
            self.assertTrue(all(item["overall_match_score"] is not None for item in candidates))
        asyncio.run(run())

    def test_failure_in_one_batch_rejects_all_ai_scores_for_consistent_fallback(self):
        async def run():
            candidates = [dict(self.outdoors), dict(self.food_city), destination("geo-third", "Ooty", ["Adventure"], ["Ooty mountain trail"], 9000)]
            first_batch = response_json(score_row("geo-mysuru", 70), score_row("geo-kochi", 60))
            with patch.object(ranker.settings, "TRIP_AI_RANK_BATCH_SIZE", 2), \
                 patch.object(GroqTravelService, "is_available", new_callable=PropertyMock, return_value=True), \
                 patch.object(gemini_service, "_selected_model", "qwen/qwen3.8-27b"), \
                 patch.object(gemini_service, "_last_http_status", 429), \
                 patch.object(gemini_service, "_chat", side_effect=[(first_batch, None), (None, "HTTP 429")]):
                with self.assertRaisesRegex(ranker.AIRankingError, "rate or quota limit"):
                    await ranker.rank_candidates(candidates, self.request)
            self.assertTrue(all("overall_match_score" not in item for item in candidates))
        asyncio.run(run())

    def test_known_token_exhausting_groq_override_is_not_selected(self):
        with patch("app.services.gemini.FALLBACK_MODEL_OVERRIDE", "openai/gpt-oss-120b"), \
             patch("app.services.gemini.get_available_model") as model_discovery, \
             patch.object(GroqTravelService, "_model_cache", None), \
             patch.object(GroqTravelService, "_init_logged", True):
            service = GroqTravelService()
        self.assertEqual(service._selected_model, "openai/gpt-oss-20b")
        model_discovery.assert_not_called()

    def test_explicit_fallback_has_no_ai_score_and_uses_evidence_then_stable_id(self):
        candidates = [dict(self.outdoors), dict(self.food_city)]
        ranked = ranker.fallback_rank_candidates(candidates, self.request)
        self.assertEqual(ranked[0]["destination_id"], "geo-mysuru")
        self.assertIsNone(ranked[0]["overall_match_score"])
        self.assertIsNone(ranked[0]["value_score"])
        self.assertEqual(ranked[0]["breakdown"], {})
        self.assertIn("no AI match score", ranked[0]["explanation"])


if __name__ == "__main__":
    unittest.main()
