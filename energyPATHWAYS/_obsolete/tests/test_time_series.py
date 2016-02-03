__author__ = 'Ryan Jones'

import unittest
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from pathways.time_series import TimeSeries


class TestTimeSeries(unittest.TestCase):
    def test_clean(self):
        newindex = np.arange(2000, 2051)

        x = np.array([])
        y = np.array([])
        self.run_all_cleaning_methods(x, y, newindex)

        x = np.array([2010])
        y = np.array([.1])
        self.run_all_cleaning_methods(x, y, newindex)

        x = np.array([2010, 2050])
        y = np.array([.1, .5])
        self.run_all_cleaning_methods(x, y, newindex)

        x = np.array([2010, 2018, 2025])
        y = np.array([.8, .7, .4])
        self.run_all_cleaning_methods(x, y, newindex)

        x = np.array([2010, 2018, 2025, 2040, 2050])
        y = np.array([.8, .7, .4, .35, .34])
        self.run_all_cleaning_methods(x, y, newindex)

        x = np.array([2010, 2020, 2030, 2040, 2050])
        y = np.array([.1, .2, .3, .4, .5])
        self.run_all_cleaning_methods(x, y, newindex)

        x = np.arange(2010, 2030)
        y = (x - 2010) ** 2
        self.run_all_cleaning_methods(x, y, newindex)

    @staticmethod
    def run_all_cleaning_methods(self, x, y, newindex):
        methods = ('linear_interpolation', 'linear_regression', 'logistic', 'cubic', 'quadratic', 'nearest')

        for method in methods:
            print method
            print x, y
            data = pd.DataFrame(y, index=x)
            newdata = TimeSeries.clean(data, newindex=newindex, interpolation_method=method)

            plt.plot(newdata.index, newdata[0])
            plt.plot(x, y, '.')