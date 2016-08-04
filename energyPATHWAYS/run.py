# -*- coding: utf-8 -*-
"""
Created on Thu Jul 07 19:20:05 2016

@author: ryandrewjones
"""

import sys
import shutil
import click
import os
import cPickle as pickle
import energyPATHWAYS.config as cfg
import energyPATHWAYS.util as util
import energyPATHWAYS.shape as shape
from energyPATHWAYS.pathways_model import PathwaysModel

import time
import cProfile

directory = os.getcwd()
model = None

def myexcepthook(exctype, value, traceback):
    # log here
    sys.__excepthook__(exctype, value, traceback)
sys.excepthook = myexcepthook

@click.command()
@click.option('-c', '--config', type=click.Path(exists=True), default='config.INI', help='filepath for the energyPATHWAYS configuration file')
@click.option('-u', '--pint', type=click.Path(exists=True), default='unit_defs.txt', help='filepath for custom unit definitions for the library pint')
@click.option('-s', '--scenario', multiple=True, help='scenario name or id')
@click.option('-ld', '--load_demand', default=False, help='load a pickle with the demand side complete')
@click.option('-sd', '--solve_demand', default=True, help='solve the demand side of the model')
@click.option('-ls', '--load_supply', default=False, help='load a pickle with the demand and supply side complete')
@click.option('-ss', '--solve_supply', default=True, help='solve the supply side of the model')
@click.option('--pickle_shapes', default=True, help='cache shapes after processing')
@click.option('--save_models', default=True, help='cashe models after running')
@click.option('-o', '--output_path', type=click.Path(exists=True), help='path for writing outputs')
def click_run(config, pint, scenario, load_demand, solve_demand, load_supply, solve_supply, pickle_shapes, save_models, output_path):
    run(config, pint, scenario, load_demand, solve_demand, load_supply, solve_supply, pickle_shapes, save_models, output_path)

def run(config, pint, scenario, load_demand=False, solve_demand=True, load_supply=False, solve_supply=True, pickle_shapes=True, save_models=True, output_path=None):
    global model
    cfg.initialize_config(config, pint, output_path)
    scenario_ids = list_scenario_ids(scenario)
    shape.init_shapes()
    
    for scenario_id in scenario_ids:
        print 'running scenario_id {}'.format(scenario_id)
        model = load_model(config, pint, load_demand, load_supply, scenario_id)
        
        solve_model(model, scenario_id, load_demand, solve_demand, load_supply, solve_supply, save_models)
            
        # remove old results first time around
        if scenario_id == scenario_ids[0]:            
            remove_old_results()
        
        if hasattr(model, 'demand_solved') and model.demand_solved:
            model.export_result('demand_outputs')
        if hasattr(model, 'supply_solved') and model.supply_solved:
            model.export_result('supply_outputs')
            model.export_result('combined_outputs')

def solve_model(model, scenario_id, load_demand, solve_demand, load_supply, solve_supply, save_models):
    try:
        if solve_demand and not (load_demand or load_supply):
            model.configure_energy_system()
            model.populate_energy_system()
            model.populate_measures(scenario_id)
            model.calculate_demand_only()
            model.demand_solved = True
            if save_models:
                with open(os.path.join(directory, str(scenario_id)+'_model.p'), 'wb') as outfile:
                    pickle.dump(model, outfile, pickle.HIGHEST_PROTOCOL)
        
        if solve_supply and not load_supply:
            if not model.demand_solved:
                raise ValueError('demand must be solved first before supply')
            model.pass_results_to_supply()
            model.calculate_supply()
            model.supply_solved = True
            if save_models:
                with open(os.path.join(directory, str(scenario_id)+'_full_model_run.p'), 'wb') as outfile:
                    pickle.dump(model, outfile, pickle.HIGHEST_PROTOCOL)
        
        if hasattr(model, 'supply_solved') and model.supply_solved:
            model.supply.calculate_supply_outputs()
            model.pass_results_to_demand()
            model.calculate_combined_results()
    except:
        with open(os.path.join(directory, str(scenario_id)+'_model_error.p'), 'wb') as outfile:
            pickle.dump(model, outfile, pickle.HIGHEST_PROTOCOL)
        raise

def load_model(config, pint, load_demand, load_supply, scenario_id):
    if load_supply:
        with open(os.path.join(directory, str(scenario_id)+'_full_model_run.p'), 'rb') as infile:
            model = pickle.load(infile)
    elif load_demand:
        with open(os.path.join(directory, str(scenario_id)+'_model.p'), 'rb') as infile:
            model = pickle.load(infile)
    else:
        model = PathwaysModel(config, pint)
    return model

def list_scenario_ids(scenario):
    processed = []
    for s in util.ensure_iterable_and_not_string(scenario):
        if util.is_numeric(s):
            # from click, scenarios may come in as unicode
            s = int(s)
            assert s in cfg.scenario_dict
        else:
            assert s in cfg.scenario_dict.values()
            # turn scenario names into scenario IDs
            s = cfg.scenario_dict.keys()[cfg.scenario_dict.values().index(s)]
        processed.append(s)
    return processed

def remove_old_results():
    folder_names = ['combined_outputs', 'demand_outputs', 'supply_outputs']
    for folder_name in folder_names:
        folder = os.path.join(os.getcwd(), folder_name)
        if os.path.isdir(folder):
            shutil.rmtree(folder)

if __name__ == "__main__":
    directory = r'C:\github\energyPATHWAYS\us_model_example'
    os.chdir(directory)
    config = os.path.join(directory, 'config.INI')
    pint = os.path.join(directory, 'unit_defs.txt')
    scenario = 5
    
    t = time.time()
    run(config, pint, scenario, load_demand=False, solve_demand=True, load_supply=False, solve_supply=True, pickle_shapes=True, save_models=True)
    print time.time() - t

#    t = time.time()
#    cProfile.run('run(config, pint, scenario, load_demand=False, solve_demand=True, load_supply=False, solve_supply=True, pickle_shapes=True, save_models=True)', filename='full_run.profile')
#    print time.time() - t