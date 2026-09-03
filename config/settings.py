from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Central application configuration loaded from environment variables."""

    PROJECT_NAME: str = "Agentic FacilityOPS AI Platform"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = "sqlite:///./data/facilityops.db"

    # Logging
    LOG_CONFIG_PATH: str = "config/logging.yaml"

    # LLM providers
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None

    # Domain configuration
    CARBON_EMISSION_FACTOR_KG_PER_KWH: float = 0.4

    # Demo/runtime behavior
    AUTO_SEED_DEMO_DATA: bool = False

    # Comma-separated browser origins, e.g. http://localhost:8501,http://127.0.0.1:8501
    CORS_ORIGINS: str = "http://localhost:8501,http://127.0.0.1:8501"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        """Return normalized CORS origins from the environment setting."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = AppSettings()
