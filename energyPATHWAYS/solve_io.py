# -*- coding: utf-8 -*-
"""
Created on Thu Jul 30 09:35:30 2015

@author: Ryan Jones
"""

import numpy as np
                                        
def solve_IO(IO_matrix, d=None):
    """ Given, the IO_matrix and intermediate demand, solve for final demand
        -> Inputs and Outputs are numpy arrays
        if no demand (d) is passed, the inverse is returned
    """
    identity_matrix = np.eye(len(IO_matrix), len(IO_matrix))
    energy_supply = np.linalg.solve(identity_matrix - IO_matrix, identity_matrix if d is None else d)
    return energy_supply

def inv_IO(IO_matrix):
    identity_matrix = np.eye(len(IO_matrix), len(IO_matrix))
    return np.linalg.inv(identity_matrix - IO_matrix)

## In IO, rows are inputs, columns are outputs
#IO_matrix = pd.DataFrame.from_csv('IO.csv')
#energy_demand = pd.DataFrame.from_csv('demand.csv')
#
#energy_supply = solve_IO(IO_matrix.values, energy_demand.values)
#


