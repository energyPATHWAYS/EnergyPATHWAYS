#
# Created 19 Sep 2017
# @author: Rich Plevin
#
# Database abstraction layer. Postgres for now, CSV files later, probably.
#
from __future__ import print_function
from collections import defaultdict
import gzip
import os
import pandas as pd
import psycopg2
import re

pd.set_option('display.width', 200)

# Set to zero to read unlimited rows
RowLimitForDebugging = 2000

if RowLimitForDebugging:
    print("\n*** Limiting to %d rows for debugging! ***\n" % RowLimitForDebugging)

from .error import PathwaysException, RowNotFound, DuplicateRowsFound, SubclassProtocolError

# TBD: move these to utils when merging code
import pkgutil
import io

def getResource(relpath):
    """
    Extract a resource (e.g., file) from the given relative path in
    the energyPATHWAYS package.

    :param relpath: (str) a path relative to the energyPATHWAYS package
    :return: the file contents
    """
    contents = pkgutil.get_data('energyPATHWAYS', relpath)
    return contents

def resourceStream(relpath):
    """
    Return a stream on the resource found on the given path relative
    to the pygcam package.

    :param relpath: (str) a path relative to the pygcam package
    :return: (file-like stream) a file-like buffer opened on the desired resource.
    """
    text = getResource(relpath)
    return io.BytesIO(text)

_Tables_to_ignore = [
    '.*Type(s)?$'       # anything ending in Type or Types
    'CleaningMethods',
    'Currencies',
    'CurrenciesConversion',
    'CurrencyYears',
    'DayHour',
    'DayType',
    'Definitions',
    'GeographyIntersection',
    'GreenhouseGases',
    'IDMap',
    'IndexLevels',
    'InflationConversion',
    'Month',
    'OptPeriods',
    'ShapesUnits',
    'StockDecayFunctions',
    'StockRolloverMethods',
    'TimeZones',
    'YearHour',
    'DispatchConfig',
    'DispatchFeeders',
    'DispatchFeedersData',
    'DispatchNodeConfig',
    'DispatchNodeData',
    'DispatchWindows'
]


class AbstractTable(object):
    def __init__(self, db, tbl_name, cache_data=False):
        self.db = db
        self.name = tbl_name
        self.cache_data = cache_data
        self.data = None
        self.columns = None
        self.children_by_fk_col = {}
        self.data_class = None

        if cache_data:
            self.load_all()

    def __str__(self):
        return "<%s %s>" % (self.__class__.__name__, self.name)

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


class PostgresTable(AbstractTable):
    """
    Implementation of AbstractTable based on the postgres database.
    """
    def __init__(self, db, tbl_name, cache_data=False):
        super(PostgresTable, self).__init__(db, tbl_name, cache_data=cache_data)

    def load_rows(self, id):
        query = 'select * from "{}" where id={}'.format(self.name, id)
        tups = self.db.fetchall(query)
        return tups

    def load_all(self):
        if self.cache_data and self.data is not None:
            return self.data

        tbl_name = self.name
        query = """select column_name, data_type from INFORMATION_SCHEMA.COLUMNS 
                   where table_name = '%s' and table_schema = 'public'""" % tbl_name
        self.columns = self.db.fetchcolumn(query)

        query = 'select * from "%s"' % tbl_name
        if RowLimitForDebugging:
            query += ' limit %d' % RowLimitForDebugging

        rows = self.db.fetchall(query)
        self.data = pd.DataFrame.from_records(data=rows, columns=self.columns, index=None)
        rows, cols = self.data.shape
        print("Cached %d rows, %d cols for table '%s'" % (rows, cols, tbl_name))
        return self.data

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
        if self.data is not None:
            return self.data

        tbl_name = self.name
        filename = self.db.file_for_table(tbl_name)

        index_col = None    # or should it be 'id'?

        if filename.endswith('.gz'):
            with gzip.open(filename, 'rb') as f:
                df = pd.read_csv(f, index_col=index_col)
        else:
            df = pd.read_csv(filename, index_col=index_col)

        self.data = df
        # self.data.fillna(value=None, inplace=True)        # TBD: can't fill with None; check preferred handling
        rows, cols = self.data.shape
        print("Cached %d rows, %d cols for table '%s' from %s" % (rows, cols, tbl_name, filename))
        return self.data


# The singleton object
_Database = None

def get_database():
    return _Database

def forget_database():
    global _Database
    _Database = None


class ForeignKey(object):
    """"
    A simple data-only class to store foreign key information
    """

    # dict keyed by parent table name, value is list of ForeignKey instances
    fk_by_parent = defaultdict(list)

    __slots__ = ['table_name', 'column_name', 'foreign_table_name', 'foreign_column_name']

    def __init__(self, tbl_name, col_name, for_tbl_name, for_col_name):
        self.table_name = tbl_name
        self.column_name = col_name
        self.foreign_table_name  = for_tbl_name
        self.foreign_column_name = for_col_name

        ForeignKey.fk_by_parent[tbl_name].append(self)

    def __str__(self):
        return "<ForeignKey %s.%s -> %s.%s>" % (self.table_name, self.column_name,
                                               self.foreign_table_name, self.foreign_column_name)

class AbstractDatabase(object):
    """
    A simple Database class that caches table data and provides a few fetch methods.
    Serves as a base for a CSV-based subclass and a PostgreSQL-based subclass.
    """
    def __init__(self, table_class, cache_data=False):
        self.cache_data = cache_data
        self.table_class = table_class
        self.table_objs = {}              # dict of table instances keyed by name
        self.table_names = {}             # all known table names

    @classmethod
    def _get_database(cls, **kwargs):
        global _Database

        if not _Database:
            _Database = cls(**kwargs)
            _Database._cache_table_names()

        return _Database

    def get_tables_names(self):
        raise SubclassProtocolError(self.__class__, 'get_table_names')

    def _cache_table_names(self):
        self.table_names = {name: True for name in self.get_tables_names()}

    def is_table(self, name):
        return self.table_names.get(name, False)

    def get_table(self, name):
        try:
            return self.table_objs[name]
        except KeyError:
            tbl = self.table_objs[name] = self.table_class(self, name, cache_data=self.cache_data)
            return tbl

    def tables_with_classes(self):
        tables = self.get_tables_names()
        result = filter(lambda name: not any([re.match(pattern, name) for pattern in _Tables_to_ignore]), tables)
        return result

    def _cache_foreign_keys(self):
        raise SubclassProtocolError(self.__class__, '_cache_foreign_keys')

    # def fk_from_table(self, table_name):
    #     return self.foreign_keys.query('table_name == "%s"' % table_name)

    # def fk_to_table(self, table_name):
    #     return self.foreign_keys.query('foreign_table_name == "%s"' % table_name)

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

# Selects all foreign key information for current database
ForeignKeyQuery = '''
SELECT
    x.table_name,
    x.column_name,
    y.table_name AS foreign_table_name,
    y.column_name AS foreign_column_name
FROM information_schema.referential_constraints c
JOIN information_schema.key_column_usage x
    ON x.constraint_name = c.constraint_name
JOIN information_schema.key_column_usage y
    ON y.ordinal_position = x.position_in_unique_constraint
    AND y.constraint_name = c.unique_constraint_name
ORDER BY c.constraint_name, x.ordinal_position;
'''

class PostgresDatabase(AbstractDatabase):
    def __init__(self, host='localhost', dbname='pathways', user='postgres', password='',
                 cache_data=False):
        super(PostgresDatabase, self).__init__(table_class=PostgresTable, cache_data=cache_data)

        conn_str = "host='%s' dbname='%s' user='%s'" % (host, dbname, user)
        if password:
            conn_str += " password='%s'" % password

        self.con = psycopg2.connect(conn_str)
        self.cur = self.con.cursor()
        self._cache_foreign_keys()

    def _get_tables_of_type(self, tableType):
        query = "select table_name from INFORMATION_SCHEMA.TABLES where table_schema = 'public' and table_type = '%s'" % tableType
        result = self.fetchcolumn(query)
        return result

    def get_tables_names(self):
        return self._get_tables_of_type('BASE TABLE')

    def get_views(self):
        return self._get_tables_of_type('VIEW')

    def get_columns(self, table):
        query = "select column_name from INFORMATION_SCHEMA.COLUMNS where table_name = '%s' and table_schema = 'public'" % table
        result = self.fetchcolumn(query)
        return result

    @classmethod
    def get_database(cls, host='localhost', dbname='pathways', user='postgres', password='',
                     cache_data=False):
        db = cls._get_database(host=host, dbname=dbname, user=user, password=password,
                               cache_data=cache_data)
        return db

    def _cache_foreign_keys(self):
        rows = self.fetchall(ForeignKeyQuery)
        for row in rows:
            ForeignKey(*row)

    def save_foreign_keys(self, pathname):
        rows = self.fetchall(ForeignKeyQuery)
        columns = ['table_name', 'column_name', 'foreign_table_name', 'foreign_column_name']
        df = pd.DataFrame(data=rows, columns=columns)
        df.to_csv(pathname, index=None)

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
        self._cache_foreign_keys()

    def get_tables_names(self):
        return self.file_map.keys()

    @classmethod
    def get_database(cls, pathname=None):
        db = cls._get_database(pathname=pathname)
        return db

    def _cache_foreign_keys(self):
        """
        The CSV database reads the foreign key data that was exported from postgres.
        """
        stream = resourceStream('data/foreign_keys.csv')
        df = pd.read_csv(stream, index_col=None)
        for _, row in df.iterrows():
            row = tuple(row)
            ForeignKey(*row)

    def create_file_map(self):
        pathname = self.pathname

        if not os.path.exists(pathname):
            raise PathwaysException('Database path "%s" does not exist')

        if not os.path.isdir(pathname):
            raise PathwaysException('Database path "%s" is not a directory')

        for root, dir, files in os.walk(pathname):
            csv_files = filter(lambda fn: fn.endswith('.csv') or fn.endswith('csv.gz'), files)
            for csv in csv_files:
                basename = os.path.basename(csv)
                tbl_name = basename.split('.')[0]
                path = os.path.join(root, csv)
                self.file_map[tbl_name] = path

        print("Found %d .CSV files for '%s'" % (len(self.file_map), pathname))

    def file_for_table(self, tbl_name):
        return self.file_map.get(tbl_name)


