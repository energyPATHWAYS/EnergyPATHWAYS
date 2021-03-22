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
import re
import gzip
from collections import defaultdict, OrderedDict
import cPickle as pickle
import pdb
from geomapper import GeoMapper

ZIP_PATTERN = re.compile('.*\.gz$', re.IGNORECASE)

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
        cleaned_output = Output.clean_df(getattr(self, output_type).copy())
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
            df = df[df.index.get_level_values('year')>=cfg.getParamAsInt('current_year', section='TIME')]
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
    
    @staticmethod
    def clean_rio_df(df, stack_years=False,add_geography=True,replace_gau=True):
        if type(df) is not pd.core.frame.DataFrame:
            raise ValueError('output_type must be a pandas dataframe')
        if stack_years and 'year' not in df.index.names:
            df = df.stack()
            util.replace_index_name(df,'year')
            df.columns = ['value']
        dct = cfg.outputs_id_map
        df = df.reset_index()
        for col_name in df.columns.get_level_values(0):
            # if col_name in cfg.outputs_id_map.keys():
            #     try:
            #         df[col_name] = [dct[col_name][x] if x in dct[col_name].keys() else x for x in df[col_name].values]
            #     except:
            #         pdb.set_trace()
            if col_name in GeoMapper.geography_to_gau.keys():
                if replace_gau:
                    util.replace_column_name(df,'gau',col_name)
                if add_geography:
                    df['geography'] = col_name
        df.columns = [x.lower() for x in df.columns]
        return df

    @staticmethod
    def pickle(obj, file_name, path):
        if not os.path.exists(path):
            os.mkdir(path)

        with open(os.path.join(path, file_name), 'wb') as outfile:
            pickle.dump(obj, outfile, pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def write(df, file_name, path, compression=None, index=True, append_when_existing=True):
        # roughly follows the solutions here: http://stackoverflow.com/questions/11114492/check-if-a-file-is-not-open-not-used-by-other-process-in-python
        # note that there is still a small, but real chance of a race condition causing an error error, thus this is "safer" but not safe
        if not os.path.exists(path):
            while True:
                try:
                    os.mkdir(path)
                    break
                except Exception as e:
                    logging.info(e)
                    raw_input('Please press any key to continue...')

        if compression == 'gzip':
            file_name += '.gz'

        if os.path.isfile(os.path.join(path, file_name)) and append_when_existing:
            tries = 1
            while True:
                try:
                    # rename the file back and forth to see if it is being used
                    os.rename(os.path.join(path, file_name), os.path.join(path, "_" + file_name))
                    os.rename(os.path.join(path, "_" + file_name), os.path.join(path, file_name))
                    # append and don't write header because the file already exists
                    df.to_csv(os.path.join(path, file_name), header=False, mode='a', compression=compression, index=index)
                    return
                except OSError:
                    wait_time = min(60, 2 ** tries)
                    logging.error('waiting {} seconds to try to write {}...'.format(wait_time,file_name))
                    time.sleep(wait_time)
                    if tries >= 60:
                        raise
                    tries += 1
        else:
            df.to_csv(os.path.join(path, file_name), header=True, mode='w', compression=compression, index=index)

    @staticmethod
    def write_rio(df, file_name, path, compression=None, index=True, force_lower=True, update=False):
        # roughly follows the solutions here: http://stackoverflow.com/questions/11114492/check-if-a-file-is-not-open-not-used-by-other-process-in-python
        # note that there is still a small, but real chance of a race condition causing an error error, thus this is "safer" but not safe
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except:
                pdb.set_trace()

        if compression == 'gzip':
            file_name += '.gz'
        elif compression == None:
            pass
        else:
            raise ValueError("unknown compression type input")

        for col in df.columns:
            if df[col].dtype == np.object:
                df[col] = df[col].str.lower()

        if os.path.isfile(os.path.join(path, file_name)):
            tries = 1
            while True:
                try:
                    # rename the file back and forth to see if it is being used
                    os.rename(os.path.join(path, file_name), os.path.join(path, "_" + file_name))
                    os.rename(os.path.join(path, "_" + file_name), os.path.join(path, file_name))
                    # append and don't write header because the file already exists
                    if update:
                        old_df = pd.read_csv(os.path.join(path, file_name))
                        df = pd.concat([old_df,df])
                        df.drop_duplicates(subset=[x for x in df.columns if x !='value'],keep='last')
                    df.to_csv(os.path.join(path, file_name), header=False, mode='a', compression=compression, index=index)
                    return
                except OSError:
                    wait_time = min(30, 2 ** tries) * np.random.rand()
                    logging.error('waiting {} seconds to try to write {}...'.format(wait_time))
                    time.sleep(wait_time)
                    if tries >= 30:
                        raise
                    tries += 1
        else:
            df.to_csv(os.path.join(path, file_name), header=True, mode='w', compression=compression, index=index)

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
    def csvwrite(path, data, writetype='a'):
        '''Writes a CSV from a series of data
        '''
        with open(path, writetype) as outfile:
            csv_writer = csv.writer(outfile, delimiter=',')
            for row in data:
                if util.is_iterable(row):
                    csv_writer.writerow(row)
                else:
                    csv_writer.writerow([row])


def delete_csv_files_in_folder(folder):
    if not os.path.exists(folder):
        return
    for file_name in os.listdir(folder):
        if file_name[-4:] == '.csv' or file_name[-3:] == '.gz':
            os.remove(os.path.join(folder, file_name))

def check_valid_gzip(path):
    try:
        with gzip.open(path, 'rb') as infile:
            csvreader = csv.reader(infile, delimiter=',')
            csvreader.next()
        return True
    except IOError:
        return False

def append_write(write_from, write_to):
    write_to_already_exists = os.path.isfile(write_to)
    # for some reason sometimes the gzip fails and it's actually a csv file with a .gz ending
    open_fun = gzip.open if check_valid_gzip(write_from) else open
    with open_fun(write_from, 'rb') as infile:
        csvreader = csv.reader(infile, delimiter=',')
        if write_to_already_exists:
            # get rid of the header row in this case
            csvreader.next()
        with open(write_to, 'ab') as outfile:
            csvwriter = csv.writer(outfile, delimiter=',')
            for row in csvreader:
                csvwriter.writerow(row)

def traverse_files(input_directory, output_directory):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    for f in os.listdir(input_directory):
        if re.match(ZIP_PATTERN, f):
            print "        {}".format(f)
            append_write(os.path.join(input_directory, f), os.path.join(output_directory, f[:-3])) #drop the .gz
        elif os.path.isdir(os.path.join(input_directory, f)):
            traverse_files(os.path.join(input_directory, f), os.path.join(output_directory, f))

def aggregate_scenario_results(scenarios, clear_results=True):
    logging.info('Aggregating run results')
    for results_folder in ['combined_outputs', 'demand_outputs', 'supply_outputs', 'dispatch_outputs']:
        agg_results_path = os.path.join(cfg.workingdir, '_aggregate_outputs', results_folder)
        util.makedirs_if_needed(agg_results_path)

        if clear_results:
            delete_csv_files_in_folder(agg_results_path)

        for scenario in util.ensure_iterable(scenarios):
            scenario_results = os.path.join(cfg.workingdir, scenario, results_folder)
            if not os.path.exists(scenario_results):
                continue
            print "    {}.{}".format(scenario, results_folder)
            traverse_files(scenario_results, agg_results_path)