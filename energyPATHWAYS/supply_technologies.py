# -*- coding: utf-8 -*-
"""
Created on Wed Oct 28 16:06:06 2015

@author: Ben
"""

import inspect
from datamapfunctions import Abstract
import util
import copy
import numpy as np
from config import cfg
from shared_classes import StockItem
from supply_classes import SupplySalesShare, SupplySales, SupplySpecifiedStock
import pandas as pd
from shape import shapes, Shape


class SupplyTechnology(StockItem):
    def __init__(self, id, cost_of_capital, **kwargs):
        self.id = id
        for col, att in util.object_att_from_table('SupplyTechs', id):
            setattr(self, col, att)
        if self.cost_of_capital is None:
            self.cost_of_capital = cost_of_capital
        self.add_costs()
        self.efficiency = SupplyTechEfficiency(id)
        self.capacity_factor = SupplyTechCapacityFactor(id)
        self.co2_capture = SupplyTechCO2Capture(id)
        self.reference_sales_shares = {}
        if self.id in util.sql_read_table('SupplySalesShareData', 'supply_technology', return_unique=True, return_iterable=True):
            self.reference_sales_shares[1] = SupplySalesShare(id=self.id, supply_node_id=self.supply_node_id, reference=True,sql_id_table='SupplySalesShare', sql_data_table='SupplySalesShareData', primary_key='supply_node_id', data_id_key='supply_technology')
        self.reference_sales = {}
        if self.id in util.sql_read_table('SupplySalesData','supply_technology', return_unique=True, return_iterable=True):
            self.reference_sales[1] = SupplySales(id=self.id, supply_node_id=self.supply_node_id, reference=True,sql_id_table='SupplySales', sql_data_table='SupplySalesData', primary_key='supply_node_id', data_id_key='supply_technology')
        StockItem.__init__(self)
        
        if self.shape_id is not None:
            self.shape = shapes.data[self.shape_id]
            shapes.activate_shape(self.shape_id)

    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        attributes = vars(self)
        for att in attributes:
            obj = getattr(self, att)
            if inspect.isclass(type(obj)) and hasattr(obj, '__dict__') and hasattr(obj, 'calculate'):
                    obj.calculate(self.vintages, self.years)

    def add_sales_share_measures(self, package_id):
        self.sales_shares = {}
        measure_ids = util.sql_read_table('SupplySalesShareMeasurePackagesData', 'measure_id', package_id=package_id,
                                          return_iterable=True)
        for measure_id in measure_ids:
            sales_share_ids = util.sql_read_table('SupplySalesShareMeasures', 'id', demand_tech_id=self.id, id=measure_id,
                                                  return_iterable=True)
            for sales_share_id in sales_share_ids:
                self.sales_shares[sales_share_id] = SupplySalesShare(id=sales_share_id, node_id=self.node_id,
                                                                     reference=False, sql_id_table='SupplySalesShareMeasures',
                                                                     sql_data_table='SupplySalesShareMeasuresData',
                                                                     primary_key='id', data_id_key='parent_id')
                                                               
    def add_sales_measures(self, package_id):
        self.sales = {}
        measure_ids = util.sql_read_table('SupplySalesMeasurePackagesData', 'measure_id', package_id=package_id,
                                          return_iterable=True)
        for measure_id in measure_ids:
            sales_ids = util.sql_read_table('SupplySalesMeasures', 'id', demand_tech_id=self.id, id=measure_id,
                                                  return_iterable=True)
            for sales_id in sales_ids:
                self.sales[sales_id] = SupplySales(id=sales_id, node_id=self.node_id,
                                                    reference=False, sql_id_table='SupplySalesMeasures',
                                                    sql_data_table='SupplySalesMeasuresData',
                                                    primary_key='id', data_id_key='parent_id')

    def add_specified_stock_measures(self, package_id):
        self.specified_stocks = {}
        measure_ids = util.sql_read_table('SupplyStockMeasurePackagesData', 'measure_id', package_id=package_id,
                                          return_iterable=True)
        for measure_id in measure_ids:
            specified_stocks = util.sql_read_table('SupplyStockMeasures', 'id', supply_technology_id=self.id,return_iterable=True)
            for specified_stock in specified_stocks:
                self.specified_stocks[specified_stock] = SupplySpecifiedStock(id=specified_stock,
                                                                        sql_id_table='SupplyStockMeasures',
                                                                        sql_data_table='SupplyStockMeasuresData')

    def add_costs(self):
        """
        Adds all conversion technology costs and uses replace_costs function on 
        equivalent costs.
        
        """
        self.capital_cost_new = SupplyTechInvestmentCost(self.id, 'SupplyTechsCapitalCost','SupplyTechsCapitalCostNewData', self.book_life, self.cost_of_capital)
        self.capital_cost_replacement = SupplyTechInvestmentCost(self.id, 'StorageTechsCapacityCapitalCost', 'SupplyTechsCapitalCostReplacementData', self.book_life, self.cost_of_capital)
        self.installation_cost_new = SupplyTechInvestmentCost(self.id, 'SupplyTechsInstallationCost', 'SupplyTechsInstallationCostNewData', self.book_life, self.cost_of_capital)
        self.installation_cost_replacement = SupplyTechInvestmentCost(self.id, 'SupplyTechsInstallationCost', 'SupplyTechsInstallationCostReplacementData', self.book_life, self.cost_of_capital)
        self.fixed_om = SupplyTechFixedOMCost(self.id, 'SupplyTechsFixedMaintenanceCost', 'SupplyTechsFixedMaintenanceCostData')
        self.variable_om = SupplyTechVariableOMCost(self.id, 'SupplyTechsVariableMaintenanceCost', 'SupplyTechsVariableMaintenanceCostData')
        
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
            if class_a_instance.data is False and hasattr(class_a_instance, 'reference_tech_id') is False and class_a is 'capital_cost_new':
                 #raises a warning if no capital costs are input   
                 print "Conversion technology %s has no capital cost data" % (self.id)
        else:
            class_a_instance = getattr(self, class_a)
            class_b_instance = getattr(self, class_b)
            if class_a_instance.data is True and class_a_instance.raw_values is not None and class_b_instance.data is True and class_b_instance.raw_values is not None:
                pass
            elif class_a_instance.data is False and class_b_instance.data is False and \
                            hasattr(class_a_instance, 'reference_tech_id') is False and \
                            hasattr(class_b_instance, 'reference_tech_id') is False:
                pass
            elif class_a_instance.data is True and class_a_instance.raw_values is not None and (class_b_instance.data is False or (class_b_instance.data is True and class_b_instance.raw_values is None)):
                setattr(self, class_b, copy.deepcopy(class_a_instance))
            elif (class_a_instance.data is False or (class_a_instance.data is True and class_a_instance.raw_values is None))and class_b_instance.data is True and class_b_instance.raw_values is not None:
                setattr(self, class_a, copy.deepcopy(class_b_instance))


class StorageTechnology(SupplyTechnology):
    def __init__(self, id, cost_of_capital, **kwargs):
        SupplyTechnology.__init__(self,id,cost_of_capital)

    def add_costs(self):
        """
        Adds all conversion technology costs and uses replace_costs function on 
        equivalent costs.
        
        """
        self.capital_cost_new_capacity = SupplyTechInvestmentCost(self.id, 'StorageTechsCapacityCapitalCost', 'StorageTechsCapacityCapitalCostNewData', self.book_life, self.cost_of_capital)
        self.capital_cost_replacement_capacity = SupplyTechInvestmentCost(self.id, 'StorageTechsCapacityCapitalCost', 'StorageTechsCapacityCapitalCostReplacementData', self.book_life, self.cost_of_capital)
        self.capital_cost_new_energy = StorageTechEnergyCost(self.id, 'StorageTechsEnergyCapitalCost', 'StorageTechsEnergyCapitalCostNewData', self.book_life, self.cost_of_capital)
        self.capital_cost_replacement_energy = StorageTechEnergyCost(self.id, 'StorageTechsEnergyCapitalCost', 'StorageTechsEnergyCapitalCostReplacementData', self.book_life, self.cost_of_capital)                                       
        
        self.installation_cost_new = SupplyTechInvestmentCost(self.id, 'SupplyTechsInstallationCost', 'SupplyTechsInstallationCostNewData', self.book_life, self.cost_of_capital)
        self.installation_cost_replacement = SupplyTechInvestmentCost(self.id, 'SupplyTechsInstallationCost', 'SupplyTechsInstallationCostReplacementData', self.book_life, self.cost_of_capital)
        self.fixed_om = SupplyTechFixedOMCost(self.id, 'SupplyTechsFixedMaintenanceCost', 'SupplyTechsFixedMaintenanceCostData')
        self.variable_om = SupplyTechVariableOMCost(self.id, 'SupplyTechsVariableMaintenanceCost', 'SupplyTechsVariableMaintenanceCostData')
        
        self.replace_costs('capital_cost_new_capacity', 'capital_cost_replacement_capacity')
        self.replace_costs('capital_cost_new_energy', 'capital_cost_replacement_energy')
        self.replace_costs('installation_cost_new', 'installation_cost_replacement')
        self.replace_costs('fixed_om')
        self.replace_costs('variable_om')

class SupplyTechCost(Abstract):
    def __init__(self, id, sql_id_table, sql_data_table, book_life=None, **kwargs):
        self.id = id
        self.name = sql_data_table
        self.input_type = 'intensity'
        self.sql_id_table = sql_id_table
        self.sql_data_table = sql_data_table
        self.book_life = book_life
        Abstract.__init__(self, id, primary_key='supply_tech_id', data_id_key='supply_tech_id')
    
    
    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        if self.data and self.raw_values is not None:
            self.convert()
            self.remap(map_from='values', map_to='values', time_index_name='vintage')
            util.convert_age(self, vintages=self.vintages, years=self.years, attr_from='values', attr_to='values_level', reverse=False)
        if self.data is False:
            self.absolute = False
        if self.raw_values is None:
            # if the class is empty, then there is no data for conversion, so the class is considered converted
            self.absolute = True


class SupplyTechInvestmentCost(SupplyTechCost):
    def __init__(self, id, sql_id_table, sql_data_table, book_life=None, cost_of_capital=None, **kwargs):
        SupplyTechCost.__init__(self, id, sql_id_table, sql_data_table, book_life)
        self.cost_of_capital = cost_of_capital
        if self.cost_of_capital is None:
            self.cost_of_capital = cost_of_capital
    
    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        if self.data and self.raw_values is not None:
            self.convert()
            self.remap(map_from='values', map_to='values', time_index_name='vintage')
            self.levelize_costs()
        if self.data is False:
            self.absolute = False
        if self.raw_values is None:
            # if the class is empty, then there is no data for conversion, so the class is considered converted
            self.absolute = True

    def levelize_costs(self):
        if hasattr(self, 'is_levelized'):
            inflation = float(cfg.cfgfile.get('case', 'inflation_rate'))
            rate = self.cost_of_capital - inflation
            if self.is_levelized == 0:
                self.values_level = - np.pmt(rate, self.book_life, 1, 0, 'end') * self.values
                util.convert_age(self, vintages=self.vintages, years=self.years, attr_from='values_level', attr_to='values_level', reverse=False)
            else:
                self.values_level = self.values.copy()
                util.convert_age(self, vintages=self.vintages, years=self.years, attr_from='values_level', attr_to='values_level', reverse=False)
                self.values = np.pv(rate, self.book_life, -1, 0, 'end') * self.values
        else:
            util.convert_age(self, vintages=self.vintages, years=self.years, reverse=False)
            
    def convert(self):
        """
        convert raw_values to model currency and capacity (energy_unit/time_step)
        """
        model_energy_unit = cfg.cfgfile.get('case', 'energy_unit')
        model_time_step = cfg.cfgfile.get('case', 'time_step')
        if self.time_unit is not None:
            # if a cost has a time_unit, then the unit is energy and must be converted to capacity
            self.values = util.unit_convert(self.raw_values, unit_from_den=self.capacity_or_energy_unit,
                                            unit_from_num=self.time_unit, unit_to_den=model_energy_unit,
                                            unit_to_num=model_time_step)
        else:
            # if a cost is a capacity unit, the model must convert the unit type to an energy unit for conversion ()
            self.values = util.unit_convert(self.raw_values, unit_from_den =cfg.ureg.Quantity(self.capacity_or_energy_unit)* cfg.ureg.Quantity(model_time_step),
                                        unit_from_num=model_time_step,
                                        unit_to_den=model_energy_unit,
                                        unit_to_num=model_time_step)
        if self.definition == 'absolute':
            self.values = util.currency_convert(self.values, self.currency_id, self.currency_year_id)
            self.absolute = True
        else:
            self.absolute = False

           
class StorageTechEnergyCost(SupplyTechInvestmentCost):           
    def _init__(self, id, sql_id_table, sql_data_table, book_life=None, cost_of_capital=None,**kwargs):
        SupplyTechInvestmentCost.__init__(self, id, sql_id_table, sql_data_table, book_life, cost_of_capital)  

    def convert(self):
        """
        convert raw_values to model currency and capacity (energy_unit/time_step)
        """
        model_energy_unit = cfg.cfgfile.get('case', 'energy_unit')
        self.values = util.unit_convert(self.raw_values, unit_from_num=self.energy_unit,unit_to_num=model_energy_unit)
        if self.definition == 'absolute':
            self.values = util.currency_convert(self.values, self.currency_id, self.currency_year_id)
            self.absolute = True
        else:
            self.absolute = False


class SupplyTechFixedOMCost(SupplyTechCost):
    def __init__(self, id, sql_id_table, sql_data_table, book_life=None, **kwargs):
        SupplyTechCost.__init__(self, id, sql_id_table, sql_data_table, book_life)
            
    def convert(self):
        """
        convert raw_values to model currency and capacity (energy_unit/time_step)
        """
        model_energy_unit = cfg.cfgfile.get('case', 'energy_unit')
        model_time_step = cfg.cfgfile.get('case', 'time_step')
        if self.time_unit is not None:
            # if a cost has a time_unit, then the unit is energy and must be converted to capacity
            self.values = util.unit_convert(self.raw_values, unit_from_num=self.capacity_or_energy_unit,
                                            unit_from_den=self.time_unit, unit_to_num=model_energy_unit,
                                            unit_to_den=model_time_step)
        else:
            # if a cost is a capacity unit, the model must convert the unit type to an energy unit for conversion ()
            self.values = util.unit_convert(self.raw_values, unit_from_den=cfg.ureg.Quantity(self.capacity_or_energy_unit)
                                                                           * cfg.ureg.Quantity(model_time_step),
                                            unit_from_num=model_time_step,
                                            unit_to_den=model_energy_unit,
                                            unit_to_num=model_time_step)
        if self.definition == 'absolute':
            self.values = util.currency_convert(self.values, self.currency_id, self.currency_year_id)
            self.absolute = True
        else:
            self.absolute = False

class SupplyTechVariableOMCost(SupplyTechCost):
    def __init__(self, id, sql_id_table, sql_data_table, book_life=None, **kwargs):
        SupplyTechCost.__init__(self, id, sql_id_table, sql_data_table, book_life)
            
    def convert(self):
        """
        convert raw_values to model currency and capacity (energy_unit/time_step)
        """
        model_energy_unit = cfg.cfgfile.get('case', 'energy_unit')
        self.values = util.unit_convert(self.raw_values, unit_from_den=self.energy_unit,unit_to_den=model_energy_unit)
        if self.definition == 'absolute':
            self.values = util.currency_convert(self.values, self.currency_id, self.currency_year_id)
            self.absolute = True
        else:
            self.absolute = False
            
            
            


class SupplyTechEfficiency(Abstract):
    def __init__(self, id, **kwargs):
        self.id = id
        self.input_type = 'intensity'
        self.sql_id_table = 'SupplyTechsEfficiency'
        self.sql_data_table = 'SupplyTechsEfficiencyData'
        Abstract.__init__(self, self.id, 'supply_tech_id')

        
    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        if self.data and self.raw_values is not None:
            self.convert()
            self.remap(map_from='values', map_to='values', time_index_name='vintage', lower=None)
            util.convert_age(self, vintages=self.vintages, years=self.years, attr_from='values', attr_to='values', reverse=True)
        if self.data is False:
            self.absolute = False
        if self.raw_values is None:
            # if the class is empty, then there is no data for conversion, so the class is considered converted
            self.absolute = True

          

    def convert(self):
        """
        return values from raw_values that are converted to units consistent with output units
        """
        if self.definition == 'absolute':
            self.values = util.unit_convert(self.raw_values,
                                            unit_from_num=self.input_unit, unit_to_num=self.output_unit)
            self.absolute = True
        else:
            self.values = self.raw_values.copy()
            self.absolute = False


class SupplyTechCapacityFactor(Abstract):
    def __init__(self, id, **kwargs):
        self.id = id
        self.input_type = 'intensity'
        self.sql_id_table = 'SupplyTechsCapacityFactor'
        self.sql_data_table = 'SupplyTechsCapacityFactorData'
        Abstract.__init__(self, id, 'supply_tech_id')
            
        
    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        if self.data and self.raw_values is not None:
            self.remap(time_index_name='vintage')
            util.convert_age(self, vintages=self.vintages, years=self.years, attr_from='values', attr_to='values', reverse=True)

 
class SupplyTechCO2Capture(Abstract):
    def __init__(self, id, **kwargs):
        self.id = id
        self.input_type = 'intensity'
        self.sql_id_table = 'SupplyTechsCO2Capture'
        self.sql_data_table = 'SupplyTechsCO2CaptureData'
        Abstract.__init__(self, id, 'supply_tech_id')
            
        
    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        if self.data and self.raw_values is not None:
            self.remap(time_index_name='vintage')
            util.convert_age(self, vintages=self.vintages, years=self.years, attr_from='values', attr_to='values', reverse=True)
        elif self.data is False:
            index = pd.MultiIndex.from_product([cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')],self.vintages], names=[cfg.cfgfile.get('case', 'primary_geography'),'vintage'])
            self.values = util.empty_df(index,columns=years,fill_value=0.0)    
            self.data = True





    