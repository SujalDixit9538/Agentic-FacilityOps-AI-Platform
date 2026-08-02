from pydantic import BaseModel
from datetime import datetime
from typing import Optional

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