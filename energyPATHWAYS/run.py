# -*- coding: utf-8 -*-
"""
Created on Thu Jul 07 19:20:05 2016

@author: ryandrewjones
"""

import sys
import signal
import click
import os
import glob
import cPickle as pickle
import psycopg2
import energyPATHWAYS.config as cfg
import energyPATHWAYS.util as util
from energyPATHWAYS.pathways_model import PathwaysModel
import energyPATHWAYS.shape as shape
from energyPATHWAYS.outputs import Output
from energyPATHWAYS.dispatch_classes import Dispatch
from energyPATHWAYS.geomapper import GeoMapper
import time
import datetime
import logging
import smtplib
import cProfile
import traceback
import pandas as pd
import pdb
import energyPATHWAYS.unit_converter as unit_converter

model = None
run_start_time = time.time()

@click.command()
@click.option('-s', '--scenario', type=str, multiple=True, help='Scenario name to run. More than one can be specified by repeating this option. If none are specified, the working directory will be scanned for .json files and all will be run.')
@click.option('-ld', '--load_demand/--no_load_demand', default=False, help='Load a cached model with the demand side complete.')
@click.option('--solve_demand/--no_solve_demand', default=True, help='Solve the demand side of the model.')
@click.option('-ls', '--load_supply/--no_load_supply', default=False, help='Load a cached model with the demand and supply side complete.')
@click.option('--solve_supply/--no_solve_supply', default=True, help='Solve the supply side of the model.')
@click.option('--load_error/--no_load_error', default=False, help='Load the error pickle of a previous model run that crashed.')
@click.option('--export_results/--no_export_results', default=True, help='Write results from the demand and supply sides of the model.')
@click.option('--save_models/--no_save_models', default=True, help='Cache models after running.')
@click.option('--clear_results/--no_clear_results', default=False, help='Should results be cleared or appended when starting a new model run')
@click.option('--subfolders/--no_subfolders', default=False, help='Most users do not need this! Used when a system of subfolders has been created for different runs')
@click.option('-r', '--rio_scenario', type=str, multiple=True, help='RIO scenario name to run. More than one can be specified by repeating this option.')
@click.option('-wsn', '--write_scenario_name', type=str, multiple=True, help='Write scenario name to run. More than one can be specified by repeating this option.')
def click_run(scenario, load_demand, solve_demand, load_supply, solve_supply, load_error, export_results, save_models, clear_results, subfolders, rio_scenario, write_scenario_name):
    run(scenario, load_demand, solve_demand, load_supply, solve_supply, load_error, export_results, save_models, clear_results, subfolders, rio_scenario, write_scenario_name)

def run(scenarios, load_demand=False, solve_demand=True, load_supply=False, solve_supply=True, load_error=False, export_results=True, save_models=True, clear_results=False, subfolders=False, rio_scenario=None, write_scenario_name=None):
    global model
    cfg.initialize_config()
    if not subfolders:
        GeoMapper.get_instance().log_geo()

    if not scenarios:
        scenarios = [os.path.basename(p) for p in glob.glob(os.path.join(cfg.workingdir, '*.json'))]
        if not scenarios:
            raise ValueError, "No scenarios specified and no .json files found in working directory."

    scenarios = util.ensure_iterable(scenarios)
    scenarios = [os.path.splitext(s)[0] for s in scenarios]
    rio_scenario = [None]*len(scenarios) if rio_scenario is None or not len(rio_scenario) else util.ensure_iterable(rio_scenario)
    write_scenario_name = [None] * len(scenarios) if write_scenario_name is None or not len(write_scenario_name) else util.ensure_iterable(write_scenario_name)

    combined_scenarios = zip(scenarios, rio_scenario, write_scenario_name)
    logging.info('Scenario run list: {}'.format(', '.join(scenarios)))
    for scenario, rio_scenario, write_scenario_name in combined_scenarios:
        if subfolders:
            logging.shutdown()
            logging.getLogger(None).handlers = []
            cfg.initialize_config()
            logging.info('SUBFOLDERS ARE IN USE')
            GeoMapper.get_instance().log_geo()
        scenario_start_time = time.time()
        logging.info('Starting scenario {}'.format(scenario))
        logging.info('Start time {}'.format(str(datetime.datetime.now()).split('.')[0]))
        if cfg.rio_supply_run:
            model = load_model(load_demand, load_supply, scenario, write_scenario_name, rio_scenario)
        else:
            model = load_model(load_demand, load_supply, scenario, None, None)
        if not load_error:
            model.run(scenario,
                      solve_demand=solve_demand,
                      solve_supply=solve_supply,
                      load_demand=load_demand,
                      load_supply=load_supply,
                      export_results=export_results,
                      save_models=save_models,
<<<<<<< Updated upstream
                      append_results=False if (scenario == scenarios[0] and clear_results) else True,rio_scenario=rio_scenario,write_scenario_name=None)
=======
                      append_results=False if (scenario == scenarios[0] and clear_results) else True,
                      rio_scenario=rio_scenario,
                      write_scenario_name=write_scenario_name)
>>>>>>> Stashed changes

        shape.Shapes._instance = None  # needed because we filter shapes and need to reload it during the next for loop
        logging.info('EnergyPATHWAYS run for scenario {} successful!'.format(scenario))
        logging.info('Scenario calculation time {}'.format(str(datetime.timedelta(seconds=time.time() - scenario_start_time)).split('.')[0]))
    logging.info('Total calculation time {}'.format(str(datetime.timedelta(seconds=time.time() - run_start_time)).split('.')[0]))
    logging.shutdown()
    logging.getLogger(None).handlers = [] # necessary to totally flush the logger

def load_model(load_demand, load_supply, scenario, write_scenario_name, rio_scenario):
    name_load_order = [write_scenario_name, scenario, rio_scenario]
    model = None
    if load_supply:
        for load_name in name_load_order:
            supply_file = os.path.join(cfg.workingdir, str(load_name) + cfg.full_model_append_name)
            if os.path.isfile(supply_file):
                with open(supply_file, 'rb') as infile:
                    model = pickle.load(infile)
                logging.info('Loaded complete EnergyPATHWAYS model from pickle')
                break
    elif load_demand:
        for load_name in name_load_order:
            demand_file = os.path.join(cfg.workingdir, str(load_name) + cfg.demand_model_append_name)
            supply_file = os.path.join(cfg.workingdir, str(load_name) + cfg.full_model_append_name)
            if os.path.isfile(demand_file):
                with open(demand_file, 'rb') as infile:
                    model = pickle.load(infile)
                logging.info('Loaded demand-side EnergyPATHWAYS demand model from pickle')
                break
            elif os.path.isfile(supply_file):
                with open(supply_file, 'rb') as infile:
                    model = pickle.load(infile)
                logging.info('Loaded complete EnergyPATHWAYS supply model from pickle')
                break
    else:
        model = PathwaysModel(scenario)
    if model is None:
        raise IOError("No model file with the names {} exists".format(name_load_order))
    else:
        return model

class SubsectorPerturbation(object):
    def __init__(self, sales_share_changes, flexible_operation, subsector):
        self.sales_share_changes = sales_share_changes
        self.flexible_operation = flexible_operation
        self.subsector = subsector

if __name__ == "__main__":
    workingdir = r'E:\EP_Runs\Restart'
    os.chdir(workingdir)
    rio_scenario = None
    scenario = ['Net Zero by 2050']
    run(scenario,
    load_demand   = True,
    solve_demand  = False,
    load_supply   = False,
    solve_supply  = True,
    export_results= False,
    load_error    = False,
    save_models   = True,
    clear_results = False,
    rio_scenario=rio_scenario)

