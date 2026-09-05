from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, Optional

class OccupancyZoneBase(BaseModel):
    facility_id: str = Field(min_length=1, max_length=64)
    floor: int = Field(ge=1, le=10_000)
    zone_name: str = Field(min_length=1, max_length=128)
    zone_type: str = Field(min_length=1, max_length=64)
    max_capacity: int = Field(ge=1, le=10_000_000)
    area_sqft: Optional[float] = Field(default=None, ge=0, le=100_000_000)
    x_position: Optional[float] = Field(default=None, ge=0, le=1)
    y_position: Optional[float] = Field(default=None, ge=0, le=1)

class OccupancyZoneResponse(OccupancyZoneBase):
    zone_id: str
    class Config:
        from_attributes = True

class OccupancyRecordBase(BaseModel):
    facility_id: str = Field(min_length=1, max_length=64)
    zone_id: str = Field(min_length=1, max_length=128)
    occupancy_count: int = Field(ge=0, le=10_000_000)
    source: str = Field(default="sensor", min_length=1, max_length=64)
    timestamp: datetime

class OccupancyRecordResponse(OccupancyRecordBase):
    occupancy_id: str
    class Config:
        from_attributes = True

class OccupancyImageBase(BaseModel):
    facility_id: str = Field(min_length=1, max_length=64)
    zone_id: str = Field(min_length=1, max_length=128)
    camera_id: Optional[str] = Field(default=None, max_length=128)
    image_path: Optional[str] = Field(default=None, max_length=500)
    captured_at: datetime
    detected_count: Optional[int] = Field(default=None, ge=0, le=10_000_000)
    confidence_score: Optional[float] = Field(default=None, ge=0, le=1)
    model_version: Optional[str] = Field(default=None, max_length=128)
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
    facility_id: str = Field(min_length=1, max_length=64)
    event_type: str = Field(min_length=1, max_length=128)
    severity: Literal["Low", "Medium", "High", "Critical"]
    event_time: datetime
    status: Literal["Open", "Investigating", "Closed"] = "Open"
    zone_level: Optional[int] = Field(default=None, ge=0, le=10)
    recent_failed_attempts: Optional[int] = Field(default=None, ge=0, le=1_000_000)

class SecurityEventResponse(SecurityEventBase):
    event_id: str
    class Config:
        from_attributes = True