# -*- coding: utf-8 -*-
"""
Created on Wed Oct 28 16:06:06 2015

@author: Ben
"""

import inspect
import util
import copy
import numpy as np
import config as cfg
from shared_classes import StockItem
from supply_classes import SupplySalesShareObj, SupplySalesShareMeasuresObj, SupplySalesMeasuresObj, SupplySalesObj, SupplySpecifiedStock,RioSpecifiedStock
import pandas as pd
import shape
import logging
import pdb
from unit_converter import UnitConverter
from geomapper import GeoMapper
from energyPATHWAYS.generated import schema

class SupplyTechnology(schema.SupplyTechs, StockItem):
    def __init__(self, name, cost_of_capital, scenario):
        schema.SupplyTechs.__init__(self, name=name, scenario=scenario)
        self.init_from_db(name, scenario)
        StockItem.__init__(self)
        if self.cost_of_capital is None:
            self.cost_of_capital = cost_of_capital
        self.scenario = scenario
        self.add_costs()
        self.efficiency = SupplyTechEfficiency(name, self.scenario)
        self.capacity_factor = SupplyTechCapacityFactor(name, self.scenario)
        self.co2_capture = SupplyTechCO2Capture(name, self.scenario)
        self.reference_sales_shares = {}
        if self.name in util.csv_read_table('SupplySalesShare', 'supply_technology', return_unique=True, return_iterable=True):
            self.reference_sales_shares[1] = SupplySalesShareObj(supply_technology=self.name, scenario=self.scenario)
        self.reference_sales = {}
        if self.name in util.csv_read_table('SupplySales', 'supply_technology', return_unique=True, return_iterable=True):
            self.reference_sales[1] = SupplySalesObj(supply_technology=self.name, scenario=self.scenario)

        # if self.shape_id is not None:
        #     self.shape = shape.shapes.data[self.shape_id]

    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        attributes = vars(self)
        for att in attributes:
            obj = getattr(self, att)
            if inspect.isclass(type(obj)) and hasattr(obj, '__dict__') and hasattr(obj, 'calculate'):
                obj.calculate(self.vintages, self.years)

    def add_sales_share_measures(self, scenario):
        self.sales_shares = {}
        measure_names = scenario.get_measures('SupplySalesShareMeasures', self.supply_node, self.name)
        for name in measure_names:
            self.sales_shares[name] = SupplySalesShareMeasuresObj(name, self.supply_node, scenario)

    def add_sales_measures(self, scenario):
        self.sales = {}
        measure_names = scenario.get_measures('SupplySalesMeasures', self.supply_node, self.name)
        for name in measure_names:
            self.sales[name] = SupplySalesMeasuresObj(name, supply_node=self.supply_node, scenario=scenario)

    def add_specified_stock_measures(self, scenario):
        self.specified_stocks = {}
        measure_names = scenario.get_measures('SupplyStockMeasures', self.supply_node, self.name)
        for name in measure_names:
            self.specified_stocks[name] = SupplySpecifiedStock(name, supply_node=self.supply_node, scenario=scenario)

    def add_rio_stock_measures(self,rio_inputs):
        self.specified_stocks = {}
        df = rio_inputs.stock
        if self.id in set(df.index.get_level_values('technology')):
            df = util.df_slice(df,[self.id],['technology'])
            if np.any([isinstance(x,int) for x in df.index.get_level_values('resource_bin').values]):
                df = df[df.index.get_level_values('resource_bin')!='n/a']
                df = df.groupby(level=df.index.names).sum()
                self.specified_stocks[1] = RioSpecifiedStock(df)
            else:
                self.specified_stocks[1] = RioSpecifiedStock(util.remove_df_levels(df,'resource_bin'))

    def add_costs(self):
        """
        Adds all conversion technology costs and uses replace_costs function on
        equivalent costs.

        """
        self.capital_cost_new = SupplyTechsCapitalCapacityCostObj(self.name, self.scenario, 'new', self.book_life, self.cost_of_capital)
        self.capital_cost_replacement = SupplyTechsCapitalCapacityCostObj(self.name, self.scenario, 'replacement', self.book_life, self.cost_of_capital)
        self.installation_cost_new = SupplyTechsInstallationCostObj(self.name, self.scenario, 'new', self.book_life, self.cost_of_capital)
        self.installation_cost_replacement = SupplyTechsInstallationCostObj(self.name, self.scenario, 'replacement', self.book_life, self.cost_of_capital)
        self.fixed_om = SupplyTechFixedOMCost(self.name, self.scenario)
        self.variable_om = SupplyTechVariableOMCost(self.name, self.scenario)

        self.replace_costs('capital_cost_new', 'capital_cost_replacement')
        self.replace_costs('installation_cost_new', 'installation_cost_replacement')
        self.replace_costs('fixed_om')
        self.replace_costs('variable_om')

    def replace_costs(self, class_a, class_b=None):
        """
        Adds all available cost data to classes. Removes classes with no data and replaces
        them with cost classes containing equivalent data.

        Ex. If capital costs for new installations are input but capital costs for replacement are not,
        it copies capital costs for new to the replacement capital cost class
        """
        # if no class_b is specified, there is no equivalent cost for class_a
        if class_b is None:
            class_a_instance = getattr(self, class_a)
            if class_a_instance._has_data is False and hasattr(class_a_instance, 'reference_tech_id') is False and class_a is 'capital_cost_new':
                logging.warning("Conversion technology %s has no capital cost data" % (self.name))
                raise ValueError
        else:
            class_a_instance = getattr(self, class_a)
            class_b_instance = getattr(self, class_b)
            if class_a_instance._has_data is True and class_a_instance.raw_values is not None and class_b_instance._has_data is True and class_b_instance.raw_values is not None:
                pass
            elif class_a_instance._has_data is False and class_b_instance._has_data is False and \
                            hasattr(class_a_instance, 'reference_tech_id') is False and \
                            hasattr(class_b_instance, 'reference_tech_id') is False:
                pass
            elif class_a_instance._has_data is True and class_a_instance.raw_values is not None and (class_b_instance._has_data is False or (class_b_instance._has_data is True and class_b_instance.raw_values is None)):
                setattr(self, class_b, copy.deepcopy(class_a_instance))
            elif (class_a_instance._has_data is False or (class_a_instance._has_data is True and class_a_instance.raw_values is None))and class_b_instance._has_data is True and class_b_instance.raw_values is not None:
                setattr(self, class_a, copy.deepcopy(class_b_instance))


class StorageTechnology(SupplyTechnology):
    def __init__(self, name, cost_of_capital, scenario):
        SupplyTechnology.__init__(self, name, cost_of_capital, scenario)

    def add_costs(self):
        """
        Adds all conversion technology costs and uses replace_costs function on
        equivalent costs.
        """
        self.capital_cost_new_capacity = SupplyTechsCapitalCapacityCostObj(self.name, self.scenario, 'new', self.book_life, self.cost_of_capital)
        self.capital_cost_replacement_capacity = SupplyTechsCapitalCapacityCostObj(self.name, self.scenario, 'replacement', self.book_life, self.cost_of_capital)
        self.capital_cost_new_energy = SupplyTechsCapitalEnergyCostObj(self.name, self.scenario, 'new', self.book_life, self.cost_of_capital)
        self.capital_cost_replacement_energy = SupplyTechsCapitalEnergyCostObj(self.name, self.scenario, 'replacement', self.book_life, self.cost_of_capital)

        self.installation_cost_new = SupplyTechsInstallationCostObj(self.name, self.scenario, 'new', self.book_life, self.cost_of_capital)
        self.installation_cost_replacement = SupplyTechsInstallationCostObj(self.name, self.scenario, 'replacement', self.book_life, self.cost_of_capital)
        self.fixed_om = SupplyTechFixedOMCost(self.name, self.scenario)
        self.variable_om = SupplyTechVariableOMCost(self.name, self.scenario)
        self.duration = StorageTechDuration(self.name, self.scenario)

        self.replace_costs('capital_cost_new_capacity', 'capital_cost_replacement_capacity')
        self.replace_costs('capital_cost_new_energy', 'capital_cost_replacement_energy')
        self.replace_costs('installation_cost_new', 'installation_cost_replacement')
        self.replace_costs('fixed_om')
        self.replace_costs('variable_om')


class SupplyTechCost(object):
    def __init__(self):
        pass

    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        if self._has_data and self.raw_values is not None:
            self.convert()
            self.remap(map_from='values', map_to='values', converted_geography=GeoMapper.supply_primary_geography, time_index_name='vintage')
            util.convert_age(self, vintages=self.vintages, years=self.years, attr_from='values', attr_to='values_level', reverse=False)
        if not self._has_data:
            self.absolute = False
        if self.raw_values is None:
            # if the class is empty, then there is no data for conversion, so the class is considered converted
            self.absolute = True


class SupplyTechInvestmentCost(SupplyTechCost):
    def __init__(self, scenario, book_life, cost_of_capital):
        SupplyTechCost.__init__(self)
        self.scenario = scenario
        self.input_type = 'intensity'
        self.book_life = book_life
        if self.cost_of_capital is None:
            self.cost_of_capital = cost_of_capital

    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        if self._has_data and self.raw_values is not None:
            if self.definition == 'absolute':
                self.convert()
            elif self.definition == 'relative':
                self.values = copy.deepcopy(self.raw_values)
            else:
                raise ValueError("no cost definition is input (absolute or relative)")
            self.remap(map_from='values', map_to='values', converted_geography=GeoMapper.supply_primary_geography, time_index_name='vintage')
            self.levelize_costs()
        if not self._has_data:
            self.absolute = False
        if self.raw_values is None:
            # if the class is empty, then there is no data for conversion, so the class is considered converted
            self.absolute = True

    def levelize_costs(self):
        if hasattr(self, 'is_levelized'):
            inflation = cfg.getParamAsFloat('inflation_rate')
            try:
                rate = self.cost_of_capital - inflation
            except:
                pdb.set_trace()
            if self.is_levelized == 0:
                self.values_level = - np.pmt(rate, self.book_life, 1, 0, 'end') * self.values
                util.convert_age(self, vintages=self.vintages, years=self.years, attr_from='values_level', attr_to='values_level', reverse=False)
            elif self.is_levelized==1:
                self.values_level = self.values.copy()
                util.convert_age(self, vintages=self.vintages, years=self.years, attr_from='values_level', attr_to='values_level', reverse=False)
                self.values = np.pv(rate, self.book_life, -1, 0, 'end') * self.values
            elif self.definition == 'relative':
                self.values_level = self.values.copy()
                util.convert_age(self, vintages=self.vintages, years=self.years, attr_from='values_level', attr_to='values_level', reverse=False)
            else:
                raise ValueError("no specification of whether the technology cost is levelized")

        else:
            raise ValueError('Supply Technology id %s needs to indicate whether costs are levelized ' %self.name)

    def convert(self):
        """
        convert raw_values to model currency and capacity (energy_unit/time_step)
        """
        model_energy_unit = cfg.calculation_energy_unit
        model_time_step = cfg.getParam('time_step')
        if hasattr(self, 'time_unit') and self.time_unit is not None:
            # if a cost has a time_unit, then the unit is energy and must be converted to capacity
            self.values = UnitConverter.unit_convert(self.raw_values, unit_from_den=self.capacity_or_energy_unit, unit_from_num=self.time_unit, unit_to_den=model_energy_unit, unit_to_num=model_time_step)
        else:
            # if a cost is a capacity unit, the model must convert the unit type to an energy unit for conversion ()
            unit_from_den = self.capacity_or_energy_unit + "_" + model_time_step
            self.values = UnitConverter.unit_convert(self.raw_values, unit_from_den=unit_from_den, unit_from_num=model_time_step, unit_to_den=model_energy_unit, unit_to_num=model_time_step)
        if self.definition == 'absolute':
            self.values = UnitConverter.currency_convert(self.values, self.currency, self.currency_year)
            self.absolute = True
        else:
            self.absolute = False

class SupplyTechsCapitalCapacityCostObj(schema.SupplyTechsCapitalCost, SupplyTechInvestmentCost):
    def __init__(self, supply_tech, scenario, new_or_replacement, book_life=None, cost_of_capital=None):
        schema.SupplyTechsCapitalCost.__init__(self, supply_tech, scenario=scenario)
        self.init_from_db(supply_tech, scenario, new_or_replacement=new_or_replacement, capacity_or_energy='capacity')
        SupplyTechInvestmentCost.__init__(self, scenario, book_life, cost_of_capital)

class SupplyTechsCapitalEnergyCostObj(schema.SupplyTechsCapitalCost, SupplyTechInvestmentCost):
    def __init__(self, supply_tech, scenario, new_or_replacement, book_life=None, cost_of_capital=None):
        schema.SupplyTechsCapitalCost.__init__(self, supply_tech, scenario=scenario)
        self.init_from_db(supply_tech, scenario, new_or_replacement=new_or_replacement, capacity_or_energy='energy')
        SupplyTechInvestmentCost.__init__(self, scenario, book_life, cost_of_capital)

    def convert(self):
        """
        convert raw_values to model currency and capacity (energy_unit/time_step)
        """
        model_energy_unit = cfg.calculation_energy_unit
        self.values = UnitConverter.unit_convert(self.raw_values, unit_from_den=self.capacity_or_energy_unit,unit_to_den=model_energy_unit)
        if self.definition == 'absolute':
            self.values = UnitConverter.currency_convert(self.values, self.currency, self.currency_year)
            self.absolute = True
        else:
            self.absolute = False

class SupplyTechsInstallationCostObj(schema.SupplyTechsInstallationCost, SupplyTechInvestmentCost):
    def __init__(self, supply_tech, scenario, new_or_replacement, book_life=None, cost_of_capital=None):
        schema.SupplyTechsInstallationCost.__init__(self, supply_tech, scenario=scenario)
        self.cost_of_capital = cost_of_capital # todo: add this to the csv
        self.init_from_db(supply_tech, scenario, new_or_replacement=new_or_replacement)
        SupplyTechInvestmentCost.__init__(self, scenario, book_life, cost_of_capital)

class StorageTechDuration(schema.StorageTechsDuration):
    def __init__(self, name, scenario):
        schema.StorageTechsDuration.__init__(self, name, scenario=scenario)
        self.init_from_db(name, scenario)
        self.scenario = scenario
        self.input_type = 'intensity'
        self.name = name

    def set_rio_duration(self,rio_inputs):
        if self.id in set(rio_inputs.duration.index.get_level_values('technology'))and self.id not in cfg.rio_excluded_technologies:
            self._has_data = True
            self.raw_values = util.df_slice(rio_inputs.duration,self.id,'technology')
            self.geography = cfg.rio_geography
            self.capacity_or_energy_unit = cfg.rio_energy_unit
            self.time_unit = cfg.rio_time_unit
            self.input_timestep = cfg.rio_timestep_multiplier
            self.interpolation_method = 'linear_interpolation'
            self.extrapolation_method = 'nearest'

    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        if self._has_data and self.raw_values is not None:
            self.remap(time_index_name='year', converted_geography=GeoMapper.supply_primary_geography,missing_intensity_geos=True,fill_value=1)
            self.values = self.values.fillna(1)


class SupplyTechFixedOMCost(schema.SupplyTechsFixedMaintenanceCost, SupplyTechCost):
    def __init__(self, name, scenario):
        schema.SupplyTechsFixedMaintenanceCost.__init__(self, name, scenario)
        self.init_from_db(name, scenario)
        self.scenario = scenario
        self.input_type = 'intensity'
        self.name = name

    def convert(self):
        """
        convert raw_values to model currency and capacity (energy_unit/time_step)
        """
        model_energy_unit = cfg.calculation_energy_unit
        model_time_step = cfg.getParam('time_step')
        if self.time_unit is not None:
            # if a cost has a time_unit, then the unit is energy and must be converted to capacity
            self.values = UnitConverter.unit_convert(self.raw_values, unit_from_den=self.capacity_or_energy_unit,
                                            unit_from_num=self.time_unit, unit_to_den=model_energy_unit,
                                            unit_to_num=model_time_step)
        else:
            # if a cost is a capacity unit, the model must convert the unit type to an energy unit for conversion ()
            unit_from_den = self.capacity_or_energy_unit + "_" + model_time_step
            self.values = UnitConverter.unit_convert(self.raw_values, unit_from_den=unit_from_den, unit_from_num=model_time_step, unit_to_den=model_energy_unit, unit_to_num=model_time_step)
        if self.definition == 'absolute':
            self.values = UnitConverter.currency_convert(self.values, self.currency, self.currency_year)
            self.absolute = True
        else:
            self.absolute = False

class SupplyTechVariableOMCost(schema.SupplyTechsVariableMaintenanceCost, SupplyTechCost):
    def __init__(self, name, scenario):
        schema.SupplyTechsVariableMaintenanceCost.__init__(self, name, scenario)
        self.init_from_db(name, scenario)
        self.scenario = scenario
        self.input_type = 'intensity'
        self.name = name

    def convert(self):
        """
        convert raw_values to model currency and capacity (energy_unit/time_step)
        """
        model_energy_unit = cfg.calculation_energy_unit
        self.values = UnitConverter.unit_convert(self.raw_values, unit_from_den=self.energy_unit,unit_to_den=model_energy_unit)
        if self.definition == 'absolute':
            self.values = UnitConverter.currency_convert(self.values, self.currency, self.currency_year)
            self.absolute = True
        else:
            self.absolute = False


class SupplyTechEfficiency(schema.SupplyTechsEfficiency):
    def __init__(self, name, scenario):
        schema.SupplyTechsEfficiency.__init__(self, name, scenario)
        self.init_from_db(name, scenario)
        self.input_type = 'intensity'
        self.scenario = scenario
        self.name = name

    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        if self._has_data and self.raw_values is not None and cfg.rio_supply_run and 'year' in self.raw_values.index.names:
            self.remap(map_from='raw_values', map_to='values', current_geography=GeoMapper.rio_geography,converted_geography=GeoMapper.supply_primary_geography,
                       time_index_name='year', lower=None, missing_intensity_geos=True)
            self.values = self.values.unstack('year')
            self.values.columns = self.values.columns.droplevel()
            self.values = pd.concat([self.values] *len(self.vintages),keys=self.vintages,names=['vintage'])
            self.values['efficiency_type'] = 1
            self.values = self.values.set_index('efficiency_type',append=True)
        elif self._has_data and self.raw_values is not None:
            self.convert()
            self.remap(map_from='values', map_to='values', converted_geography=GeoMapper.supply_primary_geography, time_index_name='vintage', lower=None,missing_intensity_geos=True)
            util.convert_age(self, vintages=self.vintages, years=self.years, attr_from='values', attr_to='values', reverse=True)
        if not self._has_data:
            self.absolute = False
        if self.raw_values is None:
            # if the class is empty, then there is no data for conversion, so the class is considered converted
            self.absolute = True

    def convert(self):
        """
        return values from raw_values that are converted to units consistent with output units
        """
        if self.definition == 'absolute':
            self.values = UnitConverter.unit_convert(self.raw_values,
                                            unit_from_num=self.input_unit, unit_to_num=self.output_unit)
            self.absolute = True
        else:
            self.values = self.raw_values.copy()
            self.absolute = False


class SupplyTechCapacityFactor(schema.SupplyTechsCapacityFactor):
    def __init__(self, name, scenario):
        schema.SupplyTechsCapacityFactor.__init__(self, name, scenario)
        self.init_from_db(name, scenario)
        self.input_type = 'intensity'
        self.scenario = scenario
        self.name = name

    def set_rio_capacity_factor(self,rio_inputs):
        df =rio_inputs.capacity_factor
        if self.name in set(df.index.get_level_values('technology')) and  self.name not in cfg.rio_excluded_technologies:
            df = util.df_slice(df, self.name, 'technology')
            if not np.any([isinstance(x,int) for x in df.index.get_level_values('resource_bin').values]):
                df = (util.remove_df_levels(df,'resource_bin'))
            else:
                df = df[df.index.get_level_values('resource_bin') != 'n/a']
                df = df.groupby(level=df.index.names).sum()
            self.raw_values = df
            self._has_data = True
            self.geography = cfg.rio_geography
            self.capacity_or_energy_unit = cfg.rio_energy_unit
            self.time_unit = cfg.rio_time_unit
            self.input_timestep = cfg.rio_timestep_multiplier
            self.interpolation_method = 'linear_interpolation'
            self.extrapolation_method = 'nearest'

        
    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        if self._has_data and self.raw_values is not None and (cfg.rio_supply_run is not True or 'vintage' in self.raw_values.index.names):
            self.remap(time_index_name='vintage', converted_geography=GeoMapper.supply_primary_geography,fill_value=np.nan)
            self.values.replace(0,1,inplace=True)
            util.convert_age(self, vintages=self.vintages, years=self.years, attr_from='values', attr_to='values', reverse=True)
        elif self._has_data and self.raw_values is not None and cfg.rio_supply_run==True:
            self.remap(time_index_name='year', converted_geography=GeoMapper.supply_primary_geography, fill_value=np.nan)
            self.values.replace(0, 1, inplace=True)
            self.values = util.add_and_set_index(self.values,'vintage',self.vintages,index_location=-1)
            self.values = self.values.squeeze().unstack(level='year')


class SupplyTechCO2Capture(schema.SupplyTechsCO2Capture):
    def __init__(self, name, scenario):
        schema.SupplyTechsCO2Capture.__init__(self, name, scenario)
        self.init_from_db(name, scenario)
        self.input_type = 'intensity'
        self.scenario = scenario
        self.name = name


    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        if self._has_data and self.raw_values is not None:
            self.remap(time_index_name='vintage',  converted_geography=GeoMapper.supply_primary_geography)
            util.convert_age(self, vintages=self.vintages, years=self.years, attr_from='values', attr_to='values', reverse=True)
        elif not self._has_data:
            index = pd.MultiIndex.from_product([GeoMapper.geography_to_gau[GeoMapper.supply_primary_geography],self.vintages], names=[GeoMapper.supply_primary_geography,'vintage'])
            self.values = util.empty_df(index,columns=years,fill_value=0.0)
            self._has_data = True





