#
# Created 19 Sep 2017
# @author: Rich Plevin
#
# Database abstraction layer. Postgres for now, CSV files later, probably.
#
from __future__ import print_function
import os
import pandas as pd
import psycopg2

from .error import PathwaysException, RowNotFound, DuplicateRowsFound, SubclassProtocolError


class AbstractTable(object):
    def __init__(self, db, tbl_name, cache_data=False):
        self.db = db
        self.name = tbl_name
        self.cache_data = cache_data
        self.data = None
        self.columns = None

        if cache_data:
            self.load_all()

    def load_rows(self, id, raise_error=True):
        """
        Load row(s) of data for the given id from the external storage (database, csv file).
        This method will differ by subclass, whereas getting data from an internal cache
        will not.

        :param id: (int) primary key for the data in `table`
        :param raise_error: (bool) whether to raise an error or return None
           if the id is not found.
        :return:
        """
        raise SubclassProtocolError(self.__class__, 'load_rows')

    def load_all(self):
        """
        Abstract method to load all rows from a table as a DataFrame.

        :return: (pd.DataFrame) The contents of the table.
        """
        raise SubclassProtocolError(self.__class__, 'load_all')

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
            tups = self.load_rows(id, raise_error=raise_error)

        count = len(tups)
        if count == 0:
            if raise_error:
                raise RowNotFound(name, id)
            else:
                return None

        if count > 1:
            raise DuplicateRowsFound(name, id)

        return tups[0]


class SqlTable(AbstractTable):
    """
    Implementation of AbstractTable based on the postgres database.
    """
    def __init__(self, db, tbl_name, cache_data=False):
        super(SqlTable, self).__init__(db, tbl_name, cache_data=cache_data)

    def load_rows(self, id):
        query = 'select * from "{}" where id={}'.format(self.name, id)
        tups = self.db.fetchall(query)
        return tups

    def load_all(self):
        tbl_name = self.name
        query = """select column_name, data_type from INFORMATION_SCHEMA.COLUMNS 
                   where table_name = '%s' and table_schema = 'public'""" % tbl_name
        self.columns = self.db.fetchcolumn(query)

        rows = self.db.fetchall('select * from "%s"' % tbl_name)
        self.data = pd.DataFrame.from_records(data=rows, columns=self.columns, index=None)
        rows, cols = self.data.shape
        print("Cached %d rows, %d cols for table '%s'" % (rows, cols, tbl_name))


class CsvTable(AbstractTable):
    """
    Implementation of AbstractTable based on a directory of CSV files.
    Note: CsvTable always caches data, so the cache_data flag is ignored.
    """
    def __init__(self, db, tbl_name, cache_data=None):
        super(CsvTable, self).__init__(db, tbl_name, cache_data=True)
        self.columns = self.data.columns

    def load_rows(self, id):
        raise PathwaysException("CsvTable.load_rows should not be called since the CSV file is always cached")

    def load_all(self):
        tbl_name = self.name
        filename = self.db.file_for_table(tbl_name)
        self.data = pd.read_csv(filename)
        # self.data.fillna(value=None, inplace=True)        # TBD: can't fill with None; check preferred handling
        rows, cols = self.data.shape
        print("Cached %d rows, %d cols for table '%s' from %s" % (rows, cols, tbl_name, filename))


# The singleton object
_Database = None

def get_database():
    return _Database

def forget_database():
    global _Database
    _Database = None

class AbstractDatabase(object):
    def __init__(self, table_class, cache_data=False):
        self.cache_data = cache_data
        self.table_class = table_class
        self.tables = {}                # dict of table instances keyed by name

    @classmethod
    def _get_database(cls, **kwargs):
        global _Database

        if not _Database:
            _Database = cls(**kwargs)

        return _Database

    def get_table(self, name):
        try:
            return self.tables[name]
        except KeyError:
            tbl = self.tables[name] = self.table_class(self, name, cache_data=self.cache_data)
            return tbl

    def fetchcolumn(self, sql):
        rows = self.fetchall(sql)
        return [row[0] for row in rows]

    def fetchone(self, sql):
        raise SubclassProtocolError(self.__class__, 'fetchone')

    def fetchall(self, sql):
        raise SubclassProtocolError(self.__class__, 'fetchall')

    def get_row_from_table(self, name, id, raise_error=True):
        tbl = self.get_table(name)
        tup = tbl.get_row(id, raise_error=raise_error)
        return tup


class SqlDatabase(AbstractDatabase):

    def __init__(self, host='localhost', dbname='pathways', user='postgres', password='',
                 cache_data=False):
        super(SqlDatabase, self).__init__(table_class=SqlTable, cache_data=cache_data)

        conn_str = "host='%s' dbname='%s' user='%s'" % (host, dbname, user)
        if password:
            conn_str += " password='%s'" % password

        self.con = psycopg2.connect(conn_str)
        self.cur = self.con.cursor()

    @classmethod
    def get_database(cls, host='localhost', dbname='pathways', user='postgres', password='',
                     cache_data=False):
        db = cls._get_database(host=host, dbname=dbname, user=user, password=password,
                               cache_data=cache_data)

        return db

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


class CsvDatabase(AbstractDatabase):

    # Dict keyed by table name of filenames under the database root folder
    file_map = {}

    def __init__(self, pathname=None):
        super(CsvDatabase, self).__init__(table_class=CsvTable, cache_data=True)
        self.pathname = pathname
        self.create_file_map()

    @classmethod
    def get_database(cls, pathname=None):
        db = cls._get_database(pathname=pathname)
        return db

    def create_file_map(self):
        pathname = self.pathname

        if not os.path.exists(pathname):
            raise PathwaysException('Database path "%s" does not exist')

        if not os.path.isdir(pathname):
            raise PathwaysException('Database path "%s" is not a directory')

        for root, dir, files in os.walk(pathname):
            csv_files = filter(lambda fn: fn.endswith('.csv'), files)
            for csv in csv_files:
                tbl_name = os.path.splitext(os.path.basename(csv))[0]
                path = os.path.join(root, csv)
                self.file_map[tbl_name] = path

        print("Found %d .CSV files for '%s'" % (len(self.file_map), pathname))

    def file_for_table(self, tbl_name):
        return self.file_map.get(tbl_name)


