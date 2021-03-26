

import pandas as pd
import pytz
import datetime as DT
import numpy as np
import cPickle as pickle
import os
import logging
import pdb
import pathos
import helper_multiprocess
import time
import shutil
from csvdb import CsvDatabase
import config as cfg
from energyPATHWAYS.geomapper import GeoMapper
import util
from energyPATHWAYS.data_object import DataObject
from csvdb.table import REF_SENSITIVITY

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

# def newest_shape_file_modified_date(database_path):
#     max_shapes_data_modified = 0
#     for dirpath, dirnames, filenames in os.walk(os.path.join(database_path, 'ShapeData'), topdown=False):
#         valid_paths = [os.path.join(dirpath, file_name) for file_name in filenames if file_name[-7:]=='.csv.gz' or file_name[-5:]=='.csv']
#         max_date_modified_in_folder = max([os.path.getmtime(valid_path) for valid_path in valid_paths]) if len(valid_paths) else 0
#         max_shapes_data_modified = max(max_shapes_data_modified, max_date_modified_in_folder)
#     shape_meta_modified = os.path.getmtime(os.path.join(database_path, 'ShapeProcessor.csv'))
#     return max(max_shapes_data_modified, shape_meta_modified)

def oldest_file_date(path):
    min_modified = np.inf
    for dirpath, dirnames, filenames in os.walk(path, topdown=False):
        valid_paths = [os.path.join(dirpath, file_name) for file_name in filenames]
        min_modified_in_folder = min([os.path.getmtime(valid_path) for valid_path in valid_paths]) if len(valid_paths) else np.inf
        min_modified = min(min_modified, min_modified_in_folder)
    return min_modified

def get_active_dates(years):
    active_dates_index = []
    for year in util.ensure_iterable(years):
        start_date, end_date = DT.datetime(year, 1, 1), DT.datetime(year, 12, 31, 23)
        active_dates_index.append(pd.date_range(start_date, end_date, freq='H'))
    return reduce(pd.DatetimeIndex.append, active_dates_index)

PICKLE_NAME_DELIMITER = "^v^"

def make_pickle_name(primary_geography, primary_subset, breakout_geography):
    pickle_tup = primary_geography, tuple(sorted(primary_subset)), tuple(breakout_geography)
    pickle_name = PICKLE_NAME_DELIMITER.join([str(tup).replace(" ", "") for tup in pickle_tup]) + '.p'
    return pickle_name

class ShapeContainer(object):
    _instance = None

    def __init__(self, database_path, scenario_obj):
        self.database_path = database_path
        self.scenario_obj = scenario_obj
        db = CsvDatabase.get_database(database_path)
        self.shape_meta = db.get_table("Shapes").data

        self.cfg_weather_years = [int(y) for y in cfg.getParam('weather_years', section='TIME').split(',')]
        self.active_dates_index = get_active_dates(self.cfg_weather_years)
        self.num_active_years = num_active_years(self.active_dates_index)

        self.load_shape_base_year = max(int(np.round(np.mean(self.cfg_weather_years))), cfg.getParamAsInt('current_year', section='TIME'))

        self.data = {}
        ShapeContainer._instance = self

    @classmethod
    def get_active_dates_index(cls):
        return cls.get_instance().active_dates_index

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            raise ValueError("ShapeContainer init must be called before get_instace")
        return cls._instance

    @classmethod
    def get_load_shape_base_year(cls):
        return cls.get_instance().load_shape_base_year

    @staticmethod
    def shape_normalize(df, num_active_years):
        group_to_normalize = [n for n in df.index.names if n != 'weather_datetime']
        # here is a special case where I have p_min and p_max in my dispatch constraints and these should not be normalized
        if 'dispatch_constraint' in group_to_normalize:
            temp = df.groupby(level=group_to_normalize).transform(lambda x: x / x.sum()) * num_active_years
            indexer = util.level_specific_indexer(temp, 'dispatch_constraint', [['p_min', 'p_max']])
            temp.loc[indexer, :] = df.loc[indexer, :]
            norm_df = temp
        else:
            norm_df = df.groupby(level=group_to_normalize).transform(lambda x: x / x.sum()) * num_active_years
        return norm_df

    @classmethod
    def get_values(cls, shape_name):
        # data should be pre-filtered by sensitivity names and years
        instance = cls.get_instance()
        if shape_name in instance.data:
            return instance.data[shape_name]

        sensitivity_name = str(instance.scenario_obj.get_sensitivity('ShapeData', shape_name) or '_reference_')
        pickle_name = make_pickle_name(GeoMapper.demand_primary_geography, GeoMapper.primary_subset, GeoMapper.breakout_geography)

        df = []
        for year in instance.cfg_weather_years:
            pickle_path = os.path.join(instance.database_path, 'ShapeData', 'pickles', shape_name, str(year), sensitivity_name, pickle_name)
            shape_obj = ShapePickler.load_pickle(pickle_path)
            df.append(shape_obj.values)
        result = pd.concat(df)
        if len(df) > 1:
            result = ShapeContainer.shape_normalize(df, num_active_years=len(df))
        instance.data[shape_name] = result

        return instance.data[shape_name]


class ShapePickler():
    # cfg_weather_years is used just when we have a time slice profile
    def __init__(self, database_path):
        self.database_path = database_path
        self.base_path = os.path.join(database_path, 'ShapeData', 'pickles')
        db = CsvDatabase.get_database(database_path)
        shape_meta = db.get_table("Shapes").data
        self.shape_objects = {}
        self.shapes_file_map = db.shapes.file_map
        self.cfg_weather_years = [int(y) for y in cfg.getParam('weather_years', section='TIME').split(',')]

        for i, meta in shape_meta.iterrows():
            if self.pickles_up_to_date(meta):
                continue

            raw_values = db.shapes.get_slice(meta['name'])

            if meta['name'] not in db.shapes.file_map:
                logging.error('Skipping shape {}: cannot find shape data'.format(meta['name']))
                continue

            if meta['shape_type'] == 'time slice':
                years = self.cfg_weather_years
                raw_values = raw_values.set_index([c for c in raw_values.columns if c != 'value']).sort_index()
                raw_values = pd.concat([raw_values]*len(years), keys=years, names=['weather_year'])
            elif meta['shape_type'] == 'weather date':
                raw_values = self.pre_process_weather_datetime_shape(raw_values, meta)
                years = sorted(set(raw_values.index.get_level_values('weather_year')))
                missing_years = list(set(self.cfg_weather_years) - set(years))
                if len(missing_years):
                    raise ValueError('Model configuration has specified weather years {}, and shape name {} is missing data for years {} in the input files'.format(self.cfg_weather_years, meta['shape_type'], missing_years))
            else:
                raise ValueError("Unrecognized shape_type '{}' for shape name '{}'".format(meta['shape_type'], meta['name']))

            raw_values.index = raw_values.index.rename(meta['geography'], level='gau')
            group_levels = ['weather_year', 'sensitivity'] if 'sensitivity' in raw_values.index.names else ['weather_year']
            groups = raw_values.groupby(level=group_levels)
            for i, raw_values_slice in groups:
                self.shape_objects[(meta['name'], i)] = ShapeObj(raw_values_slice, meta, self.base_path)

        if len(self.shape_objects):
            self.process_active_shapes()
        print "Shape pickles are complete"

    def pre_process_weather_datetime_shape(self, raw_values, meta):
        raw_values['weather_datetime'] = util.DateTimeLookup.lookup(raw_values['weather_datetime'])
        raw_values['weather_datetime'].freq = 'H'
        raw_values['weather_year'] = pd.DatetimeIndex(raw_values['weather_datetime']).year
        raw_values = raw_values.set_index([c for c in raw_values.columns if c != 'value']).sort_index()
        return raw_values

    @classmethod
    def load_pickle(cls, pickle_path):
        while True:
            try:
                with open(pickle_path, 'rb') as infile:
                    shape_obj = pickle.load(infile)
                return shape_obj
            except:
                print "unable to read from pickle path {}".format(pickle_path)
                input("press any key to retry")


    def pickles_up_to_date(self, meta):
        shape_name = meta['name']

        if not os.path.exists(os.path.join(self.base_path, shape_name)):
            return False

        pickle_date_modified = oldest_file_date(os.path.join(self.base_path, shape_name))
        shape_file_map = util.ensure_iterable(self.shapes_file_map[shape_name])
        csv_date_modified = max([os.path.getmtime(valid_path) for valid_path in shape_file_map])

        if csv_date_modified > pickle_date_modified:
            # the csv file has been updated and we need to redo the pickles after removing them all
            shutil.rmtree(os.path.join(self.base_path, shape_name))
            return False

        primary_geography = GeoMapper.demand_primary_geography if meta['supply_or_demand_side'] == 'd' else GeoMapper.supply_primary_geography
        needed_pickle_name = make_pickle_name(primary_geography, GeoMapper.primary_subset, GeoMapper.breakout_geography)
        # we could also need to process shapes if the years don't match, the geographies don't match
        for year in self.cfg_weather_years:
            path = os.path.join(self.base_path, shape_name, str(year))
            if not os.path.exists(path):
                return False # it appears we are missing the needed weather years

            for sensitivity_name in os.listdir(path):
                if not os.path.isdir(os.path.join(path, sensitivity_name)):
                    continue
                pickle_names = [file_name for file_name in os.listdir(os.path.join(path, sensitivity_name)) if file_name[-2:] == '.p']
                if needed_pickle_name not in pickle_names:
                    return False # it appears we are missing the needed geography

        return True # if we've passed all the tests, the pickles check out

    def process_active_shapes(self):
        logging.info(' mapping data for:')

        if cfg.getParamAsBoolean('parallel_process', section='CALCULATION_PARAMETERS'):
            pool = pathos.multiprocessing.Pool(processes=cfg.getParamAsInt('num_cores', section='CALCULATION_PARAMETERS'), maxtasksperchild=1)
            pool.map(helper_multiprocess.process_shapes, self.shape_objects.values(), chunksize=1)
            pool.close()
            pool.join()
        else:
            for name in self.shape_objects:
                self.shape_objects[name].process_shape()


class ShapeObj(DataObject):
    time_slice_col = ['year', 'month', 'week', 'day_type', 'hour']
    def __init__(self, raw_values, meta, base_path):
        self.name = meta['name']
        self.shape_type = meta['shape_type']
        self.input_type = meta['input_type']
        self.shape_unit_type = meta['shape_unit_type']
        self.time_zone = None if meta['time_zone'] is None else format_timezone_str(meta['time_zone'])
        self.geography = meta['geography']
        self.geography_map_key = meta['geography_map_key']
        self.interpolation_method = meta['interpolation_method']
        self.extrapolation_method = meta['extrapolation_method']

        self.primary_geography = GeoMapper.demand_primary_geography if meta['supply_or_demand_side'] == 'd' else GeoMapper.supply_primary_geography

        self.weather_year = raw_values.index.get_level_values('weather_year').unique()[0]
        self.sensitivity_name = REF_SENSITIVITY if 'sensitivity' not in raw_values.index.names else raw_values.index.get_level_values('sensitivity').unique()[0]

        raw_values = util.remove_df_levels(raw_values, ['weather_year', 'sensitivity'])
        self.raw_values = self.filter_foreign_gaus(raw_values)
        self.values = None

        self.active_dates_index = get_active_dates(self.weather_year)
        self.time_slice_elements = create_time_slice_elements(self.active_dates_index)
        self.num_active_years = 1
        self.extrapolation_growth = None

        self.pickle_path = os.path.join(base_path, str(self.name), str(self.weather_year), self.sensitivity_name)


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
        flat_shape = flat_shape.groupby(level=group_to_normalize).transform(lambda x: x / x.sum()) * ShapeContainer._instance.num_active_years
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
        self._active_time_keys = [ind for ind in raw_values.index.names if ind in ShapeObj.time_slice_col]
        self._active_time_dict = dict([(ind, loc) for loc, ind in enumerate(raw_values.index.names) if ind in ShapeObj.time_slice_col])

        self._non_time_keys = [ind for ind in raw_values.index.names if ind not in self._active_time_keys]
        self._non_time_dict = dict([(ind, loc) for loc, ind in enumerate(raw_values.index.names) if ind in self._non_time_keys])

        data = pd.DataFrame(index=pd.Index(self.active_dates_index, name='weather_datetime'))

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
                print final_data[final_data.isnull().values]
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
        logging.info('    shape: {}, {}, {}'.format(self.name, self.weather_year, self.sensitivity_name))
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
        self.pickle_self()

    def pickle_self(self):
        util.makedirs_if_needed(self.pickle_path)
        pickle_name = make_pickle_name(self.primary_geography, GeoMapper.primary_subset, GeoMapper.breakout_geography)
        with open(os.path.join(self.pickle_path, pickle_name), 'wb') as outfile:
            pickle.dump(self, outfile, pickle.HIGHEST_PROTOCOL)

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
        new_index = pd.DatetimeIndex(self.active_dates_index, tz=pytz.FixedOffset(offset))
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
        dfs = []
        for tz, group in df.groupby(level='time zone'):
            # get the time zone name and figure out the offset from UTC
            tz = pytz.timezone(self.time_zone or format_timezone_str(tz))
            _dt = DT.datetime(2015, 1, 1)
            offset = (tz.utcoffset(_dt) + tz.dst(_dt)).total_seconds() / 60.
            # localize and then convert to dispatch_outputs_timezone
            df2 = group.tz_localize(pytz.FixedOffset(offset), level='weather_datetime')
            dfs.append(df2)

        tz = pytz.timezone(cfg.getParam('dispatch_outputs_timezone', section='TIME'))
        offset = (tz.utcoffset(DT.datetime(2015, 1, 1)) + tz.dst(DT.datetime(2015, 1, 1))).total_seconds() / 60.
        local_df = pd.concat(dfs)
        local_df = local_df.tz_convert(pytz.FixedOffset(offset), level='weather_datetime')
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

