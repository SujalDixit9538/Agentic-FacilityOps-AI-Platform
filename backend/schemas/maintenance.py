from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, Optional

# Asset Schemas
class AssetBase(BaseModel):
    facility_id: str = Field(min_length=1, max_length=64)
    asset_type: str = Field(min_length=1, max_length=128)
    installation_date: datetime
    status: Literal["Operational", "Under Maintenance", "Decommissioned"] = "Operational"

class AssetResponse(AssetBase):
    asset_id: str
    class Config:
        from_attributes = True

# Maintenance Log Schemas
class MaintenanceLogBase(BaseModel):
    asset_id: str = Field(min_length=1, max_length=64)
    issue: str = Field(min_length=1, max_length=500)
    maintenance_date: datetime
    technician: Optional[str] = Field(default=None, max_length=128)
    status: Literal["Pending", "Completed"] = "Pending"
    cost: Optional[float] = Field(default=None, ge=0, le=100_000_000)
    air_temp: Optional[float] = Field(default=None, ge=-100, le=1_000)
    process_temp: Optional[float] = Field(default=None, ge=-100, le=1_000)
    speed: Optional[float] = Field(default=None, ge=0, le=100_000)
    torque: Optional[float] = Field(default=None, ge=0, le=100_000)
    wear: Optional[float] = Field(default=None, ge=0, le=100_000)

class MaintenanceLogResponse(MaintenanceLogBase):
    log_id: str
    class Config:
        from_attributes = True
