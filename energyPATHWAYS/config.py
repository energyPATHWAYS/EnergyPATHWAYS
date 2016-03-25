__author__ = 'Ben Haley & Ryan Jones'

import os
import ConfigParser
import pint
import geography
import warnings
import pandas as pd
from collections import defaultdict
import util
import psycopg2
#import ipdb

# Don't print warnings
warnings.simplefilter("ignore")

# directory = None
weibul_coeff_of_var = None
cfgfile = None
primary_geography = None

# db connection and cursor
con = None
cur = None

# common data inputs
dnmtr_col_names = None
drivr_col_names = None

# Initiate pint for unit conversions
ureg = None

##Geography conversions
geo = None

# load shape support
date_lookup = None
time_slice_col = None

# output config
currency_name = None
output_levels = None
outputs_id_map = None
output_levels = None

def initialize_config(cfgfile_path, custom_pint_definitions_path):
    # sys.path.insert(0, os.getcwd())
    # global directory
    # directory = os.getcwd().rstrip('code')
    # weibul_coefficient_of_variation is used to find weibul parameters given lifetime statistics
    global weibul_coeff_of_var
    weibul_coeff_of_var = util.create_weibul_coefficient_of_variation()
    init_cfgfile(cfgfile_path)
    # TODO: this requires the cfg global to be assigned to a config object but note that it is in the constructor. Thus the global assignment above. Yuck.
    init_db()
    init_pint(custom_pint_definitions_path)
    init_geo()
    init_shapes()
    init_outputs_id_map()

def load_config(cfgfile_path):
    global cfgfile
    cfgfile = ConfigParser.ConfigParser()
    cfgfile.read(cfgfile_path)

def init_cfgfile(cfgfile_path):
    load_config(cfgfile_path)
    global primary_geography
    #if not os.path.isfile(cfgfile_path):
    #    raise OSError('config file not found: ' + str(cfgfile_path))
    
    
    
    # cfgfile.add_section('directory')
    # cfgfile.set('directory', 'path', directory)
    cfgfile.set('case', 'years', range(int(cfgfile.get('case', 'start_year')),
                                       int(cfgfile.get('case', 'end_year')) + 1,
                                       int(cfgfile.get('case', 'year_step'))))
    cfgfile.set('case', 'supply_years', range(int(cfgfile.get('case', 'current_year')),
                                              int(cfgfile.get('case', 'end_year')) + 1,
                                              int(cfgfile.get('case', 'year_step'))))

    primary_geography = cfgfile.get('case', 'primary_geography')
        
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

    global dbCfg
    dbCfg = {
      'drivername': 'postgres',
      'host':       pg_host,
      'port':       '5432',
      'username':   pg_user,
      'password':   pg_password,
      'database':   pg_database
    }
    # Open pathways database
    con = psycopg2.connect(conn_str)
    cur = con.cursor()

    # common data inputs
    dnmtr_col_names = util.sql_read_table('DemandUnitDenominators', 'datatable_column_name')
    drivr_col_names = util.sql_read_table('DemandDriverColumns', 'datatable_column_name')

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
    global geo
    geo = geography.Geography()

def init_shapes():
    global date_lookup, time_slice_col
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
    
    import shape
    shape.shapes.create_empty_shapes()
    time_slice_col = ['year', 'month', 'hour', 'day_type_id']

def init_outputs_id_map():
    global currency_name, output_levels, outputs_id_map, output_levels
    currency_name = util.sql_read_table('Currencies', 'name', id=int(cfgfile.get('case', 'currency_id')))
    output_levels = cfgfile.get('case', 'output_levels').split(', ')       
    outputs_id_map = defaultdict(dict)
    if 'primary_geography' in output_levels:
        output_levels[output_levels.index('primary_geography')] = primary_geography
    primary_geography_id = util.sql_read_table('Geographies', 'id', name=primary_geography)
    print primary_geography_id
    outputs_id_map[primary_geography] = util.upper_dict(util.sql_read_table('GeographiesData', ['id', 'name'], geography_id=primary_geography_id, return_unique=True, return_iterable=True))
    outputs_id_map[primary_geography+"_supply"] =  outputs_id_map[primary_geography]       
    outputs_id_map['technology'] = util.upper_dict(util.sql_read_table('DemandTechs', ['id', 'name']))
    outputs_id_map['final_energy'] = util.upper_dict(util.sql_read_table('FinalEnergy', ['id', 'name']))
    outputs_id_map['supply_node'] = util.upper_dict(util.sql_read_table('SupplyNodes', ['id', 'name']))       
    outputs_id_map['supply_node_export'] = util.upper_dict(util.sql_read_table('SupplyNodes', ['id', 'name'])," EXPORT")
    outputs_id_map['subsector'] = util.upper_dict(util.sql_read_table('DemandSubsectors', ['id', 'name']))           
    outputs_id_map['sector'] = util.upper_dict(util.sql_read_table('DemandSectors', ['id', 'name']))
    outputs_id_map['ghg'] = util.upper_dict(util.sql_read_table('GreenhouseGases', ['id', 'name']))
    for id, name in util.sql_read_table('OtherIndexes', ('id', 'name'), return_iterable=True):
        if name in ('technology', 'final_energy'): 
            continue
        outputs_id_map[name] = util.upper_dict(util.sql_read_table('OtherIndexesData', ['id', 'name'], other_index_id=id, return_unique=True))

