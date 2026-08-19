from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class OccupancyZoneBase(BaseModel):
    facility_id: str
    floor: int
    zone_name: str
    zone_type: str
    max_capacity: int
    area_sqft: Optional[float] = None
    x_position: Optional[float] = None
    y_position: Optional[float] = None

class OccupancyZoneResponse(OccupancyZoneBase):
    zone_id: str
    class Config:
        from_attributes = True

class OccupancyRecordBase(BaseModel):
    facility_id: str
    zone_id: str
    occupancy_count: int
    source: str = "sensor"
    timestamp: datetime

class OccupancyRecordResponse(OccupancyRecordBase):
    occupancy_id: str
    class Config:
        from_attributes = True

class OccupancyImageBase(BaseModel):
    facility_id: str
    zone_id: str
    camera_id: Optional[str] = None
    image_path: Optional[str] = None
    captured_at: datetime
    detected_count: Optional[int] = None
    confidence_score: Optional[float] = None
    model_version: Optional[str] = None
    processed_at: Optional[datetime] = None

class OccupancyImageResponse(OccupancyImageBase):
    image_id: str
    class Config:
        from_attributes = True

class OccupancyForecastBase(BaseModel):
    facility_id: str
    zone_id: str
    forecast_date: datetime
    predicted_occupancy: int
    predicted_utilization_pct: Optional[float] = None
    model_version: Optional[str] = None

class OccupancyForecastResponse(OccupancyForecastBase):
    forecast_id: str
    class Config:
        from_attributes = True

class SecurityEventBase(BaseModel):
    facility_id: str
    event_type: str
    severity: str
    event_time: datetime
    status: str = "Open"
    zone_level: Optional[int] = None
    recent_failed_attempts: Optional[int] = None

class SecurityEventResponse(SecurityEventBase):
    event_id: str
    class Config:
        from_attributes = True