import logging
from sqlalchemy.orm import Session
from backend.repositories.cost_repository import CostRepository
from backend.agents.cost.analyzer import CostAnalyzer
from backend.services.alert_service import generate_alert

logger = logging.getLogger(__name__)

class CostAgent:
    """
    Controller for Cost Optimization Intelligence.
    Orchestrates financial data retrieval, historical variance analysis, 
    and platform alert generation for budget overruns.
    """
    def __init__(self, db: Session):
        self.db = db
        self.repository = CostRepository(db)
        self.analyzer = CostAnalyzer()

    def analyze_facility_finances(self, facility_id: str):
        logger.info(f"CostAgent initiating financial analysis for {facility_id}")
        
        # 1. Fetch historical cost records (pull a larger limit to ensure we capture months of data)
        cost_records = self.repository.get_costs_by_facility(facility_id, limit=500)
        cost_dict = [
            {
                "category": r.category,
                "amount": r.amount,
                "description": r.description,
                "incurred_date": r.incurred_date.isoformat()
            } for r in cost_records
        ]

        # 2. Run time-series and capital expenditure analysis
        analysis_result = self.analyzer.analyze_financial_health(cost_dict)

        # 3. Process anomalies into standard alerts
        alerts_generated = []
        for anomaly in analysis_result.get("anomalies", []):
            alert = generate_alert(
                source_agent="CostAgent",
                alert_type=anomaly["type"],
                severity=anomaly["severity"],
                message=anomaly["message"]
            )
            alerts_generated.append(alert)

        logger.info(f"CostAgent completed analysis. Generated {len(alerts_generated)} alerts.")

        return {
            "facility_id": facility_id,
            "analysis": analysis_result,
            "alerts": alerts_generated
        }