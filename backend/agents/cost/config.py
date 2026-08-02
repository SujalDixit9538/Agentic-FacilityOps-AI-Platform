"""
Configuration and Thresholds for the Cost Optimization Agent.
"""

COST_RULES = {
    # Flag if energy cost jumps by more than 15% month-over-month
    "ENERGY_VARIANCE_THRESHOLD_PCT": 0.15, 
    
    # Flag if a single maintenance event exceeds this dollar amount
    "MAINTENANCE_BUDGET_LIMIT": 5000.00,   
    
    # Target baseline for operational efficiency evaluations
    "TARGET_EFFICIENCY_SCORE": 85 
}