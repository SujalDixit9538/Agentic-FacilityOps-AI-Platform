from sqlalchemy.orm import Session
from backend.repositories.energy_repository import EnergyRepository
from backend.schemas.energy import EnergyRecordBase
import logging

logger = logging.getLogger(__name__)

class EnergyService:
    """
    Business logic layer for the Energy Module.
    Keeps the API router clean and decoupled from database operations.
    """
    def __init__(self, db: Session):
        self.repository = EnergyRepository(db)

    def get_facility_energy_history(self, facility_id: str, limit: int = 100):
        """Retrieves energy records for a specific facility."""
        logger.debug(f"Fetching energy history for facility: {facility_id}")
        return self.repository.get_records_by_facility(facility_id, limit)

    def log_energy_usage(self, record_data: EnergyRecordBase):
        """Logs a new energy usage record."""
        logger.info(f"Logging new energy usage for facility: {record_data.facility_id}")
        return self.repository.create_record(record_data)
        
    def get_module_status(self):
        """Returns the operational status of the Energy module."""
        # In the future, this will check if ML models are loaded and agent is ready
        return {
            "status": "operational",
            "intelligence_engine": "pending_initialization" 
        }