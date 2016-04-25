# -*- coding: utf-8 -*-
__author__ = 'Ben, Ryan, Michael'

import numpy as np
from collections import defaultdict
import pandas as pd
import energyPATHWAYS
from energyPATHWAYS.time_series import TimeSeries
import unittest
from matplotlib import pyplot as plt


class TestTimeSeries(unittest.TestCase):
    def setUp(self):
        self.methods = ('linear_interpolation', 'linear_regression', 'logistic', 'cubic', 'quadratic', 'nearest')
        
    def test_clean_empty_data(self):
        newindex = np.arange(2000, 2051)

        x = np.array([])
        y = np.array([])
        self.run_all_cleaning_methods(x, y, newindex)

    def test_clean_one_point(self):
        newindex = np.arange(2000, 2051)
        
        x = np.array([2010])
        y = np.array([.1])
        self.run_all_cleaning_methods(x, y, newindex)

    def test_clean_two_points(self):
        newindex = np.arange(2000, 2051)
        
        x = np.array([2010, 2050])
        y = np.array([.1, .5])
        self.run_all_cleaning_methods(x, y, newindex)

    def test_clean_three_points(self):
        newindex = np.arange(2000, 2051)
        
        x = np.array([2010, 2018, 2025])
        y = np.array([.8, .7, .4])
        self.run_all_cleaning_methods(x, y, newindex)

    def test_clean_scurve_points(self):
        newindex = np.arange(2000, 2051)
        
        x = np.array([2010, 2018, 2025, 2040, 2050])
        y = np.array([.8, .7, .4, .35, .34])
        self.run_all_cleaning_methods(x, y, newindex)

    def test_clean_linear_points(self):
        newindex = np.arange(2000, 2051)
        
        x = np.array([2010, 2020, 2030, 2040, 2050])
        y = np.array([.1, .2, .3, .4, .5])
        self.run_all_cleaning_methods(x, y, newindex)

    def test_clean_quadratic_points(self):
        newindex = np.arange(2000, 2051)
        
        x = np.arange(2010, 2030)
        y = (x-2010)**2
        self.run_all_cleaning_methods(x, y, newindex)


    def run_all_cleaning_methods(self, x, y, newindex):
        for method in self.methods:
            print method
            print x, y
            data = pd.DataFrame(y, index=x)
            newdata = TimeSeries.clean(data, newindex=newindex, interpolation_method=method)

            plt.plot(newdata.index, newdata[0])
            plt.plot(x, y, '.')


#newindex = np.arange(2015, 2025)

#newindex = np.arange(2012, 2017)
#x = np.array([2015, 2018, 2020])
#y = np.array([.8, .7, .4])
#data = pd.DataFrame(y, index=x)
#newdata = TimeSeries.clean(data, newindex=newindex, interpolation_method='linear_interpolation', extrapolation_method='nearest')
#
#
#newindex = np.arange(2020, 2025)
#multi_data = pd.concat([data]*3, keys=['a', 'b', 'c'], names=['dummy', 'year'])
#newdata2 = TimeSeries.clean(multi_data, time_index_name='year', newindex=newindex, interpolation_method='linear_interpolation', extrapolation_method='nearest')


#newindex = np.arange(2015, 2017)
#multi_data = pd.concat([data]*3, keys=['a', 'b', 'c'], names=['dummy', 'year'])
#newdata2 = TimeSeries.clean(multi_data, time_index_name='year', newindex=newindex, interpolation_method='linear_interpolation', extrapolation_method='nearest')


#raw_values = pd.read_csv('raw_values_example_for_clean_timeseries.csv')
#raw_values.set_index(['us', 'efficiency_type', 'supply_node', 'year'], inplace=True)
#raw_values.sort_index(inplace=True)
#
#newindex = [2015]
#newdata3 = TimeSeries.clean(raw_values, time_index_name='year', newindex=newindex, interpolation_method='linear_interpolation', extrapolation_method='nearest')
#
#print newdata3


newindex = np.arange(2012, 2030)
x = np.array([2015, 2016, 2018, 2020, 2021, 2025])
y = np.array([.8, np.inf, .7, .4, np.inf, np.nan])
data = pd.DataFrame(y, index=x)
newdata = TimeSeries.clean(data, newindex=newindex, interpolation_method='linear_interpolation', extrapolation_method='exponential')


