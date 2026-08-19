from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from backend.api.dependencies import get_db
from backend.services.occupancy_service import OccupancyService
from backend.services.mock_occupancy_service import seed_mock_occupancy_data
from backend.schemas.occupancy import (
    OccupancyRecordResponse, OccupancyZoneResponse,
    OccupancyImageBase, OccupancyImageResponse, SecurityEventResponse,
)
from backend.schemas.dashboard import OccupancyDashboardResponse
from backend.utils.api_responses import success_response

# NOTE: no prefix here — router.py's include_router(occupancy.router, prefix="/occupancy", ...)
# is what adds the /occupancy prefix, matching the energy/maintenance/cost pattern.
router = APIRouter()


@router.get("/health")
async def occupancy_module_health(db: Session = Depends(get_db)):
    """Verifies the Occupancy & Security module is online."""
    service = OccupancyService(db)
    status = service.get_module_status()
    return success_response(message="Occupancy module health check", data=status)


@router.post("/seed")
async def seed_occupancy_data(facility_id: str = Query("FAC-001"), days: int = Query(7), db: Session = Depends(get_db)):
    """Triggers the zone generation + mock occupancy/security data pipeline."""
    occ_count, sec_count = seed_mock_occupancy_data(db, facility_id=facility_id, days=days)
    return success_response(
        message="Occupancy data pipeline executed.",
        data={"facility_id": facility_id, "occupancy_records_seeded": occ_count, "security_events_seeded": sec_count},
    )


@router.get("/zones/{facility_id}")
async def get_zones(facility_id: str, db: Session = Depends(get_db)):
    """Lists the real, per-facility generated zones (for the heatmap / room analytics dashboard)."""
    service = OccupancyService(db)
    zones = service.get_zones(facility_id)
    data = [OccupancyZoneResponse.model_validate(z).model_dump() for z in zones]
    return success_response(message=f"Retrieved {len(data)} zones", data={"zones": data})


@router.get("/utilization/{facility_id}")
async def get_utilization(facility_id: str, db: Session = Depends(get_db)):
    """Current utilization %, grouped by zone_type (Office Floor / Meeting Room / Common Area / Parking)."""
    service = OccupancyService(db)
    utilization = service.get_zone_utilization(facility_id)
    return success_response(message=f"Utilization computed for {facility_id}", data=utilization)


@router.get("/records/{facility_id}")
async def get_occupancy_records(facility_id: str, limit: int = Query(100), db: Session = Depends(get_db)):
    """Retrieves headcount/utilization time-series for a given facility."""
    service = OccupancyService(db)
    records = service.get_facility_occupancy(facility_id, limit)
    data = [OccupancyRecordResponse.model_validate(r).model_dump() for r in records]
    return success_response(message=f"Retrieved {len(data)} occupancy records", data={"records": data})


@router.post("/images")
async def log_image_detection(data: OccupancyImageBase, db: Session = Depends(get_db)):
    """Logs a CNN detection — also mirrors it into occupancy_records (source='cnn') per the hybrid design."""
    service = OccupancyService(db)
    image = service.log_image_detection(data)
    return success_response(
        message="Image detection logged", data=OccupancyImageResponse.model_validate(image).model_dump()
    )


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
    return success_response(message=f"Occupancy and Security analysis completed for {facility_id}", data=insights)


@router.get("/dashboard/{facility_id}")
async def get_dashboard_data(facility_id: str, db: Session = Depends(get_db)):
    """Aggregated dashboard metrics for the Occupancy UI."""
    service = OccupancyService(db)
    data = service.get_dashboard_data(facility_id)
    return success_response(message=f"Dashboard data generated for {facility_id}", data=data)
