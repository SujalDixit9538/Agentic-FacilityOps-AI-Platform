from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Lightweight health endpoint to verify the backend is running.
    Returns a structured success response as per Blueprint guidelines.
    """
    return {
        "success": True,
        "message": "FacilityOPS Backend is operational.",
        "data": {"status": "healthy"}
    }