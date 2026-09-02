from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from backend.database.base import Base
from backend.database.models.facility import Facility
import datetime

class OccupancyZone(Base):
    __tablename__ = "occupancy_zones"
    zone_id = Column(String, primary_key=True, index=True)
    facility_id = Column(String, ForeignKey("facilities.facility_id"), index=True, nullable=False)
    floor = Column(Integer, nullable=False)
    zone_name = Column(String, nullable=False)
    zone_type = Column(String, nullable=False)
    max_capacity = Column(Integer, nullable=False)
    area_sqft = Column(Float, nullable=True)
    x_position = Column(Float, nullable=True)
    y_position = Column(Float, nullable=True)

    __table_args__ = (
        Index("ix_occupancy_zones_facility_zone", "facility_id", "zone_id"),
    )

class OccupancyRecord(Base):
    __tablename__ = "occupancy_records"
    occupancy_id = Column(String, primary_key=True, index=True)
    facility_id = Column(String, ForeignKey("facilities.facility_id"), index=True, nullable=False)
    zone_id = Column(String, index=True, nullable=False)
    occupancy_count = Column(Integer, default=0)
    source = Column(String, default="sensor")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index("ix_occupancy_records_facility_zone_timestamp", "facility_id", "zone_id", "timestamp"),
    )

class OccupancyImage(Base):
    __tablename__ = "occupancy_images"
    image_id = Column(String, primary_key=True, index=True)
    facility_id = Column(String, ForeignKey("facilities.facility_id"), index=True, nullable=False)
    zone_id = Column(String, index=True, nullable=False)
    camera_id = Column(String, nullable=True)
    image_path = Column(String, nullable=True)
    captured_at = Column(DateTime, default=datetime.datetime.utcnow)
    detected_count = Column(Integer, nullable=True)
    confidence_score = Column(Float, nullable=True)
    model_version = Column(String, nullable=True)
    processed_at = Column(DateTime, nullable=True)

class OccupancyForecast(Base):
    __tablename__ = "occupancy_forecasts"
    forecast_id = Column(String, primary_key=True, index=True)
    facility_id = Column(String, ForeignKey("facilities.facility_id"), index=True, nullable=False)
    zone_id = Column(String, index=True, nullable=False)
    forecast_date = Column(DateTime, nullable=False)
    predicted_occupancy = Column(Integer, nullable=False)
    predicted_utilization_pct = Column(Float, nullable=True)
    model_version = Column(String, nullable=True)

class SecurityEvent(Base):
    __tablename__ = "security_events"
    event_id = Column(String, primary_key=True, index=True)
    facility_id = Column(String, ForeignKey("facilities.facility_id"), index=True, nullable=False)
    event_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    event_time = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="Open")
    zone_level = Column(Integer, nullable=True)
    recent_failed_attempts = Column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_security_events_facility_time", "facility_id", "event_time"),
    )