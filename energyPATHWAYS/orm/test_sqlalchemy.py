# -*- coding: utf-8 -*-
__author__ = 'Sam'

import sys, time, os
import datetime as dt
import pandas as pd
import unittest as ut

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, backref, validates, reconstructor
from sqlalchemy.orm import relationship

from alchemy_util import engine, Session, Base, metadata, RawDataHelp

from energyPATHWAYS.tests.profile_tools import * # profile and timer decorators

class TestClassData(Base):
    __tablename__ = 'TestData'

    def __init__(self, name, value, floatVal, date):
        self.name = name
        self.value = intVal
        self.floatVal = floatVal
        self.date = date

    id        = sa.Column( sa.Integer, primary_key=True )
    parent_id = sa.Column( sa.Integer,sa.ForeignKey('Test.id') )
    parent    = relationship("TestClass", back_populates="data")
    name      = sa.Column( sa.String )
    value     = sa.Column( sa.Integer )
    floatVal  = sa.Column( sa.Float )
    date      = sa.Column( sa.DateTime )

        
class TestClass(Base, RawDataHelp):
    __tablename__ = 'Test'

    #all_raw_data = None

    def __init__(self, name):
        self.name = name
        #self.raw_data = None

    id = sa.Column( sa.Integer, primary_key=True )
    name = sa.Column( sa.String )
    data = relationship( TestClassData,order_by=TestClassData.id, back_populates='parent')



class SQLAlchemyTest(ut.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # TODO: note that leaving this here allows for inspection of 
        # side effects after the code runs, but then cleaning it out 
        # before the next run. Proper usage should be to drop_all in
        # tearDownClass
        metadata.drop_all(engine)  
        metadata.create_all(engine) 

        
        with timer('Create test data'):
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
        t  = TestClass('hallo!')
        t2 = TestClass('hullo!')
        session.add( t  )
        session.add( t2 )
        session.flush()  # force flush to the db to ensure that the Parent object has an id
        #print(t.id)
        # load 10000 rows of test data quickly with a bulk insert
        # see http://docs.sqlalchemy.org/en/latest/faq/performance.html#i-m-inserting-400-000-rows-with-the-orm-and-it-s-really-slow
        n = 10000
        session.bulk_insert_mappings(
            TestClassData,
            [
                dict(name="NAME " + str(i),
                    parent_id=t.id,
                    value=i, 
                    floatVal=i*1.0, 
                    date=dt.datetime.now())
                for i in xrange( n )
            ]
        )

        session.bulk_insert_mappings(
            TestClassData,
            [
                dict(name="NAME " + str(i),
                    parent_id=t2.id,
                    value=i, 
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
        with timer('ORM objects'):
            foo = session.query(TestClassData).filter(TestClassData.parent_id==1).all()
            print '%d TestData objects instantiated' % len(foo)
            print 'Conversion of objects into data frame TBD!'
        session.close()

    def test_core_data_select(self):
        from sqlalchemy.sql import select
        session = Session()
        t = session.query(TestClass).first()
        session.close() # TODO: for some reason, without this close, the subsequent call takes > 1 second!
        session = Session()
        with timer('Core sql into pd.DF'):
            s = select([ globals()['TestClassData'] ]).where(TestClassData.__table__.c.parent_id == t.id)
            df = pd.read_sql_query(s,engine)
            #print(df)

        print 'TestClassData returned as DataFrame %d x %d' % df.shape
        session.close()

    def test_load_class_data(self):
        session = Session()
        t = session.query(TestClass).first()

        self.assertIsNotNone( TestClass.get_all_raw_data() )
        rd = t.get_raw_data() # throws attribute error if not found

        self.assertIsNotNone( TestClass.all_raw_data )
        self.assertIsNotNone( t.raw_data )
        self.assertTrue( (rd.parent_id == t.id).all() )
        session.close()

if __name__ == '__main__':
    ut.main()