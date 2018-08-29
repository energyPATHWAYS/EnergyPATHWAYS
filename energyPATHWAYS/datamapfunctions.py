__author__ = 'ryan'

#from config import cfgfile, cur, geo, dnmtr_col_names, drivr_col_names
#import config as cfg
import config as cfg
import util
import numpy as np
import pandas as pd
from time_series import TimeSeries
from collections import OrderedDict
import os
import copy
import time
from util import DfOper
import logging
import pdb
import re


class DataMapFunctions:
    @staticmethod
    def _other_indexes_dict():
        this_method = DataMapFunctions._other_indexes_dict
        if not hasattr(this_method, 'memoized_result'):
            other_indexes_data = util.csv_read_table('OtherIndexesData', ('id', 'other_index_id'))
            this_method.memoized_result = {row[0]: row[1] for row in other_indexes_data}
        return this_method.memoized_result

    def __init__(self, data_id_key='id'):
        self.data_id_key = data_id_key
        self.index_levels = OrderedDict()
        self.column_names = OrderedDict()
        self.df_index_names = []

    def inspect_index_levels(self, headers, read_data):
        """
        creates a dictionary to store level headings (for database lookup) and
        level elements. Stored as attr 'index_level'
        """
        # if read_data is empty, there is nothing to do here
        if read_data:
            elements = [sorted(set(e)) for e in zip(*read_data)]
            # OrderedDict in necessary the way this currently works
            self.column_names = OrderedDict([(index_level, column_name) for index_level, column_name in cfg.index_levels if (column_name in headers) and (column_name not in self.data_id_key) and (elements[headers.index(column_name)] != [None])])
            self.index_levels = OrderedDict([(index_level, elements[headers.index(column_name)]) for index_level, column_name in cfg.index_levels if column_name in self.column_names.values()])
            self.df_index_names = [util.id_to_name(level, getattr(self, level)) if hasattr(self, level) else level for level in self.index_levels]

    def read_timeseries_data(self, data_column_names='value', **filters):  # This function needs to be sped up
        """reads timeseries data to dataframe from database. Stored in self.raw_values"""
        # rowmap is used in ordering the data when read from the sql table
        headers = util.sql_read_headers(self.sql_data_table)
        filters[self.data_id_key] = self.id

        # Check for a sensitivity specification for this table and id. If there is no relevant sensitivity specified
        # but the data table has a sensitivity column, we set the sensitivity filter to "None", which will filter
        # the data table rows down to those where sensitivity is NULL, which is the default, no-sensitivity condition.
        if 'sensitivity' in headers:
            filters['sensitivity'] = None
            if hasattr(self, 'scenario'):
                # Note that this will return None if the scenario doesn't specify a sensitivity for this table and id
                filters['sensitivity'] = self.scenario.get_sensitivity(self.sql_data_table, self.id)

        # read each line of the data_table matching an id and assign the value to self.raw_values
        read_data = util.csv_read_table(self.sql_data_table, return_iterable=True, **filters)
        self.inspect_index_levels(headers, read_data)
        self._validate_other_indexes(headers, read_data)

        rowmap = [headers.index(self.column_names[level]) for level in self.index_levels]
        data_col_ind = [headers.index(data_col) for data_col in util.put_in_list(data_column_names)]

        unit_prefix = self.unit_prefix if hasattr(self, 'unit_prefix') else 1
        if read_data:
            data = []
            for row in read_data:
                try:
                    data.append([row[i] for i in rowmap] + [row[i] * unit_prefix for i in data_col_ind])
                except:
                    logging.warning('error reading table: {}, row: {}'.format(self.sql_data_table, row))
                    raise
            column_names = self.df_index_names + util.put_in_list(data_column_names)
            self.raw_values = pd.DataFrame(data, columns=column_names).set_index(keys=self.df_index_names).sort()
            # print the duplicate values
            duplicate_index = self.raw_values.index.duplicated(keep=False) #keep = False keeps all of the duplicate indices
            if any(duplicate_index):
                logging.warning('Duplicate indices in table: {}, parent id: {}, by default the first index will be kept.'.format(self.sql_data_table, self.id))
                logging.warning(self.raw_values[duplicate_index])
                self.raw_values = self.raw_values.groupby(level=self.raw_values.index.names).first()
        else:
            self.raw_values = None
            # We didn't find any timeseries data for this object, so now we want to let the user know if that
            # might be a problem. We only expect to find timeseries data if self actually existed in the database
            # (as opposed to being a placeholder). The existence of self in the database is flagged by self.data.
            if self.data:
                if getattr(self, 'reference_tech_id', None):
                    logging.debug('No {} found for {} with id {}; using reference technology values instead.'.format(
                        self.sql_data_table, self.sql_id_table, self.id
                    ))
                else:
                    msg = 'No {} or reference technology found for {} with id {}.'.format(
                        self.sql_data_table, self.sql_id_table, self.id
                    )
                    if re.search("Cost(New|Replacement)?Data$", self.sql_data_table):
                        # The model can run fine without cost data and this is sometimes useful during model
                        # development so we just gently note if cost data is missing.
                        logging.debug(msg)
                    else:
                        # Any other missing data is likely to be a real problem so we complain
                        logging.critical(msg)

    def _validate_other_indexes(self, headers, read_data):
        """
        This method checks the following for both other_index_1 and other_index_2:
        1. If the parent object specifies an other index, all child data rows have a value for that index.
        2. If any child data row has a value for an other index, the parent specifies an other index that it should
           belong to.
        3. All other index data values belong to the other index specified by the parent object.
        """
        other_indexes_dict = util.sql_read_dict('OtherIndexesData', 'id', 'other_index_id')
        other_index_names = util.sql_read_dict('OtherIndexes', 'id', 'name')
        other_index_data_names = util.sql_read_dict('OtherIndexesData', 'id', 'name')

        for index_num in ('1', '2'):
            index_col = 'oth_%s_id' % index_num

            if index_col in headers:
                col_pos = headers.index(index_col)
                id_pos = headers.index('id')
                index_attr = 'other_index_%s_id' % index_num
                index_attr_value = getattr(self, index_attr, None)

                for row in read_data:
                    if row[col_pos] is None:
                        if index_attr_value:
                            logging.critical("{} with id {} is missing an expected value for {}. "
                                             "Parent {} has id {} and its {} is {} ({}).".format(
                                             self.sql_data_table, row[id_pos], index_col,
                                             self.sql_id_table, self.id, index_attr, index_attr_value,
                                             other_index_names[index_attr_value]
                            ))
                    elif index_attr_value is None:
                        logging.critical("{} with id {} has an {} value of {} ({}) "
                                         "but parent {} with id {} does not specify an {}.".format(
                                         self.sql_data_table, row[id_pos], index_col, row[col_pos],
                                         other_index_data_names[row[col_pos]],
                                         self.sql_id_table, self.id, index_attr
                        ))
                    elif other_indexes_dict[row[col_pos]] != index_attr_value:
                        logging.critical("{} with id {} has an {} value of {} ({}) "
                                         "which is not a member of parent {} with id {}'s {}, which is {} ({}).".format(
                                         self.sql_data_table, row[id_pos], index_col, row[col_pos],
                                         other_index_data_names[row[col_pos]],
                                         self.sql_id_table, self.id, index_attr, index_attr_value,
                                         other_index_names[index_attr_value]
                        ))

    def clean_timeseries(self, attr='values', inplace=True, time_index_name='year',
                         time_index=None, lower=0, upper=None, interpolation_method='missing', extrapolation_method='missing'):
        if time_index is None:
            time_index=cfg.cfgfile.get('case', 'years')
            # time_index = self._get_active_time_index(time_index, time_index_name)
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

    def geo_map(self, converted_geography, attr='values', inplace=True, current_geography=None, current_data_type=None, fill_value=0.,filter_geo=True):
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
        geography_map_key = cfg.cfgfile.get('case', 'default_geography_map_key') if not hasattr(self, 'geography_map_key') else self.geography_map_key

        if current_geography not in getattr(self, attr).index.names:
            logging.error("Dataframe being mapped doesn't have the stated current geography: {}".format(self.__class__))
            pdb.set_trace()

        mapped_data = cfg.geo.geo_map(getattr(self, attr), current_geography, converted_geography,
                                      current_data_type, geography_map_key, fill_value, filter_geo)

        if inplace:
            setattr(self, attr, mapped_data.sort())
        else:
            return mapped_data.sort()

    def account_for_foreign_gaus(self, attr, current_data_type, current_geography):
        geography_map_key = cfg.cfgfile.get('case', 'default_geography_map_key') if not hasattr(self, 'geography_map_key') else self.geography_map_key
        df = getattr(self, attr).copy()
        if cfg.include_foreign_gaus:
            native_gaus, current_gaus, foreign_gaus = cfg.geo.get_native_current_foreign_gaus(df, current_geography)
            if foreign_gaus:
                name = '{} {}'.format(self.sql_id_table, self.name if hasattr(self, 'name') else 'id '+str(self.id))
                logging.info('      Detected foreign gaus for {}: {}'.format(name, ', '.join([cfg.geo.geography_names[f] for f in foreign_gaus])))
                df, current_geography = cfg.geo.incorporate_foreign_gaus(df, current_geography, current_data_type, geography_map_key)
        else:
            df = cfg.geo.filter_foreign_gaus(df, current_geography)
        return df, current_geography

    def _add_missing_geographies(self, df, current_geography, current_data_type):
        current_number_of_geographies = len(util.get_elements_from_level(df, current_geography))
        propper_number_of_geographies = len(cfg.geo.geographies_unfiltered[current_geography])
        if current_data_type == 'total' and current_number_of_geographies != propper_number_of_geographies:
            # we only want to do it when we have a total, otherwise we can't just fill with zero
            df = util.reindex_df_level_with_new_elements(df, current_geography, cfg.geo.geographies_unfiltered[current_geography], fill_value=np.nan)
        return df

    def _get_active_time_index(self, time_index, time_index_name):
        if time_index is None:
            time_index = getattr(self, time_index_name + "s") if hasattr(self, time_index_name + "s") else cfg.cfgfile.get('case', 'years')
        return time_index # this is a list of years

    def _get_df_index_names_in_a_list(self, df):
        return df.index.names if df.index.nlevels > 1 else [df.index.name]

    def remap(self, map_from='raw_values', map_to='values', drivers=None, time_index_name='year',
              time_index=None, fill_timeseries=True, interpolation_method='missing', extrapolation_method='missing',
              converted_geography=None, current_geography=None, current_data_type=None, fill_value=0., lower=0, upper=None, filter_geo=True, driver_geography=None):
        """ Map data to drivers and geography
        Args:
            map_from (string): starting variable name (defaults to 'raw_values')
            map_to (string): ending variable name (defaults to 'values')
            drivers (list of or single dataframe): drivers for the remap
            input_type_override (string): either 'total' or 'intensity' (defaults to self.type)
        """
        driver_geography = cfg.disagg_geography if driver_geography is None else driver_geography
        current_data_type = self.input_type if current_data_type is None else current_data_type
        current_geography = self.geography if current_geography is None else current_geography
        time_index = self._get_active_time_index(time_index, time_index_name)
        if current_geography not in self._get_df_index_names_in_a_list(getattr(self, map_from)):
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
                                      interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                                      lower=lower, upper=upper)
            if current_geography != converted_geography:
                self.geo_map(converted_geography, attr=map_to, inplace=True, current_geography=current_geography,
                             current_data_type=current_data_type, fill_value=fill_value,filter_geo=filter_geo)
                current_geography = converted_geography
        else:
            # becomes an attribute of self just because we may do a geomap on it
            self.total_driver = DfOper.mult(util.put_in_list(drivers))
            # turns out we don't always have a year or vintage column for drivers. For instance when linked_demand_technology gets remapped
            if time_index_name in self.total_driver.index.names:
                # sometimes when we have a linked service demand driver in a demand subsector it will come in on a fewer number of years than self.years, making this clean timeseries necesary
                self.clean_timeseries(attr='total_driver', inplace=True, time_index_name=time_index_name, time_index=time_index, lower=None, upper=None, interpolation_method='missing', extrapolation_method='missing')

            # While not on primary geography, geography does have some information we would like to preserve
            if hasattr(self,'drivers') and len(drivers) == len(self.drivers) and set([x.input_type for x in self.drivers.values()]) == set(['intensity']) and set([x.base_driver_id for x in self.drivers.values()]) == set([None]):
                driver_mapping_data_type = 'intensity'
            else:
                driver_mapping_data_type = 'total'
            total_driver_current_geo = self.geo_map(current_geography, attr='total_driver', inplace=False, current_geography=driver_geography, current_data_type=driver_mapping_data_type, fill_value=fill_value, filter_geo=False)
            if current_data_type == 'total':
                if fill_value is np.nan:
                    df_intensity = DfOper.divi((getattr(self, map_to), total_driver_current_geo), expandable=(False, True), collapsible=(False, True),fill_value=fill_value).replace([np.inf],0)
                else:
                    df_intensity = DfOper.divi((getattr(self, map_to), total_driver_current_geo), expandable=(False, True), collapsible=(False, True),fill_value=fill_value).replace([np.inf,np.nan,-np.nan],0)
                setattr(self, map_to, df_intensity)

            # Clean the timeseries as an intensity
            if fill_timeseries:
                self.clean_timeseries(attr=map_to, inplace=True, time_index=time_index, interpolation_method=interpolation_method, extrapolation_method=extrapolation_method, lower=lower, upper=upper)

#            self.geo_map(converted_geography, attr=map_to, inplace=True, current_geography=current_geography, current_data_type='intensity', fill_value=fill_value, filter_geo=filter_geo)
#            total_driver_converted_geo = self.geo_map(converted_geography, attr='total_driver', inplace=False, current_geography=driver_geography, current_data_type=driver_mapping_data_type, fill_value=fill_value, filter_geo=filter_geo)
            if current_data_type == 'total':
                setattr(self, map_to, DfOper.mult((getattr(self, map_to), total_driver_current_geo), fill_value=fill_value))
            else:
                setattr(self, map_to, DfOper.mult((getattr(self, map_to), total_driver_current_geo), expandable=(True, False), collapsible=(False, True), fill_value=fill_value))
            self.geo_map(converted_geography, attr=map_to, inplace=True, current_geography=current_geography, current_data_type='total', fill_value=fill_value, filter_geo=filter_geo)
            # we don't want to keep this around
            del self.total_driver


    def project(self, map_from='raw_values', map_to='values', additional_drivers=None, interpolation_method='missing',extrapolation_method='missing',
                time_index_name='year', fill_timeseries=True, converted_geography=None, current_geography=None, current_data_type=None, fill_value=0.,projected=False,filter_geo=True):

        current_data_type = self.input_type if current_data_type is None else current_data_type
        if map_from != 'raw_values' and current_data_type == 'total':
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
                df, current_geography = self.account_for_foreign_gaus(map_from, current_data_type, current_geography)
                setattr(self,map_to,df)
                self.geo_map(converted_geography, current_geography=current_geography, attr=map_to, inplace=True)
                current_geography = converted_geography
            total_driver = util.DfOper.mult([self.drivers[id].values for id in denominator_driver_ids])
            self.geo_map(current_geography=current_geography, attr=map_to, converted_geography=cfg.disagg_geography, current_data_type = 'intensity')
            setattr(self, map_to, util.DfOper.mult((getattr(self, map_to), total_driver)))
            self.geo_map(current_geography=cfg.disagg_geography, attr=map_to, converted_geography=current_geography,current_data_type='total')
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
                   current_data_type=current_data_type, fill_value=fill_value,filter_geo=filter_geo)


class Abstract(DataMapFunctions):
    def __init__(self, name, primary_key='name', data_id_key=None, **filters):
        # From Ryan: I've introduced a new parameter called data_id_key, which is the key in the "Data" table
        # because we are introducing primary keys into the Data tables, it is sometimes necessary to specify them separately
        # before we only has primary_key, which was shared in the "parent" and "data" tables, and this is still the default as we make the change.
        if data_id_key is None:
            data_id_key = primary_key

        table = self.sql_id_table

        try:
            col_att = util.object_att_from_table(table, name, primary_key)
        except:
            logging.error(table, name, primary_key)
            raise

        if col_att is None:
            self.data = False
        else:
            for col, att in col_att:
                setattr(self, col, att)
            self.data = True

        DataMapFunctions.__init__(self, data_id_key)
        self.read_timeseries_data(**filters)

