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

    def predict_features(self, features_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Shared logic to predict from a features dictionary."""
        self._load_models()
        if not self.failure_model or not self.fault_model:
            raise RuntimeError("Maintenance ML models not available in models/ directory")

        # Map input JSON data to the AI4I 6-feature format.
        safe_get = lambda key, default: float(features_dict.get(key, default))
        
        type_mapping = {'L': 0, 'M': 1, 'H': 2}
        type_val = type_mapping.get(features_dict.get('type', 'M'), 1)

        features_df = pd.DataFrame([{
            'Type': type_val,
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
                "failure_probability": round(prob_failure, 4),
                "predicted_issue": predicted_issue,
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

            return self.predict_features(df.iloc[-1])

        except Exception as e:
            logger.warning("Maintenance ML analysis failed: %s. Falling back to rules.", e)
            return self._rule_based_analysis(df)