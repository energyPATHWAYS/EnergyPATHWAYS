# -*- coding: utf-8 -*-
"""
Created on Mon Oct 05 14:45:48 2015

@author: ryan
"""

import pandas as pd
import pytz
import datetime as DT
import numpy as np
import pickle
import functools
import os
import logging
import pdb
import pathos
from energyPATHWAYS import helper_multiprocess
import time
from csvdb import CsvDatabase
from energyPATHWAYS import config as cfg
from energyPATHWAYS.geomapper import GeoMapper
from energyPATHWAYS import util
from energyPATHWAYS.data_object import DataObject


#http://stackoverflow.com/questions/27491988/canonical-offset-from-utc-using-pytz

def is_leap_year(year):
    # https://support.microsoft.com/en-us/kb/214019
    if year % 4:
        if year % 100 and year % 400:
            return False
        else:
            return True
    else:
        return True

def create_time_slice_elements(active_dates_index):
    business_days = pd.bdate_range(min(active_dates_index).date(), max(active_dates_index).date())

    time_slice_elements = {}
    for ti in ['year', 'month', 'week', 'hour']:
            time_slice_elements[ti] = getattr(active_dates_index, ti)

    time_slice_elements['day_type'] = np.array(['workday' if s.date() in business_days else 'non-workday' for s in active_dates_index])
    time_slice_elements['hour24'] = time_slice_elements['hour'] + 1
    return time_slice_elements

def num_active_years(active_dates_index):
    unique_years = sorted(list(set(active_dates_index.year)))
    year_counts = [sum(active_dates_index.year==y) for y in unique_years]
    years = sum([yc/(8784. if is_leap_year(y) else 8760.) for y, yc in zip(unique_years, year_counts)])
    return int(round(years))

time_zones = pd.read_csv(os.path.join(os.path.split(os.path.dirname(os.path.realpath(__file__)))[0], 'energyPATHWAYS', 'time_zones.csv'))
time_zones = dict(zip([tz.lower() for tz in time_zones.values.flatten()],time_zones.values.flatten()))
def format_timezone_str(tz):
    return time_zones[tz.lower()]

def newest_shape_file_modified_date(database_path):
    max_shapes_data_modified = 0
    for dirpath, dirnames, filenames in os.walk(os.path.join(database_path, 'ShapeData'), topdown=False):
        valid_paths = [os.path.join(dirpath, file_name) for file_name in filenames if file_name[-7:]=='.csv.gz' or file_name[-5:]=='.csv']
        max_date_modified_in_folder = max([os.path.getmtime(valid_path) for valid_path in valid_paths]) if len(valid_paths) else 0
        max_shapes_data_modified = max(max_shapes_data_modified, max_date_modified_in_folder)
    shape_meta_modified = os.path.getmtime(os.path.join(database_path, 'Shapes.csv'))
    return max(max_shapes_data_modified, shape_meta_modified)

class Shapes(object):
    _instance = None
    time_slice_col = ['year', 'month', 'week', 'day_type', 'hour']

    def __init__(self, database_path=None):
        db = CsvDatabase.get_database(database_path)
        db.shapes.load_all()
        self.cfg_weather_years = [int(y) for y in cfg.getParam('weather_years', section='TIME').split(',')]
        self.active_dates_index = self.get_active_dates(self.cfg_weather_years)
        self.active_dates_index_unique = self.active_dates_index.unique()
        self.load_shape_base_year = max(int(np.round(np.mean(self.cfg_weather_years))), cfg.getParamAsInt('current_year', section='TIME'))
        self.time_slice_elements = create_time_slice_elements(self.active_dates_index)
        self.num_active_years = num_active_years(self.active_dates_index)
        self.cfg_hash_tuple = self.get_hash_tuple()
        self.cfg_hash = hash(self.cfg_hash_tuple)

        if len(db.shapes.slices.keys()) == 0:
            raise ValueError("No shapes data found, check database path ({}).\nThe folder ShapeData must be located in the database folder specified".format(
                database_path))

        shape_meta = db.get_table("Shapes").data
        self.data = {}
        for i, meta in shape_meta.iterrows():
            if meta['name'] not in db.shapes.slices.keys():
                logging.error('Skipping shape {}: cannot find shape data'.format(meta['name']))
                continue
            if meta['is_active']:
                self.data[meta['name']] = Shape(meta, db.shapes.get_slice(meta['name']),
                                                  self.active_dates_index,
                                                  self.active_dates_index_unique,
                                                  self.time_slice_elements,
                                                  self.num_active_years)

        self.process_active_shapes()

    @classmethod
    def get_values(cls, key, database_path=None):
        instance = cls.get_instance(database_path)
        if key not in instance.data:
            raise ValueError("shape named '{}' not found in pickled shapes".format(key))
        return instance.data[key].values

    @classmethod
    def get_active_dates_index(cls, database_path=None):
        return cls.get_instance(database_path).active_dates_index

    @classmethod
    def get_load_shape_base_year(cls, database_path=None):
        return cls.get_instance(database_path).load_shape_base_year

    @classmethod
    def get_hash_tuple(cls):
        cfg_weather_years = [int(y) for y in cfg.getParam('weather_years', section='TIME').split(',')]
        geography_check = (GeoMapper.demand_primary_geography, GeoMapper.supply_primary_geography, tuple(sorted(GeoMapper.primary_subset)), tuple(GeoMapper.breakout_geography))
        cfg_hash_tuple = geography_check + tuple(cfg_weather_years)
        return cfg_hash_tuple

    @classmethod
    def load_shape_pickle(cls, database_path, wait_time=0):
        time.sleep(wait_time)
        # load from pickle
        cfg_hash = hash(cls.get_hash_tuple())
        pickles_dir = os.path.join(database_path, 'ShapeData', 'pickles')
        pickle_path = os.path.join(pickles_dir, 'shapes_{}.p'.format(cfg_hash))

        if os.path.isfile(pickle_path) and os.path.getmtime(pickle_path) > newest_shape_file_modified_date(database_path):
            logging.info('Loading shapes')
            with open(pickle_path, 'rb') as infile:
                shapes = pickle.load(infile)
            Shapes._instance = shapes
            return True
        return False

    @classmethod
    def make_shapes(cls, database_path):
        # pickle didn't exist or was not what was needed
        Shapes._instance = Shapes(database_path)
        logging.info('Pickling shapes')
        cfg_hash = hash(cls.get_hash_tuple())
        pickles_dir = os.path.join(database_path, 'ShapeData', 'pickles')
        pickle_path = os.path.join(pickles_dir, 'shapes_{}.p'.format(cfg_hash))
        util.makedirs_if_needed(pickles_dir)
        with open(pickle_path, 'wb') as outfile:
            pickle.dump(Shapes._instance, outfile, pickle.HIGHEST_PROTOCOL)

    @classmethod
    def get_instance(cls, database_path=None, shape_owner=True):
        if Shapes._instance is not None:
            return Shapes._instance

        if database_path is None:
            from .error import PathwaysException
            raise PathwaysException("Shapes.get_instance: No Shapes instance exists and no database_path was specified")

        # load from pickle
        success = Shapes.load_shape_pickle(database_path, wait_time=0)
        if shape_owner and not success:
            Shapes.make_shapes(database_path)
        else:
            wait_time = 30
            while success is False:
                logging.info('Waiting {} seconds for shape process to finish before trying to load shapes...'.format(wait_time))
                success = Shapes.load_shape_pickle(database_path, wait_time=wait_time)

        return Shapes._instance

    def get_active_dates(self, years):
        active_dates_index = []
        for year in years:
            start_date, end_date = DT.datetime(year, 1, 1), DT.datetime(year, 12, 31, 23)
            # todo, change the frequency to change the timestep
            active_dates_index.append(pd.date_range(start_date, end_date, freq='H'))
        return functools.reduce(pd.DatetimeIndex.append, active_dates_index)

    def process_active_shapes(self):
        logging.info(' mapping data for:')

        if cfg.getParamAsBoolean('parallel_process', section='CALCULATION_PARAMETERS'):
            pool = pathos.multiprocessing.Pool(processes=cfg.getParamAsInt('num_cores', section='CALCULATION_PARAMETERS'), maxtasksperchild=1)
            shapes = pool.map(helper_multiprocess.process_shapes, self.data.values(), chunksize=1)
            pool.close()
            pool.join()
            self.data = dict(zip(self.data.keys(), shapes))
        else:
            for id in self.data:
                self.data[id].process_shape()

    def slice_sensitivities(self, sensitivities):
        logging.info(' slicing shape sensitivities')
        for shape_name in self.data:
            sensitivity_name = sensitivities.get_sensitivity('ShapeData', shape_name) or '_reference_'
            self.data[shape_name].slice_sensitivity(sensitivity_name)

class Shape(DataObject):
    def __init__(self, meta, raw_values, active_dates_index, active_dates_index_unique, time_slice_elements, num_active_years):
        self.name = meta['name']
        self.shape_type = meta['shape_type']
        self.input_type = meta['input_type']
        self.shape_unit_type = meta['shape_unit_type']
        self.time_zone = meta['time_zone']
        if self.time_zone is not None:
            self.time_zone = format_timezone_str(self.time_zone)
        self.geography = meta['geography']
        self.primary_geography = GeoMapper.demand_primary_geography if meta['supply_or_demand_side'] == 'd' else GeoMapper.supply_primary_geography
        self.geography_map_key = meta['geography_map_key']
        self.interpolation_method = meta['interpolation_method']
        self.extrapolation_method = meta['extrapolation_method']
        self.active_dates_index = active_dates_index
        self.active_dates_index_unique = active_dates_index_unique
        self.time_slice_elements = time_slice_elements
        self.num_active_years = num_active_years

        if self.shape_type=='weather date':
            raw_values['weather_datetime'] = util.DateTimeLookup.lookup(raw_values['weather_datetime'])
            raw_values['weather_datetime'].freq = 'H'

        self.raw_values = raw_values.set_index([c for c in raw_values.columns if c!='value']).sort_index()
        self.raw_values.index = self.raw_values.index.rename(self.geography, level='gau')
        self.values = None
        self.values_all_sensitivities = None
        self.extrapolation_growth = None
        self.raw_values = self.filter_foreign_gaus(self.raw_values)

    def filter_foreign_gaus(self, raw_values):
        geographies_to_keep = GeoMapper.geography_to_gau[self.geography]
        keep_index = raw_values.index.get_level_values(self.geography).isin(geographies_to_keep)
        raw_values = raw_values[keep_index].reset_index().set_index(raw_values.index.names)
        return raw_values

    @staticmethod
    def make_flat_load_shape(index, column='value'):
        assert 'weather_datetime' in index.names
        flat_shape = util.empty_df(fill_value=1., index=index, columns=[column])
        group_to_normalize = [n for n in flat_shape.index.names if n!='weather_datetime']
        flat_shape = flat_shape.groupby(level=group_to_normalize).transform(lambda x: x / x.sum()) * Shapes.get_instance().num_active_years
        return flat_shape

    def slice_sensitivity(self, sensitivity_name):
        # if the shape doesn't have sensitivities, we don't want to copy it
        if self.values_all_sensitivities is None and 'sensitivity' not in self.values.index.names:
            return

        # because we are replacing final data, we need to keep a record of the unsliced data for the next sensitivity
        if self.values_all_sensitivities is None:
            self.values_all_sensitivities = self.values.copy()

        if sensitivity_name not in self.values_all_sensitivities.index.get_level_values('sensitivity').unique():
            raise ValueError('Sensitivity name {} not found in shape {}'.format(sensitivity_name, self.name))

        self.values = self.values_all_sensitivities.xs(sensitivity_name, level='sensitivity')

    def create_empty_shape_data(self, raw_values):
        self._active_time_keys = [ind for ind in raw_values.index.names if ind in Shapes.time_slice_col]
        self._active_time_dict = dict([(ind, loc) for loc, ind in enumerate(raw_values.index.names) if ind in Shapes.time_slice_col])

        self._non_time_keys = [ind for ind in raw_values.index.names if ind not in self._active_time_keys]
        self._non_time_dict = dict([(ind, loc) for loc, ind in enumerate(raw_values.index.names) if ind in self._non_time_keys])

        data = pd.DataFrame(index=pd.DatetimeIndex(self.active_dates_index, name='weather_datetime'))

        for ti in self._active_time_keys:
            # hour is given as 1-24 not 0-23
            if ti == 'hour' and min(raw_values.index.levels[self._active_time_dict['hour']]) == 1 and max(raw_values.index.levels[self._active_time_dict['hour']]) == 24:
                # the minimum value is 1 and max value is 24
                data[ti] = self.time_slice_elements['hour24']
            else:
                data[ti] = self.time_slice_elements[ti]

        non_time_levels = [list(l) for l, n in zip(raw_values.index.levels, raw_values.index.names) if n in self._non_time_keys]
        # this next step could be done outside of a for loop, but I'm not able to get the Pandas syntax to take
        for name, level in zip(self._non_time_keys, non_time_levels):
            data = pd.concat([data] * len(level), keys=level, names=[name])

        data.reset_index(inplace=True)

        return data

    def standardize_shape_type(self, raw_values):
        if self.shape_type=='weather date':
            final_data = util.reindex_df_level_with_new_elements(raw_values, 'weather_datetime', self.active_dates_index) # this step is slow, consider replacing
            if final_data.isnull().values.any():
                # do some interpolation to fill missing values, that that still doesn't work to remove the NaNs, we raise an error
                final_data = final_data.groupby(level=[name for name in final_data.index.names if name!='weather_datetime']).apply(pd.DataFrame.interpolate).ffill().bfill()
                if final_data.isnull().values.any():
                    raise ValueError('Weather data for shape {} did not give full coverage of the active dates:\n {}'.format(self.name, final_data[final_data.isnull().values]))
        elif self.shape_type=='time slice':
            final_data = self.create_empty_shape_data(raw_values)
            final_data = pd.merge(final_data, raw_values.reset_index(), how='left')
            final_data = final_data.set_index([c for c in final_data.columns if c!='value']).sort_index()
            if self.shape_unit_type=='energy':
                if 'week' in self._active_time_keys:
                    raise ValueError('Shape unit type energy with week timeslice is not recommended due to edge effects')
                final_data = self.convert_energy_to_power(final_data)
            if final_data.isnull().values.any():
                print(final_data[final_data.isnull().values])
                raise ValueError('Shape {} time slice data did not give full coverage of the active dates.'.format(self.name))
            # reindex to remove the helper columns
            active_time_keys_keep_hydro_year = list(set(self._active_time_keys) - set(['hydro_year']))
            final_data.index = final_data.index.droplevel(active_time_keys_keep_hydro_year)
            # drop any duplicates
            final_data = final_data.groupby(level=final_data.index.names).first()
        else:
            raise ValueError('{} shape_type must be "weather date" or "time slice", not {}'.format(self.name, self.shape_type))
        final_data = final_data.swaplevel('weather_datetime', -1).sort_index()
        return final_data

    def process_shape(self):
        logging.info('    shape: ' + self.name)
        final_data = self.standardize_shape_type(self.raw_values)
        logging.debug('        ...filtering geographies')
        final_data = GeoMapper.get_instance().filter_extra_geos_from_df(final_data)
        logging.debug('        ...mapping to time zones')
        final_data = self.geomap_to_time_zone(final_data)
        final_data = self.localize_shapes(final_data)
        final_data = self.standardize_time_across_timezones(final_data)
        logging.debug('        ...mapping to model geography')
        final_data = self.geomap_to_primary_geography(final_data)
        logging.debug('        ...summing across time zones')
        final_data = self.sum_over_time_zone(final_data)
        #it's much easier to work with if we just strip out the timezone information at this point
        final_data = final_data.tz_localize(None, level='weather_datetime')
        logging.debug('        ...normalizing shapes')
        final_data = self.normalize(final_data)
        if final_data.sum().sum() == 0:
            logging.info("'{}' shape data is all zeros after processing. This indicates an error upstream and if not fixed will cause issues downstream.".format(self.name))
        self.values = final_data
        #raw values can be very large, so we delete it in this one case
        del self.raw_values

    def add_timeshift_type(self):
        """Later these shapes will need a level called timeshift type, and it is faster to add it now if it doesn't already have it"""
        if 'timeshift_type' not in self.values.index.names:
            self.values['timeshift_type'] = 'native'
            self.values = self.values.set_index('timeshift_type', append=True).swaplevel('timeshift_type', 'weather_datetime').sort_index()

    def normalize(self, df):
        group_to_normalize = [n for n in df.index.names if n!='weather_datetime']
        # here is a special case where I have p_min and p_max in my dispatch constraints and these should not be normalized
        if 'dispatch_constraint' in group_to_normalize:
            # this first normailization does what we need for hydro pmin and pmax, which is a special case of normalization
            combined_map_df = util.DfOper.mult((self.map_df_tz, self.map_df_primary))
            normalization_factors = combined_map_df.groupby(level=self.primary_geography).sum()
            norm_df = util.DfOper.divi((df, normalization_factors))

            temp = norm_df.groupby(level=group_to_normalize).transform(lambda x: x / x.sum())*self.num_active_years
            indexer = util.level_specific_indexer(temp, 'dispatch_constraint', [['p_min', 'p_max']])
            temp.loc[indexer, :] = norm_df.loc[indexer, :]

            norm_df = temp
        else:
            norm_df = df.groupby(level=group_to_normalize).transform(lambda x: x / x.sum())*self.num_active_years

        return norm_df

    def convert_energy_to_power(self, df):
        lengths = df.groupby(level=self._active_time_keys).apply(len).to_frame().rename(columns={0: 'len'})
        # here is a special case where I have p_min and p_max in my dispatch constraints and these should not be normalized
        if 'dispatch_constraint' in df.index.names:
            # this first normailization does what we need for hydro pmin and pmax, which is a special case of normalization
            df_copy = df.copy()
            new_df = util.DfOper.divi((df, lengths))
            indexer = util.level_specific_indexer(df_copy, 'dispatch_constraint', [['p_min', 'p_max']])
            new_df.loc[indexer, :] = df_copy.loc[indexer, :]
        else:
            new_df = util.DfOper.divi((df, lengths))
        return new_df

    def geomap_to_time_zone(self, df):
        """ maps a dataframe to another geography using relational GeographyMapdatabase table
        """
        geography_map_key = self.geography_map_key or GeoMapper.default_geography_map_key

        # create dataframe with map from one geography to another
        # we always want to normalize as a total here because we will re-sum over time zone later
        self.map_df_tz = GeoMapper.get_instance().map_df(self.geography, 'time zone', normalize_as='total', map_key=geography_map_key)

        mapped_data = util.DfOper.mult([df, self.map_df_tz])
        mapped_data = mapped_data.swaplevel('weather_datetime', -1)
        return mapped_data.sort_index()

    def geomap_to_primary_geography(self, df):
        """ maps the dataframe to primary geography
        """
        geography_map_key = self.geography_map_key or GeoMapper.default_geography_map_key
        # here we map to two geographies, the time zone and the model primary geography. If we don't do this it causes a bug whenever disaggregating input data
        self.map_df_primary = GeoMapper.get_instance().map_df(self.geography, ['time zone', self.primary_geography], normalize_as=self.input_type, map_key=geography_map_key)
        mapped_data = util.DfOper.mult((df, self.map_df_primary), fill_value=np.nan)

        if self.geography != self.primary_geography and self.geography != 'time zone':
            mapped_data = util.remove_df_levels(mapped_data, self.geography)
        mapped_data = mapped_data.swaplevel('weather_datetime', -1)

        mapped_data.sort_index()
        return mapped_data

    def sum_over_time_zone(self, df):
        if self.primary_geography == 'time zone':
            return df

        levels = [ind for ind in df.index.names if ind != 'time zone']
        df_no_tz = df.groupby(level=levels).sum()
        return df_no_tz.sort_index()

    def standardize_time_across_timezones(self, df):
        tz = pytz.timezone(cfg.getParam('dispatch_outputs_timezone', section='TIME'))
        offset = (tz.utcoffset(DT.datetime(2015, 1, 1)) + tz.dst(DT.datetime(2015, 1, 1))).total_seconds() / 60.
        new_index = pd.DatetimeIndex(self.active_dates_index_unique, tz=pytz.FixedOffset(offset))
        # if we have hydro year, when this does a reindex, it can introduce NaNs, so we want to remove them after
        assert not df.isnull().any().any()
        standardize_df = util.reindex_df_level_with_new_elements(df.copy(), 'weather_datetime', new_index)

        levels = [n for n in df.index.names if n != 'weather_datetime']
        standardize_df = standardize_df.groupby(level=levels).fillna(method='bfill').fillna(method='ffill')
        standardize_df = standardize_df[~standardize_df.isnull().values]

        return standardize_df

    def localize_shapes(self, df):
        """ Step through time zone and put each profile mapped to time zone in that time zone
        """
        df_list = []
        for tz, group in df.groupby(level='time zone'):
            # get the time zone name and figure out the offset from UTC
            tz = pytz.timezone(self.time_zone or format_timezone_str(tz))
            _dt = DT.datetime(2015, 1, 1)
            offset = (tz.utcoffset(_dt) + tz.dst(_dt)).total_seconds()/60.
            # localize and then convert to dispatch_outputs_timezone
            df2 = group.tz_localize(pytz.FixedOffset(offset), level='weather_datetime')
            df2 = df2.tz_convert(pytz.FixedOffset(offset), level='weather_datetime')
            df_list.append(df2)

        local_df = pd.concat(df_list)
        return local_df.sort_index()

    @staticmethod
    def ensure_feasible_flexible_load(df):
        names = [n for n in df.index.names if n != 'weather_datetime']
        cum_df = df.groupby(level=names).cumsum()

        add_to_1 = min(0, (cum_df[2] - cum_df[1]).min())*1.01
        subtract_from_3 = min(0, (cum_df[3] - cum_df[2]).min())*1.01

        if add_to_1 < 0:
            df.iloc[0,0] += add_to_1
            cum_df = df[1].groupby(level=names).cumsum()
            make_zero = np.nonzero(cum_df.values<0)[0]
            if len(make_zero):
                replace = make_zero[-1] + 1
                df.iloc[make_zero, 0] = 0
                df.iloc[replace, 0] = cum_df.iloc[replace]
            df.iloc[-1, 0] += (df[2].sum() - df[1].sum())

        if subtract_from_3 < 0:
            df.iloc[0,2] -= subtract_from_3
            cum_df = df[3].groupby(level=names).cumsum()
            cum_diff = df[2].sum() - cum_df
            make_zero = np.nonzero(cum_diff.values<0)[0][1:]
            if len(make_zero):
                replace = make_zero[0] - 1
                df.iloc[make_zero, 2] = 0
                df.iloc[replace, 2] += cum_diff.iloc[replace]
            else:
                df.iloc[-1, 2] += cum_diff.iloc[-1]

        cum_df = df.groupby(level=names).cumsum()

        if ((cum_df[1] - cum_df[2]) > 1E-12).any():
            logging.error('Infeasible flexible load constraints were created where the delayed load shape is greater than the native load shape')
            logging.error(cum_df[cum_df[1] > cum_df[2]])
            pdb.set_trace()

        if ((cum_df[2] - cum_df[3]) > 1E-12).any():
            logging.error('Infeasible flexible load constraints were created where the advanced load shape is less than the native load shape')
            logging.error(cum_df[cum_df[2] > cum_df[3]])
            pdb.set_trace()

        return df

    @staticmethod
    def produce_flexible_load(shape_df, percent_flexible=None, hr_delay=None, hr_advance=None):
        hr_delay = 0 if hr_delay is None else int(hr_delay)
        hr_advance = 0 if hr_advance is None else int(hr_advance)

        native_slice = shape_df.copy()
        native_slice_stacked = pd.concat([native_slice]*3, keys=['delayed','native','advanced'], names=['timeshift_type'])

        pflex_stacked = pd.concat([percent_flexible]*3, keys=['delayed','native','advanced'], names=['timeshift_type'])

        # positive hours is a shift forward, negative hours a shift back
        shift = lambda df, hr: df.shift(hr).ffill().fillna(value=0)

        def fix_first_point(df, hr):
            df.iloc[0] += native_slice.iloc[:hr].sum().sum()
            return df

        non_weather = [n for n in native_slice.index.names if n!='weather_datetime']

        delay_load = native_slice.groupby(level=non_weather).apply(shift, hr=hr_delay)
        advance_load = native_slice.groupby(level=non_weather).apply(shift, hr=-hr_advance)
        advance_load = advance_load.groupby(level=non_weather).transform(fix_first_point, hr=hr_advance)

        full_load = pd.concat([advance_load, delay_load, native_slice], keys=['advanced','delayed','native'], names=['timeshift_type'])

        return util.DfOper.add((util.DfOper.mult((full_load, pflex_stacked), collapsible=False),
                                util.DfOper.mult((native_slice_stacked, 1 - pflex_stacked), collapsible=False)))


