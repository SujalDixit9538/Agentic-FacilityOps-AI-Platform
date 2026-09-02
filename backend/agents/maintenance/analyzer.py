import pandas as pd
import datetime
import logging
import os
from pathlib import Path
from typing import List, Dict, Any

import joblib
import numpy as np
import time

logger = logging.getLogger(__name__)

class MaintenanceAnalyzer:
    """
    Deterministic rules-engine for Maintenance Intelligence.
    Hybrid pattern: try Two-Stage ML prediction first, fall back to deterministic rules.
    """
    _process_models = None

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

        if MaintenanceAnalyzer._process_models is not None:
            self.failure_model, self.fault_model = MaintenanceAnalyzer._process_models
            self._models_loaded = True
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
            MaintenanceAnalyzer._process_models = (self.failure_model, self.fault_model)
            logger.info("Maintenance ML models loaded successfully.")
        except Exception as e:
            logger.exception("Failed to load Maintenance ML models: %s", e)
            self._models_loaded = False

    def predict_features(self, features_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Shared logic to predict from a features dictionary."""
        required_features = {"air_temp", "process_temp", "speed", "torque", "wear"}
        missing_features = sorted(required_features - features_dict.keys())
        if missing_features:
            return {
                "status": "degraded",
                "metrics": {},
                "anomalies": [],
                "intelligence_source": "Degraded Fallback",
                "degradation_reason": f"missing_maintenance_features:{','.join(missing_features)}",
            }

        self._load_models()
        if not self.failure_model or not self.fault_model:
            raise RuntimeError("Maintenance ML models not available in models/ directory")

        # Map input JSON data to the AI4I 6-feature format.
        safe_get = lambda key: float(features_dict[key])
        
        type_mapping = {'L': 0, 'M': 1, 'H': 2}
        type_val = type_mapping.get(features_dict.get('type', 'M'), 1)

        features_df = pd.DataFrame([{
            'Type': type_val,
            'Air temperature [K]': safe_get('air_temp'),
            'Process temperature [K]': safe_get('process_temp'),
            'Rotational speed [rpm]': safe_get('speed'),
            'Torque [Nm]': safe_get('torque'),
            'Tool wear [min]': safe_get('wear')
        }])

        # 1. Predict Failure Probability (Health Score)
        model_started = time.perf_counter()
        failure_probs = self.failure_model.predict_proba(features_df)[0]
        prob_failure = float(failure_probs[1])
        if not np.isfinite(prob_failure) or not 0.0 <= prob_failure <= 1.0:
            return {
                "status": "degraded",
                "metrics": {},
                "anomalies": [],
                "intelligence_source": "Degraded Fallback",
                "degradation_reason": "non_finite_or_invalid_failure_probability",
            }
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
                "failure_probability": round(prob_failure, 4),
                "predicted_issue": predicted_issue,
                "model_latency_ms": round((time.perf_counter() - model_started) * 1000, 2),
            },
            "anomalies": anomalies,
            "intelligence_source": "ML"
        }

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
                "failure_probability": round(max(0.0, min(1.0, 1.0 - (health_score / 100.0))), 4),
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

            latest_features = df.iloc[-1].to_dict()
            required_features = {"air_temp", "process_temp", "speed", "torque", "wear"}
            if not required_features.issubset(latest_features):
                raise ValueError("missing_maintenance_telemetry")
            result = self.predict_features(latest_features)
            if result.get("status") == "degraded":
                return result
            return result

        except Exception as e:
            logger.warning("Maintenance ML analysis failed: %s. Falling back to rules.", e)
            fallback = self._rule_based_analysis(df)
            fallback["degraded"] = True
            fallback["degradation_reason"] = str(e)
            return fallback