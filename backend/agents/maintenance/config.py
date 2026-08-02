"""
Configuration and Thresholds for the Maintenance Agent.
"""

MAINTENANCE_RULES = {
    # Expected lifespan of assets in days before they are considered "High Risk"
    "EXPECTED_LIFESPAN_DAYS": {
        "HVAC Unit (Rooftop)": 3650,      # ~10 years
        "Industrial Motor (Pump A)": 1825, # ~5 years
        "Chiller System": 5475,           # ~15 years
        "Backup Generator": 7300          # ~20 years
    },
    "DEFAULT_LIFESPAN_DAYS": 3650,
    
    # Thresholds for flagging anomalies
    "CRITICAL_REPAIR_COUNT": 3,           # Flag if an asset has 3+ repairs in the window
    "REPAIR_WINDOW_DAYS": 365,            # Lookback window for frequent breakdowns (1 year)
    "HIGH_COST_THRESHOLD": 1500.0         # Flag if a single repair exceeds this cost
}