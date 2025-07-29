from datetime import datetime
import pytest
from cult_common.schemas.raw_event import RawEvent
from cult_common.schemas.signal import Signal


def test_raw_event_model():
    data = {
        "id": "uuid",
        "token_id": "t1",
        "timestamp": datetime.utcnow(),
        "volume": 10.0,
        "price": 5.0,
        "chain": "eth",
        "block_number": 100,
        "extra": {"foo": "bar"}
    }
    ev = RawEvent(**data)
    assert ev.token_id == "t1"
    assert isinstance(ev, RawEvent)


def test_signal_model():
    data = {
        "original_event_id": "uuid",
        "token_id": "t1",
        "timestamp": datetime.utcnow(),
        "score": 0.5,
        "is_anomaly": True,
        "anomaly_model_score": 0.1,
        "model_type": "IsolationForest",
        "raw_event_snippet": "...",
        "created_at": datetime.utcnow()
    }
    s = Signal(**data)
    assert s.is_anomaly is True
    assert s.score == 0.5