from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from backend.api.dependencies import get_db
from backend.services.energy_service import EnergyService
from backend.services.mock_iot_service import seed_mock_energy_data
from backend.schemas.energy import EnergyRecordResponse
from backend.utils.api_responses import success_response

router = APIRouter()

@router.get("/health")
async def energy_module_health(db: Session = Depends(get_db)):
    """Verifies the Energy module is online and services are accessible."""
    service = EnergyService(db)
    status = service.get_module_status()
    return success_response(message="Energy module health check", data=status)

@router.post("/seed")
async def seed_energy_data(facility_id: str = Query("FAC-001"), days: int = Query(7), db: Session = Depends(get_db)):
    """Triggers the mock IoT ingestion pipeline for a given facility."""
    count = seed_mock_energy_data(db, facility_id=facility_id, days=days)
    return success_response(
        message=f"Mock data pipeline executed successfully.",
        data={"facility_id": facility_id, "records_seeded": count}
    )

@router.get("/records/{facility_id}", response_model=dict)
async def get_energy_records(facility_id: str, limit: int = 200, db: Session = Depends(get_db)):
    """Retrieves basic energy consumption records for a facility."""
    service = EnergyService(db)
    records = service.get_facility_energy_history(facility_id, limit)
    
    # Convert SQLAlchemy models to dictionaries for the standard response wrapper
    data = [EnergyRecordResponse.model_validate(r).model_dump() for r in records]
    
    return success_response(
        message=f"Retrieved {len(data)} records for {facility_id}",
        data={"records": data}
    )