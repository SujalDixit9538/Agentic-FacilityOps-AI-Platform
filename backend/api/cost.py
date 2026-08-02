from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from backend.api.dependencies import get_db
from backend.services.cost_service import CostService
from backend.schemas.cost import CostRecordResponse
from backend.utils.api_responses import success_response
from backend.services.mock_cost_service import seed_mock_cost_data


router = APIRouter()

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

@router.get("/analyze/{facility_id}")
async def analyze_facility_costs(facility_id: str, db: Session = Depends(get_db)):
    """Runs the Cost Optimization Agent analysis on the specified facility's ledger."""
    service = CostService(db)
    insights = service.run_agent_analysis(facility_id)
    
    return success_response(
        message=f"Financial analysis completed for {facility_id}",
        data=insights
    )