__author__ = 'Ben Haley & Ryan Jones'

import os
import ConfigParser
import sqlite3 as sqlite
import pint
import geography
import warnings
import pandas as pd
from collections import defaultdict
import util

# Don't print warnings
warnings.simplefilter("ignore")

class Config:
    def __init__(self):
        # sys.path.insert(0, os.getcwd())
#        self.directory = os.getcwd().rstrip('code')
        
        # weibul_coefficient_of_variation is used to find weibul parameters given lifetime statistics
        self.weibul_coeff_of_var = util.create_weibul_coefficient_of_variation()

    def init_cfgfile(self, cfgfile_path):
        if not os.path.isfile(cfgfile_path):
            raise OSError('config file not found: ' + str(cfgfile_path))
        
        cfgfile = ConfigParser.ConfigParser()
            
        cfgfile.read(cfgfile_path)
        
#        cfgfile.add_section('directory')
#        cfgfile.set('directory', 'path', self.directory)
        cfgfile.set('case', 'years', range(int(cfgfile.get('case', 'start_year')),
                                           int(cfgfile.get('case', 'end_year')) + 1,
                                           int(cfgfile.get('case', 'year_step'))))
        cfgfile.set('case', 'supply_years', range(int(cfgfile.get('case', 'current_year')),
                                                  int(cfgfile.get('case', 'end_year')) + 1,
                                                  int(cfgfile.get('case', 'year_step'))))
        
        self.primary_geography = cfgfile.get('case', 'primary_geography')
        self.cfgfile = cfgfile

    def init_db(self, db_path):
        if not os.path.isfile(db_path):
            raise OSError('config file not found: ' + str(db_path))
            
        # Open pathways database
        self.con = sqlite.connect(db_path)
        self.cur = self.con.cursor()

        # common data inputs
        self.dnmtr_col_names = util.sql_read_table('DemandUnitDenominators', 'datatable_column_name')
        self.drivr_col_names = util.sql_read_table('DemandDriverColumns', 'datatable_column_name')
    
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
        self.currency_name = util.sql_read_table('Currencies', 'name', id=int(self.cfgfile.get('case', 'currency_id')))
        universal_output_levels = ['unit'] # we always want it to have an output unit
        self.output_levels = list(set(universal_output_levels + self.cfgfile.get('case', 'output_levels').split(', ')))
        self.output_currency = self.cfgfile.get('case', 'currency_year_id') + ' ' + self.currency_name
        self.outputs_id_map = defaultdict(dict)
        if 'primary_geography' in self.output_levels:
            self.output_levels[self.output_levels.index('primary_geography')] = self.primary_geography
        primary_geography_id = util.sql_read_table('Geographies', 'id', name=self.primary_geography)
        self.outputs_id_map[self.primary_geography] = util.upper_dict(util.sql_read_table('GeographiesData', ['id', 'name'], geography_id=primary_geography_id, return_unique=True, return_iterable=True))
        self.outputs_id_map[self.primary_geography+"_supply"] =  self.outputs_id_map[self.primary_geography]       
        self.outputs_id_map['technology'] = util.upper_dict(util.sql_read_table('DemandTechs', ['id', 'name']))
        self.outputs_id_map['final_energy'] = util.upper_dict(util.sql_read_table('FinalEnergy', ['id', 'name']))
        self.outputs_id_map['supply_node'] = util.upper_dict(util.sql_read_table('SupplyNodes', ['id', 'name']))       
        self.outputs_id_map['supply_node_export'] = util.upper_dict(util.sql_read_table('SupplyNodes', ['id', 'name'])," EXPORT")
        self.outputs_id_map['subsector'] = util.upper_dict(util.sql_read_table('DemandSubsectors', ['id', 'name']))           
        self.outputs_id_map['sector'] = util.upper_dict(util.sql_read_table('DemandSectors', ['id', 'name']))
        self.outputs_id_map['ghg'] = util.upper_dict(util.sql_read_table('GreenhouseGases', ['id', 'name']))
        for id, name in util.sql_read_table('OtherIndexes', ('id', 'name'), return_iterable=True):
            if name in ('technology', 'final_energy'):
                continue
            self.outputs_id_map[name] = util.upper_dict(util.sql_read_table('OtherIndexesData', ['id', 'name'], other_index_id=id, return_unique=True))


#######################
#######################
cfg = Config()
#######################