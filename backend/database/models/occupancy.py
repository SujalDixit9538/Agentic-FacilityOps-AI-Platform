from sqlalchemy import Column, Integer, String, DateTime
from backend.database.base import Base
import datetime

class OccupancyRecord(Base):
    """SQLAlchemy model for tracking room/floor utilization."""
    __tablename__ = "occupancy"

    occupancy_id = Column(String, primary_key=True, index=True)
    facility_id = Column(String, index=True)
    floor = Column(Integer, nullable=False)
    room = Column(String, nullable=False)
    occupancy_count = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class SecurityEvent(Base):
    """SQLAlchemy model for logging security incidents."""
    __tablename__ = "security_events"

    event_id = Column(String, primary_key=True, index=True)
    facility_id = Column(String, index=True)
    event_type = Column(String, nullable=False)
    severity = Column(String, nullable=False) # High, Medium, Low
    event_time = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="Open") # Open, Investigating, Closed