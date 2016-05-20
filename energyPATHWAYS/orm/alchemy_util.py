import pandas as pd
import sqlalchemy
import sqlalchemy.orm
import dbConf
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.inspection import inspect
from sqlalchemy.sql import select # for fast core queries

engine = sqlalchemy.create_engine(URL(**dbConf.conf)) #,echo=True)
Session = sqlalchemy.orm.sessionmaker(bind=engine)

Base = declarative_base()
metadata = Base.metadata

class RawDataHelp():

    @classmethod
    def get_all_raw_data(cls):
        if( not hasattr(cls,'all_raw_data') or cls.all_raw_data is None):
            mapper = inspect(cls).mapper # get the mappings for the class
            if( not hasattr(mapper.attrs,'data')): 
                raise ValueError('RawDataHelp requires a relationship named "data" on the class it mixes into.')
            dataTable = mapper.attrs.data.table # get the table reference for the attribute called data, which should be '%sData' % ( cls.__tablename__ )
            assert isinstance(dataTable, sqlalchemy.sql.schema.Table)
            #dataClass = '%sData' % ( cls.__tablename__ )
            print '[RawDataHelp] loading all raw data for class %s' % (dataTable.name)
            # try/except for when the underlying data class in not defined
            try:
                s = select([ dataTable ]) #globals()[dataClass] ])
                # column.key is the column name; any column that doesn't contain the value for the row is an index
                #indexes = [column.key for column in dataTable.columns if column.key != 'value']
                #cls.all_raw_data = pd.read_sql_query(s, engine, index_col=indexes).sort_index()
                cls.all_raw_data = pd.read_sql_query(s, engine)
            except KeyError as ke: # TODO: trap and warn or allow to become an error?
                raise( ValueError( '%s not found as a defined class has it been added to SQLAlchemy?' % (dataTable.name) ) )
        return( cls.all_raw_data )

    def get_raw_data(self):
        if( self.id is None): raise ValueError('Class id must be set to get raw data')

        if( not hasattr(self,'raw_data') or self.raw_data is None):
            allRaw = self.get_all_raw_data()
            print allRaw.head()
            self.raw_data = allRaw.loc[ allRaw['parent_id'] == self.id]
        return self.raw_data

    def clean_and_interpolate(self):
        pass # TODO: clean and intepolate raw data