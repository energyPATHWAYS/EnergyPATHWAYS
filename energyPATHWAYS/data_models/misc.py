from data_source import Base
from sqlalchemy import Column, Integer, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
import data_source


class OtherIndex(Base):
    __tablename__ = 'OtherIndexes'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)


class OtherIndexesDatum(Base):
    __tablename__ = 'OtherIndexesData'

    id = Column(Integer, primary_key=True)
    other_index_id = Column(ForeignKey(OtherIndex.id))
    name = Column(Text)

    UniqueConstraint(other_index_id, name)

    other_index = relationship(OtherIndex, backref='other_indexes_data')


class FinalEnergy(Base):
    __tablename__ = 'FinalEnergy'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)
    shape_id = Column(ForeignKey('Shapes.id'))

    shape = relationship('Shape')

    # we cache the "electricity" shape entry since it is accessed a lot
    @classmethod
    def electricity(cls):
        try:
            return cls._electricity
        except AttributeError:
            cls._electricity = data_source.fetch_one(cls, name='electricity')
            return cls._electricity