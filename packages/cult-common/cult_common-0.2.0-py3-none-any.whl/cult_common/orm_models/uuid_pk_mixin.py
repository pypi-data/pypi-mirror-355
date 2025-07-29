import uuid
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID

class UUIDPKMixin:
    """
    SQLAlchemy mixin for a UUID primary key.
    """
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)