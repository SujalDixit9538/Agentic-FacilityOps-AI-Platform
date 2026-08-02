from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# Occupancy Schemas
class OccupancyBase(BaseModel):
    facility_id: str
    floor: int
    room: str
    occupancy_count: int
    timestamp: datetime

class OccupancyResponse(OccupancyBase):
    occupancy_id: str
    class Config:
        from_attributes = True

# Security Event Schemas
class SecurityEventBase(BaseModel):
    facility_id: str
    event_type: str
    severity: str
    event_time: datetime
    status: str = "Open"

class SecurityEventResponse(SecurityEventBase):
    event_id: str
    class Config:
        from_attributes = True