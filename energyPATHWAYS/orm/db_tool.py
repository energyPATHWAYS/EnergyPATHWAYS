# -*- coding: utf-8 -*-
__author__ = 'Sam'

import sqlalchemy
# import sqlalchemy.orm
# from sqlalchemy.orm import sessionmaker, backref, validates, reconstructor
# from sqlalchemy.orm import relationship
import psycopg2

import sys, time, os
import datetime as dt
#from generated import *
import pandas as pd

# this should populate DataMapper.metadata
# order matters, so system tables go first
from energyPATHWAYS.data_models.system import *
#from energyPATHWAYS.data_models.geography import *
#from energyPATHWAYS.data_models.demand import *

from energyPATHWAYS.data_models.data_mapper import DataMapper
from energyPATHWAYS.data_models.data_source import Base
from sqlalchemy.engine.url import URL

def prompt(text,default='',compare=None):
    txt = raw_input(text)
    if(txt == ''): txt = default
    if compare is not None:
        return txt.lower() in compare
    else:
        return txt

class DB:
    def __init__(self,legacy_db_conf, new_db_conf, existing_db=None):
        new_db = {}
        legacy_db = {}
        legacy_db['conf'] = legacy_db_conf
        new_db['conf'] = new_db_conf
        if existing_db is not None:
            existing_db_conf = new_db_conf.copy()
            existing_db_conf['database'] = existing_db
            new_db['existing_conf'] = existing_db_conf
        new_db['engine'] = sqlalchemy.create_engine(URL(**new_db_conf)) #,echo=True)
        new_db['Session'] = sqlalchemy.orm.sessionmaker(bind=new_db['engine'])

        conn_str = "host='%s' dbname='%s' user='%s'" % (legacy_db_conf['pg_host'], legacy_db_conf['pg_database'], legacy_db_conf['pg_user'])
        if legacy_db_conf['pg_password']:
            conn_str += " password='%s'" % legacy_db_conf['pg_password']
        legacy_db['con'] = psycopg2.connect(conn_str)

        self.new_db = new_db
        self.legacy_db = legacy_db


    def run_sql(self, file_name, target='new'):
        raw_sql = None
        out = None
        with open(file_name, "r") as sql_file:
            raw_sql = sql_file.read()
        
        if target in ('legacy','old'):
            with self.legacy_db['con'].cursor() as cursor:
                out = cursor.execute(raw_sql).execution_options(autocommit=True)
        # note that not all DB drivers support multi-statement SQL strings as would be found in an ETL script
        # this code assumes that the driver will. This is true for psycopg2. sqlite3 has conn.executescript
        # Not sure about MySQL
        elif target in ('new'):
            conn = self.new_db['engine'].connect()
            out = conn.execute(raw_sql).execution_options(autocommit=True)
        else: 
            raise ValueError('Unrecognized target %s should be legacy or new' % (target))
        return out

    def get_engine_for_existing(self):
        engine = sqlalchemy.create_engine(URL(**self.new_db['existing_conf']))
        return engine

    def create_new_db(self):
        db_name = self.new_db['conf']['database']
        print('Creating new database %s' % (db_name) )
        conn = self.get_engine_for_existing().connect()
        # conns open with transactions. Create DB cannot run inside a transaction.
        conn.execute("commit") 

        create_stmt = sqlalchemy.sql.text("create database %s" % (db_name))
        conn.execute(create_stmt)
        conn.close()

    def drop_new_db(self):
        db_name = self.new_db['conf']['database']
        print('Dropping database %s' % (db_name) )
        conn = self.get_engine_for_existing().connect()
        # conns open with transactions. Create DB cannot run inside a transaction.
        conn.execute("commit") 

        drop_stmt = sqlalchemy.sql.text("drop database %s" % (db_name))
        conn.execute(drop_stmt)
        conn.close()

    def check_new_db(self):
        try:
            #print self.new_db['engine']
            conn = self.new_db['engine'].connect()
            conn.execute("select 1")
            conn.close()
        except sqlalchemy.exc.OperationalError: # no db of that name
            db_name = self.new_db['conf']['database']
            create = prompt("Target database %s doesn't exist create it (yes/no)? [yes]:" % (db_name), 
                                default='yes', 
                                compare=('t','true','y','yes','1') )
            if create:
                self.create_new_db()

    def drop_all_new(self):
        self.new_db['metadata'].drop_all(self.new_db['engine'])

    def create_all_new(self):
        self.check_new_db()
        print 'creating tables from class metadata:'
        print '\n'.join([t.name for t in Base.metadata.sorted_tables])
        Base.metadata.create_all(bind=self.new_db['engine'])
        #DataMapper.metadata.create_all(bind=self.new_db['engine'])



if __name__ == '__main__':
    import dbConf

    legacy_db_conf = { 
        'pg_host' : 'localhost',
        # your postgres username
        'pg_user' : 'postgres',
        # your postgres password, if required
        'pg_password' : 'postgres',
        # the name of the pathways database you'd like to use
        'pg_database' : 'sandbox'
    }

    new_db_conf = dbConf.new_conf
    db = DB( legacy_db_conf, new_db_conf, existing_db='sandbox' )

    db.create_all_new()


