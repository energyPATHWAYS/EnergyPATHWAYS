from data_source import Base
from sqlalchemy import Column, Integer, Text, Float, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship

class Geography(Base):
    __tablename__ = 'Geographies'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)


class GeographiesDatum(Base):
    __tablename__ = 'GeographiesData'

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    geography_id = Column(ForeignKey(Geography.id))

    # We could reasonably have, e.g. a state named "Texas" while also having an interconnection named "Texas"
    # (same name within different geographies) but we should never have two items within the *same* geography
    # with the same name.
    UniqueConstraint(geography_id, name)

    geography = relationship(Geography, backref='geographies_data', order_by=id)


class GeographyMapKey(Base):
    __tablename__ = 'GeographyMapKeys'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)


class GeographyIntersection(Base):
    __tablename__ = 'GeographyIntersection'

    id = Column(Integer, primary_key=True)


class GeographyIntersectionDatum(Base):
    __tablename__ = 'GeographyIntersectionData'

    id = Column(Integer, primary_key=True)
    intersection_id = Column(ForeignKey(GeographyIntersection.id))
    gau_id = Column(ForeignKey(GeographiesDatum.id))

    UniqueConstraint(intersection_id, gau_id)

    gau = relationship(GeographiesDatum)
    intersection = relationship(GeographyIntersection)


class GeographyMap(Base):
    __tablename__ = 'GeographyMap'

    id = Column(Integer, primary_key=True)
    intersection_id = Column(ForeignKey(GeographyIntersection.id))
    geography_map_key_id = Column(ForeignKey(GeographyMapKey.id))
    value = Column(Float(53))

    UniqueConstraint(intersection_id, geography_map_key_id)

    geography_map_key = relationship(GeographyMapKey)
    intersection = relationship(GeographyIntersection)
