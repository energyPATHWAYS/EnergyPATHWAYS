# -*- coding: utf-8 -*-
"""
Created on Mon Sep 28 10:03:57 2015

@author: Ben
"""

import config as cfg
import util
import pdb
from collections import defaultdict
# from datamapfunctions import DataMapFunctions, Abstract
from shared_classes import Stock
from data_object import DataObject
from .generated import schema
from geomapper import GeoMapper
from unit_converter import UnitConverter

class SubDemand():
    def __init__(self):
        self.in_use_drivers()
        self.projected = False

    def __deepcopy__(self, memo):
        return self

    def in_use_drivers(self):
        """reduces the driver dictionary to in-use drivers"""
        driver_ids = [getattr(self, col) for col in cfg.drivr_col_names if getattr(self, col) is not None]
        denominator_driver_ids = [getattr(self, col) for col in cfg.dnmtr_col_names if getattr(self, col) is not None]

        drivers = driver_ids + denominator_driver_ids
        self.drivers = {k: v for k, v in self.drivers.iteritems() if k in drivers}

    def convert_and_remap(self, unit_type, stock_unit):
        """convert service demand to stock unit for stocks defined as service demand"""
        if unit_type == 'service demand':
            self.remap(map_to='int_values', converted_geography=GeoMapper.demand_primary_geography, fill_timeseries=False)
            self.int_values = UnitConverter.unit_convert(self.int_values, unit_from_num=self.unit, unit_to_num=stock_unit)
            self.unit = stock_unit
            self.current_data_type = self.input_type
            self.projected = False
        else:
            raise ValueError("should not have called this function for this demand stock unit type")

class ServiceDemand(schema.DemandServiceDemands, SubDemand):
    def __init__(self, name, drivers, scenario=None, demand_technology=None):
        self.drivers = drivers
        self.demand_technology = demand_technology
        if scenario:
            self.scenario = scenario
        super(ServiceDemand, self).__init__(subsector=name, scenario=scenario)
        self.init_from_db(name, scenario)

class EnergyDemand(schema.DemandEnergyDemands, SubDemand):
    def __init__(self, name, drivers, scenario=None, demand_technology=None):
        self.drivers = drivers
        self.demand_technology = demand_technology
        if scenario:
            self.scenario = scenario
        super(EnergyDemand, self).__init__(subsector=name, scenario=scenario)
        self.init_from_db(name, scenario)

class DemandStock(schema.DemandStock, Stock):
    def __init__(self, name, drivers, scenario=None):
        super(DemandStock, self).__init__(subsector=name, scenario=scenario)
        self.init_from_db(name, scenario)
        self.drivers = drivers
        self.scenario = scenario
        self.in_use_drivers()
        self.projected = False
        self.efficiency_calculated = False
        self.efficiency = defaultdict(dict)
        self.levelized_costs = defaultdict(dict)
        self.annual_costs = defaultdict(dict)

class ServiceEfficiency(schema.DemandServiceEfficiency):
    def __init__(self, name, service_demand_unit, scenario=None):
        super(ServiceEfficiency, self).__init__(name=name, scenario=None)
        self.init_from_db(name, scenario=None)
        self.service_demand_unit = service_demand_unit
        self.scenario = scenario
        self.input_type = 'intensity'

    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        if self._has_data and self.raw_values is not None:
            self.convert()
            self.remap(map_from='values', converted_geography=GeoMapper.demand_primary_geography, map_to='values', time_index_name='year')
        else:
            raise ValueError("service efficiency data is not complete for subsector %s" % self.id)

    def convert(self):
        """converts energy units to model energy units and service units to subsector service demand units"""
        self.values = UnitConverter.unit_convert(self.raw_values, unit_from_num=self.energy_unit,
                                        unit_from_den=self.denominator_unit,
                                        unit_to_num=cfg.calculation_energy_unit,
                                        unit_to_den=self.service_demand_unit)

class ServiceLink(schema.DemandServiceLink):
    def __init__(self, name):
        super(ServiceLink, self).__init__(name=name, scenario=None)
        self.init_from_db(name, scenario=None)

