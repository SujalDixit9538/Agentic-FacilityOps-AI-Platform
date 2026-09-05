from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class EnergyRecordBase(BaseModel):
    facility_id: str = Field(min_length=1, max_length=64)
    timestamp: datetime
    energy_kwh: float = Field(ge=0, le=10_000_000)
    peak_demand_kw: Optional[float] = Field(default=None, ge=0, le=10_000_000)
    cost: Optional[float] = Field(default=None, ge=0, le=100_000_000)

class EnergyRecordResponse(EnergyRecordBase):
    record_id: str

    class Config:
        from_attributes = True