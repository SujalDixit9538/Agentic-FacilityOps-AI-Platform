from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.database.base import Base
from backend.database.models.cost import CostAnalysisReport, CostRecord
from backend.services.cost_service import CostService
from backend.agents.maintenance.analyzer import MaintenanceAnalyzer
from backend.agents.occupancy.analyzer import OccupancyAnalyzer
from backend.agents.occupancy.config import OCCUPANCY_RULES
from backend.agents.energy.analyzer import EnergyAnalyzer
from backend.agents.executive.agent import ExecutiveAgent
import time


def test_cost_analysis_is_idempotent_for_same_input():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = Session(engine)
    db.add(CostRecord(
        record_id="cost-1",
        facility_id="F-1",
        category="Operations",
        amount=100.0,
        description="monthly service",
        incurred_date=datetime(2026, 1, 1),
    ))
    db.commit()

    service = CostService(db)
    first = service.run_agent_analysis("F-1")
    second = service.run_agent_analysis("F-1")

    assert first["report_id"] == second["report_id"]
    assert db.query(CostAnalysisReport).count() == 1


def test_maintenance_missing_telemetry_is_degraded():
    result = MaintenanceAnalyzer().predict_features({"type": "M"})

    assert result["status"] == "degraded"
    assert result["intelligence_source"] == "Degraded Fallback"
    assert "missing_maintenance_features" in result["degradation_reason"]


def test_maintenance_non_finite_prediction_is_degraded():
    class InvalidModel:
        def predict_proba(self, frame):
            return [[0.0, float("nan")]]

        def predict(self, frame):
            return ["unknown"]

    analyzer = MaintenanceAnalyzer()
    analyzer.failure_model = InvalidModel()
    analyzer.fault_model = InvalidModel()
    analyzer._models_loaded = True

    result = analyzer.predict_features({
        "air_temp": 300,
        "process_temp": 310,
        "speed": 1500,
        "torque": 40,
        "wear": 15,
    })

    assert result["status"] == "degraded"
    assert result["degradation_reason"] == "non_finite_or_invalid_failure_probability"


def test_occupancy_threshold_and_duplicate_alert_contract():
    analyzer = OccupancyAnalyzer()
    result = analyzer.analyze_facility_state([
        {"zone_id": "z1", "occupancy_count": 90, "max_capacity": 100},
        {"zone_id": "z1", "occupancy_count": 100, "max_capacity": 100},
    ], [])

    assert OCCUPANCY_RULES["OVERCROWDING_THRESHOLD_PCT"] == 1.0
    assert len(result.anomalies) == 1


def test_energy_feature_frame_rejects_missing_temperature():
    analyzer = EnergyAnalyzer()

    try:
        analyzer._build_feature_frame({"timestamp": datetime(2026, 1, 1), "energy_kwh": 10})
    except ValueError as exc:
        assert str(exc) == "missing_energy_temperature_feature"
    else:
        raise AssertionError("missing temperature must not be fabricated")


def test_executive_agent_reports_failure_and_timeout():
    agent = ExecutiveAgent.__new__(ExecutiveAgent)

    _, failed = agent._run_agent("cost", lambda: (_ for _ in ()).throw(RuntimeError("backend down")))
    _, timed_out = agent._run_agent("energy", lambda: time.sleep(0.05), timeout_seconds=0.001)

    assert failed["status"] == "failed"
    assert failed["failure"] == "backend down"
    assert timed_out["status"] == "timeout"
