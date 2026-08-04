# import pandas as pd
# import logging
# from datetime import datetime
# from typing import List, Dict, Any
# from backend.agents.maintenance.config import MAINTENANCE_RULES

# logger = logging.getLogger(__name__)

# class MaintenanceAnalyzer:
#     """
#     Deterministic rules-engine for Predictive Maintenance.
#     Evaluates asset health based on age, repair frequency, and cost metrics.
#     """
#     def __init__(self):
#         self.lifespans = MAINTENANCE_RULES["EXPECTED_LIFESPAN_DAYS"]
#         self.default_lifespan = MAINTENANCE_RULES["DEFAULT_LIFESPAN_DAYS"]
#         self.critical_repair_count = MAINTENANCE_RULES["CRITICAL_REPAIR_COUNT"]
#         self.repair_window = MAINTENANCE_RULES["REPAIR_WINDOW_DAYS"]
#         self.high_cost_threshold = MAINTENANCE_RULES["HIGH_COST_THRESHOLD"]

#     def analyze_asset_health(self, asset: Dict[str, Any], logs: List[Dict[str, Any]]) -> Dict[str, Any]:
#         """Runs health analysis on a single asset and its maintenance history."""
#         anomalies = []
#         now = datetime.utcnow()
        
#         # 1. Analyze Asset Age
#         install_date = pd.to_datetime(asset['installation_date']).tz_localize(None)
#         age_days = (now - install_date).days
#         expected_lifespan = self.lifespans.get(asset['asset_type'], self.default_lifespan)
        
#         life_consumed_pct = (age_days / expected_lifespan) * 100
        
#         if life_consumed_pct >= 90:
#             anomalies.append({
#                 "type": "End of Life Warning",
#                 "severity": "High" if life_consumed_pct >= 100 else "Medium",
#                 "message": f"Asset has consumed {life_consumed_pct:.1f}% of its expected lifespan."
#             })

#         # 2. Analyze Maintenance History
#         total_cost = 0.0
#         recent_repairs = 0
        
#         if logs:
#             df = pd.DataFrame(logs)
#             df['maintenance_date'] = pd.to_datetime(df['maintenance_date']).dt.tz_localize(None)
#             total_cost = df['cost'].sum()
            
#             # Check for frequent recent breakdowns
#             cutoff_date = now - pd.Timedelta(days=self.repair_window)
#             recent_repairs = len(df[df['maintenance_date'] >= cutoff_date])
            
#             if recent_repairs >= self.critical_repair_count:
#                 anomalies.append({
#                     "type": "High Failure Frequency",
#                     "severity": "High",
#                     "message": f"Asset has failed {recent_repairs} times in the last {self.repair_window} days."
#                 })
                
#             # Check for catastrophic costly repairs
#             costly_repairs = df[df['cost'] > self.high_cost_threshold]
#             if not costly_repairs.empty:
#                 anomalies.append({
#                     "type": "Costly Repair History",
#                     "severity": "Medium",
#                     "message": f"Asset experienced {len(costly_repairs)} repairs exceeding ${self.high_cost_threshold}."
#                 })

#         logger.info(f"Analyzed {asset['asset_type']} ({asset['asset_id']}). Found {len(anomalies)} risk factors.")

#         # Determine overall health status
#         status = "Critical" if any(a["severity"] == "High" for a in anomalies) else "Degraded" if anomalies else "Healthy"

#         return {
#             "asset_id": asset['asset_id'],
#             "health_status": status,
#             "metrics": {
#                 "age_days": age_days,
#                 "life_consumed_pct": round(life_consumed_pct, 2),
#                 "total_repair_cost": float(total_cost),
#                 "recent_repairs": recent_repairs
#             },
#             "anomalies": anomalies
#         }

import pandas as pd
import datetime
import logging
import os
from pathlib import Path
from typing import List, Dict, Any

import joblib
import numpy as np

logger = logging.getLogger(__name__)

class MaintenanceAnalyzer:
    """
    Deterministic rules-engine for Maintenance Intelligence.
    Hybrid pattern: try Two-Stage ML prediction first, fall back to deterministic rules.
    """
    def __init__(self):
        # Model placeholders
        self._models_loaded = False
        self.failure_model = None
        self.fault_model = None
        self.feature_names = None

    def _models_dir(self) -> Path:
        return Path(os.getcwd()) / "models"

    def _load_models(self) -> None:
        if self._models_loaded:
            return

        base = self._models_dir()
        try:
            failure_path = base / "maintenance_failure_model_v1.joblib"
            fault_path = base / "maintenance_fault_model_v1.joblib"
            
            if failure_path.exists():
                self.failure_model = joblib.load(failure_path)
            if fault_path.exists():
                self.fault_model = joblib.load(fault_path)

            self._models_loaded = True
            logger.info("Maintenance ML models loaded successfully.")
        except Exception as e:
            logger.exception("Failed to load Maintenance ML models: %s", e)
            self._models_loaded = False

    def _rule_based_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Existing deterministic rule-based logic preserved as fallback."""
        anomalies = []
        health_score = 100.0
        
        # Basic mock logic for fallback
        if 'temperature' in df.columns and df['temperature'].max() > 80:
            health_score -= 25.0
            anomalies.append({
                "timestamp": datetime.datetime.now().isoformat(),
                "type": "High Temperature Warning",
                "severity": "Medium",
                "message": "Asset temperature exceeded safe thresholds."
            })

        logger.info(f"Maintenance rule-based analysis complete. Health: {health_score}")

        return {
            "status": "success",
            "metrics": {
                "asset_health_score": float(health_score),
                "predicted_issue": "None" if health_score > 80 else "Overheating (Rule-Based)",
            },
            "anomalies": anomalies,
            "intelligence_source": "Rule-Based Fallback"
        }

    def analyze_asset_health(self, asset: Dict[str, Any], logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Attempts ML prediction first; falls back to deterministic rules on any failure."""
        if not logs:
            return {"status": "insufficient_data", "anomalies": [], "metrics": {}, "intelligence_source": "Rule-Based Fallback"}

        df = pd.DataFrame(logs)
        
        try:
            self._load_models()
            if not self.failure_model or not self.fault_model:
                raise RuntimeError("Maintenance ML models not available in models/ directory")

            latest = df.iloc[-1]

            # Safely map incoming JSON data to the AI4I 6-feature format.
            safe_get = lambda col, default: float(latest[col]) if col in latest else default
            
            features_df = pd.DataFrame([{
                'Type': 1, # Default to 'Medium' quality
                'Air temperature [K]': safe_get('air_temp', 300.0),
                'Process temperature [K]': safe_get('process_temp', 310.0),
                'Rotational speed [rpm]': safe_get('speed', 1500.0),
                'Torque [Nm]': safe_get('torque', 40.0),
                'Tool wear [min]': safe_get('wear', 15.0)
            }])

            # 1. Predict Failure Probability (Health Score)
            failure_probs = self.failure_model.predict_proba(features_df)[0]
            prob_failure = float(failure_probs[1])
            health_score = max(0.0, min(100.0, (1.0 - prob_failure) * 100))

            # 2. Predict Specific Issue (if probability of failure > 50%)
            predicted_issue = "Normal Operation"
            anomalies = []
            
            if prob_failure > 0.50:
                predicted_issue = str(self.fault_model.predict(features_df)[0])
                anomalies.append({
                    "timestamp": datetime.datetime.now().isoformat(),
                    "type": "Imminent Asset Failure Predicted",
                    "severity": "High",
                    "message": f"ML indicates {prob_failure*100:.1f}% chance of failure. Diagnostic: {predicted_issue}."
                })

            logger.info(f"Maintenance ML analysis complete. Health Score: {health_score:.1f}")

            return {
                "status": "success",
                "metrics": {
                    "asset_health_score": round(health_score, 2),
                    "predicted_issue": predicted_issue,
                },
                "anomalies": anomalies,
                "intelligence_source": "ML"
            }

        except Exception as e:
            logger.warning("Maintenance ML analysis failed: %s. Falling back to rules.", e)
            return self._rule_based_analysis(df)