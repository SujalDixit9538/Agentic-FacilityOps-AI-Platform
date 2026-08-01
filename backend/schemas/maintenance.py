from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# Asset Schemas
class AssetBase(BaseModel):
    facility_id: str
    asset_type: str
    installation_date: datetime
    status: str = "Operational"

class AssetResponse(AssetBase):
    asset_id: str
    class Config:
        from_attributes = True

# Maintenance Log Schemas
class MaintenanceLogBase(BaseModel):
    asset_id: str
    issue: str
    maintenance_date: datetime
    technician: Optional[str] = None
    status: str = "Pending"
    cost: Optional[float] = None

class MaintenanceLogResponse(MaintenanceLogBase):
    log_id: str
    class Config:
        from_attributes = True