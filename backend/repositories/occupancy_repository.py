from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database.models.occupancy import OccupancyRecord, SecurityEvent, OccupancyZone, OccupancyImage
from backend.schemas.occupancy import OccupancyRecordBase, SecurityEventBase, OccupancyImageBase
import uuid

class OccupancyRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_latest_occupancy(self, facility_id: str, limit: int = 100):
        return self.db.query(OccupancyRecord).filter(
            OccupancyRecord.facility_id == facility_id
        ).order_by(OccupancyRecord.timestamp.desc()).limit(limit).all()

    def get_latest_occupancy_by_zone(self, facility_id: str):
        subq = self.db.query(
            OccupancyRecord.zone_id,
            func.max(OccupancyRecord.timestamp).label("max_ts")
        ).filter(OccupancyRecord.facility_id == facility_id).group_by(OccupancyRecord.zone_id).subquery()

        return self.db.query(OccupancyRecord).join(
            subq,
            (OccupancyRecord.zone_id == subq.c.zone_id) &
            (OccupancyRecord.timestamp == subq.c.max_ts)
        ).all()

    def create_occupancy_record(self, data: OccupancyRecordBase):
        db_record = OccupancyRecord(
            occupancy_id=f"OCC-{uuid.uuid4().hex[:12].upper()}",
            **data.model_dump()
        )
        self.db.add(db_record)
        self.db.commit()
        self.db.refresh(db_record)
        return db_record

    def get_zones_for_facility(self, facility_id: str):
        return self.db.query(OccupancyZone).filter(OccupancyZone.facility_id == facility_id).all()

    def get_zone(self, zone_id: str):
        return self.db.query(OccupancyZone).filter(OccupancyZone.zone_id == zone_id).first()

    def create_zone(self, zone: OccupancyZone):
        self.db.add(zone)
        self.db.commit()
        self.db.refresh(zone)
        return zone

    def bulk_create_zones(self, zones: list[OccupancyZone]):
        self.db.add_all(zones)
        self.db.commit()
        return zones

    def create_image_record(self, data: OccupancyImageBase):
        db_img = OccupancyImage(
            image_id=f"IMG-{uuid.uuid4().hex[:12].upper()}",
            **data.model_dump()
        )
        self.db.add(db_img)
        self.db.commit()
        self.db.refresh(db_img)
        return db_img

    def get_security_events(self, facility_id: str, limit: int = 50):
        return self.db.query(SecurityEvent).filter(
            SecurityEvent.facility_id == facility_id
        ).order_by(SecurityEvent.event_time.desc()).limit(limit).all()

    def create_security_event(self, data: SecurityEventBase):
        db_event = SecurityEvent(
            event_id=f"SEC-{uuid.uuid4().hex[:8].upper()}",
            **data.model_dump()
        )
        self.db.add(db_event)
        self.db.commit()
        self.db.refresh(db_event)
        return db_event