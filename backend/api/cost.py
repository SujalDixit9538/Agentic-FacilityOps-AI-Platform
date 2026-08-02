from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from backend.api.dependencies import get_db
from backend.services.cost_service import CostService
from backend.schemas.cost import CostRecordResponse
from backend.utils.api_responses import success_response

router = APIRouter()

@router.get("/health")
async def cost_module_health(db: Session = Depends(get_db)):
    """Verifies the Cost Optimization module is online."""
    service = CostService(db)
    status = service.get_module_status()
    return success_response(message="Cost module health check", data=status)

@router.get("/records/{facility_id}")
async def get_cost_records(facility_id: str, limit: int = Query(100), db: Session = Depends(get_db)):
    """Retrieves financial expense records for a given facility."""
    service = CostService(db)
    records = service.get_facility_costs(facility_id, limit)
    
    data = [CostRecordResponse.model_validate(r).model_dump() for r in records]
    return success_response(message=f"Retrieved {len(data)} cost records", data={"records": data})