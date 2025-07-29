from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Dict

class RawEvent(BaseModel):
    id: str = Field(..., description="Unique event ID")
    token_id: str
    timestamp: datetime
    volume: float
    price: float
    chain: str
    block_number: int
    extra: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        frozen = True
