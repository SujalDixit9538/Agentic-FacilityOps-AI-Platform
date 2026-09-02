from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Index
from backend.database.base import Base
from backend.database.models.facility import Facility
import datetime

class CostRecord(Base):
    """SQLAlchemy model for tracking facility expenses and operational costs."""
    __tablename__ = "cost_records"

    record_id = Column(String, primary_key=True, index=True)
    facility_id = Column(String, ForeignKey("facilities.facility_id"), index=True, nullable=False)
    category = Column(String, nullable=False) # e.g., Energy, Maintenance, Operations
    description = Column(String, nullable=True)
    amount = Column(Float, nullable=False)
    incurred_date = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index("ix_cost_records_facility_incurred_date", "facility_id", "incurred_date"),
    )


class CostAnalysisReport(Base):
    """Auditable result of a cost-agent run."""
    __tablename__ = "cost_analysis_reports"

    report_id = Column(String, primary_key=True, index=True)
    facility_id = Column(String, ForeignKey("facilities.facility_id"), index=True, nullable=False)
    generated_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    intelligence_source = Column(String, nullable=False)
    financial_status = Column(String, nullable=False)
    payload = Column(Text, nullable=False)


class CostRecommendation(Base):
    """Lifecycle record for a proposed cost-saving action."""
    __tablename__ = "cost_recommendations"

    recommendation_id = Column(String, primary_key=True, index=True)
    report_id = Column(String, index=True, nullable=False)
    facility_id = Column(String, index=True, nullable=False)
    action = Column(String, nullable=False)
    trigger = Column(String, nullable=True)
    priority = Column(String, nullable=False)
    estimated_savings_usd = Column(Float, nullable=True)
    status = Column(String, default="Proposed", nullable=False)
    realized_savings_usd = Column(Float, nullable=True)
    outcome_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)