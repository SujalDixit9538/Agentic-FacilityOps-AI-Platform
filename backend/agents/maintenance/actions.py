import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class MaintenanceActionEngine:
    """
    Maps detected maintenance anomalies to actionable mitigation strategies.
    Enforces Blueprint Rule: Agents must provide mitigation strategies.
    """
    
    # Pre-defined deterministic mitigation strategies based on asset health risks
    MITIGATION_STRATEGIES = {
        "End of Life Warning": [
            "Initiate procurement process for a replacement unit to avoid unplanned downtime.",
            "Increase preventative maintenance frequency by 50% until replacement is installed.",
            "Verify warranty status and check for trade-in rebates."
        ],
        "High Failure Frequency": [
            "Conduct a Level 3 Root Cause Analysis (RCA) on the frequent failure points.",
            "Halt standard repairs and dispatch a senior technician for a comprehensive audit.",
            "Review operating environment for external stressors (e.g., excessive vibration, heat)."
        ],
        "Costly Repair History": [
            "Run a Repair vs. Replace ROI analysis; cumulative repair costs are approaching replacement value.",
            "Audit previous technician invoices for price gouging or inefficient labor hours.",
            "Check if aftermarket or refurbished parts can be used for future non-critical repairs."
        ]
    }

    def generate_recommendations(self, anomalies: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Generates a list of unique recommendations based on detected risk factors."""
        if not anomalies:
            return [{"action": "Continue standard preventative maintenance schedule.", "priority": "Low"}]

        recommendations = []
        seen_actions = set()

        for anomaly in anomalies:
            anomaly_type = anomaly.get("type")
            strategies = self.MITIGATION_STRATEGIES.get(anomaly_type, ["Investigate equipment status immediately."])
            
            # Map severity to priority
            priority = "High" if anomaly.get("severity") == "High" else "Medium"

            for strategy in strategies:
                if strategy not in seen_actions:
                    recommendations.append({
                        "action": strategy,
                        "priority": priority,
                        "trigger": anomaly_type
                    })
                    seen_actions.add(strategy)

        logger.info(f"MaintenanceActionEngine generated {len(recommendations)} recommendations.")
        return recommendations