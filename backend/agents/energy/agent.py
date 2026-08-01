import logging
from sqlalchemy.orm import Session
from backend.repositories.energy_repository import EnergyRepository
from backend.agents.energy.analyzer import EnergyAnalyzer
from backend.services.alert_service import generate_alert

logger = logging.getLogger(__name__)

class EnergyAgent:
    """
    Controller for Energy Intelligence.
    Orchestrates data retrieval, rules-based analysis, and alert generation.
    """
    def __init__(self, db: Session):
        self.repository = EnergyRepository(db)
        self.analyzer = EnergyAnalyzer()

    def analyze_facility(self, facility_id: str, days: int = 7):
        logger.info(f"EnergyAgent initiating analysis for {facility_id}")
        
        # 1. Fetch recent data (hourly records)
        records = self.repository.get_records_by_facility(facility_id, limit=days*24)
        
        # Convert SQLAlchemy objects to dicts for the analyzer
        records_dict = [
            {
                "timestamp": r.timestamp.isoformat() if r.timestamp else None, 
                "energy_kwh": r.energy_kwh, 
                "peak_demand_kw": r.peak_demand_kw
            } 
            for r in records
        ]

        # 2. Run rules-based analysis
        analysis_result = self.analyzer.analyze_consumption(records_dict)

        # 3. Process anomalies into standardized alerts
        alerts_generated = []
        if analysis_result["status"] == "success":
            for anomaly in analysis_result.get("anomalies", []):
                alert = generate_alert(
                    source_agent="EnergyAgent",
                    alert_type=anomaly["type"],
                    severity=anomaly["severity"],
                    message=anomaly["message"]
                )
                alerts_generated.append(alert)

        logger.info(f"EnergyAgent completed analysis. Generated {len(alerts_generated)} alerts.")

        return {
            "facility_id": facility_id,
            "analysis": analysis_result,
            "alerts": alerts_generated
        }