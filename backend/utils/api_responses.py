from fastapi.responses import JSONResponse
from typing import Any, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


def _has_observations(value: Any) -> bool:
    if isinstance(value, list):
        return bool(value)
    if isinstance(value, dict):
        lists = [item for item in value.values() if isinstance(item, list)]
        if lists:
            return any(lists)
        nested = [item for item in value.values() if isinstance(item, dict)]
        return any(_has_observations(item) for item in nested) if nested else True
    return True

def success_response(
    message: str,
    data: Optional[Any] = None,
    *,
    provenance: Optional[dict] = None,
    freshness: Optional[dict] = None,
    degraded: Optional[bool] = None,
    quality_flags: Optional[list[str]] = None,
) -> dict:
    """Standardized response with explicit data trust metadata."""
    if data is None:
        quality_flags = quality_flags or ["data_unavailable"]
        inferred_degraded = True
        freshness_status = "unavailable"
    elif not _has_observations(data):
        quality_flags = quality_flags or ["no_data"]
        inferred_degraded = True
        freshness_status = "empty"
    else:
        inferred_degraded = False
        freshness_status = "available"

    generated_at = datetime.now(timezone.utc).isoformat()
    return {
        "success": True,
        "message": message,
        "data": data if data is not None else {},
        "provenance": provenance or {"source": "facilityops_api", "generated_at": generated_at},
        "freshness": freshness or {"status": freshness_status, "as_of": generated_at},
        "degraded": inferred_degraded if degraded is None else degraded,
        "quality_flags": quality_flags or [],
    }

def error_response(message: str, status_code: int = 400) -> JSONResponse:
    """Standardized error response generator ensuring no stack traces leak."""
    logger.error(f"API Error Response ({status_code}): {message}")
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "data": None,
            "provenance": {"source": "facilityops_api"},
            "freshness": {"status": "unavailable"},
            "degraded": True,
            "quality_flags": ["error", "data_unavailable"],
        }
    )