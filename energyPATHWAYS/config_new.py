__author__ = 'Ben Haley & Ryan Jones'

import ConfigParser
import os
import warnings
import pint
import psycopg2

import geomapper
import util
import data_models.data_source as data_source
from data_models.system import Currency
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
dnmtr_col_names = ['driver_denominator_1_id', 'driver_denominator_2_id']
drivr_col_names = ['driver_1_id', 'driver_2_id']

# Initiate pint for unit conversions
ureg = None

##Geography conversions
geo = None

# output config
currency_name = None
output_levels = None
output_currency = None


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
    init_output_parameters()

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
    data_source.init(dbCfg)

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
    global geo
    geo = geomapper.GeoMapper()


def init_output_parameters():
    global currency_name, output_levels, output_currency
    #currency_name = util.sql_read_table('Currencies', 'name', id=int(cfgfile.get('case', 'currency_id')))
    currency_name = data_source.get(Currency, int(cfgfile.get('case', 'currency_id'))).name
    output_levels = cfgfile.get('case', 'output_levels').split(', ')
    output_currency = cfgfile.get('case', 'currency_year_id') + ' ' + currency_name
