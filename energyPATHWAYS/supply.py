__author__ = 'Ben Haley & Ryan Jones'

import config as cfg
import util
import pandas as pd
import numpy as np
import copy
import logging
import time
from util import DfOper
from collections import defaultdict
from supply_measures import BlendMeasure, RioBlendMeasure, CO2PriceMeasure
from supply_technologies import SupplyTechnology, StorageTechnology
from supply_classes import SupplySpecifiedStock, SupplyStock
from shared_classes import SalesShare, SpecifiedStock, Stock, StockItem
from rollover import Rollover
from solve_io import solve_IO
from dispatch_classes import Dispatch, DispatchFeederAllocation
import dispatch_classes
import inspect
import operator
from shape import Shapes, Shape
from outputs import Output
from multiprocessing import Pool, cpu_count
import energyPATHWAYS.helper_multiprocess as helper_multiprocess
import pdb
import os
from datetime import datetime
import random
import dispatch_budget
import dispatch_generators
from unit_converter import UnitConverter
from geomapper import GeoMapper
from energyPATHWAYS.generated import schema
from data_object import DataObject

#def node_update_stock(node):
#    if hasattr(node, 'stock'):
#        node.update_stock(node.year,node.loop)
#    return node
           
class Supply(object):

    """This module calculates all supply nodes in an IO loop to calculate energy,
    emissions, and cost flows through the energy economy
    """    
    def __init__(self, scenario, demand_object=None, api_run=False,rio_scenario=None):
        """Initializes supply instance"""
        self.all_nodes, self.blend_nodes, self.non_storage_nodes, self.storage_nodes = [], [], [], []
        self.nodes = {}
        self.demand_object = demand_object # used to retrieve results from demand-side
        self.scenario = scenario # used in writing dispatch outputs
        self.rio_scenario = rio_scenario
        self.demand_sectors = demand_object.sectors.keys()
        self.demand_sectors.sort()
        self.thermal_dispatch_node_name = cfg.getParam('thermal_dispatch_node', 'opt')
        self.distribution_node_name = cfg.getParam('distribution_node', 'opt')
        self.distribution_grid_node_name = cfg.getParam('distribution_grid_node', 'opt')
        self.transmission_node_name = cfg.getParam('transmission_node', 'opt')
        self.dispatch_zones = [self.distribution_node_name, self.transmission_node_name]
        self.electricity_nodes = defaultdict(list)
        self.injection_nodes = defaultdict(list)
        self.ghgs = util.csv_read_table('GreenhouseGases', 'name', return_iterable=True)
        self.dispatch_feeder_allocation = demand_object.get_weighted_feeder_allocation_by_sector()
        self.dispatch_feeders = sorted(self.dispatch_feeder_allocation.index.get_level_values('dispatch_feeder').unique())
        self.dispatch = Dispatch(self.dispatch_feeders, GeoMapper.dispatch_geography, GeoMapper.dispatch_geographies, self.scenario)
        self.outputs = Output()
        self.outputs.hourly_dispatch_results = None
        self.outputs.hourly_marginal_cost = None
        self.outputs.hourly_production_cost = None
        self.active_thermal_dispatch_df_list = []
        self.map_dict = dict(util.csv_read_table('SupplyNodes', ['final_energy_link', 'name']))
        self.api_run = api_run
        if self.map_dict.has_key(None):
            del self.map_dict[None]
        self.add_co2_price_to_dispatch(scenario)
        self.rio_distribution_losses = dict()
        self.rio_transmission_losses = dict()
        self.rio_distribution_load = dict()
        self.rio_flex_load = dict()
        self.rio_bulk_load = dict()
        self.rio_flex_pmin = dict
        self.rio_flex_pmax = dict()
        self.add_rio_inputs()


    def add_co2_price_to_dispatch(self, scenario):
        self.CO2PriceMeasures = scenario.get_measures('CO2PriceMeasures', self.thermal_dispatch_node_name)
        if len(self.CO2PriceMeasures)>1:
             raise ValueError('multiple CO2 price measures are active')
        elif len(self.CO2PriceMeasures)==1:
            self.CO2PriceMeasure = CO2PriceMeasure(self.CO2PriceMeasures[0], scenario)
            self.CO2PriceMeasure.calculate()
        else:
            self.CO2PriceMeasure = None


    def calculate_technologies(self):
        """ initiates calculation of all technology attributes - costs, efficiency, etc.
        """
        for node in self.nodes.values():
            if not hasattr(node, 'technologies'):
                continue

            for technology in node.technologies.values():
                technology.calculate([node.vintages[0] - 1] + node.vintages, node.years)

            # indentation is correct
            if isinstance(technology, StorageTechnology):
                node.remap_tech_attrs(cfg.storage_tech_classes)
            else:
                node.remap_tech_attrs(cfg.tech_classes)

    def aggregate_results(self):
        def remove_na_levels(df):
            if df is None:
                return None
            levels_with_na_only = [name for level, name in zip(df.index.levels, df.index.names) if list(level)==[u'N/A']]
            return util.remove_df_levels(df, levels_with_na_only).sort_index()

        output_list = ['stock', 'annual_costs', 'levelized_costs', 'capacity_utilization']
        for output_name in output_list:
            df = self.group_output(output_name)
            df = remove_na_levels(df) # if a level only as N/A values, we should remove it from the final outputs
            setattr(self.outputs, "s_"+output_name, df)
        setattr(self.outputs,'s_energy',self.format_output_io_supply())

    def format_output_io_supply(self):
        energy = self.io_supply_df.stack().to_frame()
        util.replace_index_name(energy,'year')
        energy_unit = cfg.calculation_energy_unit
        energy.columns = [energy_unit.upper()]
        return energy

    def group_output(self, output_type, levels_to_keep=None):
        levels_to_keep = cfg.output_supply_levels if levels_to_keep is None else levels_to_keep
        dfs = [node.group_output(output_type, levels_to_keep) for node in self.nodes.values()]
        if all([df is None for df in dfs]) or not len(dfs):
            return None
        keys = [node.name for node in self.nodes.values()]
        dfs, keys = zip(*[(df, key) for df, key in zip(dfs, keys) if df is not None])
        new_names = 'supply_node'
        return util.df_list_concatenate(dfs, keys, new_names, levels_to_keep)

    def calculate_years(self):
        """
        Determines the period of stock rollover within a node based on the minimum year
        of specified sales or stock.
        """
        for node in self.nodes.values():
            node.min_year = cfg.getParamAsInt('current_year')
            if hasattr(node,'technologies'):
                for technology in node.technologies.values():
                    for reference_sales in technology.reference_sales.values():
                           min_year = min(reference_sales.raw_values.index.levels[util.position_in_index(reference_sales.raw_values, 'vintage')])
                           if min_year < node.min_year:
                               node.min_year = min_year
                    for sales in technology.sales.values():
                          min_year = min(sales.raw_values.index.get_level_values('vintage'))
                          if min_year < node.min_year:
                              node.min_year = min_year
            if hasattr(node,'stock') and node.stock.raw_values is not None:
                    min_year = min(node.stock.raw_values.index.levels[util.position_in_index(node.stock.raw_values, 'year')])
                    if min_year < node.min_year:
                        node.min_year = min_year
            node.min_year = int(max(node.min_year, cfg.getParamAsInt('supply_start_year')))
            node.years = range(node.min_year, cfg.getParamAsInt('end_year') + cfg.getParamAsInt('year_step'), cfg.getParamAsInt('year_step'))
            node.vintages = copy.deepcopy(node.years)
        self.years = cfg.supply_years
        self.years_subset = cfg.combined_years_subset

    def initial_calculate(self):
        """Calculates all nodes in years before IO loop"""
        logging.info("Calculating supply-side prior to current year")
        self.calculate_years()
        self.add_empty_output_df()
        logging.info("Creating input-output table")
        self.create_IO()
        self.create_inverse_dict()
        self.cost_dict = util.recursivedict()
        self.emissions_dict = util.recursivedict()
        self.create_embodied_cost_and_energy_demand_link()
        self.create_embodied_emissions_demand_link()
        logging.info("Initiating calculation of technology attributes")
        self.calculate_technologies()
        logging.info("Running stock rollover prior to current year")
        self.calculate_nodes()
        self.calculate_initial_demand()

    def final_calculate(self):
        self.concatenate_annual_costs()
        self.concatenate_levelized_costs()
        self.calculate_capacity_utilization()

    def calculate_nodes(self):
        """Performs an initial calculation for all import, conversion, delivery, and storage nodes"""
        if cfg.getParamAsBoolean('parallel_process'):
            nodes = helper_multiprocess.safe_pool(helper_multiprocess.node_calculate, self.nodes.values())
            self.nodes = dict(zip(self.nodes.keys(), nodes))
        else:
            for node in self.nodes.values():
                if node.name ==self.bulk_electricity_node_name and cfg.rio_supply_run:
                    node.calculate(calculate_residual=False)
                else:
                    node.calculate()
        for node in self.nodes.values():
            if node.name in self.blend_nodes and node.name in cfg.evolved_blend_nodes and cfg.evolved_run=='true':
                node.values = node.values.groupby(level=[x for x in node.values.index.names if x !='supply_node']).transform(lambda x: 1/float(x.count()))
                for x in node.nodes:
                    if x in self.storage_nodes:
                        indexer = util.level_specific_indexer(node.values,'supply_node',x)
                        node.values.loc[indexer,:] = 1e-7 * 4
                node.values = node.values.groupby(level=[x for x in node.values.index.names if x !='supply_node']).transform(lambda x: x/x.sum())/4.0


    def create_IO(self):
        """Creates a dictionary with year and demand sector keys to store IO table structure"""
        self.io_dict = util.recursivedict()
        index =  pd.MultiIndex.from_product([GeoMapper.supply_geographies, self.all_nodes], names=[GeoMapper.supply_primary_geography, 'supply_node'])
        for year in self.years:
            for sector in util.ensure_iterable(self.demand_sectors):
                self.io_dict[year][sector] = util.empty_df(index = index, columns = index, fill_value=0.0).sort_index(axis=0).sort_index(axis=1)

        self.io_dict = util.freeze_recursivedict(self.io_dict)

    def add_rio_inputs(self):
        if cfg.rio_supply_run:
            self.rio_inputs = RioInputs(self.rio_scenario, self)
            self.dispatch.transmission.constraints.values = self.rio_inputs.transmission_constraint
            self.dispatch.transmission.constraints.clean_timeseries(attr='values', inplace=True, time_index=cfg.supply_years,
                                  time_index_name='year', interpolation_method=self.dispatch.transmission.constraints.interpolation_method,
                                  extrapolation_method=self.dispatch.transmission.constraints.extrapolation_method)


    def add_nodes(self):
        """Adds node instances for all active supply nodes"""
        logging.info('Adding supply nodes')
        supply_nodes = util.csv_read_table('SupplyNodes', column_names=['name', 'supply_type', 'is_active'], return_iterable=True)
        supply_nodes.sort()
        for name, supply_type, is_active in supply_nodes:
            if is_active:
                self.all_nodes.append(name)
                logging.info('    {} node {}'.format(supply_type, name))
                self.add_node(name, supply_type, self.scenario)


        # this ideally should be moved to the init statements for each of the nodes
        for node in self.nodes.values():
            node.demand_sectors = self.demand_sectors
            node.ghgs = self.ghgs
            node.distribution_grid_node_name = self.distribution_grid_node_name

            # for some reason, when this next part gets moved to the init for node, the DR node ends up having a tradeable geography of none
            if node.tradable_geography is None:
                node.enforce_tradable_geography = False
                node.tradable_geography = GeoMapper.supply_primary_geography
            else:
                node.enforce_tradable_geography = True

    def add_node(self, name, supply_type, scenario):
        """Add node to Supply instance
        Args:
            name (int): supply node id
            supply_type (str): supply type i.e. 'blend'
        """
        if supply_type == "Blend":
            self.nodes[name] = BlendNode(name, scenario)
            self.blend_nodes.append(name)

        elif supply_type == "Storage":
            if len(util.csv_read_table('SupplyTechs', 'supply_node', supply_node=name, return_iterable=True)):
                self.nodes[name] = StorageNode(name, scenario)
            else:
                logging.debug(ValueError('insufficient data in storage node %s' % name))

        elif supply_type == "Import":
            self.nodes[name] = ImportNode(name, scenario)

        elif supply_type == "Primary":
            self.nodes[name] = PrimaryNode(name, scenario)

        else:
            if len(util.csv_read_table('SupplyEfficiency', 'name', name=name, return_iterable=True)):
                self.nodes[name] = SupplyNode(name, scenario)
            elif len(util.csv_read_table('SupplyTechs', 'supply_node', supply_node=name, return_iterable=True)):
                self.nodes[name] = SupplyStockNode(name, scenario)
            elif len(util.csv_read_table('SupplyStock', 'supply_node', supply_node=name, return_iterable=True)):
                self.nodes[name] = SupplyNode(name, scenario)
            else:
                logging.debug(ValueError('insufficient data in supply node %s' % name))

        if supply_type != "Storage":
            self.non_storage_nodes.append(name)
        else:
            self.storage_nodes.append(name)

    def reformat_gen_share_measures(self,df):
        def find_supply_node(x):
            for node in self.nodes.values():
                if hasattr(node,'technologies') and x in node.technologies.keys():
                    return node.name
        df['supply_node'] = [find_supply_node(x) for x in df.index.get_level_values('technology')]
        df = df.set_index('supply_node',append=True)
        df = df.groupby(level=['year',cfg.rio_geography,'supply_node']).sum()
        return df

    def reformat_fuel_share_measures(self,df):
        df = copy.deepcopy(df)
        def find_supply_node(y):
            for node in self.nodes.values():
                if hasattr(node,'technologies') and y.lower() in [x.lower() for x in node.technologies.keys()]:
                    return node.name
                elif not hasattr(node,'technologies') and y.lower()==node.name.lower():
                    return node.name
            return y
        df['supply_node'] = [find_supply_node(x) for x in df.index.get_level_values('ep_fuel')]
        df = df.set_index('supply_node',append=True)
        df = df.groupby(level=['year', 'blend',cfg.rio_geography,'supply_node']).sum()
        return df



    def reformat_delivered_gen(self,df):
        if df is not None:
            def find_supply_node(x):
                for node in self.nodes.values():
                    if hasattr(node,'technologies') and x in node.technologies.keys():
                        return node.name
            df['supply_node'] = [find_supply_node(x) for x in df.index.get_level_values('technology')]
            df = df.set_index('supply_node',append=True)
            df = df.groupby(level=['year',cfg.rio_geography + "_from",'supply_node']).sum()
            return df
        else:
            return None



    def reformat_bulk_thermal_share_measures(self,df):
        df['supply_node'] = self.thermal_dispatch_node_name
        df = df.set_index('supply_node',append=True)
        return df


    def add_measures(self):
        """ Adds measures to supply nodes based on scenario inputs"""
        logging.info('Adding supply measures')
        scenario = self.scenario
        self.discover_bulk_name()
        if cfg.rio_supply_run:
            #reformats from technology/supply node to supply node for blend measures
            self.rio_inputs.zonal_fuel_outputs = self.reformat_fuel_share_measures(self.rio_inputs.
                                                                               zonal_fuel_outputs)
            self.rio_inputs.fuel_outputs = self.reformat_fuel_share_measures(self.rio_inputs.
                                                                         fuel_outputs)
        for node in self.nodes.values():
            #all nodes have export measures
            if cfg.rio_supply_run and node.name in cfg.rio_export_blends:
                df = self.rio_inputs.zonal_fuel_exports[
                    self.rio_inputs.zonal_fuel_exports.index.get_level_values('blend') == node.name]
                node.export = RioExport(node.name, df)
            elif cfg.rio_supply_run and node.name in cfg.rio_outflow_products:
                    df = self.rio_inputs.product_exports[
                        self.rio_inputs.product_exports.index.get_level_values('supply_node') == node.name]
                    node.export = RioExport(node.name, df)
            else:
                node.add_exports(scenario)
            #once measures are loaded, export classes can be initiated
            if node.supply_type == 'Blend':
                if cfg.rio_supply_run and node.name!=self.bulk_electricity_node_name and node.name!=self.distribution_node_name and node.name!=self.thermal_dispatch_node_name and node.name not in cfg.rio_excluded_blends:
                    node.add_rio_fuel_blend_measures(self.rio_inputs)
                elif cfg.rio_supply_run and node.name==self.bulk_electricity_node_name:
                    node.blend_measures = dict()
                    node.add_rio_bulk_blend_measures(self.reformat_gen_share_measures(self.rio_inputs.bulk_share))
                    node.add_rio_bulk_blend_measures(self.reformat_bulk_thermal_share_measures(self.rio_inputs.bulk_thermal_share))
                    node.rio_trades = self.rio_inputs.electricity_trades
                    node.delivered_gen = self.reformat_delivered_gen(self.rio_inputs.cleaned_delivered_gen)
                elif cfg.rio_supply_run and node.name == self.thermal_dispatch_node_name:
                    node.add_rio_thermal_blend_measures(self.reformat_gen_share_measures(self.rio_inputs.thermal_share))
                else:
                    node.add_blend_measures(scenario)
                if cfg.rio_supply_run and node.name in self.rio_inputs.blend_levelized_costs.index.get_level_values('supply_node'):
                    df = util.df_slice(self.rio_inputs.blend_levelized_costs,node.name,'supply_node').unstack('year')
                    df.columns = df.columns.droplevel()
                    node.levelized_costs = df
            elif isinstance(node, SupplyStockNode) or isinstance(node, StorageNode):
                node.add_total_stock_measures(scenario)
                for technology in node.technologies.values():
                    if cfg.rio_supply_run and technology.name not in cfg.rio_excluded_technologies:
                        technology.add_rio_stock_measures(self.rio_inputs)
                        technology.sales = {}
                        technology.sales_shares = {}
                    else:
                        technology.add_sales_measures(scenario)
                        technology.add_sales_share_measures(scenario)
                        technology.add_specified_stock_measures(scenario)
                    if cfg.rio_supply_run and self.rio_inputs.dual_fuel_efficiency is not None and technology.name in self.rio_inputs.dual_fuel_efficiency.index.get_level_values('supply_technology'):
                        technology.efficiency.raw_values = util.df_slice(self.rio_inputs.dual_fuel_efficiency,technology.name,'supply_technology')
            elif isinstance(node, SupplyNode):
                node.add_total_stock_measures(scenario)
            if cfg.rio_supply_run:
                for node  in self.nodes.values():
                    if hasattr(node,'technologies'):
                        for technology in node.technologies.values():
                            if hasattr(technology,'capacity_factor'):
                                technology.capacity_factor.set_rio_capacity_factor(self.rio_inputs)
                            if isinstance(node, StorageNode):
                                technology.duration.set_rio_duration(self.rio_inputs)

    def _calculate_initial_loop(self):
        """
        in the first year of the io loop, we have an initial loop step called 'initial'.
        this loop is necessary in order to calculate initial active coefficients. Because we haven't calculated
        throughput for all nodes, these coefficients are just proxies in this initial loop
        """
        loop, year = 'initial', min(self.years)
        self.calculate_demand(year, loop)
        self.pass_initial_demand_to_nodes(year)
        self.discover_thermal_nodes()
        self.calculate_stocks(year, loop)
        self.calculate_coefficients(year, loop)
        self.discover_thermal_nodes()
        self.update_io_df(year, loop)
        self.calculate_io(year, loop)

    def _recalculate_stocks_and_io(self, year, loop):
        """ Basic calculation control for the IO
        """
        self.calculate_coefficients(year, loop)
        # we have just solved the dispatch, so coefficients need to be updated before updating the io
        if loop == 3 and year in self.dispatch_years and not cfg.rio_supply_run:
            self.update_coefficients_from_dispatch(year)
        self.copy_io(year,loop)
        self.update_io_df(year,loop)
        self.calculate_io(year, loop)
        self.calculate_stocks(year, loop)

    def _recalculate_after_reconciliation(self, year, loop, update_demand=False):
        """ if reconciliation has occured, we have to recalculate coefficients and resolve the io
        """
        if self.reconciled is True:
            if update_demand:
                self.update_demand(year,loop)
            self._recalculate_stocks_and_io(year, loop)
            self.reconciled = False

    def copy_io(self,year,loop):
        if year != min(self.years) and loop ==1:
            for sector in self.demand_sectors:
                self.io_dict[year][sector] = copy.deepcopy(self.io_dict[year-1][sector])

    def set_dispatch_years(self):
        dispatch_year_step = cfg.getParamAsInt('dispatch_step')
        if dispatch_year_step == 0:
            self.dispatch_years = []
            self.dispatch_write_years = []
        else:
            dispatch_write_step = cfg.getParamAsInt('dispatch_write_step', section='output_detail')
            logging.info("Dispatch year step = {}".format(dispatch_year_step))
            self.dispatch_years = sorted([min(self.years)] + range(max(self.years), min(self.years), -dispatch_year_step))
            if dispatch_write_step == 0:
                self.dispatch_write_years = []
            else:
                self.dispatch_write_years = sorted([min(self.years)] + range(max(self.years), min(self.years), -dispatch_write_step))

    def restart_loop(self):
        self.calculate_loop(self.years,self.calculated_years)

    def calculate_loop(self, years, calculated_years):
        """Performs all IO loop calculations"""
        self.set_dispatch_years()
        first_year = min(self.years)
        self._calculate_initial_loop()
        self.calculated_years = calculated_years
        for year in [x for x in years if x not in self.calculated_years]:
            logging.info("Starting supply side calculations for {}".format(year))
            for loop in [1, 2, 3]:
                # starting loop
                if loop == 1:
                    logging.info("   loop {}: input-output calculation".format(loop))
                    if year is not first_year:
                        # initialize year is not necessary in the first year
                        self.initialize_year(year, loop)
                    self._recalculate_stocks_and_io(year, loop)
                    self.calculate_coefficients(year, loop)
                # reconciliation loop
                elif loop == 2:
                    logging.info("   loop {}: supply reconciliation".format(loop))
                    # sets a flag for whether any reconciliation occurs in the loop determined in the reconcile function
                    self.reconciled = False
                    # each time, if reconciliation has occured, we have to recalculate coefficients and resolve the io
                    self.reconcile_trades(year, loop)
                    self._recalculate_after_reconciliation(year, loop, update_demand=True)
                    if cfg.rio_supply_run:
                        for i in range(1):
                            self.reconcile_oversupply(year, loop)
                            self._recalculate_after_reconciliation(year, loop, update_demand=True)
                    if not cfg.rio_supply_run:
                        for i in range(2):
                            self.reconcile_oversupply(year, loop)
                            self._recalculate_after_reconciliation(year, loop, update_demand=True)
                        self.reconcile_constraints(year,loop)
                        self._recalculate_after_reconciliation(year, loop, update_demand=True)
                        self.reconcile_oversupply(year, loop)
                        self._recalculate_after_reconciliation(year, loop, update_demand=True)
                # dispatch loop
                elif loop == 3 and year in self.dispatch_years and not cfg.getParamAsBoolean('rio_db_run', section='rio') and not cfg.getParamAsBoolean('rio_supply_run', section='rio'):
                    logging.info("   loop {}: electricity dispatch".format(loop))
                    # loop - 1 is necessary so that it uses last year's throughput
                    self.calculate_embodied_costs(year, loop-1) # necessary here because of the dispatch
                    #necessary to calculate emissions to apply CO2 price in year 1 if applicable
                    self.calculate_embodied_emissions(year)
                    self.prepare_dispatch_inputs(year, loop)
                    self.solve_electricity_dispatch(year)
                    self._recalculate_stocks_and_io(year, loop)
                elif loop == 3 and year in self.dispatch_years  and cfg.getParamAsBoolean('rio_db_run', section='rio') and not cfg.getParamAsBoolean('rio_supply_run', section='rio'):
                    logging.info("   loop {}: prepping rio electricity dispatch database inputs".format(loop))
                    self.prepare_dispatch_inputs_RIO(year,loop)
                elif loop == 3 and year in self.dispatch_years and cfg.getParamAsBoolean('rio_supply_run', section='rio'):
                    logging.info("   loop {}: solving RIO limited dispatch".format(loop))
                    # loop - 1 is necessary so that it uses last year's throughput
                    self.calculate_embodied_costs(year, loop-1) # necessary here because of the dispatch
                    #necessary to calculate emissions to apply CO2 price in year 1 if applicable
                    self.calculate_embodied_emissions(year)
                    self.prepare_dispatch_inputs(year, loop)
                    self.solve_electricity_dispatch_rio(year)
                    self._recalculate_stocks_and_io(year, loop)
            self.calculate_embodied_costs(year, loop=3)
            self.calculate_embodied_emissions(year)
            self.calculate_annual_costs(year)
            self.calculated_years.append(year)

    def discover_bulk_name(self):
        for blend in self.blend_nodes:
            if self.thermal_dispatch_node_name in self.nodes[blend].nodes:
                self.bulk_electricity_node_name = blend
                    
    def discover_thermal_nodes(self):
        self.thermal_nodes = []
        for node in self.nodes.values():
            if node.name in self.nodes[self.thermal_dispatch_node_name].values.index.get_level_values('supply_node'):
                self.thermal_nodes.append(node.name)
                node.thermal_dispatch_node = True
            else:
                node.thermal_dispatch_node = False

    def calculate_supply_outputs(self):
        self.years_subset = cfg.combined_years_subset
        self.map_dict = dict(util.csv_read_table('SupplyNodes', ['final_energy_link', 'name']))
        if self.map_dict.has_key(None):
            del self.map_dict[None]
        logging.info("calculating supply-side outputs")
        self.aggregate_results()
        logging.info("calculating supply cost link")
        self.cost_demand_link = self.map_embodied_to_demand(self.cost_dict, self.embodied_cost_link_dict)
        logging.info("calculating supply emissions link")
        self.emissions_demand_link = self.map_embodied_to_demand(self.emissions_dict, self.embodied_emissions_link_dict)
        logging.info("calculating supply energy link")
        self.energy_demand_link = self.map_embodied_to_demand(self.inverse_dict['energy'], self.embodied_energy_link_dict)
#        self.remove_blend_and_import()
        logging.info("calculate exported costs")
        self.calculate_export_result('export_costs', self.cost_dict)
        logging.info("calculate exported emissions")
        self.calculate_export_result('export_emissions', self.emissions_dict)
        logging.info("calculate exported energy")
        self.calculate_export_result('export_energy', self.inverse_dict['energy'])
        logging.info("calculate emissions rates for demand side")
        self.calculate_demand_emissions_rates()

    def calculate_embodied_supply_outputs(self):
        supply_embodied_cost = self.convert_io_matrix_dict_to_df(self.cost_dict)
        supply_embodied_cost.columns = [cfg.getParam('currency_year') + " " + cfg.getParam('currency_name')]
        self.outputs.supply_embodied_cost = supply_embodied_cost
        supply_embodied_emissions = self.convert_io_matrix_dict_to_df(self.emissions_dict)
        supply_embodied_emissions.columns = [cfg.getParam('mass_unit')]
        self.outputs.supply_embodied_emissions = supply_embodied_emissions

    def calculate_annual_costs(self, year):
        for node in self.nodes.values():
            if hasattr(node,'calculate_annual_costs'):
                node.calculate_annual_costs(year)

    def concatenate_annual_costs(self):
        for node in self.nodes.values():
            if hasattr(node,'concatenate_annual_costs'):
                node.concatenate_annual_costs()

    def concatenate_levelized_costs(self):
        for node in self.nodes.values():
            if hasattr(node,'concatenate_levelized_costs'):
                node.concatenate_annual_costs()
    def calculate_capacity_utilization(self):
        for node in self.nodes.values():
            if hasattr(node,'calculate_capacity_utilization'):
                df = util.df_slice(self.io_supply_df,node.name,'supply_node')
                node.calculate_capacity_utilization(df,self.years)

    def remove_blend_and_import(self):
        keep_list = [node.name for node in self.nodes.values() if node.supply_type != 'Blend' and node.supply_type != 'Import']
        indexer = util.level_specific_indexer(self.energy_demand_link,'supply_node',[keep_list])
        self.energy_demand_link = self.energy_demand_link.loc[indexer,:]

    def calculate_demand_emissions_rates(self):
        map_dict = self.map_dict
        index = pd.MultiIndex.from_product([GeoMapper.supply_geographies, self.demand_sectors, map_dict.keys(),self.years, self.ghgs], names=[GeoMapper.supply_primary_geography, 'sector', 'final_energy','year','ghg'])
        self.demand_emissions_rates = util.empty_df(index, ['value'])

        for final_energy, node_name in map_dict.iteritems():
            node = self.nodes[node_name]
            for year in self.years:
                df = node.pass_through_df_dict[year].groupby(level='ghg').sum()
                df = df.stack(level=[GeoMapper.supply_primary_geography,'demand_sector']).to_frame()
                df = df.reorder_levels([GeoMapper.supply_primary_geography,'demand_sector','ghg'])
                df.sort(inplace=True)
                emissions_rate_indexer = util.level_specific_indexer(self.demand_emissions_rates, ['final_energy', 'year'], [final_energy, year])
                self.demand_emissions_rates.loc[emissions_rate_indexer,:] = df.values

        for final_energy, node_name in map_dict.iteritems():
            node = self.nodes[node_name]
            if hasattr(node,'emissions') and hasattr(node.emissions, 'values_physical'):
                if 'demand_sector' not in node.emissions.values_physical.index.names:
                    keys = self.demand_sectors
                    name = ['demand_sector']
                    df = pd.concat([node.emissions.values_physical]*len(keys), keys=keys, names=name)
                df = df.stack('year').to_frame()
                df = df.groupby(level=[GeoMapper.supply_primary_geography, 'demand_sector', 'year', 'ghg']).sum()
                df = df.reorder_levels([GeoMapper.supply_primary_geography, 'demand_sector', 'year', 'ghg'])
                idx = pd.IndexSlice
                df = df.loc[idx[:, :, self.years,:], :]
                emissions_rate_indexer = util.level_specific_indexer(self.demand_emissions_rates, ['final_energy'], [final_energy])
                self.demand_emissions_rates.loc[emissions_rate_indexer,:] += df.values

    def set_dispatchability(self):
        """Determines the dispatchability of electricity generation nodes and nodes that demand electricity
        Sets:
            electricity_gen_nodes = list of all supply nodes that inject electricity onto the grid
            electricity_load_nodes = dictionary of all supply nodes that demand electricity with keys of
        """
        self.electricity_gen_nodes = util.recursivedict()
        self.electricity_load_nodes = util.recursivedict()
        for zone in self.dispatch_zones:
            self.electricity_gen_nodes[zone]['flexible'] = list(set([x for x in self.injection_nodes[zone] if self.nodes[x].is_flexible == 1]))
            self.electricity_gen_nodes[zone]['non_flexible'] = list(set([x for x in self.injection_nodes[zone] if self.nodes[x].is_flexible != 1]))
        for zone in self.dispatch_zones:
            self.electricity_load_nodes[zone]['flexible'] = list(set([x for x in self.all_electricity_load_nodes[zone] if self.nodes[x].is_flexible == 1]))
            self.electricity_load_nodes[zone]['non_flexible'] = list(set([x for x in self.all_electricity_load_nodes[zone] if self.nodes[x].is_flexible != 1]))
        self.electricity_gen_nodes = util.freeze_recursivedict(self.electricity_gen_nodes)
        self.electricity_load_nodes = util.freeze_recursivedict(self.electricity_load_nodes)

    def set_flow_nodes(self,zone):
        flow_nodes = list(set([x for x in self.nodes[zone].active_coefficients_untraded.index.get_level_values('supply_node')  if self.nodes[x].supply_type in ['Delivery','Blend'] and x not in self.dispatch_zones]))
        self.solve_flow_nodes(flow_nodes,zone)

    def solve_flow_nodes(self,flow_nodes, zone):
        for flow_node in flow_nodes:
            self.electricity_nodes[zone].append(flow_node)
            flow_nodes = list(set([x for x in util.df_slice(self.nodes[flow_node].active_coefficients_untraded,'not consumed','efficiency_type').index.get_level_values('supply_node') if self.nodes[x].supply_type in ['Delivery','Blend'] and x not in self.dispatch_zones and 'supply_node' in self.nodes[flow_node].active_coefficients_untraded.index.names]))
            if len(flow_nodes):
                self.solve_flow_nodes(flow_nodes,zone)

    def set_electricity_gen_nodes(self, dispatch_zone, node):
        """Determines all nodes that inject electricity onto the grid in a recursive loop
        args:
            dispatch_zone: key for dictionary to indicate whether the generation is at the transmission or distribution level
            node: checks for injection of electricity into this node from conversion nodes
        sets:
            self.injection_nodes = dictionary with dispatch_zone as key and a list of injection nodes as the value
            self.electricity_nodes = dictionary with dispatch_zone as key and a list of all nodes that transfer electricity (i.e. blend nodes, etc.)
        """
        for zone in self.dispatch_zones:
            self.electricity_nodes[zone].append(zone)
            self.set_flow_nodes(zone)
            for flow_node in self.electricity_nodes[zone]:
                injection_nodes = list(set([x for x in self.nodes[flow_node].active_coefficients_untraded.index.get_level_values('supply_node')  if self.nodes[x].supply_type in ['Conversion']]))
                for injection_node in injection_nodes:
                    self.injection_nodes[zone].append(injection_node)
            self.injection_nodes[zone] = list(set(self.injection_nodes[zone]))
            self.electricity_nodes[zone] = list(set(self.electricity_nodes[zone]))

    def set_electricity_load_nodes(self):
        """Determines all nodes that demand electricity from the grid
        args:
        sets:
            all_electricity_load_nodes = dictionary with dispatch_zone as key and a list of all nodes that demand electricity from that zone
        """
        self.all_electricity_load_nodes = defaultdict(list)
        for zone in self.dispatch_zones:
            for node_name in self.electricity_nodes[zone]:
                for load_node in self.nodes.values():
                    if hasattr(load_node,'active_coefficients_untraded')  and load_node.active_coefficients_untraded  is not None:
                        if node_name in load_node.active_coefficients_untraded.index.get_level_values('supply_node') and load_node not in self.electricity_nodes[zone] and load_node.supply_type != 'Storage':
                            if load_node.name not in util.flatten_list(self.electricity_nodes.values()):
                                self.all_electricity_load_nodes[zone].append(load_node.name)

    def append_heuristic_load_and_gen_to_dispatch_outputs(self, df, load_or_gen):
        if 'bulk' in util.elements_in_index_level(df,'dispatch_feeder'):
            bulk_df = util.df_slice(df, 'bulk','dispatch_feeder')
            if load_or_gen=='load':
                bulk_df = DfOper.mult([bulk_df, self.transmission_losses])
            bulk_df = self.outputs.clean_df(bulk_df)
            bulk_df.columns = [cfg.calculation_energy_unit.upper()]
            util.replace_index_name(bulk_df, 'DISPATCH_OUTPUT', 'SUPPLY_NODE')
            self.bulk_dispatch = pd.concat([self.bulk_dispatch, bulk_df.reorder_levels(self.bulk_dispatch.index.names)])
        if len([x for x in util.elements_in_index_level(df,'dispatch_feeder') if x in self.dispatch_feeders]):
            distribution_df = util.df_slice(df, [x for x in  util.elements_in_index_level(df,'dispatch_feeder') if x in self.dispatch_feeders], self.dispatch_feeders)
            distribution_df = self.outputs.clean_df(distribution_df)
            distribution_df.columns = [cfg.calculation_energy_unit.upper()]
            distribution_df = DfOper.mult([distribution_df, self.distribution_losses, self.transmission_losses])
            util.replace_index_name(distribution_df, 'DISPATCH_OUTPUT', 'SUPPLY_NODE')
            distribution_df = util.remove_df_levels(distribution_df, 'DISPATCH_FEEDER')
            self.bulk_dispatch = pd.concat([self.bulk_dispatch, distribution_df.reorder_levels(self.bulk_dispatch.index.names)])

    def set_long_duration_opt(self, year):
        # MOVE
        """sets input parameters for dispatched nodes (ex. conventional hydro)"""
        def split_and_apply(array, dispatch_periods, fun):
            energy_by_block = np.array_split(array, np.where(np.diff(dispatch_periods)!=0)[0]+1)
            return [fun(block) for block in energy_by_block]
        self.dispatch.ld_technologies = []
        for node_name in [x for x in self.dispatch.long_duration_dispatch_order if x in self.nodes.keys()]:
            node = self.nodes[node_name]
            full_energy_shape, p_min_shape, p_max_shape = node.aggregate_flexible_electricity_shapes(year, util.remove_df_levels(util.df_slice(self.dispatch_feeder_allocation,year,'year'),year))
            if node_name in self.flexible_gen.keys():
                lookup = self.flexible_gen
                load_or_gen = 'gen'
            elif node_name in self.flexible_load.keys():
                lookup = self.flexible_load
                load_or_gen = 'load'
            else:
                continue
            for geography in lookup[node_name].keys():
                for zone in lookup[node_name][geography].keys():
                    for feeder in lookup[node_name][geography][zone].keys():
                        capacity = util.remove_df_levels(lookup[node_name][geography][zone][feeder]['capacity'], 'resource_bin')
                        if capacity.sum().sum() == 0:
                            continue
                        annual_energy = lookup[node_name][geography][zone][feeder]['energy'].values.sum()
                        opt_periods = self.dispatch.period_repeated
                        dispatch_window = self.dispatch.node_config_dict[node_name].dispatch_window
                        dispatch_periods = getattr(Shapes.get_active_dates_index(), dispatch_window)
                        if load_or_gen=='load':
                            annual_energy = copy.deepcopy(annual_energy) *-1
                        if p_min_shape is None:
                            p_min = np.repeat(0.0,len(dispatch_periods))
                            p_max = np.repeat(capacity.sum().values[0],len(dispatch_periods))
                            hourly_p_min = np.repeat(0.0,len(self.dispatch.hours))
                            opt_p_min = np.repeat(0.0,len(opt_periods))
                            opt_p_max = np.repeat(capacity.sum().values[0],len(opt_periods))
                            hourly_p_max = np.repeat(capacity.sum().values[0],len(self.dispatch.hours))
                        else:
                            hourly_p_min = util.remove_df_levels(util.DfOper.mult([capacity, p_min_shape]), GeoMapper.supply_primary_geography).values
                            p_min = np.array(split_and_apply(hourly_p_min, dispatch_periods, np.mean))
                            opt_p_min = np.array(split_and_apply(hourly_p_min, opt_periods, np.mean))
                            hourly_p_max = util.remove_df_levels(util.DfOper.mult([capacity, p_max_shape]),GeoMapper.supply_primary_geography).values
                            p_max = np.array(split_and_apply(hourly_p_max, dispatch_periods, np.mean))
                            opt_p_max = np.array(split_and_apply(hourly_p_max, opt_periods, np.mean))
                        tech_name = str(tuple([geography,node_name, feeder]))
                        self.dispatch.ld_technologies.append(tech_name)
                            #reversed sign for load so that pmin always represents greatest load or smallest generation
                        if zone == self.transmission_node_name:
                            if load_or_gen=='load':
                                p_min *= self.transmission_losses.loc[geography,:].values[0]
                                p_max *= self.transmission_losses.loc[geography,:].values[0]
                                opt_p_min *= self.transmission_losses.loc[geography,:].values[0]
                                opt_p_max *= self.transmission_losses.loc[geography,:].values[0]
                                hourly_p_min *=self.transmission_losses.loc[geography,:].values[0]
                                hourly_p_max *= self.transmission_losses.loc[geography,:].values[0]
                                annual_energy*=self.transmission_losses.loc[geography,:].values[0]
                        else:
                                p_min *= self.transmission_losses.loc[geography,:].values[0] * util.df_slice(self.distribution_losses, [geography,feeder],[GeoMapper.dispatch_geography, 'dispatch_feeder']).values[0][0]
                                p_max *= self.transmission_losses.loc[geography,:].values[0] * util.df_slice(self.distribution_losses, [geography,feeder],[GeoMapper.dispatch_geography, 'dispatch_feeder']).values[0][0]
                                opt_p_min *= self.transmission_losses.loc[geography,:].values[0] * util.df_slice(self.distribution_losses, [geography,feeder],[GeoMapper.dispatch_geography, 'dispatch_feeder']).values[0][0]
                                opt_p_max *= self.transmission_losses.loc[geography,:].values[0] * util.df_slice(self.distribution_losses, [geography,feeder],[GeoMapper.dispatch_geography, 'dispatch_feeder']).values[0][0]
                                hourly_p_min *=self.transmission_losses.loc[geography,:].values[0] * util.df_slice(self.distribution_losses, [geography,feeder],[GeoMapper.dispatch_geography, 'dispatch_feeder']).values[0][0]
                                hourly_p_max *= self.transmission_losses.loc[geography,:].values[0] * util.df_slice(self.distribution_losses, [geography,feeder],[GeoMapper.dispatch_geography, 'dispatch_feeder']).values[0][0]
                                annual_energy *= self.transmission_losses.loc[geography,:].values[0] * util.df_slice(self.distribution_losses, [geography,feeder],[GeoMapper.dispatch_geography, 'dispatch_feeder']).values[0][0]
                        if load_or_gen == 'gen':
                            max_capacity = opt_p_max
                            min_capacity = opt_p_min
                            max_hourly_capacity = hourly_p_max
                            min_hourly_capacity = hourly_p_min
                        else:
                            max_capacity = -opt_p_min
                            min_capacity = -opt_p_max
                            max_hourly_capacity = -hourly_p_min
                            min_hourly_capacity = -hourly_p_max
                        self.dispatch.annual_ld_energy[tech_name] = annual_energy
                        self.dispatch.ld_geography[tech_name] = geography
                        self.dispatch.ld_capacity.update(dict([((tech_name, h), value) for h, value in enumerate(max_hourly_capacity)]))
                        self.dispatch.ld_min_capacity.update(dict([((tech_name, h), value) for h, value in enumerate(min_hourly_capacity)]))
                        for period in self.dispatch.periods:
                            self.dispatch.capacity[period][tech_name] = max_capacity[period]
                            self.dispatch.min_capacity[period][tech_name] = min_capacity[period]
                            self.dispatch.geography[period][tech_name] = geography
                            self.dispatch.feeder[period][tech_name] = feeder



    def solve_heuristic_load_and_gen(self, year):
        # MOVE
        """solves dispatch shapes for heuristically dispatched nodes (ex. conventional hydro)"""
        def split_and_apply(array, dispatch_periods, fun):
            energy_by_block = np.array_split(array, np.where(np.diff(dispatch_periods)!=0)[0]+1)
            return [fun(block) for block in energy_by_block]
        self.dispatched_bulk_load = copy.deepcopy(self.bulk_gen)*0
        self.dispatched_bulk_gen = copy.deepcopy(self.bulk_gen)*0
        self.dispatched_dist_load = copy.deepcopy(self.bulk_gen)*0
        self.dispatched_dist_gen = copy.deepcopy(self.bulk_gen)*0
        for node_name in [x for x in self.dispatch.heuristic_dispatch_order if x in self.nodes.keys()]:
            node = self.nodes[node_name]
            full_energy_shape, p_min_shape, p_max_shape = node.aggregate_flexible_electricity_shapes(year, util.remove_df_levels(util.df_slice(self.dispatch_feeder_allocation,year,'year'),year))
            if node_name in self.flexible_gen.keys():
                lookup = self.flexible_gen
                load_or_gen = 'gen'
            elif node_name in self.flexible_load.keys():
                lookup = self.flexible_load
                load_or_gen = 'load'
            else:
                continue
            logging.info("      solving dispatch for %s" %node.name)
            geography_list = []
            for geography in lookup[node_name].keys():
                for zone in lookup[node_name][geography].keys():
                    feeder_list = []
                    for feeder in lookup[node_name][geography][zone].keys():
                        capacity = lookup[node_name][geography][zone][feeder]['capacity']
                        energy = lookup[node_name][geography][zone][feeder]['energy']
                        dispatch_window = self.dispatch.node_config_dict[node_name].dispatch_window
                        dispatch_periods = getattr(Shapes.get_active_dates_index(), dispatch_window)
                        num_years = len(dispatch_periods)/8766.
                        if load_or_gen=='load':
                            energy = copy.deepcopy(energy) *-1
                        if full_energy_shape is not None and 'dispatch_feeder' in full_energy_shape.index.names:
                            energy_shape = util.df_slice(full_energy_shape, feeder, 'dispatch_feeder')
                        else:
                            energy_shape = full_energy_shape
                        if energy_shape is None:
                            energy_budgets = util.remove_df_levels(energy,[GeoMapper.supply_primary_geography,'resource_bin']).values * np.diff([0]+list(np.where(np.diff(dispatch_periods)!=0)[0]+1)+[len(dispatch_periods)-1])/8766.*num_years
                            energy_budgets = energy_budgets[0]
                        else:
                            hourly_energy = util.remove_df_levels(util.DfOper.mult([energy,energy_shape]), GeoMapper.supply_primary_geography).values
                            energy_budgets = split_and_apply(hourly_energy, dispatch_periods, sum)
                        if p_min_shape is None:
                            p_min = 0.0
                            p_max = capacity.sum().values[0]
                        else:
                            hourly_p_min = util.remove_df_levels(util.DfOper.mult([capacity,p_min_shape]),GeoMapper.supply_primary_geography).values
                            p_min = split_and_apply(hourly_p_min, dispatch_periods, np.mean)
                            hourly_p_max = util.remove_df_levels(util.DfOper.mult([capacity,p_max_shape]),GeoMapper.supply_primary_geography).values
                            p_max = split_and_apply(hourly_p_max, dispatch_periods, np.mean)
                        if zone == self.transmission_node_name:
                            net_indexer = util.level_specific_indexer(self.bulk_net_load,[GeoMapper.dispatch_geography], [geography])
                            if load_or_gen=='load':
                                self.energy_budgets = energy_budgets
                                self.p_min = p_min
                                self.p_max = p_max
                                dispatch = np.transpose([dispatch_budget.dispatch_to_energy_budget(self.bulk_net_load.loc[net_indexer,:].values.flatten(),energy_budgets, dispatch_periods, p_min, p_max)])
                                self.dispatch_result = dispatch
                                indexer = util.level_specific_indexer(self.bulk_load,[GeoMapper.dispatch_geography], [geography])
                                self.bulk_load.loc[indexer,:] += dispatch
                                indexer = util.level_specific_indexer(self.bulk_load,GeoMapper.dispatch_geography, geography)
                                self.dispatched_bulk_load.loc[indexer,:] += dispatch
                            else:
                                indexer = util.level_specific_indexer(self.bulk_gen,GeoMapper.dispatch_geography, geography)
                                dispatch = np.transpose([dispatch_budget.dispatch_to_energy_budget(self.bulk_net_load.loc[net_indexer,:].values.flatten(),np.array(energy_budgets).flatten(), dispatch_periods, p_min, p_max)])
                                self.bulk_gen.loc[indexer,:] += dispatch
                                self.dispatched_bulk_gen.loc[indexer,:] += dispatch
                        else:
                            if load_or_gen=='load':
                                indexer = util.level_specific_indexer(self.dist_load,[GeoMapper.dispatch_geography,'dispatch_feeder'], [geography,feeder])
                                dispatch =  np.transpose([dispatch_budget.dispatch_to_energy_budget(self.dist_net_load_no_feeders.loc[net_indexer,:].values.flatten(),energy_budgets, dispatch_periods, p_min, p_max)])
                                for timeshift_type in list(set(self.distribution_load.index.get_level_values('timeshift_type'))):
                                    indexer = util.level_specific_indexer(self.distribution_load,[GeoMapper.dispatch_geography,'timeshift_type'], [geography,timeshift_type])
                                    self.distribution_load.loc[indexer,:] += dispatch
                                indexer = util.level_specific_indexer(self.distribution_load,GeoMapper.dispatch_geography, geography)
                                self.dispatched_dist_load.loc[indexer,:] += dispatch

                            else:
                                indexer = util.level_specific_indexer(self.dist_gen,[GeoMapper.dispatch_geography,'dispatch_feeder'], [geography,feeder])
                                dispatch =  np.transpose([dispatch_budget.dispatch_to_energy_budget(self.dist_net_load_no_feeders.loc[net_indexer,:].values.flatten(),energy_budgets, dispatch_periods, p_min, p_max)])
                                self.distribution_gen.loc[indexer,:] += dispatch
                                self.dispatched_dist_gen.loc[indexer,:] += dispatch
                        index = pd.MultiIndex.from_product([Shapes.get_active_dates_index(),[feeder]],names=['weather_datetime','dispatch_feeder'])
                        dispatch=pd.DataFrame(dispatch,index=index,columns=['value'])
                        if load_or_gen=='gen':
                            dispatch *=-1
                        feeder_list.append(dispatch)
                    geography_list.append(pd.concat(feeder_list))
            self.update_net_load_signal()
            df = pd.concat(geography_list, keys=lookup[node_name].keys(), names=[GeoMapper.dispatch_geography])
            df = pd.concat([df], keys=[node_name], names=['supply_node'])
            df = pd.concat([df], keys=[year], names=['year'])
            if year in self.dispatch_write_years:
                self.append_heuristic_load_and_gen_to_dispatch_outputs(df, load_or_gen)

    def prepare_optimization_inputs(self,year):
        # MOVE
        logging.info("      preparing optimization inputs")
        self.dispatch.set_timeperiods()
        self.dispatch.set_losses(self.transmission_losses,self.distribution_losses)
        self.set_net_load_thresholds(year)
        #freeze the bulk net load as opt bulk net load just in case we want to rerun a year. If we don't do this, bulk_net_load would be updated with optimization results
        self.dispatch.set_opt_loads(self.distribution_load,self.distribution_flex_load,self.distribution_gen,self.bulk_load,self.bulk_gen,self.dispatched_bulk_load, self.bulk_net_load, self.active_thermal_dispatch_df)
        # self.dispatch.set_opt_loads(self.distribution_load,self.distribution_flex_load,self.distribution_gen,self.bulk_load,self.bulk_gen,self.dispatched_bulk_load, self.bulk_net_load, self.active_thermal_dispatch_df)
        flex_pmin, flex_pmax = self.demand_object.aggregate_flexible_load_pmin_pmax(year)
        self.dispatch.set_max_min_flex_loads(flex_pmin, flex_pmax)
        self.dispatch.set_technologies(self.storage_capacity_dict, self.storage_efficiency_dict, self.active_thermal_dispatch_df)
        self.set_long_duration_opt(year)

    # Ryan
    def set_grid_capacity_factors(self, year):
        max_year = max(self.years)
        distribution_grid_node = self.nodes[self.distribution_grid_node_name]
        dist_cap_factor = util.DfOper.divi([self.dist_only_net_load.groupby(level=[GeoMapper.dispatch_geography,'dispatch_feeder']).mean(),self.dist_only_net_load.groupby(level=[GeoMapper.dispatch_geography,'dispatch_feeder']).max()])
        geography_map_key = distribution_grid_node.geography_map_key if hasattr(distribution_grid_node, 'geography_map_key') and distribution_grid_node.geography_map_key is not None else GeoMapper.default_geography_map_key
        if GeoMapper.dispatch_geography != GeoMapper.supply_primary_geography:
            map_df = GeoMapper.get_instance().map_df(GeoMapper.dispatch_geography,GeoMapper.supply_primary_geography, normalize_as='intensity', map_key=geography_map_key, eliminate_zeros=False)
            dist_cap_factor = util.remove_df_levels(util.DfOper.mult([dist_cap_factor,map_df]),GeoMapper.dispatch_geography)
        dist_cap_factor = util.remove_df_levels(util.DfOper.mult([dist_cap_factor, util.df_slice(self.dispatch_feeder_allocation, year, 'year')]),'dispatch_feeder')
        dist_cap_factor = dist_cap_factor.reorder_levels([GeoMapper.supply_primary_geography,'demand_sector']).sort_index()
        distribution_grid_node.capacity_factor.values.loc[:,year] = dist_cap_factor.values
        for i in range(0,cfg.getParamAsInt('dispatch_step')+1):
            distribution_grid_node.capacity_factor.values.loc[:,min(year+i,max_year)] = dist_cap_factor.values
        if hasattr(distribution_grid_node, 'stock'):
                distribution_grid_node.update_stock(year,3)
        #hardcoded 50% assumption of colocated energy for dispatched flexible gen. I.e. wind and solar. Means that transmission capacity isn't needed to support energy demands.
        #TODO change to config parameter
        if hasattr(self, 'dispatched_bulk_load'):
            bulk_flow = util.DfOper.subt([util.DfOper.add([self.bulk_load,util.remove_df_levels(self.dist_only_net_load,'dispatch_feeder')]),self.dispatched_bulk_load * .5])
        else:
            bulk_flow = util.DfOper.add([self.bulk_load, util.remove_df_levels(self.dist_only_net_load, 'dispatch_feeder')])
        all_bulk_flow =  util.DfOper.add([self.bulk_load, util.remove_df_levels(self.dist_only_net_load, 'dispatch_feeder')])
        bulk_cap_factor = util.DfOper.divi([all_bulk_flow.groupby(level=GeoMapper.dispatch_geography).mean(),bulk_flow.groupby(level=GeoMapper.dispatch_geography).max()])
        transmission_grid_node = self.nodes[self.transmission_node_name]
        geography_map_key = transmission_grid_node.geography_map_key if hasattr(transmission_grid_node, 'geography_map_key') and transmission_grid_node.geography_map_key is not None else GeoMapper.default_geography_map_key
        if GeoMapper.dispatch_geography != GeoMapper.supply_primary_geography:
            map_df = GeoMapper.get_instance().map_df(GeoMapper.dispatch_geography,GeoMapper.supply_primary_geography, normalize_as='intensity', map_key=geography_map_key, eliminate_zeros=False)
            bulk_cap_factor = util.remove_df_levels(util.DfOper.mult([bulk_cap_factor,map_df]),GeoMapper.dispatch_geography)
        transmission_grid_node.capacity_factor.values.loc[:,year] = bulk_cap_factor.values
        for i in range(0,cfg.getParamAsInt('dispatch_step')+1):
            transmission_grid_node.capacity_factor.values.loc[:,min(year+i,max_year)] = bulk_cap_factor.values
        if hasattr(transmission_grid_node, 'stock'):
            transmission_grid_node.update_stock(year,3)

    def _get_ld_results_from_dispatch(self):
        if not len(self.dispatch.ld_technologies):
            return None, None, None
        #load and gen are the same in the ld_df, just with different signs. We want to separate and use absolute values (i.e. *- when it is load)
        ld_load = util.remove_df_levels(-self.dispatch.ld_df[self.dispatch.ld_df.values<0],'supply_node')
        ld_gen = util.remove_df_levels(self.dispatch.ld_df[self.dispatch.ld_df.values>0], 'supply_node')
        dist_ld_load = util.df_slice(ld_load, self.dispatch_feeders, 'dispatch_feeder')
        if not len(dist_ld_load):
            dist_ld_load = None
        if not len(ld_load):
            ld_load = None
        if not len(ld_gen):
            ld_gen = None
        return ld_load, ld_gen, dist_ld_load

    def solve_storage_and_flex_load_optimization(self,year):
        # MOVE
        """prepares, solves, and updates the net load with results from the storage and flexible load optimization"""
        self.dispatch.set_year(year)
        self.prepare_optimization_inputs(year)
        logging.info("      solving dispatch for storage and dispatchable load")
        self.dispatch.solve_optimization()

        ld_load, ld_gen, dist_ld_load = self._get_ld_results_from_dispatch()

        dist_storage_charge, dist_storage_discharge = None, None
        storage_charge = self.dispatch.storage_df.xs('charge', level='charge_discharge')
        storage_discharge = self.dispatch.storage_df.xs('discharge', level='charge_discharge')
        if len(set(storage_charge.index.get_level_values('dispatch_feeder')))>1:
            dist_storage_charge = util.df_slice(storage_charge, self.dispatch_feeders, 'dispatch_feeder')
            dist_storage_discharge = util.df_slice(storage_discharge, self.dispatch_feeders, 'dispatch_feeder')

        dist_flex_load = util.df_slice(self.dispatch.flex_load_df, self.dispatch_feeders, 'dispatch_feeder')
        self.distribution_load = util.DfOper.add((self.distribution_load, dist_storage_charge, dist_flex_load, dist_ld_load))
        self.distribution_gen = util.DfOper.add((self.distribution_gen, dist_storage_discharge,util.df_slice(ld_gen, self.dispatch_feeders, 'dispatch_feeder',return_none=True) ))

        imports = None
        exports = None
        if self.dispatch.transmission_flow_df is not None:
            try:
                flow_with_losses = util.DfOper.divi((self.dispatch.transmission_flow_df, 1 - self.dispatch.transmission.losses.get_values(year)))
            except:
                pdb.set_trace()
            imports = self.dispatch.transmission_flow_df.groupby(level=['gau_to', 'weather_datetime']).sum()
            exports = flow_with_losses.groupby(level=['gau_from', 'weather_datetime']).sum()
            imports.index.names = [GeoMapper.dispatch_geography, 'weather_datetime']
            exports.index.names = [GeoMapper.dispatch_geography, 'weather_datetime']
        try:
            if ld_load is not None:
                new_ld_load = util.DfOper.divi([util.df_slice(ld_load, 'bulk', 'dispatch_feeder',return_none=True),self.transmission_losses])
            else:
                new_ld_load = None
            self.bulk_load = util.DfOper.add((self.bulk_load, storage_charge.xs('bulk', level='dispatch_feeder'), new_ld_load,util.DfOper.divi([exports,self.transmission_losses])))
        except:
            pdb.set_trace()
        self.bulk_gen = util.DfOper.add((self.bulk_gen, storage_discharge.xs('bulk', level='dispatch_feeder'), util.df_slice(ld_gen, 'bulk', 'dispatch_feeder',return_none=True),imports))
        self.opt_bulk_net_load = copy.deepcopy(self.bulk_net_load)
        self.update_net_load_signal()
        self.produce_distributed_storage_outputs(year)
        self.produce_bulk_storage_outputs(year)
        self.produce_flex_load_outputs(year)
        self.produce_ld_outputs(year)
        self.produce_transmission_outputs(year)

    def produce_transmission_outputs(self, year):
        # MOVE
        if year in self.dispatch_write_years and self.dispatch.transmission_flow_df is not None:
            df_index_reset = self.dispatch.transmission_flow_df.reset_index()
            # df_index_reset['gau_from'] = map(cfg.outputs_id_map[GeoMapper.dispatch_geography].get, df_index_reset['gau_from'].values)
            # df_index_reset['gau_to'] = map(cfg.outputs_id_map[GeoMapper.dispatch_geography].get, df_index_reset['gau_to'].values)

            df_index_reset_with_losses = DfOper.divi((self.dispatch.transmission_flow_df, 1 - self.dispatch.transmission.losses.get_values(year))).reset_index()
            # df_index_reset_with_losses['gau_from'] = map(cfg.outputs_id_map[GeoMapper.dispatch_geography].get, df_index_reset_with_losses['gau_from'].values)
            # df_index_reset_with_losses['gau_to'] = map(cfg.outputs_id_map[GeoMapper.dispatch_geography].get, df_index_reset_with_losses['gau_to'].values)

            imports = df_index_reset.rename(columns={'gau_to':GeoMapper.dispatch_geography})
            exports = df_index_reset_with_losses.rename(columns={'gau_from':GeoMapper.dispatch_geography})
            exports['gau_to'] = 'TRANSMISSION EXPORT TO ' + exports['gau_to']
            imports['gau_from'] = 'TRANSMISSION IMPORT FROM ' + imports['gau_from']
            imports = imports.rename(columns={'gau_from':'DISPATCH_OUTPUT'})
            exports = exports.rename(columns={'gau_to':'DISPATCH_OUTPUT'})
            imports = imports.set_index([GeoMapper.dispatch_geography, 'DISPATCH_OUTPUT', 'weather_datetime'])
            exports = exports.set_index([GeoMapper.dispatch_geography, 'DISPATCH_OUTPUT', 'weather_datetime'])
            # drop any lines that don't have flows this is done to reduce the size of outputs
            imports = imports.groupby(level=[GeoMapper.dispatch_geography, 'DISPATCH_OUTPUT']).filter(lambda x: x.sum() > 0)
            exports = exports.groupby(level=[GeoMapper.dispatch_geography, 'DISPATCH_OUTPUT']).filter(lambda x: x.sum() > 0)
            transmission_output = pd.concat((-imports, exports))
            transmission_output = util.add_and_set_index(transmission_output, 'year', year)
            transmission_output.columns = [cfg.calculation_energy_unit.upper()]
            transmission_output = self.outputs.clean_df(transmission_output)
            self.bulk_dispatch = pd.concat([self.bulk_dispatch, transmission_output.reorder_levels(self.bulk_dispatch.index.names)])

    def produce_distributed_storage_outputs(self, year):
        # MOVE
        if year in self.dispatch_write_years and len(set(self.dispatch.storage_df.index.get_level_values('dispatch_feeder')))>1 :
            dist_storage_df = util.df_slice(self.dispatch.storage_df, self.dispatch_feeders, 'dispatch_feeder')
            distribution_df = util.remove_df_levels(util.DfOper.mult([dist_storage_df, self.distribution_losses,self.transmission_losses]), 'dispatch_feeder')
            distribution_df.columns = [cfg.calculation_energy_unit.upper()]
            charge_df = util.df_slice(distribution_df,'charge','charge_discharge')
            charge_df = self.outputs.clean_df(charge_df)
            charge_df = pd.concat([charge_df],keys=['DISTRIBUTED STORAGE CHARGE'],names=['DISPATCH_OUTPUT'])
            self.bulk_dispatch = pd.concat([self.bulk_dispatch, charge_df.reorder_levels(self.bulk_dispatch.index.names)])
            # self.bulk_dispatch = util.DfOper.add([self.bulk_dispatch, charge_df])
            discharge_df = util.df_slice(distribution_df,'discharge','charge_discharge')*-1
            discharge_df = self.outputs.clean_df(discharge_df)
            discharge_df = pd.concat([discharge_df],keys=['DISTRIBUTED STORAGE DISCHARGE'],names=['DISPATCH_OUTPUT'])
            self.bulk_dispatch = pd.concat([self.bulk_dispatch, discharge_df.reorder_levels(self.bulk_dispatch.index.names)])
            # self.bulk_dispatch = util.DfOper.add([self.bulk_dispatch, discharge_df])

    def produce_ld_outputs(self,year):
        # MOVE
        if year in self.dispatch_write_years and self.dispatch.ld_df is not None:
            #produce distributed long duration outputs
            #- changes the sign coming out of the dispatch, with is the reverse of what we want for outputs
            ld_df = -util.df_slice(self.dispatch.ld_df, self.dispatch_feeders, 'dispatch_feeder')
            if len(ld_df):
                ld_df = util.add_and_set_index(ld_df, 'year', year)
                ld_df.columns = [cfg.calculation_energy_unit.upper()]
                ld_df= self.outputs.clean_df(ld_df)
                ld_df.reset_index(['SUPPLY_NODE','DISPATCH_FEEDER'],inplace=True)
                ld_df['DISPATCH_OUTPUT'] = ld_df['DISPATCH_FEEDER'] + " " + ld_df['SUPPLY_NODE']
                ld_df.set_index('DISPATCH_OUTPUT',inplace=True, append=True)
                #remove the columns we used to set the dispatch output name
                ld_df = ld_df.iloc[:,0].to_frame()
                self.bulk_dispatch = pd.concat([self.bulk_dispatch, ld_df.reorder_levels(self.bulk_dispatch.index.names)])
            #- changes the sign coming out of the dispatch, with is the reverse of what we want for outputs
            #produce bulk long duration outputs
            ld_df = -util.df_slice(self.dispatch.ld_df, 'bulk', 'dispatch_feeder')
            if len(ld_df):
                ld_df = util.add_and_set_index(ld_df, 'year', year)
                ld_df.columns = [cfg.calculation_energy_unit.upper()]
                ld_df= self.outputs.clean_df(ld_df)
                util.replace_index_name(ld_df,'DISPATCH_OUTPUT', 'SUPPLY_NODE')
                self.bulk_dispatch = pd.concat([self.bulk_dispatch, ld_df.reorder_levels(self.bulk_dispatch.index.names)])

    def produce_bulk_storage_outputs(self, year):
        # MOVE
        if year in self.dispatch_write_years:
            bulk_df = self.dispatch.storage_df.xs('bulk', level='dispatch_feeder')
            bulk_df = util.add_and_set_index(bulk_df, 'year', year)
            bulk_df.columns = [cfg.calculation_energy_unit.upper()]
            charge_df = util.DfOper.mult([util.df_slice(bulk_df,'charge','charge_discharge'),self.transmission_losses])
            charge_df = self.outputs.clean_df(charge_df)
            charge_df = pd.concat([charge_df],keys=['BULK STORAGE CHARGE'],names=['DISPATCH_OUTPUT'])
            self.bulk_dispatch = pd.concat([self.bulk_dispatch, charge_df.reorder_levels(self.bulk_dispatch.index.names)])
            # self.bulk_dispatch = util.DfOper.add([self.bulk_dispatch, charge_df])
            discharge_df = util.df_slice(bulk_df,'discharge','charge_discharge')*-1
            discharge_df = self.outputs.clean_df(discharge_df)
            discharge_df = pd.concat([discharge_df], keys=['BULK STORAGE DISCHARGE'], names=['DISPATCH_OUTPUT'])
            self.bulk_dispatch = pd.concat([self.bulk_dispatch, discharge_df.reorder_levels(self.bulk_dispatch.index.names)])
            # self.bulk_dispatch = util.DfOper.add([self.bulk_dispatch, discharge_df])

    def produce_flex_load_outputs(self, year):
        # MOVE
        if year in self.dispatch_write_years:
            flex_load_df = util.df_slice(self.dispatch.flex_load_df, self.dispatch_feeders, 'dispatch_feeder')
            flex_load_df.columns = [cfg.calculation_energy_unit.upper()]
            flex_load_df = DfOper.mult([flex_load_df, self.distribution_losses, self.transmission_losses])
            flex_load_df= self.outputs.clean_df(flex_load_df)
            label_replace_dict = dict(zip(util.elements_in_index_level(flex_load_df,'DISPATCH_FEEDER'),[x+' FLEXIBLE LOAD' for x in util.elements_in_index_level(flex_load_df,'DISPATCH_FEEDER')]))
            util.replace_index_label(flex_load_df,label_replace_dict,'DISPATCH_FEEDER')
            util.replace_index_name(flex_load_df,'DISPATCH_OUTPUT','DISPATCH_FEEDER')
            self.bulk_dispatch = pd.concat([self.bulk_dispatch, flex_load_df.reorder_levels(self.bulk_dispatch.index.names)])
            # self.bulk_dispatch = util.DfOper.add([self.bulk_dispatch, flex_load_df])

    def set_distribution_losses(self,year):
        distribution_grid_node =self.nodes[self.distribution_grid_node_name]
        coefficients = distribution_grid_node.active_coefficients_total.sum().to_frame()
        indexer = util.level_specific_indexer(self.dispatch_feeder_allocation, 'year', year)
        a = util.DfOper.mult([coefficients, self.dispatch_feeder_allocation.loc[indexer,:], distribution_grid_node.active_supply])
        b = util.DfOper.mult([self.dispatch_feeder_allocation.loc[indexer,:], distribution_grid_node.active_supply])
        self.distribution_losses = util.DfOper.divi([util.remove_df_levels(a,'demand_sector'),util.remove_df_levels(b,'demand_sector')]).fillna(1)
        geography_map_key = distribution_grid_node.geography_map_key if hasattr(distribution_grid_node, 'geography_map_key') and distribution_grid_node.geography_map_key is not None else GeoMapper.default_geography_map_key
        if GeoMapper.dispatch_geography != GeoMapper.supply_primary_geography:
            map_df = GeoMapper.get_instance().map_df(GeoMapper.supply_primary_geography,GeoMapper.dispatch_geography,normalize_as='intensity',map_key=geography_map_key,eliminate_zeros=False)
            self.distribution_losses =  util.remove_df_levels(DfOper.mult([self.distribution_losses,map_df]),GeoMapper.supply_primary_geography)
        self.rio_distribution_losses[year] = copy.deepcopy(self.distribution_losses)


    def set_transmission_losses(self,year):
        transmission_grid_node =self.nodes[self.transmission_node_name]
        coefficients = transmission_grid_node.active_coefficients_total.sum().to_frame()
        coefficients.columns = [year]
        geography_map_key = transmission_grid_node.geography_map_key if hasattr(transmission_grid_node, 'geography_map_key') and transmission_grid_node.geography_map_key is not None else GeoMapper.default_geography_map_key
        if GeoMapper.dispatch_geography != GeoMapper.supply_primary_geography:
            map_df = GeoMapper.get_instance().map_df(GeoMapper.supply_primary_geography,GeoMapper.dispatch_geography,normalize_as='intensity',map_key=geography_map_key,eliminate_zeros=False)
            self.transmission_losses =  util.remove_df_levels(DfOper.mult([coefficients,map_df]),GeoMapper.supply_primary_geography)
        else:
            self.transmission_losses = coefficients
        self.transmission_losses = util.remove_df_levels(self.transmission_losses,'demand_sector',agg_function='mean')
        self.rio_transmission_losses[year] = copy.deepcopy(self.transmission_losses)

    def set_net_load_thresholds(self, year):
        # MOVE?
        distribution_grid_node = self.nodes[self.distribution_grid_node_name]
        dist_stock = distribution_grid_node.stock.values.groupby(level=[GeoMapper.supply_primary_geography,'demand_sector']).sum().loc[:,year].to_frame()
        dist_stock = util.remove_df_levels(DfOper.mult([dist_stock, util.df_slice(self.dispatch_feeder_allocation,year,'year')]),'demand_sector')
        geography_map_key = distribution_grid_node.geography_map_key if hasattr(distribution_grid_node, 'geography_map_key') and distribution_grid_node.geography_map_key is not None else GeoMapper.default_geography_map_key
        if GeoMapper.dispatch_geography != GeoMapper.supply_primary_geography:
            map_df = GeoMapper.get_instance().map_df(GeoMapper.supply_primary_geography,GeoMapper.dispatch_geography, normalize_as='total',map_key=geography_map_key,eliminate_zeros=False)
            dist_stock =  util.remove_df_levels(DfOper.mult([dist_stock,map_df]),GeoMapper.supply_primary_geography)
        transmission_grid_node = self.nodes[self.transmission_node_name]
        transmission_stock = transmission_grid_node.stock.values.groupby(level=[GeoMapper.supply_primary_geography]).sum().loc[:,year].to_frame()
        geography_map_key = transmission_grid_node.geography_map_key if hasattr(distribution_grid_node, 'geography_map_key') and transmission_grid_node.geography_map_key is not None else GeoMapper.default_geography_map_key
        if GeoMapper.dispatch_geography != GeoMapper.supply_primary_geography:
            map_df = GeoMapper.get_instance().map_df(GeoMapper.supply_primary_geography,GeoMapper.dispatch_geography, normalize_as='total', map_key=geography_map_key,eliminate_zeros=False)
            transmission_stock =  util.remove_df_levels(DfOper.mult([transmission_stock,map_df]),GeoMapper.supply_primary_geography)
        self.dispatch.set_thresholds(dist_stock,transmission_stock)


    def prepare_flexible_load(self,year):
        """Calculates the availability of flexible load for the hourly dispatch. Used for nodes like hydrogen and P2G.
        Args:
            year (int) = year of analysis
            loop (int or str) = loop identifier
        Sets:
            flexible_load (dict) = dictionary with keys of  supply_node_name, 'energy' or 'capacity', 'geography', zone (i.e. transmission grid
            or distribution grid), and dispatch_feeder and values of a np.array()
        """
        self.flexible_load= util.recursivedict()
        for zone in self.dispatch_zones:
            for node_name in self.electricity_load_nodes[zone]['flexible']:
                node = self.nodes[node_name]
                if hasattr(node.stock, 'coefficients'):
                    indexer =  util.level_specific_indexer(node.stock.coefficients.loc[:,year],'supply_node',[self.electricity_nodes[zone]+[zone]])
                    energy_demand = util.DfOper.mult([util.remove_df_levels(node.stock.values_energy.loc[:,year].to_frame(),['vintage','supply_technology']), util.remove_df_levels(node.stock.coefficients.loc[indexer,year].to_frame(),['vintage','supply_technology','resource_bin'])])
                    capacity = util.DfOper.mult([util.remove_df_levels(node.stock.values.loc[:,year].to_frame(),['vintage','supply_technology']), util.remove_df_levels(node.stock.coefficients.loc[indexer,year].to_frame(),['vintage','supply_technology','resource_bin'])])
                else:
                    indexer =  util.level_specific_indexer(node.active_coefficients_untraded,'supply_node',[self.electricity_nodes[zone]+[zone]])
                    energy_demand =  util.DfOper.mult([node.active_coefficients_untraded, node.active_supply])
                    capacity = util.DfOper.divi([energy_demand,node.capacity_factor.values.loc[:,year].to_frame()])/ UnitConverter.unit_convert(unit_to_num='hour', unit_from_num = 'year')
                    capacity.replace([np.nan,np.inf], 0,inplace=True)
                if zone == self.distribution_node_name and 'demand_sector' not in node.stock.values.index.names:
                    #requires energy on the distribution system to be allocated to feeder for dispatch
                    energy_demand = DfOper.mult([energy_demand, node.active_supply.groupby(level=[GeoMapper.supply_primary_geography,'demand_sector']).transform(lambda x: x/x.sum())])
                    capacity = DfOper.mult([capacity, node.active_supply.groupby(level=[GeoMapper.supply_primary_geography,'demand_sector']).transform(lambda x: x/x.sum())])
                #geomap to dispatch geography
                remove_levels = []
                if GeoMapper.dispatch_geography != GeoMapper.supply_primary_geography:
                    geography_map_key = node.geography_map_key if hasattr(node, 'geography_map_key') and node.geography_map_key is not None else GeoMapper.default_geography_map_key
                    map_df = GeoMapper.get_instance().map_df(GeoMapper.supply_primary_geography,GeoMapper.dispatch_geography,normalize_as='total',map_key=geography_map_key, eliminate_zeros=False)
                    energy_demand = DfOper.mult([energy_demand,map_df])
                    capacity = DfOper.mult([capacity,map_df])
                    remove_levels.append(GeoMapper.dispatch_geography)
                if zone == self.distribution_node_name:
                    #specific for distribution node because of feeder allocation requirement
                    indexer = util.level_specific_indexer(self.dispatch_feeder_allocation, 'year', year)
                    energy_demand = util.remove_df_levels(util.DfOper.mult([energy_demand, self.dispatch_feeder_allocation.loc[indexer, ]]), 'demand_sector')
                    capacity = util.remove_df_levels(util.DfOper.mult([capacity, self.dispatch_feeder_allocation.loc[indexer, ]]), 'demand_sector')
                    remove_levels.append('dispatch_feeder')
                    for geography in GeoMapper.dispatch_geographies:
                        for dispatch_feeder in self.dispatch_feeders:
                            indexer = util.level_specific_indexer(energy_demand, [GeoMapper.dispatch_geography, 'supply_node', 'dispatch_feeder'],[geography,zone,dispatch_feeder])
                            self.flexible_load[node.name][geography][zone][dispatch_feeder]['energy']= util.remove_df_levels(energy_demand.loc[indexer,:],remove_levels)
                            indexer = util.level_specific_indexer(capacity, [GeoMapper.dispatch_geography, 'supply_node', 'dispatch_feeder'],[geography,zone,dispatch_feeder])
                            self.flexible_load[node.name][geography][zone][dispatch_feeder]['capacity']= util.remove_df_levels(capacity.loc[indexer,:],remove_levels)
                else:
                    remove_levels.append('demand_sector')
                    for geography in GeoMapper.dispatch_geographies:
                        #feeder is set to 0 for flexible load not on the distribution system
                        indexer = util.level_specific_indexer(energy_demand, [GeoMapper.dispatch_geography, 'supply_node'],[geography,zone])
                        self.flexible_load[node.name][geography][zone]['bulk']['energy']= util.remove_df_levels(energy_demand.loc[indexer,:],remove_levels)
                        indexer = util.level_specific_indexer(capacity,[GeoMapper.dispatch_geography, 'supply_node'],[geography,zone])
                        self.flexible_load[node.name][geography][zone]['bulk']['capacity']= util.remove_df_levels(capacity.loc[indexer,:],remove_levels)
        self.flexible_load = util.freeze_recursivedict(self.flexible_load)

    def prepare_flexible_gen(self,year):
        """Calculates the availability of flexible generation for the hourly dispatch. Used for nodes like hydroelectricity.
        Args:
            year (int) = year of analysis
            loop (int or str) = loop identifier
        Sets:
            flexible_gen (dict) = dictionary with keys of  supply_node_name, 'energy' or 'capacity', 'geography', zone (i.e. transmission grid
            or distribution grid), and dispatch_feeder and values of a np.array()
        """
        self.flexible_gen = util.recursivedict()
        for zone in self.dispatch_zones:
            non_thermal_dispatch_nodes = [x for x in self.electricity_gen_nodes[zone]['flexible'] if x not in self.nodes[self.thermal_dispatch_node_name].values.index.get_level_values('supply_node')]
            for node_name in non_thermal_dispatch_nodes:
                node = self.nodes[node_name]
                energy = node.active_supply
                capacity = node.stock.values.loc[:,year].to_frame()
                if zone == self.distribution_node_name and 'demand_sector' not in node.stock.values.index.names:
                    #requires energy on the distribution system to be allocated to feeder for dispatch
                    energy = DfOper.mult([energy, node.active_supply.groupby(level=[GeoMapper.supply_primary_geography,'demand_sector']).transform(lambda x: x/x.sum())])
                    capacity = DfOper.mult([capacity, node.active_supply.groupby(level=[GeoMapper.supply_primary_geography,'demand_sector']).transform(lambda x: x/x.sum())])
                energy = util.remove_df_levels(energy,['vintage', 'supply_technology'])
                capacity = util.remove_df_levels(capacity,['vintage', 'supply_technology'])
                #geomap to dispatch geography
                if GeoMapper.dispatch_geography != GeoMapper.supply_primary_geography:
                    geography_map_key = node.geography_map_key if hasattr(node, 'geography_map_key') and node.geography_map_key is not None else GeoMapper.default_geography_map_key
                    map_df = GeoMapper.get_instance().map_df(GeoMapper.supply_primary_geography,GeoMapper.dispatch_geography,normalize_as='total',map_key=geography_map_key, eliminate_zeros=False)
                    energy = DfOper.mult([energy,map_df])
                    capacity = DfOper.mult([capacity,map_df])
                if zone == self.distribution_node_name:
                    #specific for distribution node because of feeder allocation requirement
                    indexer = util.level_specific_indexer(self.dispatch_feeder_allocation, 'year', year)
                    energy = util.remove_df_levels(util.DfOper.mult([energy, self.dispatch_feeder_allocation.loc[indexer, ]]), 'demand_sector')
                    capacity = util.remove_df_levels(util.DfOper.mult([capacity, self.dispatch_feeder_allocation.loc[indexer, ]]), 'demand_sector')
                    for geography in GeoMapper.dispatch_geographies:
                        for dispatch_feeder in self.dispatch_feeders:
                            indexer = util.level_specific_indexer(energy, GeoMapper.dispatch_geography, geography)
                            remove_list =  ['dispatch_feeder','supply_node']
                            if GeoMapper.supply_primary_geography!=GeoMapper.dispatch_geography:
                                remove_list.append(GeoMapper.dispatch_geography)
                            indexer = util.level_specific_indexer(energy, [GeoMapper.dispatch_geography, 'dispatch_feeder'],[geography,zone,dispatch_feeder])
                            self.flexible_gen[node.name][geography][zone][dispatch_feeder]['energy']= util.remove_df_levels(energy.loc[indexer,:],remove_list)
                            indexer = util.level_specific_indexer(capacity, [GeoMapper.dispatch_geography, 'dispatch_feeder'],[geography,zone,dispatch_feeder])
                            self.flexible_gen[node.name][geography][zone][dispatch_feeder]['capacity']= util.remove_df_levels(capacity.loc[indexer,:],remove_list)
                else:
                    for geography in GeoMapper.dispatch_geographies:
                        #feeder is set to 0 for flexible load not on the distribution system
                        indexer = util.level_specific_indexer(energy, GeoMapper.dispatch_geography, geography)
                        remove_list =  ['demand_sector','supply_node']
                        if GeoMapper.supply_primary_geography!=GeoMapper.dispatch_geography:
                            remove_list.append(GeoMapper.dispatch_geography)
                        self.flexible_gen[node.name][geography][zone]['bulk']['energy'] = util.remove_df_levels(energy.loc[indexer,:],remove_list)
                        indexer = util.level_specific_indexer(capacity,GeoMapper.dispatch_geography, geography)
                        self.flexible_gen[node.name][geography][zone]['bulk']['capacity'] = util.remove_df_levels(capacity.loc[indexer,:],remove_list)
        self.flexible_gen = util.freeze_recursivedict(self.flexible_gen)

    def _help_prepare_non_flexible_load_or_gen(self, energy, year, node, zone):
        energy['dispatch_zone'] = zone
        energy['supply_node'] = node.name # replace supply node with the node id
        energy = energy.set_index(['dispatch_zone', 'supply_node'], append=True)
        if zone == self.distribution_node_name:
            energy = util.DfOper.mult([energy, self.dispatch_feeder_allocation.xs(year, level='year')])
        else:
            energy['dispatch_feeder'] = 'bulk'
            energy = energy.set_index('dispatch_feeder', append=True)
        energy = util.remove_df_levels(energy, 'demand_sector')

        if GeoMapper.dispatch_geography != GeoMapper.supply_primary_geography:
           #geomap to dispatch geography
            geography_map_key = node.geography_map_key if hasattr(node, 'geography_map_key') and node.geography_map_key is not None else GeoMapper.default_geography_map_key
            map_df = GeoMapper.get_instance().map_df(GeoMapper.supply_primary_geography, GeoMapper.dispatch_geography, normalize_as='total', map_key=geography_map_key, eliminate_zeros=False)
            energy = DfOper.mult([energy, map_df])
        return energy

    def prepare_non_flexible_load(self, year):
        # MOVE
        """Calculates the demand from non-flexible load on the supply-side
        Args:
            year (int) = year of analysis
            loop (int or str) = loop identifier
        Sets:
            non_flexible_load (df)

        """
        self.non_flexible_load = []
        for zone in self.dispatch_zones:
            for node_name in self.electricity_load_nodes[zone]['non_flexible']:
                node = self.nodes[node_name]
                indexer = util.level_specific_indexer(node.active_coefficients_untraded,'supply_node',[list(set(self.electricity_nodes[zone]+[zone]))])
                energy = DfOper.mult([node.active_supply, node.active_coefficients_untraded.loc[indexer,:]])
                energy = util.remove_df_levels(energy, ['supply_node', 'efficiency_type']) # supply node is electricity transmission or distribution
                energy = self._help_prepare_non_flexible_load_or_gen(energy, year, node, zone)
                self.non_flexible_load.append(energy) # important that the order of the columns be correct
        if len(self.non_flexible_load):
            self.non_flexible_load = util.df_list_concatenate(self.non_flexible_load)
        else:
            self.non_flexible_load = None

    def prepare_non_flexible_gen(self,year):
        # MOVE
        """Calculates the supply from non-flexible generation on the supply-side
        Args:
            year (int) = year of analysis
            loop (int or str) = loop identifier
        Sets:
            non_flexible_load (df)
        """
        self.non_flexible_gen = []
        for zone in self.dispatch_zones:
            non_thermal_dispatch_nodes = [x for x in self.electricity_gen_nodes[zone]['non_flexible'] if x not in self.nodes[self.thermal_dispatch_node_name].values.index.get_level_values('supply_node')]
            for node_name in non_thermal_dispatch_nodes:
                node = self.nodes[node_name]
                energy = node.active_supply.copy()
                energy = self._help_prepare_non_flexible_load_or_gen(energy, year, node, zone)
                self.non_flexible_gen.append(energy)
        if len(self.non_flexible_gen):
            self.non_flexible_gen = util.df_list_concatenate(self.non_flexible_gen)
        else:
            self.non_flexible_gen = None

    def prepare_dispatch_inputs(self, year, loop):
        # MOVE
        """Calculates supply node parameters needed to run electricity dispatch
        Args:
            year (int) = year of analysis
            loop (int or str) = loop identifier
        """
        logging.info("      preparing dispatch inputs")
        self.solved_gen_list = []
        self.set_electricity_gen_nodes(self.nodes[self.distribution_node_name],self.nodes[self.distribution_node_name])
        self.solved_gen_list = []
        self.set_electricity_load_nodes()
        self.set_dispatchability()
        self.prepare_non_flexible_gen(year)
        self.prepare_flexible_gen(year)
        self.prepare_non_flexible_load(year)
        self.prepare_flexible_load(year)
        self.prepare_thermal_dispatch_nodes(year,loop)
        self.prepare_electricity_storage_nodes(year,loop)
        self.set_distribution_losses(year)
        self.set_transmission_losses(year)
        self.set_shapes(year)
        self.set_initial_net_load_signals(year)

    def prepare_dispatch_inputs_RIO(self, year, loop):
        # MOVE
        """Calculates supply node parameters needed to run electricity dispatch
        Args:
            year (int) = year of analysis
            loop (int or str) = loop identifier
        """
        logging.info("      preparing dispatch inputs")
        self.solved_gen_list = []
        self.set_electricity_gen_nodes(self.nodes[self.distribution_node_name],self.nodes[self.distribution_node_name])
        self.solved_gen_list = []
        self.set_electricity_load_nodes()
        self.set_dispatchability()
        self.prepare_non_flexible_gen(year)
        self.prepare_flexible_gen(year)
        self.prepare_non_flexible_load(year)
        self.prepare_flexible_load(year)
        self.set_distribution_losses(year)
        self.set_transmission_losses(year)
        self.set_shapes(year)
        self.set_initial_net_load_signals(year)

    def solve_electricity_dispatch(self, year):
        # MOVE
        """solves heuristic dispatch, optimization dispatch, and thermal dispatch
        Args:
            year (int) = year of analysis
        """
        #solves dispatched load and gen on the supply-side for nodes like hydro and H2 electrolysis
        self.solve_heuristic_load_and_gen(year)
        #solves electricity storage and flexible demand load optimizatio
        self.solve_storage_and_flex_load_optimization(year)
        #updates the grid capacity factors for distribution and transmission grid (i.e. load factors)
        self.set_grid_capacity_factors(year)
        #solves dispatch (stack model) for thermal resource connected to thermal dispatch node
        self.solve_thermal_dispatch(year)
        self.solve_hourly_curtailment(year)
        if year in self.dispatch_write_years and not self.api_run:
            if cfg.filter_dispatch_less_than_x is not None:
                self.bulk_dispatch = self.bulk_dispatch.groupby(level=['DISPATCH_OUTPUT']).filter(
                    lambda x: x.max().max()>cfg.filter_dispatch_less_than_x or x.min().min()<-cfg.filter_dispatch_less_than_x)

            if cfg.getParamAsBoolean('keep_dispatch_outputs_in_model', section='output_detail'):
                self.outputs.hourly_dispatch_results = pd.concat([self.outputs.hourly_dispatch_results, self.bulk_dispatch])
            else:
                # we are going to save them as we go along
                result_df = self.outputs.clean_df(self.bulk_dispatch)
                if cfg.rio_supply_run:
                    scenario = self.rio_scenario.upper()
                else:
                    scenario = self.scenario.name.upper()
                keys = [scenario, cfg.timestamp]
                names = ['SCENARIO','TIMESTAMP']
                for key, name in zip(keys, names):
                    result_df = pd.concat([result_df], keys=[key], names=[name])
                Output.write(result_df, 'hourly_dispatch_results.csv', os.path.join(cfg.workingdir, 'dispatch_outputs'))
        self.calculate_thermal_totals(year)
        self.calculate_curtailment(year)

    def solve_electricity_dispatch_rio(self, year):
        # MOVE
        """solves heuristic dispatch, optimization dispatch, and thermal dispatch
        Args:
            year (int) = year of analysis
        """
        #solves dispatched load and gen on the supply-side for nodes like hydro and H2 electrolysis
        self.solve_heuristic_load_and_gen(year)
        #solves electricity storage and flexible demand load optimizatio
        self.solve_storage_and_flex_load_optimization(year)
        #updates the grid capacity factors for distribution and transmission grid (i.e. load factors)
        self.set_grid_capacity_factors(year)
        #solves dispatch (stack model) for thermal resource connected to thermal dispatch node
        if year in self.dispatch_write_years and not self.api_run:
            if cfg.filter_dispatch_less_than_x is not None:
                self.bulk_dispatch = self.bulk_dispatch.groupby(level=['DISPATCH_OUTPUT']).filter(
                    lambda x: x.max().max()>cfg.filter_dispatch_less_than_x or x.min().min()<-cfg.filter_dispatch_less_than_x)
            if cfg.keep_dispatch_outputs_in_model.lower() == 'true':
                self.outputs.hourly_dispatch_results = pd.concat([self.outputs.hourly_dispatch_results, self.bulk_dispatch])
            else:
                # we are going to save them as we go along
                result_df = self.outputs.clean_df(self.bulk_dispatch)
                keys = [self.scenario.name.upper(), cfg.timestamp]
                names = ['SCENARIO','TIMESTAMP']
                for key, name in zip(keys, names):
                    result_df = pd.concat([result_df], keys=[key], names=[name])
                Output.write(result_df, 'hourly_dispatch_results.csv', os.path.join(cfg.workingdir, 'dispatch_outputs'))




    def solve_hourly_curtailment(self,year):
        # MOVE
        if year in self.dispatch_write_years:
            curtailment =  -util.remove_df_levels(self.bulk_dispatch,'DISPATCH_OUTPUT')
            curtailment['DISPATCH_OUTPUT'] = 'CURTAILMENT'
            curtailment = curtailment.set_index('DISPATCH_OUTPUT',append=True)
            curtailment = curtailment.reorder_levels(self.bulk_dispatch.index.names)
            self.bulk_dispatch = pd.concat([self.bulk_dispatch,curtailment])



    def prepare_thermal_dispatch_nodes(self,year,loop):
        # MOVE
        """Calculates the operating cost of all thermal dispatch resources
        Args:
            year (int) = year of analysis
            loop (int or str) = loop identifier
        Sets:
            thermal_dispatch_dict (dict) = dictionary with keys of dispatch location (i.e. geography analysis unit)
            , a key from the list ['capacity', 'cost', 'maintenance_outage_rate', 'forced_outage_rate', 'must_run'] and a tuple with the thermal resource identifier. Values are either float or boolean.
        """
        dataframes = []
        keys = self.demand_sectors
        names = ['demand_sector']
        #apennds sector costs to list
        for sector in self.demand_sectors:
            dataframes.append(self.cost_dict[year][sector].sum())
        #concatenates sector costs into single dataframe
        embodied_cost_df  = pd.concat(dataframes,keys=keys,names=names)
        embodied_cost_df = embodied_cost_df.reorder_levels([GeoMapper.supply_primary_geography,'demand_sector','supply_node']).to_frame()
        embodied_cost_df.sort(inplace=True)
        self.dispatch_df = embodied_cost_df
        self.thermal_dispatch_nodes = [x for x in set(list(self.nodes[self.thermal_dispatch_node_name].active_coefficients.index.get_level_values('supply_node')))]
        dispatch_resource_list = []
        for node_name in self.thermal_dispatch_nodes:
            stock_values = self.nodes[node_name].stock.values.loc[:,year].to_frame()
            cap_factor_values = self.nodes[node_name].stock.capacity_factor.loc[:,year].to_frame()
            stock_values = stock_values[((stock_values.index.get_level_values('vintage')==year) == True) | ((stock_values[year]>0) == True)]
            stock_values = stock_values[((cap_factor_values[year]>0) == True)]
            resources = [str(x[0]) for x in stock_values.groupby(level = stock_values.index.names).groups.values()]
            inputs_and_outputs = ['capacity','cost','maintenance_outage_rate','forced_outage_rate','capacity_weights','must_run','gen_cf','generation','stock_changes','thermal_capacity_multiplier']
            node_list = [node_name]
            index = pd.MultiIndex.from_product([GeoMapper.dispatch_geographies, node_list, resources,inputs_and_outputs],names = [GeoMapper.dispatch_geography, 'supply_node','thermal_generators','IO'])
            dispatch_resource_list.append(util.empty_df(index=index,columns=[year],fill_value=0.0))
        self.active_thermal_dispatch_df = pd.concat(dispatch_resource_list)
        self.active_thermal_dispatch_df.sort(inplace=True)
        for node_name in self.thermal_dispatch_nodes:
            node = self.nodes[node_name]
            if hasattr(node, 'calculate_dispatch_costs'):
                node.calculate_dispatch_costs(year, embodied_cost_df,loop)
                if hasattr(node,'active_dispatch_costs'):
                    active_dispatch_costs = node.active_dispatch_costs
                    #TODO Remove 1 is the Reference Case
                    if self.CO2PriceMeasure:
                        co2_price = util.df_slice(self.CO2PriceMeasure.values,year,'year')
                        co2_price.columns = [year]
                    else:
                        co2_price=0
                    if hasattr(node,'active_physical_emissions_coefficients') and hasattr(node,'active_co2_capture_rate'):
                        total_physical =node.active_physical_emissions_coefficients.groupby(level='supply_node').sum().stack().stack().to_frame()
                        emissions_rate = util.DfOper.mult([node.stock.dispatch_coefficients.loc[:,year].to_frame(), util.DfOper.divi([total_physical,node.active_coefficients_untraded]).replace([np.inf,np.nan],0)])
#                        emissions_rate = util.DfOper.mult([node.stock.dispatch_coefficients.loc[:,year].to_frame(), util.DfOper.divi([total_physical,node.active_emissions_coefficients.transpose().groupby(level='supply_node',axis=1).sum().stack().to_frame()]).replace([np.inf,np.nan],0)])
                        emissions_rate = util.remove_df_levels(emissions_rate,'supply_node')
                        emissions_rate = util.remove_df_levels(emissions_rate,[x for x in emissions_rate.index.names if x not in node.stock.values.index.names],agg_function='mean')
                        co2_cost = util.DfOper.mult([emissions_rate, 1-node.rollover_output(tech_class = 'co2_capture', stock_att='exist',year=year)]) * co2_price * UnitConverter.unit_convert(unit_from_den='ton',unit_to_den=cfg.getParam('mass_unit'))
                        active_dispatch_costs = util.DfOper.add([node.active_dispatch_costs ,co2_cost])
                    stock_values = node.stock.values.loc[:,year].to_frame()
                    stock_values = stock_values[((stock_values.index.get_level_values('vintage')==year) == True) | ((stock_values[year]>0) == True)]
                    capacity_factor = copy.deepcopy(node.stock.capacity_factor.loc[:,year].to_frame())
                    if GeoMapper.dispatch_geography != GeoMapper.supply_primary_geography:
                        geography_map_key = node.geography_map_key if hasattr(node, 'geography_map_key') and node.geography_map_key is not None else GeoMapper.default_geography_map_key
                        int_map_df = GeoMapper.get_instance().map_df(GeoMapper.supply_primary_geography,GeoMapper.dispatch_geography,  normalize_as='intensity', map_key=geography_map_key, eliminate_zeros=False)
                        tot_map_df = GeoMapper.get_instance().map_df(GeoMapper.supply_primary_geography, GeoMapper.dispatch_geography, normalize_as='total', map_key=geography_map_key, eliminate_zeros=False).swaplevel(0,1)
                        active_dispatch_costs = util.remove_df_levels(util.DfOper.mult([int_map_df,active_dispatch_costs],fill_value=0.0),GeoMapper.supply_primary_geography).swaplevel(0,GeoMapper.dispatch_geography)
                        active_dispatch_costs = active_dispatch_costs.replace([np.nan,np.inf],0)
                        stock_values = util.DfOper.mult([tot_map_df,stock_values],fill_value=0.0).swaplevel(0,GeoMapper.dispatch_geography).swaplevel(1,GeoMapper.supply_primary_geography)
                        capacity_factor = util.remove_df_levels(util.DfOper.mult([int_map_df, capacity_factor,],fill_value=0.0),GeoMapper.supply_primary_geography).swaplevel(0,GeoMapper.dispatch_geography)
                    groups = [x[0]for x in stock_values.groupby(level=stock_values.index.names).groups.values()]
                    for group in groups:
                        dispatch_geography = group[0]
                        if GeoMapper.supply_primary_geography == GeoMapper.dispatch_geography:
                            geomapped_resource = group
                            resource = group
                        else:
                            geomapped_resource = (group[0],) +group[2:]
                            resource = group[1:]
                        self.active_thermal_dispatch_df.loc[(dispatch_geography,node.name,str(resource),'capacity'),year] = stock_values.loc[group].values[0]
                        self.active_thermal_dispatch_df.loc[(dispatch_geography,node.name,str(resource), 'cost'),year] = active_dispatch_costs.loc[geomapped_resource].values[0]
                        self.active_thermal_dispatch_df.loc[(dispatch_geography,node.name,str(resource),'maintenance_outage_rate'),year] = (1- capacity_factor.loc[geomapped_resource].values[0])*.9
                        self.active_thermal_dispatch_df.loc[(dispatch_geography,node.name, str(resource), 'forced_outage_rate'),year]= np.nan_to_num((1- capacity_factor.loc[geomapped_resource].values[0])*.1/(1-self.active_thermal_dispatch_df.loc[(dispatch_geography,node.name,str(resource),'maintenance_outage_rate'),year]))
                        self.active_thermal_dispatch_df.loc[(dispatch_geography,node.name, str(resource), 'thermal_capacity_multiplier'),year] = node.technologies[resource[1]].thermal_capacity_multiplier
                        if hasattr(node,'is_flexible') and node.is_flexible == False:
                            self.active_thermal_dispatch_df.loc[(dispatch_geography,node.name, str(resource), 'must_run'),year] = 1
        self.active_thermal_dispatch_df = self.active_thermal_dispatch_df[((np.array([int(x[-6:-2]) for x in self.active_thermal_dispatch_df.index.get_level_values('thermal_generators')])==year) == True) | ((self.active_thermal_dispatch_df.groupby(level=[GeoMapper.dispatch_geography,'thermal_generators']).transform(lambda x: x.sum())[year]>0) == True)]

    def capacity_weights(self,year):
        """sets the share of new capacity by technology and location to resolve insufficient capacity in the thermal dispatch
        Args:
            year (int) = year of analysis
        Sets:
            thermal_dispatch_dict (dict) = set dictionary with keys of dispatch geography, 'capacity_weights', and a tuple thermal resource identifier. Values are the share of new capacity
            by thermal resource identifier in a specified dispatch geography.
        """
        weights = self.nodes[self.thermal_dispatch_node_name].values.loc[:,year].to_frame().groupby(level=[GeoMapper.supply_primary_geography,'supply_node']).mean()
        if GeoMapper.dispatch_geography != GeoMapper.supply_primary_geography:
            map_df = GeoMapper.get_instance().map_df(GeoMapper.supply_primary_geography,GeoMapper.dispatch_geography, normalize_as='intensity', eliminate_zeros=False)
            weights = util.DfOper.mult([map_df,weights]).swaplevel(0,GeoMapper.dispatch_geography)
            for dispatch_geography in GeoMapper.dispatch_geographies:
                for node_name in self.thermal_nodes:
                    node = self.nodes[node_name]
                    resources = list(set(util.df_slice(self.active_thermal_dispatch_df, [dispatch_geography, node_name], [GeoMapper.dispatch_geography, 'supply_node']).index.get_level_values('thermal_generators')))
                    for resource in resources:
                        resource = eval(resource)
                        if resource[-1] == year:
                            self.active_thermal_dispatch_df.loc[(dispatch_geography,node.name, str(resource), 'capacity_weights'),year]= (util.df_slice(weights,[dispatch_geography, resource[0], node_name],[GeoMapper.dispatch_geography,GeoMapper.supply_primary_geography,'supply_node']).values * node.active_weighted_sales.loc[resource[0:-1:1],:].values)[0][0]
        else:
            for dispatch_geography in GeoMapper.dispatch_geographies:
                for node_name in self.thermal_nodes:
                    node = self.nodes[node_name]
                    resources = list(set(util.df_slice(self.active_thermal_dispatch_df, [dispatch_geography, node_name], [GeoMapper.dispatch_geography, 'supply_node']).index.get_level_values('thermal_generators')))
                    for resource in resources:
                        resource = eval(resource)
                        if resource[-1] == year and resource[0]== dispatch_geography:
                            self.active_thermal_dispatch_df.loc[(dispatch_geography,node.name, str(resource), 'capacity_weights'),year]= (util.df_slice(weights,[dispatch_geography, node_name],[GeoMapper.dispatch_geography,'supply_node']).values * node.active_weighted_sales.loc[resource[0:-1:1],:].values)[0][0]


    def calculate_weighted_sales(self,year):
        """sets the anticipated share of sales by technology for capacity additions added in the thermal dispatch.
        Thermal dispatch inputs determines share by supply_node, so we have to determine the share of technologies for
        that capacity addition.

        Args:
            year (int) = year of analysis
        Sets:
            active_weighted_sales (dataframe) = share of sales by technology for each thermal dispatch node
        """
        for node_name in self.thermal_nodes:
            node = self.nodes[node_name]
            vintage_start = min(node.vintages) -1
            total = []
            for elements in node.rollover_groups.keys():
                elements = util.ensure_tuple(elements)
                sales_share, initial_sales_share = node.calculate_total_sales_share(elements,
                                                           node.stock.rollover_group_names)
                sales_share = sales_share[year-min(node.vintages)]
                total.append(sales_share)
            total = np.concatenate(total)
            weighted_sales = node.stock.retirements[node.stock.retirements.index.get_level_values('vintage')==year]
            if weighted_sales.sum().sum() == 0:
                weighted_sales[weighted_sales.values==0] = 1
            for tech_name in node.tech_names:
                weighted_sales[tech_name] = weighted_sales['value']
            weighted_sales = weighted_sales[node.tech_names]
            weighted_sales*=total
            weighted_sales =  weighted_sales.sum(axis=1).to_frame()
            weighted_sales.columns = ['value']
            weighted_sales *= (np.column_stack(weighted_sales.index.get_level_values('vintage').values).T-vintage_start)
            weighted_sales = util.remove_df_levels(weighted_sales,'vintage')
            weighted_sales = weighted_sales.groupby(level = GeoMapper.supply_primary_geography).transform(lambda x: x/x.sum())
            node.active_weighted_sales = weighted_sales
            node.active_weighted_sales = node.active_weighted_sales.fillna(1/float(len(node.tech_names)))

    def solve_thermal_dispatch(self, year):
        # MOVE
        """solves the thermal dispatch, updating the capacity factor for each thermal dispatch technology
        and adding capacity to each node based on determination of need"""
        logging.info('      solving thermal dispatch')
        self.calculate_weighted_sales(year)
        self.capacity_weights(year)
        parallel_params = list(zip(GeoMapper.dispatch_geographies,[util.df_slice(self.active_thermal_dispatch_df,x,GeoMapper.dispatch_geography,drop_level=False) for x in GeoMapper.dispatch_geographies],
                                   [GeoMapper.dispatch_geography]*len(GeoMapper.dispatch_geographies),
                                    [self.bulk_net_load]*len(GeoMapper.dispatch_geographies),
                                    [year in self.dispatch_write_years]*len(GeoMapper.dispatch_geographies),
                                   [cfg.getParamAsFloat('operating_reserves', 'opt')]*len(GeoMapper.dispatch_geographies),
                                   [cfg.getParamAsBoolean('schedule_maintenance', section='opt')]*len(GeoMapper.dispatch_geographies)))

        if cfg.getParamAsBoolean('parallel_process'):
            dispatch_results = helper_multiprocess.safe_pool(dispatch_generators.run_thermal_dispatch, parallel_params)
        else:
            dispatch_results = []
            for params in parallel_params:
                dispatch_results.append(dispatch_generators.run_thermal_dispatch(params))

        thermal_dispatch_df, detailed_results = zip(*dispatch_results) #both of these are lists by geography
        thermal_dispatch_df = pd.concat(thermal_dispatch_df).sort_index()
        self.active_thermal_dispatch_df = thermal_dispatch_df

        if year in self.dispatch_write_years:
            for x in detailed_results:
                x['dispatch_by_category'].index = Shapes.get_active_dates_index()

            thermal_shape = pd.concat([x['dispatch_by_category'] for x in detailed_results],axis=0,keys=GeoMapper.dispatch_geographies)
            thermal_shape = thermal_shape.stack().to_frame()
            thermal_shape = pd.concat([thermal_shape], keys=[year], names=['year'])
            thermal_shape.index.names = ['year', GeoMapper.dispatch_geography, 'weather_datetime','supply_technology']
            thermal_shape.columns = [cfg.calculation_energy_unit.upper()]
            thermal_shape_dataframe = self.outputs.clean_df(thermal_shape)
            util.replace_index_name(thermal_shape_dataframe,'DISPATCH_OUTPUT','SUPPLY_TECHNOLOGY')
            self.bulk_dispatch = pd.concat([self.bulk_dispatch, -thermal_shape_dataframe.reorder_levels(self.bulk_dispatch.index.names)])

            bulk_marginal_cost = pd.concat([pd.DataFrame(outputs['market_price'], index=Shapes.get_active_dates_index()) for outputs in detailed_results],axis=0,keys=GeoMapper.dispatch_geographies)
            bulk_production_cost = pd.concat([pd.DataFrame(outputs['production_cost'], index=Shapes.get_active_dates_index()) for outputs in detailed_results],axis=0,keys=GeoMapper.dispatch_geographies)
            bulk_marginal_cost = pd.concat([bulk_marginal_cost], keys=[year], names=['year'])
            bulk_production_cost = pd.concat([bulk_production_cost], keys=[year], names=['year'])
            bulk_marginal_cost.index.names = ['year', GeoMapper.dispatch_geography, 'weather_datetime']
            bulk_production_cost.index.names = ['year', GeoMapper.dispatch_geography, 'weather_datetime']
            # we really don't want this ever to be anything but $/MWh
            bulk_marginal_cost *= UnitConverter.unit_convert(1, unit_from_den=cfg.calculation_energy_unit,unit_to_den='megawatt_hour')
            bulk_marginal_cost.columns = ["{} / {}".format(cfg.output_currency.upper(), 'MWh')]
            bulk_production_cost.columns = [cfg.output_currency.upper()]
            # bulk_marginal_cost = self.outputs.clean_df(bulk_marginal_cost)
            # bulk_production_cost = self.outputs.clean_df(bulk_production_cost)

            if cfg.getParamAsBoolean('keep_dispatch_outputs_in_model', section='output_detail'):
                self.outputs.hourly_marginal_cost = pd.concat([self.outputs.hourly_marginal_cost, bulk_marginal_cost])
                self.outputs.hourly_production_cost = pd.concat([self.outputs.hourly_production_cost, bulk_production_cost])
            else:
                # we are going to save them as we go along
                for obj, obj_name in zip([bulk_marginal_cost, bulk_production_cost], ['hourly_marginal_cost', 'hourly_production_cost']):
                    result_df = self.outputs.clean_df(obj)
                    keys = [self.scenario.name.upper(), cfg.timestamp]
                    names = ['SCENARIO','TIMESTAMP']
                    for key, name in zip(keys, names):
                        result_df = pd.concat([result_df], keys=[key], names=[name])
                    Output.write(result_df, obj_name + '.csv', os.path.join(cfg.workingdir, 'dispatch_outputs'))


        for node_name in self.thermal_dispatch_nodes:
            node = self.nodes[node_name]
            for dispatch_geography in GeoMapper.dispatch_geographies:
                dispatch_df = util.df_slice(self.active_thermal_dispatch_df.loc[:,:],[dispatch_geography,node_name], [GeoMapper.dispatch_geography,'supply_node'],drop_level=False)
                resources = list(set([eval(x) for x in dispatch_df.index.get_level_values('thermal_generators')]))
                for resource in resources:
                    capacity_indexer = util.level_specific_indexer(dispatch_df, ['thermal_generators','IO'], [str(resource),'capacity'])
                    dispatch_capacity_indexer = util.level_specific_indexer(dispatch_df,['thermal_generators','IO'], [str(resource),'stock_changes'])
                    node.stock.dispatch_cap.loc[resource,year] += dispatch_df.loc[dispatch_capacity_indexer,year].values
            node.stock.capacity_factor.loc[:,year] = 0
            for dispatch_geography in GeoMapper.dispatch_geographies:
                dispatch_df = util.df_slice(self.active_thermal_dispatch_df.loc[:,:],[dispatch_geography,node_name], [GeoMapper.dispatch_geography,'supply_node'],drop_level=False)
                resources = list(set([eval(x) for x in dispatch_df.index.get_level_values('thermal_generators')]))
                for resource in resources:
                    capacity_indexer = util.level_specific_indexer(dispatch_df, ['thermal_generators','IO'], [str(resource),'capacity'])
                    stock_changes_indexer = util.level_specific_indexer(dispatch_df, ['thermal_generators','IO'], [str(resource),'stock_changes'])
                    if node.stock.values.loc[resource,year] ==0 and node.stock.dispatch_cap.loc[resource,year] == 0:
                        ratio = 0
                    elif node.stock.values.loc[resource,year] ==0 and node.stock.dispatch_cap.loc[resource,year] != 0:
                        ratio = dispatch_df.loc[stock_changes_indexer,year]/node.stock.dispatch_cap.loc[resource,year]
                    else:
                        ratio = dispatch_df.loc[capacity_indexer,year]/node.stock.values.loc[resource,year]
                    ratio = np.nan_to_num(ratio)
                    capacity_factor_indexer = util.level_specific_indexer(dispatch_df,['thermal_generators','IO'], [str(resource),'gen_cf'])
                    capacity_factor = np.nan_to_num(dispatch_df.loc[capacity_factor_indexer,year]*ratio)
                    node.stock.capacity_factor.loc[resource,year] += capacity_factor
                    dispatch_capacity_indexer = util.level_specific_indexer(dispatch_df,['thermal_generators','IO'], [str(resource),'stock_changes'])
                    node.stock.dispatch_cap.loc[resource,year] += dispatch_df.loc[dispatch_capacity_indexer,year].values

    def calculate_curtailment(self,year):
        if year == cfg.getParamAsInt('current_year'):
            self.curtailment_list = []
        initial_overgen = copy.deepcopy(self.bulk_net_load)
        initial_overgen[initial_overgen.values>0]=0
        initial_overgen *= -1
        initial_overgen = initial_overgen.groupby(level=GeoMapper.dispatch_geography).sum()
        bulk_net_load = copy.deepcopy(self.bulk_net_load)
        bulk_net_load[bulk_net_load.values<0] = 0
        curtailment = util.DfOper.add([util.DfOper.subt([self.thermal_totals.sum().to_frame(),bulk_net_load.groupby(level=GeoMapper.dispatch_geography).sum()]),initial_overgen])
        supply = self.nodes[self.bulk_electricity_node_name].active_supply
        if GeoMapper.supply_primary_geography!= GeoMapper.dispatch_geography:
            map_df = GeoMapper.get_instance().map_df(GeoMapper.supply_primary_geography,GeoMapper.dispatch_geography,normalize_as='total',eliminate_zeros=False)
            supply = util.DfOper.mult([supply,map_df])
        normal_supply = supply.groupby(level=[GeoMapper.dispatch_geography]).transform(lambda x: x/x.sum())
        curtailment = util.DfOper.mult([curtailment,normal_supply])
        if GeoMapper.supply_primary_geography!= GeoMapper.dispatch_geography:
            curtailment = util.remove_df_levels(curtailment,GeoMapper.dispatch_geography)
        curtailment.columns = ['value']
        self.curtailment_list.append(curtailment)
        if year == max(self.dispatch_years):
            keys = self.dispatch_years
            names = ['year']
            self.outputs.s_curtailment = pd.concat(self.curtailment_list,keys=keys, names=names)
            util.replace_index_name(self.outputs.s_curtailment,'sector','demand_sector')
            self.outputs.s_curtailment.columns = [cfg.calculation_energy_unit.upper()]

    def update_coefficients_from_dispatch(self,year):
        self.update_thermal_coefficients(year)
        self.store_active_thermal_df(year)

    def update_thermal_coefficients(self,year):
        # MOVE
        if GeoMapper.supply_primary_geography != GeoMapper.dispatch_geography:
            map_df = GeoMapper.get_instance().map_df(GeoMapper.supply_primary_geography,GeoMapper.dispatch_geography,normalize_as='total',eliminate_zeros=False)
            thermal_demand  = util.DfOper.mult([self.nodes[self.thermal_dispatch_node_name].active_supply,map_df])
            thermal_demand = thermal_demand.unstack(GeoMapper.dispatch_geography)
            thermal_demand.columns = thermal_demand.columns.droplevel()
            demand_supply_ratio = util.DfOper.divi([thermal_demand.groupby(level=GeoMapper.supply_primary_geography).sum(),self.thermal_totals.groupby(level=GeoMapper.supply_primary_geography).sum()])
            demand_supply_ratio[demand_supply_ratio>1]=1
            demand_supply_ratio.replace(np.nan,0,inplace=True)
            df =  self.nodes[self.thermal_dispatch_node_name].active_coefficients_total * 0
            native_thermal = util.DfOper.mult([self.thermal_totals,demand_supply_ratio])
            native_thermal_coefficients = util.DfOper.divi([native_thermal.sum(axis=1).to_frame(),
                                                            self.nodes[self.thermal_dispatch_node_name].active_supply.groupby(level=GeoMapper.supply_primary_geography).sum()]).fillna(0)
            residual_demand = util.DfOper.subt([thermal_demand.groupby(level=GeoMapper.supply_primary_geography).sum(),native_thermal.groupby(level=GeoMapper.supply_primary_geography).sum()])
            residual_demand[residual_demand<0] = 0
            remaining_supply = util.DfOper.subt([self.thermal_totals,native_thermal])
            residual_share = util.DfOper.divi([residual_demand.sum().to_frame(),remaining_supply.sum().to_frame()]).fillna(0)
            residual_share[residual_share>1]=1
            residual_share.replace(np.inf,0,inplace=True)
            residual_supply = copy.deepcopy(remaining_supply)
            excess_supply = copy.deepcopy(remaining_supply)
            excess_supply.loc[:,:] = remaining_supply.values * np.column_stack((1-residual_share).values)
            excess_thermal = excess_supply
            excess_thermal_coefficients = util.DfOper.divi([excess_thermal.sum(axis=1).to_frame(),self.nodes[self.thermal_dispatch_node_name].active_supply.groupby(level=GeoMapper.supply_primary_geography).sum()]).fillna(0)
            residual_supply.loc[:,:] = remaining_supply.values * np.column_stack(residual_share.values)
            undersupply_adjustment = (residual_supply.sum()/residual_demand.sum())
            undersupply_adjustment[undersupply_adjustment>1]=1
            residual_supply_share = residual_supply/residual_supply.sum() * undersupply_adjustment
            residual_supply_share = residual_supply_share.fillna(0)
            util.replace_index_name(residual_supply_share,GeoMapper.supply_primary_geography + "from",GeoMapper.supply_primary_geography)
            residual_supply_share = residual_supply_share.stack().to_frame()
            util.replace_index_name(residual_supply_share,GeoMapper.dispatch_geography)
            residual_demand_stack = residual_demand.stack().to_frame()
            util.replace_index_name(residual_demand_stack,GeoMapper.dispatch_geography)
            residual_thermal = util.remove_df_levels(util.DfOper.mult([residual_supply_share,residual_demand_stack]),GeoMapper.dispatch_geography)
            residual_thermal = residual_thermal.unstack(GeoMapper.supply_primary_geography)
            residual_thermal.columns = residual_thermal.columns.droplevel()
            residual_thermal.loc[:,:] = residual_thermal.values/np.column_stack(self.nodes[self.thermal_dispatch_node_name].active_supply.groupby(level=GeoMapper.supply_primary_geography).sum().T.values).T
            residual_thermal_coefficients = residual_thermal.fillna(0)
            util.replace_index_name(residual_thermal,GeoMapper.supply_primary_geography,GeoMapper.supply_primary_geography + "from")
            for row_sector in self.demand_sectors:
                for col_sector in self.demand_sectors:
                    for row_geo in GeoMapper.supply_geographies:
                        for col_geo in GeoMapper.supply_geographies:
                            if row_sector == col_sector and row_geo == col_geo:
                                native_coeff_row_indexer = util.level_specific_indexer(native_thermal_coefficients,[GeoMapper.supply_primary_geography],[row_geo])
                                excess_coeff_row_indexer = util.level_specific_indexer(excess_thermal_coefficients,[GeoMapper.supply_primary_geography],[row_geo])
                                df_row_indexer = util.level_specific_indexer(df,[GeoMapper.supply_primary_geography,'demand_sector'],[row_geo,row_sector])
                                df_col_indexer = util.level_specific_indexer(df,[GeoMapper.supply_primary_geography,'demand_sector'],[col_geo,col_sector],axis=1)
                                df.loc[df_row_indexer,df_col_indexer] = np.column_stack(df.loc[df_row_indexer,df_col_indexer].values).T + np.column_stack(native_thermal_coefficients.loc[native_coeff_row_indexer,:].values).T
                                df.loc[df_row_indexer,df_col_indexer] = np.column_stack(df.loc[df_row_indexer,df_col_indexer].values).T + np.column_stack(excess_thermal_coefficients.loc[excess_coeff_row_indexer,:].values).T
                            elif row_sector == col_sector:
                                df_row_indexer = util.level_specific_indexer(df,[GeoMapper.supply_primary_geography,'demand_sector'],[row_geo,row_sector])
                                df_col_indexer = util.level_specific_indexer(df,[GeoMapper.supply_primary_geography,'demand_sector'],[col_geo,col_sector],axis=1)
                                residual_coeff_row_indexer = util.level_specific_indexer(residual_thermal_coefficients,[GeoMapper.supply_primary_geography],[row_geo])
                                residual_coeff_col_indexer = util.level_specific_indexer(residual_thermal_coefficients,[GeoMapper.supply_primary_geography],[col_geo],axis=1)
                                df.loc[df_row_indexer,df_col_indexer] = np.column_stack(df.loc[df_row_indexer,df_col_indexer].values).T + np.column_stack(residual_thermal_coefficients.loc[residual_coeff_row_indexer,residual_coeff_col_indexer].values).T
        else:
            df = util.DfOper.divi([self.thermal_totals,util.remove_df_levels(self.nodes[self.thermal_dispatch_node_name].active_supply,'demand_sector')]) # todo this gives us an error when the supply geography = dispatch geography with gau and geography that is the same
            df = pd.concat([df]*len(self.demand_sectors),keys=self.demand_sectors,names=['demand_sector'])
            df = pd.concat([df]*len(self.demand_sectors),keys=self.demand_sectors,names=['demand_sector'],axis=1)
            df = df.reorder_levels([GeoMapper.supply_primary_geography,'demand_sector','supply_node'])
            df = df.reorder_levels([GeoMapper.supply_primary_geography,'demand_sector'],axis=1)
            df = df.reset_index().set_index(df.index.names)
            df = df.T.reset_index().set_index(df.columns.names).T
            df = df.sort_index(axis=0).sort_index(axis=1)
            for row_sector in self.demand_sectors:
                for col_sector in self.demand_sectors:
                    if row_sector != col_sector:
                        row_indexer = util.level_specific_indexer(df,'demand_sector',row_sector,axis=0)
                        col_indexer = util.level_specific_indexer(df,'demand_sector',col_sector,axis=1)
                        df.loc[row_indexer, col_indexer] = 0
        normalized = df.groupby(level=['demand_sector']).transform(lambda x: x/x.sum())
#        df[df<normalized] = normalized
        bulk_multiplier = df.sum()
        df = normalized
        df.replace([np.inf,np.nan],0,inplace=True)
        for row_geo in GeoMapper.supply_geographies:
            for col_geo in GeoMapper.supply_geographies:
                if row_geo == col_geo:
                    row_indexer = util.level_specific_indexer(df,GeoMapper.supply_primary_geography,row_geo)
                    col_indexer = util.level_specific_indexer(df,GeoMapper.supply_primary_geography,col_geo, axis=1)
                    sliced = df.loc[row_indexer,col_indexer]
                    sliced = sliced.clip(lower=1E-10)
                    df.loc[row_indexer,col_indexer] = sliced
        self.nodes[self.thermal_dispatch_node_name].active_coefficients_total = df
        indexer = util.level_specific_indexer(self.nodes[self.bulk_electricity_node_name].values,'supply_node',self.thermal_dispatch_node_name)
        self.nodes[self.bulk_electricity_node_name].values.loc[indexer, year] *= bulk_multiplier.values
        thermal_df = copy.deepcopy(self.nodes[self.bulk_electricity_node_name].values.loc[indexer, year])
        thermal_df[thermal_df>1]=1
        self.nodes[self.bulk_electricity_node_name].values.loc[indexer, year] =0
        #don't normalize these if it's an evolved run. Leave curtailment. Simplifies per-unit accounting
        if cfg.evolved_run == 'false':
            pass
            #self.nodes[self.bulk_electricity_node_name].values.loc[:, year] = util.DfOper.mult([self.nodes[self.bulk_electricity_node_name].values.loc[:, year].to_frame().groupby(level=[GeoMapper.supply_primary_geography,'demand_sector']).transform(lambda x: x/x.sum()),1-util.remove_df_levels(thermal_df,'supply_node').to_frame()],expandable=True)
        self.nodes[self.bulk_electricity_node_name].values.loc[indexer, year] = thermal_df
        self.nodes[self.bulk_electricity_node_name].calculate_active_coefficients(year, 3)

    def store_active_thermal_df(self,year):
        active_thermal_dispatch_df = self.active_thermal_dispatch_df.stack().to_frame()
        util.replace_index_name(active_thermal_dispatch_df,'year')
        self.active_thermal_dispatch_df_list.append(active_thermal_dispatch_df)
        if year == max(self.years):
           self.thermal_dispatch_df = pd.concat(self.active_thermal_dispatch_df_list)

    def calculate_thermal_totals(self,year):
        row_index = pd.MultiIndex.from_product([GeoMapper.supply_geographies, self.thermal_dispatch_nodes], names=[GeoMapper.supply_primary_geography, 'supply_node'])
        col_index = pd.MultiIndex.from_product([GeoMapper.dispatch_geographies],names=[GeoMapper.dispatch_geography])
        df = util.empty_df(index=row_index,columns=col_index)
        for dispatch_geography in GeoMapper.dispatch_geographies:
            for node_name in self.thermal_dispatch_nodes:
                thermal_dispatch_df = util.df_slice(self.active_thermal_dispatch_df,[dispatch_geography,'generation',node_name],[GeoMapper.dispatch_geography,'IO','supply_node'])
                resources = list(set(thermal_dispatch_df.index.get_level_values('thermal_generators')))
                for resource in resources:
                    resource = eval(resource)
                    primary_geography = resource[0]
                    df.loc[(primary_geography,node_name),(dispatch_geography)] += np.nan_to_num(thermal_dispatch_df.loc[str(resource),:].values)
        self.thermal_totals = df


    def add_column_index(self, data):
         names = ['demand_sector', GeoMapper.supply_primary_geography]
         keys = [self.demand_sectors, GeoMapper.geography_to_gau[GeoMapper.supply_primary_geography]]
         data  = copy.deepcopy(data)
         for key,name in zip(keys,names):
             data  = pd.concat([data]*len(key), axis=1, keys=key, names=[name])
         data.columns = data.columns.droplevel(-1)
         return data

    def add_row_index(self, data):
         names = ['demand_sector', GeoMapper.supply_primary_geography]
         keys = [self.demand_sectors, GeoMapper.geography_to_gau[GeoMapper.supply_primary_geography]]
         data  = copy.deepcopy(data.transpose())
         for key,name in zip(keys,names):
             data  = pd.concat([data]*len(key), axis=0, keys=key, names=[name])
         data.index = data.index.droplevel(-1)
         return data

#    def geo_map_thermal_coefficients(self,df,old_geography, new_geography, geography_map_key):
#            if old_geography != new_geography:
#                keys=GeoMapper.geography_to_gau[new_geography]
#                name = [new_geography]
#                df = pd.concat([df] * len(keys),keys=keys,names=name,axis=1)
#                df.sort(inplace=True,axis=1)
#                df.sort(inplace=True,axis=0)
#                map_df = GeoMapper.get_instance().map_df(old_geography,new_geography,geography_map_key,eliminate_zeros=False).transpose()
#                names = [x for x in df.index.names if x not in map_df.index.names]
#                names.reverse()
#                for name in names:
#                    keys=list(set(df.index.get_level_values(name)))
#                    map_df = pd.concat([map_df]*len(keys),keys=keys,names=[name])
#                map_df.index = map_df.index.droplevel(None)
#                names = [x for x in df.columns.names if x not in map_df.columns.names]
#                names.reverse()
#                keys = []
#                for name in names:
#                    keys = list(set(df.columns.get_level_values(name)))
#                    map_df = pd.concat([map_df]*len(keys),keys=keys,names=[name],axis=1)
#                map_df=map_df.reorder_levels(df.index.names,axis=0)
#                map_df = map_df.reorder_levels(df.columns.names,axis=1)
#                map_df.sort(inplace=True,axis=0)
#                map_df.sort(inplace=True,axis=1)
#                old_geographies = list(set(df.columns.get_level_values(old_geography)))
#                new_geographies =list(set(map_df.columns.get_level_values(new_geography)))
#                for old in old_geographies:
#                    for new in new_geographies:
#                        row_indexer = util.level_specific_indexer(df,[new_geography],[new],axis=0)
#                        col_indexer = util.level_specific_indexer(df,[old_geography,new_geography],[old,new],axis=1)
#                        shape = (df.loc[row_indexer,col_indexer].values.shape)
#                        diag = np.ndarray(shape)
#                        np.fill_diagonal(diag,1)
#                df *= map_df.values
#                df = df.groupby(level=util.ix_excl(df,old_geography,axis=1),axis=1).sum()
#            return df

    def prepare_electricity_storage_nodes(self,year,loop):
        """Calculates the efficiency and capacity (energy and power) of all electric
        storage nodes
            year (int) = year of analysis
            loop (int or str) = loop identifier
        Sets:
            storage_capacity_dict (dict) = dictionary with keys of 'power' or 'duration', dispatch_geography, dispatch_zone, feeder, and technology and
            values of type float
            storage_efficiency_dict (dict) = dictionary with keys dispatch_geography, dispatch_zone, feeder, and technology and
            values of type floa
        Args:t
        """
        self.storage_efficiency_dict =  util.recursivedict()
        self.storage_capacity_dict = util.recursivedict()
        for node in [x for x in self.nodes.values() if x.supply_type == 'Storage']:
            for zone in self.dispatch_zones:
                node.calculate_dispatch_coefficients(year, loop)
                if hasattr(node,'active_dispatch_coefficients'):
                    storage_node_location = list(set(node.active_dispatch_coefficients.index.get_level_values('supply_node')))
                    if len(storage_node_location)>1:
                        raise ValueError('StorageNode %s has technologies with two different supply node locations' %node.name)
                if storage_node_location[0] in self.electricity_nodes[zone]+[zone]:
                    capacity = node.stock.values.loc[:,year].to_frame().groupby(level=[GeoMapper.supply_primary_geography,'supply_technology']).sum()
                    efficiency = copy.deepcopy(node.active_dispatch_coefficients)
                    if 'demand_sector' not in capacity.index.names and zone == self.distribution_node_name:
                        capacity = pd.concat([capacity]*len(self.demand_sectors), keys=self.demand_sectors, names=['demand_sector']) / len(self.demand_sectors)
                        efficiency = pd.concat([efficiency]*len(self.demand_sectors), keys=self.demand_sectors, names=['demand_sector'])
                    if GeoMapper.dispatch_geography != GeoMapper.supply_primary_geography:
                        geography_map_key = node.geography_map_key if hasattr(node, 'geography_map_key') and node.geography_map_key is not None else GeoMapper.default_geography_map_key
                        map_df = GeoMapper.get_instance().map_df(GeoMapper.supply_primary_geography,GeoMapper.dispatch_geography,  normalize_as='total', map_key=geography_map_key, eliminate_zeros=False)
                        capacity = DfOper.mult([capacity, map_df],fill_value=0.0)
                        efficiency = DfOper.divi([util.remove_df_levels(DfOper.mult([efficiency, capacity]), GeoMapper.supply_primary_geography),util.remove_df_levels(capacity,GeoMapper.supply_primary_geography)]).fillna(0)
                        capacity = util.remove_df_levels(capacity, GeoMapper.supply_primary_geography)
                    # creates an empty database to fill with duration values, which are a technology parameter
                    duration = copy.deepcopy(capacity) * 0
                    duration = duration.sort_index()
                    for tech in node.technologies.values():
                        for geography in GeoMapper.supply_geographies:
                            tech_indexer = util.level_specific_indexer(duration,['supply_technology',GeoMapper.supply_primary_geography], [tech.name,geography])
                            year_indexer = util.level_specific_indexer(tech.duration.values,['year',GeoMapper.supply_primary_geography],[year,geography])
                            duration.loc[tech_indexer,:] = tech.duration.values.loc[year_indexer,:].values[0]
                    efficiency = util.remove_df_levels(efficiency,'supply_node')    
                    if zone == self.distribution_node_name:
                        indexer = util.level_specific_indexer(self.dispatch_feeder_allocation, 'year', year)
                        capacity = util.DfOper.mult([capacity, self.dispatch_feeder_allocation.loc[indexer, ]])
                        duration = DfOper.divi([util.remove_df_levels(DfOper.mult([duration, capacity]),'demand_sector'),util.remove_df_levels(capacity,'demand_sector')]).fillna(0)
                        efficiency = DfOper.divi([util.remove_df_levels(DfOper.mult([efficiency, capacity]),'demand_sector'),util.remove_df_levels(capacity,'demand_sector')]).fillna(1)
                        capacity = util.remove_df_levels(capacity,'demand_sector')
                        for geography in GeoMapper.dispatch_geographies:
                            for dispatch_feeder in self.dispatch_feeders:
                                for technology in node.technologies.keys():
                                    indexer = util.level_specific_indexer(efficiency, [GeoMapper.dispatch_geography, 'dispatch_feeder','supply_technology'],[geography,dispatch_feeder,technology])
                                    self.storage_efficiency_dict[geography][zone][dispatch_feeder][technology] = efficiency.loc[indexer,:].values[0][0]
                                    indexer = util.level_specific_indexer(capacity, [GeoMapper.dispatch_geography, 'dispatch_feeder','supply_technology'],[geography,dispatch_feeder,technology])
                                    self.storage_capacity_dict['power'][geography][zone][dispatch_feeder][technology] = capacity.loc[indexer,:].values[0][0]
                                    indexer = util.level_specific_indexer(duration, [GeoMapper.dispatch_geography, 'dispatch_feeder','supply_technology'],[geography,dispatch_feeder,technology])
                                    self.storage_capacity_dict['duration'][geography][zone][dispatch_feeder][technology] = duration.loc[indexer,:].values[0][0]
                    else:
                        for geography in GeoMapper.dispatch_geographies:
                            for technology in node.technologies.keys():
                                indexer = util.level_specific_indexer(capacity, [GeoMapper.dispatch_geography, 'supply_technology'],[geography,technology])
                                tech_capacity = self.ensure_frame(util.remove_df_levels(capacity.loc[indexer,:], 'demand_sector'))
                                indexer = util.level_specific_indexer(duration, [GeoMapper.dispatch_geography,'supply_technology'],[geography,technology])
                                tech_duration = self.ensure_frame(util.remove_df_levels(duration.loc[indexer,:], 'demand_sector'))
                                indexer = util.level_specific_indexer(efficiency, [GeoMapper.dispatch_geography, 'supply_technology'],[geography,technology])
                                tech_efficiency = self.ensure_frame(util.remove_df_levels(efficiency.loc[indexer,:], 'demand_sector'))
                                if tech_capacity.values[0][0] == 0:
                                    continue
                                else:
                                    self.storage_capacity_dict['power'][geography][zone]['bulk'][technology] = tech_capacity.values[0][0]
                                    self.storage_capacity_dict['duration'][geography][zone]['bulk'][technology] = tech_duration.values[0][0]
                                    self.storage_efficiency_dict[geography][zone]['bulk'][technology] = tech_efficiency.values[0][0]
    @staticmethod
    def ensure_frame(variable):
        if isinstance(variable,pd.DataFrame):
            return variable
        else:
            try:
                variable = variable.to_frame()
                return variable
            except:
                raise ValueError('variable not convertible to dataframe')

    def set_shapes(self,year):
       for zone in self.dispatch_zones:
           for node_name in self.electricity_load_nodes[zone]['non_flexible'] + self.electricity_gen_nodes[zone]['non_flexible']:
               self.nodes[node_name].active_shape = self.nodes[node_name].aggregate_electricity_shapes(year, util.remove_df_levels(util.df_slice(self.dispatch_feeder_allocation,year,'year'),year))

    def _helper_shaped_bulk_and_dist(self, year, energy_slice):
        node_names = list(set(energy_slice.index.get_level_values('supply_node')))
        if year in self.dispatch_write_years:
            # this keeps supply node as a level
            dfs = [util.DfOper.mult((energy_slice.xs(node_name, level='supply_node'), self.nodes[node_name].active_shape)) for node_name in node_names]
            df = pd.concat(dfs, keys=node_names, names=['supply_node'])
        else:
            # this removes supply node as a level and is faster
            df = util.DfOper.add([util.DfOper.mult((energy_slice.xs(node_name, level='supply_node'), self.nodes[node_name].active_shape)) for node_name in node_names], expandable=False, collapsible=False)

        if GeoMapper.supply_primary_geography != GeoMapper.dispatch_geography:
            # because energy_slice had both geographies, we have effectively done a geomap
            df = util.remove_df_levels(df, GeoMapper.supply_primary_geography)
        return df

    def shaped_dist(self, year, load_or_gen_df, generation):
        if load_or_gen_df is None or self.distribution_node_name not in load_or_gen_df.index.get_level_values('dispatch_zone'):
            return self.distribution_gen * 0

        dist_slice = load_or_gen_df.xs(self.distribution_node_name, level='dispatch_zone')
        df = self._helper_shaped_bulk_and_dist(year, dist_slice)

        if year in self.dispatch_write_years:
            df_output = df.copy()
            df_output = DfOper.mult([df_output, self.distribution_losses, self.transmission_losses])
            df_output =  self.outputs.clean_df(df_output)
            util.replace_index_name(df_output,'DISPATCH_OUTPUT','SUPPLY_NODE')
            df_output = df_output.reset_index(level=['DISPATCH_OUTPUT','DISPATCH_FEEDER'])
            df_output['NEW_DISPATCH_OUTPUT'] = df_output['DISPATCH_FEEDER'].astype(str) + " " + df_output['DISPATCH_OUTPUT'].astype(str)
            df_output = df_output.set_index('NEW_DISPATCH_OUTPUT',append=True)
            df_output = df_output[year].to_frame()
            util.replace_index_name(df_output,'DISPATCH_OUTPUT','NEW_DISPATCH_OUTPUT')
            df_output.columns = [cfg.calculation_energy_unit.upper()]
            if generation:
                df_output*=-1
            self.bulk_dispatch = pd.concat([self.bulk_dispatch, df_output.reorder_levels(self.bulk_dispatch.index.names)])
            # self.bulk_dispatch = util.DfOper.add([self.bulk_dispatch, df_output])
        df = util.remove_df_levels(df, 'supply_node') # only necessary when we origionally kept supply node as a level
        return df


    def shaped_bulk(self, year, load_or_gen_df, generation):
        if load_or_gen_df is not None and self.transmission_node_name in load_or_gen_df.index.get_level_values('dispatch_zone'):
            bulk_slice = util.remove_df_levels(load_or_gen_df.xs(self.transmission_node_name, level='dispatch_zone'), 'dispatch_feeder')
            node_names = list(set(bulk_slice.index.get_level_values('supply_node')))
            assert not any(['dispatch_feeder' in self.nodes[node_name].active_shape.index.names for node_name in node_names])
            df = self._helper_shaped_bulk_and_dist(year, bulk_slice)
            if year in self.dispatch_write_years:
                df_output = pd.concat([df],keys=[year],names=['year'])
                if generation:
                    df_output*=-1
                else:
                    df_output = DfOper.mult([df_output,self.transmission_losses])
                df_output =  self.outputs.clean_df(df_output)
                util.replace_index_name(df_output,'DISPATCH_OUTPUT','SUPPLY_NODE')
                df_output.columns = [cfg.calculation_energy_unit.upper()]
                df_output = util.reorder_b_to_match_a(df_output, self.bulk_dispatch)
                self.bulk_dispatch = pd.concat([self.bulk_dispatch, df_output.reorder_levels(self.bulk_dispatch.index.names)])
                # self.bulk_dispatch = util.DfOper.add([self.bulk_dispatch, df_output])
                df = util.remove_df_levels(df, 'supply_node') # only necessary when we origionally kept supply node as a level
            return df
        else:
            return self.bulk_gen * 0

    def set_initial_net_load_signals(self,year):
        final_demand = self.demand_object.aggregate_electricity_shapes(year)
        distribution_native_load = final_demand.xs(0, level='timeshift_type')
        if tuple(final_demand.index.get_level_values('timeshift_type').unique()) == (0,):
            self.distribution_flex_load = None
        elif tuple(final_demand.index.get_level_values('timeshift_type').unique()) == (0,'advanced','delayed','native'):
            self.distribution_flex_load = util.df_slice(final_demand, ['advanced','delayed','native'], 'timeshift_type', drop_level=False, reset_index=True)
        else:
            raise ValueError('Unrecognized timeshift types in the electricity shapes, found: {}'.format(tuple(final_demand.index.get_level_values('timeshift_type').unique())))
        if year in self.dispatch_write_years:
            self.output_final_demand_for_bulk_dispatch_outputs(distribution_native_load)
        self.distribution_gen = self.shaped_dist(year, self.non_flexible_gen, generation=True)
        self.distribution_load = util.DfOper.add([distribution_native_load, self.shaped_dist(year, self.non_flexible_load, generation=False)])
        self.rio_distribution_load[year] =copy.deepcopy(self.distribution_load)
        self.rio_flex_load[year] = copy.deepcopy(self.distribution_flex_load)
        self.bulk_gen = self.shaped_bulk(year, self.non_flexible_gen, generation=True)
        if cfg.getParamAsBoolean('rio_db_run', section='rio'):
            for blend_name in [x for x in self.blend_nodes if x not in cfg.rio_excluded_blends]:
                for node_name in self.nodes[blend_name].nodes:
                    self.non_flexible_load[self.non_flexible_load.index.get_level_values('supply_node')==node_name]=0
        self.bulk_load = self.shaped_bulk(year, self.non_flexible_load, generation=False)
        self.rio_bulk_load[year] = copy.deepcopy(self.bulk_load)
        self.update_net_load_signal()

    def output_final_demand_for_bulk_dispatch_outputs(self, distribution_native_load):
        df_output = DfOper.mult([distribution_native_load, self.distribution_losses,self.transmission_losses])
        df_output = self.outputs.clean_df(df_output)
        util.replace_index_name(df_output,'DISPATCH_OUTPUT','DISPATCH_FEEDER')
        df_output.columns = [cfg.calculation_energy_unit.upper()]
        self.bulk_dispatch = df_output

    def update_net_load_signal(self):
        self.dist_only_net_load =  DfOper.subt([self.distribution_load,self.distribution_gen])
        self.bulk_only_net_load = DfOper.subt([DfOper.mult([self.bulk_load,self.transmission_losses]),self.bulk_gen])
        self.bulk_net_load = DfOper.add([DfOper.mult([util.remove_df_levels(DfOper.mult([self.dist_only_net_load,self.distribution_losses]),'dispatch_feeder'),self.transmission_losses]),self.bulk_only_net_load])
        self.dist_net_load_no_feeders = DfOper.add([DfOper.divi([DfOper.divi([self.bulk_only_net_load,util.remove_df_levels(self.distribution_losses,'dispatch_feeder',agg_function='mean')]),self.transmission_losses]), util.remove_df_levels(self.dist_only_net_load,'dispatch_feeder')])

    def calculate_embodied_costs(self, year, loop):
        """Calculates the embodied costs for all supply nodes by multiplying each node's
        active_embodied_costs by the cost inverse. Result is stored in
        the Supply instance's 'cost_dict' attribute"
        Args:
            year (int) = year of analysis
            loop (int or str) = loop identifier
        """
        index = pd.MultiIndex.from_product([GeoMapper.supply_geographies, self.all_nodes], names=[GeoMapper.supply_primary_geography, 'supply_node'])
        for node in self.nodes.values():
            supply_indexer = util.level_specific_indexer(self.io_embodied_cost_df, 'supply_node', node.name)
            if hasattr(node,'calculate_levelized_costs'):
                node.calculate_levelized_costs(year,loop)
            elif hasattr(node,'calculate_costs'):
                node.calculate_costs(year,loop,self.transmission_node_name,self.dispatch.transmission.cost,self.dispatch.transmission.constraints)
            if hasattr(node, 'active_embodied_cost'):
                self.io_embodied_cost_df.loc[supply_indexer, year] = node.active_embodied_cost.values
        for sector in self.demand_sectors:
            inverse = self.inverse_dict['cost'][year][sector]
            indexer = util.level_specific_indexer(self.io_embodied_cost_df, 'demand_sector', sector)
            cost = np.column_stack(self.io_embodied_cost_df.loc[indexer,year].values).T
            self.cost_dict[year][sector] = pd.DataFrame(cost * inverse.values, index=index, columns=index).sort_index(axis=0).sort_index(axis=1)

    def calculate_embodied_emissions(self, year):
        """Calculates the embodied emissions for all supply nodes by multiplying each node's
        active_embodied_emissions by the emissions inverse. Result is stored in
        the Supply instance's 'emissions_dict' attribute"

        Args:
            year (int) = year of analysis
            loop (int or str) = loop identifier
        """
        self.calculate_emissions(year)
        row_index = pd.MultiIndex.from_product([GeoMapper.supply_geographies, self.all_nodes, self.ghgs], names=[GeoMapper.supply_primary_geography, 'supply_node', 'ghg'])
        col_index =  pd.MultiIndex.from_product([GeoMapper.supply_geographies, self.all_nodes], names=[GeoMapper.supply_primary_geography, 'supply_node'])
        for node in self.nodes.values():
            supply_indexer = util.level_specific_indexer(self.io_embodied_emissions_df, 'supply_node', node.name)
            if hasattr(node, 'active_embodied_emissions_rate'):
                self.io_embodied_emissions_df.loc[supply_indexer, year] = node.active_embodied_emissions_rate.values
        for sector in self.demand_sectors:    
            inverse = copy.deepcopy(self.inverse_dict['energy'][year][sector])
            keys = self.ghgs
            name = ['ghg']
            inverse = pd.concat([inverse]*len(keys), keys=keys, names=name)
            inverse = inverse.reorder_levels([GeoMapper.supply_primary_geography,'supply_node','ghg'])
            inverse.sort(axis=0,inplace=True)
            indexer = util.level_specific_indexer(self.io_embodied_emissions_df, 'demand_sector', sector)
            emissions = np.column_stack(self.io_embodied_emissions_df.loc[indexer,year].values).T
            self.emissions_dict[year][sector] = pd.DataFrame(emissions * inverse.values,index=row_index, columns=col_index).sort_index(axis=0).sort_index(axis=1)


    def map_embodied_to_demand(self, embodied_dict, link_dict):
        """Maps embodied emissions results for supply node to their associated final energy type and then
        to final energy demand.
        Args:
            embodied_dict (dict): dictionary of supply-side embodied result DataFrames (energy, emissions, or cost)
            link_dict (dict): dictionary of dataframes with structure with [geography, final_energy] multiIndex columns
            and [geography,supply_node] rows

        Returns:
            df (DataFrame)
            Dtype: Float
            Row Index: [geography, supply_node, demand_sector, ghgs (emissions results only), year]
            Cols: ['value']
        """
        sorted_map_dict_values = sorted(self.map_dict.values())
        remap_order = np.array([sorted_map_dict_values.index(self.map_dict[key]) for key in sorted(self.map_dict.keys())])
        remap_order = np.hstack([len(self.map_dict) * i + remap_order for i in range(len(GeoMapper.supply_geographies))])
        df_list = []
        for year in self.years_subset:
            sector_df_list = []
            keys = self.demand_sectors
            name = ['sector']
            idx = pd.IndexSlice
            for sector in self.demand_sectors:
                link_dict[year][sector].loc[:,:] = embodied_dict[year][sector].loc[:,idx[:, self.map_dict.values()]].values[:,remap_order]
                link_dict[year][sector] = link_dict[year][sector].stack([GeoMapper.supply_primary_geography,'final_energy']).to_frame()
                link_dict[year][sector] = link_dict[year][sector][link_dict[year][sector][0]!=0]
                levels_to_keep = [x for x in link_dict[year][sector].index.names if x in cfg.output_combined_levels]
                sector_df_list.append(link_dict[year][sector].groupby(level=levels_to_keep).sum())
            year_df = pd.concat(sector_df_list, keys=keys,names=name)
            df_list.append(year_df)
        self.sector_df_list  = sector_df_list
        self.df_list = df_list
        keys = self.years_subset
        name = ['year']
        df = pd.concat(df_list,keys=keys,names=name)
        df.columns = ['value']
        df = df.groupby(level=[x for x in df.index.names if x in cfg.output_combined_levels]).sum()
        return df


    def convert_io_matrix_dict_to_df(self, adict):
        """Converts an io dictionary to a dataframe
        Args:
            adict = dictionary containing sliced datafrmes

        Returns:
            df (DataFrame)
            Dtype: Float
            Row Index: [geography, supply_node_input, supply_node_output, year]
            Cols: ['value']
        """
        df_list = []
        for year in self.years:
            sector_df_list = []
            keys = self.demand_sectors
            name = ['sector']
            for sector in self.demand_sectors:
                df = adict[year][sector]
                levels_to_keep = [x for x in df.index.names if x in cfg.output_combined_levels]
                df = df.groupby(level=levels_to_keep).sum()
                df = df.stack([GeoMapper.supply_primary_geography,'supply_node']).to_frame()
                df.index.names = [GeoMapper.supply_primary_geography+'_input','supply_node_input',GeoMapper.supply_primary_geography,'supply_node']
                sector_df_list.append(df)
            year_df = pd.concat(sector_df_list, keys=keys,names=name)
            df_list.append(year_df)
        self.sector_df_list  = sector_df_list
        self.df_list = df_list
        keys = self.years
        name = ['year']
        df = pd.concat(df_list,keys=keys,names=name)
        df.columns = ['value']
        return df


#     def map_embodied(self, embodied_dict, link_dict):
#         """Maps embodied results for supply node to other supply nodes
#         Args:
#             embodied_dict (dict): dictionary of supply-side embodied result DataFrames (energy, emissions, or cost)
#             link_dict (dict): dictionary of dataframes with structure with [geography, final_energy] multiIndex columns
#             and [geography,supply_node] rows
#
#         Returns:
#             df (DataFrame)
#             Dtype: Float
#             Row Index: [geography, supply_node, demand_sector, ghgs (emissions results only), year]
#             Cols: ['value']
#         """
#         df_list = []
#         for year in self.years:
#             sector_df_list = []
#             keys = self.demand_sectors
#             name = ['sector']
#             idx = pd.IndexSlice
#             for sector in self.demand_sectors:
#                 remap_order = np.argsort([self.map_dict[key] for key in sorted(self.map_dict.keys())])
#                 remap_order = np.hstack([len(self.map_dict)*i+remap_order for i in range(len(GeoMapper.supply_geographies))])
#                 link_dict[year][sector].loc[:,:] = embodied_dict[year][sector].loc[:,idx[:, self.map_dict.values()]].values[:,remap_order]
#                 link_dict[year][sector]= link_dict[year][sector].stack([GeoMapper.supply_primary_geography,'final_energy']).to_frame()
# #                levels = [x for x in ['supply_node',GeoMapper.supply_primary_geography +'_supply', 'ghg',GeoMapper.supply_primary_geography,'final_energy'] if x in link_dict[year][sector].index.names]
#                 link_dict[year][sector] = link_dict[year][sector][link_dict[year][sector][0]!=0]
#                 levels_to_keep = [x for x in link_dict[year][sector].index.names if x in cfg.output_combined_levels]
#                 sector_df_list.append(link_dict[year][sector].groupby(level=levels_to_keep).sum())
#             year_df = pd.concat(sector_df_list, keys=keys,names=name)
#             df_list.append(year_df)
#         self.sector_df_list  = sector_df_list
#         self.df_list = df_list
#         keys = self.years
#         name = ['year']
#         df = pd.concat(df_list,keys=keys,names=name)
#         df.columns = ['value']
# #       levels = [x for x in ['supply_node',GeoMapper.supply_primary_geography +'_supply', 'ghg',GeoMapper.supply_primary_geography,'final_energy'] if x in df.index.names]
#         return df


    def map_embodied_to_export(self, embodied_dict):
        """Maps embodied emissions results for supply node to their associated final energy type and then
        to final energy demand.
        Args:
            embodied_dict (dict): dictionary of supply-side embodied result DataFrames (energy, emissions, or cost)
            link_dict (dict): dictionary of dataframes with structure with [geography, final_energy] multiIndex columns
            and [geography,supply_node] rows

        Returns:
            df (DataFrame)
            Dtype: Float
            Row Index: [geography, supply_node, demand_sector, ghgs (emissions results only), year]
            Cols: ['value']
        """
        export_df = self.io_export_df.stack().to_frame()
        export_df = export_df.groupby(level='supply_node').filter(lambda x: x.sum()!=0)
        util.replace_index_name(export_df, 'year')
        util.replace_column(export_df, 'value')
        supply_nodes = list(set(export_df.index.get_level_values('supply_node')))
        df_list = []
        idx = pd.IndexSlice
        for year in self.years_subset:
            sector_df_list = []
            keys = self.demand_sectors
            name = ['sector']
            for sector in self.demand_sectors:   
               df = copy.deepcopy(embodied_dict[year][sector])
               df.columns = copy.deepcopy(df.columns)
               util.replace_column_name(df, 'supply_node_export','supply_node')
               df = df.loc[:,idx[:,supply_nodes]]
               util.replace_index_name(df, GeoMapper.supply_primary_geography + "_supply", GeoMapper.supply_primary_geography)
               stack_levels = [GeoMapper.supply_primary_geography, "supply_node_export"]
               df = df.stack(stack_levels).to_frame()
               levels_to_keep = [x for x in df.index.names if x in cfg.output_combined_levels+stack_levels]
               df = df.groupby(level=list(set(levels_to_keep+ ['supply_node']))).sum()
               df = df.groupby(level='supply_node').filter(lambda x: x.sum() != 0)
               sector_df_list.append(df)
            year_df = pd.concat(sector_df_list, keys=keys,names=name)
            df_list.append(year_df)
        keys = self.years_subset
        name = ['year']
        df = pd.concat(df_list,keys=keys,names=name)
        df.columns = ['value']
        return df

    def calculate_export_result(self, export_result_name, io_dict):
        export_map_df = self.map_embodied_to_export(io_dict)
        export_df = self.io_export_df.stack().to_frame()
        export_df = export_df.groupby(level=['supply_node']).filter(lambda x: x.sum()!=0)
        if GeoMapper.supply_primary_geography+"_supply" in cfg.output_combined_levels:
            export_map_df = export_map_df.groupby(level=['supply_node',GeoMapper.supply_primary_geography+"_supply"]).filter(lambda x: x.sum()>0)
        else:
            export_map_df = export_map_df.groupby(level=['supply_node']).filter(lambda x: x.sum()!=0)
        if export_map_df.empty is False and export_df.empty is False:
            util.replace_index_name(export_df, 'year')
            util.replace_index_name(export_df, 'sector', 'demand_sector')
            util.replace_index_name(export_df,'supply_node_export','supply_node')
            util.replace_column(export_df, 'value')
            geo_df_list = []
            for geography in GeoMapper.supply_geographies:
                export_map_df_indexer = util.level_specific_indexer(export_map_df,[GeoMapper.supply_primary_geography],[geography])
                export_df_indexer = util.level_specific_indexer(export_df,[GeoMapper.supply_primary_geography],[geography])
                df = util.DfOper.mult([export_df.loc[export_df_indexer,:], export_map_df.loc[export_map_df_indexer,:]])
                geo_df_list.append(df)
            export_result = pd.concat(geo_df_list)
        else:
            export_result = None
        setattr(self, export_result_name, export_result)



##    @timecall(immediate=True)
    def adjust_for_not_incremental(self,io):
        """Adjusts for import nodes. Their io column must be zeroed out so that we don't double count upstream values.

        Args:
            io (DataFrame) = DataFrame to be adjusted
            node_class (Class) = Supply node attribute class (i.e. cost) to use to determine whether upstream values are zeroed out
        Returns:
            io_adjusted (DataFrame) = adjusted DataFrame
        """
        io_adjusted = copy.deepcopy(io)
        for node in self.nodes.values():
            if isinstance(node, ImportNode):
               col_indexer = util.level_specific_indexer(io_adjusted,'supply_node',node.name, axis=1)
               io_adjusted.loc[:,col_indexer] = 0
        return io_adjusted

    def rio_adjust(self,io):
        """Adjusts for import nodes. Their io column must be zeroed out so that we don't double count upstream values.

        Args:
            io (DataFrame) = DataFrame to be adjusted
            node_class (Class) = Supply node attribute class (i.e. cost) to use to determine whether upstream values are zeroed out
        Returns:
            io_adjusted (DataFrame) = adjusted DataFrame
        """
        io_adjusted = copy.deepcopy(io)
        for node in self.blend_nodes:
            col_indexer = util.level_specific_indexer(io_adjusted,'supply_node',node, axis=1)
            io_adjusted.loc[:,col_indexer] = 0
        return io_adjusted
                        
    def calculate_coefficients(self, year, loop):
        """Loops through all supply nodes and calculates active coefficients
        Args:
            year (int) = year of analysis
            loop (int or str) = loop identifier
        """
        for node_name in self.blend_nodes:
            node = self.nodes[node_name]
            if len(node.nodes)>1:
                if cfg.rio_supply_run and node_name==self.bulk_electricity_node_name or node_name in cfg.rio_no_negative_blends:
                    node.set_to_min(year)
                else:
                    node.update_residual(year)
        for node in self.nodes.values():
            if node.name!=self.thermal_dispatch_node_name:
                node.calculate_active_coefficients(year, loop)
            elif node.name == self.thermal_dispatch_node_name and cfg.rio_supply_run:
                node.calculate_active_coefficients(year, loop)
            elif year == cfg.getParamAsInt('current_year') and node.name == self.thermal_dispatch_node_name and not cfg.rio_supply_run:
                #thermal dispatch node is updated through the dispatch. In the first year we assume equal shares
                #TODO make capacity weighted for better approximation
                node.calculate_active_coefficients(year, loop)
                node.active_coefficients_total[node.active_coefficients_total>0] = 1E-10
                node.active_coefficients_total = node.active_coefficients_total.groupby(level=['demand_sector',GeoMapper.supply_primary_geography]).transform(lambda x: x/x.sum())
                node.active_coefficients_total.replace(to_replace=np.nan,value=0,inplace=True)

    def set_pass_through_dicts(self, year):
        """Sets pass-through dictionaries that control the loop when calculating
        physical emissions. If a node has an efficiency type that implies that energy
        is passed through it (i.e. gas distribution system) then the physical emissions values
        of the fuel are also passed through. All inputs must be calculated before loop continues downstream
        of any supply node.

        Args:
            year (int) = year of analysis
        """
        if year == min(self.years):
            for node in self.nodes.values():
                node.set_pass_through_dict(self.nodes)
            for node in self.nodes.values():
                if (hasattr(node,'pass_through_dict')) or hasattr(node,'active_physical_emissions_rate'):
                    pass
                elif hasattr(node,'name'):
                    for dict_node in self.nodes.values():
                        if hasattr(dict_node, 'pass_through_dict'):
                            if node.name in dict_node.pass_through_dict.keys():
                                del dict_node.pass_through_dict[node.name]
            for node in self.nodes.values():
                if hasattr(node,'pass_through_dict') and node.pass_through_dict == {}:
                    for dict_node in self.nodes.values():
                        if hasattr(dict_node, 'pass_through_dict'):
                            if node.name in dict_node.pass_through_dict.keys():
                                del dict_node.pass_through_dict[node.name]
        else:
            for node in self.nodes.values():
                    if hasattr(node,'pass_through_dict'):
                        for key in node.pass_through_dict.keys():
                            node.pass_through_dict[key] = False

    def calculate_stocks(self,year,loop):
        """Loops through all supply nodes that have stocks and updates those stocks

        Args:
            year (int) = year of analysis
            loop (int or str) = loop identifier
        """
        for node in self.nodes.values():
            if hasattr(node, 'stock'):
                node.update_stock(year,loop)

    def reconcile_trades(self,year,loop):
        """Reconciles internal trades. These are instances where the geographic location of supply in a node is divorced from
        the geographic location of the demand. To achieve this result, we calculate the expected location of supply and then pass
        that information to blend or import node trade adjustment dataframes so that the IO demands supply with that geographic distribution

        Args:
            year (int) = year of analysis
            loop (int or str) = loop identifier
        """
        if len(GeoMapper.supply_geographies) > 1:
            for node in self.nodes.values():
                if node.name not in self.blend_nodes:
                    #Checks whether a node has information (stocks or potential) that means that demand is not a good proxy for location of supply
                    node.calculate_internal_trades(year, loop)
            for node in self.nodes.values():
                #loops through all nodes checking for excess supply from nodes that are not curtailable, flexible, or exportable
                trade_sub = node.name
                if node.name not in self.blend_nodes:
                    #Checks whether a node has information that means that demand is not a good proxy for location of supply
                    if hasattr(node,'active_internal_trade_df') and node.internal_trades == "stop and feed":
                        #enters a loop to feed that constraint forward in the supply node until it can be reconciled at a blend node or exported
                        self.feed_internal_trades(year, trade_sub, node.active_internal_trade_df)



    def reconcile_constraints(self,year,loop):
        """Reconciles instances where IO demands exceed a node's potentia.  To achieve this result, we calculate the expected location of supply and then pass
        that information to blend or import node trade adjustment dataframes so that the IO demands supply with that geographic distribution

        Args:
            year (int) = year of analysis
            loop (int or str) = loop identifier
        """

        for node in self.nodes.values():
            #blend nodes cannot be potential constrained
            if node.name not in self.blend_nodes:
                #checks the node for an adjustment factor due to excess throughput requested from a constraiend node
                #Ex. if biomass throughput exceeeds biomass potential by 2x, the adjustment factor passed would be .5
                node.calculate_potential_constraints(year)
                #Checks whether a constraint was violated
                if node.constraint_violation:
                    #enters a loop to feed that constraint forward in the supply node
                    self.feed_constraints(year, node.name, node.active_constraint_df)




    def reconcile_oversupply(self,year,loop):
        """Reconciles instances where IO demands less than a node's expected level of supply based
        on its existing stock.  To achieve this result, we calculate the expected location of supply and then pass
        that information to blend or import node trade adjustment dataframes so that the IO demands supply with that geographic distribution

        Args:
            year (int) = year of analysis
            loop (int or str) = loop identifier
        """

        for node in self.nodes.values():
            #loops through all nodes checking for excess supply from nodes that are not curtailable, flexible, or exportable
            if cfg.rio_supply_run and node.name in cfg.rio_excluded_nodes:
                oversupply_factor = node.calculate_oversupply(year, loop) if hasattr(node,
                                                                 'calculate_oversupply') else None
            elif not cfg.rio_supply_run:
                oversupply_factor = node.calculate_oversupply(year,loop) if hasattr(node,'calculate_oversupply') else None
            else:
                oversupply_factor = None
            if oversupply_factor is not None:
               if node.is_exportable:
                   #if the node is exportable, excess supply is added to the node's exports
                   excess_supply = DfOper.subt([DfOper.mult([node.active_supply, oversupply_factor]), node.active_supply])
                   node.export.active_values = DfOper.add([node.export.active_values, excess_supply])
               elif node.name in self.nodes[self.thermal_dispatch_node_name].nodes:
                   #excess supply is not possible for thermally dispatched nodes
                   pass
               elif node.name in self.blend_nodes:
                   pass
               elif node.is_curtailable:
                   #if the node's production is curtailable, then the energy production is adjusted down in the node
                    node.adjust_energy(oversupply_factor,year)
               else:
                   #otherwise, the model enters a loop to feed that constraint forward in the supply node until it can be reconciled at a blend node or exported
                   self.feed_oversupply(year, node.name, oversupply_factor)

    def calculate_emissions(self,year):
        """Calculates physical and embodied emissions for each supply node
        Args:
            year (int) = year of analysis
        """
        self.calculate_input_emissions_rates(year)
        self.calculate_emissions_coefficients(year)
        for node in self.nodes.values():
           node.calculate_emissions(year)
           node.calculate_embodied_emissions_rate(year)

    def calculate_input_emissions_rates(self,year):
        """Calculates physical emissions coefficients for all nodes in order to calculate the actual
        physical emissions attributable to each supply node and demand subsector.
        Args:
            year (int) = year of analysis
            loop (int or str) = loop identifier
        """
        for node in self.nodes.values():
            node.update_pass_through_df_dict(year)
            node.calculate_input_emissions_rates(year, self.ghgs)

    def calculate_emissions_coefficients(self,year):
        """Calculates and propagates physical emissions coefficients to downstream nodes for internal emissions
        calculations
        Args:
            year (int) = year of analysis
            loop (int or str) = loop identifier
        """
        for node in self.nodes.values():
            if hasattr(node,'calculate_co2_capture_rate'):
                node.calculate_co2_capture_rate(year)
        for node in self.nodes.values():
            if node.active_emissions_coefficients is not None:
                node.active_physical_emissions_coefficients = node.active_emissions_coefficients * 0
        self.set_pass_through_dicts(year)
        for node in self.nodes.values():
            if hasattr(node,'active_physical_emissions_rate'):
                self.feed_physical_emissions(year, node.name, node.active_physical_emissions_rate)


    def feed_constraints(self, year, constrained_node, constraint_adjustment):
        """Propagates constraint reconciliation adjustment factors to all dependent blend nodes
        Args:
            year (int) = year of analysis
            constrained_node (int) = integer id key of supply node
            contraint_adjustment (df) = dataframe of constraint adjustment factors.
        Ex. If demanded biomass is 2 EJ and available biomass is 1 EJ, constraint adjustment factor would equal .5
        """
        #loops all potential output nodes
        for output_node in self.nodes.values():
          if hasattr(output_node, 'active_coefficients_total') and getattr(output_node, 'active_coefficients_total') is not None:
            #if the constrained sub is an input to this output node
            if constrained_node in set(output_node.active_coefficients_total.index.get_level_values('supply_node')):
                  #if this output node is a blend node, the reconciliation happens here.
                  if output_node.name in self.blend_nodes:
                     logging.info("      constrained node %s being reconciled in blend node %s" %(self.nodes[constrained_node].name, output_node.name))
                     indexer = util.level_specific_indexer(output_node.values,'supply_node', constrained_node)
                     output_node.values.loc[indexer,year] =  DfOper.mult([output_node.values.loc[indexer, year].to_frame(),constraint_adjustment]).values
                     #flag for the blend node that it has been reconciled and needs to recalculate residual
                     output_node.reconciled = True
                     #flag that anything in the supply loop has been reconciled, and so the loop needs to be resolved
                     self.reconciled = True
                  else:
                     #if the output node has the constrained sub as an input, and it is not a blend node, it becomes the constrained sub
                      #in the loop in order to feed the adjustment factor forward to dependent nodes until it terminates at a blend node
                     self.feed_constraints(year, constrained_node=output_node.name, constraint_adjustment=constraint_adjustment)
                     #TODO add logic if it reaches the end of the supply node and has never been reconicled at a blend node

    def feed_internal_trades(self, year, internal_trade_node, internal_trade_adjustment):
        """Propagates internal trading adjustments to downstream nodes
        Args:
            year (int) = year of analysis
            internal_trade_node (int) = integer id key of supply node that has internal trade adjustments
            internal_trade_adjustment (df) = dataframe of internal trade adjustments to propagate forward

        Ex. If demanded biomass is 3 EJ in geography A and 1 EJ in geography B and the supply of biomass is 1 EJ in geography A and 1 EJ in geography B,
        the internal trade adjustment is 2/3 for geography A (ratio of supply (.5) divided by ratio of demand (.75)) and 2 for geography B (.5/.25).

        """

        #loops all potential output nodes
        for output_node in self.nodes.values():
            if hasattr(output_node, 'nodes'):
              if internal_trade_node in output_node.nodes:
                  #if this output node is a blend node, or an import node, or the node has its own internal trades that are not fed forward (i.e. are on the primary geography) the reconciliation happens here.
                  if output_node.name in self.blend_nodes and output_node.tradable_geography or isinstance(output_node,ImportNode) or output_node.internal_trades == 'stop':
                     indexer = util.level_specific_indexer(output_node.active_trade_adjustment_df,'supply_node', internal_trade_node)
                     output_node.active_trade_adjustment_df.loc[indexer, :]  =  internal_trade_adjustment.values
                     self.reconciled = True
                     output_node.reconciled = True
                  elif output_node.internal_trades == 'stop and feed':
                     #if the output_node feeds forward its own trades, it becomes the trade node and recursively calls this function
                     indexer = util.level_specific_indexer(output_node.active_coefficients_total,'supply_node', internal_trade_node)
                     output_node.active_trade_adjustment_df.loc[indexer, :]  = internal_trade_adjustment.values
                     output_node.reconciled = True
                     self.reconciled = True
                     self.feed_internal_trades(year, internal_trade_node=output_node.name, internal_trade_adjustment=output_node.active_internal_trade_df)
                  elif output_node.internal_trades == 'feed':
                     #if the output node is set to feed the trades forward, it becomes the trade node while using the original trade node's adjustment factors in order to perpetuate the downstream impacts
                     self.feed_internal_trades(year, internal_trade_node=output_node.name, internal_trade_adjustment=internal_trade_adjustment)

    def feed_oversupply(self, year, oversupply_node, oversupply_factor):
        """Propagates oversupply adjustments to downstream nodes
        Args:
            year (int) = year of analysis
            oversupply_node (int) = integer id key of supply node that has the capacity to produce more throughput than demanded
            oversupply_factor (df) = dataframe of oversupply adjustments to propagate forward

        Ex. If demand form wind energy is 1 EJ and the existing stock has the ability to produce 2 EJ, if the node is not flagged as curtailable or exportable,
        the oversupply is propogated to downstream nodes until it reaches a Blend node or a node that is curtailable or exportable. If a node is curtailable, excess supply is ignored
        and the capacity is unutilized. If a node is exportable, excess supply results in exports to demand outside the model. If it reaches a Blend node, blend coefficient values are adjusted
        and reconciled so that the excess supply is then demanded in the next loop in order to resolve the conflict.
        """

        for output_node in self.nodes.values():
            if hasattr(output_node,'nodes'):
                if oversupply_node in output_node.nodes:
                    if output_node.name in self.blend_nodes:
                        # if the output node is a blend node, this is where oversupply is reconciled
                        # print oversupply_node, output_node.name, oversupply_factor
                        indexer = util.level_specific_indexer(output_node.values,'supply_node', oversupply_node)
                        output_node.values.loc[indexer, year] = DfOper.mult([output_node.values.loc[indexer, year].to_frame(),oversupply_factor]).values
                        output_node.reconciled = True
                        self.reconciled = True
                    else:
                        if output_node.is_curtailable or  output_node.name in self.thermal_nodes:
                            #if the output node is curtailable, then the excess supply feed-loop ends and the excess is curtailed within this node. If the node is flexible, excess supply
                            #will be reconciled in the dispatch loop
                            pass
                        elif output_node.is_exportable:
                            #if the output node is exportable, then excess supply is added to the export demand in this node
                            excess_supply = DfOper.subt([DfOper.mult([output_node.active_supply, oversupply_factor]), output_node.active_supply])
                            output_node.export.active_values = DfOper.add([output_node.export.active_values, excess_supply])
                        else:
                            #otherwise, continue the feed-loop until the excess supply can be reconciled
                            self.feed_oversupply(year, oversupply_node=output_node.name, oversupply_factor=oversupply_factor)



    def update_io_df(self,year,loop):
        """Updates the io dictionary with the active coefficients of all nodes
        Args:
            year (int) = year of analysis
        """
        for geography in GeoMapper.supply_geographies:
            #fix for zero energy demand
            if util.df_slice(self.io_total_active_demand_df,geography,GeoMapper.supply_primary_geography).sum().sum()==0:
                for col_node in self.nodes.values():
                    if col_node.supply_type == 'Blend':
                        if col_node.active_coefficients_total is None:
                            continue
                        else:
                            col_indexer = util.level_specific_indexer(col_node.active_coefficients_total,GeoMapper.supply_primary_geography,geography,axis=1)
                            normalized = col_node.active_coefficients_total.loc[:,col_indexer].groupby(level=['demand_sector']).transform(lambda x: x/x.sum())
                            normalized = normalized.replace([np.nan,np.inf],1E-10)
                            col_node.active_coefficients_total.loc[:,col_indexer] = normalized

        for col_node in self.nodes.values():
            if loop == 1 and col_node.name not in self.blend_nodes:
                continue
            elif col_node.active_coefficients_total is None:
               continue
            else:
               for sector in self.demand_sectors:
                    levels = ['supply_node' ]
                    col_indexer = util.level_specific_indexer(self.io_dict[year][sector], levels=levels, elements=[col_node.name])
                    row_nodes = col_node.active_coefficients_total.index.levels[util.position_in_index(col_node.active_coefficients_total,'supply_node')]
                    row_nodes = [x for x in row_nodes if x in self.all_nodes]
                    row_indexer = util.level_specific_indexer(self.io_dict[year][sector], levels=levels, elements=[row_nodes])
                    levels = ['demand_sector','supply_node']
                    active_row_indexer =  util.level_specific_indexer(col_node.active_coefficients_total, levels=levels, elements=[sector,row_nodes])
                    active_col_indexer = util.level_specific_indexer(col_node.active_coefficients_total, levels=['demand_sector'], elements=[sector], axis=1)
                    try:
                        self.io_dict[year][sector].loc[row_indexer, col_indexer] = col_node.active_coefficients_total.loc[active_row_indexer,active_col_indexer].values
                    except:
                        pdb.set_trace()
                    if col_node.overflow_node:
                        self.io_dict[year][sector].loc[row_indexer, col_indexer]=0


    def feed_physical_emissions(self, year, emissions_node, active_physical_emissions_rate):
        """Propagates physical emissions rates of energy products to downstream nodes in order to calculate emissions in each node
        Args:
            year (int) = year of analysis

            emissions_node (int) = integer id key of supply node that a physical emissions rate (ex. oil) or a node that is conveying a product
            with a physical emissions rate (i.e. oil pipeline)
            active_physical_emissions_rate (df) = dataframe of a node's physical emissions rate

        Ex. Node A is natural gas with a physical emissions rate of 53.06 kG CO2/MMBtu. Node B is the natural gas pipeline that delivers
        natural gas to Node C, which is combustion gas turbines, which consumes the natural gas. The input emissions rate of 53.06 has to pass through
        Node B to Node C in order to calculate the combustion emissions of the gas turbines.
        """
        #loops all potential output node
        for output_node in self.nodes.values():
          #check whether the node has active coefficients (i.e. complete data)
          if hasattr(output_node, 'active_coefficients') and getattr(output_node, 'active_coefficients') is not None:
              #check whether the emissions node is in the coefficient of the output node
              if emissions_node in set(output_node.active_emissions_coefficients.index.get_level_values('supply_node')):
                  #if it is, set the emissions coefficient values based on the physical emissions rate of the emissions node
                  indexer = util.level_specific_indexer(output_node.active_emissions_coefficients,['supply_node'], [emissions_node])
                  for efficiency_type in set(output_node.active_emissions_coefficients.loc[indexer,:].index.get_level_values('efficiency_type')):
                      emissions_indexer = util.level_specific_indexer(output_node.active_emissions_coefficients,['efficiency_type','supply_node'], [efficiency_type,emissions_node])
                      output_node.active_physical_emissions_coefficients.loc[emissions_indexer,:] += output_node.active_emissions_coefficients.loc[emissions_indexer,:].values * active_physical_emissions_rate.values
                  if hasattr(output_node, 'pass_through_dict') and emissions_node in output_node.pass_through_dict.keys():
                      #checks whether the node has a pass_through_dictionary (i.e. has an efficiency of type 2 in its coefficients)
                      #if so, the value of the pass_through_dict is True for the emissions node. This means that the emissions rate for
                      #this pass_through has been solved. They must all be solved before the emissions rate of the output node can be fed to
                      output_node.pass_through_dict[emissions_node] = True
                      # feeds passed-through emissions rates until it reaches a node where it is completely consumed
                      if (isinstance(output_node,ImportNode) or isinstance(output_node,BlendNode)) and output_node.emissions._has_data is True:
                         #if the node is an import node, and the emissions intensity is not incremental, the loop stops because the input emissions intensity
                         #overrides the passed through emissions intensity
                          pass
                      else:
                         indexer = util.level_specific_indexer(output_node.active_emissions_coefficients,['supply_node','efficiency_type'], [emissions_node, 'not consumed'])
                         additional_emissions_rate = output_node.active_emissions_coefficients.loc[indexer,:].values * active_physical_emissions_rate.values
                         output_node.active_pass_through_df += additional_emissions_rate
#                         output_node.active_pass_through_df.columns = output_node.active_pass_through_df.columns.droplevel(-1)
                         if all(output_node.pass_through_dict.values()):
                             emissions_rate = output_node.active_pass_through_df.groupby(level=['ghg'],axis=0).sum()
                             emissions_rate= emissions_rate.stack([GeoMapper.supply_primary_geography, 'demand_sector']).to_frame()
                             emissions_rate = emissions_rate.reorder_levels([GeoMapper.supply_primary_geography, 'demand_sector', 'ghg'])
                             emissions_rate.sort(inplace=True, axis=0)
                             keys = [self.demand_sectors,GeoMapper.supply_geographies]
                             names = ['demand_sector', GeoMapper.supply_primary_geography]
                             for key, name in zip(keys, names):
                                 emissions_rate = pd.concat([emissions_rate]*len(key),axis=1,keys=key,names=[name])
                             emissions_rate.sort(inplace=True, axis=0)
                             emissions_rate.columns = emissions_rate.columns.droplevel(-1)
                             self.feed_physical_emissions(year,output_node.name,emissions_rate)


    def initialize_year(self,year,loop):
        """Updates the dataframes of supply nodes so that the 'active' versions of dataframes reference the appropriate year
       Args:
           year (int) = year of analysis
           loop (int or str) = loop identifier
        """
        for node in self.nodes.values():
            node.reconciled = False
            if hasattr(node,'active_supply') and node.active_supply is not None:
                node.active_supply.columns = [year]
            if hasattr(node, 'active_trade_adjustment_df'):
                previous_year =  max(min(self.years), year-1)
                node.trade_adjustment_dict[previous_year] = copy.deepcopy(node.active_trade_adjustment_df)
        self.map_export_to_io(year,loop)
        self.calculate_demand(year,loop)




    def calculate_initial_demand(self):
        """Calculates the demands on the supply-side from final energy demand
        from the demand-side calculation and Export values. Export values can be updated
        during reconciliation process, so initial demand does not necessarily equal the demands on the energy
        system after the supply -side has been solved.
        """
        #year is the first year and loop is the initial loop
        year = min(self.years)
        loop = 'initial'
        self.add_initial_demand_dfs(year)
        self.add_io_df(['io_demand_df', 'io_export_df', 'io_supply_df','io_embodied_cost_df'])
        self.add_io_embodied_emissions_df()
        self.map_demand_to_io()
        self.io_active_supply_df = copy.deepcopy(self.empty_output_df)
        self.map_export_to_io(year, loop)


        self.io_total_active_demand_df = DfOper.add([self.io_demand_df.loc[:,year].to_frame(),self.io_export_df.loc[:,year].to_frame()])


    def calculate_demand(self,year,loop):
        self.map_export_to_io(year, loop)
        self.io_total_active_demand_df = util.DfOper.add([self.io_demand_df.loc[:,year].to_frame(),self.io_export_df.loc[:,year].to_frame()])



    def update_demand(self, year, loop):
        self.map_export_to_io(year, loop)
        self.io_total_active_demand_df = DfOper.add([self.io_demand_df.loc[:,year].to_frame(),self.io_export_df.loc[:,year].to_frame()])



    def calculate_io(self, year, loop):
        index = pd.MultiIndex.from_product([GeoMapper.supply_geographies, self.all_nodes
                                                                ], names=[GeoMapper.supply_primary_geography,'supply_node'])
        for sector in self.demand_sectors:
            indexer = util.level_specific_indexer(self.io_total_active_demand_df,'demand_sector', sector)
            self.active_io = self.io_dict[year][sector]
            active_cost_io = self.adjust_for_not_incremental(self.active_io)
            self.active_demand = self.io_total_active_demand_df.loc[indexer,:]
            temp = solve_IO(self.active_io.values, self.active_demand.values)
            temp[np.nonzero(self.active_io.values.sum(axis=1) + self.active_demand.values.flatten()==0)[0]] = 0
            self.io_supply_df.loc[indexer,year] = temp
            temp = solve_IO(self.active_io.values)
            temp[np.nonzero(self.active_io.values.sum(axis=1) + self.active_demand.values.flatten()==0)[0]] = 0
            self.inverse_dict['energy'][year][sector] = pd.DataFrame(temp, index=index, columns=index).sort_index(axis=0).sort_index(axis=1)
            temp = solve_IO(active_cost_io.values)
            temp[np.nonzero(active_cost_io.values.sum(axis=1) + self.active_demand.values.flatten()==0)[0]] = 0
            self.inverse_dict['cost'][year][sector] = pd.DataFrame(temp, index=index, columns=index).sort_index(axis=0).sort_index(axis=1)
        for node in self.nodes.values():
            indexer = util.level_specific_indexer(self.io_supply_df,levels=['supply_node'], elements = [node.name])
            node.active_supply = self.io_supply_df.loc[indexer,year].groupby(level=[GeoMapper.supply_primary_geography, 'demand_sector']).sum().to_frame()

    def calculate_rio_blend_demand(self):
        self.io_rio_supply_df = copy.deepcopy(self.io_supply_df)
        for year in self.dispatch_years:
        #for year in [2050]:
            logging.info("calculating rio blend demand in year %s" %year)
            total_demand = self.io_demand_df.loc[:,year].to_frame()
            for sector in self.demand_sectors:
                indexer = util.level_specific_indexer(self.io_total_active_demand_df,'demand_sector', sector)
                rio_io = self.io_dict[year][sector]
                rio_io = self.rio_adjust(rio_io)
                active_demand = total_demand.loc[indexer,:]
                temp = solve_IO(rio_io.values, active_demand.values)
                temp[np.nonzero(rio_io.values.sum(axis=1) + active_demand.values.flatten()==0)[0]] = 0
                self.io_rio_supply_df.loc[indexer,year] = temp
        self.io_rio_supply_df = util.remove_df_levels(self.io_rio_supply_df,'demand_sector')

    
    def add_initial_demand_dfs(self, year):


        for node in self.nodes.values():
            node.internal_demand = copy.deepcopy(self.empty_output_df)
            node.export_demand = copy.deepcopy(self.empty_output_df)
            node.internal_demand = copy.deepcopy(self.empty_output_df)


    def pass_initial_demand_to_nodes(self, year):
        for node in self.nodes.values():
            indexer = util.level_specific_indexer(self.io_total_active_demand_df,levels=['supply_node'], elements = [node.name])
            node.active_demand = self.io_total_active_demand_df.loc[indexer,:]

    def add_empty_output_df(self):
        """adds an empty df to node instances"""
        index =  pd.MultiIndex.from_product([GeoMapper.geography_to_gau[GeoMapper.supply_primary_geography],
                                                            self.demand_sectors], names=[GeoMapper.supply_primary_geography, 'demand_sector'])
        self.empty_output_df = util.empty_df(index = index, columns = self.years,fill_value = 1E-25)

    def add_io_df(self,attribute_names):
        #TODO only need to run years with a complete demand data set. Check demand dataframe.
        index =  pd.MultiIndex.from_product([GeoMapper.geography_to_gau[GeoMapper.supply_primary_geography],self.demand_sectors, self.all_nodes],
                                            names=[GeoMapper.supply_primary_geography, 'demand_sector', 'supply_node'])
        for attribute_name in util.put_in_list(attribute_names):
            setattr(self, attribute_name, util.empty_df(index = index, columns = self.years))


    def add_io_embodied_emissions_df(self):
        #TODO only need to run years with a complete demand data set. Check demand dataframe.
        index =  pd.MultiIndex.from_product([GeoMapper.geography_to_gau[GeoMapper.supply_primary_geography],self.demand_sectors, self.all_nodes,self.ghgs,
                                                                ], names=[GeoMapper.supply_primary_geography,
                                                                 'demand_sector', 'supply_node','ghg'])

        setattr(self, 'io_embodied_emissions_df', util.empty_df(index = index, columns = self.years))

    def create_inverse_dict(self):
        index = pd.MultiIndex.from_product([GeoMapper.geography_to_gau[GeoMapper.supply_primary_geography], self.all_nodes
                                                                ], names=[GeoMapper.supply_primary_geography,'supply_node'])
        df = util.empty_df(index = index, columns = index)
        self.inverse_dict = util.recursivedict()
        for key in ['energy', 'cost']:
            for year in self.years:
                for sector in util.ensure_iterable(self.demand_sectors):
                    self.inverse_dict[key][year][sector]= df

    def create_embodied_cost_and_energy_demand_link(self):
        map_dict = self.map_dict
        keys = sorted(map_dict.items(), key=operator.itemgetter(1))
        keys = [x[0] for x in keys]
        #sorts final energy in the same order as the supply node dataframes
        index = pd.MultiIndex.from_product([GeoMapper.supply_geographies, self.all_nodes], names=[GeoMapper.supply_primary_geography+"_supply",'supply_node'])
        columns = pd.MultiIndex.from_product([GeoMapper.supply_geographies,keys], names=[GeoMapper.supply_primary_geography,'final_energy'])
        self.embodied_cost_link_dict = util.recursivedict()
        self.embodied_energy_link_dict = util.recursivedict()
        for year in self.years:
            for sector in self.demand_sectors:
                self.embodied_cost_link_dict[year][sector] = util.empty_df(index = index, columns = columns).sort_index(axis=0).sort_index(axis=1)
                self.embodied_energy_link_dict[year][sector] = util.empty_df(index = index, columns = columns).sort_index(axis=0).sort_index(axis=1)


    def create_embodied_emissions_demand_link(self):
        map_dict = self.map_dict
        #sorts final energy in the same order as the supply node dataframes
        keys = sorted(map_dict.items(), key=operator.itemgetter(1))
        keys = [x[0] for x in keys]
        index = pd.MultiIndex.from_product([GeoMapper.supply_geographies, self.all_nodes, self.ghgs], names=[GeoMapper.supply_primary_geography+"_supply",'supply_node','ghg'])
        columns = pd.MultiIndex.from_product([GeoMapper.supply_geographies, keys], names=[GeoMapper.supply_primary_geography,'final_energy'])
        self.embodied_emissions_link_dict = util.recursivedict()
        for year in self.years:
            for sector in self.demand_sectors:
                self.embodied_emissions_link_dict[year][sector] = util.empty_df(index=index, columns=columns).sort_index(axis=0).sort_index(axis=1)


    def map_demand_to_io(self):
        """maps final energy demand ids to node nodes for IO table demand calculation"""
        #loops through all final energy types in demand df and adds
        map_dict = self.map_dict
        self.demand_df = self.demand_object.energy_supply_geography.unstack(level='year')
        # round here to get rid of really small numbers
        self.demand_df = self.demand_df.round()
        self.demand_df.columns = self.demand_df.columns.droplevel()
        self.demand_df = self.demand_df.reorder_levels(['sector', GeoMapper.supply_primary_geography, 'final_energy']).sort_index()
        for demand_sector, geography, final_energy in self.demand_df.groupby(level = self.demand_df.index.names).groups:
            try:
                supply_indexer = util.level_specific_indexer(self.io_demand_df, levels=[GeoMapper.supply_primary_geography, 'demand_sector','supply_node'],elements=[geography, demand_sector, map_dict[final_energy]])
                demand_indexer = util.level_specific_indexer(self.demand_df, levels = ['sector', GeoMapper.supply_primary_geography, 'final_energy'],elements=[demand_sector, geography, final_energy])
                self.io_demand_df.loc[supply_indexer, self.years] = self.demand_df.loc[demand_indexer, self.years].values
            except:
                'final energy found in demand not mappable to supply'
                pass


    def map_export_to_io(self,year, loop):
        """maps specified export nodes for IO table total demand calculation"""
        for node in self.nodes.values():
            supply_indexer = util.level_specific_indexer(self.io_export_df, 'supply_node', node.name)
            if loop == 'initial' or loop==1:
                node.export.allocate(node.active_supply, self.demand_sectors, self.years, year, loop)
            self.io_export_df.loc[supply_indexer, year] = node.export.active_values.sort_index().values


class Node(schema.SupplyNodes):
    def __init__(self, name, scenario):
        super(Node, self).__init__(name, scenario=scenario)
        self.init_from_db(name, scenario)
        self.scenario = scenario
        self.active_supply = None
        self.reconciled = False
        #all nodes have emissions subclass
        self.emissions = SupplyEmissions(name, self.scenario)
        # self.shape = self.determine_shape()
        self.rio_conversion_emissions = dict()

    def calculate_subclasses(self):
        """ calculates subclasses of nodes and passes requisite data"""
        if hasattr(self,'export'):
            self.export.calculate(self.years, self.demand_sectors)
        if hasattr(self,'coefficients'):
            self.coefficients.calculate(self.years, self.demand_sectors)
        if hasattr(self,'emissions'):
            self.emissions.calculate(self.conversion, self.resource_unit)
        if hasattr(self,'potential'):
            self.potential.calculate(self.conversion, self.resource_unit)
        if hasattr(self,'capacity_factor'):
            self.capacity_factor.calculate(self.years, self.demand_sectors)
        if hasattr(self,'cost'):
            self.cost.calculate(self.years, self.demand_sectors, self.conversion, self.resource_unit)

    def add_total_stock_measures(self, scenario):
        self.total_stocks = {}
        measure_names = scenario.get_measures('SupplyStockMeasures', self.name)
        for measure_name in measure_names:
            self.total_stocks[measure_name] = SupplySpecifiedStock(name=measure_name, supply_node=self.name, scenario=scenario)

    def set_cost_dataframes(self):
        index = pd.MultiIndex.from_product([GeoMapper.geography_to_gau[GeoMapper.supply_primary_geography], self.demand_sectors], names=[GeoMapper.supply_primary_geography, 'demand_sector'])
        self.levelized_costs = util.empty_df(index=index,columns=self.years,fill_value=0.0)
        self.annual_costs = util.empty_df(index=index,columns=self.years,fill_value=0.0)

    def group_output(self, output_type, levels_to_keep=None):
        levels_to_keep = cfg.output_supply_levels if levels_to_keep is None else levels_to_keep
        if output_type=='stock':
            return self.format_output_stock(levels_to_keep)
        elif output_type=='annual_costs':
            return self.format_output_annual_costs(levels_to_keep)
        elif output_type=='levelized_costs':
            return self.format_output_levelized_costs(levels_to_keep)
        elif output_type == 'capacity_utilization':
            return self.format_output_capacity_utilization(levels_to_keep)

    def format_output_stock(self, override_levels_to_keep=None):
        if not hasattr(self, 'stock'):
            return None
        levels_to_keep = cfg.output_supply_levels if override_levels_to_keep is None else override_levels_to_keep
        levels_to_eliminate = [l for l in self.stock.values.index.names if l not in levels_to_keep]
        df = util.remove_df_levels(self.stock.values, levels_to_eliminate).sort_index()
        # stock starts with vintage as an index and year as a column, but we need to stack it for export
        df = df.stack().to_frame()
        util.replace_index_name(df, 'year')
        stock_unit = cfg.calculation_energy_unit + "/" + cfg.getParam('time_step')
        df.columns =  [stock_unit.upper()]
        return df

    def format_output_capacity_utilization(self, override_levels_to_keep=None):
        if not hasattr(self, 'capacity_utilization'):
            return None
#        levels_to_keep = cfg.output_supply_levels if override_levels_to_keep is None else override_levels_to_keep
#        levels_to_eliminate = [l for l in self.capacity_utilization.index.names if l not in levels_to_keep]
#        df = util.remove_df_levels(self.capacity_utilization, levels_to_eliminate).sort_index()
        # stock starts with vintage as an index and year as a column, but we need to stack it for export
        df = self.capacity_utilization
        df = df.stack().to_frame()
        util.replace_index_name(df, 'year')
        df.columns =  ["%"]
        return df

    def format_output_annual_costs(self,override_levels_to_keep=None):
        if not hasattr(self, 'final_annual_costs'):
            return None
        levels_to_keep = cfg.output_supply_levels if override_levels_to_keep is None else override_levels_to_keep
        levels_to_eliminate = [l for l in self.final_annual_costs.index.names if l not in levels_to_keep]
        if 'vintage' in self.final_annual_costs.index.names:
            df = self.final_annual_costs
            util.replace_index_name(df, 'year','vintage')
        else:
            df = self.final_annual_costs.stack().to_frame()
            util.replace_index_name(df,'year')
        df = util.remove_df_levels(df, levels_to_eliminate).sort_index()
        cost_unit = cfg.getParam('currency_year') + " " + cfg.getParam('currency_name')
        df.columns = [cost_unit.upper()]
        return df

    def format_output_levelized_costs(self, override_levels_to_keep=None):
        if not hasattr(self, 'final_levelized_costs'):
            return None
        levels_to_keep = cfg.output_supply_levels if override_levels_to_keep is None else override_levels_to_keep
        levels_to_eliminate = [l for l in self.final_levelized_costs.index.names if l not in levels_to_keep]
        df = util.remove_df_levels(self.final_levelized_costs, levels_to_eliminate).sort_index()
        # stock starts with vintage as an index and year as a column, but we need to stack it for export
        df = df.stack().to_frame()
        util.replace_index_name(df, 'year')
        cost_unit = cfg.getParam('currency_year') + " " + cfg.getParam('currency_name')
        df.columns = [cost_unit.upper()]
        return df

    def add_conversion(self):
        """
        adds a dataframe used to convert input values that are not in energy terms, to energy terms
        ex. Biomass input as 'tons' must be converted to energy units using a conversion factor data table
        """
        energy_unit = cfg.calculation_energy_unit
        potential_unit = util.csv_read_table('SupplyPotential', 'unit', supply_node=self.name, return_unique=True)
            # check to see if unit is in energy terms, if so, no conversion necessary
        if potential_unit is not None:
            ureg = UnitConverter.get_instance().ureg
            if ureg.Quantity(potential_unit).dimensionality == ureg.Quantity(energy_unit).dimensionality:
                conversion = None
                resource_unit = None
            else:
                # if the unit is not in energy terms, create a conversion class to convert to energy units
                conversion = SupplyEnergyConversion(self.name, self.scenario)
                resource_unit = potential_unit
        else:
            conversion = None
            resource_unit = None
        return conversion, resource_unit

    def aggregate_electricity_shapes(self, year, dispatch_feeder_allocation):
        """ returns a single shape for a year with supply_technology and resource_bin removed and dispatch_feeder added
        ['dispatch_feeder', 'timeshift_type', 'gau', 'weather_datetime']
        """
        if not hasattr(self,'stock'):
            if self.shape is None:
                index = pd.MultiIndex.from_product([GeoMapper.geography_to_gau[GeoMapper.supply_primary_geography],Shapes.get_active_dates_index()], names=[GeoMapper.supply_primary_geography,'weather_datetime'])
                energy_shape = Shape.make_flat_load_shape(index)
            else:
                energy_shape = Shapes.get_values(self.shape)
        elif 'demand_sector' in self.stock.values_energy:
            values_energy = util.remove_df_levels(DfOper.mult([self.stock.values_energy[year],dispatch_feeder_allocation]),'demand_sector')
        else:
            values_energy = self.stock.values_energy[year]
        if self.shape is None and (hasattr(self, 'technologies') and  np.all([tech.shape is None for tech in self.technologies.values()]) or not hasattr(self,'technologies')):
            index = pd.MultiIndex.from_product([GeoMapper.geography_to_gau[GeoMapper.supply_primary_geography],Shapes.get_active_dates_index()], names=[GeoMapper.supply_primary_geography,'weather_datetime'])
            energy_shape = Shape.make_flat_load_shape(index)
        # we don't have technologies or none of the technologies have specific shapes
        elif not hasattr(self, 'technologies') or np.all([tech.shape is None for tech in self.technologies.values()]):
            if 'resource_bin' in Shapes.get_values(self.shape).index.names and 'resource_bin' not in self.stock.values.index.names:
                raise ValueError('Shape for %s has resource bins but the stock in this supply node does not have resource bins as a level' %self.name)
            elif 'resource_bin' in self.stock.values.index.names and 'resource_bin' not in Shapes.get_values(self.shape).index.names:
                energy_shape = Shapes.get_values(self.shape)
            elif 'resource_bin' in self.stock.values.index.names and 'resource_bin' in Shapes.get_values(self.shape).index.names:
                energy_slice = util.remove_df_levels(values_energy, ['vintage', 'supply_technology']).to_frame()
                energy_slice.columns = ['value']
                energy_shape = util.DfOper.mult([energy_slice, Shapes.get_values(self.shape)])
                energy_shape = util.DfOper.divi([util.remove_df_levels(energy_shape,'resource_bin'), util.remove_df_levels(energy_slice, 'resource_bin')])
                energy_shape = energy_shape.replace(np.nan,0)
            else:
                energy_shape = Shapes.get_values(self.shape)
        else:
            energy_slice = util.remove_df_levels(values_energy, 'vintage').to_frame()
            energy_slice.columns = ['value']
            techs_with_default_shape = [tech_name for tech_name, tech in self.technologies.items() if tech.shape is None]
            techs_with_own_shape = [tech_name for tech_name, tech in self.technologies.items() if tech.shape is not None]
            if techs_with_default_shape:
                energy_slice_default_shape = util.df_slice(energy_slice, techs_with_default_shape, 'supply_technology')
                energy_slice_default_shape = util.remove_df_levels(energy_slice_default_shape, 'supply_technology')
                default_shape_portion = util.DfOper.mult([energy_slice_default_shape, Shapes.get_values(self.shape)])
                default_shape_portion = util.remove_df_levels(default_shape_portion, ['resource_bin'])
            if techs_with_own_shape:
                energy_slice_own_shape = util.df_slice(energy_slice, techs_with_own_shape, 'supply_technology')
                tech_shapes = pd.concat([self.technologies[tech_name].shape.values for tech_name in techs_with_own_shape],keys=techs_with_own_shape,names=['supply_technology'])
                tech_shape_portion = util.DfOper.mult([energy_slice_own_shape, tech_shapes])
                tech_shape_portion = util.remove_df_levels(tech_shape_portion, ['supply_technology', 'resource_bin'])
            df = util.DfOper.add([default_shape_portion if techs_with_default_shape else None,
                                  tech_shape_portion if techs_with_own_shape else None],
                                  expandable=False, collapsible=False)
            energy_shape = DfOper.divi([df, util.remove_df_levels(energy_slice,['vintage','supply_technology','resource_bin'])])
        if 'dispatch_constraint' in energy_shape.index.names:
            energy_shape = util.df_slice(energy_shape, 'energy_budget', 'dispatch_constraint')
        return energy_shape


    def aggregate_flexible_electricity_shapes(self, year, dispatch_feeder_allocation):
        """ returns a single shape for a year with supply_technology and resource_bin removed and dispatch_feeder added
        ['dispatch_feeder', 'timeshift_type', 'gau', 'weather_datetime']
        """

        if 'demand_sector' in self.stock.values_energy:
            stock_values_energy = util.remove_df_levels(DfOper.mult([self.stock.values_energy[year],dispatch_feeder_allocation]),'demand_sector')
            stock_values = util.remove_df_levels(DfOper.mult([self.stock.values[year],dispatch_feeder_allocation]),'demand_sector')
        else:
            stock_values_energy = self.stock.values_energy[year]
            stock_values = self.stock.values[year]

        if self.shape is None or not hasattr(self, 'stock'):
            energy_shape = None
            p_max_shape = None
            p_min_shape = None
        elif not hasattr(self, 'technologies') or np.all([tech.shape is None for tech in self.technologies.values()]):
            if 'dispatch_constraint' not in Shapes.get_values(self.shape).index.names:
                if 'resource_bin' in Shapes.get_values(self.shape).index.names and 'resource_bin' not in self.stock.values.index.names:
                    raise ValueError('Shape for %s has resource bins but the stock in this supply node does not have resource bins as a level' %self.name)
                elif 'resource_bin' in self.stock.values.index.names and 'resource_bin' not in Shapes.get_values(self.shape).index.names:
                    energy_shape = Shapes.get_values(self.shape)
                elif 'resource_bin' not in self.stock.values.index.names:
                    energy_shape = Shapes.get_values(self.shape)
                elif 'resource_bin' in self.stock.values.index.names and 'resource_bin' in Shapes.get_values(self.shape).index.names:
                    energy_slice = util.remove_df_levels(stock_values_energy[year], ['vintage', 'supply_technology']).to_frame()
                    energy_slice.columns = ['value']
                    energy_shape = util.DfOper.mult([energy_slice, Shapes.get_values(self.shape)])
                    energy_shape = util.remove_df_levels(energy_shape, 'resource_bin')
                    energy_shape = DfOper.div([energy_shape, util.remove_df_levels(energy_slice,'resource_bin')])
                p_min_shape = None
                p_max_shape = None
            else:
                energy_shape, p_min_shape, p_max_shape,  = self.calculate_disp_constraints_shape(year, stock_values, stock_values_energy)
        else:
            if 'dispatch_constraint' not in Shapes.get_values(self.shape).index.names:
                energy_slice = util.remove_df_levels(self.stock.values_energy[year], 'vintage').to_frame()
                energy_slice.columns = ['value']
                techs_with_default_shape = [tech_name for tech_name, tech in self.technologies.items() if tech.shape is None or 'dispatch_constraint' in Shapes.get_values(tech.shape).index.names]
                techs_with_own_shape = [tech_name for tech_name, tech in self.technologies.items() if tech.shape is not None and 'dispatch_constraint' not in Shapes.get_values(tech.shape).index.names]
                if techs_with_default_shape:
                    energy_slice_default_shape = util.df_slice(energy_slice, techs_with_default_shape, 'supply_technology')
                    energy_slice_default_shape = util.remove_df_levels(energy_slice_default_shape, 'supply_technology')
                    default_shape_portion = util.DfOper.mult([energy_slice_default_shape, Shapes.get_values(self.shape)])
                    default_shape_portion = util.remove_df_levels(default_shape_portion, 'resource_bin')
                if techs_with_own_shape:
                    energy_slice_own_shape = util.df_slice(energy_slice, techs_with_own_shape, 'supply_technology')
                    tech_shapes = pd.concat([self.technologies[tech_name].shape.values for tech_name in techs_with_own_shape])
                    tech_shape_portion = util.DfOper.mult([energy_slice_own_shape, tech_shapes])
                    tech_shape_portion = util.remove_df_levels(tech_shape_portion, 'supply_technology', 'resource_bin')
                #TODO check with Ryan why this is not exapandable
                energy_shape = util.DfOper.add([default_shape_portion if techs_with_default_shape else None,
                                  tech_shape_portion if techs_with_own_shape else None],
                                  expandable=False, collapsible=False)
                energy_shape = util.DfOper.divi([energy_shape,util.remove_df_levels(self.stock.values_energy,['vintage','supply_technology','resource_bin'])])
                p_min_shape = None
                p_max_shape = None
            else:
                energy_shape, p_min_shape, p_max_shape = self.calculate_disp_constraints_shape(self,year, stock_values, stock_values_energy)
        return energy_shape,  p_min_shape , p_max_shape

    def calculate_disp_constraints_shape(self,year, stock_values, stock_values_energy):
        if 'resource_bin' in Shapes.get_values(self.shape).index.names and 'resource_bin' not in self.stock.values.index.names:
            raise ValueError('Shape for %s has resource bins but the stock in this supply node does not have resource bins as a level' %self.name)
        elif 'resource_bin' in self.stock.values.index.names and 'resource_bin' not in Shapes.get_values(self.shape).index.names:
            energy_shape = util.df_slice(Shapes.get_values(self.shape),'energy_budget','dispatch_constraint')
            p_min_shape = util.df_slice(Shapes.get_values(self.shape),'p_min','dispatch_constraint')
            p_max_shape = util.df_slice(Shapes.get_values(self.shape),'p_max','dispatch_constraint')
        elif 'resource_bin' in self.stock.values.index.names and 'resource_bin' in Shapes.get_values(self.shape).index.names:
            energy_slice = util.remove_df_levels(stock_values_energy, ['vintage', 'supply_technology']).to_frame()
            energy_slice.columns = ['value']
            energy_shape = util.DfOper.mult([energy_slice, util.df_slice(Shapes.get_values(self.shape),'energy_budget','dispatch_constraint')])
            energy_shape = util.remove_df_levels(energy_shape, 'resource_bin')
            energy_shape = DfOper.div([energy_shape, util.remove_df_levels(energy_slice,'resource_bin')])
            capacity_slice = util.remove_df_levels(stock_values, ['vintage', 'supply_technology']).to_frame()
            capacity_slice.columns = ['value']
            p_min_shape = util.DfOper.mult([capacity_slice, util.df_slice(Shapes.get_values(self.shape),'p_min','dispatch_constraint')])
            p_min_shape = util.remove_df_levels(p_min_shape, 'resource_bin')
            p_min_shape = DfOper.div([p_min_shape, util.remove_df_levels(capacity_slice,'resource_bin')])
            p_max_shape = util.DfOper.mult([capacity_slice, util.df_slice(Shapes.get_values(self.shape),'p_max','dispatch_constraint')])
            p_max_shape = util.remove_df_levels(p_max_shape, 'resource_bin')
            p_max_shape = DfOper.div([p_max_shape, util.remove_df_levels(capacity_slice,'resource_bin')])
        else:
            energy_shape = util.df_slice(Shapes.get_values(self.shape),'energy_budget','dispatch_constraint')
            p_min_shape = util.df_slice(Shapes.get_values(self.shape),'p_min','dispatch_constraint')
            p_max_shape = util.df_slice(Shapes.get_values(self.shape),'p_max','dispatch_constraint')
        return energy_shape, p_min_shape, p_max_shape

    def calculate_active_coefficients(self, year, loop):
        if year == cfg.getParamAsInt('current_year')and loop == 'initial' :
            #in the first loop, we take the active coefficients for the year
            throughput = self.active_demand
        else:
            throughput = self.active_supply
        if hasattr(self,'potential') and self.potential._has_data is True:
            self.potential.remap_to_potential_and_normalize(throughput, year, self.tradable_geography)
            if self.coefficients._has_data is True:
                filter_geo_potential_normal = util.remove_df_elements(self.potential.active_supply_curve_normal, [x for x in GeoMapper.geography_to_gau_unfiltered[GeoMapper.supply_primary_geography]  if x not in GeoMapper.supply_geographies],GeoMapper.supply_primary_geography)
                filter_geo_potential_normal = filter_geo_potential_normal.reset_index().set_index(filter_geo_potential_normal.index.names)
                self.active_coefficients = util.remove_df_levels(util.DfOper.mult([self.coefficients.values.loc[:,year].to_frame(),
                                                    filter_geo_potential_normal]),'resource_bin')
            else:
                self.active_coefficients = None
        elif self.coefficients._has_data is True:
            self.active_coefficients =  self.coefficients.values.groupby(level=[GeoMapper.supply_primary_geography,  'demand_sector', 'efficiency_type','supply_node']).sum().loc[:,year].to_frame()
        else:
            self.active_coefficients = None
        if self.active_coefficients is not None:
            self.active_coefficients_total_untraded = util.remove_df_levels(self.active_coefficients,'efficiency_type')
            self.active_coefficients_total = self.add_column_index(self.active_coefficients_total_untraded)
            self.active_coefficients_total = util.DfOper.mult([self.active_coefficients_total,self.active_trade_adjustment_df])
            self.active_coefficients_untraded = copy.deepcopy(self.active_coefficients)
            self.active_coefficients_untraded.sort(inplace=True,axis=0)
            nodes = list(set(self.active_trade_adjustment_df.index.get_level_values('supply_node')))
            df_list = []
            for node in nodes:
                trade_indexer = util.level_specific_indexer(self.active_trade_adjustment_df, 'supply_node', node)
                coefficient_indexer = util.level_specific_indexer(self.active_coefficients_untraded, 'supply_node', node)
                efficiency_types = list(set(self.active_coefficients_untraded.loc[coefficient_indexer,:].index.get_level_values('efficiency_type')))
                keys = efficiency_types
                name = ['efficiency_type']
                df = pd.concat([self.active_trade_adjustment_df.loc[trade_indexer,:]]*len(keys),keys=keys,names=name)
                df_list.append(df)
            active_trade_adjustment_df = pd.concat(df_list)
            self.active_coefficients = self.add_column_index(self.active_coefficients_untraded)
            self.active_coefficients = util.DfOper.mult([self.active_coefficients,active_trade_adjustment_df])
            keys = self.ghgs
            name = ['ghg']
            self.active_emissions_coefficients = pd.concat([self.active_coefficients]*len(keys), keys=keys, names=name)
            self.active_emissions_coefficients = self.active_emissions_coefficients.reorder_levels([GeoMapper.supply_primary_geography,'demand_sector', 'supply_node', 'efficiency_type', 'ghg'])
            self.active_emissions_coefficients.sort(inplace=True)
        else:
            self.active_coefficients_total = None
            self.active_emissions_coefficients = None

    def add_column_index(self, data):
         names = ['demand_sector', GeoMapper.supply_primary_geography]
         keys = [self.demand_sectors, GeoMapper.geography_to_gau[GeoMapper.supply_primary_geography]]
         data  = copy.deepcopy(data)
         for key,name in zip(keys,names):
             data  = pd.concat([data]*len(key), axis=1, keys=key, names=[name])
         data.columns = data.columns.droplevel(-1)
         return data

    def add_row_index(self, data):
         names = ['demand_sector', GeoMapper.supply_primary_geography]
         keys = [self.demand_sectors, GeoMapper.geography_to_gau[GeoMapper.supply_primary_geography]]
         data  = copy.deepcopy(data.transpose())
         for key,name in zip(keys,names):
             data  = pd.concat([data]*len(key), axis=0, keys=key, names=[name])
         data.index = data.index.droplevel(-1)
         return data

    def add_exports(self, scenario):
        measures = scenario.get_measures('SupplyExportMeasures', self.name)
        if len(measures) > 1:
            raise ValueError('model does not currently support multiple active export measures from a single supply node. Turn off an export measure in supply node %s' %self.name)
        elif len(measures) == 1:
            self.export = SupplyExportMeasuresObj(name=measures[0], scenario=scenario)
        else:
            self.export = SupplyExportObj(supply_node=self.name, scenario=scenario)

    def convert_stock(self, stock_name='stock', attr='total'):
        model_energy_unit = cfg.calculation_energy_unit
        model_time_step = cfg.getParam('time_step')
        stock = getattr(self,stock_name)
        if stock.time_unit is not None:
            # if a stock has a time_unit, then the unit is energy and must be converted to capacity
            setattr(stock, attr, UnitConverter.unit_convert(getattr(stock, attr), unit_from_num=stock.capacity_or_energy_unit, unit_from_den=stock.time_unit,
                                             unit_to_num=model_energy_unit, unit_to_den=model_time_step))
        else:
            # if a stock is a capacity unit, the model must convert the unit type to an energy unit for conversion ()
            unit_from_num = stock.capacity_or_energy_unit + "_" + model_time_step
            setattr(stock, attr, UnitConverter.unit_convert(getattr(stock, attr), unit_from_num=unit_from_num, unit_from_den=model_time_step, unit_to_num=model_energy_unit, unit_to_den=model_time_step))

    def calculate_potential_constraints(self, year):
        """calculates the exceedance factor of a node if the node active supply exceeds the potential in the node. This adjustment factor
        is passed to other nodes in the reconcile step"""
        if hasattr(self,'potential') and self.potential._has_data is True and self.enforce_potential_constraint == True and not cfg.rio_supply_run:
            #geomap potential to the tradable geography. Potential is not exceeded unless it is exceeded in a tradable geography region.
            active_geomapped_potential, active_geomapped_supply = self.potential.format_potential_and_supply_for_constraint_check(self.active_supply, self.tradable_geography, year)
            self.potential_exceedance = util.DfOper.divi([active_geomapped_potential,active_geomapped_supply], expandable = (False,False), collapsible = (True, True))
            #reformat dataframes for a remap
            self.potential_exceedance[self.potential_exceedance<0] = 1
            self.potential_exceedance = self.potential_exceedance.replace([np.nan,np.inf],[1,1])
            self.potential_exceedance= pd.DataFrame(self.potential_exceedance.stack(), columns=['value'])
            util.replace_index_name(self.potential_exceedance, 'year')
            remove_levels = [x for x in self.potential_exceedance.index.names if x not in [self.tradable_geography, 'demand_sector']]
            if len(remove_levels):
                self.potential_exceedance = util.remove_df_levels(self.potential_exceedance, remove_levels)
            geography_map_key = self.geography_map_key if hasattr(self, 'geography_map_key') else GeoMapper.default_geography_map_key
            if self.tradable_geography != GeoMapper.supply_primary_geography:
                map_df = GeoMapper.get_instance().map_df(self.tradable_geography, GeoMapper.supply_primary_geography, normalize_as='intensity', map_key=geography_map_key, eliminate_zeros=False)
                self.potential_exceedance = util.remove_df_levels(util.DfOper.mult([self.potential_exceedance,map_df]), self.tradable_geography)
            self.active_constraint_df = util.remove_df_elements(self.potential_exceedance, [x for x in GeoMapper.geography_to_gau_unfiltered[GeoMapper.supply_primary_geography]  if x not in GeoMapper.supply_geographies],GeoMapper.supply_primary_geography)
            if 'demand_sector' not in self.active_constraint_df.index.names:
                keys = self.demand_sectors
                name = ['demand_sector']
                active_constraint_df = pd.concat([self.active_constraint_df]*len(keys), keys=keys, names=name)
                active_constraint_df= active_constraint_df.swaplevel('demand_sector',-1)
                self.active_constraint_df = active_constraint_df.sort(inplace=False)
            self.active_constraint_df[self.active_constraint_df>1]=1
            if np.any(self.active_constraint_df.values<1):
                self.constraint_violation = True
            else:
                self.constraint_violation = False
        else:
            self.constraint_violation = False


    def calculate_potential_constraints_evolved(self, year, active_supply):
        """calculates the exceedance factor of a node if the node active supply exceeds the potential in the node. This adjustment factor
        is passed to other nodes in the reconcile step"""
        if hasattr(self,'potential') and self.potential._has_data is True:
            #geomap potential to the tradable geography. Potential is not exceeded unless it is exceeded in a tradable geography region.
            active_geomapped_potential, active_geomapped_supply = self.potential.format_potential_and_supply_for_constraint_check(active_supply, self.tradable_geography, year)
            self.potential_exceedance = util.DfOper.divi([active_geomapped_potential,active_geomapped_supply], expandable = (False,False), collapsible = (True, True))
            #reformat dataframes for a remap
            self.potential_exceedance[self.potential_exceedance<0] = 1
            self.potential_exceedance = self.potential_exceedance.replace([np.nan,np.inf],[1,1])
            self.potential_exceedance= pd.DataFrame(self.potential_exceedance.stack(), columns=['value'])
            util.replace_index_name(self.potential_exceedance, 'year')
            remove_levels = [x for x in self.potential_exceedance.index.names if x not in [self.tradable_geography, 'demand_sector']]
            if len(remove_levels):
                self.potential_exceedance = util.remove_df_levels(self.potential_exceedance, remove_levels)
            geography_map_key = self.geography_map_key if hasattr(self, 'geography_map_key') else GeoMapper.default_geography_map_key
            if self.tradable_geography != GeoMapper.supply_primary_geography:
                map_df = GeoMapper.get_instance().map_df(self.tradable_geography, GeoMapper.supply_primary_geography, normalize_as='intensity', map_key=geography_map_key, eliminate_zeros=False)
                self.potential_exceedance = util.remove_df_levels(util.DfOper.mult([self.potential_exceedance,map_df]), self.tradable_geography)
            self.active_constraint_df = util.remove_df_elements(self.potential_exceedance, [x for x in GeoMapper.geography_to_gau_unfiltered[GeoMapper.supply_primary_geography]  if x not in GeoMapper.supply_geographies],GeoMapper.supply_primary_geography)
            if 'demand_sector' not in self.active_constraint_df.index.names:
                keys = self.demand_sectors
                name = ['demand_sector']
                active_constraint_df = pd.concat([self.active_constraint_df]*len(keys), keys=keys, names=name)
                active_constraint_df= active_constraint_df.swaplevel('demand_sector',-1)
                self.active_constraint_df = active_constraint_df.sort(inplace=False)
            self.active_constraint_df[self.active_constraint_df>1]=1
            if np.any(self.active_constraint_df.values<1):
                self.constraint_violation = True
            else:
                self.constraint_violation = False
        else:
            self.constraint_violation = False

    def calculate_internal_trades(self, year, loop):
        """calculates internal trading adjustment factors based on the ratio of active supply to supply potential or stock
        used for nodes where the location of throughput is unrelated to the location of demand (ex. primary biomass supply)
        """
        if self.tradable_geography!= GeoMapper.supply_primary_geography and len(GeoMapper.supply_geographies)>1 :
            if hasattr(self,'potential') and self.potential._has_data is True or (hasattr(self,'stock') and (self.stock._has_data or self.stock.total.sum().sum()>0) is True):
                #tradable supply is mapping of active supply to a tradable geography
                try:
                    self.geo_step1 = GeoMapper.get_instance().map_df(GeoMapper.supply_primary_geography,self.tradable_geography, normalize_as='total', eliminate_zeros=False)
                except:
                    logging.error('self.tradable_geography = {}, primary_geography = {}, name = {}'.format(self.tradable_geography, GeoMapper.supply_primary_geography, self.name))
                    raise
                if hasattr(self,'potential') and self.potential._has_data is True:
                     df = util.remove_df_elements(self.potential.active_supply_curve, [x for x in GeoMapper.geography_to_gau_unfiltered[GeoMapper.supply_primary_geography]  if x not in GeoMapper.supply_geographies],GeoMapper.supply_primary_geography)
                     self.potential_geo = util.DfOper.mult([util.remove_df_levels(df,
                                                                                  [x for x in self.potential.active_supply_curve.index.names if x not in [GeoMapper.supply_primary_geography,'demand_sector']]),
                                                                                    GeoMapper.get_instance().map_df(GeoMapper.supply_primary_geography,self.tradable_geography,normalize_as='total')])
                     util.replace_index_name(self.potential_geo,GeoMapper.supply_primary_geography + "from", GeoMapper.supply_primary_geography)
                     #if a node has potential, this becomes the basis for remapping
                if hasattr(self,'stock') and hasattr(self.stock,'act_total_energy'):
                    total_stock = util.remove_df_levels(self.stock.act_total_energy, [x for x in self.stock.act_total_energy.index.names if x not in [GeoMapper.supply_primary_geography,'demand_sector']])
                    self.stock_energy_geo = util.DfOper.mult([total_stock,GeoMapper.get_instance().map_df(GeoMapper.supply_primary_geography,self.tradable_geography, normalize_as='total', eliminate_zeros=False)])
                    util.replace_index_name(self.stock_energy_geo,GeoMapper.supply_primary_geography+ "from", GeoMapper.supply_primary_geography)
                elif  hasattr(self,'stock') and hasattr(self.stock,'act_total'):
                    total_stock = util.remove_df_levels(self.stock.act_total, [x for x in self.stock.act_total.index.names if x not in [GeoMapper.supply_primary_geography,'demand_sector']])
                    self.stock_capacity_geo = util.DfOper.mult([total_stock,GeoMapper.get_instance().map_df(GeoMapper.supply_primary_geography, self.tradable_geography,eliminate_zeros=False)])
                    util.replace_index_name(self.stock_capacity_geo ,GeoMapper.supply_primary_geography + "from", GeoMapper.supply_primary_geography)

                if hasattr(self,'stock_energy_geo') and hasattr(self,'potential_geo'):
                    #this is a special case when we have a stock and specified potential. We want to distribute growth in the stock by potential while maintaing trades to support existing stock.
                    active_supply = util.remove_df_levels(self.active_supply, [x for x in self.active_supply.index.names if x not in self.stock.act_total_energy.index.names])
                    total_active_supply = util.remove_df_levels(util.DfOper.mult([active_supply,GeoMapper.get_instance().map_df(GeoMapper.supply_primary_geography,self.tradable_geography, normalize_as='total', eliminate_zeros=False)]),GeoMapper.supply_primary_geography)
                    total_stock = util.remove_df_levels(self.stock_energy_geo,GeoMapper.supply_primary_geography)
                    stock_share = util.remove_df_levels(util.DfOper.divi([total_stock,total_active_supply]),GeoMapper.supply_primary_geography + "from")
                    stock_share[stock_share>1] = 1
                    stock_geo_step = self.stock_energy_geo.groupby(level=util.ix_excl(self.stock_energy_geo,GeoMapper.supply_primary_geography + "from")).transform(lambda x: x/x.sum()).fillna(0)
                    stock_geo_step = util.DfOper.mult([stock_geo_step, stock_share])
                    potential_share = 1- stock_share
                    potential_geo_step = util.DfOper.subt([self.potential_geo,self.stock_energy_geo])
                    potential_geo_step[potential_geo_step<0]=0
                    potential_geo_step = potential_geo_step.groupby(level=util.ix_excl(self.potential_geo,GeoMapper.supply_primary_geography + "from")).transform(lambda x: x/x.sum()).fillna(0)
                    potential_geo_step = util.DfOper.mult([potential_geo_step, potential_share])
                    self.geo_step2 = util.DfOper.add([stock_geo_step,potential_geo_step])
                elif hasattr(self,'stock_energy_geo'):
                    self.geo_step2 = self.stock_energy_geo.groupby(level=util.ix_excl(self.stock_energy_geo,GeoMapper.supply_primary_geography + "from")).transform(lambda x: x/x.sum()).fillna(0)
                elif hasattr(self,'stock_capacity_geo'):
                    self.geo_step2 = self.stock_capacity_geo.groupby(level=util.ix_excl(self.stock_capacity_geo,GeoMapper.supply_primary_geography + "from")).transform(lambda x: x/x.sum()).fillna(0)
                elif hasattr(self,'potential_geo'):
                    self.geo_step2 = self.potential_geo.groupby(level=util.ix_excl(self.potential_geo,GeoMapper.supply_primary_geography + "from")).transform(lambda x: x/x.sum()).fillna(0)
                self.geomapped_coefficients = util.DfOper.mult([self.geo_step1, self.geo_step2])
                self.geomapped_coefficients = self.geomapped_coefficients.unstack(GeoMapper.supply_primary_geography)
                util.replace_index_name(self.geomapped_coefficients,GeoMapper.supply_primary_geography,GeoMapper.supply_primary_geography + "from")
                self.geomapped_coefficients = util.remove_df_levels(self.geomapped_coefficients,self.tradable_geography)
                self.geomapped_coefficients.columns = self.geomapped_coefficients.columns.droplevel()
                self.active_internal_trade_df = pd.concat([self.geomapped_coefficients]*len(self.demand_sectors),axis=1,keys=self.demand_sectors,names=['demand_sector'])
                self.active_internal_trade_df= self.active_internal_trade_df.swaplevel(GeoMapper.supply_primary_geography,'demand_sector',axis=1)
                if 'demand_sector' not in self.active_internal_trade_df.index.names:
                    self.active_internal_trade_df = pd.concat([self.active_internal_trade_df]*len(self.demand_sectors),axis=0,keys=self.demand_sectors,names=['demand_sector'])
                    self.active_internal_trade_df = self.active_internal_trade_df.swaplevel(GeoMapper.supply_primary_geography,'demand_sector',axis=0)
                self.active_internal_trade_df.sort(axis=0,inplace=True)
                self.active_internal_trade_df.sort(axis=1,inplace=True)
                for sector_row in self.demand_sectors:
                    for sector_column in self.demand_sectors:
                        row_indexer = util.level_specific_indexer(self.active_internal_trade_df,'demand_sector', sector_row)
                        col_indexer = util.level_specific_indexer(self.active_internal_trade_df,'demand_sector', sector_column)
                        if sector_row == sector_column:
                            mult =1
                        else:
                            mult=0
                        self.active_internal_trade_df.loc[row_indexer, col_indexer] *= mult
                if np.all(np.round(self.active_internal_trade_df.sum().values,2)==1.) or np.all(np.round(self.active_internal_trade_df.sum().values,2)==0):
                    pass
                self.internal_trades = "stop and feed"
            else:
                self.internal_trades = "stop"
        elif self.tradable_geography != GeoMapper.supply_primary_geography:
            #if there is only one geography, there is no trading
            self.internal_trades = "stop"
        elif self.tradable_geography == GeoMapper.supply_primary_geography and self.enforce_tradable_geography:
            #if the tradable geography is set to equal the primary geography, then any trades upstream are stopped at this node
            self.internal_trades = "stop"
        else:
            #otherwise, pass trades upstream to downstream nodes
            self.internal_trades = "feed"


    def calculate_input_emissions_rates(self,year,ghgs):
        "calculates the emissions rate of nodes with emissions"
        if hasattr(self,'emissions') and self.emissions._has_data is True:
            if hasattr(self,'potential') and self.potential._has_data is True:
                filter_geo_potential_normal = util.remove_df_elements(self.potential.active_supply_curve_normal, [x for x in GeoMapper.geography_to_gau_unfiltered[GeoMapper.supply_primary_geography]  if x not in GeoMapper.supply_geographies],GeoMapper.supply_primary_geography)
                filter_geo_potential_normal = filter_geo_potential_normal.reset_index().set_index(filter_geo_potential_normal.index.names)
                self.active_physical_emissions_rate = DfOper.mult([filter_geo_potential_normal,self.emissions.values_physical.loc[:,year].to_frame()])
                levels = ['demand_sector',GeoMapper.supply_primary_geography,'ghg']
                disallowed_levels = [x for x in self.active_physical_emissions_rate.index.names if x not in levels]
                if len(disallowed_levels):
                    self.active_physical_emissions_rate = util.remove_df_levels(self.active_physical_emissions_rate, disallowed_levels)
                self.active_physical_emissions_rate = util.expand_multi(self.active_physical_emissions_rate, levels_list = [GeoMapper.supply_geographies, self.demand_sectors, self.ghgs],levels_names=[GeoMapper.supply_primary_geography,'demand_sector', 'ghg'])
                self.active_accounting_emissions_rate = DfOper.mult([filter_geo_potential_normal,self.emissions.values_accounting.loc[:,year].to_frame()])
                levels = ['demand_sector',GeoMapper.supply_primary_geography,'ghg']
                disallowed_levels = [x for x in self.active_accounting_emissions_rate.index.names if x not in levels]
                if len(disallowed_levels):
                    self.active_accounting_emissions_rate = util.remove_df_levels(self.active_accounting_emissions_rate, disallowed_levels)
                self.active_accounting_emissions_rate = util.expand_multi(self.active_accounting_emissions_rate, levels_list = [GeoMapper.supply_geographies, self.demand_sectors, self.ghgs], levels_names=[GeoMapper.supply_primary_geography,'demand_sector','ghg'])
            else:
                allowed_indices = ['demand_sector', GeoMapper.supply_primary_geography, 'ghg', 'ghg_type']
                if set(self.emissions.values_physical.index.names).issubset(allowed_indices):
                    self.active_physical_emissions_rate = util.remove_df_levels(self.emissions.values_physical.loc[:,year].to_frame(), 'ghg_type')
                    self.active_physical_emissions_rate = util.expand_multi(self.active_physical_emissions_rate, levels_list = [GeoMapper.supply_geographies, self.demand_sectors, self.ghgs],levels_names=[GeoMapper.supply_primary_geography,'demand_sector', 'ghg'])
                if set(self.emissions.values_accounting.index.names).issubset(allowed_indices):
                    self.active_accounting_emissions_rate =  util.remove_df_levels(self.emissions.values_accounting.loc[:,year].to_frame(), 'ghg_type')
                    self.active_accounting_emissions_rate = util.expand_multi(self.active_accounting_emissions_rate, levels_list = [GeoMapper.supply_geographies, self.demand_sectors, self.ghgs],levels_names=[GeoMapper.supply_primary_geography,'demand_sector', 'ghg'])
                else:
                    raise ValueError("too many indexes in emissions inputs of node %s" %self.name)
            keys = [self.demand_sectors, GeoMapper.supply_geographies]
            names = ['demand_sector', GeoMapper.supply_primary_geography]
            active_physical_emissions_rate = copy.deepcopy(self.active_physical_emissions_rate)
            for key,name in zip(keys,names):
                active_physical_emissions_rate = pd.concat([active_physical_emissions_rate]*len(key), axis=1, keys=key, names=[name])
            for sector_a in self.demand_sectors:
                for sector_b in self.demand_sectors:
                    row_indexer = util.level_specific_indexer(active_physical_emissions_rate,'demand_sector', sector_a, axis=0)
                    col_indexer = util.level_specific_indexer(active_physical_emissions_rate,'demand_sector',sector_b, axis=1)
                    if sector_a == sector_b:
                        mult = 1
                    else:
                        mult = 0
                    active_physical_emissions_rate.loc[row_indexer,col_indexer] = active_physical_emissions_rate.loc[row_indexer,col_indexer].values * mult
            self.active_physical_emissions_rate = active_physical_emissions_rate
            self.active_physical_emissions_rate.columns = self.active_physical_emissions_rate.columns.droplevel(-1)
            self.emissions_rate = True
        else:
            self.emissions_rate = False


    def calculate_emissions(self,year):
        if hasattr(self,'active_physical_emissions_coefficients'):
            if 'consumed' in self.active_physical_emissions_coefficients.index.get_level_values('efficiency_type'):
                indexer = util.level_specific_indexer(self.active_physical_emissions_coefficients,'efficiency_type', 'consumed')
                combustion_emissions = copy.deepcopy(self.active_physical_emissions_coefficients.loc[indexer,:])
                combustion_emissions.loc[:,:] = self.active_supply.T.values * self.active_physical_emissions_coefficients.loc[indexer,:].values
                self.active_combustion_emissions = combustion_emissions.groupby(level='ghg').sum()
                self.active_combustion_emissions = self.active_combustion_emissions.unstack(GeoMapper.supply_primary_geography).to_frame()
                if hasattr(self,'active_co2_capture_rate'):
                    self.active_combustion_emissions = DfOper.mult([self.active_combustion_emissions, 1 - self.active_co2_capture_rate])
                    self.rio_conversion_emissions[year] = DfOper.mult([self.active_combustion_emissions, self.active_co2_capture_rate])
                self.active_combustion_emissions = util.remove_df_levels(self.active_combustion_emissions,'resource_bin')
        if hasattr(self,'active_accounting_emissions_rate'):
            self.active_accounting_emissions = DfOper.mult([self.active_accounting_emissions_rate,self.active_supply])
        if hasattr(self,'active_accounting_emissions') and hasattr(self,'active_combustion_emissions'):
            self.active_total_emissions = DfOper.add([self.active_accounting_emissions, self.active_combustion_emissions])
        elif hasattr(self,'active_accounting_emissions'):
            self.active_total_emissions = self.active_accounting_emissions
        elif hasattr(self,'active_combustion_emissions'):
            self.active_total_emissions = self.active_combustion_emissions

    def calculate_embodied_emissions_rate(self, year):
        if hasattr(self,'active_total_emissions'):
            self.active_embodied_emissions_rate = DfOper.divi([self.active_total_emissions, self.active_supply])

    def set_adjustments(self):
        self.set_trade_adjustment_dict()
        self.set_internal_trade_dict()
#        self.set_constraint_adjustment_dict()
#        self.set_constraint_dict()

    def set_trade_adjustment_dict(self):
        """sets an empty df with a fill value of 1 for trade adjustments"""
        if hasattr(self,'nodes'):
            self.trade_adjustment_dict = defaultdict(dict)
            row_index = pd.MultiIndex.from_product([GeoMapper.supply_geographies, self.demand_sectors, self.nodes], names=[GeoMapper.supply_primary_geography, 'demand_sector', 'supply_node'])
            col_index = pd.MultiIndex.from_product([GeoMapper.supply_geographies, self.demand_sectors], names=[GeoMapper.supply_primary_geography, 'demand_sector'])
            trade_adjustment_df = util.empty_df(index=row_index,columns=col_index,fill_value=0.0)
            trade_adjustment_df.sort(inplace=True, axis=0)
            trade_adjustment_df.sort(inplace=True, axis=1)
            trade_adjustment_groups = trade_adjustment_df.groupby(level=trade_adjustment_df.index.names).groups
            for elements in trade_adjustment_groups.keys():
                row_indexer = util.level_specific_indexer(trade_adjustment_df, trade_adjustment_df.index.names, elements)
                col_indexer = util.level_specific_indexer(trade_adjustment_df,[GeoMapper.supply_primary_geography, 'demand_sector'], elements[:-1], axis=1)
                trade_adjustment_df.loc[row_indexer, col_indexer] = 1.0
            for year in self.years:
               self.trade_adjustment_dict[year] = copy.deepcopy(trade_adjustment_df)
            self.active_trade_adjustment_df = trade_adjustment_df

    def set_internal_trade_dict(self):
        """sets an empty df with a fill value of 1 for internal trades"""
        if self.tradable_geography is not None:
            self.internal_trade_dict = defaultdict(dict)
            index = pd.MultiIndex.from_product([GeoMapper.supply_geographies, self.demand_sectors], names=[GeoMapper.supply_primary_geography, 'demand_sector'])
            internal_trade_df = util.empty_df(index=index,columns=index,fill_value=0.0)
            internal_trade_df.sort(inplace=True, axis=0)
            internal_trade_df.sort(inplace=True, axis=1)
            internal_trade_groups = internal_trade_df.groupby(level=internal_trade_df.index.names).groups
            for elements in internal_trade_groups.keys():
                row_indexer = util.level_specific_indexer(internal_trade_df, internal_trade_df.index.names, elements)
                col_indexer = util.level_specific_indexer(internal_trade_df,[GeoMapper.supply_primary_geography, 'demand_sector'], list(elements), axis=1)
                internal_trade_df.loc[row_indexer, col_indexer] = 1.0
            for year in self.years:
                self.internal_trade_dict[year] = copy.deepcopy(internal_trade_df)
            self.active_internal_trade_df = internal_trade_df

    def set_pass_through_df_dict(self):
        """sets an empty df with a fill value of 1 for trade adjustments"""
        self.pass_through_df_dict = defaultdict(dict)
        row_index = pd.MultiIndex.from_product([GeoMapper.supply_geographies, self.demand_sectors, self.ghgs], names=[GeoMapper.supply_primary_geography, 'demand_sector', 'ghg'])
        col_index = pd.MultiIndex.from_product([GeoMapper.supply_geographies, self.demand_sectors], names=[GeoMapper.supply_primary_geography, 'demand_sector'])
        pass_through_df = util.empty_df(index=row_index,columns=col_index,fill_value=0.0)
        pass_through_df.sort(inplace=True, axis=0)
        pass_through_df.sort(inplace=True, axis=1)
        for year in self.years:
            self.pass_through_df_dict[year] = copy.deepcopy(pass_through_df)
        self.active_pass_through_df = copy.deepcopy(self.pass_through_df_dict[year])

    def update_pass_through_df_dict(self,year, loop=None):
        if hasattr(self,'pass_through_df_dict'):
            self.active_pass_through_df =self.pass_through_df_dict[year]
            self.active_pass_through_df*=0

    def set_pass_through_dict(self, node_dict):
        if self.active_coefficients is not None:
            self.active_coefficients = self.active_coefficients.sort_index()
            if 'not consumed' in set(self.active_coefficients.index.get_level_values('efficiency_type')):
                indexer = util.level_specific_indexer(self.active_coefficients,'efficiency_type', 'not consumed')
                pass_through_subsectors = self.active_coefficients.loc[indexer,:].index.get_level_values('supply_node')
                pass_through_subsectors = [x for x in pass_through_subsectors if node_dict.has_key(x)]
                self.pass_through_dict = dict.fromkeys(pass_through_subsectors,False)

class Export(DataObject):
    def __init__(self):
        pass

    def calculate(self, years, demand_sectors):
        self.years = years
        self.demand_sectors = demand_sectors
        if self._has_data:
            self.remap(lower=None, converted_geography=GeoMapper.supply_primary_geography)
            self.convert()
            self.values = util.reindex_df_level_with_new_elements(self.values, GeoMapper.supply_primary_geography, GeoMapper.supply_geographies, fill_value=0.0)
        else:
            self.set_export_df()

    def convert(self):
       self.values = self.values.unstack(level='year')
       self.values.columns = self.values.columns.droplevel()
       self.values = UnitConverter.unit_convert(self.values, unit_from_num=self.unit, unit_to_num=cfg.calculation_energy_unit)

    def set_export_df(self):
        """sets an empty df with a fill value of 0"""
        df_index = pd.MultiIndex.from_product([GeoMapper.supply_geographies, self.demand_sectors], names=[GeoMapper.supply_primary_geography, 'demand_sector'])
        self.values= util.empty_df(index=df_index, columns=self.years, fill_value=0)

    def allocate(self, active_supply, demand_sectors, supply_years, year, loop):
        """Performs sectoral allocation of active export values. In year 1/loop1, this happens equally across sectors. Once throughput is known, it is allocated by throughput"""
        if year == min(supply_years) and loop == 'initial':
            if 'demand_sector' not in self.values.index.names:
                active_values = []
                for sector in self.demand_sectors:
                    #if we have no active supply, we must allocate exports pro-rata across number of sectors
                    active_value = copy.deepcopy(self.values.loc[:,year].to_frame()) * 1/len(self.demand_sectors)
                    active_value['demand_sector'] = sector
                    active_values.append(active_value)
                active_values = pd.concat(active_values)
                active_values.set_index('demand_sector', append=True, inplace=True)
                self.active_values = active_values
            else:
                self.active_values = self.values.loc[:,year].to_frame()
        else:
            #remap exports to active supply, which has information about sectoral throughput
            self.active_values =  self.values.loc[:,year].to_frame()
            active_supply[active_supply.values<0]=0
            self.remap(map_from='active_values', map_to='active_values', drivers=active_supply, fill_timeseries=False,
                       current_geography=GeoMapper.supply_primary_geography, converted_geography=GeoMapper.supply_primary_geography, driver_geography=GeoMapper.supply_primary_geography)
        self.active_values.replace(np.nan,0,inplace=True)
        self.active_values = self.active_values.reorder_levels([GeoMapper.supply_primary_geography, 'demand_sector'])

class SupplyExportObj(schema.SupplyExport, Export):
    def __init__(self, supply_node, scenario):
        schema.SupplyExport.__init__(self, supply_node, scenario=scenario)
        self.init_from_db(supply_node, scenario)
        self.input_type = 'total'

class SupplyExportMeasuresObj(schema.SupplyExportMeasures, Export):
    def __init__(self, name, scenario):
        schema.SupplyExportMeasures.__init__(self, name, scenario=scenario)
        self.init_from_db(name, scenario)
        self.input_type = 'total'

class RioExport(DataObject):
    def __init__(self,name,raw_values):
        self.name = name
        self._has_data = True
        self.raw_values = raw_values.groupby(level=[GeoMapper.supply_primary_geography,'year']).sum()
        self.raw_values = self.raw_values.replace(np.inf,0)
        self.raw_values = self.raw_values.fillna(0)
        self.input_type = 'total'
        self.geography = cfg.rio_geography
        self.interpolation_method = 'linear_interpolation'
        self.extrapolation_method = 'nearest'
        self.geography_map_key = None
        self.unit = cfg.rio_energy_unit
        self._cols = []


    def calculate(self, years, demand_sectors):
        self.years = years
        self.demand_sectors = demand_sectors
        if self._has_data and len(self.raw_values)>0:
            self.remap(lower=None, converted_geography=GeoMapper.supply_primary_geography)
            self.convert()
            self.values = util.reindex_df_level_with_new_elements(self.values, GeoMapper.supply_primary_geography,
                                                                  GeoMapper.supply_geographies, fill_value=0.0)
        else:
            self.set_export_df()

    def convert(self):
        self.values = self.values.unstack(level='year')
        self.values.columns = self.values.columns.droplevel()
        self.values = UnitConverter.unit_convert(self.values, unit_from_num=self.unit, unit_to_num=cfg.calculation_energy_unit)

    def set_export_df(self):
        """sets an empty df with a fill value of 0"""
        df_index = pd.MultiIndex.from_product([GeoMapper.supply_geographies, self.demand_sectors],
                                              names=[GeoMapper.supply_primary_geography, 'demand_sector'])
        self.values = util.empty_df(index=df_index, columns=self.years, fill_value=0)

    def allocate(self, active_supply, demand_sectors, supply_years, year, loop):
        """Performs sectoral allocation of active export values. In year 1/loop1, this happens equally across sectors. Once throughput is known, it is allocated by throughput"""
        if year == min(supply_years) and loop == 'initial':
            if 'demand_sector' not in self.values.index.names:
                active_values = []
                for sector in self.demand_sectors:
                    # if we have no active supply, we must allocate exports pro-rata across number of sectors
                    active_value = copy.deepcopy(self.values.loc[:, year].to_frame()) * 1 / len(self.demand_sectors)
                    active_value['demand_sector'] = sector
                    active_values.append(active_value)
                active_values = pd.concat(active_values)
                active_values.set_index('demand_sector', append=True, inplace=True)
                self.active_values = active_values
            else:
                self.active_values = self.values.loc[:, year].to_frame()
        else:
            # remap exports to active supply, which has information about sectoral throughput
            self.active_values = self.values.loc[:, year].to_frame()
            active_supply[active_supply.values <= 0] = .01
            self.active_values = util.DfOper.mult(
                [active_supply.groupby(level=GeoMapper.supply_primary_geography).transform(lambda x: x / x.sum()),
                 self.active_values])
        self.active_values.replace(np.nan, 0, inplace=True)
        self.active_values = self.active_values.reorder_levels([GeoMapper.supply_primary_geography, 'demand_sector'])

class BlendNode(Node):
    def __init__(self, name, scenario):
        super(BlendNode, self).__init__(name, scenario=scenario)
        self.nodes = util.csv_read_table('BlendNodeInputsData', 'supply_node', blend_node=name, return_iterable=True)
        #used as a flag in the annual loop for whether we need to recalculate the coefficients


    def calculate_active_coefficients(self, year, loop):
            self.active_coefficients = self.values.loc[:,year].to_frame()
            self.active_coefficients_total_untraded = util.remove_df_levels(self.active_coefficients,'efficiency_type')
            self.active_coefficients_untraded = copy.deepcopy(self.active_coefficients)
            self.active_coefficients_untraded.sort(inplace=True,axis=0)
            if cfg.rio_supply_run and hasattr(self,'rio_trades'):
                self.active_coefficients = self.add_column_index(self.active_coefficients_untraded)
                self.active_coefficients_total = self.add_column_index(self.active_coefficients_total_untraded)
            else:
                self.active_coefficients = self.add_column_index(self.active_coefficients_untraded).T.stack(['supply_node','efficiency_type'])
                self.active_coefficients_total = self.add_column_index(self.active_coefficients_total_untraded).T.stack(['supply_node'])
            self.active_coefficients_total_emissions_rate = copy.deepcopy(self.active_coefficients_total)
            if cfg.rio_supply_run and hasattr(self,'rio_trades'):
                for geography_from in GeoMapper.geography_to_gau[GeoMapper.supply_primary_geography]:
                    for geography_to in GeoMapper.geography_to_gau[GeoMapper.supply_primary_geography]:
                        df = util.df_slice(self.rio_trades,[geography_from,year],[GeoMapper.supply_primary_geography,'year']).loc[:,geography_to]
                        idx = pd.IndexSlice
                        self.active_trade_adjustment_df.loc[idx[geography_from,:,:],idx[geography_to, :]] = df.sum()
                        if self.delivered_gen is not None:
                            for group in self.delivered_gen.groupby(level=[GeoMapper.supply_primary_geography+"_from",'supply_node']).groups.keys():
                                self.active_trade_adjustment_df.loc[idx[:, :, group[1]], :] = 0
                                self.active_trade_adjustment_df.loc[idx[group[0], :, group[1]], :] = 1
                        self.active_trade_adjustment_df.loc[idx[geography_from, :, :], idx[geography_to, :]] = df.sum()
            keys = ['not consumed']
            name = ['efficiency_type']
            active_trade_adjustment_df = pd.concat([self.active_trade_adjustment_df]*len(keys), keys=keys, names=name)
            self.active_coefficients_total = DfOper.mult([self.active_coefficients_total,self.active_trade_adjustment_df])
            self.active_coefficients = DfOper.mult([self.active_coefficients, active_trade_adjustment_df])
            keys = self.ghgs
            name = ['ghg']
            self.active_emissions_coefficients = pd.concat([self.active_coefficients]*len(keys), keys=keys, names=name)
            self.active_emissions_coefficients = self.active_emissions_coefficients.reorder_levels([GeoMapper.supply_primary_geography, 'demand_sector', 'supply_node', 'efficiency_type', 'ghg'])
            self.active_emissions_coefficients.sort(inplace=True)

    def calculate_levelized_costs(self, year, loop):
        "calculates total and per-unit costs in a subsector with technologies"
        if hasattr(self,'levelized_costs'):
            self.calculate_per_unit_costs(year)

    def calculate_per_unit_costs(self, year):
        total_costs = util.remove_df_levels(self.levelized_costs.loc[:, year].to_frame(),
                                            ['vintage', 'supply_technology'])
        active_supply = self.active_supply[self.active_supply.values >= 0]
        embodied_cost = DfOper.divi([total_costs, active_supply], expandable=(False, False)).replace(
            [np.inf, np.nan, -np.nan], [0, 0, 0])
        self.active_embodied_cost = util.expand_multi(embodied_cost[year].to_frame(),
                                                      levels_list=[GeoMapper.geography_to_gau[GeoMapper.supply_primary_geography],
                                                                   self.demand_sectors],
                                                      levels_names=[GeoMapper.supply_primary_geography, 'demand_sector'])

    def add_blend_measures(self, scenario):
            """
            add all blend measures in a selected scenario to a dictionary
            """
            self.blend_measures = {name: BlendMeasure(name, scenario)
                                   for name in scenario.get_measures('BlendNodeBlendMeasures', self.name)}

    def add_rio_fuel_blend_measures(self, rio_inputs):
            """
            add all blend measures in a selected scenario to a dictionary
            """
            if self.name in set(rio_inputs.zonal_fuel_outputs.index.get_level_values('blend')):
                df = rio_inputs.zonal_fuel_outputs
            else:
                df = rio_inputs.fuel_outputs
            df = util.df_slice(df,self.name,'blend')
            input_nodes = list(set(df.index.get_level_values('supply_node')))
            self.blend_measures = dict()
            for node in input_nodes:
                data =util.df_slice(df,node,'supply_node')
                self.blend_measures[node] = RioBlendMeasure(node,data)

    def add_rio_bulk_blend_measures(self,df):
            """
            add all blend measures in a selected scenario to a dictionary
            """
            input_nodes = list(set(df.index.get_level_values('supply_node')))
            for node in input_nodes:
                data =util.df_slice(df,node,'supply_node')
                self.blend_measures[node] = RioBlendMeasure(node,data)


    def add_rio_thermal_blend_measures(self, df):
            """
            add all blend measures in a selected scenario to a dictionary
            """
            input_nodes = list(set(df.index.get_level_values('supply_node')))
            self.blend_measures = dict()
            for node in input_nodes:
                data =util.df_slice(df,node,'supply_node')
                self.blend_measures[node] = RioBlendMeasure(node,data)


    def calculate(self,calculate_residual=True):
        #all nodes can have potential conversions. Set to None if no data. 
        self.conversion, self.resource_unit = self.add_conversion()  
        measures = []
        for measure in self.blend_measures.values():
            measure.calculate(self.vintages, self.years)
            measures.append(measure.values)
        if len(measures):
            self.raw_values = util.DfOper.add(measures)
            if calculate_residual:
                self.calculate_residual()
            else:
                self.calculate_no_residual()
        else:
            self.set_residual()
        self.set_adjustments()
        self.set_pass_through_df_dict()
        self.calculate_subclasses()

    def calculate_residual(self):
         """calculates values for residual node in Blend Node dataframe
         ex. if 10% of hydrogen blend is supplied by electrolysis and the rest is unspecified,
         90% of hydrogen blend is allocated to residual node
         """
         # calculates sum of all supply_nodes
         # residual equals 1-sum of all other specified nodes
         self.values = self.raw_values.sort_index()
         if 'demand_sector' in self.values.index.names:
            self.values = util.reindex_df_level_with_new_elements(self.values,'demand_sector',self.demand_sectors,0)
         if self.residual_supply_node in self.values.index.get_level_values('supply_node'):
             indexer = util.level_specific_indexer(self.values, 'supply_node', self.residual_supply_node)
             self.values.loc[indexer,:] = 0
         residual = 1-util.remove_df_levels(self.values,['supply_node'])
         residual['supply_node'] = self.residual_supply_node
         residual.set_index('supply_node', append=True, inplace=True)
#         residual = residual.reorder_levels(residual_levels+['supply_node'])
         # concatenate values
#         residual = residual.reorder_levels(self.values.index.names)
         self.values = pd.concat([self.values, residual], join='outer', axis=0)
         # remove duplicates where a node is specified and is specified as residual node
         self.values = self.values.groupby(level=self.values.index.names).sum()
         # set negative values to 0
         self.values.loc[self.values['value'] <= 0, 'value'] = 1e-10
         self.expand_blend()
         self.values = self.values.unstack(level='year')
         self.values.columns = self.values.columns.droplevel()

    def calculate_no_residual(self):
        """calculates values for residual node in Blend Node dataframe
        ex. if 10% of hydrogen blend is supplied by electrolysis and the rest is unspecified,
        90% of hydrogen blend is allocated to residual node
        """
        # calculates sum of all supply_nodes
        # residual equals 1-sum of all other specified nodes
        self.values = self.raw_values.sort_index()
        if 'demand_sector' in self.values.index.names:
            self.values = util.reindex_df_level_with_new_elements(self.values, 'demand_sector', self.demand_sectors, 0)
        self.values = self.values.groupby(level=self.values.index.names).sum()
        # set negative values to 0
        self.values.loc[self.values['value'] <= 0, 'value'] = 1e-10
        self.expand_blend()
        self.values = self.values.unstack(level='year')
        self.values.columns = self.values.columns.droplevel()

    def update_residual(self, year):
        """calculates values for residual node in Blend Node dataframe
         ex. if 10% of hydrogen blend is supplied by electrolysis and the rest is unspecified,
         90% of hydrogen blend is allocated to residual node
         """
        # calculates sum of all supply_nodes
        indexer = util.level_specific_indexer(self.values, 'supply_node', self.residual_supply_node)
        self.values.loc[indexer,year] = 0
        residual_levels = [x for x in self.values.index.names if x != 'supply_node']
        # residual equals 1-sum of all other specified nodes
        residual = 1-self.values.loc[:,year].to_frame().groupby(level=residual_levels).sum()
        residual['supply_node'] = self.residual_supply_node
        residual.set_index('supply_node', append=True, inplace=True)
        residual = residual.reorder_levels(residual_levels+['supply_node'])
        # concatenate values
        residual = residual.reorder_levels(self.values.index.names)
        self.values.loc[indexer,year] = residual
        # remove duplicates where a node is specified and is specified as residual node
        self.values.loc[:,year] = self.values.loc[:,year].groupby(level=self.values.index.names).sum()
        # set negative values to 0
        self.values[self.values <= 0] = 1e-10

    def set_to_min(self, year):
        """calculates values for residual node in Blend Node dataframe
         ex. if 10% of hydrogen blend is supplied by electrolysis and the rest is unspecified,
         90% of hydrogen blend is allocated to residual node
         """
        # calculates sum of all supply_node
        self.values[self.values <= 0] = 1e-10

    def expand_blend(self):
        #needs a fill value because if a node is not demanding any energy from another node, it still may be supplied, and reconciliation happens via division (can't multiply by 0)
        self.values = util.reindex_df_level_with_new_elements(self.values,'supply_node', self.nodes, fill_value = 1e-10)
        if 'demand_sector' not in self.values.index.names:
            self.values = util.expand_multi(self.values, self.demand_sectors, ['demand_sector'], incremental=True)
        self.values['efficiency_type'] = 'not consumed'
        self.values.set_index('efficiency_type', append=True, inplace=True)
        self.values = self.values.reorder_levels([GeoMapper.supply_primary_geography,'demand_sector','supply_node','efficiency_type','year'])
        self.values = self.values.sort_index()

    def set_residual(self):
        """creats an empty df with the value for the residual node of 1. For nodes with no blend measures specified"""
        df_index = pd.MultiIndex.from_product([GeoMapper.geography_to_gau[GeoMapper.supply_primary_geography], self.demand_sectors, self.nodes, self.years, ['not consumed']], names=[GeoMapper.supply_primary_geography, 'demand_sector','supply_node','year','efficiency_type' ])
        self.raw_values = util.empty_df(index=df_index,columns=['value'],fill_value=1e-10)
        indexer = util.level_specific_indexer(self.raw_values, 'supply_node', self.residual_supply_node)
        self.raw_values.loc[indexer, 'value'] = 1
        self.raw_values = self.raw_values.unstack(level='year')
        self.raw_values.columns = self.raw_values.columns.droplevel()
        self.raw_values = self.raw_values.sort_index()
        self.values = copy.deepcopy(self.raw_values)


class SupplyNode(Node, StockItem):
    def __init__(self, name, scenario):
        Node.__init__(self, name, scenario)
        StockItem.__init__(self)
        self.input_type = 'total'
        self.coefficients = SupplyCoefficients(self.name, self.scenario)
        self.potential = SupplyPotential(self.name, self.enforce_potential_constraint, self.scenario)
        self.capacity_factor = SupplyCapacityFactor(self.name, self.scenario)
        self.costs = {}
        self.create_costs()
        self.add_stock()

    def calculate(self):
        self.conversion, self.resource_unit = self.add_conversion()
        self.set_rollover_groups()
        self.calculate_subclasses()
        for cost in self.costs.values():
            cost.calculate(self.years, self.demand_sectors)
        self.calculate_stock_measures()
        self.add_case_stock()
        self.setup_stock_rollover(self.years)
        if self.coefficients.raw_values is not None:
            self.nodes = set(self.coefficients.values.index.get_level_values('supply_node'))
        self.set_adjustments()
        self.set_pass_through_df_dict()

    def set_rollover_groups(self):
        """sets the internal index for use in stock and cost calculations"""
        # determines whether stock rollover needs to occur on demand sector or resource bin index
        self.rollover_group_names = []
        self.rollover_group_levels = []
        if self.potential._has_data is True:
            for name, level in zip(self.potential.raw_values.index.names, self.potential.raw_values.index.levels):
                if (name == 'resource_bin' or name == 'demand_sector') and name not in self.rollover_group_names:
                        if name == 'demand_sector':
                            level = self.demand_sectors
                        self.rollover_group_levels.append(list(level))
                        self.rollover_group_names.append(name)
        if self.stock._has_data is True:
            for name, level in zip(self.stock.raw_values.index.names, self.stock.raw_values.index.levels):
                if (name == 'resource_bin' or name == 'demand_sector') and name not in self.rollover_group_names:
                    if name == 'demand_sector':
                        level = self.demand_sectors
                    self.rollover_group_levels.append(list(level))
                    self.rollover_group_names.append(name)
        for cost in self.costs.keys():
            for name, level in zip(self.costs[cost].raw_values.index.names, self.costs[cost].raw_values.index.levels):
                if (name == 'resource_bin' or name == 'demand_sector') and name not in self.rollover_group_names:
                    if name == 'demand_sector':
                        level = self.demand_sectors
                    self.rollover_group_levels.append(list(level))
                    self.rollover_group_names.append(name)
        if self.name == self.distribution_grid_node_name and 'demand_sector' not in self.rollover_group_names:
            #requires distribution grid node to maintain demand sector resolution in its stocks
            self.rollover_group_levels.append(self.demand_sectors)
            self.rollover_group_names.append('demand_sector')
        self.rollover_group_names = [GeoMapper.supply_primary_geography] + self.rollover_group_names
        self.rollover_group_levels = [GeoMapper.geography_to_gau[GeoMapper.supply_primary_geography]] + self.rollover_group_levels

    def add_stock(self):
        """add stock instance to node"""
        self.stock = SupplyStock(supply_node=self.name, scenario=self.scenario)
        self.stock.unit = cfg.calculation_energy_unit + "/" + cfg.getParam('time_step')

    def add_case_stock(self):
       self.case_stock = StockItem()
#       total_stocks = []
#       for stock in self.total_stocks:
#           total_stocks.append(stock)
       if len(self.total_stocks):
            self.case_stock._has_data = True
            self.case_stock.total = DfOper.add([ x.values for x in self.total_stocks.values()], expandable=False)
#            self.case_stock.total[self.case_stock.total.index.get_level_values('year')<cfg.getParamAsInt('current_year')+1] = np.nan

    def calculate_stock_measures(self):
        for stock in self.total_stocks.values():
            stock.calculate(self.vintages,self.years)
            stock.convert()

    def calculate_input_stock(self):
        self.stock.years = self.years
        if self.stock._has_data is True:
            self.stock.remap(map_from='raw_values', map_to='total', converted_geography=GeoMapper.supply_primary_geography, fill_timeseries=True,fill_value=np.nan)
            self.convert_stock('stock','total')
            self.stock.total = util.remove_df_levels(self.stock.total,'supply_technology')
#        if hasattr(self.case_stock,'total'):
#            self.case_stock.remap(map_from='raw_values', map_to='total', converted_geography=GeoMapper.supply_primary_geography, fill_timeseries=True, fill_value=np.nan)
        if self.stock._has_data is True and hasattr(self.case_stock,'total'):
            self.convert_stock('case_stock','total')
#           self.case_stock.total.fillna(self.stock.total, inplace=True)
            self.stock.total = self.stock.total[self.stock.total.index.get_level_values('year')<=cfg.getParamAsInt('current_year')]
            self.case_stock.total[self.stock.total.index.get_level_values('year')>cfg.getParamAsInt('current_year')]
            self.case_stock.total = pd.concat([self.stock.total,self.case_stock.total])
            self
        elif self.stock._has_data is False and hasattr(self.case_stock,'total'):
            self.stock = self.case_stock
        elif self.stock._has_data is False and not hasattr(self.case_stock,'total'):
            index = pd.MultiIndex.from_product(self.rollover_group_levels + [self.years] ,names=self.rollover_group_names + ['year'] )
            self.stock.total = util.empty_df(index=index,columns=['value'],fill_value=np.nan)
        self.stock.total_rollover = copy.deepcopy(self.stock.total)
        self.stock.total = self.stock.total.unstack('year')
        self.stock.total.columns = self.stock.total.columns.droplevel()
        if self.stock._has_data or hasattr(self.case_stock,'data') and self.case_stock._has_data == True:
            self.stock._has_data = True

    def calc_node_survival_function(self):
            self.set_survival_parameters()
            self.set_survival_vintaged()
            self.set_decay_vintaged()
            self.set_decay_initial_stock()
            self.set_survival_initial_stock()

    def create_node_survival_functions(self):
        functions = defaultdict(list)
        for fun in ['survival_vintaged', 'survival_initial_stock', 'decay_vintaged', 'decay_initial_stock']:
                functions[fun].append(getattr(self, fun))
                setattr(self.stock, fun, pd.DataFrame(np.array(functions[fun]).T, columns=[self.name]))

    def create_node_rollover_markov_matrices(self):
        vintaged_markov = util.create_markov_vector(self.stock.decay_vintaged.values, self.stock.survival_vintaged.values)
        self.stock.vintaged_markov_matrix = util.create_markov_matrix(vintaged_markov, 1, len(self.years))
        initial_markov = util.create_markov_vector(self.stock.decay_initial_stock.values, self.stock.survival_initial_stock.values)
        self.stock.initial_markov_matrix = util.create_markov_matrix(initial_markov, 1, len(self.years))

    def setup_stock_rollover(self, years):
        """ Stock rollover function for an entire supply node"""
        #prep stock rollover for initial solve
        self.vintages = self.years
        self.calc_node_survival_function()
        self.create_node_survival_functions()
        self.create_node_rollover_markov_matrices()
        self.calculate_input_stock()
        self.ensure_capacity_factor()
        levels = self.rollover_group_levels
        names = self.rollover_group_names
        index = pd.MultiIndex.from_product(levels, names=names)
        columns = self.years
        self.stock.requirement = util.empty_df(index=index, columns=pd.Index(columns, dtype='object'))
        self.stock.requirement_energy = util.empty_df(index=index, columns=pd.Index(columns, dtype='object'))
        if len(names)>1:
            self.rollover_groups = self.stock.total.groupby(level=names).groups
        else:
            #TODO Ryan List Comprehension
            item_list = levels[0]
            self.rollover_groups = dict()
            for x in item_list:
                self.rollover_groups[(x,)] = (x,)
        full_levels = self.rollover_group_levels + [[self.vintages[0] - 1] + self.vintages]
        full_names = self.rollover_group_names + ['vintage']
        index = pd.MultiIndex.from_product(full_levels, names=full_names)
        self.stock.values = util.empty_df(index=index, columns=pd.Index(columns, dtype='object'))
        self.stock.values_energy = util.empty_df(index=index, columns=pd.Index(columns, dtype='object'))
        self.stock.remaining = util.empty_df(index=index, columns=pd.Index(columns, dtype='object'))
        self.stock.values_financial = util.empty_df(index=index, columns=pd.Index(columns, dtype='object'))
        self.stock.values_financial_energy = util.empty_df(index=index, columns=pd.Index(columns, dtype='object'))
        full_levels = self.rollover_group_levels + [self.vintages]
        index = pd.MultiIndex.from_product(full_levels, names=full_names)
        self.stock.retirements = util.empty_df(index=index, columns= self.years)
        self.stock.sales = util.empty_df(index=index, columns=['value'])
        self.stock.sales_energy = util.empty_df(index=index, columns=['value'])
        self.rollover_dict = {}
        self.total_stock = self.stock.total.stack(dropna=False)
        self.setup_financial_stock()
        for elements in self.rollover_groups.keys():
            elements = util.ensure_tuple(elements)
            total_stock = self.stock.total_rollover.loc[elements].values
            self.rollover_dict[elements] = Rollover(vintaged_markov_matrix=self.stock.vintaged_markov_matrix,
                                     initial_markov_matrix=self.stock.initial_markov_matrix,
                                     num_years=len(years), num_vintages=len(years),
                                     num_techs=1, initial_stock=total_stock[0],
                                     sales_share=None, stock_changes=None,
                                     specified_stock=total_stock, specified_retirements=None,stock_changes_as_min=True)

        for year in [x for x in self.years if x<cfg.getParamAsInt('current_year')]:
            for elements in self.rollover_groups.keys():
                elements = util.ensure_tuple(elements)
                try:
                    self.rollover_dict[elements].run(1)
                except:
                    logging.error('error encountered in rollover for node ' + str(self.name) + ' in elements '+ str(elements) + ' year ' + str(year))
                    raise
                stock_total, stock_new, stock_replacement, retirements, retirements_natural, retirements_early, sales_record, sales_new, sales_replacement = self.rollover_dict[(elements)].return_formatted_outputs(year_offset=0)
                self.stock.values.loc[elements,year] = stock_total
                sales_indexer = elements + (year,)
                self.stock.sales.loc[sales_indexer, 'value'] = sales_record
#                self.stock.retirements.loc[sales_indexer,year] = retirements
            self.financial_stock(year)
            self.calculate_energy(year)

    def ensure_capacity_factor(self):
        index = pd.MultiIndex.from_product(self.rollover_group_levels, names=self.rollover_group_names)
        columns = self.years
        df = util.empty_df(index=index, columns=pd.Index(columns, dtype='object'),fill_value=1.0)
        if self.capacity_factor._has_data is True:
            self.capacity_factor.values = DfOper.mult([df,self.capacity_factor.values])
        else:
            self.capacity_factor.values = df

    def calculate_dispatch_costs(self, year, embodied_cost_df, loop=None):
        self.active_dispatch_costs = copy.deepcopy(self.active_trade_adjustment_df)
        for node in self.active_trade_adjustment_df.index.get_level_values('supply_node'):
            embodied_cost_indexer = util.level_specific_indexer(embodied_cost_df, 'supply_node',node)
            trade_adjustment_indexer = util.level_specific_indexer(self.active_trade_adjustment_df, 'supply_node',node)
            self.active_dispatch_costs.loc[trade_adjustment_indexer,:] = util.DfOper.mult([self.active_trade_adjustment_df.loc[trade_adjustment_indexer,:],embodied_cost_df.loc[embodied_cost_indexer,:]]).values
        self.active_dispatch_costs = self.active_dispatch_costs.groupby(level='supply_node').sum()
        self.active_dispatch_costs = self.active_dispatch_costs.stack([GeoMapper.supply_primary_geography,'demand_sector'])
        self.active_dispatch_costs *= self.active_coefficients_total
        self.active_dispatch_costs = util.reduce_levels(self.active_dispatch_costs, self.rollover_group_names, agg_function='mean')
        self.active_dispatch_costs = DfOper.mult([self.active_dispatch_costs, self.active_dispatch_coefficients])
        self.active_dispatch_costs = util.remove_df_levels(self.active_dispatch_costs, 'supply_node')
        self.active_dispatch_costs = self.active_dispatch_costs.reorder_levels(self.stock.values.index.names)
        self.active_dispatch_costs[self.active_dispatch_costs<0] = 0

    def stock_rollover(self, year, loop, stock_changes):
        """stock rollover function that is used for years after the IO has been initiated"""
        #if the stock rollover's first year is also the first year of the IO loop, we set the initial stock
        #equal to the first year's stock requirement. This insures propoer rolloff of th existing stock
        if min(self.years) == year:
            for elements in self.rollover_groups.keys():
                elements = util.ensure_tuple(elements)
                self.rollover_dict[elements].initial_stock = np.array(util.ensure_iterable(self.stock.requirement.loc[elements, year]))
        #run the stock rollover for the year and record values
        for elements in self.rollover_groups.keys():
            elements = util.ensure_tuple(elements)
            try:
                self.rollover_dict[elements].use_stock_changes = True
                self.rollover_dict[elements].run(1, stock_changes.loc[elements], np.array(self.stock.total_rollover.loc[elements+(year,)]))
            except:
                logging.error('error encountered in rollover for node ' + str(self.name) + ' in elements '+ str(elements) + ' year ' + str(year))
                raise
            stock_total, stock_new, stock_replacement, retirements, retirements_natural, retirements_early, sales_record, sales_new, sales_replacement = self.rollover_dict[(elements)].return_formatted_outputs(year_offset=0)
            self.stock.values.loc[elements,year] = stock_total
            sales_indexer = elements + (year,)
            self.stock.sales.loc[sales_indexer, 'value'] = sales_record
#            self.stock.retirements[sales_indexer, year] = retirements

        self.financial_stock(year)
        self.calculate_energy(year)

    def setup_financial_stock(self):
            # creates binary matrix across years and vintages for a technology based on its book life
            self.book_life_matrix = util.book_life_df(self.book_life, self.vintages, self.years)
            # creates a linear decay of initial stock
            self.initial_book_life_matrix = util.initial_book_life_df(self.book_life, self.mean_lifetime, self.vintages, self.years)

    def calculate_energy(self, year):
        self.stock.values_energy[year] = DfOper.mult([self.stock.values[year].to_frame(), self.capacity_factor.values[year].to_frame()])* UnitConverter.unit_convert(unit_from_den=cfg.getParam('time_step'), unit_to_den='year')
        indexer = util.level_specific_indexer(self.stock.sales,'vintage', year)
        self.stock.sales_energy.loc[indexer,:] = DfOper.mult([self.stock.sales.loc[indexer,:], self.capacity_factor.values[year].to_frame()])* UnitConverter.unit_convert(unit_from_den=cfg.getParam('time_step'), unit_to_den='year')

    def financial_stock(self, year):
        """
        Calculates the amount of stock based on sales and book life
        instead of physical decay
        """
        # stock values in any year equals vintage sales multiplied by book life
        start_year = min(self.years)
        values_financial = util.DfOper.mult([self.stock.sales, self.book_life_matrix[year].to_frame()])
        indexer = util.level_specific_indexer(self.stock.values,'vintage',start_year-1)
        starting_financial_stock = self.stock.values.loc[indexer,start_year].to_frame()
        starting_financial_stock.columns = [year]
        initial_values_financial = util.DfOper.mult([starting_financial_stock, self.initial_book_life_matrix[year].to_frame()])
        # sum normal and initial stock values
        self.stock.values_financial[year] = util.DfOper.add([values_financial, initial_values_financial[year].to_frame()],non_expandable_levels=None)
        self.stock.values_financial_energy[year] = DfOper.mult([self.stock.values_financial[year].to_frame(), self.capacity_factor.values[year].to_frame()])* UnitConverter.unit_convert(unit_from_den=cfg.getParam('time_step'), unit_to_den='year')

    def calculate_active_coefficients(self,year, loop):
        """calculates the active coefficients"""
        #If a node has no potential data, then it doesn't have a supply curve. Therefore the coefficients are just the specified inputs in that year
        if year == cfg.getParamAsInt('current_year') and loop == 'initial':
            #in the initial loop of the supply-side, we only know internal demand
            throughput = self.active_demand
        else:
            #after that, our best representation of throughput is active supply, which is updated in every IO loop
            throughput = self.active_supply
        #in the first loop we take a slice of the input node efficiency
        if self.potential._has_data is False:
            #if the node has no potential data, and therefore no supply curve
            if self.coefficients._has_data is True:
                #we take the coefficients for the current year
                self.active_coefficients = self.coefficients.values.loc[:,year].to_frame()
            else:
                self.active_coefficients = None
                self.active_coefficients_total = None
        elif self.coefficients._has_data is True:
            if self.potential.raw_values is not None:
              self.potential.remap_to_potential_and_normalize(throughput, year, self.tradable_geography)
              filter_geo_potential_normal = self.potential.active_supply_curve_normal
              filter_geo_potential_normal = filter_geo_potential_normal.reset_index().set_index(filter_geo_potential_normal.index.names)
              self.active_coefficients = util.remove_df_levels(util.DfOper.mult([self.coefficients.values.loc[:,year].to_frame(),
                                                    filter_geo_potential_normal],
                                                    (True,True),(False,False)),'resource_bin')
            else:
                stock_normal = self.stock.values.loc[:,year].to_frame().groupby(level=util.ix_excl(self.stock.values,['resource_bin'])).transform(lambda x: x/x.sum())
                self.active_coefficients = DfOper.mult([self.coefficients.values.loc[:,year].to_frame(), stock_normal])
                self.active_coefficients.sort(inplace=True)
        else:
            self.active_coefficients = None
            self.active_coefficients_total = None
            self.active_emissions_coefficients = None
        #we multiply the active coefficients by the trade adjustments to account for inter-geography trades
        if self.active_coefficients is not None:
            self.active_coefficients_total_untraded = util.remove_df_levels(self.active_coefficients,'efficiency_type')
            self.active_coefficients_total = DfOper.mult([self.add_column_index(self.active_coefficients_total_untraded), self.active_trade_adjustment_df])
            self.active_coefficients_untraded = copy.deepcopy(self.active_coefficients)
            self.active_coefficients_untraded.sort(inplace=True,axis=0)
            nodes = list(set(self.active_trade_adjustment_df.index.get_level_values('supply_node')))
            df_list = []
            for node in nodes:
                trade_indexer = util.level_specific_indexer(self.active_trade_adjustment_df, 'supply_node', node)
              #  coefficient_indexer = util.level_specific_indexer(self.active_coefficients_untraded.sort_index(), 'supply_node', node)
                efficiency_types = list(set(util.df_slice(self.active_coefficients_untraded, node, 'supply_node').index.get_level_values('efficiency_type')))
                keys = efficiency_types
                name = ['efficiency_type']
                df = pd.concat([self.active_trade_adjustment_df.loc[trade_indexer,:]]*len(keys),keys=keys,names=name)
                df_list.append(df)
            active_trade_adjustment_df = pd.concat(df_list)
#            active_trade_adjustment_df = self.active_trade_adjustment_df.reindex(index = self.active_coefficients_untraded.index,method='bfill')
            self.active_coefficients = DfOper.mult([self.add_column_index(self.active_coefficients_untraded),active_trade_adjustment_df])
            keys = self.ghgs
            name = ['ghg']
            self.active_emissions_coefficients = pd.concat([self.active_coefficients]*len(keys), keys=keys, names=name)
            self.active_emissions_coefficients = self.active_emissions_coefficients.reorder_levels([GeoMapper.supply_primary_geography,'demand_sector', 'supply_node', 'efficiency_type', 'ghg'])
            self.active_emissions_coefficients.sort(inplace=True)

    def update_stock(self, year, loop):
        """updates the stock in the IO loop"""
        self.determine_throughput(year,loop)
        self.update_remaining_stock(year, loop)
        self.update_total(year)
        self.update_requirement(year)
        self.stock_rollover(year, loop, self.stock.act_stock_changes)

    def determine_throughput(self,year,loop):
        """determines the throughput requirement of the node"""
        if year == cfg.getParamAsInt('current_year') and loop == 'initial':
            #in the initial loop of the supply-side, we only know internal demand
            self.throughput = self.active_demand
        else:
            self.throughput = self.active_supply
        if  self.throughput is not None:
            self.throughput = self.throughput.groupby(level=util.ix_incl(self.throughput, self.rollover_group_names)).sum()
            self.throughput[self.throughput<0]=0

    def update_remaining_stock(self,year, loop):
        """calculates the amount of energy throughput from remaining stock (after natural rollover from the previous year)"""
        for elements in self.rollover_groups.keys():
            elements = util.ensure_tuple(elements)
            element_indexer= util.level_specific_indexer(self.stock.remaining, self.rollover_group_names,elements)
            if year == cfg.getParamAsInt('current_year') and loop == 'initial':
                self.stock.remaining.loc[element_indexer, year] = self.rollover_dict[elements].return_formatted_stock(year_offset=1)
            elif year == cfg.getParamAsInt('current_year') and loop == 1:
                self.rollover_dict[elements].rewind(1)
                self.stock.remaining.loc[element_indexer, year] = self.rollover_dict[elements].return_formatted_stock(year_offset=1)
            elif loop == 1:
                self.stock.remaining.loc[element_indexer, year] = self.rollover_dict[elements].return_formatted_stock(year_offset=1)
            else:
                self.rollover_dict[elements].rewind(1)
        self.stock.act_rem_energy = util.DfOper.mult([self.stock.remaining.loc[:,year].to_frame(), self.capacity_factor.values.loc[:,year].to_frame()]) * UnitConverter.unit_convert(unit_from_den=cfg.getParam('time_step'), unit_to_den='year')
        default_conversion = self.capacity_factor.values.loc[:,year].to_frame() * UnitConverter.unit_convert(unit_from_num='year',unit_to_num=cfg.getParam('time_step'))
        self.stock.act_energy_capacity_ratio = util.DfOper.divi([self.stock.act_rem_energy.groupby(level=util.ix_excl(self.stock.act_rem_energy,['vintage'])).sum(),
                                    self.stock.remaining.loc[:, year].to_frame().groupby(level=util.ix_excl(self.stock.remaining, ['vintage'])).sum()]).fillna(default_conversion)
        self.stock.act_energy_capacity_ratio[self.stock.act_energy_capacity_ratio==0]= UnitConverter.unit_convert(unit_from_num='year',unit_to_num=cfg.getParam('time_step'))

    def update_total(self, year):
        """sets the minimum necessary total stock - based on throughput (stock requirement) and total of the specified and remaining stock"""
        self.stock.act_total_energy = util.DfOper.mult([self.stock.total.loc[:,year].to_frame(), self.stock.act_energy_capacity_ratio],fill_value=np.nan)
        self.stock.act_total_energy = self.stock.act_total_energy.fillna(util.remove_df_levels(self.stock.act_rem_energy,'vintage'))

    def update_requirement(self,year):
        """updates annual stock requirements with the maximum of required stock and specified and remaining natural rolloff. Also
        distributes the necessary stock changes to the available residuals in the supply curve bins if the stock has resource_bin indexers
        """
        previous_year = max(min(self.years),year-1)

        if self.potential._has_data is False:
            if self.throughput is not None:
                self.stock.requirement_energy.loc[:,year] = self.throughput
            a = self.stock.requirement_energy.loc[:,year].to_frame()
            b = self.stock.act_total_energy
            a[a<b] = b
            self.stock.requirement_energy.loc[:,year] = a
            self.stock.requirement.loc[:,year] = DfOper.divi([self.stock.requirement_energy.loc[:,year].to_frame(),self.stock.act_energy_capacity_ratio]).fillna(0)
        else:
                        #calculates the total amount of energy needed to distribute
            total_residual = util.DfOper.subt([self.throughput, self.stock.act_total_energy],expandable=(False,False), collapsible=(True,True))
            total_residual[total_residual<0] = 0
            #calculates the residual amount of energy available in each bin
            bins = util.DfOper.subt([self.potential.values.loc[:, year].to_frame(), self.stock.act_total_energy],expandable=(False,False), collapsible=(True,True))
            bins[bins<0] = 0
            #calculates the supply curve of remaining energy
            bin_supply_curve = bins.groupby(level=[x for x in self.rollover_group_names if x!= 'resource_bin']).cumsum()
            #expands the total energy needed to distribute to mask against the supply curve. Used as a cap on the supply curve.
            total_residual = util.expand_multi(total_residual,bins.index.levels,bins.index.names)
            bin_supply_curve[bin_supply_curve>total_residual] = total_residual
            bin_supply_curve = bin_supply_curve.groupby(level=util.ix_excl(bin_supply_curve,'resource_bin')).diff().fillna(bin_supply_curve)
            self.stock.requirement_energy.loc[:,year] = util.DfOper.add([self.stock.act_total_energy, bin_supply_curve])
            self.stock.requirement.loc[:,year] = util.DfOper.divi([self.stock.requirement_energy.loc[:,year].to_frame(),self.stock.act_energy_capacity_ratio])

        if year == cfg.getParamAsInt('current_year') and year==min(self.years):
            self.stock.act_stock_changes = self.stock.requirement[year]*0
        else:
            self.stock.act_stock_changes = util.DfOper.subt([self.stock.requirement[year].to_frame(), util.remove_df_levels(self.stock.values[previous_year].to_frame(),['vintage'])])[year]

    def calculate_oversupply(self, year, loop):
        """calculates whether the stock would oversupply the IO requirement and returns an oversupply adjustment factor."""
        if hasattr(self,'stock'):
            oversupply_factor = util.DfOper.divi([self.stock.values_energy.loc[:,year].to_frame(), self.throughput], expandable=(False,False), collapsible=(True,True)).fillna(1)
            oversupply_factor.replace(np.inf,1,inplace=True)
            oversupply_factor[oversupply_factor<1] = 1
            if (oversupply_factor.values>1).any():
                return oversupply_factor
            else:
                return None
        else:
            return None

    def adjust_energy(self,oversupply_factor,year):
#        self.capacity_factor.values.loc[:,year] = util.DfOper.mult([self.capacity_factor.values.loc[:,year].to_frame(),1/oversupply_factor])
        self.stock.values_energy.loc[:,year] = util.DfOper.mult([self.stock.values_energy.loc[:,year].to_frame(),1/oversupply_factor])

    def create_costs(self):
        names = util.csv_read_table('SupplyCost', column_names='name', supply_node=self.name, return_iterable=True)
        for name in names:
            self.add_costs(name)

    def add_costs(self, name):
        """
        add cost object to a supply stock node

        """
        if name in self.costs:
            logging.debug("supply cost {} was added twice for node".format(name, self.name))
            return
        else:
            self.costs[name] = SupplyCost(name, self.cost_of_capital, self.scenario)

    def calculate_costs(self, year, loop, transmission_node_name, dispatch_tx_costs, dispatch_tx_constraints):
        start_year = min(self.years)
        if not hasattr(self, 'levelized_costs'):
            index = pd.MultiIndex.from_product(self.rollover_group_levels, names=self.rollover_group_names)
            self.levelized_costs = util.empty_df(index, columns=self.years, fill_value=0.)
            self.embodied_cost = util.empty_df(index, columns=self.years, fill_value=0.)
            self.embodied_cost = util.remove_df_levels(self.embodied_cost, 'resource_bin')
        if not hasattr(self, 'annual_costs'):
            index = self.stock.sales.index
            self.annual_costs = util.empty_df(index, columns=['value'], fill_value=0.)
        self.levelized_costs[year] = 0
        for cost in self.costs.values():
            rev_req = util.DfOper.add([self.calculate_dynamic_supply_costs(cost, year, start_year), self.calculate_static_supply_costs(cost, year, start_year)])
            self.levelized_costs.loc[:,year] += rev_req.values.flatten()
            self.calculate_lump_costs(year, rev_req)
            cost.prev_yr_rev_req = rev_req
        self.embodied_cost.loc[:, year] = util.DfOper.divi([self.levelized_costs[year].to_frame(), self.throughput], expandable=(False, False)).replace([np.inf, -np.inf, np.nan, -np.nan], [0, 0, 0, 0]).values
        if self.name == transmission_node_name and cfg.transmission_constraint is not None:
            if dispatch_tx_costs.cost_incremental:
                capacity = util.DfOper.subt([util.df_slice(dispatch_tx_constraints.values, year, 'year'),
                                             util.df_slice(dispatch_tx_constraints.values, min(dispatch_tx_constraints.values.index.get_level_values('year')), 'year')])
            else:
                capacity = util.df_slice(dispatch_tx_constraints.values, year, 'year')
            levelized_tx_costs = util.DfOper.mult([util.df_slice(dispatch_tx_costs.values_level, year, 'year'), capacity]).groupby(level='gau_from').sum()
            util.replace_index_name(levelized_tx_costs, GeoMapper.supply_primary_geography, 'gau_from')
            embodied_tx_costs = util.DfOper.divi([levelized_tx_costs, self.throughput])
            self.embodied_cost.loc[:, year] += embodied_tx_costs.values.flatten()
        self.active_embodied_cost = util.expand_multi(self.embodied_cost[year].to_frame(), levels_list=[GeoMapper.geography_to_gau[GeoMapper.supply_primary_geography], self.demand_sectors], levels_names=[GeoMapper.supply_primary_geography, 'demand_sector'])

    def calculate_dynamic_supply_costs(self, cost,year,start_year):
        "returns a revenue requirement for the component of costs that is correlated with throughput"
        if cost._has_data is True:
            #determine increased tariffs due to growth rate (financial/physical stock rati0)
            limited_names = self.rollover_group_names if len(self.rollover_group_names) > 1 else self.rollover_group_names[0]
            first_yr_financial_stock = self.stock.values_financial.groupby(level=limited_names).sum()[start_year].to_frame()
            first_yr_stock = self.stock.values.groupby(level= limited_names).sum()[start_year].to_frame()
            financial_stock = self.stock.values_financial.groupby(level= limited_names).sum()[year].to_frame()
            stock = self.stock.values.groupby(level= limited_names).sum()[year].to_frame()
            first_yr_energy = self.stock.values_energy.groupby(level=limited_names).sum()[start_year].to_frame()
            ini_growth_ratio = util.DfOper.divi([first_yr_stock,first_yr_financial_stock]).replace([np.inf,-np.inf],0)
            growth_ratio = util.DfOper.divi([stock, financial_stock]).replace([np.inf,-np.inf],0)
            growth_mult = util.DfOper.divi([ini_growth_ratio,growth_ratio]).replace([np.nan,-np.inf,np.inf],1)
            stock_energy = self.stock.values_energy.groupby(level= limited_names).sum()[year].to_frame()
            flow = self.active_supply.groupby(level= limited_names).sum()[year].to_frame()
            cap_factor_mult = util.DfOper.divi([stock_energy,flow]).replace([np.nan,-np.inf,np.inf],1)
            if cost.supply_cost_type == 'tariff':
                tariff = cost.values_level_no_vintage[year].to_frame()
                if cost.capacity is True:
                    rev_req = util.DfOper.mult([tariff,stock],expandable=(False,False))[year].to_frame()
                    if cost.is_capital_cost:
                        return rev_req * cost.throughput_correlation
                    else:
                        return rev_req* cost.throughput_correlation
                else:
                    stock_energy = self.stock.values_energy.groupby(level= limited_names).sum()[year].to_frame()
                    flow = self.active_supply.groupby(level= limited_names).sum()[year].to_frame()
                    cap_factor_mult = util.DfOper.mult([util.DfOper.divi([stock_energy,flow]).replace([np.nan,-np.inf,np.inf],1), util.DfOper.divi([self.capacity_factor.values[start_year].to_frame(),self.capacity_factor.values[year].to_frame()]).replace([np.nan,-np.inf,np.inf],1)])
                    rev_req = util.DfOper.mult([tariff,self.active_supply],expandable=(False,False))[year].to_frame()
                    if len(rev_req.index.names)==1:
                        rev_names = rev_req.index.names[0]
                    else:
                        rev_names = rev_req.index.names
                    rev_req = util.DfOper.mult([rev_req,financial_stock.groupby(level=rev_names).transform(lambda x: x/x.sum())]).replace([np.inf,-np.inf],0)
                    if cost.is_capital_cost:
                        return util.DfOper.mult([rev_req,cap_factor_mult]) * cost.throughput_correlation
                    else:
                        return util.DfOper.mult([rev_req,cap_factor_mult]) * cost.throughput_correlation
            elif cost.supply_cost_type == 'revenue requirement':
                    rev_req = cost.values_level_no_vintage[start_year].to_frame()
                    tariff = util.DfOper.divi([rev_req,first_yr_energy]).replace([np.nan,-np.inf,np.inf],1)
                    tariff.columns = [year]
                    rev_req = util.DfOper.mult([tariff,self.active_supply],expandable=(False,False))[year].to_frame()
                    stock_energy = self.stock.values_energy.groupby(level= limited_names).sum()[year].to_frame()
                    flow = self.active_supply.groupby(level= limited_names).sum()[year].to_frame()
                    cap_factor_mult = util.DfOper.divi([stock_energy,flow]).replace([np.nan,-np.inf,np.inf],1)
                    return util.DfOper.mult([rev_req,cap_factor_mult]) * cost.throughput_correlation
            else:
                raise ValueError("investment cost types not implemented")


    def calculate_static_supply_costs(self,cost,year,start_year):
       "returns a revenue requirement for the component of costs that is not correlated with throughput"
       first_yr_stock = self.stock.values.groupby(level= self.rollover_group_names).sum()[start_year].to_frame()
       first_yr_energy = self.stock.values_energy.groupby(level=self.rollover_group_names).sum()[start_year].to_frame()
       if cost.supply_cost_type == 'tariff':
            tariff = cost.values_level_no_vintage[year].to_frame()
            if cost.capacity is True:
                rev_req = util.DfOper.mult([tariff,first_yr_stock],expandable=(True,False))[year].to_frame()
            else:
                rev_req = util.DfOper.mult([tariff,first_yr_energy],expandable=(True,False))[year].to_frame()
       elif cost.supply_cost_type == 'revenue requirement':
            rev_req = cost.values_level_no_vintage[year].to_frame()
       return rev_req * (1- cost.throughput_correlation)


    def calculate_lump_costs(self,year, rev_req):
            start_year = min(self.years)
            indexer = util.level_specific_indexer(self.annual_costs,'vintage',year)
            self.annual_costs.loc[indexer,:] = 0
            for cost in self.costs.values():
                if cost.raw_values is not None:
                    financial_stock = self.stock.values_financial.groupby(level= self.rollover_group_names).sum()[year].to_frame()
                    if cost.is_capital_cost:
                        if year == start_year:
                            annual_costs = rev_req/(cost.book_life)
                        else:
                            rem_rev_req = cost.prev_yr_rev_req * (1 - 1/self.book_life)
                            new_rev_req = util.DfOper.subt([rev_req,rem_rev_req])
                            annual_costs = new_rev_req * cost.book_life
                            sales = util.df_slice(self.stock.sales,start_year,'vintage')
                            sales.columns = [start_year]
                            ratio =  util.DfOper.divi([sales,financial_stock]).replace([np.nan,-np.inf,np.inf],0)
                            annual_costs = util.DfOper.mult([ratio, rev_req])
                        indexer = util.level_specific_indexer(self.annual_costs,'vintage',year)
                        self.annual_costs.loc[indexer,:] += annual_costs.values
                    else:
                        pass



    def calculate_capacity_utilization(self, energy_supply, supply_years):
        energy_stock = self.stock.values[supply_years] * UnitConverter.unit_convert(1,unit_from_den='hour', unit_to_den='year')
        self.capacity_utilization = util.DfOper.divi([energy_supply,energy_stock],expandable=False).replace([np.inf,np.nan,-np.nan],[0,0,0])


class SupplyCapacityFactor(schema.SupplyCapacityFactor):
    def __init__(self, supply_node, scenario):
        super(SupplyCapacityFactor, self).__init__(supply_node, scenario=scenario)
        self.init_from_db(supply_node, scenario)
        self.input_type = 'intensity'
        self.scenario = scenario

    def calculate(self, years, demand_sectors):
        self.years = years
        self.demand_sectors = demand_sectors
        if self._has_data:
            self.remap(converted_geography=GeoMapper.supply_primary_geography)
#            self.convert()
            self.values = self.values.unstack('year')
            self.values.columns = self.values.columns.droplevel()


class SupplyPotential(schema.SupplyPotential):
    def __init__(self, name, enforce_potential_constraint, scenario):
        super(SupplyPotential, self).__init__(name, scenario=scenario)
        self.init_from_db(name, scenario)
        self.input_type = 'total'
        self.enforce_potential_constraint = enforce_potential_constraint
        self.scenario = scenario


    def calculate(self, conversion, resource_unit):
        if self._has_data:
            self.conversion = conversion
            self.resource_unit=resource_unit
            self.remap(filter_geo=False, converted_geography=GeoMapper.supply_primary_geography)
            if self.enforce_potential_constraint!=True:
                self.values = self.values[self.values.values>0]
                max_bin = np.asarray(list(set(self.values.index.get_level_values('resource_bin')))).max()
                indexer = util.level_specific_indexer(self.values,'resource_bin',max_bin)
                self.values.loc[indexer,:] = self.values.loc[indexer,:] * 1E6
            self.convert()

    def convert(self):
        self.values = self.values.unstack(level='year')
        self.values.columns = self.values.columns.droplevel()
        if hasattr(self,'time_unit') and self.time_unit is None:
            self.time_unit = 'year'
        if self.conversion is not None:
            # if a conversion is necessary, it means that original input values are in resource and not energy terms
            # this means that they must be copied to resource values and values are the result of
            # multiplying the original values by the conversion dataframe
            self.values = DfOper.mult([self.values, self.conversion.values],fill_value=self.conversion.values.mean().mean())
            self.supply_curve = self.values
        else:
            if UnitConverter.is_energy_unit(self.unit):
                self.values = UnitConverter.unit_convert(self.values, unit_from_num=self.unit, unit_from_den=self.time_unit, unit_to_num=cfg.calculation_energy_unit, unit_to_den='year')
            else:
                raise ValueError('unit is not an energy unit and no resource conversion has been entered in node %s' %self.name)
            self.supply_curve = self.values

    def remap_to_potential(self, active_throughput, year, tradable_geography=None):
        """remaps throughput to potential bins"""
        #original supply curve represents an annual timeslice
        primary_geography = GeoMapper.supply_primary_geography
        self.active_throughput = active_throughput
        #self.active_throughput[self.active_throughput<=0] = 1E-25
        original_supply_curve = util.remove_df_levels(self.supply_curve.loc[:,year].to_frame().sort_index(),[x for x in self.supply_curve.loc[:,year].index.names if x not in [primary_geography, 'resource_bin', 'demand_sector']])
        self.active_supply_curve = util.remove_df_levels(original_supply_curve,[x for x in self.supply_curve.loc[:,year].index.names if x not in [primary_geography, 'resource_bin', 'demand_sector']])
        if tradable_geography is not None and tradable_geography!=primary_geography:
                map_df = GeoMapper.get_instance().map_df(primary_geography,tradable_geography,normalize_as='total',eliminate_zeros=False,filter_geo=False)
                original_supply_curve = util.DfOper.mult([map_df,original_supply_curve])
                self.geo_map(converted_geography=tradable_geography, attr='active_supply_curve', inplace=True, current_geography=primary_geography,filter_geo=False)
                self.geo_map(converted_geography=tradable_geography, attr='active_throughput', inplace=True, current_geography=primary_geography,filter_geo=False)
        self.active_supply_curve = self.active_supply_curve.groupby(level=[x for x in self.active_supply_curve.index.names if x not in 'resource_bin']).cumsum()         
        reindexed_throughput = util.DfOper.none([self.active_throughput,self.active_supply_curve],expandable=(True,False),collapsible=(True,True))           
        self.active_supply_curve = util.expand_multi(self.active_supply_curve, reindexed_throughput.index.levels,reindexed_throughput.index.names)        
        reindexed_throughput = util.DfOper.none([self.active_throughput,self.active_supply_curve],expandable=(True,False),collapsible=(True,True))   
        bin_supply_curve = copy.deepcopy(self.active_supply_curve)
        bin_supply_curve[bin_supply_curve>reindexed_throughput] = reindexed_throughput
        self.active_supply_curve = bin_supply_curve.groupby(level=util.ix_excl(bin_supply_curve,'resource_bin')).diff().fillna(bin_supply_curve)
        if tradable_geography is not None and tradable_geography!=primary_geography:
            normalized = original_supply_curve.groupby(level=[tradable_geography,'resource_bin']).transform(lambda x: x/x.sum())
            self.active_supply_curve = util.remove_df_levels(util.DfOper.mult([normalized,self.active_supply_curve]),tradable_geography)
        self.active_supply_curve.columns = ['value']

    def remap_to_potential_and_normalize(self,active_throughput, year,tradable_geography=None) :
        """returns the proportion of the supply curve that is in each bin"""
        self.remap_to_potential(active_throughput, year, tradable_geography)
        self.active_supply_curve_normal= self.active_supply_curve.groupby(level=GeoMapper.supply_primary_geography).transform(lambda x:x/x.sum()).fillna(0.)

    def format_potential_and_supply_for_constraint_check(self,active_supply, tradable_geography, year):
        if tradable_geography == GeoMapper.supply_primary_geography:
            self.active_potential = self.values.loc[:,year].to_frame()
            self.active_geomapped_potential = self.active_potential
            self.active_geomapped_supply = active_supply
        else:
            self.active_potential = self.values.loc[:,year].to_frame()
            self.active_geomapped_potential = self.geo_map(converted_geography=tradable_geography, attr='active_potential', inplace=False, current_geography=GeoMapper.supply_primary_geography, current_data_type='total',filter_geo=False)
            self.active_geomapped_supply = active_supply
            self.active_geomapped_supply = self.geo_map(converted_geography=tradable_geography, attr='active_geomapped_supply', inplace=False, current_geography=GeoMapper.supply_primary_geography, current_data_type='total',filter_geo=False)
        levels = util.intersect(self.active_geomapped_supply.index.names, self.active_geomapped_supply.index.names)
        disallowed_potential_levels = [x for x in self.active_geomapped_potential.index.names if x not in levels]
        disallowed_supply_levels = [x for x in self.active_geomapped_supply.index.names if x not in levels]
        if len(disallowed_potential_levels):
            self.active_geomapped_potential = util.remove_df_levels(self.active_geomapped_potential, disallowed_potential_levels)
        if len(disallowed_supply_levels):
            self.active_geomapped_supply= util.remove_df_levels(self.active_geomapped_supply, disallowed_supply_levels)
        return self.active_geomapped_potential, self.active_geomapped_supply

class SupplyCost(schema.SupplyCost):
    def __init__(self, name, cost_of_capital, scenario):
        super(SupplyCost, self).__init__(name, scenario=scenario)
        self.init_from_db(name, scenario)
        if self.cost_of_capital is None:
            self.cost_of_capital = cost_of_capital

    def calculate(self, years, demand_sectors, conversion=None, resource_unit=None):
        self.years = years
        self.vintages = [years[0]-1] + years
        self.demand_sectors = demand_sectors
        if self._has_data:
            self.determ_input_type()
            self.remap(lower=None, converted_geography=GeoMapper.supply_primary_geography)
            self.convert()
            self.levelize_costs()

    def determ_input_type(self):
        """function that determines whether the input cost is a total or an intensity value"""
        if self.supply_cost_type == 'revenue requirement':
            self.input_type = 'total'
        elif self.supply_cost_type == 'tariff' or self.cost_type == 'investment':
            self.input_type = 'intensity'
        else:
            logging.error("incompatible cost type entry in cost %s" % self.name)
            raise ValueError

    def convert(self):
        """
        convert raw_values to model currency and capacity (energy_unit/time_step)
        """
        self.values = UnitConverter.currency_convert(self.values, self.currency, self.currency_year)
        model_energy_unit = cfg.calculation_energy_unit
        model_time_step = cfg.getParam('time_step')
        if self.input_type == 'intensity':
            if self.time_unit is not None:
                # if a cost has a time_unit, then the unit is energy and must be converted to capacity
                self.values = UnitConverter.unit_convert(self.values,
                                                unit_from_den=self.energy_or_capacity_unit,
                                                unit_from_num=self.time_unit, unit_to_den=model_energy_unit,
                                                unit_to_num=model_time_step)
                self.capacity = False
            else:
            # if a cost is a capacity unit, the model must convert the unit type to an energy unit for conversion ()
                if UnitConverter.is_energy_unit(self.energy_or_capacity_unit):
                    self.values = UnitConverter.unit_convert(self.values, unit_from_den =self.energy_or_capacity_unit, unit_to_den=model_energy_unit)
                    self.capacity = False
                else:
                    unit_from_den = self.energy_or_capacity_unit + "_" + model_time_step
                    self.values = UnitConverter.unit_convert(self.values,
                                                    unit_from_den=unit_from_den,
                                                    unit_from_num=model_time_step,
                                                    unit_to_den=model_energy_unit,
                                                    unit_to_num=model_time_step)
                    self.capacity = True
        else:
            self.capacity = True

    def levelize_costs(self):
        inflation = cfg.getParamAsFloat('inflation_rate')
        rate = self.cost_of_capital - inflation
        if self.supply_cost_type == 'investment':
            self.values_level = - np.pmt(rate, self.book_life, 1, 0, 'end') * self.values
#                util.convert_age(self, vintages=self.vintages, years=self.years, attr_from='values_level', attr_to='values_level', reverse=False)
        elif self.supply_cost_type == 'tariff' or  self.supply_cost_type == 'revenue requirement':
            self.values_level = self.values.copy()
#                util.convert_age(self, vintages=self.vintages, years=self.years, attr_from='values_level', attr_to='values_level', reverse=False)
            self.values = np.pv(rate, self.book_life, -1, 0, 'end') * self.values
        util.replace_index_name(self.values,'vintage','year')
        self.values_level_no_vintage = self.values_level
        keys = self.vintages
        name = ['vintage']
        self.values_level= pd.concat([self.values_level_no_vintage]*len(keys), keys=keys, names=name)
        self.values_level = self.values_level.swaplevel('vintage', -1)
        self.values_level = self.values_level.unstack('year')
        self.values_level.columns = self.values_level.columns.droplevel()
        self.values_level_no_vintage = self.values_level_no_vintage.unstack('year')
        self.values_level_no_vintage.columns = self.values_level_no_vintage.columns.droplevel()


class SupplyCoefficients(schema.SupplyEfficiency):
    def __init__(self, name, scenario):
        super(SupplyCoefficients, self).__init__(name, scenario=scenario)
        self.init_from_db(name, scenario)
        self.input_type = 'intensity'
        self.scenario = scenario


    def calculate(self, years, demand_sectors):
        self.years = years
        self.demand_sectors = demand_sectors

        if self._has_data:
            self.convert()
            self.remap(map_from='values', lower=None, converted_geography=GeoMapper.supply_primary_geography)
            self.values = self.values.unstack(level='year')
            self.values.columns = self.values.columns.droplevel()
            #TODO fix
            if 'demand_sector' not in self.values.index.names:
                keys = self.demand_sectors
                names = ['demand_sector']
                self.values = pd.concat([self.values]*len(keys),keys=keys,names=names)
            self.values = self.values.reorder_levels([x for x in [GeoMapper.supply_primary_geography,'demand_sector', 'efficiency_type', 'supply_node','resource_bin'] if x in self.values.index.names])
            self.values = self.values.sort_index()

    def convert(self):
        """
        return raw_values that are converted to units consistent with output units for
        normalized efficiency values

        """
        self.values = UnitConverter.unit_convert(self.raw_values, unit_from_num=self.input_unit, unit_to_num=self.output_unit)


class SupplyStockNode(Node):
    def __init__(self, name, scenario, **kwargs):
        Node.__init__(self, name, scenario)
        self.potential = SupplyPotential(self.name, self.enforce_potential_constraint, self.scenario)
        self.technologies = {}
        self.tech_names = []
        self.add_technologies()
#        self.add_nodes()
        self.add_stock()

    def calculate_oversupply(self, year, loop):
        """calculates whether the stock would oversupply the IO requirement and returns an oversupply adjustment factor."""
        if hasattr(self,'stock'):
            oversupply_factor = DfOper.divi([self.stock.values_energy.loc[:,year].to_frame(), self.throughput], expandable=False, collapsible=True).fillna(1)
            oversupply_factor.replace(np.inf, 1, inplace=True)
            oversupply_factor[oversupply_factor<1] = 1
            if (oversupply_factor.values>1.000000001).any():
                self.oversupply_factor = oversupply_factor
                #TODO fix
                return oversupply_factor
            else:
                return None
        else:
            return None

    def adjust_energy(self,oversupply_factor,year):
#        self.stock.capacity_factor.loc[:,year] = util.DfOper.mult([self.stock.capacity_factor.loc[:,year].to_frame(),1/oversupply_factor])
        self.stock.values_energy.loc[:,year] = util.DfOper.mult([self.stock.values_energy.loc[:,year].to_frame(),1/oversupply_factor])

    def set_rollover_groups(self):
        """sets the internal index for use in stock and cost calculations"""
        # determines whether stock rollover needs to occur on demand sector or resource bin index
        self.stock.rollover_group_levels = []
        self.stock.rollover_group_names = []
        if self.stock._has_data is True:
            for name, level in zip(self.stock.raw_values.index.names, self.stock.raw_values.index.levels):
                if (name == 'resource_bin' or name == 'demand_sector') and name not in self.stock.rollover_group_names:
                    if name == 'demand_sector':
                            level = self.demand_sectors
                    self.stock.rollover_group_levels.append(list(level))
                    self.stock.rollover_group_names.append(name)
                elif name == 'resource_bin' or name == 'demand_sector':
                    original_levels = self.stock.rollover_group_levels[self.stock.rollover_group_names.index(name)]
                    new_levels = list(set(original_levels+list(level)))
                    self.stock.rollover_group_levels[self.stock.rollover_group_names.index(name)] = new_levels
        if self.potential._has_data is True:
            for name, level in zip(self.potential.raw_values.index.names, self.potential.raw_values.index.levels):
                if (name == 'resource_bin' or name == 'demand_sector') and name not in self.stock.rollover_group_names:
                    if name == 'demand_sector':
                        level = self.demand_sectors
                    self.stock.rollover_group_levels.append(list(level))
                    self.stock.rollover_group_names.append(name)
                elif name == 'resource_bin' or name == 'demand_sector':
                    original_levels = self.stock.rollover_group_levels[self.stock.rollover_group_names.index(name)]
                    new_levels = list(set(original_levels+list(level)))
                    self.stock.rollover_group_levels[self.stock.rollover_group_names.index(name)] = new_levels
        for technology in self.technologies.values():
            attributes = vars (technology)
            for att in attributes:
                obj = getattr(technology, att)
                if inspect.isclass(type(obj)) and hasattr(obj, '__dict__') and hasattr(obj, 'raw_values') and obj.raw_values is not None:
                    for name, level in zip(obj.raw_values.index.names, obj.raw_values.index.levels):
                        if (name == 'resource_bin' or name == 'demand_sector') and name not in self.stock.rollover_group_names:
                            if name == 'demand_sector':
                                level = self.demand_sectors
                            self.stock.rollover_group_levels.append(list(level))
                            self.stock.rollover_group_names.append(name)
                        elif name == 'resource_bin' or name == 'demand_sector':
                            original_levels = self.stock.rollover_group_levels[self.stock.rollover_group_names.index(name)]
                            new_levels = list(set(original_levels+list(level)))
                            self.stock.rollover_group_levels[self.stock.rollover_group_names.index(name)] = new_levels
        if self.name == self.distribution_grid_node_name and 'demand_sector' not in self.stock.rollover_group_names:
            #requires distribution grid node to maintain demand sector resolution in its stocks
            self.stock.rollover_group_levels.append(self.demand_sectors)
            self.stock.rollover_group_names.append('demand_sector')
        elif self.name == self.distribution_grid_node_name:
            original_levels = self.stock.rollover_group_levels[self.stock.rollover_group_names.index('demand_sector')]
            new_levels = list(set(original_levels+self.demand_sectors))
            self.stock.rollover_group_levels[self.stock.rollover_group_names.index('demand_sector')] = new_levels
        self.stock.rollover_group_names = [GeoMapper.supply_primary_geography] + self.stock.rollover_group_names
        self.stock.rollover_group_levels = [GeoMapper.geography_to_gau[GeoMapper.supply_primary_geography]] + self.stock.rollover_group_levels

    def add_stock(self):
        """add stock instance to node"""
        self.stock = SupplyStock(supply_node=self.name, scenario=self.scenario)

    def calculate(self):
        #all nodes can have potential conversions. Set to None if no data.
        self.add_nodes()
        self.conversion, self.resource_unit = self.add_conversion()
        self.set_rollover_groups()
        self.calculate_subclasses()
        self.calculate_stock_measures()
        self.add_case_stock()
        self.set_adjustments()
        self.set_pass_through_df_dict()
        self.setup_stock_rollover(self.years)

    def calculate_input_stock(self):
        """calculates the technology stocks in a node based on the combination of measure-stocks and reference stocks"""
        levels = self.stock.rollover_group_levels + [self.years] + [self.tech_names]
        names = self.stock.rollover_group_names + ['year'] + ['supply_technology']
        index = pd.MultiIndex.from_product(levels,names=names)
        if self.stock._has_data is True and 'supply_technology' in self.stock.raw_values.index.names:
            #remap to technology stocks
            self.stock.years = self.years
            self.stock.remap(map_from='raw_values', map_to='technology', converted_geography=GeoMapper.supply_primary_geography, fill_timeseries=True, fill_value=np.nan)
            #TODO add to clean timeseries. Don't allow filling of timseries before raw values.
            self.stock.technology[self.stock.technology.index.get_level_values('year')<min(self.stock.raw_values.index.get_level_values('year'))] = np.nan
            self.convert_stock('stock', 'technology')
            self.stock.technology = self.stock.technology.reorder_levels(names)
            self.stock.technology = self.stock.technology.reindex(index)
            #if there's case_specific stock data, we must use that to replace reference technology stocks
            if hasattr(self.case_stock,'technology'):
                # if there are levels in the case specific stock that are not in the reference stock, we must remove that level from the case stock
                mismatched_levels = [x for x in self.case_stock.technology.index.names if x not in self.stock.technology.index.names]
                if len(mismatched_levels):
                    self.case_stock.technology= util.remove_df_levels(self.case_stock.technology,mismatched_levels)
                #if there are still level mismatches, it means the reference stock has more levels, which returns an error
                if np.any(util.difference_in_df_names(self.case_stock.technology, self.stock.technology,return_bool=True)):
                    raise ValueError("technology stock indices in node %s do not match input energy system stock data" %self.name)
                else:
                    #if the previous test is passed, we use the reference stock to fill in the Nans of the case stock
                    self.case_stock.technology = self.case_stock.technology.reorder_levels(names)
                    self.case_stock.technology = self.case_stock.technology.reindex(index)
                    self.stock.technology = self.case_stock.technology.fillna(self.stock.technology)
            self.stock.technology = self.stock.technology.unstack('year')
            self.stock.technology.columns = self.stock.technology.columns.droplevel()
            self.stock.technology = util.reindex_df_level_with_new_elements(self.stock.technology,'supply_technology',self.tech_names)
        elif hasattr(self.case_stock,'technology'):
                # if there are levels in the case specific stock that are not in the rollover groups, we must remove that level from the case stock
                mismatched_levels = [x for x in self.case_stock.technology.index.names if x not in names]
                if len(mismatched_levels):
                    self.case_stock.technology = util.remove_df_levels(self.case_stock.technology,mismatched_levels)
                #if there are still level mismatches, it means the rollover has more levels, which returns an error
                if len([x for x in self.stock.rollover_group_names if x not in self.case_stock.technology.index.names]) :
                    raise ValueError("technology stock levels in node %s do not match other node input data" %self.name)
                else:
                    #if the previous test is passed we reindex the case stock for unspecified technologies
                    self.case_stock.technology = self.case_stock.technology.reorder_levels(names)
                    structure_df = pd.DataFrame(1,index=index,columns=['value'])
                    self.case_stock.technology = self.case_stock.technology.reindex(index)
                    self.stock.technology = self.case_stock.technology
                self.stock.technology = self.stock.technology.unstack('year')
                self.stock.technology.columns = self.stock.technology.columns.droplevel()
                self.stock.technology = util.reindex_df_level_with_new_elements(self.stock.technology,'supply_technology',self.tech_names)
        else:
            levels = self.stock.rollover_group_levels  + [self.tech_names]
            names = self.stock.rollover_group_names + ['supply_technology']
            index = pd.MultiIndex.from_product(levels,names=names)
            self.stock.technology = util.empty_df(index=index,columns=self.years,fill_value=np.NaN)

        if self.stock._has_data is True and 'supply_technology' not in self.stock.raw_values.index.names:
            levels = self.stock.rollover_group_levels + [self.years]
            names = self.stock.rollover_group_names + ['year']
            index = pd.MultiIndex.from_product(levels,names=names)
            structure_df = pd.DataFrame(1,index=index,columns=['value'])
            self.stock.remap(map_from='raw_values', map_to='total', converted_geography=GeoMapper.supply_primary_geography, time_index = self.years,fill_timeseries=True, fill_value=np.nan)
            #TODO add to clean timeseries. Don't allow filling of timseries before raw values.
            self.stock.total[self.stock.total.index.get_level_values('year')<min(self.stock.raw_values.index.get_level_values('year'))] = np.nan
            self.stock.total = DfOper.mult([self.stock.total,structure_df],fill_value=np.nan)
            self.convert_stock('stock', 'total')
            if hasattr(self.case_stock,'total'):
                mismatched_levels = [x for x in self.case_stock.total.index.names if x not in names]
                if len(mismatched_levels):
                    self.case_stock.total = util.remove_df_levels(self.case_stock.total,mismatched_levels)
                #if there are still level mismatches, it means the reference stock has more levels, which returns an error
                if np.any(util.difference_in_df_names(self.case_stock.total, self.stock.total,return_bool=True)):
                    raise ValueError("total stock indices in node %s do not match input energy system stock data" %self.name)
                else:
                    #if the previous test is passed, we use the reference stock to fill in the Nans of the case stock
                    self.case_stock.total= self.case_stock.total.reorder_levels(names)
                    self.stock.total = self.stock.total.reorder_levels(names)
                    structure_df = pd.DataFrame(1,index=index,columns=['value'])
                    self.case_stock.total = DfOper.mult([self.case_stock.total,structure_df],fill_value=np.nan)
                    self.stock.total = DfOper.mult([self.stock.total,structure_df],fill_value=np.nan)
                    self.stock.total = self.case_stock.total.fillna(self.stock.total)

            self.stock.total = self.stock.total.unstack('year')
            self.stock.total.columns = self.stock.total.columns.droplevel()
        elif hasattr(self.case_stock,'total'):
                levels = self.stock.rollover_group_levels + [self.years]
                names = self.stock.rollover_group_names + ['year']
                index = pd.MultiIndex.from_product(levels,names=names)
                # if there are levels in the case specific stock that are not in the rollover groups, we must remove that level from the case stock
                mismatched_levels = [x for x in self.case_stock.total.index.names if x not in names]
                if len(mismatched_levels):
                    self.case_stock.total = util.remove_df_levels(self.case_stock.total,mismatched_levels)
                #if there are still level mismatches, it means the rollover has more levels, which returns an error
                if len([x for x in names if x not in self.case_stock.total.index.names]) :
                    raise ValueError("total stock levels in node %s do not match other node input data" %self.name)
                else:
                    self.case_stock.total= self.case_stock.total.reorder_levels(names)
                    self.case_stock.total = self.case_stock.total.reindex(index)
                    self.stock.total = self.case_stock.total
                    self.stock.total = self.stock.total.unstack('year')
                    self.stock.total.columns = self.stock.total.columns.droplevel()
        else:
             index = pd.MultiIndex.from_product(self.stock.rollover_group_levels,names=self.stock.rollover_group_names)
             self.stock.total = util.empty_df(index=index,columns=self.years,fill_value=np.NaN)
        if self.stock._has_data or hasattr(self.case_stock,'data') and self.case_stock._has_data == True:
            self.stock._has_data = True
        self.max_total()
        if cfg.rio_supply_run and self.name not in cfg.rio_excluded_nodes:
            self.stock.technology.loc[:, cfg.supply_years] = self.stock.technology.loc[:, cfg.supply_years].fillna(0)
        self.format_rollover_stocks()

    def max_total(self):
        tech_sum = util.remove_df_levels(self.stock.technology,'supply_technology')

        if hasattr(self.stock,'total'):
            if np.all(np.isnan(self.stock.total.values)) and not np.any(np.isnan(self.stock.technology.values)):
                self.stock.total = self.stock.total.fillna(tech_sum)
            else:
                self.stock.total[self.stock.total.values<tech_sum.values] = tech_sum
        else:
            self.stock.total = pd.DataFrame(np.nan, tech_sum.index,tech_sum.columns)

    def format_rollover_stocks(self):
        #transposed technology stocks are used for entry in the stock rollover function
        self.stock.technology_rollover = self.stock.technology.stack(dropna=False)
        util.replace_index_name(self.stock.technology_rollover,'year')
        self.stock.total_rollover = util.remove_df_levels(self.stock.technology_rollover,'supply_technology')
        self.stock.technology_rollover=self.stock.technology_rollover.unstack('supply_technology')
        for tech_name in self.tech_names:
            if tech_name not in self.stock.technology_rollover.columns:
                self.stock.technology_rollover[tech_name]=np.nan

    def add_case_stock(self):
       self.case_stock = StockItem()
       tech_stocks = []
       for technology in self.technologies.values():
           for stock in technology.specified_stocks.values():
               if stock.values is not None:
                   stock.values['supply_technology'] = technology.name
                   stock.values.set_index('supply_technology', append=True, inplace=True)
                   tech_stocks.append(stock.values)
       if len(tech_stocks):
            self.case_stock._has_data = True
            self.case_stock.technology = util.DfOper.add(tech_stocks, expandable=False)
            self.case_stock.technology[self.case_stock.technology.index.get_level_values('year')<cfg.getParamAsInt('current_year')] = np.nan
       total_stocks = []
       for stock in self.total_stocks.values():
            if stock.values is not None:
                self.case_stock._has_data = True
                total_stocks.append(stock.values)
       if len(total_stocks):
           self.case_stock.total = DfOper.add(total_stocks, expandable=False)
           self.case_stock.total[self.case_stock.total.index.get_level_values('year')<cfg.getParamAsInt('current_year')] = np.nan
#       elif len(tech_stocks):
#           self.case_stock.total = util.remove_df_levels(self.case_stock.technology,'supply_technology')


    def remap_tech_attrs(self, attr_classes, attr='values'):
        """
        loops through attr_classes (ex. capital_cost, energy, etc.) in order to map technologies
        that reference other technologies in their inputs (i.e. technology A is 150% of the capital cost technology B)
        """
        attr_classes = util.ensure_iterable(attr_classes)
        for technology in self.technologies.keys():
            for attr_class in attr_classes:
                self.remap_tech_attr(technology, attr_class, attr)

    def remap_tech_attr(self, technology, class_name, attr):
        """
        map reference technology values to their associated technology classes

        """
        tech_class = getattr(self.technologies[technology], class_name)
        if hasattr(tech_class, 'reference_tech'):
            if getattr(tech_class, 'reference_tech'):
                ref_tech_name = (getattr(tech_class, 'reference_tech'))
                if not self.technologies.has_key(ref_tech_name):
                    raise ValueError("supply node {} has no technology {} to serve as a reference for technology {} in attribute {}".format(self.name, ref_tech_name, technology, class_name))
                ref_tech_class = getattr(self.technologies[ref_tech_name], class_name)
                # converted is an indicator of whether an input is an absolute
                # or has already been converted to an absolute
                if not getattr(ref_tech_class, 'absolute'):
                    # If a technnology hasn't been mapped, recursion is used
                    # to map it first (this can go multiple layers)
                    self.remap_tech_attr(getattr(tech_class, 'reference_tech'), class_name, attr)
                if tech_class.raw_values is not None:
                    tech_data = getattr(tech_class, attr)
                    new_data = DfOper.mult([tech_data,
                                            getattr(ref_tech_class, attr)])
                    if hasattr(ref_tech_class,'values_level'):
                        new_data_level = DfOper.mult([tech_data,
                                            getattr(ref_tech_class, 'values_level')])
                else:
                    new_data = copy.deepcopy(getattr(ref_tech_class, attr))
                    if hasattr(ref_tech_class,'values_level'):
                        new_data_level = copy.deepcopy(getattr(ref_tech_class, 'values_level'))
                tech_attributes = vars(getattr(self.technologies[ref_tech_name], class_name))
                for attribute_name in tech_attributes.keys():
                    if not hasattr(tech_class, attribute_name) or getattr(tech_class, attribute_name) is None:
                        setattr(tech_class, attribute_name,
                                copy.deepcopy(getattr(ref_tech_class, attribute_name)) if hasattr(ref_tech_class,
                                                                                                  attribute_name) else None)
                setattr(tech_class, attr, new_data)
                if hasattr(ref_tech_class,'values_level'):
                    setattr(tech_class,'values_level',new_data_level)
        # Now that it has been converted, set indicator to true
        tech_class.absolute = True

    def add_technologies(self):
        names = util.csv_read_table('SupplyTechs', column_names='name', supply_node=self.name, return_iterable=True)
        for name in names:
            self.add_technology(name)
        self.tech_names.sort()

    def add_nodes(self):
        self.nodes = []
        for technology in self.technologies.values():
            if hasattr(technology,'efficiency') and technology.efficiency.raw_values is not None:
                for value in technology.efficiency.values.index.get_level_values('supply_node'):
                    self.nodes.append(value)
        self.nodes = list(set(self.nodes))

    def add_technology(self, name):
        """
        Adds technology instances to node
        """
        if name in self.technologies:
            logging.debug('Warning: Technology {} was added twice to supply node {}'.format(name, self.name))
            return
        self.technologies[name] = SupplyTechnology(name, self.cost_of_capital, self.scenario)
        self.tech_names.append(name)

    def calculate_stock_measures(self):
        for technology in self.technologies.values():
           for stock in technology.specified_stocks.values():
               stock.calculate(self.vintages,self.years)
               stock.convert()
        for stock in self.total_stocks.values():
            stock.calculate(self.vintages,self.years)
            stock.convert()

    def calculate_sales_shares(self):
        for tech in self.tech_names:
            technology = self.technologies[tech]
            technology.calculate_sales_shares('reference_sales_shares')
            technology.calculate_sales_shares('sales_shares')

    def reconcile_sales_shares(self):
        needed_sales_share_levels = self.stock.rollover_group_levels + [self.years]
        needed_sales_share_names = self.stock.rollover_group_names + ['vintage']
        for technology in self.technologies.values():
            technology.reconcile_sales_shares('sales_shares', needed_sales_share_levels, needed_sales_share_names)
            technology.reconcile_sales_shares('reference_sales_shares', needed_sales_share_levels,
                                              needed_sales_share_names)

    def calculate_sales(self):
        for tech in self.tech_names:
            technology = self.technologies[tech]
            try:
                technology.calculate_sales('reference_sales')
            except:
                pdb.set_trace()
            technology.calculate_sales('sales')

    def reconcile_sales(self):
        needed_sales_share_levels = self.stock.rollover_group_levels + [self.years]
        needed_sales_share_names = self.stock.rollover_group_names + ['vintage']
        for technology in self.technologies.values():
            technology.reconcile_sales('sales', needed_sales_share_levels, needed_sales_share_names)
            technology.reconcile_sales('reference_sales', needed_sales_share_levels,
                                              needed_sales_share_names)

    def calculate_total_sales_share(self, elements, levels):
        ss_measure = self.helper_calc_sales_share(elements, levels, reference=False)
        space_for_reference = 1 - np.sum(ss_measure, axis=1)
        ss_reference = self.helper_calc_sales_share(elements, levels, reference=True, space_for_reference=space_for_reference)
        if np.sum(ss_reference)==0:
            ss_reference = SalesShare.scale_reference_array_to_gap( np.tile(np.eye(len(self.tech_names)), (len(self.years), 1, 1)), space_for_reference)
            #sales shares are always 1 with only one technology so the default can be used as a reference
            if len(self.tech_names)>1 and np.sum(ss_measure)<1:
                reference_sales_shares = False
            else:
                reference_sales_shares = True
        else:
            reference_sales_shares = True
        # return SalesShare.normalize_array(ss_reference+ss_measure, retiring_must_have_replacement=True)
        # todo make retiring_must_have_replacement true after all data has been put in db
        return SalesShare.normalize_array(ss_reference + ss_measure, retiring_must_have_replacement=False), reference_sales_shares

    def calculate_total_sales_share_after_initial(self, elements, levels):
        ss_measure = self.helper_calc_sales_share(elements, levels, reference=False)
        space_for_reference = 1 - np.sum(ss_measure, axis=1)
        ss_reference = SalesShare.scale_reference_array_to_gap( np.tile(np.eye(len(self.tech_names)), (len(self.years), 1, 1)), space_for_reference)
        # return SalesShare.normalize_array(ss_reference+ss_measure, retiring_must_have_replacement=True)
        # todo make retiring_must_have_replacement true after all data has been put in db
        return SalesShare.normalize_array(ss_reference + ss_measure, retiring_must_have_replacement=False)

    def calculate_total_sales(self,elements,levels):
        s_measure = self.helper_calc_sales(elements, levels, reference=False)
        s_reference = self.helper_calc_sales(elements, levels, reference=True)
        # return SalesShare.normalize_array(ss_reference+ss_measure, retiring_must_have_replacement=True)
        # todo make retirin)g_must_have_replacement true after all data has been put in db
        s_measure = pd.DataFrame(s_measure)
        s_reference = pd.DataFrame(s_reference)
        s_combined = s_measure.fillna(s_reference).values
        return s_combined

    def helper_calc_sales(self, elements, levels, reference, space_for_reference=None):
        num_techs = len(self.tech_names)
        tech_lookup = dict(zip(self.tech_names, range(num_techs)))
        num_years = len(self.years)
        # ['vintage', 'replacing tech id', 'retiring tech id']
        ss_array = np.empty(shape=(num_years, num_techs))
        ss_array.fill(np.nan)
        # tech_names must be sorted
        # normalize ss in one of two ways
        if reference:
            for tech_name in self.tech_names:
                for sales in self.technologies[tech_name].reference_sales.values():
                    repl_index = tech_lookup[tech_name]
                    # technology sales share dataframe may not have all elements of stock dataframe
                    sales.values.index.levels
                    if any([element not in sales.values.index.levels[
                        util.position_in_index(sales.values, level)] for element, level in
                            zip(elements, levels)]):
                        continue
                    ss_array[:, repl_index] = util.df_slice(sales.values, elements, levels).values.T[0]
        else:
            for tech_name in self.tech_names:
                for sales in self.technologies[tech_name].sales.values():
                    repl_index = tech_lookup[sales.supply_technology]
                    # TODO address the discrepancy when a demand tech is specified
                    try:
                        ss_array[:, repl_index] = util.df_slice(sales.values, elements, levels).values.T[0]
                    except:
                        ss_array[:, repl_index] = util.df_slice(sales.values, elements, levels).values.flatten()
        return ss_array

    def helper_calc_sales_share(self, elements, levels, reference, space_for_reference=None):
        num_techs = len(self.tech_names)
        tech_lookup = dict(zip(self.tech_names, range(num_techs)))
        num_years = len(self.years)
        # ['vintage', 'replacing tech id', 'retiring tech id']
        ss_array = np.zeros(shape=(num_years, num_techs, num_techs))
        # tech_names must be sorted
        # normalize ss in one of two ways
        if reference:
            for tech_name in self.tech_names:
                for sales_share in self.technologies[tech_name].reference_sales_shares.values():
                    if set(sales_share.values.index.names).issubset(self.stock.sales_share_reconcile.index.names) and set(sales_share.values.index.names)!=set(self.stock.sales_share_reconcile.index.names):
                        sales_share.values = DfOper.none([sales_share.values,self.stock.sales_share_reconcile],non_expandable_levels=None)
                    repl_index = tech_lookup[tech_name]
                    reti_index = slice(None)
                    # technology sales share dataframe may not have all elements of stock dataframe
                    ss_array[:, repl_index, reti_index] += util.df_slice(sales_share.values, elements, levels).values
            ss_array = SalesShare.scale_reference_array_to_gap(ss_array, space_for_reference)
        else:
            for tech_name in self.tech_names:
                for sales_share in self.technologies[tech_name].sales_shares.values():
                    if set(sales_share.values.index.names).issubset(self.stock.sales.index.names) and set(sales_share.values.index.names)!=set(self.stock.sales.index.names):
                        sales_share.values = util.DfOper.none([sales_share.values,util.remove_df_levels(self.stock.sales_exist,'supply_technology')],non_expandable_levels=None)
                    repl_index = tech_lookup[tech_name]
                    repl_index = tech_lookup[sales_share.supply_technology]
                    reti_index = tech_lookup[
                        sales_share.replaced_supply_technology] if sales_share.replaced_supply_technology is not None and tech_lookup.has_key(
                        sales_share.replaced_supply_technology) else slice(None)
                    if sales_share.replaced_supply_technology is not None and not tech_lookup.has_key(sales_share.replaced_supply_technology):
                        #sales share specified for a technology not in the model
                        continue
                    try:
                        ss_array[:, repl_index, reti_index] += util.df_slice(sales_share.values, elements,levels).values
                    except:
                        ss_array[:, repl_index, reti_index] += util.df_slice(sales_share.values, elements,
                                                                             levels).values.flatten()

            ss_array = SalesShare.cap_array_at_1(ss_array)
        return ss_array

    def calc_tech_survival_functions(self):
        for technology in self.technologies.values():
            technology.set_survival_parameters()
            technology.set_survival_vintaged()
            technology.set_decay_vintaged()
            technology.set_decay_initial_stock()
            technology.set_survival_initial_stock()

    def create_tech_survival_functions(self):
        functions = defaultdict(list)
        for fun in ['survival_vintaged', 'survival_initial_stock', 'decay_vintaged', 'decay_initial_stock']:
            for tech_name in self.tech_names:
                technology = self.technologies[tech_name]
                functions[fun].append(getattr(technology, fun))
            setattr(self.stock, fun, pd.DataFrame(np.array(functions[fun]).T, columns=self.tech_names))

    def create_rollover_markov_matrices(self):
        vintaged_markov = util.create_markov_vector(self.stock.decay_vintaged.values,
                                                    self.stock.survival_vintaged.values)
        self.stock.vintaged_markov_matrix = util.create_markov_matrix(vintaged_markov, len(self.tech_names),
                                                                      len(self.years))

        initial_markov = util.create_markov_vector(self.stock.decay_initial_stock.values, self.stock.survival_initial_stock.values)
        self.stock.initial_markov_matrix = util.create_markov_matrix(initial_markov, len(self.tech_names),
                                                                     len(self.years))

    def setup_stock_rollover(self, years):
        """ Sets up dataframes and inputs to stock rollover before loop commences"""
        #prep stock rollover for initial solve
        self.calc_tech_survival_functions()
        self.calculate_sales_shares()
        self.calculate_sales()
        self.calculate_input_stock()
        self.create_tech_survival_functions()
        self.create_rollover_markov_matrices()
        self.add_stock_dataframes()
        self.setup_financial_stock()
        self.rollover_dict = {}
        for elements in self.rollover_groups.keys():
            elements = util.ensure_tuple(elements)
            
            sales_share, initial_sales_share = self.calculate_total_sales_share(elements,self.stock.rollover_group_names)  # group is not necessarily the same for this other dataframe
            if np.any(np.isnan(sales_share)):
                raise ValueError('Sales share has NaN values in node ' + str(self.name))
            sales = self.calculate_total_sales(elements, self.stock.rollover_group_names)
            initial_total = util.df_slice(self.stock.total_rollover, elements, self.stock.rollover_group_names).values[0]
            initial_stock, rerun_sales_shares = self.calculate_initial_stock(elements, initial_total, sales_share, initial_sales_share)
            if rerun_sales_shares:
                 sales_share = self.calculate_total_sales_share_after_initial(elements,self.stock.rollover_group_names)
            technology_stock = self.stock.return_stock_slice(elements, self.stock.rollover_group_names,'technology_rollover').values
            self.rollover_dict[elements] = Rollover(vintaged_markov_matrix=self.stock.vintaged_markov_matrix,
                                     initial_markov_matrix=self.stock.initial_markov_matrix,
                                     num_years=len(years), num_vintages=len(years),
                                     num_techs=len(self.tech_names), initial_stock=initial_stock,
                                     sales_share=sales_share, stock_changes=None, specified_sales=sales,
                                     specified_stock=technology_stock, specified_retirements=None,stock_changes_as_min=True)

        for year in [x for x in self.years if x<cfg.getParamAsInt('current_year')]:
            for elements in self.rollover_groups.keys():
                elements = util.ensure_tuple(elements)
                try:
                    self.rollover_dict[elements].run(1)
                except:
                    logging.error('error encountered in rollover for node ' + str(self.name) + ' in elements '+ str(elements) + ' year ' + str(year))
                    raise
                stock, stock_new, stock_replacement, retirements, retirements_natural, retirements_early, sales_record, sales_new, sales_replacement = self.rollover_dict[(elements)].return_formatted_outputs(year_offset=0)
                self.stock.values.loc[elements, year], self.stock.values_new.loc[elements, year], self.stock.values_replacement.loc[
                elements,year] = stock, stock_new, stock_replacement
                full_levels = [[x] for x in elements] + [self.tech_names] + [[year]]
                full_names = self.stock.rollover_group_names + ['supply_technology'] + ['vintage']
                elements_indexer = util.level_specific_indexer(self.stock.retirements, full_names, full_levels)
                self.stock.retirements.loc[elements_indexer, 'value'], self.stock.retirements_natural.loc[elements_indexer, 'value'], \
                self.stock.retirements_early.loc[elements_indexer, 'value'] = retirements, retirements_natural, retirements_early
                self.stock.sales.loc[elements_indexer, 'value'], self.stock.sales_new.loc[elements_indexer, 'value'], \
                self.stock.sales_replacement.loc[elements_indexer, 'value'] = sales_record, sales_new, sales_replacement
            self.stock_normalize(year)
            self.financial_stock(year, 1)
            self.calculate_actual_stock(year, 1)

    def calculate_initial_stock(self, elements, initial_total, sales_share, initial_sales_share):
        technology = self.stock.technology_rollover.sum(axis=1).to_frame()
        technology_years = technology[technology>0].index.get_level_values('year')
        if len(technology_years) and not np.all(np.isnan(self.stock.technology_rollover.values)):
             min_technology_year = min(technology_years)
        else:
             min_technology_year = None

        if (np.nansum(self.stock.technology_rollover.loc[elements,:].values[0])/self.stock.total_rollover.loc[elements,:].values[0])>.99 and np.nansum(self.stock.technology_rollover.loc[elements,:].values[0])>0:
            initial_stock = self.stock.technology_rollover.loc[elements,:].fillna(0).values[0]
            rerun_sales_shares = False
        elif initial_sales_share:
            initial_stock = self.stock.calc_initial_shares(initial_total=initial_total, transition_matrix=sales_share[0], num_years=len(self.years))
            rerun_sales_shares = True
            for i in range(1, len(sales_share)):
                if np.any(sales_share[0]!=sales_share[i]):
                    rerun_sales_shares=False
        elif min_technology_year:
            initial_stock = self.stock.technology_rollover.loc[elements+(min_technology_year,),:].fillna(0).values/np.nansum(self.stock.technology_rollover.loc[elements+(min_technology_year,),:].values) * initial_total
            initial_stock = np.nan_to_num(initial_stock)
            rerun_sales_shares = False
        else:
            raise ValueError("""user has not input stock data with technologies or sales share data so the model 
                                cannot determine the technology composition of the initial stock in node %s""" % self.name)

        # TODO Ben to review
        # this is a fix for the case where we have no initial stock and we don't want to rerun the reference sales share
        # the problem came up in model.supply.nodes[97].rollover_dict[(61, 1)] (CSP)
        if any(np.isnan(initial_stock)) or np.sum(initial_stock)==0:
            rerun_sales_shares = False

        return initial_stock, rerun_sales_shares

    def stock_rollover(self, year, loop, stock_changes):
        if min(self.years) == cfg.getParamAsInt('current_year') ==year:
            for elements in self.rollover_groups.keys():
                elements = util.ensure_tuple(elements)
                sales_share, initial_sales_share = self.calculate_total_sales_share(elements,self.stock.rollover_group_names)  # group is not necessarily the same for this other dataframe
                if np.any(np.isnan(sales_share)):
                    raise ValueError('Sales share has NaN values in node ' + str(self.name))
                if len(self.stock.requirement.index.names)>1:
                    initial_total = self.stock.requirement.loc[elements, year]
                else:
                    initial_total = self.stock.requirement.loc[elements, year].values
                initial_stock, rerun_sales_shares = self.calculate_initial_stock(elements, initial_total, sales_share,initial_sales_share)
                if rerun_sales_shares:
                    sales_share = self.calculate_total_sales_share_after_initial(elements,self.stock.rollover_group_names)
                self.rollover_dict[elements].initial_stock = initial_stock
                self.rollover_dict[elements].sales_share = sales_share
        for elements in self.rollover_groups.keys():
            elements = util.ensure_tuple(elements)
            try:
                self.rollover_dict[elements].use_stock_changes = True
                self.rollover_dict[elements].run(1, stock_changes.loc[elements],self.stock.return_stock_slice(elements + (year,), self.stock.rollover_group_names+['year'],'technology_rollover').values)
            except:
                logging.error('error encountered in rollover for node ' + str(self.name) + ' in elements '+ str(elements) + ' year ' + str(year))
                raise
            stock, stock_new, stock_replacement, retirements, retirements_natural, retirements_early, sales_record, sales_new, sales_replacement = self.rollover_dict[(elements)].return_formatted_outputs(year_offset=0)
            self.stock.values.loc[elements, year], self.stock.values_new.loc[elements, year], self.stock.values_replacement.loc[
                elements,year] = stock, stock_new, stock_replacement
            full_levels = [[x] for x in elements] + [self.tech_names] + [[year]]
            full_names = self.stock.rollover_group_names + ['supply_technology'] + ['vintage']
            elements_indexer = util.level_specific_indexer(self.stock.retirements, full_names, full_levels)
            self.stock.retirements.loc[elements_indexer, 'value'], self.stock.retirements_natural.loc[elements_indexer, 'value'], \
            self.stock.retirements_early.loc[elements_indexer, 'value'] = retirements, retirements_natural, retirements_early
            self.stock.sales.loc[elements_indexer, 'value'], self.stock.sales_new.loc[elements_indexer, 'value'], \
            self.stock.sales_replacement.loc[elements_indexer, 'value'] = sales_record, sales_new, sales_replacement
        self.calculate_actual_stock(year,loop)
        if loop!= 'initial':
            if not self.thermal_dispatch_node:
                adjustment_factor = self.calculate_adjustment_factor(year)
                for elements in self.rollover_groups.keys():
                    elements = util.ensure_tuple(elements)
                    self.rollover_dict[elements].factor_adjust_current_year(adjustment_factor.loc[elements].values)
                    stock, stock_new, stock_replacement, retirements, retirements_natural, retirements_early, sales_record, sales_new, sales_replacement = self.rollover_dict[(elements)].return_formatted_outputs(year_offset=0)
                    self.stock.values.loc[elements, year], self.stock.values_new.loc[elements, year], self.stock.values_replacement.loc[
                        elements,year] = stock, stock_new, stock_replacement
                    full_levels = [[x] for x in elements] + [self.tech_names] + [[year]]
                    full_names = self.stock.rollover_group_names + ['supply_technology'] + ['vintage']
                    elements_indexer = util.level_specific_indexer(self.stock.retirements, full_names, full_levels)
                    self.stock.retirements.loc[elements_indexer, 'value'], self.stock.retirements_natural.loc[elements_indexer, 'value'], \
                    self.stock.retirements_early.loc[elements_indexer, 'value'] = retirements, retirements_natural, retirements_early
                    self.stock.sales.loc[elements_indexer, 'value'], self.stock.sales_new.loc[elements_indexer, 'value'], \
                    self.stock.sales_replacement.loc[elements_indexer, 'value'] = sales_record, sales_new, sales_replacement
        self.calculate_actual_stock(year,loop)
        self.stock_normalize(year)
        self.financial_stock(year, loop)

    def add_stock_dataframes(self):
        index = pd.MultiIndex.from_product(self.stock.rollover_group_levels, names=self.stock.rollover_group_names)
        self.vintages = self.years
        columns = self.years
        index = pd.MultiIndex.from_product(self.stock.rollover_group_levels, names=self.stock.rollover_group_names)
        self.stock.requirement_energy = util.empty_df(index=index, columns=pd.Index(columns, dtype='object'))
        self.stock.requirement = util.empty_df(index=index, columns=pd.Index(columns, dtype='object'))
        if len(self.stock.rollover_group_names)>1:
            self.rollover_groups = self.stock.requirement.groupby(level=self.stock.rollover_group_names).groups
        else:
            self.rollover_groups = self.stock.requirement.groupby(level=0).groups
        full_levels = self.stock.rollover_group_levels + [self.technologies.keys()] + [
            [self.vintages[0] - 1] + self.vintages]
        full_names = self.stock.rollover_group_names + ['supply_technology', 'vintage']
        index = pd.MultiIndex.from_product(full_levels, names=full_names)
        self.stock.values = util.empty_df(index=index, columns=pd.Index(columns, dtype='object'))
        self.stock.exist = util.empty_df(index=index, columns=pd.Index(columns, dtype='object'),fill_value=1.0)
        self.stock.values_energy = copy.deepcopy(self.stock.values)
        self.stock.values_normal = copy.deepcopy(self.stock.values)
        self.stock.values_normal_energy = copy.deepcopy(self.stock.values)
        self.stock.ones = util.empty_df(index=index, columns=pd.Index(columns, dtype='object'), fill_value=1.0)
        self.stock.capacity_factor = util.empty_df(index=index, columns=pd.Index(columns, dtype='object'), fill_value=1.0)
        self.stock.capacity_factor_rio = util.empty_df(index=index, columns=pd.Index(columns, dtype='object'), fill_value=1.0)
        for year in self.years:
            self.stock.capacity_factor.loc[:,year] = self.rollover_output(tech_class='capacity_factor',stock_att='ones',year=year, non_expandable_levels=None,fill_value=1.0)
            self.stock.capacity_factor_rio.loc[:, year] = self.rollover_output(tech_class='capacity_factor', stock_att='ones', year=year, non_expandable_levels=None, fill_value=1.0)
        self.stock.remaining = util.empty_df(index=index, columns=pd.Index(columns, dtype='object'))
        self.stock.dispatch_cap = util.empty_df(index=index, columns=pd.Index(columns, dtype='object'))
        self.stock.preview = util.empty_df(index=index, columns=pd.Index(columns, dtype='object'))
        self.stock.values_new = copy.deepcopy(self.stock.values)
        self.stock.values_replacement = copy.deepcopy(self.stock.values)
        self.stock.values_normal = copy.deepcopy(self.stock.values)
        self.stock.values_financial = copy.deepcopy(self.stock.values)
        self.stock.values_financial_new = copy.deepcopy(self.stock.values)
        self.stock.values_financial_replacement = copy.deepcopy(self.stock.values)
        full_levels = self.stock.rollover_group_levels + [self.technologies.keys()] + [self.vintages]
        full_names = self.stock.rollover_group_names + ['supply_technology', 'vintage']
        index = pd.MultiIndex.from_product(full_levels, names=full_names)
        self.stock.retirements = util.empty_df(index=index, columns=['value'])
        self.stock.retirements_early = copy.deepcopy(self.stock.retirements)
        self.stock.retirements_natural = copy.deepcopy(self.stock.retirements)
        self.stock.sales = util.empty_df(index=index, columns=['value'])
        self.stock.sales_new = copy.deepcopy(self.stock.sales)
        self.stock.sales_replacement = copy.deepcopy(self.stock.sales)
        self.stock.sales_exist = util.empty_df(index=index, columns=['value'],fill_value = 1.0)
        full_levels = self.stock.rollover_group_levels + [self.vintages]
        full_names = self.stock.rollover_group_names +  ['vintage']
        index = pd.MultiIndex.from_product(full_levels, names=full_names)
        self.stock.sales_share_reconcile =  util.empty_df(index=index, columns=['value'],fill_value=1.0)

    def update_stock(self, year, loop):
        """updates the stock in the IO loop"""
        if self.thermal_dispatch_node:
            self.determine_throughput(year,loop)
            self.update_remaining_stock(year, loop)
            self.update_technology_dispatch(year)
            self.update_total_dispatch(year)
            self.update_requirement_dispatch(year)
        else:
            self.determine_throughput(year,loop)
            self.update_remaining_stock(year, loop)
            self.update_technology(year)
            self.update_total(year)
            self.update_requirement(year, loop)
        self.stock_rollover(year, loop, self.stock.act_stock_changes)
            
    def determine_throughput(self,year,loop):
        if year == cfg.getParamAsInt('current_year') and loop == 'initial':
            #in the initial loop of the supply-side, we only know internal demand
            self.throughput = self.active_demand
        else:
            self.throughput = self.active_supply
        if self.throughput is not None:
            remove_levels = [x for x in self.throughput.index.names if x not in self.stock.requirement_energy.index.names]
            self.throughput = util.remove_df_levels(self.throughput,remove_levels)
        self.throughput[self.throughput<=0] = 0
        if self.potential.raw_values is not None:
            self.potential.remap_to_potential_and_normalize(self.throughput, year, self.tradable_geography)

    def calculate_actual_stock(self,year,loop):
        """used to calculate the actual throughput of built stock. This is used to adjust the stock values if it does not
        match the required throughput in the year."""
#        for elements in self.rollover_groups.keys():
#            self.stock.values.loc[elements, year]
        self.stock.values_energy.loc[:, year] = DfOper.mult([self.stock.capacity_factor.loc[:,year].to_frame(), self.stock.values.loc[:,year].to_frame()]) * UnitConverter.unit_convert(unit_from_den=cfg.getParam('time_step'), unit_to_den='year')

    def calculate_adjustment_factor(self,year):
        """used to calculate the adjustment factor for this year's sales to make sure the stock energy meets the required
        energy"""
        num = DfOper.subt([self.stock.requirement_energy.loc[:,year].to_frame(),self.stock.act_rem_energy.groupby(level=self.stock.rollover_group_names).sum()])
        den = DfOper.subt([self.stock.values_energy.loc[:, year].to_frame().groupby(level=self.stock.rollover_group_names).sum(),self.stock.act_rem_energy.groupby(level=self.stock.rollover_group_names).sum()])
        factor = DfOper.divi([num,den]).fillna(1)
        factor = factor.replace(np.inf,1)
        factor[factor<0] = 1
        self.active_adjustment_factor = factor
        return factor

    def update_remaining_stock(self,year, loop):
        for elements in self.rollover_groups.keys():
            elements = util.ensure_tuple(elements)
            element_indexer= util.level_specific_indexer(self.stock.remaining, self.stock.rollover_group_names,elements)
            if loop == 1 or loop == 'initial':
                if year == cfg.getParamAsInt('current_year') and loop == 1:
                    self.rollover_dict[elements].rewind(1)
                self.stock.remaining.loc[element_indexer, year] = self.rollover_dict[elements].return_formatted_stock(year_offset=1)
            else:
                self.rollover_dict[elements].rewind(1)
                self.stock.preview.loc[element_indexer,year] = self.rollover_dict[elements].return_formatted_stock(year_offset=0)
        self.set_energy_capacity_ratios(year,loop)

    def set_energy_capacity_ratios(self,year,loop):
       if loop == 1 or loop == 'initial':
            self.stock.act_rem_energy = DfOper.mult([self.stock.remaining.loc[:,year].to_frame(),self.stock.capacity_factor.loc[:,year].to_frame()]) * UnitConverter.unit_convert(unit_from_den=cfg.getParam('time_step'), unit_to_den='year')
            exist_cap_factor = self.stock.capacity_factor.loc[:,year].to_frame()
            exist_cap_factor[exist_cap_factor==0]=np.nan
            default_conversion = exist_cap_factor.groupby(level=self.stock.rollover_group_names).mean().fillna(1)*UnitConverter.unit_convert(unit_from_num='year',unit_to_num=cfg.getParam('time_step'))
            default_conversion[default_conversion==0] = 1
            self.stock.act_energy_capacity_ratio = util.DfOper.divi([util.remove_df_levels(self.stock.act_rem_energy,['vintage','supply_technology']),
                                                                    util.remove_df_levels(self.stock.remaining.loc[:, year].to_frame(),['vintage','supply_technology'])]).fillna(default_conversion)
            self.stock.act_energy_capacity_ratio[self.stock.act_energy_capacity_ratio==0] = default_conversion
       else:
           preview = util.df_slice(self.stock.preview.loc[:,year].to_frame(), year, 'vintage')
           preview_energy = util.DfOper.mult([preview,util.df_slice(self.stock.capacity_factor.loc[:,year].to_frame(),year,'vintage')])*UnitConverter.unit_convert(unit_from_den=cfg.getParam('time_step'), unit_to_den='year')
           preview = util.remove_df_levels(preview,['vintage','supply_technology'])
           preview_energy = util.remove_df_levels(preview_energy,['vintage','supply_technology'])
           exist_cap_factor = DfOper.divi([DfOper.mult([self.stock.capacity_factor.loc[:,year].to_frame(),self.stock.values.loc[:,year].to_frame()]).groupby(level=self.stock.rollover_group_names).sum(),self.stock.values.loc[:,year].to_frame().groupby(level=self.stock.rollover_group_names).sum()])
           exist_cap_factor[exist_cap_factor==0]=np.nan
           default_conversion = exist_cap_factor.fillna(1)*UnitConverter.unit_convert(unit_from_num='year',unit_to_num=cfg.getParam('time_step'))
           default_conversion[default_conversion==0] = 1
           self.stock.act_rem_energy = util.DfOper.mult([self.stock.remaining.loc[:,year].to_frame(),self.stock.capacity_factor.loc[:,year].to_frame()]) * UnitConverter.unit_convert(unit_from_den=cfg.getParam('time_step'), unit_to_den='year')
           self.stock.act_energy_capacity_ratio = util.DfOper.divi([util.remove_df_levels(self.stock.act_rem_energy,['vintage','supply_technology']),
                                                                    util.remove_df_levels(self.stock.remaining.loc[:, year].to_frame(),['vintage','supply_technology'])]).fillna(default_conversion)
           self.stock.act_energy_capacity_ratio[self.stock.act_energy_capacity_ratio==0] = default_conversion
           self.stock.preview_energy_capacity_ratio = util.DfOper.divi([preview_energy,preview]).fillna(self.stock.act_energy_capacity_ratio)

    def update_technology(self, year):
        """sets the minimum necessary stock by technology based on remaining stock after natural rollover and technology stock amounts"""
        self.stock.act_tech_energy = util.DfOper.mult([self.stock.technology.loc[:,year].to_frame(), self.stock.act_energy_capacity_ratio],fill_value=np.nan)
        self.stock.act_tech_or_rem_energy = self.stock.act_tech_energy.fillna(self.stock.act_rem_energy.groupby(level=self.stock.act_tech_energy.index.names).sum())
        self.stock.act_tech_or_rem = util.remove_df_levels(util.DfOper.divi([self.stock.act_tech_or_rem_energy, self.stock.act_energy_capacity_ratio]),'supply_technology')

    def update_technology_dispatch(self, year):
        """sets the minimum necessary stock by technology based on remaining stock after natural rollover and technology stock amounts"""
        self.stock.act_tech = self.stock.technology.loc[:,year].to_frame()
        self.stock.act_rem = (self.stock.remaining.loc[:,year].to_frame().groupby(level=util.ix_incl(self.stock.act_tech,self.stock.act_tech.index.names)).sum())
        self.stock.act_tech_or_rem = self.stock.act_tech.fillna(self.stock.act_rem)
        self.stock.act_tech_or_rem = DfOper.add([self.stock.act_tech_or_rem,util.remove_df_levels(self.stock.dispatch_cap.loc[:,year].to_frame(),'vintage')])

    def update_total(self, year):
        """sets the minimum necessary total stock - based on throughput (stock requirement) and total of the technology and remaining stock"""
        self.stock.act_total_energy = DfOper.mult([self.stock.total.loc[:,year].to_frame(), self.stock.act_energy_capacity_ratio],fill_value=np.nan)
        self.stock.act_total_energy = self.stock.act_total_energy.fillna(self.stock.act_tech_or_rem_energy.groupby(level=self.stock.rollover_group_names).sum())

    def update_total_dispatch(self, year):
        """sets the minimum necessary total stock - based on throughput (stock requirement) and total of the technology and remaining stock"""
        self.stock.act_total= util.DfOper.add([self.stock.total.loc[:,year].to_frame(),util.remove_df_levels(self.stock.dispatch_cap.loc[:,year].to_frame(),['supply_technology','vintage'])])
        self.stock.act_total = self.stock.act_total.fillna(self.stock.act_tech_or_rem.groupby(level=self.stock.rollover_group_names).sum())

    def update_requirement(self,year,loop):
        """updates annual stock requirements with the maximum of required stock and specified and remaining natural rolloff. Also
        distributes the necessary stock changes to the available residuals in the supply curve bins if the stock has resource_bin indexers
        """
        previous_year = max(min(self.years),year-1)
        if self.potential._has_data is False:
            if self.throughput is not None:
                if cfg.rio_supply_run and self.name not in cfg.rio_excluded_nodes:
                    self.stock.requirement_energy.loc[:, year] = 0
                else:
                    self.stock.requirement_energy.loc[:, year] = self.throughput
            a = copy.deepcopy(self.stock.requirement_energy.loc[:,year].to_frame())
            b = copy.deepcopy(self.stock.act_total_energy)
            b[b<a] = a
            self.stock.requirement_energy.loc[:,year] = b
            self.stock.requirement.loc[:,year] = DfOper.divi([self.stock.requirement_energy.loc[:,year].to_frame(),self.stock.act_energy_capacity_ratio])
        else:
            #calculates the total amount of energy needed to distribute
            total_residual = util.DfOper.subt([self.throughput, self.stock.act_total_energy],expandable=(False,False), collapsible=(True,True))
            total_residual[total_residual<0] = 0
            #calculates the residual amount of energy available in each bin
            df = util.remove_df_elements(self.potential.values,[x for x in GeoMapper.geography_to_gau_unfiltered[GeoMapper.supply_primary_geography] if x not in GeoMapper.supply_geographies],GeoMapper.supply_primary_geography)
            bins = util.DfOper.subt([df[year].to_frame(), self.stock.act_total_energy],expandable=(False,False), collapsible=(True,True))
            bins = bins.reset_index().set_index(bins.index.names)
            bins[bins<0] = 0
            #calculates the supply curve of remaining energy
            bin_supply_curve = bins.groupby(level=[x for x in self.stock.rollover_group_names if x!= 'resource_bin']).cumsum()
            #expands the total energy needed to distribute to mask against the supply curve. Used as a cap on the supply curve.
            total_residual = util.expand_multi(total_residual,bins.index.levels,bins.index.names)
            bin_supply_curve[bin_supply_curve>total_residual] = total_residual
            bin_supply_curve = bin_supply_curve.groupby(level=util.ix_excl(bin_supply_curve,'resource_bin')).diff().fillna(bin_supply_curve)
            if cfg.rio_supply_run and self.name not in cfg.rio_excluded_nodes:
                self.stock.requirement_energy.loc[:,year] = self.stock.act_total_energy
                self.stock.requirement.loc[:,year] = util.DfOper.divi([self.stock.requirement_energy.loc[:,year].to_frame(),self.stock.act_energy_capacity_ratio])
            else:
                self.stock.requirement_energy.loc[:,year] = util.DfOper.add([self.stock.act_total_energy, bin_supply_curve])
                self.stock.requirement.loc[:,year] = util.DfOper.divi([self.stock.requirement_energy.loc[:,year].to_frame(),self.stock.act_energy_capacity_ratio])
        if year == cfg.getParamAsInt('current_year') and year==min(self.years):
            self.stock.act_stock_energy_changes = self.stock.requirement_energy[year].to_frame()*0
#            self.stock.act_stock_capacity_changes = 0
#            self.stock.act_max_negative_stock_capacity_changes = 0
        else:
            self.stock.act_stock_energy_changes = util.DfOper.subt([self.stock.requirement_energy[year].to_frame(),
                                                        util.remove_df_levels(self.stock.values_energy[previous_year].to_frame(),['vintage','supply_technology'])])

#            self.stock.act_stock_capacity_changes = DfOper.subt([self.stock.total[year].to_frame(),util.remove_df_levels(self.stock.values[previous_year].to_frame(),['vintage','supply_technology'])],fill_value=np.nan)
#            self.stock.act_max_negative_stock_capacity_changes = DfOper.subt([self.stock.total_min[year].to_frame(),util.remove_df_levels(self.stock.values[previous_year].to_frame(),['vintage','supply_technology'])],fill_value=np.nan)
        if loop == 'initial' or loop ==1:
            needed_capacity_ratio = self.stock.act_energy_capacity_ratio
        else:
            needed_capacity_ratio = self.stock.preview_energy_capacity_ratio
        if_positive_stock_changes = util.DfOper.divi([self.stock.act_stock_energy_changes,needed_capacity_ratio]).fillna(0)
        if_negative_stock_changes = util.DfOper.divi([self.stock.act_stock_energy_changes,self.stock.act_energy_capacity_ratio]).fillna(0)
        max_retirable = -self.stock.values.loc[:,previous_year].to_frame().groupby(level=self.stock.rollover_group_names).sum()
        max_retirable.columns = [year]
#        if_negative_stock_changes[self.stock.act_stock_capacity_changes<if_negative_stock_changes] = self.stock.act_stock_capacity_changes
        if_negative_stock_changes[if_negative_stock_changes<=max_retirable]=max_retirable
#        if_negative_stock_changes[if_negative_stock_changes<=self.stock.act_max_negative_stock_capacity_changes]=self.stock.act_max_negative_stock_capacity_changes
        if_positive_stock_changes[if_positive_stock_changes<0] = if_negative_stock_changes
#        if_positive_stock_changes[self.stock.act_stock_capacity_changes>if_positive_stock_changes] = self.stock.act_stock_capacity_changes
        self.stock.act_stock_changes = if_positive_stock_changes
#        self.stock.act_stock_changes[self.stock.act_stock_changes<self.stock.act_stock_capacity_changes] = self.stock.act_stock_capacity_changes
        self.stock.act_stock_changes = self.stock.act_stock_changes[year]

    def update_requirement_dispatch(self,year):
        """updates annual stock requirements with the maximum of required stock and specified and remaining natural rolloff.
        """
        previous_year = max(min(self.years),year-1)
        #TODO Flexible Nodes can't have SupplyPotential
        self.stock.requirement.loc[:,year] = self.stock.act_total
        if year == cfg.getParamAsInt('current_year') and year==min(self.years):
            self.stock.act_stock_changes = self.stock.requirement[year].to_frame()*0
        else:
            #stock changes only equal capacity added from the dispatch
            self.stock.act_stock_changes = util.DfOper.subt([self.stock.requirement.loc[:,year].to_frame(), util.remove_df_levels(self.stock.values[previous_year].to_frame(),['vintage','supply_technology'])])
        self.stock.act_stock_changes = self.stock.act_stock_changes[year]

    def setup_financial_stock(self):
        for tech in self.technologies.values():
            # creates binary matrix across years and vintages for a technology based on its book life
            tech.book_life_matrix = util.book_life_df(tech.book_life, self.vintages, self.years)
            # creates a linear decay of initial stock
            tech.initial_book_life_matrix = util.initial_book_life_df(tech.book_life, tech.mean_lifetime, self.vintages, self.years)

    def financial_stock(self, year, loop):
        """
        Calculates the amount of stock based on sales and technology book life
        instead of physical decay
        """
        # reformat the book_life_matrix dataframes to match the stock dataframe
        # creates a list of formatted tech dataframes and concatenates them
        tech_dfs = [self.reformat_tech_df(self.stock.sales, tech, tech_class=None, tech_att='book_life_matrix', tech_name=tech.name, year=year) for
            tech in self.technologies.values()]
        tech_df = pd.concat(tech_dfs)
        # initial_stock_df uses the stock values dataframe and removes vintagesot
        initial_stock_df = self.stock.values[min(self.years)]
        # formats tech dfs to match stock df
        initial_tech_dfs = [self.reformat_tech_df(initial_stock_df, tech, tech_class=None, tech_att='initial_book_life_matrix',tech_name=tech.name, year=year) for tech in self.technologies.values()]
        initial_tech_df = pd.concat(initial_tech_dfs)
        # stock values in any year equals vintage sales multiplied by book life
        values_financial_new = DfOper.mult([self.stock.sales_new, tech_df])
        values_financial_new.columns = [year]
        values_financial_replacement = DfOper.mult([self.stock.sales_replacement, tech_df])
        values_financial_replacement.columns = [year]
        # initial stock values in any year equals stock.values multiplied by the initial tech_df
        initial_values_financial_new = DfOper.mult([self.stock.values_new.loc[:,year].to_frame(), initial_tech_df],non_expandable_levels=None)
        initial_values_financial_replacement = DfOper.mult([self.stock.values_replacement.loc[:,year].to_frame(), initial_tech_df],non_expandable_levels=None)
        # sum normal and initial stock values
        self.stock.values_financial_new.loc[:,year] = DfOper.add([values_financial_new, initial_values_financial_new], non_expandable_levels=None)
        self.stock.values_financial_replacement.loc[:,year] = DfOper.add(
            [values_financial_replacement, initial_values_financial_replacement],non_expandable_levels=None)

    def calculate_levelized_costs(self,year, loop):
        "calculates total and per-unit costs in a subsector with technologies"
        if not hasattr(self.stock,'capital_cost_new'):
            index = self.rollover_output(tech_class='capital_cost_new', tech_att= 'values_level', stock_att='values_normal_energy',year=year).index
            self.stock.capital_cost_new= util.empty_df(index, columns=self.years,fill_value=0)
            self.stock.capital_cost_replacement = util.empty_df(index, columns=self.years,fill_value=0)
            self.stock.capital_cost = util.empty_df(index, columns=self.years,fill_value=0)
            self.stock.installation_cost_new = util.empty_df(index, columns=self.years,fill_value=0)
            self.stock.installation_cost_replacement = util.empty_df(index, columns=self.years,fill_value=0)
            self.stock.installation_cost = util.empty_df(index, columns=self.years,fill_value=0)
            self.stock.fixed_om = util.empty_df(index, columns=self.years,fill_value=0)
            self.stock.variable_om = util.empty_df(index, columns=self.years,fill_value= 0)
            self.levelized_costs = util.empty_df(index, columns=self.years,fill_value= 0)
            index = pd.MultiIndex.from_product(self.stock.rollover_group_levels, names=self.stock.rollover_group_names)
            self.embodied_cost = util.empty_df(index, columns=self.years,fill_value=0)
            self.embodied_cost = util.remove_df_levels(self.embodied_cost,'resource_bin')

        self.stock.capital_cost_new.loc[:,year] = self.rollover_output(tech_class='capital_cost_new',tech_att='values_level',
                                                                         stock_att='values_financial_new',year=year)
        self.stock.capital_cost_replacement.loc[:,year] = self.rollover_output(tech_class='capital_cost_replacement',tech_att='values_level',
                                                                         stock_att='values_financial_replacement',year=year)
        self.stock.fixed_om.loc[:,year] =  self.rollover_output(tech_class='fixed_om',tech_att='values_level', stock_att='values',year=year)
        self.stock.variable_om.loc[:,year] = self.rollover_output(tech_class='variable_om',tech_att='values_level',
                                                                         stock_att='values_energy',year=year)
        self.stock.installation_cost_new.loc[:,year] = self.rollover_output(tech_class='installation_cost_new',tech_att='values_level',
                                                                         stock_att='values_financial_new',year=year)
        self.stock.installation_cost_replacement.loc[:,year] = self.rollover_output(tech_class='installation_cost_replacement',tech_att='values_level',
                                                                         stock_att='values_financial_replacement',year=year)
        self.stock.capital_cost.loc[:,year] = DfOper.add([self.stock.capital_cost_new.loc[:,year].to_frame(), self.stock.capital_cost_replacement.loc[:,year].to_frame()])
        self.stock.installation_cost.loc[:,year] = DfOper.add([self.stock.installation_cost_new.loc[:,year].to_frame(), self.stock.installation_cost_replacement.loc[:,year].to_frame()])
        self.levelized_costs.loc[:,year] = DfOper.add([self.stock.capital_cost.loc[:,year].to_frame(), self.stock.installation_cost.loc[:,year].to_frame(), self.stock.fixed_om.loc[:,year].to_frame(), self.stock.variable_om.loc[:,year].to_frame()])
        self.calculate_per_unit_costs(year)
        
    def calculate_per_unit_costs(self,year):
            total_costs = util.remove_df_levels(self.levelized_costs.loc[:,year].to_frame(),['vintage', 'supply_technology'])
            active_supply = self.active_supply[self.active_supply.values>=0]
            self.embodied_cost.loc[:,year] = DfOper.divi([total_costs, active_supply],expandable=(False,False)).replace([np.inf,np.nan,-np.nan],[0,0,0])
            self.active_embodied_cost = util.expand_multi(self.embodied_cost[year].to_frame(), levels_list = [GeoMapper.geography_to_gau[GeoMapper.supply_primary_geography], self.demand_sectors],levels_names=[GeoMapper.supply_primary_geography,'demand_sector'])

    def calculate_annual_costs(self,year):
        if not hasattr(self.stock,'capital_cost_new_annual'):
            index = self.stock.sales.index
            self.stock.capital_cost_new_annual= util.empty_df(index, columns=['value'],fill_value=0)
            self.stock.capital_cost_replacement_annual = util.empty_df(index, columns=['value'],fill_value=0)
            self.stock.installation_cost_new_annual = util.empty_df(index, columns=['value'],fill_value=0)
            self.stock.installation_cost_replacement_annual = util.empty_df(index, columns=['value'],fill_value=0)
        indexer = util.level_specific_indexer(self.stock.capital_cost_new_annual,'vintage', year)
        self.stock.capital_cost_new_annual.loc[indexer,:] = self.rollover_output(tech_class='capital_cost_new', tech_att= 'values', stock_att='sales_new',year=year)
        self.stock.capital_cost_replacement_annual.loc[indexer,:] = self.rollover_output(tech_class='capital_cost_replacement', tech_att= 'values', stock_att='sales_replacement',year=year)
        self.stock.installation_cost_new_annual.loc[indexer,:] = self.rollover_output(tech_class='installation_cost_new', tech_att= 'values', stock_att='sales_new',year=year)
        self.stock.installation_cost_replacement_annual.loc[indexer,:] = self.rollover_output(tech_class='installation_cost_new', tech_att= 'values', stock_att='sales_new',year=year)
        #in the last year of the analysis, these need to be concatenated together for output

    def concatenate_annual_costs(self):
        fixed_om = util.remove_df_levels(self.stock.fixed_om,'vintage').stack().to_frame()
        util.replace_index_name(fixed_om,'vintage',)
        fixed_om.columns = ['value']
        variable_om = util.remove_df_levels(self.stock.fixed_om,'vintage').stack().to_frame()
        util.replace_index_name(variable_om,'vintage')
        variable_om.columns = ['value']
        keys = ['capital cost - new', 'capital cost - replacement','installation cost - new','installation cost - replacement',
                'fixed om', 'variable om']
        keys = [x.upper() for x in keys]
        names = ['cost_type']
        self.final_annual_costs = pd.concat([self.stock.capital_cost_new_annual, self.stock.capital_cost_replacement_annual, self.stock.installation_cost_new_annual,
                                           self.stock.installation_cost_replacement_annual, fixed_om, variable_om],keys=keys, names=names)

    def concatenate_levelized_costs(self):
        keys = ['capital cost - new', 'capital cost - replacement','installation cost - new','installation cost - replacement',
                'fixed om', 'variable om']
        keys = [x.upper() for x in keys]
        names = ['cost_type']
        self.final_levelized_costs = pd.concat([self.stock.capital_cost_new, self.stock.capital_cost_replacement, self.stock.installation_cost_new,
                                           self.stock.installation_cost_replacement, self.stock.fixed_om, self.stock.variable_om],keys=keys, names=names)

    def calculate_dispatch_costs(self, year, embodied_cost_df, loop=None):
        self.calculate_dispatch_coefficients(year, loop)
        if not isinstance(self, StorageNode):
            self.active_dispatch_costs = copy.deepcopy(self.active_trade_adjustment_df)
            for node in list(set(self.active_trade_adjustment_df.index.get_level_values('supply_node'))):
                embodied_cost_indexer = util.level_specific_indexer(embodied_cost_df, 'supply_node',node)
                trade_adjustment_indexer = util.level_specific_indexer(self.active_trade_adjustment_df, 'supply_node',node)
                self.active_dispatch_costs.loc[trade_adjustment_indexer,:] = util.DfOper.mult([self.active_trade_adjustment_df.loc[trade_adjustment_indexer,:],embodied_cost_df.loc[embodied_cost_indexer,:]]).values
            self.active_dispatch_costs = self.active_dispatch_costs.groupby(level='supply_node').sum()
            self.active_dispatch_costs = self.active_dispatch_costs.stack([GeoMapper.supply_primary_geography,'demand_sector'])
            self.active_dispatch_costs = util.reduce_levels(self.active_dispatch_costs, self.stock.rollover_group_names+['supply_node'], agg_function='mean')
            self.active_dispatch_costs = util.DfOper.mult([self.active_dispatch_costs.to_frame(), self.active_dispatch_coefficients])
            self.active_dispatch_costs = util.remove_df_levels(self.active_dispatch_costs, 'supply_node')
            self.active_dispatch_costs = self.active_dispatch_costs.reorder_levels(self.stock.values.index.names)
            self.active_dispatch_costs = util.DfOper.add([self.active_dispatch_costs,self.rollover_output(tech_class='variable_om', tech_att= 'values_level', stock_att='ones',year=year)])
            self.active_dispatch_costs[self.active_dispatch_costs<0] = 0

    def stock_normalize(self,year):
        """returns normalized stocks for use in other node calculations"""
        self.stock.values_normal.loc[:,year] = self.stock.values.loc[:,year].to_frame().groupby(level=[x for x in self.stock.rollover_group_names if x!='resource_bin']).transform(lambda x: x / x.sum()).fillna(0)
        self.stock.values_normal_energy.loc[:,year] = DfOper.mult([self.stock.values.loc[:,year].to_frame(), self.stock.capacity_factor.loc[:,year].to_frame()]).groupby(level=[x for x in self.stock.rollover_group_names if x!='resource_bin']).transform(lambda x: x / x.sum()).fillna(0)
        self.stock.values_normal.loc[:,year].replace(np.inf,0,inplace=True)
        self.stock.values_normal_energy.loc[:,year].replace(np.inf,0,inplace=True)

    def calculate_co2_capture_rate(self,year):
         if not hasattr(self,'co2_capture_rate'):
             index = self.rollover_output(tech_class='co2_capture',stock_att='values_normal_energy',year=year).index
             self.co2_capture_rate= util.empty_df(index, columns=self.years,fill_value=0)
         self.co2_capture_rate.loc[:,year] = self.rollover_output(tech_class = 'co2_capture', stock_att='values_normal_energy',year=year)
         self.active_co2_capture_rate = util.remove_df_levels(self.co2_capture_rate.loc[:,year].to_frame(),['supply_technology','vintage'])

    def calculate_active_coefficients(self, year,loop):
        """
        Calculate rollover efficiency outputs for a supply node
        """
        self.stock_normalize(year)
        if hasattr(self.stock,'coefficients'):
                self.stock.coefficients.loc[:,year] = self.rollover_output(tech_class='efficiency',
                                                                             stock_att='values_normal_energy',year=year)
                self.stock.coefficients_rio.loc[:,year] = self.rollover_output(tech_class='efficiency',
                                                                             stock_att='ones',year=year)
        else:
            index = self.rollover_output(tech_class='efficiency',stock_att='values_normal_energy',year=year).index
            self.stock.coefficients = util.empty_df(index, columns=self.years,fill_value=0.)
            self.stock.coefficients_rio = util.empty_df(index, columns=self.years, fill_value=0.)
            self.stock.coefficients.loc[:,year] = self.rollover_output(tech_class='efficiency',stock_att='values_normal_energy',year=year)
            self.stock.coefficients_rio.loc[:, year] = self.rollover_output(tech_class='efficiency', stock_att='ones', year=year)
        if cfg.rio_supply_run and 'supply_node' in self.stock.coefficients.index.names:
                self.stock.coefficients.loc[:, year][(self.stock.coefficients.loc[:, year].to_frame().index.get_level_values('supply_node').isin(cfg.rio_no_negative_blends)) & (self.stock.coefficients.loc[:, year].to_frame().values<0).flatten()] = 0
        if 'supply_node' not in self.stock.coefficients.index.names:
            print ("no efficiency has been input for technologies in the %s supply node" %self.name)
            index = pd.MultiIndex.from_product([self.name,GeoMapper.supply_geographies],names = ['supply_node', GeoMapper.supply_primary_geography],)
            columns = [year]
            self.stock.coefficients = pd.DataFrame(0, index=index, columns = columns)
            self.stock.coefficients_rio = pd.DataFrame(0, index=index, columns=columns)
        if 'demand_sector' not in self.stock.rollover_group_names:
            keys = self.demand_sectors
            name = ['demand_sector']
            self.active_coefficients = util.remove_df_levels(pd.concat([self.stock.coefficients.loc[:,year].to_frame()]*len(keys), keys=keys,names=name).fillna(0),['supply_technology', 'vintage','resource_bin'])
            self.active_coefficients_untraded = copy.deepcopy(self.active_coefficients)
            self.active_coefficients_untraded.sort(inplace=True,axis=0)
            self.active_coefficients_total_untraded = util.remove_df_levels(self.active_coefficients,['efficiency_type']).reorder_levels([GeoMapper.supply_primary_geography,'demand_sector', 'supply_node']).sort_index().fillna(0)
        else:
            self.active_coefficients = util.remove_df_levels(self.stock.coefficients.loc[:,year].to_frame().fillna(0),['supply_technology', 'vintage','resource_bin'])
            self.active_coefficients_untraded = copy.deepcopy(self.active_coefficients)
            self.active_coefficients_untraded.sort(inplace=True,axis=0)
            self.active_coefficients_total_untraded = util.remove_df_levels(self.active_coefficients,['efficiency_type']).reorder_levels([GeoMapper.supply_primary_geography,'demand_sector', 'supply_node']).sort_index().fillna(0)
        self.active_coefficients_total = DfOper.mult([self.add_column_index(self.active_coefficients_total_untraded),self.active_trade_adjustment_df]).fillna(0)
        nodes = list(set(self.active_trade_adjustment_df.index.get_level_values('supply_node')))
        if len(nodes):
            df_list = []
            for node in nodes:
                trade_indexer = util.level_specific_indexer(self.active_trade_adjustment_df, 'supply_node', node)
                coefficient_indexer = util.level_specific_indexer(self.active_coefficients_untraded, 'supply_node', node)
                efficiency_types = list(set(self.active_coefficients_untraded.loc[coefficient_indexer,:].index.get_level_values('efficiency_type')))
                keys = efficiency_types
                name = ['efficiency_type']
                df = pd.concat([self.active_trade_adjustment_df.loc[trade_indexer,:]]*len(keys),keys=keys,names=name)
                df_list.append(df)
            active_trade_adjustment_df = pd.concat(df_list)
            self.active_coefficients = DfOper.mult([self.add_column_index(self.active_coefficients),active_trade_adjustment_df])
            keys = self.ghgs
            name = ['ghg']
            self.active_emissions_coefficients = pd.concat([self.active_coefficients]*len(keys), keys=keys, names=name)
            self.active_emissions_coefficients = self.active_emissions_coefficients.reorder_levels([GeoMapper.supply_primary_geography,'demand_sector', 'supply_node', 'efficiency_type', 'ghg'])
            self.active_emissions_coefficients.sort(inplace=True)

    def calculate_dispatch_coefficients(self, year,loop):
        """
            Calculates operating costs for all technology/vintage combinations
        """
        if loop == 3:
            if hasattr(self.stock,'dispatch_coefficients'):
                self.stock.dispatch_coefficients.loc[:,year] = self.rollover_output(tech_class='efficiency',
                                                                             stock_att='exist',year=year)

            else:
                index = self.rollover_output(tech_class='efficiency',stock_att='exist',year=year).index
                self.stock.dispatch_coefficients = util.empty_df(index, columns=self.years,fill_value=0)
                self.stock.dispatch_coefficients.loc[:,year] = self.rollover_output(tech_class='efficiency', stock_att='exist',year=year)
            self.active_dispatch_coefficients = self.stock.dispatch_coefficients.loc[:,year].to_frame()
            self.active_dispatch_coefficients= util.remove_df_levels(self.active_dispatch_coefficients,['efficiency_type'])

    def calculate_capacity_utilization(self,energy_supply,supply_years):
        energy_stock = self.stock.values[supply_years] * UnitConverter.unit_convert(1,unit_from_den='hour', unit_to_den='year')
        self.capacity_utilization = util.DfOper.divi([energy_supply,energy_stock],expandable=False).replace([np.inf,np.nan,-np.nan],[0,0,0])



    def rollover_output(self, tech_class=None, tech_att='values', stock_att=None, year=None, non_expandable_levels=('year', 'vintage'),fill_value=0.0):
        """ Produces rollover outputs for a node stock based on the tech_att class, att of the class, and the attribute of the stock
        """
        stock_df = getattr(self.stock, stock_att)
        stock_df = stock_df.sort_index()
        tech_classes = util.put_in_list(tech_class)
        tech_dfs = []
        for tech_class in tech_classes:
            tech_dfs += ([self.reformat_tech_df(stock_df, tech, tech_class, tech_att, tech.name, year) for tech in
                                self.technologies.values() if hasattr(getattr(tech, tech_class), tech_att) and getattr(getattr(tech, tech_class),tech_att) is not None])
        if len(tech_dfs):
            first_tech_order = tech_dfs[0].index.names
            for x, value in enumerate(tech_dfs):
                if 'resource_bin' in first_tech_order and 'resource_bin' not in value.index.names:
                   tech_dfs[x] =  util.add_and_set_index(value,'resource_bin',[1])
            tech_df = pd.concat([x.reorder_levels(first_tech_order) for x in tech_dfs])
            tech_df = tech_df.reorder_levels([x for x in stock_df.index.names if x in tech_df.index.names]+ [x for x in tech_df.index.names if x not in stock_df.index.names])
            tech_df = tech_df.sort_index()
            if year in stock_df.columns.values:
                result_df = util.DfOper.mult((stock_df.loc[:,year].to_frame(),tech_df), expandable=(True, True), collapsible=(True, False),non_expandable_levels=non_expandable_levels,fill_value=fill_value)
            else:
                stock_vintage_indexer = util.level_specific_indexer(stock_df,'vintage', year)
                tech_vintage_indexer = util.level_specific_indexer(tech_df, 'vintage', year)
                result_df = DfOper.mult((stock_df.loc[stock_vintage_indexer,:], tech_df.loc[tech_vintage_indexer,:]), expandable=(True, True), collapsible=(True, False), non_expandable_levels=non_expandable_levels,fill_value=fill_value)
                #TODO shouldn't be necessary
                result_vintage_indexer = util.level_specific_indexer(result_df, 'vintage', year)
                result_df = result_df.loc[result_vintage_indexer,:]
            return result_df
        else:
            if year in stock_df.columns.values:
                stock_df.loc[:,year] = fill_value
                return stock_df.loc[:,year].to_frame()
            else:
                vintage_indexer = util.level_specific_indexer(stock_df,'vintage', year)
                stock_df.loc[vintage_indexer,:] = fill_value
                return stock_df.loc[vintage_indexer,:]

    def reformat_tech_df(self, stock_df, tech, tech_class, tech_att, tech_name, year):
        """
        reformat technology dataframes for use in stock-level dataframe operations
        """
        if tech_class is None:
            tech_df = getattr(tech, tech_att)
        else:
            tech_df = getattr(getattr(tech, tech_class), tech_att)
        if 'supply_technology' not in tech_df.index.names:
            tech_df['supply_technology'] = tech_name
            tech_df.set_index('supply_technology', append=True, inplace=True)
        if year in tech_df.columns.values:
            #tech df has a year/vintage structure. We locate the values for year of all vintages
            tech_df = tech_df.loc[:,year].to_frame()
        else:
            #tech has a vintage/value structure. We locate the values for the year's vintage
            indexer = util.level_specific_indexer(tech_df, 'vintage', year)
            tech_df = tech_df.loc[indexer,:]
        return tech_df


class StorageNode(SupplyStockNode):
    def __init__(self, name, scenario, **kwargs):
        SupplyStockNode.__init__(self, name, scenario, **kwargs)

    def add_technology(self, name):
        """
        Adds technology instances to node
        """
        if name in self.technologies:
            logging.debug("Warning, storage tech {} was added twice to node {}".format(name, self.name))
            return
        self.technologies[name] = StorageTechnology(name, self.cost_of_capital, self.scenario)
        self.tech_names.append(name)

    def determine_throughput(self,year,loop):
        if year == cfg.getParamAsInt('current_year') and loop == 'initial':
            #in the initial loop of the supply-side, we only know internal demand
            self.throughput = self.active_demand
        else:
            self.throughput = self.active_supply
        if self.throughput is not None:
            remove_levels = [x for x in self.throughput.index.names if x not in self.stock.requirement_energy.index.names]
            self.throughput = util.remove_df_levels(self.throughput,remove_levels)
        self.throughput[self.throughput>=0] = 1E-10


    def calculate_levelized_costs(self,year, loop):
        "calculates per-unit costs in a subsector with technologies"
        if not hasattr(self.stock,'capital_cost_new_energy'):
            index = self.rollover_output(tech_class='capital_cost_new_energy', tech_att= 'values_level', stock_att='values_normal_energy',year=year).index
            self.stock.capital_cost_new_energy= util.empty_df(index, columns=self.years,fill_value=0)
            self.stock.capital_cost_replacement_energy = util.empty_df(index, columns=self.years,fill_value=0)
            self.stock.capital_cost_new_capacity= util.empty_df(index, columns=self.years,fill_value=0)
            self.stock.capital_cost_replacement_capacity = util.empty_df(index, columns=self.years,fill_value=0)
            self.stock.capital_cost = util.empty_df(index, columns=self.years,fill_value=0)
            self.stock.installation_cost_new = util.empty_df(index, columns=self.years,fill_value=0)
            self.stock.installation_cost_replacement = util.empty_df(index, columns=self.years,fill_value=0)
            self.stock.installation_cost = util.empty_df(index, columns=self.years,fill_value=0)
            self.stock.fixed_om = util.empty_df(index, columns=self.years,fill_value=0)
            self.stock.variable_om = util.empty_df(index, columns=self.years,fill_value= 0)
            self.levelized_costs = util.empty_df(index, columns=self.years,fill_value= 0)
            index = pd.MultiIndex.from_product(self.stock.rollover_group_levels, names=self.stock.rollover_group_names)
            self.embodied_cost = util.empty_df(index, columns=self.years,fill_value=0)
        self.stock.values_financial_new_energy = copy.deepcopy(self.stock.values_financial_new.loc[:,year].to_frame())
        self.stock.values_financial_replacement_energy = copy.deepcopy(self.stock.values_financial_replacement.loc[:,year].to_frame())
        for tech in self.technologies.values():
            tech_indexer = util.level_specific_indexer(self.stock.values_financial_new,['supply_technology'], [tech.name])
            year_indexer = util.level_specific_indexer(tech.duration.values,'year', year)
            self.stock.values_financial_new_energy.loc[tech_indexer,:] = util.DfOper.mult([self.stock.values_financial_new.loc[tech_indexer,year].to_frame(),util.remove_df_levels(tech.duration.values.loc[year_indexer,:],'year')])
            self.stock.values_financial_replacement_energy.loc[tech_indexer,:] = util.DfOper.mult([self.stock.values_financial_replacement.loc[tech_indexer,year].to_frame(), util.remove_df_levels(tech.duration.values.loc[year_indexer,:],'year')])
        self.stock.capital_cost_new_energy.loc[:,year] = self.rollover_output(tech_class='capital_cost_new_energy',tech_att='values_level',
                                                                         stock_att='values_financial_new_energy',year=year)
        self.stock.capital_cost_replacement_energy.loc[:,year] = self.rollover_output(tech_class='capital_cost_replacement_energy',tech_att='values_level',
                                                                         stock_att='values_financial_replacement_energy',year=year)
        self.stock.capital_cost_new_capacity.loc[:,year] = self.rollover_output(tech_class='capital_cost_new_capacity',tech_att='values_level',
                                                                         stock_att='values_financial_new',year=year)
        self.stock.capital_cost_replacement_capacity.loc[:,year] = self.rollover_output(tech_class='capital_cost_replacement_capacity',tech_att='values_level',
                                                                         stock_att='values_financial_replacement',year=year)
        self.stock.fixed_om.loc[:,year]=  self.rollover_output(tech_class='fixed_om',tech_att='values_level',
                                                                         stock_att='values',year=year)
        self.stock.variable_om.loc[:,year] = DfOper.mult([self.rollover_output(tech_class='variable_om',tech_att='values_level', stock_att='values_normal_energy',year=year), self.active_supply],non_expandable_levels=None).groupby(level=self.stock.variable_om.index.names).sum()
        self.stock.installation_cost_new.loc[:,year] = self.rollover_output(tech_class='installation_cost_new',tech_att='values_level',
                                                                         stock_att='values_financial_new',year=year)
        self.stock.installation_cost_replacement.loc[:,year] = self.rollover_output(tech_class='installation_cost_replacement',tech_att='values_level',
                                                                         stock_att='values_financial_replacement',year=year)
        self.stock.capital_cost.loc[:,year] = DfOper.add([self.stock.capital_cost_new_energy.loc[:,year].to_frame(), self.stock.capital_cost_replacement_energy.loc[:,year].to_frame(),self.stock.capital_cost_new_capacity.loc[:,year].to_frame(), self.stock.capital_cost_replacement_capacity.loc[:,year].to_frame()])
        self.stock.installation_cost.loc[:,year] = DfOper.add([self.stock.installation_cost_new.loc[:,year].to_frame(), self.stock.installation_cost_replacement.loc[:,year].to_frame()])
        self.levelized_costs.loc[:,year]= DfOper.add([self.stock.capital_cost.loc[:,year].to_frame(), self.stock.installation_cost.loc[:,year].to_frame(), self.stock.fixed_om.loc[:,year].to_frame(), self.stock.variable_om.loc[:,year].to_frame()])
        total_costs = util.remove_df_levels(self.levelized_costs.loc[:,year].to_frame(),['vintage', 'supply_technology'])
#        total_stock = util.remove_df_levels(self.stock.values_energy.loc[:,year].to_frame(), ['vintage', 'supply_technology'])
        self.embodied_cost.loc[:,year] = DfOper.divi([total_costs, self.active_supply.groupby(level=self.stock.rollover_group_names).sum()])
        self.active_embodied_cost = util.expand_multi(self.embodied_cost[year].to_frame(), levels_list = [GeoMapper.geography_to_gau[GeoMapper.supply_primary_geography], self.demand_sectors],levels_names=[GeoMapper.supply_primary_geography,'demand_sector'])

    def calculate_annual_costs(self,year):
        if not hasattr(self.stock,'capital_cost_new_annual_energy'):
            index = self.stock.sales.index
            self.stock.capital_cost_new_annual_energy= util.empty_df(index, columns=['value'],fill_value=0)
            self.stock.capital_cost_new_annual_capacity = util.empty_df(index, columns=['value'],fill_value=0)
            self.stock.capital_cost_replacement_annual_energy = util.empty_df(index, columns=['value'],fill_value=0)
            self.stock.capital_cost_replacement_annual_capacity = util.empty_df(index, columns=['value'],fill_value=0)
            self.stock.installation_cost_new_annual = util.empty_df(index, columns=['value'],fill_value=0)
            self.stock.installation_cost_replacement_annual = util.empty_df(index, columns=['value'],fill_value=0)
        indexer = util.level_specific_indexer(self.stock.capital_cost_new_annual_energy,'vintage', year)
        self.stock.capital_cost_new_annual_energy.loc[indexer,:] = self.rollover_output(tech_class='capital_cost_new_energy', tech_att= 'values', stock_att='sales_new',year=year)
        self.stock.capital_cost_new_annual_capacity.loc[indexer,:] = self.rollover_output(tech_class='capital_cost_new_capacity', tech_att= 'values', stock_att='sales_new',year=year)
        self.stock.capital_cost_replacement_annual_energy.loc[indexer,:] = self.rollover_output(tech_class='capital_cost_replacement_energy', tech_att= 'values', stock_att='sales_replacement',year=year)
        self.stock.capital_cost_replacement_annual_capacity.loc[indexer,:] = self.rollover_output(tech_class='capital_cost_replacement_capacity', tech_att= 'values', stock_att='sales_replacement',year=year)
        self.stock.installation_cost_new_annual.loc[indexer,:] = self.rollover_output(tech_class='installation_cost_new', tech_att= 'values', stock_att='sales_new',year=year)
        self.stock.installation_cost_replacement_annual.loc[indexer,:] = self.rollover_output(tech_class='installation_cost_new', tech_att= 'values', stock_att='sales_new',year=year)

    def concatenate_annual_costs(self):
        fixed_om = util.remove_df_levels(self.stock.fixed_om,'vintage').stack().to_frame()
        util.replace_index_name(fixed_om,'vintage')
        fixed_om.columns =['value']
        variable_om = util.remove_df_levels(self.stock.variable_om,'vintage').stack().to_frame()
        util.replace_index_name(variable_om,'vintage')
        variable_om.columns =['value']
        keys = ['capital cost energy - new', 'capital cost capacity - new', 'capital cost energy - replacement', 'capital cost capacity - replacement', 'installation cost - new','installation cost - replacement',
                'fixed om', 'variable om']
        keys = [x.upper() for x in keys]
        names = ['cost_type']
        self.final_annual_costs = pd.concat([self.stock.capital_cost_new_annual_energy, self.stock.capital_cost_new_annual_capacity, self.stock.capital_cost_replacement_annual_energy,self.stock.capital_cost_replacement_annual_capacity,
                                       self.stock.installation_cost_new_annual,
                                           self.stock.installation_cost_replacement_annual, fixed_om, variable_om], keys=keys, names=names)
    def concatenate_levelized_costs(self):
        keys = ['capital cost energy - new', 'capital cost capacity - new', 'capital cost energy - replacement', 'capital cost capacity - replacement', 'installation cost - new','installation cost - replacement',
                'fixed om', 'variable om']
        keys = [x.upper() for x in keys]
        names = ['cost_type']
        self.final_levelized_costs = pd.concat([self.stock.capital_cost_new_energy, self.stock.capital_cost_new_capacity, self.stock.capital_cost_replacement_energy,self.stock.capital_cost_replacement_capacity,
                                       self.stock.installation_cost_new,
                                           self.stock.installation_cost_replacement, self.stock.fixed_om, self.stock.variable_om], keys=keys, names=names)

    def calculate_dispatch_coefficients(self, year,loop):
        """
            Calculates operating costs for all technology/vintage combinations
        """

        self.stock.values_normal_tech = self.stock.values.loc[:,year].to_frame().groupby(level=[GeoMapper.supply_primary_geography,'supply_technology']).transform(lambda x: x/x.sum())
        self.stock.values_normal_tech.replace(np.inf,0,inplace=True)
        if loop == 3:
            if hasattr(self.stock,'dispatch_coefficients'):
                self.stock.dispatch_coefficients.loc[:,year] = self.rollover_output(tech_class='efficiency',
                                                                             stock_att='values_normal_tech',year=year)
            else:
                index = self.rollover_output(tech_class='efficiency',stock_att='exist',year=year).index
                self.stock.dispatch_coefficients = util.empty_df(index, columns=self.years,fill_value=0)
                self.stock.dispatch_coefficients.loc[:,year] = self.rollover_output(tech_class='efficiency',
                                                                             stock_att='values_normal_tech',year=year)
            self.active_dispatch_coefficients = self.stock.dispatch_coefficients.loc[:,year].to_frame().groupby(level=[GeoMapper.supply_primary_geography,'supply_node','supply_technology']).sum()
            self.active_dispatch_coefficients= util.remove_df_levels(self.active_dispatch_coefficients,['efficiency_type'])


class ImportNode(Node):
    def __init__(self, name, scenario):
        Node.__init__(self, name, scenario)
        self.cost = ImportCost(self.name, scenario)
        self.potential = SupplyPotential(self.name, self.enforce_potential_constraint, self.scenario)
        self.coefficients = SupplyCoefficients(self.name, self.scenario)

    def calculate(self):
        #all nodes can have potential conversions. Set to None if no data.
        self.conversion, self.resource_unit = self.add_conversion()
#        self.set_rollover_groups()
        self.calculate_subclasses()
        if self.coefficients.raw_values is not None:
            self.nodes = list(set(self.coefficients.values.index.get_level_values('supply_node')))
        self.set_trade_adjustment_dict()
        self.set_pass_through_df_dict()
        self.set_cost_dataframes()

    def calculate_levelized_costs(self,year,loop):
        "calculates the embodied costs of nodes with emissions"
        if hasattr(self,'cost') and self.cost._has_data is True:
            if hasattr(self,'potential') and self.potential._has_data is True and self.cost.cost_method == 'average':
                self.active_embodied_cost = self.calculate_avg_costs(year)
            elif hasattr(self,'potential') and self.potential._has_data is True and self.cost.cost_method == 'marginal':
                self.active_embodied_cost = self.calculate_marginal_costs(year)
            else:
                allowed_indices = ['demand_sector', GeoMapper.supply_primary_geography]
                if set(self.cost.values.index.names).issubset(allowed_indices):
                    self.active_embodied_cost = self.cost.values.loc[:,year].to_frame()
                    self.active_embodied_cost = util.expand_multi(self.active_embodied_cost, levels_list = [GeoMapper.geography_to_gau[GeoMapper.supply_primary_geography], self.demand_sectors],levels_names=[GeoMapper.supply_primary_geography,'demand_sector'])
                else:
                    raise ValueError("too many indexes in cost inputs of node %s" %self.name)
            self.levelized_costs.loc[:,year] = DfOper.mult([self.active_embodied_cost,self.active_supply]).values

    def calculate_annual_costs(self,year):
        if hasattr(self,'active_embodied_cost'):
            self.annual_costs.loc[:,year] = DfOper.mult([self.active_embodied_cost,self.active_supply]).values
        if year == cfg.getParamAsInt('end_year'):
            self.final_annual_costs = self.annual_costs



    def calculate_avg_costs(self,year):
        filter_geo_potential_normal = util.remove_df_elements(self.potential.active_supply_curve_normal, [x for x in GeoMapper.geography_to_gau_unfiltered[GeoMapper.supply_primary_geography] if x not in GeoMapper.supply_geographies],GeoMapper.supply_primary_geography)
        filter_geo_potential_normal = filter_geo_potential_normal.reset_index().set_index(filter_geo_potential_normal.index.names)
        supply_curve = filter_geo_potential_normal
        supply_curve = supply_curve[supply_curve.values>0]
        supply_curve = util.DfOper.mult([util.DfOper.divi([self.potential.values.loc[:,year].to_frame(),
                                                           util.remove_df_levels(self.potential.values.loc[:,year].to_frame(),[x for x in self.potential.values.index.names if x not in ['demand_sector',GeoMapper.supply_primary_geography,'resource_bin']])]),
                                                        supply_curve])
        cost = util.DfOper.mult([supply_curve,self.cost.values.loc[:,year].to_frame()])
        levels = ['demand_sector',GeoMapper.supply_primary_geography]
        cost = cost.groupby(level = [x for x in levels if x in cost.index.names]).sum()
        return  util.expand_multi(cost, levels_list = [GeoMapper.geography_to_gau[GeoMapper.supply_primary_geography], self.demand_sectors], levels_names=[GeoMapper.supply_primary_geography,'demand_sector']).replace([np.nan,np.inf],0)


    def calculate_marginal_costs(self,year):
        filter_geo_potential_normal = util.remove_df_elements(self.potential.active_supply_curve_normal, [x for x in GeoMapper.geography_to_gau_unfiltered[GeoMapper.supply_primary_geography] if x not in GeoMapper.supply_geographies],GeoMapper.supply_primary_geography)
        filter_geo_potential_normal = filter_geo_potential_normal.reset_index().set_index(filter_geo_potential_normal.index.names)
        supply_curve = filter_geo_potential_normal
        supply_curve = supply_curve[supply_curve.values>0]
        supply_curve = util.DfOper.mult([util.DfOper.divi([self.potential.values.loc[:,year].to_frame(),
                                                           util.remove_df_levels(self.potential.values.loc[:,year].to_frame(),[x for x in self.potential.values.index.names if x not in ['demand_sector',GeoMapper.supply_primary_geography,'resource_bin']])]),
                                                        supply_curve])
        supply_curve[supply_curve.values>0] = 1
        cost = util.DfOper.mult([supply_curve,self.cost.values.loc[:,year].to_frame()])
        levels = ['demand_sector',GeoMapper.supply_primary_geography]
        tradable_levels = ['demand_sector',self.tradable_geography]
        map_df = GeoMapper.get_instance().map_df(GeoMapper.supply_primary_geography,self.tradable_geography,normalize_as='total',eliminate_zeros=False,filter_geo=False)
        traded_cost = util.DfOper.mult([cost,map_df])
        traded_cost = traded_cost.groupby(level=[x for x in tradable_levels if x in traded_cost.index.names]).transform(lambda x: x.max())
        cost = traded_cost.groupby(level = [x for x in levels if x in cost.index.names]).max()
        return  util.expand_multi(cost, levels_list = [GeoMapper.geography_to_gau[GeoMapper.supply_primary_geography], self.demand_sectors], levels_names=[GeoMapper.supply_primary_geography,'demand_sector']).replace([np.nan,np.inf],0)


class ImportCost(schema.ImportCost):
    def __init__(self, name, scenario):
        super(ImportCost, self).__init__(name, scenario=scenario)
        self.init_from_db(name, scenario)
        self.input_type = 'intensity'
        self.scenario = scenario

    def calculate(self, years, demand_sectors, conversion=None, resource_unit=None):
        self.years = years
        self.demand_sectors = demand_sectors
        if self._has_data:
            self.remap(converted_geography=GeoMapper.supply_primary_geography)
            self.convert()

    def convert(self):
        """
        return cost values converted to model energy and currency unit

        """
        self.values = UnitConverter.currency_convert(self.values, self.currency, self.currency_year)
        self.values = UnitConverter.unit_convert(self.values, unit_from_den=self.denominator_unit,
                                        unit_to_den=cfg.calculation_energy_unit)
        self.values = self.values.unstack(level='year')
        self.values.columns = self.values.columns.droplevel()


class PrimaryNode(Node):
    def __init__(self, name, scenario):
        Node.__init__(self, name, scenario)
        self.potential = SupplyPotential(self.name, self.enforce_potential_constraint, self.scenario)
        self.cost = PrimaryCost(self.name, scenario)
        self.coefficients = SupplyCoefficients(self.name, self.scenario)

    def calculate(self):
        #all nodes can have potential conversions. Set to None if no data.
        self.conversion, self.resource_unit = self.add_conversion()
        if self.conversion is not None:
            self.conversion.calculate(self.resource_unit)
        self.potential.calculate(self.conversion, self.resource_unit)
        self.cost.calculate(self.years, self.demand_sectors,self.conversion, self.resource_unit)
        self.emissions.calculate(self.conversion, self.resource_unit)
        self.coefficients.calculate(self.years, self.demand_sectors)
        if self.coefficients._has_data is True:
            self.nodes = list(set(self.coefficients.values.index.get_level_values('supply_node')))
        self.set_adjustments()
        self.set_pass_through_df_dict()
        self.set_cost_dataframes()
        self.export.calculate(self.years, self.demand_sectors)

    def calculate_levelized_costs(self,year,loop):
        "calculates the embodied costs of nodes with emissions"
        if hasattr(self,'cost') and self.cost._has_data is True:
            if hasattr(self,'potential') and self.potential._has_data is True and self.cost.cost_method == 'average':
                self.active_embodied_cost = self.calculate_avg_costs(year)
            elif hasattr(self,'potential') and self.potential._has_data is True and self.cost.cost_method == 'marginal':
                self.active_embodied_cost = self.calculate_marginal_costs(year)
            else:
                allowed_indices = ['demand_sector', GeoMapper.supply_primary_geography]
                if set(self.cost.values.index.names).issubset(allowed_indices):
                    self.active_embodied_cost = self.cost.values.loc[:,year].to_frame()
                    self.active_embodied_cost = util.expand_multi(self.active_embodied_cost, levels_list = [GeoMapper.geography_to_gau[GeoMapper.supply_primary_geography], self.demand_sectors],levels_names=[GeoMapper.supply_primary_geography,'demand_sector'])
                else:
                    raise ValueError("too many indexes in cost inputs of node %s" %self.name)
            try:
                self.levelized_costs.loc[:,year] = DfOper.mult([self.active_embodied_cost,self.active_supply]).values
            except:
                pdb.set_trace()

    def calculate_annual_costs(self,year):
        if hasattr(self,'active_embodied_cost'):
            self.annual_costs.loc[:,year] = DfOper.mult([self.active_embodied_cost,self.active_supply]).values
        if year == cfg.getParamAsInt('end_year'):
            self.final_annual_costs = self.annual_costs


    def calculate_avg_costs(self,year):
        filter_geo_potential_normal = util.remove_df_elements(self.potential.active_supply_curve_normal, [x for x in GeoMapper.geography_to_gau_unfiltered[GeoMapper.supply_primary_geography] if x not in GeoMapper.supply_geographies],GeoMapper.supply_primary_geography)
        filter_geo_potential_normal = filter_geo_potential_normal.reset_index().set_index(filter_geo_potential_normal.index.names)
        supply_curve = filter_geo_potential_normal
        supply_curve = supply_curve[supply_curve.values>=0]
        supply_curve = util.DfOper.mult([util.DfOper.divi([self.potential.values.loc[:,year].to_frame(),
                                                           util.remove_df_levels(self.potential.values.loc[:,year].to_frame(),[x for x in self.potential.values.index.names if x not in ['demand_sector',GeoMapper.supply_primary_geography,'resource_bin']])]),
                                                        supply_curve])
        cost = util.DfOper.mult([supply_curve,self.cost.values.loc[:,year].to_frame()])
        levels = ['demand_sector',GeoMapper.supply_primary_geography]
        cost = cost.groupby(level = [x for x in levels if x in cost.index.names]).sum()
        cost = cost[cost.index.get_level_values(GeoMapper.supply_primary_geography).isin(GeoMapper.geography_to_gau[GeoMapper.supply_primary_geography])]
        return util.expand_multi(cost, levels_list = [GeoMapper.geography_to_gau[GeoMapper.supply_primary_geography], self.demand_sectors], levels_names=[GeoMapper.supply_primary_geography,'demand_sector']).replace([np.nan,np.inf],0)


    def calculate_marginal_costs(self,year):
        filter_geo_potential_normal = util.remove_df_elements(self.potential.active_supply_curve_normal, [x for x in GeoMapper.geography_to_gau_unfiltered[GeoMapper.supply_primary_geography] if x not in GeoMapper.supply_geographies],GeoMapper.supply_primary_geography)
        filter_geo_potential_normal = filter_geo_potential_normal.reset_index().set_index(filter_geo_potential_normal.index.names)
        supply_curve = filter_geo_potential_normal
        supply_curve = supply_curve[supply_curve.values>0]
        supply_curve = util.DfOper.mult([util.DfOper.divi([self.potential.values.loc[:,year].to_frame(),
                                                           util.remove_df_levels(self.potential.values.loc[:,year].to_frame(),[x for x in self.potential.values.index.names if x not in ['demand_sector',GeoMapper.supply_primary_geography,'resource_bin']])]),
                                                        supply_curve])
        supply_curve[supply_curve.values>0] = 1
        cost = util.DfOper.mult([supply_curve,self.cost.values.loc[:,year].to_frame()])
        levels = ['demand_sector',GeoMapper.supply_primary_geography]
        tradable_levels = ['demand_sector',self.tradable_geography]
        map_df = GeoMapper.get_instance().map_df(GeoMapper.supply_primary_geography,self.tradable_geography,normalize_as='total',eliminate_zeros=False,filter_geo=False)
        traded_cost = util.DfOper.mult([cost,map_df])
        traded_cost = traded_cost.groupby(level=[x for x in tradable_levels if x in traded_cost.index.names]).transform(lambda x: x.max())
        cost = traded_cost.groupby(level = [x for x in levels if x in cost.index.names]).max()
        cost = cost[cost.index.get_level_values(GeoMapper.supply_primary_geography).isin(
            GeoMapper.geography_to_gau[GeoMapper.supply_primary_geography])]
        return util.expand_multi(cost, levels_list = [GeoMapper.geography_to_gau[GeoMapper.supply_primary_geography], self.demand_sectors], levels_names=[GeoMapper.supply_primary_geography,'demand_sector']).replace([np.nan,np.inf],0)

class PrimaryCost(schema.PrimaryCost):
    def __init__(self, primary_node, scenario):
        super(PrimaryCost, self).__init__(primary_node=primary_node, scenario=scenario)
        self.init_from_db(primary_node, scenario)
        self.scenario = scenario
        self.input_type = 'intensity'

    def calculate(self, years, demand_sectors, conversion, resource_unit):
        if self._has_data:
            self.conversion = conversion
            self.resource_unit=resource_unit
            self.remap(converted_geography=GeoMapper.supply_primary_geography)
            self.convert()

    def convert(self):
        self.values = self.values.unstack(level='year')
        self.values.columns = self.values.columns.droplevel()
        if self.conversion is not None:
            self.energy = UnitConverter.is_energy_unit(self.denominator_unit)
            # checks if a conversion dataframe is available
            if self.energy:
                # if input values for cost are in energy terms, converts currency to model
                # currency and converts denominator_units into model energy units. Resource values are
                # (ex. $/ton of biomass) are a result of using conversion dataframe mutliplied by values
                self.values = UnitConverter.currency_convert(self.values, self.currency, self.currency_year)
                self.values = UnitConverter.unit_convert(self.values, unit_from_den=self.denominator_unit,
                                                unit_to_den=cfg.calculation_energy_unit)
#                self.resource_values = DfOper.mult([self.values, self.conversion.values])
            else:
                # if input values for costs are not in energy terms, cost values must be converted to model currency
                # and resource values are a result of unit conversion to the node resource unit.
                # ex. if costs for biomass were in $/kg and the node resource unit was tons, the costs would
                # need to be converted to $/ton. Then, these values can be converted to energy by dividing the
                #  values by the conversion dataframe.
                self.values = UnitConverter.currency_convert(self.values, self.currency, self.currency_year)
                self.values = UnitConverter.unit_convert(self.values, unit_from_den=self.denominator_unit,
                                                         unit_to_den=self.resource_unit)
                self.values = DfOper.divi([self.values, self.conversion.values])
        else:
            # if there is no conversion necessary, a simple conversion to model currency and
            # energy units is effected
            self.values = UnitConverter.currency_convert(self.values, self.currency, self.currency_year)
            self.values = UnitConverter.unit_convert(self.values, unit_from_den=self.denominator_unit,
                                            unit_to_den=cfg.calculation_energy_unit)


class SupplyEmissions(schema.SupplyEmissions):
    def __init__(self, name, scenario):
        super(SupplyEmissions, self).__init__(name, scenario=scenario)
        self.init_from_db(name, scenario)
        self.input_type = 'intensity'
        self.scenario = scenario


    def calculate(self, conversion, resource_unit):
        if self._has_data:
            self.conversion = conversion
            self.resource_unit=resource_unit
            self.remap(lower=None, converted_geography=GeoMapper.supply_primary_geography)
            self.convert()
            self.calculate_physical_and_accounting()

    def convert(self):
        self.values = self.values.unstack(level='year')
        self.values.columns = self.values.columns.droplevel()
        if self.conversion is not None:
            # checks whether a conversion dataframe has been created and the values can
            # be represented in energy and resource terms
            self.energy = UnitConverter.is_energy_unit(self.denominator_unit)
            if self.energy:
                # if the input values are in energy terms, the input mass unit and energy units are
                # converted to model mass units and energy units. These values are multiplied by the
                # conversion dataframe to produce resource values
                self.values = UnitConverter.unit_convert(self.values, unit_from_num=self.mass_unit,
                                                unit_from_den=self.denominator_unit,
                                                unit_to_num=cfg.getParam('mass_unit'),
                                                unit_to_den=cfg.calculation_energy_unit)
#                    self.resource_values = DfOper.mult([self.values, self.conversion.values])
            else:
                # if the input values are in resource terms, values are converted from input mass and resource units
                # to model units and node resource units. These resource values are divided by the conversion
                # dataframe to produce values.
                self.values = UnitConverter.unit_convert(self.values, unit_from_num=self.mass_unit,
                                                         unit_from_den=self.denominator_unit,
                                                         unit_to_num=cfg.getParam('mass_unit'),
                                                         unit_to_den=self.resource_unit)

                self.values = DfOper.divi([self.values, self.conversion.values])
        else:
            # if there is no conversion, then values are converted to model mass and energy units
            self.values = UnitConverter.unit_convert(self.values, unit_from_num=self.mass_unit,
                                            unit_from_den=self.denominator_unit,
                                            unit_to_num=cfg.getParam('mass_unit'),
                                            unit_to_den=cfg.calculation_energy_unit)
        self.ghgs = util.csv_read_table('GreenhouseGases', 'name', return_iterable=True)
        self.values = util.reindex_df_level_with_new_elements(self.values,'ghg',self.ghgs,fill_value=0.).sort_index()

    def calculate_physical_and_accounting(self):
          """converts emissions intensities for use in physical and accounting emissions calculations"""
          physical_emissions_indexer = util.level_specific_indexer(self.values, 'ghg_type', 'physical')
          self.values_physical =  self.values.loc[physical_emissions_indexer,:]
          accounting_emissions_indexer = util.level_specific_indexer(self.values, 'ghg_type', 'accounting')
          if 'accounting' in self.values.index.get_level_values('ghg_type'):
              self.values_accounting =  self.values.loc[accounting_emissions_indexer,:]
          else:
              self.values_accounting = self.values_physical * 0


class SupplyEnergyConversion(schema.SupplyPotentialConversion):
    def __init__(self, supply_node, scenario=None):
        """
        creates a dataframe of conversion values from energy (i.e. exajoule) to
        # resource terms (i.e. tons of biomass)
        """
        schema.SupplyPotentialConversion.__init__(self, supply_node, scenario=scenario)
        self.init_from_db(supply_node, scenario)
        self.input_type = 'intensity'

    def calculate(self, resource_unit):
        if self._has_data:
            self.resource_unit = resource_unit
            self.remap(converted_geography=GeoMapper.supply_primary_geography)
            self.values = UnitConverter.unit_convert(self.values, unit_from_num=self.energy_unit_numerator,
                                        unit_from_den=self.resource_unit_denominator,
                                        unit_to_num=cfg.calculation_energy_unit,
                                        unit_to_den=self.resource_unit)
            self.values = self.values.unstack(level='year')
            self.values.columns = self.values.columns.droplevel()

class RioInputs(DataObject):
    def __init__(self,scenario, supply):
        tech_list = util.csv_read_table('SupplyTechs','name',return_iterable=True)
        self.supply_technology_mapping = dict(zip([x.lower() for x in tech_list], tech_list))
        node_list = util.csv_read_table('SupplyNodes','name',return_iterable=True)
        self.supply_node_mapping = dict(zip([x.lower() for x in node_list], node_list))
        gau_list = util.csv_read_table('Geographies','gau',return_iterable=True)
        self.geography_mapping = dict(zip([x.lower() for x in gau_list], gau_list))
        self.scenario = scenario
        self.supply = supply
        self.rio_standard_unit_dict = self.create_rio_standard_unit_dict()
        fuel_energy= pd.read_csv(os.path.join(cfg.workingdir, 'rio_db_import\\annual_fuel_outputs.csv'),
                                  usecols=['unit','output','zone','year','blend','fuel','value','run name'],
                                 index_col=['unit','output','zone','year','blend','fuel','run name'])
        gen_energy = pd.read_csv(os.path.join(cfg.workingdir, 'rio_db_import\\annual_energy.csv'),
                                 usecols=['year','output', 'zone', 'feeder','resource', 'value','run name'],
                                 index_col=['year','output', 'zone', 'feeder','resource','run name'])
        capacity = pd.read_csv(os.path.join(cfg.workingdir, 'rio_db_import\\capacity.csv'), usecols=['output','unit','year','zone','feeder','resource','value','run name'],
                                         index_col=['output','unit','year','zone','feeder','resource','run name'])

        try:
            self.delivered_gen = pd.read_csv(os.path.join(cfg.workingdir, 'rio_db_import\\annual_deliverable_gen.csv'),
                                 usecols=['zone from','zone to', 'resource', 'resource_agg', 'year', 'value','run name'], index_col=['zone from','zone to', 'resource', 'resource_agg', 'year','run name'])
        except:
            logging.info("no annual_deliverable_gen csv found, returning None")
            self.delivered_gen = None
        self.cleaned_delivered_gen = self.clean_delivered_rio_gen()
        self.blend_levelized_costs = self.calc_blend_levelized_costs(self.scenario)
        self.dual_fuel_efficiency = self.calc_dual_fuel_efficiency(self.scenario)
        self.zonal_fuel_outputs = self.calc_fuel_share(scenario,fuel_energy,True)
        self.zonal_fuel_exports = self.calc_blend_exports(scenario, fuel_energy)
        self.product_exports = self.calc_product_exports(scenario, fuel_energy)
        self.fuel_outputs = self.calc_fuel_share(scenario,fuel_energy,False)
        self.stock = self.calc_stocks(scenario,capacity)
        self.duration = self.calc_duration(scenario, capacity,gen_energy)
        self.capacity_factor = self.calc_capacity_factors(scenario,gen_energy,fuel_energy)
        self.bulk_share = self.calc_bulk_share(scenario,gen_energy)
        self.thermal_share = self.calc_thermal_share(scenario,gen_energy)
        self.electricity_trades = self.calc_trades(scenario,gen_energy)
        self.bulk_thermal_share = self.calc_bulk_thermal_share(scenario,gen_energy)
        self.transmission_constraint = self.calc_transmission_constraint(scenario)
        self.adjust_bulk_shares_for_missing_techs()
        for attr in ['bulk_share','fuel_outputs','zonal_fuel_outputs','zonal_fuel_exports','product_exports','blend_levelized_costs']:
            self.clean_timeseries_and_fill_with_zeros(attr)

    def adjust_bulk_shares_for_missing_techs(self):
        multiplier = 1/util.DfOper.add([self.bulk_share.groupby(level=[cfg.rio_geography,'year']).sum(),self.bulk_thermal_share.groupby(level=[cfg.rio_geography,'year']).sum()])
        self.bulk_share = util.DfOper.mult([self.bulk_share,multiplier])
        self.bulk_thermal_share = util.DfOper.mult([self.bulk_thermal_share, multiplier])



    def clean_delivered_rio_gen(self):
        if self.delivered_gen is None:
            return None
        df = util.df_slice(self.delivered_gen,self.scenario, 'run name')
        df['technology'] = [self.supply_technology_mapping[x.split('||')[1]] if len(x.split('_')) > 3 else
                            self.supply_technology_mapping[x.split('||')[0]] for x in df.index.get_level_values('resource')]
        df = df.set_index(['technology'], append=True)
        df = df.groupby(level=['zone from', 'zone to',
                               'year', 'technology']).sum()
        df = df.reset_index('zone from')
        df[cfg.rio_geography+"_from"] = [self.geography_mapping[x] for x in df['zone from'].values]
        df.pop('zone from')
        df = df.reset_index('zone to')
        df[cfg.rio_geography + "_to"] = [self.geography_mapping[x] for x in df['zone to'].values]
        df.pop("zone to")
        df = df.set_index(cfg.rio_geography + "_from", append=True)
        df = df.set_index(cfg.rio_geography + "_to", append=True)
        df = df.unstack(cfg.rio_geography + "_to")
        return df

    def clean_name(self, x, gen_regions):
        x = x.split("||")
        x = [x for x in x if x not in gen_regions and x not in ['existing']]
        x = [x.replace("existing_", "") for x in x]
        x = [x.replace("li_ion", "li-ion") for x in x]
        x = [x.replace("oos_nm", "oos nm_1") for x in x]
        x = [x.replace("oos_wy", "oos wy_1") for x in x]
        x = [x.lower() for x in x]
        x = [x.strip('*') for x in x]
        x = '_'.join(x)
        return x

    def create_rio_standard_unit_dict(self):
        return dict(zip([cfg.rio_energy_unit, cfg.rio_mass_unit, cfg.rio_distance_unit, cfg.rio_volume_unit,
                         cfg.rio_energy_unit+ "/" + cfg.rio_time_unit, cfg.rio_mass_unit + "/" + cfg.rio_time_unit, cfg.rio_distance_unit+ "/" + cfg.rio_time_unit,cfg.rio_volume_unit + "/" + cfg.rio_time_unit],
                                     [cfg.rio_standard_energy_unit,cfg.rio_standard_mass_unit,cfg.rio_standard_distance_unit,cfg.rio_standard_volume_unit,
                                      cfg.rio_standard_energy_unit + "/" + cfg.rio_time_unit,
                                      cfg.rio_standard_mass_unit + "/" + cfg.rio_time_unit,
                                      cfg.rio_standard_distance_unit + "/" + cfg.rio_time_unit,
                                      cfg.rio_standard_volume_unit + "/" + cfg.rio_time_unit]
                                      ))




    def calc_blend_levelized_costs(self, scenario):
        levelized_cost = pd.read_csv(os.path.join(cfg.workingdir, 'rio_db_import\\levelized_cost.csv'),
                                 usecols=['vintage','zone', 'year', 'resource_agg', 'output', 'value','run name'], index_col=['vintage','zone', 'year', 'resource_agg', 'output','run name'])
        levelized_cost = util.df_slice(levelized_cost,scenario,'run name')
        df = util.remove_df_levels(levelized_cost[levelized_cost.index.get_level_values('output').isin(['blend energy storage'])],'vintage')
        df = util.remove_df_levels(df,'output')
        df = df.reset_index()
        df[cfg.rio_geography] = [self.geography_mapping[x] for x in df['zone'].values]
        df['supply_node'] = [self.supply_node_mapping[x] for x in df['resource_agg'].values]
        df = df[['supply_node',cfg.rio_geography,'year','value']]
        df = df.set_index([cfg.rio_geography,'year','supply_node'])
        return df.groupby(level='supply_node').filter(lambda x: x.sum()>0)

    def calc_dual_fuel_efficiency(self,scenario):
        try:
            dual_fuel_efficiency = pd.read_csv(os.path.join(cfg.workingdir, 'rio_db_import\\dual_fuel_efficiency.csv'), usecols=['year','blend', 'resource_agg', 'zone', 'value','run name'], index_col=['year','blend', 'resource_agg', 'zone','run name'])
        except:
            logging.info("no dual_fuel_efficiency csv found, returning None")
            return None
        if len(dual_fuel_efficiency) == 0:
            return None

        df = dual_fuel_efficiency.groupby(level=dual_fuel_efficiency.index.names).sum() # this is necessary to sum over new and existing
        annual_energy = pd.read_csv(os.path.join(cfg.workingdir, 'rio_db_import\\annual_energy.csv'),
                                 usecols=['year', 'output', 'zone', 'resource_agg', 'value', 'run name'],
                                 index_col=['year', 'output', 'zone', 'resource_agg', 'run name'])
        annual_energy = annual_energy.xs('thermal', level='output')
        resources = df.index.get_level_values('resource_agg').unique()
        annual_energy = util.df_slice(annual_energy, resources, 'resource_agg')
        annual_energy = annual_energy.groupby(level=annual_energy.index.names).sum() # this is necessary to sum over new and existing
        df = util.DfOper.divi([df,annual_energy],non_expandable_levels='resource_agg')*-1
        df = df[np.isfinite(df.values)]
        df = df.groupby(level=df.index.names).mean()
        df = util.df_slice(df, scenario, 'run name')
        df = df.reset_index()
        df[cfg.rio_geography] = [self.geography_mapping[x] for x in df['zone'].values]
        df['supply_node'] = [self.supply_node_mapping[x] for x in df['blend'].values]
        df['supply_technology'] = [self.supply_technology_mapping[x] for x in df['resource_agg'].values]
        df = df[['supply_technology',cfg.rio_geography,'supply_node', 'year','value']]
        return df.set_index(['supply_technology',cfg.rio_geography, 'supply_node','year'])


    def calc_capacity_factors(self,scenario,gen_energy,fuel_energy):
        gen_annual_energy = self.calc_gen_annual_energy(gen_energy,scenario)
        fuel_annual_energy = self.calc_fuel_annual_energy(fuel_energy,scenario)
        annual_energy = pd.concat([gen_annual_energy,fuel_annual_energy])
        capacity_factor = util.DfOper.divi([annual_energy,self.stock*8784])
        capacity_factor = capacity_factor.clip(.0001,1)
        capacity_factor = capacity_factor.fillna(0)
        return capacity_factor

    def calc_transmission_constraint(self,scenario):
        tx_capacity = pd.read_csv(os.path.join(cfg.workingdir, 'rio_db_import\\total_transmission_capacity.csv'),
                                 usecols=['zone from','zone to','year','value','run name'],
                                  index_col=['zone from','zone to','year','run name'])
        tx_capacity = util.df_slice(tx_capacity,scenario,'run name')
        tx_capacity.index.names = ['gau_from','gau_to','year']
        tx_capacity = tx_capacity.reset_index('gau_from')
        tx_capacity['gau_from'] = [self.geography_mapping[x] for x in tx_capacity['gau_from'].values]
        tx_capacity = tx_capacity.reset_index('gau_to')
        tx_capacity['gau_to'] = [self.geography_mapping[x] for x in tx_capacity['gau_to'].values]
        tx_capacity = tx_capacity.set_index(['gau_from','gau_to'], append=True)
        tx_capacity.index = tx_capacity.index.reorder_levels(['gau_from','gau_to','year'])
        tx_capacity = util.reindex_df_level_with_new_elements(tx_capacity, 'gau_from', GeoMapper.dispatch_geographies)
        tx_capacity = util.reindex_df_level_with_new_elements(tx_capacity, 'gau_to', GeoMapper.dispatch_geographies)
        tx_capacity = UnitConverter.unit_convert(tx_capacity,unit_from_num = cfg.rio_energy_unit,unit_to_num=cfg.calculation_energy_unit)
        tx_capacity = tx_capacity.fillna(0)
        return tx_capacity


    def calc_duration(self, scenario, capacity,gen_energy):
        df = util.df_slice(capacity, scenario, 'run name')
        df = df[df.index.get_level_values('output').isin(['storage', 'storage energy'])]
        df = df.groupby(level=['zone', 'year', 'resource','output']).sum()
        capacity_df = util.df_slice(df, 'storage', 'output')
        energy_df = util.df_slice(df, 'storage energy', 'output')
        df = util.DfOper.divi([energy_df,capacity_df])
        df = df.reset_index('resource')
        gen_regions = list(set(df.index.get_level_values('zone')))
        df['resource'] = df['resource'].apply(lambda x: self.clean_name(x, gen_regions))
        df['technology'] = [self.supply_technology_mapping[x.split('_')[1]] if len(x.split('_')) > 3 else
                            self.supply_technology_mapping[x.split('_')[0]] for x in df['resource'].values]
        df.pop('resource')
        df = df.set_index(['technology'], append=True)
        df = df.groupby(level=['zone', 'year', 'technology']).mean()
        df = df.reset_index('zone')
        df[cfg.rio_geography] = [self.geography_mapping[x] for x in df['zone'].values]
        df = df.set_index(cfg.rio_geography, append=True)
        df.pop('zone')
        df = df.fillna(0)
        return df

    def calc_gen_annual_energy(self,gen_energy, scenario):
        df = util.df_slice(gen_energy, scenario, 'run name')
        df = df[df.index.get_level_values('output').isin(['thermal', 'fixed', 'hydro'])]
        df = util.remove_df_levels(df,'output')
        df*=-1
        df = df.reset_index('resource')
        gen_regions = list(set(df.index.get_level_values('zone')))
        df['resource'] = df['resource'].apply(lambda x: self.clean_name(x,gen_regions))
        df['technology'] = [self.supply_technology_mapping[x.split('_')[1]] if len(x.split('_'))>3 else self.supply_technology_mapping[x.split('_')[0]]   for x in df['resource'].values]
        df['resource'] = [x.replace('all','1') for x in df['resource'].values]
        df['resource_bin'] = [int(x.split('_')[2]) if len(x.split('_')) == 5 else int(x.split('_')[1]) if len(x.split('_')) == 3 else 'n/a' for x in df['resource'].values]
        df.pop('resource')
        df = df.set_index(['technology','resource_bin'],append=True)
        df = df.groupby(level=['zone', 'year', 'technology','resource_bin']).sum()
        df = df.reset_index('zone')
        df[cfg.rio_geography] = [self.geography_mapping[x] for x in df['zone'].values]
        df = df.set_index(cfg.rio_geography,append=True)
        df.pop('zone')
        df = df.fillna(0)
        return df

    def calc_bulk_thermal_share(self,scenario,gen_energy):
        df = util.df_slice(gen_energy, scenario, 'run name')
        df_gen_all = df[df.index.get_level_values('output').isin(['hydro','fixed','thermal','storage discharge','storage reliability gen'])]*-1
        df_gen_thermal = util.remove_df_levels(df[df.index.get_level_values('output').isin(['thermal'])]*-1,'output')
        df = util.DfOper.divi([df_gen_thermal, df_gen_all.groupby(level=['year', 'zone']).sum()]).groupby(level=['year','zone']).sum()
        df = df.reset_index('zone')
        df[cfg.rio_geography] = [self.geography_mapping[x] for x in df['zone'].values]
        df = df.set_index(cfg.rio_geography,append=True)
        df.pop('zone')
        df = df.fillna(0)
        return df

    def calc_bulk_share(self,scenario,gen_energy):
        df = util.df_slice(gen_energy, scenario, 'run name')
        df_gen_all = df[df.index.get_level_values('output').isin(['hydro','fixed','thermal','storage discharge','storage reliability gen'])]*-1
        df_gen_bulk = util.remove_df_levels(df[df.index.get_level_values('output').isin(['hydro','fixed','curtailment','storage discharge','storage reliability gen'])]*-1,'output')


        if self.delivered_gen is not None:
            delivered_gen_reduction = util.df_slice(self.delivered_gen,scenario,'run name').groupby(level=['zone from','resource','resource_agg','year']).sum()
            util.replace_index_name(delivered_gen_reduction,'zone','zone from')
            delivered_gen_addition = util.df_slice(self.delivered_gen, scenario, 'run name').groupby(
                level=['zone to', 'resource', 'resource_agg', 'year']).sum()
            util.replace_index_name(delivered_gen_addition, 'zone', 'zone to')
            df_gen_bulk = util.remove_df_levels(util.df_list_concatenate([df_gen_bulk,delivered_gen_addition,-delivered_gen_reduction],new_names='output',keys=['a','b','c']),'output')
        df = util.DfOper.divi([df_gen_bulk,df_gen_all.groupby(level=['year','zone']).sum()])
        df = df.reset_index('resource')
        gen_regions = list(set(df.index.get_level_values('zone')))
        df['resource'] = df['resource'].apply(lambda x: self.clean_name(x,gen_regions))
        df['technology'] = [self.supply_technology_mapping[x.split('_')[1]] if len(x.split('_'))>3 else self.supply_technology_mapping[x.split('_')[0]]   for x in df['resource'].values]
        df['resource'] = [x.replace('all', '1') for x in df['resource'].values]
        df['resource_bin'] = [int(x.split('_')[2]) if len(x.split('_')) == 5 else int(x.split('_')[1]) if len(x.split('_')) == 3 else 'n/a' for x in df['resource'].values]
        df.pop('resource')
        df = df.set_index(['technology','resource_bin'],append=True)
        df = df.groupby(level=['zone', 'year', 'technology','resource_bin']).sum()
        df = df[~df.index.get_level_values('technology').isin(cfg.rio_excluded_technologies)]
        df = df.reset_index('zone')
        df[cfg.rio_geography] = [self.geography_mapping[x] for x in df['zone'].values]
        df = df.set_index(cfg.rio_geography,append=True)
        df.pop('zone')
        df = df.fillna(0)
        return df

    def clean_timeseries_and_fill_with_zeros(self,attr):
        if getattr(self,attr) is None or len(getattr(self,attr))==0:
            print attr
            return None
        self.clean_timeseries(attr, time_index_name = 'year',time_index = list(set(getattr(self,attr).index.get_level_values('year'))),extrapolation_method=None,interpolation_method='linear_interpolation')
        setattr(self, attr, getattr(self, attr).fillna(0))
        self.clean_timeseries(attr, extrapolation_method='linear_interpolation', interpolation_method='linear_interpolation')
        setattr(self,attr,getattr(self,attr).fillna(0))

    def calc_trades(self,scenario,gen_energy):
        df = util.df_slice(gen_energy, scenario, 'run name')
        df_load = df[~df.index.get_level_values('output').isin(['hydro','thermal','fixed'])]
        df_load = df_load.replace([np.inf,-np.inf],0)
        df_load = util.remove_df_levels(df_load,'feeder')
        df_load = util.remove_df_levels(df_load, ['output', 'resource'])
        df_load = df_load.reset_index('zone')
        df_load['zone'] = [self.geography_mapping[x] for x in df_load['zone'].values]
        df_load = df_load.set_index('zone',append=True)
        transmission_imports = pd.read_csv(os.path.join(cfg.workingdir, 'rio_db_import\\annual_transmission_flow.csv'),
                                 usecols=['zone from','zone to','year','value','run name'], index_col=['zone from','zone to','year','run name'])
        tx_flows =util.df_slice(transmission_imports, scenario, 'run name')
        if self.delivered_gen is not None:
            tx_flows = util.DfOper.mult([util.DfOper.divi([util.remove_df_levels(util.DfOper.subt([tx_flows, util.df_slice(self.delivered_gen,scenario,'run name').groupby(level=['zone from','zone to','year']).sum()]),'zone from'),util.remove_df_levels(tx_flows,'zone from')]),tx_flows])
        tx_losses = pd.read_csv(os.path.join(cfg.workingdir, 'rio_db_import\\TX_LOSSES.csv'),
                                 usecols=['name','from','to','year','value'], index_col=['name','from','to','year'])
        tx_losses = tx_losses.groupby(level=['from','to','year']).mean()
        tx_flows = tx_flows.reset_index("zone from")
        tx_flows = tx_flows.reset_index("zone to")
        tx_flows["zone from"] = [self.geography_mapping[x] for x in tx_flows['zone from'].values]
        tx_flows["zone to"] = [self.geography_mapping[x] for x in tx_flows['zone to'].values]
        tx_flows.set_index("zone from",append=True,inplace=True)
        tx_flows.set_index("zone to", append=True, inplace=True)
        tx_losses = tx_losses.reset_index("from")
        tx_losses = tx_losses.reset_index("to")
        tx_losses["from"] = [self.geography_mapping[x] for x in tx_losses['from'].values]
        tx_losses["to"] = [self.geography_mapping[x] for x in tx_losses['to'].values]
        tx_losses.set_index("from",append=True,inplace=True)
        tx_losses.set_index("to", append=True, inplace=True)
        rio_years = set(tx_flows.index.get_level_values('year'))
        row_index = pd.MultiIndex.from_product([GeoMapper.supply_geographies, rio_years],
                                               names=[cfg.rio_geography, 'year'])
        trade_df = pd.DataFrame(0,index=row_index,columns = GeoMapper.supply_geographies)
        active_rio_geographies = set(tx_flows.index.get_level_values('zone from'))
        for geography_from in GeoMapper.supply_geographies:
            for geography_to in GeoMapper.supply_geographies:
                if geography_from == geography_to or geography_from not in active_rio_geographies or geography_to not in active_rio_geographies:
                    continue
                for year in rio_years:
                    imports_df = util.df_slice(tx_flows,[geography_from,geography_to,year],['zone from','zone to','year'])
                    if not len(imports_df):
                        continue
                    load_df = util.df_slice(df_load,[geography_to,year],['zone','year'])
                    trade_share = imports_df.sum().sum()/load_df.sum().sum()
                    trade_df.loc[(geography_from,year),geography_to] = trade_share
        copied_trade_df = copy.deepcopy(trade_df)
        for geography_from in GeoMapper.supply_geographies:
            for geography_to in GeoMapper.supply_geographies:
                for year in rio_years:
                    if geography_from == geography_to:
                        trade_df.loc[(geography_from, year), geography_to] = 1-copied_trade_df.groupby(level='year').sum().loc[year,geography_to]
        for geography_from in GeoMapper.supply_geographies:
            for geography_to in GeoMapper.supply_geographies:
                if geography_from == geography_to or geography_from not in active_rio_geographies or geography_to not in active_rio_geographies:
                    continue
                for year in rio_years:
                    losses_df = util.df_slice(tx_losses,[geography_from,geography_to,year],['from','to','year'])
                    if not len(losses_df):
                        continue
                    trade_df.loc[(geography_from,year),geography_to] *= 1+losses_df.sum().sum()
        self.trade_df = trade_df
        self._cols = []
        self.remap('trade_df', 'trade_df', converted_geography=GeoMapper.supply_primary_geography,
                   current_geography=cfg.rio_geography, current_data_type='intensity',
                   interpolation_method='linear_interpolation', extrapolation_method='nearest')

        return self.trade_df






    def calc_thermal_share(self,scenario,gen_energy):
        df = util.df_slice(gen_energy, scenario, 'run name')
        df = df[df.index.get_level_values('output').isin(['thermal'])]
        df = df.groupby(level=df.index.names).sum()
        df = util.DfOper.divi([df,util.remove_df_levels(df,'resource')])
        df = df.reset_index('resource')
        gen_regions = list(set(df.index.get_level_values('zone')))
        df['resource'] = df['resource'].apply(lambda x: self.clean_name(x,gen_regions))
        df['technology'] = [self.supply_technology_mapping[x.split('_')[1]] if len(x.split('_'))>3 else self.supply_technology_mapping[x.split('_')[0]]   for x in df['resource'].values]
        df['resource'] = [x.replace('all', '1') for x in df['resource'].values]
        df['resource_bin'] = [int(x.split('_')[2]) if len(x.split('_')) == 5 else int(x.split('_')[1]) if len(x.split('_')) == 3 else 'n/a' for x in df['resource'].values]
        df.pop('resource')
        df = df.set_index(['technology','resource_bin'],append=True)
        df = df.groupby(level=['zone', 'year', 'technology','resource_bin']).sum()
        df = df.reset_index('zone')
        df[cfg.rio_geography] = [self.geography_mapping[x] for x in df['zone'].values]
        df = df.set_index(cfg.rio_geography,append=True)
        df.pop('zone')
        df = df.fillna(0)
        return df


    def calc_fuel_annual_energy(self,fuel_energy, scenario):
        df = util.df_slice(fuel_energy, scenario, 'run name')
        df = df[df.index.get_level_values('output').isin(['conversion inflow'])]
        df = util.remove_df_levels(df,'output')
        df = df.reset_index('fuel')
        gen_regions = list(set(df.index.get_level_values('zone')))
        df['fuel'] = df['fuel'].apply(lambda x: self.clean_name(x,gen_regions))
        df['technology'] = [self.supply_technology_mapping[x.split('_')[1]] if len(x.split('_'))>3 else self.supply_technology_mapping[x.split('_')[0]]   for x in df['fuel'].values]
        df['fuel'] = [x.replace('all', '1') for x in df['fuel'].values]
        df['resource_bin'] = [int(x.split('_')[2]) if len(x.split('_')) == 5 else int(x.split('_')[1]) if len(x.split('_')) == 3 else 'n/a' for x in df['fuel'].values]
        df.pop('fuel')
        df = df.set_index(['technology','resource_bin'],append=True)
        df = df.groupby(level=['zone', 'year', 'technology','resource_bin']).sum()
        df = df.reset_index('zone')
        df[cfg.rio_geography] = [self.geography_mapping[x] for x in df['zone'].values]
        df = df.set_index(cfg.rio_geography,append=True)
        df.pop('zone')
        df = df.fillna(0)
        return df

    def calc_stocks(self,scenario,capacity):
        df = util.df_slice(capacity, scenario, 'run name')
        df = df[~df.index.get_level_values('output').isin(['blend storage','storage energy','flexible load'])]
        df *= np.vstack(np.array([ UnitConverter.unit_convert(1,a,b) for a,b in zip(df.index.get_level_values('unit'),[self.rio_standard_unit_dict[x] for x in df.index.get_level_values('unit')])]))
        df *=  UnitConverter.unit_convert(1,cfg.rio_standard_energy_unit,cfg.rio_energy_unit)
        df = df.reset_index('resource')
        gen_regions = list(set(df.index.get_level_values('zone')))
        df['resource'] = df['resource'].apply(lambda x: self.clean_name(x,gen_regions))
        df['technology'] = [self.supply_technology_mapping[x.split('_')[1]] if len(x.split('_'))>3 else self.supply_technology_mapping[x.split('_')[0]]   for x in df['resource'].values]
        df['resource'] = [x.replace('all','1') for x in df['resource'].values]
        df['resource_bin'] = [int(x.split('_')[2]) if len(x.split('_')) == 5 else int(x.split('_')[1]) if len(x.split('_')) == 3 else 'n/a' for x in df['resource'].values]
        df.pop('resource')
        df = df.set_index(['technology','resource_bin'],append=True)
        df = df.groupby(level=['zone', 'year', 'technology','resource_bin']).sum()
        df = df.reset_index('zone')
        df[cfg.rio_geography] = [self.geography_mapping[x] for x in df['zone'].values]
        df = df.set_index(cfg.rio_geography,append=True)
        df.pop('zone')
        df = df.fillna(0)
        return df

    def calc_fuel_share(self,scenario,fuel_outputs,zonal):
        df = util.df_slice(fuel_outputs,scenario,'run name')
        df_supply = df[df.values >= 0]
        df_supply = df_supply[df_supply.index.get_level_values('output').isin(
            ['conversion inflow','product flow'])]
        df_supply['blend_new'] = [self.supply_node_mapping[x] for x in df_supply.index.get_level_values('blend')]
        df_supply = df_supply.reset_index('blend')
        df_supply['blend'] = df_supply['blend_new']
        df_supply.pop('blend_new')
        if zonal:
            df_supply = df_supply[df_supply['blend'].isin(cfg.rio_zonal_blend_nodes)]
        else:
            df_supply = df_supply[~df_supply['blend'].isin(cfg.rio_zonal_blend_nodes)]
        supply_node_names = [x.split('_')[-2] if len(x.split('_'))>1 else x for x in [x.split('||')[0] for x in df_supply.index.get_level_values('fuel')]]
        df_supply = df_supply.reset_index('fuel')
        df_supply['ep_fuel'] = supply_node_names
        df_supply.pop('fuel')
        df_supply[cfg.rio_geography] = [self.geography_mapping[x] for x in df_supply.index.get_level_values('zone')]
        df_supply = df_supply.reset_index('zone')
        df_supply.pop('zone')
        df_supply = df_supply.set_index(['blend','ep_fuel',cfg.rio_geography],append=True)
        df_supply[df_supply.values<0]=0
        df_supply = df_supply.fillna(0)
        df_supply = df_supply.groupby(level=['blend','ep_fuel',cfg.rio_geography,'year']).sum()
        if not zonal:
            df = util.remove_df_levels(df_supply, cfg.rio_geography).groupby(level=['blend','year']).transform(lambda x: x/x.sum())
            df = util.add_and_set_index(df, cfg.rio_geography, GeoMapper.geography_to_gau[cfg.rio_geography])
        else:
            df = df_supply.groupby(level=[cfg.rio_geography,'blend','year']).transform(lambda x: x / x.sum())
        df = df.replace([np.inf,np.nan],0,0)
        return df


    def calc_blend_exports(self,scenario,fuel_outputs):
        df = util.df_slice(fuel_outputs,scenario,'run name')
        df = df.groupby(level=['unit','blend','zone','year']).sum()
        df = df[df.values>0]
        df *= np.vstack(np.array([ UnitConverter.unit_convert(1,a,b) for a,b in zip(df.index.get_level_values('unit'),[self.rio_standard_unit_dict[x] for x in df.index.get_level_values('unit')])]))
        df *= UnitConverter.unit_convert(1,cfg.rio_standard_energy_unit,cfg.rio_energy_unit)
        df['blend_new'] = [self.supply_node_mapping[x] for x in df.index.get_level_values('blend')]
        df = df.reset_index('blend')
        df['blend'] = df['blend_new']
        df.pop('blend_new')
        df = df[df['blend'].isin(cfg.rio_export_blends)]
        df[cfg.rio_geography] = [self.geography_mapping[x] for x in df.index.get_level_values('zone')]
        df = df.reset_index('zone')
        df.pop('zone')
        df = df.set_index(['blend',cfg.rio_geography],append=True)
        return  df

    def calc_product_exports(self,scenario,fuel_outputs):
        df = util.df_slice(fuel_outputs,scenario,'run name')
        df = df[df.index.get_level_values('output').isin(
            ['product flow'])]
        df = df[df.values<0]*-1
        if len(df) == 0:
            return None
        df *= np.vstack(np.array([ UnitConverter.unit_convert(1,a,b) for a,b in zip(df.index.get_level_values('unit'),[self.rio_standard_unit_dict[x] for x in df.index.get_level_values('unit')])]))
        df *=  UnitConverter.unit_convert(1,cfg.rio_standard_energy_unit,cfg.rio_energy_unit)
        supply_node_names = [x.split('_')[0] for x in [x.split('||')[0] for x in df.index.get_level_values('fuel')]]
        df= df.reset_index()
        df['supply_node'] = [self.supply_node_mapping[x] for x in supply_node_names]
        df = df[df['supply_node'].isin(cfg.rio_outflow_products)]
        df[cfg.rio_geography] = [self.geography_mapping[x] for x in df['zone']]
        df = df[['supply_node',cfg.rio_geography,'year','value']]
        df = df.set_index(['supply_node',cfg.rio_geography,'year'])
        df = df.groupby(level=df.index.names).sum()
        return  df


