# -*- coding: utf-8 -*-
__author__ = 'Sam'

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, backref, validates, reconstructor
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.sql import select # for fast core queries

from data_provider import engine, Session
import sys, time
import datetime as dt
#from generated import *
import pandas as pd
import unittest as ut

import cProfile
import StringIO
import pstats
import contextlib

Base = declarative_base()
metadata = Base.metadata

@contextlib.contextmanager
def profiled():
    pr = cProfile.Profile()
    pr.enable()
    yield
    pr.disable()
    s = StringIO.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats()
    # uncomment this to see who's calling what
    # ps.print_callers()
    print s.getvalue()

@contextlib.contextmanager
def timed(prefix='time'):
    start = time.time()
    yield
    end = time.time()
    print '%s: %0.4fs' % (prefix, end - start)


class TestData(Base):
    __tablename__ = 'TestData'

    def __init__(self, name, intVal, floatVal, date):
        self.name = name
        self.intVal = intVal
        self.floatVal = floatVal
        self.date = date

    id        = sa.Column( sa.Integer, primary_key=True )
    parent_id = sa.Column( sa.Integer,sa.ForeignKey('Test.id') )
    parent    = relationship("Test", back_populates="data")
    name      = sa.Column( sa.String )
    intVal    = sa.Column( sa.Integer )
    floatVal  = sa.Column( sa.Float )
    date      = sa.Column( sa.DateTime )

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
        
class Test(Base, RawDataHelp):
    __tablename__ = 'Test'

    #all_raw_data = None

    def __init__(self, name):
        self.name = name
        #self.raw_data = None

    id = sa.Column( sa.Integer, primary_key=True )
    name = sa.Column( sa.String )
    data = relationship( TestData,order_by=TestData.id, back_populates='parent')



class SQLAlchemyTest(ut.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # TODO: note that leaving this here allows for inspection of 
        # side effects after the code runs, but then cleaning it out 
        # before the next run. Proper usage should be to drop_all in
        # tearDownClass
        metadata.drop_all(engine)  
        metadata.create_all(engine) 

        
        with timed('Create test data'):
            SQLAlchemyTest.createTestData()

        # connect to the database, open a transaction, and bind a 
        # new session to the transaction in progress
        #self.connection = engine.connect()
        #self.trans = self.connection.begin()
        #self.session = Session(bind=self.connection)

    @classmethod
    def tearDownClass(cls):
        #metadata.drop_all(engine)
        pass

    @classmethod
    def createTestData(cls):
        # use the session in tests.
        session = Session()
        t  = Test('hallo!')
        t2 = Test('hullo!')
        session.add( t  )
        session.add( t2 )
        session.flush()  # force flush to the db to ensure that the Parent object has an id
        #print(t.id)
        # load 10000 rows of test data quickly with a bulk insert
        # see http://docs.sqlalchemy.org/en/latest/faq/performance.html#i-m-inserting-400-000-rows-with-the-orm-and-it-s-really-slow
        n = 10000
        session.bulk_insert_mappings(
            TestData,
            [
                dict(name="NAME " + str(i),
                    parent_id=t.id,
                    intVal=i, 
                    floatVal=i*1.0, 
                    date=dt.datetime.now())
                for i in xrange( n )
            ]
        )

        session.bulk_insert_mappings(
            TestData,
            [
                dict(name="NAME " + str(i),
                    parent_id=t2.id,
                    intVal=i, 
                    floatVal=i*1.0, 
                    date=dt.datetime.now())
                for i in xrange( n )
            ]
        )
        # t.data = [
        #     TestData( 'foo',1,14.5,dt.datetime.now() ),
        #     TestData( 'bar',12,14.5,dt.datetime.now() ),
        #     TestData( 'asd',41,14.5,dt.datetime.now() ),

        # ]
        
        session.commit()

    def setUp(self):
        pass # see class setup

    def tearDown(self):
        # close the session and roll back changes to keep the db 
        # in pristine condition
        #self.session.close()
        #self.trans.rollback()
        # return connection to the Engine
        #self.connection.close()
        #metadata.drop_all(engine)
        pass

    def test_ORM_object_select(self):
        session = Session()
        with timed('ORM objects'):
            foo = session.query(TestData).filter(TestData.parent_id==1).all()
            print '%d TestData objects instantiated' % len(foo)
            print 'Conversion of objects into data frame TBD!'
        session.close()

    def test_core_data_select(self):
        from sqlalchemy.sql import select
        session = Session()
        t = session.query(Test).first()
        session.close() # TODO: for some reason, without this close, the subsequent call takes > 1 second!
        session = Session()
        with timed('Core sql into pd.DF'):
            s = select([ globals()['TestData'] ]).where(TestData.__table__.c.parent_id == t.id)
            df = pd.read_sql_query(s,engine)
            #print(df)

        print 'TestData returned as DataFrame %d x %d' % df.shape
        session.close()

    def test_load_class_data(self):
        session = Session()
        t = session.query(Test).first()

        self.assertIsNotNone( Test.getAllRawData() )
        rd = t.getRawData() # throws attribute error if not found

        self.assertIsNotNone( Test.all_raw_data )
        self.assertIsNotNone( t.raw_data )
        self.assertTrue( (rd.parent_id == t.id).all() )


if __name__ == '__main__':
    ut.main()