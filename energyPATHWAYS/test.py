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


    def set_max_flex_loads(self, distribution_load):
        self.max_flex_load = defaultdict(dict)
        for geography in self.dispatch_geographies:
            for feeder in self.feeders:
                for period in self.periods:
                    start = period * self.opt_hours
                    stop = (period+1) * self.opt_hours - 1
                    if feeder !=0:
                        self.max_flex_load[period][(geography,feeder)] = util.df_slice(distribution_load, [geography, feeder, 2], [self.dispatch_geography, 'dispatch_feeder', 'timeshift_type']).iloc[start:stop].max().values[0] 
                    else:
                        self.max_flex_load[period][(geography,feeder)] = 0.0