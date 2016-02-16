# -*- coding: utf-8 -*-
"""
Created on Mon Feb 15 22:06:19 2016

@author: Ben
"""
import util
import numpy as np 
from datamapfunctions import Abstract
import copy


class Dispatch(object):
    def __init__(self, **kwargs):
        #TODO replace 1 with a config parameter
        for col, att in util.object_att_from_table('DispatchConfig',1):
            setattr(self, col, att)
        self.opt_hours = util.sql_read_table('StorageOptHours','hours', id=self.opt_hours)
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