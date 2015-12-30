# -*- coding: utf-8 -*-
"""
Created on Mon Oct 05 14:45:48 2015

@author: ryan
"""

#import config as cfg
from config import cfg
#import config
import datamapfunctions as dmf
import util
import pandas as pd
import pytz
import datetime as DT
import time
import numpy as np

#http://stackoverflow.com/questions/27491988/canonical-offset-from-utc-using-pytz

class Shapes(object):
    def __init__(self):
        self.data = {}
        self.sql_id_table = 'Shapes'
        self.active_shape_ids = []
        self.start_date = None
        self.end_date = None

    def create_empty_shapes(self):
        for id in util.sql_read_table(self.sql_id_table, column_names='id', return_unique=True, return_iterable=True):
            self.data[id] = Shape(id)

    def activate_shape(self, id):
        if id in self.data:
            self.active_shape_ids.append(id)

    def initiate_active_shapes(self):
        for id in self.active_shape_ids:
            shape = self.data[id]
            
            if hasattr(shape, 'raw_values'):
                return
            
            shape.read_timeseries_data()
            
            if shape.shape_type=='weather date':
                date_position = util.position_in_index(shape.raw_values, 'weather_datetime')
                shape.start_date = DT.datetime.strptime(shape.raw_values.index.levels[date_position][0], '%m/%d/%y %H:%M')
                shape.end_date = DT.datetime.strptime(shape.raw_values.index.levels[date_position][-1], '%m/%d/%y %H:%M')
    
                self.start_date = shape.start_date if self.start_date is None else max(shape.start_date, self.start_date)
                self.end_date = shape.end_date if self.end_date is None else min(shape.end_date, self.end_date)
        
        self.set_active_dates()

    def set_active_dates(self):
        if self.start_date is self.end_date is None:
            self.start_date = DT.datetime(int(cfg.cfgfile.get('case', 'current_year')), 1, 1)
            self.end_date = DT.datetime(int(cfg.cfgfile.get('case', 'current_year')), 12, 31)

#        self.active_dates_index = pd.date_range(self.start_date - DT.timedelta(1), self.end_date + DT.timedelta(1), freq='H')
        self.active_dates_index = pd.date_range(self.start_date, self.end_date, freq='H')
        self.time_slice_elements = self.create_time_slice_elements(self.active_dates_index)

    def process_active_shapes(self):
        #run the weather date shapes first because they inform the daterange for dispatch
        for id in self.active_shape_ids:
            self.data[id].process_shape(self.active_dates_index, self.time_slice_elements)
    
    @staticmethod
    def create_time_slice_elements(active_dates_index):
        business_days = pd.bdate_range(active_dates_index[0].date(), active_dates_index[-1].date())
        biz_map = {v: k for k, v in util.sql_read_table('DayType', column_names='*', return_iterable=False)}
        
        time_slice_elements = {}
        for ti in cfg.time_slice_col:
            if ti=='day_type_id':
                time_slice_elements['day_type_id'] = [biz_map['workday'] if s.date() in business_days else biz_map['non-workday'] for s in active_dates_index]
            else:
                time_slice_elements[ti] = getattr(active_dates_index, ti)
        time_slice_elements['hour24'] = time_slice_elements['hour'] + 1
        return time_slice_elements

class Shape(dmf.DataMapFunctions):
    def __init__(self, id=None):
        if id is not None:
            self.id = id
            self.sql_id_table = 'Shapes'
            self.sql_data_table = 'ShapesData'
            for col, att in util.object_att_from_table(self.sql_id_table, id):
                setattr(self, col, att)
            # creates the index_levels dictionary
            dmf.DataMapFunctions.__init__(self)

    def create_empty_shape_data(self):
        self._active_time_keys = [ind for ind in self.raw_values.index.names if ind in cfg.time_slice_col]
        self._active_time_dict = dict([(ind, loc) for loc, ind in enumerate(self.raw_values.index.names) if ind in cfg.time_slice_col])
        
        self._non_time_keys = [ind for ind in self.raw_values.index.names if ind not in self._active_time_keys]
        self.non_time_levels = [l for l, n in zip(self.raw_values.index.levels, self.raw_values.index.names) if n in self._non_time_keys]
        self._non_time_dict = dict([(ind, loc) for loc, ind in enumerate(self.raw_values.index.names) if ind in self._non_time_keys])
        
        self.final_index = pd.MultiIndex.from_product(self.non_time_levels+[self.active_dates_index], names=self._non_time_keys+['weather_datetime'])
        data = pd.DataFrame(index=self.final_index, columns=['value'])

        for ti in self._active_time_keys:
            #hour is given as 1-24 not 0-23
            if ti=='hour' and min(self.raw_values.index.levels[self._active_time_dict['hour']])==1 and max(self.raw_values.index.levels[self._active_time_dict['hour']])==24:
                # the minimum value is 1 and max value is 24
                data[ti] = self.time_slice_elements['hour24']
            else:
                data[ti] = self.time_slice_elements[ti]
        
        data.reset_index(inplace=True)
        data.set_index(self._non_time_keys+self._active_time_keys+['weather_datetime'], inplace=True)
        data.sort(inplace=True)
        return data

    def normalize(self):
        group_to_normalize = [n for n in self.values.index.names if n!='weather_datetime']
        self.values = self.values.groupby(level=group_to_normalize).transform(lambda x: x / (x.sum()))*self.num_active_years

    def process_shape(self, active_dates_index=None, time_slice_elements=None):
        self.num_active_years = len(active_dates_index)/8766.
        if active_dates_index is not None:
            self.active_dates_index = active_dates_index

        if active_dates_index is None:
            raise ValueError('processing a shape requires an active date index')

        self.time_slice_elements = Shapes.create_time_slice_elements(active_dates_index) if time_slice_elements is None else time_slice_elements
        
        if self.shape_type=='weather date':
            self.convert_index_to_datetime('raw_values', 'weather_datetime')
            # Reindex with a day on either side so that data is preserved when it is shifted for time zones
            self.values = util.reindex_df_level_with_new_elements(self.raw_values, 'weather_datetime', active_dates_index) # this step is slow, consider replacing
#            self.values = pd.merge(self.raw_values.reset_index(), 
#                                   pd.DataFrame(self.active_dates_index, columns=['weather_datetime']), 
#                                   how='right').set_index(self.raw_values.index.names)
            if self.values.isnull().values.any():
                raise ValueError('Weather data did not give full coverage of the active dates')

        elif self.shape_type=='time slice':
            self.values = self.create_empty_shape_data()
            
            for ind, value in self.raw_values.iterrows():
                indexer = tuple([ind[self._non_time_dict[e]] for e in self._non_time_keys] +
                                [ind[self._active_time_dict[e]] for e in self._active_time_keys] +
                                [slice(None)])
                if self.shape_unit_type=='energy':
                    len_slice = len(self.values.loc[indexer])
                    self.values.loc[indexer] = value[0]/float(len_slice)*self.num_active_years
                elif self.shape_unit_type=='power':
                    self.values.loc[indexer] = value[0]
            
            if self.values.isnull().values.any():
                raise ValueError('Shape time slice data did not give full coverage of the active dates')
            # reindex to remove the helper columns
            self.values.index = self.values.index.droplevel(self._active_time_keys)
            self.values.sort()

        self.geomap_to_time_zone()
        self.localize_shapes()
        self.geomap_to_primary_geography()
        self.sum_over_time_zone()
        self.normalize()

    def geomap_to_time_zone(self, attr='values', inplace=True):
        """ maps a dataframe to another geography using relational GeographyMapdatabase table
        """
        if self.geography=='time zones':
            if inplace:
                return
            else:
                return getattr(self, attr)
        
        geography_map_key = cfg.cfgfile.get('case', 'default_geography_map_key') if not hasattr(self, 'geography_map_key') else self.geography_map_key
        
        subsection, supersection = 'time zones', self.geography
        # create dataframe with map from one geography to another
        map_df = cfg.geo.map_df(subsection, supersection, column=geography_map_key)
        map_df[:] = 1
        self.map_df = map_df

        mapped_data = util.DfOper.mult([getattr(self, attr), map_df])
        mapped_data = mapped_data.swaplevel('time zones', 1)
        mapped_data.sort(inplace=True)
        if inplace:
            setattr(self, attr, mapped_data)
        else:
            return mapped_data

    def geomap_to_primary_geography(self, attr='values', inplace=True, converted_geography=None):
        """This needs more testing for cases where the converted_geography is time zone or self.geography is time zone
        """
        converted_geography = cfg.cfgfile.get('case', 'primary_geography')
        geography_map_key = cfg.cfgfile.get('case', 'default_geography_map_key') if not hasattr(self, 'geography_map_key') else self.geography_map_key

        if self.geography==converted_geography:
            if inplace:
                return
            else:
                return getattr(self, attr)

        # we should add dispatch region as another subsection to ensure proper geomap to dispatch region after
        subsection = 'time zones' if self.geography=='time zones' else ['time zones', self.geography]
        supersection = converted_geography
        
        map_df = cfg.geo.map_df(subsection, supersection, column=geography_map_key)
        mapped_data = util.DfOper.mult((getattr(self, attr), map_df), fill_value=None)
        levels = [ind for ind in mapped_data.index.names if (ind!=self.geography and self.geography!='time zones')]
        mapped_data = mapped_data.groupby(level=levels).sum()
        mapped_data.sort(inplace=True)

        if inplace:
            setattr(self, attr, mapped_data)
        else:
            return mapped_data

    def sum_over_time_zone(self, attr='values', inplace=True):
        converted_geography = cfg.cfgfile.get('case', 'primary_geography')
        
        if converted_geography=='time zones':
            if inplace:
                return
            else:
                return getattr(self, attr)
        
        levels = [ind for ind in getattr(self, attr).index.names if ind!='time zones']
        df = getattr(self, attr).groupby(level=levels).sum()
        df.sort(inplace=True)

        if inplace:
            setattr(self, attr, df)
        else:
            return df

    def localize_shapes(self, attr='values', inplace=True):
        """ Step through time zones and put each profile maped to time zone in that time zone
        """
        new_df = []
        for tz_id, group in getattr(self, attr).groupby(level='time zones'):
            # get the time zone name and figure out the offset from UTC
            tz = pytz.timezone(cfg.geo.geography_names[tz_id])
            _dt = DT.datetime(2015, 1, 1)
            offset = (tz.utcoffset(_dt) + tz.dst(_dt)).total_seconds()/60.
            df = group.tz_localize(pytz.FixedOffset(offset), level='weather_datetime')
            
#            offset = (tz.utcoffset(_dt) + tz.dst(_dt)).total_seconds()/3600.
#            # localize profile in UTC, then shift the profile, this is the easiest way to bring in a profile in standard time
#            df = group.tz_localize('UTC', level='weather_datetime')
#            df = df.shift(periods=int(-offset))
#            if offset%1:
#                raise ValueError('time zones with an offset of '+str(offset)+' not implemented')
#                #this general approach should work, but we need to reset the index first
#                df.resample(rule='15min').interpolate().resample(rule='H', how='first')
            # convert to local time
#            df = df.tz_convert(tz, level='weather_datetime')
            new_df.append(df)
        if inplace:
            setattr(self, attr, pd.concat(new_df))
        else:
            return pd.concat(new_df)

    def convert_index_to_datetime(self, dataframe_name, index_name='weather_datetime'):
        df = getattr(self, dataframe_name)
        names = df.index.names
        df.reset_index(inplace=True)
        df['weather_datetime'] = cfg.date_lookup.lookup(self.raw_values['weather_datetime'])
        df['weather_datetime'].freq = 'H'
        df.set_index(names, inplace=True)
        df.sort_index(inplace=True)


#######################
#######################
shapes = Shapes()
#######################


#t = util.time_stamp(t)
#test3 = Shape(id=3)
#t = util.time_stamp(t)
#test4 = Shape(id=4)
#t = util.time_stamp(t)
#self = test1



#pd.DatetimeIndex(start='2011-03-13 00:00:00', freq='H', periods=24, is_dst=False).tz_localize(cfg.geo.geography_names[tz_id], ambiguous='infer')
#test = self.values.groupby(level='time zones').apply(implement_time_zones)


##slow but right
#new_df = []
#for tz_id, group in self.values.groupby(level='time zones'):
#    names = group.index.names
#    group = group.tz_localize('UTC', level='weather_datetime')
#    group.reset_index(inplace=True)
#    group.set_index('weather_datetime', inplace=True)
#    group = group.shift(periods=4, freq='H') #freq makes this really slow
#    group = group.tz_convert(cfg.geo.geography_names[tz_id], level='weather_datetime')
#    group.reset_index(inplace=True)
#    group.set_index(names)
#    new_df.append(group)
#new_df = pd.concat(new_df)


#561408

#pytz.timezone(cfg.geo.geography_names[tz_id]) - pytz.timezone('UTC')
#
#temp = pd.DatetimeIndex(start='2011-03-13 00:00:00', freq='H', periods=24)
#eastern = pytz.timezone('US/Eastern')
#temp2 = pd.DatetimeIndex([eastern.localize(t, is_dst=False) for t in temp])
#
#new_df = []
#for tz_id, group in self.values.groupby(level='time zones'):
#    if tz_id==167:
#        continue
#    print cfg.geo.geography_names[tz_id]
#    date_position = util.position_in_index(self.values, 'weather_datetime')
#    hourly_dst = np.zeros(len(group), dtype=int)
#    
#    group.reset_index(inplace=True)
#    group.set_index('weather_datetime', inplace=True)
#    
#    try:
#        group.tz_localize(cfg.geo.geography_names[tz_id], ambiguous='infer', level='weather_datetime')
#        group.tz_localize(cfg.geo.geography_names[tz_id], ambiguous=hourly_dst, level='weather_datetime')
#        
#        group = group.tz_localize(pytz.timezone(cfg.geo.geography_names[tz_id]), ambiguous=hourly_dst, level='weather_datetime')
#        new_df.append(group)
#    except:
#        print 'error'
##    group = group.tz_convert(pytz.timezone('UTC'), level='weather_datetime')
#new_df = pd.concat(new_df)
#
#
#rng_hourly = pd.DatetimeIndex(['11/06/2011 00:00', '11/06/2011 01:00','11/06/2011 01:00', '11/06/2011 02:00','11/06/2011 03:00'])

#test_pac = pd.DataFrame(range(24), index=pd.date_range('1/1/2011', periods=24, freq='H', tz=pytz.timezone('US/Pacific')))
#test_chat = pd.DataFrame(range(24), index=pd.date_range('1/1/2011', periods=24, freq='H', tz=pytz.timezone('Pacific/Chatham')))

#temp_az = pd.DataFrame(range(24), index=pd.DatetimeIndex(start='2011-03-12 20:00:00', freq='H', periods=24))
#temp_pac = pd.DataFrame(range(24), index=pd.DatetimeIndex(start='2011-03-12 20:00:00', freq='H', periods=24))
#
#temp_az.tz_localize(pytz.FixedOffset(-5*60))
#
#temp_az = temp_az.tz_localize('UTC')
#temp_pac = temp_pac.tz_localize('UTC')
#
#temp_pac.tz_localize(pytz.timezone('US/Pacific'))
#
#az = temp_az.tz_convert(pytz.timezone('US/Arizona'))
#pac = temp_az.tz_convert(pytz.timezone('US/Pacific'))


#if offset%1:


#pytz.timezone('UTC')
#
#test_chat.tz_convert('UTC').resample(rule='15min').interpolate().resample(rule='H', how='first')
#
#test_pac.tz_convert('UTC').resample(rule='15min').interpolate().resample(rule='H', how='first')
#
##test_chat.tz_convert('UTC').resample(rule='15min').interpolate().resample(rule='H')
#
#test_chat.tz_convert('UTC').resample(rule='H', how='mean')
#
#added = test_pac+test_chat

