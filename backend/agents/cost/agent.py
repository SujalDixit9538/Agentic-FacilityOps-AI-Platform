import logging
from sqlalchemy.orm import Session
from backend.repositories.cost_repository import CostRepository
from backend.agents.cost.analyzer import CostAnalyzer
from backend.agents.cost.actions import CostActionEngine
from backend.services.alert_service import generate_alert
from backend.services.facility_state_service import FacilityStateService

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
        self.action_engine = CostActionEngine()
        self.facility_state_service = FacilityStateService(db)

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

        facility_state = self.facility_state_service.get_facility_state(facility_id)

        # 2. Run time-series and capital expenditure analysis
        analysis_result = self.analyzer.analyze_financial_health(cost_dict, facility_state)

        # 3. Process anomalies into standard alerts
        alerts_generated = []
        recommendations = []
        
        anomalies = analysis_result.get("anomalies", [])
        
        if anomalies:
            # --- Generate Mitigations ---
            recommendations = self.action_engine.generate_recommendations(anomalies)
            
            # --- Generate Alerts ---
            for anomaly in anomalies:
                alert = generate_alert(
                    source_agent="CostAgent",
                    alert_type=anomaly["type"],
                    severity=anomaly["severity"],
                    message=anomaly["message"]
                )
                alerts_generated.append(alert)

        if analysis_result.get("metrics", {}).get("prescriptive_action"):
            recommendations.extend(
                self.action_engine.generate_ml_recommendations(
                    action=analysis_result["metrics"]["prescriptive_action"],
                    predicted_savings=analysis_result["metrics"].get("predicted_savings_usd", 0),
                )
            )

        logger.info(f"CostAgent completed analysis. Generated {len(alerts_generated)} alerts and {len(recommendations)} recommendations.")

        return {
            "facility_id": facility_id,
            "analysis": analysis_result,
            "facility_state": facility_state,
            "alerts": alerts_generated,
            "recommendations": recommendations
        }