# -*- coding: utf-8 -*-
"""
Created on Mon Feb 15 22:06:19 2016

@author: Ben
"""
import util
import numpy as np 
from datamapfunctions import Abstract,DataMapFunctions
import copy
import pandas as pd
from scipy import optimize, interpolate, stats
import math
from config import cfg
from collections import defaultdict
import os
from pyomo.opt import SolverFactory
import csv
import logging
from sklearn.cluster import KMeans
from pathos.multiprocessing import Pool
import multiprocessing
from profilehooks import profile, timecall
# Dispatch modules
import dispatch_problem_PATHWAYS
import year_to_period_allocation


  
def run_optimization(zipped_inputs):
    import numpy as np
    period = zipped_inputs[0]
    model = zipped_inputs[1]
    bulk_storage_df = zipped_inputs[2]
    dist_storage_df = zipped_inputs[3]
    flex_load_df = zipped_inputs[4]
    opt_hours = zipped_inputs[5]
    period_hours = zipped_inputs[6]
    hours = list(period * opt_hours + np.asarray(period_hours))  
    solver_name = zipped_inputs[7]      
    stdout_detail = zipped_inputs[8]
    dispatch_geography = zipped_inputs[9]
    if stdout_detail:
        print "Optimizing dispatch for period " + str(period)
    if stdout_detail:
        print "Getting problem formulation..."
    if stdout_detail:
        print "Creating model instance..."
    instance = model.create_instance(None)
    if stdout_detail:
        print "Getting solver..."
    solver = SolverFactory(solver_name)
    if stdout_detail:
        print "Solving..."
    solution = solver.solve(instance)
    if stdout_detail:
        print "Loading solution..."
    instance.solutions.load_from(solution)        
    timepoints_set = getattr(instance, "TIMEPOINTS")
    storage_tech_set = getattr(instance, "STORAGE_TECHNOLOGIES")
    #TODO Ryan List Comprehension
    for tech in storage_tech_set:
        feeder = instance.feeder[tech] 
        geography = instance.geography[tech]
        charge = []
        discharge = []
        if feeder == 0:
            charge_indexer = util.level_specific_indexer(bulk_storage_df, [dispatch_geography, 'charge_discharge', 'hour'], [geography, 'charge',(hours)])
            discharge_indexer = util.level_specific_indexer(bulk_storage_df, [dispatch_geography, 'charge_discharge', 'hour'], [geography, 'discharge',(hours)]) 
            for timepoint in timepoints_set:                
                charge.append(instance.Charge[tech, timepoint].value)
                discharge.append(instance.Provide_Power[tech, timepoint].value)
            charge = np.column_stack(np.asarray(charge)).T
            discharge = np.column_stack(np.asarray(discharge)).T
            bulk_storage_df.loc[charge_indexer,:] += charge
            bulk_storage_df.loc[discharge_indexer,:] += discharge
        else:
            charge_indexer = util.level_specific_indexer(dist_storage_df, [dispatch_geography,'dispatch_feeder','charge_discharge','hour'], [geography, feeder, 'charge', (hours)])
            discharge_indexer = util.level_specific_indexer(dist_storage_df, [dispatch_geography,'dispatch_feeder','charge_discharge','hour'], [geography, feeder, 'discharge', (hours)]) 
            for timepoint in timepoints_set:                
                charge.append(instance.Charge[tech, timepoint].value)
                discharge.append(instance.Provide_Power[tech, timepoint].value)
            charge = np.column_stack(np.asarray(charge)).T
            discharge = np.column_stack(np.asarray(discharge)).T
            dist_storage_df.loc[charge_indexer,:] += charge
            dist_storage_df.loc[discharge_indexer,:] += discharge
    timepoints_set = getattr(instance, "TIMEPOINTS")
    geographies_set = getattr(instance, "GEOGRAPHIES")
    feeder_set = getattr(instance,"FEEDERS")
    #TODO Ryan List Comprehension
    for geography in geographies_set:
        for feeder in feeder_set:
            if feeder != 0:
                flex_load = []
                indexer = util.level_specific_indexer(flex_load_df, [dispatch_geography,'dispatch_feeder','hour'], [geography, feeder,(hours)])
                for timepoint in timepoints_set:                
                    flex_load.append(instance.Flexible_Load[geography, timepoint, feeder].value)
                flex_load = np.asarray(flex_load)
                flex_load_df.loc[indexer,:] = flex_load 
    return [bulk_storage_df,dist_storage_df,flex_load_df]




class DispatchNodeConfig(DataMapFunctions):
    def __init__(self, id, **kwargs):
        self.id = id
        self.sql_id_table = 'DispatchNodeConfig'
#        self.sql_data_table = 'DispatchNodeData'
        for col, att in util.object_att_from_table(self.sql_id_table, id, primary_key='supply_node_id'):
            setattr(self, col, att)

        

class Dispatch(object):
    def __init__(self, dispatch_feeders, dispatch_geography, dispatch_geographies, 
                 stdout_detail, results_directory,  **kwargs):
        #TODO replace 1 with a config parameter
        for col, att in util.object_att_from_table('DispatchConfig',1):
            setattr(self, col, att)
        self.opt_hours = util.sql_read_table('OptPeriods','hours', id=self.opt_hours)
        self.node_config_dict = dict()
        for supply_node in util.sql_read_table('DispatchNodeConfig','supply_node_id'):
            self.node_config_dict[supply_node] = DispatchNodeConfig(supply_node)
        self.set_dispatch_order()
        self.dispatch_window_dict = dict(util.sql_read_table('DispatchWindows'))  
        self.curtailment_cost = util.unit_convert(10**2,unit_from_den='megawatt_hour',unit_to_den=cfg.cfgfile.get('case','energy_unit'))
        self.unserved_energy_cost = util.unit_convert(10**5,unit_from_den='megawatt_hour',unit_to_den=cfg.cfgfile.get('case','energy_unit'))
        self.dist_net_load_penalty = util.unit_convert(10**3,unit_from_den='megawatt_hour',unit_to_den=cfg.cfgfile.get('case','energy_unit'))
        self.bulk_net_load_penalty = util.unit_convert(10**3,unit_from_den='megawatt_hour',unit_to_den=cfg.cfgfile.get('case','energy_unit'))
        self.dispatch_feeders = dispatch_feeders
        self.feeders = [0] + dispatch_feeders
        self.dispatch_geography = dispatch_geography
        self.dispatch_geographies = dispatch_geographies
        self.solver_name = self.find_solver()
        self.stdout_detail = stdout_detail
        if self.stdout_detail == 'False':
            self.stdout_detail = False
        else:
            self.stdout_detail = True
        self.results_directory = results_directory
        self.solve_kwargs = {"keepfiles": False, "tee": False}
        self.upward_imbalance_penalty = util.unit_convert(1000.0,unit_from_den='megawatt_hour',unit_to_den=cfg.cfgfile.get('case','energy_unit'))
        self.downward_imbalance_penalty = util.unit_convert(100.0,unit_from_den='megawatt_hour',unit_to_den=cfg.cfgfile.get('case','energy_unit'))
  
  
    def find_solver(self):
        requested_solvers = cfg.cfgfile.get('opt', 'dispatch_solver').replace(' ', '').split(',')
        solver_name = None
        # inspired by the solver detection code at https://software.sandia.gov/trac/pyomo/browser/pyomo/trunk/pyomo/scripting/driver_help.py#L336
        # suppress logging of warnings for solvers that are not found
        logger = logging.getLogger('pyomo.solvers')
        _level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)
        for requested_solver in requested_solvers:
#            print "Looking for %s solver" % requested_solver
            if SolverFactory(requested_solver).available(False):
                solver_name = requested_solver
                print "Using %s solver" % requested_solver
                break
        # restore logging
        logger.setLevel(_level)
    
        assert solver_name is not None, "Dispatch could not find any of the solvers requested in your configuration (%s) please see README.md, check your configuration, and make sure you have at least one requested solver installed." % ', '.join(requested_solvers)        
        return solver_name
  
    def set_dispatch_order(self):
        order = [x.dispatch_order for x in self.node_config_dict.values()]
        order_index = np.argsort(order)
        self.dispatch_order = [self.node_config_dict.keys()[i] for i in order_index]
      
    def set_timeperiods(self, time_index):
          """sets optimization periods based on selection of optimization hours
          in the dispatch configuration
          sets:
            period_hours = range from 1 to the number of opt_hours
            periods = range from 1 to the maximum number of periods (i.e. 8760/period_hours)
            period_timepoints = dictionary with keys of period and values of period hours
            period_flex_load_timepoints = dictionary with keys of period and values of a nested dictionary with the keys of period_hours and the values of those period hours offset
            by the flexible_load_constraint_offset configuration parameter
          """
          self.hours = np.arange(1,len(time_index)+1)
          self.period_hours = range(1,self.opt_hours+1)
          self.periods = range(0,len(time_index)/(self.opt_hours-1))
          self.period_timepoints = dict()
          self.period_flex_load_timepoints = dict()
          self.period_previous_timepoints = dict()
          for period in self.periods:
              hours = [int(x) for x in list(period * self.opt_hours + np.asarray(self.period_hours,dtype=int))]
              self.period_timepoints[period] = hours
              self.period_flex_load_timepoints[period] = dict(zip(hours,util.rotate(hours,self.flex_load_constraints_offset)))     
              self.period_previous_timepoints[period] = dict(zip(hours,util.rotate(hours,1)))

    def set_losses(self,distribution_losses):
        self.t_and_d_losses = dict()
        for geography in self.dispatch_geographies:
            for feeder in self.feeders:
                if feeder == 0:
                    self.t_and_d_losses[(geography,feeder)] = 0
                else:
                    self.t_and_d_losses[(geography,feeder)] = util.df_slice(distribution_losses, [geography,feeder],[self.dispatch_geography, 'dispatch_feeder']).values[0][0]

    def set_thresholds(self,distribution_stock, transmission_stock):
        self.bulk_net_load_thresholds = dict()
        self.dist_net_load_thresholds = dict()
        for geography in self.dispatch_geographies:
            self.bulk_net_load_thresholds[geography] = transmission_stock.loc[geography].values[0]
            for feeder in self.feeders:
                if feeder == 0:
                    self.dist_net_load_thresholds[(geography,feeder)] = 0 
                else:
                    self.dist_net_load_thresholds[(geography,feeder)] =  util.df_slice(distribution_stock,[geography, feeder],[self.dispatch_geography, 'dispatch_feeder']).values[0][0]

    def set_opt_loads(self, distribution_load, distribution_gen, bulk_load, bulk_gen):
        self.distribution_load = util.recursivedict()
        self.distribution_gen = util.recursivedict()
        self.min_cumulative_flex_load = util.recursivedict()
        self.max_cumulative_flex_load = util.recursivedict()
        self.cumulative_distribution_load = util.recursivedict()
        self.bulk_load = util.recursivedict()
        self.bulk_gen = util.recursivedict()
        self.set_opt_distribution_net_loads(distribution_load,distribution_gen)
        self.set_opt_bulk_net_loads(bulk_load,bulk_gen)
        
    def set_opt_distribution_net_loads(self, distribution_load, distribution_gen):
        self.set_max_flex_loads(distribution_load)
        active_timeshift_types = list(set(distribution_load.index.get_level_values('timeshift_type')))
        for geography in self.dispatch_geographies:
            for feeder in self.feeders:
                for period in self.periods:
                       if feeder != 0:
                           for timeshift in [2,1,3]:      
                               load_df = util.df_slice(distribution_load, [geography, feeder, 2], [self.dispatch_geography, 'dispatch_feeder', 'timeshift_type'])
                               gen_df = util.df_slice(distribution_gen, [geography, feeder], [self.dispatch_geography, 'dispatch_feeder'])
                               if timeshift == 2:
                                  for timepoint in self.period_timepoints[period]:
                                      time_index =  timepoint-1
                                      self.distribution_load[period][(geography,timepoint,feeder)] = load_df.iloc[time_index].values[0]
                                      self.cumulative_distribution_load[period][(geography,timepoint,feeder)] = load_df.cumsum().iloc[time_index].values[0]
                                      self.distribution_gen[period][(geography,timepoint,feeder)] = gen_df.iloc[time_index].values[0] 
                               elif timeshift == 1:
                                   if timeshift in active_timeshift_types:
                                       df = util.df_slice(distribution_load, [geography, feeder, timeshift], [self.dispatch_geography, 'dispatch_feeder', 'timeshift_type']).cumsum()
                                       for timepoint in self.period_timepoints[period]:
                                           time_index = timepoint-1
                                           self.min_cumulative_flex_load[period][(geography,timepoint,feeder)] = df.iloc[time_index].values[0][0]
                                   else:
                                       df = load_df 
                                       df = df.cumsum() 
                                       for timepoint in self.period_timepoints[period]:
                                           time_index = timepoint-1
                                           self.min_cumulative_flex_load[period][(geography,timepoint,feeder)] = df.iloc[time_index].values[0] 
                               elif timeshift == 3:
                                    if timeshift in active_timeshift_types:
                                       df = util.df_slice(distribution_load, [geography, feeder, timeshift], [self.dispatch_geography, 'dispatch_feeder', 'timeshift_type']).cumsum()
                                       for timepoint in self.period_timepoints[period]:
                                           time_index = timepoint -1
                                           self.max_cumulative_flex_load[period][(geography,timepoint,feeder)] = df.iloc[time_index].values[0][0] 
                                    else:
                                        df = load_df 
                                        df = df.cumsum()
                                        for timepoint in self.period_timepoints[period]:
                                            time_index = timepoint -1
                                            self.max_cumulative_flex_load[period][(geography,timepoint,feeder)] = df.iloc[time_index].values[0] 
                       else:
                            for timepoint in self.period_timepoints[period]:
                                self.distribution_load[period][(geography,timepoint,feeder)] = 0.0
                                self.distribution_gen[period][(geography,timepoint,feeder)] = 0.0
                                self.max_cumulative_flex_load[period][(geography,timepoint,feeder)] = 0.0
                                self.min_cumulative_flex_load[period][(geography,timepoint,feeder)] = 0.0
                                self.cumulative_distribution_load[period][(geography,timepoint,feeder)] = 0.0
                                
                                
                                
    def set_opt_bulk_net_loads(self, bulk_load, bulk_gen):
        for geography in self.dispatch_geographies:
            for period in self.periods:
                load_df = util.df_slice(bulk_load, [geography, 2], [self.dispatch_geography, 'timeshift_type'])
                gen_df = util.df_slice(bulk_gen, [geography, 2], [self.dispatch_geography, 'timeshift_type'])
                for timepoint in self.period_timepoints[period]:
                   time_index = timepoint -1
                   self.bulk_load[period][(geography,timepoint)] = load_df.iloc[time_index].values[0]     
                   self.bulk_gen[period][(geography,timepoint)] = gen_df.iloc[time_index].values[0]
                   
    def set_max_flex_loads(self, distribution_load):
        self.max_flex_load = defaultdict(dict)
        for geography in self.dispatch_geographies:
            for feeder in self.feeders:
                for period in self.periods:
                    start = period * self.opt_hours
                    stop = (period+1) * self.opt_hours
                    if feeder !=0:
                        self.max_flex_load[period][(geography,feeder)] = util.df_slice(distribution_load, [geography, feeder, 2], [self.dispatch_geography, 'dispatch_feeder', 'timeshift_type']).iloc[start:stop].max().values[0] 
                    else:
                        self.max_flex_load[period][(geography,feeder)] = 0.0
   
    def set_average_net_loads(self,total_net_load):
        self.period_net_load = defaultdict(dict)
        self.average_net_load = dict()
        for geography in self.dispatch_geographies:
            df = util.df_slice(total_net_load, [geography, 2], [self.dispatch_geography,'timeshift_type'])
            self.average_net_load[geography] =  (df).mean().values[0]
            for period in self.periods:
                start = period * self.opt_hours
                stop = (period+1) * self.opt_hours- 1
                self.period_net_load[(geography, period)] = df.iloc[start:stop].mean().values[0]

    
    def set_technologies(self,storage_capacity_dict, storage_efficiency_dict, thermal_dispatch_dict):
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
      self.generation_technologies = []
      self.variable_costs = {}
      for dispatch_geography in storage_capacity_dict['power'].keys():
          for zone in storage_capacity_dict['power'][dispatch_geography].keys():
             for feeder in storage_capacity_dict['power'][dispatch_geography][zone].keys():
                 for tech in storage_capacity_dict['power'][dispatch_geography][zone][feeder].keys():
                     tech_dispatch_id = str((dispatch_geography,zone,feeder,tech))
                     self.storage_technologies.append(tech_dispatch_id)
                     self.geography[tech_dispatch_id ] = dispatch_geography
                     self.capacity[tech_dispatch_id] = storage_capacity_dict['power'][dispatch_geography][zone][feeder][tech]
                     self.duration[tech_dispatch_id] = storage_capacity_dict['duration'][dispatch_geography][zone][feeder][tech]
                     self.energy[tech_dispatch_id] = self.capacity[tech_dispatch_id] * self.duration[tech_dispatch_id]
                     if self.duration[tech_dispatch_id ]>=self.large_storage_duration:
                        self.alloc_technologies.append(tech_dispatch_id)
                        self.large_storage[tech_dispatch_id] = 1
                        self.alloc_geography[tech_dispatch_id] = dispatch_geography
                        self.alloc_capacity[tech_dispatch_id] = self.capacity[tech_dispatch_id] * len(self.period_hours)
                        self.alloc_energy[tech_dispatch_id] = self.energy[tech_dispatch_id]
                     else:
                        self.large_storage[tech_dispatch_id] = 0
                     x = 1/np.sqrt(storage_efficiency_dict[dispatch_geography][zone][feeder][tech])
                     if not np.isfinite(x):
                         x = 1
                     self.charging_efficiency[tech_dispatch_id] = x
                     self.discharging_efficiency[tech_dispatch_id] = copy.deepcopy(self.charging_efficiency)[tech_dispatch_id] 
                     self.feeder[tech_dispatch_id] = feeder
          self.set_gen_technologies(dispatch_geography,thermal_dispatch_dict)
      self.capacity = self.convert_to_period(self.capacity)
      self.duration = self.convert_to_period(self.duration)
      self.energy = self.convert_to_period(self.energy)
      self.feeder = self.convert_to_period(self.feeder)
      self.geography = self.convert_to_period(self.geography)
            
            
    
    def set_gen_technologies(self, geography, thermal_dispatch_dict):
        pmaxs = np.array(thermal_dispatch_dict[geography]['capacity'].values())
        marginal_costs = np.array(thermal_dispatch_dict[geography]['cost'].values())
        MOR = np.array(thermal_dispatch_dict[geography]['maintenance_outage_rate'].values())
        FOR = np.array(thermal_dispatch_dict[geography]['forced_outage_rate'].values())
        must_runs = np.array(thermal_dispatch_dict[geography]['must_run'].values())
        clustered_dict = Dispatch._cluster_generators(n_clusters = int(cfg.cfgfile.get('opt','generator_steps')), pmax=pmaxs, marginal_cost=marginal_costs, FORs=FOR, 
                                     MORs=MOR, must_run=must_runs, pad_stack=True, zero_mc_4_must_run=True)
        generator_numbers = range(len(clustered_dict['derated_pmax']))
        for number in generator_numbers:
            generator = str(self.dispatch_geographies.index(geography) * (number + 1))
            if generator not in self.generation_technologies:
                self.generation_technologies.append(generator)
            self.geography[generator] = geography
            self.feeder[generator] = 0
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

    ##################################################################
    ##################################################################
    ## POWER TO GAS, ELECTROLYSIS AND HYDRO DISPATCH
    ##################################################################
    @staticmethod
    def residual_energy(load_cutoff, load, energy_budget, pmin=0, pmax=None):
        """
        energy_budget > 0 is generation (hydro)
        energy_budget < 0 is load (P2G)
        """
        dct = (1 if energy_budget>0 else -1)
        return np.sum(np.clip(dct*load[dct*load>dct*(load_cutoff + pmin)] - dct*load_cutoff, a_min=pmin, a_max=pmax) - pmin) + len(load)*pmin - dct*energy_budget
    
    @staticmethod
    def dispatch_shape(load, load_cutoff, dct, pmin=0, pmax=None):
        """
        dct = 1 is generation (hydro)
        dct = -1 is load (P2G)
        """
        dispatch = np.zeros_like(load) - dct*pmin
        dispatch[dct*load>dct*(load_cutoff + pmin)] -= dct*(np.clip(dct*load[dct*load>dct*(load_cutoff + pmin)] - dct*load_cutoff, a_min=pmin, a_max=pmax) - pmin)
        return dispatch * -dct #always positive
    
    @staticmethod
    def solve_for_load_cutoff(load, energy_budget, pmin=0, pmax=None):
        return optimize.root(Dispatch.residual_energy, x0=np.mean(load), args=(load, energy_budget, pmin, pmax))['x']
    
    @staticmethod
    def solve_for_dispatch_shape(load, energy_budget, pmin=0, pmax=None):
        load_cutoff = Dispatch.solve_for_load_cutoff(load, energy_budget, pmin, pmax)
        return Dispatch.dispatch_shape(load, load_cutoff, (1 if energy_budget>0 else -1), pmin, pmax)
    
    @staticmethod
    def dispatch_to_energy_budget(load, energy_budgets, dispatch_periods=None, pmins=0, pmaxs=None):
        """ Dispatch to energy budget produces a dispatch shape for a load or generating energy budget
    
        Common uses would be hydro, power2gas, and hydrogen electrolysis
        
        energy_budget > 0 is generation (hydro)
        energy_budget < 0 is load (P2G)
        
        Args:
            load: net load shape (ndarray)
            energy_budgets: availabile energy (float or ndarray)
            dispatch_periods: identifiers for each load hour (ndarray) defaults to None
            pmins: min power for the dispatch (float or ndarray) defaults to zero
            pmaxs: max power for the dispatch (float or ndarray) defaults to None
        
        Returns:
            dispatch: (ndarray)
        
        This function solves based on a huristic, which returns the same solution as optimization
        
        Note that every change in dispatch period results in a new dispatch group, for instance,
         range(12) + range(12) will result in 24 dispatch groups, not 12, as might be expected.
        """
        if dispatch_periods is not None and len(dispatch_periods) != len(load):
            raise ValueError('Dispatch period identifiers must match the length of the load data')
        
        #spit the load into dispatch groups
        load_groups = (load,) if dispatch_periods is None else np.array_split(load, np.where(np.diff(dispatch_periods)!=0)[0]+1)
        energy_budgets = util.ensure_iterable_and_not_string(energy_budgets)
        pmins, pmaxs = util.ensure_iterable_and_not_string(pmins), util.ensure_iterable_and_not_string(pmaxs)
    
        if len(energy_budgets) != len(load_groups):
            raise ValueError('Number of energy_budgets must match the number of dispatch periods')
    
        if len(pmins) != len(load_groups):
            if len(pmins)==1:
                #expand to match the number of load groups
                pmins*=len(load_groups)
            else:
                raise ValueError('Number of pmin values must match the number of dispatch periods')
    
        if len(pmaxs) != len(load_groups):
            if len(pmaxs)==1:
                #expand to match the number of load groups
                pmaxs*=len(load_groups)
            else:
                raise ValueError('Number of pmax values must match the number of dispatch periods')
        
        #call solve for dispatch on each group and concatenate
        return np.concatenate([Dispatch.solve_for_dispatch_shape(load_group, energy_budget, pmin, pmax)
            for load_group, energy_budget, pmin, pmax in zip(load_groups, energy_budgets, pmins, pmaxs)])
    
    ##################################################################
    ##################################################################
    ## GENERATOR DISPATCH (LOOKUP HEURISTIC)
    ##################################################################
    @staticmethod
    def _cluster_generators(n_clusters, pmax, marginal_cost, FORs, MORs, must_run, pad_stack=False, zero_mc_4_must_run=False):
        """ Cluster generators is a function that takes a generator stack and clusters them by marginal_cost and must run status.
        
        clustering is done with sklearn KMeans
        
        Args:
            n_clusters (int): controls the number of output generators (must between 1 and the number of generators)
            pmax (1d array): pmax of each generator
            marginal_cost (1d array): the full marginal marginal cost for each generator
            FORs (1d array): forced outage rates by generator
            MORs (1d array): maintenance rates by generator
            must_run (bool 1d array): boolean array indicating whether each generator is must run
            pad_stack (bool): if true, the highest cost dispatchable generator has it's capacity increased
            zero_mc_4_must_run (bool): if true, must run generators are returned with zero marginal cost
        
        Returns:
            clustered: a dictionary with generator clusters
        """
        assert n_clusters>=1
        assert n_clusters<=len(pmax)
        
        new_mc = copy.deepcopy(marginal_cost) #copy mc before changing it
        if zero_mc_4_must_run:
            new_mc[np.nonzero(must_run)] = 0
        
        # clustering is done here
        cluster = KMeans(n_clusters=n_clusters, precompute_distances='auto')
        factor = (max(marginal_cost) - min(marginal_cost))*10
        fit = cluster.fit_predict(np.vstack((must_run*factor, new_mc)).T)
        
        # helper functions for results
        group_sum = lambda c, a: sum(a[fit==c])
        group_wgtav = lambda c, a, b: np.dot(a[fit==c], b[fit==c])/group_sum(c, a)

        combined_rate = Dispatch._get_combined_outage_rate(FORs, MORs)
        derated_pmax = pmax * (1-combined_rate)

        clustered = {}
        clustered['marginal_cost'] = np.array([group_wgtav(c, derated_pmax, new_mc) for c in range(n_clusters)])
        order = np.argsort(clustered['marginal_cost']) #order the result by marginal cost
        clustered['marginal_cost'] = clustered['marginal_cost'][order]
        
        clustered['derated_pmax'] = np.array([group_sum(c, derated_pmax) for c in range(n_clusters)])[order]
        clustered['pmax'] = np.array([group_sum(c, pmax) for c in range(n_clusters)])[order]
        clustered['FORs'] = np.array([group_wgtav(c, pmax, FORs) for c in range(n_clusters)])[order]
        clustered['MORs'] = np.array([group_wgtav(c, pmax, MORs) for c in range(n_clusters)])[order]
        clustered['must_run'] = np.array([round(group_wgtav(c, pmax, must_run)) for c in range(n_clusters)], dtype=int)[order]
        
        # check the result
        np.testing.assert_almost_equal(sum(clustered['pmax'][np.where(clustered['must_run']==0)]), sum(pmax[np.where(must_run==0)]))
        
        # if we are padding the stack, increse the size of the last dispatchable generator
        if pad_stack:
            dispatchable_index = np.where(clustered['must_run']==0)[0]
            clustered['derated_pmax'][dispatchable_index[-1]] += sum(clustered['derated_pmax'])
            clustered['pmax'][dispatchable_index[-1]] += sum(clustered['pmax'])
            
        return clustered

    @staticmethod
    def schedule_generator_maintenance(load, pmaxs, annual_maintenance_rates, dispatch_periods=None, min_maint=0., max_maint=.5, load_ptile=99.8):
        group_cuts = list(np.where(np.diff(dispatch_periods)!=0)[0]+1) if dispatch_periods is not None else None
        # we have to have dispatch periods or we can't allocate, if we don't have them, we just return the base maintenance rates
        if dispatch_periods is None or not group_cuts:
            return annual_maintenance_rates
        
        pmax = np.max(pmaxs, axis=0) if pmaxs.ndim > 1 else pmaxs
        capacity_sum = sum(pmax)
        cap_by_group = np.sum(pmaxs, axis=1) if pmaxs.ndim > 1 else [sum(pmaxs)]*len(dispatch_periods)
        maintenance_energy = np.dot(pmax, annual_maintenance_rates)*len(load)
        load_cut = np.percentile(load, load_ptile)
        
        okay_for_maint = [np.all(group) for group in np.array_split(load<load_cut, group_cuts)]
        
        load_for_maint = np.copy(load)
        for ok, cut_start, cut_end in zip(okay_for_maint, [0]+group_cuts[:-1], group_cuts):
            if not ok:
                load_for_maint[cut_start:cut_end] = max(load)
        energy_allocation = Dispatch.dispatch_to_energy_budget(load_for_maint, -maintenance_energy, pmins=capacity_sum*min_maint, pmaxs=capacity_sum*max_maint)
        common_rates = [sum(group)/len(group)/float(cap) for group, cap in zip(np.array_split(energy_allocation, group_cuts), cap_by_group)]
    
        return np.array([common_rates]*len(pmax)).T

    @staticmethod
    def _get_combined_outage_rate(FORs, MORs):
        return MORs + (1 - MORs) * FORs

    @staticmethod
    def _get_derated_capacity(pmax, combined_rate, decimals=0):
        return np.array(np.round(pmax * (1 - combined_rate) * 10**decimals), dtype=int)

    @staticmethod
    def _get_marginal_cost_order(marginal_cost, must_run=None):
        if must_run is None:
            must_run = np.zeros_like(marginal_cost)
        must_run_index, dispat_index = np.nonzero(must_run)[0], np.nonzero(must_run==0)[0] 
        sorted_cost = np.argsort(marginal_cost)
        marginal_cost_order = np.concatenate(([mc for mc in sorted_cost if mc in must_run_index],
                                              [mc for mc in sorted_cost if mc in dispat_index])).astype(int)
        return marginal_cost_order

    @staticmethod
    def generator_supply_curve(pmax, marginal_cost, FORs, MORs, must_run, decimals=0, zero_mc_4_must_run=False):
        combined_rate = Dispatch._get_combined_outage_rate(FORs, MORs)
        derated_capacity = Dispatch._get_derated_capacity(pmax, combined_rate, decimals)
        
        marginal_cost_order = Dispatch._get_marginal_cost_order(marginal_cost, must_run)
        
        must_run_index = np.nonzero(must_run)[0]
        mc_lookup = lambda i: 0 if (zero_mc_4_must_run and i in must_run_index) else marginal_cost[i]
        
        full_mp = np.array([0] + util.flatten_list([[mc_lookup(i)]*derated_capacity[i] for i in marginal_cost_order]))
    
        return full_mp

    @staticmethod
    def _get_load_level_lookup(load, must_run_sum=0, operating_reserves=0, decimals=0):
        return np.array(np.clip(np.round(load * (1 + operating_reserves) * 10**decimals), a_min=must_run_sum, a_max=None), dtype=int)

    @staticmethod
    def _fix_energy_due_to_rounding(energy, marginal_cost, pmax, derated_capacity, combined_rate, lookup, decimals=0):
        nonzero_cap_index = np.nonzero(derated_capacity)
        for i, cap in enumerate(derated_capacity):
            if cap!=0:
                continue
            cf_index = np.argsort((marginal_cost[nonzero_cap_index]-marginal_cost[i])**2)[0]
            ratio = energy[nonzero_cap_index][cf_index]/np.array(derated_capacity[nonzero_cap_index][cf_index], dtype=float)
            energy[i] = pmax[i]*(1-combined_rate[i])*ratio*10**decimals        
        return energy

    @staticmethod
    def _get_energy_by_generator(lookup, derated_capacity, marginal_cost, must_run, pmax, combined_rate, decimals=0):
        marginal_cost_order = Dispatch._get_marginal_cost_order(marginal_cost, must_run)
        derated_sum = sum(derated_capacity)
        hist = np.array_split(np.cumsum(np.histogram(lookup, bins=derated_sum, range=(0, derated_sum))[0][-1:0:-1])[-1:0:-1],
                              np.cumsum(derated_capacity[marginal_cost_order])[:-1])
        energy = np.array([np.sum(group) for group in hist], dtype=float)[np.argsort(marginal_cost_order)] / 10**decimals
        
        energy = Dispatch._fix_energy_due_to_rounding(energy, marginal_cost, pmax, derated_capacity, combined_rate, lookup, decimals)
        
        return energy

    @staticmethod
    def solve_gen_dispatch(load, pmax, marginal_cost, FORs, MORs, must_run, decimals=0, operating_reserves=0.03):
        combined_rate = Dispatch._get_combined_outage_rate(FORs, MORs)
        derated_capacity = Dispatch._get_derated_capacity(pmax, combined_rate, decimals)
        
        full_mp = Dispatch.generator_supply_curve(pmax, marginal_cost, FORs, MORs, must_run, decimals)
        full_pc = np.cumsum(full_mp)/10**decimals
        
        must_run_sum = sum(derated_capacity[np.nonzero(must_run)])
        lookup = Dispatch._get_load_level_lookup(load, must_run_sum, operating_reserves=0, decimals=decimals)
        lookup_plus_reserves = Dispatch._get_load_level_lookup(load, must_run_sum, operating_reserves, decimals=decimals)
        
        market_price = full_mp[lookup_plus_reserves]
        market_price[np.where(load*10**decimals<must_run_sum)] = 0
        production_cost = full_pc[lookup]
        
        energy = Dispatch._get_energy_by_generator(lookup, derated_capacity, marginal_cost, must_run, pmax, combined_rate, decimals)

        return market_price, production_cost, energy, np.array(lookup / 10**decimals, dtype=float)

    @staticmethod
    def _format_gen_dispatch_inputs(num_groups, pmaxs, marginal_costs, dispatch_periods=None, FOR=None, MOR=None, must_runs=None, capacity_weights=None):
        marginal_costs = np.tile(marginal_costs, (num_groups,1)) if len(marginal_costs.shape)==1 else marginal_costs
        pmaxs = np.tile(pmaxs, (num_groups,1)) if len(pmaxs.shape)==1 else pmaxs
        FOR = np.zeros_like(pmaxs) if FOR is None else (np.tile(FOR, (num_groups,1)) if len(FOR.shape)==1 else FOR)
        MOR = np.zeros_like(pmaxs) if MOR is None else (np.tile(MOR, (num_groups,1)) if len(MOR.shape)==1 else MOR)
        must_runs = np.ones_like(pmaxs, dtype=bool) if must_runs is None else np.array(np.tile(must_runs, (num_groups,1)) if len(must_runs.shape)==1 else must_runs, dtype=bool)
        capacity_weights = np.full(pmaxs.shape, 1/float(len(pmaxs)), dtype=float) if capacity_weights is None else np.array(capacity_weights, dtype=float)
        
        return marginal_costs, pmaxs, FOR, MOR, must_runs, capacity_weights

    @staticmethod
    def _get_stock_changes(load_groups, pmaxs, FOR, MOR, capacity_weights, decimals=0, reserves=0.03):
        stock_changes = np.zeros(len(capacity_weights))
        
        for i, load_group in enumerate(load_groups):
            max_lookup = Dispatch._get_load_level_lookup(np.array([max(load_group)]), 0, reserves+.01, decimals)[0]
            combined_rate = Dispatch._get_combined_outage_rate(FOR[i], MOR[i])
            derated_capacity = Dispatch._get_derated_capacity(pmaxs[i]+stock_changes, combined_rate, decimals)
            total_capacity_weight = sum(capacity_weights)
            
            residual_for_load_balance = float(max_lookup - sum(derated_capacity))/10**decimals + (1./10**decimals)
            
            # we need more capacity
            if residual_for_load_balance > 0:
                    residual_capacity_growth= residual_for_load_balance/float(total_capacity_weight)
                    stock_changes += capacity_weights * residual_capacity_growth / (1 - combined_rate)
        
        return stock_changes
    
    @staticmethod
    def generator_stack_dispatch(load, pmaxs, marginal_costs, dispatch_periods=None, FOR=None, MOR=None, must_runs=None, capacity_weights=None, operating_reserves=0.03):
        """ Dispatch generators to a net load signal
        
        Args:
            load: net load shape (ndarray[h])
            pmaxs: max capacity (ndarray[d, n])
            marginal_costs: marginal generator operating cost (ndarray[d, n])
            dispatch_periods: identifiers for each load hour (ndarray[d]) defaults to None
            FOR: generator forced outage rates (ndarray[d, n]) defaults to zero for each generator
            MOR: maintenance outage rates (ndarray[d, n]) defaults to zero for each generator
            must_run: generator must run status (ndarray[d, n]) defaults to False for each generator
            periods_per_year: number of periods per year, used to calculate capacity factors, default is 8760
        Returns:
            dispatch_results: dictionary
             --market_price: hourly market price over the dispatch (ndarray[h])
             --production_cost: hourly production cost over the dispatch (ndarray[h])
             --gen_cf: generator capacity factors over the dispatch period (ndarray[n])
        """
        if len(pmaxs) != len(marginal_costs):
            raise ValueError('Number of generator pmaxs must equal number of marginal_costs')
        
        if capacity_weights is not None and capacity_weights.ndim>1:
            raise ValueError('capacity weights should not vary across dispatch periods')
        
        decimals = 6 - int(math.log10(max(load)))
        
        load_groups = (load,) if dispatch_periods is None else np.array_split(load, np.where(np.diff(dispatch_periods)!=0)[0]+1)
        num_groups = len(load_groups)
        
        marginal_costs, pmaxs, FOR, MOR, must_runs, capacity_weights = Dispatch._format_gen_dispatch_inputs(num_groups, pmaxs, marginal_costs, dispatch_periods, FOR, MOR, must_runs, capacity_weights)
        
        market_prices, production_costs, gen_dispatch_shape = [], [], []
        gen_energies = np.zeros(pmaxs.shape[1])
        
        stock_changes = Dispatch._get_stock_changes(load_groups, pmaxs, FOR, MOR, capacity_weights, decimals, reserves=operating_reserves)
        
        for i, load_group in enumerate(load_groups):
            market_price, production_cost, gen_energy, shape = Dispatch.solve_gen_dispatch(load_group, pmaxs[i]+stock_changes, marginal_costs[i], FOR[i], MOR[i], must_runs[i], decimals, operating_reserves)
            market_prices += list(market_price)
            production_costs += list(production_cost)
            gen_dispatch_shape += list(shape)
            gen_energies += gen_energy
        
        #fix up rounding
        combined_rate = Dispatch._get_combined_outage_rate(FOR, MOR)
        pmax_est = np.max((pmaxs+stock_changes)*(1-combined_rate), axis=0)
        pmax_rounded = np.round(pmax_est, decimals)
        rounding_error = pmax_est/pmax_rounded
        gen_energies[pmax_rounded!=0] *= rounding_error[pmax_rounded!=0]
#        gen_energies *= sum(load)/sum(gen_energies) #this can cause problems if you have too much must run
        
        gen_cf = gen_energies/np.max((pmaxs+stock_changes), axis=0)/float(len(load))
        dispatch_results = dict(zip(['market_price', 'production_cost', 'gen_energies', 'gen_cf', 'gen_dispatch_shape', 'stock_changes'],
                                    [market_prices,    production_costs,   gen_energies,   gen_cf,   gen_dispatch_shape, stock_changes]))
        return dispatch_results

    def run_pyomo(self, model, data, **kwargs):
        """
        Pyomo optimization steps: create model instance from model formulation and data,
        get solver, solve instance, and load solution.
        :param model:
        :param data:
        :param solver_name:
        :param stdout_detail:
        :param kwargs:
        :return: instance
        """
        if self.stdout_detail:
            print "Creating model instance..."
        instance = model.create_instance(data)
        if self.stdout_detail:
            print "Getting solver..."
        solver = SolverFactory(self.solver_name)
        if self.stdout_detail:
            print "Solving..."
        solution = solver.solve(instance, **kwargs)
        if self.stdout_detail:
            print "Loading solution..."
        instance.solutions.load_from(solution)
        return instance

    def parallelize_opt(self,year):
        state_of_charge = self.run_year_to_month_allocation()
        start_state_of_charge, end_state_of_charge = state_of_charge[0], state_of_charge[1]
        model_list = []
        periods = copy.deepcopy(self.periods)
        opt_hours = [self.opt_hours]* len(periods)
        period_hours = [copy.deepcopy(self.period_hours)] * len(periods)
        bulk_storage_index = pd.MultiIndex.from_product([self.dispatch_geographies, ['charge','discharge'],self.hours], names=[self.dispatch_geography,'charge_discharge','hour'])
        dist_storage_index = pd.MultiIndex.from_product([self.dispatch_geographies, self.dispatch_feeders,['charge','discharge'], self.hours], names=[self.dispatch_geography,'dispatch_feeder','charge_discharge','hour'])
        bulk_storage_df = [util.empty_df(index=bulk_storage_index,columns=[year],fill_value=0.0)]*len(periods)  
        dist_storage_df = [util.empty_df(index=dist_storage_index,columns=[year],fill_value=0.0)]*len(periods)     
        flex_load_index =  pd.MultiIndex.from_product([self.dispatch_geographies, self.dispatch_feeders, self.hours], names=[self.dispatch_geography,'dispatch_feeder','hour'])
        flex_load_df = [util.empty_df(index=flex_load_index,columns=[year],fill_value=0.0)]*len(periods)   
        solver_name = [self.solver_name] * len(periods)
        stdout_detail = [self.stdout_detail] * len(periods)
        dispatch_geography = [self.dispatch_geography] * len(periods)
        
        if cfg.cfgfile.get('case','parallel_process') == 'True':
            for period in self.periods:
                model_list.append(dispatch_problem_PATHWAYS.dispatch_problem_formulation(self, start_state_of_charge,
                                                              end_state_of_charge, period))  
            zipped_inputs = list(zip(periods, model_list,bulk_storage_df, dist_storage_df, flex_load_df,opt_hours, period_hours, solver_name,stdout_detail, dispatch_geography))
            available_cpus = multiprocessing.cpu_count()
            pool = Pool(processes=available_cpus)
            results = pool.map(run_optimization,zipped_inputs)
            pool.close()
            pool.join()
            pool.terminate()
        else:
            results = []
            for period in self.periods:
                model_list.append(dispatch_problem_PATHWAYS.dispatch_problem_formulation(self, start_state_of_charge,
                                                              end_state_of_charge, period)) 
                results.append(run_optimization(zipped_inputs))
        bulk_storage_dfs = [x[0] for x in results]
        dist_storage_dfs = [x[1] for x in results]
        flex_load_dfs = [x[2] for x in results]
        self.bulk_storage_df = util.DfOper.add(bulk_storage_dfs)
        self.dist_storage_df = util.DfOper.add(dist_storage_dfs)
        self.flex_load_df = util.DfOper.add(flex_load_dfs)
  

            
            
    def run_dispatch_optimization(self, start_state_of_charge, end_state_of_charge, period):
        """
        :param period:
        :return:
        """


                
    def run_year_to_month_allocation(self):
        model = year_to_period_allocation.year_to_period_allocation_formulation(self)
        results = self.run_pyomo(model,None)
        state_of_charge = self.export_allocation_results(results, self.results_directory)
        return state_of_charge

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

    def export_allocation_results(self, instance, results_directory, write_to_file=False):

        periods_set = getattr(instance, "PERIODS")
        geographies_set = getattr(instance, "GEOGRAPHIES")
        tech_set = getattr(instance, "VERY_LARGE_STORAGE_TECHNOLOGIES")

        if write_to_file:
            load_writer = csv.writer(open(os.path.join(results_directory, "alloc_loads.csv"), "wb"))
            load_writer.writerow(["geography", "period", "avg_net_load", "period_net_load"])

            for g in geographies_set:
                for p in periods_set:
                    load_writer.writerow([g, p, instance.average_net_load[g], instance.period_net_load[g, p]])

            net_charge_writer = csv.writer(open(os.path.join(results_directory, "alloc_results_state_of_charge.csv"), "wb"))
            net_charge_writer.writerow(["technology", "period", "geography", "discharge", "charge", "net_power", "start_state_of_charge",
                                    "end_state_of_charge"])
        start_soc = dict()
        end_soc = dict()

        for t in tech_set:
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

                Dispatch.nested_dict(start_soc, [p, t], instance.Energy_in_Storage[t, p].value)
                Dispatch.nested_dict(end_soc, [p, t], instance.Energy_in_Storage[t, p].value - (instance.Discharge[t, p].value-instance.Charge[t, p].value))

        state_of_charge = [start_soc, end_soc]
        return state_of_charge


class DispatchFeederAllocation(Abstract):
    """loads and cleans the data that allocates demand sectors to dispatch feeders"""
    def __init__(self, id,**kwargs):
        self.id = id
        self.sql_id_table = 'DispatchFeedersAllocation'
        self.sql_data_table = 'DispatchFeedersAllocationData'
        Abstract.__init__(self, self.id, primary_key='id', data_id_key='parent_id')
        self.remap()
        self.values.sort_index(inplace=True)


