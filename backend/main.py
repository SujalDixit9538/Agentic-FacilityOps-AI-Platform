from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from backend.api.router import api_router
from backend.middleware.exceptions import global_exception_handler
from backend.services.mock_cost_service import seed_mock_cost_data
from backend.services.mock_maintenance_service import seed_mock_maintenance_data
from backend.services.mock_occupancy_service import seed_mock_occupancy_data
from backend.services.logging_service import setup_logging
from backend.middleware.timing import timing_middleware
from backend.core.config import settings
from backend.database.connection import engine
from backend.database.base import Base
from backend.database.connection import SessionLocal
from backend.services.mock_iot_service import seed_mock_energy_data

setup_logging()

Base.metadata.create_all(bind=engine)

# Initialize FastAPI Application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Lightweight backend for Facility Intelligence",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# 1. Register Global Exception Handler
app.add_exception_handler(Exception, global_exception_handler)

# 2. Register Custom Middleware
app.add_middleware(BaseHTTPMiddleware, dispatch=timing_middleware)

# 3. Foundational Middleware (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Register API Router
app.include_router(api_router)

# 5. Root Redirect (Fixes the "Not Found" UI issue)
@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirects the root URL to the interactive Swagger UI."""
    return RedirectResponse(url="/api/docs")

@app.on_event("startup")
async def initialize_default_data():
    """
    Automatically seeds the database with initial mock data on startup 
    if the database is empty. Prevents the "empty state" on first boot.
    """
    from backend.database.connection import SessionLocal
    db = SessionLocal()
    try:
        # Seed Energy Data
        from backend.services.mock_iot_service import seed_mock_energy_data
        seed_mock_energy_data(db, facility_id="FAC-001", days=7)
        seed_mock_energy_data(db, facility_id="FAC-002", days=7)
        
        # Seed Maintenance Data
        from backend.services.mock_maintenance_service import seed_mock_maintenance_data
        seed_mock_maintenance_data(db, facility_id="FAC-001")
        seed_mock_maintenance_data(db, facility_id="FAC-002")
        
        # Seed Occupancy & Security Data
        from backend.services.mock_occupancy_service import seed_mock_occupancy_data
        seed_mock_occupancy_data(db, facility_id="FAC-001", days=7)
        seed_mock_occupancy_data(db, facility_id="FAC-002", days=7)
        
        # Seed Cost Optimization Data (ETP-019)
        seed_mock_cost_data(db, facility_id="FAC-001", months_back=6)
        seed_mock_cost_data(db, facility_id="FAC-002", months_back=6)
        
    except Exception as e:
        print(f"Startup data seeding skipped: {e}")
    finally:
        db.close()