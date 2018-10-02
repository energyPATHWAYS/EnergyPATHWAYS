# -*- coding: utf-8 -*-
"""
Created on Tue Oct 27 15:36:21 2015

@author: Ben
"""

import config as cfg
import pandas as pd
import util
from datamapfunctions import Abstract,DataMapFunctions
import numpy as np
import inspect
from util import DfOper

class SupplyMeasure(object):
    def __init__(self):
        pass
    
class CO2PriceMeasure(Abstract):
    def __init__(self, id, **kwargs):
        self.id = id 
        self.sql_id_table = 'CO2PriceMeasures'
        self.sql_data_table = 'CO2PriceMeasuresData'
        Abstract.__init__(self, self.id, primary_key='id', data_id_key='parent_id')
        self.input_type = 'intensity'

    def calculate(self):
        self.remap(converted_geography=cfg.supply_primary_geography)
        self.values.sort_index(inplace=True)
    
class BlendMeasure(Abstract):
    def __init__(self, id, scenario=None):
        self.id = id
        self.sql_id_table = 'BlendNodeBlendMeasures'
        self.sql_data_table = 'BlendNodeBlendMeasuresData' 
        self.scenario = scenario
        Abstract.__init__(self, self.id, data_id_key='parent_id')
    
    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        self.input_type = 'intensity'
        self.remap(converted_geography=cfg.supply_primary_geography)
        self.values['supply_node'] = self.supply_node_id
        self.values.set_index('supply_node',append=True,inplace=True)
        primary_geography = cfg.supply_primary_geography
        self.values = util.reindex_df_level_with_new_elements(self.values, primary_geography, cfg.geo.geographies[primary_geography],fill_value=0.0)


class RioBlendMeasure(DataMapFunctions):
    def __init__(self, id,raw_values):
        self.id = id
        self.raw_values = raw_values
        self.raw_values = self.raw_values.replace(np.inf,0)
        self.raw_values = self.raw_values.fillna(0)
        self.input_type = 'intensity'
        self.geography = cfg.rio_geography
        self.interpolation_method = 'linear_interpolation'
        self.extrapolation_method = 'nearest'
        self.geography_map_key = None


    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        try:
            self.remap(converted_geography=cfg.supply_primary_geography)
        except:
            pdb.set_trace()
        self.values['supply_node'] = self.id
        self.values.set_index('supply_node', append=True, inplace=True)
        primary_geography = cfg.supply_primary_geography
        self.values = util.reindex_df_level_with_new_elements(self.values, primary_geography,
                                                              cfg.geo.geographies[primary_geography], fill_value=0.0)
        
class ExportMeasure(Abstract):
    def __init__(self,id):
        self.id = id
        Abstract.__init__(self, self.id)
        
class StockMeasure(Abstract):
    def __init__(self,id):
        self.id = id
        self.input_type = 'total'
        Abstract.__init__(self, self.id)
    
class StockSalesMeasure(StockMeasure):
    def __init__(self,id, input_type):
        StockMeasure.__init__(self,id)