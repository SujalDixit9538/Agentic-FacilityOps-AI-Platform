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
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Import all underlying domain agents
from backend.agents.energy.agent import EnergyAgent
from backend.agents.maintenance.agent import MaintenanceAgent
from backend.agents.occupancy.agent import OccupancyAgent
from backend.agents.cost.agent import CostAgent
from backend.database.models.maintenance import Asset
from backend.services.facility_state_service import FacilityStateService
from backend.core.config import settings

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
        self.facility_state_service = FacilityStateService(db)

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

    def _run_agent(self, name, operation, timeout_seconds=10):
        started = time.perf_counter()
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(operation)
        try:
            report = future.result(timeout=timeout_seconds)
            return report, {
                "status": "success" if not isinstance(report, dict) or report.get("status") != "error" else "failed",
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                "failure": report.get("message") if isinstance(report, dict) and report.get("status") == "error" else None,
            }
        except TimeoutError:
            future.cancel()
            return {"alerts": [], "recommendations": [], "analysis": {}, "status": "error"}, {
                "status": "timeout",
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                "failure": f"{name}_timeout",
            }
        except Exception as exc:
            logger.exception("Executive %s agent failed", name)
            return {"alerts": [], "recommendations": [], "analysis": {}, "status": "error"}, {
                "status": "failed",
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                "failure": str(exc),
            }
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    def generate_executive_summary(self, facility_id: str):
        logger.info(f"ExecutiveAgent compiling unified summary for {facility_id}")
        
        # 1. Poll Domain Agents
        energy_report, energy_status = self._run_agent("energy", lambda: self.energy_agent.analyze_facility(facility_id))
        occupancy_report, occupancy_status = self._run_agent("occupancy_security", lambda: self.occupancy_agent.analyze_facility(facility_id))
        cost_report, cost_status = self._run_agent("cost", lambda: self.cost_agent.analyze_facility_finances(facility_id))
        facility_state, state_status = self._run_agent("facility_state", lambda: self.facility_state_service.get_facility_state(facility_id))

        maintenance_reports, maintenance_status = self._run_agent(
            "maintenance", lambda: self.maintenance_agent.analyze_facility(facility_id, limit=25)
        )
        if not isinstance(maintenance_reports, list):
            maintenance_reports = []

        agent_status = {
            "energy": energy_status,
            "occupancy_security": occupancy_status,
            "cost": cost_status,
            "facility_state": state_status,
            "maintenance": {**maintenance_status, "assets_analyzed": len(maintenance_reports)},
        }

        # 2. Aggregate Alerts and Recommendations
        all_alerts = []
        all_recommendations = []
        
        for report in [energy_report, occupancy_report, cost_report, *maintenance_reports]:
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
                "cost": cost_report.get("analysis", {}).get("metrics", {}),
                "facility_state": facility_state,
                "maintenance": maintenance_reports,
            }
        }

        insights = self._generate_fallback_insights(platform_status, len(all_alerts))
        llm_status = {
            "status": "unavailable",
            "source": "rules",
            "degraded": True,
            "reason": "groq_client_unavailable",
        }

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
                llm_started = time.perf_counter()
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
                llm_status = {"status": "success", "source": "Groq", "degraded": False, "latency_ms": round((time.perf_counter() - llm_started) * 1000, 2)}
                
                logger.info(f"✅ Success! Groq generated insights using {self.model_name}.")
                
            except Exception as e:
                logger.error(f"❌ Groq generation failed: {e}. Falling back to programmatic rules.")
                llm_status["reason"] = "groq_request_failed"

        state_values = [
            value for value in (
                facility_state.get("asset_health"),
                facility_state.get("occupancy_pct"),
            ) if value is not None
        ]
        energy_metrics = energy_report.get("analysis", {}).get("metrics", {})
        efficiency_score = energy_metrics.get("efficiency_score")
        if efficiency_score is not None:
            state_values.append(float(efficiency_score))
        required_score_values = [facility_state.get("asset_health"), facility_state.get("occupancy_pct"), efficiency_score]
        score_degraded = any(value is None for value in required_score_values)
        health_score = round(min(100, max(0, sum(state_values) / len(state_values))), 1) if state_values and not score_degraded else None
        total_kwh = energy_metrics.get("total_kwh")
        carbon_kg_co2e = round(total_kwh * settings.CARBON_EMISSION_FACTOR_KG_PER_KWH, 2) if total_kwh is not None else None

        # 5. Compile Unified Payload
        return {
            "facility_id": facility_id,
            "executive_status": platform_status,
            "total_active_alerts": len(all_alerts),
            "critical_alerts": len(critical_alerts),
            "executive_insights": insights,
            "llm_status": llm_status,
            "facility_health_score": health_score,
            "health_score_formula": {
                "version": "v1",
                "definition": "Arithmetic mean of asset_health, occupancy_pct, and energy efficiency_score; unknown when any required value is unavailable.",
                "degraded": score_degraded,
            },
            "agent_status": agent_status,
            "provenance": {"source": "ExecutiveAgent", "facility_id": facility_id, "llm": "Groq" if self.client else "unavailable"},
            "freshness": {"status": "degraded" if score_degraded else "available"},
            "degraded": score_degraded or any(item.get("status") != "success" for item in agent_status.values() if isinstance(item, dict) and "status" in item),
            "quality_flags": (["health_score_inputs_unavailable"] if score_degraded else []),
            "facility_state": facility_state,
            "domain_reports": {
                "energy_efficiency": efficiency_score,
                "security_threat_level": occupancy_report.get("analysis", {}).get("threat_level", "Unknown"),
                "financial_status": cost_report.get("analysis", {}).get("financial_status", "Unknown"),
                "maintenance_assets_analyzed": len(maintenance_reports),
                "resource_utilization_pct": facility_state.get("occupancy_pct"),
                "sustainability": {
                    "energy_kwh": total_kwh,
                    "carbon_kg_co2e": carbon_kg_co2e,
                    "emissions_factor_kg_per_kwh": settings.CARBON_EMISSION_FACTOR_KG_PER_KWH,
                    "status": "Estimated from configured grid factor" if carbon_kg_co2e is not None else "Unavailable",
                },
            },
            "consolidated_alerts": sorted(all_alerts, key=lambda x: x.get("severity") != "High"),
            "consolidated_recommendations": all_recommendations
        }