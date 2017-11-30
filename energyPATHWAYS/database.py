#
# Created 19 Sep 2017
# @author: Rich Plevin
#
# Database abstraction layer.
#
from __future__ import print_function
from collections import defaultdict
import glob
import gzip
import numpy as np
import os
import pandas as pd

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

def _find_col(table, exceptions, candidates, cols):
    col = exceptions.get(table)
    if col:
        return col

    for col in candidates:
        if col in cols:
            return col
    return None

def find_key_col(table, cols):
    '''
    Find the key column.
    '''
    exceptions = {
        'DemandFlexibleLoadMeasures': 'subsector', # has 'name' col that isn't the key
    }

    key_cols = ('name', 'parent', 'subsector', 'demand_technology', 'supply_node',
                'supply_tech', 'import_node', 'primary_node', 'index_level')
    return _find_col(table, exceptions, key_cols, cols)

def find_parent_col(table, cols):
    '''
    Find the column identifying the parent record.
    '''
    exceptions = {
        'DemandSalesData'               : 'demand_technology',
        'DispatchFeedersAllocationData' : 'name',
        'SupplyTechsEfficiencyData'     : 'supply_tech',
        'SupplySalesData'               : 'supply_technology',
        'SupplySalesShareData'          : 'supply_technology',
    }

    # List adapted from scenario_loader.PARENT_COLUMN_NAMES. We don't reference that
    # and replace "_id" with "" since that list will become obsolete at some point.
    parent_cols = ('parent', 'subsector', 'supply_node', 'primary_node', 'import_node',
                   'demand_tech', 'demand_technology', 'supply_tech', 'supply_technology')

    return _find_col(table, exceptions, parent_cols, cols)


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


class AbstractTable(object):
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

        print("Linking table {}".format(parent_tbl_name))

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
                        print("** Skipping missing table '{}'".format(child_tbl_name))
                    else:
                        setattr(parent_obj, parent_col, text)       # Never encountered this line
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
            rows = self.data.query(query)
            # print('Getting row {} from cache'.format(query))
            # print(rows)
            tups = []
            for idx, row in rows.iterrows():
                tups.append(tuple(row))
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


class CsvTable(AbstractTable):
    """
    Implementation of AbstractTable based on a directory of CSV files.
    Note: CsvTable always caches data, so the cache_data flag is ignored.
    """
    def __init__(self, db, tbl_name, cache_data=None):
        super(CsvTable, self).__init__(db, tbl_name, cache_data=True)

    def load_rows(self, id):
        raise PathwaysException("CsvTable.load_rows should not be called since the CSV file is always cached")

    def load_all(self):
        if self.data is not None:
            return self.data

        tbl_name = self.name
        filename = self.db.file_for_table(tbl_name)

        if not filename:
            raise PathwaysException('Missing filename for table "{}"'.format(tbl_name))

        if filename.endswith('.gz'):
            with gzip.open(filename, 'rb') as f:
                df = pd.read_csv(f, index_col=None)
        else:
            df = pd.read_csv(filename, index_col=None)

        # ensure that keys are read as strings
        col = find_key_col(tbl_name, df.columns)
        df[col] = df[col].astype(str)

        # ditto for parent id columns
        if tbl_name.endswith('Data'):
            col = find_parent_col(tbl_name, df.columns)
            if col:
                df[col] = df[col].astype(str)

        self.data = df

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
                self.slices[shape_name] = df

    def get_slice(self, name):
        name = name.replace(' ', '_')
        return self.slices[name]

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
            tbl = self.table_class(self, name, cache_data=self.cache_data)
            self.table_objs[name] = tbl
            return tbl

    def tables_with_classes(self, include_on_demand=False):
        exclude = ['CurrenciesConversion', 'GeographyMap', 'IDMap', 'InflationConversion',
                   'DispatchTransmissionHurdleRate', 'DispatchTransmissionLosses',
                   'Version', 'foreign_keys'] + Simple_mapping_tables

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


class CsvDatabase(AbstractDatabase):

    # Dict keyed by table name of filenames under the database root folder
    file_map = {}

    def __init__(self, pathname=None, load=True, exclude=[]):
        super(CsvDatabase, self).__init__(table_class=CsvTable, cache_data=True)
        self.pathname = pathname
        self.create_file_map()
        self._cache_foreign_keys()
        self.shapes = ShapeDataMgr(pathname)

        # cache data for all tables for which there are generated classes
        if load:
            table_names = self.tables_with_classes()
            for name in table_names:
                if name not in exclude:
                    self.get_table(name)

    def get_slice(self, name):
        '''
        Pass thru to ShapeDataMgr
        '''
        return self.shapes.get_slice(name)

    def get_tables_names(self):
        return self.file_map.keys()

    @classmethod
    def get_database(cls, pathname=None, load=True, exclude=[]):
        # Add ".db" if missing
        if pathname:
            pathname += ('' if pathname.endswith('.db') else '.db')

        db = cls._get_database(pathname=pathname, load=load, exclude=[])
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
            raise PathwaysException('Database path "{}" does not exist'.format(pathname))

        if not os.path.isdir(pathname):
            raise PathwaysException('Database path "{}" is not a directory'.format(pathname))

        all_csv = os.path.join(pathname, '*.csv')
        all_gz  = all_csv + '.gz'
        all_files = glob.glob(all_csv) + glob.glob(all_gz)

        for filename in all_files:
            basename = os.path.basename(filename)
            tbl_name = basename.split('.')[0]
            self.file_map[tbl_name] = os.path.abspath(filename)

        print("Found {} .CSV files for '{}'".format(len(self.file_map), pathname))

    def file_for_table(self, tbl_name):
        return self.file_map.get(tbl_name)
