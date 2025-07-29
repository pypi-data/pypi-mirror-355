import uuid
from cult_common.orm_models.uuid_pk_mixin import UUIDPKMixin
from sqlalchemy import Column, Integer, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class TestModel(UUIDPKMixin, Base):
    __tablename__ = 'test_model'
    # include another column to satisfy SQLAlchemy
    dummy = Column(Integer)

    def __init__(self, dummy):
        self.dummy = dummy


def test_uuid_pk():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    obj = TestModel(dummy=123)
    session.add(obj)
    session.commit()

    assert isinstance(obj.id, uuid.UUID)