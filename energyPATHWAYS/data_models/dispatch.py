from data_source import Base
from sqlalchemy import Column, Integer, Text


class DispatchFeeder(Base):
    __tablename__ = 'DispatchFeeders'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)