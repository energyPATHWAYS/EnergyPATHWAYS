# -*- coding: utf-8 -*-
"""
Created on Mon Oct 05 14:45:48 2015

@author: ryan
"""

import pandas as pd
import pytz
import datetime as DT
# PyCharm complains about dateutil not being listed in the project requirements, but my understanding is that
# it is bundled with matplotlib, so it is listed implicitly.
from dateutil.relativedelta import relativedelta
import time
import numpy as np
import cPickle as pickle
import os
import logging
import pdb

from csvdb import CsvDatabase
from . import config as cfg
from .geomapper import GeoMapper
from .time_series import TimeSeries
from . import util

from .data_object import DataObject

# from RIO.riodb.data_mapper import DataMapper
# from RIO import fileio

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

def format_timezone_str(tz):
    tz = tz.split("/")
    tz = [x.split("_") for x in tz]
    tz = [[y.lower().capitalize() if len(y) != 2 else y.upper() for y in x] for x in tz]
    tz = ["_".join(x) for x in tz]
    tz = "/".join(tz)
    return tz

def newest_shape_file_modified_date(database_path):
    return max([os.path.getmtime(os.path.join(database_path, 'ShapeData', file_name)) for file_name in os.listdir(os.path.join(database_path, 'ShapeData'))])

class Shapes(object):
    _instance = None
    time_slice_col = ['year', 'month', 'week', 'day_type', 'hour']

    def __init__(self, database_path=None):
        db = CsvDatabase.get_database(database_path)
        db.shapes.load_all()
        self.cfg_weather_years = [int(y) for y in cfg.getParam('weather_years').split(',')]
        self.set_active_dates()
        self.num_active_years = num_active_years(self.active_dates_index)
        self.cfg_outputs_timezone = pytz.timezone(cfg.getParam('dispatch_outputs_timezone'))
        self.cfg_hash_tuple = (GeoMapper.cfg_geography, tuple(sorted(GeoMapper.cfg_gau_subset)),
                               tuple(GeoMapper.cfg_gau_breakout), tuple([int(y) for y in cfg.getParam('weather_years').split(',')]), tuple(DataObject.get_default_years()))
        self.cfg_hash = hash(self.cfg_hash_tuple)

        shape_meta = db.get_table("SHAPE_META").data
        self.data = {}
        for i, meta in shape_meta.iterrows():
            if meta['name'] not in db.shapes.slices.keys():
                logging.error('Skipping shape {}: cannot find shape data'.format(meta['name']))
                continue
            self.data[meta['name']] = Shape(meta, db.shapes.get_slice(meta['name']), self)

        self.process_active_shapes()

    @classmethod
    def get_instance(cls, database_path):
        if Shapes._instance is not None:
            return Shapes._instance

        # load from pickle
        cfg_hash = hash((GeoMapper.cfg_geography, tuple(sorted(GeoMapper.cfg_gau_subset)),
                         tuple(GeoMapper.cfg_gau_breakout), tuple([int(y) for y in cfg.getParam('weather_years').split(',')]), tuple(DataObject.get_default_years())))
        pickle_path = os.path.join(database_path, 'ShapeData', 'pickles', '{}_shapes_{}.p'.format(GeoMapper.cfg_geography, cfg_hash))
        if os.path.isfile(pickle_path) and os.path.getmtime(pickle_path) > newest_shape_file_modified_date(database_path):
            logging.info('Loading shapes')
            with open(pickle_path, 'rb') as infile:
                shapes = pickle.load(infile)
            Shapes._instance = shapes
            return Shapes._instance

        # pickle didn't exist or was not what was needed
        Shapes._instance = Shapes(database_path)
        logging.info('Pickling shapes')
        util.makedirs_if_needed(os.path.join(database_path, 'ShapeData', 'pickles'))
        with open(pickle_path, 'wb') as outfile:
            pickle.dump(Shapes._instance, outfile, pickle.HIGHEST_PROTOCOL)
        return Shapes._instance

    def set_active_dates(self):
        active_dates_index = []
        for year in self.cfg_weather_years:
            start_date, end_date = DT.datetime(year, 1, 1), DT.datetime(year, 12, 31, 23)
            active_dates_index.append(pd.date_range(start_date, end_date, freq='H'))

        self.active_dates_index = reduce(pd.DatetimeIndex.append, active_dates_index)
        self.time_slice_elements = create_time_slice_elements(self.active_dates_index)

    def process_active_shapes(self):
        #run the weather date shapes first because they inform the daterange for dispatch
        logging.info(' mapping data for:')

        for shape_name in self.data:
            self.data[shape_name].process_shape()

    def slice_sensitivities(self, sensitivities):
        logging.info(' slicing shape sensitivities')
        index_divider = '--'
        for shape_name in self.data:
            sensitivity_id = shape_name + index_divider + shape_name
            sensitivity_name = sensitivities[sensitivity_id] if sensitivity_id in sensitivities.index else '_reference_'
            self.data[shape_name].slice_sensitivity(sensitivity_name)

class Shape(DataObject):
    def __init__(self, meta, timeseries, all_shapes):
        self.name = meta['name']
        self.shape_type = meta['shape_type']
        self.input_type = meta['input_type']
        self.shape_unit_type = meta['shape_unit_type']
        self.time_zone = meta['time_zone']
        if self.time_zone is not None:
            self.time_zone = format_timezone_str(self.time_zone)
        self.geography = meta['geography']
        self.geography_map_key = meta['geography_map_key']
        self.interpolation_method = meta['interpolation_method']
        self.extrapolation_method = meta['extrapolation_method']
        self.all_shapes = all_shapes

        if self.shape_type=='weather date':
            timeseries['weather_datetime'] = util.DateTimeLookup.lookup(timeseries['weather_datetime'])
            timeseries['weather_datetime'].freq = 'H'

        self.timeseries = timeseries.set_index([c for c in timeseries.columns if c!='value']).sort_index()
        self.timeseries.index = self.timeseries.index.rename(self.geography, level='gau')
        self.final_data = None
        self.final_data_all_sensitivities = None

    def slice_sensitivity(self, sensitivity_name):
        # if the shape doesn't have sensitivities, we don't want to copy it
        if self.final_data_all_sensitivities is None and 'sensitivity' not in self.final_data.index.names:
            return

        # because we are replacing final data, we need to keep a record of the unsliced data for the next sensitivity
        if self.final_data_all_sensitivities is None:
            self.final_data_all_sensitivities = self.final_data.copy()

        if sensitivity_name not in self.final_data_all_sensitivities.index.get_level_values('sensitivity').unique():
            raise ValueError('Sensitivity name {} not found in shape {}'.format(sensitivity_name, self.name))

        self.final_data = self.final_data_all_sensitivities.xs(sensitivity_name, level='sensitivity')

    def create_empty_shape_data(self):
        self._active_time_keys = [ind for ind in self.timeseries.index.names if ind in Shapes.time_slice_col]
        self._active_time_dict = dict([(ind, loc) for loc, ind in enumerate(self.timeseries.index.names) if ind in Shapes.time_slice_col])

        self._non_time_keys = [ind for ind in self.timeseries.index.names if ind not in self._active_time_keys]
        self._non_time_dict = dict([(ind, loc) for loc, ind in enumerate(self.timeseries.index.names) if ind in self._non_time_keys])

        data = pd.DataFrame(index=pd.Index(self.all_shapes.active_dates_index, name='weather_datetime'))

        for ti in self._active_time_keys:
            #hour is given as 1-24 not 0-23
            if ti=='hour' and min(self.timeseries.index.levels[self._active_time_dict['hour']])==1 and max(self.timeseries.index.levels[self._active_time_dict['hour']])==24:
                # the minimum value is 1 and max value is 24
                data[ti] = self.all_shapes.time_slice_elements['hour24']
            else:
                data[ti] = self.all_shapes.time_slice_elements[ti]

        non_time_levels = [list(l) for l, n in zip(self.timeseries.index.levels, self.timeseries.index.names) if n in self._non_time_keys]
        # this next step could be done outside of a for loop, but I'm not able to get the Pandas syntax to take
        for name, level in zip(self._non_time_keys, non_time_levels):
            data = pd.concat([data]*len(level), keys=level, names=[name])

        data.reset_index(inplace=True)

        return data.set_index(self._non_time_keys+self._active_time_keys+['weather_datetime']).sort_index()

    def process_shape(self):
        logging.info('    shape: ' + self.name)
        if self.shape_type=='weather date':
            final_data = util.reindex_df_level_with_new_elements(self.timeseries, 'weather_datetime', self.all_shapes.active_dates_index) # this step is slow, consider replacing
            if final_data.isnull().values.any():
                raise ValueError('Weather data for shape {} did not give full coverage of the active dates'.format(self.name))
        elif self.shape_type=='time slice':
            final_data = self.create_empty_shape_data()
            final_data = pd.merge(final_data.reset_index(), self.timeseries.reset_index())
            final_data = final_data.set_index([c for c in final_data.columns if c!='value']).sort_index()
            if self.shape_unit_type=='energy':
                final_data = self.convert_energy_to_power(final_data)
            if final_data.isnull().values.any():
                raise ValueError('Shape time slice data did not give full coverage of the active dates')
            # reindex to remove the helper columns
            final_data.index = final_data.index.droplevel(self._active_time_keys)

        final_data = final_data.swaplevel('weather_datetime', -1).sort_index()
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
        if 'year' in final_data.index.names:
            self.extrapolation_growth = None
            final_data = self.clean_timeseries(df=final_data)
        self.final_data = final_data
        #raw values can be very large, so we delete it in this one case
        #index = pd.MultiIndex.from_product([GeoMapper.get_cfg_gaus(), self.all_shapes.active_dates_index], names=[GeoMapper.cfg_geography, 'weather_datetime'])
        #self.final_data = self.make_flat_load_shape(index)
        del self.timeseries

    def add_timeshift_type(self):
        """Later these shapes will need a level called timeshift type, and it is faster to add it now if it doesn't already have it"""
        if 'timeshift_type' not in self.values.index.names:
            self.values['timeshift_type'] = 2 # index two is the native demand shape
            self.values = self.values.set_index('timeshift_type', append=True).swaplevel('timeshift_type', 'weather_datetime').sort_index()

    def normalize(self, df):
        group_to_normalize = [n for n in df.index.names if n!='weather_datetime']
        # here is a special case where I have p_min and p_max in my dispatch constraints and these should not be normalized
        if 'dispatch_constraint' in group_to_normalize:
            # this first normailization does what we need for hydro pmin and pmax, which is a special case of normalization
            combined_map_df = util.DfOper.mult((self.map_df_tz, self.map_df_primary))
            normalization_factors = combined_map_df.groupby(level=GeoMapper.cfg_geography).sum()
            norm_df = util.DfOper.divi((df, normalization_factors))

            temp = norm_df.groupby(level=group_to_normalize).transform(lambda x: x / x.sum())*self.all_shapes.num_active_years
            indexer = util.level_specific_indexer(temp, 'dispatch_constraint', [['p_min', 'p_max']])
            temp.loc[indexer, :] = norm_df.loc[indexer, :]

            norm_df = temp
        else:
            norm_df = df.groupby(level=group_to_normalize).transform(lambda x: x / x.sum())*self.all_shapes.num_active_years

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
        geography_map_key = self.geography_map_key or GeoMapper.cfg_default_geography_map_key

        # create dataframe with map from one geography to another
        # we always want to normalize as a total here because we will re-sum over time zone later
        self.map_df_tz = GeoMapper.get_instance().map_df(self.geography, 'time zone', normalize_as='total', map_key=geography_map_key)

        mapped_data = util.DfOper.mult([df, self.map_df_tz])
        mapped_data = mapped_data.swaplevel('weather_datetime', -1)
        return mapped_data.sort_index()

    def geomap_to_primary_geography(self, df):
        """ maps the dataframe to primary geography
        """
        geography_map_key = self.geography_map_key or GeoMapper.cfg_default_geography_map_key

        self.map_df_primary = GeoMapper.get_instance().map_df(self.geography, GeoMapper.cfg_geography, normalize_as=self.input_type, map_key=geography_map_key)
        mapped_data = util.DfOper.mult((df, self.map_df_primary), fill_value=None)

        if self.geography!=GeoMapper.cfg_geography and self.geography!='time zone':
            mapped_data = util.remove_df_levels(mapped_data, self.geography)
        mapped_data = mapped_data.swaplevel('weather_datetime', -1)

        mapped_data.sort_index()
        return mapped_data

    def sum_over_time_zone(self, df):
        if GeoMapper.cfg_geography=='time zone':
            return df

        levels = [ind for ind in df.index.names if ind!='time zone']
        df_no_tz = df.groupby(level=levels).sum()
        return df_no_tz.sort_index()

    def standardize_time_across_timezones(self, df):
        tz = self.all_shapes.cfg_outputs_timezone
        offset = (tz.utcoffset(DT.datetime(2015, 1, 1)) + tz.dst(DT.datetime(2015, 1, 1))).total_seconds()/60.
        self.final_dates_index = pd.date_range(min(self.all_shapes.active_dates_index), periods=len(self.all_shapes.active_dates_index), freq='H', tz=pytz.FixedOffset(offset))

        standardize_df = util.reindex_df_level_with_new_elements(df.copy(), 'weather_datetime', self.final_dates_index)

        levels = [n for n in df.index.names if n!='weather_datetime']
        standardize_df = standardize_df.groupby(level=levels).fillna(method='bfill').fillna(method='ffill')

        return standardize_df

    def localize_shapes(self, df):
        """ Step through time zone and put each profile maped to time zone in that time zone
        """
        local_df = []
        for tz, group in df.groupby(level='time zone'):
            # get the time zone name and figure out the offset from UTC
            tz = pytz.timezone(self.time_zone or format_timezone_str(tz))
            _dt = DT.datetime(2015, 1, 1)
            offset = (tz.utcoffset(_dt) + tz.dst(_dt)).total_seconds()/60.
            # localize and then convert to dispatch_outputs_timezone
            df2 = group.tz_localize(pytz.FixedOffset(offset), level='weather_datetime')
            local_df.append(df2)

        tz = self.all_shapes.cfg_outputs_timezone
        offset = (tz.utcoffset(DT.datetime(2015, 1, 1)) + tz.dst(DT.datetime(2015, 1, 1))).total_seconds()/60.
        local_df = pd.concat(local_df).tz_convert(pytz.FixedOffset(offset), level='weather_datetime')
        return local_df.sort_index()


    def make_flat_load_shape(self, index, column='value', num_active_years=None):
        assert 'weather_datetime' in index.names
        flat_shape = util.empty_df(fill_value=1., index=index, columns=[column])
        group_to_normalize = [n for n in flat_shape.index.names if n!='weather_datetime']
        num_active_years =  self.all_shapes.num_active_years if num_active_years is None else num_active_years
        flat_shape = flat_shape.groupby(level=group_to_normalize).transform(lambda x: x / x.sum())*num_active_years
        return flat_shape

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
        hr_delay = 0 if hr_delay is None else hr_delay
        hr_advance = 0 if hr_advance is None else hr_advance

        native_slice = util.df_slice(shape_df, elements=2, levels='timeshift_type')
        native_slice_stacked = pd.concat([native_slice]*3, keys=[1,2,3], names=['timeshift_type'])

        pflex_stacked = pd.concat([percent_flexible]*3, keys=[1,2,3], names=['timeshift_type'])

        timeshift_levels = sorted(list(util.get_elements_from_level(shape_df, 'timeshift_type')))
        if timeshift_levels==[1, 2, 3]:
            # here, we have flexible load profiles already specified by the user
            names = shape_df.index.names
            full_load = shape_df.squeeze().unstack('timeshift_type')
            group_by_names = [n for n in full_load.index.names if n != 'weather_datetime']
            full_load = full_load.groupby(level=group_by_names).apply(Shape.ensure_feasible_flexible_load)
            full_load = full_load.stack('timeshift_type').reorder_levels(names).sort_index().to_frame()
            full_load.columns = ['value']
        elif timeshift_levels==[2]:
            # positive hours is a shift forward, negative hours a shift back
            shift = lambda df, hr: df.shift(hr).ffill().fillna(value=0)

            def fix_first_point(df, hr):
                df.iloc[0] += native_slice.iloc[:hr].sum().sum()
                return df

            non_weather = [n for n in native_slice.index.names if n!='weather_datetime']

            delay_load = native_slice.groupby(level=non_weather).apply(shift, hr=hr_delay)
            advance_load = native_slice.groupby(level=non_weather).apply(shift, hr=-hr_advance)
            advance_load = advance_load.groupby(level=non_weather).transform(fix_first_point, hr=hr_advance)

            full_load = pd.concat([delay_load, native_slice, advance_load], keys=[1,2,3], names=['timeshift_type'])
        else:
            raise ValueError("elements in the level timeshift_type are not recognized")

        return util.DfOper.add((util.DfOper.mult((full_load, pflex_stacked), collapsible=False),
                                util.DfOper.mult((native_slice_stacked, 1-pflex_stacked), collapsible=False)))


