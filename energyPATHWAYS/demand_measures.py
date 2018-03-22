# -*- coding: utf-8 -*-
"""
Created on Mon Sep 28 09:55:19 2015

@author: Ben
"""
import config as cfg
import pandas as pd
import util
from datamapfunctions import Abstract
import numpy as np
import inspect
from util import DfOper
from shared_classes import StockItem
import logging
import pdb


class FlexibleLoadMeasure(Abstract):
    def __init__(self, id):
        self.id = id
        self.sql_id_table = 'DemandFlexibleLoadMeasures'
        self.sql_data_table = 'DemandFlexibleLoadMeasuresData'
        Abstract.__init__(self, self.id, primary_key='id', data_id_key='parent_id')
        self.input_type = 'intensity'
        self.remap(converted_geography=cfg.demand_primary_geography)
        self.values.sort_index(inplace=True)

    #TODO we should really do something like this to separate the class constructor from the DB
    @classmethod
    def make_from_db(cls, id):
        # read DB here
        return FlexibleLoadMeasure()

    @classmethod
    def make_from_perturbation(cls, perturbation):
        # set up here
        return FlexibleLoadMeasure()

# this class really should be combined with the top flexible load measure class but the constructor is not flexible enough
class FlexibleLoadMeasure2(Abstract):
    def __init__(self, perturbation):
        self.raw_values = self.perturbation_to_raw_values(perturbation)
        self.name = 'perturbation'
        self.interpolation_method = 'nearest'
        self.extrapolation_method = 'nearest'
        self.input_type = 'intensity'
        self.geography = cfg.demand_primary_geography # the perturbations come in already geomapped
        self.remap(converted_geography=cfg.demand_primary_geography)
        org_index = self.values.index.names
        temp = self.values.reset_index()
        start_year = self.raw_values.index.get_level_values('year').min()
        temp.loc[temp['year'] < start_year, 'value'] = 0
        self.values = temp.set_index(org_index).sort()

    def perturbation_to_raw_values(self, perturbation):
        raw_values = perturbation.sales_share_changes['percent_of_load_that_is_flexible'].to_frame()
        raw_values.columns = ['value']
        raw_values.index = raw_values.index.rename('demand_technology', 'demand_technology_id')
        raw_values = raw_values.groupby(level=['demand_technology', cfg.demand_primary_geography, 'year']).mean()
        raw_values = raw_values.reset_index()
        # this is because when we have linked technologies, that technology linkage is not updated with our new tech names
        if perturbation.sales_share_changes['adoption_achieved'].sum()>0:
            raw_values['demand_technology'] = raw_values['demand_technology'].map(perturbation.new_techs)
        raw_values = raw_values.set_index(['demand_technology', cfg.demand_primary_geography, 'year'])
        assert not any(raw_values.values>1)
        return raw_values

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
            self.remap(map_from='raw_values', map_to='values', converted_geography=cfg.demand_primary_geography, time_index_name='year',lower=-100)

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
            logging.debug("incomplete lifetime information entered for technology %s" % self.name)


class ServiceDemandMeasure(Abstract, DemandMeasure):
    def __init__(self, id, cost_of_capital, **kwargs):
        self.id = id
#        self.service_demand_unit = service_demand_unit
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
            logging.debug("incomplete lifetime information entered for technology %s" % self.name)


class FuelSwitchingImpact(Abstract):
    def __init__(self, id, *kwargs):
        self.id = id
        self.sql_id_table = 'DemandFuelSwitchingMeasuresImpact'
        self.sql_data_table = 'DemandFuelSwitchingMeasuresImpactData'
        Abstract.__init__(self, self.id, primary_key='parent_id', data_id_key='parent_id')

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
            self.remap(map_from='raw_values', map_to='values', converted_geography=cfg.demand_primary_geography, time_index_name='year')

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
        Abstract.__init__(self, id, primary_key='parent_id', data_id_key='parent_id')


    def calculate(self, years, vintages, unit_to):
        self.years = years
        self.remap(map_from='raw_values', map_to='values', converted_geography=cfg.demand_primary_geography, time_index=self.years)


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
            self.remap(map_from='values', map_to='values', converted_geography=cfg.demand_primary_geography, time_index_name='vintage')
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