__author__ = 'Ben Haley & Ryan Jones'

import os
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
import pdb
from multiprocessing import cpu_count

# Don't print warnings
warnings.simplefilter("ignore")

# core inputs
workingdir = None
cfgfile = None
cfgfile_name = None
scenario_dict = None
weibul_coeff_of_var = None

# db connection and cursor
con = None
cur = None

# common data inputs
dnmtr_col_names = ['driver_denominator_1_id', 'driver_denominator_2_id']
drivr_col_names = ['driver_1_id', 'driver_2_id']
tech_classes = ['capital_cost_new', 'capital_cost_replacement', 'installation_cost_new', 'installation_cost_replacement', 'fixed_om', 'variable_om', 'efficiency']
#storage techs have additional attributes specifying costs for energy (i.e. kWh of energy storage) and discharge capacity (i.e. kW)
storage_tech_classes = ['installation_cost_new','installation_cost_replacement', 'fixed_om', 'variable_om', 'efficiency', 'capital_cost_new_capacity', 'capital_cost_replacement_capacity',
                        'capital_cost_new_energy', 'capital_cost_replacement_energy']

# Initiate pint for unit conversions
ureg = None
pint_definitions_file = None
calculation_energy_unit = None

# Geography
geo = None
primary_geography = None
primary_geography_id = None
primary_subset_id = None
breakout_geography_id = None
geographies = None
include_foreign_gaus = None
dispatch_geography = None
dispatch_geography_id = None
dispatch_subset_id = None
dispatch_breakout_geography_id = None
dispatch_geographies = None

# run years
years = None
supply_years = None

# electricity shapes
date_lookup = None
time_slice_col = None
electricity_energy_type_id = None
electricity_energy_type_shape_id = None

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

# parallel processing
available_cpus = None

#logging
log_name = None


def initialize_config(_path, _cfgfile_name, _pint_definitions_file, _log_name):
    global weibul_coeff_of_var, scenario_dict, available_cpus, workingdir, cfgfile_name, pint_definitions_file, log_name, log_initialized
    workingdir = os.getcwd() if _path is None else _path
    cfgfile_name = _cfgfile_name
    pint_definitions_file = _pint_definitions_file    
    init_cfgfile(os.path.join(workingdir, cfgfile_name))
    
    log_name = '{} energyPATHWAYS log.log'.format(str(datetime.datetime.now())[:-4].replace(':', '.')) if _log_name is None else _log_name
    setuplogging()
    
    init_db()
    init_units(os.path.join(workingdir, pint_definitions_file))
    init_geo()
    init_date_lookup()
    init_output_parameters()
    
    scenario_dict = dict(util.sql_read_table('Scenarios',['id', 'name'], return_iterable=True))
    available_cpus = min(cpu_count(), int(cfgfile.get('case','num_cores')))
    weibul_coeff_of_var = util.create_weibul_coefficient_of_variation()

def setuplogging():
    log_path = os.path.join(workingdir, log_name)
    log_level = cfgfile.get('log', 'log_level').upper()
    logging.basicConfig(filename=log_path, level=log_level)
    logger = logging.getLogger()
    if cfgfile.get('log', 'stdout').lower() == 'true' and not any(type(h) is logging.StreamHandler for h in logger.handlers):
        soh = logging.StreamHandler(sys.stdout)
        soh.setLevel(log_level)
        logger.addHandler(soh)

def init_cfgfile(cfgfile_path):
    global cfgfile, years, supply_years

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
    

def init_units(pint_definitions_path):
    # Initiate pint for unit conversions
    global ureg, output_energy_unit, calculation_energy_unit
    ureg = pint.UnitRegistry()
    
    output_energy_unit = cfgfile.get('case', 'output_energy_unit')
    calculation_energy_unit = cfgfile.get('case', 'calculation_energy_unit')
    
    if pint_definitions_path is not None:
        if not os.path.isfile(pint_definitions_path):
            raise OSError('pint definitions file not found: ' + str(pint_definitions_path))
        ureg.load_definitions(pint_definitions_path)
        
def init_geo():
    #Geography conversions
    global geo, primary_geography, primary_geography_id, geographies, dispatch_geography, dispatch_geographies, dispatch_geography_id
    global primary_subset_id, breakout_geography_id, dispatch_breakout_geography_id, include_foreign_gaus
    
    # from config file
    primary_geography_id = int(cfgfile.get('case', 'primary_geography_id'))
    primary_subset_id = [int(g) for g in cfgfile.get('case', 'primary_subset_id').split(',') if len(g)]
    breakout_geography_id = [int(g) for g in cfgfile.get('case', 'breakout_geography_id').split(',') if len(g)]
    dispatch_geography_id = int(cfgfile.get('case', 'dispatch_geography_id'))
    dispatch_breakout_geography_id = [int(g) for g in cfgfile.get('case', 'dispatch_breakout_geography_id').split(',') if len(g)]
    include_foreign_gaus = True if cfgfile.get('case', 'include_foreign_gaus').lower()=='true' else False
    keep_oth_index_over_oth_gau = True if cfgfile.get('case', 'keep_oth_index_over_oth_gau').lower()=='true' else False
    
    # geography conversion object
    geo = geomapper.GeoMapper()
    
    # derived from inputs and geomapper object
    dispatch_geography = geo.get_dispatch_geography_name()
    primary_geography = geo.get_primary_geography_name()
    dispatch_geographies = geo.geographies[dispatch_geography] 
    geographies = geo.geographies[primary_geography]
    
def init_date_lookup():
    global date_lookup, time_slice_col, electricity_energy_type_id, electricity_energy_type_shape_id
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
    time_slice_col = ['year', 'month', 'week', 'hour', 'day_type_id']
    electricity_energy_type_id, electricity_energy_type_shape_id = util.sql_read_table('FinalEnergy', column_names=['id', 'shape_id'], name='electricity')

def init_output_levels():
    global output_demand_levels, output_supply_levels, output_combined_levels
    output_demand_levels = ['year','technology', primary_geography,'sector','subsector','final_energy']
    output_supply_levels = ['year','vintage','supply_technology',primary_geography, primary_geography + "_supply", 'demand_sector','final_energy','supply_node','ghg','resource_bins']
    output_combined_levels = list(set(output_supply_levels + output_demand_levels))
    
    if cfgfile.get('output_detail','vintage').lower() != 'true':
        output_combined_levels.remove('vintage')
        
    if cfgfile.get('output_detail','technology').lower() != 'true':
        output_combined_levels.remove('technology')
    
    if cfgfile.get('output_detail','supply_geography').lower() != 'true':
        output_combined_levels.remove(primary_geography + "_supply")

def init_outputs_id_map():
    global outputs_id_map
    outputs_id_map[primary_geography] = util.upper_dict(geo.geography_names.items())
    outputs_id_map[primary_geography+"_supply"] =  outputs_id_map[primary_geography]     
    outputs_id_map['technology'] = util.upper_dict(util.sql_read_table('DemandTechs', ['id', 'name']))
    outputs_id_map['supply_technology'] = util.upper_dict(util.sql_read_table('SupplyTechs', ['id', 'name']))
    outputs_id_map['final_energy'] = util.upper_dict(util.sql_read_table('FinalEnergy', ['id', 'name']))
    outputs_id_map['supply_node'] = util.upper_dict(util.sql_read_table('SupplyNodes', ['id', 'name']))       
    outputs_id_map['supply_node_export'] = util.upper_dict(util.sql_read_table('SupplyNodes', ['id', 'name'])," EXPORT")
    outputs_id_map['subsector'] = util.upper_dict(util.sql_read_table('DemandSubsectors', ['id', 'name']))           
    outputs_id_map['sector'] = util.upper_dict(util.sql_read_table('DemandSectors', ['id', 'name']))
    outputs_id_map['ghg'] = util.upper_dict(util.sql_read_table('GreenhouseGases', ['id', 'name']))
    outputs_id_map['driver'] = util.upper_dict(util.sql_read_table('DemandDrivers', ['id', 'name']))
    outputs_id_map[dispatch_geography] = util.upper_dict(util.sql_read_table('GeographiesData', ['id', 'name'], geography_id=dispatch_geography_id, return_unique=True, return_iterable=True))
    outputs_id_map['dispatch_feeder'] = util.upper_dict(util.sql_read_table('DispatchFeeders', ['id', 'name']))
    outputs_id_map['dispatch_feeder'][0] = 'BULK'

    for id, name in util.sql_read_table('OtherIndexes', ('id', 'name'), return_iterable=True):
        if name in ('technology', 'final_energy'):
            continue
        outputs_id_map[name] = util.upper_dict(util.sql_read_table('OtherIndexesData', ['id', 'name'], other_index_id=id, return_unique=True))

def init_output_parameters():
    global currency_name, output_currency
    currency_name = cfgfile.get('case', 'currency_name')
    output_currency = cfgfile.get('case', 'currency_year_id') + ' ' + currency_name
    init_output_levels()
    init_outputs_id_map()

