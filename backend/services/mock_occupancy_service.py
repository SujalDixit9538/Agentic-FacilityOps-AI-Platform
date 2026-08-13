import random
import numpy as np
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from backend.repositories.occupancy_repository import OccupancyRepository
from backend.schemas.occupancy import OccupancyBase, SecurityEventBase

logger = logging.getLogger(__name__)

def seed_mock_occupancy_data(db: Session, facility_id: str = "FAC-001", days: int = 7):
    """
    Generates realistic historical occupancy headcounts and security events.
    """
    repository = OccupancyRepository(db)
    
    # Check if data already exists to prevent duplication
    existing = repository.get_latest_occupancy(facility_id, limit=1)
    if existing:
        logger.info(f"Occupancy data already exists for {facility_id}. Skipping seed.")
        return 0, 0

    logger.info(f"Seeding occupancy and security data for {facility_id} over {days} days...")
    
    base_time = datetime.utcnow() - timedelta(days=days)
    occ_created = 0
    sec_created = 0
    
    # 1. Define standard zones
    zones = [
        {"room": "Main Lobby", "floor": 1, "max_capacity": 150},
        {"room": "Meeting Room A", "floor": 3, "max_capacity": 20},
        {"room": "Cafeteria", "floor": 5, "max_capacity": 200},
        {"room": "Server Room", "floor": 2, "max_capacity": 5}
    ]
    
    # 2. Generate Time-Series Occupancy (Hourly)
    for i in range(days * 24):
        current_time = base_time + timedelta(hours=i)
        hour = current_time.hour
        is_working_hours = 8 <= hour <= 18
        
        for zone in zones:
            # Simulate realistic utilization (high during day, near zero at night)
            if zone["room"] == "Server Room":
                count = random.randint(0, 2) # Server room is always low occupancy
            elif is_working_hours:
                count = random.randint(int(zone["max_capacity"] * 0.2), zone["max_capacity"])
            else:
                count = random.randint(0, int(zone["max_capacity"] * 0.05))
                
            occ_data = OccupancyBase(
                facility_id=facility_id,
                floor=zone["floor"],
                room=zone["room"],
                occupancy_count=count,
                timestamp=current_time
            )
            repository.create_occupancy_record(occ_data)
            occ_created += 1

    # 3. Generate Correlated Security Events
    SECURITY_ISSUE_PROFILES = [
        # (event_type, severity, zone_level_choices, zone_weights, failed_attempts_range)
        ("Unauthorized Access", "High",   [1, 2],    [0.3, 0.7],      (3, 8)),
        ("Tailgating Detected", "Medium", [0, 1],    [0.4, 0.6],      (0, 2)),
        ("Door Left Open",      "Medium", [0, 1, 2], [0.5, 0.3, 0.2], (0, 1)),
        ("After-hours Motion",  "Low",    [0, 1],    [0.6, 0.4],      (0, 1)),
    ]

    def _generate_security_event():
        event_type, severity, zones, weights, attempts_range = random.choice(SECURITY_ISSUE_PROFILES)
        zone_level = int(np.random.choice(zones, p=weights))
        recent_failed_attempts = random.randint(*attempts_range)
        # Escalate if attempts are unusually high in a restricted zone
        if recent_failed_attempts >= 5 and zone_level == 2:
            event_type, severity = "Unauthorized Access", "High"
        return event_type, severity, zone_level, recent_failed_attempts

    # Scatter roughly 0.5-1.5 events per day across the timeline, so longer
    # seed windows produce proportionally more events instead of a flat 5-15
    # regardless of `days`.
    num_events = max(3, random.randint(int(days * 0.5), int(days * 1.5)))
    for _ in range(num_events):
        event_time = base_time + timedelta(hours=random.randint(0, days * 24))
        issue, severity, zone_level, recent_failed_attempts = _generate_security_event()
        
        sec_data = SecurityEventBase(
            facility_id=facility_id,
            event_type=issue,
            severity=severity,
            event_time=event_time,
            status=random.choice(["Open", "Investigating", "Closed"]),
            zone_level=zone_level,
            recent_failed_attempts=recent_failed_attempts
        )
        repository.create_security_event(sec_data)
        sec_created += 1

    logger.info(f"Seeded {occ_created} occupancy records and {sec_created} security events for {facility_id}.")
    return occ_created, sec_created