from sqlalchemy.orm import Session
from backend.database.models.occupancy import OccupancyRecord, SecurityEvent
from backend.schemas.occupancy import OccupancyBase, SecurityEventBase
import uuid

class OccupancyRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- Occupancy Methods ---
    def get_latest_occupancy(self, facility_id: str, limit: int = 100):
        return self.db.query(OccupancyRecord).filter(
            OccupancyRecord.facility_id == facility_id
        ).order_by(OccupancyRecord.timestamp.desc()).limit(limit).all()

    def create_occupancy_record(self, data: OccupancyBase):
        db_record = OccupancyRecord(
            occupancy_id=f"OCC-{uuid.uuid4().hex[:6].upper()}",
            **data.model_dump()
        )
        self.db.add(db_record)
        self.db.commit()
        self.db.refresh(db_record)
        return db_record

    # --- Security Methods ---
    def get_security_events(self, facility_id: str, limit: int = 50):
        return self.db.query(SecurityEvent).filter(
            SecurityEvent.facility_id == facility_id
        ).order_by(SecurityEvent.event_time.desc()).limit(limit).all()

    def create_security_event(self, data: SecurityEventBase):
        db_event = SecurityEvent(
            event_id=f"SEC-{uuid.uuid4().hex[:8].upper()}",
            facility_id=data.facility_id,
            event_type=data.event_type,
            severity=data.severity,
            event_time=data.event_time,
            status=data.status,
            zone_level=data.zone_level,
            recent_failed_attempts=data.recent_failed_attempts
        )
        self.db.add(db_event)
        self.db.commit()
        self.db.refresh(db_event)
        return db_event