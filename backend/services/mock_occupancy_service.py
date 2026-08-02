import random
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

    # 3. Generate Random Security Events
    security_issues = [
        ("Unauthorized Access", "High"),
        ("Door Left Open", "Medium"),
        ("Tailgating Detected", "Medium"),
        ("After-hours Motion", "Low")
    ]
    
    # Scatter 5 to 15 random events across the timeline
    for _ in range(random.randint(5, 15)):
        event_time = base_time + timedelta(hours=random.randint(0, days * 24))
        issue, severity = random.choice(security_issues)
        
        sec_data = SecurityEventBase(
            facility_id=facility_id,
            event_type=issue,
            severity=severity,
            event_time=event_time,
            status=random.choice(["Open", "Investigating", "Closed"])
        )
        repository.create_security_event(sec_data)
        sec_created += 1

    logger.info(f"Seeded {occ_created} occupancy records and {sec_created} security events for {facility_id}.")
    return occ_created, sec_created