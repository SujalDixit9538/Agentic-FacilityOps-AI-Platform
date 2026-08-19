
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database.models.occupancy import OccupancyZone, OccupancyRecord
from backend.services.mock_occupancy_service import seed_mock_occupancy_data
from config.settings import settings
import sys

# Initialize DB
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("--- RUNTIME SEED ---")
try:
    # 1. Run seed
    seed_mock_occupancy_data(db, 'FAC-001', 1)
    print("PASS")
    
    # 2. Verify Zones
    print("\n--- ZONE VERIFICATION ---")
    zones = db.query(OccupancyZone).all()
    # Required: Office Floor, Meeting Room A, Meeting Room B, Common Area, Parking
    expected_zones = {
        "Office Floor": 100,
        "Meeting Room A": 10,
        "Meeting Room B": 20,
        "Common Area": 50,
        "Parking": 100
    }
    
    for zone in zones:
        capacity = zone.max_capacity
        exists = zone.zone_name in expected_zones
        print(f"| {zone.zone_name} | {zone.zone_id} | {capacity} | {exists} |")
        
    # 3. Verify latest records
    print("\n--- OCCUPANCY VERIFICATION ---")
    # Latest records
    records = db.query(OccupancyRecord).order_by(OccupancyRecord.timestamp.desc()).limit(5).all()
    for rec in records:
        zone = db.query(OccupancyZone).filter(OccupancyZone.zone_id == rec.zone_id).first()
        valid = zone is not None
        print(f"| {zone.zone_name if zone else 'Unknown'} | {rec.occupancy_count} | {valid} |")

    # 4. Duplicate Test
    print("\n--- DUPLICATE TEST ---")
    count_before = db.query(OccupancyZone).count()
    seed_mock_occupancy_data(db, 'FAC-001', 1)
    count_after = db.query(OccupancyZone).count()
    if count_before == count_after:
        print("PASS")
    else:
        print(f"FAIL: {count_before} -> {count_after}")

except Exception as e:
    print(f"\n--- ISSUES ---")
    print(f"Error: {e}")
    sys.exit(1)
finally:
    db.close()
