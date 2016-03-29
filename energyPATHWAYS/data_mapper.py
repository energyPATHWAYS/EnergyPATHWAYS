__author__ = 'ryan & michael'

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
from sqlalchemy.orm import reconstructor
from sqlalchemy.ext.declarative import declarative_base
import data_source


class DataMapper(object):
    data_tables = {}

    @classmethod
    def get_all_raw_values(cls, data_cls):
        print '[DataMapper] loading all raw values from %s' % data_cls
        cls.data_tables[data_cls] = data_source.fetch_as_df(data_cls)
        return cls.data_tables[data_cls]

    @classmethod
    def get_raw_values(cls, id_):
        if id_ is None:
            raise ValueError('Primary key id required to get raw data')

        # this assumes that the child class has a property called "data" that is a relationship to the data table
        data_cls = cls.data.mapper.class_

        if data_cls not in cls.data_tables:
            cls.get_all_raw_values(data_cls)

        # get the slice of this class' data table that references the requested object id_
        df = cls.data_tables[data_cls].loc[id_]

        # Drop any columns that are unused (all NaN) within the slice
        # Note that we are now working with a copy to avoid inadvertently affecting the underlying
        # data frame for the whole table (that is, data_tables[data_cls])
        df = df.dropna(axis='columns', how='all')

        assert df.notnull().values.all(), "%s contains a null (NaN) value in a column with at least one non-null" \
                                          "value for parent_id %i; for a given parent_id, each column should either" \
                                          "be all null or have no nulls" % (data_cls, id_)

        # any column that doesn't contain the value for the row is an index
        indexes = [col for col in df.columns.values if col != 'value']
        # the index columns may be of type float if they ever contained any NaN values in the original data table,
        # so we will coerce them to int now. Note that this would fail if there were any remaining NaN values in the
        # column, but we screened for that in the assertion above so it should be safe.
        df[indexes] = df[indexes].astype(int)
        df.set_index(indexes, inplace=True)

        return df

    @reconstructor
    def read_timeseries_data(self):
        """reads timeseries data to dataframe from database. Stored in self.raw_values"""
        self.raw_values = self.get_raw_values(self.id)

        # FIXME: this is a band-aid until I can understand and straighten up the more generalized black magic that
        # DataMapFunctions works with IndexLevels.
        # the idea is that if we have an index level called "gau_id" (the id of a geographical unit) and the geography
        # for this object is "census division" we want to label the column "census division" instead of "gau_id"
        # We need to re-evaluate how to do this in general for columns other than gau_id, but this is enough of a
        # patch to get DemandDrivers working as a DataMapper rather than a DataMapFunctions
        new_names = []
        for name in self.raw_values.index.names:
            if name == 'gau_id':
                new_names.append(self.geography.name)
            elif name == 'oth_1_id':
                new_names.append(self.other_index_1.name)
            else:
                new_names.append(name)

        self.raw_values.index.names = new_names

        if hasattr(self, 'unit_prefix'):
            self.raw_values = self.raw_values * self.unit_prefix


    def clean_timeseries(self, attr='values', inplace=True, time_index_name='year', 
                         time_index=None, lower=0, upper=None, interpolation_method='missing', extrapolation_method='missing'):
        if time_index is None:
            time_index=cfg.cfgfile.get('case', 'years')
        interpolation_method = self.interpolation_method.name if interpolation_method is 'missing' else interpolation_method
        extrapolation_method = self.extrapolation_method.name if extrapolation_method is 'missing' else extrapolation_method
        
        data = getattr(self, attr)
        clean_data = TimeSeries.clean(data=data, newindex=time_index, time_index_name=time_index_name,
                                      interpolation_method=interpolation_method,
                                      extrapolation_method=extrapolation_method).clip(lower=lower, upper=upper)

        if inplace:
            setattr(self, attr, clean_data)
        else:
            return clean_data


    def geo_map(self, converted_geography, attr='values', inplace=True, current_geography=None, current_data_type=None,fill_value=0.):
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
        current_data_type = self.input_type.name if current_data_type is None else current_data_type
        current_geography = self.geography.name if current_geography is None else current_geography
        geography_map_key = cfg.cfgfile.get('case', 'default_geography_map_key') if not hasattr(self,
                                                                                            'geography_map_key') else self.geography_map_key.name

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
        current_data_type = copy.copy(self.input_type.name) if current_data_type is None else current_data_type
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
        current_data_type = self.input_type.name if current_data_type is None else current_data_type
        current_geography = self.geography.name if current_geography is None else current_geography
        # TODO fix pluralization
        if time_index is None:
            time_index = getattr(self, time_index_name + "s") if hasattr(self, time_index_name + "s") else cfg.cfgfile.get('case', 'years')
        
        setattr(self, map_to, getattr(self, map_from).copy())
        
        mapf = getattr(self, map_from)
        if current_geography not in (mapf.index.names if mapf.index.nlevels > 1 else [mapf.index.name]):
            raise ValueError('current geography does not match the geography of the dataframe in remap')
        else:
            current_geography_index_levels = mapf.index.levels[util.position_in_index(mapf, current_geography)] if mapf.index.nlevels > 1 else mapf.index.tolist()

        if (drivers is None) or (not len(drivers)):
            if fill_timeseries:     
                self.clean_timeseries(attr=map_to, inplace=True, time_index=time_index, time_index_name=time_index_name, interpolation_method=interpolation_method, extrapolation_method=extrapolation_method, lower=lower, upper=upper)
            if current_geography != converted_geography:
                self.geo_map(converted_geography, attr=map_to, inplace=True, current_geography=current_geography,
                             current_data_type=current_data_type, fill_value=fill_value)
                current_geography = converted_geography
        else:
            total_driver = DfOper.mult(util.put_in_list(drivers))
            if len(current_geography_index_levels) > 1 and current_geography != converted_geography:
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
        current_data_type = self.input_type.name if current_data_type is None else current_data_type
        if hasattr(self, 'projected_input_type'):
            current_data_type = self.projected_input_type
            denominator_driver_ids = []
        else:
            denominator_driver_ids = [getattr(self, col) for col in cfg.dnmtr_col_names if getattr(self, col) is not None]

        current_geography = self.geography.name if current_geography is None else current_geography
        setattr(self, map_to, getattr(self, map_from).copy())

        if len(denominator_driver_ids):
            if current_data_type != 'intensity':
                raise ValueError(str(self.__class__) + ' id ' + str(self.id) + ': type must be intensity if variable has denominator drivers')

            if len(self.index_levels['geography_id']) > 1 and (current_geography != converted_geography):
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

DataMapper = declarative_base(cls=DataMapper)