import logging
import pandas as pd
from sklearn.ensemble import IsolationForest
from backend.agents.occupancy.config import OCCUPANCY_RULES

OVERCROWDING_THRESHOLD_PCT = OCCUPANCY_RULES["OVERCROWDING_THRESHOLD_PCT"]
WORKING_HOURS = OCCUPANCY_RULES["WORKING_HOURS"]

logger = logging.getLogger(__name__)


class OccupancyAnalyzer:
    """
    Rules-based overcrowding detection (real per-zone capacity from the DB,
    no more hardcoded config lookup) + Isolation Forest security anomaly
    detection over real zone_level / recent_failed_attempts signal.
    """

    def __init__(self):
        self.overcrowding_limit = OVERCROWDING_THRESHOLD_PCT
        self.work_start = WORKING_HOURS["start"]
        self.work_end = WORKING_HOURS["end"]

    def analyze_facility_state(self, df_occ: pd.DataFrame, df_sec: pd.DataFrame):
        """
        df_occ: one row per zone, already joined with zone metadata —
                columns: zone_id, zone_name, zone_type, max_capacity,
                         occupancy_count, source, timestamp
        df_sec: recent security events — columns include event_type, severity,
                status, event_time, zone_level, recent_failed_attempts
        """
        anomalies = []
        state_summary = {"overcrowded_zones": [], "active_security_threats": 0}

        # --- Occupancy: overcrowding check against real per-zone capacity ---
        if not df_occ.empty:
            for _, row in df_occ.iterrows():
                if row["max_capacity"] > 0:
                    utilization = row["occupancy_count"] / row["max_capacity"]
                    if utilization >= self.overcrowding_limit:
                        state_summary["overcrowded_zones"].append(row["zone_id"])
                        anomalies.append({
                            "type": "Overcrowding Detected",
                            "severity": "High",
                            "message": f"{row['zone_name']} exceeds configured capacity.",
                        })

        # --- Security: Isolation Forest over real zone_level / recent_failed_attempts ---
        if not df_sec.empty:
            df_sec = df_sec.copy()
            df_sec["hour"] = pd.to_datetime(df_sec["event_time"]).dt.hour
            df_sec["severity_num"] = df_sec["severity"].map({"Low": 1, "Medium": 2, "High": 3}).fillna(1)
            df_sec["zone_level"] = df_sec.get("zone_level", 0)
            df_sec["zone_level"] = df_sec["zone_level"].fillna(0)
            df_sec["recent_failed_attempts"] = df_sec.get("recent_failed_attempts", 0)
            df_sec["recent_failed_attempts"] = df_sec["recent_failed_attempts"].fillna(0)

            if len(df_sec) > 5:
                features = df_sec[["hour", "severity_num", "zone_level", "recent_failed_attempts"]]
                model = IsolationForest(contamination=0.1, random_state=42)
                preds = model.fit_predict(features)
                flagged = df_sec[preds == -1]
                for _, row in flagged.iterrows():
                    # Naming matches actions.py's MITIGATION_STRATEGIES partial-match
                    # key ("Active Security Breach") so real canned mitigations fire
                    # instead of the generic fallback.
                    anomalies.append({
                        "type": f"Active Security Breach - {row['event_type']}",
                        "severity": row["severity"],
                        "message": f"Unusual {row['event_type']} pattern detected at hour {int(row['hour'])} "
                                   f"(zone level {int(row['zone_level'])}, {int(row['recent_failed_attempts'])} recent failed attempts).",
                    })

            state_summary["active_security_threats"] = int((df_sec["status"] == "Open").sum())

        return anomalies, state_summary