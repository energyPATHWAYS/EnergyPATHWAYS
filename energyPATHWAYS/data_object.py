__author__ = 'ryan and rich'
import logging
import pdb
from collections import OrderedDict

import numpy as np

import config as cfg
from energyPATHWAYS.config import getParam, getParamAsBoolean
from energyPATHWAYS.time_series import TimeSeries
from energyPATHWAYS.util import (DfOper, put_in_list, get_elements_from_level,
                   reindex_df_level_with_new_elements,remove_df_levels)
from energyPATHWAYS.geomapper import GeoMapper

from csvdb.data_object import DataObject as CsvDataObject, get_database


def _isListOfNoneOrNan(obj):
    if len(obj) != 1:
        return False

    item = obj[0]
    return item is None or (isinstance(item, float) and np.isnan(obj[0]))


BASE_CLASS = 'DataObject'

class DataObject(CsvDataObject):

    _data_table_name = None # deprecated

    def __init__(self, key, scenario):
        """
        Append self to a list for our subclass
        """
        super(DataObject, self).__init__(key, scenario)

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

    def get_geography_map_key(self):
        return (self.geography_map_key if 'geography_map_key' in self._cols
                else GeoMapper.default_geography_map_key)

    def add_sensitivity_filter(self, key, filters): # This overwrites a parent function
        db = get_database()
        tbl_name = self._table_name
        tbl = db.get_table(tbl_name)

        if 'sensitivity' in tbl.data.columns:
            # check to see if we have a matching sensitivity in our scenario
            if tbl_name in self._scenario._sensitivities and key in self._scenario._sensitivities[tbl_name]:
                filters['sensitivity'] = self._scenario._sensitivities[tbl_name][key]
            else:
                filters['sensitivity'] = '_reference_'
        return filters

    def timeseries_cleanup(self, timeseries): # This overwrites a parent function
        db = get_database()
        tbl_name = self._table_name
        tbl = db.get_table(tbl_name)
        md = tbl.metadata

        # drop any columns that are all NaN
        timeseries = timeseries.loc[:,~timeseries.isnull().all()]
        if 'sensitivity' in timeseries.columns: #We've filtered sensitivities in an earlier step, for EP we drop them
            del timeseries['sensitivity']

        index_cols = [c for c in timeseries.columns if c not in md.df_value_col]
        timeseries = timeseries.set_index(index_cols).sort_index()
        return timeseries


    def create_index_levels_new(self):
        if self._child_data is None:
            return None

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

        tups = [(level, col) for level, col in level_tups
                if (col in data_cols and not _isListOfNoneOrNan(elements[col]))]
                     #col not in self.data_id_key and   # TODO: Was this really intended to be a substring test?

        # OrderedDict in necessary the way this currently works
        self.column_names = OrderedDict(tups)

        target_cols = self.column_names.values()
        tups = [(level, elements[col]) for level, col in level_tups if col in target_cols]
        index_levels = self.index_levels = OrderedDict(tups)

        self.df_index_names = [getattr(self, level, level) for level in index_levels]

        return index_levels

    def clean_timeseries(self, attr='values', inplace=True, time_index_name='year',
                         time_index=None, lower=0, upper=None, interpolation_method='missing', extrapolation_method='missing'):
        if time_index is None:
            time_index = cfg.years
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

    def geo_map(self, converted_geography, attr='values', inplace=True, current_geography=None, current_data_type=None, fill_value=0.,filter_geo=True,remove_current_geography=True):
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

        mapped_data = GeoMapper.geo_map(getattr(self, attr), current_geography, converted_geography,
                                      current_data_type, geography_map_key, fill_value, filter_geo,remove_current_geography=remove_current_geography)

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
        Subtract data for "foreign" GAUs (e.g., states) from larger regions (e.g., census
        divisions) to produce a modified "rest of {larger region}" that sums with the
        foreign regions to the original values.
        """
        geography_map_key = self.get_geography_map_key()

        df = getattr(self, attr).copy()
        if getParamAsBoolean('include_foreign_gaus'):
            native_gaus, current_gaus, foreign_gaus = GeoMapper.get_instance().get_native_current_foreign_gaus(df, current_geography)

            if foreign_gaus:
                name = '{} {}'.format(self._table_name, getattr(self, '_key_col'))
                logging.info('      Detected foreign gaus for {}: {}'.format(name, ', '.join(foreign_gaus)))
                df, current_geography = GeoMapper.get_instance().incorporate_foreign_gaus(df, current_geography, current_data_type, geography_map_key)
        else:
            df = GeoMapper.get_instance().filter_foreign_gaus(df, current_geography)
        return df, current_geography

    def _add_missing_geographies(self, df, current_geography, current_data_type, missing_intensity_geos,fill_value,filter_geo=False):
        df = df.reset_index().set_index(df.index.names)
        current_number_of_geographies = len(get_elements_from_level(df, current_geography))
        if not filter_geo:
            propper_number_of_geographies = len(GeoMapper.geography_to_gau_unfiltered[current_geography])
            if (current_data_type == 'total' or missing_intensity_geos) and current_number_of_geographies != propper_number_of_geographies:
                # we only want to do it when we have a total, otherwise we can't just fill with zero
                df = reindex_df_level_with_new_elements(df, current_geography,
                                                        GeoMapper.geography_to_gau_unfiltered[current_geography],
                                                        fill_value=fill_value)
        else:
            propper_number_of_geographies = len(GeoMapper.geography_to_gau[current_geography])
            if (current_data_type == 'total' or missing_intensity_geos) and current_number_of_geographies != propper_number_of_geographies:
                # we only want to do it when we have a total, otherwise we can't just fill with zero
                df = reindex_df_level_with_new_elements(df, current_geography,
                                                        GeoMapper.geography_to_gau[current_geography],
                                                        fill_value=fill_value)

        return df

    def _get_active_time_index(self, time_index, time_index_name):
        if time_index is None:
            time_index = getattr(self, time_index_name + "s") if hasattr(self, time_index_name + "s") else cfg.years
        return time_index # this is a list of years

    def _get_df_index_names_in_a_list(self, df):
        # TODO: is this intended to handle a case of no index? Because index.names returns [name] when nlevels == 1
        return df.index.names if df.index.nlevels > 1 else [df.index.name]

    def remap(self, map_from='raw_values', map_to='values', drivers=None, time_index_name='year',
              time_index=None, fill_timeseries=True, interpolation_method='missing', extrapolation_method='missing',
              converted_geography=None, current_geography=None, current_data_type=None, fill_value=0., lower=0, upper=None, filter_geo=True, driver_geography=None, missing_intensity_geos=False):
        """ Map data to drivers and geography
        Args:
            map_from (string): starting variable name (defaults to 'raw_values')
            map_to (string): ending variable name (defaults to 'values')
            drivers (list of or single dataframe): drivers for the remap
            input_type_override (string): either 'total' or 'intensity' (defaults to self.type)
        """
        driver_geography    = driver_geography or getParam('disagg_geography')
        converted_geography = converted_geography or getParam('primary_geography')
        current_data_type   = current_data_type or self.input_type
        current_geography   = current_geography or self.geography
        time_index = self._get_active_time_index(time_index, time_index_name)

        map_df = getattr(self, map_from)
        index_names = self._get_df_index_names_in_a_list(map_df)
        if current_geography not in index_names:
            raise ValueError('Current geography does not match the geography of the dataframe in remap')


        # deals with foreign gaus and updates the geography
        df, current_geography = self.account_for_foreign_gaus(map_from, current_data_type, current_geography)

        setattr(self, map_to, df)

        # This happens when we are on a geography level and some of the elements are missing. Such as no PR when we have all the other U.S. States.
        setattr(self, map_to, self._add_missing_geographies(df, current_geography, current_data_type, missing_intensity_geos,fill_value=fill_value,filter_geo=filter_geo))

        if drivers is None or len(drivers) == 0:
            # we have no drivers, just need to do a clean timeseries and a geomap
            if fill_timeseries:
                self.clean_timeseries(attr=map_to, inplace=True, time_index=time_index, time_index_name=time_index_name,
                                      interpolation_method=interpolation_method,
                                      extrapolation_method=extrapolation_method,
                                      lower=lower, upper=upper)
            if current_geography != converted_geography:
                self.geo_map(converted_geography, attr=map_to, inplace=True, current_geography=current_geography,
                             current_data_type=current_data_type, fill_value=fill_value, filter_geo=filter_geo)
        else:
            # becomes an attribute of self just because we may do a geomap on it
            driver_dfs = put_in_list(drivers)
            self.error_check_drivers(getattr(self, map_to), driver_dfs)
            self.total_driver = DfOper.mult(driver_dfs)
            #self.total_driver_unitless = DfOper.add([x.groupby(level=[y for y in getattr(self,map_to).index.names if y in x.index.names]).apply(lambda x:x/x.sum()) for x in driver_dfs],expandable=False)
            # turns out we don't always have a year or vintage column for drivers. For instance when linked_demand_technology gets remapped
            if time_index_name in self.total_driver.index.names:
                # sometimes when we have a linked service demand driver in a demand subsector it will come in on a fewer number of years than self.years, making this clean timeseries necesary
                self.clean_timeseries(attr='total_driver', inplace=True, time_index_name=time_index_name,
                                      time_index=time_index, lower=None, upper=None, interpolation_method='missing',
                                      extrapolation_method='missing')
                #self.clean_timeseries(attr='total_driver_unitless', inplace=True, time_index_name=time_index_name,
                                      #time_index=time_index, lower=None, upper=None, interpolation_method='missing',
                                      #extrapolation_method='missing')

            # While not on primary geography, geography does have some information we would like to preserve.
            if hasattr(self, 'drivers') and len(drivers) == len(self.drivers) and set([x.input_type for x in self.drivers.values()]) == set(['intensity']) and set([x.base_driver_id for x in self.drivers.values()]) == set([None]):
                driver_mapping_data_type = 'intensity'
            else:
                driver_mapping_data_type = 'total'
            total_driver_current_geo = self.geo_map(current_geography, attr='total_driver', inplace=False,
                                                    current_geography=driver_geography,
                                                    current_data_type=driver_mapping_data_type,
                                                    fill_value=fill_value, filter_geo=filter_geo,remove_current_geography=False)
            #total_driver_current_geo_unitless = self.geo_map(current_geography, attr='total_driver_unitless', inplace=False,
                                                    #current_geography=driver_geography,
                                                    #current_data_type=driver_mapping_data_type,
                                                    #fill_value=0, filter_geo=filter_geo,remove_current_geography=False)
            level_set = [x for x in set([x for x in getattr(self,map_to).index.names] + [current_geography,driver_geography]) if x in total_driver_current_geo.index.names]
            if current_data_type == 'total':
                if current_geography!=driver_geography:
                    levels = [x for x in level_set if x!=driver_geography]
                else:
                    levels = [x for x in level_set]
                #if 'demand_technology' in getattr(self,map_to).index.names and 'Cordwood Stoves' in getattr(self,map_to).index.get_level_values('demand_technology'):
                    #pdb.set_trace()
                if fill_value is np.nan:
                    df_intensity = DfOper.divi([DfOper.mult((getattr(self, map_to), total_driver_current_geo.groupby(level=levels).apply(lambda x: x/x.sum())),
                                               expandable=(True, True), collapsible=(False, False),
                                               fill_value=fill_value),total_driver_current_geo],
                                               expandable=(False, True), collapsible=(False, True))
                else:
                    df_intensity = DfOper.divi([DfOper.mult((getattr(self, map_to), total_driver_current_geo.groupby(level=levels).apply(lambda x: x/x.sum())),
                                               expandable=(True, True), collapsible=(False, False),
                                               fill_value=fill_value),total_driver_current_geo],
                                               expandable=(False, True), collapsible=(False, True)).replace([np.inf, np.nan, -np.nan], 0)
                setattr(self, map_to, df_intensity)

            # Clean the timeseries as an intensity
            if fill_timeseries:
                try:
                    self.clean_timeseries(attr=map_to, inplace=True, time_index=time_index, interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,lower=-np.inf)
                except:
                    pdb.set_trace()
            if current_data_type == 'total':
                setattr(self, map_to, DfOper.mult((getattr(self, map_to), total_driver_current_geo),fill_value=fill_value))
                if len(set(getattr(self,map_to).index.get_level_values(current_geography)))>len(set(getattr(self,map_to).index.get_level_values(driver_geography))):
                    setattr(self,map_to,remove_df_levels(getattr(self,map_to),driver_geography))
                elif len(set(getattr(self, map_to).index.get_level_values(current_geography))) < len(
                            set(getattr(self, map_to).index.get_level_values(driver_geography))):
                    setattr(self, map_to, remove_df_levels(getattr(self, map_to), current_geography))
                    current_geography = driver_geography
                elif current_geography!=driver_geography:
                    setattr(self, map_to, remove_df_levels(getattr(self, map_to), driver_geography))
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
                current_data_type=None, fill_value=0.0, filter_geo=True,
                projected=False): # TODO: 'projected' is unused; remove it from callers to avoid confusion.

        # TODO: for integration stage only. Later, we'll pass this in instead of the old dict(id -> Driver)
        drivers_by_name = {driver.name: driver for driver in self.drivers.values()}

        current_geography = current_geography or self.geography
        current_data_type = self.input_type if current_data_type is None else current_data_type
        if map_from != 'raw_values' and current_data_type == 'total':
            denominator_drivers = None
        else:
            denominators = [self.driver_denominator_1, self.driver_denominator_2]
            denominator_drivers = filter(None, denominators)

        setattr(self, map_to, getattr(self, map_from).copy())

        if denominator_drivers:
            if current_data_type != 'intensity':
                msg = "{} : type must be intensity if variable has denominator drivers".format(self)
                raise ValueError(msg)

            if current_geography != converted_geography:
                # While not on primary geography, geography does have some information we would like to preserve
                df, current_geography = self.account_for_foreign_gaus(map_from, current_data_type, current_geography)
                setattr(self, map_to, df)
                self.geo_map(converted_geography, current_geography=current_geography, attr=map_to, inplace=True)
                current_geography = converted_geography

            denom_drivers = [drivers_by_name[name].values for name in denominator_drivers]
            self.error_check_drivers(getattr(self, map_to), denom_drivers)
            total_driver = DfOper.mult(denom_drivers)
            self.geo_map(current_geography=current_geography, attr=map_to, converted_geography=GeoMapper.disagg_geography,
                         current_data_type='intensity')

            setattr(self, map_to, DfOper.mult((getattr(self, map_to), total_driver)))
            self.geo_map(current_geography=GeoMapper.disagg_geography, attr=map_to, converted_geography=current_geography,
                         current_data_type='total')

            # the datatype is now total
            current_data_type = 'total'

        driver_names = [self.driver_1, self.driver_2,self.driver_3]
        driverDFs = [drivers_by_name[name].values for name in driver_names if name]
        # drivers = [self.drivers[key].values for key in driver_names]

        if additional_drivers is not None:
            driverDFs += put_in_list(additional_drivers)
        # both map_from and map_to are the same
        self.remap(map_from=map_to, map_to=map_to, drivers=driverDFs,
                   time_index_name=time_index_name, fill_timeseries=fill_timeseries,
                   interpolation_method=interpolation_method,
                   extrapolation_method=extrapolation_method,
                   converted_geography=converted_geography, current_geography=current_geography,
                   current_data_type=current_data_type, fill_value=fill_value, filter_geo=filter_geo)

    def error_check_drivers(self, df, drivers):
        # check to see that for each index in drivers that is in df, that all the elements are the same
        df = df.reset_index().set_index(df.index.names)
        df_levels = {df.index.name: df.index.values} if df.index.nlevels==1 else dict(zip(df.index.names, df.index.levels))
        for driver in drivers:
            for index_name in driver.index.names:
                if index_name in df_levels:
                    if index_name in ['year', 'vintage']:
                        overlapping = set(df_levels[index_name]) & set(driver.index.get_level_values(index_name))
                        if len(overlapping)==0:
                            raise ValueError('Index elements in the data that are not found in the driver. \n data: {} \n The elements in the driver index "{}" include: {}'.format(df, index_name, set(driver.index.get_level_values(index_name))))
                    else:
                        missing_elements = set(df_levels[index_name]) - set(driver.index.get_level_values(index_name))
                        if len(missing_elements):
                            raise ValueError('Index elements in the data that are not found in the driver. \n data: {} \n The following elements are missing from driver index "{}": {}'.format(df, index_name, missing_elements))