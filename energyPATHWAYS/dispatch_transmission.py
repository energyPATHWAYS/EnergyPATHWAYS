
import util
import numpy as np
from datamapfunctions import Abstract,DataMapFunctions
import copy
import pandas as pd
import math
import config as cfg
import os
from pyomo.opt import SolverFactory, SolverStatus
import csv
import logging
import matplotlib.pyplot as plt
from energyPATHWAYS.outputs import Output
import dispatch_formulation
import pdb
import shape
import helper_multiprocess
import cPickle as pickle
import dispatch_generators
import dispatch_maintenance

class TransmissionSuper(Abstract):
    """loads and cleans the data that allocates demand sectors to dispatch feeders"""
    def __init__(self):
        if self.id is None:
            self._setup_zero_constraints()
        else:
            self._setup_and_validate()

    def _setup_and_validate(self):
        Abstract.__init__(self, self.id, primary_key='id', data_id_key='parent_id')
        if self.raw_values is None:
            self._setup_zero_constraints()
            return

        self._validate_gaus()
        self.values = self.clean_timeseries(attr='raw_values', inplace=False, time_index=cfg.supply_years, time_index_name='year', interpolation_method=self.interpolation_method, extrapolation_method=self.extrapolation_method)

        # fill in any missing combinations of geographies
        self.values = util.reindex_df_level_with_new_elements(self.values, 'geography_from', cfg.dispatch_geographies)
        self.values = util.reindex_df_level_with_new_elements(self.values, 'geography_to', cfg.dispatch_geographies)
        self.values = self.values.fillna(0)
        self.values = self.values.sort()

    def _setup_zero_constraints(self):
        index = pd.MultiIndex.from_product([cfg.supply_years,cfg.dispatch_geographies, cfg.dispatch_geographies], names=['year', 'geography_from', 'geography_to'])
        self.values = pd.DataFrame(0, index=index, columns=['value'])

    def _validate_gaus(self):
        dispatch_geographies = set(cfg.dispatch_geographies)
        geography_from_ids = self.raw_values.index.get_level_values('geography_from')
        if len(set(geography_from_ids) - dispatch_geographies):
            raise ValueError("gau_from_ids {} are found in transmission constraint id {} "
                             "but not found in the dispatch_geographies {}".format(list(set(geography_from_ids) - dispatch_geographies), self.id, cfg.dispatch_geographies))
        geography_to_ids = self.raw_values.index.get_level_values('geography_to')
        if len(set(geography_to_ids) - dispatch_geographies):
            raise ValueError("gau_to_ids {} are found in transmission constraint id {} "
                             "but not found in the dispatch_geographies {}".format(list(set(geography_to_ids) - dispatch_geographies), self.id, cfg.dispatch_geographies))

        if any([name in self.raw_values.index.names for name in ('month', 'hour', 'day_type_id')]):
            print 'Time slices for transmission constraints are not implemented yet, average of all combinations will be used'
            self.raw_values = util.remove_df_levels(self.raw_values,[name for name in ('month', 'hour', 'day_type_id')],agg_function='mean')

    def get_values_as_dict(self, year):
       # capacity = self.values.loc[year].squeeze().to_dict()
        capacity = self.values.loc[year,'value'].to_dict()
        for key in capacity.keys():
            if key[0]==key[1]:
                del capacity[key]
        # tuple needs to be a string in the optimization
        capacity = dict(zip([str((int(key[0]), int(key[1]))) for key in capacity.keys()],
                            capacity.values()))
        return capacity

    def get_values(self, year):
        return self.values.loc[year]

class DispatchTransmissionConstraint(TransmissionSuper):
    """loads and cleans the data that allocates demand sectors to dispatch feeders"""
    def __init__(self, id, scenario):
        self.id = id
        self.scenario = scenario
        self.sql_id_table = 'DispatchTransmissionConstraint'
        self.sql_data_table = 'DispatchTransmissionConstraintData'
        TransmissionSuper.__init__(self)
        self.convert_units()

    def convert_units(self):
        if hasattr(self,'energy_unit'):
            unit_factor = util.unit_convert(1, unit_from_den=self.energy_unit, unit_to_den=cfg.calculation_energy_unit)
            self.values /= unit_factor

class DispatchTransmissionHurdleRate(TransmissionSuper):
    """loads and cleans the data that allocates demand sectors to dispatch feeders"""
    def __init__(self, id, scenario):
        self.id = id
        self.scenario = scenario
        self.sql_id_table = 'DispatchTransmissionConstraint'
        self.sql_data_table = 'DispatchTransmissionHurdleRate'
        TransmissionSuper.__init__(self)
        self.convert_units()

    def convert_units(self):
        if hasattr(self,'energy_unit'):
            unit_factor = util.unit_convert(1, unit_from_den=self.energy_unit, unit_to_den=cfg.calculation_energy_unit)
            self.values *= unit_factor


class DispatchTransmissionCost(TransmissionSuper):
    """loads and cleans the data that allocates demand sectors to dispatch feeders"""
    def __init__(self, id, scenario):
        self.id = id
        self.scenario = scenario
        self.sql_id_table = 'DispatchTransmissionCost'
        self.sql_data_table = 'DispatchTransmissionCostData'
        TransmissionSuper.__init__(self)
        self.convert()
        self.levelize_costs()


    def convert(self):
        """
        convert raw_values to model currency and capacity (energy_unit/time_step)
        """
        self.values = util.currency_convert(self.values, self.currency_id, self.currency_year_id)
        model_energy_unit = cfg.calculation_energy_unit
        model_time_step = cfg.cfgfile.get('case', 'time_step')
        if self.time_unit is not None:
            # if a cost has a time_unit, then the unit is energy and must be converted to capacity
            self.values = util.unit_convert(self.values,
                                            unit_from_den=self.self.capacity_or_energy_unit,
                                            unit_from_num=self.time_unit, unit_to_den=model_energy_unit,
                                            unit_to_num=model_time_step)
        else:
            self.values = util.unit_convert(self.values, unit_from_den=self.capacity_or_energy_unit+"_"+model_time_step,
                                                unit_to_den=model_energy_unit)


    def levelize_costs(self):
        inflation = float(cfg.cfgfile.get('case', 'inflation_rate'))
        rate = self.cost_of_capital - inflation
        self.values_level = - np.pmt(rate, self.lifetime, 1, 0, 'end') * self.values




class DispatchTransmissionLosses(TransmissionSuper):
    """loads and cleans the data that allocates demand sectors to dispatch feeders"""
    def __init__(self, id, scenario):
        self.id = id
        self.scenario = scenario
        self.sql_id_table = 'DispatchTransmissionConstraint'
        self.sql_data_table = 'DispatchTransmissionLosses'
        TransmissionSuper.__init__(self)

class DispatchTransmission():
    def __init__(self, id, scenario):
        self.id = id
        self.constraints = DispatchTransmissionConstraint(id, scenario)
        self.hurdles = DispatchTransmissionHurdleRate(id, scenario)
        self.losses = DispatchTransmissionLosses(id, scenario)
        self.cost = DispatchTransmissionCost(id,scenario)
        self.list_transmission_lines = self.get_transmission_lines()

    def get_transmission_lines(self):
        transmission_lines = []
        for t_from in cfg.dispatch_geographies:
            for t_to in cfg.dispatch_geographies:
                if t_from==t_to:
                    continue
                transmission_lines.append(str((int(t_from), int(t_to))))
        return transmission_lines