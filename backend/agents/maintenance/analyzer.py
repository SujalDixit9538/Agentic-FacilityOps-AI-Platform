import pandas as pd
import logging
from datetime import datetime
from typing import List, Dict, Any
from backend.agents.maintenance.config import MAINTENANCE_RULES

logger = logging.getLogger(__name__)

class MaintenanceAnalyzer:
    """
    Deterministic rules-engine for Predictive Maintenance.
    Evaluates asset health based on age, repair frequency, and cost metrics.
    """
    def __init__(self):
        self.lifespans = MAINTENANCE_RULES["EXPECTED_LIFESPAN_DAYS"]
        self.default_lifespan = MAINTENANCE_RULES["DEFAULT_LIFESPAN_DAYS"]
        self.critical_repair_count = MAINTENANCE_RULES["CRITICAL_REPAIR_COUNT"]
        self.repair_window = MAINTENANCE_RULES["REPAIR_WINDOW_DAYS"]
        self.high_cost_threshold = MAINTENANCE_RULES["HIGH_COST_THRESHOLD"]

    def analyze_asset_health(self, asset: Dict[str, Any], logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Runs health analysis on a single asset and its maintenance history."""
        anomalies = []
        now = datetime.utcnow()
        
        # 1. Analyze Asset Age
        install_date = pd.to_datetime(asset['installation_date']).tz_localize(None)
        age_days = (now - install_date).days
        expected_lifespan = self.lifespans.get(asset['asset_type'], self.default_lifespan)
        
        life_consumed_pct = (age_days / expected_lifespan) * 100
        
        if life_consumed_pct >= 90:
            anomalies.append({
                "type": "End of Life Warning",
                "severity": "High" if life_consumed_pct >= 100 else "Medium",
                "message": f"Asset has consumed {life_consumed_pct:.1f}% of its expected lifespan."
            })

        # 2. Analyze Maintenance History
        total_cost = 0.0
        recent_repairs = 0
        
        if logs:
            df = pd.DataFrame(logs)
            df['maintenance_date'] = pd.to_datetime(df['maintenance_date']).dt.tz_localize(None)
            total_cost = df['cost'].sum()
            
            # Check for frequent recent breakdowns
            cutoff_date = now - pd.Timedelta(days=self.repair_window)
            recent_repairs = len(df[df['maintenance_date'] >= cutoff_date])
            
            if recent_repairs >= self.critical_repair_count:
                anomalies.append({
                    "type": "High Failure Frequency",
                    "severity": "High",
                    "message": f"Asset has failed {recent_repairs} times in the last {self.repair_window} days."
                })
                
            # Check for catastrophic costly repairs
            costly_repairs = df[df['cost'] > self.high_cost_threshold]
            if not costly_repairs.empty:
                anomalies.append({
                    "type": "Costly Repair History",
                    "severity": "Medium",
                    "message": f"Asset experienced {len(costly_repairs)} repairs exceeding ${self.high_cost_threshold}."
                })

        logger.info(f"Analyzed {asset['asset_type']} ({asset['asset_id']}). Found {len(anomalies)} risk factors.")

        # Determine overall health status
        status = "Critical" if any(a["severity"] == "High" for a in anomalies) else "Degraded" if anomalies else "Healthy"

        return {
            "asset_id": asset['asset_id'],
            "health_status": status,
            "metrics": {
                "age_days": age_days,
                "life_consumed_pct": round(life_consumed_pct, 2),
                "total_repair_cost": float(total_cost),
                "recent_repairs": recent_repairs
            },
            "anomalies": anomalies
        }