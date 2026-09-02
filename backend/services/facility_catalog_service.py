from datetime import datetime
from typing import Iterable

from sqlalchemy.orm import Session

from backend.database.models.facility import Facility


class FacilityCatalogService:
    """Owns canonical facility identity and metadata."""

    def __init__(self, db: Session):
        self.db = db

    def list_active(self) -> list[Facility]:
        return (
            self.db.query(Facility)
            .filter(Facility.is_active.is_(True))
            .order_by(Facility.facility_id)
            .all()
        )

    def ensure(self, facility_id: str, **values) -> Facility:
        facility = self.db.get(Facility, facility_id)
        if facility is None:
            facility = Facility(
                facility_id=facility_id,
                name=values.get("name", facility_id),
                facility_type=values.get("facility_type"),
                total_area_sqft=values.get("total_area_sqft"),
                total_floors=values.get("total_floors"),
                created_at=values.get("created_at", datetime.utcnow()),
            )
            self.db.add(facility)
        return facility

    def ensure_many(self, facility_ids: Iterable[str]) -> list[Facility]:
        facilities = [self.ensure(facility_id) for facility_id in dict.fromkeys(facility_ids) if facility_id]
        self.db.commit()
        return facilities
