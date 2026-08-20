from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class DashboardSummary(BaseModel):
    total_occupants: int
    total_capacity: int
    utilization_percent: float
    overcrowded_zones: int
    highly_utilized_zones: int
    underutilized_zones: int

class ZoneDashboardInfo(BaseModel):
    zone_id: str
    zone_name: str
    zone_type: str
    floor: int
    occupancy: int
    capacity: int
    utilization_percent: float
    status: str
    x_position: Optional[float]
    y_position: Optional[float]

class AlertInfo(BaseModel):
    alert_type: str
    severity: str
    zone_id: str
    zone_name: str
    message: str
    utilization_percent: float

class TrendInfo(BaseModel):
    timestamp: datetime
    occupancy: int
    utilization_percent: float

class OccupancyDashboardResponse(BaseModel):
    facility_id: str
    summary: DashboardSummary
    zones: List[ZoneDashboardInfo]
    room_utilization: List[ZoneDashboardInfo]
    zone_analytics: List[dict]
    alerts: List[AlertInfo]
    trend: List[TrendInfo]

class OccupancyDashboardEnvelope(BaseModel):
    success: bool
    message: str
    data: OccupancyDashboardResponse
