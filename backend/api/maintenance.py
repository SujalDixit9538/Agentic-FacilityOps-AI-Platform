from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from backend.api.dependencies import get_db
from backend.services.maintenance_service import MaintenanceService
from backend.services.mock_maintenance_service import seed_mock_maintenance_data
from backend.schemas.maintenance import AssetResponse, MaintenanceLogResponse
from backend.schemas.manual_predict import ManualPredictRequest
from backend.utils.api_responses import success_response
from backend.agents.maintenance.analyzer import MaintenanceAnalyzer

router = APIRouter()

@router.get("/health")
async def maintenance_module_health(db: Session = Depends(get_db)):
    """Verifies the Maintenance module is online."""
    service = MaintenanceService(db)
    status = service.get_module_status()
    return success_response(message="Maintenance module health check", data=status)

@router.get("/facilities")
async def get_facilities(db: Session = Depends(get_db)):
    """Returns a list of distinct facility_ids from the assets table."""
    from backend.database.models.maintenance import Asset
    facilities = db.query(Asset.facility_id).distinct().all()
    facility_list = [f[0] for f in facilities]
    return success_response(message="Retrieved facilities", data={"facilities": facility_list})

@router.post("/seed")
async def seed_maintenance_data(facility_id: str = Query(None), db: Session = Depends(get_db)):
    """Triggers the mock asset and maintenance history pipeline."""
    # If no facility_id provided, default to first in CSV
    import pandas as pd
    df = pd.read_csv("data/processed_facilities.csv")
    
    # If facility_id not provided, seed ALL facilities found in CSV
    target_facilities = [facility_id] if facility_id else df["facility_id"].tolist()
        
    results = []
    for f_id in target_facilities:
        assets_count, logs_created = seed_mock_maintenance_data(db, facility_id=f_id)
        results.append({"facility_id": f_id, "assets_seeded": assets_count, "logs_seeded": logs_created})
        
    return success_response(
        message="Maintenance data pipeline executed.",
        data=results
    )

@router.get("/assets/{facility_id}")
async def get_assets(facility_id: str, db: Session = Depends(get_db)):
    """Retrieves all assets for a given facility."""
    service = MaintenanceService(db)
    assets = service.get_facility_assets(facility_id)
    
    data = [AssetResponse.model_validate(a).model_dump() for a in assets]
    return success_response(message=f"Retrieved {len(data)} assets", data={"assets": data})

@router.get("/logs/{asset_id}")
async def get_maintenance_logs(asset_id: str, limit: int = 50, db: Session = Depends(get_db)):
    """Retrieves the maintenance history for a given asset."""
    service = MaintenanceService(db)
    logs = service.get_asset_maintenance_history(asset_id, limit)
    
    data = [MaintenanceLogResponse.model_validate(l).model_dump() for l in logs]
    return success_response(message=f"Retrieved {len(data)} maintenance logs", data={"logs": data})

@router.get("/analyze/{asset_id}")
async def analyze_asset(asset_id: str, db: Session = Depends(get_db)):
    """Runs the Predictive Maintenance Agent analysis on the specified asset."""
    service = MaintenanceService(db)
    insights = service.run_agent_analysis(asset_id)
    
    if insights.get("status") == "error":
        return success_response(message="Asset analysis failed", data=insights)
        
    return success_response(
        message=f"Maintenance analysis completed for {asset_id}",
        data=insights
    )

@router.post("/predict-manual")
async def predict_manual(request: ManualPredictRequest):
    """Predicts asset health based on manually entered sensor data."""
    analyzer = MaintenanceAnalyzer()
    features = request.dict()
    result = analyzer.predict_features(features)
    return success_response(message="Manual prediction complete", data=result)

@router.post("/generate-workorder/{asset_id}")
async def generate_workorder(asset_id: str, db: Session = Depends(get_db)):
    """Triggers the Maintenance Agent to generate a work order."""
    service = MaintenanceService(db)
    result = service.generate_work_order(asset_id)
    return success_response(message="Work order generation complete", data=result)

@router.get("/assets-analyzed/{facility_id}")
async def get_assets_analyzed(facility_id: str, db: Session = Depends(get_db)):
    """Retrieves all assets for a given facility with analyzed maintenance data."""
    service = MaintenanceService(db)
    assets = service.get_facility_assets(facility_id)
    
    analyzed_assets = []
    for asset in assets:
        asset_dict = AssetResponse.model_validate(asset).model_dump()
        insights = service.run_agent_analysis(asset.asset_id)
        
        # Merge health score and probability
        analysis = insights.get("analysis", {})
        metrics = analysis.get("metrics", {})
        
        if insights.get("asset_id"):
            asset_dict["predicted_issue"] = metrics.get("predicted_issue", "Unknown")
            asset_dict["health_score"] = metrics.get("asset_health_score")
            # Prefer explicit failure_probability from analyzer when available
            asset_dict["failure_probability"] = metrics.get(
                "failure_probability",
                1.0 - (metrics.get("asset_health_score", 100.0) / 100.0)
            )
            asset_dict["intelligence_source"] = analysis.get("intelligence_source", "ML")

            latest_log = service.get_asset_maintenance_history(asset.asset_id, limit=1)
            latest_telemetry = latest_log[0] if latest_log else None
            
            for field in ["air_temp", "process_temp", "speed", "torque", "wear"]:
                asset_dict[field] = getattr(latest_telemetry, field, None)
        else:
            asset_dict["predicted_issue"] = "Unknown"
            asset_dict["health_score"] = None
            asset_dict["failure_probability"] = None
            asset_dict["intelligence_source"] = "N/A"
            for field in ["air_temp", "process_temp", "speed", "torque", "wear"]:
                asset_dict[field] = None
            
        analyzed_assets.append(asset_dict)
        
    return success_response(message=f"Retrieved {len(analyzed_assets)} analyzed assets", data={"assets": analyzed_assets})