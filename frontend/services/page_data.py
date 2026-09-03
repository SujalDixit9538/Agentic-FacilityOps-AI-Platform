"""Shared, trust-preserving data helpers for Streamlit pages."""

from frontend.services.api_client import safe_get


def get_facility_options() -> tuple[list[dict], dict]:
    """Return canonical facility metadata for selectors and page context."""
    response = safe_get(
        "/energy/facilities",
        fallback_data={"facilities": [], "facility_options": []},
    )
    data = response.get("data") if isinstance(response, dict) else None
    options = data.get("facility_options", []) if isinstance(data, dict) else []
    if options:
        return [item for item in options if isinstance(item, dict) and item.get("facility_id")], response

    facilities = data.get("facilities", []) if isinstance(data, dict) else []
    return [{"facility_id": str(item)} for item in facilities if item], response


def get_facilities() -> tuple[list[str], dict]:
    """Backward-compatible facility ID helper."""
    options, response = get_facility_options()
    return [str(item["facility_id"]) for item in options], response


def metadata(response: dict) -> dict:
    return {
        "freshness": response.get("freshness", {}) or {},
        "provenance": response.get("provenance", {}) or {},
        "quality_flags": response.get("quality_flags", []) or [],
        "degraded": bool(response.get("degraded", False)),
    }


def state_message(response: dict) -> str | None:
    if not response.get("success"):
        return response.get("message", "Service unavailable. No verified data was received.")
    details = metadata(response)
    flags = ", ".join(details["quality_flags"])
    freshness = details["freshness"].get("status")
    if freshness in {"stale", "expired"}:
        return "Telemetry is stale. Confirm the latest ingestion before taking action."
    if details["degraded"] and flags:
        return f"Analysis is degraded: {flags.replace('_', ' ')}."
    return None
