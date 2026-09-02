"""Shared, trust-preserving data helpers for Streamlit pages."""

from frontend.services.api_client import safe_get


def get_facilities() -> tuple[list[str], dict]:
    response = safe_get("/energy/facilities", fallback_data={"facilities": []})
    data = response.get("data") if isinstance(response, dict) else None
    facilities = data.get("facilities", []) if isinstance(data, dict) else []
    return [str(item) for item in facilities if item], response


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