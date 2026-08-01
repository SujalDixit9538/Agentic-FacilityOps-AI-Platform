import pandas as pd
import logging
from typing import List, Dict, Any
from backend.agents.energy.config import ENERGY_RULES

logger = logging.getLogger(__name__)

class EnergyAnalyzer:
    """
    Deterministic rules-engine for Energy Intelligence.
    Implements Blueprint Rule: Rules first, ML second.
    """
    def __init__(self):
        self.peak_threshold = ENERGY_RULES["PEAK_DEMAND_THRESHOLD_KW"]
        self.usage_multiplier = ENERGY_RULES["ABNORMAL_USAGE_MULTIPLIER"]
        self.min_data = ENERGY_RULES["MINIMUM_DATA_POINTS"]

    def analyze_consumption(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Runs rule-based anomaly detection on raw energy data."""
        if not records or len(records) < self.min_data:
            logger.warning("Insufficient data for robust energy analysis.")
            return {"status": "insufficient_data", "anomalies": [], "metrics": {}}

        # Load into Pandas for efficient vector operations
        df = pd.DataFrame(records)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')

        # Calculate Rolling Baseline
        average_consumption = df['energy_kwh'].mean()
        
        anomalies = []
        
        # Rule 1: Absolute Peak Demand Violation
        peak_violations = df[df['peak_demand_kw'] > self.peak_threshold]
        for _, row in peak_violations.iterrows():
            anomalies.append({
                "timestamp": row['timestamp'].isoformat(),
                "type": "Peak Demand Exceeded",
                "severity": "High",
                "message": f"Demand reached {row['peak_demand_kw']:.2f} kW (Threshold: {self.peak_threshold} kW)"
            })

        # Rule 2: Relative Abnormal Usage Spike
        spike_threshold = average_consumption * self.usage_multiplier
        usage_spikes = df[df['energy_kwh'] > spike_threshold]
        for _, row in usage_spikes.iterrows():
            anomalies.append({
                "timestamp": row['timestamp'].isoformat(),
                "type": "Abnormal Usage Spike",
                "severity": "Medium",
                "message": f"Usage spiked to {row['energy_kwh']:.2f} kWh (Avg: {average_consumption:.2f} kWh)"
            })

        logger.info(f"Energy analysis complete. Found {len(anomalies)} anomalies.")

        return {
            "status": "success",
            "metrics": {
                "total_kwh": float(df['energy_kwh'].sum()),
                "peak_kw": float(df['peak_demand_kw'].max()),
                "avg_kwh": float(average_consumption)
            },
            "anomalies": anomalies
        }