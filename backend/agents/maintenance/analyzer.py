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
    """Deterministic rules-engine for Maintenance Intelligence with ML prediction."""
    _process_models = None

    def __init__(self):
        self._models_loaded = False
        self.failure_model = None
        self.fault_model = None
        self.feature_names = None

    def _models_dir(self) -> Path:
        return Path(__file__).resolve().parents[3] / "models"

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
            if not failure_path.exists() or not fault_path.exists():
                raise FileNotFoundError(f"Maintenance model artifacts not found under {base}")
            self.failure_model = joblib.load(failure_path)
            self.fault_model = joblib.load(fault_path)
            self._models_loaded = True
            MaintenanceAnalyzer._process_models = (self.failure_model, self.fault_model)
            logger.info("Maintenance ML models loaded successfully from %s", base)
        except Exception as e:
            logger.exception("Failed to load Maintenance ML models: %s", e)
            self._models_loaded = False
            self.failure_model = None
            self.fault_model = None

    def predict_features(self, features_dict: Dict[str, Any]) -> Dict[str, Any]:
        required_features = {"air_temp", "process_temp", "speed", "torque", "wear"}
        missing_features = sorted(required_features - features_dict.keys())
        if missing_features:
            return {"status":"degraded","metrics":{},"anomalies":[],"intelligence_source":"Degraded Fallback","degradation_reason":f"missing_maintenance_features:{','.join(missing_features)}"}
        self._load_models()
        if self.failure_model is None or self.fault_model is None:
            raise RuntimeError(f"Maintenance ML models not available in {self._models_dir()}")
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
        model_started = time.perf_counter()
        failure_probs = self.failure_model.predict_proba(features_df)[0]
        prob_failure = float(failure_probs[1])
        if not np.isfinite(prob_failure) or not 0.0 <= prob_failure <= 1.0:
            raise ValueError("Maintenance model returned an invalid failure probability")
        health_score = max(0.0, min(100.0, (1.0 - prob_failure) * 100))
        predicted_issue = "Normal Operation"
        anomalies = []
        if prob_failure > 0.50:
            predicted_issue = str(self.fault_model.predict(features_df)[0])
            anomalies.append({"timestamp":datetime.datetime.now().isoformat(),"type":"Imminent Asset Failure Predicted","severity":"High","message":f"ML indicates {prob_failure*100:.1f}% chance of failure. Diagnostic: {predicted_issue}."})
        logger.info("Maintenance ML analysis complete. Health Score: %.1f", health_score)
        return {"status":"success","metrics":{"asset_health_score":round(health_score,2),"failure_probability":round(prob_failure,4),"predicted_issue":predicted_issue,"model_latency_ms":round((time.perf_counter()-model_started)*1000,2)},"anomalies":anomalies,"intelligence_source":"ML"}

    def _rule_based_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Existing deterministic rule-based logic preserved as fallback."""
        average = df['energy_kwh'].mean() if 'energy_kwh' in df else 0
        return {"status":"success","metrics":{"average_consumption":float(average)},"anomalies":[]}
