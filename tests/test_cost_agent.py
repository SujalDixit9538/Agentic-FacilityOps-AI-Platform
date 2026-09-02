from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.agents.cost.agent import CostAgent
from backend.agents.energy.agent import EnergyAgent
from backend.database.base import Base
from backend.database.models.cost import CostRecord
from backend.database.models.energy import EnergyRecord
from backend.database.models.maintenance import Asset
from backend.database.models.occupancy import OccupancyRecord, OccupancyZone


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_cost_agent_uses_real_cross_domain_state():
    db = make_session()
    now = datetime(2026, 1, 15, 12)
    db.add_all([
        EnergyRecord(record_id="e1", facility_id="F-1", timestamp=now, energy_kwh=1200, peak_demand_kw=240),
        OccupancyZone(zone_id="z1", facility_id="F-1", floor=1, zone_name="Office", zone_type="office", max_capacity=100),
        OccupancyRecord(occupancy_id="o1", facility_id="F-1", zone_id="z1", occupancy_count=60, timestamp=now),
        Asset(asset_id="a1", facility_id="F-1", asset_type="HVAC", installation_date=now, status="Operational"),
        CostRecord(record_id="c1", facility_id="F-1", category="Energy", amount=100, description="bill", incurred_date=now),
    ])
    db.commit()

    result = CostAgent(db).analyze_facility_finances("F-1")

    assert result["facility_state"]["energy_load"] == 240
    assert result["facility_state"]["occupancy_pct"] == 60
    assert result["facility_state"]["asset_health"] == 100
    assert result["analysis"]["metrics"]["intelligence_source"] == "ML (Prescriptive AI)"


def test_cost_agent_discloses_degraded_state():
    db = make_session()
    db.add(CostRecord(
        record_id="c1", facility_id="F-1", category="Operations", amount=100,
        description="bill", incurred_date=datetime(2026, 1, 15),
    ))
    db.commit()

    result = CostAgent(db).analyze_facility_finances("F-1")

    assert result["analysis"]["metrics"]["intelligence_source"] == "Rules Only"
    assert result["analysis"]["metrics"]["degradation_reason"] == "complete_cross_domain_state_unavailable"


def test_energy_agent_uses_database_telemetry():
    db = make_session()
    db.add(EnergyRecord(
        record_id="e1", facility_id="F-1", timestamp=datetime(2026, 1, 15),
        energy_kwh=123.4, peak_demand_kw=201,
    ))
    db.commit()

    result = EnergyAgent(db).analyze_facility("F-1")

    assert result["analysis"]["metrics"]["total_kwh"] == 123.4
    assert result["analysis"]["metrics"]["peak_kw"] == 201
