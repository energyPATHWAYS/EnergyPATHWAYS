

__author__ = 'Ben Haley & Ryan Jones'

import pandas as pd
import numpy as np
import cPickle as pickle
import os
from energyPATHWAYS import *
cfg = energyPATHWAYS.cfg
from energyPATHWAYS.shape import shapes
import time

directory = os.getcwd()

cfgfile_path = os.path.join(directory, 'configurations.INI')
custom_pint_definitions_path = os.path.join(directory, 'unit_defs.txt')

###########
#Save models after the demand-side calculation or after the supply-loop calculation
save_models = True
#resolve the demand-side. A completed demand-side model must be saved.
resolve_demand = True
#resolve the supply-side. A completed supply-side model must be saved. 
resolve_supply = False
append_results = False
###########`
#
#
if __name__ == "__main__":
    if resolve_demand and resolve_supply:
        model = energyPATHWAYS.PathwaysModel(cfgfile_path, custom_pint_definitions_path)
        model.configure_energy_system()
        model.populate_shapes()
        with open(os.path.join(directory, 'shapes.p'), 'wb') as outfile:
            pickle.dump(shapes, outfile, pickle.HIGHEST_PROTOCOL)
        for scenario_id in model.scenario_dict.keys():
            model.populate_energy_system()
            model.populate_measures(scenario_id)
            model.calculate_demand_only()
            if save_models:
                with open(os.path.join(directory, str(scenario_id)+'_model.p'), 'wb') as outfile:
                    pickle.dump(model, outfile, pickle.HIGHEST_PROTOCOL)
            model.pass_results_to_supply()
            model.calculate_supply()
            if save_models:
                with open(os.path.join(directory, str(scenario_id)+'_full_model_run.p'), 'wb') as outfile:
                    pickle.dump(model, outfile, pickle.HIGHEST_PROTOCOL)
            model.supply.calculate_supply_outputs()
            model.pass_results_to_demand()
            model.calculate_combined_results()
            model.export_results(append_results)
    elif resolve_demand and not resolve_supply: 
        model = energyPATHWAYS.PathwaysModel(cfgfile_path, custom_pint_definitions_path)
        model.configure_energy_system()
        model.populate_shapes()
        with open(os.path.join(directory, 'shapes.p'), 'wb') as outfile:
            pickle.dump(shapes, outfile, pickle.HIGHEST_PROTOCOL)
        for scenario_id in model.scenario_dict.keys():
            model.populate_energy_system()
            model.populate_measures(scenario_id)
            model.calculate_demand_only()
            if save_models:
                with open(os.path.join(directory, str(scenario_id)+'_model.p'), 'wb') as outfile:
                    pickle.dump(model, outfile, pickle.HIGHEST_PROTOCOL)
            model.export_results(append_results)
    elif resolve_supply and not resolve_demand:
        model = energyPATHWAYS.PathwaysModel(cfgfile_path, custom_pint_definitions_path)
        for scenario_id in model.scenario_dict.keys():
            with open(os.path.join(directory, str(scenario_id)+'_model.p'), 'rb') as infile:
                model = pickle.load(infile)
            model.model_config(cfgfile_path, custom_pint_definitions_path)
            model.pass_results_to_supply()
            model.calculate_supply()
            if save_models:
                with open(os.path.join(directory, str(scenario_id)+'_full_model_run.p'), 'wb') as outfile:
                    pickle.dump(model, outfile, pickle.HIGHEST_PROTOCOL)
            model.supply.calculate_supply_outputs()
            model.pass_results_to_demand()
            model.calculate_combined_results()
            model.export_results(append_results)
    else:
        model = energyPATHWAYS.PathwaysModel(cfgfile_path, custom_pint_definitions_path)
        for scenario_id in model.scenario_dict.keys():
            with open(os.path.join(directory, str(scenario_id)+'_full_model_run.p'), 'rb') as infile:
                model = pickle.load(infile)
            model.model_config(cfgfile_path, custom_pint_definitions_path)
            model.supply.calculate_supply_outputs()
            model.pass_results_to_demand()
            model.calculate_combined_results()
            model.export_results(append_results)
#
