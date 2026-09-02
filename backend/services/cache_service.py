from typing import Any, Optional
import logging
import time
from threading import RLock

logger = logging.getLogger(__name__)

# In-memory dictionary for v1 (Replaces the need for Redis in Codespaces)
_internal_cache = {}
_cache_lock = RLock()

def set_cache(key: str, value: Any, ttl_seconds: float = 30.0) -> None:
    """Stores a value in the application cache."""
    with _cache_lock:
        _internal_cache[key] = (time.monotonic() + ttl_seconds, value)
    logger.debug(f"Cache set for key: {key}")

def get_cache(key: str) -> Optional[Any]:
    """Retrieves a value from the application cache if it exists."""
    with _cache_lock:
        entry = _internal_cache.get(key)
        if entry is None:
            logger.debug(f"Cache miss for key: {key}")
            return None
        expires_at, value = entry
        if expires_at <= time.monotonic():
            _internal_cache.pop(key, None)
            logger.debug(f"Cache expired for key: {key}")
            return None
        logger.debug(f"Cache hit for key: {key}")
        return value


def scoped_cache_key(namespace: str, facility_id: str, **parameters: Any) -> str:
    encoded = "&".join(f"{key}={parameters[key]}" for key in sorted(parameters))
    return f"{namespace}:facility={facility_id}:{encoded}"