"""Explicit development/demo data seeding command."""

import argparse

import pandas as pd

from backend.database.connection import SessionLocal
from backend.services.facility_catalog_service import FacilityCatalogService
from backend.services.mock_cost_service import seed_mock_cost_data
from backend.services.mock_iot_service import seed_mock_energy_data
from backend.services.mock_maintenance_service import seed_mock_maintenance_data
from backend.services.mock_occupancy_service import seed_mock_occupancy_data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--facility-id", action="append", dest="facility_ids")
    args = parser.parse_args()
    source_ids = pd.read_csv("data/processed_facilities.csv")["facility_id"].dropna().tolist()
    facility_ids = args.facility_ids or ["FAC-001", "FAC-002", *source_ids]

    db = SessionLocal()
    try:
        FacilityCatalogService(db).ensure_many(facility_ids)
        for facility_id in dict.fromkeys(facility_ids):
            seed_mock_energy_data(db, facility_id=facility_id)
            seed_mock_cost_data(db, facility_id=facility_id)
            seed_mock_maintenance_data(db, facility_id=facility_id)
            seed_mock_occupancy_data(db, facility_id=facility_id)
    finally:
        db.close()


if __name__ == "__main__":
    main()