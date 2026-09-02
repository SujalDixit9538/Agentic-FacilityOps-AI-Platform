import requests
import logging
import os
import time
import uuid

# Note: This will be moved to a centralized config file in ETP-004
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")


def _failure(message: str, fallback_data=None, correlation_id: str | None = None) -> dict:
    return {
        "success": False,
        "message": message,
        "data": fallback_data,
        "provenance": {"source": "frontend_api_client", "correlation_id": correlation_id},
        "freshness": {"status": "unavailable"},
        "degraded": True,
        "quality_flags": ["api_unavailable"],
    }


def _request(method: str, endpoint: str, *, payload=None, params=None, timeout=5.0, fallback_data=None) -> dict:
    correlation_id = str(uuid.uuid4())
    headers = {"X-Correlation-ID": correlation_id}
    for attempt in range(2):
        try:
            response = requests.request(
                method, f"{BASE_URL}{endpoint}", json=payload, params=params,
                headers=headers, timeout=timeout,
            )
            response.raise_for_status()
            body = response.json()
            if not isinstance(body, dict) or "success" not in body or "data" not in body:
                return _failure("The service returned an invalid response.", fallback_data, correlation_id)
            body.setdefault("provenance", {})["correlation_id"] = correlation_id
            return body
        except (requests.exceptions.RequestException, ValueError) as exc:
            logging.warning("API %s failed for %s (attempt %s): %s", method, endpoint, attempt + 1, exc)
            if attempt == 0:
                time.sleep(0.1)
    return _failure("Service unavailable. No verified data was received.", fallback_data, correlation_id)

def safe_get(endpoint: str, fallback_data=None) -> dict:
    """
    Executes a GET request with strict timeout and fallback handling.
    Enforces Blueprint Rules 5.1 (No crashes) and 5.2 (Timeout handling).
    """
    return _request("GET", endpoint, timeout=5.0, fallback_data=fallback_data)

def safe_post(endpoint: str, payload: dict = None, params: dict = None, fallback_data=None) -> dict:
    """
    Executes a POST request with strict timeout and fallback handling.
    """
    return _request("POST", endpoint, payload=payload, params=params, timeout=10.0, fallback_data=fallback_data)


def safe_patch(endpoint: str, payload: dict | None = None, fallback_data=None) -> dict:
    """Issue a persisted update while preserving the standard response envelope."""
    return _request("PATCH", endpoint, payload=payload, timeout=10.0, fallback_data=fallback_data)