from fastapi.responses import JSONResponse
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

def success_response(message: str, data: Optional[Any] = None) -> dict:
    """Standardized success response generator."""
    return {
        "success": True,
        "message": message,
        "data": data or {}
    }

def error_response(message: str, status_code: int = 400) -> JSONResponse:
    """Standardized error response generator ensuring no stack traces leak."""
    logger.error(f"API Error Response ({status_code}): {message}")
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "data": None
        }
    )