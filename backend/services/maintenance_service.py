from sqlalchemy.orm import Session
from backend.agents.maintenance.agent import MaintenanceAgent
from backend.repositories.maintenance_repository import MaintenanceRepository
from backend.schemas.maintenance import AssetBase, MaintenanceLogBase
import logging

logger = logging.getLogger(__name__)

class MaintenanceService:
    """
    Business logic layer for the Predictive Maintenance Module.
    """
    def __init__(self, db: Session):
        self.repository = MaintenanceRepository(db)

    def get_facility_assets(self, facility_id: str):
        """Retrieves all registered assets for a specific facility."""
        logger.debug(f"Fetching assets for facility: {facility_id}")
        return self.repository.get_assets_by_facility(facility_id)

    def register_new_asset(self, asset_data: AssetBase):
        """Registers a new physical asset into the system."""
        logger.info(f"Registering new asset of type {asset_data.asset_type} for facility: {asset_data.facility_id}")
        return self.repository.create_asset(asset_data)

    def get_asset_maintenance_history(self, asset_id: str, limit: int = 50):
        """Retrieves the maintenance log history for a specific asset."""
        logger.debug(f"Fetching maintenance history for asset: {asset_id}")
        return self.repository.get_logs_by_asset(asset_id, limit)

    def log_maintenance_event(self, log_data: MaintenanceLogBase):
        """Records a maintenance event (repair, inspection, failure)."""
        logger.info(f"Logging maintenance event for asset: {log_data.asset_id}")
        return self.repository.create_maintenance_log(log_data)

    def run_agent_analysis(self, asset_id: str): # <-- NEW METHOD
        """Triggers the Maintenance Agent to analyze specific equipment."""
        agent = MaintenanceAgent(self.repository.db)
        return agent.analyze_asset(asset_id)

    def generate_work_order(self, asset_id: str):
        """Triggers the Maintenance Agent to generate a work order."""
        agent = MaintenanceAgent(self.repository.db)
        return agent.generate_work_order(asset_id)

    def get_module_status(self):
        """Returns the operational status of the Maintenance module."""
        return {
            "status": "operational",
            "intelligence_engine": "rules_based_active"
        }