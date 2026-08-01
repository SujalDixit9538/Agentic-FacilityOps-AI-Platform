from typing import Generator
from config.settings import settings
from backend.database.connection import SessionLocal

def get_settings():
    """Dependency injection for settings."""
    return settings

def get_db() -> Generator:
    """
    Dependency injection for the database session.
    Ensures the session is safely closed after the request completes,
    even if an exception occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()