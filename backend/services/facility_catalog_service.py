from datetime import datetime
from pathlib import Path
from typing import Iterable
import csv

from sqlalchemy.orm import Session

from backend.database.models.facility import Facility


class FacilityCatalogService:
    """Owns canonical facility identity and metadata."""

    def __init__(self, db: Session):
        self.db = db

    def list_active(self) -> list[Facility]:
        """Return active facilities, bootstrapping only the identity catalog when empty.

        This keeps the canonical catalog as the source used by the UI while making a
        fresh/demo database immediately usable when the repository's processed
        facility catalog is present. No operational measurements are generated here.
        """
        facilities = (
            self.db.query(Facility)
            .filter(Facility.is_active.is_(True))
            .order_by(Facility.facility_id)
            .all()
        )
        if facilities:
            return facilities

        catalog_path = Path("data/processed_facilities.csv")
        if not catalog_path.exists():
            return []

        facility_ids: list[str] = []
        try:
            with catalog_path.open("r", encoding="utf-8-sig", newline="") as handle:
                for row in csv.DictReader(handle):
                    facility_id = (row.get("facility_id") or "").strip()
                    if facility_id:
                        facility_ids.append(facility_id)
        except (OSError, csv.Error):
            return []

        if not facility_ids:
            return []

        facilities = self.ensure_many(facility_ids)
        return sorted(facilities, key=lambda facility: facility.facility_id)

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
