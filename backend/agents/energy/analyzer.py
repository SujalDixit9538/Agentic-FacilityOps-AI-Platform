# import pandas as pd
# import datetime
# import logging
# import os
# from pathlib import Path
# from typing import List, Dict, Any

# import joblib
# import numpy as np

# from backend.agents.energy.config import ENERGY_RULES

# logger = logging.getLogger(__name__)


# class EnergyAnalyzer:
#     """
#     Deterministic rules-engine for Energy Intelligence.
#     Hybrid pattern: try ML prediction first, fall back to deterministic rules.
#     """
#     def __init__(self):
#         self.peak_threshold = ENERGY_RULES["PEAK_DEMAND_THRESHOLD_KW"]
#         self.usage_multiplier = ENERGY_RULES["ABNORMAL_USAGE_MULTIPLIER"]
#         self.min_data = ENERGY_RULES["MINIMUM_DATA_POINTS"]

#         # Model placeholders
#         self._models_loaded = False
#         self.total_model = None
#         self.hvac_model = None
#         self.feature_pipeline = None

#     def _models_dir(self) -> Path:
#         # Prefer project-root `models/` directory
#         return Path(os.getcwd()) / "models"

#     def _load_models(self) -> None:
#         if self._models_loaded:
#             return

#         base = self._models_dir()
#         try:
#             total_path = base / "energy_model_total_v1.joblib"
#             hvac_path = base / "energy_model_hvac_v1.joblib"
#             features_path = base / "energy_model_features.joblib"

#             if total_path.exists():
#                 self.total_model = joblib.load(total_path)
#             if hvac_path.exists():
#                 self.hvac_model = joblib.load(hvac_path)
#             if features_path.exists():
#                 self.feature_pipeline = joblib.load(features_path)

#             self._models_loaded = True
#             logger.info("Energy ML models loaded (where available).")
#         except Exception as e:
#             # Any problem loading models should not break the rules engine
#             logger.exception("Failed to load ML models: %s", e)
#             self._models_loaded = False

#     def _rule_based_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
#         """Existing deterministic rule-based logic preserved as fallback."""
#         average_consumption = df['energy_kwh'].mean()
#         anomalies = []

#         peak_violations = df[df['peak_demand_kw'] > self.peak_threshold]
#         for _, row in peak_violations.iterrows():
#             anomalies.append({
#                 "timestamp": row['timestamp'].isoformat(),
#                 "type": "Peak Demand Exceeded",
#                 "severity": "High",
#                 "message": f"Demand reached {row['peak_demand_kw']:.2f} kW (Threshold: {self.peak_threshold} kW)"
#             })

#         spike_threshold = average_consumption * self.usage_multiplier
#         usage_spikes = df[df['energy_kwh'] > spike_threshold]
#         for _, row in usage_spikes.iterrows():
#             anomalies.append({
#                 "timestamp": row['timestamp'].isoformat(),
#                 "type": "Abnormal Usage Spike",
#                 "severity": "Medium",
#                 "message": f"Usage spiked to {row['energy_kwh']:.2f} kWh (Avg: {average_consumption:.2f} kWh)"
#             })

#         logger.info(f"Energy rule-based analysis complete. Found {len(anomalies)} anomalies.")

#         return {
#             "status": "success",
#             "metrics": {
#                 "total_kwh": float(df['energy_kwh'].sum()),
#                 "peak_kw": float(df['peak_demand_kw'].max()),
#                 "avg_kwh": float(average_consumption)
#             },
#             "anomalies": anomalies,
#             "intelligence_source": "Rule-Based Fallback"
#         }

#     def analyze_consumption(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
#         """Attempts ML prediction first; falls back to deterministic rules on any failure."""
#         if not records or len(records) < self.min_data:
#             logger.warning("Insufficient data for robust energy analysis.")
#             return {"status": "insufficient_data", "anomalies": [], "metrics": {}, "intelligence_source": "Rule-Based Fallback"}

#         # Load into Pandas for efficient vector operations
#         df = pd.DataFrame(records)
#         df['timestamp'] = pd.to_datetime(df['timestamp'])
#         df = df.sort_values('timestamp')

#         # Prepare baseline values used by both ML and rules
#         average_consumption = df['energy_kwh'].mean()

#         # Try ML-based path first
#         try:
#             self._load_models()
#             if not self.total_model:
#                 raise RuntimeError("Total energy model not available")

#             # Build feature vector using most-recent record
#             latest = df.iloc[-1]

#             # Find a temperature column if present
#             temp_cols = [c for c in df.columns if 'temp' in c.lower() or 'temperature' in c.lower()]
#             if not temp_cols:
#                 raise ValueError("No temperature-like feature available for ML prediction")

#             temp_col = temp_cols[0]
#             temperature = float(latest[temp_col])

#             hour = int(pd.to_datetime(latest['timestamp']).hour)
#             weekday = int(pd.to_datetime(latest['timestamp']).weekday())

#             features = np.array([[temperature, hour, weekday]])

#             # Apply feature pipeline if present
#             if self.feature_pipeline is not None:
#                 try:
#                     features = self.feature_pipeline.transform(features)
#                 except Exception:
#                     # Feature pipeline could be expecting a different shape; try a fallback
#                     logger.exception("Feature pipeline transform failed; attempting raw features.")

#             # Run model inference (guarded)
#             predicted_total = None
#             predicted_hvac = None
#             try:
#                 predicted_total = float(self.total_model.predict(features)[0])
#             except Exception:
#                 logger.exception("Total energy model inference failed")
#                 raise

#             if self.hvac_model is not None:
#                 try:
#                     predicted_hvac = float(self.hvac_model.predict(features)[0])
#                 except Exception:
#                     logger.exception("HVAC model inference failed; continuing without HVAC prediction")

#             # Build ML response
#             metrics = {
#                 "predicted_total_kwh": predicted_total,
#                 "predicted_hvac_kwh": predicted_hvac if predicted_hvac is not None else None,
#                 "avg_kwh": float(average_consumption)
#             }

#             # Optionally run lightweight anomaly heuristics on predicted_total
#             anomalies = []
#             spike_threshold = average_consumption * self.usage_multiplier
#             if predicted_total is not None and predicted_total > spike_threshold:
#                 anomalies.append({
#                     "timestamp": latest['timestamp'].isoformat(),
#                     "type": "Predicted Abnormal Usage",
#                     "severity": "Medium",
#                     "message": f"ML predicted total {predicted_total:.2f} kWh (Avg: {average_consumption:.2f} kWh)"
#                 })

#             logger.info("Energy ML analysis complete.")

#             return {
#                 "status": "success",
#                 "metrics": metrics,
#                 "anomalies": anomalies,
#                 "intelligence_source": "ML"
#             }

#         except Exception as e:
#             # Any failure in model-loading or inference should trigger rule-based fallback
#             logger.warning("ML analysis unavailable or failed: %s. Falling back to rules.", e)
#             return self._rule_based_analysis(df)




import pandas as pd
import datetime
import logging
import os
from pathlib import Path
from typing import List, Dict, Any

import joblib
import numpy as np

from backend.agents.energy.config import ENERGY_RULES

logger = logging.getLogger(__name__)

class EnergyAnalyzer:
    """
    Deterministic rules-engine for Energy Intelligence.
    Hybrid pattern: try ML prediction first, fall back to deterministic rules.
    """
    def __init__(self):
        self.peak_threshold = ENERGY_RULES["PEAK_DEMAND_THRESHOLD_KW"]
        self.usage_multiplier = ENERGY_RULES["ABNORMAL_USAGE_MULTIPLIER"]
        self.min_data = ENERGY_RULES["MINIMUM_DATA_POINTS"]

        # Model placeholders
        self._models_loaded = False
        self.total_model = None
        self.hvac_model = None
        self.feature_names = None

    def _models_dir(self) -> Path:
        # Prefer project-root `models/` directory
        return Path(os.getcwd()) / "models"

    def _load_models(self) -> None:
        if self._models_loaded:
            return

        base = self._models_dir()
        try:
            total_path = base / "energy_model_total_v1.joblib"
            hvac_path = base / "energy_model_hvac_v1.joblib"
            features_path = base / "energy_model_features.joblib"

            if total_path.exists():
                self.total_model = joblib.load(total_path)
            if hvac_path.exists():
                self.hvac_model = joblib.load(hvac_path)
            if features_path.exists():
                self.feature_names = joblib.load(features_path)

            self._models_loaded = True
            logger.info("Energy ML models loaded (where available).")
        except Exception as e:
            # Any problem loading models should not break the rules engine
            logger.exception("Failed to load ML models: %s", e)
            self._models_loaded = False

    def _rule_based_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Existing deterministic rule-based logic preserved as fallback."""
        average_consumption = df['energy_kwh'].mean()
        anomalies = []

        peak_violations = df[df['peak_demand_kw'] > self.peak_threshold]
        for _, row in peak_violations.iterrows():
            anomalies.append({
                "timestamp": row['timestamp'].isoformat(),
                "type": "Peak Demand Exceeded",
                "severity": "High",
                "message": f"Demand reached {row['peak_demand_kw']:.2f} kW (Threshold: {self.peak_threshold} kW)"
            })

        spike_threshold = average_consumption * self.usage_multiplier
        usage_spikes = df[df['energy_kwh'] > spike_threshold]
        for _, row in usage_spikes.iterrows():
            anomalies.append({
                "timestamp": row['timestamp'].isoformat(),
                "type": "Abnormal Usage Spike",
                "severity": "Medium",
                "message": f"Usage spiked to {row['energy_kwh']:.2f} kWh (Avg: {average_consumption:.2f} kWh)"
            })

        logger.info(f"Energy rule-based analysis complete. Found {len(anomalies)} anomalies.")

        return {
            "status": "success",
            "metrics": {
                "total_kwh": float(df['energy_kwh'].sum()),
                "peak_kw": float(df['peak_demand_kw'].max()),
                "avg_kwh": float(average_consumption)
            },
            "anomalies": anomalies,
            "intelligence_source": "Rule-Based Fallback"
        }

    def analyze_consumption(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Attempts ML prediction first; falls back to deterministic rules on any failure."""
        if not records or len(records) < self.min_data:
            logger.warning("Insufficient data for robust energy analysis.")
            return {"status": "insufficient_data", "anomalies": [], "metrics": {}, "intelligence_source": "Rule-Based Fallback"}

        # Load into Pandas for efficient vector operations
        df = pd.DataFrame(records)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')

        # Prepare baseline values used by both ML and rules
        average_consumption = df['energy_kwh'].mean()

        # Try ML-based path first
        try:
            self._load_models()
            if not self.total_model:
                raise RuntimeError("Total energy model not available")

            # Build feature vector using most-recent record
            latest = df.iloc[-1]

            # Find a temperature column if present, otherwise default to 22.5 to prevent crashes
            temp_cols = [c for c in df.columns if 'temp' in c.lower() or 'temperature' in c.lower()]
            temperature = float(latest[temp_cols[0]]) if temp_cols else 22.5

            dt = pd.to_datetime(latest['timestamp'])

            # Build exact 5-feature DataFrame expected by the model
            features_df = pd.DataFrame([{
                'hour': dt.hour,
                'day_of_week': dt.dayofweek,
                'month': dt.month,
                'is_weekend': int(dt.dayofweek >= 5),
                'air_temperature': temperature
            }])

            # Run model inference (guarded)
            predicted_total = None
            predicted_hvac = None
            try:
                predicted_total = float(self.total_model.predict(features_df)[0])
            except Exception:
                logger.exception("Total energy model inference failed")
                raise

            if self.hvac_model is not None:
                try:
                    predicted_hvac = float(self.hvac_model.predict(features_df)[0])
                except Exception:
                    logger.exception("HVAC model inference failed; continuing without HVAC prediction")

            # Build ML response
            metrics = {
                "predicted_total_kwh": predicted_total,
                "predicted_hvac_kwh": predicted_hvac if predicted_hvac is not None else None,
                "avg_kwh": float(average_consumption)
            }

            # Optionally run lightweight anomaly heuristics on predicted_total
            anomalies = []
            spike_threshold = average_consumption * self.usage_multiplier
            if predicted_total is not None and predicted_total > spike_threshold:
                anomalies.append({
                    "timestamp": latest['timestamp'].isoformat(),
                    "type": "Predicted Abnormal Usage",
                    "severity": "Medium",
                    "message": f"ML predicted total {predicted_total:.2f} kWh (Avg: {average_consumption:.2f} kWh)"
                })

            logger.info("Energy ML analysis complete.")

            return {
                "status": "success",
                "metrics": metrics,
                "anomalies": anomalies,
                "intelligence_source": "ML"
            }

        except Exception as e:
            # Any failure in model-loading or inference should trigger rule-based fallback
            logger.warning("ML analysis unavailable or failed: %s. Falling back to rules.", e)
            return self._rule_based_analysis(df)