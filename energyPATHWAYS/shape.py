# -*- coding: utf-8 -*-
"""
Created on Mon Oct 05 14:45:48 2015

@author: ryan
"""

from config import cfg
import datamapfunctions as dmf
import util
import pandas as pd
import pytz
import datetime as DT
import time
import numpy as np
import cPickle as pickle
import os

#http://stackoverflow.com/questions/27491988/canonical-offset-from-utc-using-pytz

class Shapes(object):
    def __init__(self):
        self.data = {}
        self.sql_id_table = 'Shapes'
        self.active_shape_ids = []
        self.start_date = None
        self.end_date = None

    def create_empty_shapes(self):
        """ This should be called first as it creates a record of all of the shapes that are in the database."""
        for id in util.sql_read_table(self.sql_id_table, column_names='id', return_unique=True, return_iterable=True):
            self.data[id] = Shape(id)

    def activate_shape(self, id):
        if id not in self.active_shape_ids:
            if id not in self.data:
                raise ValueError("Shape with id "+str(id)+" not found")
            self.active_shape_ids.append(id)

    def initiate_active_shapes(self):
        print ' reading data for:'
        for id in self.active_shape_ids:
            shape = self.data[id]
            print '     shape: ' + shape.name
            
            if hasattr(shape, 'raw_values'):
                return
            
            shape.read_timeseries_data()
            
            if shape.shape_type=='weather date':
                shape.convert_index_to_datetime('raw_values', 'weather_datetime')
                date_position = util.position_in_index(shape.raw_values, 'weather_datetime')
                
                shape.start_date, shape.end_date = min(shape.raw_values.index.levels[date_position]), max(shape.raw_values.index.levels[date_position])
                
                self.start_date = shape.start_date if self.start_date is None else max(shape.start_date, self.start_date)
                self.end_date = shape.end_date if self.end_date is None else min(shape.end_date, self.end_date)
        
        self.set_active_dates()

    def set_active_dates(self):
        if self.start_date is self.end_date is None:
            self.start_date = DT.datetime(int(cfg.cfgfile.get('case', 'current_year')), 1, 1)
            self.end_date = DT.datetime(int(cfg.cfgfile.get('case', 'current_year')), 12, 31, 23)

#        self.active_dates_index = pd.date_range(self.start_date - DT.timedelta(1), self.end_date + DT.timedelta(1), freq='H')
        self.active_dates_index = pd.date_range(self.start_date, self.end_date, freq='H')
        self.time_slice_elements = self.create_time_slice_elements(self.active_dates_index)

    def process_active_shapes(self):
        #run the weather date shapes first because they inform the daterange for dispatch
        print ' mapping data for:'
        for id in self.active_shape_ids:
            shape = self.data[id]
            print '     shape: ' + shape.name
            shape.process_shape(self.active_dates_index, self.time_slice_elements)
        dispatch_outputs_timezone_id = int(cfg.cfgfile.get('case', 'dispatch_outputs_timezone_id'))
        self.dispatch_outputs_timezone = pytz.timezone(cfg.geo.timezone_names[dispatch_outputs_timezone_id])
        self.active_dates_index = pd.date_range(self.active_dates_index[0], periods=len(self.active_dates_index), freq='H', tz=self.dispatch_outputs_timezone)
    
    
    
    @staticmethod
    def create_time_slice_elements(active_dates_index):
        business_days = pd.bdate_range(active_dates_index[0].date(), active_dates_index[-1].date())
        biz_map = {v: k for k, v in util.sql_read_table('DayType', column_names='*', return_iterable=False)}
        
        time_slice_elements = {}
        for ti in cfg.time_slice_col:
            if ti=='day_type_id':
                time_slice_elements['day_type_id'] = np.array([biz_map['workday'] if s.date() in business_days else biz_map['non-workday'] for s in active_dates_index], dtype=int)
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
            dmf.DataMapFunctions.__init__(self, data_id_key='parent_id')

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
        
        data.reset_index(inplace=True)
        data.set_index(self._non_time_keys+self._active_time_keys+['weather_datetime'], inplace=True)
        data.sort(inplace=True)
        return data

    def process_shape(self, active_dates_index=None, time_slice_elements=None):
        self.num_active_years = len(active_dates_index)/8766.
        if active_dates_index is not None:
            self.active_dates_index = active_dates_index

        if active_dates_index is None:
            raise ValueError('processing a shape requires an active date index')

        self.time_slice_elements = Shapes.create_time_slice_elements(active_dates_index) if time_slice_elements is None else time_slice_elements
        
        if self.shape_type=='weather date':
            self.values = util.reindex_df_level_with_new_elements(self.raw_values, 'weather_datetime', active_dates_index) # this step is slow, consider replacing
            if self.values.isnull().values.any():
                raise ValueError('Weather data did not give full coverage of the active dates')

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
        
        self.values = self.values.swaplevel('weather_datetime', -1).sort_index()
        self.geomap_to_time_zone()
        self.localize_shapes()
        self.standardize_time_across_timezones()
        self.geomap_to_primary_geography()
        self.sum_over_time_zone()
        self.normalize()
        self.add_timeshift_type()

    def add_timeshift_type(self):
        """Later these shapes will need a level called timeshift type, and it is faster to add it now if it doesn't already have it"""
        if 'timeshift_type' not in self.values.index.names:
            self.values['timeshift_type'] = 2 # index two is the native demand shape
            self.values = self.values.set_index('timeshift_type', append=True).swaplevel('timeshift_type', 'weather_datetime').sort_index()

    def normalize(self):
        group_to_normalize = [n for n in self.values.index.names if n!='weather_datetime']
        # here is a special case where I have p_min and p_max in my dispatch constraints and these should not be normalized
        if 'dispatch_constraint' in group_to_normalize:
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
        if self.geography=='time zones':
            if inplace:
                return
            else:
                return getattr(self, attr)
        
        geography_map_key = cfg.cfgfile.get('case', 'default_geography_map_key') if not hasattr(self, 'geography_map_key') else self.geography_map_key
        
        subsection, supersection = 'time zones', self.geography
        # create dataframe with map from one geography to another
        map_df = cfg.geo.map_df(subsection, supersection, column=geography_map_key)
        self.map_df = map_df

        mapped_data = util.DfOper.mult([getattr(self, attr), map_df])
        mapped_data = mapped_data.swaplevel('weather_datetime', -1)
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
        mapped_data = mapped_data.swaplevel('weather_datetime', -1)
        mapped_data.sort(inplace=True)

        if inplace:
            setattr(self, attr, mapped_data)
        else:
            return mapped_data

    @staticmethod
    def geomap_to_dispatch_geography(df):
        """ maps a dataframe to another geography using relational GeographyMapdatabase table
        """
        converted_geography = cfg.cfgfile.get('case', 'primary_geography')
        dispatch_geography = cfg.cfgfile.get('case', 'dispatch_geography')
        if converted_geography==dispatch_geography:
            return df
        geography_map_key = cfg.cfgfile.get('case', 'default_geography_map_key')
        
        subsection, supersection = dispatch_geography, converted_geography
        # create dataframe with map from one geography to another
        map_df = cfg.geo.map_df(subsection, supersection, column=geography_map_key)
        mapped_data = util.DfOper.mult([df, map_df])
        
        levels = [ind for ind in mapped_data.index.names if ind!=converted_geography]
        mapped_data = mapped_data.groupby(level=levels).sum()
        mapped_data.sort(inplace=True)
        
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
        """ Step through time zones and put each profile maped to time zone in that time zone
        """
        dispatch_outputs_timezone_id = int(cfg.cfgfile.get('case', 'dispatch_outputs_timezone_id'))
        self.dispatch_outputs_timezone = pytz.timezone(cfg.geo.timezone_names[dispatch_outputs_timezone_id])
        new_df = []
        for tz_id, group in getattr(self, attr).groupby(level='time zones'):
            # get the time zone name and figure out the offset from UTC
            tz_id = tz_id if self.time_zone_id is None else self.time_zone_id
            tz = pytz.timezone(cfg.geo.timezone_names[tz_id])
            _dt = DT.datetime(2015, 1, 1)
            offset = (tz.utcoffset(_dt) + tz.dst(_dt)).total_seconds()/60.
            # localize and then convert to dispatch_outputs_timezone
            df = group.tz_localize(pytz.FixedOffset(offset), level='weather_datetime').tz_convert(self.dispatch_outputs_timezone, level='weather_datetime')
            new_df.append(df)
        
        if inplace:
            setattr(self, attr, pd.concat(new_df).sort_index())
        else:
            return pd.concat(new_df).sort_index()

    def convert_index_to_datetime(self, dataframe_name, index_name='weather_datetime'):
        df = getattr(self, dataframe_name)
        names = df.index.names
        df.reset_index(inplace=True)
        df['weather_datetime'] = cfg.date_lookup.lookup(self.raw_values['weather_datetime'])
        df['weather_datetime'].freq = 'H'
        df.set_index(names, inplace=True)
        df.sort_index(inplace=True)
    
    @staticmethod
    def produce_flexible_load(shape_df, percent_flexible=None, hr_delay=None, hr_advance=None):
        percent_flexible = 0 if percent_flexible is None else percent_flexible
        hr_delay = 0 if hr_delay is None else hr_delay
        hr_advance = 0 if hr_advance is None else hr_advance
        
        if percent_flexible==0 or (hr_delay==0 and hr_advance==0):
            return util.df_slice(shape_df, elements=2, levels='timeshift_type')
                
        timeshift_levels = list(util.get_elements_from_level(shape_df, 'timeshift_type'))
        timeshift_levels.sort()
        if timeshift_levels==[1, 2, 3]:
            delay = util.df_slice(shape_df, elements=1, levels='timeshift_type')
            native = util.df_slice(shape_df, elements=2, levels='timeshift_type')
            advance = util.df_slice(shape_df, elements=3, levels='timeshift_type')
        elif timeshift_levels==[2]:
            # TODO this could be a lambda function
            def shift(df, hr):
                """ positive hours is a shift forward, negative hours a shift back"""
                return df.shift(hr).bfill().ffill()
                
            non_weather = [n for n in shape_df.index.names if n!='weather_datetime']
            delay = shape_df.groupby(level=non_weather).apply(shift, hr=hr_delay)
            native = shape_df
            advance = shape_df.groupby(level=non_weather).apply(shift, hr=-hr_advance)
        else:
            raise ValueError("elements in the level timeshift_type are not recognized")

        return pd.concat([delay*percent_flexible + native*(1-percent_flexible),
                          native,
                          advance*percent_flexible + native*(1-percent_flexible)], keys=[1,2,3], names=['timeshift_type'])


directory = os.getcwd()
rerun_shapes = False

#######################
#######################
if rerun_shapes:
    shapes = Shapes()
    shapes.rerun = True
else:
    with open(os.path.join(directory, 'shapes.p'), 'rb') as infile:
        shapes = pickle.load(infile)
    shapes.rerun = False
    
#######################


