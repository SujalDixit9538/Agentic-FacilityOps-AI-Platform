from fastapi import APIRouter
from backend.api import health
from backend.api import energy
from backend.api import occupancy
from backend.api import maintenance

# Central API Router with versioning
api_router = APIRouter(prefix="/api/v1")

# Register endpoints
api_router.include_router(health.router, tags=["Platform Health"])

# Register the Energy Module
api_router.include_router(energy.router, prefix="/energy", tags=["Energy"])

# Register the Maintenance Module
api_router.include_router(maintenance.router, prefix="/maintenance", tags=["Maintenance"])

# Register the Occupancy & Security Module
api_router.include_router(occupancy.router, prefix="/occupancy", tags=["Occupancy"])

# Placeholders for future ETP modules
# api_router.include_router(cost.router, prefix="/cost", tags=["Cost"])