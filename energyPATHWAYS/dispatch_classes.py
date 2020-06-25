# -*- coding: utf-8 -*-
"""
Created on Mon Feb 15 22:06:19 2016

@author: Ben
"""
import util
import numpy as np
import copy
import pandas as pd
import config as cfg
from config import getParam, getParamAsBoolean
import os
from pyomo.opt import SolverFactory
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
import dispatch_transmission
import dispatch_long_duration
from pyomo.opt import TerminationCondition
from pyomo.environ import Constraint
from unit_converter import UnitConverter

from geomapper import GeoMapper
from energyPATHWAYS.generated import schema

class DispatchFeederAllocation(schema.DispatchFeedersAllocation):
    """loads and cleans the data that allocates demand sectors to dispatch feeders"""
    def __init__(self, name, scenario=None):
        super(DispatchFeederAllocation, self).__init__(name, scenario=scenario)
        self.init_from_db(name, scenario)

        if self.raw_values is not None:
            assert (self.raw_values.groupby(level=['year', self.geography]).sum() == 1).all().all()
            self.remap(map_from='raw_values', map_to='values', converted_geography=getParam('demand_primary_geography'))
            self.values.sort_index(inplace=True)

class DispatchNodeConfig(schema.DispatchNodeConfig):
    def __init__(self, name, scenario=None):
        super(DispatchNodeConfig, self).__init__(name, scenario=scenario)
        self.init_from_db(name, scenario=scenario)

        # for col, att in util.object_att_from_table(self.sql_id_table, id, primary_key='supply_node_id'):
        #     setattr(self, col, att)

def all_results_to_list(instance):
    return {'Charge':storage_result_to_list(instance.Charge),
            'Transmission_Flows':storage_result_to_list(instance.Transmit_Power),
            'Storage_Provide_Power': storage_result_to_list(instance.Storage_Provide_Power),
            'Generator_Provide_Power': storage_result_to_list(instance.Generation_Provide_Power),
            'LD_Provide_Power':storage_result_to_list(instance.LD_Provide_Power),
            'Flexible_Load':flexible_load_result_to_list(instance.Flexible_Load)}

def storage_result_to_list(charge_or_discharge):
    items = charge_or_discharge.iteritems()
    lists = [[string for string in key[0].replace("')", '').replace("('", '').split("', '")] + [key[1]] + [value.value] for key, value in items]
    return lists


def flexible_load_result_to_list(flexible_load):
    items = flexible_load.iteritems()
    lists = [key + (value.value,) for key, value in items]
    return lists


def ld_result_to_list(provide_power):
    items = provide_power.iteritems()
    ld_list = [[key[0]] + [key[1]] + [value.value] for key, value in items]
    return ld_list


class DispatchSuper(object):
    def __init__(self, dispatch_feeders, dispatch_geography, dispatch_geographies):
        pass

    @classmethod
    def from_supply_obj(cls, supply):
        # most of the data setup is probably universal and can go here
        pass

    @classmethod
    def from_pickle(cls, path):
        # most of the data setup is probably universal and can go here
        pass

    def write_self(self, path):
        # important function that will allow us to write the data and then change functions and then test
        pass

class SeriesHourlyDispatch(DispatchSuper):
    def __init__(self):
        pass

    def calculate(self):
        # here is where we can put the calculations
        pass

    def get_output_X(self):
        # pattern we can use for getting outputs back to supply, some of this could go into the super class, but much is likely specific
        pass

class Dispatch(object):
    def __init__(self, dispatch_feeders, dispatch_geography, dispatch_geographies, scenario):
        # Todo, this doesn't seem necessary because we can put these things in the config
        # #TODO replace 1 with a config parameter
        # for col, att in util.object_att_from_table('DispatchConfig', 1):
        #     setattr(self, col, att)
        self.node_config_dict = dict()

        for supply_node in util.csv_read_table('DispatchNodeConfig', 'supply_node', return_iterable=True):
            self.node_config_dict[supply_node] = DispatchNodeConfig(supply_node)

        self.set_dispatch_orders()
        # self.dispatch_window_dict = dict(util.csv_read_table('DispatchWindows')) # todo doesn't seem used
        self.curtailment_cost = UnitConverter.unit_convert(0, unit_from_den='megawatt_hour',unit_to_den=cfg.calculation_energy_unit)
        self.unserved_capacity_cost = UnitConverter.unit_convert(10000.0, unit_from_den='megawatt_hour',unit_to_den=cfg.calculation_energy_unit)
        self.dist_net_load_penalty = UnitConverter.unit_convert(75000.0, unit_from_den='megawatt_hour',unit_to_den=cfg.calculation_energy_unit)

        # this bulk penalty is mostly for transmission
        self.bulk_net_load_penalty = UnitConverter.unit_convert(5000.0, unit_from_den='megawatt_hour',unit_to_den=cfg.calculation_energy_unit)
        self.ld_upward_imbalance_penalty = UnitConverter.unit_convert(150.0, unit_from_den='megawatt_hour',unit_to_den=cfg.calculation_energy_unit)
        self.ld_downward_imbalance_penalty = UnitConverter.unit_convert(50.0, unit_from_den='megawatt_hour',unit_to_den=cfg.calculation_energy_unit)
        self.dispatch_feeders = dispatch_feeders
        self.feeders = ['bulk'] + dispatch_feeders
        self.dispatch_geography = dispatch_geography
        self.dispatch_geographies = dispatch_geographies
        self.stdout_detail = getParamAsBoolean('stdout_detail', 'opt')
        self.transmission = dispatch_transmission.DispatchTransmission(cfg.transmission_constraint, scenario)

        self.solve_kwargs = {"keepfiles": False, "tee": False}

    def set_dispatch_orders(self):
        order = [x.dispatch_order for x in self.node_config_dict.values() if x.optimized!=True]
        nodes = [x for x in self.node_config_dict.keys() if self.node_config_dict[x].optimized!=True]
        order_index = np.argsort(order)
        self.heuristic_dispatch_order = [nodes[i] for i in order_index]
        order = [x.dispatch_order for x in self.node_config_dict.values() if x.optimized==True]
        nodes = [x for x in self.node_config_dict.keys() if self.node_config_dict[x].optimized==True]
        order_index = np.argsort(order)
        self.long_duration_dispatch_order = [nodes[i] for i in order_index]

    def set_year(self, year):
        self.year = year

    def set_timeperiods(self):
        """sets optimization periods based on selection of optimization hours
        in the dispatch configuration
        sets:
          period_hours = range from 1 to the number of opt_hours
          periods = range from 1 to the maximum number of periods (i.e. 8760/period_hours)
          period_timepoints = dictionary with keys of period and values of period hours
          period_flex_load_timepoints = dictionary with keys of period and values of a nested dictionary with the keys of period_hours and the values of those period hours offset
          by the flexible_load_constraint_offset configuration parameter
        """
        if hasattr(self,'hours'):
            return
        self.num_hours = len(shape.Shapes.get_active_dates_index())
        self.hours = range(self.num_hours)
        num_periods = int(round(self.num_hours / float(cfg.opt_period_length)))
        self.periods = range(num_periods)
        split_hours = [list(a) for a in np.array_split(self.hours, num_periods)] # splits into roughly equal lengths
        self.period_lengths = dict(zip(self.periods, [len(a) for a in split_hours]))
        self.period_timepoints = dict(zip(self.periods, split_hours))
        self.period_previous_timepoints = dict(zip(self.periods, [dict(zip(*(a, util.rotate(a,1)))) for a in split_hours]))
        self.period_repeated = util.flatten_list([[p]*self.period_lengths[p] for p in self.periods])

    def set_losses(self, transmission_losses, distribution_losses):
        self.t_and_d_losses = dict()
        for geography in self.dispatch_geographies:
            for feeder in self.feeders:
                if feeder == 'bulk':
                    self.t_and_d_losses[(geography,feeder)] = transmission_losses.loc[geography,:].values[0]
                else:
                    self.t_and_d_losses[(geography,feeder)] = util.df_slice(distribution_losses, [geography,feeder],[self.dispatch_geography, 'dispatch_feeder']).values[0][0] * transmission_losses.loc[geography,:].values[0]

    def set_thresholds(self,distribution_stock, transmission_stock):
        self.bulk_net_load_thresholds = dict()
        self.dist_net_load_thresholds = dict()
        for geography in self.dispatch_geographies:
            self.bulk_net_load_thresholds[geography] = transmission_stock.loc[geography].values[0]
            for feeder in self.feeders:
                if feeder == 'bulk':
                    self.dist_net_load_thresholds[(geography,feeder)] = 0
                else:
                    self.dist_net_load_thresholds[(geography,feeder)] =  util.df_slice(distribution_stock,[geography, feeder],[self.dispatch_geography, 'dispatch_feeder']).values[0][0]

    def set_opt_loads(self, distribution_load, distribution_flex_load, distribution_gen, bulk_load, bulk_gen, dispatched_bulk_load, bulk_net_load, active_thermal_dispatch_df):
        self.distribution_load_input, self.distribution_flex_load_input, self.distribution_gen_input, self.bulk_load_input, self.bulk_gen_input, self.dispatched_bulk_load_input = distribution_load, distribution_flex_load, distribution_gen, bulk_load, bulk_gen, dispatched_bulk_load
        self.precision_adjust = dict(zip(self.dispatch_geographies,[x[0] for x in distribution_load.groupby(level=self.dispatch_geography).max().values/1E6]))
        self.set_opt_distribution_net_loads(distribution_load, distribution_flex_load, distribution_gen)
        self.set_opt_bulk_net_loads(bulk_load, bulk_gen, dispatched_bulk_load, bulk_net_load, active_thermal_dispatch_df)

    def _convert_weather_datetime_to_hour(self, input_df):
        df = input_df.copy() # necessary to avoid pass by reference errors
        repeats = int(df.size / self.num_hours)
        df['hour'] = self.hours * repeats
        df['period'] = self.period_repeated * repeats
        df = df.set_index(['period', 'hour'], append=True)
        df = df.reset_index(level='weather_datetime', drop=True)
        level_order = ['timeshift_type', 'period', self.dispatch_geography, 'hour', 'dispatch_feeder']
        df = df.reorder_levels([l for l in level_order if l in df.index.names])
        return df.sort_index().squeeze() # squeeze turns it into a series, which is better when using the to_dict method

    def _convert_ld_weather_datetime_to_hour(self, input_df):
        df = input_df.copy() # necessary to avoid pass by reference errors
        repeats = int(df.size / self.num_hours)
        df['hour'] = self.hours * repeats
        df = df.set_index(['hour'], append=True)
        df = df.reset_index(level='weather_datetime', drop=True)
        level_order = [self.dispatch_geography, 'hour']
        df = df.reorder_levels([l for l in level_order if l in df.index.names])
        return df.sort_index().squeeze() # squeeze turns it into a series, which is better when using the to_dict method

    def _add_dispatch_feeder_level_zero(self, df):
        # if we already have dispatch feeder zero, we shouldn't add it
        if 'dispatch_feeder' in df.index.names and 'bulk' in df.index.get_level_values('dispatch_feeder'):
            return df
        levels = [list(l) if n != 'dispatch_feeder' else ['bulk'] for l, n in zip(df.index.levels, df.index.names)]
        index = pd.MultiIndex.from_product(levels, names=df.index.names)
        return pd.concat((df, pd.DataFrame(0.0, columns=df.columns, index=index))).sort_index()

    def _timeseries_to_dict(self, df):
        return dict(zip(self.periods, [df.xs(p, level='period').to_dict() for p in self.periods]))

    def _ensure_feasible_flexible_load(self, cum_df):
        # we have flexible load
        active_timeshift_types = tuple(sorted(set(cum_df.index.get_level_values('timeshift_type'))))
        if active_timeshift_types == ('advanced','delayed','native'):
            unstacked = cum_df.unstack(level='timeshift_type')
            unstacked['delayed'] = unstacked[['delayed','native']].min(axis=1)
            unstacked['advanced'] = unstacked[['native','advanced']].max(axis=1)
            cum_df = unstacked.stack().reorder_levels(['timeshift_type', 'period', self.dispatch_geography, 'hour', 'dispatch_feeder'])
            return cum_df.sort_index()
        else:
            return cum_df

    def set_opt_distribution_net_loads(self, distribution_load, distribution_flex_load, distribution_gen):
        #[period][(geography,timepoint,feeder)]
        distribution_load = self._add_dispatch_feeder_level_zero(distribution_load)
        distribution_load = self._convert_weather_datetime_to_hour(distribution_load)
        self.distribution_load = self._timeseries_to_dict(distribution_load)

        distribution_gen = self._add_dispatch_feeder_level_zero(distribution_gen)
        distribution_gen = self._convert_weather_datetime_to_hour(distribution_gen)
        self.distribution_gen = self._timeseries_to_dict(distribution_gen)

        self.has_flexible_load = False if distribution_flex_load is None else True
        if self.has_flexible_load:
            distribution_flex_load = self._add_dispatch_feeder_level_zero(distribution_flex_load)
            distribution_flex_load = self._convert_weather_datetime_to_hour(distribution_flex_load)
            cum_distribution_load = distribution_flex_load.groupby(level=['timeshift_type', self.dispatch_geography, 'dispatch_feeder']).cumsum()
            cum_distribution_load = self._ensure_feasible_flexible_load(cum_distribution_load)

            self.native_flex = self._timeseries_to_dict(distribution_flex_load.xs('native', level='timeshift_type'))
            self.native_cumulative_flex = self._timeseries_to_dict(cum_distribution_load.xs('native', level='timeshift_type'))
            self.min_cumulative_flex = self._timeseries_to_dict(cum_distribution_load.xs('delayed', level='timeshift_type'))
            self.max_cumulative_flex = self._timeseries_to_dict(cum_distribution_load.xs('advanced', level='timeshift_type'))

    def set_max_min_flex_loads(self, flex_pmin, flex_pmax):
        self.flex_load_penalty_short = UnitConverter.unit_convert(cfg.getParamAsFloat('flex_load_penalty_short', 'opt'), unit_from_den='megawatt_hour', unit_to_den=cfg.calculation_energy_unit)
        self.flex_load_penalty_long = UnitConverter.unit_convert(cfg.getParamAsFloat('flex_load_penalty_long', 'opt'), unit_from_den='megawatt_hour', unit_to_den=cfg.calculation_energy_unit)
        if self.has_flexible_load:
            self.max_flex_load = flex_pmax.squeeze().to_dict()
            self.min_flex_load = flex_pmin.squeeze().to_dict()

    def set_opt_bulk_net_loads(self, bulk_load, bulk_gen, dispatched_bulk_load, bulk_net_load, active_thermal_dispatch_df):
        bulk_load = self._convert_weather_datetime_to_hour(bulk_load)
        bulk_gen = self._convert_weather_datetime_to_hour(bulk_gen)
        dispatched_bulk_load = self._convert_weather_datetime_to_hour(dispatched_bulk_load)
        bulk_net_load = util.remove_df_levels(bulk_net_load,'year')
        bulk_net_load = self._convert_ld_weather_datetime_to_hour(bulk_net_load)
        self.bulk_load = self._timeseries_to_dict(bulk_load)
        self.dispatched_bulk_load = self._timeseries_to_dict(dispatched_bulk_load)
        self.bulk_gen = self._timeseries_to_dict(bulk_gen)
        thermal_unstacked = active_thermal_dispatch_df.squeeze().unstack('IO')
        must_run_sum = thermal_unstacked[thermal_unstacked['must_run']==1]['capacity'].groupby(level=GeoMapper.dispatch_geography).sum().to_frame()
        # this includes must run generation
        self.ld_bulk_net_load_df = util.DfOper.subt((util.remove_df_levels(bulk_net_load,'period').to_frame(), must_run_sum))
        self.ld_bulk_net_load = self.ld_bulk_net_load_df.squeeze().to_dict()

    def set_average_net_loads(self, total_net_load):
        df = total_net_load.copy()
        df['period'] = util.flatten_list([[p]*self.period_lengths[p] for p in self.periods])*len(GeoMapper.dispatch_geographies)
        df = df.set_index(['period'], append=True)
        self.period_net_load = df.groupby(level=[self.dispatch_geography, 'period']).sum().squeeze().to_dict()
        self.average_net_load = df.groupby(level=[self.dispatch_geography]).sum()/float(len(self.periods))
        self.average_net_load = self.average_net_load[self.average_net_load.columns[0]].to_dict()

    def set_technologies(self,storage_capacity_dict, storage_efficiency_dict, thermal_dispatch_df):
      """prepares storage technologies for dispatch optimization
        args:
            storage_capacity_dict = dictionary of storage discharge capacity and storage discharge duration
            storage_efficiency_dict = dictionary of storage efficiency
        sets:
            capacity = dictionary of storage discharge capacity with keys of dispatch period and unique tech_dispatch_id, a tuple of dispatch_geography,zone,feeder,and technology
            duration = dictionary of storage discharge duration with keys of dispatch period and unique tech_dispatch_id, a tuple of dispatch_geography,zone,feeder,and technology
            feeder = dictionary of feeder ids with keys of dispatch period and unique tech_dispatch_id, a tuple of dispatch_geography,zone,feeder,and technology
            region = dictionary of dispatch regions with keys of dispatch period and unique tech_dispatch_id, a tuple of dispatch_geography,zone,feeder,and technology
            charging_efficiency = dictionary of storage charging efficiency with keys of unique tech_dispatch_id, a tuple of dispatch_geography,zone,feeder,and technology
            discharging_efficiency = dictionary of storage discharging efficiency (equal to charging efficiency) with keys of unique tech_dispatch_id, a tuple of dispatch_geography,zone,feeder,and technology
            large_storage = dictionary of binary flags indicating whether a resource is considered large storage with keys of unique tech_dispatch_id, a tuple of dispatch_geography,zone,feeder,and technology
      """
      self.geography= dict()
      self.min_capacity = dict()
      self.capacity = dict()
      self.charging_efficiency = dict()
      self.discharging_efficiency = dict()
      self.duration = dict()
      self.feeder = dict()
      self.large_storage = dict()
      self.energy = dict()
      self.storage_technologies = []
      self.alloc_technologies = []
      self.alloc_geography = dict()
      self.alloc_capacity = dict()
      self.alloc_energy = dict()
      self.alloc_charging_efficiency = dict()
      self.alloc_discharging_efficiency = dict()
      self.generation_technologies = []
      self.variable_costs = {}
      self.annual_ld_energy= util.recursivedict()
      self.ld_geography = util.recursivedict()
      self.ld_capacity = util.recursivedict()
      self.ld_min_capacity = util.recursivedict()
      self.ld_feeder = util.recursivedict()
      for dispatch_geography in storage_capacity_dict['power'].keys():
          for zone in storage_capacity_dict['power'][dispatch_geography].keys():
             for feeder in storage_capacity_dict['power'][dispatch_geography][zone].keys():
                 for tech in storage_capacity_dict['power'][dispatch_geography][zone][feeder].keys():
                     tech_dispatch_id = str((dispatch_geography,zone,feeder,tech))
                     self.storage_technologies.append(tech_dispatch_id)
                     self.geography[tech_dispatch_id ] = dispatch_geography
                     self.min_capacity[tech_dispatch_id] = 0
                     self.capacity[tech_dispatch_id] = storage_capacity_dict['power'][dispatch_geography][zone][feeder][tech]
                     self.duration[tech_dispatch_id] = storage_capacity_dict['duration'][dispatch_geography][zone][feeder][tech]
                     self.energy[tech_dispatch_id] = self.capacity[tech_dispatch_id] * self.duration[tech_dispatch_id]
                     if self.duration[tech_dispatch_id] >= cfg.getParamAsInt('large_storage_duration', section='opt'):
                        self.alloc_technologies.append(tech_dispatch_id)
                        self.large_storage[tech_dispatch_id] = 1
                        self.alloc_geography[tech_dispatch_id] = dispatch_geography
                        self.alloc_capacity[tech_dispatch_id] = self.capacity[tech_dispatch_id] * len(self.hours)
                        self.alloc_energy[tech_dispatch_id] = self.energy[tech_dispatch_id]
                        x = 1/np.sqrt(storage_efficiency_dict[dispatch_geography][zone][feeder][tech])
                        if not np.isfinite(x):
                            x = 1
                        self.alloc_charging_efficiency[tech_dispatch_id] = x
                        self.alloc_discharging_efficiency[tech_dispatch_id] = copy.deepcopy(self.alloc_charging_efficiency)[tech_dispatch_id]
                     else:
                        self.large_storage[tech_dispatch_id] = 0
                     x = 1/np.sqrt(storage_efficiency_dict[dispatch_geography][zone][feeder][tech])
                     if not np.isfinite(x):
                         x = 1
                     self.charging_efficiency[tech_dispatch_id] = x
                     self.discharging_efficiency[tech_dispatch_id] = copy.deepcopy(self.charging_efficiency)[tech_dispatch_id]
                     self.feeder[tech_dispatch_id] = feeder
      for dispatch_geography in GeoMapper.dispatch_geographies:
          self.set_gen_technologies(dispatch_geography,thermal_dispatch_df)
      self.convert_all_to_period()
      self.set_transmission_energy()

    def set_transmission_energy(self):
        self.tx_energy_dict = util.recursivedict()
        tx_dict = self.transmission.constraints.get_values_as_dict(self.year)
        for t in tx_dict.keys():
            for p in self.period_lengths.keys():
                self.tx_energy_dict[(t,p)] = tx_dict[t] * self.period_lengths[p]
        

    def convert_all_to_period(self):
      self.min_capacity = self.convert_to_period(self.min_capacity)
      self.capacity = self.convert_to_period(self.capacity)
      self.duration = self.convert_to_period(self.duration)
      self.energy = self.convert_to_period(self.energy)
      self.feeder = self.convert_to_period(self.feeder)
      self.geography = self.convert_to_period(self.geography)

    def set_gen_technologies(self, geography, thermal_dispatch_df):
        pmax = np.array(util.df_slice(thermal_dispatch_df,['capacity',geography],['IO',self.dispatch_geography]).values).T[0]
        marginal_cost = np.array(util.df_slice(thermal_dispatch_df,['cost',geography],['IO',self.dispatch_geography]).values).T[0]
        MORs = np.array(util.df_slice(thermal_dispatch_df,['maintenance_outage_rate',geography],['IO',self.dispatch_geography]).values).T[0]
        FORs = np.array(util.df_slice(thermal_dispatch_df,['forced_outage_rate',geography],['IO',self.dispatch_geography]).values).T[0]
        must_run = np.array(util.df_slice(thermal_dispatch_df,['must_run',geography],['IO',self.dispatch_geography]).values).T[0]
        clustered_dict = dispatch_generators.cluster_generators(n_clusters = cfg.getParamAsInt('generator_steps', 'opt'), pmax=pmax, marginal_cost=marginal_cost, FORs=FORs,
                                                                MORs=MORs, must_run=must_run, pad_stack=False, zero_mc_4_must_run=True)
        generator_numbers = range(len(clustered_dict['derated_pmax']))
        for number in generator_numbers:
            generator = str(((max(generator_numbers)+1)* (self.dispatch_geographies.index(geography))) + (number)+1)
            if generator not in self.generation_technologies:
                self.generation_technologies.append(generator)
            self.geography[generator] = geography
            self.feeder[generator] = 'bulk'
            self.min_capacity[generator] = 0
            self.capacity[generator] = clustered_dict['derated_pmax'][number]
            self.variable_costs[generator] = clustered_dict['marginal_cost'][number]

    def convert_to_period(self, dictionary):
        """repeats a dictionary's values of all periods in the optimization
        args:
            dictionary
        returns:
            new_dictionary
        """
        new_dictionary = dict()
        for period in self.periods:
            new_dictionary[period] = dictionary
        return new_dictionary

    def run_pyomo(self, model, data, **kwargs):
        """
        Pyomo optimization steps: create model instance from model formulation and data,
        get solver, solve instance, and load solution.
        """
        logging.debug("Creating model instance...")
        instance = model.create_instance(data)
        logging.debug("Getting solver...")
        solver = SolverFactory(cfg.solver_name)
        logging.debug("Solving...")
        solution = solver.solve(instance, **kwargs)
        logging.debug("Loading solution...")
        instance.solutions.load_from(solution)
        return instance

    def pickle_for_debugging(self):
        with open(os.path.join(cfg.workingdir, 'dispatch_class.p'), 'wb') as outfile:
            pickle.dump(self, outfile, pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def load_from_pickle():
        with open(os.path.join(cfg.workingdir, 'dispatch_class.p'), 'rb') as infile:
            dispatch = pickle.load(infile)
        return dispatch

    def parse_storage_result(self, lists, period):
        charge_columns = [self.dispatch_geography, 'supply_node', 'dispatch_feeder', 'tech', 'hour', self.year]
        df = pd.DataFrame(lists, columns=charge_columns)
        df = df.set_index(charge_columns[:-1])
        df = df.groupby(level=[self.dispatch_geography, 'dispatch_feeder', 'hour']).sum()
        if df.squeeze().isnull().any():
            self.pickle_for_debugging()
            raise ValueError('NaNs in storage dispatch outputs in dispatch period {}'.format(period))
        return df


    def parse_generator_result(self, lists, period):
        charge_columns = ['tech','hour',self.year,self.dispatch_geography]
        for x in lists:
            x.append(self.geography[0][str(x[0])])
        try:
            df = pd.DataFrame(lists, columns=charge_columns)
            df = df.set_index([charge_columns[0], charge_columns[1], charge_columns[3]])
            df = df.groupby(level=[self.dispatch_geography, 'tech', 'hour']).sum()
            if df.squeeze().isnull().any():
                self.pickle_for_debugging()
                raise ValueError('NaNs in generator dispatch outputs in dispatch period {}'.format(period))
            return df
        except:
            pdb.set_trace()

    def parse_ld_result(self, lists, period):
        columns = [self.dispatch_geography, 'supply_node', 'dispatch_feeder', 'hour', self.year]
        df = pd.DataFrame(lists, columns=columns)
        df = df.set_index(columns[:-1])
        df = df.groupby(level=[self.dispatch_geography, 'supply_node', 'dispatch_feeder', 'hour']).sum()
#        if df.squeeze().isnull().any():
#            self.pickle_for_debugging()
#            raise ValueError('NaNs in long-duration dispatch outputs in dispatch period {}'.format(period))
        return df

    def parse_ld_opt_result(self, list):
        columns = ['ld_technology','hour', self.year]
        df = pd.DataFrame(list, columns=columns)
        df = df.set_index(columns[:-1])
        return df

    def parse_flexible_load_result(self, lists, period):
        charge_columns = [self.dispatch_geography, 'hour', 'dispatch_feeder', self.year]
        df = pd.DataFrame(lists, columns=charge_columns)
        df = df.set_index([self.dispatch_geography, 'dispatch_feeder', 'hour']).sort_index()
        if df.squeeze().isnull().any():
            self.pickle_for_debugging()
            raise ValueError('NaNs in flexible load outputs in dispatch period {}'.format(period))
        return df

    def parse_transmission_flows(self, lists, period):
        transmission_columns = ['gau_from', 'gau_to', 'hour', self.year]
        df = pd.DataFrame(lists, columns=transmission_columns)
        df = df.set_index(['gau_from', 'gau_to', 'hour']).sort_index()
        if df.sum().isnull().any():
            self.pickle_for_debugging()
            raise ValueError('NaNs in flexible load outputs in dispatch period {}'.format(period))
        return df

    def parse_net_transmission_flows(self, transmission_flow_df):
        imports = transmission_flow_df.groupby(level=['gau_to', 'weather_datetime']).sum()
        exports = transmission_flow_df.groupby(level=['gau_from', 'weather_datetime']).sum()
        net_flow = pd.concat([imports, exports], keys=['import flows','export flows'], names=['dispatch_output'])
        net_flow.index.names = [GeoMapper.dispatch_geography, 'weather_datetime']
        return net_flow

    def _replace_hour_with_weather_datetime(self, df):
        i_h = df.index.names.index('hour')
        df.index.levels = [level if i != i_h else shape.Shapes.get_active_dates_index() for i, level in enumerate(df.index.levels)]
        df.index.names = [name if i != i_h else 'weather_datetime' for i, name in enumerate(df.index.names)]
        return df

    def parse_optimization_results(self, results):
        # we still have model instances and need to unzip the result
        if type(results[0]) is not dict:
            results = [all_results_to_list(instance) for instance in results]
        charge = pd.concat([self.parse_storage_result(result['Charge'], period) for period, result in enumerate(results)])
        discharge = pd.concat([self.parse_storage_result(result['Storage_Provide_Power'], period) for period, result in enumerate(results)])
        flex_load_df = pd.concat([self.parse_flexible_load_result(result['Flexible_Load'], period) for period, result in enumerate(results)])
        generator_df = pd.concat([self.parse_generator_result(result['Generator_Provide_Power'], period) for period, result in enumerate(results)])
        if len(self.ld_technologies):
            ld_df = pd.concat([self.parse_ld_result(result['LD_Provide_Power'], period) for period, result in enumerate(results)])
            ld_df = self._replace_hour_with_weather_datetime(ld_df)
        else:
            ld_df = None
        transmission_flow_df = pd.concat([self.parse_transmission_flows(result['Transmission_Flows'], period) for period, result in enumerate(results)])
        transmission_flow_df = self._replace_hour_with_weather_datetime(transmission_flow_df)
        if not len(transmission_flow_df):
            transmission_flow_df = None
        storage_df = pd.concat([charge, discharge], keys=['charge','discharge'], names=['charge_discharge'])
        storage_df = self._replace_hour_with_weather_datetime(storage_df)
        storage_df = storage_df.reorder_levels([self.dispatch_geography, 'dispatch_feeder', 'charge_discharge', 'weather_datetime']).sort_index()
        flex_load_df = self._replace_hour_with_weather_datetime(flex_load_df)

        return storage_df, flex_load_df, ld_df, transmission_flow_df, generator_df


    def solve_optimization_period(self, period, return_model_instance=False):
        model = dispatch_formulation.create_dispatch_model(self, period)
        instance = model.create_instance(report_timing=False) # report_timing=True used to try to make this step faster
        solver = SolverFactory(cfg.solver_name)
        solution = solver.solve(instance)
        instance.solutions.load_from(solution)
        return instance if return_model_instance else all_results_to_list(instance)

    def test_instance_constraints(model):
        instance = model.create_instance(report_timing=False)
        for c in instance.component_objects(Constraint):
            c.activate()
            solver = SolverFactory(cfg.solver_name)
            solution = solver.solve(instance)
            if solution.solver.termination_condition == TerminationCondition.infeasible:
                pass
            else:
                print c.name
                c.activate()


    @staticmethod
    def get_empty_plot(num_rows, num_columns):
        fig, axes = plt.subplots(num_rows, num_columns, figsize=(24, 12))
        plt.subplots_adjust(wspace=0.1, hspace=0.1)
        return fig, axes

    def solve_and_plot(self):
        self.solve_optimization()

        fig, axes = self.get_empty_plot(num_rows=len(self.dispatch_geographies), num_columns=len(self.dispatch_feeders))
        flex_load = util.df_slice(self.flex_load_df, self.dispatch_feeders, 'dispatch_feeder')
        flex_load = Output.clean_df(flex_load.squeeze().unstack(self.dispatch_geography).unstack('dispatch_feeder'))
        flex_load.plot(subplots=True, ax=axes, title='FLEXIBLE LOAD')

        fig, axes = self.get_empty_plot(num_rows=len(self.dispatch_geographies), num_columns=len(self.dispatch_feeders))
        datetime = flex_load.index.get_level_values('weather_datetime')
        hour = flex_load.groupby((datetime.hour+1)).mean()
        hour.plot(subplots=True, ax=axes, title='AVERAGE FLEXIBLE LOAD BY HOUR')

        fig, axes = self.get_empty_plot(num_rows=len(self.dispatch_geographies), num_columns=len(self.dispatch_feeders)+1)
        charge = -self.storage_df.xs('charge', level='charge_discharge')
        discharge = self.storage_df.xs('discharge', level='charge_discharge')
        charge = Output.clean_df(charge.squeeze().unstack(self.dispatch_geography).unstack('dispatch_feeder'))
        discharge = Output.clean_df(discharge.squeeze().unstack(self.dispatch_geography).unstack('dispatch_feeder'))
        charge.plot(subplots=True, ax=axes)
        discharge.plot(subplots=True, ax=axes, title='STORAGE CHARGE (-) AND DISCHARGE (+)')

        fig, axes = self.get_empty_plot(num_rows=len(self.dispatch_geographies), num_columns=len(self.dispatch_feeders)+1)
        datetime = charge.index.get_level_values('weather_datetime')
        hour_charge = charge.groupby((datetime.hour+1)).mean()
        hour_discharge = discharge.groupby((datetime.hour+1)).mean()
        hour_charge.plot(subplots=True, ax=axes)
        hour_discharge.plot(subplots=True, ax=axes, title='AVERAGE STORAGE CHARGE (-) AND DISCHARGE (+) BY HOUR')

    def solve_optimization(self):
        try:
            self.ld_energy_budgets = self.solve_ld_optimization()
            self.set_average_net_loads(self.ld_bulk_net_load_df_updated)
            state_of_charge = self.run_year_to_month_allocation()
            self.start_soc_large_storage, self.end_soc_large_storage = state_of_charge[0], state_of_charge[1]
            for period in self.periods:
                for technology in self.ld_technologies:
                    if self.ld_energy_budgets[period][technology]>= self.capacity[period][technology] * self.period_lengths[period]:
                        self.ld_energy_budgets[period][technology]= self.capacity[period][technology] * self.period_lengths[period]-1
                    if self.ld_energy_budgets[period][technology]<= self.min_capacity[period][technology] * self.period_lengths[period]:
                        self.ld_energy_budgets[period][technology]= self.min_capacity[period][technology] * self.period_lengths[period]+1
            if cfg.getParamAsBoolean('parallel_process'):
                params = [(dispatch_formulation.create_dispatch_model(self, period), cfg.solver_name) for period in self.periods]
                results = helper_multiprocess.safe_pool(helper_multiprocess.run_optimization, params)
            else:
                results = [self.solve_optimization_period(period) for period in self.periods]
            self.storage_df, self.flex_load_df, self.ld_df, self.transmission_flow_df, self.generator_df  = self.parse_optimization_results(results)
        except:
            self.pickle_for_debugging()
            raise

    def run_year_to_month_allocation(self):
        model = dispatch_long_duration.ld_storage_formulation(self)
        results = self.run_pyomo(model, None)
        state_of_charge, ld_energy_budgets = self.export_allocation_results(results)
        return state_of_charge, ld_energy_budgets


    def solve_ld_optimization(self):
        if len(self.ld_technologies):
            model = dispatch_long_duration.ld_energy_formulation(self)
            results = self.run_pyomo(model, None)
            ld_opt_df = self.parse_ld_opt_result(ld_result_to_list(results.Provide_Power))
            temp_df = pd.DataFrame([[r[0], r[-2], r[-1]] for r in storage_result_to_list(results.Provide_Power)], columns=[GeoMapper.dispatch_geography, 'hour', self.year])
            temp_df = temp_df.set_index([GeoMapper.dispatch_geography, 'hour']).groupby(level=[GeoMapper.dispatch_geography, 'hour']).sum()
            # this doesn't have transmission losses, so it is an approximation
            transmit_power = pd.DataFrame([[key[0], key[1], value.value] for key, value in results.Net_Transmit_Power_by_Geo.iteritems()], columns=[GeoMapper.dispatch_geography, 'hour', self.year])
            self.ld_bulk_net_load_df_updated = self.ld_bulk_net_load_df - temp_df - transmit_power.set_index([GeoMapper.dispatch_geography, 'hour'])
            ld_energy_budgets = util.recursivedict()
            def split_and_apply(array, dispatch_periods, fun):
                energy_by_block = np.array_split(array, np.where(np.diff(dispatch_periods)!=0)[0]+1)
                return [fun(block) for block in energy_by_block]
            for tech in self.ld_technologies:
                energy_budgets = split_and_apply(util.df_slice(ld_opt_df, tech, 'ld_technology').values,self.period_repeated, sum)
                for period in self.periods:
                    ld_energy_budgets[period][tech] = energy_budgets[period][0]
            return ld_energy_budgets
        else:
            self.ld_bulk_net_load_df_updated = self.ld_bulk_net_load_df
            return util.recursivedict()


    @staticmethod
    def nested_dict(dic, keys, value):
        """
        Create a nested dictionary.
        :param dic:
        :param keys:
        :param value:
        :return:
        """
        for key in keys[:-1]:
             dic = dic.setdefault(key, {})
        dic[keys[-1]] = value

    def export_allocation_results(self, instance, write_to_file=False):

        periods_set = getattr(instance, "PERIODS")
        geographies_set = getattr(instance, "GEOGRAPHIES")
        storage_tech_set = getattr(instance, "VERY_LARGE_STORAGE_TECHNOLOGIES")
        if write_to_file:
            path = os.path.join(cfg.workingdir, 'dispatch_outputs')

            load_writer = csv.writer(open(os.path.join(path, "alloc_loads.csv"), "wb"))
            load_writer.writerow(["geography", "period", "avg_net_load", "period_net_load"])

            for g in geographies_set:
                for p in periods_set:
                    load_writer.writerow([g, p, instance.average_net_load[g], instance.period_net_load[g, p]])

            net_charge_writer = csv.writer(open(os.path.join(path, "alloc_results_state_of_charge.csv"), "wb"))
            net_charge_writer.writerow(["technology", "period", "geography", "discharge", "charge", "net_power", "start_state_of_charge",
                                    "end_state_of_charge"])
        start_soc = dict()
        end_soc = dict()
        for t in storage_tech_set:
            for p in periods_set:
                if write_to_file:
                    net_charge_writer.writerow([t, p, instance.region[t],
                                            instance.Discharge[t, p].value, instance.Charge[t, p].value,
                                            (instance.Discharge[t, p].value-instance.Charge[t, p].value),
                                            instance.Energy_in_Storage[t, p].value,
                                            (instance.Energy_in_Storage[t, p].value -
                                             (instance.Discharge[t, p].value-instance.Charge[t, p].value)
                                             )]
                                           )

                Dispatch.nested_dict(start_soc, [p, t], np.floor(instance.Energy_in_Storage[t, p].value*1E7)/1E7)
                Dispatch.nested_dict(end_soc, [p, t], np.floor((instance.Energy_in_Storage[t, p].value - (instance.Discharge[t, p].value-instance.Charge[t, p].value))*1E7)/1E77)

        state_of_charge = [start_soc, end_soc]
        return state_of_charge


