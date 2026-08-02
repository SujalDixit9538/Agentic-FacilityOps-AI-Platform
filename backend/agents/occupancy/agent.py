import logging
from sqlalchemy.orm import Session
from backend.repositories.occupancy_repository import OccupancyRepository
from backend.agents.occupancy.analyzer import OccupancyAnalyzer
from backend.agents.occupancy.actions import OccupancyActionEngine
from backend.services.alert_service import generate_alert

logger = logging.getLogger(__name__)

class OccupancyAgent:
    """
    Controller for Occupancy & Security Intelligence.
    Orchestrates facility-wide data retrieval, cross-correlation analysis, 
    and platform alert generation.
    """
    def __init__(self, db: Session):
        self.db = db
        self.repository = OccupancyRepository(db)
        self.analyzer = OccupancyAnalyzer()
        self.action_engine = OccupancyActionEngine()

    def analyze_facility(self, facility_id: str):
        logger.info(f"OccupancyAgent initiating facility-wide analysis for {facility_id}")
        
        # 1. Fetch latest occupancy data (limit to recent records to capture current state)
        occ_records = self.repository.get_latest_occupancy(facility_id, limit=100)
        occ_dict = [
            {
                "room": r.room,
                "occupancy_count": r.occupancy_count,
                "timestamp": r.timestamp.isoformat()
            } for r in occ_records
        ]

        # 2. Fetch recent security events
        sec_events = self.repository.get_security_events(facility_id, limit=50)
        sec_dict = [
            {
                "event_type": e.event_type,
                "severity": e.severity,
                "status": e.status,
                "event_time": e.event_time.isoformat()
            } for e in sec_events
        ]

        # 3. Run cross-correlation analysis
        analysis_result = self.analyzer.analyze_facility_state(occ_dict, sec_dict)

        # 4. Process anomalies into standard alerts
        alerts_generated = []
        recommendations = []
        
        anomalies = analysis_result.get("anomalies", [])
        
        if anomalies:
            # --- Generate Mitigations ---
            recommendations = self.action_engine.generate_recommendations(anomalies)
            
            # --- Generate Alerts ---
            for anomaly in anomalies:
                alert = generate_alert(
                    source_agent="OccupancyAgent",
                    alert_type=anomaly["type"],
                    severity=anomaly["severity"],
                    message=anomaly["message"]
                )
                alerts_generated.append(alert)

        logger.info(f"OccupancyAgent completed analysis. Generated {len(alerts_generated)} alerts and {len(recommendations)} recommendations.")

        return {
            "facility_id": facility_id,
            "analysis": analysis_result,
            "alerts": alerts_generated,
            "recommendations": recommendations  
        }