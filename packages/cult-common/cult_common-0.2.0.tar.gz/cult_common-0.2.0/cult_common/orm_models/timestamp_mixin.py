# cult_common/orm_models/timestamp_mixin.py

from datetime import datetime
from sqlalchemy import Column, DateTime

def utcnow() -> datetime:
    return datetime.utcnow()

class TimestampMixin:
    """
    Mixin that sets both created_at and updated_at to the same default value on insert.
    """
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, nullable=False)

