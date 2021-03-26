# -*- coding: utf-8 -*-
"""
Created on Tue Oct 27 15:36:21 2015

@author: Ben
"""

from energyPATHWAYS import config as cfg
import pandas as pd
from energyPATHWAYS import util
import numpy as np
import pdb
from energyPATHWAYS. geomapper import GeoMapper
from energyPATHWAYS.generated import schema
from energyPATHWAYS.data_object import DataObject

class SupplyMeasure(object):
    def __init__(self):
        pass
    
class CO2PriceMeasure(schema.CO2PriceMeasures):
    def __init__(self, name, scenario=None):
        schema.CO2PriceMeasures.__init__(self, name=name, scenario=scenario)
        self.init_from_db(name, scenario)
        self.scenario = scenario
        self.input_type = 'intensity'

    def calculate(self):
        self.remap(converted_geography=GeoMapper.supply_primary_geography)
        self.values.sort_index(inplace=True)
    
class BlendMeasure(schema.BlendNodeBlendMeasures):
    def __init__(self, name, scenario=None):
        schema.BlendNodeBlendMeasures.__init__(self, name=name, scenario=scenario)
        self.init_from_db(name, scenario)
        self.scenario = scenario
        self.input_type = 'intensity'
    
    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        self.remap(converted_geography=GeoMapper.supply_primary_geography)
        self.values['supply_node'] = self.supply_node
        self.values.set_index('supply_node',append=True,inplace=True)
        primary_geography = GeoMapper.supply_primary_geography
        self.values = util.reindex_df_level_with_new_elements(self.values, primary_geography, GeoMapper.geography_to_gau[primary_geography],fill_value=0.0)


class RioBlendMeasure(DataObject):
    def __init__(self, name,raw_values):
        self.name = name
        self.raw_values = raw_values
        self.raw_values = self.raw_values.replace(np.inf,0)
        self.raw_values = self.raw_values.fillna(0)
        self.input_type = 'intensity'
        self.geography = cfg.rio_geography
        self.interpolation_method = 'linear_interpolation'
        self.extrapolation_method = 'nearest'
        self.geography_map_key = None
        self._cols = []


    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        self.remap(converted_geography=GeoMapper.supply_primary_geography)
        self.values['supply_node'] = self.name
        self.values.set_index('supply_node', append=True, inplace=True)
        primary_geography = GeoMapper.supply_primary_geography
        self.values = util.reindex_df_level_with_new_elements(self.values, primary_geography,
                                                              GeoMapper.geography_to_gau[primary_geography], fill_value=0.0)
        
