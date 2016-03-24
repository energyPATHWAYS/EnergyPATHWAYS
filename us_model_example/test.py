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
import copy
import numpy as np
from collections import defaultdict
from energyPATHWAYS import util
import pandas as pd
import os 
import pickle
from energyPATHWAYS import config




def solve_storage_and_flex_load_optimization(self,year):
    for geography in self.dispatch_geographies:
        for feeder in self.dispatch_feeders:
            load_indexer = util.level_specific_indexer(self.distribution_load, [self.dispatch_geography, 'dispatch_feeder','timeshift_type'], [geography, feeder, 2])
            self.distribution_load.loc[load_indexer,: ] += util.df_slice(self.dispatch.dist_storage_df,[geography, feeder, 'charge'], [self.dispatch_geography, 'dispatch_feeder', 'charge_discharge']).values
            self.distribution_load.loc[load_indexer,: ] += util.df_slice(self.dispatch.flex_load_df,[geography, feeder], [self.dispatch_geography, 'dispatch_feeder']).values             
            gen_indexer = util.level_specific_indexer(self.distribution_gen,[self.dispatch_geography, 'dispatch_feeder','timeshift_type'], [geography, feeder, 2])
            self.distribution_gen.loc[gen_indexer,: ] += util.df_slice(self.dispatch.dist_storage_df,[geography, feeder, 'discharge'], [self.dispatch_geography, 'dispatch_feeder', 'charge_discharge']).values
    for geography in self.dispatch.geographies:       
        load_indexer = util.level_specific_indexer(self.bulk_load, [self.dispatch_geography], [geography])
        self.bulk_load.loc[load_indexer,: ] += util.df_slice(self.dispatch.bulk_storage_df,[geography,'charge'], [self.dispatch_geography, 'charge_discharge']).values
        gen_indexer = util.level_specific_indexer(self.bulk_gen, [self.dispatch_geography], [geography])
        self.bulk_gen.loc[gen_indexer,: ] += util.df_slice(self.dispatch.bulk_storage_df,[geography,'discharge'], [self.dispatch_geography, 'charge_discharge']).values    
    self.update_net_load_signal()  