from sqlalchemy.orm import Session
from backend.database.models.energy import EnergyRecord
from backend.schemas.energy import EnergyRecordBase
import uuid
import datetime

class EnergyRepository:
    """
    Handles all database operations for Energy records.
    Enforces Blueprint Rule: Repositories perform only CRUD and Queries.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_records_by_facility(self, facility_id: str, limit: int = 100):
        return self.db.query(EnergyRecord).filter(
            EnergyRecord.facility_id == facility_id
        ).order_by(EnergyRecord.timestamp.desc()).limit(limit).all()

    def create_record(self, record_data: EnergyRecordBase):
        db_record = EnergyRecord(
            record_id=f"ENG-{uuid.uuid4().hex[:8]}",
            facility_id=record_data.facility_id,
            timestamp=record_data.timestamp or datetime.datetime.utcnow(),
            energy_kwh=record_data.energy_kwh,
            peak_demand_kw=record_data.peak_demand_kw,
            cost=record_data.cost
        )
        self.db.add(db_record)
        self.db.commit()
        self.db.refresh(db_record)
        return db_record