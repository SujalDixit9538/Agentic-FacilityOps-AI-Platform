from sqlalchemy import Column, Integer, String, Float, DateTime
from backend.database.base import Base
import datetime

class CostRecord(Base):
    """SQLAlchemy model for tracking facility expenses and operational costs."""
    __tablename__ = "cost_records"

    record_id = Column(String, primary_key=True, index=True)
    facility_id = Column(String, index=True)
    category = Column(String, nullable=False) # e.g., Energy, Maintenance, Operations
    description = Column(String, nullable=True)
    amount = Column(Float, nullable=False)
    incurred_date = Column(DateTime, default=datetime.datetime.utcnow)