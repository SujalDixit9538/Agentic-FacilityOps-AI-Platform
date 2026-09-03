"""Energy analytics with safe ML integration and a deterministic baseline forecast."""

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List

import joblib
import numpy as np
import pandas as pd

from backend.agents.energy.config import ENERGY_RULES

logger = logging.getLogger(__name__)


class EnergyAnalyzer:
    """Analyze energy telemetry and provide explainable operational intelligence."""

    _process_models = None

    def __init__(self):
        self.peak_threshold = ENERGY_RULES["PEAK_DEMAND_THRESHOLD_KW"]
        self.usage_multiplier = ENERGY_RULES["ABNORMAL_USAGE_MULTIPLIER"]
        self.min_data = ENERGY_RULES["MINIMUM_DATA_POINTS"]
        self._models_loaded = False
        self.total_model = None
        self.hvac_model = None
        self.feature_names = None

    def _models_dir(self) -> Path:
        return Path(os.getcwd()) / "models"

    def _load_models(self) -> None:
        if self._models_loaded:
            return
        if EnergyAnalyzer._process_models is not None:
            self.total_model, self.hvac_model, self.feature_names = EnergyAnalyzer._process_models
            self._models_loaded = True
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
            EnergyAnalyzer._process_models = (self.total_model, self.hvac_model, self.feature_names)
        except Exception as exc:
            logger.warning("Energy ML artifacts unavailable: %s", exc)
            self._models_loaded = False

    @staticmethod
    def _prepare_frame(records: List[Dict[str, Any]]) -> pd.DataFrame:
        df = pd.DataFrame(records).copy()
        if df.empty:
            return df
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["energy_kwh"] = pd.to_numeric(df["energy_kwh"], errors="coerce")
        df["peak_demand_kw"] = pd.to_numeric(df["peak_demand_kw"], errors="coerce")
        df = df.dropna(subset=["timestamp", "energy_kwh"]).sort_values("timestamp")
        return df

    def _rule_based_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        average = float(df["energy_kwh"].mean()) if not df.empty else 0.0
        peak = float(df["peak_demand_kw"].max()) if df["peak_demand_kw"].notna().any() else None
        anomalies = []

        if "peak_demand_kw" in df:
            for _, row in df[df["peak_demand_kw"] > self.peak_threshold].iterrows():
                anomalies.append({
                    "timestamp": row["timestamp"].isoformat(),
                    "type": "Peak Demand Exceeded",
                    "severity": "High",
                    "message": f"Demand reached {row['peak_demand_kw']:.2f} kW (threshold: {self.peak_threshold:.2f} kW).",
                })

        spike_threshold = average * self.usage_multiplier
        for _, row in df[df["energy_kwh"] > spike_threshold].iterrows():
            anomalies.append({
                "timestamp": row["timestamp"].isoformat(),
                "type": "Abnormal Usage Spike",
                "severity": "Medium",
                "message": f"Usage reached {row['energy_kwh']:.2f} kWh versus average {average:.2f} kWh.",
            })

        return {
            "status": "success",
            "metrics": {"total_kwh": float(df["energy_kwh"].sum()), "peak_kw": peak, "avg_kwh": average},
            "anomalies": anomalies,
            "intelligence_source": "Rules",
        }

    def _baseline_forecast(self, df: pd.DataFrame, horizon: int = 24) -> Dict[str, Any]:
        """Forecast the next hours using historical hour/day patterns; no ML artifact required."""
        if len(df) < self.min_data:
            return {"status": "insufficient_data", "horizon_hours": 0, "points": []}

        work = df.set_index("timestamp")["energy_kwh"].resample("h").mean().dropna()
        if len(work) < self.min_data:
            return {"status": "insufficient_data", "horizon_hours": 0, "points": []}

        hourly = work.groupby(work.index.hour).mean()
        recent = work.tail(min(24, len(work))).mean()
        last_ts = work.index[-1]
        points = []
        for step in range(1, horizon + 1):
            ts = last_ts + pd.Timedelta(hours=step)
            pattern = float(hourly.get(ts.hour, recent))
            # Blend the historical hourly pattern with the most recent level.
            predicted = max(0.0, (0.7 * pattern) + (0.3 * float(recent)))
            points.append({"timestamp": ts.isoformat(), "predicted_kwh": round(predicted, 3)})

        return {
            "status": "success",
            "method": "historical_hourly_baseline",
            "horizon_hours": horizon,
            "points": points,
        }

    @staticmethod
    def _recommendations(metrics: Dict[str, Any], anomalies: List[Dict[str, Any]], forecast: Dict[str, Any]) -> List[Dict[str, Any]]:
        recommendations = []
        high_peak = any(a.get("type") == "Peak Demand Exceeded" for a in anomalies)
        spikes = sum(1 for a in anomalies if a.get("type") == "Abnormal Usage Spike")
        if high_peak:
            recommendations.append({
                "priority": "High",
                "action": "Review HVAC and other peak-load equipment schedules around demand events.",
                "reason": "Peak demand exceeded the configured operational threshold.",
            })
        if spikes >= 2:
            recommendations.append({
                "priority": "Medium",
                "action": "Investigate recurring consumption spikes against operating schedules and equipment state.",
                "reason": f"{spikes} abnormal consumption events were detected in the analysis window.",
            })
        if forecast.get("status") == "success" and forecast.get("points"):
            peak_forecast = max(point["predicted_kwh"] for point in forecast["points"])
            if metrics.get("avg_kwh") and peak_forecast > float(metrics["avg_kwh"]) * 1.25:
                recommendations.append({
                    "priority": "Medium",
                    "action": "Review the upcoming high-consumption periods and pre-plan load reduction measures.",
                    "reason": "The baseline forecast indicates a period materially above the historical average.",
                })
        if not recommendations:
            recommendations.append({
                "priority": "Low",
                "action": "Continue monitoring consumption and investigate material changes from the established baseline.",
                "reason": "No high-confidence operational exception was identified.",
            })
        return recommendations

    def _try_ml(self, df: pd.DataFrame) -> Dict[str, Any] | None:
        self._load_models()
        if self.total_model is None:
            return None
        latest = df.iloc[-1]
        temp_cols = [c for c in latest.index if "temp" in c.lower() or "temperature" in c.lower()]
        if not temp_cols or pd.isna(latest[temp_cols[0]]):
            return None
        dt = latest["timestamp"]
        features = pd.DataFrame([{
            "hour": dt.hour,
            "day_of_week": dt.dayofweek,
            "month": dt.month,
            "is_weekend": int(dt.dayofweek >= 5),
            "air_temperature": float(latest[temp_cols[0]]),
        }])
        if self.feature_names is not None:
            expected = list(self.feature_names)
            missing = sorted(set(expected) - set(features.columns))
            if missing:
                return None
            features = features[expected]
        started = time.perf_counter()
        prediction = float(self.total_model.predict(features)[0])
        if not np.isfinite(prediction):
            return None
        return {
            "predicted_total_kwh": prediction,
            "model_latency_ms": round((time.perf_counter() - started) * 1000, 2),
        }

    def analyze_consumption(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        df = self._prepare_frame(records)
        if df.empty or len(df) < self.min_data:
            return {
                "status": "insufficient_data",
                "metrics": {},
                "anomalies": [],
                "forecast": {"status": "insufficient_data", "horizon_hours": 0, "points": []},
                "recommendations": [],
                "intelligence_source": "Rules Only",
                "degraded": True,
                "degradation_reason": "insufficient_energy_data",
            }

        result = self._rule_based_analysis(df)
        forecast = self._baseline_forecast(df)
        result["forecast"] = forecast
        result["recommendations"] = self._recommendations(result["metrics"], result["anomalies"], forecast)

        ml_result = None
        try:
            ml_result = self._try_ml(df)
        except Exception as exc:
            logger.warning("Energy ML inference unavailable; retaining deterministic intelligence: %s", exc)

        if ml_result:
            result["ml_prediction"] = ml_result
            result["intelligence_source"] = "Rules + ML"
        else:
            result["intelligence_source"] = "Rules + Baseline Forecast"

        result["degraded"] = False
        return result
