from fastapi import APIRouter, Depends
from backend.api import cost
from backend.api import health
from backend.api import energy
from backend.api import occupancy
from backend.api import maintenance
from backend.api import executive
from backend.api.dependencies import enforce_rate_limit, require_api_auth, require_mutation_auth, require_facility_access

# Central API Router with versioning
api_router = APIRouter(prefix="/api/v1")

# Register endpoints
api_router.include_router(health.router, tags=["Platform Health"])

# Register the Energy Module
api_router.include_router(energy.router, prefix="/energy", tags=["Energy"], dependencies=[Depends(require_api_auth), Depends(require_mutation_auth), Depends(require_facility_access), Depends(enforce_rate_limit)])

# Register the Maintenance Module
api_router.include_router(maintenance.router, prefix="/maintenance", tags=["Maintenance"], dependencies=[Depends(require_api_auth), Depends(require_mutation_auth), Depends(require_facility_access), Depends(enforce_rate_limit)])

# Register the Occupancy & Security Module
api_router.include_router(occupancy.router, prefix="/occupancy", tags=["Occupancy"], dependencies=[Depends(require_api_auth), Depends(require_mutation_auth), Depends(require_facility_access), Depends(enforce_rate_limit)])

# Register the Cost Optimization Module
api_router.include_router(cost.router, prefix="/cost", tags=["Cost"], dependencies=[Depends(require_api_auth), Depends(require_mutation_auth), Depends(require_facility_access), Depends(enforce_rate_limit)])

# Register the Executive Agent Module
api_router.include_router(executive.router, prefix="/executive", tags=["Executive Intelligence"], dependencies=[Depends(require_api_auth), Depends(require_mutation_auth), Depends(require_facility_access), Depends(enforce_rate_limit)])