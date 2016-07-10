# -*- coding: utf-8 -*-
"""
Created on Thu Jul 07 19:20:05 2016

@author: ryandrewjones
"""


import click
import os
from pathways_model import PathwaysModel

@click.command()
@click.argument('config', type=click.Path(exists=True))
@click.option('--pint_units', type=click.Path(exists=True))
@click.option('--load_demand', default=False)
@click.option('--load_supply', default=False)
@click.option('--solve_supply', default=True)
def run(config, pint_units, load_demand, solve_demand, load_supply, solve_supply):
    
    click.echo(config is None)
#    model = PathwaysModel(config, pint_units)
#    click.echo(model)


#


#
#import pandas as pd
#import numpy as np
#import cPickle as pickle
#import os
#from energyPATHWAYS import *
#cfg = energyPATHWAYS.cfg
#from energyPATHWAYS.shape import shapes
#from matplotlib import pylab
#
#directory = os.getcwd()
#
#cfgfile_path = os.path.join(directory, 'configurations.INI')
#custom_pint_definitions_path = os.path.join(directory, 'unit_defs.txt')
#
############
##Save models after the demand-side calculation or after the supply-loop calculation
#save_models = True
##resolve the demand-side. A completed demand-side model must be saved.
#resolve_demand = True
##resolve the supply-side. A completed supply-side model must be saved. 
#resolve_supply = True
#append_results = False
############
#
#def remove_results(append_results):
#   if append_results == False:
#       for folder in [os.path.join(os.getcwd(),'combined_outputs'),os.path.join(os.getcwd(),'demand_outputs'), os.path.join(os.getcwd(),'supply_outputs')]:
#           if os.path.exists(folder):
#               result_dir = [os.listdir(folder)][0]
#               for result_file in result_dir:
#                   os.remove(os.path.join(folder,result_file))
#
#if __name__ == "__main__":
#    if resolve_demand and resolve_supply:
#        model = energyPATHWAYS.PathwaysModel(cfgfile_path, custom_pint_definitions_path)
#        model.populate_shapes()
#        with open(os.path.join(directory, 'shapes.p'), 'wb') as outfile:
#            pickle.dump(shapes, outfile, pickle.HIGHEST_PROTOCOL)
#        for scenario_id in model.scenario_dict.keys():
#            model.model_config(cfgfile_path, custom_pint_definitions_path)
#            model.configure_energy_system()
#            model.populate_energy_system()
#            model.populate_measures(scenario_id)
#            model.calculate_demand_only()
#            if save_models:
#                with open(os.path.join(directory, str(scenario_id)+'_model.p'), 'wb') as outfile:
#                    pickle.dump(model, outfile, pickle.HIGHEST_PROTOCOL)
#            model.pass_results_to_supply()
#            model.calculate_supply()
#            if save_models:
#                with open(os.path.join(directory, str(scenario_id)+'_full_model_run.p'), 'wb') as outfile:
#                    pickle.dump(model, outfile, pickle.HIGHEST_PROTOCOL)
#            model.supply.calculate_supply_outputs()
#            model.pass_results_to_demand()
#            model.calculate_combined_results()
#            remove_results(append_results)
#            #after the first secnario loop, we want to append results so we change the boolean to True
#            append_results = True
#            model.export_results()
#    elif resolve_demand and not resolve_supply: 
#        model = energyPATHWAYS.PathwaysModel(cfgfile_path, custom_pint_definitions_path)
#        model.populate_shapes()
#        with open(os.path.join(directory, 'shapes.p'), 'wb') as outfile:
#                pickle.dump(shapes, outfile, pickle.HIGHEST_PROTOCOL)
#        for scenario_id in model.scenario_dict.keys():
#            model.model_config(cfgfile_path, custom_pint_definitions_path)
#            model.configure_energy_system()
#            model.populate_energy_system()
#            model.populate_measures(scenario_id)
#            model.calculate_demand_only()
#            if save_models:
#                with open(os.path.join(directory, str(scenario_id)+'_model.p'), 'wb') as outfile:
#                    pickle.dump(model, outfile, pickle.HIGHEST_PROTOCOL)
#            remove_results(append_results)
#            #after the first secnario loop, we want to append results so we change the boolean to True
#            append_results = True
#            model.export_results()
#    elif resolve_supply and not resolve_demand:
#        model = energyPATHWAYS.PathwaysModel(cfgfile_path, custom_pint_definitions_path)
#        for scenario_id in model.scenario_dict.keys():
#            with open(os.path.join(directory, str(scenario_id)+'_model.p'), 'rb') as infile:
#                model = pickle.load(infile)
#            model.model_config(cfgfile_path, custom_pint_definitions_path)
#            model.pass_results_to_supply()
#            model.calculate_supply()
#            if save_models:
#                with open(os.path.join(directory, str(scenario_id)+'_full_model_run.p'), 'wb') as outfile:
#                    pickle.dump(model, outfile, pickle.HIGHEST_PROTOCOL)
#            model.supply.calculate_supply_outputs()
#            model.pass_results_to_demand()
#            model.calculate_combined_results()
#            remove_results(append_results)
#            #after the first secnario loop, we want to append results so we change the boolean to True
#            append_results = True
#            model.export_results()
#    else:
#        model = energyPATHWAYS.PathwaysModel(cfgfile_path, custom_pint_definitions_path)
#        for scenario_id in model.scenario_dict.keys():
#            with open(os.path.join(directory, str(scenario_id)+'_full_model_run.p'), 'rb') as infile:
#                model = pickle.load(infile)
#            model.model_config(cfgfile_path, custom_pint_definitions_path)
#            model.demand.aggregate_results()
#            model.supply.calculate_supply_outputs()
#            model.pass_results_to_demand()
#            model.calculate_combined_results()
#            remove_results(append_results)
#            #after the first secnario loop, we want to append results so we change the boolean to True
#            append_results = True
#            model.export_results()
#
