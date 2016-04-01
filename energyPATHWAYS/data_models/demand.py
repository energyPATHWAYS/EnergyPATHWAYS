from data_source import Base
from data_mapper import DataMapper
from sqlalchemy import Column, Float, ForeignKey, Integer, Text, text
from sqlalchemy.orm import relationship, reconstructor
from system import CleaningMethod, InputType, OtherIndex
from geography import Geography, GeographyMapKey

class DemandDriver(DataMapper):
    __tablename__ = 'DemandDrivers'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandDrivers_id_seq\"'::regclass)"))
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

class DemandDriverData(Base):
    __tablename__ = 'DemandDriversData'

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey(DemandDriver.id))
    gau_id = Column(Integer)  # TODO: ForeignKey('Geography.id')
    oth_1_id = Column(Integer)  # TODO: ForeignKey('???')
    oth_2_id = Column(Integer)
    year = Column(Integer)
    value = Column(Float)
    demand_driver = relationship(DemandDriver, order_by=id, backref='data')