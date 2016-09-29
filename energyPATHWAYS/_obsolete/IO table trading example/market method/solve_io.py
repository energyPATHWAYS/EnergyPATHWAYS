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

def inv_IO(IO_matrix):
    identity_matrix = np.eye(len(IO_matrix), len(IO_matrix))
    return np.linalg.inv(identity_matrix - IO_matrix)

# In IO, rows are inputs, columns are outputs
IO_matrix = pd.DataFrame.from_csv('IO_trading.csv', index_col=[0,1], header=1)
IO_matrix.columns = IO_matrix.index

energy_demand = pd.DataFrame.from_csv('demand.csv', index_col=[0,1])

final_energy = pd.DataFrame(solve_IO(IO_matrix.values, energy_demand.values), index=energy_demand.index, columns=['final energy'])
final_energy.to_csv('final_energy.csv')


#energy_demand = pd.DataFrame.from_csv('demand.csv')
#direct_emissions = pd.DataFrame.from_csv('direct_emissions.csv')
#embodied_emissions = pd.DataFrame.from_csv('embodied_carbon.csv')
#
#final_energy = pd.DataFrame(solve_IO(IO_matrix.values, energy_demand.values), index=energy_demand.index, columns=['final energy'])
#final_energy.to_csv('final_energy.csv')
#
#inverse = pd.DataFrame(inv_IO(IO_matrix.values), index=IO_matrix.index, columns=IO_matrix.columns)
#inverse.to_csv('inverse.csv')
#
#effective_emissions = pd.DataFrame(index=energy_demand.index)
#effective_emissions['direct'] = np.dot(direct_emissions.values.flatten(), inverse.values)
#effective_emissions['embodied'] = np.dot(embodied_emissions.values.flatten(), inverse.values)
#
#
#effective_emissions.to_csv('effective_emissions.csv')
