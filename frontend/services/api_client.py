import logging
import os
import time
import uuid
from pathlib import Path

import requests


def _load_local_env() -> None:
    """Load non-secret local .env values when the frontend is started outside dotenv-aware tooling.

    Existing process environment variables always win. Values are read only to configure the
    local frontend client; secrets are never logged or displayed.
    """
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and value and key not in os.environ:
                os.environ[key] = value
    except OSError:
        # The API client will simply operate without optional local credentials.
        return


_load_local_env()

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
API_AUTH_TOKEN = os.getenv("API_AUTH_TOKEN")
API_ADMIN_TOKEN = os.getenv("API_ADMIN_TOKEN")


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
    request_token = API_ADMIN_TOKEN or API_AUTH_TOKEN
    if request_token:
        headers["Authorization"] = f"Bearer {request_token}"
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
    return _request("GET", endpoint, timeout=5.0, fallback_data=fallback_data)


def safe_post(endpoint: str, payload: dict = None, params: dict = None, fallback_data=None) -> dict:
    return _request("POST", endpoint, payload=payload, params=params, timeout=10.0, fallback_data=fallback_data)


def safe_patch(endpoint: str, payload: dict | None = None, params: dict | None = None, fallback_data=None) -> dict:
    return _request("PATCH", endpoint, payload=payload, params=params, timeout=10.0, fallback_data=fallback_data)
