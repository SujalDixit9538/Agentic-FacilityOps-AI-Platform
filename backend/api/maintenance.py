from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from backend.api.dependencies import get_db
from backend.services.maintenance_service import MaintenanceService
from backend.services.mock_maintenance_service import seed_mock_maintenance_data
from backend.schemas.maintenance import AssetResponse, MaintenanceLogResponse
from backend.utils.api_responses import success_response

router = APIRouter()

@router.get("/health")
async def maintenance_module_health(db: Session = Depends(get_db)):
    """Verifies the Maintenance module is online."""
    service = MaintenanceService(db)
    status = service.get_module_status()
    return success_response(message="Maintenance module health check", data=status)

@router.post("/seed")
async def seed_maintenance_data(facility_id: str = Query("FAC-001"), db: Session = Depends(get_db)):
    """Triggers the mock asset and maintenance history pipeline."""
    assets_count, logs_count = seed_mock_maintenance_data(db, facility_id=facility_id)
    return success_response(
        message="Maintenance data pipeline executed.",
        data={"facility_id": facility_id, "assets_seeded": assets_count, "logs_seeded": logs_count}
    )

@router.get("/assets/{facility_id}")
async def get_assets(facility_id: str, db: Session = Depends(get_db)):
    """Retrieves all assets for a given facility."""
    service = MaintenanceService(db)
    assets = service.get_facility_assets(facility_id)
    
    data = [AssetResponse.model_validate(a).model_dump() for a in assets]
    return success_response(message=f"Retrieved {len(data)} assets", data={"assets": data})

@router.get("/logs/{asset_id}")
async def get_maintenance_logs(asset_id: str, limit: int = 50, db: Session = Depends(get_db)):
    """Retrieves the maintenance history for a given asset."""
    service = MaintenanceService(db)
    logs = service.get_asset_maintenance_history(asset_id, limit)
    
    data = [MaintenanceLogResponse.model_validate(l).model_dump() for l in logs]
    return success_response(message=f"Retrieved {len(data)} maintenance logs", data={"logs": data})