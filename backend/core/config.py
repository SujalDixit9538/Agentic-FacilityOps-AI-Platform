from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Centralized configuration hook as per Blueprint Rule 2.4.
    Will be expanded in ETP-004.
    """
    PROJECT_NAME: str = "Agentic FacilityOPS AI Platform"
    API_V1_STR: str = "/api/v1"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Instantiate a global settings object to be used across the backend
settings = Settings()