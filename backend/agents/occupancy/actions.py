import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class OccupancyActionEngine:
    """
    Maps detected security and occupancy anomalies to actionable mitigation protocols.
    Enforces Blueprint Rule: Agents must provide mitigation strategies.
    """
    
    # Pre-defined deterministic mitigation strategies based on threat vectors
    MITIGATION_STRATEGIES = {
        "Overcrowding Detected": [
            "Deploy overflow management protocol and open secondary assembly areas.",
            "Dispatch security personnel to manage crowd flow at major egress points.",
            "Verify HVAC ventilation is maximized for the overcrowded zone."
        ],
        "Off-Hours Presence": [
            "Dispatch night patrol to verify authorization of personnel on site.",
            "Cross-reference active badge-in records for the affected zone."
        ],
        "Active Security Breach": [ 
            "Initiate immediate localized lockdown protocol.",
            "Dispatch primary security response team to the location.",
            "Log all camera feeds and temporarily restrict badge access to standard personnel."
        ]
    }

    def generate_recommendations(self, anomalies: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Generates a list of unique recommendations based on detected risk factors."""
        if not anomalies:
            return [{"action": "Maintain standard facility patrol routes and capacity monitoring.", "priority": "Low"}]

        recommendations = []
        seen_actions = set()

        for anomaly in anomalies:
            anomaly_type = anomaly.get("type", "")
            priority = "High" if anomaly.get("severity") == "High" else "Medium"
            
            # Match the anomaly to our strategies (handling dynamic security breach names)
            strategies = ["Investigate flagged anomaly immediately."]
            if anomaly_type in self.MITIGATION_STRATEGIES:
                strategies = self.MITIGATION_STRATEGIES[anomaly_type]
            elif "Active Security Breach" in anomaly_type:
                strategies = self.MITIGATION_STRATEGIES["Active Security Breach"]

            for strategy in strategies:
                if strategy not in seen_actions:
                    recommendations.append({
                        "action": strategy,
                        "priority": priority,
                        "trigger": anomaly_type
                    })
                    seen_actions.add(strategy)

        logger.info(f"OccupancyActionEngine generated {len(recommendations)} recommendations.")
        return recommendations