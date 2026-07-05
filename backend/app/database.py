import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import OperationalError
from app.config import settings

logger = logging.getLogger("uvicorn.error")

# Try to connect to PostgreSQL. Fallback to SQLite if it fails.
engine = None
is_sqlite = False

try:
    # Attempt to initialize PostgreSQL engine
    if settings.DATABASE_URL.startswith("postgresql"):
        engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 5}  # Short timeout to detect failure quickly
        )
        # Test connection
        with engine.connect() as conn:
            logger.info("Successfully connected to PostgreSQL database.")
    else:
        raise ValueError("Not a PostgreSQL URL")
except (OperationalError, Exception) as e:
    logger.warning(
        f"PostgreSQL connection failed: {e}. Falling back to SQLite database at {settings.SQLITE_FALLBACK_URL}"
    )
    is_sqlite = True
    engine = create_engine(
        settings.SQLITE_FALLBACK_URL,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
