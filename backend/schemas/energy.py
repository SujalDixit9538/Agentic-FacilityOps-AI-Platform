from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class EnergyRecordBase(BaseModel):
    facility_id: str
    timestamp: datetime
    energy_kwh: float
    peak_demand_kw: Optional[float] = None
    cost: Optional[float] = None

class EnergyRecordResponse(EnergyRecordBase):
    record_id: str

    class Config:
        from_attributes = True