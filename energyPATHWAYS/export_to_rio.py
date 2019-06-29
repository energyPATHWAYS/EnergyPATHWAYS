import pandas as pd
from outputs import Output
import os
from demand import Demand
import util
from outputs import Output
import shutil
import config as cfg
from supply import Supply
import pandas as pd
import logging
import shape
import pdb
from scenario_loader import Scenario
import copy
import numpy as np
from collections import defaultdict
import glob
import time
import cPickle as pickle
from energyPATHWAYS.supply import StorageNode,BlendNode,SupplyStockNode,ImportNode, PrimaryNode
import ast
import shape as ep_shape
import datetime as DT
from dateutil.relativedelta import relativedelta


class RioExport(object):
    def __init__(self, model, scenario_index):
        self.supply = model.supply
        #todo fix this hardcode
        self.supply.bulk_node_id = 6
        self.db_dir = os.path.join(cfg.workingdir, 'rio_db_export')
        self.meta_dict = defaultdict(list)
        self.scenario_index = scenario_index


    def write_all(self):
        self.write_blend()
        self.flex_load_df = self.flatten_flex_load_dict()
        if self.scenario_index == 0:
            self.write_reference_tables()
            self.write_all_empty()
            self.write_shapes()
            self.write_blend_main()
            self.write_new_tech_main()
            self.write_existing_gen()
            self.write_conversion_main()
            if self.flex_load_df is not None:
                self.write_flex_tech_main()
            self.write_capacity_zone_main()
            self.write_product_main()
        self.write_conversion()
        self.write_product()
        self.write_topography()
        self.write_potential_group()
        self.write_new_gen()
        self.write_transmission()
        self.write_flex_load()



    def write_reference_tables(self):
        self.write_geographies()
        self.write_geography_map_keys()
        self.write_geography_spatial_join()
        self.write_currency_conversion()
        self.write_inflation_conversion()

    def write_geographies(self):
        df = pd.DataFrame.from_dict(cfg.geo.geographies, orient='index').stack().to_frame()
        df.index.names = ['geography','col_index']
        df.columns = ['gau']
        df['gau'] = [cfg.outputs_id_map[cfg.supply_primary_geography][x] if x in cfg.outputs_id_map[cfg.supply_primary_geography].keys() else x for x in df['gau'].values]
        df = Output.clean_rio_df(df)
        df = df[['geography','gau']]
        Output.write_rio(df, "GEOGRAPHIES" + ".csv", self.db_dir , index=False)

    def write_geography_spatial_join(self):
        df = cfg.geo.values
        df = Output.clean_rio_df(df,add_geography=False,replace_gau=False)
        Output.write_rio(df, "GEOGRAPHIES_SPATIAL_JOIN" + ".csv", self.db_dir , index=False)

    def write_geography_map_keys(self):
       df = pd.DataFrame(cfg.geo.values.columns,columns=['name'])
       Output.write_rio(df, "GEOGRAPHY_MAP_KEYS" + ".csv", self.db_dir, index=False)

    def write_currency_conversion(self):
        df = pd.DataFrame(self.supply.currencies_conversion,columns = ['currency','year','value'])
        df = Output.clean_rio_df(df)
        Output.write_rio(df,"CURRENCY_CONVERSION"+".csv",self.db_dir,index=False)

    def write_inflation_conversion(self):
        df = pd.DataFrame(self.supply.inflation__conversion,columns = ['year','currency','value'])
        df = Output.clean_rio_df(df)
        Output.write_rio(df,"INFLATION_CONVERSION"+".csv",self.db_dir,index=False)




    def write_flex_load(self):
        if self.flex_load_df is not None:
            self.write_flex_tech_shapes()
            self.write_flex_tech_p_max()
            self.write_flex_tech_p_min()
            self.write_flex_tech_energy()
            self.write_flex_tech_schedule()
        else:
            self.write_empty('FLEX_TECH_MAIN', '\\Technology Inputs\\Flex Load', ['name', 'capacity_zone', 'ancillary_service_eligible', 'shape'])
            self.write_empty('FLEX_TECH_PMAX', '\\Technology Inputs\\Flex Load',['name', 'source','notes','unit','geography','gau','geography_map_key','interpolation_method','extrapolation_method','vintage','value','sensitivity'])
            self.write_empty('FLEX_TECH_PMIN', '\\Technology Inputs\\Flex Load', ['name', 'source','notes','unit','geography','gau','geography_map_key','interpolation_method','extrapolation_method','vintage','value','sensitivity'])
            self.write_empty('FLEX_TECH_ENERGY', '\\Technology Inputs\\Flex Load', ['name', 'source', 'notes', 'unit', 'geography', 'gau', 'geography_map_key', 'interpolation_method',
                 'extrapolation_method', 'vintage', 'value', 'sensitivity'])
            self.write_empty('FLEX_TECH_SCHEDULE', '\\Technology Inputs\\Flex Load', ['name','geography','gau','geography_map_key','interpolation_method','extrapolation_method','year','value','sensitivity'])

    def write_shapes(self):
        shapes = {}
        active_nodes = self.supply.nodes[self.supply.bulk_id].nodes + self.supply.nodes[
            self.supply.thermal_dispatch_node_id].nodes + self.supply.nodes[self.supply.distribution_node_id].nodes
        for node in active_nodes:
            if not isinstance(self.supply.nodes[node], BlendNode) and hasattr(self.supply.nodes[node],'technologies'):
                for technology in self.supply.nodes[node].technologies.keys():
                    if hasattr(self.supply.nodes[node].technologies[technology], 'shape'):
                        shapes[self.supply.nodes[node].technologies[technology].shape.name] = self.supply.nodes[node].technologies[technology].shape
                    elif hasattr(self.supply.nodes[node], 'shape') and self.supply.nodes[
                        node].shape is not None:
                        shapes[self.supply.nodes[node].shape.name] = self.supply.nodes[node].shape
                    else:
                        if "flat" in shapes.keys():
                            continue
                        else:
                            start_date = cfg.shape_start_date
                            end_date = start_date + relativedelta(years=cfg.shape_years, hours=-1)
                            active_dates_index = pd.date_range(start_date, end_date, freq='H')
                            index = pd.MultiIndex.from_product([cfg.geo.geographies[cfg.supply_primary_geography],active_dates_index], names=[cfg.supply_primary_geography,'weather_datetime'])
                            shapes['flat'] = ep_shape.shapes.make_flat_load_shape(index,num_active_years = 1)
        for shape_name, shape in shapes.iteritems():
            self.meta_dict['name'].append(shape_name.lower())
            self.meta_dict['shape_type'].append( 'weather date')
            self.meta_dict['input_type'].append( 'intensity')
            self.meta_dict['shape_unit_type'].append('power')
            self.meta_dict['time_zone'].append(cfg.outputs_id_map[cfg.supply_primary_geography][int(cfg.cfgfile.get('case', 'dispatch_outputs_timezone_id'))])
            self.meta_dict['geography'].append(cfg.supply_primary_geography)
            self.meta_dict['geography_map_key'].append(None)
            self.meta_dict['interpolation_method'].append('linear_interpolation')
            self.meta_dict['extrapolation_method'].append('nearest')
            shape_df =  shape if isinstance(shape,pd.DataFrame) else shape.values
            shape_df = util.remove_df_levels(shape_df,['resource_bin','dispatch_feeder'],agg_function='mean')
            #shape_df = shape_df.tz_localize(None, level='weather_datetime')
            shape_df = Output.clean_rio_df(shape_df,add_geography=False)
            Output.write_rio(shape_df,shape_name.lower()+ ".csv",self.db_dir + "\\ShapeData",index=False)
        self.meta_dict['name'].append('bulk')
        self.meta_dict['shape_type'].append('weather date')
        self.meta_dict['input_type'].append('intensity')
        self.meta_dict['shape_unit_type'].append('power')
        self.meta_dict['time_zone'].append(
        cfg.outputs_id_map['time zone'][int(cfg.cfgfile.get('case', 'dispatch_outputs_timezone_id'))])
        self.meta_dict['geography'].append(cfg.dispatch_geography)
        self.meta_dict['geography_map_key'].append(None)
        self.meta_dict['interpolation_method'].append('linear_interpolation')
        self.meta_dict['extrapolation_method'].append('nearest')
        df = pd.DataFrame(self.meta_dict)
        df = df[['name', 'shape_type', 'input_type', 'shape_unit_type', 'time_zone', 'geography', 'geography_map_key', 'interpolation_method', 'extrapolation_method']]
        Output.write_rio(df, "SHAPE_META" + '.csv', self.db_dir, index=False)

    def write_flex_tech_main(self):
        dct = dict()
        if len(cfg.rio_feeder_geographies):
            for geography in cfg.rio_feeder_geographies:
                dct['name'] = [cfg.outputs_id_map[cfg.supply_primary_geography][geography].lower() + "_" + cfg.outputs_id_map['dispatch_feeder'][x] for x in self.supply.dispatch_feeders]
                dct['capacity_zone'] = dct['name']
                dct['ancillary_service_eligible'] = [True for x in dct['name']]
                dct['shape'] = ["flex_"+  x.upper() for x in dct['name']]
                df1 = pd.DataFrame(dct)
                df1 = df1[['name', 'capacity_zone','ancillary_service_eligible','shape']]
        else:
            df1 = None
        dct = dict()
        dct['name'] = [cfg.outputs_id_map['dispatch_feeder'][x] for x in self.supply.dispatch_feeders]
        dct['capacity_zone'] = ["bulk" for x in dct['name']]
        dct['ancillary_service_eligible'] = [True for x in dct['name']]
        dct['shape'] = ["flex_"+ x.upper() for x in dct['name']]
        df2 = pd.DataFrame(dct)
        df2 = df2[['name', 'capacity_zone','ancillary_service_eligible','shape']]
        df = pd.concat([df1,df2])
        Output.write_rio(df,"FLEX_TECH_MAIN"+'.csv',self.db_dir + "\\Technology Inputs\\Flex Load", index=False)




    def write_flex_tech_schedule(self):
        dist_losses, bulk_losses = self.flatten_loss_dicts()
        df = util.df_slice(self.flex_load_df,2,'timeshift_type')
        df = util.unit_convert(df.groupby(level=[x for x in df.index.names if x not in 'weather_datetime']).sum(),
                               unit_from_num=cfg.calculation_energy_unit,unit_to_num='megawatt_hour')
        df_list = []
        for geography in cfg.rio_feeder_geographies:
            for feeder in self.supply.dispatch_feeders:
                tech_df = util.df_slice(df,[feeder],['dispatch_feeder'])
                tech_df = util.df_slice(tech_df,[geography],cfg.supply_primary_geography,drop_level=False)
                tech_df['name'] = cfg.outputs_id_map[cfg.supply_primary_geography][geography].lower() + "_" + cfg.outputs_id_map['dispatch_feeder'][feeder]
                tech_df['source'] = None
                tech_df['notes'] = None
                tech_df['geography'] = cfg.supply_primary_geography
                #tech_df['gau'] = geography
                tech_df['geography_map_key'] = None
                tech_df['interpolation_method'] = 'linear_interpolation'
                tech_df['extrapolation_method'] = 'nearest'
                tech_df[tech_df.index.get_level_values('year').values == min(self.supply.years)]
                util.replace_index_name(tech_df, 'year', 'vintage')
                tech_df['sensitivity'] = self.supply.scenario.name
                df_list.append(copy.deepcopy(tech_df))
        for feeder in self.supply.dispatch_feeders:
            tech_df = util.DfOper.mult([util.df_slice(df, feeder, 'dispatch_feeder'),bulk_losses])
            tech_df[tech_df.index.get_level_values(cfg.supply_primary_geography).isin(cfg.rio_feeder_geographies)] = 0
            tech_df['name'] = cfg.outputs_id_map['dispatch_feeder'][feeder]
            tech_df['source'] = None
            tech_df['notes'] = None
            tech_df['geography'] = cfg.supply_primary_geography
            tech_df['geography_map_key'] = None
            tech_df['interpolation_method'] = 'linear_interpolation'
            tech_df['extrapolation_method'] = 'nearest'
            tech_df[tech_df.index.get_level_values('year').values == min(self.supply.years)]
            util.replace_index_name(tech_df, 'year','vintage')
            tech_df['sensitivity'] = self.supply.scenario.name
            df_list.append(tech_df)
        df = pd.concat(df_list)
        df = Output.clean_rio_df(df)
        df = df[['name','geography','gau','geography_map_key','interpolation_method','extrapolation_method','year','value','sensitivity']]
        Output.write_rio(df, "FLEX_TECH_SCHEDULE" + '.csv', self.db_dir + "\\Technology Inputs\\Flex Load", index=False)

    def write_flex_tech_shapes(self):
        df = copy.deepcopy(self.flex_load_df)
        for geography in cfg.rio_feeder_geographies:
            for feeder in self.supply.dispatch_feeders:
                tech_df = util.df_slice(df,[feeder],['dispatch_feeder'])
                tech_df = util.df_slice(tech_df,[geography],cfg.supply_primary_geography,drop_level=False)
                tech_df = util.DfOper.divi([tech_df, util.remove_df_levels(tech_df, ['weather_datetime',cfg.supply_primary_geography], 'sum')])
                #tech_df = tech_df.tz_localize(None, level='weather_datetime')
                tech_df['sensitivity'] = self.supply.scenario.name
                name = "flex_" + cfg.outputs_id_map[cfg.supply_primary_geography][geography].lower() + "_"+ cfg.outputs_id_map['dispatch_feeder'][feeder].lower()
                tech_df = Output.clean_rio_df(tech_df,add_geography=False)
                Output.write_rio(tech_df, name + ".csv",
                         self.db_dir + "\\ShapeData", index=False)
                self.meta_dict['name'].append(name)
                self.meta_dict['shape_type'].append( 'weather date')
                self.meta_dict['input_type'].append( 'intensity')
                self.meta_dict['shape_unit_type'].append('power')
                self.meta_dict['time_zone'].append(cfg.outputs_id_map['time zone'][int(cfg.cfgfile.get('case', 'dispatch_outputs_timezone_id'))])
                self.meta_dict['geography'].append(cfg.dispatch_geography)
                self.meta_dict['geography_map_key'].append(None)
                self.meta_dict['interpolation_method'].append('linear_interpolation')
                self.meta_dict['extrapolation_method'].append('nearest')
        for feeder in self.supply.dispatch_feeders:
            tech_df = util.df_slice(df, feeder, 'dispatch_feeder')
            tech_df = util.DfOper.divi([tech_df, util.remove_df_levels(tech_df, 'weather_datetime', 'sum')])
            # tech_df = tech_df.tz_localize(None, level='weather_datetime')
            tech_df['sensitivity'] = self.supply.scenario.name
            name = "flex_" + cfg.outputs_id_map['dispatch_feeder'][feeder].lower()
            tech_df = Output.clean_rio_df(tech_df, add_geography=False)
            Output.write_rio(tech_df, name + ".csv",
                             self.db_dir + "\\ShapeData", index=False)
            self.meta_dict['name'].append(name)
            self.meta_dict['shape_type'].append('weather date')
            self.meta_dict['input_type'].append('intensity')
            self.meta_dict['shape_unit_type'].append('power')
            self.meta_dict['time_zone'].append(
                cfg.outputs_id_map['time zone'][int(cfg.cfgfile.get('case', 'dispatch_outputs_timezone_id'))])
            self.meta_dict['geography'].append(cfg.dispatch_geography)
            self.meta_dict['geography_map_key'].append(None)
            self.meta_dict['interpolation_method'].append('linear_interpolation')
            self.meta_dict['extrapolation_method'].append('nearest')


    def write_flex_tech_p_max(self):
        df = util.remove_df_levels(util.df_slice(self.flex_load_df,2,'timeshift_type'),'weather_datetime')
        df_list = []
        for geography in cfg.rio_feeder_geographies:
            for feeder in self.supply.dispatch_feeders:
                tech_df = util.df_slice(df,[feeder],['dispatch_feeder'])
                tech_df = util.df_slice(tech_df,[geography],cfg.supply_primary_geography,drop_level=False)
                tech_df['value'] = 1
                tech_df['name'] = cfg.outputs_id_map[cfg.supply_primary_geography][geography].lower() + "_" + cfg.outputs_id_map['dispatch_feeder'][feeder]
                tech_df['source'] = None
                tech_df['notes'] = None
                df['unit'] = 'megawatt'
                tech_df['geography_map_key'] = None
                tech_df['interpolation_method'] = 'linear_interpolation'
                tech_df['extrapolation_method'] = 'nearest'
                tech_df[tech_df.index.get_level_values('year').values == min(self.supply.years)]
                util.replace_index_name(tech_df,'vintage','year')
                tech_df['sensitivity'] = self.supply.scenario.name
                df_list.append(copy.deepcopy(tech_df))
        for feeder in self.supply.dispatch_feeders:
            tech_df = util.df_slice(df,feeder,'dispatch_feeder')
            tech_df[tech_df.index.get_level_values(cfg.supply_primary_geography).isin(cfg.rio_feeder_geographies)]=0
            tech_df['value'] = 1
            tech_df['name'] = cfg.outputs_id_map['dispatch_feeder'][feeder]
            tech_df['source'] = None
            tech_df['notes'] = None
            tech_df['unit'] = 'megawatt'
            tech_df['geography_map_key'] = None
            tech_df['interpolation_method'] = 'linear_interpolation'
            tech_df['extrapolation_method'] = 'nearest'
            tech_df[tech_df.index.get_level_values('year').values == min(self.supply.years)]
            util.replace_index_name(tech_df,'vintage','year')
            tech_df['sensitivity'] = self.supply.scenario.name
            df_list.append(tech_df)
        df = pd.concat(df_list)
        df = Output.clean_rio_df(df)
        df = df[['name', 'source','notes','unit','geography','gau','geography_map_key','interpolation_method','extrapolation_method','vintage','value','sensitivity']]
        Output.write_rio(df, "FLEX_TECH_P_MAX" + '.csv', self.db_dir + "\\Technology Inputs\\Flex Load", index=False)

    def write_flex_tech_p_min(self):
        df = util.remove_df_levels(util.df_slice(self.flex_load_df, 2, 'timeshift_type'), 'weather_datetime')
        #todo make mins work
        df_list = []
        for geography in cfg.rio_feeder_geographies:
            for feeder in self.supply.dispatch_feeders:
                tech_df = util.df_slice(df,[feeder],['dispatch_feeder'])
                tech_df = util.df_slice(tech_df,[geography],cfg.supply_primary_geography,drop_level=False)
                tech_df['name'] = cfg.outputs_id_map[cfg.supply_primary_geography][geography].lower() + "_" + cfg.outputs_id_map['dispatch_feeder'][feeder]
                tech_df['source'] = None
                tech_df['notes'] = None
                tech_df['unit'] = 'megawatt'
                tech_df['geography_map_key'] = None
                tech_df['interpolation_method'] = 'linear_interpolation'
                tech_df['extrapolation_method'] = 'nearest'
                tech_df[tech_df.index.get_level_values('year').values == min(self.supply.years)]
                util.replace_index_name(tech_df, 'vintage', 'year')
                tech_df['sensitivity'] = self.supply.scenario.name
                df_list.append(copy.deepcopy(tech_df))
        for feeder in self.supply.dispatch_feeders:
            tech_df = util.df_slice(df, feeder, 'dispatch_feeder')
            tech_df[tech_df.index.get_level_values(cfg.supply_primary_geography).isin(cfg.rio_feeder_geographies)] = 0
            tech_df['name'] = cfg.outputs_id_map['dispatch_feeder'][feeder]
            tech_df['source'] = None
            tech_df['notes'] = None
            tech_df['unit'] = 'megawatt'
            tech_df['geography_map_key'] = None
            tech_df['interpolation_method'] = 'linear_interpolation'
            tech_df['extrapolation_method'] = 'nearest'
            tech_df[tech_df.index.get_level_values('year').values == min(self.supply.years)]
            util.replace_index_name(tech_df, 'vintage', 'year')
            tech_df['sensitivity'] = self.supply.scenario.name
            df_list.append(tech_df)
        df = pd.concat(df_list)
        df = Output.clean_rio_df(df)
        df = df[['name', 'source','notes','unit','geography','gau','geography_map_key','interpolation_method','extrapolation_method','vintage','value','sensitivity']]
        Output.write_rio(df, "FLEX_TECH_P_MIN" + '.csv', self.db_dir + "\\Technology Inputs\\Flex Load", index=False)

    def write_flex_tech_energy(self):
        df = util.df_slice(self.flex_load_df, 2, 'timeshift_type')
        df = df.groupby(level=[x for x in df.index.names if x not in ['weather_datetime']]).sum()
        df_list = []
        for geography in cfg.rio_feeder_geographies:
            for feeder in self.supply.dispatch_feeders:
                tech_df = util.df_slice(df,[feeder],['dispatch_feeder'])
                tech_df['value'] = 1
                tech_df = util.df_slice(tech_df,[geography],cfg.supply_primary_geography,drop_level=False)
                tech_df['name'] = cfg.outputs_id_map[cfg.supply_primary_geography][geography].lower() + "_" + cfg.outputs_id_map['dispatch_feeder'][feeder]
                tech_df['source'] = None
                tech_df['notes'] = None
                tech_df['unit'] = 'megawatt_hour'
                tech_df['geography_map_key'] = None
                tech_df['interpolation_method'] = 'linear_interpolation'
                tech_df['extrapolation_method'] = 'nearest'
                tech_df[tech_df.index.get_level_values('year').values == min(self.supply.years)]
                util.replace_index_name(tech_df, 'vintage', 'year')
                tech_df['sensitivity'] = self.supply.scenario.name
                df_list.append(copy.deepcopy(tech_df))
        for feeder in self.supply.dispatch_feeders:
            tech_df = util.df_slice(df, feeder, 'dispatch_feeder')
            tech_df['value'] = 1
            tech_df['name'] = cfg.outputs_id_map['dispatch_feeder'][feeder]
            tech_df['source'] = None
            tech_df['notes'] = None
            tech_df['unit'] = 'megawatt'
            tech_df['geography_map_key'] = None
            tech_df['interpolation_method'] = 'linear_interpolation'
            tech_df['extrapolation_method'] = 'nearest'
            tech_df[tech_df.index.get_level_values('year').values == min(self.supply.years)]
            util.replace_index_name(tech_df, 'vintage', 'year')
            tech_df['sensitivity'] = self.supply.scenario.name
            df_list.append(tech_df)
        df = pd.concat(df_list)
        df = Output.clean_rio_df(df)
        df = df[['name', 'source', 'notes', 'unit', 'geography', 'gau', 'geography_map_key', 'interpolation_method',
                 'extrapolation_method', 'vintage', 'value', 'sensitivity']]
        Output.write_rio(df, "FLEX_TECH_ENERGY" + '.csv', self.db_dir + "\\Technology Inputs\\Flex Load", index=False)






            



    def write_conversion(self):
        #self.write_conversion_main()
        self.write_conversion_capital_cost()
        self.write_conversion_fixed_om()
        self.write_conversion_variable_om()
        self.write_conversion_efficiency()
        self.write_conversion_schedule()

    def write_product(self):
       # self.write_product_main()
        self.write_product_emissions()
        self.write_product_cost()
        self.write_product_potential()

    def write_blend(self):
        self.determine_blends()
        self.write_blend_exo_demand()
        self.write_blend_inputs()

    def write_transmission(self):
        self.write_transmission_main()
        self.write_transmission_schedule()
        self.write_transmission_potential()
        self.write_transmission_hurdles()
        self.write_transmission_losses()

    def write_all_empty(self):
        self.write_blend_empty()
        self.write_conversions_empty()
        self.write_product_empty()
        self.write_new_gen_empty()
        self.write_existing_gen_empty()
        self.write_capacity_zones_empty()
        self.write_transmission_empty()
        self.write_flex_tech_empty()
        self.write_system_empty()
        self.write_potential_empty()



    def write_new_gen(self):
        self.write_new_tech_capacity_factor()
        self.write_new_tech_capital_cost()
        self.write_new_tech_duration()
        self.write_new_tech_efficiency()
        self.write_new_tech_fixed_om()
        self.write_new_tech_p_min()
        self.write_new_tech_ramp()
        self.write_new_tech_standard_unit()
        self.write_new_tech_variable_om()

    def write_transmission_main(self):
        line_list = list(set([tuple(sorted(list(ast.literal_eval(x)))) for x in self.supply.dispatch.transmission.list_transmission_lines]))
        line_names = [
            cfg.outputs_id_map[cfg.dispatch_geography][x[0]] + "_to_" + cfg.outputs_id_map[cfg.dispatch_geography][
                x[1]] for x in line_list]
        line_from_names = [cfg.outputs_id_map[cfg.dispatch_geography][x[0]]
                           for x in line_list]
        line_to_names = [cfg.outputs_id_map[cfg.dispatch_geography][x[1]]
                         for x in line_list]
        df = pd.DataFrame({'name': line_names, "gau_from": line_from_names, "gau_to": line_to_names})
        df = df[['name','gau_from','gau_to']]
        Output.write_rio(df,"TRANSMISSION_MAIN" + '.csv', self.db_dir + "\\Topography Inputs\\Transmission", index=False)
        self.line_list = line_list
        self.line_names = line_names
        self.line_from_names = line_from_names
        self.line_to_names = line_to_names

    def write_transmission_schedule(self):
        df_list = []
        if len(self.line_list):
            for line in self.line_list:
                df = util.df_slice(self.supply.dispatch.transmission.constraints.values,line,['geography_from','geography_to'])
                util.replace_index_name(df,'gau_to','geography_to')
                util.replace_index_name(df, 'gau_from', 'geography_from')
                df['flow_value'] = df['value']
                df['counterflow_value'] = util.df_slice(self.supply.dispatch.transmission.constraints.values,line,['geography_to','geography_from']).values
                df['unit'] = cfg.calculation_energy_unit
                df['time_unit'] = 'hour'
                df['interpolation_method'] = 'linear_interpolation'
                df['extrapolation_method'] = 'nearest'
                df['sensitivity'] = self.supply.scenario.name
                df['name'] = self.line_names[self.line_list.index(line)]
                df['geography'] = cfg.dispatch_geography
                df_list.append(df)
            df = pd.concat(df_list)
            df = Output.clean_rio_df(df)
            df = df[['name','unit','time_unit','interpolation_method','extrapolation_method','year','flow_value','counterflow_value','sensitivity']]
            Output.write_rio(df,
                         "TRANSMISSION_SCHEDULE" + '.csv', self.db_dir + "\\Topography Inputs\\Transmission", index=False)
        else:
            self.write_empty('TRANSMISSION_SCHEDULE',"\\Topography Inputs\\Transmission", ['name','unit','time_unit','interpolation_method','extrapolation_method','year','flow_value','counterflow_value','sensitivity'])

    def write_transmission_potential(self):
        df_list = []
        if len(self.line_list):
            for line in self.line_list:
                df = util.df_slice(self.supply.dispatch.transmission.constraints.values,line,['geography_from','geography_to']) * 0
                util.replace_index_name(df,'gau_to','geography_to')
                util.replace_index_name(df, 'gau_from', 'geography_from')
                df['unit'] = cfg.calculation_energy_unit
                df['time_unit'] = 'hour'
                df['interpolation_method'] = 'linear_interpolation'
                df['extrapolation_method'] = 'nearest'
                df['sensitivity'] = self.supply.scenario.name
                df['name'] = self.line_names[self.line_list.index(line)]
                df['type'] = 'cumulative'
                df['geography'] = cfg.dispatch_geography
                df_list.append(df)
            df = pd.concat(df_list)
            df = Output.clean_rio_df(df)
            df = df[['name', 'type','unit','time_unit','interpolation_method','extrapolation_method','year','value','sensitivity']]
            Output.write_rio(df,
                         "TRANSMISSION_POTENTIAL" + '.csv', self.db_dir + "\\Topography Inputs\\Transmission", index=False)
        else:
            self.write_empty('TRANSMISSION_POTENTIAL',"\\Topography Inputs\\Transmission",
                             ['name', 'unit', 'time_unit', 'interpolation_method', 'extrapolation_method', 'year', 'value', 'sensitivity'])

    def write_transmission_hurdles(self):
        df_list = []
        if len(self.line_list):
            for line in self.line_list:
                df = util.df_slice(self.supply.dispatch.transmission.hurdles.values, line,
                                   ['geography_from', 'geography_to'])
                util.replace_index_name(df, 'gau_to', 'geography_to')
                util.replace_index_name(df, 'gau_from', 'geography_from')
                df['flow_value'] = df['value']
                df['counterflow_value'] = util.df_slice(self.supply.dispatch.transmission.hurdles.values, line,
                                                        ['geography_to', 'geography_from']).values
                df['source'] = None
                df['notes'] = None
                df['unit'] = cfg.calculation_energy_unit
                df['currency'] = cfg.currency_name
                df['currency_year'] = cfg.cfgfile.get('case', 'currency_year_id')
                df['interpolation_method'] = 'linear_interpolation'
                df['extrapolation_method'] = 'nearest'
                df['sensitivity'] = self.supply.scenario.name
                df['name'] = self.line_names[self.line_list.index(line)]
                df_list.append(df)
            df = pd.concat(df_list)
            df = Output.clean_rio_df(df)
            df = df[['name', 'source','notes','currency','currency_year','unit','interpolation_method', 'extrapolation_method', 'year', 'flow_value',
                     'counterflow_value', 'sensitivity']]
            Output.write_rio(df,
                         "TRANSMISSION_HURDLE" + '.csv', self.db_dir + "\\Topography Inputs\\Transmission", index=False)
        else:
            self.write_empty('TRANSMISSION_HURDLE', "\\Topography Inputs\\Transmission",['name', 'source','notes','currency','currency_year','unit','interpolation_method', 'extrapolation_method', 'year', 'flow_value',
                 'counterflow_value', 'sensitivity'])

    def write_transmission_losses(self):
        df_list = []
        if len(self.line_list):
            for line in self.line_list:
                df = util.df_slice(self.supply.dispatch.transmission.hurdles.values, line,
                                   ['geography_from', 'geography_to'])
                util.replace_index_name(df, 'gau_to', 'geography_to')
                util.replace_index_name(df, 'gau_from', 'geography_from')
                df['source'] = None
                df['notes'] = None
                df['interpolation_method'] = 'linear_interpolation'
                df['extrapolation_method'] = 'nearest'
                df['sensitivity'] = self.supply.scenario.name
                df['name'] = self.line_names[self.line_list.index(line)]
                df['vintage'] = min(cfg.supply_years)
                df_list.append(df)
            df = pd.concat(df_list)
            df = Output.clean_rio_df(df)
            df = df[['name', 'source','notes','interpolation_method', 'extrapolation_method','vintage', 'year', 'value', 'sensitivity']]
            Output.write_rio(df,"TRANSMISSION_LOSSES" + '.csv', self.db_dir + "\\Topography Inputs\\Transmission", index=False)
        else:
            self.write_empty('TRANSMISSION_LOSSES',  "\\Topography Inputs\\Transmission",['name', 'source','notes','interpolation_method', 'extrapolation_method', 'year', 'value', 'sensitivity'])



    def write_existing_gen(self):
        include_dispatch_feeders = False
        df_list = []
        active_nodes = self.supply.nodes[self.supply.bulk_id].nodes + self.supply.nodes[self.supply.thermal_dispatch_node_id].nodes + self.supply.nodes[self.supply.distribution_node_id].nodes
        for node in active_nodes:
            if not isinstance(self.supply.nodes[node],BlendNode) and hasattr(self.supply.nodes[node],'technologies'):
                if self.supply.nodes[node].stock.technology.sum().sum() > 0 or len(self.supply.nodes[node].technologies)==1:
                    pass
                else:
                    print "No existing technologies in %s" % node
                    continue
                for gau in cfg.geo.geographies[cfg.supply_primary_geography]:
                    if hasattr(self.supply.nodes[node].case_stock, 'total') or hasattr(
                        self.supply.nodes[node].case_stock, 'technology'):
                        node_df = util.remove_df_levels(util.df_slice(self.supply.nodes[node].stock.values.loc[:,min(cfg.supply_years)].to_frame(),gau,cfg.supply_primary_geography),'demand_sector')
                        node_df = util.DfOper.add([util.remove_df_levels(util.df_slice(self.supply.nodes[node].stock.sales, gau, cfg.supply_primary_geography),
                                                        'demand_sector'),node_df])
                        node_df = node_df[node_df.index.get_level_values('vintage') > 1949]
                    elif self.supply.nodes[node].stock.technology.sum().sum() > 0 and hasattr(self.supply.nodes[node].stock,'extrapolation_method') and self.supply.nodes[node].stock.extrapolation_method != 'none' :
                        node_df = util.remove_df_levels(util.df_slice(self.supply.nodes[node].stock.technology,gau,cfg.supply_primary_geography),
                                                        'demand_sector')
                        node_df.replace(np.nan,0)
                        #node_df.iloc[:,1:] = node_df.iloc[:,1:].values - node_df.iloc[:,:-1].values
                        #node_df[node_df.values==np.nan] = util.df_slice(self.supply.nodes[node].stock.technology,gau,cfg.supply_primary_geography)
                        node_df = node_df.stack().to_frame()
                        util.replace_index_name(node_df,'vintage','year')
                        node_df.columns = ['value']
                    else:
                        node_df = util.remove_df_levels(util.df_slice(self.supply.nodes[node].stock.values.loc[:,min(cfg.supply_years)].to_frame(),gau,cfg.supply_primary_geography),'demand_sector')
                        node_df = node_df[node_df.index.get_level_values('vintage')<min(cfg.supply_years)]
                        node_df = node_df[node_df.index.get_level_values('vintage') > 1949]
                    for plant in node_df.groupby(level=node_df.index.names).groups.keys():
                        df = node_df.loc[plant]
                        tech_id = df.name[-2]
                        df_rows = self.calc_existing_gen_efficiency(gau,node,tech_id,plant)
                        if df_rows is None:
                            df_rows =  pd.DataFrame({'supply_node': [None], 'max_gen_efficiency':[0],'min_gen_efficiency':[0]})
                        #capacity weighting means we have to multiply the efficiency by the number of efficiency rows and divide the capacity by the number of efficiency rows
                        df_rows['max_gen_efficiency']*=  float(len(df_rows))
                        df_rows['min_gen_efficiency'] *= float(len(df_rows))
                        df_rows['capacity_unit'] = 'megawatt'
                        df_rows['capacity'] = util.unit_convert(df.values[0],unit_from_num=cfg.calculation_energy_unit,unit_to_num='megawatt_hour')/float(len(df_rows))
                        df_rows['standard_unit_size'] = df_rows['capacity']
                        df_rows['net_to_gross'] = 1
                        if len(plant) == 3:
                            name = "existing_" + cfg.outputs_id_map['supply_technology'][tech_id]  + "_" + str(plant[0])
                            df_rows['name'] = name
                        else:
                            name = "existing_" + cfg.outputs_id_map['supply_technology'][tech_id]
                            df_rows['name'] = name
                        if df_rows['capacity'].sum()>1:
                            pass
                        else:
                            continue
                        if isinstance(self.supply.nodes[node],StorageNode):
                            gen_type = 'storage'
                        elif self.supply.nodes[node].is_flexible==True and node in self.supply.nodes[self.supply.bulk_id].nodes:
                            gen_type  = 'hydro'
                        elif node in self.supply.nodes[self.supply.thermal_dispatch_node_id].nodes:
                            gen_type = 'thermal'
                        else:
                            gen_type = 'fixed'
                        df_rows['type'] = gen_type
                        df_rows['energy'] = df_rows['capacity'].values * self.supply.nodes[node].technologies[tech_id].duration.values.loc[(gau,plant[-1]),:].values if gen_type == 'storage' else np.nan
                        df_rows['energy_unit'] = 'megawatt_hour'
                        #we specify the lifetime as 1 and 'rebuild' the stock every year if it is specified.'
                        try:
                            if hasattr(self.supply.nodes[node].stock, 'extrapolation_method') and self.supply.nodes[
                                node].stock.extrapolation_method != 'none':
                                df_rows['lifetime'] = 1
                            else:
                                df_rows['lifetime'] = self.supply.nodes[node].technologies[tech_id].mean_lifetime
                        except:
                            pdb.set_trace()
                        df_rows['cost_of_capital'] = self.supply.nodes[node].technologies[tech_id].cost_of_capital -float(cfg.cfgfile.get('case', 'inflation_rate'))
                        df_rows['retirement_type'] = 'simple' if self.supply.nodes[node].stock.extrapolation_method!='none' else 'complex'
                        df_rows['use_retirement_year'] = False
                        if len(plant) == 3:
                            df_rows['potential_group_geo'] = cfg.outputs_id_map['supply_technology'][tech_id]  + "_" + str(plant[0])
                        else:
                            df_rows['potential_group_geo'] = None
                        df_rows['potential_group'] = None
                        df_rows['ancillary_service_eligible'] = True if gen_type=='hydro' or gen_type == 'thermal' else False
                        for node_row in df_rows['supply_node'].values:
                            df_rows['plant'] =  "_".join([str(x) for x in plant]) + "_" + str(node_row)
                        df_rows['capacity_zone'] = 'bulk'
                        if hasattr(self.supply.nodes[node].technologies[tech_id],'shape'):
                            df_rows['shape'] = self.supply.nodes[node].technologies[tech_id].shape.name
                        elif hasattr(self.supply.nodes[node],'shape') and self.supply.nodes[node].shape is not None:
                            df_rows['shape'] = self.supply.nodes[node].shape.name
                        else:
                            df_rows['shape'] = 'flat'
                        df_rows['net_for_binning'] = True if gen_type == 'hydro' else False
                        if  node in self.supply.nodes[self.supply.thermal_dispatch_node_id].nodes and self.supply.nodes[node].is_flexible==False:
                            df_rows['must_run'] = True
                        elif node in self.supply.nodes[self.supply.thermal_dispatch_node_id].nodes and self.supply.nodes[node].is_flexible==True:
                            df_rows['must_run'] = False
                        else:
                            df_rows['must_run'] = False
                        df_rows['geography'] = cfg.supply_primary_geography
                        df_rows['gau'] = cfg.outputs_id_map[cfg.supply_primary_geography][gau]
                        df_rows['generation_p_min'] = 0
                        df_rows['generation_p_max'] = 1
                        df_rows['load_p_min'] = 0 if gen_type == 'storage' else np.nan
                        df_rows['load_p_max'] = 1 if gen_type == 'storage' else np.nan
                        df_rows['ramp_rate'] = 1
                        df_rows['ramp_rate_time_unit'] = 'minute'
                        df_rows['unit_in'] = cfg.calculation_energy_unit
                        df_rows['unit_out'] = cfg.calculation_energy_unit
                        df_rows['output_numerator'] = False
                        df_rows['currency'] = cfg.currency_name
                        df_rows['currency_year'] = cfg.cfgfile.get('case', 'currency_year_id')
                        if hasattr(self.supply.nodes[node].technologies[tech_id].variable_om,'values'):
                            df_rows['variable_om'] = util.unit_convert(self.supply.nodes[node].technologies[tech_id].variable_om.values.loc[gau,plant[-1]][0],unit_from_den=cfg.calculation_energy_unit,unit_to_num='megawatt_hour')
                        else:
                            df_rows['variable_om'] = 0
                        df_rows['variable_om_unit'] = cfg.calculation_energy_unit
                        if hasattr(self.supply.nodes[node].technologies[tech_id].fixed_om,'values'):
                            try:
                                if 'resource_bin' in self.supply.nodes[node].technologies[tech_id].fixed_om.values.index.names:
                                    indexer = (gau,)+plant[0:1]+plant[2:3]
                                else:
                                    indexer = (gau,) + (plant[-1],)
                                df_rows['fixed_om'] = util.unit_convert(self.supply.nodes[node].technologies[tech_id].fixed_om.values.loc[indexer][0],unit_from_den=cfg.calculation_energy_unit,unit_to_den='megawatt_hour')
                            except:
                                pdb.set_trace()
                        else:
                             df_rows['fixed_om'] = 0
                        df_rows['fixed_om_unit'] = 'megawatt'
                        df_rows['allow_long_term_charging'] = False
                        df_rows['capacity_factor'] = util.remove_df_levels(self.supply.nodes[node].stock.capacity_factor_rio,'demand_sector',agg_function='mean').loc[(gau,) + plant].max()
                        df_rows['operating_year'] = plant[-1]
                        df_rows['retirement_year'] = df_rows['operating_year'] + df_rows['lifetime']
                        df_rows['shutdown_cost_unit'] = 'megawatt'
                        df_rows['shutdown_cost'] = 0
                        df_rows['startup_cost_unit'] = 'megawatt'
                        df_rows['startup_cost'] = 0
                        df_rows['curtailment_cost_unit'] = 'megawatt_hour'
                        df_rows['curtailment_cost'] = 0
                        df_rows['ptc_end_year'] = 2100
                        df_rows['ptc_unit'] = 'megawatt_hour'
                        df_rows['ptc'] = 0
                        df_list.append(df_rows)
        df = pd.concat(df_list)
        df['supply_node'] = [x if x not in [self.supply.bulk_node_id, self.supply.distribution_node_id] else 'electricity' for x in df['supply_node'].values]
        df = Output.clean_rio_df(df,add_geography=False,replace_gau=False)
        df['blend_in'] = df['supply_node']
        df = df[['name','type','lifetime','cost_of_capital','retirement_type','use_retirement_year','potential_group','potential_group_geo', 'ancillary_service_eligible','plant', 'capacity_zone','shape',\
                 'net_for_binning', 'must_run','allow_long_term_charging','geography','gau','capacity_unit','capacity','standard_unit_size','net_to_gross','energy_unit','energy',\
                 'generation_p_min','generation_p_max',
                            'load_p_min','load_p_max','ramp_rate', 'ramp_rate_time_unit','unit_in','unit_out','blend_in',\
                            'output_numerator','min_gen_efficiency','max_gen_efficiency','capacity_factor','operating_year','retirement_year', 'currency','currency_year',
                            'variable_om_unit','variable_om','shutdown_cost_unit','shutdown_cost', 'startup_cost_unit','startup_cost', 'fixed_om_unit','fixed_om', 'curtailment_cost_unit','curtailment_cost','ptc_end_year', 'ptc_unit','ptc']]
        Output.write_rio(df, "EXISTING_TECH_MAIN" + '.csv', self.db_dir + "\\Technology Inputs\\Generation\\Existing Generation", index=False)

    def write_potential_group(self):
        df_list = []
        active_nodes = self.supply.nodes[self.supply.bulk_id].nodes + self.supply.nodes[self.supply.distribution_node_id].nodes
        for node in active_nodes:
            if hasattr(self.supply.nodes[node],'potential'):
                pass
            else:
                continue
            if hasattr(self.supply.nodes[node].potential,'values'):
                df = util.DfOper.divi([self.supply.nodes[node].potential.values,
                                       self.supply.nodes[node].stock.capacity_factor_rio.groupby(level=[x for x in self.supply.nodes[node].stock.capacity_factor_rio.index.names if x not in ['vintage']]).max().loc[:,self.supply.nodes[node].potential.values.columns]*8760])
                df = df.stack().to_frame()
                util.replace_index_name(df,'year')
                df.columns = ['value']
                df['incremental_to_existing'] = False
                df['source'] = None
                df['notes'] = None
                df['unit'] = cfg.calculation_energy_unit
                df['time_unit'] = 'hour'
                df['geography'] = cfg.supply_primary_geography
                df['geography_map_key'] = None
                df['interpolation_method'] = 'linear_interpolation'
                df['extrapolation_method'] = 'nearest'
                df['extrapolation_growth_rate'] = None
                df['sensitivity'] = self.supply.scenario.name
                df['name'] = [a + "_" + b for a,b  in zip([cfg.outputs_id_map['supply_technology'][x] for x in df.index.get_level_values('supply_technology').values], [str(x) for x in df.index.get_level_values('resource_bin').values])]
                df_list.append(df)
        df = pd.concat(df_list)
        df = Output.clean_rio_df(df)
        df = df[['name','incremental_to_existing','source','notes','unit','time_unit','geography','gau','geography_map_key','interpolation_method','extrapolation_method','extrapolation_growth_rate','year','value','sensitivity']]
        Output.write_rio(df, "POTENTIAL_GROUP_GEO" + '.csv', self.db_dir + "\\Technology Inputs\\Generation", index=False)

    def write_new_tech_capacity_factor(self):
        df_list = []
        active_nodes = self.supply.nodes[self.supply.bulk_id].nodes + self.supply.nodes[
            self.supply.thermal_dispatch_node_id].nodes + self.supply.nodes[self.supply.distribution_node_id].nodes
        for node in active_nodes:
            if not isinstance(self.supply.nodes[node], BlendNode) and hasattr(self.supply.nodes[node], 'technologies'):
                sales_df = copy.deepcopy(self.supply.nodes[node].stock.sales)
                node_df = copy.deepcopy(self.supply.nodes[node].stock.capacity_factor_rio).max(axis=1).to_frame()
                node_df.columns = ['value']
                node_df = node_df[node_df.index.get_level_values('vintage') >= min(cfg.supply_years)]
                plant_index = [x for x in sales_df.index.names if x not in [cfg.supply_primary_geography,'vintage']]
                for plant in sales_df.groupby(level=plant_index).groups.keys():
                    plant = util.ensure_iterable_and_not_string(plant)
                    df = util.df_slice(node_df,plant,plant_index)
                    if len(util.ensure_iterable_and_not_string(plant)) == 2:
                        name = cfg.outputs_id_map['supply_technology'][plant[-1]] + "_" + str(plant[0])
                    else:
                        name = cfg.outputs_id_map['supply_technology'][plant[-1]]
                    df['name'] = name
                    df['source'] = None
                    df['notes'] = None
                    df['geography_map_key'] = None
                    df['interpolation_method'] = 'linear_interpolation'
                    df['extrapolation_method'] = 'nearest'
                    df['extrapolation_growth_rate'] = None
                    df['sensitivity'] = self.supply.scenario.name
                    df_list.append(df)
        df = pd.concat(df_list)
        df = Output.clean_rio_df(df)
        df = df[
            ['name', 'source','notes','geography','gau','geography_map_key','interpolation_method','extrapolation_method','extrapolation_growth_rate',\
             'vintage','value','sensitivity']]
        Output.write_rio(df, "NEW_TECH_CAPACITY_FACTOR" + '.csv', self.db_dir + "\\Technology Inputs\\Generation\\New Generation", index=False)

    def write_new_tech_capital_cost(self):
        cap_df = self.write_new_tech_capital_cost_capacity()
        energy_df = self.write_new_tech_capital_cost_energy()
        df = pd.concat([cap_df,energy_df])
        df = df[
            ['name', 'source','notes', 'construction_time','lifetime','cycle_life','currency','currency_year','cost_type','lifecycle','unit','time_unit','geography','gau','geography_map_key',\
             'interpolation_method','extrapolation_method','extrapolation_growth_rate',\
             'cost_of_capital','levelized','vintage','value','sensitivity']]
        Output.write_rio(df, "NEW_TECH_CAPITAL_COST" + '.csv', self.db_dir + "\\Technology Inputs\\Generation\\New Generation", index=False)

    def write_new_tech_capital_cost_capacity(self):
        df_list = []
        active_nodes =  self.supply.nodes[self.supply.bulk_id].nodes + self.supply.nodes[self.supply.thermal_dispatch_node_id].nodes + self.supply.nodes[self.supply.distribution_node_id].nodes
        for node in active_nodes:
            if not isinstance(self.supply.nodes[node], BlendNode) and hasattr(self.supply.nodes[node], 'technologies'):
                sales_df = copy.deepcopy(self.supply.nodes[node].stock.sales)
                plant_index = [x for x in sales_df.index.names if x not in [cfg.supply_primary_geography,'vintage']]
                for plant in sales_df.groupby(level=plant_index).groups.keys():
                    plant = util.ensure_iterable_and_not_string(plant)
                    tech_id = plant[-1]
                    if isinstance(self.supply.nodes[node], StorageNode):
                        cap_cost_df = self.supply.nodes[node].technologies[tech_id].capital_cost_new_capacity.values if hasattr(
                            self.supply.nodes[node].technologies[tech_id].capital_cost_new_capacity, 'values') else None
                    else:
                        cap_cost_df = self.supply.nodes[node].technologies[tech_id].capital_cost_new.values if hasattr(self.supply.nodes[node].technologies[tech_id].capital_cost_new,'values') else None
                    installation_cost_df = self.supply.nodes[node].technologies[tech_id].installation_cost_new.values if hasattr(
                            self.supply.nodes[node].technologies[tech_id].installation_cost_new, 'values') else None
                    node_df =  util.DfOper.add([cap_cost_df,\
                                                installation_cost_df])
                    if node_df is None:
                        node_df = sales_df *0
                    node_df = node_df[node_df.index.get_level_values('vintage') >= min(cfg.supply_years)]
                    df = util.df_slice(node_df,plant,plant_index)
                    if len(util.ensure_iterable_and_not_string(plant)) == 2:
                        name = cfg.outputs_id_map['supply_technology'][tech_id] + "_" + str(plant[0])
                    else:
                        name = cfg.outputs_id_map['supply_technology'][tech_id]
                    df['name'] = name
                    df['source'] = None
                    df['notes'] = None
                    df['construction_time'] = 1
                    df['lifetime'] = self.supply.nodes[node].technologies[tech_id].mean_lifetime
                    df['cycle_life'] = 0
                    df['unit'] = cfg.calculation_energy_unit
                    df['time_unit'] = 'hour'
                    df['currency'] = cfg.currency_name
                    df['currency_year'] = cfg.cfgfile.get('case', 'currency_year_id')
                    df['cost_type'] = 'capacity'
                    df['lifecycle'] = 'new'
                    df['cost_of_capital'] = self.supply.nodes[node].technologies[tech_id].cost_of_capital -float(cfg.cfgfile.get('case', 'inflation_rate'))
                    df['levelized'] = False
                    df['geography_map_key'] = None
                    df['interpolation_method'] = 'linear_interpolation'
                    df['extrapolation_method'] = 'nearest'
                    df['extrapolation_growth_rate'] = None
                    df['sensitivity'] = self.supply.scenario.name
                    df_list.append(df)
        df = pd.concat(df_list)
        df = Output.clean_rio_df(df)
        df = df[
            ['name', 'source','notes', 'construction_time','lifetime','cycle_life','currency','currency_year','cost_type','lifecycle','unit','time_unit','geography','gau','geography_map_key',\
             'interpolation_method','extrapolation_method','extrapolation_growth_rate',\
             'cost_of_capital','levelized','vintage','value','sensitivity']]
        return df

    def write_new_tech_capital_cost_energy(self):
        df_list = []
        active_nodes = self.supply.nodes[self.supply.bulk_id].nodes  + self.supply.nodes[self.supply.distribution_node_id].nodes
        for node in active_nodes:
            if isinstance(self.supply.nodes[node], StorageNode):
                sales_df = copy.deepcopy(self.supply.nodes[node].stock.sales)
                plant_index = [x for x in sales_df.index.names if x not in [cfg.supply_primary_geography,'vintage']]
                for plant in sales_df.groupby(level=plant_index).groups.keys():
                    plant = util.ensure_iterable_and_not_string(plant)
                    tech_id = plant[-1]
                    node_df = self.supply.nodes[node].technologies[tech_id].capital_cost_new_energy.values if hasattr(
                            self.supply.nodes[node].technologies[tech_id].capital_cost_new_energy, 'values') else None
                    if node_df is None:
                        continue
                    node_df = node_df[node_df.index.get_level_values('vintage') >= min(cfg.supply_years)]
                    df = util.df_slice(node_df,plant,plant_index)
                    if len(util.ensure_iterable_and_not_string(plant)) == 2:
                        name = cfg.outputs_id_map['supply_technology'][tech_id] + "_" + str(plant[0])
                    else:
                        name = cfg.outputs_id_map['supply_technology'][tech_id]
                    df['name'] = name
                    df['source'] = None
                    df['notes'] = None
                    df['construction_time'] = 1
                    df['lifetime'] = self.supply.nodes[node].technologies[tech_id].mean_lifetime
                    df['cycle_life'] = 0
                    df['unit'] = cfg.calculation_energy_unit
                    df['time_unit'] = 'hour'
                    df['currency'] = cfg.currency_name
                    df['currency_year'] = cfg.cfgfile.get('case', 'currency_year_id')
                    df['cost_type'] = 'energy'
                    df['lifecycle'] = 'new'
                    df['cost_of_capital'] = self.supply.nodes[node].technologies[tech_id].cost_of_capital -float(cfg.cfgfile.get('case', 'inflation_rate'))
                    df['levelized'] = False
                    df['geography_map_key'] = None
                    df['interpolation_method'] = 'linear_interpolation'
                    df['extrapolation_method'] = 'nearest'
                    df['extrapolation_growth_rate'] = None
                    df['sensitivity'] = self.supply.scenario.name
                    df_list.append(df)
        df = pd.concat(df_list)
        df = Output.clean_rio_df(df)
        df = df[
            ['name', 'source','notes', 'construction_time','lifetime','cycle_life','currency','currency_year','cost_type','lifecycle','unit','time_unit','geography','gau','geography_map_key',\
             'interpolation_method','extrapolation_method','extrapolation_growth_rate',\
             'cost_of_capital','levelized','vintage','value','sensitivity']]

        return df

    def write_new_tech_duration(self):
        df_list = []
        active_nodes = self.supply.nodes[self.supply.bulk_id].nodes  + self.supply.nodes[self.supply.distribution_node_id].nodes
        for node in active_nodes:
            if isinstance(self.supply.nodes[node], StorageNode):
                sales_df = copy.deepcopy(self.supply.nodes[node].stock.sales)
                plant_index = [x for x in sales_df.index.names if x not in [cfg.supply_primary_geography,'vintage']]
                for plant in sales_df.groupby(level=plant_index).groups.keys():
                    plant = util.ensure_iterable_and_not_string(plant)
                    tech_id = plant[-1]
                    df = util.df_slice(sales_df,plant,plant_index)
                    df['value'] = self.supply.nodes[node].technologies[tech_id].discharge_duration
                    name = cfg.outputs_id_map['supply_technology'][tech_id]
                    df['name'] = name
                    df['source'] = None
                    df['notes'] = None
                    df['time_unit'] = 'hour'
                    df['geography_map_key'] = None
                    df['interpolation_method'] = 'linear_interpolation'
                    df['extrapolation_method'] = 'nearest'
                    df['sensitivity'] = self.supply.scenario.name
                    df_list.append(df)
        df = pd.concat(df_list)
        df = Output.clean_rio_df(df)
        df = df[
            ['name', 'source','notes','geography','gau','time_unit','geography_map_key',\
             'interpolation_method','extrapolation_method','vintage', 'value','sensitivity']]
        Output.write_rio(df, "NEW_TECH_DURATION" + '.csv', self.db_dir + "\\Technology Inputs\\Generation\\New Generation", index=False)

    def write_new_tech_standard_unit(self):
        df_list = []
        active_nodes = self.supply.nodes[self.supply.thermal_dispatch_node_id].nodes
        for node in active_nodes:
            sales_df = copy.deepcopy(self.supply.nodes[node].stock.sales)
            plant_index = [x for x in sales_df.index.names if x not in [cfg.supply_primary_geography,'vintage']]
            for plant in sales_df.groupby(level=plant_index).groups.keys():
                plant = util.ensure_iterable_and_not_string(plant)
                tech_id = plant[-1]
                df = util.df_slice(sales_df,plant,plant_index)
                df['value'] = 100
                name = cfg.outputs_id_map['supply_technology'][tech_id]
                df['name'] = name
                df['source'] = None
                df['notes'] = None
                df['unit'] = cfg.calculation_energy_unit
                df['time_unit'] = 'hour'
                df['geography_map_key'] = None
                df['interpolation_method'] = 'linear_interpolation'
                df['extrapolation_method'] = 'nearest'
                df['sensitivity'] = self.supply.scenario.name
                df_list.append(df)
        df = pd.concat(df_list)
        df = Output.clean_rio_df(df)
        df = df[
            ['name', 'source','notes','unit','time_unit','geography','gau', 'geography_map_key',\
             'interpolation_method','extrapolation_method','vintage','value','sensitivity']]
        Output.write_rio(df, "NEW_TECH_STANDARD_UNIT" + '.csv', self.db_dir + "\\Technology Inputs\\Generation\\New Generation", index=False)

    def write_new_tech_ramp(self):
        df_list = []
        active_nodes = self.supply.nodes[self.supply.thermal_dispatch_node_id].nodes +  self.supply.nodes[self.supply.bulk_id].nodes  + self.supply.nodes[self.supply.distribution_node_id].nodes
        for node in active_nodes:
            if not isinstance(self.supply.nodes[node],BlendNode) and hasattr(self.supply.nodes[node],'technologies'):
                sales_df = copy.deepcopy(self.supply.nodes[node].stock.sales)
                plant_index = [x for x in sales_df.index.names if x not in [cfg.supply_primary_geography,'vintage']]
                for plant in sales_df.groupby(level=plant_index).groups.keys():
                    plant = util.ensure_iterable_and_not_string(plant)
                    tech_id = plant[-1]
                    df = util.df_slice(sales_df,plant,plant_index)
                    df['value'] = 1
                    name = cfg.outputs_id_map['supply_technology'][tech_id]
                    df['name'] = name
                    df['source'] = None
                    df['notes'] = None
                    df['time_unit'] = 'minute'
                    df['geography_map_key'] = None
                    df['interpolation_method'] = 'linear_interpolation'
                    df['extrapolation_method'] = 'nearest'
                    df['sensitivity'] = self.supply.scenario.name
                    df_list.append(df)
        df = pd.concat(df_list)
        df = Output.clean_rio_df(df)
        df = df[
            ['name', 'source','notes','time_unit','geography','gau','geography_map_key',\
             'interpolation_method','extrapolation_method','vintage','value','sensitivity']]
        Output.write_rio(df, "NEW_TECH_RAMP" + '.csv', self.db_dir + "\\Technology Inputs\\Generation\\New Generation", index=False)

    def write_new_tech_p_min(self):
        gen_df = self.write_new_tech_generation_p_min()
        load_df = self.write_new_tech_load_p_min()
        df = pd.concat([gen_df,load_df])
        Output.write_rio(df, "NEW_TECH_P_MIN" + '.csv', self.db_dir + "\\Technology Inputs\\Generation\\New Generation", index=False)



    def write_new_tech_generation_p_min(self):
        df_list = []
        active_nodes = self.supply.nodes[self.supply.bulk_id].nodes + self.supply.nodes[self.supply.thermal_dispatch_node_id].nodes + self.supply.nodes[self.supply.distribution_node_id].nodes
        for node in active_nodes:
            if not isinstance(self.supply.nodes[node], BlendNode) and hasattr(self.supply.nodes[node], 'technologies'):
                sales_df = copy.deepcopy(self.supply.nodes[node].stock.sales)
                plant_index = [x for x in sales_df.index.names if x not in [cfg.supply_primary_geography,'vintage']]
                for plant in sales_df.groupby(level=plant_index).groups.keys():
                    plant = util.ensure_iterable_and_not_string(plant)
                    tech_id = plant[-1]
                    node_df = sales_df[sales_df.index.get_level_values('vintage') >= min(cfg.supply_years)]
                    df = util.df_slice(node_df, plant, plant_index)
                    if len(util.ensure_iterable_and_not_string(plant)) == 2:
                        name = cfg.outputs_id_map['supply_technology'][tech_id] + "_" + str(plant[0])
                    else:
                        name = cfg.outputs_id_map['supply_technology'][tech_id]
                    df['value'] = 0
                    df['name'] = name
                    df['source'] = None
                    df['notes'] = None
                    df['type'] = 'generation'
                    df['geography_map_key'] = None
                    df['interpolation_method'] = 'linear_interpolation'
                    df['extrapolation_method'] = 'nearest'
                    df['sensitivity'] = self.supply.scenario.name
                    df_list.append(df)
        df = pd.concat(df_list)
        df = Output.clean_rio_df(df)
        df = df[
            ['name', 'source','notes', 'type','geography','gau','geography_map_key',\
             'interpolation_method','extrapolation_method','vintage','value','sensitivity']]
        return df

    def write_new_tech_main(self):
        df_list = []
        active_nodes = self.supply.nodes[self.supply.bulk_id].nodes + self.supply.nodes[
            self.supply.thermal_dispatch_node_id].nodes + self.supply.nodes[self.supply.distribution_node_id].nodes
        for node in active_nodes:
            if not isinstance(self.supply.nodes[node], BlendNode) and hasattr(self.supply.nodes[node], 'technologies'):
                sales_df = copy.deepcopy(self.supply.nodes[node].stock.sales)
                #if 'demand_sector' in sales_df.index.names:
                 #   self.write_new_tech_main_local(sales_df,df_list,node)
                #else:
                self.write_new_tech_main_bulk(sales_df,df_list,node)
        df = pd.concat(df_list)
        df = Output.clean_rio_df(df)
        df = df[['name',  'potential_group','potential_group_geo','retirement_type','is_active','type','allow_long_term_charging','capacity_zone','must_run','ancillary_service_eligible','net_for_binning','shape']]
        Output.write_rio(df, "NEW_TECH_MAIN" + '.csv', self.db_dir + "\\Technology Inputs\\Generation\\New Generation", index=False)

    def write_new_tech_main_bulk(self,sales_df,df_list,node):
        plant_index = [x for x in sales_df.index.names if
                       x not in [cfg.supply_primary_geography, 'vintage', 'demand_sector']]
        for plant in sales_df.groupby(level=plant_index).groups.keys():
            plant = util.ensure_iterable_and_not_string(plant)
            tech_id = plant[-1]
            dct = {}
            if len(plant) == 2:
                name = cfg.outputs_id_map['supply_technology'][tech_id] + "_" + str(plant[0])
            else:
                name = cfg.outputs_id_map['supply_technology'][tech_id]
            dct['name'] = [name]
            if len(plant) == 2:
                dct['potential_group_geo'] = [name]
            else:
                dct['potential_group_geo'] = [None]
            dct['potential_group'] = [None]
            dct['retirement_type'] = ['simple']
            dct['is_active'] = [True]
            if isinstance(self.supply.nodes[node], StorageNode):
                gen_type = 'storage'
            elif self.supply.nodes[node].is_flexible == True and node in self.supply.nodes[
                self.supply.bulk_id].nodes:
                gen_type = 'hydro'
            elif node in self.supply.nodes[
                self.supply.thermal_dispatch_node_id].nodes:
                gen_type = 'thermal'
            else:
                gen_type = 'fixed'
            dct['type'] = [gen_type]
            dct['allow_long_term_charging'] = False
            dct['capacity_zone'] = 'bulk'
            if node in self.supply.nodes[self.supply.thermal_dispatch_node_id].nodes and self.supply.nodes[
                node].is_flexible == False:
                dct['must_run'] = [True]
            elif node in self.supply.nodes[self.supply.thermal_dispatch_node_id].nodes and self.supply.nodes[
                node].is_flexible == True:
                dct['must_run'] = [False]
            else:
                dct['must_run'] = [False]
            if gen_type is not 'fixed':
                dct['ancillary_service_eligible'] = [True]
            else:
                dct['ancillary_service_eligible'] = [False]
            dct['net_for_binning'] = [False]
            if hasattr(self.supply.nodes[node].technologies[tech_id], 'shape'):
                dct['shape'] = self.supply.nodes[node].technologies[tech_id].shape.name
            elif hasattr(self.supply.nodes[node], 'shape') and self.supply.nodes[
                node].shape is not None:
                dct['shape'] = [self.supply.nodes[node].shape.name]
            else:
                dct['shape'] = ['flat']
            df_list.append(pd.DataFrame(dct))

    def write_new_tech_main_local(self,sales_df,df_list,node):
        plant_index = [x for x in sales_df.index.names if
                       x not in [cfg.supply_primary_geography, 'vintage']]
        for plant in sales_df.groupby(level=plant_index).groups.keys():
            plant = util.ensure_iterable_and_not_string(plant)
            tech_id = plant[-1]
            dct = {}
            try:
                name = cfg.outputs_id_map['supply_technology'][tech_id] + "_" + cfg.outputs_id_map['demand_sector'][int(plant[0])]
            except:
                pdb.set_trace()
            dct['name'] = [name]
            dct['potential_group_geo'] = [None]
            dct['potential_group'] = [None]
            dct['retirement_type'] = ['simple']
            dct['is_active'] = [True]
            if isinstance(self.supply.nodes[node], StorageNode):
                gen_type = 'storage'
            elif self.supply.nodes[node].is_flexible == True and node in self.supply.nodes[
                self.supply.bulk_id].nodes:
                gen_type = 'hydro'
            elif node in self.supply.nodes[
                self.supply.thermal_dispatch_node_id].nodes:
                gen_type = 'thermal'
            else:
                gen_type = 'fixed'
            dct['type'] = [gen_type]
            dct['allow_long_term_charging'] = False
            dct['capacity_zone'] = 'bulk'
            if node in self.supply.nodes[self.supply.thermal_dispatch_node_id].nodes and self.supply.nodes[
                node].is_flexible == False:
                dct['must_run'] = [True]
            elif node in self.supply.nodes[self.supply.thermal_dispatch_node_id].nodes and self.supply.nodes[
                node].is_flexible == True:
                dct['must_run'] = [False]
            else:
                dct['must_run'] = [False]
            if gen_type is not 'fixed':
                dct['ancillary_service_eligible'] = [True]
            else:
                dct['ancillary_service_eligible'] = [False]
            dct['net_for_binning'] = [False]
            if hasattr(self.supply.nodes[node].technologies[tech_id], 'shape'):
                dct['shape'] = self.supply.nodes[node].technologies[tech_id].shape.name
            elif hasattr(self.supply.nodes[node], 'shape') and self.supply.nodes[
                node].shape is not None:
                dct['shape'] = [self.supply.nodes[node].shape.name]
            else:
                dct['shape'] = ['flat']
            df_list.append(pd.DataFrame(dct))
            for geography in cfg.rio_feeder_geographies:
                plant = util.ensure_iterable_and_not_string(plant)
                tech_id = plant[-1]
                dct = {}
                name = cfg.outputs_id_map[cfg.supply_primary_geography][geography] + "_"+ cfg.outputs_id_map['supply_technology'][tech_id] + "_" + cfg.outputs_id_map['demand_sector'][int(plant[0])]
                dct['name'] = [name]
                dct['potential_group_geo'] = [None]
                dct['potential_group'] = [None]
                dct['retirement_type'] = ['simple']
                dct['is_active'] = [True]
                if isinstance(self.supply.nodes[node], StorageNode):
                    gen_type = 'storage'
                elif self.supply.nodes[node].is_flexible == True and node in self.supply.nodes[
                    self.supply.bulk_id].nodes:
                    gen_type = 'hydro'
                elif node in self.supply.nodes[
                    self.supply.thermal_dispatch_node_id].nodes:
                    gen_type = 'thermal'
                else:
                    gen_type = 'fixed'
                dct['type'] = [gen_type]
                dct['capacity_zone'] = cfg.outputs_id_map[cfg.supply_primary_geography][geography] + "_" + cfg.outputs_id_map['demand_sector'][int(plant[0])]
                dct['allow_long_term_charging'] = False
                if node in self.supply.nodes[self.supply.thermal_dispatch_node_id].nodes and self.supply.nodes[
                    node].is_flexible == False:
                    dct['must_run'] = [True]
                elif node in self.supply.nodes[self.supply.thermal_dispatch_node_id].nodes and self.supply.nodes[
                    node].is_flexible == True:
                    dct['must_run'] = [False]
                else:
                    dct['must_run'] = [False]
                if gen_type is not 'fixed':
                    dct['ancillary_service_eligible'] = [True]
                else:
                    dct['ancillary_service_eligible'] = [False]
                dct['net_for_binning'] = [False]
                if hasattr(self.supply.nodes[node].technologies[tech_id], 'shape'):
                    dct['shape'] = self.supply.nodes[node].technologies[tech_id].shape.name
                elif hasattr(self.supply.nodes[node], 'shape') and self.supply.nodes[
                    node].shape is not None:
                    dct['shape'] = [self.supply.nodes[node].shape.name]
                else:
                    dct['shape'] = ['flat']
                df_list.append(pd.DataFrame(dct))


    def write_new_tech_load_p_min(self):
        df_list = []
        active_nodes = self.supply.nodes[self.supply.bulk_id].nodes  + self.supply.nodes[self.supply.distribution_node_id].nodes
        for node in active_nodes:
            if isinstance(self.supply.nodes[node],StorageNode):
                sales_df = copy.deepcopy(self.supply.nodes[node].stock.sales)
                plant_index = [x for x in sales_df.index.names if x not in [cfg.supply_primary_geography,'vintage']]
                for plant in sales_df.groupby(level=plant_index).groups.keys():
                    plant = util.ensure_iterable_and_not_string(plant)
                    tech_id = plant[-1]
                    node_df = sales_df[sales_df.index.get_level_values('vintage') >= min(cfg.supply_years)]
                    df = util.df_slice(node_df, plant, plant_index)
                    if len(util.ensure_iterable_and_not_string(plant)) == 2:
                        name = cfg.outputs_id_map['supply_technology'][tech_id] + "_" + str(plant[0])
                    else:
                        name = cfg.outputs_id_map['supply_technology'][tech_id]
                    df['value'] = 0
                    df['name'] = name
                    df['source'] = None
                    df['notes'] = None
                    df['type'] = 'load'
                    df['geography_map_key'] = None
                    df['interpolation_method'] = 'linear_interpolation'
                    df['extrapolation_method'] = 'nearest'
                    df['sensitivity'] = self.supply.scenario.name
                    df_list.append(df)
        df = pd.concat(df_list)
        df = Output.clean_rio_df(df)
        df = df[
            ['name', 'source','notes', 'type','geography','gau','geography_map_key',\
             'interpolation_method','extrapolation_method','vintage', 'value','sensitivity']]
        return df

    def write_new_tech_capital_cost_capacity(self):
        df_list = []
        active_nodes = self.supply.nodes[self.supply.bulk_id].nodes + self.supply.nodes[self.supply.thermal_dispatch_node_id].nodes + self.supply.nodes[self.supply.distribution_node_id].nodes
        for node in active_nodes:
            if not isinstance(self.supply.nodes[node], BlendNode) and hasattr(self.supply.nodes[node], 'technologies'):
                sales_df = copy.deepcopy(self.supply.nodes[node].stock.sales)
                plant_index = [x for x in sales_df.index.names if x not in [cfg.supply_primary_geography,'vintage']]
                for plant in sales_df.groupby(level=plant_index).groups.keys():
                    plant = util.ensure_iterable_and_not_string(plant)
                    tech_id = plant[-1]
                    if isinstance(self.supply.nodes[node], StorageNode):
                        cap_cost_df = self.supply.nodes[node].technologies[tech_id].capital_cost_new_capacity.values if hasattr(
                            self.supply.nodes[node].technologies[tech_id].capital_cost_new_capacity, 'values') else None
                    else:
                        cap_cost_df = self.supply.nodes[node].technologies[tech_id].capital_cost_new.values if hasattr(self.supply.nodes[node].technologies[tech_id].capital_cost_new,'values') else None
                    installation_cost_df = self.supply.nodes[node].technologies[tech_id].installation_cost_new.values if hasattr(
                            self.supply.nodes[node].technologies[tech_id].installation_cost_new, 'values') else None
                    node_df =  util.DfOper.add([cap_cost_df,\
                                                installation_cost_df])
                    if node_df is None:
                        continue
                    node_df = node_df[node_df.index.get_level_values('vintage') >= min(cfg.supply_years)]
                    df = util.df_slice(node_df,plant,plant_index)
                    if len(util.ensure_iterable_and_not_string(plant)) == 2:
                        name = cfg.outputs_id_map['supply_technology'][tech_id] + "_" + str(plant[0])
                    else:
                        name = cfg.outputs_id_map['supply_technology'][tech_id]
                    df['name'] = name
                    df['source'] = None
                    df['notes'] = None
                    df['construction_time'] = 1
                    df['lifetime'] = self.supply.nodes[node].technologies[tech_id].mean_lifetime
                    df['unit'] = cfg.calculation_energy_unit
                    df['time_unit'] = 'hour'
                    df['currency'] = cfg.currency_name
                    df['currency_year'] = cfg.cfgfile.get('case', 'currency_year_id')
                    df['cost_type'] = 'capacity'
                    df['lifecycle'] = 'new'
                    df['cost_of_capital'] = self.supply.nodes[node].technologies[tech_id].cost_of_capital-float(cfg.cfgfile.get('case', 'inflation_rate'))
                    df['levelized'] = False
                    df['geography_map_key'] = None
                    df['interpolation_method'] = 'linear_interpolation'
                    df['extrapolation_method'] = 'nearest'
                    df['extrapolation_growth_rate'] = None
                    df['sensitivity'] = self.supply.scenario.name
                    df_list.append(df)
        df = pd.concat(df_list)
        df = Output.clean_rio_df(df)
        df = df[
            ['name', 'source','notes', 'construction_time','lifetime','currency','currency_year','cost_type','lifecycle','unit','time_unit','geography','gau','geography_map_key',\
             'interpolation_method','extrapolation_method','extrapolation_growth_rate',\
             'cost_of_capital','levelized','vintage','value','sensitivity']]
        return df


    def write_new_tech_fixed_om(self):
        df_list = []
        active_nodes = self.supply.nodes[self.supply.bulk_id].nodes + self.supply.nodes[self.supply.thermal_dispatch_node_id].nodes + self.supply.nodes[self.supply.distribution_node_id].nodes
        for node in active_nodes:
            if not isinstance(self.supply.nodes[node], BlendNode) and hasattr(self.supply.nodes[node], 'technologies'):
                sales_df = copy.deepcopy(self.supply.nodes[node].stock.sales)
                plant_index = [x for x in sales_df.index.names if x not in [cfg.supply_primary_geography,'vintage']]
                for plant in sales_df.groupby(level=plant_index).groups.keys():
                    plant = util.ensure_iterable_and_not_string(plant)
                    tech_id = plant[-1]
                    node_df = self.supply.nodes[node].technologies[tech_id].fixed_om.values_level if hasattr(self.supply.nodes[node].technologies[tech_id].fixed_om,'values_level') else None
                    if node_df is not None:
                        node_df = util.unit_convert(node_df,unit_from_den=cfg.calculation_energy_unit,unit_to_den='megawatt_hour')
                    else:
                        continue
                    node_df = node_df.stack().to_frame()
                    node_df.columns = ['value']
                    util.replace_index_name(node_df,'year')
                    node_df = node_df[node_df.index.get_level_values('vintage').values == node_df.index.get_level_values('year').values]
                    node_df = node_df[node_df.index.get_level_values('vintage') >= min(cfg.supply_years)]
                    df = util.df_slice(node_df,plant,plant_index)
                    if len(util.ensure_iterable_and_not_string(plant)) == 2:
                        name = cfg.outputs_id_map['supply_technology'][tech_id] + "_" + str(plant[0])
                    else:
                        name = cfg.outputs_id_map['supply_technology'][tech_id]
                    df['name'] = name
                    df['source'] = None
                    df['notes'] = None
                    df['unit'] = 'megawatt'
                    df['currency'] = cfg.currency_name
                    df['currency_year'] = cfg.cfgfile.get('case', 'currency_year_id')
                    df['geography_map_key'] = None
                    df['interpolation_method'] = 'linear_interpolation'
                    df['extrapolation_method'] = 'nearest'
                    df['sensitivity'] = self.supply.scenario.name
                    df_list.append(df)
        df = pd.concat(df_list)
        df = Output.clean_rio_df(df)
        df = df[
            ['name', 'source','notes', 'currency','currency_year','unit','geography','gau','geography_map_key',\
             'interpolation_method','extrapolation_method',\
             'vintage','value','sensitivity']]
        Output.write_rio(df, "NEW_TECH_FIXED_OM" + '.csv', self.db_dir + "\\Technology Inputs\\Generation\\New Generation", index=False)

    def write_new_tech_variable_om(self):
        df_list = []
        active_nodes = self.supply.nodes[self.supply.bulk_id].nodes + self.supply.nodes[self.supply.thermal_dispatch_node_id].nodes + self.supply.nodes[self.supply.distribution_node_id].nodes
        for node in active_nodes:
            if not isinstance(self.supply.nodes[node], BlendNode) and hasattr(self.supply.nodes[node], 'technologies'):
                sales_df = copy.deepcopy(self.supply.nodes[node].stock.sales)
                plant_index = [x for x in sales_df.index.names if x not in [cfg.supply_primary_geography,'vintage']]
                for plant in sales_df.groupby(level=plant_index).groups.keys():
                    plant = util.ensure_iterable_and_not_string(plant)
                    tech_id = plant[-1]
                    node_df = self.supply.nodes[node].technologies[tech_id].variable_om.values_level if hasattr(
                        self.supply.nodes[node].technologies[tech_id].variable_om, 'values_level') else None
                    if node_df is not None:
                        node_df = util.unit_convert(node_df,unit_from_den=cfg.calculation_energy_unit,unit_to_den='megawatt_hour')
                    else:
                        continue
                    node_df = node_df.stack().to_frame()
                    util.replace_index_name(node_df,'year')
                    node_df.columns = ['value']
                    node_df['age'] = node_df.index.get_level_values('year').values - node_df.index.get_level_values('vintage').values
                    if node_df is None:
                        continue
                    node_df = node_df[node_df.index.get_level_values('vintage') >= min(cfg.supply_years)]
                    node_df = node_df[node_df['age']==0]
                    df = util.df_slice(node_df,plant,plant_index)
                    if len(util.ensure_iterable_and_not_string(plant)) == 2:
                        name = cfg.outputs_id_map['supply_technology'][tech_id] + "_" + str(plant[0])
                    else:
                        name = cfg.outputs_id_map['supply_technology'][tech_id]
                    df['name'] = name
                    df['source'] = None
                    df['notes'] = None
                    df['unit'] = 'megawatt_hour'
                    df['currency'] = cfg.currency_name
                    df['currency_year'] = cfg.cfgfile.get('case', 'currency_year_id')
                    df['geography_map_key'] = None
                    df['interpolation_method'] = 'linear_interpolation'
                    df['extrapolation_method'] = 'nearest'
                    df['sensitivity'] = self.supply.scenario.name
                    df_list.append(df)
        df = pd.concat(df_list)
        df = Output.clean_rio_df(df)
        df = df[
            ['name', 'source','notes', 'currency','currency_year','unit','geography','gau','geography_map_key',\
             'interpolation_method','extrapolation_method',\
             'vintage','age','value','sensitivity']]
        Output.write_rio(df, "NEW_TECH_VARIABLE_OM" + '.csv', self.db_dir + "\\Technology Inputs\\Generation\\New Generation", index=False)



    def calc_existing_gen_efficiency(self,gau,node,technology,plant):
        if len(plant) == 3:
            resource_bin = plant[0]
            vintage = plant[-1]
        elif len(plant) == 2:
            vintage = plant[-1]
        if hasattr(self.supply.nodes[node].technologies[technology].efficiency,'values') and'resource_bin' in self.supply.nodes[node].technologies[technology].efficiency.values.index.names:
            if gau not in self.supply.nodes[node].technologies[technology].efficiency.values.index.get_level_values(
                    cfg.supply_primary_geography).values:
                eff_df = util.remove_df_levels(util.df_slice(self.supply.nodes[node].technologies[technology].efficiency.values,[resource_bin,vintage],['resource_bin','vintage']),cfg.supply_primary_geography,agg_function='mean')
            else:
                eff_df = util.df_slice(self.supply.nodes[node].technologies[technology].efficiency.values,[resource_bin,vintage,gau],['resource_bin','vintage',cfg.supply_primary_geography])
        elif hasattr(self.supply.nodes[node].technologies[technology].efficiency,'values'):
            if gau not in self.supply.nodes[node].technologies[technology].efficiency.values.index.get_level_values(
                    cfg.supply_primary_geography).values:
                eff_df = util.remove_df_levels(util.df_slice(self.supply.nodes[node].technologies[technology].efficiency.values,[vintage],['vintage']),cfg.supply_primary_geography,agg_function='mean')
            else:
                eff_df = util.df_slice(self.supply.nodes[node].technologies[technology].efficiency.values,[vintage,gau],['vintage',cfg.supply_primary_geography])
        else:
            return None
        eff_df = util.remove_df_levels(eff_df,['supply_technology','efficiency_type'])
        eff_df = eff_df.stack().to_frame()
        eff_df.columns = ['value']
        util.replace_index_name(eff_df, 'year')
        eff_df = eff_df[vintage == eff_df.index.get_level_values('year')]
        eff_df = util.remove_df_levels(eff_df, 'year')
        if len(eff_df) == 0:
            return None
        idx = pd.IndexSlice
        if np.any([x in eff_df.index.get_level_values('supply_node').values for x in self.supply.blend_nodes]):
            blend_nodes = [x for x in eff_df.index.get_level_values('supply_node').values if x in self.supply.blend_nodes]
            eff_blend_df = eff_df.loc[idx[blend_nodes], :]
        else:
            eff_blend_df = None
        if eff_blend_df is not None:
            eff_blend_df['max_gen_efficiency'] = eff_blend_df['value']
            eff_blend_df['min_gen_efficiency'] = eff_blend_df['value']
            eff_blend_df = eff_blend_df.drop(axis=1,labels='value')
            eff_blend_df = eff_blend_df.dropna()
            eff_blend_df = eff_blend_df.reset_index()
        eff_del = None
        for delivery_node in set(eff_df.index.get_level_values('supply_node')):
            if self.supply.nodes[delivery_node].supply_type == 'Delivery':
                temp_df = eff_df.loc[delivery_node,:]
                eff_del = util.df_slice(self.supply.nodes[delivery_node].coefficients.values,gau,cfg.supply_primary_geography).groupby(
                    level=['demand_sector',
                           'supply_node']).sum().groupby(
                    level=['supply_node']).mean()
                eff_del = eff_del.mean(axis=1).to_frame()
                util.replace_index_name(eff_del,'year')
                eff_del.columns = ['value']
                eff_del = eff_del.loc[idx[self.supply.blend_nodes], :]
                eff_del = eff_del.dropna()
        if eff_del is not None and len (eff_del)>0:
            eff_del = temp_df *eff_del
            eff_del = util.remove_df_levels(eff_del,'efficiency_type')
            eff_del['max_gen_efficiency'] = eff_del['value']
            eff_del['min_gen_efficiency'] = eff_del['value']
            eff_del = eff_del.drop(axis=1,labels='value')
            eff_del = eff_del.reset_index()
        else:
            eff_del = None
        try:
            if eff_blend_df is None and eff_del is None:
                return None
            else:
                return pd.concat([eff_blend_df,eff_del])
        except:
            pdb.set_trace()


    def calc_new_gen_efficiency(self,node,technology,plant,plant_index):
        if hasattr(self.supply.nodes[node].technologies[technology].efficiency,'values'):
            eff_df = util.df_slice(self.supply.nodes[node].technologies[technology].efficiency.values,plant,plant_index)
            eff_df = util.remove_df_levels(eff_df,['supply_technology','efficiency_type'])
            eff_df = eff_df.stack().to_frame()
            eff_df.columns = ['value']
            util.replace_index_name(eff_df, 'year')
            eff_df = eff_df[eff_df.index.get_level_values('vintage') == eff_df.index.get_level_values('year')]
            eff_df = util.remove_df_levels(eff_df, 'year')
            if len(eff_df) == 0:
                return None
            idx = pd.IndexSlice
            #if np.any(self.supply.blend_nodes in eff_df.index.get_level_values('supply_node').values):
            eff_blend_df = eff_df.loc[idx[:,self.supply.blend_nodes,:], :]
            if eff_blend_df is not None and len(eff_blend_df)>0:
                eff_blend_df['max_gen_value'] = eff_blend_df['value']
                eff_blend_df['min_gen_value'] = eff_blend_df['value']
                eff_blend_df.drop(axis=1,labels='value')
                eff_blend_df = eff_blend_df.dropna()
            else:
                eff_blend_df = None
            eff_del = None
            eff_del_list = []
            for delivery_node in set(eff_df.index.get_level_values('supply_node')):
                if self.supply.nodes[delivery_node].supply_type == 'Delivery':
                    temp_df = util.remove_df_levels(eff_df.loc[idx[:, delivery_node], :],'supply_node')
                    eff_del = self.supply.nodes[delivery_node].coefficients.values.groupby(
                        level=[cfg.supply_primary_geography, 'demand_sector',
                               'supply_node']).sum().groupby(
                        level=[cfg.supply_primary_geography, 'supply_node']).mean()
                    eff_del = eff_del.mean(axis=1).to_frame()
                    util.replace_index_name(eff_del,'year')
                    eff_del.columns = ['value']
                    eff_del = eff_del.loc[idx[:,self.supply.blend_nodes], :]
                    eff_del = eff_del.dropna()
                    if len(eff_del) >0:
                        eff_del_list.append(util.remove_df_levels(util.DfOper.mult([eff_del,temp_df]),'efficiency_type'))
        else:
            return None
        if len(eff_del_list):
            eff_del = pd.concat(eff_del_list)
            eff_del['max_gen_value'] = eff_del['value']
            eff_del['min_gen_value'] = eff_del['value']
            eff_del.drop(axis=1,labels='value')
        else:
            eff_del = None
        return util.DfOper.add([eff_blend_df,eff_del])

    def write_new_tech_efficiency(self):
        df_list = []
        active_nodes = self.supply.nodes[self.supply.bulk_id].nodes + self.supply.nodes[self.supply.thermal_dispatch_node_id].nodes + self.supply.nodes[self.supply.distribution_node_id].nodes
        for node in active_nodes:
            if not isinstance(self.supply.nodes[node], BlendNode) and hasattr(self.supply.nodes[node], 'technologies'):
                sales_df = copy.deepcopy(self.supply.nodes[node].stock.sales)
                plant_index = [x for x in sales_df.index.names if x not in [cfg.supply_primary_geography,'vintage']]
                for plant in sales_df.groupby(level=plant_index).groups.keys():
                    plant = util.ensure_iterable_and_not_string(plant)
                    tech_id = plant[-1]
                    df = self.calc_new_gen_efficiency(node, tech_id,plant,plant_index)
                    if df is None:
                        continue
                    df = df[df.index.get_level_values('vintage')>= min(cfg.supply_years)]
                    if len(util.ensure_iterable_and_not_string(plant)) == 2:
                        name = cfg.outputs_id_map['supply_technology'][tech_id] + "_" + str(plant[0])
                    else:
                        name = cfg.outputs_id_map['supply_technology'][tech_id]
                    df['name'] = name
                    df['source'] = None
                    df['notes'] = None
                    df['interpolation_method'] = 'linear_interpolation'
                    df['extrapolation_method'] = 'nearest'
                    df['output_numerator'] = False
                    df['unit_in'] = cfg.calculation_energy_unit
                    df['unit_out'] = cfg.calculation_energy_unit
                    df['sensitivity'] = self.supply.scenario.name
                    df_list.append(df)
        df = pd.concat(df_list)
        df = df.reset_index('supply_node')
        df['supply_node'] = [x if x not in [self.supply.bulk_node_id,self.supply.distribution_node_id] else 'electricity' for x in df['supply_node'].values]
        df = Output.clean_rio_df(df)
        df['blend_in'] = df['supply_node']

        cfg.outputs_id_map['supply_node'][self.supply.distribution_node_id] = 'electricity'

        df = df[
            ['name', 'source','notes', 'geography','gau',\
             'interpolation_method','extrapolation_method',\
             'output_numerator','unit_in','unit_out','blend_in','vintage','max_gen_value', 'min_gen_value','sensitivity']]
        Output.write_rio(df, "NEW_TECH_EFFICIENCY" + '.csv', self.db_dir + "\\Technology Inputs\\Generation\\New Generation", index=False)







                    
                    
            
        
  
        
        
    

    def write_topography(self):
        #self.write_capacity_zone_main()
        self.write_capacity_zone_load()
        self.write_bulk_capacity_zone_losses()


    def determine_blends(self):
        blend_node_subset = [x for x in self.supply.blend_nodes if x not in [self.supply.bulk_id,
                                                                             self.supply.thermal_dispatch_node_id,
                                                                             self.supply.distribution_node_id]]
        blend_node_inputs = list(set(util.flatten_list([self.supply.nodes[x].nodes for x in blend_node_subset])))
        self.redundant_blend_nodes = [x for x in blend_node_subset if x in blend_node_inputs]
        self.blend_node_subset = [x for x in blend_node_subset if x not in blend_node_inputs]
        try:
            self.blend_node_subset = [x for x in self.blend_node_subset if self.input_compatibility_check(self.supply.nodes[x].nodes)]
        except:
            pdb.set_trace()
        self.blend_node_subset_names = [self.supply.nodes[x].name.upper() for x in self.blend_node_subset]
        self.blend_node_subset_lookup = dict(zip(self.blend_node_subset,self.blend_node_subset_names))
        self.blend_node_inputs = list(set(util.flatten_list([self.supply.nodes[x].nodes for x in self.blend_node_subset])))

    def write_blend_main(self):
        df = pd.DataFrame(self.blend_node_subset_names)
        df['exceed_demand'] = True
        #df['enforce_geography'] = [False if self.supply.nodes[x].tradable_geography!= cfg.supply_primary_geography else True for x in self.blend_node_subset]
        df['enforce_zonal_constraints'] = False
        df['enforce_storage_constraints'] = False
        df.columns = ['name', 'enforce_zonal_constraints','exceed_demand','enforce_storage_constraints']
        Output.write_rio(df, "BLEND_MAIN" + '.csv', self.db_dir+'\\Fuel Inputs\\Blends', index=False)


    def input_compatibility_check(self,nodes):
        for node in nodes:
            if isinstance(self.supply.nodes[node],SupplyStockNode):
                return True
            elif isinstance(self.supply.nodes[node],ImportNode):
                return True
            elif isinstance(self.supply.nodes[node],PrimaryNode):
                return True
            else:
                continue


    def write_blend_exo_demand(self):
        self.supply.calculate_rio_blend_demand()
        idx = pd.IndexSlice
        df = self.supply.io_rio_supply_df.loc[idx[:, self.blend_node_subset], :]
        df = df.stack().to_frame()
        util.replace_index_name(df, 'year')
        df.columns = ['value']
        #todo
        df[df.values<=0] = 0
        df = Output.clean_rio_df(df)
        util.replace_column_name(df, 'name', 'supply_node')
        df['unit'] = cfg.calculation_energy_unit
        df['interpolation_method'] = 'linear_interpolation'
        df['extrapolation_method'] = 'nearest'
        df['sensitivity'] = self.supply.scenario.name
        try:
            df = df[['name', 'unit', 'geography', 'gau',
                     'interpolation_method', 'extrapolation_method',
                     'year', 'value', 'sensitivity']]
        except:
            pdb.set_trace()
        Output.write_rio(df, "BLEND_EXO_DEMAND" + '.csv', self.db_dir+'\\Fuel Inputs\\Blends', index=False)

    def write_blend_inputs(self):
        blend_list = []
        fuel_list = []
        for blend in self.blend_node_subset:
            for node in self.supply.nodes[blend].nodes:
                if self.supply.nodes[node].supply_type == 'Primary' or self.supply.nodes[node].supply_type == 'Import':
                    if self.supply.nodes[node].potential.raw_values is not None:
                        for resource_bin in set(
                                self.supply.nodes[node].potential.raw_values.index.get_level_values('resource_bin')):
                            blend_list.append(cfg.outputs_id_map['supply_node'][blend])
                            fuel_list.append(cfg.outputs_id_map['supply_node'][node] + "_" + str(resource_bin))
                    else:
                        blend_list.append(cfg.outputs_id_map['supply_node'][blend])
                        fuel_list.append(cfg.outputs_id_map['supply_node'][node])
                elif self.supply.nodes[node].supply_type == 'Conversion':
                    if self.supply.nodes[node].potential.raw_values is not None:
                        for technology in self.supply.nodes[node].technologies.keys():
                            for resource_bin in set(self.supply.nodes[node].potential.raw_values.index.get_level_values(
                                    'resource_bin')):
                                blend_list.append(cfg.outputs_id_map['supply_node'][blend])
                                fuel_list.append(cfg.outputs_id_map['supply_node'][node] + "_" +
                                                 cfg.outputs_id_map['supply_technology'][technology] + "_" + str(
                                    resource_bin)+ "_" + self.blend_node_subset_lookup[blend])
                    else:
                        for technology in self.supply.nodes[node].technologies.keys():
                            blend_list.append(cfg.outputs_id_map['supply_node'][blend])
                            fuel_list.append(
                                cfg.outputs_id_map['supply_node'][node] + "_" + cfg.outputs_id_map['supply_technology'][
                                    technology]+ "_" + self.blend_node_subset_lookup[blend])
        df = pd.DataFrame(zip(blend_list, fuel_list), columns=['name', 'fuel'])
        df['geography'] = 'global'
        df['gau'] = 'all'
        df['interpolation_method'] = 'linear_interpolation'
        df['extrapolation_method'] = 'nearest'
        df['year'] = min(cfg.supply_years)
        df['value'] = 1
        df['sensitivity'] = self.supply.scenario.name
        df = df[['name', 'geography', 'gau', 'interpolation_method', 'extrapolation_method', 'year', 'fuel', 'value',
                 'sensitivity']]
        Output.write_rio(df, "BLEND_FUEL_INPUTS" + '.csv', self.db_dir + '\\Fuel Inputs\\Blends' , index=False)

    def write_blend_empty(self):
        self.write_empty('BLEND_CAPITAL_COST','\\Fuel Inputs\\Blends',['name','source','notes','currency','currency_year','unit','geography','gau','geography_map_key',\
                                               'interpolation_method','extrapolation_method','extrapolation_growth_rate','lifetime','cost_of_capital',\
                                               'levelized','vintage','value','sensitivity'])
        self.write_empty('BLEND_STORAGE_SCHEDULE','\\Fuel Inputs\\Blends',['name','source','notes','unit','geography','gau','geography_map_key',\
                                               'interpolation_method','extrapolation_method','extrapolation_growth_rate','year','value','sensitivity'])
    def write_conversions_empty(self):
        self.write_empty('CONVERSION_RPS','\\Fuel Inputs\\Conversions',['name','type','geography','gau','geography_map_key',\
                                               'interpolation_method','extrapolation_method','vintage','year','value','sensitivity'])
        self.write_empty('CONVERSION_POTENTIAL', '\\Fuel Inputs\\Conversions', ['name', 'type', 'unit','time_unit','geography', 'gau', 'geography_map_key', \
                                                                          'interpolation_method', 'extrapolation_method',  'year', 'value', 'sensitivity'])

    def write_product_empty(self):
        self.write_empty('PRODUCT_RPS','\\Fuel Inputs\\Products',['name','geography','gau','geography_map_key',\
                                               'interpolation_method','extrapolation_method','exponential_growth_rate','year','value','sensitivity'])

    def write_system_empty(self):
        self.write_empty('BINNING_WEIGHT','\\System Inputs',['name','shape','binning_group','geography','gau','geography_map_key',\
                                               'interpolation_method','extrapolation_method','year','value','sensitivity'])
        self.write_empty('EMISSIONS_CONSTRAINT','\\System Inputs',['name','source','notes','geography','gau','unit',\
                                               'interpolation_method','extrapolation_method','geography_map_key','year','value','sensitivity'])
        self.write_empty('OPERATING_RESERVES_CONSTRAINT','\\System Inputs',['name','geography','type','gau','unit',\
                                               'interpolation_method','extrapolation_method','geography_map_key','year','value','sensitivity'])
        self.write_empty('CAPACITY_RESERVES_CONSTRAINT','\\System Inputs',['name','geography','gau','unit',\
                                               'interpolation_method','extrapolation_method','geography_map_key','year','value','sensitivity'])
        self.write_empty('RPS_BINNING','\\System Inputs',['name','geography','gau','geography_map_key'\
                                               'interpolation_method','extrapolation_method','year','value','sensitivity'])
        self.write_empty('RPS_CONSTRAINT','\\System Inputs',['name','geography','gau','geography_map_key',\
                                               'interpolation_method','extrapolation_method','year','value','sensitivity'])
    def write_flex_tech_empty(self):
        self.write_empty('FLEX_TECH_CAPITAL_COST','\\Technology Inputs\\Flex Load',['name','source','notes','lifetime','currency','currency_year','geography','gau',\
                                               'geography_map_key','interpolation_method','extrapolation_method','cost_of_capital','levelized','vintage','value','sensitivity'])
        self.write_empty('FLEX_TECH_FIXED_OM','\\Technology Inputs\\Flex Load',['name','source','notes','currency','currency_year','geography','gau',\
                                               'geography_map_key','interpolation_method','extrapolation_method','vintage','value','sensitivity'])
        self.write_empty('FLEX_TECH_POTENTIAL','\\Technology Inputs\\Flex Load',['name','type','unit','time_unit','geography','gau',\
                                               'geography_map_key','interpolation_method','extrapolation_method','year','value','sensitivity'])

        self.write_empty('FLEX_TECH_SHIFT','\\Technology Inputs\\Flex Load',['name','type','source','notes','unit','geography','gau',\
                                               'geography_map_key','interpolation_method','extrapolation_method','vintage','value','sensitivity'])
        self.write_empty('FLEX_TECH_P_MIN','\\Technology Inputs\\Flex Load',['name','source','notes','unit','geography','gau',\
                                               'geography_map_key','interpolation_method','extrapolation_method','vintage','value','sensitivity'])
        self.write_empty('FLEX_TECH_P_MAX','\\Technology Inputs\\Flex Load',['name','source','notes','unit','geography','gau',\
                                               'geography_map_key','interpolation_method','extrapolation_method','vintage','value','sensitivity'])
        self.write_empty('FLEX_TECH_VARIABLE_OM','\\Technology Inputs\\Flex Load',['name','source','notes','currency','currency_year','unit','geography','gau',\
                                               'geography_map_key','interpolation_method','extrapolation_method','vintage','age','value','sensitivity'])

    def write_existing_gen_empty(self):
        self.write_empty('EXISTING_TECH_CAPITAL_COST','\\Technology Inputs\\Generation\\Existing Generation',['name','source','notes','currency','currency_year','cost_type','lifecycle','lifetime','unit','time_unit','geography','gau',\
                                               'geography_map_key','interpolation_method','extrapolation_method','cost_of_capital','levelized','vintage','value','sensitivity'])

        self.write_empty('EXISTING_TECH_DEPENDABILITY','\\Technology Inputs\\Generation\\Existing Generation',['name','source','notes','geography','gau',\
                                               'geography_map_key','interpolation_method','extrapolation_method','year','value','sensitivity'])
        self.write_empty('EXISTING_TECH_ITC','\\Technology Inputs\\Generation\\Existing Generation',['name','source','notes','currency','currency_year','unit','input_type','geography','gau',\
                                               'geography_map_key','interpolation_method','extrapolation_method','vintage','value','sensitivity'])
        self.write_empty('EXISTING_TECH_RPS','\\Technology Inputs\\Generation\\Existing Generation',['name','source','notes','load_modifier','geography','gau',\
                                               'geography_map_key','interpolation_method','extrapolation_method','vintage','year','value','sensitivity'])
        self.write_empty('EXISTING_TECH_OPERATING_RESERVE_REQUIREMENT','\\Technology Inputs\\Generation\\Existing Generation',['name','source','notes','geography','gau',\
                                               'geography_map_key','interpolation_method','extrapolation_method','year','value','sensitivity'])

    def write_new_gen_empty(self):
        self.write_empty('NEW_TECH_CURTAILMENT_COST','\\Technology Inputs\\Generation\\New Generation',['name','currency','currency_year','geography','gau',\
                                               'geography_map_key','interpolation_method','extrapolation_method','unit','vintage','year','value','sensitivity'])
        self.write_empty('NEW_TECH_PTC','\\Technology Inputs\\Generation\\New Generation',['name','currency','currency_year','unit','geography','gau',\
                                               'geography_map_key','interpolation_method','extrapolation_method','vintage','age','value','sensitivity'])
        self.write_empty('NEW_TECH_POTENTIAL','\\Technology Inputs\\Generation\\New Generation',['name','type','unit','time_unit','geography','gau','geography_map_key','interpolation_method',\
                         'extrapolation_method','year','value','sensitivity'])
        self.write_empty('NEW_TECH_DEPENDABILITY','\\Technology Inputs\\Generation\\New Generation',['name','source','notes','geography','gau',\
                                               'geography_map_key','interpolation_method','extrapolation_method','vintage','year','value','sensitivity'])
        self.write_empty('NEW_TECH_ITC', '\\Technology Inputs\\Generation\\New Generation', ['name', 'source', 'notes', 'currency', 'currency_year', 'unit', 'input_type', 'geography', 'gau', \
                                                                                                       'geography_map_key', 'interpolation_method', 'extrapolation_method', 'vintage', 'value',
                                                                                                       'sensitivity'])
        self.write_empty('NEW_TECH_RPS','\\Technology Inputs\\Generation\\New Generation',['name','source','notes','load_modifier','geography','gau',\
                                               'geography_map_key','interpolation_method','extrapolation_method','vintage','year','value','sensitivity'])
        self.write_empty('NEW_TECH_SCHEDULE','\\Technology Inputs\\Generation\\New Generation',['name','type','unit','time_unit','geography','gau',\
                                               'geography_map_key','interpolation_method','extrapolation_method','year','value','sensitivity'])
        self.write_empty('NEW_TECH_SHUTDOWN_COST','\\Technology Inputs\\Generation\\New Generation',['name','source','notes','currency','currency_year','unit','geography','gau',\
                                               'geography_map_key','interpolation_method','extrapolation_method','vintage','value','sensitivity'])
        self.write_empty('NEW_TECH_STARTUP_COST','\\Technology Inputs\\Generation\\New Generation',['name','source','notes','currency','currency_year','unit','geography','gau',\
                                               'geography_map_key','interpolation_method','extrapolation_method','vintage','value','sensitivity'])
        self.write_empty('NEW_TECH_TX_COST','\\Technology Inputs\\Generation\\New Generation',['name','source','notes','lifetime','currency','currency_year','unit','time_unit','geography','gau',\
                                               'geography_map_key','interpolation_method','extrapolation_method','cost_of_capital','levelized','vintage','value','sensitivity'])
        self.write_empty('NEW_TECH_OPERATING_RESERVE_REQUIREMENT','\\Technology Inputs\\Generation\\New Generation',['name','source','notes','geography','gau',\
                                               'geography_map_key','interpolation_method','extrapolation_method','vintage','year','value','sensitivity'])





    def write_transmission_empty(self):
        self.write_empty('TRANSMISSION_CAPITAL_COST','\\Topography Inputs\\Transmission',['name','source','notes','lifetime','currency','currency_year','unit','time_unit',\
                                               'interpolation_method','extrapolation_method','cost_of_capital',\
                                               'levelized','vintage','value','sensitivity'])
        self.write_empty('TRANSMISSION_DEPENDABILITY','\\Topography Inputs\\Transmission',['name','source','notes','geography','gau','geography_map_key',
                                               'interpolation_method','extrapolation_method','year','flow_value','counterflow_value','sensitivity'])
        self.write_empty('TRANSMISSION_FIXED_OM','\\Topography Inputs\\Transmission',['name','source','notes','currency','currency_year','unit',\
                                               'interpolation_method','extrapolation_method','vintage','value','sensitivity'])
        self.write_empty('TRANSMISSION_POTENTIAL','\\Topography Inputs\\Transmission',['name','type','unit','time_unit',
                                               'interpolation_method','extrapolation_method','year','value','sensitivity'])
        self.write_empty('ZONAL_NET_FLOW_CONSTRAINT','\\Topography Inputs\\Transmission',['name','type','source','notes',
                                               'geography','gau','geography_map_key','interpolation_method','extrapolation_method','year','unit','value','sensitivity'])

    def write_capacity_zones_empty(self):
        self.write_empty('LOCAL_CAPACITY_ZONE_CAPITAL_COST','\\Topography Inputs\\Capacity Zones',['name','source','notes','construction_time','lifetime','currency','currency_year','unit','time_unit',\
                                                'geography','gau','geography_map_key',\
                                               'interpolation_method','extrapolation_method','cost_of_capital',\
                                               'levelized','vintage','value','sensitivity'])
        self.write_empty('LOCAL_CAPACITY_ZONE_LOAD','\\Topography Inputs\\Capacity Zones',['name','unit','interpolation_method','extrapolation_method','year','value','sensitivity'])
        self.write_empty('LOCAL_CAPACITY_ZONE_LOSSES', '\\Topography Inputs\\Capacity Zones', ['name','interpolation_method', 'extrapolation_method', 'year', 'value', 'sensitivity'])



    def write_empty(self,name,subfolder,headers):
        path = self.db_dir + subfolder
        df = pd.DataFrame(columns=headers)
        Output.write_rio(df,name + ".csv",path,index=False)




    def write_conversion_efficiency(self):
        df_list = []
        for blend in self.blend_node_subset:
            for node in self.supply.nodes[blend].nodes:
                if self.supply.nodes[node].supply_type == 'Conversion':
                    if self.supply.nodes[node].potential.raw_values is not None:
                        pass
                        # todo allow for resource bins
                    else:
                        for technology in self.supply.nodes[node].technologies.keys():
                            eff_df = self.supply.nodes[node].technologies[technology].efficiency.values.groupby(
                                level=[cfg.supply_primary_geography, 'supply_node', 'vintage']).sum()
                            eff_df = eff_df.stack().to_frame()
                            eff_df.columns = ['value']
                            util.replace_index_name(eff_df, 'year')
                            eff_df = eff_df[
                                eff_df.index.get_level_values('vintage') == eff_df.index.get_level_values('year')]
                            eff_df = util.remove_df_levels(eff_df, 'year')
                            idx = pd.IndexSlice
                            eff_blend_df = eff_df.loc[idx[:, self.supply.blend_nodes, :], :]
                            if len(eff_blend_df) > 0:
                                eff_blend_df = eff_blend_df.reorder_levels(
                                    [cfg.supply_primary_geography, 'vintage', 'supply_node'])
                                eff_blend_df['name'] = cfg.outputs_id_map['supply_node'][node] + "_" + \
                                                       cfg.outputs_id_map['supply_technology'][technology] + "_" + self.blend_node_subset_lookup[blend]
                                df_list.append(eff_blend_df)
                            for delivery_node in set(eff_df.index.get_level_values('supply_node')):
                                if self.supply.nodes[delivery_node].supply_type == 'Delivery':
                                    temp_df = util.df_slice(eff_df, delivery_node, 'supply_node')
                                    eff_del = self.supply.nodes[delivery_node].coefficients.values.groupby(
                                        level=[cfg.supply_primary_geography, 'demand_sector',
                                               'supply_node']).sum().groupby(
                                        level=[cfg.supply_primary_geography, 'supply_node']).mean()
                                    eff_del = eff_del.mean(axis=1).to_frame()
                                    eff_del.columns = ['value']
                                    eff_del = eff_del.loc[idx[:, self.supply.blend_nodes], :]
                                    if len (eff_del)>0:
                                        eff_del = util.DfOper.mult([temp_df, eff_del]).reorder_levels(
                                                [cfg.supply_primary_geography, 'vintage', 'supply_node'])
                                        eff_del['name'] = cfg.outputs_id_map['supply_node'][node] + "_" + \
                                                      cfg.outputs_id_map['supply_technology'][technology]+ "_" + self.blend_node_subset_lookup[blend]
                                        df_list.append(eff_del)
        df = pd.concat(df_list)
        df = Output.clean_rio_df(df)
        util.replace_column_name(df, 'gau', cfg.supply_primary_geography)
        util.replace_column_name(df, 'blend_in', 'supply_node')
        df['unit_in'] = cfg.calculation_energy_unit
        df['unit_out'] = cfg.calculation_energy_unit
        df['output_numerator'] = False
        df['source'] = None
        df['notes'] = None
        df['interpolation_method'] = 'linear_interpolation'
        df['extrapolation_method'] = 'nearest'
        df['extrapolation_growth_rate'] = None
        df['sensitivity'] = self.supply.scenario.name
        df['geography_map_key'] = None
        df = df[['name', 'source', 'notes', 'blend_in', 'unit_in', 'unit_out', 'output_numerator', 'geography', 'gau',
                 'geography_map_key', 'interpolation_method', 'extrapolation_method', 'extrapolation_growth_rate',
                 'vintage', 'value', 'sensitivity']]
        electric_df = df.loc[df['blend_in'].isin([cfg.outputs_id_map['supply_node'][x] for x in [self.supply.bulk_id,
                                                  self.supply.thermal_dispatch_node_id,
                                                  self.supply.distribution_node_id]])]
        blend_df = df.loc[~df['blend_in'].isin([cfg.outputs_id_map['supply_node'][x] for x in [self.supply.bulk_id,
                                                  self.supply.thermal_dispatch_node_id,
                                                  self.supply.distribution_node_id]])]

        Output.write_rio(blend_df, "CONVERSION_BLEND_EFFICIENCY" + '.csv', self.db_dir + "\\Fuel Inputs\\Conversions", index=False)
        Output.write_rio(electric_df.drop(labels='blend_in', axis=1), "CONVERSION_ELECTRICITY_EFFICIENCY" + '.csv',
                     self.db_dir + "\\Fuel Inputs\\Conversions", index=False)

    def write_conversion_fixed_om(self):
        df_list = []
        for blend in self.blend_node_subset:
            for node in self.supply.nodes[blend].nodes:
                if self.supply.nodes[node].supply_type == 'Conversion':
                    if self.supply.nodes[node].potential.raw_values is not None:
                        pass
                        # todo allow for resource bins
                    else:
                        for technology in self.supply.nodes[node].technologies.keys():
                            if hasattr(self.supply.nodes[node].technologies[technology].fixed_om, 'values'):
                                cost_df = self.supply.nodes[node].technologies[technology].fixed_om.values.groupby(
                                    level=[cfg.supply_primary_geography, 'vintage']).sum()
                                cost_df['name'] = cfg.outputs_id_map['supply_node'][node] + "_" + \
                                                  cfg.outputs_id_map['supply_technology'][technology]+ "_" + self.blend_node_subset_lookup[blend]
                                df_list.append(cost_df)
        df = pd.concat(df_list)
        df = Output.clean_rio_df(df)
        util.replace_column_name(df, 'blend_in', 'supply_node')
        df['source'] = None
        df['notes'] = None
        df['interpolation_method'] = 'linear_interpolation'
        df['extrapolation_method'] = 'nearest'
        df['construction_time'] = 1
        df['unit'] = cfg.calculation_energy_unit
        df['time_unit'] = 'hour'
        df['currency'] = cfg.currency_name
        df['currency_year'] = cfg.cfgfile.get('case', 'currency_year_id')
        df['sensitivity'] = self.supply.scenario.name
        df['geography_map_key'] = None
        df = df[['name', 'source', 'notes', 'currency', 'currency_year', 'unit', 'time_unit', \
                 'geography', 'gau', 'geography_map_key', 'interpolation_method', 'extrapolation_method', \
                 'vintage', 'value', 'sensitivity']]
        Output.write_rio(df, "CONVERSION_FIXED_OM" + '.csv', self.db_dir + "\\Fuel Inputs\\Conversions", index=False)

    def write_conversion_schedule(self):
        df_list = []
        for blend in self.blend_node_subset:
            for node in self.supply.nodes[blend].nodes:
                if self.supply.nodes[node].supply_type == 'Conversion':
                    if self.supply.nodes[node].potential.raw_values is not None:
                        pass
                        # todo allow for resource bins
                    else:
                        for technology in self.supply.nodes[node].technologies.keys():
                            df = util.df_slice(self.supply.nodes[node].stock.technology, technology, 'supply_technology')
                            df = df.stack().to_frame()
                            df.columns = ['value']
                            util.replace_index_name(df, 'year')
                            df = df[np.isfinite(df.values)]
                            df['name'] = cfg.outputs_id_map['supply_node'][node] + "_" + \
                                         cfg.outputs_id_map['supply_technology'][technology]+ "_" + self.blend_node_subset_lookup[blend]
                            df_list.append(df)
        df = pd.concat(df_list)
        df = Output.clean_rio_df(df)
        df['interpolation_method'] = 'linear_interpolation'
        df['extrapolation_method'] = 'nearest'
        df['unit'] = cfg.calculation_energy_unit
        df['time_unit'] = 'hour'
        df['type'] = 'capacity'
        df['sensitivity'] = self.supply.scenario.name
        df['geography_map_key'] = None
        df = df[['name', 'type', 'unit', 'time_unit',
                 'geography', 'gau', 'geography_map_key', 'interpolation_method', 'extrapolation_method', \
                 'year', 'value', 'sensitivity']]
        Output.write_rio(df, "CONVERSION_SCHEDULE" + '.csv', self.db_dir + "\\Fuel Inputs\\Conversions", index=False)

    def write_conversion_variable_om(self):
        df_list = []
        for blend in self.blend_node_subset:
            for node in self.supply.nodes[blend].nodes:
                if self.supply.nodes[node].supply_type == 'Conversion':
                    if self.supply.nodes[node].potential.raw_values is not None:
                        pass
                        # todo allow for resource bins
                    else:
                        for technology in self.supply.nodes[node].technologies.keys():
                            if hasattr(self.supply.nodes[node].technologies[technology].variable_om, 'values_level'):
                                cost_df = self.supply.nodes[node].technologies[
                                    technology].variable_om.values_level.groupby(
                                    level=[cfg.supply_primary_geography, 'vintage']).sum()
                                cost_df = cost_df.stack().to_frame()
                                cost_df.columns = ['value']
                                util.replace_index_name(cost_df, 'year')
                                cost_df['age'] = cost_df.index.get_level_values(
                                    'year') - cost_df.index.get_level_values('vintage')
                                cost_df = cost_df[cost_df['age'] == 0]
                                cost_df.set_index('age', append=True, inplace=True)
                                cost_df = util.remove_df_levels(cost_df, 'year')
                                cost_df['name'] = cfg.outputs_id_map['supply_node'][node] + "_" + \
                                                  cfg.outputs_id_map['supply_technology'][technology]+ "_" + self.blend_node_subset_lookup[blend]
                                df_list.append(cost_df)
        df = pd.concat(df_list)
        df = Output.clean_rio_df(df)
        df['source'] = None
        df['notes'] = None
        df['interpolation_method'] = 'linear_interpolation'
        df['extrapolation_method'] = 'nearest'
        df['construction_time'] = 1
        df['unit'] = cfg.calculation_energy_unit
        df['currency'] = cfg.currency_name
        df['currency_year'] = cfg.cfgfile.get('case', 'currency_year_id')
        df['sensitivity'] = self.supply.scenario.name
        df['geography_map_key'] = None
        df = df[['name', 'source', 'notes', 'currency', 'currency_year', 'unit',
                 'geography', 'gau', 'geography_map_key', 'interpolation_method', 'extrapolation_method', \
                 'vintage', 'age', 'value', 'sensitivity']]
        Output.write_rio(df, "CONVERSION_VARIABLE_OM" + '.csv', self.db_dir + "\\Fuel Inputs\\Conversions", index=False)

    def write_conversion_capital_cost(self):
        df_list = []
        for blend in self.blend_node_subset:
            for node in self.supply.nodes[blend].nodes:
                if self.supply.nodes[node].supply_type == 'Conversion':
                    if self.supply.nodes[node].potential.raw_values is not None:
                        pass
                        # todo allow for resource bins
                    else:
                        for technology in self.supply.nodes[node].technologies.keys():
                            cost_df = self.supply.nodes[node].technologies[technology].capital_cost_new.values.groupby(
                                level=[cfg.supply_primary_geography, 'vintage']).sum()
                            if hasattr(self.supply.nodes[node].technologies[technology].installation_cost_new,
                                       'values'):
                                cost_df = util.DfOper.add([cost_df, self.supply.nodes[node].technologies[
                                    technology].installation_cost_new.values.groupby(
                                    level=[cfg.supply_primary_geography, 'vintage']).sum()])
                            cost_df['name'] = cfg.outputs_id_map['supply_node'][node] + "_" + \
                                              cfg.outputs_id_map['supply_technology'][technology]+ "_" + self.blend_node_subset_lookup[blend]
                            cost_df['lifetime'] = self.supply.nodes[node].technologies[technology].mean_lifetime
                            cost_df['cost_of_capital'] = self.supply.nodes[node].technologies[
                                technology].cost_of_capital -float(cfg.cfgfile.get('case', 'inflation_rate'))
                            df_list.append(cost_df)
        df = pd.concat(df_list)
        df.reset_index(inplace=True)
        df = Output.clean_rio_df(df)
        df['source'] = None
        df['notes'] = None
        df['interpolation_method'] = 'linear_interpolation'
        df['extrapolation_method'] = 'nearest'
        df['extrapolation_growth_rate'] = None
        df['construction_time'] = 1
        df['levelized'] = False
        df['unit'] = cfg.calculation_energy_unit
        df['time_unit'] = 'hour'
        df['currency'] = cfg.currency_name
        df['currency_year'] = cfg.cfgfile.get('case', 'currency_year_id')
        df['sensitivity'] = self.supply.scenario.name
        df['geography_map_key'] = None
        df = df[['name', 'source', 'notes', 'currency', 'currency_year', 'unit', 'time_unit', \
                 'geography', 'gau', 'geography_map_key', 'interpolation_method', 'extrapolation_method',
                 'extrapolation_growth_rate', \
                 'lifetime', 'construction_time', 'cost_of_capital', 'levelized', \
                 'vintage', 'value', 'sensitivity']]
        Output.write_rio(df, "CONVERSION_CAPITAL_COST" + '.csv', self.db_dir + "\\Fuel Inputs\\Conversions", index=False)

    def write_product_main(self):
        self.product_names = []
        for node in self.blend_node_inputs:
            if self.supply.nodes[node].supply_type == 'Primary' or self.supply.nodes[node].supply_type == 'Import':
                if self.supply.nodes[node].potential.raw_values is not None:
                    for resource_bin in set(
                            self.supply.nodes[node].potential.raw_values.index.get_level_values('resource_bin')):
                        self.product_names.append(self.supply.nodes[node].name + "_" + str(resource_bin))
                else:
                    self.product_names.append(self.supply.nodes[node].name)
        df = pd.DataFrame(zip(self.product_names, [None for x in self.product_names]), columns=['name', 'dummy'])
        Output.write_rio(df, "PRODUCT_MAIN" + '.csv', self.db_dir + "\\Fuel Inputs\\Products", index=False)

    def write_product_cost(self):
        residual_nodes = [x.residual_supply_node_id for x in self.supply.nodes.values()]
        df_list = []
        for node in self.blend_node_inputs:
            #necessary to bias against selection of residual nodes, so that products with the same cost are ordered. Ex. Domestic vs. International Oil
            mult = 1.005 if node in residual_nodes else 1
            if self.supply.nodes[node].supply_type == 'Primary' or self.supply.nodes[node].supply_type == 'Import':
                if self.supply.nodes[node].potential.raw_values is not None:
                    for resource_bin in set(
                            self.supply.nodes[node].potential.raw_values.index.get_level_values('resource_bin')):
                        if hasattr(self.supply.nodes[node].cost,'values'):
                            if 'resource_bin' in self.supply.nodes[node].cost.values.index.names:
                                df = util.df_slice(self.supply.nodes[node].cost.values * mult, resource_bin, 'resource_bin')
                            else:
                                df = copy.deepcopy(self.supply.nodes[node].cost.values*mult)
                            if len(df.index.names) > 1:
                                df = df.groupby(level=[cfg.supply_primary_geography]).mean()
                            df = df.stack().to_frame()
                            df.columns = ['value']
                            util.replace_index_name(df, 'year')
                            df['name'] = self.supply.nodes[node].name + "_" + str(resource_bin)
                            df_list.append(df)
                else:
                    if hasattr(self.supply.nodes[node].cost,'values'):
                        df = self.supply.nodes[node].cost.values * mult
                        if len(df.index.names) > 1:
                            df = df.groupby(level=[cfg.supply_primary_geography]).mean()
                        df = df.stack().to_frame()
                        df.columns = ['value']
                        util.replace_index_name(df, 'year')
                        df['name'] = self.supply.nodes[node].name
                        df_list.append(df)
        df = pd.concat(df_list)
        df = Output.clean_rio_df(df)
        df['source'] = None
        df['notes'] = None
        df['interpolation_method'] = 'linear_interpolation'
        df['extrapolation_method'] = 'nearest'
        df['exponential_growth_rate'] = None
        df['unit'] = cfg.calculation_energy_unit
        df['currency'] = cfg.currency_name
        df['currency_year'] = cfg.cfgfile.get('case', 'currency_year_id')
        df['sensitivity'] = self.supply.scenario.name
        df['geography_map_key'] = None
        df = df[['name', 'source', 'notes', 'currency', 'currency_year', 'unit', \
                 'geography', 'gau', 'geography_map_key', 'interpolation_method', 'extrapolation_method',
                 'exponential_growth_rate', \
                 'year', 'value', 'sensitivity']]
        Output.write_rio(df, "PRODUCT_COST" + '.csv', self.db_dir + "\\Fuel Inputs\\Products", index=False)

    def write_product_emissions(self):
        df_list = []
        upstream_df = self.calc_upstream_emissions()
        for node in self.blend_node_inputs:
            if self.supply.nodes[node].supply_type == 'Primary' or self.supply.nodes[node].supply_type == 'Import':
                if self.supply.nodes[node].potential.raw_values is not None:
                    for resource_bin in set(
                            self.supply.nodes[node].potential.raw_values.index.get_level_values('resource_bin')):
                        if hasattr(self.supply.nodes[node].emissions,'values'):
                            if 'resource_bin' in self.supply.nodes[node].emissions.values.index.names:
                                df = util.df_slice(self.supply.nodes[node].emissions.values, resource_bin, 'resource_bin')
                            else:
                                df = self.supply.nodes[node].emissions.values
                            if len(df.index.names) > 1:
                                df = df.groupby(level=[cfg.supply_primary_geography]).mean()
                            df = df.stack().to_frame()
                            df.columns = ['value']
                            util.replace_index_name(df, 'year')
                            total_df = util.DfOper.add([df, util.df_slice(upstream_df, node, 'supply_node')])
                            total_df = total_df.groupby(level=[cfg.supply_primary_geography,'year']).sum()
                            total_df['name'] = self.supply.nodes[node].name + "_" + str(resource_bin)
                            df_list.append(total_df)
                        else:
                            total_df = util.df_slice(upstream_df, node, 'supply_node')
                            total_df = total_df.groupby(level=[cfg.supply_primary_geography, 'year']).sum()
                            total_df['name'] = self.supply.nodes[node].name+ "_" + str(resource_bin)
                            df_list.append(total_df)
                else:
                    if hasattr(self.supply.nodes[node].emissions,'values'):
                        df = copy.deepcopy(self.supply.nodes[node].emissions.values)
                        df = df.stack().to_frame()
                        df = df.groupby(level=[cfg.supply_primary_geography, 'year']).sum()
                        df.columns = ['value']
                        util.replace_index_name(df, 'year')
                        total_df = util.DfOper.add([df, util.df_slice(upstream_df, node, 'supply_node')])
                        total_df['name'] = self.supply.nodes[node].name
                        df_list.append(total_df)
                    else:
                        total_df = util.df_slice(upstream_df, node, 'supply_node')
                        total_df['name'] = self.supply.nodes[node].name
                        df_list.append(total_df)
        df = pd.concat(df_list)
        df = Output.clean_rio_df(df)
        df['source'] = None
        df['notes'] = None
        df['interpolation_method'] = 'linear_interpolation'
        df['extrapolation_method'] = 'nearest'
        df['extrapolation_growth_rate'] = None
        df['energy_unit'] = cfg.calculation_energy_unit
        df['mass_unit'] = cfg.cfgfile.get('case', "mass_unit")
        df['sensitivity'] = self.supply.scenario.name
        df['geography_map_key'] = None
        df = df[['name', 'source', 'notes', 'mass_unit', 'energy_unit',
                 'geography', 'gau', 'geography_map_key', 'interpolation_method', 'extrapolation_method',
                 'extrapolation_growth_rate', \
                 'year', 'value', 'sensitivity']]
        Output.write_rio(df, "PRODUCT_EMISSIONS" + '.csv', self.db_dir + "\\Fuel Inputs\\Products", index=False)

    def write_product_potential(self):
        df_list = []
        df_geo_nodes = []
        for node in self.blend_node_inputs:
            if self.supply.nodes[node].supply_type == 'Primary' or self.supply.nodes[node].supply_type == 'Import':
                if self.supply.nodes[node].potential.raw_values is not None:
                    for resource_bin in set(
                            self.supply.nodes[node].potential.raw_values.index.get_level_values('resource_bin')):
                        if hasattr(self.supply.nodes[node].potential, 'values'):
                            try:
                                df = util.df_slice(self.supply.nodes[node].potential.values, resource_bin, 'resource_bin')
                            except:
                                print "no potential in resource bin %s in node %s " %(resource_bin,node)
                                continue
                            if len(df.index.names)>1:
                                df = df.groupby(level=[cfg.supply_primary_geography]).sum()
                            df = df.stack().to_frame()
                            df.columns = ['value']
                            util.replace_index_name(df, 'year')
                            df['name']=self.supply.nodes[node].name + "_" + str(resource_bin)
                            df_list.append(df)
                            if self.supply.nodes[node].tradable_geography == cfg.supply_primary_geography:
                                df_geo_nodes.append(self.supply.nodes[node].name + "_" + str(resource_bin))
        df = pd.concat(df_list)
        df = Output.clean_rio_df(df)
        util.replace_column_name(df, 'gau', cfg.supply_primary_geography)
        df['source'] = None
        df['notes'] = None
        df['interpolation_method'] = 'linear_interpolation'
        df['extrapolation_method'] = 'nearest'
        df['extrapolation_growth_rate'] = None
        df['unit'] = cfg.calculation_energy_unit
        df['geography'] = cfg.geo.id_to_geography[cfg.supply_primary_geography_id]
        df['sensitivity'] = self.supply.scenario.name
        df = df[['name', 'source', 'notes', 'unit',
                 'geography', 'gau', 'interpolation_method', 'extrapolation_method', 'extrapolation_growth_rate', \
                 'year', 'value', 'sensitivity']]
        non_geo_df = df.loc[~df['name'].isin(df_geo_nodes)]
        geo_df = df.loc[df['name'].isin(df_geo_nodes)]
        Output.write_rio(non_geo_df, "PRODUCT_POTENTIAL" + '.csv', self.db_dir + "\\Fuel Inputs\\Products", index=False)
        Output.write_rio(geo_df, "PRODUCT_POTENTIAL_GEO" + '.csv', self.db_dir + "\\Fuel Inputs\\Products", index=False)

    def calc_upstream_emissions(self):
        active_node_list = []
        active_product_list = []
        for blend in self.supply.blend_nodes:
            for node in self.supply.nodes[blend].nodes:
                if self.supply.nodes[node].supply_type == 'Primary' or self.supply.nodes[node].supply_type == 'Import':
                    active_node_list.append(node)
                    active_product_list.append(node)
                elif self.supply.nodes[node].supply_type == 'Conversion':
                    active_node_list.append(node)

        omitted_node_list = [x for x in self.supply.nodes if x not in active_node_list]
        df_list = []
        for year in self.supply.years:
            df = copy.deepcopy(self.supply.emissions_dict[year][1])
            idx = pd.IndexSlice
            df = df.loc[idx[:, omitted_node_list], idx[:, active_product_list]].sum().to_frame()
            df.columns = ['value']
            df_list.append(df)
        df = pd.concat(df_list, keys=self.supply.years, names=['year'])
        return df.reorder_levels(['supply_node',cfg.supply_primary_geography,'year'])

    def write_conversion_main(self):
        self.conversion_names = []
        for node in self.blend_node_inputs:
            if self.supply.nodes[node].supply_type == 'Conversion':
                for blend in self.blend_node_subset:
                    if node in self.supply.nodes[blend].nodes:
                        if self.supply.nodes[node].potential.raw_values is not None:
                            for technology in self.supply.nodes[node].technologies.keys():
                                for resource_bin in set(
                                        self.supply.nodes[node].potential.raw_values.index.get_level_values('resource_bin')):
                                    self.conversion_names.append(
                                        self.supply.nodes[node].name + "_" + self.supply.nodes[node].technologies[
                                            technology].name + "_" + str(resource_bin)) + "_" + self.blend_node_subset_lookup[blend]
                        else:
                            for technology in self.supply.nodes[node].technologies.keys():
                                self.conversion_names.append(
                                    self.supply.nodes[node].name + "_" + self.supply.nodes[node].technologies[technology].name+ "_" + self.blend_node_subset_lookup[blend])
        df = pd.DataFrame(zip(self.conversion_names, [None for x in self.conversion_names]), columns=['name', 'dummy'])
        Output.write_rio(df, "CONVERSION_MAIN" + '.csv', self.db_dir + "\\Fuel Inputs\\Conversions", index=False)

    def write_capacity_zone_main(self):
        if len(cfg.rio_feeder_geographies):
            name = ['bulk']
            level = ['bulk']
            gau = ['all']
            shape = ['bulk']
            for x in self.supply.dispatch_feeders:
                for y in cfg.rio_feeder_geographies:
                    name.append(
                        cfg.outputs_id_map[cfg.dispatch_geography][y] + "_" + cfg.outputs_id_map['dispatch_feeder'][x].lower())
                    level.append('local')
                    gau.append(cfg.outputs_id_map[cfg.dispatch_geography][y])
                    shape.append(
                        cfg.outputs_id_map[cfg.dispatch_geography][y] + "_" + cfg.outputs_id_map['dispatch_feeder'][x].lower())
        else:
            name = ['bulk']
            level = ['bulk']
            gau = ['all']
            shape = ['bulk']
        df = pd.DataFrame({'name' : name, 'level': level, 'gau': gau, 'shape':shape})
        df = df[['name','level','gau','shape']]
        Output.write_rio(df, "CAPACITY_ZONE_MAIN" + '.csv', self.db_dir + "\\Topography Inputs\\Capacity Zones", index=False)

    def write_bulk_capacity_zone_losses(self):
        dist_df, bulk_df = self.flatten_loss_dicts()
        df = bulk_df -1
        df['name'] = 'bulk'
        df['geography_map_key'] = None
        df['interpolation_method'] = 'linear_interpolation'
        df['extrapolation_method'] = 'nearest'
        df['sensitivity'] = self.supply.scenario.name
        df = Output.clean_rio_df(df)
        df = df[['name','geography','gau','geography_map_key','interpolation_method','extrapolation_method','year','value','sensitivity']]
        Output.write_rio(df,"BULK_CAPACITY_ZONE_LOSSES"+".csv",self.db_dir + "\\Topography Inputs\\Capacity Zones", index=False)

    def write_capacity_zone_load(self):
        df_list = []
        dist_load, bulk_load = self.flatten_load_dicts()
        if len(cfg.rio_feeder_geographies):
            for geography in cfg.rio_feeder_geographies:
                for feeder in self.supply.dispatch_feeders:
                    df = util.df_slice(dist_load,feeder,'dispatch_feeder')
                    df = util.df_slice(df,geography,cfg.supply_primary_geography,drop_level=False)
                    load_shape_df = util.DfOper.divi([df, util.remove_df_levels(df, 'weather_datetime', 'sum')])
                    #load_shape_df = load_shape_df.tz_localize(None, level='weather_datetime')
                    load_shape_df = Output.clean_rio_df(load_shape_df,add_geography=False)
                    load_shape_df['sensitivity'] = self.supply.scenario.name
                    df = util.remove_df_levels(df,'weather_datetime')
                    df = Output.clean_rio_df(df)
                    df['interpolation_method'] = 'linear_interpolation'
                    df['extrapolation_method'] = 'nearest'
                    df['unit'] = cfg.calculation_energy_unit
                    df['sensitivity'] = self.supply.scenario.name
                    df['name'] = cfg.outputs_id_map[cfg.supply_primary_geography][geography].lower() + "_" + cfg.outputs_id_map['dispatch_feeder'][feeder].lower()
                    df = df[['name', 'geography', 'gau', 'unit', 'interpolation_method', 'extrapolation_method', \
                         'year', 'value', 'sensitivity']]
                    df_list.append(copy.deepcopy(df))
                    Output.write_rio(load_shape_df, cfg.outputs_id_map[cfg.supply_primary_geography][geography].lower() + "_" + cfg.outputs_id_map['dispatch_feeder'][feeder].lower() + ".csv", self.db_dir + "\\ShapeData",                                                                                                                                       index=False)
            df = pd.concat(df_list)
            Output.write_rio(df, "LOCAL_CAPACITY_ZONE_LOAD" + '.csv', self.db_dir + "\\Topography Inputs\Capacity Zones", index=False)
        df_list, load_shape_list = [], []
        for geography in cfg.supply_geographies:
            if geography not in cfg.rio_feeder_geographies:
                dist_load, bulk_load = self.flatten_load_dicts()
                dist_losses, bulk_losses = self.flatten_loss_dicts()
                dist_load_grossed = util.DfOper.mult([dist_load, dist_losses]).groupby(
                        level=[cfg.dispatch_geography, 'year','weather_datetime']).sum()
                df = util.DfOper.add([dist_load_grossed, bulk_load])
                df = util.df_slice(df,geography,cfg.supply_primary_geography, reset_index=True, drop_level=False)
            else:
                df = bulk_load
                df = util.df_slice(df, geography, cfg.supply_primary_geography, reset_index=True, drop_level=False)
            load_shape_df = util.DfOper.divi([df, util.remove_df_levels(df, 'weather_datetime', 'sum')])
            #load_shape_df = load_shape_df.tz_localize(None, level='weather_datetime')
            load_shape_df = Output.clean_rio_df(load_shape_df,add_geography=False)
            load_shape_df['sensitivity'] = self.supply.scenario.name
            df = util.remove_df_levels(df,'weather_datetime')
            df = Output.clean_rio_df(df)
            df['interpolation_method'] = 'linear_interpolation'
            df['extrapolation_method'] = 'nearest'
            df['unit'] = cfg.calculation_energy_unit
            df['sensitivity'] = self.supply.scenario.name
            df['name'] = 'bulk'
            df = df[['name', 'geography', 'gau', 'unit', 'interpolation_method', 'extrapolation_method', \
                     'year', 'value', 'sensitivity']]
            df_list.append(df)
            load_shape_list.append(load_shape_df)
        load_shape = pd.concat(load_shape_list)
        Output.write_rio(load_shape, "bulk" + ".csv", self.db_dir + "\\ShapeData", index=False)
        df = pd.concat(df_list)
        Output.write_rio(df, "BULK_CAPACITY_ZONE_LOAD" + '.csv', self.db_dir + "\\Topography Inputs\Capacity Zones", index=False)

    def flatten_load_dicts(self):
        dist_list = []
        bulk_list = []
        for year in self.supply.rio_distribution_load.keys():
            dist_df = self.supply.rio_distribution_load[year]
            dist_df.columns = ['value']
            dist_list.append(dist_df)
            bulk_df  = self.supply.rio_bulk_load[year]
            bulk_df.columns = ['value']
            bulk_list.append(bulk_df)
        return pd.concat(dist_list, keys=self.supply.rio_distribution_load.keys(), names=['year']), pd.concat(bulk_list, keys=self.supply.rio_distribution_load.keys(),
                                                                                     names=['year'])
    def flatten_flex_load_dict(self):
        df_list = []
        for year in self.supply.rio_flex_load.keys():
            df = self.supply.rio_flex_load[year]
            if df is not None:
                df.columns = ['value']
                df_list.append(df)
        if len(df_list):
            return pd.concat(df_list, keys=self.supply.rio_flex_load.keys(), names=['year'])
        else:
            return None

    def flatten_loss_dicts(self):
        dist_list = []
        bulk_list = []
        for year in self.supply.rio_distribution_losses.keys():
            dist_df = self.supply.rio_distribution_losses[year]
            dist_df.columns = ['value']
            dist_list.append(dist_df)
            bulk_df = self.supply.rio_transmission_losses[year]
            bulk_df.columns = ['value']
            bulk_list.append(bulk_df)
        return pd.concat(dist_list), pd.concat(bulk_list,keys=self.supply.rio_distribution_losses.keys(),names=['year'])

    def write_potential_empty(self):
       self.write_empty("POTENTIAL_GROUP","\\Technology Inputs\\Generation",['name', 'incremental_to_existing', 'source', 'notes', 'unit', 'time_unit', 'geography', 'gau', 'geography_map_key','interpolation_method', 'extrapolation_method', 'extrapolation_growth_rate', 'year', 'value', 'sensitivity'])

def run(path, config, scenarios):
    global model
    path = os.getcwd() if path is None else path
    cfg.initialize_config(path, config, None)
    if not scenarios:
        scenarios = [os.path.basename(p) for p in glob.glob(os.path.join(cfg.workingdir, '*.json'))]
        if not scenarios:
            raise ValueError, "No scenarios specified and no .json files found in working directory."

    # Users may have specified a scenario using the full filename, but for our purposes the 'id' of the scenario
    # is just the part before the .json
    scenarios = [os.path.splitext(s)[0] for s in scenarios]

    logging.info('Scenario run list: {}'.format(', '.join(scenarios)))
    folder =os.path.join(cfg.workingdir, 'rio_db_export')
    if os.path.exists(folder):
        for file in folder:
            filelist = [f for f in os.listdir(folder) if f.endswith(".csv")]
            for f in filelist:
                os.remove(os.path.join(folder, f))
        for dir in os.listdir(folder):
            if os.path.isdir(os.path.join(folder,dir)) and dir != 'System Inputs':
                shutil.rmtree(os.path.join(folder,dir))
    for scenario_index, scenario in enumerate(scenarios):
        model = load_model(False, True, False, scenario)
        export = RioExport(model,scenario_index)
        export.write_all()
        logging.info('EnergyPATHWAYS to RIO  for scenario {} successful!'.format(scenario))
    return export


def load_model(load_demand, load_supply, load_error, scenario):
    if load_error:
        with open(os.path.join(cfg.workingdir, str(scenario) + cfg.model_error_append_name), 'rb+') as infile:
            #        with open(os.path.join(cfg.workingdir, 'dispatch_class.p'), 'rb') as infile:
            model = pickle.load(infile)
        logging.info('Loaded crashed EnergyPATHWAYS model from pickle')
    elif load_supply:
        with open(os.path.join(cfg.workingdir, str(scenario) + cfg.full_model_append_name), 'rb') as infile:
            model = pickle.load(infile)
        logging.info('Loaded complete EnergyPATHWAYS model from pickle')
    elif load_demand:
        demand_file = os.path.join(cfg.workingdir, str(scenario) + cfg.demand_model_append_name)
        supply_file = os.path.join(cfg.workingdir, str(scenario) + cfg.full_model_append_name)
        if os.path.isfile(demand_file):
            with open(os.path.join(cfg.workingdir, str(scenario) + cfg.demand_model_append_name), 'rb') as infile:
                model = pickle.load(infile)
                logging.info('Loaded demand-side EnergyPATHWAYS model from pickle')
        elif os.path.isfile(supply_file):
            with open(os.path.join(cfg.workingdir, str(scenario) + cfg.full_model_append_name), 'rb') as infile:
                model = pickle.load(infile)
                logging.info('Loaded complete EnergyPATHWAYS model from pickle')
        else:
            raise ("No model file exists")
    else:
        model = PathwaysModel(scenario)
    return model


if __name__ == "__main__":
    workingdir = r'C:\Github\EnergyPATHWAYS_scenarios\UCS'
    config = 'config.INI'
    scenario = ['UCS','ref_moder_aeo']
    export = run(workingdir, config, scenario)
    self = export
