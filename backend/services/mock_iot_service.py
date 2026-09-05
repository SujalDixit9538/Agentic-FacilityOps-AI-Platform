from datetime import datetime, timedelta
import random
import logging
from sqlalchemy.orm import Session
from backend.repositories.energy_repository import EnergyRepository
from backend.schemas.energy import EnergyRecordBase
from backend.database.models.energy import EnergyRecord
import uuid

logger = logging.getLogger(__name__)

def seed_mock_energy_data(db: Session, facility_id: str, days: int = 7):
    """
    Generates realistic historical energy consumption records and persists them 
    via the EnergyRepository. Satisfies ETP-007 requirements.
    """
    repository = EnergyRepository(db)
    
    # Check if records already exist to prevent redundant seeding
    existing = repository.get_records_by_facility(facility_id, limit=1)
    if existing:
        logger.info(f"Mock data already exists for facility {facility_id}. Skipping seed.")
        return 0

    logger.info(f"Seeding mock energy data for facility {facility_id} over {days} days...")
    
    base_time = datetime.utcnow() - timedelta(days=days)
    records_created = 0
    
    # Generate hourly data points over the specified timeframe
    total_hours = days * 24
    for i in range(total_hours):
        current_time = base_time + timedelta(hours=i)
        
        # Simulate realistic daily consumption curves (higher during day, lower at night)
        hour = current_time.hour
        base_load = 50.0 if 8 <= hour <= 18 else 20.0
        noise = random.uniform(-5.0, 15.0)
        energy_kwh = max(10.0, base_load + noise)
        
        peak_demand_kw = energy_kwh * random.uniform(1.1, 1.3)
        cost = energy_kwh * 0.12  # Estimated utility rate per kWh

        records_created += 1
        db.add(EnergyRecord(
            record_id=f"ENG-{uuid.uuid4().hex[:12].upper()}",
            facility_id=facility_id,
            timestamp=current_time,
            energy_kwh=round(energy_kwh, 2),
            peak_demand_kw=round(peak_demand_kw, 2),
            cost=round(cost, 2),
        ))

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    logger.info(f"Successfully seeded {records_created} energy records for {facility_id}.")
    return records_created