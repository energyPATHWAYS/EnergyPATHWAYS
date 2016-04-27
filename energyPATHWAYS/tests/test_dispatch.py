# -*- coding: utf-8 -*-
__author__ = 'Ryan'

import unittest
import energyPATHWAYS
import numpy as np



import pylab


generator_supply_curve = energyPATHWAYS.dispatch_classes.Dispatch.generator_supply_curve
cluster_generators = energyPATHWAYS.dispatch_classes.Dispatch._cluster_generators

pmax = np.array([.001, .01, .1, 1, 10, 60, 50, 20, 20, 5, 2, 2.4, 2.6])
marginal_cost = np.array([80, 70, 60, 50, 40, 45, 60, 30, 61, 80, 100, 42, 55])
FORs = np.array([0, 0, 0, 0, 0, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05])
MORs = FORs[-1::-1]
must_run = np.array([0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1])

decimals = 1
zero_mc_4_must_run = True

n_clusters = 4
mc_approx = cluster_generators(n_clusters, pmax, marginal_cost, FORs, MORs, must_run, pad_stack=True, zero_mc_4_must_run=zero_mc_4_must_run)
new_supply_curve = generator_supply_curve(mc_approx['pmax'], mc_approx['marginal_cost'], mc_approx['FORs'], mc_approx['MORs'], mc_approx['must_run'], decimals, zero_mc_4_must_run)
pylab.plot(new_supply_curve)

supply_curve = generator_supply_curve(pmax, marginal_cost, FORs, MORs, must_run, decimals, zero_mc_4_must_run)
pylab.plot(supply_curve)

