# -*- coding: utf-8 -*-
"""
Created on Mon Feb 15 22:06:19 2016

@author: Ben
"""
import util
import numpy as np 
from datamapfunctions import Abstract
import copy
import pandas as pd
from scipy import optimize, interpolate, stats
from matplotlib import pyplot as plt
import time


class Dispatch(object):
    def __init__(self, **kwargs):
        #TODO replace 1 with a config parameter
        for col, att in util.object_att_from_table('DispatchConfig',1):
            setattr(self, col, att)
        self.opt_hours = util.sql_read_table('DispatchWindows','hours', id=self.opt_hours)
        self.set_timeperiods()
          
    
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
    

    def run(self,thermal_resource_capacity, thermal_resource_costs,
            storage_capacity, storage_efficiency, 
            non_dispatchable_gen, dispatchable_gen, dispatchable_load_supply,
            non_dispatchable_load_supply, demand_load):
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
                     self.discharging_efficiency[tech_dispatch_id] = 1/copy.deepcopy(self.charging_efficiency)
                     self.feeder[tech_dispatch_id] = feeder
      self.capacity = self.convert_to_period(self.capacity)
      self.duration = self.convert_to_period(self.duration)
      self.feeder= self.convert_to_period(self.feeder)
      self.region = self.convert_to_period(self.region)
            
    
    def convert_to_period(self,dictionary):
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
        
        
    def flatten_list(list_to_flatten):
        """Returns a list with sublists removed"""
        return [item for sublist in list_to_flatten for item in sublist]

    ##################################################################
    ##################################################################
    ## POWER TO GAS, ELECTROLYSIS AND HYDRO DISPATCH
    ##################################################################
    
    def residual_energy(self,load_cutoff, load, energy_budget, pmin=0, pmax=None):
        """
        energy_budget > 0 is generation (hydro)
        energy_budget < 0 is load (P2G)
        """
        dct = (1 if energy_budget>0 else -1)
        return np.sum(np.clip(dct*load[dct*load>dct*(load_cutoff + pmin)] - dct*load_cutoff, a_min=pmin, a_max=pmax) - pmin) + len(load)*pmin - dct*energy_budget
    
    
    def dispatch_shape(load, load_cutoff, dct, pmin=0, pmax=None):
        """
        dct = 1 is generation (hydro)
        dct = -1 is load (P2G)
        """
        dispatch = np.zeros_like(load) - dct*pmin
        dispatch[dct*load>dct*(load_cutoff + pmin)] -= dct*(np.clip(dct*load[dct*load>dct*(load_cutoff + pmin)] - dct*load_cutoff, a_min=pmin, a_max=pmax) - pmin)
        return dispatch #negative if gen, positive if load
    
    def solve_for_load_cutoff(self,load, energy_budget, pmin=0, pmax=None):
        return optimize.root(self.residual_energy, x0=np.mean(load), args=(load, energy_budget, pmin, pmax))['x']
    
    def solve_for_dispatch_shape(self,load, energy_budget, pmin=0, pmax=None):
        load_cutoff = self.solve_for_load_cutoff(load, energy_budget, pmin, pmax)
        return self.dispatch_shape(load, load_cutoff, (1 if energy_budget>0 else -1), pmin, pmax)
    
    def dispatch_to_energy_budget(self,load, energy_budgets, dispatch_periods=None, pmins=0, pmaxs=None):
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
        return np.concatenate([self.solve_for_dispatch_shape(load_group, energy_budget, pmin, pmax)
            for load_group, energy_budget, pmin, pmax in zip(load_groups, energy_budgets, pmins, pmaxs)])
    
    ##################################################################
    ##################################################################
    ## GENERATOR DISPATCH (LOOKUP HEURISTIC)
    ##################################################################
    
    def schedule_generator_maintenance(self,load, pmaxs, annual_maintenance_rates, dispatch_periods=None, min_maint=0., max_maint=.15, load_ptile=99.8):
        pmax = np.max(pmaxs, axis=0) if len(pmaxs.shape) > 1 else pmaxs
        capacity_sum = sum(pmax)
        cap_by_group = np.sum(pmaxs, axis=1)
        maintenace_energy = np.dot(pmax, annual_maintenance_rates)*len(load)
        
        load_cut = np.percentile(load, load_ptile)
        
        group_cuts = list(np.where(np.diff(dispatch_periods)!=0)[0]+1)
        okay_for_maint = [np.all(group) for group in np.array_split(load<load_cut, group_cuts)]
        
        load_for_maint = np.copy(load)
        for ok, cut_start, cut_end in zip(okay_for_maint, [0]+group_cuts[:-1], group_cuts):
            if not ok:
                load_for_maint[cut_start:cut_end] = max(load)
        
        
        energy_allocation = self.dispatch_to_energy_budget(load_for_maint, -maintenace_energy, pmins=capacity_sum*min_maint, pmaxs=capacity_sum*max_maint)
        common_rates = [sum(group)/len(group)/float(cap) for group, cap in zip(np.array_split(energy_allocation, group_cuts), cap_by_group)]
        
        return np.array([common_rates]*len(pmax)).T
    
    def solve_gen_dispatch(self,load, pmax, marginal_cost, FORs, MORs, must_run, decimals=0, operating_reserves=0.03):
        must_run_index = np.nonzero(must_run)[0]
        dispat_index = np.nonzero(~must_run)[0]
        
        combined_rate = MORs + (1 - MORs) * FORs
        derated_capacity = np.array(np.round(pmax * (1 - combined_rate) * 10**decimals), dtype=int)
        
        derated_sum, must_run_sum = sum(derated_capacity), sum(derated_capacity[must_run_index])
        
        sorted_cost = np.argsort(marginal_cost)
        marginal_cost_order = np.concatenate(([mc for mc in sorted_cost if mc in must_run_index],
                                              [mc for mc in sorted_cost if mc in dispat_index]))
        
        full_mp = np.array([0] + self.flatten_list([[marginal_cost[i]]*derated_capacity[i] for i in marginal_cost_order]))
        full_pc = np.cumsum(full_mp)/10**decimals
        
        plt.plot(full_mp)
        
        lookup = np.array(np.clip(np.round(load * 10**decimals), a_min=must_run_sum, a_max=None), dtype=int)
        lookup_plus_reserves = np.array(np.clip(np.round(load * (1 + operating_reserves) * 10**decimals), a_min=must_run_sum, a_max=None), dtype=int)
        
        if max(lookup_plus_reserves)>derated_sum:
            raise ValueError('Gen dispatch resulted in unserved energy')
        
        market_price = full_mp[lookup_plus_reserves]
        market_price[np.where(load*10**decimals<must_run_sum)] = -1
        production_cost = full_pc[lookup]
        
        energy = np.array([np.sum(group) for group in 
                           np.array_split(np.cumsum(np.histogram(lookup, bins=derated_sum, range=(0, derated_sum))[0][-1:0:-1])[-1:0:-1],
                                          np.cumsum(derated_capacity[marginal_cost_order])[:-1])])[np.argsort(marginal_cost_order)] / 10**decimals
        
        return market_price, production_cost, energy, np.array(lookup / 10**decimals, dtype=float)
    
    def generator_stack_dispatch(self,load, pmaxs, marginal_costs, dispatch_periods=None, FOR=None, MOR=None, must_runs=None, periods_per_year=8760):
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
        
        load_groups = (load,) if dispatch_periods is None else np.array_split(load, np.where(np.diff(dispatch_periods)!=0)[0]+1)
        num_groups = len(load_groups)
            
        marginal_costs = np.tile(marginal_costs, (num_groups,1)) if len(marginal_costs.shape)==1 else marginal_costs
        pmaxs = np.tile(pmaxs, (num_groups,1)) if len(pmaxs.shape)==1 else pmaxs
        FOR = np.zeros_like(pmaxs) if FOR is None else (np.tile(FOR, (num_groups,1)) if len(FOR.shape)==1 else FOR)
        MOR = np.zeros_like(pmaxs) if MOR is None else MOR
        
        must_runs = np.zeros_like(pmaxs, dtype=bool) if must_runs is None else np.array(np.tile(must_runs, (num_groups,1)) if len(must_runs.shape)==1 else must_runs, dtype=bool)
        
        market_prices, production_costs, gen_dispatch_shape = [], [], []
        gen_energies = np.zeros(pmaxs.shape[1])
        for i, load_group in enumerate(load_groups):
            market_price, production_cost, gen_energy, shape = self.solve_gen_dispatch(load_group, pmaxs[i], marginal_costs[i], FOR[i], MOR[i], must_runs[i])
            market_prices += list(market_price)
            production_costs += list(production_cost)
            gen_dispatch_shape += list(shape)
            gen_energies += gen_energy
        
        gen_cf = gen_energies/pmaxs[i]/len(load)
        dispatch_results = dict(zip(['market_price', 'production_cost', 'gen_energies', 'gen_cf', 'gen_dispatch_shape'],
                                    [market_prices,    production_costs,   gen_energies,   gen_cf,   gen_dispatch_shape]))
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
    def __init__(self,id,**kwargs):
        self.id = id
        self.sql_id_table = 'DispatchFeeders'
        self.sql_data_table = 'DispatchFeedersData'
        self.interpolation_method = None
        self.extrapolation_method = None
        Abstract.__init__(self,self.id)  
        self.values = self.clean_timeseries('raw_values',inplace=False)
        self.values.sort(inplace=True)