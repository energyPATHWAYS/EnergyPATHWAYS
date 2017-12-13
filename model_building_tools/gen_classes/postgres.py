import os
import gzip
import pandas as pd
import psycopg2
from energyPATHWAYS.database import AbstractDatabase, AbstractTable, Text_mapping_tables, ForeignKey, mkdirs
from energyPATHWAYS.error import RowNotFound, DuplicateRowsFound, SubclassProtocolError

# TODO: Abstract class copied from database.py. Integrate into Postgres{Table,Database} classes

class AbstractTable2(object):
    def __init__(self, db, tbl_name, cache_data=False):
        self.db = db
        self.name = tbl_name
        self.cache_data = cache_data
        self.data = None
        self.children_by_fk_col = {}
        self.data_class = None

        if cache_data:
            self.load_all()

    def __str__(self):
        return "<{} {}>".format(self.__class__.__name__, self.name)

    def load_rows(self, id):
        """
        Load row(s) of data for the given id from the external storage (database, csv file).
        This method will differ by subclass, whereas getting data from an internal cache
        will not.

        :param id: (int) primary key for the data in `table`
        :return:
        """
        raise SubclassProtocolError(self.__class__, 'load_rows')

    def load_all(self):
        """
        Abstract method to load all rows from a table as a DataFrame.

        :return: (pd.DataFrame) The contents of the table.
        """
        raise SubclassProtocolError(self.__class__, 'load_all')

    def load_data_object(self, cls, scenario):
        self.data_class = cls
        df = self.load_all()
        print("Loaded {} rows for {}".format(df.shape[0], self.name))

        key_col = cls._key_col
        for _, row in df.iterrows():
            key = row[key_col]
            obj = cls(key, scenario)  # adds itself to the classes _instances_by_id dict
            obj.init_from_series(row, scenario)


    def get_row(self, key_col, key, raise_error=True):
        """
        Get a tuple for the row with the given id in the table associated with this class.
        Expects to find exactly one row with the given id. User must instantiate the database
        before calling this method.

        :param key_col: (str) the name of the column holding the key value
        :param key: (str) the unique id of a row in `table`
        :param raise_error: (bool) whether to raise an error or return None if the id
           is not found.
        :return: (tuple) of values in the order the columns are defined in the table
        :raises RowNotFound: if raise_error is True and `id` is not present in `table`.
        """
        name = self.name
        query = "{} == '{}'".format(key_col, key)

        if self.data is not None:
            rows = self.data.query(query)
            # print('Getting row {} from cache'.format(query))
            # print(rows)
            tups = [tuple(row) for idx, row in rows.iterrows()]
        else:
            # print('Getting row {} from database'.format(query))
            tups = self.load_rows(key)

        count = len(tups)
        if count == 0:
            if raise_error:
                raise RowNotFound(name, key)
            else:
                return None

        if count > 1:
            raise DuplicateRowsFound(name, key)

        return tups[0]


class PostgresTable(AbstractTable):
    """
    Implementation of AbstractTable based on the postgres database.
    """
    def __init__(self, db, tbl_name, cache_data=False):
        super(PostgresTable, self).__init__(db, tbl_name, cache_data=cache_data)
        self.mapped_cols = {}    # maps original columns with IDs to added columns with strings
        self.renames = {}

    def load_rows(self, key):
        query = 'select * from "{}" where key="{}"'.format(self.name, key)
        tups = self.db.fetchall(query)
        return tups

    def load_all(self, limit=0, prefix='_'):
        if self.cache_data and self.data is not None:
            return self.data

        tbl_name = self.name
        query = """select column_name, data_type from INFORMATION_SCHEMA.COLUMNS 
                   where table_name = '{}' and table_schema = 'public'""".format(tbl_name)
        columns = self.db.fetchcolumn(query)

        query = 'select * from "{}"'.format(tbl_name)
        if limit:
            query += ' limit {}'.format(limit)

        rows = self.db.fetchall(query)
        self.data = pd.DataFrame.from_records(data=rows, columns=columns, index=None)
        rows, cols = self.data.shape
        print("Cached {} rows, {} cols for table '{}'".format(rows, cols, tbl_name))

        self.map_strings()
        return self.data

    def map_strings(self, save_ids=False):
        tbl_name = self.name
        df = self.data
        text_maps = self.db.text_maps

        fkeys = ForeignKey.fk_by_parent.get(tbl_name) or []
        for fk in fkeys:
            ftable = fk.foreign_table_name
            text_map = text_maps.get(ftable)
            if text_map is not None:
                str_col = id_col = fk.column_name

                # Special case for SupplyEfficiency (and others?)
                if str_col == 'id':
                    str_col = 'name'
                elif str_col.endswith('_id'):
                    str_col = str_col[:-3]    # strip off "_id"

                # add a column with the corresponding string value
                df[str_col] = df[id_col].map(text_map.get)

                # and record the mapping
                self.mapped_cols[id_col] = str_col

    col_renames = {
        'CurrenciesConversion':
            {'currency_year_id' : 'currency_year'},
        # 'DemandTechsServiceLink':
        #     {'service_link' : 'name'},
        'DemandTechsServiceLinkData':
            {'parent_id' : 'service_link'},
        'DispatchFeedersAllocationData':
            {'parent_id' : 'name'},
        'DispatchFeedersAllocation':
            {'id': 'name'},
        'SupplyEfficiency':
            {'id': 'name'},
    }

    def to_csv(self, db_dir, save_ids=False):
        """
        Save the cached data to a CSV file in the given "db", which is just a
        directory named with a ".db" extension, containing CSV "table" files.
        ID columns are not saved unless save_ids is True.

        :param db_dir: (str) the directory in which to write the CSV file
        :param save_ids: (bool) whether to include integer ids in the CSV file
        :return: none
        """
        name = self.name
        data = self.data
        mapped = self.mapped_cols

        renames = self.col_renames.get(name)

        # since we map the originals (to maintain order) we don't include these again
        skip = mapped.values()

        # Save text mapping tables for validation purposes, but drop the id col (unless we're renaming it)
        if name in Text_mapping_tables and not (renames and renames.get('id')) and not save_ids:
            skip.append('id')

        # Swap out str cols for id cols where they exist
        cols_to_save = [mapped.get(col, col) for col in data.columns if col not in skip]

        df = data[cols_to_save]

        if renames:
            print("Renaming columns for {}: {}".format(name, renames))
            df = df.rename(columns=renames)
            self.renames = renames

        # TBD: temp fix to make keys unique in these 4 tables
        tables_to_patch = {
            'DemandFuelSwitchingMeasures': '{name} - {subsector} - {final_energy_from} to {final_energy_to}',
            # 'DemandTechsServiceLink' : None
        }

        if name in tables_to_patch:
            df = df.copy()
            from energyPATHWAYS.database import find_key_col
            key_col = find_key_col(name, cols_to_save)
            template = tables_to_patch[name]
            for idx, row in df.iterrows():
                kwargs = {col: row[col] for col in cols_to_save}
                df.loc[idx, key_col] = template.format(**kwargs)

        # Handle special case for ShapesData. Split this 3.5 GB data file
        # into individual files for each Shape ID (translated to name)
        if name == 'ShapesData':
            dirname = os.path.join(db_dir, 'ShapeData')
            mkdirs(dirname)

            shapes = self.db.get_table('Shapes')
            shape_names = list(shapes.data.name)

            for shape_name in shape_names:
                filename = shape_name.replace(' ', '_') + '.csv.gz'
                pathname = os.path.join(dirname, filename)
                chunk = df.query('parent == "{}"'.format(shape_name))
                print("Writing {} rows to {}".format(len(chunk), pathname))
                with gzip.open(pathname, 'wb') as f:
                    chunk.to_csv(f, index=None)
        else:
            pathname = os.path.join(db_dir, name + '.csv')
            df.to_csv(pathname, index=None)

            # Also save the "skipped" columns in {table}_IDS.csv
            pathname = os.path.join(db_dir, 'ids', name + '.csv')
            columns = list(set(data.columns) - set(cols_to_save))
            if 'id' in cols_to_save:
                columns.insert(0, 'id')
            df = data[columns]
            df.to_csv(pathname, index=None)


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

class AbstractDatabase2(object):
    """
    A simple Database class that caches table data and provides a few fetch methods.
    Serves as a base for a CSV-based subclass and a PostgreSQL-based subclass.
    """
    instance = None

    def __init__(self, table_class, cache_data=False):
        self.cache_data = cache_data
        self.table_class = table_class
        self.table_objs = {}              # dict of table instances keyed by name
        self.table_names = {}             # all known table names
        self.text_maps = {}               # dict by table name of dicts by id of text mapping tables

    @classmethod
    def _get_database(cls, **kwargs):
        if not AbstractDatabase.instance:
            instance = AbstractDatabase.instance = cls(**kwargs)
            instance._cache_table_names()

        return instance

    def get_table_names(self):
        raise SubclassProtocolError(self.__class__, 'get_table_names')

    def _cache_table_names(self):
        self.table_names = {name: True for name in self.get_table_names()}

    def is_table(self, name):
        return self.table_names.get(name, False)

    def get_table(self, name):
        try:
            return self.table_objs[name]

        except KeyError:
            tbl = self.table_class(self, name, cache_data=self.cache_data)
            self.table_objs[name] = tbl
            return tbl

    def tables_with_classes(self, include_on_demand=False):
        exclude = ['CurrenciesConversion', 'GeographyMap', 'IDMap', 'InflationConversion',
                   'DispatchTransmissionHurdleRate', 'DispatchTransmissionLosses',
                   'Version', 'foreign_keys'] + Simple_mapping_tables

        # Don't create classes for "Data" tables; these are rendered as DataFrames only
        tables = [name for name in self.get_table_names() if not (name in exclude or name.endswith('Data'))]
        ignore = Tables_to_ignore + (Tables_to_load_on_demand if not include_on_demand else [])
        result = sorted(list(set(tables) - set(ignore)))
        return result

    def load_text_mappings(self):
        for name in Text_mapping_tables:
            tbl = self.get_table(name)

            # class generator needs this since we don't load entire DB
            if tbl.data is None:
                tbl.load_all()

            # some mapping tables have other columns, but we need just id and name
            id_col = 'id'
            name_col = 'name'

            df = tbl.data[[id_col, name_col]]
            # coerce names to str since we use numeric ids in some cases
            self.text_maps[name] = {id: str(name) for idx, (id, name) in df.iterrows()}

        print('Loaded text mappings')

    def get_text(self, tableName, key=None):
        """
        Get a value from a given text mapping table or the mapping dict itself,
        if key is None.

        :param tableName: (str) the name of the table that held this mapping data
        :param key: (int) the key to map to a text value, or None
        :return: (str or dict) if the key is None, return the text mapping dict
           itself, otherwise return the text value for the given key.
        """
        try:
            text_map = self.text_maps[tableName]
            if key is None:
                return text_map

            return text_map[key]
        except KeyError:
            return None

    def _cache_foreign_keys(self):
        raise SubclassProtocolError(self.__class__, '_cache_foreign_keys')

    def fetchcolumn(self, sql):
        rows = self.fetchall(sql)
        return [row[0] for row in rows]

    def fetchone(self, sql):
        raise SubclassProtocolError(self.__class__, 'fetchone')

    def fetchall(self, sql):
        raise SubclassProtocolError(self.__class__, 'fetchall')

    def get_columns(self, table):
        raise SubclassProtocolError(self.__class__, 'get_columns')

    def get_row_from_table(self, name, key_col, key, raise_error=True):
        tbl = self.get_table(name)
        tup = tbl.get_row(key_col, key, raise_error=raise_error)
        return tup


class PostgresDatabase(AbstractDatabase):
    def __init__(self, host='localhost', dbname='pathways', user='postgres', password='',
                 cache_data=False):
        super(PostgresDatabase, self).__init__(table_class=PostgresTable, cache_data=cache_data)

        conn_str = "host='{}' dbname='{}' user='{}'".format(host, dbname, user)
        if password:
            conn_str += " password='{}'".format(password)

        self.con = psycopg2.connect(conn_str)
        self.cur = self.con.cursor()
        self._cache_foreign_keys()

    def _get_tables_of_type(self, tableType):
        query = "select table_name from INFORMATION_SCHEMA.TABLES where table_schema = 'public' and table_type = '{}'".format(tableType)
        result = self.fetchcolumn(query)
        return result

    def get_table_names(self):
        return self._get_tables_of_type('BASE TABLE')

    def get_views(self):
        return self._get_tables_of_type('VIEW')

    def get_columns(self, table):
        query = "select column_name from INFORMATION_SCHEMA.COLUMNS where table_name = '{}' and table_schema = 'public'".format(table)
        result = self.fetchcolumn(query)
        return result

    @classmethod
    def get_database(cls, host='localhost', dbname='pathways', user='postgres', password='',
                     cache_data=False):
        db = cls._get_database(host=host, dbname=dbname, user=user, password=password,
                               cache_data=cache_data)
        db.load_text_mappings()
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
