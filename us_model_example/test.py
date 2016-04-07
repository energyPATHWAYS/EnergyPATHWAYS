# -*- coding: utf-8 -*-
"""
Created on Mon Mar 07 14:33:35 2016

@author: Ben
"""

# -*- coding: utf-8 -*-
"""
Created on Fri Mar 04 10:23:57 2016

@author: Ben
"""
import types
from energyPATHWAYS import parallel
#import copy
#import numpy as np
#from collections import defaultdict
#from energyPATHWAYS import util
#import pandas as pd
#import os 
#import pickle
#from energyPATHWAYS import config
#

def run_optimization(self,parallel=False):
    state_of_charge = self.run_year_to_month_allocation()
    alloc_start_state_of_charge, alloc_end_state_of_charge = state_of_charge[0], state_of_charge[1]
    self.alloc_start_state_of_charge = alloc_start_state_of_charge
    self.alloc_end_state_of_charge = alloc_end_state_of_charge
    #replace with multiprocessing if parallel
    results = []
    for period in self.periods:
        p = multiprocessing.Process(target=parallel.run_dispatch_optimization, args=(self,alloc_start_state_of_charge, alloc_end_state_of_charge,period))
        results.append(p)
        p.start()
    for period in self.periods:      
        result = results[0]
        self.export_storage_results(result, period) 
        self.export_flex_load_results(result, period)