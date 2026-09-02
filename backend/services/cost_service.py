from sqlalchemy.orm import Session
import hashlib
import json
from backend.repositories.cost_repository import CostRepository
from backend.schemas.cost import CostRecordBase
from backend.agents.cost.agent import CostAgent
import logging

logger = logging.getLogger(__name__)


def _stable_analysis(value):
    if isinstance(value, dict):
        return {
            key: _stable_analysis(item)
            for key, item in sorted(value.items())
            if key not in {"alert_id", "timestamp", "generated_at", "as_of"}
        }
    if isinstance(value, list):
        return [_stable_analysis(item) for item in value]
    return value

class CostService:
    """
    Business logic layer for the Cost Optimization Module.
    """
    def __init__(self, db: Session):
        self.repository = CostRepository(db)

    def get_facility_costs(self, facility_id: str, limit: int = 100):
        """Retrieves general cost records for a specific facility."""
        logger.debug(f"Fetching cost records for facility: {facility_id}")
        return self.repository.get_costs_by_facility(facility_id, limit)

    def log_facility_cost(self, cost_data: CostRecordBase):
        """Records a new facility expense."""
        logger.info(f"Logging new {cost_data.category} cost for facility: {cost_data.facility_id}")
        return self.repository.create_cost_record(cost_data)

    def run_agent_analysis(self, facility_id: str): # <-- NEW METHOD
        """Triggers the Cost Agent to analyze the facility's financial health."""
        agent = CostAgent(self.repository.db)
        analysis = agent.analyze_facility_finances(facility_id)
        fingerprint = hashlib.sha256(
            json.dumps(_stable_analysis(analysis), default=str, sort_keys=True).encode()
        ).hexdigest()
        report = self.repository.get_analysis_report_by_fingerprint(facility_id, fingerprint)
        if report is None:
            report = self.repository.create_analysis_report(facility_id, analysis, fingerprint)
        analysis["report_id"] = report.report_id
        analysis["provenance"] = {
            "source": "CostAgent",
            "facility_id": facility_id,
            "report_id": report.report_id,
            "idempotent": True,
        }
        return analysis

    def get_analysis_reports(self, facility_id: str, limit: int = 20):
        return self.repository.get_analysis_reports(facility_id, limit)

    def update_recommendation(self, recommendation_id: str, status: str, realized_savings_usd=None, outcome_notes=None):
        return self.repository.update_recommendation(
            recommendation_id, status, realized_savings_usd, outcome_notes
        )

    def get_module_status(self):
        """Returns the operational status of the Cost module."""
        return {
            "status": "operational",
            "intelligence_engine": "ml_with_explicit_degradation"
        }