import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String

from backend.database.base import Base


class Facility(Base):
    """Canonical facility identity shared by every domain table."""

    __tablename__ = "facilities"

    facility_id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    facility_type = Column(String(64), nullable=True)
    total_area_sqft = Column(Float, nullable=True)
    total_floors = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)