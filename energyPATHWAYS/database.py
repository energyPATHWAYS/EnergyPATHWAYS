#
# Created 19 Sep 2017
# @author: Rich Plevin
#
# Database abstraction layer. Postgres for now, CSV files later, probably.
#
from __future__ import print_function
from collections import defaultdict
import glob
import gzip
import numpy as np
import os
import pandas as pd
import psycopg2

pd.set_option('display.width', 200)

from .error import PathwaysException, RowNotFound, DuplicateRowsFound, SubclassProtocolError

def mkdirs(newdir, mode=0o770):
    """
    Try to create the full path `newdir` and ignore the error if it already exists.

    :param newdir: the directory to create (along with any needed parent directories)
    :return: nothing
    """
    from errno import EEXIST

    try:
        os.makedirs(newdir, mode)
    except OSError as e:
        if e.errno != EEXIST:
            raise

def find_col(candidates, cols):
    for col in candidates:
        if col in cols:
            return col
    return None

def find_key_col(cols):
    '''
    Find the key column.
    '''
    key_cols = ('name', 'parent', 'subsector', 'demand_technology', 'supply_node',
                'supply_tech', 'import_node', 'primary_node', 'index_level')
    return find_col(key_cols, cols)

def find_parent_col(cols):
    '''
    Find the column identifying the parent record.
    '''
    parent_cols = ('parent', 'subsector', 'demand_technology', 'supply_node', 'supply_tech')
    return find_col(parent_cols, cols)


# Tables with only one column
Simple_mapping_tables = [
    'AgeGrowthOrDecayType',
    'CleaningMethods',
    'Currencies',
    'DayType',
    'Definitions',
    'DemandStockUnitTypes',
    'DemandTechEfficiencyTypes',
    'DemandTechUnitTypes',
    'DispatchConstraintTypes',
    'DispatchFeeders',
    'DispatchWindows',
    'EfficiencyTypes',
    'FlexibleLoadShiftTypes',
    'Geographies',
    'GeographyMapKeys',
    'GreenhouseGasEmissionsType',
    'InputTypes',
    'OtherIndexes',
    'ShapesTypes',
    'ShapesUnits',
    'StockDecayFunctions',
    'SupplyCostTypes',
    'SupplyTypes'
]

# Tables that map strings but have other columns as well
Text_mapping_tables = Simple_mapping_tables + [
    'BlendNodeBlendMeasures',
    'CO2PriceMeasures',
    'DemandCO2CaptureMeasures',
    'DemandDrivers',
    'DemandEnergyEfficiencyMeasures',
    'DemandFlexibleLoadMeasures',
    'DemandFuelSwitchingMeasures',
    'DemandSalesShareMeasures',
    'DemandSectors',
    'DemandServiceDemandMeasures',
    'DemandServiceLink',
    'DemandStockMeasures',
    'DemandSubsectors',
    'DemandTechs',
    'DispatchTransmissionConstraint',
    'FinalEnergy',
    'GeographiesData',
    'GreenhouseGases',
    'OtherIndexesData',
    'Shapes',
    'SupplyCost',
    'SupplyExportMeasures',
    'SupplyNodes',
    'SupplySalesMeasures',
    'SupplySalesShareMeasures',
    'SupplyStockMeasures',
    'SupplyTechs',
]

Tables_to_ignore = [
    'CurrencyYears',
    'DispatchConfig',
    'GeographyIntersection',
    'GeographyIntersectionData',
    'GeographyMap',
]

Tables_to_load_on_demand = [
    'ShapesData',
]

class StringMap(object):
    """
    A simple class to map strings to integer IDs and back again.
    """
    instance = None

    @classmethod
    def getInstance(cls):
        if not cls.instance:
            cls.instance = cls()

        return cls.instance

    def __init__(self):
        self.txt_to_id = {}     # maps text to integer id
        self.id_to_txt = {}     # maps id back to text
        self.next_id = 1        # the next id to assign

    def store(self, txt):
        # If already known, return it
        id = self.get_id(txt, raise_error=False)
        if id is not None:
            return id

        id = self.next_id
        self.next_id += 1

        self.txt_to_id[txt] = id
        self.id_to_txt[id] = txt
        return id

    def get_id(self, txt, raise_error=True):
        return self.txt_to_id[txt] if raise_error else self.txt_to_id.get(txt, None)

    def get_txt(self, id, raise_error=True):
        return self.id_to_txt[id] if raise_error else self.id_to_txt.get(id, None)


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
        print("Loaded %d rows for %s" % (df.shape[0], self.name))

        # This is inefficient for Postgres since we go from list(tuple)->DataFrame->Series->tuple,
        # but eventually, for the CSV "database", it's just DataFrame->Series->tuple
        for _, row in df.iterrows():
            cls.from_series(scenario, row)  # adds itself to the classes _instances_by_id dict

    # TBD: obsolete once psql-to-csv conversion is complete
    def link_children(self, missing):
        fk_by_parent = ForeignKey.fk_by_parent

        # After loading all "direct" data, link child records via foreign keys
        parent_tbl = self
        parent_tbl_name = parent_tbl.name
        parent_cls = parent_tbl.data_class

        fkeys = fk_by_parent[parent_tbl_name]

        if not fkeys:
            return

        print("Linking table %s" % parent_tbl_name)

        for parent_obj in parent_cls.instances():
            for fk in fkeys:
                parent_col      = fk.column_name
                child_tbl_name  = fk.foreign_table_name
                child_col_name  = fk.foreign_column_name

                if missing.get(child_tbl_name):
                    continue

                child_tbl = self.db.get_table(child_tbl_name)
                child_cls = child_tbl.data_class

                if not child_cls:
                    # See if it's a text mapping class
                    key = getattr(parent_obj, parent_col)
                    if key is None or np.isnan(key):
                        continue

                    text = self.db.get_text(child_tbl_name, int(key))
                    if text is None:
                        missing[child_tbl_name] = 1
                        print("** Skipping missing table '%s'" % child_tbl_name)
                    else:
                        setattr(parent_obj, parent_col, text)       # Never encountered this line!
                    continue

                # create and save a list of all matching data class instances with matching ids
                children = [obj for obj in child_cls.instances() if getattr(obj, child_col_name) == getattr(parent_obj, parent_col)]
                parent_tbl.children_by_fk_col[parent_col] = children


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
            print('Getting row {} from cache'.format(query))
            rows = self.data.query(query)
            print(rows)
            tups = []
            for idx, row in rows.iterrows():
                tups.append(tuple(row))
        else:
            print('Getting row {} from database'.format(query))
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
        self.columns = self.db.fetchcolumn(query)

        query = 'select * from "%s"' % tbl_name
        if limit:
            query += ' limit %d' % limit

        rows = self.db.fetchall(query)
        self.data = pd.DataFrame.from_records(data=rows, columns=self.columns, index=None)
        rows, cols = self.data.shape
        print("Cached {} rows, {} cols for table '{}'".format(rows, cols, tbl_name))

        self.map_strings()
        return self.data

    def map_strings(self):
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

    def to_csv(self, db_dir):
        """
        Save the cached data to a CSV file in the given "db", which is just a
        directory named with a ".db" extension, containing CSV "table" files.
        String ID columns are not saved; string columns are saved instead.

        :param db_dir: (str) the directory in which to write the CSV file
        :return: none
        """
        name = self.name
        data = self.data
        mapped = self.mapped_cols

        renames = self.col_renames.get(name)

        # since we map the originals (to maintain order) we don't include these again
        skip = mapped.values()

        # Save text mapping tables for validation purposes, but drop the id col (unless we're renaming it)
        if name in Text_mapping_tables and not (renames and renames.get('id')):
            skip.append('id')

        # Swap out str cols for id cols where they exist
        cols_to_save = [mapped.get(col, col) for col in data.columns if col not in skip]

        df = data[cols_to_save]

        if renames:
            print("Renaming columns for %s: %s" % (name, renames))
            df.rename(columns=renames, inplace=True)

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

    def load_all(self, drop_str_cols=True):
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

        mapper = StringMap.getInstance()

        # TBD: redo this using a dict of table.column keys
        # String mapped columns are prefixed with "_"
        str_cols = [col for col in df.columns if col[0] == '_']

        for col in str_cols:
            # Ensure that all values are in the StringMap
            values = df[col].unique()
            for value in values:
                mapper.store(value)

            # change "_foo" to "foo_id"
            id_col = col[1:] + '_id'

            # create a column with integer ids
            df[id_col] = df[col].map(mapper.txt_to_id)

        if drop_str_cols:
            df.drop(str_cols, axis=1, inplace=True)

        self.data = df

        # TBD: can't fill with None; check preferred handling
        # self.data.fillna(value=None, inplace=True)

        rows, cols = self.data.shape
        print("Cached {} rows, {} cols for table '{}' from {}".format(rows, cols, tbl_name, filename))
        return self.data


class ShapeDataMgr(object):
    """
    Handles the special case of the pre-sliced ShapesData
    """
    def __init__(self, db_path):
        self.db_path = db_path
        self.tbl_name = 'ShapeData'
        self.slices = {}        # maps shape name to DF containing that shape's data rows
        self.file_map = {}

    def load_all(self):
        if self.slices:
            return self.slices

        # ShapeData is stored in gzipped slices of original 3.5 GB table.
        # The files are in a "{db_name}.db/ShapeData/{shape_name}.csv.gz"
        shape_files = glob.glob(os.path.join(self.db_path, self.tbl_name, '*.csv.gz'))

        for filename in shape_files:
            basename = os.path.basename(filename)
            shape_name = basename.split('.')[0]

            with gzip.open(filename, 'rb') as f:
                print("Reading shape data for {}".format(shape_name))
                df = pd.read_csv(f, index_col=None)
                self.slice[shape_name] = df

    def get_slice(self, name):
        name = name.replace(' ', '_')
        return self.slice[name]

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
        return "<ForeignKey {}.{} -> {}.{}>".format(self.table_name, self.column_name,
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
        self.text_maps = {}               # dict by table name of dicts by id of text mapping tables

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

    def tables_with_classes(self, include_on_demand=False):
        exclude = ['CurrenciesConversion', 'GeographyMap', 'IDMap', 'InflationConversion', 'Version', 'foreign_keys'] + Simple_mapping_tables

        # Don't create classes for "Data" tables; these are rendered as DataFrames only
        tables = [name for name in self.get_tables_names() if not (name in exclude or name.endswith('Data'))]
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

            # if name == 'ImportCost':
            #     id_col = 'import_node_id'

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

    def get_columns(self, table):
        raise SubclassProtocolError(self.__class__, 'get_columns')

    def get_row_from_table(self, name, key_col, key, raise_error=True):
        tbl = self.get_table(name)
        tup = tbl.get_row(key_col, key, raise_error=raise_error)
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

        conn_str = "host='{}' dbname='{}' user='{}'".format(host, dbname, user)
        if password:
            conn_str += " password='{}'".format(password)

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


class CsvDatabase(AbstractDatabase):

    # Dict keyed by table name of filenames under the database root folder
    file_map = {}

    def __init__(self, pathname=None):
        super(CsvDatabase, self).__init__(table_class=CsvTable, cache_data=True)
        self.pathname = pathname
        self.create_file_map()
        self._cache_foreign_keys()
        self.shapes = ShapeDataMgr(pathname)

    def get_slice(self, name):
        '''
        Pass thru to ShapeDataMgr
        '''
        return self.shapes.get_slice(name)

    def get_tables_names(self):
        return self.file_map.keys()

    @classmethod
    def get_database(cls, pathname=None):
        # Add ".db" if missing
        if pathname:
            pathname += ('' if pathname.endswith('.db') else '.db')

        db = cls._get_database(pathname=pathname)
        return db

    def get_columns(self, table):
        pathname = self.file_for_table(table)
        with open(pathname, 'r') as f:
            headers = f.readline().strip()
        result = headers.split(',')
        return result

    def _cache_foreign_keys(self):
        """
        The CSV database reads the foreign key data that was exported from postgres.
        """
        pathname = self.file_for_table('foreign_keys')
        df = pd.read_csv(pathname, index_col=None)
        for _, row in df.iterrows():
            tbl_name, col_name, for_tbl_name, for_col_name = tuple(row)
            ForeignKey(tbl_name, col_name, for_tbl_name, for_col_name)

    def create_file_map(self):
        pathname = self.pathname

        if not os.path.exists(pathname):
            raise PathwaysException('Database path "%s" does not exist')

        if not os.path.isdir(pathname):
            raise PathwaysException('Database path "%s" is not a directory')

        all_csv = os.path.join(pathname, '*.csv')
        all_gz  = all_csv + '.gz'
        all_files = glob.glob(all_csv) + glob.glob(all_gz)

        for filename in all_files:
            basename = os.path.basename(filename)
            tbl_name = basename.split('.')[0]
            self.file_map[tbl_name] = os.path.abspath(filename)

        print("Found %d .CSV files for '%s'" % (len(self.file_map), pathname))

    def file_for_table(self, tbl_name):
        return self.file_map.get(tbl_name)
