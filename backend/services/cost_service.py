from sqlalchemy.orm import Session
from backend.repositories.cost_repository import CostRepository
from backend.schemas.cost import CostRecordBase
import logging

logger = logging.getLogger(__name__)

class CostService:
    """
    Business logic layer for the Cost Optimization Module.
    """
    def __init__(self, db: Session):
        self.repository = CostRepository(db)

    def get_facility_costs(self, facility_id: str, limit: int = 100):
        """Retrieves general cost records for a specific facility."""
        logger.debug(f"Fetching cost records for facility: {facility_id}")
        return self.repository.get_costs_by_facility(facility_id, limit)

    def log_facility_cost(self, cost_data: CostRecordBase):
        """Records a new facility expense."""
        logger.info(f"Logging new {cost_data.category} cost for facility: {cost_data.facility_id}")
        return self.repository.create_cost_record(cost_data)

    def get_module_status(self):
        """Returns the operational status of the Cost module."""
        return {
            "status": "operational",
            "intelligence_engine": "pending_initialization"
        }