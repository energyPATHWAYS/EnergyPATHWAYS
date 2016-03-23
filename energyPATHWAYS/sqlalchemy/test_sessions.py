import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, backref, validates, reconstructor
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from data_provider import engine, Session
import sys, time
import datetime as dt
#from generated import *
import pandas as pd
import unittest

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
    print '%s: %0.4f s' % (prefix, end - start)


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

class Test(Base):
    __tablename__ = 'Test'

    raw_data = None

    def __init__(self, name):
        self.name = name

    id = sa.Column( sa.Integer, primary_key=True )
    name = sa.Column( sa.String )
    data = relationship( TestData,order_by=TestData.id, back_populates='parent')



class SessionTest(unittest.TestCase):
    def setUp(self):
        metadata.drop_all(engine)
        metadata.create_all(engine)

        # connect to the database, open a transaction, and bind a 
        # new session to the transaction in progress
        #self.connection = engine.connect()
        #self.trans = self.connection.begin()
        #self.session = Session(bind=self.connection)
        with timed('Create test data'):
            self.createTestData()

    def createTestData(self):
        # use the session in tests.
        session = Session()
        t = Test('hallo!')

        session.add( t )
        session.flush()  # force flush to the db to ensure that the Parent object has an id
        #print(t.id)
        # load 10000 rows of test data quickly with a bulk insert
        # see http://docs.sqlalchemy.org/en/latest/faq/performance.html#i-m-inserting-400-000-rows-with-the-orm-and-it-s-really-slow
        session.bulk_insert_mappings(
            TestData,
            [
                dict(name="NAME " + str(i),
                    parent_id=t.id,
                    intVal=i, 
                    floatVal=i*1.0, 
                    date=dt.datetime.now())
                for i in xrange(10000)
            ]
        )
        # t.data = [
        #     TestData( 'foo',1,14.5,dt.datetime.now() ),
        #     TestData( 'bar',12,14.5,dt.datetime.now() ),
        #     TestData( 'asd',41,14.5,dt.datetime.now() ),

        # ]
        
        session.commit()


    def test_ORM_object_select(self):
        session = Session()
        with timed():
            foo = session.query(TestData).filter(TestData.parent_id==1).all()
            print '%d TestData objects instantiated' % len(foo)
            print 'Conversion of objects into data frame TBD!'
        session.close()

    def test_core_data_select(self):
        from sqlalchemy.sql import select
        session = Session()
        tid = session.query(Test.id).first()[0]
        session.close()
        print(tid)
        session = Session()
        with timed('Core sql'):
            s = select([TestData]).where(TestData.__table__.c.parent_id == tid)
            df = pd.read_sql_query(s,engine)
            #print(df)

        print 'TestData returned as DataFrame %d x %d' % df.shape
        session.close()


    def tearDown(self):
        # close the session and roll back changes to keep the db 
        # in pristine condition
        #self.session.close()
        #self.trans.rollback()
        # return connection to the Engine
        #self.connection.close()
        pass

if __name__ == '__main__':
    unittest.main()