# -*- coding: utf-8 -*-
"""
Created on Fri Jul 29 10:12:07 2016

@author: ryandrewjones
"""

import config as cfg
#import util
#import numpy as np
#from dispatch_classes import Dispatch

def node_calculate(node):
    cfg.initialize_config(node.workingdir, node.cfgfile_name, node.pint_definitions_file, node.log_name)
    node.calculate()
    cfg.cur.close()
    return node

def subsector_calculate(subsector):
    if not subsector.calculated:
        cfg.initialize_config(subsector.workingdir, subsector.cfgfile_name, subsector.pint_definitions_file, subsector.log_name)
        subsector.calculate()
        cfg.cur.close()
    return subsector

def subsector_populate(subsector):
    cfg.initialize_config(subsector.workingdir, subsector.cfgfile_name, subsector.pint_definitions_file, subsector.log_name)
    subsector.add_energy_system_data()
    cfg.cur.close()
    return subsector


def aggregate_electricity_shapes(params):
    subsector = params[0]
    year = params[1]
    active_shape = params[2]
    feeder_allocation = params[3]
    default_max_lead_hours = params[4]
    default_max_lag_hours = params[5]
    
    cfg.initialize_config(subsector.workingdir, subsector.cfgfile_name, subsector.pint_definitions_file, subsector.log_name)
    aggregate_electricity_shape = subsector.aggregate_electricity_shapes(year, active_shape, feeder_allocation, default_max_lead_hours, default_max_lag_hours)
    cfg.cur.close()
    
    return aggregate_electricity_shape

#def rollover_subset_run(key_value_pair):
#    elements = key_value_pair.keys()[0]
#    rollover = key_value_pair.values()[0]
#    rollover.run()
#    stock, stock_new, stock_replacement, retirements, retirements_natural, retirements_early, sales_record, sales_new, sales_replacement = rollover.return_formatted_outputs()
#    return stock, stock_new, stock_replacement, retirements, retirements_natural, retirements_early, sales_record, sales_new, sales_replacement, elements

