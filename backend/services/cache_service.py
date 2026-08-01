from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

# In-memory dictionary for v1 (Replaces the need for Redis in Codespaces)
_internal_cache = {}

def set_cache(key: str, value: Any) -> None:
    """Stores a value in the application cache."""
    _internal_cache[key] = value
    logger.debug(f"Cache set for key: {key}")

def get_cache(key: str) -> Optional[Any]:
    """Retrieves a value from the application cache if it exists."""
    value = _internal_cache.get(key)
    if value:
        logger.debug(f"Cache hit for key: {key}")
    else:
        logger.debug(f"Cache miss for key: {key}")
    return value