import os
import sys
import pytest

# Ensure repository root is on PYTHONPATH for imports like `backend.*`
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.agents.maintenance.analyzer import MaintenanceAnalyzer


def test_rule_based_fallback_includes_failure_probability():
    analyzer = MaintenanceAnalyzer()

    # Provide logs that trigger the rule-based high temperature anomaly
    logs = [
        {
            "log_id": "l1",
            "temperature": 85.0,
            "air_temp": 300.0,
            "process_temp": 310.0,
            "speed": 1500.0,
            "torque": 40.0,
            "wear": 15.0,
        }
    ]

    result = analyzer.analyze_asset_health({"asset_id": "A-1"}, logs)

    assert result.get("status") == "success"
    metrics = result.get("metrics", {})
    assert "asset_health_score" in metrics
    assert "failure_probability" in metrics

    health = float(metrics["asset_health_score"])
    prob = float(metrics["failure_probability"])

    # failure_probability should equal 1 - health/100 (within rounding)
    assert pytest.approx(prob, rel=1e-3) == round(max(0.0, min(1.0, 1.0 - (health / 100.0))), 4)
