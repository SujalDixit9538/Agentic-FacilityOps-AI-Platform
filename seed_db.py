from backend.database.connection import SessionLocal
from backend.services.mock_maintenance_service import seed_mock_maintenance_data
import pandas as pd

db = SessionLocal()
facilities_df = pd.read_csv('data/processed_facilities.csv')
for f_id in facilities_df['facility_id'].head(5):
    print(f"Seeding {f_id}")
    seed_mock_maintenance_data(db, f_id)
db.commit()
db.close()
print("Done seeding")
