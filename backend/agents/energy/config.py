"""
Configuration and Thresholds for the Energy Agent.
"""

ENERGY_RULES = {
    "PEAK_DEMAND_THRESHOLD_KW": 75.0,       # Flag if demand exceeds this value
    "ABNORMAL_USAGE_MULTIPLIER": 1.5,       # Flag if hourly usage is 1.5x the rolling average
    "MINIMUM_DATA_POINTS": 24               # Require at least 24 hours of data for reliable analysis
}