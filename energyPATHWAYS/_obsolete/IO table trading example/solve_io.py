# -*- coding: utf-8 -*-
"""
Created on Thu Jul 30 09:35:30 2015

@author: Ryan Jones
"""

import pandas as pd
import numpy as np
import time


def solve_IO(IO_matrix, energy_demand):
    """ Given, the IO_matrix and intermediate demand, solve for final demand
        -> Inputs and Outputs are numpy arrays
    """
    identity_matrix = np.eye(len(IO_matrix), len(IO_matrix))
    energy_supply = np.linalg.solve(identity_matrix - IO_matrix, energy_demand)
    return energy_supply

# In IO, rows are inputs, columns are outputs
IO_matrix = pd.DataFrame.from_csv('IO.csv')
energy_demand = pd.DataFrame.from_csv('demand.csv')

energy_supply = solve_IO(IO_matrix.values, energy_demand.values)

back_to_demand = energy_supply - np.dot(IO_matrix.values, energy_supply)

##################
# Perturb system
##################
perturb_diesel = pd.DataFrame.from_csv('perturb_diesel.csv')
perturb_pellets = pd.DataFrame.from_csv('perturb_pellets.csv')

energy_supply_unit_diesel = solve_IO(IO_matrix.values, perturb_diesel.values)
energy_supply_unit_pellets = solve_IO(IO_matrix.values, perturb_pellets.values)


1.1378 * 50 + 0.378 * 100 == 94.69
