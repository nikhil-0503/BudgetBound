import asyncio
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx

from app.services import google_place_ratings as ratings
from app.config import BACKEND_ENV_FILE, Settings


def candidate(name="Ooty", lat=11.41, lon=76.69):
    return {"name": name, "region": "Tamil Nadu", "country": "India", "country_code": "IN", "latitude": lat, "longitude": lon}


def google_place(**changes):
    item = {
        "id": "google-ooty-id",
        "displayName": {"text": "Ooty"},
        "adrFormatAddress": "<span>Ooty, Tamil Nadu, India</span>",
        "location": {"latitude": 11.41, "longitude": 76.69},
        "rating": 4.6,
        "userRatingCount": 2350,
        "googleMapsUri": "https://maps.google.com/?cid=ooty",
    }
    item.update(changes)
    return item


class GooglePlaceRatingsTests(unittest.TestCase):
    def setUp(self):
        ratings.clear_rating_cache()

    def test_google_maps_key_uses_backend_env_file_and_expected_setting_name(self):
        self.assertEqual(BACKEND_ENV_FILE, Path(__file__).resolve().parent / ".env")
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text("GOOGLE_MAPS_API_KEY=unit-test-placeholder\n", encoding="utf-8")
            with patch.dict(os.environ, {}, clear=True):
                configured = Settings(_env_file=env_file)
        self.assertTrue(configured.GOOGLE_MAPS_API_KEY == "unit-test-placeholder", "backend env key did not load")
        with patch.object(ratings.settings, "GOOGLE_MAPS_API_KEY", "unit-test-placeholder"):
            self.assertEqual(ratings.configuration_status(), "configured")

    def test_normalizes_only_provider_supplied_rating_fields(self):
        normalized = ratings.normalize_matching_result(candidate(), google_place())
        self.assertEqual(normalized, {
            "rating": 4.6, "user_rating_count": 2350, "google_place_id": "google-ooty-id",
            "google_maps_uri": "https://maps.google.com/?cid=ooty", "rating_source": "google_places",
        })
        unavailable = ratings.normalize_matching_result(candidate(), google_place(rating=None, userRatingCount=12))
        self.assertIsNone(unavailable["rating"])
        self.assertEqual(unavailable["user_rating_count"], 12)

    def test_rejects_foreign_wrong_city_far_and_attraction_matches(self):
        self.assertIsNone(ratings.normalize_matching_result(candidate(), google_place(adrFormatAddress="Kathmandu, Nepal")))
        self.assertIsNone(ratings.normalize_matching_result(candidate(), google_place(displayName={"text": "Mysore Palace"})))
        self.assertIsNone(ratings.normalize_matching_result(candidate(), google_place(location={"latitude": 13.0, "longitude": 77.0})))
        self.assertIsNone(ratings.normalize_matching_result(candidate(), google_place(displayName={"text": "Ooty Botanical Garden"})))

    def test_text_search_uses_google_endpoint_fields_india_bias_and_api_key_header(self):
        async def run():
            response = httpx.Response(200, json={"places": [google_place()]}, request=httpx.Request("POST", ratings.TEXT_URL))
            with patch.object(ratings.settings, "GOOGLE_MAPS_API_KEY", "unit-test-secret"), \
                 patch("app.services.google_place_ratings.httpx.AsyncClient") as client_type:
                client = client_type.return_value.__aenter__.return_value
                client.post = AsyncMock(return_value=response)
                result = await ratings.search_candidate(candidate())
                args, kwargs = client.post.await_args
                self.assertEqual(args[0], "https://places.googleapis.com/v1/places:searchText")
                self.assertEqual(kwargs["headers"]["X-Goog-Api-Key"], "unit-test-secret")
                self.assertIn("places.rating", kwargs["headers"]["X-Goog-FieldMask"])
                self.assertEqual(kwargs["json"]["regionCode"], "IN")
                self.assertEqual(kwargs["json"]["locationBias"]["circle"]["center"], {"latitude": 11.41, "longitude": 76.69})
                self.assertEqual(result["rating"], 4.6)
        asyncio.run(run())

    def test_empty_results_are_unavailable_not_an_error(self):
        async def run():
            response = httpx.Response(200, json={"places": []}, request=httpx.Request("POST", ratings.TEXT_URL))
            with patch.object(ratings.settings, "GOOGLE_MAPS_API_KEY", "test"), \
                 patch("app.services.google_place_ratings.httpx.AsyncClient") as client_type:
                client_type.return_value.__aenter__.return_value.post = AsyncMock(return_value=response)
                self.assertIsNone(await ratings.search_candidate(candidate()))
        asyncio.run(run())

    def test_similarly_named_equally_close_matches_are_rejected_as_ambiguous(self):
        async def run():
            second = google_place(id="google-ooty-duplicate", location={"latitude": 11.411, "longitude": 76.69})
            response = httpx.Response(200, json={"places": [google_place(), second]}, request=httpx.Request("POST", ratings.TEXT_URL))
            with patch.object(ratings.settings, "GOOGLE_MAPS_API_KEY", "test"), patch("app.services.google_place_ratings.httpx.AsyncClient") as client_type:
                client_type.return_value.__aenter__.return_value.post = AsyncMock(return_value=response)
                self.assertIsNone(await ratings.search_candidate(candidate()))
        asyncio.run(run())

    def test_missing_or_invalid_key_does_not_send_request(self):
        async def run():
            with patch.object(ratings.settings, "GOOGLE_MAPS_API_KEY", " "), \
                 patch("app.services.google_place_ratings.httpx.AsyncClient") as client_type:
                with self.assertRaisesRegex(ratings.GoogleRatingError, "not configured"):
                    await ratings.search_candidate(candidate())
                client_type.assert_not_called()
        asyncio.run(run())

    def test_401_403_429_5xx_and_timeout_map_to_actionable_errors(self):
        async def run_status(status):
            response = httpx.Response(status, request=httpx.Request("POST", ratings.TEXT_URL))
            with patch.object(ratings.settings, "GOOGLE_MAPS_API_KEY", "test"), \
                 patch("app.services.google_place_ratings.httpx.AsyncClient") as client_type:
                client_type.return_value.__aenter__.return_value.post = AsyncMock(return_value=response)
                with self.assertRaises(ratings.GoogleRatingError) as caught:
                    await ratings.search_candidate(candidate())
                return caught.exception

        async def run():
            for status, message in ((400, "parameters"), (401, "rejected"), (403, "denied"), (429, "rate limited"), (500, "unavailable")):
                error = await run_status(status)
                self.assertIn(message, str(error))
            with patch.object(ratings.settings, "GOOGLE_MAPS_API_KEY", "test"), \
                 patch("app.services.google_place_ratings.httpx.AsyncClient") as client_type:
                client_type.return_value.__aenter__.return_value.post = AsyncMock(side_effect=httpx.TimeoutException("late"))
                with self.assertRaisesRegex(ratings.GoogleRatingError, "timed out"):
                    await ratings.search_candidate(candidate())
        asyncio.run(run())

    def test_google_api_disabled_permission_denied_and_quota_have_distinct_codes(self):
        async def run(status, payload, expected):
            response = httpx.Response(status, json=payload, request=httpx.Request("POST", ratings.TEXT_URL))
            with patch.object(ratings.settings, "GOOGLE_MAPS_API_KEY", "test-placeholder"), patch("app.services.google_place_ratings.httpx.AsyncClient") as client_type:
                client_type.return_value.__aenter__.return_value.post = AsyncMock(return_value=response)
                with self.assertRaises(ratings.GoogleRatingError) as caught:
                    await ratings.search_candidate(candidate())
            self.assertEqual(caught.exception.diagnostic_code, expected)

        async def check_all():
            await run(403, {"error": {"status": "SERVICE_DISABLED", "message": "API has not been used or is disabled"}}, "api_disabled")
            await run(403, {"error": {"status": "PERMISSION_DENIED", "message": "permission denied"}}, "permission_denied")
            await run(403, {"error": {"status": "PERMISSION_DENIED", "message": "Billing is not enabled for this project"}}, "billing_error")
            await run(429, {"error": {"status": "RESOURCE_EXHAUSTED", "message": "quota exceeded"}}, "quota_exceeded")
            await run(429, {}, "rate_limited")
            await run(400, {"error": {"status": "INVALID_ARGUMENT", "message": "Invalid field mask"}}, "invalid_field_mask")
        asyncio.run(check_all())

    def test_successful_rating_lookup_is_cached_for_repeated_searches(self):
        async def run():
            response = httpx.Response(200, json={"places": [google_place()]}, request=httpx.Request("POST", ratings.TEXT_URL))
            with patch.object(ratings.settings, "GOOGLE_MAPS_API_KEY", "test-placeholder"), patch("app.services.google_place_ratings.httpx.AsyncClient") as client_type:
                client_type.return_value.__aenter__.return_value.post = AsyncMock(return_value=response)
                first = await ratings.search_candidate(candidate())
                second = await ratings.search_candidate(candidate())
            self.assertEqual(first["rating"], 4.6)
            self.assertEqual(second["user_rating_count"], 2350)
            self.assertEqual(client_type.return_value.__aenter__.return_value.post.await_count, 1)
        asyncio.run(run())

    def test_temporary_rate_limit_retries_with_bounded_attempts(self):
        async def run():
            responses = [
                httpx.Response(429, json={"error": {"status": "RESOURCE_EXHAUSTED", "message": "Too many requests; rate limit"}}, request=httpx.Request("POST", ratings.TEXT_URL)),
                httpx.Response(200, json={"places": [google_place()]}, request=httpx.Request("POST", ratings.TEXT_URL)),
            ]
            with patch.object(ratings.settings, "GOOGLE_MAPS_API_KEY", "test-placeholder"), patch("app.services.google_place_ratings.httpx.AsyncClient") as client_type, patch("app.services.google_place_ratings.asyncio.sleep", new_callable=AsyncMock):
                client_type.return_value.__aenter__.return_value.post = AsyncMock(side_effect=responses)
                result = await ratings.search_candidate(candidate())
            self.assertEqual(result["rating"], 4.6)
            self.assertEqual(client_type.return_value.__aenter__.return_value.post.await_count, 2)
        asyncio.run(run())

    def test_permanent_quota_error_is_not_retried_or_cached(self):
        async def run():
            quota = httpx.Response(429, json={"error": {"status": "RESOURCE_EXHAUSTED", "message": "Quota exceeded"}}, request=httpx.Request("POST", ratings.TEXT_URL))
            with patch.object(ratings.settings, "GOOGLE_MAPS_API_KEY", "test-placeholder"), patch("app.services.google_place_ratings.httpx.AsyncClient") as client_type:
                client_type.return_value.__aenter__.return_value.post = AsyncMock(return_value=quota)
                for _ in range(2):
                    with self.assertRaises(ratings.GoogleRatingError) as caught:
                        await ratings.search_candidate(candidate())
                    self.assertEqual(caught.exception.diagnostic_code, "quota_exceeded")
            self.assertEqual(client_type.return_value.__aenter__.return_value.post.await_count, 2)
        asyncio.run(run())

    def test_enrichment_is_bounded_to_ranked_shortlist_and_retains_candidates_on_failure(self):
        async def run():
            ranked = [candidate("Ooty"), candidate("Mysuru", 12.3, 76.65), candidate("Kochi", 9.93, 76.27)]
            with patch.object(ratings.settings, "GOOGLE_MAPS_API_KEY", "configured-test-key"), patch("app.services.google_place_ratings.search_candidate", new_callable=AsyncMock, side_effect=[google_place(), ratings.GoogleRatingError("rate limited")]) as search:
                issues = await ratings.enrich_candidates(ranked, limit=2, concurrency=1)
            self.assertEqual(search.await_count, 2)
            self.assertEqual(ranked[0]["rating"], 4.6)
            self.assertEqual(ranked[1]["rating_source"], "unavailable")
            self.assertEqual(ranked[1]["rating_unavailable_reason"], "rate limited")
            self.assertEqual(ranked[2]["rating_source"], "unavailable")
            self.assertIn("shortlist", ranked[2]["rating_unavailable_reason"])
            self.assertTrue(issues)
        asyncio.run(run())

    def test_missing_google_key_is_explicit_and_enrichment_makes_no_lookup(self):
        async def run():
            rows = [candidate("Ooty")]
            with patch.object(ratings.settings, "GOOGLE_MAPS_API_KEY", ""), patch("app.services.google_place_ratings.search_candidate", new_callable=AsyncMock) as search:
                issues = await ratings.enrich_candidates(rows, limit=8)
            search.assert_not_awaited()
            self.assertIn("GOOGLE_MAPS_API_KEY", issues[0])
            self.assertEqual(rows[0]["rating"], None)
            self.assertIn("not been configured", rows[0]["rating_unavailable_reason"])
        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
