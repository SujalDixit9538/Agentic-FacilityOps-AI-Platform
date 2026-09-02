import logging
import json
import os
from datetime import date, timedelta
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from backend.database.models.maintenance import Asset, MaintenanceLog
from backend.repositories.maintenance_repository import MaintenanceRepository
from backend.agents.maintenance.actions import MaintenanceActionEngine
from backend.agents.maintenance.analyzer import MaintenanceAnalyzer
from backend.services.alert_service import generate_alert

load_dotenv()

try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

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
        self.api_key = os.getenv("GROQ_API_KEY")
        self.client = None
        self.model_name = "llama-3.3-70b-versatile"
        
        if HAS_GROQ and self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Groq Init Failed: {e}")

    def generate_work_order(self, asset_id: str):
        analysis = self.analyze_asset(asset_id)
        if "status" in analysis and analysis["status"] == "error":
            return analysis
        
        analysis_data = analysis.get("analysis", {})
        metrics = analysis_data.get("metrics", {})
        health_score = metrics.get("asset_health_score", 100)
        failure_probability = metrics.get("failure_probability", 0)
        predicted_issue = metrics.get("predicted_issue", "General maintenance review")
        anomalies = analysis_data.get("anomalies", [])
        
        urgency = "Medium"
        recommended_date = date.today() + timedelta(days=14)
        actions = []
        work_order_summary = f"Review asset {asset_id}: {predicted_issue}"
        work_order_created = False
        
        if self.client:
            system_prompt = (
                f"Today's date is {date.today().isoformat()}. "
                "You are an AI Maintenance Agent. Given an asset's health score, failure probability, "
                "predicted issue, and telemetry, decide how urgently it needs maintenance. "
                "Respond ONLY with valid JSON: {\"urgency\": \"Low\"|\"Medium\"|\"High\"|\"Critical\", "
                "\"recommended_date\": \"YYYY-MM-DD\", \"actions\": [\"...\", \"...\"], "
                "\"work_order_summary\": \"one sentence for a technician ticket\"}"
            )
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": json.dumps({"health_score": health_score, "failure_probability": failure_probability, "predicted_issue": predicted_issue, "anomalies": anomalies})}
                    ],
                    model=self.model_name,
                    temperature=0.2,
                    response_format={"type": "json_object"}
                )
                groq_resp = json.loads(chat_completion.choices[0].message.content)
                urgency = groq_resp.get("urgency", urgency)
                recommended_date = groq_resp.get("recommended_date", recommended_date)
                if isinstance(recommended_date, str):
                    try:
                        from datetime import datetime as _dt
                        recommended_date = _dt.strptime(recommended_date, "%Y-%m-%d").date()
                    except Exception:
                        recommended_date = date.today() + timedelta(days=14)
                
                # Ground recommended_date
                if recommended_date < date.today():
                    recommended_date = date.today() + timedelta(days=14)

                actions = groq_resp.get("actions", actions)
                work_order_summary = groq_resp.get("work_order_summary", work_order_summary)
            except Exception as e:
                logger.error(f"Groq generation failed: {e}")
        else:
            if failure_probability > 0.5:
                urgency = "High"
                recommended_date = date.today() + timedelta(days=3)
            elif health_score < 70:
                urgency = "Medium"
                recommended_date = date.today() + timedelta(days=14)
            else:
                urgency = "Low"
                recommended_date = date.today() + timedelta(days=60)
            actions = [a.get("message", "General Inspection") for a in anomalies]
        
        if urgency in ["High", "Critical"]:
            existing_log = self.repository.get_pending_log_by_asset(asset_id)
            if existing_log:
                work_order_created = True
            else:
                try:
                    self.repository.create_pending_work_order(asset_id, work_order_summary, recommended_date)
                    self.repository.update_asset_status(asset_id, "Maintenance Required")
                    work_order_created = True
                except Exception as e:
                    logger.error(f"Failed to create work order: {e}")
        
        return {
            "asset_id": asset_id,
            "urgency": urgency,
            "recommended_date": str(recommended_date),
            "actions": actions,
            "work_order_summary": work_order_summary,
            "work_order_created": work_order_created
        }

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
                "cost": l.cost,
                "air_temp": l.air_temp,
                "process_temp": l.process_temp,
                "speed": l.speed,
                "torque": l.torque,
                "wear": l.wear
            } for l in reversed(logs) if l.air_temp is not None
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

    def analyze_facility(self, facility_id: str, limit: int = 25):
        """Analyze a bounded fleet using one asset query and one log query."""
        assets = self.db.query(Asset).filter(Asset.facility_id == facility_id).limit(limit).all()
        asset_ids = [asset.asset_id for asset in assets]
        logs = self.db.query(MaintenanceLog).filter(MaintenanceLog.asset_id.in_(asset_ids)).order_by(MaintenanceLog.maintenance_date.desc()).all() if asset_ids else []
        logs_by_asset = {}
        for log in logs:
            logs_by_asset.setdefault(log.asset_id, []).append({
                "log_id": log.log_id,
                "issue": log.issue,
                "maintenance_date": log.maintenance_date.isoformat(),
                "cost": log.cost,
                "air_temp": log.air_temp,
                "process_temp": log.process_temp,
                "speed": log.speed,
                "torque": log.torque,
                "wear": log.wear,
            })

        reports = []
        for asset in assets:
            analysis = self.analyzer.analyze_asset_health({"asset_id": asset.asset_id}, list(reversed(logs_by_asset.get(asset.asset_id, []))))
            reports.append({"asset_id": asset.asset_id, "analysis": analysis, "alerts": [], "recommendations": []})
        return reports
