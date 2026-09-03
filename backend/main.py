from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.api.router import api_router
from backend.core.config import settings
from backend.middleware.exceptions import global_exception_handler
from backend.middleware.timing import timing_middleware
from backend.services.logging_service import setup_logging

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle hook.

    Database schema management is intentionally handled by Alembic rather than
    mutating the schema during application import/startup.
    """
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Lightweight backend for Facility Intelligence",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

app.add_exception_handler(Exception, global_exception_handler)
app.add_middleware(BaseHTTPMiddleware, dispatch=timing_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

app.include_router(api_router)


@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect the root URL to the interactive API documentation."""
    return RedirectResponse(url="/api/docs")
