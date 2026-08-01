import logging
from fastapi import Request
from fastapi.responses import JSONResponse

# Note: We will wire this into a centralized logging service in ETP-004
logger = logging.getLogger(__name__)

async def global_exception_handler(request: Request, exc: Exception):
    """
    Catches unhandled exceptions to prevent stack traces from reaching the UI.
    Enforces Blueprint Rule 5.3.
    """
    logger.error(f"Unhandled exception on {request.url.path}: {repr(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An internal system error occurred. The platform is running in degraded mode.",
            "data": None
        }
    )