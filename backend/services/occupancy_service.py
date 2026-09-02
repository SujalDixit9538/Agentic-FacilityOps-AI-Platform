from sqlalchemy.orm import Session
from backend.agents.occupancy.agent import OccupancyAgent
from backend.repositories.occupancy_repository import OccupancyRepository
from backend.schemas.occupancy import OccupancyRecordBase, SecurityEventBase, OccupancyImageBase
from backend.agents.occupancy.config import OCCUPANCY_RULES
import logging

logger = logging.getLogger(__name__)

class OccupancyService:
    def __init__(self, db: Session):
        self.repository = OccupancyRepository(db)

    def get_facility_occupancy(self, facility_id: str, limit: int = 100):
        return self.repository.get_latest_occupancy(facility_id, limit)

    def log_occupancy(self, data: OccupancyRecordBase):
        return self.repository.create_occupancy_record(data)

    def get_zones(self, facility_id: str):
        return self.repository.get_zones_for_facility(facility_id)

    def get_zone_utilization(self, facility_id: str):
        zones = {z.zone_id: z for z in self.repository.get_zones_for_facility(facility_id)}
        latest_records = self.repository.get_latest_occupancy_by_zone(facility_id)

        utilization_by_type = {}
        for record in latest_records:
            zone = zones.get(record.zone_id)
            if zone and zone.max_capacity > 0:
                util_pct = (record.occupancy_count / zone.max_capacity) * 100
                utilization_by_type.setdefault(zone.zone_type, []).append(util_pct)

        return {
            z_type: round(sum(pcts) / len(pcts), 1)
            for z_type, pcts in utilization_by_type.items()
        }

    def log_image_detection(self, data: OccupancyImageBase):
        img = self.repository.create_image_record(data)
        rec_data = OccupancyRecordBase(
            facility_id=data.facility_id,
            zone_id=data.zone_id,
            occupancy_count=data.detected_count or 0,
            source="cnn",
            timestamp=data.captured_at
        )
        self.repository.create_occupancy_record(rec_data)
        return img

    def get_security_logs(self, facility_id: str, limit: int = 50):
        return self.repository.get_security_events(facility_id, limit)

    def get_occupancy_history(self, facility_id: str, days: int = 30):
        import datetime
        from sqlalchemy import func
        from backend.database.models.occupancy import OccupancyRecord
        limit_date = datetime.datetime.now() - datetime.timedelta(days=days)

        # Get historical average occupancy per day
        records = self.repository.db.query(
            func.date(OccupancyRecord.timestamp).label("date"),
            func.sum(OccupancyRecord.occupancy_count).label("total_occ")
        ).filter(
            OccupancyRecord.facility_id == facility_id,
            OccupancyRecord.timestamp >= limit_date
        ).group_by(func.date(OccupancyRecord.timestamp)).order_by(func.date(OccupancyRecord.timestamp)).all()

        zones = self.repository.get_zones_for_facility(facility_id)
        total_capacity = sum(zone.max_capacity for zone in zones)
        return [
            {
                "timestamp": datetime.datetime.combine(
                    r.date if isinstance(r.date, datetime.date) else datetime.date.fromisoformat(r.date),
                    datetime.time.min,
                ),
                "occupancy": r.total_occ,
                "utilization_percent": round((r.total_occ / total_capacity * 100) if total_capacity > 0 else 0, 1),
            }
            for r in records
        ]

    def log_security_event(self, data: SecurityEventBase):
        return self.repository.create_security_event(data)

    def run_agent_analysis(self, facility_id: str):
        agent = OccupancyAgent(self.repository.db)
        return agent.analyze_facility(facility_id)

    def get_module_status(self):
        return {"status": "operational", "intelligence_engine": "rules_based_active"}

    def get_dashboard_data(self, facility_id: str):
        zones = self.repository.get_zones_for_facility(facility_id)
        latest_records = {r.zone_id: r for r in self.repository.get_latest_occupancy_by_zone(facility_id)}
        
        # Calculate summary
        total_occ = 0
        total_cap = 0
        overcrowded = 0
        highly = 0
        under = 0
        
        zone_info = []
        alerts = []
        zone_analytics = {}
        
        for zone in zones:
            record = latest_records.get(zone.zone_id)
            occ = record.occupancy_count if record else 0
            cap = zone.max_capacity
            util = (occ / cap * 100) if cap > 0 else 0

            # Status
            if util >= OCCUPANCY_RULES["OVERCROWDING_THRESHOLD_PCT"] * 100:
                status = "OVERCROWDED"
                overcrowded += 1
                alerts.append({
                    "alert_type": "OCCUPANCY",
                    "severity": "HIGH",
                    "zone_id": zone.zone_id,
                    "zone_name": zone.zone_name,
                    "message": f"{zone.zone_name} is at capacity.",
                    "utilization_percent": round(util, 1)
                })
            elif util >= OCCUPANCY_RULES["HIGH_UTILIZATION_THRESHOLD_PCT"] * 100:
                status = "HIGHLY_UTILIZED"
                highly += 1
            elif util >= 40:
                status = "NORMAL"
            else:
                status = "UNDERUTILIZED"
                under += 1
                
            zone_info.append({
                "zone_id": zone.zone_id,
                "zone_name": zone.zone_name,
                "zone_type": zone.zone_type,
                "floor": zone.floor,
                "occupancy": occ,
                "capacity": cap,
                "utilization_percent": round(util, 1),
                "status": status,
                "x_position": zone.x_position,
                "y_position": zone.y_position
            })

            zone_analytics.setdefault(zone.zone_type, {"occupancy": 0, "capacity": 0})
            zone_analytics[zone.zone_type]["occupancy"] += occ
            zone_analytics[zone.zone_type]["capacity"] += cap

            total_occ += occ
            total_cap += cap

        return {
            "facility_id": facility_id,
            "summary": {
                "total_occupants": total_occ,
                "total_capacity": total_cap,
                "utilization_percent": round((total_occ / total_cap * 100) if total_cap > 0 else 0, 1),
                "overcrowded_zones": overcrowded,
                "highly_utilized_zones": highly,
                "underutilized_zones": under
            },
            "zones": zone_info,
            "room_utilization": [
                z for z in zone_info if z["zone_type"] in {"meeting_room", "room"}
            ],
            "zone_analytics": [
                {
                    "zone_type": zone_type,
                    "occupancy": values["occupancy"],
                    "capacity": values["capacity"],
                    "utilization_percent": round(
                        values["occupancy"] / values["capacity"] * 100
                        if values["capacity"] > 0 else 0,
                        1,
                    ),
                }
                for zone_type, values in sorted(zone_analytics.items())
            ],
            "alerts": alerts,
            "trend": self.get_occupancy_history(facility_id)
        }
