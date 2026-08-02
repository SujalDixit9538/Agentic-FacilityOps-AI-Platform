import logging
from sqlalchemy.orm import Session
from backend.database.models.maintenance import Asset
from backend.repositories.maintenance_repository import MaintenanceRepository
from backend.agents.maintenance.actions import MaintenanceActionEngine
from backend.agents.maintenance.analyzer import MaintenanceAnalyzer
from backend.services.alert_service import generate_alert

logger = logging.getLogger(__name__)

class MaintenanceAgent:
    """
    Controller for Predictive Maintenance Intelligence.
    Orchestrates data retrieval, rules-based analysis, and alert generation.
    """
    def __init__(self, db: Session):
        self.db = db
        self.repository = MaintenanceRepository(db)
        self.analyzer = MaintenanceAnalyzer()
        self.action_engine = MaintenanceActionEngine()

    def analyze_asset(self, asset_id: str):
        logger.info(f"MaintenanceAgent initiating analysis for asset {asset_id}")
        
        # 1. Fetch the physical asset details
        asset = self.db.query(Asset).filter(Asset.asset_id == asset_id).first()
        if not asset:
            logger.error(f"Asset {asset_id} not found.")
            return {"status": "error", "message": f"Asset {asset_id} not found."}
        
        asset_dict = {
            "asset_id": asset.asset_id,
            "asset_type": asset.asset_type,
            "installation_date": asset.installation_date.isoformat(),
            "status": asset.status
        }

        # 2. Fetch the historical maintenance logs
        logs = self.repository.get_logs_by_asset(asset_id, limit=100)
        logs_dict = [
            {
                "log_id": l.log_id,
                "issue": l.issue,
                "maintenance_date": l.maintenance_date.isoformat(),
                "cost": l.cost
            } for l in logs
        ]

        # 3. Run rules-based health analysis
        analysis_result = self.analyzer.analyze_asset_health(asset_dict, logs_dict)

        # 4. Process risk factors into standardized system alerts
        alerts_generated = []
        recommendations = []

        anomalies = analysis_result.get("anomalies", [])

        if anomalies:
            # --- Generate Mitigations ---
            recommendations = self.action_engine.generate_recommendations(anomalies)

            # --- Generate Alerts ---
            for anomaly in anomalies:
                alert = generate_alert(
                    source_agent="MaintenanceAgent",
                    alert_type=anomaly["type"],
                    severity=anomaly["severity"],
                    message=f"[{asset.asset_type}] " + anomaly["message"]
                )
                alerts_generated.append(alert)


        logger.info(f"MaintenanceAgent completed analysis. Generated {len(alerts_generated)} alerts and {len(recommendations)} recommendations.")

        return {
            "asset_id": asset_id,
            "analysis": analysis_result,
            "alerts": alerts_generated,
            "recommendations": recommendations
        }