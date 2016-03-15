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



def set_thermal_coefficients(self,year):
    row_index = pd.MultiIndex.from_product([self.geographies, self.thermal_dispatch_nodes], names=[self.geography, 'supply_node'])
    col_index = pd.multiIndex.from_product([self.dispatch_geographies])
    df = util.empty_df(index=row_index,columns=col_index)
    for geography in self.dispatch_geographies:
        for node_id in self.thermal_dispatch_nodes:
            resources = [x for x in self.thermal_dispatch_dict[geography]['generation'].keys() if x[0] == node_id]
            for resource in resources:
                location = resource[1]
                node = resource[0]
                df.loc[(location,node),(geography)] += self.thermal_dispatch_dict[geography]['generation'][resource]
                
                
def capacity_weights(self,year):
    weights = self.nodes[self.thermal_dispatch_node_id].values.loc[:,year].to_frame()
    for geography in self.dispatch_geographies:
        for resource in self.thermal_dispatch_dict[geography]['capacity'].keys():
            for node_id in self.thermal_nodes:
                if resource[0] == node_id:                 
                    loc_geo = resource[1]
                    self.thermal_dispatch_dict[geography]['capacity_weights'][resource] = util.index_slice(weights,[loc_geo,node_id],[self.geography,'supply_node']).sum().values