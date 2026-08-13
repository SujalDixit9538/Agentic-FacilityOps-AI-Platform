import logging
from datetime import datetime
import pandas as pd
import numpy as np
import os
from pathlib import Path
from typing import List, Dict, Any
import joblib
from backend.agents.occupancy.config import OCCUPANCY_RULES

logger = logging.getLogger(__name__)

class OccupancyAnalyzer:
    """
    Deterministic rules-engine with Hybrid ML Occupancy & Security Intelligence.
    Evaluates overcrowding via Regression and security threats via Isolation Forest.
    """
    def __init__(self):
        self.capacities = OCCUPANCY_RULES["ZONE_CAPACITIES"]
        self.overcrowding_limit = OCCUPANCY_RULES["OVERCROWDING_THRESHOLD_PCT"]
        self.work_start = OCCUPANCY_RULES["WORKING_HOURS"]["start"]
        self.work_end = OCCUPANCY_RULES["WORKING_HOURS"]["end"]

        # Model placeholders
        self._models_loaded = False
        self.occupancy_model = None
        self.security_model = None

    def _models_dir(self) -> Path:
        return Path(os.getcwd()) / "models"

    def _load_models(self) -> None:
        if self._models_loaded:
            return

        base = self._models_dir()
        try:
            occ_path = base / "occupancy_model_v1.joblib"
            sec_path = base / "security_model_v1.joblib"

            if occ_path.exists():
                self.occupancy_model = joblib.load(occ_path)
            if sec_path.exists():
                self.security_model = joblib.load(sec_path)

            self._models_loaded = True
            logger.info("Occupancy & Security ML models loaded successfully.")
        except Exception as e:
            logger.exception("Failed to load ML models: %s", e)
            self._models_loaded = False

    def analyze_facility_state(self, occupancy_records: List[Dict[str, Any]], security_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Correlates real-time occupancy and security events using Dual ML models."""
        anomalies = []
        now = datetime.utcnow()
        current_hour = now.hour
        is_working_hours = self.work_start <= current_hour <= self.work_end

        ml_occ_success = False
        ml_sec_success = False

        self._load_models()

        # ==========================================
        # 1. OCCUPANCY ANALYSIS (Regression)
        # ==========================================
        try:
            if self.occupancy_model is not None and occupancy_records:
                df_occ = pd.DataFrame(occupancy_records)
                df_occ['timestamp'] = pd.to_datetime(df_occ['timestamp'])
                df_occ = df_occ.sort_values('timestamp').groupby('room').last().reset_index()

                def get_zone_type(room_name):
                    max_cap = self.capacities.get(room_name, 100)
                    if max_cap >= 100:
                        return 0
                    elif max_cap >= 20:
                        return 1
                    else:
                        return 2

                df_occ['zone_type'] = df_occ['room'].apply(get_zone_type)

                features_df = pd.DataFrame({
                    'hour': current_hour,
                    'day_of_week': now.weekday(),
                    'month': now.month,
                    'zone_type': df_occ['zone_type']
                })

                df_occ['expected_count'] = self.occupancy_model.predict(features_df)
                ml_occ_success = True

                for idx, row in df_occ.iterrows():
                    room = row['room']
                    count = row['occupancy_count']
                    expected = row['expected_count']
                    max_cap = self.capacities.get(room, 100)

                    # ML Anomaly Check
                    if count > max(20, expected * 1.6):
                        anomalies.append({
                            "type": "ML Predicted Overcrowding Spike",
                            "severity": "High" if count >= max_cap else "Medium",
                            "message": f"[{room}] Actual crowd ({count}) heavily exceeds ML baseline expectation ({expected:.1f})."
                        })
                    # Hard Capacity Check
                    elif count >= (max_cap * self.overcrowding_limit):
                        anomalies.append({
                            "type": "Overcrowding Detected",
                            "severity": "High" if count >= max_cap else "Medium",
                            "message": f"[{room}] Headcount at {count}/{max_cap} ({int((count/max_cap)*100)}% capacity)."
                        })
            else:
                raise RuntimeError("Occupancy model missing or empty data.")
        except Exception as e:
            logger.warning("Occupancy ML failed: %s. Falling back to rules.", e)
            # Fallback rules
            if occupancy_records:
                for row in occupancy_records:
                    count = row.get('occupancy_count', 0)
                    room = row.get('room', 'Unknown')
                    max_cap = self.capacities.get(room, 100)
                    if count >= (max_cap * self.overcrowding_limit):
                        anomalies.append({
                            "type": "Overcrowding Detected",
                            "severity": "High",
                            "message": f"[{room}] Headcount at capacity threshold."
                        })

        # ==========================================
        # 2. SECURITY ANALYSIS (Isolation Forest)
        # ==========================================
        try:
            if self.security_model is not None and security_events:
                for event in security_events:
                    # Parse Event Time
                    try:
                        ev_time = datetime.fromisoformat(event.get('event_time', now.isoformat()))
                    except:
                        ev_time = now
                    
                    ev_type = event.get('event_type', '').lower()

                    # Infer features from DB string
                    zone_level = 0
                    if 'server' in ev_type or 'restricted' in ev_type: zone_level = 2
                    elif 'office' in ev_type: zone_level = 1
                    
                    failed_attempts = 3 if 'failed' in ev_type or 'denied' in ev_type else 0

                    sec_features = pd.DataFrame([{
                        'hour': ev_time.hour,
                        'day_of_week': ev_time.weekday(),
                        'zone_level': zone_level,
                        'recent_failed_attempts': failed_attempts
                    }])

                    # Predict Anomaly (-1 = Anomaly, 1 = Normal)
                    if self.security_model.predict(sec_features)[0] == -1:
                        anomalies.append({
                            "type": f"ML Security Anomaly: {event.get('event_type', 'Suspicious Activity')}",
                            "severity": "High",
                            "message": f"Isolation Forest flagged irregular access pattern at {ev_time.strftime('%H:%M')}."
                        })
                    elif event.get('status') in ["Open", "Investigating"] and event.get('severity') in ["High", "Medium"]:
                        # Retain standard open alerts even if ML thinks they are normal
                        anomalies.append({
                            "type": f"Active Security Breach: {event.get('event_type')}",
                            "severity": event.get('severity'),
                            "message": f"Security alert ({event.get('event_type')}) flagged."
                        })
                ml_sec_success = True
            else:
                raise RuntimeError("Security model missing or empty data.")
        except Exception as e:
            logger.warning("Security ML failed: %s. Falling back to rules.", e)
            # Fallback rules
            if security_events:
                for event in security_events:
                    if event.get('status') in ["Open", "Investigating"] and event.get('severity') in ["High", "Medium"]:
                        anomalies.append({
                            "type": f"Active Security Breach: {event.get('event_type')}",
                            "severity": event.get('severity'),
                            "message": f"Security alert ({event.get('event_type')}) flagged."
                        })

        # ==========================================
        # 3. REPORTING
        # ==========================================
        if ml_occ_success and ml_sec_success:
            intelligence_source = "ML (Dual Pipeline)"
        elif ml_occ_success or ml_sec_success:
            intelligence_source = "ML (Partial)"
        else:
            intelligence_source = "Rule-Based Fallback"

        threat_level = "Elevated" if any(a["severity"] == "High" for a in anomalies) else "Moderate" if anomalies else "Secure"

        return {
            "threat_level": threat_level,
            "metrics": {
                "active_anomalies": len(anomalies),
                "is_working_hours": is_working_hours,
                "intelligence_source": intelligence_source
            },
            "anomalies": anomalies
        }