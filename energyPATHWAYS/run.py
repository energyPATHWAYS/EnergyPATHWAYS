# -*- coding: utf-8 -*-
"""
Created on Thu Jul 07 19:20:05 2016

@author: ryandrewjones
"""

import sys
import click
import os
import cPickle as pickle
import energyPATHWAYS.config as cfg
import energyPATHWAYS.util as util
from energyPATHWAYS.pathways_model import PathwaysModel
import energyPATHWAYS.shape as shape
import time
import datetime
import logging
import cProfile
import pdb
import traceback

model = None

def myexcepthook(exctype, value, tb):
    logging.error(''.join(traceback.format_tb(tb)))
    sys.__excepthook__(exctype, value, tb)
sys.excepthook = myexcepthook

@click.command()
@click.option('-p', '--path', type=click.Path(exists=True), help='working directory for energyPATHWAYS run')
@click.option('-c', '--config', default='config.INI', help='file name for the energyPATHWAYS configuration file')
@click.option('-u', '--pint', default='unit_defs.txt', help='file name for custom unit definitions for the library pint')
@click.option('-s', '--scenario', multiple=True, help='scenario name or id')
@click.option('-ld', '--load_demand/--no_load_demand', default=False, help='load a cached model with the demand side complete')
@click.option('--solve_demand/--no_solve_demand', default=True, help='solve the demand side of the model')
@click.option('-ls', '--load_supply/--no_load_supply', default=False, help='load a cached model with the demand and supply side complete')
@click.option('--solve_supply/--no_solve_supply', default=True, help='solve the supply side of the model')
@click.option('--pickle_shapes/--no_pickle_shapes', default=True, help='cache shapes after processing')
@click.option('--save_models/no_save_models', default=True, help='cashe models after running')
@click.option('--log_name', help='file name for the log file')
@click.option('--log_level', default='INFO', help='available levels are CRITICAL, ERROR, WARNING, INFO, or DEBUG')
@click.option('--stdout/--no_stdout', default=True, help='print logger to the command line')
@click.option('-a', '--api_run/--no_api_run', default=False)
def click_run(path, config, pint, scenario, load_demand, solve_demand, load_supply, solve_supply, pickle_shapes, save_models, log_name, log_level, stdout, api_run):
    run(path, config, pint, scenario, load_demand, solve_demand, load_supply, solve_supply, pickle_shapes, save_models, log_name, log_level, stdout, api_run)

def run(path, config, pint, scenario, load_demand=False, solve_demand=True, load_supply=False,
        solve_supply=True, pickle_shapes=True, save_models=True, log_name=None, log_level='INFO', stdout=True, api_run=False):
    global model
    cfg.initialize_config(path, config, pint)
    setuplogging(log_name, log_level, stdout)
    shape.init_shapes()
    scenario_id = get_scenario_id(scenario)
    
    logging.info('running scenario_id {}'.format(scenario_id))
    if api_run:
        util.update_status(scenario_id, 2)
    model = load_model(path, load_demand, load_supply, scenario_id)
    model.run(scenario_id,
              solve_demand=solve_demand and not (load_demand or load_supply),
              solve_supply=solve_supply and not load_supply,
              save_models=save_models)

    if api_run:
        util.update_status(scenario_id, 3)

def load_model(path, load_demand, load_supply, scenario_id):
    if load_supply:
        with open(os.path.join(path, str(scenario_id)+'_full_model_run.p'), 'rb') as infile:
            model = pickle.load(infile)
    elif load_demand:
        with open(os.path.join(path, str(scenario_id)+'_model.p'), 'rb') as infile:
            model = pickle.load(infile)
    else:
        model = PathwaysModel(scenario_id)
    return model

def get_scenario_id(scenario):
    if util.is_numeric(scenario):
        # from click, scenarios may come in as unicode
        scenario_id = int(scenario)
        assert scenario_id in cfg.scenario_dict
    else:
        assert scenario in cfg.scenario_dict.values()
        # turn scenario names into scenario IDs
        scenario_id = cfg.scenario_dict.keys()[cfg.scenario_dict.values().index(scenario)]
    return scenario_id

def setuplogging(log_name, log_level, stdout=True):
    log_name = '{} energyPATHWAYS.log'.format(str(datetime.datetime.now())[:-4].replace(':', '.')) if log_name is None else log_name
    logging.basicConfig(filename=log_name, level=log_level)
    if stdout:
        soh = logging.StreamHandler(sys.stdout)
        soh.setLevel(log_level)
        logger = logging.getLogger()
        logger.addHandler(soh)

if __name__ == "__main__":
    workingdir = r'C:\github\energyPATHWAYS\us_model_example'
    os.chdir(workingdir)
    config = 'config.INI'
    pint = 'unit_defs.txt'
    scenario = 5

    t = time.time()
    run(workingdir, config, pint, scenario, load_demand=False, solve_demand=True, load_supply=False, solve_supply=True, pickle_shapes=True, save_models=True, api_run=False)
    print time.time() - t

#    t = time.time()
#    cProfile.run('run(path, config, pint, scenario, load_demand=False, solve_demand=True, load_supply=False, solve_supply=True, pickle_shapes=True, save_models=True, api_run=False)', filename='full_run.profile')
#    print time.time() - t