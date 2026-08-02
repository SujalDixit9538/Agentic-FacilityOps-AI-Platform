import logging
import pandas as pd
from typing import List, Dict, Any
from backend.agents.cost.config import COST_RULES

logger = logging.getLogger(__name__)

class CostAnalyzer:
    """
    Deterministic rules-engine for Cost Optimization.
    Evaluates month-over-month utility variances and capital expenditure thresholds.
    """
    def __init__(self):
        self.energy_variance_limit = COST_RULES["ENERGY_VARIANCE_THRESHOLD_PCT"]
        self.maint_budget_limit = COST_RULES["MAINTENANCE_BUDGET_LIMIT"]

    def analyze_financial_health(self, cost_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyzes historical cost records to identify budget anomalies and inefficiencies."""
        anomalies = []
        metrics = {"total_records_evaluated": len(cost_records)}

        if not cost_records:
            logger.warning("CostAnalyzer received empty dataset.")
            return {"financial_status": "Unknown", "metrics": metrics, "anomalies": []}

        # Load into DataFrame for time-series analysis
        df = pd.DataFrame(cost_records)
        df['incurred_date'] = pd.to_datetime(df['incurred_date'])
        df = df.sort_values('incurred_date')

        # --- Rule A: Capital Expenditure Warning (Maintenance) ---
        maint_costs = df[df['category'] == 'Maintenance']
        for _, row in maint_costs.iterrows():
            if row['amount'] > self.maint_budget_limit:
                anomalies.append({
                    "type": "Capital Expenditure Warning",
                    "severity": "High",
                    "message": f"Maintenance event '{row['description']}' exceeded individual budget limit at ${row['amount']:,.2f}."
                })

        # --- Rule B: Month-over-Month Energy Spike ---
        energy_costs = df[df['category'] == 'Energy'].set_index('incurred_date').resample('ME')['amount'].sum()
        # Drop months with 0 to avoid division errors
        energy_costs = energy_costs[energy_costs > 0] 
        
        if len(energy_costs) >= 2:
            recent_energy = energy_costs.iloc[-1]
            prev_energy = energy_costs.iloc[-2]
            
            variance = (recent_energy - prev_energy) / prev_energy
            if variance > self.energy_variance_limit:
                anomalies.append({
                    "type": "Energy Cost Spike",
                    "severity": "Medium",
                    "message": f"Energy costs jumped by {variance*100:.1f}% compared to the previous billing cycle."
                })
            
            metrics["latest_energy_variance"] = round(variance * 100, 1)

        # Determine overall financial health status
        financial_status = "Critical" if any(a["severity"] == "High" for a in anomalies) else "Review Required" if anomalies else "Optimized"

        logger.info(f"Cost analysis complete. Found {len(anomalies)} financial anomalies.")

        return {
            "financial_status": financial_status,
            "metrics": metrics,
            "anomalies": anomalies
        }