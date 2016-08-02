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
from multiprocessing import cpu_count

# Don't print warnings
warnings.simplefilter("ignore")

# various inputs
output_path = None
cfgfile = None
primary_geography = None
primary_geography_id = None
scenario_dict = None
weibul_coeff_of_var = None

# db connection and cursor
con = None
cur = None

# common data inputs
dnmtr_col_names = ['driver_denominator_1_id', 'driver_denominator_2_id']
drivr_col_names = ['driver_1_id', 'driver_2_id']

# Initiate pint for unit conversions
ureg = None

# Geography conversions
geo = None

# output config
currency_name = None
output_levels = None
output_currency = None

# run years
years = None
supply_years = None

# electricity shapes
date_lookup = None
time_slice_col = None
electricity_energy_type_id = None
electricity_energy_type_shape_id = None

# outputs
currency_name = None
output_currency = None
output_demand_levels = None
output_supply_levels = None
output_combined_levels = None
outputs_id_map = defaultdict(dict)

# parallel processing
available_cpus = None

def initialize_config(cfgfile_path, custom_pint_definitions_path, _output_path=None):
    global weibul_coeff_of_var, scenario_dict, available_cpus, output_path
    output_path = os.getcwd() if _output_path is None else _output_path 
    weibul_coeff_of_var = util.create_weibul_coefficient_of_variation()
    init_cfgfile(cfgfile_path)
    # TODO: this requires the cfg global to be assigned to a config object but note that it is in the constructor. Thus the global assignment above. Yuck.
    init_db()
    scenario_dict = dict(util.sql_read_table('Scenarios',['id', 'name'], return_iterable=True))
    available_cpus = min(cpu_count(), int(cfgfile.get('case','num_cores')))
    init_pint(custom_pint_definitions_path)
    init_geo()
    init_date_lookup()
    init_output_parameters()

def load_config(cfgfile_path):
    global cfgfile
    cfgfile = ConfigParser.ConfigParser()
    cfgfile.read(cfgfile_path)

def init_cfgfile(cfgfile_path):
    load_config(cfgfile_path)
    global primary_geography, years, supply_years
    
    primary_geography = cfgfile.get('case', 'primary_geography')
    
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

    # Open pathways database
    con = psycopg2.connect(conn_str)
    cur = con.cursor()
        

def init_pint(custom_pint_definitions_path=None):
    # Initiate pint for unit conversions
    global ureg
    ureg = pint.UnitRegistry()
    
    if custom_pint_definitions_path is not None:
        if not os.path.isfile(custom_pint_definitions_path):
            raise OSError('pint definitions file not found: ' + str(custom_pint_definitions_path))
        ureg.load_definitions(custom_pint_definitions_path)
        
def init_geo():
    #Geography conversions
    global geo, primary_geography_id
    geo = geomapper.GeoMapper()
    primary_geography_id = util.sql_read_table('Geographies', 'id', name=primary_geography)

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
    output_demand_levels = ['year','technology',cfgfile.get('case','primary_geography'),'sector','subsector','final_energy']
    output_supply_levels = ['year','vintage','supply_technology',cfgfile.get('case','primary_geography'), cfgfile.get('case','primary_geography') + "_supply", 'demand_sector','final_energy','supply_node','ghg','resource_bins']
    output_combined_levels = list(set(output_supply_levels + output_demand_levels))
    
    if cfgfile.get('output_detail','vintage').lower() != 'true':
        output_combined_levels.remove('vintage')
        
    if cfgfile.get('output_detail','technology').lower() != 'true':
        output_combined_levels.remove('technology')
    
    if cfgfile.get('output_detail','supply_geography').lower() != 'true':
        output_combined_levels.remove(cfgfile.get('case','primary_geography') + "_supply")

def init_outputs_id_map():
    global outputs_id_map
    outputs_id_map[primary_geography] = util.upper_dict(util.sql_read_table('GeographiesData', ['id', 'name'], geography_id=primary_geography_id, return_unique=True, return_iterable=True))
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

