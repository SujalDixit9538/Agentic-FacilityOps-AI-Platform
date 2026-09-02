from pathlib import Path

from frontend.services.page_data import metadata, state_message
from frontend.services import api_client

ROOT = Path(__file__).parents[1]


def test_api_state_messages_distinguish_failure_stale_and_degraded():
    assert "unavailable" in state_message({"success": False, "message": "API unavailable"}).lower()
    assert "stale" in state_message({"success": True, "freshness": {"status": "stale"}}).lower()
    assert "degraded" in state_message({"success": True, "degraded": True, "quality_flags": ["missing_model"]}).lower()
    assert state_message({"success": True, "freshness": {"status": "available"}}) is None


def test_pages_use_canonical_catalog_and_aggregate_endpoints():
    for page in ("Dashboard.py", "Cost.py", "Energy.py", "Maintenance.py", "Occupancy_and_Security.py"):
        source = (ROOT / "frontend" / "pages" / page).read_text()
        assert "get_facilities" in source
        assert "use_container_width" not in source
    assert "records/" not in (ROOT / "frontend/pages/Cost.py").read_text()
    assert "limit=8000" not in (ROOT / "frontend/pages/Occupancy_and_Security.py").read_text()


def test_energy_does_not_present_unverified_operational_metrics():
    source = (ROOT / "frontend/pages/Energy.py").read_text()
    for value in ("94%", "0.12", "0.38", "Under Budget", "Deploy to Edge Devices"):
        assert value not in source


def test_metadata_preserves_trust_fields():
    result = metadata({
        "freshness": {"status": "stale"},
        "provenance": {"source": "aggregate"},
        "quality_flags": ["old_data"],
        "degraded": True,
    })
    assert result == {
        "freshness": {"status": "stale"},
        "provenance": {"source": "aggregate"},
        "quality_flags": ["old_data"],
        "degraded": True,
    }


def test_api_client_rejects_malformed_response(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"unexpected": True}

    monkeypatch.setattr(api_client.requests, "request", lambda *args, **kwargs: Response())
    response = api_client.safe_get("/health", fallback_data={"status": "unknown"})
    assert response["success"] is False
    assert "invalid response" in response["message"].lower()
    assert response["degraded"] is True
