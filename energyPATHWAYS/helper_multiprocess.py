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
import energyPATHWAYS.dispatch_classes as dispatch_classes
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
    try:
        cfg.initialize_config()
        node.calculate()
    except Exception as e:
        traceback.print_exc()
        raise e
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
    try:
        cfg.initialize_config()
        logging.info('    shape: ' + shape.name)
        shape.read_timeseries_data()
    except Exception as e:
        traceback.print_exc()
        raise e
    return shape

def individual_calculate(evolve, individual):
    evolve.calculate(individual)

def run_optimization(params, return_model_instance=False):
    try:
        model, solver_name = params
        instance = model.create_instance()
        solver = SolverFactory(solver_name)
        solution = solver.solve(instance)
        instance.solutions.load_from(solution)
    except Exception as e:
        traceback.print_exc()
        raise e
    return instance if return_model_instance else dispatch_classes.all_results_to_list(instance)

# Applies method to data using parallel processes and returns the result, but closes the main process's database
# connection first, since otherwise the connection winds up in an unusable state on macOS.
def safe_pool(method, data):
    pool = Pool(processes=cfg.available_cpus)
    result = pool.map(method, data)
    pool.close()
    pool.join()
    return result
