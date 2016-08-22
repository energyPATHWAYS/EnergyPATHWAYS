# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 19:11:59 2015

@author: Ben
"""

import pandas as pd
import util
import config as cfg

class Output(object):
    def __init__(self):
        pass
    
    def return_cleaned_output(self, output_type):
        if not hasattr(self, output_type):
            return None
        if type(getattr(self, output_type)) is not pd.core.frame.DataFrame:
            raise ValueError('output_type must be a pandas dataframe')
        cleaned_output = getattr(self, output_type).copy()
        if 'year' in cleaned_output.index.names:
            cleaned_output = cleaned_output[cleaned_output.index.get_level_values('year')>=int(cfg.cfgfile.get('case','current_year'))]
        dct = cfg.outputs_id_map
        index = cleaned_output.index
        index.set_levels([[dct[name].get(item, item) for item in level] for name, level in zip(index.names, index.levels)], inplace=True)
        index.names = [x.upper() if isinstance(x, basestring) else x for x in index.names]
        if isinstance(cleaned_output.columns,pd.MultiIndex):
            columns = cleaned_output.columns
            columns.set_levels([[dct[name].get(item, item) for item in level] for name, level in zip(columns.names, columns.levels)], inplace=True)
            columns.names = [x.upper() if isinstance(x, basestring) else x for x in columns.names]
        else:
            cleaned_output.columns = [x.upper() if isinstance(x, basestring) else x for x in cleaned_output.columns]        
        return cleaned_output

    def clean_df(self, df):
        if type(df) is not pd.core.frame.DataFrame:
            raise ValueError('output_type must be a pandas dataframe')
        if 'year' in df.index.names:
            df = df[df.index.get_level_values('year')>=int(cfg.cfgfile.get('case','current_year'))]
        dct = cfg.outputs_id_map
        index = df.index
        index.set_levels([[dct[name].get(item, item) for item in level] for name, level in zip(index.names, index.levels)], inplace=True)
        index.names = [x.upper() if isinstance(x, basestring) else x for x in index.names]
        if isinstance(df.columns,pd.MultiIndex):
            columns = df.columns
            columns.set_levels([[dct[name].get(item, item) for item in level] for name, level in zip(columns.names, columns.levels)], inplace=True)
            columns.names = [x.upper() if isinstance(x, basestring) else x for x in columns.names]
        else:
            df.columns = [x.upper() if isinstance(x, basestring) else x for x in df.columns]        
        return df