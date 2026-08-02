from sqlalchemy.orm import Session
from backend.repositories.occupancy_repository import OccupancyRepository
from backend.schemas.occupancy import OccupancyBase, SecurityEventBase
import logging

logger = logging.getLogger(__name__)

class OccupancyService:
    """
    Business logic layer for the Occupancy and Security Module.
    """
    def __init__(self, db: Session):
        self.repository = OccupancyRepository(db)

    def get_facility_occupancy(self, facility_id: str, limit: int = 100):
        """Retrieves recent occupancy tracking records for a facility."""
        logger.debug(f"Fetching occupancy data for {facility_id}")
        return self.repository.get_latest_occupancy(facility_id, limit)

    def log_occupancy(self, data: OccupancyBase):
        """Records a new room/floor occupancy headcount."""
        return self.repository.create_occupancy_record(data)

    def get_security_logs(self, facility_id: str, limit: int = 50):
        """Retrieves historical security events for a facility."""
        logger.debug(f"Fetching security logs for {facility_id}")
        return self.repository.get_security_events(facility_id, limit)

    def log_security_event(self, data: SecurityEventBase):
        """Records a new security incident or violation."""
        logger.info(f"Logging security event ({data.event_type}) for {data.facility_id}")
        return self.repository.create_security_event(data)

    def get_module_status(self):
        """Returns the operational status of the Occupancy & Security module."""
        return {
            "status": "operational",
            "intelligence_engine": "pending_initialization"
        }