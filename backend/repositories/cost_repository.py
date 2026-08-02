from sqlalchemy.orm import Session
from backend.database.models.cost import CostRecord
from backend.schemas.cost import CostRecordBase
import uuid

class CostRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_costs_by_facility(self, facility_id: str, limit: int = 100):
        return self.db.query(CostRecord).filter(
            CostRecord.facility_id == facility_id
        ).order_by(CostRecord.incurred_date.desc()).limit(limit).all()

    def get_costs_by_category(self, facility_id: str, category: str, limit: int = 100):
        return self.db.query(CostRecord).filter(
            CostRecord.facility_id == facility_id,
            CostRecord.category == category
        ).order_by(CostRecord.incurred_date.desc()).limit(limit).all()

    def create_cost_record(self, data: CostRecordBase):
        db_record = CostRecord(
            record_id=f"CST-{uuid.uuid4().hex[:6].upper()}",
            **data.model_dump()
        )
        self.db.add(db_record)
        self.db.commit()
        self.db.refresh(db_record)
        return db_record