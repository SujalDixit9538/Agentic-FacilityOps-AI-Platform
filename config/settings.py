from pydantic_settings import BaseSettings
from typing import Optional

class AppSettings(BaseSettings):
    """
    Centralized configuration as per Blueprint Part 5 (Sprint 2).
    No hardcoded values should exist outside this file.
    """
    PROJECT_NAME: str = "Agentic FacilityOPS AI Platform"
    API_V1_STR: str = "/api/v1"
    
    # Database config for Micro-step 2
    DATABASE_URL: str = "sqlite:///./data/facilityops.db"
    
    # Logging
    LOG_CONFIG_PATH: str = "config/logging.yaml"

    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = AppSettings()