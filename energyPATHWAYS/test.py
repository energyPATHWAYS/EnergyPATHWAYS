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


def group_linked_output(self, supply_link, levels_to_keep=None):
    levels_to_keep = cfg.output_demand_levels if levels_to_keep is None else levels_to_keep
#        levels_to_keep = ['census region', 'sector', 'subsector', 'final_energy', 'year', 'technology']
#        year_df_list = []
    levels_to_keep = [x for x in levels_to_keep if x in self.outputs.energy.index.names]
    demand_df = self.outputs.energy.groupby(level=levels_to_keep).sum()
#        years =  list(set(supply_link.index.get_level_values('year')))
#        for year in years:
#            print year
    geography_df_list = []
    for geography in self.geographies:
        if geography in supply_link.index.get_level_values(self.geography):
            supply_indexer = util.level_specific_indexer(supply_link,[self.geography],[geography])
            demand_indexer = util.level_specific_indexer(demand_df,[self.geography],[geography])
#            levels = [x for x in ['supply_node', self.geography + "_supply",'final_energy'] if x in supply_link.index.names]
            supply_df = supply_link.loc[supply_indexer,:]           
#            if len(levels):            
#                supply_df = supply_df.groupby(level=levels).filter(lambda x: x.sum()!=0)
            geography_df =  util.DfOper.mult([demand_df.loc[demand_indexer,:],supply_df])
#                names = geography_df.index.names
#                geography_df = geography_df.reset_index().dropna().set_index(names)
            geography_df_list.append(geography_df)
#            year_df = pd.concat(geography_df_list)
#            year_df_list.append(year_df)
    df = pd.concat(geography_df_list)      
    return df