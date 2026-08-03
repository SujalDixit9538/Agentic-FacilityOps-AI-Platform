from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.services.executive_service import ExecutiveService
from backend.utils.api_responses import success_response

router = APIRouter()

@router.get("/analyze/{facility_id}")
async def analyze_facility_executive(facility_id: str, db: Session = Depends(get_db)):
    """
    Runs the Executive Agent to poll all domain agents and synthesize 
    a unified, facility-wide health and threat report.
    """
    service = ExecutiveService(db)
    insights = service.run_platform_analysis(facility_id)
    
    return success_response(
        message=f"Executive cross-module analysis completed for {facility_id}",
        data=insights
    )