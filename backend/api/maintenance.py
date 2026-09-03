from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from backend.api.dependencies import get_db
from backend.services.maintenance_service import MaintenanceService
from backend.services.mock_maintenance_service import seed_mock_maintenance_data
from backend.schemas.maintenance import AssetResponse, MaintenanceLogResponse
from backend.schemas.manual_predict import ManualPredictRequest
from backend.utils.api_responses import success_response
from backend.agents.maintenance.analyzer import MaintenanceAnalyzer
from backend.services.facility_catalog_service import FacilityCatalogService

router = APIRouter()

@router.get("/health")
async def maintenance_module_health(db: Session = Depends(get_db)):
    """Verifies the Maintenance module is online."""
    service = MaintenanceService(db)
    status = service.get_module_status()
    return success_response(message="Maintenance module health check", data=status)

@router.get("/facilities")
async def get_facilities(db: Session = Depends(get_db)):
    """Return active canonical facilities and display metadata."""
    facilities = FacilityCatalogService(db).list_active()
    facility_ids = [facility.facility_id for facility in facilities]
    facility_options = [
        {
            "facility_id": facility.facility_id,
            "name": facility.name,
            "facility_type": facility.facility_type,
            "total_area_sqft": facility.total_area_sqft,
            "total_floors": facility.total_floors,
        }
        for facility in facilities
    ]
    return success_response(
        message="Retrieved facilities",
        data={
            "facilities": facility_ids,
            "facility_options": facility_options,
        },
    )

@router.post("/seed")
async def seed_maintenance_data(facility_id: str = Query(None), db: Session = Depends(get_db)):
    """Triggers the mock asset and maintenance history pipeline."""
    import pandas as pd
    df = pd.read_csv("data/processed_facilities.csv")
    target_facilities = [facility_id] if facility_id else df["facility_id"].tolist()

    results = []
    for f_id in target_facilities:
        assets_count, logs_created = seed_mock_maintenance_data(db, facility_id=f_id)
        results.append({"facility_id": f_id, "assets_seeded": assets_count, "logs_seeded": logs_created})

    return success_response(
        message="Maintenance data pipeline executed.",
        data={"results": results},
    )
