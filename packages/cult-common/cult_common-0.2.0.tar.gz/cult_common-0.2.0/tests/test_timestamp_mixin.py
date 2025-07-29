# cult_common/orm_models/timestamp_mixin.py

from datetime import datetime
from sqlalchemy import Column, DateTime, event
from sqlalchemy.orm import declarative_mixin

def utcnow():
    return datetime.utcnow()

@declarative_mixin
class TimestampMixin:
    """
    On INSERT:
      - created_at gets default utcnow()
      - updated_at is then set equal to created_at (via listener)
    On UPDATE:
      - developers can manually set updated_at if desired
    """
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, nullable=False)

# Sync updated_at to created_at on insert
@event.listens_for(TimestampMixin, "before_insert", propagate=True)
def _timestamp_before_insert(mapper, connection, target):
    # Ensure updated_at exactly equals created_at
    target.updated_at = target.created_at
