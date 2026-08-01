from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.services.logging_service import get_logger
from backend.utils.api_responses import success_response
from backend.api.dependencies import get_db

logger = get_logger(__name__)
router = APIRouter()

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health endpoint that also verifies database connectivity (ETP-005 Integration).
    """
    logger.info("Health check endpoint accessed.")
    
    try:
        # Lightweight query to confirm database initialization succeeds
        db.execute(text("SELECT 1"))
        db_status = "operational"
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        db_status = "degraded"
    
    # Utilize our shared utility
    return success_response(
        message="FacilityOPS Backend is operational.",
        data={
            "status": "healthy",
            "database": db_status
        }
    )