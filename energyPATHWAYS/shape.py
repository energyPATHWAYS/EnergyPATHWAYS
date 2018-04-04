# -*- coding: utf-8 -*-
"""
Created on Mon Oct 05 14:45:48 2015

@author: ryan
"""

import config as cfg
import datamapfunctions as dmf
import util
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
import helper_multiprocess
import pdb
import numpy as np

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

def num_active_years(active_dates_index):
    unique_years = sorted(list(set(active_dates_index.year)))
    year_counts = [sum(active_dates_index.year==y) for y in unique_years]
    years = sum([yc/(8784. if is_leap_year(y) else 8760.) for y, yc in zip(unique_years, year_counts)])
    return min(1., years) # we normalize up to one year
    
class Shapes(object):
    def __init__(self):
        self.data = {}
        self.sql_id_table = 'Shapes'
        self.active_shape_ids = []
        self.start_date = None
        self.end_date = None
        self._geography_check = None
        self._timespan_check = None
        self._version = version

    def create_empty_shapes(self):
        """ This should be called first as it creates a record of all of the shapes that are in the database."""
        for id in util.sql_read_table(self.sql_id_table, column_names='id', return_unique=True, return_iterable=True):
            self.data[id] = Shape(id)
            self.active_shape_ids.append(id)

    def initiate_active_shapes(self):
        logging.info(' reading data for:')

        if cfg.cfgfile.get('case', 'parallel_process').lower() == 'true':
            shapes = helper_multiprocess.safe_pool(helper_multiprocess.shapes_populate, self.data.values())
            self.data = dict(zip(self.data.keys(), shapes))
        else:
            for id in self.active_shape_ids:
                shape = self.data[id]
                logging.info('    shape: ' + shape.name)
                if hasattr(shape, 'raw_values'):
                    return
                shape.read_timeseries_data()

        for id in self.active_shape_ids:
            shape = self.data[id]
            if shape.shape_type=='weather date':
                shape.convert_index_to_datetime('raw_values', 'weather_datetime')
                date_position = util.position_in_index(shape.raw_values, 'weather_datetime')
                
                shape.start_date, shape.end_date = min(shape.raw_values.index.levels[date_position]), max(shape.raw_values.index.levels[date_position])
                
                self.start_date = shape.start_date if self.start_date is None else max(shape.start_date, self.start_date)
                self.end_date = shape.end_date if self.end_date is None else min(shape.end_date, self.end_date)
        self.set_active_dates()

    def set_active_dates(self):
        requested_shape_start_date = cfg.shape_start_date
        if requested_shape_start_date:
            # self.start_date and self.end_date could be None here if we encountered no 'weather date' shapes
            # in initiate_active_shapes().
            if (self.start_date is None or requested_shape_start_date >= self.start_date) and\
               (self.end_date is None or requested_shape_start_date <= self.end_date):
                self.start_date = requested_shape_start_date
                shape_years = cfg.shape_years or 1
                # Need to subtract an hour because all timestamps are hour-beginning.
                requested_shape_end_date = self.start_date + relativedelta(years=shape_years, hours=-1)
                # We only need to check the "right hand" boundary here, because: A) we already confirmed that the
                # start_date was within the allowable range, and B) config.py requires shape_years to be positive.
                # In other words, there's no way at this point that requested_shape_end_date could be < self.start_date
                if self.end_date is None or requested_shape_end_date <= self.end_date:
                    self.end_date = requested_shape_end_date
                else:
                    raise ValueError("The requested shape_start_date from your config plus the requested shape_years "
                                     "give an end date of {}, which is after the end date of at least one of "
                                     "your shapes.".format(requested_shape_end_date))
            else:
                raise ValueError("The requested shape_start_date from your config ({}) is outside the range of dates "
                                 "available in your shapes.".format(requested_shape_start_date))

        # This is a last resort; it's unlikely that we could get here without either:
        # A) encountering at least one weather_datetime shape in initiate_active_shapes(), or
        # B) having a shape_start_date requested in the config
        # but if both of those have happened, we set the date range to the case's current year
        if self.start_date is self.end_date is None:
            self.start_date = DT.datetime(int(cfg.cfgfile.get('case', 'current_year')), 1, 1)
            self.end_date = DT.datetime(int(cfg.cfgfile.get('case', 'current_year')), 12, 31, 23)

        logging.debug("shape_start_date: {}, shape_years: {}, start_date: {}, end_date: {}".format(
            cfg.shape_start_date, cfg.shape_years, self.start_date, self.end_date))

        self.active_dates_index = pd.date_range(self.start_date, self.end_date, freq='H')
        self.time_slice_elements = self.create_time_slice_elements(self.active_dates_index)
        
        for id in self.active_shape_ids:
            self.data[id].active_dates_index = self.active_dates_index
            self.data[id].time_slice_elements = self.time_slice_elements

    def process_active_shapes(self):
        #run the weather date shapes first because they inform the daterange for dispatch
        logging.info(' mapping data for:')
        
        if cfg.cfgfile.get('case','parallel_process').lower() == 'true':
            shapes = helper_multiprocess.safe_pool(helper_multiprocess.process_shapes, self.data.values())
            self.data = dict(zip(self.data.keys(), shapes))
        else:
            for id in self.active_shape_ids:
                self.data[id].process_shape()
        
        dispatch_outputs_timezone_id = int(cfg.cfgfile.get('case', 'dispatch_outputs_timezone_id'))
        self.dispatch_outputs_timezone = pytz.timezone(cfg.geo.timezone_names[dispatch_outputs_timezone_id])
        self.active_dates_index = pd.date_range(self.active_dates_index[0], periods=len(self.active_dates_index), freq='H', tz=self.dispatch_outputs_timezone)
        self.num_active_years = num_active_years(self.active_dates_index)
        self._geography_check = (cfg.demand_primary_geography_id, cfg.supply_primary_geography_id, tuple(sorted(cfg.primary_subset_id)), tuple(cfg.breakout_geography_id))
        self._timespan_check = (cfg.shape_start_date, cfg.shape_years)
    
    @staticmethod
    def create_time_slice_elements(active_dates_index):
        business_days = pd.bdate_range(active_dates_index[0].date(), active_dates_index[-1].date())
        biz_map = {v: k for k, v in util.sql_read_table('DayType', column_names='*', return_iterable=False)}
        
        time_slice_elements = {}
        for ti in cfg.time_slice_col:
            if ti=='day_type':
                time_slice_elements['day_type'] = np.array([biz_map['workday'] if s.date() in business_days else biz_map['non-workday'] for s in active_dates_index], dtype=int)
            else:
                time_slice_elements[ti] = getattr(active_dates_index, ti)
        time_slice_elements['hour24'] = time_slice_elements['hour'] + 1
        return time_slice_elements

    def make_flat_load_shape(self, index, column='value'):
        assert 'weather_datetime' in index.names
        flat_shape = util.empty_df(fill_value=1., index=index, columns=[column])
        group_to_normalize = [n for n in flat_shape.index.names if n!='weather_datetime']
        flat_shape = flat_shape.groupby(level=group_to_normalize).transform(lambda x: x / x.sum())*self.num_active_years
        return flat_shape

class Shape(dmf.DataMapFunctions):    
    def __init__(self, id):
        self.id = id
        self.sql_id_table = 'Shapes'
        self.sql_data_table = 'ShapesData'
        for col, att in util.object_att_from_table(self.sql_id_table, id):
            setattr(self, col, att)
        dmf.DataMapFunctions.__init__(self, data_id_key='parent_id')
        # needed for parallel process
        self.workingdir = cfg.workingdir
        self.cfgfile_name = cfg.cfgfile_name
        self.log_name = cfg.log_name
        self.primary_geography = cfg.demand_primary_geography if self.supply_or_demand_side == 'd' else cfg.supply_primary_geography

    def create_empty_shape_data(self):
        self._active_time_keys = [ind for ind in self.raw_values.index.names if ind in cfg.time_slice_col]
        self._active_time_dict = dict([(ind, loc) for loc, ind in enumerate(self.raw_values.index.names) if ind in cfg.time_slice_col])
        
        self._non_time_keys = [ind for ind in self.raw_values.index.names if ind not in self._active_time_keys]
        self._non_time_dict = dict([(ind, loc) for loc, ind in enumerate(self.raw_values.index.names) if ind in self._non_time_keys])
        
        data = pd.DataFrame(index=pd.Index(self.active_dates_index, name='weather_datetime'), columns=['value'])

        for ti in self._active_time_keys:
            #hour is given as 1-24 not 0-23
            if ti=='hour' and min(self.raw_values.index.levels[self._active_time_dict['hour']])==1 and max(self.raw_values.index.levels[self._active_time_dict['hour']])==24:
                # the minimum value is 1 and max value is 24
                data[ti] = self.time_slice_elements['hour24']
            else:
                data[ti] = self.time_slice_elements[ti]
        
        non_time_levels = [list(l) for l, n in zip(self.raw_values.index.levels, self.raw_values.index.names) if n in self._non_time_keys]
        # this next step could be done outside of a for loop, but I'm not able to get the Pandas syntax to take
        for name, level in zip(self._non_time_keys, non_time_levels):
            data = pd.concat([data]*len(level), keys=level, names=[name])  
        try:
            data.reset_index(inplace=True)
        except:
            pdb.set_trace()
        data.set_index(self._non_time_keys+self._active_time_keys+['weather_datetime'], inplace=True)
        data.sort(inplace=True)
        return data

    def process_shape(self):
        logging.info('    shape: ' + self.name)
        self.num_active_years = num_active_years(self.active_dates_index)
        
        if self.shape_type=='weather date':
            self.values = util.reindex_df_level_with_new_elements(self.raw_values, 'weather_datetime', self.active_dates_index)
            self.values  = self.values.replace(np.nan,0)# this step is slow, consider replacing
            if self.values.isnull().values.any():
                raise ValueError('Weather data for shape {} did not give full coverage of the active dates'.format(self.name))

        elif self.shape_type=='time slice':
            self.values = self.create_empty_shape_data()
            
            non_time_elements_in_levels = [list(util.get_elements_from_level(self.values, e)) for e in self._non_time_keys]
            time_elements_in_levels = [list(util.get_elements_from_level(self.values, e)) for e in self._active_time_keys]
            
            for ind, value in self.raw_values.iterrows():
                non_time_portion = [ind[self._non_time_dict[e]] for e in self._non_time_keys]
                time_portion = [ind[self._active_time_dict[e]] for e in self._active_time_keys]
                if not np.all([s in l for s, l in zip(non_time_portion+time_portion, non_time_elements_in_levels+time_elements_in_levels)]):
                    continue
                
                indexer = tuple(non_time_portion + time_portion + [slice(None)])
                                
                if self.shape_unit_type=='energy':
                    len_slice = len(self.values.loc[indexer])
                    self.values.loc[indexer] = value[0]/float(len_slice)*self.num_active_years
                elif self.shape_unit_type=='power':
                    self.values.loc[indexer] = value[0]
            
            if self.values.isnull().values.any():
                raise ValueError('Shape time slice data did not give full coverage of the active dates')
            # reindex to remove the helper columns
            self.values.index = self.values.index.droplevel(self._active_time_keys)

        self.values = cfg.geo.filter_extra_geos_from_df(self.values.swaplevel('weather_datetime', -1).sort())
        self.geomap_to_time_zone()
        self.localize_shapes()
        self.standardize_time_across_timezones()
        self.geomap_to_primary_geography()
        self.sum_over_time_zone()
        self.normalize()
        # self.add_timeshift_type()
        # raw values can be very large, so we delete it in this one case
        del self.raw_values

    def add_timeshift_type(self):
        """Later these shapes will need a level called timeshift type, and it is faster to add it now if it doesn't already have it"""
        if 'timeshift_type' not in self.values.index.names:
            self.values['timeshift_type'] = 2 # index two is the native demand shape
            self.values = self.values.set_index('timeshift_type', append=True).swaplevel('timeshift_type', 'weather_datetime').sort_index()

    def normalize(self):
        group_to_normalize = [n for n in self.values.index.names if n!='weather_datetime']
        # here is a special case where I have p_min and p_max in my dispatch constraints and these should not be normalized
        if 'dispatch_constraint' in group_to_normalize:
            # this first normailization does what we need for hydro pmin and pmax, which is a special case of normalization
            combined_map_df = util.DfOper.mult((self.map_df_tz, self.map_df_primary))
            normalization_factors = combined_map_df.groupby(level=self.primary_geography).sum()
            self.values = util.DfOper.divi((self.values, normalization_factors))
            
            temp = self.values.groupby(level=group_to_normalize).transform(lambda x: x / x.sum())*self.num_active_years
            # TODO: 2, and 3 should not be hard coded here, they represent p_min and p_max
            indexer = util.level_specific_indexer(temp, 'dispatch_constraint', [[2,3]])
            temp.loc[indexer, :] = self.values.loc[indexer, :]
            
            self.values = temp
        else:
            self.values = self.values.groupby(level=group_to_normalize).transform(lambda x: x / x.sum())*self.num_active_years        

    def geomap_to_time_zone(self, attr='values', inplace=True):
        """ maps a dataframe to another geography using relational GeographyMapdatabase table
        """
        geography_map_key = cfg.cfgfile.get('case', 'default_geography_map_key') if not hasattr(self, 'geography_map_key') else self.geography_map_key
        
        # create dataframe with map from one geography to another
        # we always want to normalize as a total here because we will re-sum over time zone later
        self.map_df_tz = cfg.geo.map_df(self.geography, 'time zone', normalize_as='total', map_key=geography_map_key)

        mapped_data = util.DfOper.mult([getattr(self, attr), self.map_df_tz])
        mapped_data = mapped_data.swaplevel('weather_datetime', -1)
        if inplace:
            setattr(self, attr, mapped_data.sort())
        else:
            return mapped_data.sort()

    def geomap_to_primary_geography(self, attr='values', inplace=True):
        """ maps the dataframe to primary geography
        """
        geography_map_key = cfg.cfgfile.get('case', 'default_geography_map_key') if not hasattr(self, 'geography_map_key') else self.geography_map_key
        
        self.map_df_primary = cfg.geo.map_df(self.geography, self.primary_geography, normalize_as=self.input_type, map_key=geography_map_key)
        mapped_data = util.DfOper.mult((getattr(self, attr), self.map_df_primary), fill_value=None)
        if self.geography!=self.primary_geography and self.geography!='time zone':
            mapped_data = util.remove_df_levels(mapped_data, self.geography)
        mapped_data = mapped_data.swaplevel('weather_datetime', -1)

        if inplace:
            setattr(self, attr, mapped_data.sort())
        else:
            return mapped_data.sort()

    def sum_over_time_zone(self, attr='values', inplace=True):
        converted_geography = self.primary_geography
        
        if converted_geography=='time zone':
            if inplace:
                return
            else:
                return getattr(self, attr)
                
        levels = [ind for ind in getattr(self, attr).index.names if ind!='time zone']
        df = getattr(self, attr).groupby(level=levels).sum()
        df.sort(inplace=True)

        if inplace:
            setattr(self, attr, df)
        else:
            return df

    def standardize_time_across_timezones(self, attr='values', inplace=True):
        self.final_dates_index = pd.date_range(self.active_dates_index[0], periods=len(self.active_dates_index), freq='H', tz=self.dispatch_outputs_timezone)
        df = util.reindex_df_level_with_new_elements(getattr(self, attr).copy(), 'weather_datetime', self.final_dates_index)
        levels = [n for n in self.values.index.names if n!='weather_datetime']
        df = df.groupby(level=levels).fillna(method='bfill').fillna(method='ffill')
        
        if inplace:
            setattr(self, attr, df)
        else:
            return df

    def localize_shapes(self, attr='values', inplace=True):
        """ Step through time zone and put each profile maped to time zone in that time zone
        """
        dispatch_outputs_timezone_id = int(cfg.cfgfile.get('case', 'dispatch_outputs_timezone_id'))
        self.dispatch_outputs_timezone = pytz.timezone(cfg.geo.timezone_names[dispatch_outputs_timezone_id])
        new_df = []
        for tz_id, group in getattr(self, attr).groupby(level='time zone'):
            # get the time zone name and figure out the offset from UTC
            tz_id = tz_id if self.time_zone_id is None else self.time_zone_id
            tz = pytz.timezone(cfg.geo.timezone_names[tz_id])
            _dt = DT.datetime(2015, 1, 1)
            offset = (tz.utcoffset(_dt) + tz.dst(_dt)).total_seconds()/60.
            # localize and then convert to dispatch_outputs_timezone
            df = group.tz_localize(pytz.FixedOffset(offset), level='weather_datetime')
            new_df.append(df)
        
        if inplace:
            setattr(self, attr, pd.concat(new_df).tz_convert(self.dispatch_outputs_timezone, level='weather_datetime').sort_index())
        else:
            return pd.concat(new_df).tz_convert(self.dispatch_outputs_timezone, level='weather_datetime').sort_index()

    def convert_index_to_datetime(self, dataframe_name, index_name='weather_datetime'):
        df = getattr(self, dataframe_name)
        names = df.index.names
        df.reset_index(inplace=True)
        df['weather_datetime'] = cfg.date_lookup.lookup(self.raw_values['weather_datetime'])
        df['weather_datetime'].freq = 'H'
        df.set_index(names, inplace=True)
        df.sort_index(inplace=True)

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
    def produce_flexible_load(native_slice, percent_flexible=None, hr_delay=None, hr_advance=None):
        hr_delay = 0 if hr_delay is None else hr_delay
        hr_advance = 0 if hr_advance is None else hr_advance
        
        native_slice_stacked = pd.concat([native_slice]*3, keys=[1,2,3], names=['timeshift_type'])

        pflex_stacked = pd.concat([percent_flexible]*3, keys=[1,2,3], names=['timeshift_type'])

        non_weather = [n for n in native_slice.index.names if n!='weather_datetime']

        # positive hours is a shift forward, negative hours a shift back
        shift = lambda df, hr: df.shift(hr).ffill().fillna(value=0)
        delay_load = native_slice.groupby(level=non_weather).apply(shift, hr=hr_delay)

        def advance_load_function(df, hr):
            df_adv = df.shift(-hr).ffill().fillna(value=0)
            df_adv.iloc[0] += df.iloc[:hr].sum().sum()
            return df_adv
        advance_load = native_slice.groupby(level=non_weather).apply(advance_load_function, hr=hr_advance)

        full_load = pd.concat([delay_load, native_slice, advance_load], keys=[1,2,3], names=['timeshift_type'])
        
        return util.DfOper.add((util.DfOper.mult((full_load, pflex_stacked), collapsible=False),
                                util.DfOper.mult((native_slice_stacked, 1-pflex_stacked), collapsible=False)))

# electricity shapes
force_rerun_shapes = False
version = 5 #change this when you need to force users to rerun shapes
shapes = Shapes()

def init_shapes(pickle_shapes=True):
    global shapes
    filename = 'd_{}_s_{}_shapes.p'.format(cfg.demand_primary_geography, cfg.supply_primary_geography)
    if os.path.isfile(os.path.join(cfg.workingdir, filename)):
        logging.info('Loading shapes')
        with open(os.path.join(cfg.workingdir, filename), 'rb') as infile:
            shapes = pickle.load(infile)
    
    geography_check = (cfg.demand_primary_geography_id, cfg.supply_primary_geography_id, tuple(sorted(cfg.primary_subset_id)), tuple(cfg.breakout_geography_id))
    timespan_check = (cfg.shape_start_date, cfg.shape_years)
    if (shapes._version != version) or (shapes._geography_check != geography_check) or (shapes._timespan_check != timespan_check) or force_rerun_shapes:
        logging.info('Processing shapes')
        shapes.__init__()
        shapes.create_empty_shapes()
        shapes.initiate_active_shapes()
        shapes.process_active_shapes()
        
        if pickle_shapes:
            logging.info('Pickling shapes')
            filename = 'd_{}_s_{}_shapes.p'.format(cfg.demand_primary_geography, cfg.supply_primary_geography)
            with open(os.path.join(cfg.workingdir, filename), 'wb') as outfile:
                pickle.dump(shapes, outfile, pickle.HIGHEST_PROTOCOL)
