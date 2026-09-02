from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from backend.database.base import Base
from backend.database.models.facility import Facility
import datetime

class EnergyRecord(Base):
    """
    SQLAlchemy model for energy usage data.
    Aligns with the operational database schema defined in the project brief.
    """
    __tablename__ = "energy_usage"

    record_id = Column(String, primary_key=True, index=True)
    facility_id = Column(String, ForeignKey("facilities.facility_id"), index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    energy_kwh = Column(Float, nullable=False)
    peak_demand_kw = Column(Float, nullable=True)
    cost = Column(Float, nullable=True)

    __table_args__ = (
        Index("ix_energy_usage_facility_timestamp", "facility_id", "timestamp"),
    )