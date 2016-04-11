from data_source import Base
from data_mapper import DataMapper
from sqlalchemy import Column, Integer, Text, Float, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from system import CleaningMethod, DayType, DispatchConstraintType, FlexibleLoadShiftType, ShapesType, ShapesUnit,\
    TimeZone
from geography import Geography, GeographiesDatum, GeographyMapKey
from dispatch import DispatchFeeder


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

    other_index = relationship(OtherIndex)


class Shape(DataMapper, Base):
    __tablename__ = 'Shapes'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)
    shape_type_id = Column(ForeignKey(ShapesType.id))
    shape_unit_type_id = Column(ForeignKey(ShapesUnit.id))
    time_zone_id = Column(ForeignKey(TimeZone.id))
    geography_id = Column(ForeignKey(Geography.id))
    other_index_1_id = Column(ForeignKey(OtherIndex.id))
    other_index_2_id = Column(ForeignKey(OtherIndex.id))
    geography_map_key_id = Column(ForeignKey(GeographyMapKey.id))
    interpolation_method_id = Column(ForeignKey(CleaningMethod.id))
    extrapolation_method_id = Column(ForeignKey(CleaningMethod.id))

    extrapolation_method = relationship(CleaningMethod, primaryjoin='Shape.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(Geography)
    geography_map_key = relationship(GeographyMapKey)
    interpolation_method = relationship(CleaningMethod, primaryjoin='Shape.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(OtherIndex, primaryjoin='Shape.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(OtherIndex, primaryjoin='Shape.other_index_2_id == OtherIndex.id')
    shape_type = relationship(ShapesType)
    shape_unit_type = relationship(ShapesUnit)
    time_zone = relationship(TimeZone)


class ShapesDatum(Base):
    __tablename__ = 'ShapesData'

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer)
    gau_id = Column(ForeignKey(GeographiesDatum.id))
    dispatch_feeder_id = Column(ForeignKey(DispatchFeeder.id))
    timeshift_type_id = Column(ForeignKey(FlexibleLoadShiftType.id))
    resource_bin = Column(Integer)
    dispatch_constraint_type_id = Column(ForeignKey(DispatchConstraintType.id))
    year = Column(Integer)
    month = Column(Integer)
    week = Column(Integer)
    hour = Column(Integer)
    day_type_id = Column(ForeignKey(DayType.id))
    weather_datetime = Column(DateTime)
    value = Column(Float)

    UniqueConstraint(parent_id, gau_id, dispatch_feeder_id, timeshift_type_id, resource_bin)

    day_type = relationship(DayType)
    dispatch_feeder = relationship(DispatchFeeder)
    gau = relationship(GeographiesDatum)
    timeshift_type = relationship(FlexibleLoadShiftType)
    dispatch_constraint_type = relationship(DispatchConstraintType)