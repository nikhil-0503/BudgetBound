import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "budgetbound_super_secret_signing_key_2026_dev")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Primary: PostgreSQL, Fallback: local SQLite file
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/budgetbound")
    SQLITE_FALLBACK_URL: str = "sqlite:///./budgetbound.db"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
