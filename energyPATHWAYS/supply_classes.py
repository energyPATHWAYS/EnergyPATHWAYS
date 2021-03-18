# -*- coding: utf-8 -*-
"""
Created on Tue Nov 17 09:36:07 2015

@author: Ben
"""

from shared_classes import Stock, StockItem, SpecifiedStock
import util
import numpy as np    
import config as cfg
from geomapper import GeoMapper
from unit_converter import UnitConverter
from energyPATHWAYS.generated import schema
from data_object import DataObject
import pdb
        
# class SupplyStock(Stock, StockItem):
#     def __init__(self, id, drivers, sql_id_table='SupplyStock', sql_data_table='SupplyStockData',
#                  primary_key='node_id', **kwargs):
#         Stock.__init__(self, id, drivers, sql_id_table='SupplyStock', sql_data_table='SupplyStockData',
#                      primary_key='node_id', **kwargs)
#         StockItem.__init__(self)
#
#     def return_stock_slice(self, elements):
#         group = self.specified.loc[elements].transpose()
#
#         return group

class SupplyStock(schema.SupplyStock, Stock):
    def __init__(self, supply_node, scenario=None):
        super(SupplyStock, self).__init__(supply_node=supply_node, scenario=scenario)
        self.init_from_db(supply_node, scenario)
        self.input_type = 'total'
        self.drivers = None
        self.scenario = scenario

class SupplySales(DataObject):
    def __init__(self):
        # self.id = id
        self.input_type = 'total'
        self.primary_geography = GeoMapper.supply_primary_geography
        self.mapped = False

    def calculate(self, vintages, years, interpolation_method=None, extrapolation_method=None):
        self.vintages = vintages
        self.years = years
        self.remap(time_index_name='vintage',fill_timeseries=True, converted_geography=GeoMapper.supply_primary_geography, interpolation_method=interpolation_method, extrapolation_method=extrapolation_method, fill_value=np.nan)
        if cfg.rio_supply_run:
            self.values[self.values.index.get_level_values('vintage')>min(cfg.supply_years)] = np.nan
        self.convert()

    def convert(self):
        model_energy_unit = cfg.calculation_energy_unit
        model_time_step = cfg.getParam('time_step', section='TIME')
        if self.time_unit is not None:
            # if sales has a time_unit, then the unit is energy and must be converted to capacity
            self.values = UnitConverter.unit_convert(self.values, unit_from_num=self.capacity_or_energy_unit,
                                            unit_from_den=self.time_unit, unit_to_num=model_energy_unit,
                                            unit_to_den=model_time_step)
        else:
            # if sales is a capacity unit, the model must convert the unit type to an energy unit for conversion ()
            unit_from_num = self.capacity_or_energy_unit + "_" + model_time_step
            self.values = UnitConverter.unit_convert(self.values,
                                            unit_from_num=unit_from_num,
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

class SupplySalesObj(schema.SupplySales, SupplySales):
    def __init__(self, supply_technology, scenario=None):
        schema.SupplySales.__init__(self, supply_technology=supply_technology, scenario=scenario)
        self.init_from_db(supply_technology, scenario)
        SupplySales.__init__(self)
        self.scenario = scenario


class SupplySalesMeasuresObj(schema.SupplySalesMeasures, SupplySales):
    def __init__(self, name, supply_node, scenario=None):
        schema.SupplySalesMeasures.__init__(self, name=name, scenario=scenario)
        self.init_from_db(name, scenario, supply_node=supply_node)
        SupplySales.__init__(self)
        self.scenario = scenario

class SupplySalesShare(object):
    def __init__(self):
        self.input_type = 'intensity'
        self.primary_geography = GeoMapper.supply_primary_geography
        self.mapped = False

    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        self.remap(time_index_name='vintage', converted_geography=GeoMapper.supply_primary_geography)

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

class SupplySalesShareObj(schema.SupplySalesShare, SupplySalesShare):
    def __init__(self, supply_technology, scenario=None):
        schema.SupplySalesShare.__init__(self, supply_technology=supply_technology, scenario=scenario)
        self.init_from_db(supply_technology, scenario)
        SupplySalesShare.__init__(self)
        self.scenario = scenario


class SupplySalesShareMeasuresObj(schema.SupplySalesShareMeasures, SupplySalesShare):
    def __init__(self, name, supply_node, scenario=None):
        schema.SupplySalesShareMeasures.__init__(self, name=name, scenario=scenario)
        self.init_from_db(name, scenario, supply_node=supply_node)
        SupplySalesShare.__init__(self)
        self.scenario = scenario


class SupplySpecifiedStock(schema.SupplyStockMeasures, SpecifiedStock):
    def __init__(self, name, supply_node, scenario):
        schema.SupplyStockMeasures.__init__(self, name=name, scenario=scenario)
        self.init_from_db(name, scenario, supply_node=supply_node)
        self.primary_geography = GeoMapper.supply_primary_geography
        self.scenario = scenario
        self.mapped = False
        self.input_type='total'
        
    def convert(self):
        """
        convert values to model currency and capacity (energy_unit/time_step)
        """
        if self.values is not None:
            model_energy_unit = cfg.calculation_energy_unit
            model_time_step = cfg.getParam('time_step', section='TIME')
            if self.time_unit is not None:
                self.values = UnitConverter.unit_convert(self.values, unit_from_num=self.capacity_or_energy_unit,
                                            unit_from_den=self.time_unit, unit_to_num=model_energy_unit,
                                            unit_to_den=model_time_step)
            else:
                unit_from_num = self.capacity_or_energy_unit + "_" + model_time_step
                self.values = UnitConverter.unit_convert(self.values,
                                                         unit_from_num=unit_from_num,
                                                         unit_from_den = model_time_step,
                                                         unit_to_num=model_energy_unit,
                                                         unit_to_den=model_time_step)



class RioSpecifiedStock(DataObject):
    def __init__(self, rio_data):
        self.raw_values = rio_data
        self.geography = cfg.rio_geography
        self.capacity_or_energy_unit = cfg.rio_energy_unit
        self.time_unit = cfg.rio_time_unit
        self.input_timestep = cfg.rio_timestep_multiplier
        self.input_type = 'total'
        self.interpolation_method = 'linear_interpolation'
        self.extrapolation_method = 'nearest'
        self._cols = []

    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        if self.raw_values is not None:
            try:
                self.remap(fill_value=np.nan, converted_geography=GeoMapper.supply_primary_geography)
            except:
                print(self.raw_values)
                raise
        else:
            self.values = None

    def convert(self):
        """
        convert values to model currency and capacity (energy_unit/time_step)
        """
        if self.values is not None:
            model_energy_unit = cfg.calculation_energy_unit
            model_time_step = cfg.getParam('time_step', section='TIME')
            if self.time_unit is not None:
                self.values = UnitConverter.unit_convert(self.values/self.input_timestep, unit_from_num=self.capacity_or_energy_unit,
                                                unit_from_den=self.time_unit, unit_to_num=model_energy_unit,
                                                unit_to_den=model_time_step)
            else:
                unit_from_num = self.capacity_or_energy_unit + "_" + model_time_step
                self.values = UnitConverter.unit_convert(self.values/self.input_timestep,
                                                         unit_from_num=unit_from_num,
                                                         unit_from_den=model_time_step,
                                                         unit_to_num=model_energy_unit,
                                                         unit_to_den=model_time_step)
