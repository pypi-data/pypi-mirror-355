# cult_common/schemas/signal.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Signal(BaseModel):
    original_event_id: str
    token_id: str
    timestamp: datetime
    score: float
    is_anomaly: bool
    anomaly_model_score: float
    model_type: str
    raw_event_snippet: str
    created_at: datetime
    signal_type: Optional[str] = None

    class Config:
        validate_assignment = True
        frozen = True
