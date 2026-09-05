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
    CORS_ORIGINS: str = "http://localhost:8501,http://127.0.0.1:8501"
    API_AUTH_TOKEN: Optional[str] = None
    API_ADMIN_TOKEN: Optional[str] = None
    FACILITY_ACCESS_ALLOWLIST: str = ""
    RATE_LIMIT_PER_MINUTE: int = 120

    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    CARBON_EMISSION_FACTOR_KG_PER_KWH: float = 0.4
    AUTO_SEED_DEMO_DATA: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = AppSettings()