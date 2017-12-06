__author__ = 'ryan and rich'
import logging
import pdb
#import re
from collections import OrderedDict, defaultdict

import numpy as np
#import pandas as pd

from . import config as cfg
from .time_series import TimeSeries
from .util import (DfOper, put_in_list, remove_df_levels, get_elements_from_level,
                   reindex_df_level_with_new_elements)
from .database import get_database, find_parent_col
from .error import SubclassProtocolError
from .text_mappings import MappedCols

DropStrCols = True

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
        self.text_to_id = {}     # maps text to integer id
        self.id_to_text = {}     # maps id back to text
        self.next_id = 1        # the next id to assign

    def store(self, text):
        # If already known, return it
        id = self.get_id(text, raise_error=False)
        if id is not None:
            return id

        id = self.next_id
        self.next_id += 1

        self.text_to_id[text] = id
        self.id_to_text[id] = text
        return id

    def get_id(self, text, raise_error=True):
        return self.text_to_id[text] if raise_error else (None if id is None else self.text_to_id.get(text, None))

    def get_text(self, id, raise_error=True):
        return self.id_to_text[id] if raise_error else (None if id is None else self.id_to_text.get(id, None))


BASE_CLASS = 'DataObject'

class DataObject(object):
    # dict keyed by class object; value is list of instances of the class
    instancesByClass = defaultdict(list)

    # These are here for completeness; they're shadowed in generated subclasses.
    _instances_by_key = {}
    _key_col = None
    _cols = None
    _table_name = None      # ditto
    _data_table_name = None # ditto

    _index_level_tups = None

    def __init__(self, key, scenario):
        """
        Append self to a list for our subclass
        """
        cls = self.__class__
        self.instancesByClass[cls].append(self)
        self.scenario = scenario
        self._key = key
        self._child_data = None
        self.children_by_fk_col = {}

        # ivars set in create_index_levels:
        self.column_names = None
        self.index_levels = None       # TODO: needed?
        self.df_index_names = None     # TODO: needed?

        self.raw_values = None         # TODO: eliminate _child_data?

        # added in effort to eliminate "if hasattr" tests
        self.driver_1 = self.driver_2 = None
        self.driver_denominator_1 = self.driver_denominator_2 = None
        self.drivers = []
        self.geography = None
        self.input_type = None

    def __str__(self):
        return "<{} {}='{}'>".format(self.__class__._table_name, self._key_col, self._key)

    # Added for compatibility with prior implementation
    @property
    def sql_data_table(self):
        return self._data_table_name

    @property
    def sql_id_table(self):
        return self._table_name

    @property
    def data_id_key(self):
        return self._key_col

    @classmethod
    def instances(cls):
        """
        Return instances for any subclass of DataObject.
        """
        return DataObject.instancesByClass[cls]

    @classmethod
    def get_instance(cls, key):
        cls._instances_by_key.get(key, None)  # uses each class' internal dict

    def init_from_tuple(self, tup, scenario, **kwargs):
        """
        Generated method
        """
        raise SubclassProtocolError(self.__class__, 'init_from_tuple')

    def init_from_series(self, series, scenario, **kwargs):
        self.init_from_tuple(tuple(series), scenario, **kwargs)

    def init_from_db(self, key, scenario, **kwargs):
        tup = self.__class__.get_row(key)
        self.init_from_tuple(tup, scenario, **kwargs)

    def get_geography_map_key(self):
        return (self.geography_map_key if 'geography_map_key' in self._cols
                else cfg.cfgfile.get('case', 'default_geography_map_key'))

    @classmethod
    def get_row(cls, key, raise_error=True):
        """
        Get a tuple for the row with the given id in the table associated with this class.
        Expects to find exactly one row with the given id. User must instantiate the database
        prior before calling this method.

        :param key: (str) the unique id of a row in `table`
        :param raise_error: (bool) whether to raise an error or return None if the id
           is not found.
        :return: (tuple) of values in the order the columns are defined in the table
        :raises RowNotFound: if `id` is not present in `table`.
        """
        db = get_database()
        tup = db.get_row_from_table(cls._table_name, cls._key_col, key, raise_error=raise_error)
        return tup

    # TODO: consider setting default copy=False once conversion is debugged
    def load_child_data(self, copy=True, **filters):
        """
        If self._data_table_name is set, load the data corresponding to this object
        in a DataFrame as self._child_data

        :param id: (.database.CsvDatabase) the database object
        :param copy: (bool) whether to copy the slice from the child table's DF
        :param **filters (dict of keyword args) constraints to apply when reading
           child data table.
        :return: none
        """
        db = get_database()

        if self._data_table_name:
            child_tbl = db.get_table(self._data_table_name)
            parent_col = find_parent_col(self._data_table_name, child_tbl.data.columns)

            # TODO: to add (from read_timeseries_data)
            # if 'sensitivity' in self._cols:
            #     filters['sensitivity'] = None
            #     if self.scenario:
            #         filters['sensitivity'] = self.scenario.get_sensitivity(self._data_table_name, self._key)

            query = "{} == '{}'".format(parent_col, self._key)
            slice = child_tbl.data.query(query)

            slice = slice.copy(deep=True) if copy else slice
            self.map_strings(slice)     # on-the-fly conversion of strings to integers for use in DF indexes
            self._child_data = slice

    def create_index_levels(self):
        if self._child_data is not None:
            data = self._child_data
            data_cols = data.columns

            elements = {col : sorted(data[col].unique()) for col in data_cols}

            if not DataObject._index_level_tups:
                # collect the tuples on the first call and cache them in a class variable
                db = get_database()
                levels_tbl = db.get_table('IndexLevels')
                levels = levels_tbl.data
                DataObject._index_level_tups = [(row.index_level, row.data_column_name) for idx, row in levels.iterrows()]

            level_tups = DataObject._index_level_tups

            def isListOfNoneOrNan(obj):
                if len(obj) != 1:
                    return False

                item = obj[0]
                return item is None or (isinstance(item, float) and np.isnan(obj[0]))

            tups = [(level, col) for level, col in level_tups
                     if (col in data_cols and not isListOfNoneOrNan(elements[col]))]
                         #col not in self.data_id_key and   # TODO: a substring test?

            # OrderedDict in necessary the way this currently works
            self.column_names = OrderedDict(tups)

            target_cols = self.column_names.values()
            tups = [(level, elements[col]) for level, col in level_tups if col in target_cols]
            index_levels = self.index_levels = OrderedDict(tups)

            self.df_index_names = [getattr(self, level, level) for level in index_levels]

        return index_levels

    def map_strings(self, df):
        tbl_name = self._data_table_name

        strmap = StringMap.getInstance()
        str_cols = MappedCols.get(tbl_name, [])

        for col in str_cols:
            # Ensure that all values are in the StringMap
            values = df[col].unique()
            for value in values:
                strmap.store(value)

            # mapped column "foo" becomes "foo_id"
            id_col = col + '_id'

            # Force string cols to str and replace 'nan' with None
            df[col] = df[col].astype(str)
            df.loc[df[col] == 'nan', col] = None

            # create a column with integer ids
            df[id_col] = df[col].map(lambda txt: strmap.get_id(txt, raise_error=False))

        if DropStrCols:
            df.drop(str_cols, axis=1, inplace=True)

    #
    # TODO: the remainder of this file is a modified subset of datamapfunctions
    #

    def clean_timeseries(self, attr='values', inplace=True, time_index_name='year',
                         time_index=None, lower=0, upper=None, interpolation_method='missing',
                         extrapolation_method='missing'):
        if time_index is None:
            time_index = cfg.cfgfile.get('case', 'years')
        interpolation_method = self.interpolation_method if interpolation_method is 'missing' else interpolation_method
        extrapolation_method = self.extrapolation_method if extrapolation_method is 'missing' else extrapolation_method
        exp_growth_rate = self.extrapolation_growth if hasattr(self, 'extrapolation_growth') else None

        data = getattr(self, attr)
        clean_data = TimeSeries.clean(data=data, newindex=time_index, time_index_name=time_index_name,
                                      interpolation_method=interpolation_method,
                                      extrapolation_method=extrapolation_method,
                                      exp_growth_rate=exp_growth_rate).clip(lower=lower, upper=upper)

        if inplace:
            setattr(self, attr, clean_data)
        else:
            return clean_data

    def geo_map(self, converted_geography, attr='values', inplace=True, current_geography=None, current_data_type=None,
                fill_value=0., filter_geo=True):
        """ maps a dataframe to another geography using relational GeographyMapdatabase table
        if input type is a total, then the subsection is the geography
        to convert to and the supersection is the initial geography.
        Example:
          input_type = 'total'
          state --> census division.
          How much of state maine is in census division new england?
          new england = subsection
          maine = supersection
        Otherwise the subsection and supersection values are reversed.
        Example:
           input_type = 'intensity'
           state --> census division.
           How much of census division new england does the state of maine represent?
           maine = subsection
           new england = supersection
        """
        # Unless specified, input_type used is attribute of the object
        current_data_type = current_data_type or self.input_type
        current_geography = current_geography or self.geography
        geography_map_key = self.get_geography_map_key()

        # TODO: need to see which attrs are used, then to root out the getattr.
        if current_geography not in getattr(self, attr).index.names:
            logging.error("Dataframe being mapped doesn't have the stated current geography: {}".format(self.__class__))
            pdb.set_trace()

        # create dataframe with map from one geography to another
        map_df = cfg.geo.map_df(current_geography, converted_geography, normalize_as=current_data_type,
                                map_key=geography_map_key, filter_geo=filter_geo)
        mapped_data = DfOper.mult([getattr(self, attr), map_df], fill_value=fill_value)

        if current_geography != converted_geography:
            mapped_data = remove_df_levels(mapped_data, current_geography)

        if hasattr(mapped_data.index, 'swaplevel'):
            mapped_data = DataObject.reorder_df_geo_left_year_right(mapped_data, converted_geography)

        if inplace:
            setattr(self, attr, mapped_data.sort())
        else:
            return mapped_data.sort()

    @staticmethod
    def reorder_df_geo_left_year_right(df, current_geography):
        if 'year' in df.index.names:
            y_or_v = ['year']
        elif 'vintage' in df.index.names:
            y_or_v = ['vintage']
        else:
            y_or_v = []
        new_order = [current_geography] + [l for l in df.index.names if l not in [current_geography] + y_or_v] + y_or_v
        mapped_data = df.reorder_levels(new_order)
        return mapped_data

    def account_for_foreign_gaus(self, attr, current_data_type, current_geography):
        """
        TODO: Ryan/Ben, please correct this if needed.
        Subtract data for "foreign" GAUs (e.g., states) from larger regions (e.g., census
        divisions) to produce a modified "rest of {larger region}" that sums with the
        foreign regions to the original values.
        """
        geography_map_key = self.get_geography_map_key()

        # TODO: need to see which attrs are used, then to root out the getattr.
        df = getattr(self, attr).copy()
        if cfg.include_foreign_gaus:
            native_gaus, current_gaus, foreign_gaus = cfg.geo.get_native_current_foreign_gaus(df, current_geography)

            if foreign_gaus:
                name = '{} {}'.format(self.sql_id_table, self.name if hasattr(self, 'name') else 'id ' + str(self.id))

                logging.info('      Detected foreign gaus for {}: {}'.format(name, ', '.join(
                    [cfg.geo.geography_names[f] for f in foreign_gaus])))

                df, current_geography = cfg.geo.incorporate_foreign_gaus(df, current_geography, current_data_type,
                                                                         geography_map_key)
        else:
            df = cfg.geo.filter_foreign_gaus(df, current_geography)
        return df, current_geography

    def _add_missing_geographies(self, df, current_geography, current_data_type):
        current_number_of_geographies = len(get_elements_from_level(df, current_geography))
        propper_number_of_geographies = len(cfg.geo.geographies_unfiltered[current_geography])
        if current_data_type == 'total' and current_number_of_geographies != propper_number_of_geographies:
            # we only want to do it when we have a total, otherwise we can't just fill with zero
            df = reindex_df_level_with_new_elements(df, current_geography,
                                                    cfg.geo.geographies_unfiltered[current_geography],
                                                    fill_value=np.nan)
        return df

    def _get_active_time_index(self, time_index, time_index_name):
        if time_index is None:
            index_plus_s = time_index_name + "s"
            time_index = getattr(self, index_plus_s) if hasattr(self, index_plus_s) else cfg.cfgfile.get('case', 'years')
        return time_index  # this is a list of years

    def _get_df_index_names_in_a_list(self, df):
        return df.index.names if df.index.nlevels > 1 else [df.index.name]

    def remap(self, map_from='raw_values', map_to='values', drivers=None, time_index_name='year',
              time_index=None, fill_timeseries=True, interpolation_method='missing', extrapolation_method='missing',
              converted_geography=None, current_geography=None, current_data_type=None, fill_value=0., lower=0,
              upper=None, filter_geo=True, driver_geography=None):
        """ Map data to drivers and geography
        Args:
            map_from (string): starting variable name (defaults to 'raw_values')
            map_to (string): ending variable name (defaults to 'values')
            drivers (list of or single dataframe): drivers for the remap
            input_type_override (string): either 'total' or 'intensity' (defaults to self.type)
        """
        driver_geography = cfg.disagg_geography if driver_geography is None else driver_geography
        converted_geography = cfg.primary_geography if converted_geography is None else converted_geography
        current_data_type = self.input_type if current_data_type is None else current_data_type
        current_geography = self.geography if current_geography is None else current_geography
        time_index = self._get_active_time_index(time_index, time_index_name)

        map_df = getattr(self, map_from)
        index_names = self._get_df_index_names_in_a_list(map_df)
        if current_geography not in index_names:
            raise ValueError('Current geography does not match the geography of the dataframe in remap')

        # deals with foreign gaus and updates the geography
        df, current_geography = self.account_for_foreign_gaus(map_from, current_data_type, current_geography)
        setattr(self, map_to, df)

        # This happens when we are on a geography level and some of the elements are missing. Such as no PR when we have all the other U.S. States.
        setattr(self, map_to, self._add_missing_geographies(df, current_geography, current_data_type))

        if (drivers is None) or (not len(drivers)):
            # we have no drivers, just need to do a clean timeseries and a geomap
            if fill_timeseries:
                self.clean_timeseries(attr=map_to, inplace=True, time_index=time_index, time_index_name=time_index_name,
                                      interpolation_method=interpolation_method,
                                      extrapolation_method=extrapolation_method,
                                      lower=lower, upper=upper)
            if current_geography != converted_geography:
                self.geo_map(converted_geography, attr=map_to, inplace=True, current_geography=current_geography,
                             current_data_type=current_data_type, fill_value=fill_value, filter_geo=filter_geo)
                current_geography = converted_geography
        else:
            # becomes an attribute of self just because we may do a geomap on it
            self.total_driver = DfOper.mult(put_in_list(drivers))
            # turns out we don't always have a year or vintage column for drivers. For instance when linked_demand_technology gets remapped
            if time_index_name in self.total_driver.index.names:
                # sometimes when we have a linked service demand driver in a demand subsector it will come in on a fewer number of years than self.years, making this clean timeseries necesary
                self.clean_timeseries(attr='total_driver', inplace=True, time_index_name=time_index_name,
                                      time_index=time_index, lower=None, upper=None, interpolation_method='missing',
                                      extrapolation_method='missing')

            # While not on primary geography, geography does have some information we would like to preserve
            if hasattr(self, 'drivers') and len(drivers) == len(self.drivers) and set(
                    [x.input_type for x in self.drivers.values()]) == set(['intensity']) and set(
                    [x.base_driver_id for x in self.drivers.values()]) == set([None]):
                driver_mapping_data_type = 'intensity'
            else:
                driver_mapping_data_type = 'total'
            total_driver_current_geo = self.geo_map(current_geography, attr='total_driver', inplace=False,
                                                    current_geography=driver_geography,
                                                    current_data_type=driver_mapping_data_type,
                                                    fill_value=fill_value, filter_geo=False)

            if current_data_type == 'total':
                if fill_value is np.nan:
                    df_intensity = DfOper.divi((getattr(self, map_to), total_driver_current_geo),
                                               expandable=(False, True), collapsible=(False, True),
                                               fill_value=fill_value).replace([np.inf], 0)
                else:
                    df_intensity = DfOper.divi((getattr(self, map_to), total_driver_current_geo),
                                               expandable=(False, True), collapsible=(False, True),
                                               fill_value=fill_value).replace([np.inf, np.nan, -np.nan], 0)
                setattr(self, map_to, df_intensity)

            # Clean the timeseries as an intensity
            if fill_timeseries:
                self.clean_timeseries(attr=map_to, inplace=True, time_index=time_index,
                                      interpolation_method=interpolation_method,
                                      extrapolation_method=extrapolation_method)

            #            self.geo_map(converted_geography, attr=map_to, inplace=True, current_geography=current_geography, current_data_type='intensity', fill_value=fill_value, filter_geo=filter_geo)
            #            total_driver_converted_geo = self.geo_map(converted_geography, attr='total_driver', inplace=False, current_geography=driver_geography, current_data_type=driver_mapping_data_type, fill_value=fill_value, filter_geo=filter_geo)

            if current_data_type == 'total':
                setattr(self, map_to,
                        DfOper.mult((getattr(self, map_to), total_driver_current_geo), fill_value=fill_value))
            else:
                setattr(self, map_to,
                        DfOper.mult((getattr(self, map_to), total_driver_current_geo), expandable=(True, False),
                                    collapsible=(False, True), fill_value=fill_value))
            self.geo_map(converted_geography, attr=map_to, inplace=True, current_geography=current_geography,
                         current_data_type='total', fill_value=fill_value, filter_geo=filter_geo)
            # we don't want to keep this around
            del self.total_driver

    def project(self, map_from='raw_values', map_to='values', additional_drivers=None,
                interpolation_method='missing', extrapolation_method='missing',
                time_index_name='year', fill_timeseries=True, converted_geography=None, current_geography=None,
                current_data_type=None, fill_value=0.0, projected=False, filter_geo=True):

        converted_geography = converted_geography or cfg.primary_geography
        current_data_type = current_data_type or self.input_type

        if map_from != 'raw_values' and current_data_type == 'total':
            denominator_driver_ids = None
        else:
            denominator_driver_ids = [getattr(self, col) for col in cfg.denom_col_names if
                                      getattr(self, col) is not None]

        current_geography = current_geography or self.geography
        setattr(self, map_to, getattr(self, map_from).copy())

        if denominator_driver_ids:
            if current_data_type != 'intensity':
                msg = "{} id {}: type must be intensity if variable has denominator drivers".format(self.__class__, self.id)
                raise ValueError(msg)

            if current_geography != converted_geography:
                # While not on primary geography, geography does have some information we would like to preserve
                self.geo_map(converted_geography, attr=map_to, inplace=True)
                current_geography = converted_geography

            total_driver = DfOper.mult([self.drivers[id].values for id in denominator_driver_ids])
            self.geo_map(current_geography=current_geography, attr=map_to, converted_geography=cfg.disagg_geography,
                         current_data_type='intensity')

            setattr(self, map_to, DfOper.mult((getattr(self, map_to), total_driver)))
            self.geo_map(current_geography=cfg.disagg_geography, attr=map_to, converted_geography=current_geography,
                         current_data_type='total')

            # the datatype is now total
            current_data_type = 'total'

        driver_ids = filter(None, [self.driver_1, self.driver_2])
        drivers = [self.drivers[key].values for key in driver_ids]
        if additional_drivers is not None:
            drivers += put_in_list(additional_drivers)

        # both map_from and map_to are the same
        self.remap(map_from=map_to, map_to=map_to, drivers=drivers,
                   time_index_name=time_index_name, fill_timeseries=fill_timeseries,
                   interpolation_method=interpolation_method,
                   extrapolation_method=extrapolation_method,
                   converted_geography=converted_geography, current_geography=current_geography,
                   current_data_type=current_data_type, fill_value=fill_value, filter_geo=filter_geo)
