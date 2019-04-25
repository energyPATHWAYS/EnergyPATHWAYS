# -*- coding: utf-8 -*-
"""
Created on Fri Jul 29 10:12:07 2016

@author: ryandrewjones
"""

import config as cfg
import logging
from multiprocessing import Pool
from pyomo.opt import SolverFactory
#import util
#import numpy as np
import dispatch_classes
import traceback

def process_shapes(shape):
    try:
        cfg.initialize_config()
        shape.process_shape()
    except Exception as e:
        print 'Caught exception in shape {}'.format(shape.name)
        traceback.print_exc()
        raise e
    return shape


def node_calculate(node):
    cfg.initialize_config()
    if node.id == 6 and cfg.rio_supply_run:
        node.calculate(calculate_residual=False)
    else:
        node.calculate()
    return node

def subsector_calculate(subsector):
    try:
        if not subsector.calculated:
            cfg.initialize_config()
            subsector.calculate()
    except Exception as e:
        traceback.print_exc()
        raise e
    return subsector

def subsector_populate(subsector):
    cfg.initialize_config()
    try:
        subsector.add_energy_system_data()
    except Exception as e:
        traceback.print_exc()
        raise e
    return subsector

def shapes_populate(shape):
    cfg.initialize_config()
    logging.info('    shape: ' + shape.name)
    shape.read_timeseries_data()
    return shape

def individual_calculate(evolve, individual):
    evolve.calculate(individual)

def aggregate_subsector_shapes(params):
    subsector = params[0]
    year = params[1]    
    cfg.initialize_config()
    aggregate_electricity_shape = subsector.aggregate_electricity_shapes(year)  
    return aggregate_electricity_shape

def aggregate_sector_shapes(params):
    sector = params[0]
    year = params[1]    
    cfg.initialize_config()
    aggregate_electricity_shape = sector.aggregate_inflexible_electricity_shape(year)
    return aggregate_electricity_shape
    
def run_optimization(params, return_model_instance=False):
    model, solver_name = params
    instance = model.create_instance()
    solver = SolverFactory(solver_name)
    solution = solver.solve(instance)
    instance.solutions.load_from(solution)
    return instance if return_model_instance else dispatch_classes.all_results_to_list(instance)

# Applies method to data using parallel processes and returns the result, but closes the main process's database
# connection first, since otherwise the connection winds up in an unusable state on macOS.
def safe_pool(method, data):
    pool = Pool(processes=cfg.available_cpus)
    result = pool.map(method, data)
    pool.close()
    pool.join()
    return result
