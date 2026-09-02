import logging
from backend.agents.energy.analyzer import EnergyAnalyzer
from backend.database.models.energy import EnergyRecord
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class EnergyAgent:
    def __init__(self, db: Session):
        self.db = db
        self.analyzer = EnergyAnalyzer()

    def analyze_facility(self, facility_id: str, days: int = 7):
        records = self.db.query(EnergyRecord).filter(
            EnergyRecord.facility_id == facility_id
        ).order_by(EnergyRecord.timestamp.desc()).limit(days * 24).all()
        records_dict = [
            {
                "timestamp": record.timestamp.isoformat() if record.timestamp else None,
                "energy_kwh": record.energy_kwh,
                "peak_demand_kw": record.peak_demand_kw,
            }
            for record in records
        ]
        analysis = self.analyzer.analyze_consumption(records_dict)
        metrics = analysis.setdefault("metrics", {})
        metrics["records_evaluated"] = len(records)
        metrics["intelligence_source"] = analysis.get("intelligence_source", "Rules Only")
        if not records:
            analysis["degraded"] = True
            analysis["degradation_reason"] = "energy_telemetry_unavailable"

        return {
            "facility_id": facility_id,
            "alerts": analysis.get("anomalies", []),
            "recommendations": [],
            "analysis": analysis,
            "provenance": {"source": "EnergyAnalyzer", "facility_id": facility_id},
            "freshness": {"status": "available" if records else "unavailable"},
            "degraded": bool(analysis.get("degraded", analysis.get("status") != "success")),
            "quality_flags": ([analysis["degradation_reason"]] if analysis.get("degradation_reason") else []),
        }























        
# import logging
# from sqlalchemy.orm import Session
# from backend.repositories.energy_repository import EnergyRepository
# from backend.agents.energy.analyzer import EnergyAnalyzer
# from backend.agents.energy.actions import EnergyActionEngine  
# from backend.services.alert_service import generate_alert

# logger = logging.getLogger(__name__)

# class EnergyAgent:
#     """
#     Controller for Energy Intelligence.
#     Orchestrates data retrieval, rules-based analysis, alert generation, 
#     and actionable recommendations.
#     """
#     def __init__(self, db: Session):
#         self.repository = EnergyRepository(db)
#         self.analyzer = EnergyAnalyzer()
#         self.action_engine = EnergyActionEngine()  # INITIALIZE ACTION ENGINE

#     def analyze_facility(self, facility_id: str, days: int = 7):
#         logger.info(f"EnergyAgent initiating analysis for {facility_id}")
        
#         # 1. Fetch recent data (hourly records)
#         records = self.repository.get_records_by_facility(facility_id, limit=days*24)
        
#         # Convert SQLAlchemy objects to dicts for the analyzer
#         records_dict = [
#             {
#                 "timestamp": r.timestamp.isoformat() if r.timestamp else None, 
#                 "energy_kwh": r.energy_kwh, 
#                 "peak_demand_kw": r.peak_demand_kw
#             } 
#             for r in records
#         ]

#         # 2. Run rules-based analysis
#         analysis_result = self.analyzer.analyze_consumption(records_dict)

#         # 3. Process anomalies into standard alerts AND generate recommendations
#         alerts_generated = []
#         recommendations = []  
        
#         if analysis_result["status"] == "success":
#             anomalies = analysis_result.get("anomalies", [])
            
#             # --- Generate Mitigations ---
#             recommendations = self.action_engine.generate_recommendations(anomalies)
            
#             # --- Generate Alerts ---
#             for anomaly in anomalies:
#                 alert = generate_alert(
#                     source_agent="EnergyAgent",
#                     alert_type=anomaly["type"],
#                     severity=anomaly["severity"],
#                     message=anomaly["message"]
#                 )
#                 alerts_generated.append(alert)

#         logger.info(f"EnergyAgent completed analysis. Generated {len(alerts_generated)} alerts and {len(recommendations)} recommendations.")

#         return {
#             "facility_id": facility_id,
#             "analysis": analysis_result,
#             "alerts": alerts_generated,
#             "recommendations": recommendations  # APPEND TO RESPONSE
#         }

