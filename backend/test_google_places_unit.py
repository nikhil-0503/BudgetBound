import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from app.services import google_places


class GooglePlacesTests(unittest.TestCase):
    def test_country_code_requires_well_formed_authoritative_component(self):
        base = {"id": "places/a", "displayName": {"text": "Hill town"}, "location": {"latitude": 10, "longitude": 76}}
        valid = google_places.normalize_place({**base, "addressComponents": [{"longText": "India", "shortText": "in", "types": ["country"]}]})
        self.assertEqual(valid["country_code"], "IN")
        self.assertIsNone(google_places.normalize_place({**base, "addressComponents": [{"longText": "India", "types": "country"}]} )["country_code"])
        self.assertIsNone(google_places.normalize_place({**base, "addressComponents": None})["country_code"])

    def test_place_normalization_keeps_real_fields_and_drops_incomplete(self):
        place = google_places.normalize_place({"id": "places/a", "displayName": {"text": "Museum"}, "formattedAddress": "1 Road", "location": {"latitude": 51.5, "longitude": -0.1}, "rating": 4.7, "userRatingCount": 200})
        self.assertEqual(place["rating"], 4.7)
        self.assertEqual(place["user_rating_count"], 200)
        self.assertEqual(place["address"], "1 Road")
        self.assertIsNone(google_places.normalize_place({"id": "places/b", "displayName": {"text": "No coordinates"}}))

    def test_duplicate_ids_deduplicated_and_google_key_backend_only(self):
        google_places.settings.GOOGLE_MAPS_API_KEY = "test-key"
        response = type("Response", (), {"status_code": 200, "json": lambda self: {"places": [
            {"id": "places/a", "displayName": {"text": "Museum"}, "location": {"latitude": 1, "longitude": 2}, "addressComponents": [{"longText": "India", "shortText": "IN", "types": ["country"]}]},
            {"id": "places/a", "displayName": {"text": "Museum duplicate"}, "location": {"latitude": 1, "longitude": 2}, "addressComponents": [{"longText": "India", "shortText": "IN", "types": ["country"]}]},
            {"id": "places/pak", "displayName": {"text": "Pakistan museum"}, "location": {"latitude": 1, "longitude": 2}, "addressComponents": [{"longText": "Pakistan", "shortText": "PK", "types": ["country"]}]},
        ]}, "raise_for_status": lambda self: None})()
        client = AsyncMock(); client.post.return_value = response
        async def run():
            diagnostics = {}
            with patch.object(google_places.httpx, "AsyncClient") as factory:
                factory.return_value.__aenter__.return_value = client
                result = await google_places.text_search("museum in India", region_code="IN", country_code="IN", diagnostics=diagnostics)
                self.assertEqual(len(result), 1)
                self.assertEqual(result[0]["data_source"], "google_places")
                self.assertEqual(client.post.await_args.kwargs["headers"]["X-Goog-Api-Key"], "test-key")
                self.assertEqual(client.post.await_args.kwargs["json"]["regionCode"], "IN")
                self.assertEqual(result[0]["country_code"], "IN")
                self.assertNotIn("Pakistan", str(result))
                self.assertEqual(diagnostics["received"], 3)
                self.assertEqual(diagnostics["country_rejected"], 1)
                self.assertNotIn("test-key", str(result))
        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
