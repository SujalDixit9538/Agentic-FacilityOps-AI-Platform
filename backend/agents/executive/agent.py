# import logging
# from sqlalchemy.orm import Session

# # Import all underlying domain agents
# from backend.agents.energy.agent import EnergyAgent
# from backend.agents.maintenance.agent import MaintenanceAgent
# from backend.agents.occupancy.agent import OccupancyAgent
# from backend.agents.cost.agent import CostAgent

# logger = logging.getLogger(__name__)

# class ExecutiveAgent:
#     """
#     Platform-level Orchestrator.
#     Polls all domain agents (Energy, Maintenance, Occupancy, Cost),
#     aggregates their findings, and synthesizes a unified facility health report.
#     """
#     def __init__(self, db: Session):
#         self.db = db
#         # Instantiate domain agents
#         self.energy_agent = EnergyAgent(db)
#         self.maintenance_agent = MaintenanceAgent(db)
#         self.occupancy_agent = OccupancyAgent(db)
#         self.cost_agent = CostAgent(db)

#     def generate_executive_summary(self, facility_id: str):
#         logger.info(f"ExecutiveAgent compiling unified summary for {facility_id}")
        
#         # 1. Poll Domain Agents
#         energy_report = self.energy_agent.analyze_facility(facility_id)
        
#         # Note: Maintenance is asset-specific, but for the executive summary, 
#         # we will just check the platform's central alert cache for maintenance issues
#         # (This avoids heavy looping over every single asset in the building)
        
#         occupancy_report = self.occupancy_agent.analyze_facility(facility_id)
#         cost_report = self.cost_agent.analyze_facility_finances(facility_id)

#         # 2. Aggregate Alerts and Recommendations
#         all_alerts = []
#         all_recommendations = []
        
#         # Aggregate Energy
#         all_alerts.extend(energy_report.get("alerts", []))
#         all_recommendations.extend(energy_report.get("recommendations", []))
        
#         # Aggregate Occupancy
#         all_alerts.extend(occupancy_report.get("alerts", []))
#         all_recommendations.extend(occupancy_report.get("recommendations", []))
        
#         # Aggregate Cost
#         all_alerts.extend(cost_report.get("alerts", []))
#         all_recommendations.extend(cost_report.get("recommendations", []))

#         # 3. Synthesize Overall Platform Threat Level
#         critical_alerts = [a for a in all_alerts if a.get("severity") == "High"]
        
#         if len(critical_alerts) >= 3:
#             platform_status = "CRITICAL EMERGENCY"
#         elif len(critical_alerts) > 0:
#             platform_status = "ELEVATED RISK"
#         elif all_alerts:
#             platform_status = "MODERATE WARNINGS"
#         else:
#             platform_status = "OPTIMAL"

#         # 4. Compile Unified JSON Payload
#         return {
#             "facility_id": facility_id,
#             "executive_status": platform_status,
#             "total_active_alerts": len(all_alerts),
#             "critical_alerts": len(critical_alerts),
#             "domain_reports": {
#                 "energy_efficiency": energy_report.get("analysis", {}).get("efficiency_score", "N/A"),
#                 "security_threat_level": occupancy_report.get("analysis", {}).get("threat_level", "Unknown"),
#                 "financial_status": cost_report.get("analysis", {}).get("financial_status", "Unknown")
#             },
#             "consolidated_alerts": sorted(all_alerts, key=lambda x: x.get("severity") != "High"), # High severity first
#             "consolidated_recommendations": all_recommendations
#         }




import logging
import json
import os
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Import all underlying domain agents
from backend.agents.energy.agent import EnergyAgent
from backend.agents.maintenance.agent import MaintenanceAgent
from backend.agents.occupancy.agent import OccupancyAgent
from backend.agents.cost.agent import CostAgent

load_dotenv()

try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

logger = logging.getLogger(__name__)

class ExecutiveAgent:
    """
    Platform-level Orchestrator with Groq (Llama 3) LLM Reasoning.
    """
    def __init__(self, db: Session):
        self.db = db
        self.energy_agent = EnergyAgent(db)
        self.maintenance_agent = MaintenanceAgent(db)
        self.occupancy_agent = OccupancyAgent(db)
        self.cost_agent = CostAgent(db)

        self.api_key = os.getenv("GROQ_API_KEY")
        self.client = None
        self.model_name = "llama-3.3-70b-versatile"
        
        if HAS_GROQ and self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
                logger.info(f"Successfully initialized Groq client using {self.model_name}.")
            except Exception as e:
                logger.error(f"Failed to initialize Groq Client: {e}")

    def _generate_fallback_insights(self, platform_status: str, total_alerts: int) -> dict:
        return {
            "executive_summary": f"Facility is operating at {platform_status} status with {total_alerts} active alerts. LLM reasoning bypassed.",
            "strategic_explanation": "Review the consolidated alerts below to address the most critical cross-domain issues."
        }

    def generate_executive_summary(self, facility_id: str):
        logger.info(f"ExecutiveAgent compiling unified summary for {facility_id}")
        
        # 1. Poll Domain Agents
        energy_report = self.energy_agent.analyze_facility(facility_id)
        occupancy_report = self.occupancy_agent.analyze_facility(facility_id)
        cost_report = self.cost_agent.analyze_facility_finances(facility_id) 

        # 2. Aggregate Alerts and Recommendations
        all_alerts = []
        all_recommendations = []
        
        for report in [energy_report, occupancy_report, cost_report]:
            all_alerts.extend(report.get("alerts", []))
            all_recommendations.extend(report.get("recommendations", []))

        # 3. Synthesize Overall Platform Threat Level
        critical_alerts = [a for a in all_alerts if a.get("severity") == "High"]
        
        if len(critical_alerts) >= 3:
            platform_status = "CRITICAL EMERGENCY"
        elif len(critical_alerts) > 0:
            platform_status = "ELEVATED RISK"
        elif all_alerts:
            platform_status = "MODERATE WARNINGS"
        else:
            platform_status = "OPTIMAL"

        # 4. LLM Reasoning Layer
        combined_state = {
            "facility_id": facility_id,
            "platform_status": platform_status,
            "active_alerts": all_alerts,
            "domain_metrics": {
                "energy": energy_report.get("analysis", {}).get("metrics", {}),
                "occupancy": occupancy_report.get("analysis", {}).get("metrics", {}),
                "cost": cost_report.get("analysis", {}).get("metrics", {})
            }
        }

        insights = self._generate_fallback_insights(platform_status, len(all_alerts))

        if self.client:
            system_prompt = (
                "You are the Executive AI Orchestrator for a Facility Management Platform. "
                "Analyze the provided JSON facility state. Correlate the data across Energy, Occupancy, and Cost domains. "
                "Respond ONLY with a valid JSON object containing exactly these two keys:\n"
                '{"executive_summary": "A 2-sentence C-level summary of the facility state.",\n'
                '"strategic_explanation": "A 3-sentence explanation of the primary issues and the best cross-domain action to take."}'
            )

            try:
                logger.info(f"Attempting LLM generation with Groq ({self.model_name})...")
                
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt,
                        },
                        {
                            "role": "user",
                            "content": f"Facility State:\n{json.dumps(combined_state)}",
                        }
                    ],
                    model=self.model_name,
                    temperature=0.2,
                    response_format={"type": "json_object"}
                )
                
                llm_data = json.loads(chat_completion.choices[0].message.content)
                insights["executive_summary"] = llm_data.get("executive_summary", insights["executive_summary"])
                insights["strategic_explanation"] = llm_data.get("strategic_explanation", insights["strategic_explanation"])
                
                logger.info(f"✅ Success! Groq generated insights using {self.model_name}.")
                
            except Exception as e:
                logger.error(f"❌ Groq generation failed: {e}. Falling back to programmatic rules.")

        # 5. Compile Unified JSON Payload
        return {
            "facility_id": facility_id,
            "executive_status": platform_status,
            "total_active_alerts": len(all_alerts),
            "critical_alerts": len(critical_alerts),
            "executive_insights": insights,
            "domain_reports": {
                "energy_efficiency": energy_report.get("analysis", {}).get("metrics", {}).get("efficiency_score", "N/A"),
                "security_threat_level": occupancy_report.get("analysis", {}).get("threat_level", "Unknown"),
                "financial_status": cost_report.get("analysis", {}).get("financial_status", "Unknown")
            },
            "consolidated_alerts": sorted(all_alerts, key=lambda x: x.get("severity") != "High"),
            "consolidated_recommendations": all_recommendations
        }