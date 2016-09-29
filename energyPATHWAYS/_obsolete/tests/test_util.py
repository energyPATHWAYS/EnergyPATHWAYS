# -*- coding: utf-8 -*-
"""
Created on Wed Jul 29 14:58:23 2015

@author: Ryan Jones
"""

import pandas as pd
import config  # must happen before importing util
import util
import os
import numpy as np

population = pd.DataFrame.from_csv(os.path.join('data4tests', 'population.csv'))
shower_intensity = pd.DataFrame.from_csv(os.path.join('data4tests', 'showers pp.csv'))

population.set_index([x for x in population.columns.tolist() if x != 'value'], inplace=True)
shower_intensity.set_index([x for x in shower_intensity.columns.tolist() if x != 'value'], inplace=True)

total_showers_d = util.multindex_operation(shower_intensity, population, operation='divide', how='left',
                                           return_col_name='value')

total_showers_m = util.multindex_operation(total_showers_d, population, operation='multiply', how='right',
                                           return_col_name='value')

np.testing.assert_approx_equal(total_showers_m.sum()[0], 1800)

