"""Open-Meteo forecast client with a small in-process TTL cache."""
import asyncio
import logging
import re
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
TTL_SECONDS = 20 * 60
_cache: dict[tuple, tuple[float, dict[str, Any]]] = {}
_locks: dict[tuple, asyncio.Lock] = {}


class WeatherServiceError(Exception):
    pass


def validate_coordinates(latitude: float, longitude: float) -> None:
    if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
        raise ValueError("Latitude must be between -90 and 90 and longitude between -180 and 180.")


async def get_forecast(latitude: float, longitude: float, days: int = 7, location_name: str | None = None) -> dict[str, Any]:
    validate_coordinates(latitude, longitude)
    if not 1 <= days <= 16:
        raise ValueError("Forecast days must be between 1 and 16.")
    lat, lon = round(latitude, 3), round(longitude, 3)
    key = (lat, lon, days)
    now = time.monotonic()
    cached = _cache.get(key)
    if cached and now - cached[0] < TTL_SECONDS:
        data = cached[1].copy()
        if location_name:
            data["location_name"] = location_name
        return data
    lock = _locks.setdefault(key, asyncio.Lock())
    async with lock:
        cached = _cache.get(key)
        if cached and time.monotonic() - cached[0] < TTL_SECONDS:
            data = cached[1].copy()
            if location_name:
                data["location_name"] = location_name
            return data
        params = {
            "latitude": lat, "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
            "hourly": "temperature_2m,precipitation_probability,weather_code",
            "daily": "weather_code,temperature_2m_min,temperature_2m_max,precipitation_probability_max,sunrise,sunset",
            "forecast_days": days, "timezone": "auto",
        }
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=4.0)) as client:
                response = await client.get(FORECAST_URL, params=params)
                response.raise_for_status()
                raw = response.json()
            current, daily = raw.get("current"), raw.get("daily")
            if not isinstance(current, dict) or not isinstance(daily, dict) or not isinstance(daily.get("time"), list):
                raise WeatherServiceError("Weather provider returned an incomplete forecast.")
            required_daily = ("weather_code", "temperature_2m_min", "temperature_2m_max")
            if any(not isinstance(daily.get(field), list) for field in required_daily):
                raise WeatherServiceError("Weather provider returned malformed daily data.")
            forecast = {
                "location_name": location_name, "latitude": raw.get("latitude", lat), "longitude": raw.get("longitude", lon),
                "timezone": raw.get("timezone"), "current": current, "hourly": raw.get("hourly", {}), "daily": daily,
                "forecast_days": len(daily["time"]), "units": {"current": raw.get("current_units", {}), "daily": raw.get("daily_units", {})},
            }
            _cache[key] = (time.monotonic(), forecast)
            return forecast
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            logger.warning("Open-Meteo request failed (%s)", type(exc).__name__)
            raise WeatherServiceError("Weather forecast is temporarily unavailable.") from exc
        except httpx.HTTPStatusError as exc:
            logger.warning("Open-Meteo returned HTTP %s", exc.response.status_code)
            raise WeatherServiceError("Weather forecast provider returned an error.") from exc
        except (ValueError, TypeError) as exc:
            logger.warning("Open-Meteo returned invalid JSON")
            raise WeatherServiceError("Weather forecast provider returned invalid data.") from exc
        finally:
            if not lock.locked():
                _locks.pop(key, None)


async def resolve_location(query: str) -> tuple[float, float, str]:
    """Resolve an exact or recognized alias without silently choosing a nearby name."""
    aliases = {"bangalore": "bengaluru", "bombay": "mumbai", "calcutta": "kolkata", "madras": "chennai", "mysore": "mysuru", "gurgaon": "gurugram", "new delhi": "delhi", "pondicherry": "puducherry"}
    def normalized(value: str) -> str:
        return " ".join(re.sub(r"[^a-z0-9 ]+", " ", value.casefold()).split())

    query_full = normalized(query)
    query_name = normalized(query.split(",", 1)[0])
    query_key = aliases.get(query_name, query_name)
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(8.0, connect=4.0)) as client:
            response = await client.get("https://geocoding-api.open-meteo.com/v1/search", params={"name": query, "count": 10, "language": "en", "format": "json"})
            response.raise_for_status()
            data = response.json()
        results = data.get("results") or []
        matches = []
        for place in results:
            place_name = normalized(str(place.get("name") or ""))
            place_key = aliases.get(place_name, place_name)
            # Exact name or canonical alias. A longer query may add a state or country.
            if place_key == query_key or (query_full.startswith(place_name + " ") and place_name):
                matches.append(place)
        if len(matches) > 1:
            india_matches = [place for place in matches if normalized(str(place.get("country") or "")) == "india"]
            if len(india_matches) == 1:
                matches = india_matches
        if not matches and len(results) == 1:
            only_name = normalized(str(results[0].get("name") or ""))
            if only_name and (only_name.startswith(query_name) or query_name.startswith(only_name)):
                matches = [results[0]]
        # Collapse duplicate geocoder records at the same point; otherwise an
        # ambiguous same-name city must be made more specific by the user.
        unique = {}
        for place in matches:
            try:
                key = (round(float(place["latitude"]), 3), round(float(place["longitude"]), 3), normalized(str(place.get("country") or "")))
                unique[key] = place
            except (KeyError, TypeError, ValueError):
                continue
        if len(unique) != 1:
            raise WeatherServiceError("Location is ambiguous; please choose a more specific destination.")
        place = next(iter(unique.values()))
        lat, lon = float(place["latitude"]), float(place["longitude"])
        validate_coordinates(lat, lon)
        return lat, lon, ", ".join(part for part in (place.get("name"), place.get("admin1"), place.get("country")) if part)
    except WeatherServiceError:
        raise
    except (httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
        logger.warning("Open-Meteo geocoding failed for a place query")
        raise WeatherServiceError("Could not resolve this destination for a forecast.") from exc
