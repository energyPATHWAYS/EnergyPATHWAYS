__author__ = 'Ben Haley & Ryan Jones'

import pandas as pd
import numpy as np
import cPickle as pickle
import os
from energyPATHWAYS import *
cfg = energyPATHWAYS.cfg

directory = os.getcwd()

cfgfile_path = os.path.join(directory, 'configurations.INI')
db_path = os.path.join(directory, 'pathways.db')
custom_pint_definitions_path = os.path.join(directory, 'unit_defs.txt')

###########
resolve = True
###########

if __name__ == "__main__":
    if resolve:
        model = energyPATHWAYS.PathwaysModel(db_path, cfgfile_path, custom_pint_definitions_path)
        model.configure_energy_system()
        model.populate_energy_system()
        model.populate_measures()
        model.calculate_demand_only()
        model.pass_results_to_supply()
        model.calculate_supply()

        with open(os.path.join(directory, 'model.p'), 'wb') as outfile:
            pickle.dump(model, outfile)
    
    else:
        with open(os.path.join(directory, 'model.p'), 'rb') as infile:
            model = pickle.load(infile)
        model.model_config(db_path, cfgfile_path, custom_pint_definitions_path)
    model.supply.calculate_loop()
    model.pass_results_to_demand()
    model.export_results()


