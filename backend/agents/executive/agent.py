import logging
from sqlalchemy.orm import Session

# Import all underlying domain agents
from backend.agents.energy.agent import EnergyAgent
from backend.agents.maintenance.agent import MaintenanceAgent
from backend.agents.occupancy.agent import OccupancyAgent
from backend.agents.cost.agent import CostAgent

logger = logging.getLogger(__name__)

class ExecutiveAgent:
    """
    Platform-level Orchestrator.
    Polls all domain agents (Energy, Maintenance, Occupancy, Cost),
    aggregates their findings, and synthesizes a unified facility health report.
    """
    def __init__(self, db: Session):
        self.db = db
        # Instantiate domain agents
        self.energy_agent = EnergyAgent(db)
        self.maintenance_agent = MaintenanceAgent(db)
        self.occupancy_agent = OccupancyAgent(db)
        self.cost_agent = CostAgent(db)

    def generate_executive_summary(self, facility_id: str):
        logger.info(f"ExecutiveAgent compiling unified summary for {facility_id}")
        
        # 1. Poll Domain Agents
        energy_report = self.energy_agent.analyze_facility(facility_id)
        
        # Note: Maintenance is asset-specific, but for the executive summary, 
        # we will just check the platform's central alert cache for maintenance issues
        # (This avoids heavy looping over every single asset in the building)
        
        occupancy_report = self.occupancy_agent.analyze_facility(facility_id)
        cost_report = self.cost_agent.analyze_facility_finances(facility_id)

        # 2. Aggregate Alerts and Recommendations
        all_alerts = []
        all_recommendations = []
        
        # Aggregate Energy
        all_alerts.extend(energy_report.get("alerts", []))
        all_recommendations.extend(energy_report.get("recommendations", []))
        
        # Aggregate Occupancy
        all_alerts.extend(occupancy_report.get("alerts", []))
        all_recommendations.extend(occupancy_report.get("recommendations", []))
        
        # Aggregate Cost
        all_alerts.extend(cost_report.get("alerts", []))
        all_recommendations.extend(cost_report.get("recommendations", []))

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

        # 4. Compile Unified JSON Payload
        return {
            "facility_id": facility_id,
            "executive_status": platform_status,
            "total_active_alerts": len(all_alerts),
            "critical_alerts": len(critical_alerts),
            "domain_reports": {
                "energy_efficiency": energy_report.get("analysis", {}).get("efficiency_score", "N/A"),
                "security_threat_level": occupancy_report.get("analysis", {}).get("threat_level", "Unknown"),
                "financial_status": cost_report.get("analysis", {}).get("financial_status", "Unknown")
            },
            "consolidated_alerts": sorted(all_alerts, key=lambda x: x.get("severity") != "High"), # High severity first
            "consolidated_recommendations": all_recommendations
        }