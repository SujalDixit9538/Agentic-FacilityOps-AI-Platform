from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.api.dependencies import get_db
from backend.services.cost_service import CostService
from backend.schemas.cost import CostRecordBase, CostRecordResponse, CostRecommendationUpdate, CostRecommendationResponse
from backend.utils.api_responses import success_response
from backend.services.mock_cost_service import seed_mock_cost_data
from backend.database.models.cost import CostRecord
from sqlalchemy import func
import time
from backend.services.cache_service import get_cache, set_cache, scoped_cache_key
from backend.services.facility_catalog_service import FacilityCatalogService


router = APIRouter()

@router.get("/facilities")
async def get_cost_facilities(db: Session = Depends(get_db)):
    facilities = FacilityCatalogService(db).list_active()
    return success_response(message="Retrieved canonical facilities", data={"facilities": [f.facility_id for f in facilities]})

@router.post("/records", response_model=None)
async def create_cost_record(data: CostRecordBase, db: Session = Depends(get_db)):
    """Ingests one validated expense into the facility ledger."""
    record = CostService(db).log_facility_cost(data)
    return success_response(message="Cost record created", data=CostRecordResponse.model_validate(record).model_dump())

@router.get("/health")
async def cost_module_health(db: Session = Depends(get_db)):
    """Verifies the Cost Optimization module is online."""
    service = CostService(db)
    status = service.get_module_status()
    return success_response(message="Cost module health check", data=status)

@router.post("/seed")
async def seed_cost_data(facility_id: str = Query("FAC-001"), months: int = Query(6), db: Session = Depends(get_db)):
    """Triggers the mock financial data pipeline."""
    records_count = seed_mock_cost_data(db, facility_id=facility_id, months_back=months)
    return success_response(
        message="Cost data pipeline executed.",
        data={"facility_id": facility_id, "financial_records_seeded": records_count}
    )

@router.get("/records/{facility_id}")
async def get_cost_records(facility_id: str, limit: int = Query(100), db: Session = Depends(get_db)):
    """Retrieves financial expense records for a given facility."""
    service = CostService(db)
    records = service.get_facility_costs(facility_id, limit)
    
    data = [CostRecordResponse.model_validate(r).model_dump() for r in records]
    return success_response(message=f"Retrieved {len(data)} cost records", data={"records": data})

@router.get("/dashboard/{facility_id}")
async def get_cost_dashboard(facility_id: str, db: Session = Depends(get_db)):
    cache_key = scoped_cache_key("cost-dashboard", facility_id, window="all")
    cached = get_cache(cache_key)
    if cached is not None:
        return cached
    query_started = time.perf_counter()
    rows = db.query(
        CostRecord.category,
        func.sum(CostRecord.amount).label("total_amount"),
        func.count(CostRecord.record_id).label("record_count"),
        func.max(CostRecord.incurred_date).label("as_of"),
    ).filter(CostRecord.facility_id == facility_id).group_by(CostRecord.category).all()
    data = {"facility_id": facility_id, "categories": [
        {"category": row.category, "total_amount": float(row.total_amount), "record_count": row.record_count}
        for row in rows
        ], "as_of": max((row.as_of for row in rows), default=None),
            "timing_ms": {"query": round((time.perf_counter() - query_started) * 1000, 2)}}
    response = success_response(
        message=f"Cost dashboard summary generated for {facility_id}", data=data,
        provenance={"source": "cost_aggregate_query", "facility_id": facility_id},
        freshness={"status": "available" if rows else "empty", "as_of": data["as_of"]},
        degraded=not bool(rows), quality_flags=[] if rows else ["cost_data_unavailable"],
    )
    set_cache(cache_key, response, ttl_seconds=30)
    return response

@router.get("/analyze/{facility_id}")
async def analyze_facility_costs(facility_id: str, db: Session = Depends(get_db)):
    """Runs the Cost Optimization Agent analysis on the specified facility's ledger."""
    service = CostService(db)
    insights = service.run_agent_analysis(facility_id)
    
    return success_response(
        message=f"Financial analysis completed for {facility_id}",
        data=insights
    )

@router.get("/reports/{facility_id}")
async def get_cost_reports(facility_id: str, limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    reports = CostService(db).get_analysis_reports(facility_id, limit)
    return success_response(message=f"Retrieved {len(reports)} cost reports", data={
        "reports": [{"report_id": r.report_id, "facility_id": r.facility_id,
                     "generated_at": r.generated_at, "intelligence_source": r.intelligence_source,
                     "financial_status": r.financial_status} for r in reports]
    })

@router.patch("/recommendations/{recommendation_id}")
async def update_cost_recommendation(recommendation_id: str, data: CostRecommendationUpdate, db: Session = Depends(get_db)):
    recommendation = CostService(db).update_recommendation(
        recommendation_id, data.status, data.realized_savings_usd, data.outcome_notes
    )
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return success_response(message="Recommendation updated", data=CostRecommendationResponse.model_validate(recommendation).model_dump())