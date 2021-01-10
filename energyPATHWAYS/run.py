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
from energyPATHWAYS import outputs
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

def all_finished(all_scenarios):
    return all([sensitivity_is_finished(os.path.join(os.getcwd(), scenario)) for scenario in all_scenarios])

def sensitivity_is_finished(scenario_path):
    #todo make this more robust!!!! things are written after d_stock
    if os.path.exists(os.path.join(scenario_path, 'outputs', 'd_stock.csv.gz')): # the last file written and a very small one
        return True
    else:
        return False

@click.command()
@click.option('-s', '--scenario', type=str, multiple=True, help='Scenario name to run. More than one can be specified by repeating this option. If none are specified, the working directory will be scanned for .json files and all will be run.')
@click.option('-ld', '--load_demand/--no_load_demand', default=False, help='Load a cached model with the demand side complete.')
@click.option('--solve_demand/--no_solve_demand', default=True, help='Solve the demand side of the model.')
@click.option('-ls', '--load_supply/--no_load_supply', default=False, help='Load a cached model with the demand and supply side complete.')
@click.option('--solve_supply/--no_solve_supply', default=True, help='Solve the supply side of the model.')
@click.option('--export_results/--no_export_results', default=True, help='Write results from the demand and supply sides of the model.')
@click.option('--save_models/--no_save_models', default=True, help='Cache models after running.')
@click.option('--shape_owner/--no_shape_owner', default=True, help='Controls the process that runs the shapes')
@click.option('--compile_mode/--no_compile_mode', default=False, help='Compile scenarios only.')
def click_run(scenario, load_demand, solve_demand, load_supply, solve_supply, export_results, save_models, shape_owner, compile_mode):
    run(scenario, load_demand, solve_demand, load_supply, solve_supply, export_results, save_models, shape_owner, compile_mode)

def run(scenarios, load_demand=False, solve_demand=True, load_supply=False, solve_supply=True, export_results=True, save_models=True, shape_owner=True, compile_mode=False):
    global model
    cfg.initialize_config()
    GeoMapper.get_instance().log_geo()
    scenarios = util.ensure_iterable(scenarios)

    logging.info('Scenario run list: {}'.format(', '.join(scenarios)))

    if not compile_mode:
        for scenario in scenarios:
            scenario_start_time = time.time()
            logging.info('Starting scenario {}'.format(scenario))
            logging.info('Start time {}'.format(str(datetime.datetime.now()).split('.')[0]))
            model = load_model(load_demand, load_supply, scenario)
            model.run(solve_demand=solve_demand,
                      solve_supply=solve_supply,
                      load_demand=load_demand,
                      load_supply=load_supply,
                      export_results=export_results,
                      save_models=save_models,
                      shape_owner=shape_owner)

            logging.info('EnergyPATHWAYS run for scenario {} successful!'.format(scenario))
            logging.info('Scenario calculation time {}'.format(str(datetime.timedelta(seconds=time.time() - scenario_start_time)).split('.')[0]))

    all_scenarios = util.get_all_scenario_names(cfg.workingdir)
    if (all_finished(all_scenarios) and export_results) or compile_mode:
        outputs.aggregate_scenario_results(all_scenarios)

    logging.info('Total calculation time {}'.format(str(datetime.timedelta(seconds=time.time() - run_start_time)).split('.')[0]))
    logging.shutdown()
    logging.getLogger(None).handlers = [] # necessary to totally flush the logger

def load_model(load_demand, load_supply, scenario):
    if load_supply:
        try:
            with open(os.path.join(cfg.workingdir, str(scenario), str(scenario) + cfg.full_model_append_name), 'rb') as infile:
                model = pickle.load(infile)
            logging.info('Loaded complete EnergyPATHWAYS model from pickle')
        except:
            with open(os.path.join(cfg.workingdir, str(scenario), str(scenario) + cfg.full_model_append_name), 'rb') as infile:
                model = pickle.load(infile)
            logging.info('Loaded complete EnergyPATHWAYS model from pickle')
    elif load_demand:
        demand_file = os.path.join(cfg.workingdir, str(scenario), str(scenario) + cfg.demand_model_append_name)
        supply_file = os.path.join(cfg.workingdir, str(scenario), str(scenario) + cfg.full_model_append_name)
        if os.path.isfile(demand_file):
            with open(os.path.join(cfg.workingdir, str(scenario), str(scenario) + cfg.demand_model_append_name), 'rb') as infile:
                model = pickle.load(infile)
                logging.info('Loaded demand-side EnergyPATHWAYS model from pickle')
        elif os.path.isfile(supply_file):
            with open(os.path.join(cfg.workingdir, str(scenario), str(scenario) + cfg.full_model_append_name), 'rb') as infile:
                model = pickle.load(infile)
                logging.info('Loaded complete EnergyPATHWAYS model from pickle')
        else:
            raise IOError("No model file exists")
    else:
        model = PathwaysModel(scenario)
    return model

class SubsectorPerturbation(object):
    def __init__(self, sales_share_changes, flexible_operation, subsector):
        self.sales_share_changes = sales_share_changes
        self.flexible_operation = flexible_operation
        self.subsector = subsector

if __name__ == "__main__":
    workingdir = r'C:\Users\ryandrewjones\Dropbox (EER)\Evolved Energy Research\Tools\EnergyPATHWAYS\Active Runs\project_restart'
    os.chdir(workingdir)
    scenario = ['Net Zero by 2050']
    run(scenario,
    load_demand   = False,
    solve_demand  = False,
    load_supply   = True,
    solve_supply  = False,
    export_results= True,
    save_models   = True,
    compile_mode  = False,
    )
