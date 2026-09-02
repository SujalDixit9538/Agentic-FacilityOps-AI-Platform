from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.database.base import Base
from backend.database.models.facility import Facility
from backend.database.models.occupancy import OccupancyRecord, OccupancyZone
from backend.repositories.occupancy_repository import OccupancyRepository
from backend.services.facility_state_service import FacilityStateService


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_latest_occupancy_is_facility_scoped_and_one_row_per_zone():
    db = make_session()
    db.add_all([
        Facility(facility_id="F-1", name="One"),
        Facility(facility_id="F-2", name="Two"),
        OccupancyZone(zone_id="shared-zone", facility_id="F-1", floor=1, zone_name="One", zone_type="office", max_capacity=100),
        OccupancyZone(zone_id="shared-zone-2", facility_id="F-2", floor=1, zone_name="Two", zone_type="office", max_capacity=100),
    ])
    now = datetime(2026, 1, 1, 12)
    db.add_all([
        OccupancyRecord(occupancy_id="f1-old", facility_id="F-1", zone_id="shared-zone", occupancy_count=10, timestamp=now - timedelta(minutes=1)),
        OccupancyRecord(occupancy_id="f1-new", facility_id="F-1", zone_id="shared-zone", occupancy_count=20, timestamp=now),
        OccupancyRecord(occupancy_id="f2-new", facility_id="F-2", zone_id="shared-zone", occupancy_count=99, timestamp=now + timedelta(minutes=1)),
    ])
    db.commit()

    result = OccupancyRepository(db).get_latest_occupancy_by_zone("F-1")

    assert [(record.zone_id, record.occupancy_count) for record in result] == [("shared-zone", 20)]


def test_facility_state_aggregates_latest_reading_per_zone():
    db = make_session()
    db.add(Facility(facility_id="F-1", name="One"))
    db.add_all([
        OccupancyZone(zone_id="z1", facility_id="F-1", floor=1, zone_name="One", zone_type="office", max_capacity=100),
        OccupancyZone(zone_id="z2", facility_id="F-1", floor=1, zone_name="Two", zone_type="office", max_capacity=100),
    ])
    now = datetime(2026, 1, 1, 12)
    db.add_all([
        OccupancyRecord(occupancy_id="z1-old", facility_id="F-1", zone_id="z1", occupancy_count=1, timestamp=now - timedelta(minutes=1)),
        OccupancyRecord(occupancy_id="z1-new", facility_id="F-1", zone_id="z1", occupancy_count=40, timestamp=now),
        OccupancyRecord(occupancy_id="z2-new", facility_id="F-1", zone_id="z2", occupancy_count=60, timestamp=now),
    ])
    db.commit()

    state = FacilityStateService(db).get_facility_state("F-1", as_of=now)

    assert state["occupancy_pct"] == 50.0
    assert "occupancy_reading_unavailable" not in state["quality_flags"]
    assert state["degraded"] is True
    assert state["provenance"]["facility_id"] == "F-1"