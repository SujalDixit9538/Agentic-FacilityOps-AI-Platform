import random
import numpy as np
import pandas as pd
import datetime
import logging
from sqlalchemy.orm import Session
from backend.repositories.occupancy_repository import OccupancyRepository
from backend.services.occupancy_zone_generator import generate_zones_for_facility
from backend.schemas.occupancy import OccupancyRecordBase, SecurityEventBase
from backend.database.models.occupancy import OccupancyRecord, SecurityEvent
import uuid

logger = logging.getLogger(__name__)

# Correlated security issue profiles: (event_type, severity, zone_level_choices, zone_weights, failed_attempts_range)
SECURITY_ISSUE_PROFILES = [
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


def _resolve_facility_row(facility_id: str):
    """Looks up a facility's type/area/floors from the real dataset.
    Falls back to a reasonable default only if the id or file is missing,
    so seeding never hard-crashes on an unexpected facility_id."""
    try:
        facilities_df = pd.read_csv("data/processed_facilities.csv")
        match = facilities_df[facilities_df["facility_id"] == facility_id]
        if not match.empty:
            row = match.iloc[0]
            return str(row["facility_type"]), float(row["total_area_sqft"]), int(row["total_floors"])
    except FileNotFoundError:
        pass
    logger.warning(f"No facility row found for {facility_id}; using default zone template.")
    return "Office", 50000.0, 3


def seed_mock_occupancy_data(db: Session, facility_id: str, days: int = 7):
    """
    Generates a real per-facility zone layout (if not already present), then
    realistic historical occupancy headcounts and correlated security events.
    """
    repo = OccupancyRepository(db)

    # 1. Ensure zones exist for this facility (dynamic, type/area-aware generation)
    zones = repo.get_zones_for_facility(facility_id)
    if not zones:
        facility_type, total_area_sqft, total_floors = _resolve_facility_row(facility_id)
        zones_to_create = generate_zones_for_facility(
            facility_id=facility_id,
            facility_type=facility_type,
            total_area_sqft=total_area_sqft,
            total_floors=total_floors,
        )
        db.add_all(zones_to_create)
        db.flush()
        zones = zones_to_create
        logger.info(f"Generated {len(zones)} zones for {facility_id}.")

    # 2. Idempotency check — don't re-seed if occupancy data already exists
    if repo.get_latest_occupancy_by_zone(facility_id):
        logger.info(f"Occupancy data already exists for {facility_id}. Skipping seed.")
        return 0, 0

    logger.info(f"Seeding occupancy and security data for {facility_id} over {days} days...")
    base_time = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    occ_created = 0
    sec_created = 0

    # 3. Generate deterministic time-series occupancy for the requested window.
    random.seed(42)
    base_time = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    occ_created = 0
    meeting_room_zones = [zone for zone in zones if zone.zone_type == "meeting_room"]

    for i in range(days * 24):
        current_time = base_time + datetime.timedelta(hours=i)
        hour = current_time.hour
        is_working_hours = 8 <= hour <= 18

        for zone in zones:
            if zone.zone_type == "server_room":
                count = random.randint(0, 2)
            elif is_working_hours:
                count = random.randint(int(zone.max_capacity * 0.2), int(zone.max_capacity * 0.8))
            else:
                count = random.randint(0, max(int(zone.max_capacity * 0.05), 1))

            # Demo Scenarios
            if i == (days * 24 - 1):
                if zone.zone_type == "office_floor":
                    count = int(zone.max_capacity * 0.82)
                elif meeting_room_zones and zone is meeting_room_zones[0]:
                    count = max(zone.max_capacity + 1, int(zone.max_capacity * 1.05))
                elif len(meeting_room_zones) > 1 and zone is meeting_room_zones[1]:
                    count = int(zone.max_capacity * 0.25)

            record_data = OccupancyRecordBase(
                facility_id=facility_id,
                zone_id=zone.zone_id,
                occupancy_count=max(0, count),
                source="demo_sensor",
                timestamp=current_time,
            )
            db.add(OccupancyRecord(occupancy_id=f"OCC-{uuid.uuid4().hex[:12].upper()}", **record_data.model_dump()))
            occ_created += 1

    # 4. Generate Correlated Security Events — scales with `days`, not a flat count
    num_events = max(3, random.randint(int(days * 0.5), int(days * 1.5)))
    for _ in range(num_events):
        event_time = base_time + datetime.timedelta(hours=random.randint(0, days * 24))
        issue, severity, zone_level, recent_failed_attempts = _generate_security_event()

        sec_data = SecurityEventBase(
            facility_id=facility_id,
            event_type=issue,
            severity=severity,
            event_time=event_time,
            status=random.choice(["Open", "Investigating", "Closed"]),
            zone_level=zone_level,
            recent_failed_attempts=recent_failed_attempts,
        )
        db.add(SecurityEvent(event_id=f"SEC-{uuid.uuid4().hex[:12].upper()}", **sec_data.model_dump()))
        sec_created += 1

    logger.info(f"Seeded {occ_created} occupancy records and {sec_created} security events for {facility_id}.")
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return occ_created, sec_created