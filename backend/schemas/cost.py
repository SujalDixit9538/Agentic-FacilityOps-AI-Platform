from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, Optional

class CostRecordBase(BaseModel):
    facility_id: str = Field(min_length=1, max_length=64)
    category: str = Field(min_length=1, max_length=64)
    description: Optional[str] = Field(default=None, max_length=500)
    amount: float = Field(ge=0, le=100_000_000)
    incurred_date: datetime

class CostRecordResponse(CostRecordBase):
    record_id: str
    class Config:
        from_attributes = True


class CostRecommendationUpdate(BaseModel):
    status: Literal["proposed", "accepted", "completed", "dismissed"]
    realized_savings_usd: Optional[float] = Field(default=None, ge=0, le=100_000_000)
    outcome_notes: Optional[str] = Field(default=None, max_length=2000)


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