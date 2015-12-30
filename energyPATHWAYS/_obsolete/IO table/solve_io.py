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
IO_matrix = pd.DataFrame.from_csv('IO_energy.csv')
energy_demand = pd.DataFrame.from_csv('demand.csv')

energy_supply = solve_IO(IO_matrix.values, energy_demand.values)


