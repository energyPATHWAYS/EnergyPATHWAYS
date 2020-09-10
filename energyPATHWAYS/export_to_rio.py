
from outputs import Output
import os
import util
import shutil
import config as cfg
import pandas as pd
import logging
import pdb
import copy
import numpy as np
from collections import defaultdict
import glob
import cPickle as pickle
from energyPATHWAYS.supply import StorageNode, BlendNode, SupplyStockNode, ImportNode, PrimaryNode
import ast
from shape import Shapes, Shape
from dateutil.relativedelta import relativedelta
from energyPATHWAYS.geomapper import GeoMapper
from unit_converter import UnitConverter
import datetime as DT

class RioExport(object):
    def __init__(self, model, scenario_index,scenario):
        self.scenario = scenario
        self.supply = model.supply
        self.supply.bulk_electricity_node_name = 'Bulk Electricity Blend'
        self.db_dir = os.path.join(cfg.workingdir, 'rio_db_export')
        self.meta_dict = defaultdict(list)
        self.scenario_index = scenario_index
        # self.shapes = Shapes.get_instance(cfg.getParam('database_path'))


    def write_all(self):
        # logging.info("writing blends")
        self.write_demand_subsector()
        self.write_blend()
        #logging.info("writing flex load df")
        self.flex_load_df = self.flatten_flex_load_dict()
        if self.scenario_index == 0:
            logging.info("writing new flex techs")
            if self.flex_load_df is not None:
               self.write_flex_tech_main()
        self.write_conversion()
        logging.info("writing topography")
        self.write_topography()
        logging.info("writing flex load")
        self.write_flex_load()

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

    def write_demand_shapes(self):
        def get_active_dates(years):
            active_dates_index = []
            for year in years:
                start_date, end_date = DT.datetime(year, 1, 1), DT.datetime(year, 12, 31, 23)
                # todo, change the frequency to change the timestep
                active_dates_index.append(pd.date_range(start_date, end_date, freq='H'))
            return reduce(pd.DatetimeIndex.append, active_dates_index)
        weather_years = [int(y) for y in cfg.getParam('weather_years').split(',')]
        self.active_dates_index = get_active_dates(weather_years)
        shapes = {}
        for subsector_name in cfg.rio_opt_demand_subsectors:
            for sector in model.demand.sectors.values():
                if subsector_name in sector.subsectors.keys():
                    subsector = sector.subsectors[subsector_name]
                    for tech in subsector.technologies.values():
                        if not 'electricity' in tech.efficiency_main.values.index.get_level_values('final_energy'):
                            continue
                        if tech.shape is not None:
                            shapes[tech.name] = Shapes.get_values(tech.shape)
                        elif subsector.shape is not None:
                            shapes[tech.name] = Shapes.get_values(subsector.shape)
                        else:
                            shapes[tech.name] = Shapes.get_values('flat_demand_side')
        for shape_name, shape in shapes.iteritems():
            self.meta_dict['name'].append(shape_name.lower())
            self.meta_dict['shape_type'].append( 'weather date')
            self.meta_dict['input_type'].append( 'intensity')
            self.meta_dict['shape_unit_type'].append('power')
            self.meta_dict['time_zone'].append(GeoMapper.dispatch_geographies)
            self.meta_dict['geography'].append(GeoMapper.supply_primary_geography)
            self.meta_dict['geography_map_key'].append(None)
            self.meta_dict['interpolation_method'].append('linear_interpolation')
            self.meta_dict['extrapolation_method'].append('nearest')
            shape_df = util.remove_df_levels(shape,['resource_bin','dispatch_feeder'],agg_function='mean')
            shape_df = Output.clean_rio_df(shape_df,add_geography=False)
            Output.write_rio(shape_df,shape_name.lower() + ".csv",self.db_dir + "\\ShapeData"+"\\"+shape_name.lower()+".csvd",index=False)
        shape_df = Output.clean_rio_df(model.demand.electricity_reconciliation, add_geography=False)
        Output.write_rio(shape_df, 'electricity_reconcilitation'+ ".csv", self.db_dir + "\\ShapeData" + "\\" + 'electricity_reconcilitation' + ".csvd", index=False)
        for name in ['bulk','electricity_reconciliation']:
            self.meta_dict['name'].append(name)
            self.meta_dict['shape_type'].append('weather date')
            self.meta_dict['input_type'].append('intensity')
            self.meta_dict['shape_unit_type'].append('power')
            self.meta_dict['time_zone'].append(cfg.getParam('dispatch_outputs_timezone'))
            self.meta_dict['geography'].append(GeoMapper.dispatch_geography)
            self.meta_dict['geography_map_key'].append(None)
            self.meta_dict['interpolation_method'].append('linear_interpolation')
            self.meta_dict['extrapolation_method'].append('nearest')
        df = pd.DataFrame(self.meta_dict)
        df = df[['name', 'shape_type', 'input_type', 'shape_unit_type', 'time_zone', 'geography', 'geography_map_key', 'interpolation_method', 'extrapolation_method']]
        Output.write_rio(df, "SHAPE_META" + '.csv', self.db_dir, index=False)


        reconciliation_df =  Output.clean_rio_df(model.demand.electricity_reconciliation,add_geography=False)
        Output.write_rio(shape_df, shape_name.lower() + "_" + self.scenario + ".csv", self.db_dir + "\\ShapeData" + "\\" + shape_name.lower() + ".csvd", index=False)

    def write_flex_tech_main(self):
        dct = dict()
        if len(cfg.rio_feeder_geographies):
            for geography in cfg.rio_feeder_geographies:
                dct['name'] = [geography.lower() + "_" + x for x in self.supply.dispatch_feeders]
                dct['capacity_zone'] = dct['name']
                dct['ancillary_service_eligible'] = [True for x in dct['name']]
                dct['shape'] = ["flex_"+  x.upper() for x in dct['name']]
                df1 = pd.DataFrame(dct)
                df1 = df1[['name', 'capacity_zone','ancillary_service_eligible','shape']]
        else:
            df1 = None
        dct = dict()
        dct['name'] = self.supply.dispatch_feeders
        dct['capacity_zone'] = ["bulk" for x in dct['name']]
        dct['ancillary_service_eligible'] = [True for x in dct['name']]
        dct['shape'] = ["flex_"+ x.upper() for x in dct['name']]
        df2 = pd.DataFrame(dct)
        df2 = df2[['name', 'capacity_zone','ancillary_service_eligible','shape']]
        df = pd.concat([df1,df2])
        Output.write_rio(df,"FLEX_TECH_MAIN"+'.csv',self.db_dir + "\\Technology Inputs\\Flex Load", index=False)




    def write_flex_tech_schedule(self):
        dist_losses, bulk_losses = self.flatten_loss_dicts()
        df = util.df_slice(self.flex_load_df,'native','timeshift_type')
        df = UnitConverter.unit_convert(df.groupby(level=[x for x in df.index.names if x not in 'weather_datetime']).sum(),
                               unit_from_num=cfg.calculation_energy_unit,unit_to_num='megawatt_hour')
        df /= len(Shapes.get_instance().cfg_weather_years)
        df_list = []
        for geography in cfg.rio_feeder_geographies:
            for feeder in self.supply.dispatch_feeders:
                tech_df = util.df_slice(df,[feeder],['dispatch_feeder'])
                tech_df = util.df_slice(tech_df,[geography],GeoMapper.supply_primary_geography,drop_level=False)
                tech_df['name'] = geography.lower() + "_" + feeder
                tech_df['source'] = None
                tech_df['notes'] = None
                tech_df['geography'] = GeoMapper.supply_primary_geography
                tech_df['geography_map_key'] = None
                tech_df['interpolation_method'] = 'linear_interpolation'
                tech_df['extrapolation_method'] = 'nearest'
                tech_df[tech_df.index.get_level_values('year').values == min(self.supply.years)]
                util.replace_index_name(tech_df, 'year', 'vintage')
                tech_df['sensitivity'] = self.scenario
                df_list.append(copy.deepcopy(tech_df))
        for feeder in self.supply.dispatch_feeders:
            tech_df = util.DfOper.mult([util.df_slice(df, feeder, 'dispatch_feeder'),bulk_losses])
            tech_df[tech_df.index.get_level_values(GeoMapper.supply_primary_geography).isin(cfg.rio_feeder_geographies)] = 0
            tech_df['name'] = feeder
            tech_df['source'] = None
            tech_df['notes'] = None
            tech_df['geography'] = GeoMapper.supply_primary_geography
            tech_df['geography_map_key'] = None
            tech_df['interpolation_method'] = 'linear_interpolation'
            tech_df['extrapolation_method'] = 'nearest'
            tech_df[tech_df.index.get_level_values('year').values == min(self.supply.years)]
            util.replace_index_name(tech_df, 'year','vintage')
            tech_df['sensitivity'] = self.scenario
            df_list.append(tech_df)
        df = pd.concat(df_list)
        df = Output.clean_rio_df(df)
        df = df[['name','geography','gau','geography_map_key','interpolation_method','extrapolation_method','year','value','sensitivity']]
        try:
            Output.write_rio(df, "FLEX_TECH_SCHEDULE" + '.csv', self.db_dir + "\\Technology Inputs\\Flex Load", index=False)
        except:
            pdb.set_trace()

    def write_flex_tech_shapes(self):
        df = copy.deepcopy(self.flex_load_df)
        if len(cfg.rio_feeder_geographies)>0:
            for geography in cfg.rio_feeder_geographies:
                for feeder in self.supply.dispatch_feeders:
                    tech_df = util.df_slice(df,[feeder],['dispatch_feeder'])
                    tech_df = util.df_slice(tech_df,[geography],GeoMapper.supply_primary_geography,drop_level=False)
                    tech_df = util.DfOper.divi([tech_df, util.remove_df_levels(tech_df, ['weather_datetime',GeoMapper.supply_primary_geography], 'sum')])
                    #tech_df = tech_df.tz_localize(None, level='weather_datetime')
                    tech_df['sensitivity'] = self.scenario
                    name = "flex_" + geography + "_"+ feeder.lower()
                    tech_df = Output.clean_rio_df(tech_df,add_geography=False)
                    for year in self.supply.dispatch_years:
                        Output.write_rio(tech_df[tech_df['year']==year], name + "_"+ str(year) + "_" + 'sensitivity' + ".csv",
                                     self.db_dir + "\\ShapeData\\" + name + ".csvd" + "\\", index=False,compression='gzip')
                    self.meta_dict['name'].append(name)
                    self.meta_dict['shape_type'].append( 'weather date')
                    self.meta_dict['input_type'].append( 'intensity')
                    self.meta_dict['shape_unit_type'].append('power')
                    self.meta_dict['time_zone'].append(cfg.getParam('dispatch_outputs_timezone'))
                    self.meta_dict['geography'].append(GeoMapper.dispatch_geography)
                    self.meta_dict['geography_map_key'].append(None)
                    self.meta_dict['interpolation_method'].append('linear_interpolation')
                    self.meta_dict['extrapolation_method'].append('nearest')
        for feeder in self.supply.dispatch_feeders:
            tech_df = util.df_slice(df, feeder, 'dispatch_feeder')
            tech_df = util.DfOper.divi([tech_df, util.remove_df_levels(tech_df, 'weather_datetime', 'sum')])
            # tech_df = tech_df.tz_localize(None, level='weather_datetime')
            tech_df['sensitivity'] = self.scenario
            name = "flex_" + feeder.lower()
            tech_df = Output.clean_rio_df(tech_df, add_geography=False)
            for year in self.supply.dispatch_years:
                Output.write_rio(tech_df[tech_df['year']==year], name + "_"+ str(year) + "_" +  self.scenario+".csv",
                                 self.db_dir + "\\ShapeData\\"+name+".csvd"+"\\", index=False,compression='gzip')
            self.meta_dict['name'].append(name)
            self.meta_dict['shape_type'].append('weather date')
            self.meta_dict['input_type'].append('intensity')
            self.meta_dict['shape_unit_type'].append('power')
            self.meta_dict['time_zone'].append(
               cfg.getParam('dispatch_outputs_timezone'))
            self.meta_dict['geography'].append(GeoMapper.dispatch_geography)
            self.meta_dict['geography_map_key'].append(None)
            self.meta_dict['interpolation_method'].append('linear_interpolation')
            self.meta_dict['extrapolation_method'].append('nearest')


    def write_flex_tech_p_max(self):
        df = util.remove_df_levels(util.df_slice(self.flex_load_df,'native','timeshift_type'),'weather_datetime')
        df_list = []
        for geography in cfg.rio_feeder_geographies:
            for feeder in self.supply.dispatch_feeders:
                tech_df = util.df_slice(df,[feeder],['dispatch_feeder'])
                tech_df = util.df_slice(tech_df,[geography],GeoMapper.supply_primary_geography,drop_level=False)
                tech_df['value'] = 1
                tech_df['name'] = geography.lower() + "_" + feeder
                tech_df['source'] = None
                tech_df['notes'] = None
                df['unit'] = 'megawatt'
                tech_df['geography_map_key'] = None
                tech_df['interpolation_method'] = 'linear_interpolation'
                tech_df['extrapolation_method'] = 'nearest'
                tech_df[tech_df.index.get_level_values('year').values == min(self.supply.years)]
                util.replace_index_name(tech_df,'vintage','year')
                tech_df['sensitivity'] = self.scenario
                df_list.append(copy.deepcopy(tech_df))
        for feeder in self.supply.dispatch_feeders:
            tech_df = util.df_slice(df,feeder,'dispatch_feeder')
            tech_df[tech_df.index.get_level_values(GeoMapper.supply_primary_geography).isin(cfg.rio_feeder_geographies)]=0
            tech_df['value'] = 1
            tech_df['name'] = feeder
            tech_df['source'] = None
            tech_df['notes'] = None
            tech_df['unit'] = 'megawatt'
            tech_df['geography_map_key'] = None
            tech_df['interpolation_method'] = 'linear_interpolation'
            tech_df['extrapolation_method'] = 'nearest'
            tech_df[tech_df.index.get_level_values('year').values == min(self.supply.years)]
            util.replace_index_name(tech_df,'vintage','year')
            tech_df['sensitivity'] = self.scenario
            df_list.append(tech_df)
        df = pd.concat(df_list)
        df = Output.clean_rio_df(df)
        df = df[['name', 'source','notes','unit','geography','gau','geography_map_key','interpolation_method','extrapolation_method','vintage','value','sensitivity']]
        Output.write_rio(df, "FLEX_TECH_P_MAX" + '.csv', self.db_dir + "\\Technology Inputs\\Flex Load", index=False)

    def write_flex_tech_p_min(self):
        df = util.remove_df_levels(util.df_slice(self.flex_load_df, 'native', 'timeshift_type'), 'weather_datetime')
        #todo make mins work
        df_list = []
        for geography in cfg.rio_feeder_geographies:
            for feeder in self.supply.dispatch_feeders:
                tech_df = util.df_slice(df,[feeder],['dispatch_feeder'])
                tech_df = util.df_slice(tech_df,[geography],GeoMapper.supply_primary_geography,drop_level=False)
                tech_df['name'] = geography.lower() + "_" + feeder
                tech_df['source'] = None
                tech_df['notes'] = None
                tech_df['unit'] = 'megawatt'
                tech_df['geography_map_key'] = None
                tech_df['interpolation_method'] = 'linear_interpolation'
                tech_df['extrapolation_method'] = 'nearest'
                tech_df[tech_df.index.get_level_values('year').values == min(self.supply.years)]
                util.replace_index_name(tech_df, 'vintage', 'year')
                tech_df['sensitivity'] = self.scenario
                df_list.append(copy.deepcopy(tech_df))
        for feeder in self.supply.dispatch_feeders:
            tech_df = util.df_slice(df, feeder, 'dispatch_feeder')
            tech_df[tech_df.index.get_level_values(GeoMapper.supply_primary_geography).isin(cfg.rio_feeder_geographies)] = 0
            tech_df['name'] = feeder
            tech_df['source'] = None
            tech_df['notes'] = None
            tech_df['unit'] = 'megawatt'
            tech_df['geography_map_key'] = None
            tech_df['interpolation_method'] = 'linear_interpolation'
            tech_df['extrapolation_method'] = 'nearest'
            tech_df[tech_df.index.get_level_values('year').values == min(self.supply.years)]
            util.replace_index_name(tech_df, 'vintage', 'year')
            tech_df['sensitivity'] = self.scenario
            df_list.append(tech_df)
        df = pd.concat(df_list)
        df = Output.clean_rio_df(df)
        df = df[['name', 'source','notes','unit','geography','gau','geography_map_key','interpolation_method','extrapolation_method','vintage','value','sensitivity']]
        Output.write_rio(df, "FLEX_TECH_P_MIN" + '.csv', self.db_dir + "\\Technology Inputs\\Flex Load", index=False)

    def write_flex_tech_energy(self):
        df = util.df_slice(self.flex_load_df, 'native', 'timeshift_type')
        df = df.groupby(level=[x for x in df.index.names if x not in ['weather_datetime']]).sum()
        df_list = []
        for geography in cfg.rio_feeder_geographies:
            for feeder in self.supply.dispatch_feeders:
                tech_df = util.df_slice(df,[feeder],['dispatch_feeder'])
                tech_df['value'] = 1
                tech_df = util.df_slice(tech_df,[geography],GeoMapper.supply_primary_geography,drop_level=False)
                tech_df['name'] = geography.lower() + "_" + feeder
                tech_df['source'] = None
                tech_df['notes'] = None
                tech_df['unit'] = 'megawatt_hour'
                tech_df['geography_map_key'] = None
                tech_df['interpolation_method'] = 'linear_interpolation'
                tech_df['extrapolation_method'] = 'nearest'
                tech_df[tech_df.index.get_level_values('year').values == min(self.supply.years)]
                util.replace_index_name(tech_df, 'vintage', 'year')
                tech_df['sensitivity'] = self.scenario
                df_list.append(copy.deepcopy(tech_df))
        for feeder in self.supply.dispatch_feeders:
            tech_df = util.df_slice(df, feeder, 'dispatch_feeder')
            tech_df['value'] = 1
            tech_df['name'] = feeder
            tech_df['source'] = None
            tech_df['notes'] = None
            tech_df['unit'] = 'megawatt'
            tech_df['geography_map_key'] = None
            tech_df['interpolation_method'] = 'linear_interpolation'
            tech_df['extrapolation_method'] = 'nearest'
            tech_df[tech_df.index.get_level_values('year').values == min(self.supply.years)]
            util.replace_index_name(tech_df, 'vintage', 'year')
            tech_df['sensitivity'] = self.scenario
            df_list.append(tech_df)
        df = pd.concat(df_list)
        df = Output.clean_rio_df(df)
        df = df[['name', 'source', 'notes', 'unit', 'geography', 'gau', 'geography_map_key', 'interpolation_method',
                 'extrapolation_method', 'vintage', 'value', 'sensitivity']]
        Output.write_rio(df, "FLEX_TECH_ENERGY" + '.csv', self.db_dir + "\\Technology Inputs\\Flex Load", index=False)










    def write_conversion(self):
        self.write_conversion_schedule()

    def write_blend(self):
        self.determine_blends()
        self.write_blend_exo_demand()

    def write_topography(self):
        self.write_capacity_zone_load()


    def determine_blends(self):
        blend_node_subset = [x for x in self.supply.blend_nodes if x not in [self.supply.bulk_electricity_node_name,
                                                                             self.supply.thermal_dispatch_node_name,
                                                                             self.supply.distribution_node_name]]
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

    def input_compatibility_check(self, nodes):
        for node in nodes:
            if isinstance(self.supply.nodes[node], SupplyStockNode):
                return True
            elif isinstance(self.supply.nodes[node], ImportNode):
                return True
            elif isinstance(self.supply.nodes[node], PrimaryNode):
                return True
            else:
                continue

    def write_blend_exo_demand(self):
        self.supply.calculate_rio_blend_demand(cfg.rio_opt_demand_subsectors)
        idx = pd.IndexSlice
        df = self.supply.io_rio_supply_df.loc[idx[:, self.blend_node_subset], :]
        df = df.stack().to_frame()
        util.replace_index_name(df, 'year')
        #df[df.index.get_level_values('supply_node') == 'co2 utilization blend A'] = df[df.index.get_level_values('supply_node')== 'Captured CO2 Blend'].values*-1
        df = df[df.index.get_level_values('supply_node') != 'Captured CO2 Blend']
        df = df[df.index.get_level_values('year').isin(self.supply.dispatch_years)]
        df.columns = ['value']
        #todo
        #df[(df.index.get_level_values('supply_node') != 'co2 utilization blend') &(df.values<=0)]=0
        #df[df.values<=0] = 0
        df *= UnitConverter.unit_convert(unit_from_num=cfg.calculation_energy_unit,unit_to_num='TBTU')
        df = Output.clean_rio_df(df)
        util.replace_column_name(df, 'name', 'supply_node')
        df['unit'] = 'TBTU'
        df['interpolation_method'] = 'linear_interpolation'
        df['extrapolation_method'] = 'nearest'
        df['sensitivity'] = self.scenario
        try:
            df = df[['name', 'unit', 'geography', 'gau',
                     'interpolation_method', 'extrapolation_method',
                     'year', 'value', 'sensitivity']]
        except:
            pdb.set_trace()
        Output.write_rio(df, "BLEND_EXO_DEMAND" + '.csv', self.db_dir+'\\Fuel Inputs\\Blends', index=False)



    def write_conversion_schedule(self):
        df_list = []
        for blend in self.blend_node_subset:
            for node in self.supply.nodes[blend].nodes:
                if node not in self.supply.nodes.keys():
                    continue
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
                            df['name'] = node + "_" + \
                                         technology+ "_" + self.blend_node_subset_lookup[blend]
                            df_list.append(df)
        df = pd.concat(df_list)
        df = Output.clean_rio_df(df)
        df['interpolation_method'] = 'linear_interpolation'
        df['extrapolation_method'] = 'nearest'
        df['unit'] = cfg.calculation_energy_unit
        df['time_unit'] = 'hour'
        df['type'] = 'capacity'
        df['sensitivity'] = self.scenario
        df['geography_map_key'] = None
        df = df[['name', 'type', 'unit', 'time_unit',
                 'geography', 'gau', 'geography_map_key', 'interpolation_method', 'extrapolation_method', \
                 'year', 'value', 'sensitivity']]
        Output.write_rio(df, "CONVERSION_SCHEDULE" + '.csv', self.db_dir + "\\Fuel Inputs\\Conversions", index=False)


    def write_capacity_zone_main(self):
        if len(cfg.rio_feeder_geographies):
            name = ['bulk']
            level = ['bulk']
            gau = ['all']
            shape = ['bulk']
            for x in self.supply.dispatch_feeders:
                for y in cfg.rio_feeder_geographies:
                    name.append(
                        y  + "_" + x.lower())
                    level.append('local')
                    gau.append(y)
                    shape.append(
                        y + "_" + x.lower())
        else:
            name = ['bulk']
            level = ['bulk']
            gau = ['all']
            shape = ['bulk']
        df = pd.DataFrame({'name' : name, 'level': level, 'gau': gau, 'shape':shape})
        df = df[['name','level','gau','shape']]
        Output.write_rio(df, "CAPACITY_ZONE_MAIN" + '.csv', self.db_dir + "\\Topography Inputs\\Capacity Zones", index=False)

    def write_capacity_zone_load(self):
        df_list = []
        dist_load, bulk_load = self.flatten_load_dicts()
        if len(cfg.rio_feeder_geographies)>0:
            for geography in cfg.rio_feeder_geographies:
                for feeder in self.supply.dispatch_feeders:
                    df = util.df_slice(dist_load,feeder,'dispatch_feeder')
                    df = util.df_slice(df,geography,GeoMapper.supply_primary_geography,drop_level=False)
                    load_shape_df = util.DfOper.divi([df, util.remove_df_levels(df, 'weather_datetime', 'sum')])
                    #load_shape_df = load_shape_df.tz_localize(None, level='weather_datetime')
                    load_shape_df = Output.clean_rio_df(load_shape_df,add_geography=False)
                    load_shape_df['sensitivity'] = self.scenario
                    df = util.remove_df_levels(df,'weather_datetime')
                    df /= len(Shapes.get_instance().cfg_weather_years)
                    df *= UnitConverter.unit_convert(unit_from=cfg.calculation_energy_unit,unit_to='TWh')
                    df = Output.clean_rio_df(df)
                    df['interpolation_method'] = 'linear_interpolation'
                    df['extrapolation_method'] = 'nearest'
                    df['unit'] = 'TWh'
                    df['sensitivity'] = self.scenario
                    df['name'] = geography.lower() + "_" + feeder.lower()
                    df = df[['name', 'geography', 'gau', 'unit', 'interpolation_method', 'extrapolation_method', \
                         'year', 'value', 'sensitivity']]
                    df_list.append(copy.deepcopy(df))
                    for year in self.supply.years:
                        Output.write_rio(load_shape_df['year']==year, geography.lower() + "_" + feeder.lower() +"_" + str(year)+"_"+ self.scenario + ".csv", self.db_dir + "\\ShapeData\\"+geography.lower() + "_" + feeder.lower() + ".csvd", index=False, compression='gzip')
            df = pd.concat(df_list)
            Output.write_rio(df, "LOCAL_CAPACITY_ZONE_LOAD" + '.csv', self.db_dir + "\\Topography Inputs\Capacity Zones", index=False)
        df_list, load_shape_list = [], []
        for geography in GeoMapper.supply_geographies:
            if geography not in cfg.rio_feeder_geographies:
                dist_load, bulk_load = self.flatten_load_dicts()
                dist_losses, bulk_losses = self.flatten_loss_dicts()
                dist_load_grossed = util.DfOper.mult([dist_load, dist_losses]).groupby(
                        level=[GeoMapper.dispatch_geography, 'year','weather_datetime']).sum()
                df = util.DfOper.add([dist_load_grossed, bulk_load])
                df = util.df_slice(df,geography,GeoMapper.supply_primary_geography, reset_index=True, drop_level=False)
            else:
                df = bulk_load
                df = util.df_slice(df, geography, GeoMapper.supply_primary_geography, reset_index=True, drop_level=False)
            load_shape_df = util.DfOper.divi([df, util.remove_df_levels(df, 'weather_datetime', 'sum')])
            #load_shape_df = load_shape_df.tz_localize(None, level='weather_datetime')
            load_shape_df = Output.clean_rio_df(load_shape_df,add_geography=False)
            load_shape_df['sensitivity'] = self.scenario
            df = util.remove_df_levels(df,'weather_datetime')
            df *=  UnitConverter.unit_convert(unit_from_num=cfg.calculation_energy_unit, unit_to_num='TWh')
            df/=len(Shapes.get_instance().cfg_weather_years)
            df = Output.clean_rio_df(df)
            df['interpolation_method'] = 'linear_interpolation'
            df['extrapolation_method'] = 'nearest'
            df['unit'] = 'TWh'
            df['sensitivity'] = self.scenario
            df['name'] = 'bulk'
            df = df[['name', 'geography', 'gau', 'unit', 'interpolation_method', 'extrapolation_method', \
                     'year', 'value', 'sensitivity']]
            df_list.append(df)
            load_shape_list.append(load_shape_df)
        load_shape = pd.concat(load_shape_list)
        for year in self.supply.dispatch_years:
            Output.write_rio(load_shape[load_shape['year']==year], "bulk" + "_"+ str(year)+ "_"+ self.scenario +".csv", self.db_dir + "\\ShapeData\\bulk.csvd", index=False, compression='gzip')
        df = pd.concat(df_list)
        Output.write_rio(df, "BULK_CAPACITY_ZONE_LOAD" + '.csv', self.db_dir + "\\Topography Inputs\Capacity Zones", index=False)

    def flatten_load_dicts(self):
        dist_list = []
        bulk_list = []
        for year in self.supply.rio_distribution_load.keys():
            dist_df = self.supply.rio_distribution_load[year]
            dist_df.columns = ['value']
            dist_list.append(dist_df)
            bulk_df = self.supply.rio_bulk_load[year]
            bulk_df.columns = ['value']
            bulk_list.append(bulk_df)
        return pd.concat(dist_list, keys=self.supply.rio_distribution_load.keys(), names=['year']), \
               pd.concat(bulk_list, keys=self.supply.rio_distribution_load.keys(), names=['year'])

    def flatten_flex_load_dict(self):
        df_list = []
        years = []
        for year in self.supply.rio_flex_load.keys():
            df = self.supply.rio_flex_load[year]
            if df is not None:
                df.columns = ['value']
                df_list.append(df)
                years.append(year)
        if len(df_list):
            return pd.concat(df_list, keys=years, names=['year'])
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

    def write_demand_subsector(self):
        if self.scenario_index == 0:
            self.write_demand_service_demand()
            self.write_existing_service_demand()
            self.write_existing_energy()
            self.write_demand_tech_main()
            self.write_demand_tech_service_demand()
            self.write_demand_shapes()
            self.write_demand_tech_sales()
            self.write_demand_tech_capital_costs()
            self.write_demand_tech_fixed_om()
            self.write_demand_tech_service_demand_modifier()
            self.write_demand_tech_efficiency()
        else:
            self.write_demand_service_demand()






    def write_demand_tech_sales(self):
        sales_dfs = []
        for subsector_name in cfg.rio_opt_demand_subsectors:
            for sector in model.demand.sectors.values():
                if subsector_name in sector.subsectors.keys():
                    subsector = sector.subsectors[subsector_name]
                    df = subsector.stock.sales
                    util.replace_index_name(df,'name','demand_technology')
                    util.replace_index_name(df, 'vintage', 'year')
                    util.replace_index_name(df, 'gau', GeoMapper.supply_primary_geography)
                    if 'other_index_1'not in df.index.names:
                        df['other_index'] = None
                    elif 'other_index_1'in df.index.names:
                        util.replace_index_name(df, 'other_index', 'other_index_1')
                    if 'other_index_1' and 'other_index_2' in df.index.names:
                        df['other_index'] == [x + "||" + y for x,y in zip(df.index.get_level_values('other_index_1'),df.index.get_level_values('other_index_2'))]
                    df['interpolation_method'] = 'linear_interpolation'
                    df['extrapolation_method'] = 'nearest'
                    df['extrapolation_growth_rate'] = None
                    df['sensitivity'] = None
                    df['geography'] = GeoMapper.supply_primary_geography
                    df = df.reset_index()
                    df = df[['name','geography','gau','interpolation_method','extrapolation_method', 'extrapolation_growth_rate','vintage','other_index','value','sensitivity']]
                    sales_dfs.append(df)
        df = pd.concat(sales_dfs)
        Output.write_rio(df, "DEMAND_TECH_SALES" + '.csv', self.db_dir + "\\Technology Inputs\\Demand", index=False)
        df = df[df['vintage'].isin(self.supply.dispatch_years)]
        df['value'] = 1
        df['interpolation_method'] = 'logistic'
        Output.write_rio(df, "DEMAND_TECH_SALES_CAP" + '.csv', self.db_dir + "\\Technology Inputs\\Demand", index=False)

    def write_demand_service_demand(self):
        service_demand_dfs = []
        subsector_names = []
        for subsector_name in cfg.rio_opt_demand_subsectors:
            for sector in model.demand.sectors.values():
                if subsector_name in sector.subsectors.keys():
                    subsector = sector.subsectors[subsector_name]
                    df = subsector.service_demand.values.stack('year').to_frame()
                    df.columns = ['value']
                    util.replace_index_name(df, 'gau', GeoMapper.supply_primary_geography)
                    if subsector.service_demand.other_index_1 not in df.index.names:
                        df['other_index'] = None
                    if subsector.service_demand.other_index_1 and subsector.service_demand.other_index_2 in df.index.names:
                        df['other_index'] == [x + "||" + y for x,y in zip(df.index.get_level_values(subsector.service_demand.other_index_1),df.index.get_level_values(subsector.service_demand.other_index_2))]
                    elif subsector.service_demand.other_index_1 in df.index.names:
                        util.replace_index_name(df, 'other_index',subsector.service_demand.other_index_1)
                    df['interpolation_method'] = 'linear_interpolation'
                    df['extrapolation_method'] = 'nearest'
                    df['extrapolation_growth_rate'] = None
                    df['source'] = None
                    df['notes'] = None
                    df['sensitivity'] = None
                    df['geography'] = GeoMapper.supply_primary_geography
                    df['unit'] = subsector.service_demand.unit
                    df = df.reset_index()
                    df = df[['source','notes','geography','gau','unit','interpolation_method','extrapolation_method', 'extrapolation_growth_rate','other_index','year','value','sensitivity']]
                    service_demand_dfs.append(df)
                    subsector_names.append(subsector_name)
        df = pd.concat(service_demand_dfs,keys=subsector_names,names=['name']).reset_index()
        del df['level_1']
        Output.write_rio(df, "DEMAND_SERVICE_DEMAND" + '.csv', self.db_dir + "\\Topography Inputs\\Demand", index=False)

    def write_demand_tech_service_demand(self):
        service_demand_dfs = []
        for subsector_name in cfg.rio_opt_demand_subsectors:
            for sector in model.demand.sectors.values():
                if subsector_name in sector.subsectors.keys():
                    subsector = sector.subsectors[subsector_name]
                    df1 = subsector.service_demand.values.stack('year').to_frame()
                    df2 = subsector.stock.total
                    df = util.DfOper.divi([df1,df2])
                    df.columns = ['value']
                    df = util.add_and_set_index(df,'name',subsector.technologies.keys(),)
                    util.replace_index_name(df, 'gau', GeoMapper.supply_primary_geography)
                    if subsector.service_demand.other_index_1 not in df.index.names:
                        df['other_index'] = None
                    if subsector.service_demand.other_index_1 and subsector.service_demand.other_index_2 in df.index.names:
                        df['other_index'] == [x + "||" + y for x,y in zip(df.index.get_level_values(subsector.service_demand.other_index_1),df.index.get_level_values(subsector.service_demand.other_index_2))]
                    elif subsector.service_demand.other_index_1 in df.index.names:
                        util.replace_index_name(df, 'other_index',subsector.service_demand.other_index_1)
                    df['interpolation_method'] = 'linear_interpolation'
                    df['extrapolation_method'] = 'nearest'
                    df['extrapolation_growth_rate'] = None
                    df['source'] = None
                    df['notes'] = None
                    df['sensitivity'] = None
                    df['geography'] = GeoMapper.supply_primary_geography
                    df['unit'] = subsector.service_demand.unit
                    df = df.reset_index()
                    df = df[['name','source','notes','geography','gau','unit','interpolation_method','extrapolation_method', 'extrapolation_growth_rate','other_index','year','value','sensitivity']]
                    service_demand_dfs.append(df)
        df = pd.concat(service_demand_dfs)
        Output.write_rio(df, "DEMAND_TECH_SERVICE_DEMAND" + '.csv', self.db_dir + "\\Technology Inputs\\Demand", index=False)

    def write_existing_service_demand(self):
        service_demand_dfs = []
        for subsector_name in cfg.rio_opt_demand_subsectors:
            for sector in model.demand.sectors.values():
                if subsector_name in sector.subsectors.keys():
                    subsector = sector.subsectors[subsector_name]
                    df = util.DfOper.mult([subsector.stock.values_normal, subsector.service_demand.modifier,subsector.service_demand.values])
                    df = df.stack().to_frame()
                    util.replace_index_name(df,'year')
                    df.columns = ['value']
                    df = df[df.index.get_level_values('vintage')<cfg.rio_start_year]
                    df = util.remove_df_levels(df,['final_energy','demand_technology','vintage'])
                    util.replace_index_name(df, 'gau', GeoMapper.supply_primary_geography)
                    if subsector.service_demand.other_index_1 not in df.index.names:
                        df['other_index'] = None
                    if subsector.service_demand.other_index_1 and subsector.service_demand.other_index_2 in df.index.names:
                        df['other_index'] == [x + "||" + y for x,y in zip(df.index.get_level_values(subsector.service_demand.other_index_1),df.index.get_level_values(subsector.service_demand.other_index_2))]
                    elif subsector.service_demand.other_index_1 in df.index.names:
                        util.replace_index_name(df, 'other_index',subsector.service_demand.other_index_1)
                    df['interpolation_method'] = 'linear_interpolation'
                    df['extrapolation_method'] = 'nearest'
                    df['extrapolation_growth_rate'] = None
                    df['source'] = None
                    df['notes'] = None
                    df['sensitivity'] = None
                    df['geography'] = GeoMapper.supply_primary_geography
                    df['unit'] = subsector.service_demand.unit
                    df['name'] = subsector_name
                    df = df.reset_index()
                    df = df[['name','source','notes','geography','gau','unit','interpolation_method','extrapolation_method', 'extrapolation_growth_rate','other_index','year','value','sensitivity']]
                    service_demand_dfs.append(df)
        df = pd.concat(service_demand_dfs)
        Output.write_rio(df, "DEMAND_EXISTING_SERVICE_DEMAND" + '.csv', self.db_dir + "\\Topography Inputs\\Demand", index=False)

    def write_existing_energy(self):
        demand_dfs = []
        for subsector_name in cfg.rio_opt_demand_subsectors:
            for sector in model.demand.sectors.values():
                if subsector_name in sector.subsectors.keys():
                    subsector = sector.subsectors[subsector_name]
                    df = subsector.energy_forecast
                    df = df[df.index.get_level_values('vintage')<cfg.rio_start_year]
                    df = util.remove_df_levels(df,['vintage'])
                    util.replace_index_name(df, 'gau', GeoMapper.supply_primary_geography)
                    util.replace_index_name(df,'blend_in','final_energy')
                    util.replace_index_name(df,'name','demand_technology')
                    if 'other_index_1' not in df.index.names:
                        df['other_index'] = None
                    elif 'other_index_1' and 'other_index_2' in df.index.names:
                        df['other_index'] == [x + "||" + y for x,y in zip(df.index.get_level_values(subsector.service_demand.other_index_1),df.index.get_level_values(subsector.service_demand.other_index_2))]
                    elif 'other_index_1' in df.index.names:
                        util.replace_index_name(df, 'other_index','other_index_1')
                    df['interpolation_method'] = 'linear_interpolation'
                    df['extrapolation_method'] = 'nearest'
                    df['extrapolation_growth_rate'] = None
                    df['source'] = None
                    df['notes'] = None
                    df['sensitivity'] = None
                    df['geography'] = GeoMapper.supply_primary_geography
                    df['unit'] = cfg.calculation_energy_unit
                    #df['name'] = subsector_name
                    df = df.reset_index()
                    df = df[['name','source','notes','geography','gau','unit','interpolation_method','extrapolation_method', 'extrapolation_growth_rate','other_index',
                             'blend_in','year','value','sensitivity']]
                    demand_dfs.append(df)
        df = pd.concat(demand_dfs)
        Output.write_rio(df[df['blend_in'].values=='electricity'], "DEMAND_EXISTING_ELECTRICITY_DEMAND" + '.csv', self.db_dir + "\\Technology Inputs\\Demand", index=False)
        Output.write_rio(df[df['blend_in'].values != 'electricity'], "DEMAND_EXISTING_BLEND_DEMAND" + '.csv', self.db_dir + "\\Technology Inputs\\Demand", index=False)




    def write_demand_tech_sales_cap(self):
        sales_dfs = []
        for subsector_name in cfg.rio_opt_demand_subsectors:
            for sector in model.demand.sectors.values():
                if subsector_name in sector.subsectors.keys():
                    subsector = sector.subsectors[subsector_name]
                    df = subsector.stock.sales
                    util.replace_index_name(df,'name','demand_technology')
                    util.replace_index_name(df, 'vintage', 'year')
                    util.replace_index_name(df, 'gau', GeoMapper.supply_primary_geography)
                    if 'other_index_1'not in df.index.names:
                        df['other_index'] = None
                    elif 'other_index_1'in df.index.names:
                        util.replace_index_name(df, 'other_index', 'other_index_1')
                    if 'other_index_1' and 'other_index_2' in df.index.names:
                        df['other_index'] == [x + "||" + y for x,y in zip(df.index.get_level_values('other_index_1'),df.index.get_level_values('other_index_2'))]
                    df['interpolation_method'] = 'linear_interpolation'
                    df['extrapolation_method'] = 'nearest'
                    df['extrapolation_growth_rate'] = None
                    df['sensitivity'] = None
                    df['geography'] = GeoMapper.supply_primary_geography
                    df = df.reset_index()
                    df = df[['name','geography','gau','interpolation_method','extrapolation_method', 'extrapolation_growth_rate','vintage','other_index','value','sensitivity']]
                    sales_dfs.append(df)
        df = pd.concat(sales_dfs)
        Output.write_rio(df, "DEMAND_TECH_SALES" + '.csv', self.db_dir + "\\Technology Inputs\\Demand", index=False)
        df = df[df['vintage'].isin(self.supply.dispatch_years)]
        df['value'] = 1
        df['interpolation_method'] = 'logistic'
        Output.write_rio(df, "DEMAND_TECH_SALES_CAP" + '.csv', self.db_dir + "\\Technology Inputs\\Demand", index=False)


    def write_demand_tech_capital_costs(self):
        tech_dfs = []
        for subsector_name in cfg.rio_opt_demand_subsectors:
            for sector in model.demand.sectors.values():
                if subsector_name in sector.subsectors.keys():
                    subsector = sector.subsectors[subsector_name]
                    for technology in subsector.technologies.values():
                        df = util.DfOper.add([technology.capital_cost_new.values,technology.installation_cost_new.values if hasattr(technology.installation_cost_new,'values') else None])
                        df = GeoMapper.geo_map(df, GeoMapper.supply_primary_geography, technology.capital_cost_new.geography,'intensity', geography_map_key=None, fill_value=0, filter_geo=False, remove_current_geography=True)
                        util.replace_index_name(df,'name','demand_technology')
                        util.replace_index_name(df, 'gau',technology.capital_cost_new.geography)
                        length = len([x for x in [technology.capital_cost_new.other_index_1,technology.capital_cost_new.other_index_2] if x is not None])
                        if length == 0:
                            df['other_index'] = None
                        elif length == 1:
                            util.replace_index_name(df, 'other_index', technology.capital_cost_new.other_index_1)
                        elif length ==2:
                            df['other_index'] == df.index.get_level_values(technology.capital_cost_new.other_index_1) + "||" + df.index.get_level_values(technology.capital_cost_new.other_index_2)
                        df['interpolation_method'] = 'linear_interpolation'
                        df['extrapolation_method'] = 'nearest'
                        df['extrapolation_growth_rate'] = None
                        df['sensitivity'] = None
                        df['geography'] = technology.capital_cost_new.geography
                        df['currency'] = cfg.currency_name
                        df['currency_year'] = cfg.getParamAsInt('currency_year')
                        df['source'] = None
                        df['notes'] = None
                        df = df.reset_index()
                        df = df[['name','source','notes','geography','gau','interpolation_method','extrapolation_method', 'extrapolation_growth_rate','currency','currency_year','other_index','vintage','value','sensitivity']]
                        tech_dfs.append(df)
        df = pd.concat(tech_dfs)
        Output.write_rio(df.drop_duplicates(subset=df.columns.difference(['vintage'])), "DEMAND_TECH_CAPITAL_COST" + '.csv', self.db_dir + "\\Technology Inputs\\Demand", index=False)

    def write_demand_tech_fixed_om(self):
        tech_dfs = []
        for subsector_name in cfg.rio_opt_demand_subsectors:
            for sector in model.demand.sectors.values():
                if subsector_name in sector.subsectors.keys():
                    subsector = sector.subsectors[subsector_name]
                    for technology in subsector.technologies.values():
                        if not hasattr(technology.fixed_om,'values'):
                            continue
                        df = technology.fixed_om.values
                        df = GeoMapper.geo_map(df, GeoMapper.supply_primary_geography, technology.fixed_om.geography, 'intensity', geography_map_key=None, fill_value=0, filter_geo=False, remove_current_geography=True)
                        util.replace_index_name(df,'name','demand_technology')
                        util.replace_index_name(df, 'gau', technology.fixed_om.geography)
                        length = len([x for x in [technology.fixed_om.other_index_1,technology.fixed_om.other_index_2] if x is not None])
                        if length == 0:
                            df['other_index'] = None
                        elif length == 1:
                            util.replace_index_name(df, 'other_index',technology.fixed_om.other_index_1)
                        elif length ==2:
                            df['other_index'] == df.index.get_level_values(technology.fixed_om.other_index_1) + "||" + df.index.get_level_values(technology.fixed_om.other_index_2)
                        df['interpolation_method'] = 'linear_interpolation'
                        df['extrapolation_method'] = 'nearest'
                        df['extrapolation_growth_rate'] = None
                        df['sensitivity'] = None
                        df['geography'] = GeoMapper.supply_primary_geography
                        df['currency'] = cfg.currency_name
                        df['currency_year'] = cfg.getParamAsInt('currency_year')
                        df['source'] = None
                        df['notes'] = None
                        df = df.reset_index()
                        df['year'] = df['vintage']
                        df = df[['name','source','notes','geography','gau','interpolation_method','extrapolation_method', 'extrapolation_growth_rate','currency','currency_year','other_index','vintage','year','value','sensitivity']]
                        tech_dfs.append(df)
        df = pd.concat(tech_dfs)
        Output.write_rio(df.drop_duplicates(subset=df.columns.difference(['vintage','year'])), "DEMAND_TECH_FIXED_OM" + '.csv', self.db_dir + "\\Technology Inputs\\Demand", index=False)

    def write_demand_tech_efficiency(self):
        tech_dfs = []
        for subsector_name in cfg.rio_opt_demand_subsectors:
            for sector in model.demand.sectors.values():
                if subsector_name in sector.subsectors.keys():
                    subsector = sector.subsectors[subsector_name]
                    for technology in subsector.technologies.values():
                        efficiency = technology.efficiency_main.values[max(self.supply.dispatch_years)].to_frame()
                        efficiency.columns = ['value']
                        if len(GeoMapper.geography_to_gau[technology.efficiency_main.geography])>1:
                            geography = GeoMapper.supply_primary_geography
                        else:
                            efficiency = GeoMapper.geo_map(efficiency, GeoMapper.supply_primary_geography, technology.efficiency_main.geography, 'intensity', geography_map_key= technology.efficiency_main.geography_map_key, fill_value=0, filter_geo=False, remove_current_geography=True)
                            geography = technology.efficiency_main.geography

                        if technology.efficiency_main.utility_factor !=1:
                            efficiency_aux = technology.efficiency_aux.values[max(self.supply.dispatch_years)].to_frame() if hasattr(technology.efficiency_aux,'values') else None
                            efficiency_aux.columns = ['value']
                            if len(GeoMapper.geography_to_gau[technology.efficiency_main.geography]) == 1:
                                efficiency_aux = GeoMapper.geo_map(efficiency_aux, GeoMapper.supply_primary_geography, technology.efficiency_main.geography, 'intensity', geography_map_key=technology.efficiency_main.geography_map_key, fill_value=0, filter_geo=False, remove_current_geography=True)
                            efficiency_aux *= 1- technology.efficiency_main.utility_factor
                            efficiency_main = efficiency * technology.efficiency_main.utility_factor
                            efficiency = util.DfOper.add([efficiency_aux,efficiency_main])
                        df = efficiency
                        util.replace_index_name(df,'name','demand_technology')
                        util.replace_index_name(df, 'gau', geography)
                        util.replace_index_name(df, 'blend_in', 'final_energy')
                        length = len([x for x in [technology.efficiency_main.other_index_1,technology.efficiency_main.other_index_2] if x is not None])
                        if length == 0:
                            df['other_index'] = None
                        elif length == 1:
                            util.replace_index_name(df, 'other_index', technology.efficiency_main.other_index_1)
                        elif length ==2:
                            df['other_index'] == df.index.get_level_values(technology.efficiency_main.other_index_1) + "||" + df.index.get_level_values(technology.efficiency_main.other_index_2)
                        df['interpolation_method'] = 'logistic'
                        df['extrapolation_method'] = 'nearest'
                        df['extrapolation_growth_rate'] = None
                        df['sensitivity'] = None
                        df['geography'] = geography
                        df['source'] = None
                        df['notes'] = None
                        df['is_numerator_service'] = True
                        energy_unit_to = technology.efficiency_main.denominator_unit if technology.efficiency_main.is_numerator_service else technology.efficiency_main.numerator_unit
                        df['denominator_unit'] =  energy_unit_to
                        df['numerator_unit'] = technology.service_demand_unit
                        df = df.reset_index()
                        df['value'] = 1/df['value']
                        df['value']*= UnitConverter.unit_convert(1,
                                                   unit_from_den=cfg.calculation_energy_unit,
                                                   unit_to_den=energy_unit_to)
                        df = df[['name','source','notes','geography','gau','interpolation_method','extrapolation_method', 'extrapolation_growth_rate',
                                 'is_numerator_service','numerator_unit','denominator_unit','blend_in','other_index','vintage','value','sensitivity']]
                        tech_dfs.append(df)
        df = pd.concat(tech_dfs)
        Output.write_rio(df[~df['blend_in'].isin(['electricity'])].drop_duplicates(subset=df.columns.difference(['vintage'])), "DEMAND_TECH_BLEND_EFFICIENCY" + '.csv', self.db_dir + "\\Technology Inputs\\Demand", index=False)
        electric_df = df[df['blend_in'].isin(['electricity'])]
        electric_df = electric_df.drop('blend_in')
        Output.write_rio(electric_df.drop('blend_in').drop_duplicates(subset=electric_df.columns.difference(['vintage'])),"DEMAND_TECH_ELECTRIC_EFFICIENCY" + '.csv', self.db_dir + "\\Technology Inputs\\Demand", index=False)


    def write_demand_tech_service_demand_modifier(self):
        tech_dfs = []
        tech_names = []
        for subsector_name in cfg.rio_opt_demand_subsectors:
            for sector in model.demand.sectors.values():
                if subsector_name in sector.subsectors.keys():
                    subsector = sector.subsectors[subsector_name]
                    for technology in subsector.technologies.values():
                        if not hasattr(technology.service_demand_modifier,'values'):
                            continue
                        df = technology.service_demand_modifier.values
                        df = df.stack('year').to_frame()
                        df.columns = ['value']
                        df = GeoMapper.geo_map(df, GeoMapper.supply_primary_geography, technology.service_demand_modifier.geography, 'intensity', geography_map_key=None, fill_value=0, filter_geo=False, remove_current_geography=True)
                        util.replace_index_name(df,'name','demand_technology')
                        util.replace_index_name(df, 'gau', technology.service_demand_modifier.geography)
                        length = len([x for x in [technology.service_demand_modifier.other_index_1,technology.service_demand_modifier.other_index_2] if x is not None])
                        if length == 0:
                            df['other_index'] = None
                        elif length == 1:
                            util.replace_index_name(df, 'other_index', technology.service_demand_modifier.other_index_1)
                        elif length ==2:
                            df['other_index'] == df.index.get_level_values(technology.service_demand_modifier.other_index_1) + "||" + df.index.get_level_values(technology.service_demand_modifier.other_index_2)
                        df['interpolation_method'] = 'logistic'
                        df['extrapolation_method'] = 'nearest'
                        df['extrapolation_growth_rate'] = None
                        df['sensitivity'] = None
                        df['geography'] = GeoMapper.supply_primary_geography
                        df['source'] = None
                        df['notes'] = None
                        df = df.reset_index()
                        df = df[['source','notes','geography','gau','interpolation_method','extrapolation_method', 'extrapolation_growth_rate',
                                 'other_index','vintage','year','value','sensitivity']]
                        tech_dfs.append(df)
                        tech_names.append(technology.name)
        df = pd.concat(tech_dfs,keys=tech_names,names=['name']).reset_index()
        del df['level_1']
        Output.write_rio(df.drop_duplicates(subset=df.columns.difference(['vintage','year'])), "DEMAND_TECH_SERVICE_DEMAND_MODIFIER" + '.csv', self.db_dir + "\\Technology Inputs\\Demand", index=False)




    def write_demand_tech_main(self):
        dct = defaultdict(list)
        for subsector_name in cfg.rio_opt_demand_subsectors:
            for sector in model.demand.sectors.values():
                if subsector_name in sector.subsectors.keys():
                    subsector = sector.subsectors[subsector_name]
                    for tech in subsector.technologies.values():
                        dct['name'].append(tech.name)
                        dct['subsector'].append(subsector_name)
                        dct['lifetime'].append(tech.mean_lifetime)
                        dct['demand_tech_unit_type'].append(tech.demand_tech_unit_type)
                        dct['unit'].append(tech.unit)
                        dct['time_unit'].append(tech.time_unit)
                        dct['shape'].append('flat' if tech.shape==None else tech.shape)
        df = pd.DataFrame(dct)
        Output.write_rio(df, "DEMAND_TECH_MAIN" + '.csv', self.db_dir + "\\Technology Inputs\\Demand", index=False)

def run(path, config, scenarios):
    global model
    cfg.initialize_config()
    GeoMapper.get_instance().log_geo()
    Shapes.get_instance(cfg.getParam('database_path'))
    
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
        export = RioExport(model,scenario_index,scenario)
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
    workingdir = r'E:\EP_Runs\EDF'
    os.chdir(workingdir)
    config = 'config.INI'
    scenario = ['Aggressive Policy Support','Modest Policy Support']
    export = run(workingdir, config, scenario)
    self = export
