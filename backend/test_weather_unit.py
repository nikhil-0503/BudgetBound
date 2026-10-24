import asyncio
import unittest
from unittest.mock import AsyncMock, patch

import httpx

from app.services import weather


class WeatherServiceTests(unittest.TestCase):
    def test_geocoding_selects_named_city_alias_not_first_search_result(self):
        async def run():
            response = httpx.Response(200, json={"results": [
                {"name": "Bengaluru", "latitude": 12.97, "longitude": 77.59, "country": "India", "admin1": "Karnataka"},
                {"name": "Bangalore", "latitude": 34.0, "longitude": -81.0, "country": "United States", "admin1": "South Carolina"},
            ]}, request=httpx.Request("GET", "https://geocoding-api.open-meteo.com/v1/search"))
            client = AsyncMock(); client.get.return_value = response
            with patch.object(weather.httpx, "AsyncClient") as factory:
                factory.return_value.__aenter__.return_value = client
                lat, lon, label = await weather.resolve_location("Bangalore")
            self.assertEqual((lat, lon), (12.97, 77.59))
            self.assertIn("Bengaluru", label)
            self.assertEqual(client.get.await_args.kwargs["params"]["count"], 10)
        asyncio.run(run())

    def test_geocoding_does_not_substitute_an_unmatched_place(self):
        async def run():
            response = httpx.Response(200, json={"results": [{"name": "Nearby District", "latitude": 20, "longitude": 80, "country": "India"}]}, request=httpx.Request("GET", "https://geocoding-api.open-meteo.com/v1/search"))
            client = AsyncMock(); client.get.return_value = response
            with patch.object(weather.httpx, "AsyncClient") as factory:
                factory.return_value.__aenter__.return_value = client
                with self.assertRaisesRegex(weather.WeatherServiceError, "ambiguous"):
                    await weather.resolve_location("A City That Does Not Match")
        asyncio.run(run())

    def test_coordinates_and_forecast_cache(self):
        weather._cache.clear()
        payload = {"latitude": 12.9, "longitude": 77.6, "timezone": "Asia/Kolkata", "current": {"temperature_2m": 28}, "hourly": {}, "daily": {"time": ["2026-10-23"], "weather_code": [1], "temperature_2m_min": [22], "temperature_2m_max": [30]}}
        response = type("Response", (), {"json": lambda self: payload, "raise_for_status": lambda self: None})()
        client = AsyncMock(); client.get.return_value = response

        async def run():
            with patch.object(weather.httpx, "AsyncClient") as factory:
                factory.return_value.__aenter__.return_value = client
                result = await weather.get_forecast(12.9, 77.6, 1, "Bengaluru")
                await weather.get_forecast(12.9, 77.6, 1, "Bengaluru")
                self.assertEqual(result["daily"]["temperature_2m_max"], [30])
                self.assertEqual(client.get.await_count, 1)
        asyncio.run(run())
        with self.assertRaises(ValueError):
            weather.validate_coordinates(90.1, 0)


if __name__ == "__main__":
    unittest.main()
