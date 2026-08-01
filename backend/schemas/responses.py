from typing import Any, Optional
from pydantic import BaseModel

class StandardResponse(BaseModel):
    """
    Standardized response format required by Blueprint Part 5.
    Ensures the frontend always receives predictable shapes.
    """
    success: bool
    message: str
    data: Optional[Any] = None