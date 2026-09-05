from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import func
import time
from backend.database.models.energy import EnergyRecord

from backend.api.dependencies import get_db
from backend.services.energy_service import EnergyService
from backend.services.mock_iot_service import seed_mock_energy_data
from backend.schemas.energy import EnergyRecordResponse
from backend.utils.api_responses import success_response
from backend.services.facility_catalog_service import FacilityCatalogService
from backend.services.cache_service import get_cache, set_cache, scoped_cache_key

router = APIRouter()

@router.get("/facilities")
async def get_energy_facilities(db: Session = Depends(get_db)):
    facilities = FacilityCatalogService(db).list_active()
    return success_response(message="Retrieved canonical facilities", data={"facilities": [f.facility_id for f in facilities]})

@router.get("/health")
async def energy_module_health(db: Session = Depends(get_db)):
    """Verifies the Energy module is online and services are accessible."""
    service = EnergyService(db)
    status = service.get_module_status()
    return success_response(message="Energy module health check", data=status)

@router.post("/seed")
async def seed_energy_data(facility_id: str = Query(..., min_length=1, max_length=64), days: int = Query(7, ge=1, le=31), db: Session = Depends(get_db)):
    """Triggers the mock IoT ingestion pipeline for a given facility."""
    count = seed_mock_energy_data(db, facility_id=facility_id, days=days)
    return success_response(
        message=f"Mock data pipeline executed successfully.",
        data={"facility_id": facility_id, "records_seeded": count}
    )

@router.get("/records/{facility_id}", response_model=dict)
async def get_energy_records(facility_id: str, limit: int = Query(200, ge=1, le=1000), db: Session = Depends(get_db)):
    """Retrieves basic energy consumption records for a facility."""
    service = EnergyService(db)
    records = service.get_facility_energy_history(facility_id, limit)
    
    # Convert SQLAlchemy models to dictionaries for the standard response wrapper
    data = [EnergyRecordResponse.model_validate(r).model_dump() for r in records]
    
    return success_response(
        message=f"Retrieved {len(data)} records for {facility_id}",
        data={"records": data}
    )

@router.get("/dashboard/{facility_id}")
async def get_energy_dashboard(facility_id: str, db: Session = Depends(get_db)):
    cache_key = scoped_cache_key("energy-dashboard", facility_id, window="all")
    cached = get_cache(cache_key)
    if cached is not None:
        return cached
    query_started = time.perf_counter()
    row = db.query(
        func.coalesce(func.sum(EnergyRecord.energy_kwh), 0),
        func.max(EnergyRecord.peak_demand_kw),
        func.count(EnergyRecord.record_id),
        func.max(EnergyRecord.timestamp),
    ).filter(EnergyRecord.facility_id == facility_id).one()
    total_kwh, peak_kw, record_count, as_of = row
    response = success_response(
        message=f"Energy dashboard summary generated for {facility_id}",
          data={"facility_id": facility_id, "total_kwh": float(total_kwh or 0), "peak_kw": peak_kw,
              "records_evaluated": record_count, "as_of": as_of,
              "timing_ms": {"query": round((time.perf_counter() - query_started) * 1000, 2)}},
        provenance={"source": "energy_aggregate_query", "facility_id": facility_id},
        freshness={"status": "available" if record_count else "empty", "as_of": as_of},
        degraded=not bool(record_count),
        quality_flags=[] if record_count else ["energy_telemetry_unavailable"],
    )
    set_cache(cache_key, response, ttl_seconds=30)
    return response

@router.get("/analyze/{facility_id}")
async def analyze_energy(facility_id: str, days: int = Query(7, ge=1, le=31), db: Session = Depends(get_db)):
    """Runs the Energy Agent analysis on the specified facility."""
    service = EnergyService(db)
    insights = service.run_agent_analysis(facility_id, days)
    return success_response(
        message=f"Energy analysis completed for {facility_id}",
        data=insights
    )