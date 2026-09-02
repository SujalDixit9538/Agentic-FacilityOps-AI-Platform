import random
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from backend.repositories.cost_repository import CostRepository
from backend.schemas.cost import CostRecordBase
from backend.database.models.cost import CostRecord
import uuid

logger = logging.getLogger(__name__)

def seed_mock_cost_data(db: Session, facility_id: str = "FAC-001", months_back: int = 6):
    """
    Generates realistic historical cost records across Energy, Maintenance, and Operations.
    """
    repository = CostRepository(db)
    
    # Check if data already exists to prevent duplication
    existing = repository.get_costs_by_facility(facility_id, limit=1)
    if existing:
        logger.info(f"Cost data already exists for {facility_id}. Skipping seed.")
        return 0

    logger.info(f"Seeding cost data for {facility_id} over the last {months_back} months...")
    
    records_created = 0
    now = datetime.utcnow()
    
    # 1. Generate Monthly Recurring Costs (Energy & Operations)
    for i in range(months_back):
        billing_date = now - timedelta(days=(i * 30) + 15) # Roughly middle of the month
        
        # Energy Bills (High variance based on season)
        energy_cost = CostRecordBase(
            facility_id=facility_id,
            category="Energy",
            description=f"Monthly Utility Bill - {billing_date.strftime('%B %Y')}",
            amount=round(random.uniform(12000.0, 18000.0), 2),
            incurred_date=billing_date
        )
        db.add(CostRecord(record_id=f"CST-{uuid.uuid4().hex[:12].upper()}", **energy_cost.model_dump()))
        records_created += 1
        
        # Operational Fixed Costs (Low variance)
        ops_cost = CostRecordBase(
            facility_id=facility_id,
            category="Operations",
            description=f"Facility Management Services - {billing_date.strftime('%B %Y')}",
            amount=round(random.uniform(4000.0, 4500.0), 2),
            incurred_date=billing_date
        )
        db.add(CostRecord(record_id=f"CST-{uuid.uuid4().hex[:12].upper()}", **ops_cost.model_dump()))
        records_created += 1

    # 2. Generate Random Maintenance Events (Spiky costs)
    maintenance_issues = [
        ("HVAC Filter Replacement", 500.0, 1000.0),
        ("Elevator Annual Inspection", 2000.0, 3000.0),
        ("Emergency Plumbing Repair", 1500.0, 4500.0),
        ("Lighting Fixture Upgrade", 800.0, 1500.0),
        ("Chiller Compressor Overhaul", 8000.0, 15000.0)
    ]
    
    # Scatter 3 to 8 random maintenance expenses across the timeline
    for _ in range(random.randint(3, 8)):
        event_date = now - timedelta(days=random.randint(1, months_back * 30))
        issue, min_cost, max_cost = random.choice(maintenance_issues)
        
        maint_cost = CostRecordBase(
            facility_id=facility_id,
            category="Maintenance",
            description=f"Contractor Invoice: {issue}",
            amount=round(random.uniform(min_cost, max_cost), 2),
            incurred_date=event_date
        )
        db.add(CostRecord(record_id=f"CST-{uuid.uuid4().hex[:12].upper()}", **maint_cost.model_dump()))
        records_created += 1

    logger.info(f"Seeded {records_created} financial records for {facility_id}.")
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return records_created