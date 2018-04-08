__author__ = 'Ben Haley & Ryan Jones'

import os
import errno
import ConfigParser
import pint
import geomapper
import warnings
import pandas as pd
from collections import defaultdict
import psycopg2
import util
import datetime
import logging
import sys
from pyomo.opt import SolverFactory
import pdb

# Don't print warnings
warnings.simplefilter("ignore")

# core inputs
workingdir = None
cfgfile = None
cfgfile_name = None
weibul_coeff_of_var = None

# db connection and cursor
con = None
cur = None

# pickle names
full_model_append_name = '_full_model.p'
demand_model_append_name = '_demand_model.p'
model_error_append_name = '_model_error.p'

# common data inputs
index_levels = None
dnmtr_col_names = ['driver_denominator_1_id', 'driver_denominator_2_id']
drivr_col_names = ['driver_1_id', 'driver_2_id']
tech_classes = ['capital_cost_new', 'capital_cost_replacement', 'installation_cost_new', 'installation_cost_replacement', 'fixed_om', 'variable_om', 'efficiency']
#storage techs have additional attributes specifying costs for energy (i.e. kWh of energy storage) and discharge capacity (i.e. kW)
storage_tech_classes = ['installation_cost_new','installation_cost_replacement', 'fixed_om', 'variable_om', 'efficiency', 'capital_cost_new_capacity', 'capital_cost_replacement_capacity',
                        'capital_cost_new_energy', 'capital_cost_replacement_energy']

# Initiate pint for unit conversions
ureg = None
calculation_energy_unit = None

# Geography
geo = None
demand_primary_geography = None
demand_primary_geography_id = None
supply_primary_geography = None
supply_primary_geography_id = None
combined_outputs_geography_side = None
combined_outputs_geography = None
primary_subset_id = None
breakout_geography_id = None
demand_geographies = None
supply_geographies = None
include_foreign_gaus = None
dispatch_geography = None
dispatch_geography_id = None
dispatch_subset_id = None
dispatch_breakout_geography_id = None
dispatch_geographies = None
disagg_geography = None
disagg_geography_id = None
combined_geographies = None

# run years
years = None
supply_years = None

# shapes
shape_start_date = None
shape_years = None
date_lookup = None
time_slice_col = None
electricity_energy_type_id = None
electricity_energy_type_shape_id = None
opt_period_length = None
solver_name = None
transmission_constraint_id = None
filter_dispatch_less_than_x = None

# outputs
output_levels = None
currency_name = None
output_energy_unit = None
output_currency = None
output_demand_levels = None
output_supply_levels = None
output_combined_levels = None
outputs_id_map = defaultdict(dict)
dispatch_write_years = None
timestamp = None

# parallel processing
available_cpus = None

#logging
log_name = None

unit_defs = ['US_gge = 120,500 * BTU',
            'US_gde = 138,490 * BTU',
            'US_gee = 80337.35 * BTU',
            'lng_gallon = 82,644 * BTU',
            'mmBtu = 1,000,000 * BTU',
            'mmbtu = 1,000,000 * BTU',
            'lumen = candela * steradian',
            'lumen_hour = candela * steradian * hour',
            'lumen_year = candela * steradian * year',
            'quad = 1,000,000,000,000,000 * BTU',
            'cubic_foot = 28316.8 * cubic_centimeter',
            'cubic_meter = 1000000 * cubic_centimeter',
            'cubic_foot_hour = cubic_foot * hour',
            'cubic_foot_year = cubic_foot * year',
            'cubic_feet_year = cubic_foot * year',
            'TBtu  = 1,000,000,000,000 * BTU',
            'ton_mile = ton * mile',
            'h2_kilogram = 39.5 * kilowatt_hour',
            'jet_fuel_gallon = 125800 * Btu',
            'pipeline_gas_cubic_meter = 9000 * kilocalorie',
            'boe = 5,800,000 * Btu',
            'bee = 3,559,000 * Btu']

def initialize_config(_path, _cfgfile_name, _log_name):
    global weibul_coeff_of_var, available_cpus, workingdir, cfgfile_name, log_name, log_initialized, index_levels, solver_name, timestamp
    workingdir = os.getcwd() if _path is None else _path
    cfgfile_name = _cfgfile_name 
    init_cfgfile(os.path.join(workingdir, cfgfile_name))
    
    log_name = '{} energyPATHWAYS log.log'.format(str(datetime.datetime.now())[:-4].replace(':', '.')) if _log_name is None else _log_name
    setuplogging()
    
    init_db()
    init_units()
    init_geo()
    init_shapes()
    init_date_lookup()
    init_output_parameters()
    # used when reading in raw_values from data tables
    index_levels = util.sql_read_table('IndexLevels', column_names=['index_level', 'data_column_name'])
    solver_name = find_solver()

    available_cpus = int(cfgfile.get('case','num_cores'))
    weibul_coeff_of_var = util.create_weibul_coefficient_of_variation()
    timestamp = str(datetime.datetime.now().replace(second=0,microsecond=0))

def setuplogging():
    if not os.path.exists(os.path.join(workingdir, 'logs')):
        os.makedirs(os.path.join(workingdir, 'logs'))
    log_path = os.path.join(workingdir, 'logs', log_name)
    log_level = cfgfile.get('log', 'log_level').upper()
    logging.basicConfig(filename=log_path, level=log_level)
    logger = logging.getLogger()
    if cfgfile.get('log', 'stdout').lower() == 'true' and not any(type(h) is logging.StreamHandler for h in logger.handlers):
        soh = logging.StreamHandler(sys.stdout)
        soh.setLevel(log_level)
        logger.addHandler(soh)

def init_cfgfile(cfgfile_path):
    global cfgfile, years, supply_years

    if not os.path.isfile(cfgfile_path):
        raise IOError(errno.ENOENT, "Unable to load configuration file. "
                                    "Please make sure your configuration file is located at {}, "
                                    "or use the -p and -c command line options to specify a different location. "
                                    "Type `energyPATHWAYS --help` for help on these options.".format(str(cfgfile_path)))

    cfgfile = ConfigParser.ConfigParser()
    cfgfile.read(cfgfile_path)

    years = range(int(cfgfile.get('case', 'demand_start_year')),
                   int(cfgfile.get('case', 'end_year')) + 1,
                   int(cfgfile.get('case', 'year_step')))
                   
    supply_years = range(int(cfgfile.get('case', 'current_year')),
                          int(cfgfile.get('case', 'end_year')) + 1,
                          int(cfgfile.get('case', 'year_step')))
    
    cfgfile.set('case', 'years', years)
    cfgfile.set('case', 'supply_years', supply_years)

def init_db():
    global con, cur, dnmtr_col_names, drivr_col_names
    pg_host = cfgfile.get('database', 'pg_host')
    if not pg_host:
        pg_host = 'localhost'
    pg_user = cfgfile.get('database', 'pg_user')
    pg_password = cfgfile.get('database', 'pg_password')
    pg_database = cfgfile.get('database', 'pg_database')
    conn_str = "host='%s' dbname='%s' user='%s'" % (pg_host, pg_database, pg_user)
    if pg_password:
        conn_str += " password='%s'" % pg_password
    
    logging.debug("Connecting to postgres database {}".format(pg_database))
    # Open pathways database
    con = psycopg2.connect(conn_str)
    cur = con.cursor()
    logging.debug("Connection successful...")
    

def init_units():
    # Initiate pint for unit conversions
    global ureg, output_energy_unit, calculation_energy_unit
    ureg = pint.UnitRegistry()
    
    # output_energy_unit = cfgfile.get('case', 'output_energy_unit')
    calculation_energy_unit = cfgfile.get('case', 'calculation_energy_unit')
    
    for unit_def in unit_defs:
        unit_name = unit_def.split(' = ')[0]
        if hasattr(ureg, unit_name):
            logging.debug('pint already has unit {}, unit is not being redefined'.format(unit_name))
            continue
        ureg.define(unit_def)
        
def init_geo():
    #Geography conversions
    global geo, demand_geographies, supply_geographies, dispatch_geography, dispatch_geographies, dispatch_geography_id, disagg_geography, disagg_geography_id
    global primary_subset_id, breakout_geography_id, dispatch_breakout_geography_id, disagg_breakout_geography_id, include_foreign_gaus
    global demand_primary_geography, demand_primary_geography_id, supply_primary_geography, supply_primary_geography_id, combined_outputs_geography_side, combined_outputs_geography
    global combined_geographies
    
    # from config file
    demand_primary_geography_id = int(cfgfile.get('case', 'demand_primary_geography_id'))
    supply_primary_geography_id = int(cfgfile.get('case', 'supply_primary_geography_id'))
    combined_outputs_geography_side = cfgfile.get('case', 'combined_outputs_geography_side')
    primary_subset_id = [int(g) for g in cfgfile.get('case', 'primary_subset_id').split(',') if len(g)]
    breakout_geography_id = [int(g) for g in cfgfile.get('case', 'breakout_geography_id').split(',') if len(g)]
    dispatch_geography_id = int(cfgfile.get('case', 'dispatch_geography_id'))
    dispatch_breakout_geography_id = [int(g) for g in cfgfile.get('case', 'dispatch_breakout_geography_id').split(',') if len(g)]
    disagg_geography_id = int(cfgfile.get('case', 'disagg_geography_id'))
    disagg_breakout_geography_id = [int(g) for g in cfgfile.get('case', 'disagg_breakout_geography_id').split(',') if len(g)]
    include_foreign_gaus = True if cfgfile.get('case', 'include_foreign_gaus').lower()=='true' else False
    
    # geography conversion object
    geo = geomapper.GeoMapper()
    
    # derived from inputs and geomapper object
    dispatch_geography = geo.get_dispatch_geography_name()
    demand_primary_geography = geo.get_demand_primary_geography_name()
    supply_primary_geography = geo.get_supply_primary_geography_name()
    assert combined_outputs_geography_side.lower() == 'demand' or combined_outputs_geography_side.lower() == 'supply'
    combined_outputs_geography = demand_primary_geography if combined_outputs_geography_side.lower() == 'demand' else supply_primary_geography
    disagg_geography = geo.get_disagg_geography_name()
    dispatch_geographies = geo.geographies[dispatch_geography]
    demand_geographies = geo.geographies[demand_primary_geography]
    supply_geographies = geo.geographies[supply_primary_geography]
    combined_geographies = geo.geographies[combined_outputs_geography]

def init_shapes():
    global shape_start_date, shape_years

    raw_shape_start_date = cfgfile.get('opt', 'shape_start_date')
    if raw_shape_start_date:
        shape_start_date = datetime.datetime.strptime(raw_shape_start_date, '%Y-%m-%d')

    raw_shape_years = cfgfile.get('opt', 'shape_years')
    if raw_shape_years:
        shape_years = int(raw_shape_years)
        if shape_years < 1:
            raise ValueError('shape_years, if provided, must be a positive integer.')


def init_date_lookup():
    global date_lookup, time_slice_col, electricity_energy_type_id, electricity_energy_type_shape_id, opt_period_length, transmission_constraint_id, filter_dispatch_less_than_x
    class DateTimeLookup:
        def __init__(self):
            self.dates = {}
        
        def lookup(self, series):
            """
            This is a faster approach to datetime parsing.
            For large data, the same dates are often repeated. Rather than
            re-parse these, we store all unique dates, parse them, and
            use a lookup to convert all dates.
            """
            self.dates.update({date: pd.to_datetime(date) for date in series.unique() if not self.dates.has_key(date)})
            return series.apply(lambda v: self.dates[v])
            ## Shapes
    
    date_lookup = DateTimeLookup()
    time_slice_col = ['year', 'month', 'week', 'hour', 'day_type']
    electricity_energy_type_id, electricity_energy_type_shape_id = util.sql_read_table('FinalEnergy', column_names=['id', 'shape_id'], name='electricity')
    opt_period_length = int(cfgfile.get('opt', 'period_length'))
    transmission_constraint_id = cfgfile.get('opt','transmission_constraint_id')
    transmission_constraint_id = int(transmission_constraint_id) if transmission_constraint_id != "" else None
    filter_dispatch_less_than_x = cfgfile.get('output_detail','filter_dispatch_less_than_x')
    filter_dispatch_less_than_x = float(filter_dispatch_less_than_x) if filter_dispatch_less_than_x != "" else None

def init_removed_levels():
    global removed_demand_levels
    removed_demand_levels  = [str(g) for g in cfgfile.get('removed_levels', 'levels').split(',') if len(g)]


def init_output_levels():
    global output_demand_levels, output_supply_levels, output_combined_levels
    output_demand_levels = ['year', 'vintage', 'demand_technology', demand_primary_geography, 'sector', 'subsector', 'final_energy','other_index_1','other_index_2','cost_type','new/replacement']
    output_supply_levels = ['year', 'vintage', 'supply_technology', supply_primary_geography,  'demand_sector', 'supply_node', 'ghg', 'resource_bin','cost_type']
    output_combined_levels = list(set(output_supply_levels + output_demand_levels + [combined_outputs_geography + "_supply"]))
    output_combined_levels = list(set(output_combined_levels) - set([demand_primary_geography, supply_primary_geography])) + [combined_outputs_geography]

    for x in [x[0] for x in cfgfile.items('demand_output_detail')]:
        if x in output_demand_levels and cfgfile.get('demand_output_detail', x).lower() != 'true':
            output_demand_levels.remove(x)
    for x in [x[0] for x in cfgfile.items('supply_output_detail')]:
        if x in output_supply_levels and cfgfile.get('supply_output_detail',x).lower() != 'true':
            output_supply_levels.remove(x)
    for x in [x[0] for x in cfgfile.items('combined_output_detail')]:
        if cfgfile.get('combined_output_detail',x).lower() != 'true':
            if x == 'supply_geography':
                x = combined_outputs_geography + "_supply"
            if x in output_combined_levels:
                output_combined_levels.remove(x)

        

def init_outputs_id_map():
    global outputs_id_map
    demand_primary_geography = geo.get_demand_primary_geography_name()
    supply_primary_geography = geo.get_supply_primary_geography_name()
    dispatch_geography_name = geo.get_dispatch_geography_name()
    outputs_id_map[demand_primary_geography] = util.upper_dict(geo.geography_names.items())
    outputs_id_map[supply_primary_geography] = util.upper_dict(geo.geography_names.items())
    outputs_id_map[supply_primary_geography + "_supply"] = util.upper_dict(geo.geography_names.items())
    outputs_id_map[supply_primary_geography + "_input"] = util.upper_dict(geo.geography_names.items())
    outputs_id_map[supply_primary_geography + "_output"] = util.upper_dict(geo.geography_names.items())
    outputs_id_map[demand_primary_geography + "_input"] = util.upper_dict(geo.geography_names.items())
    outputs_id_map[demand_primary_geography + "_output"] = util.upper_dict(geo.geography_names.items())
    outputs_id_map[dispatch_geography_name] = util.upper_dict(geo.geography_names.items())
    outputs_id_map['demand_technology'] = util.upper_dict(util.sql_read_table('DemandTechs', ['id', 'name']))
    outputs_id_map['supply_technology'] = util.upper_dict(util.sql_read_table('SupplyTechs', ['id', 'name']))
    outputs_id_map['final_energy'] = util.upper_dict(util.sql_read_table('FinalEnergy', ['id', 'name']))
    outputs_id_map['supply_node'] = util.upper_dict(util.sql_read_table('SupplyNodes', ['id', 'name']))     
    outputs_id_map['blend_node'] = util.upper_dict(util.sql_read_table('SupplyNodes', ['id', 'name']))     
    outputs_id_map['input_node'] = util.upper_dict(util.sql_read_table('SupplyNodes', ['id', 'name']))         
    outputs_id_map['supply_node_output'] = outputs_id_map['supply_node']
    outputs_id_map['supply_node_input'] = outputs_id_map['supply_node']
    outputs_id_map['supply_node_export'] = util.upper_dict(util.sql_read_table('SupplyNodes', ['id', 'name'])," EXPORT")
    outputs_id_map['subsector'] = util.upper_dict(util.sql_read_table('DemandSubsectors', ['id', 'name']))           
    outputs_id_map['demand_sector'] = util.upper_dict(util.sql_read_table('DemandSectors', ['id', 'name']))
    outputs_id_map['sector'] = outputs_id_map['demand_sector']
    outputs_id_map['ghg'] = util.upper_dict(util.sql_read_table('GreenhouseGases', ['id', 'name']))
    outputs_id_map['driver'] = util.upper_dict(util.sql_read_table('DemandDrivers', ['id', 'name']))
    outputs_id_map['dispatch_feeder'] = util.upper_dict(util.sql_read_table('DispatchFeeders', ['id', 'name']))
    outputs_id_map['dispatch_feeder'][0] = 'BULK'
    outputs_id_map['other_index_1'] = util.upper_dict(util.sql_read_table('OtherIndexesData', ['id', 'name']))
    outputs_id_map['other_index_2'] = util.upper_dict(util.sql_read_table('OtherIndexesData', ['id', 'name']))
    outputs_id_map['timeshift_type'] = util.upper_dict(util.sql_read_table('FlexibleLoadShiftTypes', ['id', 'name']))
    for id, name in util.sql_read_table('OtherIndexes', ('id', 'name'), return_iterable=True):
        if name in ('demand_technology', 'final_energy'):
            continue
        outputs_id_map[name] = util.upper_dict(util.sql_read_table('OtherIndexesData', ['id', 'name'], other_index_id=id, return_unique=True))

def init_output_parameters():
    global currency_name, output_currency, output_tco, output_payback, evolved_run, evolved_blend_nodes, evolved_years
    currency_name = cfgfile.get('case', 'currency_name')
    output_currency = cfgfile.get('case', 'currency_year_id') + ' ' + currency_name
    output_tco = cfgfile.get('output_detail', 'output_tco').lower()
    output_payback = cfgfile.get('output_detail', 'output_payback').lower()
    evolved_run = cfgfile.get('evolved','evolved_run').lower()
    evolved_years = [int(x) for x in util.ensure_iterable_and_not_string(cfgfile.get('evolved','evolved_years'))]
    evolved_blend_nodes =  [int(g) for g in cfgfile.get('evolved','evolved_blend_nodes').split(',') if len(g)]
    init_removed_levels()
    init_output_levels()
    init_outputs_id_map()

def find_solver():
    requested_solvers = cfgfile.get('opt', 'dispatch_solver').replace(' ', '').split(',')
    solver_name = None
    # inspired by the solver detection code at https://software.sandia.gov/trac/pyomo/browser/pyomo/trunk/pyomo/scripting/driver_help.py#L336
    # suppress logging of warnings for solvers that are not found
    logger = logging.getLogger('pyomo.solvers')
    _level = logger.getEffectiveLevel()
    logger.setLevel(logging.ERROR)
    for requested_solver in requested_solvers:
        logging.debug("Looking for %s solver" % requested_solver)
        if SolverFactory(requested_solver).available(False):
            solver_name = requested_solver
            logging.debug("Using %s solver" % requested_solver)
            break
    # restore logging
    logger.setLevel(_level)

    assert solver_name is not None, "Dispatch could not find any of the solvers requested in your configuration (%s) please see README.md, check your configuration, and make sure you have at least one requested solver installed." % ', '.join(requested_solvers)
    return solver_name