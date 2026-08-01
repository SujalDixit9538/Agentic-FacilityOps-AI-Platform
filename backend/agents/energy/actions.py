import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class EnergyActionEngine:
    """
    Maps detected energy anomalies to actionable facility recommendations.
    Enforces Blueprint Rule: Agents must provide mitigation strategies.
    """
    
    # Pre-defined deterministic mitigation strategies
    MITIGATION_STRATEGIES = {
        "Peak Demand Exceeded": [
            "Initiate immediate load shedding protocol for non-critical zones.",
            "Stagger startup times for heavy HVAC equipment to flatten the peak curve.",
            "Temporarily dim lighting in common areas by 20%."
        ],
        "Abnormal Usage Spike": [
            "Dispatch maintenance to inspect equipment for continuous running/stuck relays.",
            "Verify Building Management System (BMS) schedules for off-hours overrides.",
            "Check for unusual occupancy patterns in the affected zones."
        ]
    }

    def generate_recommendations(self, anomalies: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Generates a list of unique recommendations based on detected anomalies."""
        if not anomalies:
            return [{"action": "Maintain current operational parameters. No action required.", "priority": "Low"}]

        recommendations = []
        seen_actions = set()

        for anomaly in anomalies:
            anomaly_type = anomaly.get("type")
            strategies = self.MITIGATION_STRATEGIES.get(anomaly_type, ["Investigate anomaly source."])
            
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

        logger.info(f"ActionEngine generated {len(recommendations)} recommendations.")
        return recommendations