from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class CostRecordBase(BaseModel):
    facility_id: str
    category: str
    description: Optional[str] = None
    amount: float
    incurred_date: datetime

class CostRecordResponse(CostRecordBase):
    record_id: str
    class Config:
        from_attributes = True


class CostRecommendationUpdate(BaseModel):
    status: str
    realized_savings_usd: Optional[float] = None
    outcome_notes: Optional[str] = None


class CostRecommendationResponse(BaseModel):
    recommendation_id: str
    report_id: str
    facility_id: str
    action: str
    trigger: Optional[str]
    priority: str
    estimated_savings_usd: Optional[float]
    status: str
    realized_savings_usd: Optional[float]
    outcome_notes: Optional[str]

    class Config:
        from_attributes = True