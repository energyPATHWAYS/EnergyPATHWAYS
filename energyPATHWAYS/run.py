# -*- coding: utf-8 -*-
"""
Created on Thu Jul 07 19:20:05 2016

@author: ryandrewjones
"""

import sys
import signal
import click
import os
import cPickle as pickle
import energyPATHWAYS.config as cfg
import energyPATHWAYS.util as util
from energyPATHWAYS.pathways_model import PathwaysModel
import energyPATHWAYS.shape as shape
from energyPATHWAYS.outputs import Output
from energyPATHWAYS.dispatch_classes import Dispatch
import time
import datetime
import logging
import cProfile
import traceback
import pandas as pd

model = None
run_start_time = time.time()

def update_api_run_status(status_id):
    logging.debug("Updating scenario run status in database.")
    try:
        global model
        if model and model.api_run:
            util.update_status(model.scenario_id, status_id)
    # This is one of the few times I think a broad except clause is justified; if we've failed to update the run
    # status in the database at this point we don't really care why, and we don't want it to prevent any other
    # cleanup code from running. We'll just log it for future troubleshooting.
    except Exception:
        logging.exception("Exception caught attempting to write abnormal termination status %i to database."
                          % (status_id,))
    logging.debug("Finished updating scenario run status in database.")

def myexcepthook(exctype, value, tb):
    logging.error("Exception caught during model run.", exc_info=(exctype, value, tb))
    # It is possible that we arrived here due to a database exception, and if so the database will be in a state
    # where it is not accepting commands. To be safe, we do a rollback before attempting to write the run status.
    cfg.con.rollback()
    update_api_run_status(4)
    sys.__excepthook__(exctype, value, tb)
sys.excepthook = myexcepthook

def signal_handler(signal, frame):
    logging.error('Execution interrupted by signal ' + str(signal))
    # As documented here,
    # http://stackoverflow.com/questions/39215527/psycopg2-connection-unusable-after-selects-interrupted-by-os-signal
    # The normal database connection may be in an unusable state here if the signal arrived while the connection
    # was in the middle of performing some work. Therefore, we re-initialize the connection so that we can use it to
    # write the cancelation status to the db.
    cfg.init_db()
    update_api_run_status(5)
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

@click.command()
@click.option('-p', '--path', type=click.Path(exists=True), help='Working directory for energyPATHWAYS run.')
@click.option('-c', '--config', default='config.INI', help='File name for the energyPATHWAYS configuration file.')
@click.option('-u', '--pint', default='unit_defs.txt', help='File name for custom unit definitions for the library pint.')
@click.option('-s', '--scenario', type=str, help='Scenario ids [example: 1,3,5]')
@click.option('-ld', '--load_demand/--no_load_demand', default=False, help='Load a cached model with the demand side complete.')
@click.option('--solve_demand/--no_solve_demand', default=True, help='Solve the demand side of the model.')
@click.option('-ls', '--load_supply/--no_load_supply', default=False, help='Load a cached model with the demand and supply side complete.')
@click.option('--solve_supply/--no_solve_supply', default=True, help='Solve the supply side of the model.')
@click.option('--pickle_shapes/--no_pickle_shapes', default=True, help='Cache shapes after processing.')
@click.option('--save_models/--no_save_models', default=True, help='Cashe models after running.')
@click.option('--log_name', help='File name for the log file.')
@click.option('-a', '--api_run/--no_api_run', default=False)
@click.option('-d', '--debug/--no_debug', default=False, help='On error the model will exit into an ipython debugger.')
@click.option('--clear_results/--no_clear_results', default=False, help='Should results be cleared or appended when starting a new model run')
def click_run(path, config, pint, scenario, load_demand, solve_demand, load_supply, solve_supply, pickle_shapes, save_models, log_name, api_run, debug, clear_results):
    if debug:
        import ipdb
        with ipdb.launch_ipdb_on_exception():
            run(path, config, pint, scenario, load_demand, solve_demand, load_supply, solve_supply, pickle_shapes, save_models, log_name, api_run, clear_results)
    else:
        run(path, config, pint, scenario, load_demand, solve_demand, load_supply, solve_supply, pickle_shapes, save_models, log_name, api_run, clear_results)

def run(path, config, pint, scenario, load_demand=False, solve_demand=True, load_supply=False,
        solve_supply=True, pickle_shapes=True, save_models=True, log_name=None, api_run=False, clear_results=False):
    global model
    cfg.initialize_config(path, config, pint, log_name)
    cfg.geo.log_geo()
    shape.init_shapes()
    
    scenario_ids = parse_scenario_ids(scenario)
    logging.info('Scenario_ids run list = {}'.format(scenario_ids))
    for scenario_id in scenario_ids:
        scenario_start_time = time.time()
        logging.info('Starting scenario_id {}'.format(scenario_id))
        if api_run:
            util.update_status(scenario_id, 2)
        
        model = load_model(load_demand, load_supply, scenario_id, api_run)
        model.run(scenario_id,
                  solve_demand=solve_demand,
                  solve_supply=solve_supply,
                  load_demand = load_demand,
                  load_supply = load_supply,
                  save_models=save_models,
                  append_results=False if (scenario_id==scenario_ids[0] and clear_results) else True)
    
        if api_run:
            util.update_status(scenario_id, 3)
        logging.info('EnergyPATHWAYS run for scenario_id {} successful!'.format(scenario_id))
        logging.info('Scenario calculation time {} seconds'.format(time.time() - scenario_start_time))
    logging.info('Total calculation time {} seconds'.format(time.time() - run_start_time))
    logging.shutdown()
    logging.getLogger(None).handlers = [] # necessary to totally flush the logger

def parse_scenario_ids(scenario):
    if scenario is None or len(str(scenario))==0:
        return []
    if (type(scenario) is not tuple) and (type(scenario) is not list):
        scenario = str(scenario).split(',')
    return [int(str(s).rstrip().lstrip()) for s in scenario]

def load_model(load_demand, load_supply, scenario_id, api_run):
    # Note that the api_run parameter is effectively ignored if you are loading a previously pickled model
    # (with load_supply or load_demand); the model's api_run property will be set to whatever it was when the model
    # was pickled.
    if load_supply:
        with open(os.path.join(cfg.workingdir, str(scenario_id)+'_full_model_run.p'), 'rb') as infile:
            model = pickle.load(infile)
        logging.info('Loaded complete EnergyPATHWAYS model from pickle')
    elif load_demand:
        with open(os.path.join(cfg.workingdir, str(scenario_id)+'_model.p'), 'rb') as infile:
            model = pickle.load(infile)
        logging.info('Loaded demand-side EnergyPATHWAYS model from pickle')
    else:
        model = PathwaysModel(scenario_id, api_run)
    return model


if __name__ == "__main__":
    workingdir = r'C:\github\energyPATHWAYS\washington_model_example'
    os.chdir(workingdir)
    config = 'config.INI'
    pint = 'unit_defs.txt'
    scenario = [15]
    
    run(workingdir, config, pint, scenario,
    load_demand   = True,
    solve_demand  = False,
    load_supply   = False,
    solve_supply  = False,
    pickle_shapes = True,
    save_models   = True,
    api_run       = False,
    clear_results = True)

##    test = model.demand.aggregate_electricity_shapes(2020)
#    model.demand.create_electricity_reconciliation()
#    self = model.demand.sectors[3].subsectors[72]
##    active_shape = self.shape
##    shape_df = util.DfOper.mult((active_shape.values, self.electricity_reconciliation))
##    percent_flexible = self.flexible_load_measure.values.xs(2020, level='year')
##    percent_flexible[:] = 1
##    test = shape.Shape.produce_flexible_load(shape_df, percent_flexible)
#    test = self.aggregate_electricity_shapes(2050)
#    test.xs([36, 1], level=['us and new york', 'dispatch_feeder']).unstack('timeshift_type').cumsum().plot()

#    dispatch = Dispatch.load_from_pickle()
#    self = dispatch
#    self.set_opt_distribution_net_loads(self.distribution_load_input, self.distribution_gen_input)
#     instance = dispatch.solve_optimization_period(1, return_model_instance=True)
#    results = dispatch.solve_optimization_period(5, return_model_instance=False)
#    flex = pd.DataFrame(results['Flexible_Load'], columns=[dispatch.dispatch_geography, 'hour', 'dispatch_feeder', 'value'])
#    flex = flex.set_index([dispatch.dispatch_geography, 'dispatch_feeder', 'hour']).sort_index()
#    flex.xs([36, 1], level=[self.dispatch_geography, 'dispatch_feeder']).cumsum().plot()
##
##    dispatch.distribution_load_input.xs([36, 1], level=[dispatch.dispatch_geography, 'dispatch_feeder']).unstack('timeshift_type').cumsum().plot()
#    dispatch.solve_and_plot()

#
#    cum = util.remove_df_levels(cum_distribution_load.xs([36, 1], level=['us and new york', 'dispatch_feeder']), 'period').unstack('timeshift_type')
#    cum

    # note that when running the profiler, it is recommended to not run the model for more than 10 years due to memory use
    # cProfile.run('run(path, config, pint, scenario, load_demand=False, solve_demand=True, load_supply=False, solve_supply=True, pickle_shapes=True, save_models=True, api_run=False)', filename='full_run.profile')
    # Output.writeobj(model)


#self = model.demand.drivers[1]

#self = cfg.geo
#current_geography = 'census division'
#converted_geography = 'us'
#normalize_as='total'
#,1
#subset_geographies = set(cfg.geo.gau_to_geography[id] for id in cfg.primary_subset_id)
#current_geography = util.ensure_iterable_and_not_string(current_geography)
#converted_geography = util.ensure_iterable_and_not_string(converted_geography)
#union_geo = list(set(current_geography) | set(converted_geography) | subset_geographies)
#level_to_remove = list(subset_geographies - set(current_geography) - set(converted_geography))
#map_key = cfg.cfgfile.get('case', 'default_geography_map_key')
#
#self.map_df(current_geography, converted_geography, normalize_as='total')
#self.map_df(current_geography, converted_geography, normalize_as='intensity')


#shapes = shape.Shapes()
#shapes.create_empty_shapes()
#shapes.initiate_active_shapes()

#self = shapes.data[8]
#self.process_shape(shapes.active_dates_index, shapes.time_slice_elements)

#self = shapes.data[1]
#self.process_shape(shapes.active_dates_index, shapes.time_slice_elements)
#
#hydro = shapes.data[7]
#hydro.process_shape(shapes.active_dates_index, shapes.time_slice_elements)



from collections import defaultdict
from energyPATHWAYS.shared_classes import StockItem
from energyPATHWAYS.rollover import Rollover
import numpy as np
import matplotlib
from matplotlib import cm

start_year = 2000
end_year = 2050
years = range(start_year, end_year+1)
num_years = end_year-start_year+1 # number of years to run in the stock rollover
num_vintages = end_year-start_year+1 # it might be that this is unneeeded and should just be set to num_years

num_techs = 1 # number of technologies in a subsector (can be 1 and often is)
tech_ids = [0]
steps_per_year = 1

# start a record for a single technology
tech = StockItem()
tech.mean_lifetime = 50 # years
tech.lifetime_variance = 20 # years
# Other ways to define lifetime are min_lifetime and max_lifetime
tech.stock_decay_function = 'weibull' # other options here ('linear' or 'exponential')
tech.spy = steps_per_year
tech.years = years
        
tech.set_survival_parameters()
tech.set_survival_vintaged()
tech.set_decay_vintaged()
tech.set_survival_initial_stock()
tech.set_decay_initial_stock()

# wrap the technologies together
technologies = dict(zip(tech_ids, [tech]))

# at this point we have all the survival functions, but we don't yet have the markov matrix

functions = defaultdict(list)
for fun in ['survival_vintaged', 'survival_initial_stock', 'decay_vintaged', 'decay_initial_stock']:
    for tech_id in tech_ids:
        technology = technologies[tech_id]
        functions[fun].append(getattr(technology, fun))
    functions[fun] = pd.DataFrame(np.array(functions[fun]).T, columns=tech_ids)


vintaged_markov = util.create_markov_vector(functions['decay_vintaged'].values, functions['survival_vintaged'].values)
vintaged_markov_matrix = util.create_markov_matrix(vintaged_markov, num_techs, num_years, steps_per_year)

initial_markov = util.create_markov_vector(functions['decay_initial_stock'].values, functions['survival_initial_stock'].values)
initial_markov_matrix = util.create_markov_matrix(initial_markov, num_techs, num_years, steps_per_year)

ext_stock = pd.DataFrame.from_csv('households.csv')
initial_stock = ext_stock.iloc[0]
stock_changes = ext_stock.diff().fillna(0).values.flatten()

# now we have the markov matrix and we are ready to do stock rollover
rollover = Rollover(vintaged_markov_matrix, initial_markov_matrix, num_years, num_vintages, num_techs, initial_stock=initial_stock, stock_changes=stock_changes)
rollover.run()
outputs = rollover.return_formatted_outputs()
stock = outputs[0]/1E6

df = pd.DataFrame(stock, index=[1999]+years, columns=years)
df.transpose().plot(stacked=True, kind='area', colormap=matplotlib.cm.Set2, legend=False)