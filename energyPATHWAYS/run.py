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
import time
import datetime
import logging
import cProfile
import traceback


model = None
run_start_time = time.time()


def update_api_run_status(status_id):
    logging.debug("Updating scenario run status in database.")
    try:
        global model
        if model and model.api_run:
            util.update_status(model.scenario_id, status_id)
    # This is one of the few times I think a broad except clause is justified; if we've failed to update the run
    # status in the database at this point we don't really care why, and we don't want it to prevent any other
    # cleanup code from running. We'll just log it for future troubleshooting.
    except Exception:
        logging.exception("Exception caught attempting to write abnormal termination status %i to database."
                          % (status_id,))
    logging.debug("Finished updating scenario run status in database.")


def myexcepthook(exctype, value, tb):
    logging.error("Exception caught during model run.", exc_info=(exctype, value, tb))
    # It is possible that we arrived here due to a database exception, and if so the database will be in a state
    # where it is not accepting commands. To be safe, we do a rollback before attempting to write the run status.
    cfg.con.rollback()
    update_api_run_status(4)
    sys.__excepthook__(exctype, value, tb)
sys.excepthook = myexcepthook


def signal_handler(signal, frame):
    logging.error('Execution interrupted by signal ' + str(signal))
    # As documented here,
    # http://stackoverflow.com/questions/39215527/psycopg2-connection-unusable-after-selects-interrupted-by-os-signal
    # The normal database connection may be in an unusable state here if the signal arrived while the connection
    # was in the middle of performing some work. Therefore, we re-initialize the connection so that we can use it to
    # write the cancelation status to the db.
    cfg.init_db()
    update_api_run_status(5)
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


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
        model = load_model(path, load_demand, load_supply, scenario_id, api_run)
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

def load_model(path, load_demand, load_supply, scenario_id, api_run):
    # Note that the api_run parameter is effectively ignored if you are loading a previously pickled model
    # (with load_supply or load_demand); the model's api_run property will be set to whatever it was when the model
    # was pickled.
    if load_supply:
        with open(os.path.join(path, str(scenario_id)+'_full_model_run.p'), 'rb') as infile:
            model = pickle.load(infile)
        logging.info('Loaded complete EnergyPATHWAYS model from pickle')
    elif load_demand:
        with open(os.path.join(path, str(scenario_id)+'_model.p'), 'rb') as infile:
            model = pickle.load(infile)
        logging.info('Loaded demand-side EnergyPATHWAYS model from pickle')
    else:
        model = PathwaysModel(scenario_id, api_run)
    return model

if __name__ == "__main__":
    workingdir = r'C:\github\energyPATHWAYS\us_model_example'
    os.chdir(workingdir)
    config = 'config.INI'
    pint = 'unit_defs.txt'
    scenario = 5
    
    run(workingdir, config, pint, scenario, load_demand=False, solve_demand=True, load_supply=False, solve_supply=True, pickle_shapes=True, save_models=True, api_run=False)
#    cProfile.run('run(path, config, pint, scenario, load_demand=False, solve_demand=True, load_supply=False, solve_supply=True, pickle_shapes=True, save_models=True, api_run=False)', filename='full_run.profile')

    