from sqlalchemy.orm import Session
from backend.agents.occupancy.agent import OccupancyAgent
from backend.repositories.occupancy_repository import OccupancyRepository
from backend.schemas.occupancy import OccupancyRecordBase, SecurityEventBase, OccupancyImageBase
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

    def log_security_event(self, data: SecurityEventBase):
        return self.repository.create_security_event(data)

    def run_agent_analysis(self, facility_id: str):
        agent = OccupancyAgent(self.repository.db)
        return agent.analyze_facility(facility_id)

    def get_module_status(self):
        return {"status": "operational", "intelligence_engine": "rules_based_active"}