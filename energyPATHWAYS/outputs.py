# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 19:11:59 2015

@author: Ben
"""

import pandas as pd
import util
from config import cfg

class Output(object):
    def __init__(self):
        self.output_types = ['energy_outputs', 'cost_outputs', 'stock_outputs', 'emissions_outputs']
    
    def return_cleaned_output(self, output_type):
        if not hasattr(self, output_type):
            return None
        if type(getattr(self, output_type)) is not pd.core.frame.DataFrame:
            raise ValueError('output_type must be a pandas dataframe')
        cleaned_output = getattr(self, output_type).copy()
        
        dct = cfg.outputs_id_map
        index = cleaned_output.index
        index.set_levels([[dct[name].get(item, item) for item in level] for name, level in zip(index.names, index.levels)], inplace=True)
        index.names = [x.upper() if isinstance(x, basestring) else x for x in index.names]
        cleaned_output.columns = [x.upper() if isinstance(x, basestring) else x for x in cleaned_output.columns]
        
        return cleaned_output

#class Output(object):
#    """creates an empty container"""
#    def __init__(self, output_name, name):
#        self.output_name = output_name.upper()
#        self.name = name.upper()
#
#
#class DemandSectorOutput(Output):
#    def __init__(self, output_name, name, sector_id):
#        self.sector_id = sector_id
#        Output.__init__(self, output_name=output_name, name=name)
#
#
#class DemandSubsectorOutput(Output):
#    def __init__(self, output_name, name, subsector_id):
#        self.subsector_id = subsector_id
#        Output.__init__(self, output_name=output_name, name=name)
#
#    def clean_subsector_outputs(self):
#        """
#        cleans subsector outputs for viewing outside the model
#        """
#        geography_lookup_dict = None
#        technology_lookup_dict = None
#        final_energy_lookup_dict = None
#        attributes = vars(self)
#        for att in attributes:
#            att = getattr(self, att)
#            if type(att) == pd.core.frame.DataFrame:
#                self.clean_subsector_geography(att, geography_lookup_dict)
#                self.clean_subsector_technology(att, self.subsector_id, technology_lookup_dict)
#                self.clean_subsector_energy(att, final_energy_lookup_dict)
#                self.clean_subsector_other_indexes(att, self.subsector_id)
#                self.append_subsector(att)
#                self.uppercase_levels_and_names(att)
#
#    def uppercase_levels_and_names(self, attribute):
#        """changes the level names and labels to uppercase"""
#        for name in attribute.index.names:
#            level_loc = util.position_in_index(attribute, name)
#            level = attribute.index.levels[level_loc]
#            level_upper = [x.upper() for x in level if isinstance(x, unicode)]
#            level_dict = dict(zip(level, level_upper))
#            util.replace_index_label(attribute, level_dict, name)
#        attribute.index.names = [x.upper() for x in attribute.index.names]
#
#    def append_subsector(self, attribute):
#        """append subsector id to dataframe levels"""
#        attribute['subsector'] = util.sql_read_table('DemandSubsectors', 'name', id=self.subsector_id)
#        attribute.set_index('subsector', append=True, inplace=True)
#
#
#    def clean_subsector_geography(self, attribute, geography_lookup_dict):
#        """replace geography ids with names"""
#        if geography_lookup_dict is None:
#            primary_geography = cfg.cfgfile.get('case', 'primary_geography')
#            primary_geography_id = util.sql_read_table('Geographies', 'id', name=primary_geography)
#            geography_lookup_dict = dict(util.sql_read_table('GeographiesData', ['id', 'name'],
#                                                             geography_id=primary_geography_id, return_unique=True,
#                                                             return_iterable=True))
#
#        util.replace_index_label(attribute, geography_lookup_dict, primary_geography)
#        util.replace_index_name(attribute, 'geography', primary_geography)
#
#    def clean_subsector_technology(self, attribute, subsector_id, technology_lookup_dict):
#        """replace technology ids with technology names"""
#        if 'technology' in attribute.index.names:
#            if technology_lookup_dict is None:
#                technology_lookup_dict = dict(
#                    util.sql_read_table('DemandTechs', ['id', 'name'], subsector_id=subsector_id))
#            util.replace_index_label(attribute, technology_lookup_dict, 'technology')
#        if 'technology_temp' in attribute.index.names:
#            util.replace_index_name(attribute, 'technology', 'technology_temp')
#
#    def clean_subsector_energy(self, attribute, final_energy_lookup_dict):
#        """replace final energy ids with names"""
#        if 'final_energy' in attribute.index.names:
#            if final_energy_lookup_dict is None:
#                final_energy_lookup_dict = dict(util.sql_read_table('FinalEnergy', ['id', 'name']))
#            util.replace_index_label(attribute, final_energy_lookup_dict, 'final_energy')
#
#    def clean_subsector_other_indexes(self, attribute, subsector_id):
#        """replace other index ids with names"""
#        other_indexes = [x for x in util.sql_read_table('OtherIndexes', 'name', return_iterable=True) if
#                         x not in ['technology', 'final_energy']]
#        other_indexes = [x for x in attribute.index.names if x in other_indexes]
#        for other_index in other_indexes:
#            index_id = util.sql_read_table('OtherIndexes', 'id', name=other_index)
#            lookup_dict = dict(util.sql_read_table('OtherIndexesData', ['id', 'name'], other_index_id=index_id))
#            util.replace_index_label(attribute, lookup_dict, other_index)