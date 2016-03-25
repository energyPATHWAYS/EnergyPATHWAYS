import pandas as pd
from sqlalchemy.sql import select # for fast core queries

class RawDataHelp():

    @classmethod
    def getAllRawData(cls):
        if( not hasattr(cls,'all_raw_data') or cls.all_raw_data is None):
            dataClass = '%sData' % ( cls.__tablename__ )
            print '[RawDataHelp] loading all raw data for class %s' % (dataClass)
            # try/except for when the underlying data class in not defined
            try:
                s = select([ globals()[dataClass] ])
                cls.all_raw_data = pd.read_sql_query(s,engine)
            except KeyError as ke: # TODO: trap and warn or allow to become an error?
                raise( ValueError( '%s not found as a defined class has it been added to SQLAlchemy?' % (dataClass) ) )
        return( cls.all_raw_data )

    def getRawData(self):
        if( self.id is None): raise ValueError('Class id must be set to get raw data')

        if( not hasattr(self,'raw_data') or self.raw_data is None):
            allRaw = self.getAllRawData()
            self.raw_data = allRaw.loc[ allRaw['parent_id'] == self.id]
        return self.raw_data

    def cleanAndInterpolate(self):
        pass # TODO: clean and intepolate raw data