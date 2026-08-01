from sqlalchemy.orm import Session
from backend.repositories.energy_repository import EnergyRepository
from backend.schemas.energy import EnergyRecordBase
from backend.agents.energy.agent import EnergyAgent  
import logging

logger = logging.getLogger(__name__)

class EnergyService:
    def __init__(self, db: Session):
        self.repository = EnergyRepository(db)

    def get_facility_energy_history(self, facility_id: str, limit: int = 100):
        return self.repository.get_records_by_facility(facility_id, limit)

    def log_energy_usage(self, record_data: EnergyRecordBase):
        return self.repository.create_record(record_data)
        
    def run_agent_analysis(self, facility_id: str, days: int = 7): 
        """Triggers the Energy Agent to analyze facility data."""
        agent = EnergyAgent(self.repository.db)
        return agent.analyze_facility(facility_id, days)

    def get_module_status(self):
        """Returns the operational status of the Energy module."""
        return {
            "status": "operational",
            "intelligence_engine": "rules_based_active" 
        }