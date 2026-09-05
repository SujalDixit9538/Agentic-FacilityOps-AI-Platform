import secrets
import threading
import time
from typing import Generator
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from config.settings import settings
from backend.database.connection import SessionLocal

bearer_scheme = HTTPBearer(auto_error=False)
_rate_limit_lock = threading.Lock()
_rate_limit_events: dict[str, list[float]] = {}


def require_api_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> None:
    """Require the configured service token for protected API routes."""
    configured_token = settings.API_AUTH_TOKEN
    if not configured_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication is not configured.",
        )
    if credentials is None or credentials.scheme.lower() != "bearer" or not secrets.compare_digest(
        credentials.credentials, configured_token
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid API authentication is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_mutation_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> None:
    """Require the separate administrator token for state-changing methods."""
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return

    configured_token = settings.API_ADMIN_TOKEN
    if not configured_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API administrator authentication is not configured.",
        )
    if credentials is None or credentials.scheme.lower() != "bearer" or not secrets.compare_digest(
        credentials.credentials, configured_token
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator authentication is required for this operation.",
        )


def require_facility_access(facility_id: str | None = None) -> None:
    """Enforce an optional deployment-level facility access allowlist."""
    configured_facilities = {
        item.strip()
        for item in settings.FACILITY_ACCESS_ALLOWLIST.split(",")
        if item.strip()
    }
    if configured_facilities and facility_id and facility_id not in configured_facilities:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this facility is not permitted.",
        )


def enforce_rate_limit(request: Request) -> None:
    """Apply a small process-local request limit to protected API routes."""
    limit = settings.RATE_LIMIT_PER_MINUTE
    if limit <= 0:
        return
    client_host = request.client.host if request.client else "unknown"
    now = time.monotonic()
    cutoff = now - 60
    with _rate_limit_lock:
        events = [event for event in _rate_limit_events.get(client_host, []) if event > cutoff]
        if len(events) >= limit:
            _rate_limit_events[client_host] = events
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded.")
        events.append(now)
        _rate_limit_events[client_host] = events

def get_settings():
    """Dependency injection for settings."""
    return settings

def get_db() -> Generator:
    """
    Dependency injection for the database session.
    Ensures the session is safely closed after the request completes,
    even if an exception occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()