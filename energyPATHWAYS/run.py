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
import traceback

model = None
run_start_time = time.time()

def myexcepthook(exctype, value, tb):
    logging.error(''.join(traceback.format_tb(tb)))
    sys.__excepthook__(exctype, value, tb)
sys.excepthook = myexcepthook

@click.command()
@click.option('-p', '--path', type=click.Path(exists=True), help='Working directory for energyPATHWAYS run.')
@click.option('-c', '--config', default='config.INI', help='File name for the energyPATHWAYS configuration file.')
@click.option('-u', '--pint', default='unit_defs.txt', help='File name for custom unit definitions for the library pint.')
@click.option('-s', '--scenario', type=str, help='Scenario ids [example: 1,3,5]')
@click.option('-ld', '--load_demand/--no_load_demand', default=False, help='Load a cached model with the demand side complete.')
@click.option('--solve_demand/--no_solve_demand', default=True, help='Solve the demand side of the model.')
@click.option('-ls', '--load_supply/--no_load_supply', default=False, help='Load a cached model with the demand and supply side complete.')
@click.option('--solve_supply/--no_solve_supply', default=True, help='Solve the supply side of the model.')
@click.option('--pickle_shapes/--no_pickle_shapes', default=True, help='Cache shapes after processing.')
@click.option('--save_models/--no_save_models', default=True, help='Cashe models after running.')
@click.option('--log_name', help='File name for the log file.')
@click.option('-a', '--api_run/--no_api_run', default=False)
@click.option('-d', '--debug/--no_debug', default=False, help='On error the model will exit into an ipython debugger.')
def click_run(path, config, pint, scenario, load_demand, solve_demand, load_supply, solve_supply, pickle_shapes, save_models, log_name, api_run, debug):
    if debug:
        import ipdb
        with ipdb.launch_ipdb_on_exception():
            run(path, config, pint, scenario, load_demand, solve_demand, load_supply, solve_supply, pickle_shapes, save_models, log_name, api_run)
    else:
        run(path, config, pint, scenario, load_demand, solve_demand, load_supply, solve_supply, pickle_shapes, save_models, log_name, api_run)

def run(path, config, pint, scenario, load_demand=False, solve_demand=True, load_supply=False,
        solve_supply=True, pickle_shapes=True, save_models=True, log_name=None, api_run=False):
    global model
    cfg.initialize_config(path, config, pint, log_name)
    shape.init_shapes()
    
    scenario_ids = parse_scenario_ids(scenario)
    logging.info('Scenario_ids run list = {}'.format(scenario_ids))
    for scenario_id in scenario_ids:
        scenario_start_time = time.time()
        logging.info('Starting scenario_id {}'.format(scenario_id))
        if api_run:
            util.update_status(scenario_id, 2)
        model = load_model(path, load_demand, load_supply, scenario_id)
        model.run(scenario_id,
                  solve_demand=solve_demand and not (load_demand or load_supply),
                  solve_supply=solve_supply and not load_supply,
                  save_models=save_models,
                  append_results=True if scenario_id!=scenario_ids[0] else False)
    
        if api_run:
            util.update_status(scenario_id, 3)
        logging.info('EnergyPATHWAYS run for scenario_id {} successful!'.format(scenario_id))
        logging.info('Scenario calculation time {} seconds'.format(time.time() - scenario_start_time))
    logging.info('Total calculation time {} seconds'.format(time.time() - run_start_time))
    logging.shutdown()
    logging.getLogger(None).handlers = [] # necessary to totally flush the logger

def parse_scenario_ids(scenario):
    if scenario is None or len(str(scenario))==0:
        return []
    if (type(scenario) is not tuple) and (type(scenario) is not list):
        scenario = str(scenario).split(',')
    return [int(str(s).rstrip().lstrip()) for s in scenario]

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

if __name__ == "__main__":
    workingdir = r'C:\github\energyPATHWAYS\us_model_example'
    os.chdir(workingdir)
    config = 'config.INI'
    pint = 'unit_defs.txt'
    scenario = 1
    
    run(workingdir, config, pint, scenario, load_demand=True, solve_demand=True, load_supply=False, solve_supply=True, pickle_shapes=True, save_models=True, api_run=False)
#    cProfile.run('run(path, config, pint, scenario, load_demand=False, solve_demand=True, load_supply=False, solve_supply=True, pickle_shapes=True, save_models=True, api_run=False)', filename='full_run.profile')

    