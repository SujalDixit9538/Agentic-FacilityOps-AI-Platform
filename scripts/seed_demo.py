"""Explicit development/demo data seeding command."""

import argparse

import pandas as pd

from backend.database.connection import SessionLocal
from backend.services.facility_catalog_service import FacilityCatalogService
from backend.services.mock_cost_service import seed_mock_cost_data
from backend.services.mock_iot_service import seed_mock_energy_data
from backend.services.mock_maintenance_service import seed_mock_maintenance_data
from backend.services.mock_occupancy_service import seed_mock_occupancy_data


CATALOG_PATH = "data/processed_facilities.csv"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--facility-id", action="append", dest="facility_ids")
    args = parser.parse_args()

    catalog = pd.read_csv(CATALOG_PATH).dropna(subset=["facility_id"])
    catalog["facility_id"] = catalog["facility_id"].astype(str).str.strip()
    catalog_by_id = catalog.set_index("facility_id").to_dict("index")

    # The supplied catalog is the canonical demo population. Synthetic IDs are
    # supported only when explicitly requested with --facility-id.
    facility_ids = args.facility_ids or list(catalog_by_id)

    db = SessionLocal()
    try:
        catalog_service = FacilityCatalogService(db)
        for facility_id in dict.fromkeys(facility_ids):
            source = catalog_by_id.get(facility_id, {})
            catalog_service.ensure(
                facility_id,
                name=source.get("name", facility_id),
                facility_type=source.get("facility_type"),
                total_area_sqft=source.get("total_area_sqft"),
                total_floors=source.get("total_floors"),
            )
        db.commit()

        for facility_id in dict.fromkeys(facility_ids):
            seed_mock_energy_data(db, facility_id=facility_id)
            seed_mock_cost_data(db, facility_id=facility_id)
            seed_mock_maintenance_data(db, facility_id=facility_id)
            seed_mock_occupancy_data(db, facility_id=facility_id)
    finally:
        db.close()


if __name__ == "__main__":
    main()
