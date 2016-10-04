# -*- coding: utf-8 -*-
"""
Created on Thu Jul 07 19:20:05 2016

@author: ryandrewjones
"""

import sys
import signal
import click
import os
import cPickle as pickle
import energyPATHWAYS.config as cfg
import energyPATHWAYS.util as util
from energyPATHWAYS.pathways_model import PathwaysModel
import energyPATHWAYS.shape as shape
from energyPATHWAYS.outputs import Output
import csv
import time
import datetime
import logging
import cProfile
import traceback
import pandas as pd

# set up a dummy model
path = os.getcwd()
config = 'config.INI'
pint = 'unit_defs.txt'
scenario_id = 1

cfg.initialize_config(path, config, pint, _log_name='log.txt')
cfg.primary_geography = 'intersection_id'
    
model = PathwaysModel(scenario_id, api_run=False)
model.run(scenario_id, solve_demand=False, solve_supply=False, save_models=False, append_results=False)

demand = model.demand
demand.add_drivers()

existing_geo_map_key_ids, existing_geo_map_key_names = zip(*util.sql_read_table('GeographyMapKeys'))
next_map_key_id = max(existing_geo_map_key_ids)+1
next_geo_map_id = max(util.sql_read_table('GeographyMap', 'id'))+1

###############################################
# user inputs
driver_ids_to_make_map_keys = [38, 39, 40, 41, 42, 43, 44, 45]
basis_year_for_map_key = int(cfg.cfgfile.get('case', 'current_year'))

###############################################

# make our new map keys
GeographyMapKeys = [['id', 'name']]
GeographyMap_columns = ['intersection_id', 'geography_map_key_id', 'value', 'id']
GeographyMap = []
for driver_id in driver_ids_to_make_map_keys:
    driver = demand.drivers[driver_id]
    demand.remap_driver(driver) # remaps to our new super detailed geography
    values = util.df_slice(driver.values, basis_year_for_map_key, 'year')
    
    if values.index.nlevels>1:
        levels_to_remove = [n for n in values.index.names if n!='intersection_id']
        values = util.remove_df_levels(values, levels_to_remove)
    
    new_key_name = driver.name
    if new_key_name in existing_geo_map_key_names:
        raise ValueError('driver name {} is already in the existing map keys, please rename driver id {}'.format(driver.name, driver.id))
    
    GeographyMapKeys.append([next_map_key_id, new_key_name])
    
    values = values.reset_index()
    values['id'] = range(next_geo_map_id, next_geo_map_id+len(values))
    values['geography_map_key_id'] = next_map_key_id
    
    GeographyMap.append(values)
    next_geo_map_id += len(values)
    next_map_key_id+=1

output = pd.concat(GeographyMap)[GeographyMap_columns]
output.to_csv(os.path.join(path, 'outputs', 'GeographyMap.csv'), index=False)

with open(os.path.join(path, 'outputs', 'GeographyMapKeys.csv'), 'wb') as outfile:
    csvwriter = csv.writer(outfile, delimiter=',')
    for row in GeographyMapKeys:
        csvwriter.writerow(row)
