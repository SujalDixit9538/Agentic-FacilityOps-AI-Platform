from sqlalchemy import Column, Integer, String, Float, DateTime
from backend.database.base import Base
import datetime

class EnergyRecord(Base):
    """
    SQLAlchemy model for energy usage data.
    Aligns with the operational database schema defined in the project brief.
    """
    __tablename__ = "energy_usage"

    record_id = Column(String, primary_key=True, index=True)
    facility_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    energy_kwh = Column(Float, nullable=False)
    peak_demand_kw = Column(Float, nullable=True)
    cost = Column(Float, nullable=True)