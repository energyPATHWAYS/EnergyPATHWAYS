# -*- coding: utf-8 -*-
"""
Created on Mon Sep 28 09:55:19 2015

@author: Ben
"""
from config import cfg
import pandas as pd
import util
from datamapfunctions import Abstract
import numpy as np
import inspect
from util import DfOper
from shared_classes import StockItem


class DemandMeasure(StockItem):
    def __init__(self):
        StockItem.__init__(self)

    def calculate(self, vintages, years, unit_to):
        self.vintages = vintages
        self.years = years
        self.unit_to = unit_to
        self.convert()
        self.clean_data()
        attributes = vars(self)
        for att in attributes:
            obj = getattr(self, att)
            if inspect.isclass(type(obj)) and hasattr(obj, '__dict__') and hasattr(obj, 'calculate'):
                obj.calculate(self.vintages, self.years, self.unit_to)


    def clean_data(self):
        if self.input_type == 'total':
            self.savings = self.clean_timeseries('values', inplace=False, time_index_name='year', time_index=self.years)
        else:
            self.remap(map_from='raw_values', map_to='values', time_index_name='year')

    def convert(self):
        if self.input_type == 'total':
            self.values = util.unit_convert(self.raw_values, unit_from_num=self.unit,
                                            unit_to_num=self.unit_to)
        else:
            self.values = self.raw_values

    def calculate_book_life(self):
        """ 
        determines book life for measures based on input mean or max/min lifetimes. 
        Used for cost levelization
        """
        if hasattr(self, 'mean_lifetime'):
            self.book_life = getattr(self, 'mean_lifetime')
        elif hasattr(self, 'max_lifetime') and hasattr(self, 'min_lifetime'):
            self.book_life = (getattr(self, 'min_lifetime') + getattr(self, 'max_lifetime')) / 2
        else:
            print "incomplete lifetime information entered for technology %s" % self.name


class ServiceDemandMeasure(Abstract, DemandMeasure):
    def __init__(self, id, cost_of_capital, service_demand_unit, **kwargs):
        self.id = id
        self.service_demand_unit = service_demand_unit
        self.sql_id_table = 'DemandServiceDemandMeasures'
        self.sql_data_table = 'DemandServiceDemandMeasuresData'
        Abstract.__init__(self, self.id, primary_key='id', data_id_key = 'parent_id')
        DemandMeasure.__init__(self)
        self.cost_of_capital = cost_of_capital
        self.calculate_book_life()
        self.cost = DemandMeasureCost(id, self.cost_of_capital, self.book_life, 'DemandServiceDemandMeasuresCost', 'DemandServiceDemandMeasuresCostData')


class EnergyEfficiencyMeasure(Abstract, DemandMeasure):
    def __init__(self, id, cost_of_capital, **kwargs):
        self.id = id
        self.sql_id_table = 'DemandEnergyEfficiencyMeasures'
        self.sql_data_table = 'DemandEnergyEfficiencyMeasuresData'
        Abstract.__init__(self, self.id, primary_key='id', data_id_key='parent_id')
        DemandMeasure.__init__(self)
        self.calculate_book_life()
        self.cost_of_capital = cost_of_capital
        self.cost = DemandMeasureCost(id, self.cost_of_capital, self.book_life, 'DemandEnergyEfficiencyMeasuresCost', 'DemandEnergyEfficiencyMeasuresCostData')


class FuelSwitchingMeasure(Abstract, StockItem):
    def __init__(self, id, cost_of_capital, **kwargs):
        self.id = id
        self.sql_id_table = 'DemandFuelSwitchingMeasures'
        self.sql_data_table = 'DemandFuelSwitchingMeasuresData'
        for col, att in util.object_att_from_table(self.sql_id_table, self.id):
            if att is not None:
                setattr(self, col, att)
        self.calculate_book_life()
        self.cost_of_capital = cost_of_capital
        self.impact = FuelSwitchingImpact(self.id)
        self.energy_intensity = FuelSwitchingEnergyIntensity(self.id)
        self.cost = DemandMeasureCost(id, self.cost_of_capital, self.book_life, 'DemandFuelSwitchingMeasuresCost', 'DemandFuelSwitchingMeasuresCostData')

    def calculate(self, vintages, years, unit_to):
        self.vintages = vintages
        self.years = years
        self.unit_to = unit_to
        attributes = vars(self)
        for att in attributes:
            obj = getattr(self, att)
            if inspect.isclass(type(obj)) and hasattr(obj, '__dict__') and hasattr(obj, 'calculate'):
                obj.calculate(self.vintages, self.years, self.unit_to)

    def energy_replace(self):
        self.replace_impact = DfOper.mult([self.energy_intensity, self.impact])

    def calculate_book_life(self):
        """ 
        determines book life for measures based on input mean or max/min lifetimes. 
        Used for cost levelization
        """
        if hasattr(self, 'mean_lifetime'):
            self.book_life = getattr(self, 'mean_lifetime')
        elif hasattr(self, 'max_lifetime') and hasattr(self, 'min_lifetime'):
            self.book_life = (getattr(self, 'min_lifetime') + getattr(self, 'max_lifetime')) / 2
        else:
            print "incomplete lifetime information entered for technology %s" % self.name


class FuelSwitchingImpact(Abstract):
    def __init__(self, id, *kwargs):
        self.id = id
        self.sql_id_table = 'DemandFuelSwitchingMeasuresImpact'
        self.sql_data_table = 'DemandFuelSwitchingMeasuresImpactData'
        Abstract.__init__(self, self.id, primary_key='id', data_id_key='parent_id')

    def calculate(self, vintages, years, unit_to):
        self.vintages = vintages
        self.years = years
        self.unit_to = unit_to
        self.clean_data()
        self.convert()

    def clean_data(self):
        if self.input_type == 'total':
            self.savings = self.clean_timeseries('values', inplace=False, time_index=self.years)
        else:
            self.remap(map_from='raw_values', map_to='values', time_index_name='year')

    def convert(self):
        if self.input_type == 'total':
            self.values = util.unit_convert(self.raw_values, unit_from_num=self.unit,
                                            unit_to_num=self.unit_to)
        else:
            pass


class FuelSwitchingEnergyIntensity(Abstract):
    def __init__(self, id, **kwargs):
        self.id = id
        self.sql_id_table = 'DemandFuelSwitchingMeasuresEnergyIntensity'
        self.sql_data_table = 'DemandFuelSwitchingMeasuresEnergyIntensityData'
        self.input_type = 'intensity'
        Abstract.__init__(self, id, primary_key='id', data_id_key='parent_id')


    def calculate(self, years, vintages, unit_to):
        self.years = years
        self.remap(map_from='raw_values', map_to='values', time_index=self.years)


class DemandMeasureCost(Abstract):
    def __init__(self, id, cost_of_capital, book_life, sql_id_table, sql_data_table, **kwargs):
        self.id = id
        self.book_life = book_life
        self.input_type = 'intensity'
        self.sql_id_table = sql_id_table
        self.sql_data_table = sql_data_table
        Abstract.__init__(self, id, primary_key='parent_id', data_id_key='parent_id')
        if hasattr(self, 'cost_of_capital'):
            if self.cost_of_capital is None:
                self.cost_of_capital = cost_of_capital

    def calculate(self, vintages, years, unit_to):
        self.vintages = vintages
        self.years = years
        self.unit_to = unit_to
        if self.data and self.raw_values is not None:
            self.convert_cost()
            self.remap(map_from='values', map_to='values', time_index_name='vintage')
            self.levelize_costs()
        if self.data is False:
            self.absolute = False
        if self.raw_values is None:
            # if the class is empty, then there is no data for conversion, so the class is considered absolute
            self.absolute = True

    def convert_cost(self):
        """
        convert raw_values to model currency and energy
        """

        self.values = util.unit_convert(self.raw_values, unit_from_den=self.cost_denominator_unit,
                                        unit_to_den=self.unit_to)
        self.values = util.currency_convert(self.values, self.currency_id, self.currency_year_id)

    def levelize_costs(self):
        if self.is_levelized == 1:
            inflation = float(cfg.cfgfile.get('case', 'inflation_rate'))
            rate = self.cost_of_capital - inflation
            if self.is_levelized == 0:
                self.values_level = - np.pmt(rate, self.book_life, 1, 0, 'end') * self.values
                util.convert_age(self, attr_from='values_level', attr_to='values_level', reverse=False,
                                 vintages=self.vintages, years=self.years)
            else:
                self.values_level = self.values.copy()
                util.convert_age(self, attr_from='values_level', attr_to='values_level', reverse=False,
                                 vintages=self.vintages, years=self.years)
                self.values = np.pv(rate, self.book_life, -1, 0, 'end') * self.values
        else:
            util.convert_age(self, reverse=False, vintages=self.vintages, years=self.years)