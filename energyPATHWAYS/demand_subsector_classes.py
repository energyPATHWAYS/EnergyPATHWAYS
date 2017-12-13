# -*- coding: utf-8 -*-
"""
Created on Mon Sep 28 10:03:57 2015

@author: Ben
"""

import config as cfg
import util
from collections import defaultdict
from datamapfunctions import DataMapFunctions, Abstract
from shared_classes import Stock
from . import schema

class EnergyDemands(schema.DemandEnergyDemands):
    def __init__(self, name, drivers, scenario=None, demand_technology_id=None):
        super(EnergyDemands, self).__init__(name, scenario)
        self.init_from_db(name, scenario)

        self.drivers = drivers
        self.demand_technology_id = demand_technology_id

        # TODO: move this to DataObject.__init__?
        self.index_levels = self.df_index_names = self.column_names = None
        self.raw_values = self.create_raw_values()

        self.in_use_drivers()
        self.projected = False

    def in_use_drivers(self):
        """
        Reduces the driver dictionary to in-use drivers
        """
        possible_drivers = [self.driver_1, self.driver_2, self.driver_denominator_1, self.driver_denominator_2]
        driver_names = filter(None, possible_drivers)

        # TODO: this should eventually use Demand.drivers_new, which keys on name rather than ID
        self.drivers = {id : obj for id, obj in self.drivers.iteritems() if obj.name in driver_names}
        #self.drivers = {k.id: self.drivers[k] for k in drivers + denom_drivers}

class SubDemand(object, DataMapFunctions):
    def __init__(self, id, drivers, sql_id_table, sql_data_table, scenario=None, demand_technology_id=None):
        self.id = id
        self.drivers = drivers
        self.demand_technology_id = demand_technology_id
        self.sql_id_table = sql_id_table
        self.sql_data_table = sql_data_table
        if scenario:
            self.scenario = scenario
        self.primary_key = 'subsector_id'
        self.data_id_key = 'subsector_id'
        for col, att in util.object_att_from_table(self.sql_id_table, self.id, 'subsector_id'):
            setattr(self, col, att)
        self.in_use_drivers()
        DataMapFunctions.__init__(self, self.data_id_key)
        self.read_timeseries_data()
        self.projected = False

    def __deepcopy__(self, memo):
        return self

    def in_use_drivers(self):
        """reduces the driver dictionary to in-use drivers"""
        driver_ids = [getattr(self, col) for col in cfg.drivr_col_names if getattr(self, col) is not None]
        denominator_driver_ids = [getattr(self, col) for col in cfg.dnmtr_col_names if getattr(self, col) is not None]

        drivers = driver_ids + denominator_driver_ids

        # RJP: simpler and faster than searching for k in drivers repeatedly
        self.drivers = {k: self.drivers[k] for k in drivers}
        # self.drivers = {k: v for k, v in self.drivers.iteritems() if k in drivers}


    def convert_and_remap(self, unit_type, stock_unit):
        """convert service demand to stock unit for stocks defined as service demand"""
        if unit_type == 'service demand':
            self.remap(map_to='int_values',fill_timeseries=False)
            self.int_values = util.unit_convert(self.int_values, unit_from_num=self.unit, unit_to_num=stock_unit)
            self.unit = stock_unit
            self.current_data_type = self.input_type
            self.projected = False
        else:
            raise ValueError("should not have called this function for this demand stock unit type")


class DemandStock(Stock):
    def __init__(self, id, drivers, sql_id_table='DemandStock', sql_data_table='DemandStockData', primary_key='subsector_id', scenario=None, **kwargs):
        Stock.__init__(self, id, drivers, sql_id_table='DemandStock', sql_data_table='DemandStockData', primary_key='subsector_id', scenario=scenario, **kwargs)
        self.drivers = drivers
        self.in_use_drivers()
        self.projected = False
        self.efficiency_calculated = False
        self.efficiency = defaultdict(dict)
        self.levelized_costs = defaultdict(dict)
        self.annual_costs= defaultdict(dict)

class ServiceEfficiency(Abstract):
    def __init__(self, id, service_demand_unit, scenario=None, **kwargs):
        self.id = id
        self.service_demand_unit = service_demand_unit
        self.scenario = scenario
        self.sql_id_table = 'DemandServiceEfficiency'
        self.sql_data_table = 'DemandServiceEfficiencyData'
        self.input_type = 'intensity'
        Abstract.__init__(self, self.id, 'subsector_id')

    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        if self.data and self.raw_values is not None:
            self.convert()
            self.remap(map_from='values', map_to='values', time_index_name='year')
        else:
            raise ValueError("service efficiency data is not complete for subsector %s" % self.id)

    def convert(self):
        """converts energy units to model energy units and service units to subsector service demand units"""
        self.values = util.unit_convert(self.raw_values, unit_from_num=self.energy_unit,
                                        unit_from_den=self.denominator_unit,
                                        unit_to_num=cfg.calculation_energy_unit,
                                        unit_to_den=self.service_demand_unit)

class ServiceLink(Abstract):
    def __init__(self, id):
        self.id = id
        for col, att in util.object_att_from_table('DemandServiceLink', self.id):
            setattr(self, col, att)


