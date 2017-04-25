# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 19:11:59 2015

@author: Ben
"""

import pandas as pd
import numpy as np
import util
import config as cfg
import os
import logging
import time
import inspect
import csv
from collections import defaultdict, OrderedDict

class Output(object):
    def __init__(self):
        pass
    
    def return_cleaned_output(self, output_type):
        if not hasattr(self, output_type):
            return None
        elif getattr(self,output_type) is None:
            print "%s is not calculated in this model run" %output_type
            return None
        elif type(getattr(self, output_type)) is not pd.core.frame.DataFrame:
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

    @staticmethod
    def clean_df(df, stack_years=False):
        if type(df) is not pd.core.frame.DataFrame:
            raise ValueError('output_type must be a pandas dataframe')
        if stack_years and 'year' not in df.index.names:
            df = df.stack()
            util.replace_index_name(df,'year')
            df.columns = ['value']
        if 'year' in df.index.names:
            df = df[df.index.get_level_values('year')>=int(cfg.cfgfile.get('case','current_year'))]
        dct = cfg.outputs_id_map
        index = df.index
        try:
            index.set_levels([[dct[name].get(item, item) for item in level] for name, level in zip(index.names, index.levels)], inplace=True)
            index.names = [x.upper() if isinstance(x, basestring) else x for x in index.names]
        except:
            pass
        if isinstance(df.columns,pd.MultiIndex):
            columns = df.columns
            columns.set_levels([[dct[name].get(item, item) for item in level] for name, level in zip(columns.names, columns.levels)], inplace=True)
            columns.names = [x.upper() if isinstance(x, basestring) else x for x in columns.names]
        else:
            df.columns = [x.upper() if isinstance(x, basestring) else x for x in df.columns]        
        return df

    @staticmethod
    def write(df, file_name, path):
        if not os.path.exists(path):
            os.mkdir(path)
        
        tries = 1
        while True:
            try:
                if os.path.isfile(os.path.join(path, file_name)):
                    # append and don't write header if the file already exists
                    df.to_csv(os.path.join(path, file_name), header=False, mode='ab')
                else:
                    df.to_csv(os.path.join(path, file_name), header=True, mode='w')
                return
            except Exception as e:
                logging.error('file {} cannot be written: {}'.format(file_name, e))
                if tries>6:
                    raise
                elif tries>=4:
                    raw_input('Close file {} and press enter to continue...'.format(file_name))
                elif tries<4:
                    logging.error('waiting {} seconds...'.format(4**tries))
                    time.sleep(4**tries)
                tries += 1

    @staticmethod
    def writeobj(obj, write_directory=None, name=None, clean=False):
        if name is None:
            name = Output._format_name(obj)

        if write_directory is None:
            write_directory = "\\\\?\\" + cfg.workingdir
        
        if not os.path.exists(write_directory):
            os.makedirs(write_directory)
        
        if util.is_numeric(obj) or (type(obj) is str) or (type(obj) is bool):
            Output.csvwrite(os.path.join(write_directory, 'vars.csv'), [[name, obj]], writetype='ab')
        elif (type(obj) == dict) or (type(obj) == defaultdict) or (type(obj) == OrderedDict):
            Output._writedict(obj, write_directory, name)
        elif type(obj) == list or type(obj) == tuple:
            Output._writelist(obj, write_directory, name)
        elif type(obj) == pd.core.frame.DataFrame:
            obj = Output.clean_df(obj)
            obj.to_csv(os.path.join(write_directory, str(name)+'.csv'))
        elif type(obj) is pd.tseries.index.DatetimeIndex:
            pd.DataFrame(obj).to_csv(os.path.join(write_directory, str(name)+'.csv'))
        elif inspect.isclass(type(obj)) and hasattr(obj, '__dict__'):
            Output._writeclass(obj, write_directory, name)

    @staticmethod
    def _writelist(obj, write_directory, name):
        csv_elements = [item for item in obj if util.is_numeric(item) or type(item) == str]
        Output.csvwrite(os.path.join(write_directory, 'vars.csv'), [[name] + csv_elements], writetype='ab')

    @staticmethod
    def _writedict(obj, write_directory, name):
        if not len(obj):
            return
        # two types of dictionaries one is key and class obj value
        if all([util.is_numeric(val) or (type(val) is str) or (type(val) is bool) or (type(val) is list) or (type(val) == tuple) or (type(val) == np.ndarray) for val in obj.values()]):
            Output.csvwrite(os.path.join(write_directory, str(name)+'.csv'), obj.items())
        else:
            new_directory = os.path.join(write_directory, str(name))
            for key, value in obj.items():
                Output.writeobj(value, new_directory, Output._clean_string(key))

    @staticmethod
    def _writeclass(obj, write_directory, name):
        new_name = str(Output._format_name(obj, default=name))
        new_directory = os.path.join(write_directory, new_name)
        attnames = [attname for attname in vars(obj) if not attname.startswith('_')]
        atts = [getattr(obj, attname) for attname in attnames]
        for attname, att in zip(attnames, atts):
            Output.writeobj(att, new_directory, Output._clean_string(attname))

    @staticmethod
    def _get_name(obj):
        if hasattr(obj, 'long_name'):
            return getattr(obj, 'long_name')
        elif hasattr(obj, 'name'):
            return getattr(obj, 'name')
        elif inspect.isclass(type(obj)) and hasattr(obj, '__dict__'):
            return obj.__module__.split('.')[-1]
        else:
            return None

    @staticmethod
    def _format_name(obj, default=None):
        name = Output._get_name(obj)
        if default is None or name==default:
            return Output._clean_string(name)
        
        if util.is_numeric(default):
            name = str(default) + '--' + str(name)
        else:
            name = str(default)
        
        return Output._clean_string(name)

    @staticmethod
    def _clean_string(s):
        s = str(s).rstrip().lstrip()
        s = s.replace('"', '').replace('<', 'L').replace('>', 'G').replace('/', '-').replace('\\', '-').replace('\n', '').replace('\r', '')
        return s

    @staticmethod
    def csvwrite(path, data, writetype='ab'):
        '''Writes a CSV from a series of data
        '''
        with open(path, writetype) as outfile:
            csv_writer = csv.writer(outfile, delimiter=',')
            for row in data:
                if util.is_iterable(row):
                    csv_writer.writerow(row)
                else:
                    csv_writer.writerow([row])