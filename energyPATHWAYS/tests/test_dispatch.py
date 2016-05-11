# -*- coding: utf-8 -*-
__author__ = 'Ryan'

import unittest
import energyPATHWAYS
import numpy as np
import pandas as pd
import pylab
import os


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

util = energyPATHWAYS.util
dispatch_to_energy_budget = energyPATHWAYS.dispatch_classes.Dispatch.dispatch_to_energy_budget
schedule_generator_maintenance = energyPATHWAYS.dispatch_classes.Dispatch.schedule_generator_maintenance
generator_stack_dispatch = energyPATHWAYS.dispatch_classes.Dispatch.schedule_generator_maintenance

load = pd.DataFrame.from_csv(os.path.join(os.getcwd(), 'test_dispatch_data', 'load.csv'))
load = load.values.flatten()

dispatch_periods = pd.DataFrame.from_csv(os.path.join(os.getcwd(), 'test_dispatch_data', 'dispatch_periods.csv'))
dispatch_periods = dispatch_periods.values.flatten()

marginal_costs = pd.DataFrame.from_csv(os.path.join(os.getcwd(), 'test_dispatch_data', 'marginal_costs.csv')).values
pmaxs = pd.DataFrame.from_csv(os.path.join(os.getcwd(), 'test_dispatch_data', 'pmaxs.csv')).values
outage_rates = pd.DataFrame.from_csv(os.path.join(os.getcwd(), 'test_dispatch_data', 'outage_rates.csv')).values
must_runs = pd.DataFrame.from_csv(os.path.join(os.getcwd(), 'test_dispatch_data', 'must_runs.csv')).values


#dispatch = dispatch_to_energy_budget(load, [-5000*8760/12]*12, dispatch_periods=dispatch_periods, pmins=0, pmaxs=10000)
#pylab.plot(load)
#pylab.plot(load+dispatch)

outage_rates[0][0] = .5

maintenance_rates = schedule_generator_maintenance(load, pmaxs, outage_rates[0], dispatch_periods=dispatch_periods, min_maint=0., max_maint=.15, load_ptile=99.8)
pd.DataFrame(maintenance_rates).to_clipboard()

#dispatch_results = generator_stack_dispatch(load, pmaxs, marginal_costs, dispatch_periods, outage_rates, maintenance_rates, must_runs)


#plt.plot(dispatch_results['gen_cf'])
#plt.plot(dispatch_results['market_price'])
#plt.plot(dispatch_results['production_cost'])

#print np.mean(dispatch_results['market_price'])
#print np.sum(dispatch_results['production_cost'])

