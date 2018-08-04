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
import time
import datetime
import logging
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import cProfile
import traceback
import pandas as pd

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
    try:
        cfg.con.rollback()
    except (psycopg2.InterfaceError, AttributeError):
        logging.exception("Unable to rollback database connection while handling an exception, "
                          "probably because the connection hasn't been opened yet or was already closed.")
    update_api_run_status(5)
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
    update_api_run_status(6)
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

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
@click.option('-a', '--api_run/--no_api_run', default=False)
@click.option('-d', '--debug/--no_debug', default=False, help='On error the model will exit into an ipython debugger.')
@click.option('--clear_results/--no_clear_results', default=False, help='Should results be cleared or appended when starting a new model run')
def click_run(path, config, scenario, load_demand, solve_demand, load_supply, solve_supply, load_error, export_results, pickle_shapes, save_models, log_name, api_run, debug, clear_results):
    if debug:
        import ipdb
        with ipdb.launch_ipdb_on_exception():
            run(path, config, scenario, load_demand, solve_demand, load_supply, solve_supply, load_error, export_results, pickle_shapes, save_models, log_name, api_run, clear_results)
    else:
        run(path, config, scenario, load_demand, solve_demand, load_supply, solve_supply, load_error, export_results, pickle_shapes, save_models, log_name, api_run, clear_results)

def run(path, config, scenario_ids, load_demand=False, solve_demand=True, load_supply=False, solve_supply=True, load_error=False,
        export_results=True, pickle_shapes=True, save_models=True, log_name=None, api_run=False, clear_results=False):
    global model
    cfg.initialize_config(path, config, log_name)
    cfg.geo.log_geo()
    shape.init_shapes(pickle_shapes)

    if not scenario_ids:
        scenario_ids = [os.path.basename(p) for p in glob.glob(os.path.join(cfg.workingdir, '*.json'))]
        if not scenario_ids:
            raise ValueError, "No scenarios specified and no .json files found in working directory."

    # Users may have specified a scenario using the full filename, but for our purposes the 'id' of the scenario
    # is just the part before the .json
    scenario_ids = [os.path.splitext(s)[0] for s in scenario_ids]

    logging.info('Scenario run list: {}'.format(', '.join(scenario_ids)))
    for scenario_id in scenario_ids:
        scenario_start_time = time.time()
        logging.info('Starting scenario {}'.format(scenario_id))
        logging.info('Start time {}'.format(str(datetime.datetime.now()).split('.')[0]))
        if api_run:
            # FIXME: This will be broken since we changed the scenario list from a list of database ids to a list of
            # filenames. The API-related code will need to be updated before we can update the server with newer
            # model code.
            util.update_status(scenario_id, 3)
            scenario_name = util.scenario_name(scenario_id)
            subject = 'Now running: EnergyPathways scenario "%s"' % (scenario_name,)
            body = 'EnergyPathways is now running your scenario titled "%s". A scenario run generally ' \
                   'finishes within a few hours, and you will receive another email when your run is complete. ' \
                   'If more than 24 hours pass without you receiving a confirmation email, please log in to ' \
                   'https://energypathways.com to check the status of the run. ' \
                   'If the run is not complete, please reply to this email and we will investigate.' % (scenario_name,)
            send_gmail(scenario_id, subject, body)

        model = load_model(load_demand, load_supply, load_error, scenario_id, api_run)
        if not load_error:
            model.run(scenario_id,
                      solve_demand=solve_demand,
                      solve_supply=solve_supply,
                      load_demand=load_demand,
                      load_supply=load_supply,
                      export_results=export_results,
                      save_models=save_models,
                      append_results=False if (scenario_id == scenario_ids[0] and clear_results) else True)

        if api_run:
            util.update_status(scenario_id, 4)
            subject = 'Completed: EnergyPathways scenario "%s"' % (scenario_name,)
            body = 'EnergyPathways has completed running your scenario titled "%s". ' \
                   'Please return to https://energypathways.com to view your results.' % (scenario_name,)
            send_gmail(scenario_id, subject, body)

        logging.info('EnergyPATHWAYS run for scenario_id {} successful!'.format(scenario_id))
        logging.info('Scenario calculation time {}'.format(str(datetime.timedelta(seconds=time.time() - scenario_start_time)).split('.')[0]))
    logging.info('Total calculation time {}'.format(str(datetime.timedelta(seconds=time.time() - run_start_time)).split('.')[0]))
    logging.shutdown()
    logging.getLogger(None).handlers = [] # necessary to totally flush the logger

def load_model(load_demand, load_supply, load_error, scenario_id, api_run):
    # Note that the api_run parameter is effectively ignored if you are loading a previously pickled model
    # (with load_supply or load_demand); the model's api_run property will be set to whatever it was when the model
    # was pickled.
    error_file  = os.path.join(cfg.workingdir, str(scenario_id) + cfg.model_error_append_name)
    supply_file = os.path.join(cfg.workingdir, str(scenario_id) + cfg.full_model_append_name)
    demand_file = os.path.join(cfg.workingdir, str(scenario_id) + cfg.demand_model_append_name)

    # local func to reduce redundancy
    def read_pickle(file, desc):
        with open(file, 'rb') as f:
            model = pickle.load(f)

        logging.info('Loaded %s EnergyPATHWAYS model from pickle', desc)
        return model

    if load_error:
        with open(os.path.join(cfg.workingdir, str(scenario_id) + cfg.model_error_append_name), 'rb+') as infile:
#        with open(os.path.join(cfg.workingdir, 'dispatch_class.p'), 'rb') as infile:
            model = pickle.load(infile)
        logging.info('Loaded crashed EnergyPATHWAYS model from pickle')
    elif load_supply:
        model = read_pickle(supply_file, 'complete')

    elif load_demand:
        if os.path.isfile(demand_file):
            model = read_pickle(demand_file, 'demand-side')

        elif os.path.isfile(supply_file):
            model = read_pickle(supply_file, 'complete')

        else:
            raise("No model file exists")
    else:
        model = PathwaysModel(scenario_id, api_run)

    return model

def send_gmail(scenario_id, subject, body):
    toaddr = util.active_user_emailzx(scenario_id)
    if not toaddr:
        logging.warning('Unable to find a user email for scenario %s; skipping sending email with subject "%s".' %\
                        (scenario_id, subject))
        return

    fromaddr = cfg.cfgfile.get('email', 'email_address')
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, cfg.cfgfile.get('email', 'email_password'))
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()

class SubsectorPerturbation(object):
    def __init__(self, sales_share_changes, flexible_operation, subsector):
        self.sales_share_changes = sales_share_changes
        self.flexible_operation = flexible_operation
        self.subsector = subsector

if __name__ == "__main__":
    if os.getenv('USER') == 'rjp':
        workingdir = '/Users/rjp/Projects/EvolvedEnergy/integration'
    else:
        workingdir = r'C:\Github\EnergyPATHWAYS_scenarios\OCT'
    config = 'config.INI'
    scenario = ['aeo_2017_reference']

    run(workingdir, config, scenario,
    load_demand   = False,
    solve_demand  = True,
    load_supply   = False,
    solve_supply  = False,
    export_results= True,
    load_error    = False,
    pickle_shapes = True,
    save_models   = True,
    api_run       = False,
    clear_results = False)
    
