import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class CostActionEngine:
    """
    Maps detected financial anomalies to actionable cost-reduction strategies.
    Enforces Blueprint Rule: Agents must provide mitigation strategies.
    """
    
    # Pre-defined deterministic mitigation strategies based on budget risks
    MITIGATION_STRATEGIES = {
        "Energy Cost Spike": [
            "Conduct an immediate energy audit on high-consumption HVAC and lighting systems.",
            "Review utility provider peak-hour pricing and shift heavy operations to off-peak hours.",
            "Inspect building envelope for insulation leaks causing heating/cooling loss."
        ],
        "Capital Expenditure Warning": [
            "Initiate an ROI analysis to determine if future repairs justify full asset replacement.",
            "Solicit competing bids from alternative contractors to ensure fair market pricing.",
            "Review warranty documentation to see if recent repairs qualify for reimbursement."
        ]
    }

    def generate_recommendations(self, anomalies: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Generates a list of unique recommendations based on detected financial anomalies."""
        if not anomalies:
            return [{"action": "Continue current facility operations; spending is within expected baselines.", "priority": "Low"}]

        recommendations = []
        seen_actions = set()

        for anomaly in anomalies:
            anomaly_type = anomaly.get("type", "")
            # Map severity directly to action priority
            priority = "High" if anomaly.get("severity") == "High" else "Medium"
            
            # Retrieve specific strategies or use a fallback
            strategies = self.MITIGATION_STRATEGIES.get(
                anomaly_type, 
                ["Review flagged expense report with the facility management team."]
            )

            for strategy in strategies:
                if strategy not in seen_actions:
                    recommendations.append({
                        "action": strategy,
                        "priority": priority,
                        "trigger": anomaly_type
                    })
                    seen_actions.add(strategy)

        logger.info(f"CostActionEngine generated {len(recommendations)} recommendations.")
        return recommendations