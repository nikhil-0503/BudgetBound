import asyncio
import unittest
from unittest.mock import patch

import httpx

from app.services import geoapify_places as geo


def feature(place_id="x", *, name="Mysuru Park", city="Mysuru", country="India", country_code="in", lat=12.3, lon=76.6, categories=None, rating=None, reviews=None):
    props = {"place_id": place_id, "name": name, "city": city, "state": "Karnataka", "country": country, "country_code": country_code, "lat": lat, "lon": lon, "formatted": f"{name}, {city}, {country}", "categories": categories or ["natural.mountain"]}
    if rating is not None:
        props["rating"] = rating
    if reviews is not None:
        props["review_count"] = reviews
    return {"type": "Feature", "id": place_id, "properties": props, "geometry": {"type": "Point", "coordinates": [lon, lat]}}


class FakeAsyncClient:
    def __init__(self, response):
        self.response = response
        self.call = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def get(self, url, *, params):
        self.call = (url, params)
        self.response._request = httpx.Request("GET", url)
        return self.response


class TimeoutAsyncClient(FakeAsyncClient):
    async def get(self, url, *, params):
        raise httpx.ReadTimeout("request timed out")


class GeoapifyPlacesTests(unittest.TestCase):
    def test_normalizes_geojson_and_does_not_fabricate_ratings(self):
        normalized = geo.normalize_place(feature())
        self.assertEqual(normalized["place_id"], "x")
        self.assertEqual(normalized["country_code"], "IN")
        self.assertEqual(normalized["locality"], "Mysuru")
        self.assertEqual(normalized["categories"], ["natural.mountain"])
        self.assertIsNone(normalized["rating"])
        self.assertIsNone(normalized["user_rating_count"])
        self.assertIsNone(normalized["map_url"])

    def test_provider_supplied_rating_review_count_and_map_url_are_preserved(self):
        row = feature(rating=4.7, reviews=81)
        row["properties"]["place_url"] = "https://example.test/place/x"
        normalized = geo.normalize_place(row)
        self.assertEqual(normalized["rating"], 4.7)
        self.assertEqual(normalized["user_rating_count"], 81)
        self.assertEqual(normalized["map_url"], "https://example.test/place/x")

    def test_rejects_conflicting_or_swapped_geojson_geometry_coordinates(self):
        row = feature()
        row["geometry"]["coordinates"] = [12.3, 76.6]
        self.assertIsNone(geo.normalize_place(row))

    def test_success_uses_official_endpoint_supported_categories_and_lon_lat_filter(self):
        async def run():
            response = httpx.Response(200, json={"features": [feature()]})
            client = FakeAsyncClient(response)
            with patch.object(geo.settings, "GEOAPIFY_API_KEY", "unit-test-key"), patch.object(geo.httpx, "AsyncClient", return_value=client):
                result = await geo.search_places(latitude=12.3, longitude=76.6, radius_m=60000, categories=geo.category_values("Nature"), limit=40)
            url, params = client.call
            self.assertEqual(url, "https://api.geoapify.com/v2/places")
            self.assertEqual(params["filter"], "circle:76.6,12.3,60000")
            self.assertEqual(params["categories"], "national_park,natural,leisure.park")
            self.assertEqual(params["apiKey"], "unit-test-key")
            self.assertEqual(result[0]["data_source"], "geoapify")
        asyncio.run(run())

    def test_successful_empty_response_is_not_provider_error(self):
        async def run():
            client = FakeAsyncClient(httpx.Response(200, json={"features": []}))
            with patch.object(geo.settings, "GEOAPIFY_API_KEY", "unit-test-key"), patch.object(geo.httpx, "AsyncClient", return_value=client):
                self.assertEqual(await geo.search_places(latitude=12.3, longitude=76.6, radius_m=1000, categories=("natural",)), [])
        asyncio.run(run())

    def test_bangalore_and_hyderabad_circle_centers_use_longitude_latitude(self):
        async def run(latitude, longitude, expected):
            client = FakeAsyncClient(httpx.Response(200, json={"features": []}))
            with patch.object(geo.settings, "GEOAPIFY_API_KEY", "unit-test-key"), patch.object(geo.httpx, "AsyncClient", return_value=client):
                await geo.search_places(latitude=latitude, longitude=longitude, radius_m=1000, categories=("natural",))
            self.assertEqual(client.call[1]["filter"], expected)
            self.assertEqual(client.call[1]["bias"], "proximity:" + expected.removeprefix("circle:").rsplit(",", 1)[0])
        asyncio.run(run(12.97, 77.59, "circle:77.59,12.97,1000"))
        asyncio.run(run(17.385, 78.4867, "circle:78.4867,17.385,1000"))

    def test_only_verified_india_passes_filter(self):
        self.assertTrue(geo.is_destination_in_india(geo.normalize_place(feature())))
        self.assertFalse(geo.is_destination_in_india(geo.normalize_place(feature(country="Nepal", country_code="np"))))
        self.assertFalse(geo.is_destination_in_india(geo.normalize_place(feature(country_code=None))))
        self.assertFalse(geo.is_destination_in_india(geo.normalize_place(feature(country=None))))
        self.assertFalse(geo.is_destination_in_india(geo.normalize_place(feature(lat=40, lon=80))))

    def test_explicit_geoapify_category_mapping(self):
        self.assertEqual(geo.matched_trip_categories(["natural.mountain"]), {"Nature", "Adventure", "Solo"})
        self.assertIn("Religious", geo.matched_trip_categories(["religion.place_of_worship.hinduism"]))
        for category in ("Nature", "Adventure", "Family", "Religious", "Beach", "City Exploration", "Romantic", "Solo"):
            self.assertTrue(geo.category_values(category), category)

    def test_missing_key_fails_without_network_or_secret_in_message(self):
        async def run():
            with patch.object(geo.settings, "GEOAPIFY_API_KEY", ""), patch.object(geo.httpx, "AsyncClient") as client:
                with self.assertRaises(geo.GeoapifyError) as error:
                    await geo.search_places(latitude=12.3, longitude=76.6, radius_m=1000, categories=("natural",))
                client.assert_not_called()
                self.assertIn("GEOAPIFY_API_KEY", str(error.exception))
        asyncio.run(run())

    def test_timeout_is_reported_as_provider_unavailable(self):
        async def run():
            with patch.object(geo.settings, "GEOAPIFY_API_KEY", "unit-test-key"), patch.object(geo.httpx, "AsyncClient", return_value=TimeoutAsyncClient(None)):
                with self.assertRaises(geo.GeoapifyError) as error:
                    await geo.search_places(latitude=12.3, longitude=76.6, radius_m=1000, categories=("natural",))
            self.assertEqual(error.exception.status_code, 503)
            self.assertIn("timed out", str(error.exception))
        asyncio.run(run())

    def test_status_errors_are_actionable_and_do_not_include_key(self):
        async def run(status, expected_status, phrase):
            client = FakeAsyncClient(httpx.Response(status, json={"message": "provider error"}))
            with patch.object(geo.settings, "GEOAPIFY_API_KEY", "private-test-key"), patch.object(geo.httpx, "AsyncClient", return_value=client):
                with self.assertRaises(geo.GeoapifyError) as error:
                    await geo.search_places(latitude=12.3, longitude=76.6, radius_m=1000, categories=("natural",))
            self.assertEqual(error.exception.status_code, expected_status)
            self.assertIn(phrase, str(error.exception))
            self.assertNotIn("private-test-key", str(error.exception))
        asyncio.run(run(401, 503, "rejected"))
        asyncio.run(run(403, 503, "restrictions"))
        asyncio.run(run(400, 502, "categories"))
        asyncio.run(run(429, 429, "quota"))
        asyncio.run(run(503, 503, "temporarily unavailable"))


if __name__ == "__main__":
    unittest.main()
