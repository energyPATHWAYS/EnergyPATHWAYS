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

# Don't print warnings
warnings.simplefilter("ignore")

class Config:
    def __init__(self):
        # sys.path.insert(0, os.getcwd())
#        self.directory = os.getcwd().rstrip('code')
        
        # weibul_coefficient_of_variation is used to find weibul parameters given lifetime statistics
        self.weibul_coeff_of_var = util.create_weibul_coefficient_of_variation()
        self.dnmtr_col_names = ['driver_denominator_1_id', 'driver_denominator_2_id']
        self.drivr_col_names = ['driver_1_id', 'driver_2_id']
        
    def init_cfgfile(self, cfgfile_path):
        if not os.path.isfile(cfgfile_path):
            raise OSError('config file not found: ' + str(cfgfile_path))
        
        cfgfile = ConfigParser.ConfigParser()
            
        cfgfile.read(cfgfile_path)
        
#        cfgfile.add_section('directory')
#        cfgfile.set('directory', 'path', self.directory)
        cfgfile.set('case', 'years', range(int(cfgfile.get('case', 'demand_start_year')),
                                           int(cfgfile.get('case', 'end_year')) + 1,
                                           int(cfgfile.get('case', 'year_step'))))
        cfgfile.set('case', 'supply_years', range(int(cfgfile.get('case', 'current_year')),
                                                  int(cfgfile.get('case', 'end_year')) + 1,
                                                  int(cfgfile.get('case', 'year_step'))))
        
        self.primary_geography = cfgfile.get('case', 'primary_geography')
        self.cfgfile = cfgfile
        
        
    def init_db(self):
        pg_host = cfg.cfgfile.get('database', 'pg_host')
        if not pg_host:
            pg_host = 'localhost'
        pg_user = self.cfgfile.get('database', 'pg_user')
        pg_password = self.cfgfile.get('database', 'pg_password')
        pg_database = self.cfgfile.get('database', 'pg_database')
        conn_str = "host='%s' dbname='%s' user='%s'" % (pg_host, pg_database, pg_user)
        if pg_password:
            conn_str += " password='%s'" % pg_password
    
        # Open pathways database
        self.con = psycopg2.connect(conn_str)
        self.cur = self.con.cursor()
        
    def drop_df(self,cfgfile):
        self.cur.close()
        del self.cur
        del self.con
        


    def init_pint(self, custom_pint_definitions_path=None):
        # Initiate pint for unit conversions
        self.ureg = pint.UnitRegistry()
        
        if custom_pint_definitions_path is not None:
            if not os.path.isfile(custom_pint_definitions_path):
                raise OSError('pint definitions file not found: ' + str(custom_pint_definitions_path))
            self.ureg.load_definitions(custom_pint_definitions_path)

    def init_geo(self):
        ##Geography conversions
        self.geo = geography.Geography()


    def init_date_lookup(self):
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
        
        self.date_lookup = DateTimeLookup()
        self.time_slice_col = ['year', 'month', 'week', 'hour', 'day_type_id']
        self.electricity_energy_type_id, self.electricity_energy_type_shape_id = util.sql_read_table('FinalEnergy', column_names=['id', 'shape_id'], name='electricity')

    def init_outputs_id_map(self):
        self.currency_name = self.cfgfile.get('case', 'currency_name')
#        self.output_demand_levels = ['year','vintage','technology',self.cfgfile.get('case','primary_geography'),'sector','subsector','final_energy']
        self.output_demand_levels = ['year','technology',self.cfgfile.get('case','primary_geography'),'sector','subsector','final_energy']
        self.output_supply_levels = ['year','vintage','supply_technology',self.cfgfile.get('case','primary_geography'), self.cfgfile.get('case','primary_geography') + "_supply", 'demand_sector','final_energy','supply_node','ghg','resource_bins']
        self.output_combined_levels = list(set(self.output_supply_levels+self.output_demand_levels))
        vintage = self.cfgfile.get('output_detail','vintage')
        if vintage != 'True':
            self.output_combined_levels.remove('vintage')
        technology = self.cfgfile.get('output_detail','technology')
        if technology != 'True':
            self.output_combined_levels.remove('technology')
        supply_geography = self.cfgfile.get('output_detail','supply_geography') 
        if supply_geography != 'True':
            self.output_combined_levels.remove(self.cfgfile.get('case','primary_geography') + "_supply")            
        self.output_currency = self.cfgfile.get('case', 'currency_year_id') + ' ' + self.currency_name
        self.outputs_id_map = defaultdict(dict)
#        if 'primary_geography' in self.output_demand_levels:
#            self.output_demand_levels[self.output_demand_levels.index('primary_geography')] = self.primary_geography
#        if 'primary_geography' in self.output_supply_levels:
#            self.output_supply_levels[self.output_supply_levels.index('primary_geography')] = self.primary_geography     
        primary_geography_id = util.sql_read_table('Geographies', 'id', name=self.primary_geography)
        self.outputs_id_map[self.primary_geography] = util.upper_dict(util.sql_read_table('GeographiesData', ['id', 'name'], geography_id=primary_geography_id, return_unique=True, return_iterable=True))
        self.outputs_id_map[self.primary_geography+"_supply"] =  self.outputs_id_map[self.primary_geography]       
        self.outputs_id_map['technology'] = util.upper_dict(util.sql_read_table('DemandTechs', ['id', 'name']))
        self.outputs_id_map['supply_technology'] = util.upper_dict(util.sql_read_table('SupplyTechs', ['id', 'name']))
        self.outputs_id_map['final_energy'] = util.upper_dict(util.sql_read_table('FinalEnergy', ['id', 'name']))
        self.outputs_id_map['supply_node'] = util.upper_dict(util.sql_read_table('SupplyNodes', ['id', 'name']))       
        self.outputs_id_map['supply_node_export'] = util.upper_dict(util.sql_read_table('SupplyNodes', ['id', 'name'])," EXPORT")
        self.outputs_id_map['subsector'] = util.upper_dict(util.sql_read_table('DemandSubsectors', ['id', 'name']))           
        self.outputs_id_map['sector'] = util.upper_dict(util.sql_read_table('DemandSectors', ['id', 'name']))
        self.outputs_id_map['ghg'] = util.upper_dict(util.sql_read_table('GreenhouseGases', ['id', 'name']))
        self.outputs_id_map['driver'] = util.upper_dict(util.sql_read_table('DemandDrivers', ['id', 'name']))
        for id, name in util.sql_read_table('OtherIndexes', ('id', 'name'), return_iterable=True):
            if name in ('technology', 'final_energy'):
                continue
            self.outputs_id_map[name] = util.upper_dict(util.sql_read_table('OtherIndexesData', ['id', 'name'], other_index_id=id, return_unique=True))


#######################
#######################
cfg = Config()
#######################