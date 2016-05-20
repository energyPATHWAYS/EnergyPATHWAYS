# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 19:11:59 2015

@author: Ben
"""

import pandas as pd
import util
from config import cfg
from collections import defaultdict
import data_models.data_source as data_source
from data_models.system import GreenhouseGas
from data_models.geography import Geography
from data_models.misc import FinalEnergy, OtherIndex
from data_models.demand import DemandSector


class Output(object):
    def outputs_id_map(self):
        try:
            return self._outputs_id_map
        except AttributeError:
            self._outputs_id_map = defaultdict(dict)
            primary_geography_obj = data_source.fetch_one(Geography, name=cfg.primary_geography)
            self._outputs_id_map[cfg.primary_geography] = util.new_upper_dict(
                data_source.models_to_lookup(primary_geography_obj.geographies_data)
            )
            self._outputs_id_map[cfg.primary_geography + "_supply"] = self._outputs_id_map[cfg.primary_geography]
            self._outputs_id_map['technology'] = util.upper_dict(util.sql_read_table('DemandTechs', ['id', 'name']))
            self._outputs_id_map['final_energy'] = util.new_upper_dict(data_source.fetch_as_lookup(FinalEnergy))
            self._outputs_id_map['supply_node'] = util.upper_dict(util.sql_read_table('SupplyNodes', ['id', 'name']))
            self._outputs_id_map['supply_node_export'] = util.upper_dict(util.sql_read_table('SupplyNodes', ['id', 'name']), " EXPORT")
            self._outputs_id_map['subsector'] = util.upper_dict(util.sql_read_table('DemandSubsectors', ['id', 'name']))
            self._outputs_id_map['sector'] = util.new_upper_dict(data_source.fetch_as_lookup(DemandSector))
            self._outputs_id_map['ghg'] = util.new_upper_dict(data_source.fetch_as_lookup(GreenhouseGas))
            for oth_idx in data_source.fetch(OtherIndex):
                if oth_idx.name in ('technology', 'final_energy'):
                    continue
                self._outputs_id_map[oth_idx.name] = util.new_upper_dict(
                    data_source.models_to_lookup(oth_idx.other_indexes_data))
            
            return self._outputs_id_map
    
    def return_cleaned_output(self, output_type):
        if not hasattr(self, output_type):
            return None
        if type(getattr(self, output_type)) is not pd.core.frame.DataFrame:
            raise ValueError('output_type must be a pandas dataframe')
        cleaned_output = getattr(self, output_type).copy()
        if 'year' in cleaned_output.index.names:
            cleaned_output = cleaned_output[cleaned_output.index.get_level_values('year')>=int(cfg.cfgfile.get('case','current_year'))]
        dct = self.outputs_id_map()
        index = cleaned_output.index
        index.set_levels([[dct[name].get(item, item) for item in level] for name, level in zip(index.names, index.levels)], inplace=True)
        index.names = [x.upper() if isinstance(x, basestring) else x for x in index.names]
        cleaned_output.columns = [x.upper() if isinstance(x, basestring) else x for x in cleaned_output.columns]
        
        return cleaned_output

