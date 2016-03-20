# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 19:11:59 2015

@author: Ben
"""

import pandas as pd
import util
from config import cfg

class Output(object):
    def __init__(self):
        pass
    
    def return_cleaned_output(self, output_type):
        if not hasattr(self, output_type):
            return None
        if type(getattr(self, output_type)) is not pd.core.frame.DataFrame:
            raise ValueError('output_type must be a pandas dataframe')
        cleaned_output = getattr(self, output_type).copy()
        
        dct = cfg.outputs_id_map
        index = cleaned_output.index
        index.set_levels([[dct[name].get(item, item) for item in level] for name, level in zip(index.names, index.levels)], inplace=True)
        index.names = [x.upper() if isinstance(x, basestring) else x for x in index.names]
        cleaned_output.columns = [x.upper() if isinstance(x, basestring) else x for x in cleaned_output.columns]
        
        return cleaned_output

