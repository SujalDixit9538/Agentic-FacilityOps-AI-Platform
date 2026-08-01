from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database.base import Base
import datetime

class Asset(Base):
    """SQLAlchemy model for physical facility assets."""
    __tablename__ = "assets"

    asset_id = Column(String, primary_key=True, index=True)
    facility_id = Column(String, index=True)
    asset_type = Column(String, nullable=False)
    installation_date = Column(DateTime, nullable=False)
    status = Column(String, default="Operational") # Operational, Under Maintenance, Decommissioned
    
    # Relationship to maintenance logs
    maintenance_logs = relationship("MaintenanceLog", back_populates="asset")

class MaintenanceLog(Base):
    """SQLAlchemy model for historical maintenance records."""
    __tablename__ = "maintenance_logs"

    log_id = Column(String, primary_key=True, index=True)
    asset_id = Column(String, ForeignKey("assets.asset_id"), index=True)
    issue = Column(String, nullable=False)
    maintenance_date = Column(DateTime, nullable=False)
    technician = Column(String, nullable=True)
    status = Column(String, default="Pending") # Completed, Pending
    cost = Column(Float, nullable=True)

    asset = relationship("Asset", back_populates="maintenance_logs")