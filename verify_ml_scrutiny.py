import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database.models.maintenance import Asset, MaintenanceLog
from backend.agents.maintenance.analyzer import MaintenanceAnalyzer
import pandas as pd

# 1. Open a DB session
DATABASE_URL = "sqlite:///./data/facilityops.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# 2. Get assets across both facilities
assets = db.query(Asset).all()

analyzer = MaintenanceAnalyzer()

print(f"{'Asset ID':<12} | {'Facility':<8} | {'Wear':<6} | {'Torque':<6} | {'Speed':<6} | {'Health Score':<12} | {'Fail Probability':<18} | {'Source':<10}")
print("-" * 100)

for asset in assets:
    # 3. Get logs
    logs = db.query(MaintenanceLog).filter(MaintenanceLog.asset_id == asset.asset_id).order_by(MaintenanceLog.maintenance_date.desc()).all()
    if not logs:
        continue
        
    latest_log = logs[0]
    
    # 4. Call the analyzer
    logs_dict = [log.__dict__ for log in logs]
    for log in logs_dict:
        log.pop('_sa_instance_state', None)
        
    result = analyzer.analyze_asset_health(asset.__dict__, logs_dict)
    
    # Calculate probability of failure
    prob_failure = 1.0 - (result['metrics'].get('asset_health_score') / 100.0)
    
    print(f"{asset.asset_id:<12} | {asset.facility_id:<8} | {latest_log.wear:<6.1f} | {latest_log.torque:<6.1f} | {latest_log.speed:<6.1f} | {result['metrics'].get('asset_health_score'):<12.2f} | {prob_failure:<18.2f} | {result['intelligence_source']:<10}")

db.close()
