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

def process_shapes(shape):
    cfg.initialize_config(shape.workingdir, shape.cfgfile_name, shape.log_name)
    shape.process_shape()
    cfg.cur.close()
    return shape

def node_calculate(node):
    cfg.initialize_config(node.workingdir, node.cfgfile_name, node.log_name)
    if node.id == 6 and cfg.rio_supply_run:
        node.calculate(calculate_residual=False)
    else:
        node.calculate()
    cfg.cur.close()
    return node

def subsector_calculate(subsector):
    if not subsector.calculated:
        cfg.initialize_config(subsector.workingdir, subsector.cfgfile_name, subsector.log_name)
        subsector.calculate()
        cfg.cur.close()
    return subsector

def subsector_populate(subsector):
    cfg.initialize_config(subsector.workingdir, subsector.cfgfile_name, subsector.log_name)
    subsector.add_energy_system_data()
    cfg.cur.close()
    return subsector

def shapes_populate(shape):
    cfg.initialize_config(shape.workingdir, shape.cfgfile_name, shape.log_name)
    logging.info('    shape: ' + shape.name)
    shape.read_timeseries_data()
    cfg.cur.close()
    return shape

def individual_calculate(evolve, individual):
    evolve.calculate(individual)
    

def aggregate_subsector_shapes(params):
    subsector = params[0]
    year = params[1]    
    cfg.initialize_config(subsector.workingdir, subsector.cfgfile_name, subsector.log_name)
    aggregate_electricity_shape = subsector.aggregate_electricity_shapes(year)
    cfg.cur.close()    
    return aggregate_electricity_shape

def aggregate_sector_shapes(params):
    sector = params[0]
    year = params[1]    
    cfg.initialize_config(sector.workingdir, sector.cfgfile_name, sector.log_name)
    aggregate_electricity_shape = sector.aggregate_inflexible_electricity_shape(year)
    cfg.cur.close()
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
    cfg.cur.close()

    pool = Pool(processes=cfg.available_cpus)
    result = pool.map(method, data)
    pool.close()
    pool.join()

    cfg.init_db()
    return result
