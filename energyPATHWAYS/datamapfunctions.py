__author__ = 'ryan'

import config as cfg
import util
import numpy as np
import pandas as pd
from time_series import TimeSeries
from collections import OrderedDict
import os
import copy
import time
from pprint import pprint
from util import DfOper


class DataMapFunctions:
    def __init__(self, data_id_key='id'):
        # ToDo remove from being an ordered dict, this shouldn't be necessary
        self.data_id_key = data_id_key
        self.index_levels = OrderedDict()
        self.column_names = OrderedDict()
        self.read_index_levels()
        # creates list of dataframe headers from relational table lookup with database headers
        #  i.e. gau = geography ; self.geography = 'state'.
#        self.df_index_names = [level if hasattr(self, level) else level for level in self.index_levels]
        self.df_index_names = [util.id_to_name(level, getattr(self, level)) if hasattr(self, level) else level for level
                               in self.index_levels]

    def read_index_levels(self):
        """
        creates a dictionary to store level headings (for database lookup) and
        level elements. Stored as attr 'index_level'
        """
        data_table_columns = [x for x in util.sql_read_headers(self.sql_data_table) if x not in self.data_id_key]
        for id, index_level, column_name in util.sql_read_table('IndexLevels'):
            if column_name not in data_table_columns:
                continue
            elements = util.sql_read_table(self.sql_data_table, column_names=column_name,
                                           return_iterable=True, return_unique=True,
                                           **dict([(self.data_id_key, self.id)]))
            if len(elements):
                self.index_levels[index_level] = elements
                self.column_names[index_level] = column_name


    def read_timeseries_data(self, data_column_names='value', hide_exceptions=False, **filters):  # This function needs to be sped up
        """reads timeseries data to dataframe from database. Stored in self.raw_values"""
        # rowmap is used in ordering the data when read from the sql table
        headers = util.sql_read_headers(self.sql_data_table)
        rowmap = [headers.index(self.column_names[level]) for level in self.index_levels]
        data_col_ind  = []
        for data_col in util.put_in_list(data_column_names):
            data_col_ind.append(headers.index(data_col))
        # read each line of the data_table matching an id and assign the value to self.raw_values
        data = []
        if len(filters):
            merged_dict = dict({self.data_id_key: self.id}, **filters)
            read_data = util.sql_read_table(self.sql_data_table, return_iterable=True, **merged_dict)
        else:
            read_data = util.sql_read_table(self.sql_data_table, return_iterable=True,
                                            **dict([(self.data_id_key, self.id)]))
        if read_data:
            for row in read_data:
                try:
                    data.append([row[i] for i in rowmap] +
                                [row[i] * (self.unit_prefix if hasattr(self, 'unit_prefix') else 1) for i in data_col_ind ])
                except:
                    if hide_exceptions == False:
                        print (self.id, row, i)
            column_names = self.df_index_names + util.put_in_list(data_column_names)
            self.raw_values = pd.DataFrame(data, columns=column_names).set_index(keys=self.df_index_names).sort_index()
        else:
            self.raw_values = None

    def clean_timeseries(self, attr='values', inplace=True, time_index_name='year', 
                         time_index=None, lower=0, upper=None, interpolation_method='missing', extrapolation_method='missing'):
        if time_index is None:
            time_index=cfg.cfgfile.get('case', 'years')
        interpolation_method= self.interpolation_method if interpolation_method is 'missing' else interpolation_method
        extrapolation_method = self.extrapolation_method if extrapolation_method is 'missing' else extrapolation_method
        
        data = getattr(self, attr)
        clean_data = TimeSeries.clean(data=data, newindex=time_index, time_index_name=time_index_name,
                                      interpolation_method=interpolation_method,
                                      extrapolation_method=extrapolation_method).clip(lower=lower, upper=upper)

        if inplace:
            setattr(self, attr, clean_data)
        else:
            return clean_data


    def geo_map(self, converted_geography, attr='values', inplace=True, current_geography=None, current_data_type=None, fill_value=0.):
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
        current_data_type = self.input_type if current_data_type is None else current_data_type
        current_geography = self.geography if current_geography is None else current_geography
        geography_map_key = cfg.cfgfile.get('case', 'default_geography_map_key') if not hasattr(self,
                                                                                            'geography_map_key') else self.geography_map_key

        if current_geography == converted_geography:
            if inplace:
                return
            else:
                return getattr(self, attr)
        if current_data_type == 'total':
            subsection, supersection = converted_geography, current_geography
        elif current_data_type == 'intensity':
            subsection, supersection = current_geography, converted_geography
        else:
            raise ValueError('Input_type must be either "total" or "intensity"')

        # create dataframe with map from one geography to another
        map_df = cfg.geo.map_df(subsection, supersection, column=geography_map_key)
        # converted_gau = geo.geographies[converted_geography]

        # necessary to expand our dataframe over the new geography. keys and names set up a new dataframe level.
        # expanded = pd.concat([getattr(self, attr)]*len(converted_gau), keys=converted_gau, names=(converted_geography,))

        mapped_data = DfOper.mult([getattr(self, attr), map_df],fill_value=fill_value)
        mapped_data = util.remove_df_levels(mapped_data, current_geography)
        mapped_data = mapped_data.swaplevel(converted_geography,0)
        mapped_data.sort(inplace=True)
        if inplace:
            setattr(self, attr, mapped_data)
        # setattr(self, 'geography', converted_geography)
        else:
            return mapped_data

    def ensure_correct_geography(self, map_to, converted_geography, current_geography=None, current_data_type=None):
        current_data_type = copy.copy(self.input_type) if current_data_type is None else current_data_type
        mapt = getattr(self, map_to)
        mapt_level_names = mapt.index.names if mapt.index.nlevels > 1 else [mapt.index.name]
        if converted_geography in mapt_level_names:
            # we have picked up the converted_geography geography
            if (current_geography in mapt_level_names) and (current_geography != converted_geography):
                # our starting geography is still in the dataframe and is not equal to our converted_geography, remove it
                setattr(self, map_to, util.remove_df_levels(getattr(self, map_to), current_geography))
        else:
            # we still need to do a geomap because mapping to a driver didn't give us our converted_geography
            self.geo_map(converted_geography, attr=map_to, inplace=True, current_geography=current_geography, current_data_type=current_data_type)

    def remap(self, map_from='raw_values', map_to='values', drivers=None, time_index_name='year',
              time_index=None, fill_timeseries=True, interpolation_method='missing', extrapolation_method='missing',
              converted_geography=None, current_geography=None, current_data_type=None, fill_value=0., lower=0, upper=None):
        """ Map data to drivers and geography
        Args:
            map_from (string): starting variable name (defaults to 'raw_values')
            map_to (string): ending variable name (defaults to 'values')
            drivers (list of or single dataframe): drivers for the remap
            input_type_override (string): either 'total' or 'intensity' (defaults to self.type)
        """
        converted_geography = cfg.cfgfile.get('case', 'primary_geography') if converted_geography is None else converted_geography
        current_data_type = self.input_type if current_data_type is None else current_data_type
        current_geography = self.geography if current_geography is None else current_geography
        # TODO fix pluralization
        if time_index is None:
            time_index = getattr(self, time_index_name + "s") if hasattr(self, time_index_name + "s") else cfg.cfgfile.get('case', 'years')
        
        setattr(self, map_to, getattr(self, map_from).copy())
        
        mapf = getattr(self, map_from)
        if current_geography not in (mapf.index.names if mapf.index.nlevels > 1 else [mapf.index.name]):
            raise ValueError('current geography does not match the geography of the dataframe in remap')
#        else:
#            current_geography_index_levels = mapf.index.levels[util.position_in_index(mapf, current_geography)] if mapf.index.nlevels > 1 else mapf.index.tolist()

        if (drivers is None) or (not len(drivers)):
            if fill_timeseries:     
                self.clean_timeseries(attr=map_to, inplace=True, time_index=time_index, time_index_name=time_index_name, interpolation_method=interpolation_method, extrapolation_method=extrapolation_method, lower=lower, upper=upper)
            if current_geography != converted_geography:
                self.geo_map(converted_geography, attr=map_to, inplace=True, current_geography=current_geography,
                             current_data_type=current_data_type, fill_value=fill_value)
                current_geography = converted_geography
        else:
            total_driver = DfOper.mult(util.put_in_list(drivers))
            if current_geography != converted_geography:
                # While not on primary geography, geography does have some information we would like to preserve
                self.geo_map(converted_geography, attr=map_to, inplace=True, current_geography=current_geography,
                             current_data_type=current_data_type, fill_value=fill_value)
                current_geography = converted_geography

            if current_data_type == 'total':
                # Divide by drivers to turn a total to intensity. multindex_operation will aggregate to common levels.
                df_intensity = DfOper.divi((getattr(self, map_to), total_driver), expandable=(False, True), collapsible=(False, True),fill_value=fill_value)
                setattr(self, map_to, df_intensity)
            # Clean the timeseries as an intensity
            if fill_timeseries:
                # print getattr(self,map_to)
                # print time_index
                self.clean_timeseries(attr=map_to, inplace=True, time_index=time_index, interpolation_method=interpolation_method, extrapolation_method=extrapolation_method)
            if current_data_type == 'total':
                setattr(self, map_to, DfOper.mult((getattr(self, map_to), total_driver),fill_value=fill_value))
            else:
                setattr(self, map_to, DfOper.mult((getattr(self, map_to), total_driver), expandable=(True, False),
                                                  collapsible=(False, True),fill_value=fill_value))
            self.ensure_correct_geography(map_to, converted_geography, current_geography, current_data_type)


    def project(self, map_from='raw_values', map_to='values', additional_drivers=None, interpolation_method='missing',extrapolation_method='missing',
                time_index_name='year', fill_timeseries=True, converted_geography=None, current_geography=None, current_data_type=None, fill_value=0.):
        
        converted_geography = cfg.cfgfile.get('case', 'primary_geography') if converted_geography is None else converted_geography
        current_data_type = self.input_type if current_data_type is None else current_data_type
        if hasattr(self, 'projected_input_type'):
            current_data_type = self.projected_input_type
            denominator_driver_ids = []
        else:
            denominator_driver_ids = [getattr(self, col) for col in cfg.dnmtr_col_names if getattr(self, col) is not None]

        current_geography = self.geography if current_geography is None else current_geography
        setattr(self, map_to, getattr(self, map_from).copy())

        if len(denominator_driver_ids):
            if current_data_type != 'intensity':
                raise ValueError(str(self.__class__) + ' id ' + str(self.id) + ': type must be intensity if variable has denominator drivers')

            if current_geography != converted_geography:
                # While not on primary geography, geography does have some information we would like to preserve
                self.geo_map(converted_geography, attr=map_to, inplace=True)
                current_geography = converted_geography
            total_driver = DfOper.mult([self.drivers[id].values for id in denominator_driver_ids])
            try:
                setattr(self, map_to, DfOper.mult((getattr(self, map_to), total_driver)))
            except:
                print getattr(self, map_to)
                print total_driver
            # the datatype is now total
            current_data_type = 'total'

        driver_ids = [getattr(self, col) for col in cfg.drivr_col_names if getattr(self, col) is not None]
        drivers = [self.drivers[id].values for id in driver_ids]
        if additional_drivers is not None:
            drivers += util.put_in_list(additional_drivers)
        # both map_from and map_to are the same
        self.remap(map_from=map_to, map_to=map_to, drivers=drivers,
                   time_index_name=time_index_name, fill_timeseries=fill_timeseries, interpolation_method=interpolation_method,
                   extrapolation_method=extrapolation_method,
                   converted_geography=converted_geography, current_geography=current_geography,
                   current_data_type=current_data_type, fill_value=fill_value)
        self.projected_input_type = 'total'


class Abstract(DataMapFunctions):
    def __init__(self, id, primary_key='id', data_id_key=None, **filters):
        
        # Ryan: I've introduced a new parameter called data_id_key, which is the key in the "Data" table
        # because we are introducing primary keys into the Data tables, it is sometimes necessary to specify them separately
        # before we only has primary_key, which was shared in the "parent" and "data" tables, and this is still the default as we make the change.
        if data_id_key is None:
            data_id_key = primary_key

        try:
            col_att = util.object_att_from_table(self.sql_id_table, id, primary_key)
        except:
            print self.sql_id_table, id, primary_key
            raise

        if col_att is None:
            self.data = False
        else:
            for col, att in col_att:
                # if att is not None:
                setattr(self, col, att)
            self.data = True

        DataMapFunctions.__init__(self, data_id_key)
        self.read_timeseries_data(**filters)

