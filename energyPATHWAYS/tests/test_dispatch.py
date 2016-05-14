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

#generator_supply_curve = energyPATHWAYS.dispatch_classes.Dispatch.generator_supply_curve
#cluster_generators = energyPATHWAYS.dispatch_classes.Dispatch._cluster_generators
#
#pmax = np.array([.001, .01, .1, 1, 10, 60, 50, 20, 20, 5, 2, 2.4, 2.6])
#marginal_cost = np.array([80, 70, 60, 50, 40, 45, 60, 30, 61, 80, 100, 42, 55])
#FORs = np.array([0, 0, 0, 0, 0, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05])
#MORs = FORs[-1::-1]
#must_run = np.array([0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1])
#
#
#decimals = 1
#zero_mc_4_must_run = True
#
#n_clusters = 4
#mc_approx = cluster_generators(n_clusters, pmax, marginal_cost, FORs, MORs, must_run, pad_stack=True, zero_mc_4_must_run=zero_mc_4_must_run)
#new_supply_curve = generator_supply_curve(mc_approx['pmax'], mc_approx['marginal_cost'], mc_approx['FORs'], mc_approx['MORs'], mc_approx['must_run'], decimals, zero_mc_4_must_run)
#pylab.plot(new_supply_curve)
#
#supply_curve = generator_supply_curve(pmax, marginal_cost, FORs, MORs, must_run, decimals, zero_mc_4_must_run)
#pylab.plot(supply_curve)

test_data_dir = os.path.join(os.getcwd(), 'test_dispatch_data')

util = energyPATHWAYS.util
dispatch_to_energy_budget = energyPATHWAYS.dispatch_classes.Dispatch.dispatch_to_energy_budget
schedule_generator_maintenance = energyPATHWAYS.dispatch_classes.Dispatch.schedule_generator_maintenance
generator_stack_dispatch = energyPATHWAYS.dispatch_classes.Dispatch.generator_stack_dispatch

load = pd.DataFrame.from_csv(os.path.join(test_data_dir, 'load.csv'))['Load 2']
load = load.values.flatten()
#load-=30000
#load = np.vstack((load, load))

dispatch_periods = pd.DataFrame.from_csv(os.path.join(test_data_dir, 'dispatch_periods.csv'))
dispatch_periods = dispatch_periods.values.flatten()

#marginal_costs = pd.DataFrame.from_csv(os.path.join(test_data_dir, 'marginal_costs.csv')).values.flatten()
#pmaxs = pd.DataFrame.from_csv(os.path.join(test_data_dir, 'pmaxs.csv')).values
#outage_rates = pd.DataFrame.from_csv(os.path.join(test_data_dir, 'outage_rates.csv')).values
#must_runs = pd.DataFrame.from_csv(os.path.join(test_data_dir, 'must_runs.csv')).values

generator_params = pd.DataFrame.from_csv(os.path.join(test_data_dir, 'generator_params.csv'))
marginal_costs = generator_params['marginal_costs'].values
pmaxs = generator_params['pmaxs'].values
FOR = generator_params['FOR'].values
MOR = generator_params['MOR'].values
must_runs = generator_params['must_runs'].values
capacity_weights = generator_params['capacity_weights'].values

#dispatch = dispatch_to_energy_budget(load, [-5000*8760/12]*12, dispatch_periods=dispatch_periods, pmins=0, pmaxs=10000)
#pylab.plot(load)
#pylab.plot(load+dispatch)

#MOR = np.copy(outage_rates[0])
#MOR[marginal_costs<33] = 1.5

#pmaxs = pmaxs[0]
#pmaxs[0] = -.1

operating_reserves = 0.05
reserves = 0.05

t = time.time()
MOR = schedule_generator_maintenance(load, pmaxs, MOR, dispatch_periods=dispatch_periods)
print time.time() - t
pd.DataFrame(MOR).to_clipboard()

dispatch_results = generator_stack_dispatch(load, pmaxs, marginal_costs, dispatch_periods, FOR=FOR, MOR=MOR, must_runs=must_runs, capacity_weights=None)


#pylab.plot(marginal_costs, dispatch_results['gen_cf'], '*')
#pylab.plot(dispatch_results['market_price'])
#pylab.plot(dispatch_results['production_cost'])
#pylab.plot(dispatch_results['gen_dispatch_shape'])

#print np.mean(dispatch_results['market_price'])
#print np.sum(dispatch_results['production_cost'])

