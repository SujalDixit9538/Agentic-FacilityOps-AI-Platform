from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from backend.api.dependencies import get_db
from backend.services.occupancy_service import OccupancyService
from backend.services.mock_occupancy_service import seed_mock_occupancy_data
from backend.schemas.occupancy import OccupancyResponse, SecurityEventResponse
from backend.utils.api_responses import success_response

router = APIRouter()

@router.get("/health")
async def occupancy_module_health(db: Session = Depends(get_db)):
    """Verifies the Occupancy & Security module is online."""
    service = OccupancyService(db)
    status = service.get_module_status()
    return success_response(message="Occupancy module health check", data=status)

@router.post("/seed")
async def seed_occupancy_data(facility_id: str = Query("FAC-001"), days: int = Query(7), db: Session = Depends(get_db)):
    """Triggers the mock occupancy and security data pipeline."""
    occ_count, sec_count = seed_mock_occupancy_data(db, facility_id=facility_id, days=days)
    return success_response(
        message="Occupancy data pipeline executed.",
        data={"facility_id": facility_id, "occupancy_records_seeded": occ_count, "security_events_seeded": sec_count}
    )

@router.get("/records/{facility_id}")
async def get_occupancy_records(facility_id: str, limit: int = Query(100), db: Session = Depends(get_db)):
    """Retrieves headcount/utilization data for a given facility."""
    service = OccupancyService(db)
    records = service.get_facility_occupancy(facility_id, limit)
    
    data = [OccupancyResponse.model_validate(r).model_dump() for r in records]
    return success_response(message=f"Retrieved {len(data)} occupancy records", data={"records": data})

@router.get("/security/{facility_id}")
async def get_security_events(facility_id: str, limit: int = Query(50), db: Session = Depends(get_db)):
    """Retrieves security incidents for a given facility."""
    service = OccupancyService(db)
    events = service.get_security_logs(facility_id, limit)
    
    data = [SecurityEventResponse.model_validate(e).model_dump() for e in events]
    return success_response(message=f"Retrieved {len(data)} security events", data={"events": data})

@router.get("/analyze/{facility_id}")
async def analyze_facility_security(facility_id: str, db: Session = Depends(get_db)):
    """Runs the Occupancy & Security Agent analysis on the specified facility."""
    service = OccupancyService(db)
    insights = service.run_agent_analysis(facility_id)
    
    return success_response(
        message=f"Occupancy and Security analysis completed for {facility_id}",
        data=insights
    )