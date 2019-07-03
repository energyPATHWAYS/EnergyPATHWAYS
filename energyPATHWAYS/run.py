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

# Deprecated
# def myexcepthook(exctype, value, tb):
#     logging.error("Exception caught during model run.", exc_info=(exctype, value, tb))
#     # It is possible that we arrived here due to a database exception, and if so the database will be in a state
#     # where it is not accepting commands. To be safe, we do a rollback before attempting to write the run status.
#     try:
#         cfg.con.rollback()
#     except (psycopg2.InterfaceError, AttributeError):
#         logging.exception("Unable to rollback database connection while handling an exception, "
#                           "probably because the connection hasn't been opened yet or was already closed.")
#     sys.__excepthook__(exctype, value, tb)
# sys.excepthook = myexcepthook
#
# def signal_handler(signal, frame):
#     logging.error('Execution interrupted by signal ' + str(signal))
#     # As documented here,
#     # http://stackoverflow.com/questions/39215527/psycopg2-connection-unusable-after-selects-interrupted-by-os-signal
#     # The normal database connection may be in an unusable state here if the signal arrived while the connection
#     # was in the middle of performing some work. Therefore, we re-initialize the connection so that we can use it to
#     # write the cancelation status to the db.
#     cfg.init_db()
#     sys.exit(0)
# signal.signal(signal.SIGINT, signal_handler)
# signal.signal(signal.SIGTERM, signal_handler)

@click.command()
@click.option('-p', '--path', type=click.Path(exists=True), help='Working directory for energyPATHWAYS run.')
@click.option('-c', '--config', default='config.INI', help='File name for the energyPATHWAYS configuration file.')
@click.option('-s', '--scenario', type=str, multiple=True, help='Scenario name to run. More than one can be specified by repeating this option. If none are specified, the working directory will be scanned for .json files and all will be run.')
@click.option('-ld', '--load_demand/--no_load_demand', default=False, help='Load a cached model with the demand side complete.')
@click.option('--solve_demand/--no_solve_demand', default=True, help='Solve the demand side of the model.')
@click.option('-ls', '--load_supply/--no_load_supply', default=False, help='Load a cached model with the demand and supply side complete.')
@click.option('--solve_supply/--no_solve_supply', default=True, help='Solve the supply side of the model.')
@click.option('--load_error/--no_load_error', default=False, help='Load the error pickle of a previous model run that crashed.')
@click.option('--export_results/--no_export_results', default=True, help='Write results from the demand and supply sides of the model.')
@click.option('--pickle_shapes/--no_pickle_shapes', default=True, help='Cache shapes after processing.')
@click.option('--save_models/--no_save_models', default=True, help='Cache models after running.')
@click.option('--log_name', help='File name for the log file.')
@click.option('--clear_results/--no_clear_results', default=False, help='Should results be cleared or appended when starting a new model run')
@click.option('--subfolders/--no_subfolders', default=False, help='Most users do not need this! Used when a system of subfolders has been created for different runs')
def click_run(path, config, scenario, load_demand, solve_demand, load_supply, solve_supply, load_error, export_results, pickle_shapes, save_models, log_name, clear_results, subfolders):
    run(path, config, scenario, load_demand, solve_demand, load_supply, solve_supply, load_error, export_results, pickle_shapes, save_models, log_name, clear_results, subfolders)

def run(path, config, scenarios, load_demand=False, solve_demand=True, load_supply=False, solve_supply=True, load_error=False,
        export_results=True, pickle_shapes=True, save_models=True, log_name=None, clear_results=False, subfolders=False,rio_scenario=None):
    global model
    path = os.getcwd() if path is None else path
    cfg.initialize_config()
    if not subfolders:
        GeoMapper.get_instance().log_geo()

    shape.Shapes.get_instance(cfg.getParam('database_path'))

    if not scenarios:
        scenarios = [os.path.basename(p) for p in glob.glob(os.path.join(cfg.workingdir, '*.json'))]
        if not scenarios:
            raise ValueError, "No scenarios specified and no .json files found in working directory."

    # Users may have specified a scenario using the full filename, but for our purposes the 'id' of the scenario
    # is just the part before the .json
    scenarios = util.ensure_iterable(scenarios)
    scenarios = [os.path.splitext(s)[0] for s in scenarios]
    rio_scenario = [None]*len(scenarios) if rio_scenario is None else util.ensure_iterable(rio_scenario)

    combined_scenarios = zip(scenarios, rio_scenario)
    logging.info('Scenario run list: {}'.format(', '.join(scenarios)))
    for scenario, rio_scenario in combined_scenarios:
        if subfolders:
            logging.shutdown()
            logging.getLogger(None).handlers = []
            cfg.initialize_config(os.path.join(path, scenario), config, log_name)
            logging.info('SUBFOLDERS ARE IN USE')
            GeoMapper.get_instance().log_geo()
        scenario_start_time = time.time()
        logging.info('Starting scenario {}'.format(scenario))
        logging.info('Start time {}'.format(str(datetime.datetime.now()).split('.')[0]))
        if cfg.rio_supply_run:
            model = load_model(load_demand, load_supply, load_error, scenario, rio_scenario)
        else:
            model = load_model(load_demand, load_supply, load_error, scenario, None)
        if not load_error:
            model.run(scenario,
                      solve_demand=solve_demand,
                      solve_supply=solve_supply,
                      load_demand=load_demand,
                      load_supply=load_supply,
                      export_results=export_results,
                      save_models=save_models,
                      append_results=False if (scenario == scenarios[0] and clear_results) else True,rio_scenario=rio_scenario)

        logging.info('EnergyPATHWAYS run for scenario {} successful!'.format(scenario))
        logging.info('Scenario calculation time {}'.format(str(datetime.timedelta(seconds=time.time() - scenario_start_time)).split('.')[0]))
    logging.info('Total calculation time {}'.format(str(datetime.timedelta(seconds=time.time() - run_start_time)).split('.')[0]))
    logging.shutdown()
    logging.getLogger(None).handlers = [] # necessary to totally flush the logger

def load_model(load_demand, load_supply, load_error, scenario,rio_scenario):
    pathways_scenario = scenario
    scenario = scenario if rio_scenario is None else rio_scenario
    if load_error:
        with open(os.path.join(cfg.workingdir, str(pathways_scenario) + cfg.model_error_append_name), 'rb+') as infile:
#        with open(os.path.join(cfg.workingdir, 'dispatch_class.p'), 'rb') as infile:
            model = pickle.load(infile)
        logging.info('Loaded crashed EnergyPATHWAYS model from pickle')
    elif load_supply:
        try:
            with open(os.path.join(cfg.workingdir, str(scenario) + cfg.full_model_append_name), 'rb') as infile:
                model = pickle.load(infile)
            logging.info('Loaded complete EnergyPATHWAYS model from pickle')
        except:
            with open(os.path.join(cfg.workingdir, str(pathways_scenario) + cfg.full_model_append_name), 'rb') as infile:
                model = pickle.load(infile)
            logging.info('Loaded complete EnergyPATHWAYS model from pickle')
    elif load_demand:
        demand_file = os.path.join(cfg.workingdir, str(pathways_scenario) + cfg.demand_model_append_name)
        supply_file = os.path.join(cfg.workingdir, str(pathways_scenario) + cfg.full_model_append_name)
        if os.path.isfile(demand_file):
            with open(os.path.join(cfg.workingdir, str(pathways_scenario) + cfg.demand_model_append_name), 'rb') as infile:
                model = pickle.load(infile)
                logging.info('Loaded demand-side EnergyPATHWAYS model from pickle')
        elif os.path.isfile(supply_file):
            with open(os.path.join(cfg.workingdir, str(pathways_scenario) + cfg.full_model_append_name), 'rb') as infile:
                model = pickle.load(infile)
                logging.info('Loaded complete EnergyPATHWAYS model from pickle')
        else:
            raise("No model file exists")
    else:
        model = PathwaysModel(pathways_scenario)
    return model

class SubsectorPerturbation(object):
    def __init__(self, sales_share_changes, flexible_operation, subsector):
        self.sales_share_changes = sales_share_changes
        self.flexible_operation = flexible_operation
        self.subsector = subsector

if __name__ == "__main__":
    workingdir = r'C:\github\EP_runs\IADB_csv'
    os.chdir(workingdir)
    config = 'config.INI'
    rio_scenario = None
    scenario = None

    run(workingdir, config, scenario,
    load_demand   = False,
    solve_demand  = True,
    load_supply   = False,
    solve_supply  = False,
    export_results= True,
    load_error    = False,
    pickle_shapes = True,
    save_models   = True,
    clear_results = True,
    rio_scenario=rio_scenario)

    # run_str = "run('C:\Github\EnergyPATHWAYS_scenarios\SDG&E', 'config.INI', 'scoping_plan', \
    # load_demand   = True,\
    # solve_demand  = True,\
    # load_supply   = False,\
    # solve_supply  = True,\
    # export_results= False,\
    # load_error    = False,\
    # pickle_shapes = True,\
    # save_models   = True,\
    # clear_results = False,\
    # rio_scenario=None)"
    #
    # cProfile.run(run_str, filename='system.prof')