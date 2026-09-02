from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database.models.energy import EnergyRecord
from backend.database.models.maintenance import Asset
from backend.database.models.occupancy import OccupancyRecord, OccupancyZone


class FacilityStateService:
    """Builds the latest correlated state shared by domain agents."""

    def __init__(self, db: Session):
        self.db = db

    def get_facility_state(self, facility_id: str, as_of: Optional[datetime] = None) -> Dict[str, Any]:
        as_of = as_of or datetime.now(timezone.utc).replace(tzinfo=None)
        quality = []

        energy = (
            self.db.query(EnergyRecord)
            .filter(EnergyRecord.facility_id == facility_id, EnergyRecord.timestamp <= as_of)
            .order_by(EnergyRecord.timestamp.desc())
            .first()
        )
        zones = self.db.query(OccupancyZone).filter(OccupancyZone.facility_id == facility_id).all()
        latest_occupancy = (
            self.db.query(
                OccupancyRecord.zone_id,
                OccupancyRecord.occupancy_count,
                OccupancyRecord.timestamp,
                func.row_number().over(
                    partition_by=OccupancyRecord.zone_id,
                    order_by=(OccupancyRecord.timestamp.desc(), OccupancyRecord.occupancy_id.desc()),
                ).label("row_number"),
            )
            .filter(OccupancyRecord.facility_id == facility_id, OccupancyRecord.timestamp <= as_of)
            .subquery()
        )
        occupancy_rows = self.db.query(latest_occupancy).filter(latest_occupancy.c.row_number == 1).all()
        assets = self.db.query(Asset).filter(Asset.facility_id == facility_id).all()

        energy_load = energy.peak_demand_kw if energy and energy.peak_demand_kw is not None else None
        if energy_load is None and energy:
            energy_load = energy.energy_kwh
        if energy_load is None:
            quality.append("energy_load_unavailable")

        capacity = sum(zone.max_capacity or 0 for zone in zones)
        occupancy_pct = None
        occupancy_timestamp = None
        if occupancy_rows and capacity > 0:
            occupancy_pct = round((sum(row.occupancy_count or 0 for row in occupancy_rows) / capacity) * 100, 2)
            occupancy_timestamp = max(row.timestamp for row in occupancy_rows)
        elif not zones:
            quality.append("occupancy_capacity_unavailable")
        else:
            quality.append("occupancy_reading_unavailable")
            occupancy_timestamp = None

        asset_health = None
        if assets:
            health_values = {"Operational": 100.0, "Under Maintenance": 50.0, "Decommissioned": 0.0}
            asset_health = round(
                sum(health_values.get(asset.status, 50.0) for asset in assets) / len(assets), 2
            )
        else:
            quality.append("asset_health_unavailable")

        return {
            "facility_id": facility_id,
            "as_of": as_of.isoformat() + "Z",
            "energy_load": energy_load,
            "asset_health": asset_health,
            "occupancy_pct": occupancy_pct,
            "energy_timestamp": energy.timestamp.isoformat() if energy else None,
            "occupancy_timestamp": occupancy_timestamp.isoformat() if occupancy_timestamp else None,
            "asset_count": len(assets),
            "occupancy_capacity": capacity,
            "quality_flags": quality,
            "is_complete": not quality,
            "provenance": {"source": "facility_state_service", "facility_id": facility_id},
            "freshness": {
                "status": "available" if not quality else "degraded",
                "as_of": as_of.isoformat() + "Z",
            },
            "degraded": bool(quality),
        }