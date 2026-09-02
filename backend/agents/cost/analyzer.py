# import logging
# import pandas as pd
# from typing import List, Dict, Any
# from backend.agents.cost.config import COST_RULES

# logger = logging.getLogger(__name__)

# class CostAnalyzer:
#     """
#     Deterministic rules-engine for Cost Optimization.
#     Evaluates month-over-month utility variances and capital expenditure thresholds.
#     """
#     def __init__(self):
#         self.energy_variance_limit = COST_RULES["ENERGY_VARIANCE_THRESHOLD_PCT"]
#         self.maint_budget_limit = COST_RULES["MAINTENANCE_BUDGET_LIMIT"]

#     def analyze_financial_health(self, cost_records: List[Dict[str, Any]]) -> Dict[str, Any]:
#         """Analyzes historical cost records to identify budget anomalies and inefficiencies."""
#         anomalies = []
#         metrics = {"total_records_evaluated": len(cost_records)}

#         if not cost_records:
#             logger.warning("CostAnalyzer received empty dataset.")
#             return {"financial_status": "Unknown", "metrics": metrics, "anomalies": []}

#         # Load into DataFrame for time-series analysis
#         df = pd.DataFrame(cost_records)
#         df['incurred_date'] = pd.to_datetime(df['incurred_date'])
#         df = df.sort_values('incurred_date')

#         # --- Rule A: Capital Expenditure Warning (Maintenance) ---
#         maint_costs = df[df['category'] == 'Maintenance']
#         for _, row in maint_costs.iterrows():
#             if row['amount'] > self.maint_budget_limit:
#                 anomalies.append({
#                     "type": "Capital Expenditure Warning",
#                     "severity": "High",
#                     "message": f"Maintenance event '{row['description']}' exceeded individual budget limit at ${row['amount']:,.2f}."
#                 })

#         # --- Rule B: Month-over-Month Energy Spike ---
#         energy_costs = df[df['category'] == 'Energy'].set_index('incurred_date').resample('ME')['amount'].sum()
#         # Drop months with 0 to avoid division errors
#         energy_costs = energy_costs[energy_costs > 0] 
        
#         if len(energy_costs) >= 2:
#             recent_energy = energy_costs.iloc[-1]
#             prev_energy = energy_costs.iloc[-2]
            
#             variance = (recent_energy - prev_energy) / prev_energy
#             if variance > self.energy_variance_limit:
#                 anomalies.append({
#                     "type": "Energy Cost Spike",
#                     "severity": "Medium",
#                     "message": f"Energy costs jumped by {variance*100:.1f}% compared to the previous billing cycle."
#                 })
            
#             metrics["latest_energy_variance"] = round(variance * 100, 1)

#         # Determine overall financial health status
#         financial_status = "Critical" if any(a["severity"] == "High" for a in anomalies) else "Review Required" if anomalies else "Optimized"

#         logger.info(f"Cost analysis complete. Found {len(anomalies)} financial anomalies.")

#         return {
#             "financial_status": financial_status,
#             "metrics": metrics,
#             "anomalies": anomalies
#         }





import logging
from datetime import datetime, timezone
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
import joblib
from backend.agents.cost.config import COST_RULES

logger = logging.getLogger(__name__)

class CostAnalyzer:
    """
    Hybrid Intelligence for Cost Optimization.
    Evaluates historical utility variances (rules) AND prescribes future cost-saving actions (ML).
    """
    def __init__(self):
        self.energy_variance_limit = COST_RULES["ENERGY_VARIANCE_THRESHOLD_PCT"]
        self.maint_budget_limit = COST_RULES["MAINTENANCE_BUDGET_LIMIT"]
        
        # Model placeholders
        self._models_loaded = False
        self.action_model = None
        self.savings_model = None

    def _models_dir(self) -> Path:
        return Path(__file__).resolve().parents[3] / "models"

    def _load_models(self) -> None:
        if self._models_loaded:
            return

        base = self._models_dir()
        try:
            action_path = base / "cost_action_model_v1.joblib"
            savings_path = base / "cost_savings_model_v1.joblib"
            feature_path = base / "cost_model_features.joblib"

            if action_path.exists():
                self.action_model = joblib.load(action_path)
            if savings_path.exists():
                self.savings_model = joblib.load(savings_path)

            expected_features = joblib.load(feature_path)
            model_features = list(getattr(self.action_model, "feature_names_in_", []))
            if not model_features or model_features != list(expected_features):
                raise ValueError("Cost model feature metadata does not match the action model.")
            if list(getattr(self.savings_model, "feature_names_in_", [])) != model_features:
                raise ValueError("Cost model feature metadata does not match the savings model.")

            self._models_loaded = True
            logger.info("Cost Prescriptive ML models loaded successfully.")
        except Exception as e:
            logger.exception("Failed to load Cost ML models: %s", e)
            self._models_loaded = False

    def analyze_financial_health(
        self,
        cost_records: List[Dict[str, Any]],
        facility_state: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Analyzes historical costs and prescribes future optimizations via ML."""
        anomalies = []
        metrics = {"total_records_evaluated": len(cost_records)}
        intelligence_source = "Rules Only"
        degradation_reason = None

        if not cost_records:
            logger.warning("CostAnalyzer received empty dataset.")
            return {"financial_status": "Unknown", "metrics": metrics, "anomalies": [], "intelligence_source": intelligence_source}

        # ==========================================
        # 1. BACKWARD-LOOKING: Financial Audit (Rules)
        # ==========================================
        try:
            df = pd.DataFrame(cost_records)
            if 'incurred_date' in df.columns and 'amount' in df.columns and 'category' in df.columns:
                df['incurred_date'] = pd.to_datetime(df['incurred_date'])
                df = df.sort_values('incurred_date')

                # Rule A: Capital Expenditure Warning (Maintenance)
                maint_costs = df[df['category'] == 'Maintenance']
                for _, row in maint_costs.iterrows():
                    if row['amount'] > self.maint_budget_limit:
                        anomalies.append({
                            "type": "Capital Expenditure Warning",
                            "severity": "High",
                            "message": f"Maintenance event '{row.get('description', 'Unknown')}' exceeded budget limit at ${row['amount']:,.2f}."
                        })

                # Rule B: Month-over-Month Energy Spike
                energy_costs = df[df['category'] == 'Energy'].set_index('incurred_date').resample('ME')['amount'].sum()
                energy_costs = energy_costs[energy_costs > 0] 
                
                if len(energy_costs) >= 2:
                    recent_energy = energy_costs.iloc[-1]
                    prev_energy = energy_costs.iloc[-2]
                    
                    variance = (recent_energy - prev_energy) / prev_energy
                    if variance > self.energy_variance_limit:
                        anomalies.append({
                            "type": "Energy Cost Spike",
                            "severity": "Medium",
                            "message": f"Energy costs jumped by {variance*100:.1f}% compared to previous billing cycle."
                        })
                    
                    metrics["latest_energy_variance"] = round(variance * 100, 1)
        except Exception as e:
            logger.warning(f"Rule-based financial audit encountered an issue: {e}")

        # ==========================================
        # 2. FORWARD-LOOKING: Prescriptive Orchestration (ML)
        # ==========================================
        try:
            self._load_models()
            if self.action_model is not None and self.savings_model is not None:
                if not facility_state or not facility_state.get("is_complete"):
                    degradation_reason = "complete_cross_domain_state_unavailable"
                    raise RuntimeError(degradation_reason)

                features_df = pd.DataFrame([{
                    "energy_load": float(facility_state["energy_load"]),
                    "asset_health": float(facility_state["asset_health"]),
                    "occupancy_pct": float(facility_state["occupancy_pct"]),
                    "hour": datetime.now(timezone.utc).hour,
                }], columns=["energy_load", "asset_health", "occupancy_pct", "hour"])

                # A. Predict Optimal Action (Classification)
                optimal_action = str(self.action_model.predict(features_df)[0])

                # B. Predict ROI Savings (Regression)
                predicted_savings = float(self.savings_model.predict(features_df)[0])

                metrics["prescriptive_action"] = optimal_action
                metrics["predicted_savings_usd"] = round(predicted_savings, 2)
                
                intelligence_source = "ML (Prescriptive AI)"

                # Route the ML recommendation as an actionable anomaly/alert
                if optimal_action != "Maintain Standard Operations" and predicted_savings > 0:
                    anomalies.append({
                        "type": "Prescriptive Optimization Available",
                        "severity": "Medium", # Medium severity since it's an opportunity, not a failure
                        "message": f"ML Orchestrator recommends '{optimal_action}'. Estimated ROI: ${predicted_savings:,.2f}."
                    })
            else:
                raise RuntimeError("Prescriptive ML models missing from models/ directory.")

        except Exception as e:
            if degradation_reason is None:
                degradation_reason = str(e)
            logger.warning("Prescriptive ML analysis failed: %s. Relying purely on historical rules.", e)

        # ==========================================
        # 3. REPORTING
        # ==========================================
        financial_status = "Critical" if any(a.get("severity") == "High" for a in anomalies) else "Review Required" if anomalies else "Optimized"
        
        # Attach the intelligence source to the metrics payload for the UI
        metrics["intelligence_source"] = intelligence_source
        if degradation_reason:
            metrics["degradation_reason"] = degradation_reason

        logger.info(f"Cost analysis complete via {intelligence_source}. Found {len(anomalies)} alerts/recommendations.")

        return {
            "financial_status": financial_status,
            "metrics": metrics,
            "anomalies": anomalies
        }