import time
from fastapi import Request

async def timing_middleware(request: Request, call_next):
    """
    Measures request execution time and appends it to response headers.
    Helps monitor performance budgets across milestones.
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    response.headers["X-Process-Time"] = f"{process_time:.4f} sec"
    response.headers["X-Response-Budget"] = "analysis=10s;dashboard=2s"
    return response