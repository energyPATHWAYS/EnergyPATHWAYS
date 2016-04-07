# -*- coding: utf-8 -*-
"""
Created on Tue Oct 27 15:36:21 2015

@author: Ben
"""

import pandas as pd
import util
from datamapfunctions import Abstract
import numpy as np
import inspect
from util import DfOper

class SupplyMeasure(object):
    def __init__(self):
        pass
    
class BlendMeasure(Abstract):
    def __init__(self,id):
        self.id = id
        self.sql_id_table = 'BlendNodeBlendMeasures'
        self.sql_data_table = 'BlendNodeBlendMeasuresData'       
        Abstract.__init__(self, self.id, data_id_key='parent_id')
    
    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        self.input_type = 'intensity'
        self.remap()
        self.values['supply_node'] = self.supply_node_id
        self.values.set_index('supply_node',append=True,inplace=True)
        
        
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