__author__ = 'Ben Haley & Ryan Jones'

import pandas as pd
import numpy as np
import cPickle as pickle
import os
import energyPATHWAYS
from energyPATHWAYS import *

#cfg = energyPATHWAYS.config
from energyPATHWAYS.shape import shapes
import ipdb

directory = os.getcwd()

cfgfile_path = os.path.join(directory, 'configurations.INI')
custom_pint_definitions_path = os.path.join(directory, 'unit_defs.txt')

###########
#Save models after the demand-side calculation or after the supply-loop calculation
save_models = True
#resolve the demand-side. A completed demand-side model must be saved.
resolve_demand = True
#resolve the supply-side. A completed supply-side model must be saved. 
resolve_supply = True
###########

with ipdb.launch_ipdb_on_exception():
    if __name__ == "__main__":
        if resolve_demand and resolve_supply:
            model = energyPATHWAYS.PathwaysModel(cfgfile_path, custom_pint_definitions_path)
            model.configure_energy_system()
            model.populate_energy_system()
            model.populate_measures()
            model.calculate_demand_only()
            with open(os.path.join(directory, 'model.p'), 'wb') as outfile:
                pickle.dump(model, outfile, pickle.HIGHEST_PROTOCOL)
            model.pass_results_to_supply()
            model.calculate_supply()
            model.supply.calculate_loop()
            if save_models:
                with open(os.path.join(directory, 'full_model_run.p'), 'wb') as outfile:
                    pickle.dump(model, outfile, pickle.HIGHEST_PROTOCOL)
        elif resolve_demand and not resolve_supply: 
            raise ValueError('Cant resolve demand and not resolve supply')
        elif resolve_supply and not resolve_demand:
            with open(os.path.join(directory, 'model.p'), 'rb') as infile:
                model = pickle.load(infile)
            model.model_config(db_path, cfgfile_path, custom_pint_definitions_path)
            model.pass_results_to_supply()
            model.calculate_supply()
            model.supply.calculate_loop()
            if save_models:
                with open(os.path.join(directory, 'full_model_run.p'), 'wb') as outfile:
                    pickle.dump(model, outfile, pickle.HIGHEST_PROTOCOL)
        else:
            with open(os.path.join(directory, 'full_model_run.p'), 'rb') as infile:
                model = pickle.load(infile)
            model.model_config(db_path, cfgfile_path, custom_pint_definitions_path)   
        model.supply.calculate_supply_outputs()
        model.pass_results_to_demand()
        model.calculate_combined_results()
        model.export_results()

