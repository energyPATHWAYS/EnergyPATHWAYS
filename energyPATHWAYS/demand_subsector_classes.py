# -*- coding: utf-8 -*-
"""
Created on Mon Sep 28 10:03:57 2015

@author: Ben
"""

from config import cfg
import util
from collections import defaultdict
from datamapfunctions import DataMapFunctions, Abstract
from shared_classes import Stock

class SubDemand(object, DataMapFunctions):
    def __init__(self, id, drivers, sql_id_table, sql_data_table, primary_key, technology_id=None, **kwargs):
        self.id = id
        self.drivers = drivers
        self.technology_id = technology_id
        self.sql_id_table = sql_id_table
        self.sql_data_table = sql_data_table
        self.primary_key = primary_key
        for col, att in util.object_att_from_table(self.sql_id_table, self.id, 'subsector_id'):
            setattr(self, col, att)
        self.in_use_drivers()
        DataMapFunctions.__init__(self, self.primary_key)
        self.read_timeseries_data()
        self.projected = False


    def in_use_drivers(self):
        """reduces the driver dictionary to in-use drivers"""
        driver_ids = [getattr(self, col) for col in cfg.drivr_col_names if getattr(self, col) is not None]
        denominator_driver_ids = [getattr(self, col) for col in cfg.dnmtr_col_names if getattr(self, col) is not None]

        drivers = driver_ids + denominator_driver_ids
        self.drivers = {k: v for k, v in self.drivers.iteritems() if k in drivers}


    def convert_and_remap(self, unit_type, stock_unit):
        """convert service demand to stock unit for stocks defined as service demand"""
        if unit_type == 'service demand':
            self.remap(map_to='int_values',fill_timeseries=False)
            self.int_values = util.unit_convert(self.int_values, unit_from_num=self.unit, unit_to_num=stock_unit)
        else:
            raise ValueError("should not have called this function for this demand stock unit type")


class DemandStock(Stock):
    def __init__(self, id, drivers, sql_id_table='DemandStock', sql_data_table='DemandStockData',
                 primary_key='subsector_id', **kwargs):
        Stock.__init__(self, id, drivers, sql_id_table='DemandStock', sql_data_table='DemandStockData',
                     primary_key='subsector_id', **kwargs)
        self.drivers = drivers
        self.in_use_drivers()
        self.projected = False
        self.efficiency_calculated = False
        self.efficiency = defaultdict(dict)
        self.levelized_costs = defaultdict(dict)
        self.investment = defaultdict(dict)

class ServiceEfficiency(Abstract):
    def __init__(self, id, service_demand_unit, **kwargs):
        self.id = id
        self.service_demand_unit = service_demand_unit
        self.sql_id_table = 'DemandServiceEfficiency'
        self.sql_data_table = 'DemandServiceEfficiencyData'
        self.input_type = 'intensity'
        Abstract.__init__(self, self.id, 'subsector_id')

    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        if self.data and self.empty is False:
            self.convert()
            self.remap(map_from='values', map_to='values', time_index_name='year')
        else:
            raise ValueError("service efficiency data is not complete for subsector %s" % self.id)

    def convert(self):
        """converts energy units to model energy units and service units to subsector service demand units"""
        self.values = util.unit_convert(self.raw_values, unit_from_num=self.energy_unit,
                                        unit_from_den=self.denominator_unit,
                                        unit_to_num=cfg.cfgfile.get('case', 'energy_unit'),
                                        unit_to_den=self.service_demand_unit)

class ServiceLink(object):
    def __init__(self, id):
        self.id = id
        for col, att in util.object_att_from_table('DemandServiceLink', self.id):
            setattr(self, col, att)


