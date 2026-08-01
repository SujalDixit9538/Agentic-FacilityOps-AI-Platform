from fastapi import APIRouter
from backend.services.logging_service import get_logger
from backend.utils.api_responses import success_response

logger = get_logger(__name__)
router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Lightweight health endpoint to verify the backend is running.
    """
    logger.info("Health check endpoint accessed.")
    logger.debug("Health check debug trace successful.")
    
    # Utilize our new shared utility
    return success_response(
        message="FacilityOPS Backend is operational.",
        data={"status": "healthy"}
    )