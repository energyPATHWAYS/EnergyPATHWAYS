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
            other_indexes_data = util.sql_read_table('OtherIndexesData', ('id', 'other_index_id'))
            this_method.memoized_result = {row[0]: row[1] for row in other_indexes_data}
        return this_method.memoized_result

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


    def read_timeseries_data(self, data_column_names='value', **filters):  # This function needs to be sped up
        """reads timeseries data to dataframe from database. Stored in self.raw_values"""
        # rowmap is used in ordering the data when read from the sql table
        headers = util.sql_read_headers(self.sql_data_table)
        rowmap = [headers.index(self.column_names[level]) for level in self.index_levels]
        data_col_ind  = []
        for data_col in util.put_in_list(data_column_names):
            data_col_ind.append(headers.index(data_col))
        # read each line of the data_table matching an id and assign the value to self.raw_values
        if len(filters):
            merged_dict = dict({self.data_id_key: self.id}, **filters)
            read_data = util.sql_read_table(self.sql_data_table, return_iterable=True, **merged_dict)
        else:
            read_data = util.sql_read_table(self.sql_data_table, return_iterable=True, **dict([(self.data_id_key, self.id)]))

        self._validate_other_indexes(headers, read_data)

        data = []
        if read_data:
            for row in read_data:
                try:
                    data.append([row[i] for i in rowmap] + [row[i] * (self.unit_prefix if hasattr(self, 'unit_prefix') else 1) for i in data_col_ind])
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
            msg = 'No {} found for {} with id {}.'.format(self.sql_data_table, self.sql_id_table, self.id)
            if re.search("Cost(New|Replacement)?Data$", self.sql_data_table) or \
                self.sql_data_table in ['DemandTechsAuxEfficiencyData',
                                        'DemandTechsParasiticEnergyData',
                                        'DemandTechsServiceDemandModifierData']:
                # The model can run fine without cost data as well as some kinds of supplementary data about demand
                # technologies, and this is sometimes useful during model development so we just gently note if cost
                # data is missing.
                logging.debug(msg)
            else:
                # Any other missing data is potentially fatal so we complain
                # FIXME: but for now we're leaving this at debug level as well since we haven't fully defined
                # what constitutes problematically missing data
                logging.debug(msg)

            self.raw_values = None

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

        # create dataframe with map from one geography to another
        map_df = cfg.geo.map_df(current_geography, converted_geography, normalize_as=current_data_type, map_key=geography_map_key,filter_geo=filter_geo)

        mapped_data = DfOper.mult([getattr(self, attr), map_df], fill_value=fill_value)
        if current_geography!=converted_geography:
            mapped_data = util.remove_df_levels(mapped_data, current_geography)
            
        if hasattr(mapped_data.index,'swaplevel'):
            mapped_data = mapped_data.swaplevel(converted_geography, 0)
        
        if inplace:
            setattr(self, attr, mapped_data.sort())
        else:
            return mapped_data.sort()

    def ensure_correct_geography(self, map_to, converted_geography, current_geography=None, current_data_type=None, filter_geo=True):
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

        if filter_geo:
           setattr(self, map_to, cfg.geo.filter_extra_geos_from_df(getattr(self, map_to)))

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

    def remap(self, map_from='raw_values', map_to='values', drivers=None, time_index_name='year',
              time_index=None, fill_timeseries=True, interpolation_method='missing', extrapolation_method='missing',
              converted_geography=None, current_geography=None, current_data_type=None, fill_value=0., lower=0, upper=None, filter_geo=True):
        """ Map data to drivers and geography
        Args:
            map_from (string): starting variable name (defaults to 'raw_values')
            map_to (string): ending variable name (defaults to 'values')
            drivers (list of or single dataframe): drivers for the remap
            input_type_override (string): either 'total' or 'intensity' (defaults to self.type)
        """
        converted_geography = cfg.primary_geography if converted_geography is None else converted_geography
        current_data_type = self.input_type if current_data_type is None else current_data_type
        current_geography = self.geography if current_geography is None else current_geography

        if time_index is None:
            time_index = getattr(self, time_index_name + "s") if hasattr(self, time_index_name + "s") else cfg.cfgfile.get('case', 'years')

        mapf_index_names = getattr(self, map_from).index.names if getattr(self, map_from).index.nlevels > 1 else [getattr(self, map_from).index.name]
        if current_geography not in mapf_index_names:
            raise ValueError('Current geography does not match the geography of the dataframe in remap')
        
        # deals with foreign gaus and updates the geography
        df, current_geography = self.account_for_foreign_gaus(map_from, current_data_type, current_geography)
        setattr(self, map_to, df)

        if current_data_type == 'total' and len(cfg.geo.geographies_unfiltered[current_geography])!=len(util.get_elements_from_level(getattr(self,map_to),current_geography)):
            setattr(self, map_to, util.reindex_df_level_with_new_elements(getattr(self,map_to), current_geography, cfg.geo.geographies_unfiltered[current_geography], fill_value=np.nan))

        if (drivers is None) or (not len(drivers)):
            if fill_timeseries:     
                self.clean_timeseries(attr=map_to, inplace=True, time_index=time_index, time_index_name=time_index_name, interpolation_method=interpolation_method, extrapolation_method=extrapolation_method, lower=lower, upper=upper)
            if current_geography != converted_geography:
                self.geo_map(converted_geography, attr=map_to, inplace=True, current_geography=current_geography,
                             current_data_type=current_data_type, fill_value=fill_value,filter_geo=filter_geo)
                current_geography = converted_geography
        else:
            self.total_driver = DfOper.mult(util.put_in_list(drivers))
            if current_geography != converted_geography and len(util.put_in_list(drivers))<=1:
                # While not on primary geography, geography does have some information we would like to preserve
                self.geomapped_total_driver = self.geo_map(current_geography, attr='total_driver', inplace=False, current_geography=converted_geography,
                         current_data_type='total', fill_value=fill_value,filter_geo=False)
            elif current_geography!=converted_geography:
                self.geo_map(converted_geography, attr=map_to, inplace=True, current_geography=current_geography,
                         current_data_type=current_data_type, fill_value=fill_value)
                current_geography = converted_geography
            # Divide by drivers to turn a total to intensity. multindex_operation will aggregate to common levels.
            if current_data_type == 'total' :
                df_intensity = DfOper.divi((getattr(self, map_to),  self.geomapped_total_driver if hasattr(self,'geomapped_total_driver') else self.total_driver), expandable=(False, True), collapsible=(False, True),fill_value=fill_value).replace([np.inf,np.nan,-np.nan],0)
                setattr(self, map_to, df_intensity)
            self.geo_map(converted_geography, attr=map_to, inplace=True, current_geography=current_geography,
                     current_data_type='intensity', fill_value=fill_value,filter_geo=filter_geo)
            if hasattr(self,'geomapped_total_driver'):
                delattr(self,'geomapped_total_driver')
            current_geography = converted_geography
            # Clean the timeseries as an intensity
            if fill_timeseries:
                # print getattr(self,map_to)
                # print time_index
                self.clean_timeseries(attr=map_to, inplace=True, time_index=time_index, interpolation_method=interpolation_method, extrapolation_method=extrapolation_method)

            if current_data_type == 'total':
                setattr(self, map_to, DfOper.mult((getattr(self, map_to), self.total_driver),fill_value=fill_value))
            else:
                try:
                    setattr(self, map_to, DfOper.mult((getattr(self, map_to), self.total_driver), expandable=(True, False), collapsible=(False, True), fill_value=fill_value))
                except:
                    pdb.set_trace()
        self.ensure_correct_geography(map_to, converted_geography, current_geography, current_data_type,filter_geo=filter_geo)


    def project(self, map_from='raw_values', map_to='values', additional_drivers=None, interpolation_method='missing',extrapolation_method='missing',
                time_index_name='year', fill_timeseries=True, converted_geography=None, current_geography=None, current_data_type=None, fill_value=0.,projected=False,filter_geo=True):
        
        converted_geography = cfg.primary_geography if converted_geography is None else converted_geography
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
                self.geo_map(converted_geography, attr=map_to, inplace=True)
                current_geography = converted_geography
            total_driver = DfOper.mult([self.drivers[id].values for id in denominator_driver_ids])
            setattr(self, map_to, DfOper.mult((getattr(self, map_to), total_driver)))
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
    def __init__(self, id, primary_key='id', data_id_key=None, **filters):
        # From Ryan: I've introduced a new parameter called data_id_key, which is the key in the "Data" table
        # because we are introducing primary keys into the Data tables, it is sometimes necessary to specify them separately
        # before we only has primary_key, which was shared in the "parent" and "data" tables, and this is still the default as we make the change.
        if data_id_key is None:
            data_id_key = primary_key

        try:
            col_att = util.object_att_from_table(self.sql_id_table, id, primary_key)
        except:
            logging.error(self.sql_id_table, id, primary_key)
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

