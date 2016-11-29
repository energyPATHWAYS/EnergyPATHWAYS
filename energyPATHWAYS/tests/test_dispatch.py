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
Dispatch = energyPATHWAYS.dispatch_classes.Dispatch

load = pd.DataFrame.from_csv(os.path.join(test_data_dir, 'load.csv'))['Load 2']
load = load.values.flatten()

#load = np.array([np.max(load)]*len(load))
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
categories = generator_params['categories'].values

#dispatch = dispatch_to_energy_budget(load, [-5000*8760/12]*12, dispatch_periods=dispatch_periods, pmins=0, pmaxs=10000)
#pylab.plot(load)
#pylab.plot(load+dispatch)

#MOR = np.copy(outage_rates[0])
#MOR[marginal_costs<33] = 1.5

#pmaxs = pmaxs[0]
#pmaxs[0] = -.1

capacity_reserves = 0.03
operating_reserves = 0.01

MOR = schedule_generator_maintenance(load, pmaxs, MOR, dispatch_periods=dispatch_periods)
dispatch_results = generator_stack_dispatch(load, pmaxs, marginal_costs, dispatch_periods, FOR=FOR, MOR=MOR, must_runs=must_runs, capacity_weights=capacity_weights, gen_categories=categories, return_dispatch_by_category=True)

dispatch_by_category = dispatch_results['dispatch_by_category']



#count = lambda x: len(x.T) if x.ndim>1 else len(x)
#if count(pmaxs) != count(marginal_costs):
#    raise ValueError('Number of generator pmaxs must equal number of marginal_costs')
#
#if capacity_weights is not None and capacity_weights.ndim>1:
#    raise ValueError('capacity weights should not vary across dispatch periods')
#
#load[load<0] = 0
#decimals = 6 - int(math.log10(max(np.abs(load))))
#
#load_groups = (load,) if dispatch_periods is None else np.array_split(load, np.where(np.diff(dispatch_periods)!=0)[0]+1)
#num_groups = len(load_groups)
#
#marginal_costs, pmaxs, FOR, MOR, must_runs, capacity_weights = Dispatch._format_gen_dispatch_inputs(num_groups, pmaxs, marginal_costs, dispatch_periods, FOR, MOR, must_runs, capacity_weights)
#
#market_prices, production_costs, gen_dispatch_shape = [], [], []
#gen_energies = np.zeros(pmaxs.shape[1])
#
#stock_changes = Dispatch._get_stock_changes(load_groups, pmaxs, FOR, MOR, capacity_weights, decimals, reserves=capacity_reserves)
#
#stock_changes_2 = Dispatch._get_stock_changes(load_groups, pmaxs+stock_changes, FOR, MOR, capacity_weights, decimals, reserves=capacity_reserves)

#combined_rate = Dispatch._get_combined_outage_rate(FOR[i], MOR[i])

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

