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
from matplotlib import pyplot as plt
import time
import numpy as np
import math


class DispatchNodeConfig(DataMapFunctions):
    def __init__(self, id, **kwargs):
        self.id = id
        self.sql_id_table = 'DispatchNodeConfig'
#        self.sql_data_table = 'DispatchNodeData'
        for col, att in util.object_att_from_table(self.sql_id_table, id, primary_key='supply_node_id'):
            setattr(self, col, att)
#        DataMapFunctions.__init__(self,primary_key='supply_node_id')
#        for value in ['p_max','p_min','energy_budget']:
#            self.read_timeseries_data(data_column_names=value, hide_exceptions=True)
#            setattr(self, value + '_raw_values',self.raw_values)
        
            
        

class Dispatch(object):
    def __init__(self, **kwargs):
        #TODO replace 1 with a config parameter
        for col, att in util.object_att_from_table('DispatchConfig',1):
            setattr(self, col, att)
        self.opt_hours = util.sql_read_table('OptPeriods','hours', id=self.opt_hours)
        self.set_timeperiods()
        self.node_config_dict = dict()
        for supply_node in util.sql_read_table('DispatchNodeConfig','supply_node_id'):
            self.node_config_dict[supply_node] = DispatchNodeConfig(supply_node)
        self.set_dispatch_order()
        self.dispatch_window_dict = dict(util.sql_read_table('DispatchWindows'))  
   
    def set_dispatch_order(self):
        order = [x.dispatch_order for x in self.node_config_dict.values()]
        order_index = np.argsort(order)
        self.dispatch_order = [self.node_config_dict.keys()[i] for i in order_index]
            
      
    
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
          self.period_hours = range(1,self.opt_hours+1)
          self.periods = range(0,8760/self.opt_hours-1)
          self.period_timepoints = dict()
          self.period_flex_load_timepoints = dict()
          for period in self.periods:
              self.period_timepoints[period] = self.period_hours
              self.period_flex_load_timepoints[period] = dict(zip(self.period_hours,util.rotate(self.period_hours,self.flex_load_constraints_offset)))     
    

    def run(self,thermal_resource_capacity, thermal_resource_costs, thermal_resource_cf,
            storage_capacity, storage_efficiency, 
            non_dispatchable_gen, dispatchable_gen, dispatchable_load_supply,
            non_dispatchable_load_supply, demand_load, distribution_losses):
                pass
         #Step 1 Prepare Inputs
        #TODO Ryan reformat thermal resource stack from capacity and resource cost dictionaries
        #TODO Ryan reformat dispatchable supply for heuristic optimization
    

                    


    def set_storage_technologies(self,storage_capacity_dict, storage_efficiency_dict):
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
      self.region = dict()
      self.capacity = dict()
      self.charging_efficiency = dict()
      self.discharging_efficiency = dict()
      self.duration = dict()
      self.feeder = dict()
      self.large_storage = dict()
      self.storage_technologies = []
      for dispatch_geography in storage_capacity_dict['power'].keys():
          for zone in storage_capacity_dict['power'][dispatch_geography].keys():
             for feeder in storage_capacity_dict['power'][dispatch_geography][zone].keys():
                 for tech in storage_capacity_dict['power'][dispatch_geography][zone][feeder].keys():
                     tech_dispatch_id = (dispatch_geography,zone,feeder,tech)
                     self.storage_technologies.append(tech_dispatch_id)
                     self.region[tech_dispatch_id ] = dispatch_geography
                     self.capacity[tech_dispatch_id] = storage_capacity_dict['power'][dispatch_geography][zone][feeder][tech]
                     self.duration[tech_dispatch_id] = storage_capacity_dict['duration'][dispatch_geography][zone][feeder][tech]
                     if self.duration[tech_dispatch_id ]>=self.large_storage_duration:
                        self.large_storage[tech_dispatch_id] = 1
                     else:
                        self.large_storage[tech_dispatch_id] = 0
                     self.charging_efficiency[tech_dispatch_id] = 1/np.sqrt(storage_efficiency_dict[dispatch_geography][zone][feeder][tech])
                     self.discharging_efficiency[tech_dispatch_id] = 1/copy.deepcopy(self.charging_efficiency)[tech_dispatch_id] 
                     self.feeder[tech_dispatch_id] = feeder
      self.capacity = self.convert_to_period(self.capacity)
      self.duration = self.convert_to_period(self.duration)
      self.feeder = self.convert_to_period(self.feeder)
      self.region = self.convert_to_period(self.region)
            
    
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
    def schedule_generator_maintenance(load, pmaxs, annual_maintenance_rates, dispatch_periods=None, min_maint=0., max_maint=.15, load_ptile=99.8):
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
        
#    
##    load = pd.DataFrame.from_csv('load.csv')
#    load = load.values.flatten()
#    
#    dispatch_periods = pd.DataFrame.from_csv('dispatch_periods.csv')
#    dispatch_periods = dispatch_periods.values.flatten()
#    
#    marginal_costs = pd.DataFrame.from_csv('marginal_costs.csv').values
#    pmaxs = pd.DataFrame.from_csv('pmaxs.csv').values
#    outage_rates = pd.DataFrame.from_csv('outage_rates.csv').values
#    must_runs = pd.DataFrame.from_csv('must_runs.csv').values
    
    #t = time.time()
    #for i in range(100):
    #    dispatch = dispatch_to_energy_budget(load, [-5000*8760/12]*12, dispatch_periods=dispatch_periods, pmins=0, pmaxs=10000)
    #t = e3.utils.time_stamp(t)
    #
    #plt.plot(load)
    #plt.plot(load+dispatch)
    
#    t = time.time()
#    for i in range(1):
#        maintenance_rates = schedule_generator_maintenance(load, pmaxs, outage_rates[0], dispatch_periods=dispatch_periods)
#    t = e3.utils.time_stamp(t)
#    
#    for i in range(1):
#        dispatch_results = generator_stack_dispatch(load, pmaxs, marginal_costs, dispatch_periods, outage_rates, maintenance_rates, must_runs)
#    e3.utils.time_stamp(t)
    
    #plt.plot(dispatch_results['gen_cf'])
    #plt.plot(dispatch_results['market_price'])
    #plt.plot(dispatch_results['production_cost'])
    
    #print np.mean(dispatch_results['market_price'])
    #print np.sum(dispatch_results['production_cost'])
        
class DispatchFeederAllocation(Abstract):
    """loads and cleans the data that allocates demand sectors to dispatch feeders"""
    def __init__(self, id,**kwargs):
        self.id = id
        self.sql_id_table = 'DispatchFeedersAllocation'
        self.sql_data_table = 'DispatchFeedersAllocationData'
        Abstract.__init__(self,self.id)
        
        self.remap()
        self.values.sort_index(inplace=True)
        
#        self.values = self.clean_timeseries('raw_values', inplace=False)
#        self.values.sort(inplace=True)