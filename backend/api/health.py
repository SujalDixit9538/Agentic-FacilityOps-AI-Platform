from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.services.logging_service import get_logger
from backend.utils.api_responses import success_response

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Backward-compatible health endpoint with dependency status."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "operational"
        overall_status = "healthy"
    except Exception:
        logger.exception("Database connection failed during health check")
        db_status = "degraded"
        overall_status = "degraded"

    return success_response(
        message="FacilityOPS Backend health status.",
        data={
            "status": overall_status,
            "database": db_status,
        },
    )


@router.get("/liveness")
async def liveness_check():
    """Confirm that the API process is alive without checking dependencies."""
    return success_response(
        message="FacilityOPS Backend is alive.",
        data={"status": "alive"},
    )


@router.get("/readiness")
async def readiness_check(
    response: Response,
    db: Session = Depends(get_db),
):
    """Confirm that the API can serve requests requiring its database."""
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Database readiness check failed")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return success_response(
            message="FacilityOPS Backend is not ready.",
            data={"status": "not_ready", "database": "unavailable"},
        )

    return success_response(
        message="FacilityOPS Backend is ready.",
        data={"status": "ready", "database": "operational"},
    )
