# -*- coding: utf-8 -*-
"""
Created on Mon Sep 28 10:01:16 2015

@author: Ben
"""

import config as cfg
import util
from datamapfunctions import Abstract
import numpy as np
import copy
import inspect
from shared_classes import StockItem, SalesShare, SpecifiedStock
import shape
import logging
import pdb


class DemandTechCost(Abstract):
    def __init__(self, tech, sql_id_table, sql_data_table, scenario=None):
        self.id = tech.id
        self.scenario = scenario
        self.book_life = tech.book_life
        self.demand_tech_unit_type = tech.demand_tech_unit_type
        self.unit = tech.unit
        self.tech_time_unit = tech.time_unit
        self.service_demand_unit = tech.service_demand_unit
        self.stock_time_unit = tech.stock_time_unit
        self.cost_of_capital = tech.cost_of_capital
        self.input_type = 'intensity'
        self.sql_id_table = sql_id_table
        self.sql_data_table = sql_data_table
        Abstract.__init__(self, self.id, 'demand_technology_id')


    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        if self.data and self.raw_values is not None:
            self.convert_cost()
            self.remap(map_from='values', map_to='values', time_index_name='vintage')
            self.levelize_costs()
        if self.data is False:
            self.absolute = False
        if self.raw_values is None:
            # if the class is empty, then there is no data for conversion, so the class is considered converted
            self.absolute = True


    def convert_cost(self):
        """
        convert raw_values to model currency and capacity (energy_unit/time_step)
        """
        if self.demand_tech_unit_type == 'service demand':
            if self.tech_time_unit is None:
                self.time_unit = 'year'
            self.values = util.unit_convert(self.raw_values, unit_from_num=self.tech_time_unit,
                                            unit_from_den=self.unit,
                                            unit_to_num=self.stock_time_unit, unit_to_den=self.service_demand_unit)
        else:
            self.values = copy.deepcopy(self.raw_values)
        if self.definition == 'absolute':
            self.values = util.currency_convert(self.values, self.currency_id, self.currency_year_id)
            self.absolute = True
        else:
            self.absolute = False

    def levelize_costs(self):
        if self.definition == 'absolute':
            if hasattr(self, 'is_levelized'):
                inflation = float(cfg.cfgfile.get('case', 'inflation_rate'))
                rate = self.cost_of_capital - inflation
                if self.is_levelized == 0:
                    self.values_level = - np.pmt(rate, self.book_life, 1, 0, 'end') * self.values
                    util.convert_age(self, attr_from='values_level', attr_to='values_level', reverse=False,
                                     vintages=self.vintages, years=self.years)
                else:
                    self.values_level = self.values.copy()
                    util.convert_age(self, attr_from='values_level', attr_to='value_level', reverse=False,
                                     vintages=self.vintages, years=self.years)
                    self.values = np.pv(rate, self.book_life, -1, 0, 'end') * self.values
            else:
                util.convert_age(self, reverse=False, vintages=self.vintages, years=self.years)
        else:
            self.values_level = self.values.copy()


class ParasiticEnergy(Abstract):
    def __init__(self, tech, sql_id_table, sql_data_table, scenario=None, **kwargs):
        self.id = tech.id
        self.scenario = scenario
        self.input_type = 'intensity'
        self.sql_id_table = sql_id_table
        self.sql_data_table = sql_data_table
        self.tech_unit = tech.unit
        self.demand_tech_unit_type = tech.demand_tech_unit_type
        self.service_demand_unit = tech.service_demand_unit
        Abstract.__init__(self, self.id, 'demand_technology_id')


    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        if self.data and self.raw_values is not None:
            self.convert()
            self.remap(map_from='values', map_to='values', time_index_name='vintage')
            util.convert_age(self, reverse=True, vintages=self.vintages, years=self.years)
        if self.data is False:
            self.absolute = False
        if self.raw_values is None:
            # if the class is empty, then there is no data for conversion, so the class is considered absolute
            self.absolute = True

    def convert(self):
        """
        return values from raw_values that are converted to units consistent with output units - energy and annual
        """
        if self.definition == 'absolute':
            if self.time_unit is None:
                self.time_unit = 'year'
            self.values = util.unit_convert(self.raw_values, unit_from_num=self.energy_unit,
                                            unit_from_den=self.time_unit,
                                            unit_to_num=cfg.calculation_energy_unit,
                                            unit_to_den='year')
            if self.demand_tech_unit_type == 'service demand':
                self.values = util.unit_convert(self.values, unit_from_num=self.unit,
                                                unit_to_num=self.service_demand_unit)
            self.absolute = True


        else:
            self.values = self.raw_values.copy()
            self.absolute = False


class DemandTechEfficiency(Abstract):
    def __init__(self, tech, sql_id_table, sql_data_table, scenario=None, **kwargs):
        self.id = tech.id
        self.scenario = scenario
        self.service_demand_unit = tech.service_demand_unit
        self.input_type = 'intensity'
        self.sql_id_table = sql_id_table
        self.sql_data_table = sql_data_table
        Abstract.__init__(self, self.id, 'demand_technology_id')


    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        if self.data and self.raw_values is not None:
            self.convert()
            self.remap(map_from='values', map_to='values', time_index_name='vintage')
            util.convert_age(self, reverse=True, vintages=self.vintages, years=self.years)
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
            if self.is_numerator_service == 1:
                # if the numerator is service, definition has to be flipped in order to make the numerator an energy unit
                self.values = 1 / self.raw_values
                numerator_unit = self.denominator_unit
                denominator_unit = self.numerator_unit
                self.flipped = True
            else:
                self.values = self.raw_values
                numerator_unit = self.numerator_unit
                denominator_unit = self.denominator_unit
                self.flipped = False
            self.values = util.unit_convert(self.values, unit_from_num=numerator_unit,
                                            unit_from_den=denominator_unit,
                                            unit_to_num=cfg.calculation_energy_unit,
                                            unit_to_den=self.service_demand_unit)
            self.absolute = True
        else:
            self.values = self.raw_values.copy()
            self.absolute = False


class DemandTechServiceLink(Abstract):
    """ service link efficiency
    ex. clothes washer hot water efficiency
    """

    def __init__(self, service_link_id, id, sql_id_table, sql_data_table, scenario=None, **kwargs):
        self.service_link_id = service_link_id
        self.id = id
        self.scenario = scenario
        self.input_type = 'intensity'
        self.sql_id_table = sql_id_table
        self.sql_data_table = sql_data_table
        Abstract.__init__(self, self.id, primary_key='id', data_id_key='parent_id')


    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        if self.data and self.raw_values is not None:
            self.remap(map_from='raw_values', map_to='values', time_index_name='vintage')
            util.convert_age(self, reverse=True, vintages=self.vintages, years=self.years)
        if self.data is False:
           self.absolute = False
        if self.raw_values is None:
            # if the class is empty, then there is no data for conversion, so the class is considered converted
            self.absolute = True


class ServiceDemandModifier(Abstract):
    """ technology specified service demand modifier. Replaces calculated modifiers
    based on stock and service/energy demand inputs."""

    def __init__(self, tech, sql_id_table, sql_data_table, scenario=None, **kwargs):
        self.id = tech.id
        self.scenario = scenario
        self.input_type = 'intensity'
        self.sql_id_table = sql_id_table
        self.sql_data_table = sql_data_table
        Abstract.__init__(self, self.id, 'demand_technology_id')

    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        if self.data and self.raw_values is not None:
            self.remap(map_from='raw_values', map_to='values', time_index_name='vintage')
            util.convert_age(self, attr_from='values', attr_to='values', reverse=False, vintages=self.vintages,
                             years=self.years)
        if self.data is False:
            self.absolute = False
        if self.raw_values is None:
            # if the class is empty, then there is no data for conversion, so the class is considered converted
            self.absolute = True


class DemandTechnology(StockItem):
    def __init__(self, id, subsector_id, service_demand_unit, stock_time_unit, cost_of_capital, scenario=None, **kwargs):
        self.id = id
        self.subsector_id = subsector_id
        self.scenario = scenario
        StockItem.__init__(self)
        self.service_demand_unit = service_demand_unit
        self.stock_time_unit = stock_time_unit
        for col, att in util.object_att_from_table('DemandTechs', self.id):
            setattr(self, col, att)
        # if cost_of_capital at the technology level is None, it uses subsector defaults
        if self.cost_of_capital is None:
            self.cost_of_capital = cost_of_capital
        else:
            pass
        # we can have multiple sales shares because sales share may be specific
        # to the transition between two technolog)
        self.reference_sales_shares = {}
        if self.id in util.sql_read_table('DemandSalesData', 'demand_technology_id', return_unique=True, return_iterable=True):
            self.reference_sales_shares[1] = SalesShare(id=self.id, subsector_id=self.subsector_id, reference=True,
                                                        sql_id_table='DemandSales', sql_data_table='DemandSalesData',
                                                        primary_key='subsector_id', data_id_key='demand_technology_id',
                                                        scenario=scenario)
        self.book_life()
        self.add_class()
        self.min_year()
        self.shape = shape.shapes.data[self.shape_id] if self.shape_id is not None else None

    def get_shape(self, default_shape):
        return default_shape.values if self.shape is None else self.shape.values

    def get_max_lead_hours(self):
        return self.max_lead_hours if self.max_lead_hours else None

    def get_max_lag_hours(self):
        return self.max_lag_hours if self.max_lag_hours else None

    def add_sales_share_measures(self):
        self.sales_shares = {}
        sales_share_ids = self.scenario.get_measures('DemandSalesShareMeasures', self.subsector_id, self.id)
        for sales_share_id in sales_share_ids:
            self.sales_shares[sales_share_id] = SalesShare(id=sales_share_id, subsector_id=self.subsector_id,
                                                           reference=False, sql_id_table='DemandSalesShareMeasures',
                                                           sql_data_table='DemandSalesShareMeasuresData',
                                                           primary_key='id', data_id_key='parent_id',
                                                           scenario=self.scenario)

    def add_specified_stock_measures(self):
        self.specified_stocks = {}
        specified_stock_ids = self.scenario.get_measures('DemandStockMeasures', self.subsector_id, self.id)
        for specified_stock_id in specified_stock_ids:
            self.specified_stocks[specified_stock_id] = SpecifiedStock(id=specified_stock_id,
                                                                    sql_id_table='DemandStockMeasures',
                                                                    sql_data_table='DemandStockMeasuresData',
                                                                    scenario=self.scenario)

    def add_service_links(self):
        """adds all technology service links"""
        self.service_links = {}
        service_links = util.sql_read_table('DemandTechsServiceLink', 'service_link_id', return_unique=True,
                                            demand_technology_id=self.id)
        if service_links is not None:
            service_links = util.ensure_iterable_and_not_string(service_links)
            for service_link in service_links:
                id = util.sql_read_table('DemandTechsServiceLink', 'id', return_unique=True, demand_technology_id=self.id,
                                         service_link_id=service_link)
                self.service_links[service_link] = DemandTechServiceLink(self, id, 'DemandTechsServiceLink',
                                                                         'DemandTechsServiceLinkData',
                                                                         scenario=self.scenario)

    def min_year(self):
        """calculates the minimum or start year of data in the technology specification.
        Used to determine start year of subsector for analysis."""

        attributes = vars(self)
        self.min_year = cfg.cfgfile.get('case', 'current_year')
        for att in attributes:
            obj = getattr(self, att)
            if inspect.isclass(type(obj)) and hasattr(obj, '__dict__') and hasattr(obj, 'raw_values'):
                try:
                    att_min_year = min(obj.raw_values.index.levels[util.position_in_index(obj.raw_values, 'vintage')])
                except:
                    att_min_year = self.min_year
                if att_min_year < self.min_year:
                    self.min_year = att_min_year
                else:
                    pass

    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        attributes = vars(self)
        for att in attributes:
            obj = getattr(self, att)
            if inspect.isclass(type(obj)) and hasattr(obj, '__dict__') and hasattr(obj, 'calculate'):
                obj.calculate(self.vintages, self.years)
        for links in self.service_links.values():
            links.calculate(self.vintages, self.years)

    def book_life(self):
        """
        determines book life for measures based on input mean or max/min lifetimes.
        Used for cost levelization
        """
        if self.mean_lifetime is not None:
            self.book_life = getattr(self, 'mean_lifetime')
        elif self.max_lifetime is not None and self.min_lifetime is not None:
            self.book_life = (getattr(self, 'min_lifetime') + getattr(self, 'max_lifetime')) / 2
        else:
            logging.debug("incomplete lifetime information entered for technology %s" % self.name)


    def add_class(self):
        """
        Adds all demand technology classes and uses replace_costs function on
        equivalent costs.

        """
        self.capital_cost_new = DemandTechCost(self, 'DemandTechsCapitalCost', 'DemandTechsCapitalCostNewData', scenario=self.scenario)
        self.capital_cost_replacement = DemandTechCost(self, 'DemandTechsCapitalCost', 'DemandTechsCapitalCostReplacementData', scenario=self.scenario)
        self.installation_cost_new = DemandTechCost(self, 'DemandTechsInstallationCost', 'DemandTechsInstallationCostNewData', scenario=self.scenario)
        self.installation_cost_replacement = DemandTechCost(self, 'DemandTechsInstallationCost', 'DemandTechsInstallationCostReplacementData', scenario=self.scenario)
        self.fuel_switch_cost = DemandTechCost(self, 'DemandTechsFuelSwitchCost', 'DemandTechsFuelSwitchCostData', scenario=self.scenario)
        self.fixed_om = DemandTechCost(self, 'DemandTechsFixedMaintenanceCost', 'DemandTechsFixedMaintenanceCostData', scenario=self.scenario)

        self.efficiency_main = DemandTechEfficiency(self, 'DemandTechsMainEfficiency', 'DemandTechsMainEfficiencyData', scenario=self.scenario)
        self.efficiency_aux = DemandTechEfficiency(self, 'DemandTechsAuxEfficiency', 'DemandTechsAuxEfficiencyData', scenario=self.scenario)
        if hasattr(self.efficiency_main,'definition') and self.efficiency_main.definition == 'absolute':
            self.efficiency_aux.utility_factor = 1 - self.efficiency_main.utility_factor
        self.service_demand_modifier = ServiceDemandModifier(self, 'DemandTechsServiceDemandModifier', 'DemandTechsServiceDemandModifierData', scenario=self.scenario)
        self.parasitic_energy = ParasiticEnergy(self, 'DemandTechsParasiticEnergy', 'DemandTechsParasiticEnergyData', scenario=self.scenario)
        # add service links to service links dictionary
        self.add_service_links()
        self.replace_class('capital_cost_new', 'capital_cost_replacement')
        self.replace_class('installation_cost_new', 'installation_cost_replacement')
        self.replace_class('fuel_switch_cost')
        self.replace_class('fixed_om')


    def replace_class(self, class_a, class_b=None):
        """
        Adds all available cost data to classes. Removes classes with no data and replaces
        them with cost classes containing equivalent data.

        Ex. If capital costs for new installations are input but capital costs for replacement are not,
        it copies capital costs for new to the replacement capital cost class
        """
        # if no class_b is specified, there is no equivalent cost for class_a
        if class_b is None:
            class_a_instance = getattr(self, class_a)
            if class_a_instance.data is False and hasattr(class_a_instance, 'reference_tech_id') is False:
                logging.debug("demand technology %s has no %s cost data" % (self.id, class_a))
        else:
            class_a_instance = getattr(self, class_a)
            class_b_instance = getattr(self, class_b)
            if class_a_instance.data is True and class_a_instance.raw_values is not None and class_b_instance.data is True and class_b_instance.raw_values is not None:
                pass
            elif class_a_instance.data is False and class_b_instance.data is False and \
                            hasattr(class_a_instance, 'reference_tech_id') is False and \
                            hasattr(class_b_instance, 'reference_tech_id') is False:
                logging.debug("demand technology %s has no input data for %s or %s" % (self.id, class_a, class_b))
            elif class_a_instance.data is True and class_a_instance.raw_values is not None and (class_b_instance.data is False or (class_b_instance.data is True and class_b_instance.raw_values is None)):
                setattr(self, class_b, copy.deepcopy(class_a_instance))
            elif (class_a_instance.data is False or (class_a_instance.data is True and class_a_instance.raw_values is None))and class_b_instance.data is True and class_b_instance.raw_values is not None:
                setattr(self, class_a, copy.deepcopy(class_b_instance))