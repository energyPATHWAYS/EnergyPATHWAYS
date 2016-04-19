from data_source import Base
from data_mapper import DataMapper
from sqlalchemy import Column, Float, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import relationship, reconstructor
from system import CleaningMethod, InputType
from misc import OtherIndex, OtherIndexesDatum, Shape, ShapeUser
from geography import Geography, GeographiesDatum, GeographyMapKey


class DemandSector(ShapeUser, Base):
    __tablename__ = 'DemandSectors'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)
    shape_id = Column(ForeignKey(Shape.id))
    max_lead_hours = Column(Integer)
    max_lag_hours = Column(Integer)


class DemandDriver(DataMapper, Base):
    __tablename__ = 'DemandDrivers'

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    base_driver_id = Column(ForeignKey(u'DemandDrivers.id'))
    input_type_id = Column(ForeignKey(InputType.id))
    unit_prefix = Column(Integer)
    unit_base = Column(Text)
    geography_id = Column(ForeignKey(Geography.id))
    other_index_1_id = Column(ForeignKey(OtherIndex.id))
    other_index_2_id = Column(ForeignKey(OtherIndex.id))
    geography_map_key_id = Column(ForeignKey(GeographyMapKey.id))
    interpolation_method_id = Column(ForeignKey(CleaningMethod.id))
    extrapolation_method_id = Column(ForeignKey(CleaningMethod.id))
    extrapolation_growth = Column(Float)

    base_driver = relationship(u'DemandDriver', remote_side=[id])
    _extrapolation_method = relationship(CleaningMethod, foreign_keys='DemandDriver.extrapolation_method_id', lazy='joined') # , primaryjoin='DemandDriver.extrapolation_method_id == CleaningMethods.id'
    _geography = relationship(Geography, lazy='joined')
    _geography_map_key = relationship(GeographyMapKey, lazy='joined')
    _input_type = relationship(InputType, lazy='joined')
    _interpolation_method = relationship(CleaningMethod, foreign_keys='DemandDriver.interpolation_method_id', lazy='joined') # primaryjoin='DemandDriver.interpolation_method_id == CleaningMethods.id',
    _other_index_1 = relationship(OtherIndex, foreign_keys='DemandDriver.other_index_1_id', lazy='joined')
    _other_index_2 = relationship(OtherIndex, foreign_keys='DemandDriver.other_index_2_id', lazy='joined')

    @reconstructor
    def reconstruct(self):
        self.mapped = False
        # since we have named this as the reconstructor thus "overriding" the parent class' reconstructor,
        # we need to call it manually.
        self.read_timeseries_data()

class DemandDriverDatum(Base):
    __tablename__ = 'DemandDriversData'

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey(DemandDriver.id))
    gau_id = Column(ForeignKey(GeographiesDatum.id))
    oth_1_id = Column(ForeignKey(OtherIndexesDatum.id))
    oth_2_id = Column(ForeignKey(OtherIndexesDatum.id))
    year = Column(Integer)
    value = Column(Float)

    UniqueConstraint(parent_id, gau_id, oth_1_id, oth_2_id, year)

    gau = relationship(GeographiesDatum)
    other_index_1 = relationship(OtherIndexesDatum, foreign_keys=oth_1_id)
    other_index_2 = relationship(OtherIndexesDatum, foreign_keys=oth_2_id)
    demand_driver = relationship(DemandDriver, order_by=id, backref='data')