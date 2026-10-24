import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Resolve the backend's own .env independently of the process working directory.
BACKEND_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(BACKEND_ENV_FILE, override=False)

class Settings(BaseSettings):
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "budgetbound_super_secret_signing_key_2026_dev")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Primary: PostgreSQL, Fallback: local SQLite file
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/budgetbound")
    SQLITE_FALLBACK_URL: str = "sqlite:///./budgetbound.db"
    GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "")
    GOOGLE_PLACES_TIMEOUT_SECONDS: float = 10.0
    FOURSQUARE_API_KEY: str = os.getenv("FOURSQUARE_API_KEY", "")
    FOURSQUARE_TIMEOUT_SECONDS: float = float(os.getenv("FOURSQUARE_TIMEOUT_SECONDS", "10"))
    FOURSQUARE_RATING_CACHE_TTL_SECONDS: int = int(os.getenv("FOURSQUARE_RATING_CACHE_TTL_SECONDS", "21600"))
    TRIP_FOURSQUARE_RATING_ENRICH_LIMIT: int = int(os.getenv("TRIP_FOURSQUARE_RATING_ENRICH_LIMIT", "8"))
    TRIP_FOURSQUARE_RATING_CONCURRENCY: int = int(os.getenv("TRIP_FOURSQUARE_RATING_CONCURRENCY", "3"))
    TRIP_DISCOVERY_SHORTLIST_SIZE: int = int(os.getenv("TRIP_DISCOVERY_SHORTLIST_SIZE", "6"))
    # Maximum candidates per Groq request. All feasible candidates are ranked in batches.
    # Reduced to 8 to fit within Groq context limits and reduce token usage
    TRIP_AI_RANK_BATCH_SIZE: int = int(os.getenv("TRIP_AI_RANK_BATCH_SIZE", "8"))
    GEOAPIFY_API_KEY: str = os.getenv("GEOAPIFY_API_KEY", "")
    GEOAPIFY_TIMEOUT_SECONDS: float = 10.0
    TRIP_MIN_DESTINATION_DISTANCE_KM: float = float(os.getenv("TRIP_MIN_DESTINATION_DISTANCE_KM", "50"))
    TRIP_MIN_LOCAL_GETAWAY_KM: float = float(os.getenv("TRIP_MIN_LOCAL_GETAWAY_KM", "20"))
    TRIP_ESTIMATE_INTERCITY_PER_KM_INR: float = float(os.getenv("TRIP_ESTIMATE_INTERCITY_PER_KM_INR", "1.5"))

    class Config:
        env_file = BACKEND_ENV_FILE
        extra = "ignore"

settings = Settings()
