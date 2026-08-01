from fastapi import APIRouter
from backend.api import health

# Central API Router with versioning
api_router = APIRouter(prefix="/api/v1")

# Register the health endpoint
api_router.include_router(health.router, tags=["Health"])

# Placeholders for future ETP modules (Do not uncomment yet)
# api_router.include_router(energy.router, prefix="/energy", tags=["Energy"])
# api_router.include_router(maintenance.router, prefix="/maintenance", tags=["Maintenance"])
# api_router.include_router(occupancy.router, prefix="/occupancy", tags=["Occupancy"])
# api_router.include_router(security.router, prefix="/security", tags=["Security"])
# api_router.include_router(cost.router, prefix="/cost", tags=["Cost"])