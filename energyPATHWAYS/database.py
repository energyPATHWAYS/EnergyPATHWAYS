#
# Created 19 Sep 2017
# @author: Rich Plevin
#
# Database abstraction layer. Postgres for now, CSV files later, probably.
#
from __future__ import print_function
import pandas as pd
import psycopg2

from .error import RowNotFound, DuplicateRowsFound


class Table(object):
    def __init__(self, db, tbl_name, cache_data=False):
        self.db   = db
        self.name = tbl_name

        query = """select column_name, data_type from INFORMATION_SCHEMA.COLUMNS 
                   where table_name = '%s' and table_schema = 'public'""" % tbl_name
        self.columns = db.fetchcolumn(query)

        if cache_data:
            rows = db.fetchall('select * from "%s"' % tbl_name)
            self.data = pd.DataFrame.from_records(data=rows, columns=self.columns, index=None)
            rows, cols = self.data.shape
            print("Cached data for %s (%d row, %d cols)" % (tbl_name, rows, cols))
        else:
            self.data = None


    def get_row(self, id, raise_error=True):
        """
        Get a tuple for the row with the given id in the table associated with this class.
        Expects to find exactly one row with the given id. User must instantiate the database
        prior before calling this method.

        :param id: (int) the unique id of a row in `table`
        :param raise_error: (bool) whether to raise an error or return None if the id
           is not found.
        :return: (tuple) of values in the order the columns are defined in the table
        :raises RowNotFound: if raise_error is True and `id` is not present in `table`.
        """
        name = self.name

        if self.data is not None:
            print('Getting row for %s id=%d from cache' % (name, id))
            rows = self.data.query("id == %d" % id)
            print(rows)
            tups = []
            for idx, row in rows.iterrows():
                tups.append(tuple(row))
        else:
            print('Getting row for %s id=%d from database' % (name, id))
            query = 'select * from "{}" where id={}'.format(name, id)
            tups = self.db.fetchall(query)

        count = len(tups)
        if count == 0:
            if raise_error:
                raise RowNotFound(name, id)
            else:
                return None

        if count > 1:
            raise DuplicateRowsFound(name, id)

        return tups[0]


class Database(object):

    singleton = None

    def __init__(self, host, dbname, user, password, cache_data=False):
        conn_str = "host='%s' dbname='%s' user='%s'" % (host, dbname, user)
        if password:
            conn_str += " password='%s'" % password

        self.con = psycopg2.connect(conn_str)
        self.cur = self.con.cursor()

        self.cache_data = cache_data

        self.tables = {}    # dict of table instances keyed by name

    @classmethod
    def get_database(cls, host='localhost', dbname='postgres', user='pguser',
                     password='', cache_data=False):
        if not cls.singleton:
            cls.singleton = cls(host, dbname, user, password, cache_data=cache_data)

        return cls.singleton

    def get_table(self, name):
        try:
            return self.tables[name]
        except KeyError:
            tbl = self.tables[name] = Table(self, name, cache_data=self.cache_data)
            return tbl

    def fetchone(self, sql):
        self.cur.execute(sql)
        tup = self.cur.fetchone()
        return tup

    def fetchcolumn(self, sql):
        rows = self.fetchall(sql)
        return [row[0] for row in rows]

    def fetchall(self, sql):
        self.cur.execute(sql)
        rows = self.cur.fetchall()
        return rows

    def get_row_from_table(self, name, id, raise_error=True):
        tbl = self.get_table(name)
        tup = tbl.get_row(id, raise_error=raise_error)
        return tup

