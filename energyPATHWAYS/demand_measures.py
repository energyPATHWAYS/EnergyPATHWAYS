# -*- coding: utf-8 -*-
"""
Created on Mon Sep 28 09:55:19 2015

@author: Ben
"""
import config as cfg
import pandas as pd
import util
import numpy as np
import inspect
from util import DfOper
from shared_classes import StockItem
import logging
import pdb
from energyPATHWAYS.generated import schema
from unit_converter import UnitConverter
from geomapper import GeoMapper
from data_object import DataObject


class FlexibleLoadMeasure(schema.DemandFlexibleLoadMeasures):
    def __init__(self, name, scenario=None):
        schema.DemandFlexibleLoadMeasures.__init__(self, name, scenario=scenario)
        self.init_from_db(name, scenario)
        self.input_type = 'intensity'
        self.remap(converted_geography=GeoMapper.demand_primary_geography, missing_intensity_geos=True)
        self.values.sort_index(inplace=True)
        self.p_max = 1. if self.p_max is None else self.p_max
        self.p_min = 1. if self.p_min is None else self.p_min


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
            self.remap(map_from='raw_values', map_to='values', converted_geography=GeoMapper.demand_primary_geography, time_index_name='year',lower=-100)

    def convert(self):
        if self.input_type == 'total':
            self.values = UnitConverter.unit_convert(self.raw_values, unit_from_num=self.unit,
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
            logging.debug("incomplete lifetime information entered for technology %s" % self.name)


class ServiceDemandMeasure(schema.DemandServiceDemandMeasures, DemandMeasure):
    def __init__(self, name, cost_of_capital, scenario=None):
        self.name = name
        schema.DemandServiceDemandMeasures.__init__(self, name, scenario=scenario)
        self.init_from_db(name, scenario)
        DemandMeasure.__init__(self)
        self.cost_of_capital = cost_of_capital
        self.calculate_book_life()
        self.cost = ServiceDemandMeasuresCost(name, self.cost_of_capital, self.book_life)


class EnergyEfficiencyMeasure(schema.DemandEnergyEfficiencyMeasures, DemandMeasure):
    def __init__(self, name, cost_of_capital, scenario=None):
        self.name = name
        schema.DemandEnergyEfficiencyMeasures.__init__(self, name, scenario=scenario)
        self.init_from_db(name, scenario)
        DemandMeasure.__init__(self)
        self.calculate_book_life()
        self.cost_of_capital = cost_of_capital
        self.cost = EnergyEfficiencyMeastureCost(name, self.cost_of_capital, self.book_life)


class FuelSwitchingMeasure(schema.DemandFuelSwitchingMeasures, StockItem):
    def __init__(self, name, cost_of_capital, scenario=None):
        self.name = name
        schema.DemandFuelSwitchingMeasures.__init__(self, name, scenario=scenario)
        self.init_from_db(name, scenario)
        StockItem.__init__(self)
        self.calculate_book_life()
        self.cost_of_capital = cost_of_capital
        self.impact = FuelSwitchingImpact(self.name)
        self.energy_intensity = FuelSwitchingEnergyIntensity(self.name)
        self.cost = FuelSwitchingMeasuresCost(self.name, self.cost_of_capital, self.book_life)

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
            logging.debug("incomplete lifetime information entered for technology %s" % self.name)


class FuelSwitchingImpact(schema.DemandFuelSwitchingMeasuresImpact):
    def __init__(self, name, scenario=None):
        self.name = name
        schema.DemandFuelSwitchingMeasuresImpact.__init__(self, name, scenario=scenario)
        self.init_from_db(name, scenario)

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
            self.remap(map_from='raw_values', map_to='values', converted_geography=GeoMapper.demand_primary_geography, time_index_name='year')

    def convert(self):
        if self.input_type == 'total':
            self.values = UnitConverter.unit_convert(self.raw_values, unit_from_num=self.unit,
                                            unit_to_num=self.unit_to)
        else:
            pass


class FuelSwitchingEnergyIntensity(schema.DemandFuelSwitchingMeasuresEnergyIntensity):
    def __init__(self, name, scenario=None):
        self.name = name
        schema.DemandFuelSwitchingMeasuresEnergyIntensity.__init__(self, name, scenario=scenario)
        self.init_from_db(name, scenario)
        self.input_type = 'intensity'

    def calculate(self, years, vintages, unit_to):
        self.years = years
        try:
            self.remap(map_from='raw_values', map_to='values', converted_geography=GeoMapper.demand_primary_geography, time_index=self.years)
        except:
            pdb.set_trace()


class DemandMeasureCost(DataObject):
    def __init__(self, cost_of_capital, book_life):
        self.book_life = book_life
        self.input_type = 'intensity'
        if hasattr(self, 'cost_of_capital'):
            if self.cost_of_capital is None:
                self.cost_of_capital = cost_of_capital

    def calculate(self, vintages, years, unit_to):
        self.vintages = vintages
        self.years = years
        self.unit_to = unit_to
        if self._has_data and self.raw_values is not None:
            self.convert_cost()
            self.remap(map_from='values', map_to='values', converted_geography=GeoMapper.demand_primary_geography, time_index_name='vintage')
            self.levelize_costs()
        if self._has_data is False:
            self.absolute = False
        if self.raw_values is None:
            # if the class is empty, then there is no data for conversion, so the class is considered absolute
            self.absolute = True

    def convert_cost(self):
        """
        convert raw_values to model currency and energy
        """

        self.values = UnitConverter.unit_convert(self.raw_values, unit_from_den=self.cost_denominator_unit,
                                        unit_to_den=self.unit_to)
        self.values = UnitConverter.currency_convert(self.values, self.currency, self.currency_year)

    def levelize_costs(self):
        if self.is_levelized == 1:
            inflation = cfg.getParamAsFloat('inflation_rate', section='UNITS')
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

class EnergyEfficiencyMeastureCost(schema.DemandEnergyEfficiencyMeasuresCost, DemandMeasureCost):
    def __init__(self, name, cost_of_capital, book_life, scenario=None):
        self.name = name
        schema.DemandEnergyEfficiencyMeasuresCost.__init__(self, name, scenario=scenario)
        self.init_from_db(name, scenario)
        DemandMeasureCost.__init__(self, cost_of_capital, book_life)

class FuelSwitchingMeasuresCost(schema.DemandFuelSwitchingMeasuresCost, DemandMeasureCost):
    def __init__(self, name, cost_of_capital, book_life, scenario=None):
        self.name = name
        schema.DemandFuelSwitchingMeasuresCost.__init__(self, name, scenario=scenario)
        self.init_from_db(name, scenario)
        DemandMeasureCost.__init__(self, cost_of_capital, book_life)

class ServiceDemandMeasuresCost(schema.DemandServiceDemandMeasuresCost, DemandMeasureCost):
    def __init__(self, name, cost_of_capital, book_life, scenario=None):
        self.name = name
        schema.DemandServiceDemandMeasuresCost.__init__(self, name, scenario=scenario)
        self.init_from_db(name, scenario)
        DemandMeasureCost.__init__(self, cost_of_capital, book_life)