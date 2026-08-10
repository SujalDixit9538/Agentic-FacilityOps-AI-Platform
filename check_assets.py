from backend.database.connection import SessionLocal
from backend.repositories.maintenance_repository import MaintenanceRepository

db = SessionLocal()
repo = MaintenanceRepository(db)

# Get assets from different facilities
assets = repo.get_all_assets()
selected_assets = assets[:4]

print(f"{'Facility':<10} | {'Asset':<25} | {'Health Score':<12} | {'Failure Prob':<12}")
print("-" * 75)

for asset in selected_assets:
    # This is a simplified check assuming the repo/model has health data
    # In a real scenario, this might involve calling an analyzer service
    # For now, print what is available directly from asset record if possible
    # Assuming health_score and failure_probability are attributes of the asset
    # Or in maintenance logs
    print(f"{asset.facility_id:<10} | {asset.asset_type:<25} | {getattr(asset, 'health_score', 'N/A'):<12} | {getattr(asset, 'failure_probability', 'N/A'):<12}")

db.close()
