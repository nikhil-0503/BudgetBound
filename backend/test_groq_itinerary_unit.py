import json
import unittest
from unittest.mock import MagicMock, patch

import httpx

from app.services.gemini import GroqTravelService


def service():
    instance = GroqTravelService.__new__(GroqTravelService)
    instance.api_key = "unit-test-key"
    instance._selected_model = "unit-test-model"
    instance._model_discovery_error = None
    instance._fallback_reason = None
    instance._last_finish_reason = None
    instance._last_http_status = None
    instance._last_provider_error = None
    instance._request_stats = {"total_requests": 0, "successful_requests": 0, "failed_requests": 0, "token_exhaustion_count": 0, "empty_response_count": 0, "fallback_activations": 0}
    return instance


class GroqItineraryTests(unittest.TestCase):
    def test_chat_tuple_is_parsed_and_successful_result_matches_canonical_schema(self):
        model = service()
        raw = json.dumps([{"day_number": 1, "description": "A short visit", "activities": [{"time": "Morning", "title": "Mysuru Palace", "cost": 100}]}])
        model._chat = MagicMock(return_value=(raw, None))
        result = model.generate_itinerary("Mysuru", "Karnataka", "Adventure", ["Mysuru Palace"], "Adventure", 1, 50, 900, 500, budget_limit=20000)
        self.assertEqual(result[0]["activities"][0]["title"], "Mysuru Palace")
        model._chat.assert_called_once()

    def test_malformed_and_incomplete_responses_fail_without_fabricated_days(self):
        for raw in ("not json", json.dumps([{"day_number": 1, "activities": [{"time": "Morning", "title": "Missing cost"}]}])):
            model = service()
            model._chat = MagicMock(return_value=(raw, None))
            self.assertIsNone(model.generate_itinerary("Mysuru", "Karnataka", "Adventure", [], "Adventure", 1, 50, 900, 500, budget_limit=20000))

        model = service()
        model._chat = MagicMock(return_value=(json.dumps([{"day_number": 2, "activities": [], "description": "Wrong day"}]), None))
        self.assertIsNone(model.generate_itinerary("Mysuru", "Karnataka", "Adventure", [], "Adventure", 1, 50, 900, 500, budget_limit=20000))

    def test_timeout_and_rate_limit_have_bounded_retries_and_diagnostic_state(self):
        model = service()
        timeout_client = MagicMock()
        timeout_client.__enter__.return_value = timeout_client
        timeout_client.__exit__.return_value = False
        timeout_client.post.side_effect = httpx.TimeoutException("provider timeout")
        with patch("app.services.gemini.httpx.Client", return_value=timeout_client), patch("app.services.gemini.time.sleep") as sleep:
            content, error = model._chat("prompt", max_retries=2)
        self.assertIsNone(content)
        self.assertIsNotNone(error)
        self.assertEqual(timeout_client.post.call_count, 2)
        self.assertEqual(sleep.call_count, 1)

        model = service()
        rate_limited = MagicMock(status_code=429)
        rate_limited.json.return_value = {"error": {"message": "rate limited"}}
        rate_client = MagicMock()
        rate_client.__enter__.return_value = rate_client
        rate_client.__exit__.return_value = False
        rate_client.post.return_value = rate_limited
        with patch("app.services.gemini.httpx.Client", return_value=rate_client), patch("app.services.gemini.time.sleep"):
            content, error = model._chat("prompt", max_retries=2)
        self.assertIsNone(content)
        self.assertEqual(error, "rate limited")
        self.assertEqual(rate_client.post.call_count, 2)
        self.assertEqual(model._last_http_status, 429)
        self.assertEqual(model._selected_model, "unit-test-model")

    def test_strict_schema_only_request_never_silently_retries_without_schema(self):
        model = service()
        rejected = MagicMock(status_code=400)
        rejected.json.return_value = {"error": {"message": "json_schema is not supported by this model"}}
        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = False
        client.post.return_value = rejected
        with patch("app.services.gemini.httpx.Client", return_value=client):
            content, error = model._chat("ranking", max_retries=2, response_schema={"type": "object"}, strict_schema_only=True)
        self.assertIsNone(content)
        self.assertIn("json_schema", error)
        self.assertEqual(client.post.call_count, 1)


if __name__ == "__main__":
    unittest.main()
