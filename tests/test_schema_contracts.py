import pytest
from pydantic import ValidationError

from backend.schemas.cost import CostRecommendationUpdate, CostRecordBase
from backend.schemas.energy import EnergyRecordBase
from backend.schemas.maintenance import AssetBase
from backend.schemas.occupancy import OccupancyImageBase, SecurityEventBase


def test_cost_record_rejects_negative_amount_and_oversized_description():
    with pytest.raises(ValidationError):
        CostRecordBase(
            facility_id="F-1",
            category="Energy",
            amount=-1,
            incurred_date="2026-01-01T00:00:00",
        )

    with pytest.raises(ValidationError):
        CostRecordBase(
            facility_id="F-1",
            category="Energy",
            amount=1,
            description="x" * 501,
            incurred_date="2026-01-01T00:00:00",
        )


def test_recommendation_update_uses_explicit_status_values():
    assert CostRecommendationUpdate(status="completed").status == "completed"
    with pytest.raises(ValidationError):
        CostRecommendationUpdate(status="anything")


def test_domain_schemas_reject_invalid_ranges_and_enums():
    with pytest.raises(ValidationError):
        EnergyRecordBase(facility_id="F-1", timestamp="2026-01-01T00:00:00", energy_kwh=-1)
    with pytest.raises(ValidationError):
        AssetBase(facility_id="F-1", asset_type="HVAC", installation_date="2026-01-01T00:00:00", status="Unknown")
    with pytest.raises(ValidationError):
        OccupancyImageBase(
            facility_id="F-1", zone_id="Z-1", captured_at="2026-01-01T00:00:00", confidence_score=2
        )
    with pytest.raises(ValidationError):
        SecurityEventBase(
            facility_id="F-1", event_type="Door", severity="Unknown", event_time="2026-01-01T00:00:00"
        )