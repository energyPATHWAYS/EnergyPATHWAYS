# -*- coding: utf-8 -*-
"""
Created on Tue Nov 17 09:36:07 2015

@author: Ben
"""

from shared_classes import Stock, StockItem, SpecifiedStock
from datamapfunctions import DataMapFunctions, Abstract
import util
import numpy as np    
import config as cfg
        
class SupplyStock(Stock, StockItem):
    def __init__(self, id, drivers, sql_id_table='SupplyStock', sql_data_table='SupplyStockData',
                 primary_key='node_id', **kwargs):
        Stock.__init__(self, id, drivers, sql_id_table='SupplyStock', sql_data_table='SupplyStockData',
                     primary_key='node_id', **kwargs)
        StockItem.__init__(self)
        
    def return_stock_slice(self, elements):
        group = self.specified.loc[elements].transpose()

        return group

class SupplySales(Abstract, DataMapFunctions):
    def __init__(self, id, supply_node_id, sql_id_table, sql_data_table, primary_key, data_id_key, reference=False):
        self.id = id
        self.input_type = 'total'
        self.supply_node_id = supply_node_id
        self.sql_id_table = sql_id_table
        self.sql_data_table = sql_data_table
        self.mapped = False
        if reference:
            for col, att in util.object_att_from_table(self.sql_id_table, self.supply_node_id, primary_key):
                setattr(self, col, att)
            DataMapFunctions.__init__(self, data_id_key)
            self.read_timeseries_data(supply_node_id=self.supply_node_id)
            self.raw_values = util.remove_df_levels(self.raw_values, 'supply_technology')
        else:
            # measure specific sales does not require technology filtering
            Abstract.__init__(self, self.id, primary_key=primary_key, data_id_key=data_id_key)

    def calculate(self, vintages, years, interpolation_method=None, extrapolation_method=None):
        self.vintages = vintages
        self.years = years
        self.remap(time_index_name='vintage',fill_timeseries=True, interpolation_method=interpolation_method, extrapolation_method=extrapolation_method, fill_value=np.nan)
        self.convert()

    def convert(self):
        model_energy_unit = cfg.cfgfile.get('case', 'energy_unit')
        model_time_step = cfg.cfgfile.get('case', 'time_step')
        if self.time_unit is not None:
            # if sales has a time_unit, then the unit is energy and must be converted to capacity
            self.values = util.unit_convert(self.values, unit_from_num=self.capacity_or_energy_unit,
                                            unit_from_den=self.time_unit, unit_to_num=model_energy_unit,
                                            unit_to_den=model_time_step)
        else:
            # if sales is a capacity unit, the model must convert the unit type to an energy unit for conversion ()
            self.values = util.unit_convert(self.values, unit_from_num=cfg.ureg.Quantity(self.capacity_or_energy_unit)
                                                                           * cfg.ureg.Quantity(model_time_step),
                                            unit_from_den=model_time_step,
                                            unit_to_num=model_energy_unit,
                                            unit_to_den=model_time_step)


    def reconcile_with_stock_levels(self, needed_sales_share_levels, needed_sales_names):
            if not set(needed_sales_names).issubset(self.values.index.names):
                # we can't have more specificity in sales share than in stock
                raise ValueError('Sales share expressed as an intensity cannot have levels not in stock')
            # pick up extra levels
            self.values = util.expand_multi(self.values, needed_sales_share_levels,
                                            needed_sales_names).sort_index()

class SupplySalesShare(Abstract, DataMapFunctions):
    def __init__(self, id, supply_node_id, sql_id_table, sql_data_table, primary_key, data_id_key, reference=False):
        self.id = id
        self.supply_node_id = supply_node_id
        self.sql_id_table = sql_id_table
        self.sql_data_table = sql_data_table
        self.mapped = False
        self.input_type = 'intensity'
        if reference:
            for col, att in util.object_att_from_table(self.sql_id_table, self.supply_node_id, primary_key):
                if att is not None:
                    setattr(self, col, att)
            DataMapFunctions.__init__(self, data_id_key)
            self.read_timeseries_data(supply_node_id=self.supply_node_id)
            self.raw_values = util.remove_df_levels(self.raw_values, ['supply_node', 'supply_technology'])
        else:
            # measure specific sales share does not require technology filtering
            Abstract.__init__(self, self.id, primary_key=primary_key, data_id_key=data_id_key)

    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        self.remap(time_index_name='vintage')

    def reconcile_with_stock_levels(self, needed_sales_share_levels, needed_sales_share_names):
        if self.input_type == 'intensity':
            if not set(self.values.index.names).issubset(needed_sales_share_names):
                # we can't have more specificity in sales share than in stock
                raise ValueError('Sales share expressed as an intensity cannot have levels not in stock')
            # pick up extra levels
            self.values = util.expand_multi(self.values, needed_sales_share_levels,
                                            needed_sales_share_names).sort_index()
            self.values.fillna(0, inplace=True)
        elif self.input_type == 'total':
            raise ValueError(
                'A sales share type of total is not currently supported. Please normalize to sales share as a percentage')
            # if not set(sales_share.values.index.names).issubset(stock.values.index.names):
            # we have extra salesshare levels and we need to do a groupby sum
            # sales_share.values = sales_share.values.groupby(level=needed_sales_share_levels).sum()
            # todo: add logic here so that if stock and service demand
            # has more specificity than sales share, we raise an exception

    @staticmethod
    def scale_reference_array_to_gap(ss_array, space_for_reference):
        num_years, num_techs, num_techs = np.shape(ss_array)

        ref_sums = np.sum(ss_array, axis=1)

        # ignore where no reference is specified to avoid dividing by zero
        vintage_no_ref, retiring_no_ref = np.nonzero(ref_sums)

        factors = np.zeros(np.shape(ref_sums))
        factors[vintage_no_ref, retiring_no_ref] += space_for_reference[vintage_no_ref, retiring_no_ref] / ref_sums[
            vintage_no_ref, retiring_no_ref]

        factors = np.reshape(np.repeat(factors, num_techs, axis=0), (num_years, num_techs, num_techs))

        # gross up reference sales share with the need
        return ss_array * factors

    @staticmethod
    def normalize_array(ss_array, retiring_must_have_replacement=True):
        # Normalize to 1
        sums = np.sum(ss_array, axis=1)

        if np.any(sums == 0) and retiring_must_have_replacement:
            raise ValueError('Every retiring technology must have a replacement specified in sales share')

        # indicies needing scaling
        vintage, retiring = np.nonzero(sums != 1)

        # normalize all to 1
        ss_array[vintage, :, retiring] = (ss_array[vintage, :, retiring].T / sums[vintage, retiring]).T
        return ss_array

    @staticmethod
    def cap_array_at_1(ss_array):
        # Normalize down to 1
        sums = np.sum(ss_array, axis=1)
        vintage, retiring = np.nonzero(sums > 1)
        # normalize those greater than 1
        ss_array[vintage, :, retiring] = (ss_array[vintage, :, retiring].T / sums[vintage, retiring]).T
        return ss_array

class SupplySpecifiedStock(SpecifiedStock):
    def __init__(self, id, sql_id_table, sql_data_table):
        SpecifiedStock.__init__(self, id, sql_id_table, sql_data_table)
        
    def convert(self):
        """
        convert values to model currency and capacity (energy_unit/time_step)
        """
        if self.values is not None:
            model_energy_unit = cfg.cfgfile.get('case', 'energy_unit')
            model_time_step = cfg.cfgfile.get('case', 'time_step')
            if self.time_unit is not None:
                self.values = util.unit_convert(self.values, unit_from_num=self.capacity_or_energy_unit,
                                            unit_from_den=self.time_unit, unit_to_num=model_energy_unit,
                                            unit_to_den=model_time_step)
            else:
               self.values = util.unit_convert(self.values, unit_from_num=cfg.ureg.Quantity(self.capacity_or_energy_unit)
                                                                           * cfg.ureg.Quantity(model_time_step),
                                            unit_from_den = model_time_step,
                                            unit_to_num=model_energy_unit,
                                            unit_to_den=model_time_step)
                                            