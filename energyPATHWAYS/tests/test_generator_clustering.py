# -*- coding: utf-8 -*-
__author__ = 'Ryan'

import unittest
import energyPATHWAYS
import numpy as np
import pandas as pd
import pylab
import os
import time
from energyPATHWAYS.dispatch_classes import Dispatch
import math
import copy

class TestClusterGenerators(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def _set_simple_dispatch_inputs(self):
        self.pmax = np.array([.0000001, .001, .01, .1, 1, 10, 60, 50, 20, 20, 5, 2, 2.4, 2.6])
        self.marginal_cost = np.array([30, 80, 70, 60, 50, 40, 45, 60, 30, 61, 80, 100, 42, 55])
        self.FORs = np.array([0, 0, 0, 0, 0, 0, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05])
        self.MORs = self.FORs[-1::-1]
        self.must_run = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1])
        self.n_clusters = 4
        self.zero_mc_4_must_run = True
        self.pad_stack=True

    def test_simple_generator_dispatch_problem(self):
        self._set_simple_dispatch_inputs()

    def _set_simple_cluster_inputs(self):
        self.pmax = np.array([.001, .01, .1, 1, 10, 60, 50, 20, 20, 5, 2, 2.4, 2.6])
        self.marginal_cost = np.array([80, 70, 60, 50, 40, 45, 60, 30, 61, 80, 100, 42, 55])
        self.FORs = np.array([0, 0, 0, 0, 0, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05])
        self.MORs = self.FORs[-1::-1]
        self.must_run = np.array([0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1])
        self.n_clusters = 4
        self.zero_mc_4_must_run = True
        self.pad_stack=True

    def _helper_run_cluster_generators(self):
        mc_approx = Dispatch._cluster_generators(self.n_clusters,
                                                   self.pmax,
                                                   self.marginal_cost,
                                                   self.FORs,
                                                   self.MORs,
                                                   self.must_run,
                                                   pad_stack=self.pad_stack,
                                                   zero_mc_4_must_run=self.zero_mc_4_must_run)
        return mc_approx

    def test_generator_cluster_FORs(self):
        self._set_simple_cluster_inputs()
        mc_approx = self._helper_run_cluster_generators()
        np.testing.assert_almost_equal(mc_approx['FORs'], [0.05,  0.04458874,  0.04892368,  0.04989024])

    def test_generator_cluster_MORs(self):
        self._set_simple_cluster_inputs()
        mc_approx = self._helper_run_cluster_generators()
        np.testing.assert_almost_equal(mc_approx['MORs'], [0., 0.0487013, 0.05, 0.00010976])

    def test_generator_cluster_derated_pmax(self):
        self._set_simple_cluster_inputs()
        mc_approx = self._helper_run_cluster_generators()
        np.testing.assert_almost_equal(mc_approx['derated_pmax'], [23.37, 83.98, 46.17, 163.0409])

    def test_generator_cluster_marginal_cost(self):
        self._set_simple_cluster_inputs()
        mc_approx = self._helper_run_cluster_generators()
        np.testing.assert_almost_equal(mc_approx['marginal_cost'], [0., 41.12895928, 59.79423868, 79.9800439])

    def test_generator_cluster_must_run(self):
        self._set_simple_cluster_inputs()
        mc_approx = self._helper_run_cluster_generators()
        np.testing.assert_almost_equal(mc_approx['must_run'], [1, 0, 0, 0])

    def test_generator_cluster_pmax(self):
        self._set_simple_cluster_inputs()
        mc_approx = self._helper_run_cluster_generators()
        np.testing.assert_almost_equal(mc_approx['pmax'], [24.6, 92.4, 51.1, 178.122])

    def plot_cluster_generator_example(self):
        decimals = 1
        self._set_simple_cluster_inputs()
        mc_approx = self._helper_run_cluster_generators()
        new_supply_curve = Dispatch.generator_supply_curve(mc_approx['pmax'], mc_approx['marginal_cost'],
                                                           mc_approx['FORs'], mc_approx['MORs'], mc_approx['must_run'],
                                                           decimals, self.zero_mc_4_must_run)
        pylab.plot(new_supply_curve)
        supply_curve = Dispatch.generator_supply_curve(self.pmax, self.marginal_cost, self.FORs, self.MORs,
                                                       self.must_run, decimals, self.zero_mc_4_must_run)
        pylab.plot(supply_curve)
