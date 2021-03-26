# -*- coding: utf-8 -*-
"""
Created on Thu Jul 30 09:35:30 2015

@author: Ryan Jones
"""

import numpy as np
import pdb
                                        
def solve_IO(IO_matrix, f=None):
    """ Given, the IO_matrix and intermediate demand, solve for final demand
        -> Inputs and Outputs are numpy arrays
        if no demand (d) is passed, the inverse is returned
    """
    identity_matrix = np.eye(len(IO_matrix), len(IO_matrix))
    energy_supply = np.linalg.solve(identity_matrix - IO_matrix, identity_matrix if f is None else f)
    return energy_supply

def inv_IO(IO_matrix):
    identity_matrix = np.eye(len(IO_matrix), len(IO_matrix))
    return np.linalg.inv(identity_matrix - IO_matrix)


# directory = os.getcwd()
#
# ## In IO, rows are inputs, columns are outputs
# IO_matrix = pd.DataFrame.from_csv(r'C:\github\EnergyPATHWAYS\energyPATHWAYS\tests\IO.csv').fillna(0)
# energy_demand = np.array([0,0,0,100])
# #
# energy_supply = solve_IO(IO_matrix.values, energy_demand)
#


