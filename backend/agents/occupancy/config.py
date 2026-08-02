"""
Configuration and Thresholds for the Security & Occupancy Agent.
"""

OCCUPANCY_RULES = {
    # Threshold at which a room is considered critically overcrowded
    "OVERCROWDING_THRESHOLD_PCT": 0.90, 
    
    # Standard max capacities for facility zones
    "ZONE_CAPACITIES": {
        "Main Lobby": 150,
        "Meeting Room A": 20,
        "Cafeteria": 200,
        "Server Room": 5
    },
    
    # Expected standard operating hours
    "WORKING_HOURS": {
        "start": 8,  # 8:00 AM
        "end": 18    # 6:00 PM
    }
}