import random
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from backend.repositories.maintenance_repository import MaintenanceRepository
from backend.schemas.maintenance import AssetBase, MaintenanceLogBase

logger = logging.getLogger(__name__)

def seed_mock_maintenance_data(db: Session, facility_id: str = "FAC-001"):
    """
    Generates realistic assets and historical maintenance logs.
    Satisfies ETP-011 data ingestion requirements.
    """
    repository = MaintenanceRepository(db)
    
    # Check if assets already exist
    existing_assets = repository.get_assets_by_facility(facility_id)
    if existing_assets:
        logger.info(f"Mock maintenance data already exists for {facility_id}. Skipping seed.")
        return 0, 0

    logger.info(f"Seeding mock maintenance data for {facility_id}...")
    
    # 1. Define standard equipment to seed
    equipment_templates = [
        {"type": "HVAC Unit (Rooftop)", "age_days": 1200},
        {"type": "Industrial Motor (Pump A)", "age_days": 800},
        {"type": "Chiller System", "age_days": 1500},
        {"type": "Backup Generator", "age_days": 500}
    ]
    
    assets_created = 0
    logs_created = 0
    
    # 2. Generate Assets and their Logs
    for equip in equipment_templates:
        install_date = datetime.utcnow() - timedelta(days=equip["age_days"])
        
        # Create the Asset
        asset_data = AssetBase(
            facility_id=facility_id,
            asset_type=equip["type"],
            installation_date=install_date,
            status="Operational"
        )
        db_asset = repository.create_asset(asset_data)
        assets_created += 1
        
        # Generate 3 to 6 historical events so wear can accumulate over time.
        num_logs = random.randint(2, 5)
        event_offsets = sorted(
            random.sample(range(10, equip["age_days"] - 10), num_logs),
            reverse=True
        )
        asset_profile = {
            "air_temp_base": random.uniform(295.0, 305.0),
            "process_temp_base": random.uniform(305.0, 315.0),
            "speed_base": random.uniform(1350.0, 1700.0),
            "torque_base": random.uniform(32.0, 48.0),
            "wear_step": random.uniform(35.0, 60.0),
            "wear_start": random.uniform(0.0, 12.0),
        }

        for log_index, days_ago in enumerate(event_offsets):
            event_date = datetime.utcnow() - timedelta(days=days_ago)
            
            issues = ["Filter Replacement", "Vibration Anomaly", "Calibration", "Lubrication", "Part Failure"]
            issue_selected = random.choice(issues)
            
            # Minor issues cost less, failures cost more
            cost = random.uniform(50.0, 300.0) if issue_selected != "Part Failure" else random.uniform(1000.0, 5000.0)

            wear = asset_profile["wear_start"] + (log_index * asset_profile["wear_step"]) + random.uniform(0.0, 18.0)
            strain = min(wear / 220.0, 1.4)
            torque = asset_profile["torque_base"] + (strain * random.uniform(4.0, 8.0)) + random.uniform(-2.0, 2.0)
            speed = asset_profile["speed_base"] - (strain * random.uniform(80.0, 180.0)) + random.uniform(-45.0, 45.0)
            air_temp = asset_profile["air_temp_base"] + random.uniform(-1.8, 1.8)
            process_temp = asset_profile["process_temp_base"] + (strain * random.uniform(1.5, 4.5)) + random.uniform(-1.2, 1.2)
            
            log_data = MaintenanceLogBase(
                asset_id=db_asset.asset_id,
                issue=issue_selected,
                maintenance_date=event_date,
                technician=random.choice(["Tech A. Smith", "Tech B. Jones", "Ext. Contractor"]),
                status="Completed",
                cost=round(cost, 2),
                air_temp=round(max(292.0, min(308.0, air_temp)), 2),
                process_temp=round(max(302.0, min(320.0, process_temp)), 2),
                speed=round(max(1200.0, min(1800.0, speed)), 2),
                torque=round(max(30.0, min(55.0, torque)), 2),
                wear=round(wear, 2)
            )
            repository.create_maintenance_log(log_data)
            logs_created += 1

    logger.info(f"Seeded {assets_created} assets and {logs_created} maintenance logs for {facility_id}.")
    return assets_created, logs_created
