from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

try:
    # connect_args={"check_same_thread": False} is required for SQLite in FastAPI 
    # to prevent issues when multiple requests attempt to access the DB simultaneously.
    engine = create_engine(
        settings.DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("Database engine and session maker initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize database connection: {e}")