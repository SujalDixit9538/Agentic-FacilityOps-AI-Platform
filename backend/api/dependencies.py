from backend.core.config import Settings, settings

def get_settings() -> Settings:
    """
    Dependency injection for settings. 
    Future services (like database sessions and agent configurations) 
    will follow this exact pattern.
    """
    return settings