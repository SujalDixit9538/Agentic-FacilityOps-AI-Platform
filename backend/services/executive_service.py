import logging
from sqlalchemy.orm import Session
from backend.agents.executive.agent import ExecutiveAgent

logger = logging.getLogger(__name__)

class ExecutiveService:
    """
    Business logic layer for the Platform Executive Module.
    """
    def __init__(self, db: Session):
        self.db = db

    def run_platform_analysis(self, facility_id: str):
        """Triggers the Executive Agent to synthesize cross-module intelligence."""
        logger.info(f"Triggering Executive Agent analysis for facility: {facility_id}")
        agent = ExecutiveAgent(self.db)
        return agent.generate_executive_summary(facility_id)