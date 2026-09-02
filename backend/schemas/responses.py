from typing import Any, Optional
from pydantic import BaseModel, Field

class StandardResponse(BaseModel):
    """
    Standardized response format required by Blueprint Part 5.
    Ensures the frontend always receives predictable shapes.
    """
    success: bool
    message: str
    data: Optional[Any] = None
    provenance: dict = Field(default_factory=dict)
    freshness: dict = Field(default_factory=dict)
    degraded: bool = False
    quality_flags: list[str] = Field(default_factory=list)