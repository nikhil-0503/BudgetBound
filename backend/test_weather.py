"""Weather service tests; all provider calls are mocked and offline."""
import asyncio
import json
import os
import sys
from unittest.mock import AsyncMock, patch

import httpx
import pytest

sys.path.insert(0, os.path.dirname(__file__))
from app.services import weather


def sample():
    return {
        "latitude": 13.0, "longitude": 80.0, "timezone": "Asia/Kolkata",
        "current": {"temperature_2m": 29, "weather_code": 1}, "current_units": {"temperature_2m": "°C"},
        "hourly": {"time": [], "temperature_2m": [], "precipitation_probability": [], "weather_code": []},
        "daily": {"time": ["2026-10-23"], "weather_code": [1], "temperature_2m_min": [24], "temperature_2m_max": [31], "precipitation_probability_max": [10], "sunrise": [None], "sunset": [None]},
        "daily_units": {"temperature_2m_min": "°C", "temperature_2m_max": "°C"},
    }


def test_valid_forecast_and_coordinate_requests_and_cache():
    weather._cache.clear()
    client = AsyncMock()
    response = httpx.Response(200, json=sample())
    client.get.return_value = response

    async def go():
        with patch.object(weather.httpx, "AsyncClient") as factory:
            factory.return_value.__aenter__.return_value = client
            first = await weather.get_forecast(13.0, 80.0, 1, "Chennai")
            again = await weather.get_forecast(13.0, 80.0, 1, "Chennai")
            other = await weather.get_forecast(28.6, 77.2, 1, "Delhi")
        assert first["daily"]["temperature_2m_max"] == [31]
        assert again["timezone"] == "Asia/Kolkata"
        assert client.get.await_count == 2
        assert client.get.await_args_list[0].kwargs["params"]["latitude"] == 28.6
        assert other["location_name"] == "Delhi"
    asyncio.run(go())


def test_invalid_coordinates_days_and_malformed_payload():
    with pytest.raises(ValueError):
        weather.validate_coordinates(91, 0)
    with pytest.raises(ValueError):
        asyncio.run(weather.get_forecast(0, 181))
    response = httpx.Response(200, json={"current": {}, "daily": {"time": []}})
    async def go():
        with patch.object(weather.httpx, "AsyncClient") as factory:
            factory.return_value.__aenter__.return_value.get.return_value = response
            with pytest.raises(weather.WeatherServiceError):
                await weather.get_forecast(40, 10, 2)
    asyncio.run(go())


def test_ambiguous_geocode_and_upstream_errors():
    response = httpx.Response(200, json={"results": [{"latitude": 1, "longitude": 2}, {"latitude": 3, "longitude": 4}]})
    async def go():
        with patch.object(weather.httpx, "AsyncClient") as factory:
            factory.return_value.__aenter__.return_value.get.return_value = response
            with pytest.raises(weather.WeatherServiceError, match="ambiguous"):
                await weather.resolve_location("Springfield")
    asyncio.run(go())
