
from pyomo.environ import *
import numpy as np
import util
import config as cfg
import pdb
import pandas as pd
import copy
import dispatch_budget
import logging

def surplus_capacity(model):
    return model.surplus_capacity + model.peak_penalty * model.weight_on_peak_penalty

def define_penalty_to_preference_high_cost_gen_maint_during_peak(model):
    # if forced to choose between having high cost or low cost gen be on maintenance when load is high, we'd rather high cost gen be doing maintenance
    # this should lower production cost overall and make maintenance schedules less random
    return model.peak_penalty == sum([sum([model.marginal_costs[g]*model.max_load_by_group[i]*model.scheduled_maintenance[i, g] for g in model.g])
                                      for i in model.i])

def feasible_maintenance_constraint_0(model, i, g):
    return model.scheduled_maintenance[i, g] >= 0

def feasible_maintenance_constraint_1(model, i, g):
    return model.scheduled_maintenance[i, g] <= 1

def define_available_gen(model, i):
    return model.available_gen[i] == sum([(1 - model.scheduled_maintenance[i, g]) * model.pmax[g] for g in model.g])

def meet_maintenance_constraint(model, g):
    # average maintenance across the hours == annual maintenance rate
    return sum([model.scheduled_maintenance[i, g] * model.group_lengths[i] for i in model.i]) == model.annual_maintenace_hours[g]

def define_surplus_capacity(model, i):
    return model.surplus_capacity >= model.available_gen[i] - model.max_load_by_group[i]

def scale_load_to_system(load, pmaxs, typical_reserve=1.15):
    max_load = load.max()
    sum_cap = sum(pmaxs)
    if (max_load * typical_reserve) > sum_cap:
        assert max_load != 0
        load2 = load * (sum_cap / (max_load * typical_reserve))
        return load2
    else:
        return load

def schedule_generator_maintenance(load, pmaxs, annual_maintenance_rates, dispatch_periods, marginal_costs, print_opt=False):
    # annual maintenance rates must be between zero and one
    annual_maintenance_rates = np.clip(annual_maintenance_rates, 0, 1)

    # gives the index for the change between dispatch_periods
    group_cuts = list(np.where(np.diff(dispatch_periods) != 0)[0] + 1) if dispatch_periods is not None else None
    group_lengths = np.array([group_cuts[0]] + list(np.diff(group_cuts)) + [len(load) - group_cuts[-1]])
    num_groups = len(group_cuts) + 1

    # necessary to scale load in some cases for the optimization to work. Basically, load shouldn't be > gen
    load_scaled = scale_load_to_system(load, pmaxs)
    max_load_by_group = np.array([np.max(ls) for ls in np.array_split(load_scaled, np.array(group_cuts))])

    annual_maintenace_hours = annual_maintenance_rates*len(load)

    pmaxs_zero = np.nonzero(pmaxs==0)[0]
    pmaxs_not_zero = np.nonzero(pmaxs)[0]

    estimated_peak_penalty = sum(sum(np.outer(marginal_costs[pmaxs_not_zero],max_load_by_group).T*annual_maintenance_rates[pmaxs_not_zero]))
    estimated_surplus_capacity = (pmaxs.sum() - max_load_by_group.min())*(1-annual_maintenance_rates.mean())
    weight_on_peak_penalty = estimated_surplus_capacity/estimated_peak_penalty/10.

    model = ConcreteModel()

    # INPUT PARAMS
    model.i = RangeSet(0, num_groups - 1)
    model.g = RangeSet(0, len(pmaxs_not_zero) - 1)
    model.annual_maintenace_hours = Param(model.g, initialize=dict(zip(model.g.keys(), annual_maintenace_hours[pmaxs_not_zero])))
    model.pmax = Param(model.g, initialize=dict(zip(model.g.keys(), pmaxs[pmaxs_not_zero])))
    model.marginal_costs = Param(model.g, initialize=dict(zip(model.g.keys(), marginal_costs[pmaxs_not_zero])))
    model.max_load_by_group = Param(model.i, initialize=dict(zip(model.i.keys(), max_load_by_group)))
    model.group_lengths = Param(model.i, initialize=dict(zip(model.i.keys(), group_lengths)))
    model.weight_on_peak_penalty = Param(default=weight_on_peak_penalty)

    # DECISIONS VARIABLES
    model.available_gen = Var(model.i, within=NonNegativeReals)
    model.scheduled_maintenance = Var(model.i, model.g, within=NonNegativeReals)
    model.surplus_capacity = Var(within=NonNegativeReals)
    model.peak_penalty = Var(within=NonNegativeReals)

    # CONSTRAINTS
    model.define_available_gen = Constraint(model.i, rule=define_available_gen)
    model.feasible_maintenance_constraint_0 = Constraint(model.i, model.g, rule=feasible_maintenance_constraint_0)
    model.feasible_maintenance_constraint_1 = Constraint(model.i, model.g, rule=feasible_maintenance_constraint_1)
    model.meet_maintenance_constraint = Constraint(model.g, rule=meet_maintenance_constraint)
    model.define_surplus_capacity = Constraint(model.i, rule=define_surplus_capacity)
    model.define_penalty_to_preference_high_cost_gen_maint_during_peak = Constraint(rule=define_penalty_to_preference_high_cost_gen_maint_during_peak)

    # OBJECTIVE
    model.objective = Objective(rule=surplus_capacity, sense=minimize)

    # SOLVE AND EXPORT RESULTS
    solver = SolverFactory(cfg.solver_name or "cbc") # use cbc by default for testing, when you import config in a test, solver_name is None
    results = solver.solve(model, tee=print_opt)
    model.solutions.load_from(results)

    scheduled_maintenance = np.empty((num_groups, len(pmaxs)))
    scheduled_maintenance[:, pmaxs_zero] = annual_maintenance_rates[pmaxs_zero]
    scheduled_maintenance[:, pmaxs_not_zero] = np.array([[model.scheduled_maintenance[i, g].value for i in model.i.keys()] for g in model.g.keys()]).T
    return scheduled_maintenance


def schedule_generator_maintenance_loop(load, pmaxs, annual_maintenance_rates, dispatch_periods, scheduling_order):
    # if nothing else, better to schedule the large generators first
    scheduling_order = np.argsort(-pmaxs) if scheduling_order is None else scheduling_order

    # annual maintenance rates must be between zero and one
    annual_maintenance_rates = np.clip(annual_maintenance_rates, 0, 1)

    # gives the index for the change between dispatch_periods
    group_cuts = list(np.where(np.diff(dispatch_periods) != 0)[0] + 1) if dispatch_periods is not None else None
    group_lengths = np.array([group_cuts[0]] + list(np.diff(group_cuts)) + [len(load) - group_cuts[-1]])
    num_groups = len(group_cuts) + 1

    # necessary to scale load in some cases for the optimization to work. Basically, load shouldn't be > gen
    load_scaled = scale_load_to_system(load, pmaxs)
    load_scaled = np.concatenate([[np.max(ls)]*gl for gl, ls in zip(group_lengths, np.array_split(load_scaled, np.array(group_cuts)))])

    pmaxs_clipped = copy.deepcopy(pmaxs)
    pmaxs_clipped = np.clip(pmaxs_clipped, 1e-1, None)
    maintenance_energy = annual_maintenance_rates*pmaxs_clipped*len(load)
    scheduled_maintenance = np.zeros((num_groups, len(pmaxs)))

    # loop through and schedule maintenance for each generator one at a time. Update the net load after each one.
    for i in scheduling_order:
        energy_allocation = dispatch_budget.dispatch_to_energy_budget(load_scaled, -maintenance_energy[i], pmins=0, pmaxs=pmaxs_clipped[i])
        scheduled_maintenance[:, i] = np.clip(np.array([np.mean(ls) for ls in np.array_split(energy_allocation, np.array(group_cuts))])/pmaxs_clipped[i], 0, 1)
        load_scaled += np.concatenate([[sm * pmaxs[i]]*gl for gl, sm in zip(group_lengths, scheduled_maintenance[:, i])])

    if not all(np.isclose(annual_maintenance_rates, (scheduled_maintenance.T * group_lengths).sum(axis=1)/len(load))):
        logging.warning("scheduled maintance rates don't all match the annual maintenance rates")
    return scheduled_maintenance