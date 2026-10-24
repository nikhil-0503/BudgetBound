from fastapi import APIRouter, HTTPException, Query

from app.services.weather import WeatherServiceError, get_forecast, validate_coordinates

router = APIRouter(prefix="/api/weather", tags=["Weather"])


@router.get("/forecast", summary="Get a destination forecast from Open-Meteo")
async def weather_forecast(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    days: int = Query(7, ge=1, le=16),
    location_name: str | None = Query(None, max_length=160),
):
    try:
        validate_coordinates(latitude, longitude)
        return await get_forecast(latitude, longitude, days, location_name)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except WeatherServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
