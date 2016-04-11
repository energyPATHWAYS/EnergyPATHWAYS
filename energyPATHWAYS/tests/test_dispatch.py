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

num_steps = 3
mc_approx = cluster_generators(num_steps, pmax, marginal_cost, FORs, MORs, must_run, pad_last_generator=False)
new_supply_curve = generator_supply_curve(mc_approx[:,0], mc_approx[:,1], np.zeros(num_steps), np.zeros(num_steps), np.zeros(num_steps), decimals, zero_mc_4_must_run)
pylab.plot(new_supply_curve)

supply_curve = generator_supply_curve(pmax, marginal_cost, FORs, MORs, must_run, decimals, zero_mc_4_must_run)
pylab.plot(supply_curve)


#def supply_curve_approx(changeovers, mc_levels, curve_max):
#    print changeovers
#    print mc_levels
#    print ''
#    counts = [int(round(changeovers[0]))] + list(np.array(np.round(np.diff(changeovers)), dtype=int)) 
#    counts.append(int(curve_max-np.sum(counts)))
#    return energyPATHWAYS.util.flatten_list([[mc]*c for mc, c in zip(mc_levels, counts)])
#
#def fix_up_x(mc_levels, changeovers, curve_max):
#    changeovers[0] = max(changeovers[0], 0)
#    changeovers[-1] = min(changeovers[-1], curve_max-1)
#    changeovers[1:] = np.max([changeovers[1:], changeovers[:-1]], axis=0)
#    changeovers[:-1] = np.min([changeovers[1:], changeovers[:-1]], axis=0)
#    
#    mc_levels[0] = max(mc_levels[0], 0)
#    mc_levels[1:] = np.max([mc_levels[1:], mc_levels[:-1]], axis=0)
#    mc_levels[:-1] = np.min([mc_levels[1:], mc_levels[:-1]], axis=0)
#    
#    return mc_levels, changeovers
#    
#
#def mse_supply_curve_approx(x, supply_curve):
#    mc_levels, changeovers = np.array_split(x, 2)
#    
#    curve_max = len(supply_curve)
#    mc_levels, changeovers = fix_up_x(mc_levels, changeovers, curve_max)
#    
#    mc_approx = supply_curve_approx(changeovers, mc_levels, curve_max)
#    
#    return np.sum((np.array(mc_approx) - np.array(supply_curve))**2)/float(len(supply_curve))
#
#supply_curve = generator_supply_curve(pmax, marginal_cost, FORs, MORs, must_run, decimals, zero_mc_4_must_run)
#
#num_steps = 4
#
#curve_max = len(supply_curve)
#changeovers = np.arange(1, num_steps)*curve_max/float(num_steps)
#mc_levels = np.percentile(supply_curve, np.linspace(0, 100, num_steps))
#
##mc_start = supply_curve_approx(changeovers, mc_levels, curve_max)
##pylab.plot(mc_start)
#
#x0 = np.concatenate((mc_levels, changeovers))
#opt = optimize.minimize(mse_supply_curve_approx, x0=x0, args=(supply_curve), method='Nelder-Mead')
#
#x = opt['x']
#mc_levels, changeovers = np.array_split(x, 2)
#
#mc_approx = supply_curve_approx(changeovers, mc_levels, curve_max)
#
#pylab.plot(mc_approx)
#pylab.plot(supply_curve)

