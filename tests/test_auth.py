from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from backend.api import dependencies
from backend.api.router import api_router


def test_api_auth_accepts_configured_bearer_token(monkeypatch):
    monkeypatch.setattr(dependencies.settings, "API_AUTH_TOKEN", "test-token")

    assert dependencies.require_api_auth(
        HTTPAuthorizationCredentials(scheme="Bearer", credentials="test-token")
    ) is None


def test_api_auth_rejects_invalid_token(monkeypatch):
    monkeypatch.setattr(dependencies.settings, "API_AUTH_TOKEN", "test-token")

    try:
        dependencies.require_api_auth(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials="wrong-token")
        )
    except HTTPException as exc:
        assert exc.status_code == 401
        assert exc.headers == {"WWW-Authenticate": "Bearer"}
    else:
        raise AssertionError("invalid token must be rejected")


def test_api_auth_fails_closed_when_token_is_not_configured(monkeypatch):
    monkeypatch.setattr(dependencies.settings, "API_AUTH_TOKEN", None)

    try:
        dependencies.require_api_auth(None)
    except HTTPException as exc:
        assert exc.status_code == 503
    else:
        raise AssertionError("missing configuration must fail closed")


def test_domain_routes_require_authentication_but_health_remains_public():
    protected_paths = {
        route.path
        for route in api_router.routes
        if route.path != "/api/v1/health"
    }

    assert protected_paths
    for route in api_router.routes:
        dependency_callables = {
            dependency.call
            for dependency in route.dependant.dependencies
        }
        if route.path == "/api/v1/health":
            assert dependencies.require_api_auth not in dependency_callables
        else:
            assert dependencies.require_api_auth in dependency_callables


def test_mutations_require_the_separate_admin_token(monkeypatch):
    monkeypatch.setattr(dependencies.settings, "API_AUTH_TOKEN", "read-token")
    monkeypatch.setattr(dependencies.settings, "API_ADMIN_TOKEN", "admin-token")

    assert dependencies.require_api_auth(
        HTTPAuthorizationCredentials(scheme="Bearer", credentials="read-token")
    ) is None

    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="read-token")
    try:
        dependencies.require_mutation_auth(_request("POST"), credentials)
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("read token must not authorize mutations")

    assert dependencies.require_mutation_auth(
        _request("POST"),
        HTTPAuthorizationCredentials(scheme="Bearer", credentials="admin-token"),
    ) is None


def _request(method):
    return type("Request", (), {"method": method})()


def test_facility_allowlist_rejects_unlisted_facilities(monkeypatch):
    monkeypatch.setattr(dependencies.settings, "FACILITY_ACCESS_ALLOWLIST", "F-1, F-2")

    assert dependencies.require_facility_access("F-1") is None
    assert dependencies.require_facility_access(None) is None
    try:
        dependencies.require_facility_access("F-3")
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("unlisted facility must be rejected")


def test_rate_limit_rejects_requests_over_configured_cap(monkeypatch):
    dependencies._rate_limit_events.clear()
    monkeypatch.setattr(dependencies.settings, "RATE_LIMIT_PER_MINUTE", 1)
    request = type("Request", (), {"client": type("Client", (), {"host": "test-client"})()})()

    assert dependencies.enforce_rate_limit(request) is None
    try:
        dependencies.enforce_rate_limit(request)
    except HTTPException as exc:
        assert exc.status_code == 429
    else:
        raise AssertionError("requests over the configured cap must be rejected")