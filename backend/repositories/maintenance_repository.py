from sqlalchemy.orm import Session
from backend.database.models.maintenance import Asset, MaintenanceLog
from backend.schemas.maintenance import AssetBase, MaintenanceLogBase
import uuid

class MaintenanceRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- Asset Methods ---
    def get_assets_by_facility(self, facility_id: str):
        return self.db.query(Asset).filter(Asset.facility_id == facility_id).all()

    def create_asset(self, asset_data: AssetBase):
        db_asset = Asset(
            asset_id=f"AST-{uuid.uuid4().hex[:6].upper()}",
            **asset_data.model_dump()
        )
        self.db.add(db_asset)
        self.db.commit()
        self.db.refresh(db_asset)
        return db_asset

    # --- Maintenance Log Methods ---
    def get_logs_by_asset(self, asset_id: str, limit: int = 50):
        return self.db.query(MaintenanceLog).filter(
            MaintenanceLog.asset_id == asset_id
        ).order_by(MaintenanceLog.maintenance_date.desc()).limit(limit).all()

    def create_maintenance_log(self, log_data: MaintenanceLogBase):
        db_log = MaintenanceLog(
            log_id=f"MLG-{uuid.uuid4().hex[:8].upper()}",
            **log_data.model_dump()
        )
        self.db.add(db_log)
        self.db.commit()
        self.db.refresh(db_log)
        return db_log