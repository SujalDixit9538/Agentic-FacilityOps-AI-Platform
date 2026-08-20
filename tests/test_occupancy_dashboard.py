import pytest
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from backend.database.base import Base
from backend.database.models.occupancy import OccupancyZone, OccupancyRecord
from backend.services.occupancy_service import OccupancyService
import datetime

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    return session

def test_dashboard_logic(db_session):
    # Setup zones
    zone1 = OccupancyZone(zone_id="Z1", facility_id="F1", floor=1, zone_name="Meeting Room A", zone_type="meeting_room", max_capacity=20)
    zone2 = OccupancyZone(zone_id="Z2", facility_id="F1", floor=1, zone_name="Meeting Room B", zone_type="meeting_room", max_capacity=20)
    zone3 = OccupancyZone(zone_id="Z3", facility_id="F1", floor=1, zone_name="Lobby", zone_type="lobby", max_capacity=10)
    
    db_session.add_all([zone1, zone2, zone3])
    db_session.commit()
    
    # Setup records
    # Test 1: 20/20 -> 100% (Overcrowded)
    # Test 2: 21/20 -> 105% (Overcrowded, High Alert)
    # Test 3: 5/10 -> 50% (Normal)
    
    records = [
        OccupancyRecord(occupancy_id="R1", facility_id="F1", zone_id="Z1", occupancy_count=20, timestamp=datetime.datetime.utcnow()),
        OccupancyRecord(occupancy_id="R2", facility_id="F1", zone_id="Z2", occupancy_count=21, timestamp=datetime.datetime.utcnow()),
        OccupancyRecord(occupancy_id="R3", facility_id="F1", zone_id="Z3", occupancy_count=5, timestamp=datetime.datetime.utcnow()),
    ]
    db_session.add_all(records)
    db_session.commit()
    
    service = OccupancyService(db_session)
    data = service.get_dashboard_data("F1")
    
    # Verify zone Z1
    z1 = next(z for z in data['zones'] if z['zone_id'] == 'Z1')
    assert z1['status'] == "OVERCROWDED"
    assert z1['utilization_percent'] == 100.0
    
    # Verify zone Z2
    z2 = next(z for z in data['zones'] if z['zone_id'] == 'Z2')
    assert z2['status'] == "OVERCROWDED"
    assert z2['utilization_percent'] == 105.0
    
    # Verify alert
    assert any(a['zone_id'] == 'Z2' for a in data['alerts'])
    
    # Verify summary
    assert data['summary']['total_occupants'] == 46
    assert data['summary']['overcrowded_zones'] == 2
    assert data['summary']['highly_utilized_zones'] == 0
    assert data['room_utilization']
    assert data['zone_analytics']
    assert data['trend']
    assert all("utilization_percent" in point for point in data['trend'])
