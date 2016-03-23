import sqlalchemy

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, backref, validates, reconstructor
#from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.declarative import declarative_base
from generated import *
import pandas as pd
import data_provider
import sys

import ipdb

# Using same Base as generated.py
#Base = declarative_base()

class DemandDriver(Base):
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

    #data = sqlalchemy.orm.column_property()

    #demand_drivers_data = relationship(u'DemandDriversData', lazy='dynamic') # collection_class=pd.DataFrame - doesn't work: Type DataFrame must elect a remover method to be a collection class

    @classmethod
    def with_data(cls, df, **kw_args):
        new_obj = cls(**kw_args)
        new_obj.data = df
        # can do whatever other validation we like here too
        new_obj.validate_data
        return new_obj

    @reconstructor
    def setup(self):
        self.load_data()
        self.validate_data()

    #@validates(data)
    def validate_data(self):
        assert len(self.data) > 1

    def data_table(self):
        return getattr(sys.modules['generated'], 't_' + self.__tablename__ + 'Data')

    def load_data(self):
        self.data = data_provider.load(self.data_table(), self.id)

    def save_data(self):
        data_provider.save(self.data_table(), self.id, self.data)


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


session = data_provider.Session()

with ipdb.launch_ipdb_on_exception():
    dd = session.query(DemandDriver).first()
    dd.save_data()


ipdb.set_trace()