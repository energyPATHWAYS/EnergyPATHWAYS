# -*- coding: utf-8 -*-
__author__ = 'Ryan'

import unittest
import energyPATHWAYS
import numpy as np
import pandas as pd
import pylab
import os
import time
import math
import copy
from ddt import ddt, data, unpack
from energyPATHWAYS import dispatch_generators
from energyPATHWAYS import dispatch_maintenance
import pandas as pd

class TestGeneratorDispatch(unittest.TestCase):
    # def __init__(self):
    #     self.data_dir = os.path.join(os.getcwd(), 'test_dispatch_data')

    def setUp(self):
        self.data_dir = os.path.join(os.getcwd(), 'test_dispatch_data')

    def tearDown(self):
        pass

    def _set_simple_dispatch_inputs(self):
        self.pmaxs = np.array([.00000000000001, .001, .01, .1, 1, 10, 60, 50, 20, 20, 5, 2, 2.4, 2.6])
        self.marginal_costs = np.array([30, 80, 70, 60, 50, 40, 45, 60, 30, 61, 80, 100, 42, 55])
        self.FORs = np.array([0, 0, 0, 0, 0, 0, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05])
        self.MORs = self.FORs[-1::-1]
        self.must_runs = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1])
        self.n_clusters = 4
        self.zero_mc_4_must_run = True
        self.pad_stack = True
        self.categories = [1]*4 + [2]*5 + [4]*5
        self.load = None # we need to make something up here if we want to use this

    def _set_detailed_dispatch_inputs(self):
        self.load = pd.DataFrame.from_csv(os.path.join(self.data_dir, 'load.csv'))['Load 2']
        self.load = self.load.values.flatten()

        generator_params = pd.DataFrame.from_csv(os.path.join(self.data_dir, 'generator_params.csv'))
        self.marginal_costs = generator_params['marginal_costs'].values
        self.pmaxs = generator_params['pmaxs'].values
        self.FORs = generator_params['FOR'].values
        self.MORs = generator_params['MOR'].values
        self.must_runs = generator_params['must_runs'].values
        self.capacity_weights = generator_params['capacity_weights'].values
        self.categories = generator_params['categories'].values

        self.dispatch_periods = pd.DataFrame.from_csv(os.path.join(self.data_dir, 'dispatch_periods.csv'))
        self.dispatch_periods = self.dispatch_periods['week'].values.flatten()

        self.reserves = 0.05

    def test_simple_generator_dispatch_problem(self):
        self._set_simple_dispatch_inputs()

    def _helper_return_generator_maintenance(self):
        MOR = dispatch_maintenance.schedule_generator_maintenance(self.load, self.pmaxs, self.MORs,
                                                                 dispatch_periods=self.dispatch_periods)
        return MOR

    def test_complex_maintenance_sums(self):
        # This compares the scheduled maintenance by month to the annual maintenance rate
        self._set_detailed_dispatch_inputs()
        MOR = dispatch_maintenance.schedule_generator_maintenance(self.load, self.pmaxs, self.MORs, dispatch_periods=self.dispatch_periods)
        self.assertAlmostEqual(np.sum(self.MORs * self.pmaxs), np.sum(MOR * self.pmaxs) / float(len(set(self.dispatch_periods))))

    def test_complex_maintenance_no_month_worse_off(self):
        # after scheduling maintenance, no month should have swapped places with another month in terms of degree of capacity shortage
        self._set_detailed_dispatch_inputs()
        MOR = dispatch_maintenance.schedule_generator_maintenance(self.load, self.pmaxs, self.MORs, dispatch_periods=self.dispatch_periods)
        # TODO

    def test_complex_maintenance_sums_with_flat_load(self):
        # This compares the scheduled maintenance by month to the annual maintenance rate
        self._set_detailed_dispatch_inputs()
        self.load = np.array([np.sum(self.pmaxs)] * len(self.dispatch_periods))
        MOR = dispatch_maintenance.schedule_generator_maintenance(self.load, self.pmaxs, self.MORs, dispatch_periods=self.dispatch_periods)
        self.assertAlmostEqual(np.sum(self.MORs * self.pmaxs), np.sum(MOR * self.pmaxs) / float(len(set(self.dispatch_periods))))

    def test_complex_no_maintenance_in_highest_month(self):
        # This makes sure that in the period with the highest load, we are not scheduling maintenance
        self._set_detailed_dispatch_inputs()
        self.load -= np.median(self.load)
        MOR = dispatch_maintenance.schedule_generator_maintenance(self.load, self.pmaxs, self.MORs, dispatch_periods=self.dispatch_periods)
        group_cuts = list(np.where(np.diff(self.dispatch_periods) != 0)[0] + 1) if self.dispatch_periods is not None else None
        sum_across_dispatch_period = MOR.sum(axis=1)
        self.assertAlmostEqual(0, sum_across_dispatch_period[np.nonzero(group_cuts > np.argmax(self.load))[0][0]])

    def test_complex_maintenance_zero_maintenance_rate(self):
        # This makes sure that in the period with the highest load, we are not scheduling maintenance
        self._set_detailed_dispatch_inputs()
        self.MORs[:] = 0
        MOR = dispatch_maintenance.schedule_generator_maintenance(self.load, self.pmaxs, self.MORs, dispatch_periods=self.dispatch_periods)
        self.assertAlmostEqual(0, MOR.sum())

    def _helper_return_dispatch_results(self):
        MOR = self._helper_return_generator_maintenance()
        dispatch_results = dispatch_generators.generator_stack_dispatch(self.load, self.pmaxs, self.marginal_costs, self.dispatch_periods,
                                                                        FOR=self.FORs, MOR=MOR, must_runs=self.must_runs,
                                                                        capacity_weights=self.capacity_weights,
                                                                        gen_categories=self.categories, return_dispatch_by_category=True,
                                                                        reserves=self.reserves)
        return dispatch_results

    def test_complex_generator_generation(self):
        # the generation should equal the sum of positive load
        self._set_detailed_dispatch_inputs()
        dispatch_results = self._helper_return_dispatch_results()
        generation_by_unit = dispatch_results['generation']
        self.assertAlmostEqual(np.sum(generation_by_unit), np.sum(self.load[self.load > 0]))
        return dispatch_results

    def test_complex_generator_generation_with_negative_load(self):
        # the generation should equal the sum of positive load
        self._set_detailed_dispatch_inputs()
        self.load -= np.median(self.load)
        self.must_runs[:] = 0
        dispatch_results = self._helper_return_dispatch_results()
        generation_by_unit = dispatch_results['generation']
        self.assertAlmostEqual(np.sum(generation_by_unit), np.sum(self.load[self.load > 0]))

    def test_complex_generator_generation_with_zero_load(self):
        # the generation should equal the sum of positive load
        self._set_detailed_dispatch_inputs()
        self.load[:] = 0
        self.must_runs[:] = 0
        dispatch_results = self._helper_return_dispatch_results()
        generation_by_unit = dispatch_results['generation']
        self.assertAlmostEqual(np.sum(generation_by_unit), 0)

    def test_complex_generator_generation_with_zero_load_and_must_run_generation(self):
        # the generation should equal the sum of positive load
        self._set_detailed_dispatch_inputs()
        self.load[:] = 0
        self.FORs[:] = 0
        self.MORs[:] = 0
        dispatch_results = self._helper_return_dispatch_results()
        generation_by_unit = dispatch_results['generation']
        self.assertAlmostEqual(np.sum(generation_by_unit), np.sum(self.pmaxs[np.nonzero(self.must_runs)]*len(self.load)))

    def test_complex_generator_generation_all_generators_must_run(self):
        # the generation should equal the sum of positive load
        self._set_detailed_dispatch_inputs()
        self.must_runs[:] = 1
        self.FORs[:] = 0
        self.MORs[:] = 0
        dispatch_results = self._helper_return_dispatch_results()
        gen_cf = dispatch_results['gen_cf']
        positive_pmax = np.nonzero(self.pmaxs >= 1e-15)[0]
        np.testing.assert_almost_equal(gen_cf[positive_pmax], np.ones(len(positive_pmax)))
        # return dispatch_results

    def test_complex_generator_capacity_factors(self):
        # the capacity factors * pmax * load should equal the energy generation
        self._set_detailed_dispatch_inputs()
        dispatch_results = self._helper_return_dispatch_results()
        gen_cf = dispatch_results['gen_cf']
        generation_by_unit = dispatch_results['generation']
        np.testing.assert_almost_equal(gen_cf * (self.pmaxs + dispatch_results['stock_changes']) * len(self.load), generation_by_unit)

    def test_complex_generator_capacity_factors_are_less_than_one(self):
        # all capacity factors should be between zero and one
        self._set_detailed_dispatch_inputs()
        dispatch_results = self._helper_return_dispatch_results()
        gen_cf = dispatch_results['gen_cf']
        self.assertLessEqual(round(max(gen_cf), 9), 1)

    def test_complex_generator_capacity_factors_are_greater_than_zero(self):
        # all capacity factors should be between zero and one
        self._set_detailed_dispatch_inputs()
        dispatch_results = self._helper_return_dispatch_results()
        gen_cf = dispatch_results['gen_cf']
        self.assertGreaterEqual(round(max(gen_cf), 9), 0)

    def test_complex_generator_dispatch_stock_changes(self):
        self._set_detailed_dispatch_inputs()
        new_max_load = np.sum(self.pmaxs) * .75
        self.load *= np.max(self.load)/new_max_load

        dispatch_results = self._helper_return_dispatch_results()
        # return dispatch_results
        stock_changes = dispatch_results['stock_changes']

        derated_capacity = (self.pmaxs * (1 - self.FORs)).sum()
        derated_stock_changes = (stock_changes * (1 - self.FORs)).sum()

        max_load_by_period = np.array([np.max(self.load[self.dispatch_periods==p]) for p in np.unique(self.dispatch_periods)])
        max_load_plus_reserves = (1 + self.reserves) * max_load_by_period
        max_period = np.argmax(max_load_plus_reserves-derated_capacity-derated_stock_changes)

        self.assertAlmostEqual(max_load_plus_reserves[max_period], derated_capacity + derated_stock_changes)

    def plot_dispatch_outputs(self):
        #pylab.plot(load)
        #pylab.plot(np.array([sum(pmaxs[0]+stock_changes)]*len(load)))
        #pylab.plot(np.array([sum(pmaxs[0])]*len(load)))
        #
        #pylab.plot(np.sum(pmaxs * MOR, axis=1))

        #pylab.plot(marginal_costs, dispatch_results['gen_cf'], '*')
        #pylab.plot(dispatch_results['market_price'])
        #pylab.plot(dispatch_results['production_cost'])
        #pylab.plot(dispatch_results['gen_dispatch_shape'])

        #print np.mean(dispatch_results['market_price'])
        #print np.sum(dispatch_results['production_cost'])
        pass


# self = TestGeneratorDispatch()
# t = time.time()
# MOR = self.test_complex_no_maintenance_in_highest_month()
# mean_across_dispatch_period = MOR.mean(axis=1)
# sum_across_dispatch_period = MOR.sum(axis=1)
# group_cuts = list(np.where(np.diff(self.dispatch_periods)!=0)[0]+1) if self.dispatch_periods is not None else None
# print sum_across_dispatch_period[np.nonzero(group_cuts > np.argmax(self.load))[0][0]]
# pylab.plot(mean_across_dispatch_period)
# t = energyPATHWAYS.util.time_stamp(t)



# Initially takes 5.669000 seconds to execute
# Now takes 3.400000

# data_dir = os.path.join(os.getcwd(), 'test_dispatch_data')
# generator_params = pd.DataFrame.from_csv(os.path.join(data_dir, 'generator_params_pge_error.csv'))
# pmaxs = generator_params['pmaxs'].values
# MORs = generator_params['MOR'].values
# marginal_costs = np.arange(0,.01*len(MORs),.01)
#
# dispatch_periods = pd.DataFrame.from_csv(os.path.join(data_dir, 'dispatch_periods_pge_error.csv'))
# dispatch_periods = dispatch_periods['week'].values.flatten()
#
# load = pd.DataFrame.from_csv(os.path.join(data_dir, 'load_pge_error.csv'))['load']
# load = load.values.flatten()
#
# t=time.time()
# MOR = dispatch_maintenance.schedule_generator_maintenance(load, pmaxs, MORs, dispatch_periods, marginal_costs)
# t=energyPATHWAYS.util.time_stamp(t)
# MOR2 = dispatch_maintenance.schedule_generator_maintenance_steady(load, pmaxs, MORs, dispatch_periods, np.argsort(marginal_costs))
# t=energyPATHWAYS.util.time_stamp(t)
#
# pd.DataFrame(MOR.mean(axis=1)).plot()
# pd.DataFrame(MOR2.mean(axis=1)).plot()