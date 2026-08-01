import requests
import logging

# Note: This will be moved to a centralized config file in ETP-004
BASE_URL = "http://localhost:8000/api/v1"

def safe_get(endpoint: str, fallback_data=None) -> dict:
    """
    Executes a GET request with strict timeout and fallback handling.
    Enforces Blueprint Rules 5.1 (No crashes) and 5.2 (Timeout handling).
    """
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=5.0)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"API call failed for {endpoint}: {e}")
        # Return a standardized failure shape matching our backend schema
        return {
            "success": False,
            "message": "Service unreachable. The platform is running in degraded mode.",
            "data": fallback_data
        }

def safe_post(endpoint: str, payload: dict = None, params: dict = None, fallback_data=None) -> dict:
    """
    Executes a POST request with strict timeout and fallback handling.
    """
    try:
        response = requests.post(f"{BASE_URL}{endpoint}", json=payload, params=params, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"API POST failed for {endpoint}: {e}")
        return {
            "success": False,
            "message": "Service unreachable or request failed.",
            "data": fallback_data
        }