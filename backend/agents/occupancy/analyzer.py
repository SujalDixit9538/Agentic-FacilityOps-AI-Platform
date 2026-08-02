import logging
from datetime import datetime
import pandas as pd
from typing import List, Dict, Any
from backend.agents.occupancy.config import OCCUPANCY_RULES

logger = logging.getLogger(__name__)

class OccupancyAnalyzer:
    """
    Deterministic rules-engine for Occupancy & Security.
    Evaluates overcrowding, off-hours presence, and critical security breaches.
    """
    def __init__(self):
        self.capacities = OCCUPANCY_RULES["ZONE_CAPACITIES"]
        self.overcrowding_limit = OCCUPANCY_RULES["OVERCROWDING_THRESHOLD_PCT"]
        self.work_start = OCCUPANCY_RULES["WORKING_HOURS"]["start"]
        self.work_end = OCCUPANCY_RULES["WORKING_HOURS"]["end"]

    def analyze_facility_state(self, occupancy_records: List[Dict[str, Any]], security_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Correlates real-time occupancy with recent security events."""
        anomalies = []
        current_hour = datetime.utcnow().hour
        is_working_hours = self.work_start <= current_hour <= self.work_end

        # 1. Analyze Occupancy for Overcrowding & Off-Hours Presence
        if occupancy_records:
            # Group by room to get the absolute latest headcount per zone
            df_occ = pd.DataFrame(occupancy_records)
            df_occ = df_occ.sort_values('timestamp').groupby('room').last().reset_index()

            for _, row in df_occ.iterrows():
                room = row['room']
                count = row['occupancy_count']
                max_cap = self.capacities.get(room, 100) # fallback to 100 if unknown
                
                # Rule A: Overcrowding
                if count >= (max_cap * self.overcrowding_limit):
                    anomalies.append({
                        "type": "Overcrowding Detected",
                        "severity": "High" if count >= max_cap else "Medium",
                        "message": f"[{room}] Headcount at {count}/{max_cap} ({int((count/max_cap)*100)}% capacity)."
                    })
                
                # Rule B: Unauthorized Off-Hours Presence
                if not is_working_hours and count > 0 and room != "Server Room":
                    # Server room might have 24/7 staffing, but normal rooms shouldn't
                    anomalies.append({
                        "type": "Off-Hours Presence",
                        "severity": "Medium",
                        "message": f"[{room}] Unauthorized presence of {count} personnel outside standard operating hours."
                    })

        # 2. Analyze Active Security Breaches
        if security_events:
            for event in security_events:
                if event['status'] in ["Open", "Investigating"] and event['severity'] in ["High", "Medium"]:
                    anomalies.append({
                        "type": f"Active Security Breach: {event['event_type']}",
                        "severity": event['severity'],
                        "message": f"Security alert ({event['event_type']}) flagged at {event['event_time']}. Status: {event['status']}."
                    })

        logger.info(f"Occupancy & Security analysis complete. Found {len(anomalies)} anomalies.")

        # Determine overall facility threat level
        threat_level = "Elevated" if any(a["severity"] == "High" for a in anomalies) else "Moderate" if anomalies else "Secure"

        return {
            "threat_level": threat_level,
            "metrics": {
                "active_anomalies": len(anomalies),
                "is_working_hours": is_working_hours
            },
            "anomalies": anomalies
        }