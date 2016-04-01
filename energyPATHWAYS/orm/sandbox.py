import sqlalchemy

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, backref, validates, reconstructor
#from sqlalchemy.ext.automap import automap_base
from model import *
import pandas as pd
import data_provider
import sys

from alchemy_util import Base, metadata
from alchemy_util import RawDataHelp

#import ipdb

class DemandDriverData(Base):
    __tablename__ = 'DemandDriversData'

    def __init__(self, name, value, floatVal, date):
        self.name = name
        self.value = intVal
        self.floatVal = floatVal
        self.date = date

    id        = Column( Integer, primary_key=True )
    parent_id = Column( Integer, ForeignKey('DemandDriver.id') )
    parent    = relationship("DemandDriver", primaryjoin='DemandDriverData.parent_id == DemandDriver.id', back_populates="data")
    gau_id    = Column( Integer ) # TODO: ForeignKey('Geography.id')
    oth_1_id  = Column( Integer ) # TODO: ForeignKey('???')
    oth_2_id  = Column( Integer )
    year      = Column( Integer )
    value     = Column( Float ) 

class DemandDriver(Base, RawDataHelp):
    __tablename__ = 'DemandDrivers'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandDrivers_id_seq\"'::regclass)"))
    name = Column(Text)
    base_driver_id = Column(ForeignKey(u'DemandDrivers.id'))
    input_type_id = Column(ForeignKey(u'InputTypes.id'))
    unit_prefix = Column(Integer)
    unit_base = Column(Text)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    other_index_2_id = Column(ForeignKey(u'OtherIndexes.id'))
    geography_map_key_id = Column(ForeignKey(u'GeographyMapKeys.id'))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    base_driver = relationship(u'DemandDriver', remote_side=[id])
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandDriver.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    geography_map_key = relationship(u'GeographyMapKey')
    input_type = relationship(u'InputType')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandDriver.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandDriver.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandDriver.other_index_2_id == OtherIndex.id')
    data = relationship(DemandDriverData, order_by=DemandDriverData.id, back_populates='parent')

    @classmethod
    def with_data(cls, df, **kw_args):
        new_obj = cls(**kw_args)
        new_obj.raw_values = df
        # can do whatever other validation we like here too
        new_obj.validate_data
        return new_obj

    @reconstructor
    def setup(self):
        self.load_raw_values()
        self.validate_raw_values()

    #@validates(raw_values)
    def validate_raw_values(self):
        assert len(self.raw_values) > 1

    def data_table_name(self):
        return getattr(sys.modules['generated'], 't_' + self.__tablename__ + 'Data')

    def load_raw_values(self):
        self.raw_values = data_provider.load(self.data_table(), self.id)

    def save_raw_values(self):
        data_provider.save(self.data_table_name(), self.id, self.raw_values)


# FIXME: 'after_update' only happens if the object is "dirty"
# so maybe we mark some random attribute as dirty in a setter for raw_values?
# (http://stackoverflow.com/questions/29830229/force-object-to-be-dirty-in-sqlalchemy)
# that covers the case where raw_values is replaced wholesale, but would not cover in-place updates within the
# DataFrame. Also, it feels risky to dirty attributes that aren't really dirty.
# Another option would be to register an event at the level of the session being flushed, and then loop through
# all of the objects being saved (dirty or not) and see if their current raw_values are equal to what
# data_provider.load() gives, saving the raw_values if they are different. That would be more foolproof
# (assuming there's an easy way to test DataFrames for equality of contents?) but slower.
@event.listens_for(DemandDriver, 'after_update')
@event.listens_for(DemandDriver, 'after_insert')
def updated(mapper, connection, target):
    target.save_raw_values()


# class DemandDriversData(Base):
#     __tablename__ = 'DemandDriversData'
#
#     id = Column('id', ForeignKey(u'DemandDrivers.id'), primary_key=True)
#     gau_id = Column('gau_id', ForeignKey(u'GeographiesData.id'), primary_key=True)
#     oth_1_id = Column('oth_1_id', ForeignKey(u'OtherIndexesData.id'))
#     oth_2_id = Column('oth_2_id', ForeignKey(u'OtherIndexesData.id'))
#     year = Column('year', Integer, primary_key=True)
#     value = Column('value', Float(53))
#
#     demand_driver = relationship(DemandDriver)


if __name__ == '__main__':
    from alchemy_util import Session
    session = Session()

    with ipdb.launch_ipdb_on_exception():
        dd = session.query(DemandDriver).first()
        print dd.get_raw_data().head()

    session.close()

#ipdb.set_trace()