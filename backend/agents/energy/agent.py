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


import logging
import json
import os
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

logger = logging.getLogger(__name__)

class EnergyAgent:
    def __init__(self, db: Session):
        self.db = db
        self.api_key = os.getenv("GROQ_API_KEY")
        self.client = None
        self.model_name = "llama-3.3-70b-versatile"
        
        if HAS_GROQ and self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Groq Init Failed: {e}")

    def analyze_facility(self, facility_id: str, days: int = 7):
        # 1. Fetch your rule-based data (keep your existing logic here that checks DB)
        # For example, let's assume your existing rules generate this basic dictionary:
        base_alerts = [{"type": "High HVAC Load", "severity": "High", "message": "Consumption spiked 15%"}]
        base_metrics = {"total_kwh": 4500, "peak_kw": 210}

        # 2. Dynamic LLM Recommendations (THE FIX)
        dynamic_recommendations = []
        
        if self.client and base_alerts:
            system_prompt = (
                "You are an AI Energy Agent for a commercial facility. "
                "Analyze the provided alerts and metrics. "
                "Generate exactly TWO highly specific, actionable engineering recommendations to reduce energy consumption. "
                "Output ONLY valid JSON in this format: {\"recommendations\": [{\"action\": \"...\", \"priority\": \"High\"}]}"
            )
            
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": json.dumps({"alerts": base_alerts, "metrics": base_metrics})}
                    ],
                    model=self.model_name,
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
                llm_data = json.loads(chat_completion.choices[0].message.content)
                dynamic_recommendations = llm_data.get("recommendations", [])
            except Exception as e:
                logger.error(f"Energy LLM failed: {e}")
                # Fallback to rules if API fails
                dynamic_recommendations = [{"action": "Manually inspect HVAC schedule.", "priority": "Medium"}]

        # 3. Return payload to the Streamlit UI
        return {
            "facility_id": facility_id,
            "alerts": base_alerts,
            "recommendations": dynamic_recommendations,
            "analysis": {"metrics": base_metrics}
        }