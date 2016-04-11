from data_source import Base
from sqlalchemy import Column, Integer, Text, UniqueConstraint, ForeignKey
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

    geography = relationship(Geography)


class GeographyMapKey(Base):
    __tablename__ = 'GeographyMapKeys'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)