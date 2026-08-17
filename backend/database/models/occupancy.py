from sqlalchemy import Column, Integer, String, Float, DateTime
from backend.database.base import Base
import datetime

class OccupancyZone(Base):
    """Master data for a room/zone within a facility. Replaces the hardcoded
    ZONE_CAPACITIES config dict — capacities are now per-facility, dynamically
    seeded from data/processed_facilities.csv."""
    __tablename__ = "occupancy_zones"

    zone_id = Column(String, primary_key=True, index=True)
    facility_id = Column(String, index=True, nullable=False)
    floor = Column(Integer, nullable=False)
    zone_name = Column(String, nullable=False)
    zone_type = Column(String, nullable=False)  # office_floor, meeting_room, common_area, parking, server_room
    max_capacity = Column(Integer, nullable=False)
    area_sqft = Column(Float, nullable=True)


class OccupancyRecord(Base):
    """Time-series headcount for a zone. Replaces the old free-text
    floor/room columns with a zone_id FK into occupancy_zones."""
    __tablename__ = "occupancy_records"

    occupancy_id = Column(String, primary_key=True, index=True)
    facility_id = Column(String, index=True, nullable=False)
    zone_id = Column(String, index=True, nullable=False)
    occupancy_count = Column(Integer, default=0)
    source = Column(String, default="sensor")  # sensor, cnn, manual
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class OccupancyImage(Base):
    """CNN pipeline log. Schema-ready ahead of the real camera feed
    integration — image_path is a file reference, never a DB blob."""
    __tablename__ = "occupancy_images"

    image_id = Column(String, primary_key=True, index=True)
    facility_id = Column(String, index=True, nullable=False)
    zone_id = Column(String, index=True, nullable=False)
    camera_id = Column(String, nullable=True)
    image_path = Column(String, nullable=True)
    captured_at = Column(DateTime, default=datetime.datetime.utcnow)
    detected_count = Column(Integer, nullable=True)
    confidence_score = Column(Float, nullable=True)
    model_version = Column(String, nullable=True)
    processed_at = Column(DateTime, nullable=True)


class OccupancyForecast(Base):
    """Predicted future utilization per zone."""
    __tablename__ = "occupancy_forecasts"

    forecast_id = Column(String, primary_key=True, index=True)
    facility_id = Column(String, index=True, nullable=False)
    zone_id = Column(String, index=True, nullable=False)
    forecast_date = Column(DateTime, nullable=False)
    predicted_occupancy = Column(Integer, nullable=False)
    predicted_utilization_pct = Column(Float, nullable=True)
    model_version = Column(String, nullable=True)


class SecurityEvent(Base):
    """SQLAlchemy model for logging security incidents. (unchanged)"""
    __tablename__ = "security_events"

    event_id = Column(String, primary_key=True, index=True)
    facility_id = Column(String, index=True)
    event_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    event_time = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="Open")