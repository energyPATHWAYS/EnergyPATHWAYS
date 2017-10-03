
from pyomo.environ import *
import numpy as np
import util
import config as cfg
import pdb

def surplus_capacity(model):
    return model.surplus_capacity

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
        load *= sum_cap / (max_load * typical_reserve)
    return load

def schedule_generator_maintenance(load, pmaxs, annual_maintenance_rates, dispatch_periods=None, load_ptile=99.9, print_opt=False):
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

    load_cut = np.percentile(load, load_ptile)
    # checks to see if we have a low level that is in the top percentile, if we do, we don't schedule maintenance in that month
    not_okay_for_maint = util.flatten_list([[np.any(group)] * len(group) for group in np.array_split(load > load_cut, group_cuts)])

    pmaxs_zero = np.nonzero(pmaxs==0)[0]
    pmaxs_not_zero = np.nonzero(pmaxs)[0]
    model = ConcreteModel()

    # INPUT PARAMS
    model.i = RangeSet(0, num_groups - 1)
    model.g = RangeSet(0, len(pmaxs_not_zero) - 1)
    model.annual_maintenace_hours = Param(model.g, initialize=dict(zip(model.g.keys(), annual_maintenace_hours[pmaxs_not_zero])))
    model.pmax = Param(model.g, initialize=dict(zip(model.g.keys(), pmaxs[pmaxs_not_zero])))
    model.max_load_by_group = Param(model.i, initialize=dict(zip(model.i.keys(), max_load_by_group)))
    model.group_lengths = Param(model.i, initialize=dict(zip(model.i.keys(), group_lengths)))

    # DECISIONS VARIABLES
    model.available_gen = Var(model.i, within=NonNegativeReals)
    model.scheduled_maintenance = Var(model.i, model.g, within=NonNegativeReals)
    model.surplus_capacity = Var(within=NonNegativeReals)

    # CONSTRAINTS
    model.define_available_gen = Constraint(model.i, rule=define_available_gen)
    model.feasible_maintenance_constraint_0 = Constraint(model.i, model.g, rule=feasible_maintenance_constraint_0)
    model.feasible_maintenance_constraint_1 = Constraint(model.i, model.g, rule=feasible_maintenance_constraint_1)
    model.meet_maintenance_constraint = Constraint(model.g, rule=meet_maintenance_constraint)
    model.define_surplus_capacity = Constraint(model.i, rule=define_surplus_capacity)

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
