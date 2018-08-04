__author__ = 'Ben Haley & Ryan Jones'

import config as cfg
import util
import pandas as pd
import numpy as np
from datamapfunctions import DataMapFunctions, Abstract
import copy
import logging
import time
from util import DfOper
from collections import defaultdict
from supply_measures import BlendMeasure, ExportMeasure, StockMeasure, StockSalesMeasure, CO2PriceMeasure
from supply_technologies import SupplyTechnology, StorageTechnology
from supply_classes import SupplySpecifiedStock
from shared_classes import SalesShare, SpecifiedStock, Stock, StockItem
from rollover import Rollover
from solve_io import solve_IO
from dispatch_classes import Dispatch, DispatchFeederAllocation
import dispatch_classes
import inspect
import operator
import shape
from outputs import Output
from multiprocessing import Pool, cpu_count
import energyPATHWAYS.helper_multiprocess as helper_multiprocess
import pdb
import os
from datetime import datetime
import random
import dispatch_budget
import dispatch_generators

#def node_update_stock(node):
#    if hasattr(node, 'stock'):
#        node.update_stock(node.year,node.loop)
#    return node 
           
class Supply(object):

    """This module calculates all supply nodes in an IO loop to calculate energy, 
    emissions, and cost flows through the energy economy
    """    
    def __init__(self, scenario, demand_object=None, api_run=False):
        """Initializes supply instance"""
        self.all_nodes, self.blend_nodes, self.non_storage_nodes, self.storage_nodes = [], [], [], []
        self.nodes = {}
        self.demand_object = demand_object # used to retrieve results from demand-side
        self.scenario = scenario # used in writing dispatch outputs
        self.demand_sectors = util.sql_read_table('DemandSectors','id',return_iterable=True)
        self.demand_sectors.sort()
        self.thermal_dispatch_node_id = util.sql_read_table('DispatchConfig', 'thermal_dispatch_node_id')
        self.distribution_node_id = util.sql_read_table('DispatchConfig', 'distribution_node_id')
        self.distribution_grid_node_id = util.sql_read_table('DispatchConfig', 'distribution_grid_node_id')
        self.transmission_node_id = util.sql_read_table('DispatchConfig', 'transmission_node_id')
        self.dispatch_zones = [self.distribution_node_id, self.transmission_node_id]
        self.electricity_nodes = defaultdict(list)
        self.injection_nodes = defaultdict(list)
        self.ghgs = util.sql_read_table('GreenhouseGases','id', return_iterable=True)
        self.dispatch_feeder_allocation = DispatchFeederAllocation(id=1)
        self.dispatch_feeders = list(set(self.dispatch_feeder_allocation.values.index.get_level_values('dispatch_feeder')))
        self.dispatch = Dispatch(self.dispatch_feeders, cfg.dispatch_geography, cfg.dispatch_geographies, self.scenario)
        self.outputs = Output()
        self.outputs.hourly_dispatch_results = None
        self.outputs.hourly_marginal_cost = None
        self.outputs.hourly_production_cost = None
        self.active_thermal_dispatch_df_list = []
        self.map_dict = dict(util.sql_read_table('SupplyNodes', ['final_energy_link', 'id']))
        self.api_run = api_run
        if self.map_dict.has_key(None):
            del self.map_dict[None]
        self.CO2PriceMeasures = scenario.get_measures('CO2PriceMeasures', self.thermal_dispatch_node_id)
        self.add_co2_price_to_dispatch(self.CO2PriceMeasures)
    
    def add_co2_price_to_dispatch(self,CO2PriceMeasures):
        if len(self.CO2PriceMeasures)>1:
             raise ValueError('multiple CO2 price measures are active')
        elif len(self.CO2PriceMeasures) ==0:
            self.CO2PriceMeasure=None
        else:
            self.CO2PriceMeasure = CO2PriceMeasure(self.CO2PriceMeasures[0])
            self.CO2PriceMeasure.calculate()
        
     
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
        keys = [node.id for node in self.nodes.values()]
        dfs, keys = zip(*[(df, key) for df, key in zip(dfs, keys) if df is not None])
        new_names = 'supply_node'
        return util.df_list_concatenate(dfs, keys, new_names, levels_to_keep)

    def calculate_years(self):
        """
        Determines the period of stock rollover within a node based on the minimum year 
        of specified sales or stock. 
        """
        for node in self.nodes.values():
            node.min_year = int(cfg.cfgfile.get('case', 'current_year'))
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
            node.min_year = max(node.min_year, int(cfg.cfgfile.get('case','supply_start_year')))
            node.years = range(node.min_year, int(cfg.cfgfile.get('case', 'end_year')) +  int(cfg.cfgfile.get('case', 'year_step')), int(cfg.cfgfile.get('case', 'year_step')))
            node.vintages = copy.deepcopy(node.years)
        self.years = cfg.cfgfile.get('case','supply_years') 
            
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
        if cfg.cfgfile.get('case','parallel_process').lower() == 'true':
            nodes = helper_multiprocess.safe_pool(helper_multiprocess.node_calculate, self.nodes.values())
            self.nodes = dict(zip(self.nodes.keys(), nodes))
        else:
            for node in self.nodes.values():
                node.calculate()
        for node in self.nodes.values():
            if node.id in self.blend_nodes and node.id in cfg.evolved_blend_nodes and cfg.evolved_run=='true':
                node.values = node.values.groupby(level=[x for x in node.values.index.names if x !='supply_node']).transform(lambda x: 1/float(x.count()))
                for x in node.nodes:
                    if x in self.storage_nodes:
                        indexer = util.level_specific_indexer(node.values,'supply_node',x)
                        node.values.loc[indexer,:] = 1e-7 * 4
                node.values = node.values.groupby(level=[x for x in node.values.index.names if x !='supply_node']).transform(lambda x: x/x.sum())/4.0
            
    
    def create_IO(self):
        """Creates a dictionary with year and demand sector keys to store IO table structure"""
        self.io_dict = util.recursivedict()
        index =  pd.MultiIndex.from_product([cfg.geographies, self.all_nodes], names=[cfg.primary_geography,
                                                         'supply_node'])
        for year in self.years:
            for sector in util.ensure_iterable_and_not_string(self.demand_sectors):
                self.io_dict[year][sector] = util.empty_df(index = index, columns = index, fill_value=0.0)

        self.io_dict = util.freeze_recursivedict(self.io_dict)

    def add_nodes(self):
        """Adds node instances for all active supply nodes"""
        logging.info('Adding supply nodes')
        supply_type_dict = dict(util.sql_read_table('SupplyTypes', column_names=['id', 'name']))
        supply_nodes = util.sql_read_table('SupplyNodes', column_names=['id', 'name', 'supply_type_id', 'is_active'], return_iterable=True)
        supply_nodes.sort()
        for node_id, name, supply_type_id, is_active  in supply_nodes:
            if is_active:
                self.all_nodes.append(node_id)
                logging.info('    {} node {}'.format(supply_type_dict[supply_type_id], name))
                self.add_node(node_id, supply_type_dict[supply_type_id], self.scenario)
        
        # this ideally should be moved to the init statements for each of the nodes
        for node in self.nodes.values():
            node.demand_sectors = self.demand_sectors
            node.ghgs = self.ghgs
            node.distribution_grid_node_id = self.distribution_grid_node_id

            # for some reason, when this next part gets moved to the init for node, the DR node ends up having a tradeable geography of none
            if node.tradable_geography is None:
                node.enforce_tradable_geography = False
                node.tradable_geography = cfg.primary_geography
            else:
                node.enforce_tradable_geography = True

    def add_node(self, id, supply_type, scenario):
        """Add node to Supply instance
        Args: 
            id (int): supply node id 
            supply_type (str): supply type i.e. 'blend'
        """
        if supply_type == "Blend":
            self.nodes[id] = BlendNode(id, supply_type, scenario)
            self.blend_nodes.append(id)

        elif supply_type == "Storage":
            if len(util.sql_read_table('SupplyTechs', 'supply_node_id', supply_node_id=id, return_iterable=True)):          
                self.nodes[id] = StorageNode(id, supply_type, scenario)
            else:
                logging.debug(ValueError('insufficient data in storage node %s' %id))

        elif supply_type == "Import":
            self.nodes[id] = ImportNode(id, supply_type, scenario)

        elif supply_type == "Primary":
            self.nodes[id] = PrimaryNode(id, supply_type, scenario)

        else:
            if len(util.sql_read_table('SupplyEfficiency', 'id', id=id, return_iterable=True)):          
                self.nodes[id] = SupplyNode(id, supply_type, scenario)
            elif len(util.sql_read_table('SupplyTechs', 'supply_node_id', supply_node_id=id, return_iterable=True)):          
                self.nodes[id] = SupplyStockNode(id, supply_type, scenario)
            elif len(util.sql_read_table('SupplyStock', 'supply_node_id', supply_node_id=id, return_iterable=True)):          
                self.nodes[id] = SupplyNode(id, supply_type, scenario)
            else:
                logging.debug(ValueError('insufficient data in supply node %s' %id))

        if supply_type != "Storage":
            self.non_storage_nodes.append(id)
        else:
            self.storage_nodes.append(id)

    def add_measures(self):
        """ Adds measures to supply nodes based on scenario inputs"""
        logging.info('Adding supply measures')
        scenario = self.scenario
        for node in self.nodes.values():
            #all nodes have export measures
            node.add_export_measures(scenario)
            #once measures are loaded, export classes can be initiated
            node.add_exports()
            if node.supply_type == 'Blend':
                node.add_blend_measures(scenario)
            elif isinstance(node, SupplyStockNode) or isinstance(node, StorageNode): 
                node.add_total_stock_measures(scenario)
                for technology in node.technologies.values():                                                        
                    technology.add_sales_measures(scenario)
                    technology.add_sales_share_measures(scenario)
                    technology.add_specified_stock_measures(scenario)
            elif isinstance(node, SupplyNode):
                node.add_total_stock_measures(scenario)

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
        self.bulk_node_id = self.discover_bulk_id()
        self.discover_thermal_nodes()
        self.update_io_df(year, loop)
        self.calculate_io(year, loop)

    def _recalculate_stocks_and_io(self, year, loop):
        """ Basic calculation control for the IO
        """
        self.calculate_coefficients(year, loop)
        # we have just solved the dispatch, so coefficients need to be updated before updating the io
        if loop == 3 and year in self.dispatch_years:
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
        dispatch_year_step = int(cfg.cfgfile.get('case','dispatch_step'))
        dispatch_write_step = int(cfg.cfgfile.get('output_detail','dispatch_write_step'))
        logging.info("Dispatch year step = {}".format(dispatch_year_step))
        self.dispatch_years = sorted([min(self.years)] + range(max(self.years), min(self.years), -dispatch_year_step))
        if dispatch_year_step ==0:
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
                    for i in range(2):
                        self.reconcile_oversupply(year, loop)
                        self._recalculate_after_reconciliation(year, loop, update_demand=True)
                    self.reconcile_constraints(year,loop)
                    self._recalculate_after_reconciliation(year, loop, update_demand=True)
                    self.reconcile_oversupply(year, loop)
                    self._recalculate_after_reconciliation(year, loop, update_demand=True)
                # dispatch loop
                elif loop == 3 and year in self.dispatch_years:
                    logging.info("   loop {}: electricity dispatch".format(loop))
                    # loop - 1 is necessary so that it uses last year's throughput
                    self.calculate_embodied_costs(year, loop-1) # necessary here because of the dispatch
                    #necessary to calculate emissions to apply CO2 price in year 1 if applicable                    
#                    if year == min(self.years):
                    self.calculate_embodied_emissions(year)
                    self.prepare_dispatch_inputs(year, loop)
                    self.solve_electricity_dispatch(year)
                    self._recalculate_stocks_and_io(year, loop)
            self.calculate_embodied_costs(year, loop=3)
            self.calculate_embodied_emissions(year)
            self.calculate_annual_costs(year)
            self.calculated_years.append(year)

    def discover_bulk_id(self):
        for node in self.nodes.values():
            if hasattr(node, 'active_coefficients_total') and getattr(node, 'active_coefficients_total') is not None:
                if self.thermal_dispatch_node_id in node.active_coefficients_total.index.get_level_values('supply_node'):
                    self.bulk_id = node.id
                    
    def discover_thermal_nodes(self):
        self.thermal_nodes = []
        for node in self.nodes.values():
            if node.id in self.nodes[self.thermal_dispatch_node_id].values.index.get_level_values('supply_node'):
                self.thermal_nodes.append(node.id)
                node.thermal_dispatch_node = True
            else:
                node.thermal_dispatch_node = False
                            
    def calculate_supply_outputs(self):
        self.map_dict = dict(util.sql_read_table('SupplyNodes', ['final_energy_link', 'id']))
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
        supply_embodied_cost.columns = [cfg.cfgfile.get('case','currency_year_id') + " " + cfg.cfgfile.get('case','currency_name')]
        self.outputs.supply_embodied_cost = supply_embodied_cost
        supply_embodied_emissions = self.convert_io_matrix_dict_to_df(self.emissions_dict)
        supply_embodied_emissions.columns = [cfg.cfgfile.get('case', 'mass_unit')]
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
                df = util.df_slice(self.io_supply_df,node.id,'supply_node')
                node.calculate_capacity_utilization(df,self.years)
        
    def remove_blend_and_import(self):
        keep_list = [node.id for node in self.nodes.values() if node.supply_type != 'Blend' and node.supply_type != 'Import']
        indexer = util.level_specific_indexer(self.energy_demand_link,'supply_node',[keep_list])
        self.energy_demand_link = self.energy_demand_link.loc[indexer,:]       
        
    def calculate_demand_emissions_rates(self):
        map_dict = self.map_dict
        index = pd.MultiIndex.from_product([cfg.geographies, self.demand_sectors, map_dict.keys(),self.years, self.ghgs], names=[cfg.primary_geography, 'sector', 'final_energy','year','ghg'])
        self.demand_emissions_rates = util.empty_df(index, ['value'])

        for final_energy, node_id in map_dict.iteritems():
            node = self.nodes[node_id]
            for year in self.years:
                df = node.pass_through_df_dict[year].groupby(level='ghg').sum()
                df = df.stack(level=[cfg.primary_geography,'demand_sector']).to_frame()
                df = df.reorder_levels([cfg.primary_geography,'demand_sector','ghg'])
                df.sort(inplace=True)
                emissions_rate_indexer = util.level_specific_indexer(self.demand_emissions_rates, ['final_energy', 'year'], [final_energy, year])
                self.demand_emissions_rates.loc[emissions_rate_indexer,:] = df.values

        for final_energy, node_id in map_dict.iteritems():
            node = self.nodes[node_id] 
            if hasattr(node,'emissions') and hasattr(node.emissions, 'values_physical'):
                if 'demand_sector' not in node.emissions.values_physical.index.names:
                    keys = self.demand_sectors
                    name = ['demand_sector']
                    df = pd.concat([node.emissions.values_physical]*len(keys), keys=keys, names=name)
                df = df.stack('year').to_frame()
                df = df.groupby(level=[cfg.primary_geography, 'demand_sector', 'year', 'ghg']).sum()
                df = df.reorder_levels([cfg.primary_geography, 'demand_sector', 'year', 'ghg'])
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
            flow_nodes = list(set([x for x in util.df_slice(self.nodes[flow_node].active_coefficients_untraded,2,'efficiency_type').index.get_level_values('supply_node') if self.nodes[x].supply_type in ['Delivery','Blend'] and x not in self.dispatch_zones ]))
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
            for node_id in self.electricity_nodes[zone]:
                for load_node in self.nodes.values():
                    if hasattr(load_node,'active_coefficients_untraded')  and load_node.active_coefficients_untraded  is not None:
                        if node_id in load_node.active_coefficients_untraded.index.get_level_values('supply_node') and load_node not in self.electricity_nodes[zone] and load_node.supply_type != 'Storage':
                            if load_node.id not in util.flatten_list(self.electricity_nodes.values()):
                                self.all_electricity_load_nodes[zone].append(load_node.id)

    def append_heuristic_load_and_gen_to_dispatch_outputs(self, df, load_or_gen):
        if 0 in util.elements_in_index_level(df,'dispatch_feeder'):
            bulk_df = util.df_slice(df,0,'dispatch_feeder')
            if load_or_gen=='load':
                bulk_df = DfOper.mult([bulk_df, self.transmission_losses])
            bulk_df = self.outputs.clean_df(bulk_df)
            bulk_df.columns = [cfg.calculation_energy_unit.upper()]
            util.replace_index_name(bulk_df, 'DISPATCH_OUTPUT', 'SUPPLY_NODE')
            self.bulk_dispatch = pd.concat([self.bulk_dispatch, bulk_df.reorder_levels(self.bulk_dispatch.index.names)])
        if len([x for x in  util.elements_in_index_level(df,'dispatch_feeder') if x in self.dispatch_feeders]):
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
        for node_id in [x for x in self.dispatch.long_duration_dispatch_order if x in self.nodes.keys()]:
            node = self.nodes[node_id]
            full_energy_shape, p_min_shape, p_max_shape = node.aggregate_flexible_electricity_shapes(year, util.remove_df_levels(util.df_slice(self.dispatch_feeder_allocation.values,year,'year'),year))
            if node_id in self.flexible_gen.keys():
                lookup = self.flexible_gen
                load_or_gen = 'gen'
            elif node_id in self.flexible_load.keys():
                lookup = self.flexible_load
                load_or_gen = 'load'
            else:
                continue
            for geography in lookup[node_id].keys():
                for zone in lookup[node_id][geography].keys():
                    for feeder in lookup[node_id][geography][zone].keys():
                        capacity = util.remove_df_levels(lookup[node_id][geography][zone][feeder]['capacity'], 'resource_bin')
                        if capacity.sum().sum() == 0:
                            continue
                        annual_energy = lookup[node_id][geography][zone][feeder]['energy'].values.sum()
                        opt_periods = self.dispatch.period_repeated
                        dispatch_window = self.dispatch.dispatch_window_dict[self.dispatch.node_config_dict[node_id].dispatch_window_id]
                        dispatch_periods = getattr(shape.shapes.active_dates_index, dispatch_window)
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
                            hourly_p_min = util.remove_df_levels(util.DfOper.mult([capacity, p_min_shape]), cfg.primary_geography).values
                            p_min = np.array(split_and_apply(hourly_p_min, dispatch_periods, np.mean))
                            opt_p_min = np.array(split_and_apply(hourly_p_min, opt_periods, np.mean))
                            hourly_p_max = util.remove_df_levels(util.DfOper.mult([capacity, p_max_shape]),cfg.primary_geography).values
                            p_max = np.array(split_and_apply(hourly_p_max, dispatch_periods, np.mean))
                            opt_p_max = np.array(split_and_apply(hourly_p_max, opt_periods, np.mean))
                        tech_id = str(tuple([geography,node_id, feeder]))
                        self.dispatch.ld_technologies.append(tech_id)
                            #reversed sign for load so that pmin always represents greatest load or smallest generation
                        if zone == self.transmission_node_id:
                            if load_or_gen=='load':
                                p_min *= self.transmission_losses.loc[geography,:].values[0]
                                p_max *= self.transmission_losses.loc[geography,:].values[0]
                                opt_p_min *= self.transmission_losses.loc[geography,:].values[0]
                                opt_p_max *= self.transmission_losses.loc[geography,:].values[0]
                                hourly_p_min *=self.transmission_losses.loc[geography,:].values[0]
                                hourly_p_max *= self.transmission_losses.loc[geography,:].values[0]
                                annual_energy*=self.transmission_losses.loc[geography,:].values[0]              
                        else:
                                p_min *= self.transmission_losses.loc[geography,:].values[0] * util.df_slice(self.distribution_losses, [geography,feeder],[cfg.dispatch_geography, 'dispatch_feeder']).values[0][0]
                                p_max *= self.transmission_losses.loc[geography,:].values[0] * util.df_slice(self.distribution_losses, [geography,feeder],[cfg.dispatch_geography, 'dispatch_feeder']).values[0][0]
                                opt_p_min *= self.transmission_losses.loc[geography,:].values[0] * util.df_slice(self.distribution_losses, [geography,feeder],[cfg.dispatch_geography, 'dispatch_feeder']).values[0][0]
                                opt_p_max *= self.transmission_losses.loc[geography,:].values[0] * util.df_slice(self.distribution_losses, [geography,feeder],[cfg.dispatch_geography, 'dispatch_feeder']).values[0][0]
                                hourly_p_min *=self.transmission_losses.loc[geography,:].values[0] * util.df_slice(self.distribution_losses, [geography,feeder],[cfg.dispatch_geography, 'dispatch_feeder']).values[0][0]
                                hourly_p_max *= self.transmission_losses.loc[geography,:].values[0] * util.df_slice(self.distribution_losses, [geography,feeder],[cfg.dispatch_geography, 'dispatch_feeder']).values[0][0]
                                annual_energy *= self.transmission_losses.loc[geography,:].values[0] * util.df_slice(self.distribution_losses, [geography,feeder],[cfg.dispatch_geography, 'dispatch_feeder']).values[0][0]        
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
                        self.dispatch.annual_ld_energy[tech_id] = annual_energy
                        self.dispatch.ld_geography[tech_id] = geography
                        self.dispatch.ld_capacity.update(dict([((tech_id, h), value) for h, value in enumerate(max_hourly_capacity)]))
                        self.dispatch.ld_min_capacity.update(dict([((tech_id, h), value) for h, value in enumerate(min_hourly_capacity)]))
                        for period in self.dispatch.periods:
                            self.dispatch.capacity[period][tech_id] = max_capacity[period]
                            self.dispatch.min_capacity[period][tech_id] = min_capacity[period]
                            self.dispatch.geography[period][tech_id] = geography
                            self.dispatch.feeder[period][tech_id] = feeder
                            
                            

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
        for node_id in [x for x in self.dispatch.heuristic_dispatch_order if x in self.nodes.keys() ]:
            node = self.nodes[node_id]
            full_energy_shape, p_min_shape, p_max_shape = node.aggregate_flexible_electricity_shapes(year, util.remove_df_levels(util.df_slice(self.dispatch_feeder_allocation.values,year,'year'),year))
            if node_id in self.flexible_gen.keys():
                lookup = self.flexible_gen
                load_or_gen = 'gen'
            elif node_id in self.flexible_load.keys():
                lookup = self.flexible_load
                load_or_gen = 'load'
            else:
                continue        
            logging.info("      solving dispatch for %s" %node.name)
            geography_list = []
            for geography in lookup[node_id].keys():
                for zone in lookup[node_id][geography].keys():
                    feeder_list = []
                    for feeder in lookup[node_id][geography][zone].keys():
                        capacity = lookup[node_id][geography][zone][feeder]['capacity']
                        energy = lookup[node_id][geography][zone][feeder]['energy']
                        dispatch_window = self.dispatch.dispatch_window_dict[self.dispatch.node_config_dict[node_id].dispatch_window_id]
                        dispatch_periods = getattr(shape.shapes.active_dates_index, dispatch_window)
                        num_years = len(dispatch_periods)/8766.
                        if load_or_gen=='load':
                            energy = copy.deepcopy(energy) *-1
                        if full_energy_shape is not None and 'dispatch_feeder' in full_energy_shape.index.names:
                            energy_shape = util.df_slice(full_energy_shape, feeder, 'dispatch_feeder')     
                        else:
                            energy_shape = full_energy_shape
                        if energy_shape is None:                            
                            energy_budgets = util.remove_df_levels(energy,[cfg.primary_geography,'resource_bin']).values * np.diff([0]+list(np.where(np.diff(dispatch_periods)!=0)[0]+1)+[len(dispatch_periods)-1])/8766.*num_years
                            energy_budgets = energy_budgets[0]
                        else:
                            hourly_energy = util.remove_df_levels(util.DfOper.mult([energy,energy_shape]), cfg.primary_geography).values
                            energy_budgets = split_and_apply(hourly_energy, dispatch_periods, sum)
                        if p_min_shape is None:   
                            p_min = 0.0
                            p_max = capacity.sum().values[0]
                        else:
                            hourly_p_min = util.remove_df_levels(util.DfOper.mult([capacity,p_min_shape]),cfg.primary_geography).values
                            p_min = split_and_apply(hourly_p_min, dispatch_periods, np.mean)
                            hourly_p_max = util.remove_df_levels(util.DfOper.mult([capacity,p_max_shape]),cfg.primary_geography).values
                            p_max = split_and_apply(hourly_p_max, dispatch_periods, np.mean)                        
                        if zone == self.transmission_node_id:                    
                            net_indexer = util.level_specific_indexer(self.bulk_net_load,[cfg.dispatch_geography,'timeshift_type'], [geography,2])
                            if load_or_gen=='load':
                                self.energy_budgets = energy_budgets
                                self.p_min = p_min
                                self.p_max = p_max
                                dispatch = np.transpose([dispatch_budget.dispatch_to_energy_budget(self.bulk_net_load.loc[net_indexer,:].values.flatten(),energy_budgets, dispatch_periods, p_min, p_max)])
                                self.dispatch_result = dispatch            
                                indexer = util.level_specific_indexer(self.bulk_load,[cfg.dispatch_geography], [geography])
                                self.bulk_load.loc[indexer,:] += dispatch
                                indexer = util.level_specific_indexer(self.bulk_load,cfg.dispatch_geography, geography)
                                self.dispatched_bulk_load.loc[indexer,:] += dispatch
                            else:
                                indexer = util.level_specific_indexer(self.bulk_gen,cfg.dispatch_geography, geography)
                                dispatch = np.transpose([dispatch_budget.dispatch_to_energy_budget(self.bulk_net_load.loc[net_indexer,:].values.flatten(),np.array(energy_budgets).flatten(), dispatch_periods, p_min, p_max)])
                                self.bulk_gen.loc[indexer,:] += dispatch
                                self.dispatched_bulk_gen.loc[indexer,:] += dispatch
                        else:
                            if load_or_gen=='load':
                                indexer = util.level_specific_indexer(self.dist_load,[cfg.dispatch_geography,'dispatch_feeder'], [geography,feeder])
                                dispatch =  np.transpose([dispatch_budget.dispatch_to_energy_budget(self.dist_net_load_no_feeders.loc[net_indexer,:].values.flatten(),energy_budgets, dispatch_periods, p_min, p_max)])
                                for timeshift_type in list(set(self.distribution_load.index.get_level_values('timeshift_type'))):
                                    indexer = util.level_specific_indexer(self.distribution_load,[cfg.dispatch_geography,'timeshift_type'], [geography,timeshift_type])
                                    self.distribution_load.loc[indexer,:] += dispatch
                                indexer = util.level_specific_indexer(self.distribution_load,cfg.dispatch_geography, geography)
                                self.dispatched_dist_load.loc[indexer,:] += dispatch

                            else:
                                indexer = util.level_specific_indexer(self.dist_gen,[cfg.dispatch_geography,'dispatch_feeder'], [geography,feeder])
                                dispatch =  np.transpose([dispatch_budget.dispatch_to_energy_budget(self.dist_net_load_no_feeders.loc[net_indexer,:].values.flatten(),energy_budgets, dispatch_periods, p_min, p_max)])
                                self.distribution_gen.loc[indexer,:] += dispatch
                                self.dispatched_dist_gen.loc[indexer,:] += dispatch
                        index = pd.MultiIndex.from_product([shape.shapes.active_dates_index,[feeder]],names=['weather_datetime','dispatch_feeder'])
                        dispatch=pd.DataFrame(dispatch,index=index,columns=['value'])
                        if load_or_gen=='gen':
                            dispatch *=-1
                        feeder_list.append(dispatch)
                    geography_list.append(pd.concat(feeder_list))
            self.update_net_load_signal()
            df = pd.concat(geography_list, keys=lookup[node_id].keys(), names=[cfg.dispatch_geography])
            df = pd.concat([df], keys=[node_id], names=['supply_node'])
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
        self.dispatch.set_opt_loads(self.distribution_load,self.distribution_gen,self.bulk_load,self.bulk_gen,self.dispatched_bulk_load, self.bulk_net_load, self.active_thermal_dispatch_df)
        self.dispatch.set_technologies(self.storage_capacity_dict, self.storage_efficiency_dict, self.active_thermal_dispatch_df)
        self.set_long_duration_opt(year)

    def set_grid_capacity_factors(self, year):
        max_year = max(self.years)
        distribution_grid_node = self.nodes[self.distribution_grid_node_id]        
        dist_cap_factor = util.DfOper.divi([util.df_slice(self.dist_only_net_load,2,'timeshift_type').groupby(level=[cfg.dispatch_geography,'dispatch_feeder']).mean(),util.df_slice(self.dist_only_net_load,2,'timeshift_type').groupby(level=[cfg.dispatch_geography,'dispatch_feeder']).max()])
        geography_map_key = distribution_grid_node.geography_map_key if hasattr(distribution_grid_node, 'geography_map_key') and distribution_grid_node.geography_map_key is not None else cfg.cfgfile.get('case','default_geography_map_key')       
        if cfg.dispatch_geography != cfg.primary_geography:
            map_df = cfg.geo.map_df(cfg.dispatch_geography,cfg.primary_geography, normalize_as='intensity', map_key=geography_map_key, eliminate_zeros=False)
            dist_cap_factor = util.remove_df_levels(util.DfOper.mult([dist_cap_factor,map_df]),cfg.dispatch_geography)
        dist_cap_factor = util.remove_df_levels(util.DfOper.mult([dist_cap_factor, util.df_slice(self.dispatch_feeder_allocation.values,year, 'year')]),'dispatch_feeder')
        dist_cap_factor = dist_cap_factor.reorder_levels([cfg.primary_geography,'demand_sector']).sort()
        distribution_grid_node.capacity_factor.values.loc[:,year] = dist_cap_factor.values
        for i in range(0,int(cfg.cfgfile.get('case','dispatch_step'))+1):
            distribution_grid_node.capacity_factor.values.loc[:,min(year+i,max_year)] = dist_cap_factor.values
        if hasattr(distribution_grid_node, 'stock'):
                distribution_grid_node.update_stock(year,3)
        #hardcoded 50% assumption of colocated energy for dispatched flexible gen. I.e. wind and solar. Means that transmission capacity isn't needed to support energy demands. 
        #TODO change to config parameter
        bulk_flow = util.df_slice(util.DfOper.subt([util.DfOper.add([self.bulk_load,util.remove_df_levels(self.dist_only_net_load,'dispatch_feeder')]),self.dispatched_bulk_load * .5]),2,'timeshift_type')
        bulk_cap_factor = util.DfOper.divi([bulk_flow.groupby(level=cfg.dispatch_geography).mean(),bulk_flow.groupby(level=cfg.dispatch_geography).max()])
        transmission_grid_node = self.nodes[self.transmission_node_id]              
        geography_map_key = transmission_grid_node.geography_map_key if hasattr(transmission_grid_node, 'geography_map_key') and transmission_grid_node.geography_map_key is not None else cfg.cfgfile.get('case','default_geography_map_key')       
        if cfg.dispatch_geography != cfg.primary_geography:
            map_df = cfg.geo.map_df(cfg.dispatch_geography,cfg.primary_geography, normalize_as='intensity', map_key=geography_map_key, eliminate_zeros=False)
            bulk_cap_factor = util.remove_df_levels(util.DfOper.mult([bulk_cap_factor,map_df]),cfg.dispatch_geography)
        transmission_grid_node.capacity_factor.values.loc[:,year] = bulk_cap_factor.values
        for i in range(0,int(cfg.cfgfile.get('case','dispatch_step'))+1):
            transmission_grid_node.capacity_factor.values.loc[:,min(year+i,max_year)] = bulk_cap_factor.values
        if hasattr(transmission_grid_node, 'stock'):
            transmission_grid_node.update_stock(year,3)

    def solve_storage_and_flex_load_optimization(self,year):
        # MOVE
        """prepares, solves, and updates the net load with results from the storage and flexible load optimization""" 
        self.dispatch.set_year(year)
        self.prepare_optimization_inputs(year)
        logging.info("      solving dispatch for storage and dispatchable load")
        self.dispatch.solve_optimization()
        storage_charge = self.dispatch.storage_df.xs('charge', level='charge_discharge')
        storage_discharge = self.dispatch.storage_df.xs('discharge', level='charge_discharge')
        #load and gen are the same in the ld_df, just with different signs. We want to separate and use absolute values (i.e. *- when it is load)
        timeshift_types = list(set(self.distribution_load.index.get_level_values('timeshift_type')))
        if len(self.dispatch.ld_technologies):
            ld_load = util.remove_df_levels(-self.dispatch.ld_df[self.dispatch.ld_df.values<0],'supply_node')
            ld_gen = util.remove_df_levels(self.dispatch.ld_df[self.dispatch.ld_df.values>0], 'supply_node')

            dist_ld_load = util.add_and_set_index(util.df_slice(ld_load, self.dispatch_feeders, 'dispatch_feeder'), 'timeshift_type', timeshift_types)
            if not len(dist_ld_load):
                dist_ld_load = None
            if not len(ld_load):
                ld_load = None
            if not len(ld_gen):
                ld_gen = None
        else:
            ld_load = None
            ld_gen = None
            dist_ld_load = None
        if len(set(storage_charge.index.get_level_values('dispatch_feeder')))>1:            
            dist_storage_charge = util.add_and_set_index(util.df_slice(storage_charge, self.dispatch_feeders, 'dispatch_feeder'), 'timeshift_type', timeshift_types)
            dist_storage_discharge = util.df_slice(storage_discharge, self.dispatch_feeders, 'dispatch_feeder')
        else:
            dist_storage_charge = None
            dist_storage_discharge = None
        dist_flex_load = util.add_and_set_index(util.df_slice(self.dispatch.flex_load_df, self.dispatch_feeders, 'dispatch_feeder'), 'timeshift_type', timeshift_types)
        self.distribution_load = util.DfOper.add((self.distribution_load, dist_storage_charge, dist_flex_load, dist_ld_load))
        self.distribution_gen = util.DfOper.add((self.distribution_gen, dist_storage_discharge,util.df_slice(ld_gen, self.dispatch_feeders, 'dispatch_feeder',return_none=True) ))
        
        if self.dispatch.transmission_flow_df is not None:
            flow_with_losses = util.DfOper.divi((self.dispatch.transmission_flow_df, 1 - self.dispatch.transmission.losses.get_values(year)))
            imports = self.dispatch.transmission_flow_df.groupby(level=['geography_to', 'weather_datetime']).sum()
            exports = flow_with_losses.groupby(level=['geography_from', 'weather_datetime']).sum()
            imports.index.names = [cfg.dispatch_geography, 'weather_datetime']
            exports.index.names = [cfg.dispatch_geography, 'weather_datetime']
        else:
            imports = None
            exports = None
        self.bulk_load = util.DfOper.add((self.bulk_load, storage_charge.xs(0, level='dispatch_feeder'), util.DfOper.divi([util.df_slice(ld_load, 0, 'dispatch_feeder',return_none=True),self.transmission_losses]),util.DfOper.divi([exports,self.transmission_losses])))
        self.bulk_gen = util.DfOper.add((self.bulk_gen, storage_discharge.xs(0, level='dispatch_feeder'),util.df_slice(ld_gen, 0, 'dispatch_feeder',return_none=True),imports))
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
            df_index_reset['geography_from'] = map(cfg.outputs_id_map[cfg.dispatch_geography].get, df_index_reset['geography_from'].values)
            df_index_reset['geography_to'] = map(cfg.outputs_id_map[cfg.dispatch_geography].get, df_index_reset['geography_to'].values)

            df_index_reset_with_losses = DfOper.divi((self.dispatch.transmission_flow_df, 1 - self.dispatch.transmission.losses.get_values(year))).reset_index()
            df_index_reset_with_losses['geography_from'] = map(cfg.outputs_id_map[cfg.dispatch_geography].get, df_index_reset_with_losses['geography_from'].values)
            df_index_reset_with_losses['geography_to'] = map(cfg.outputs_id_map[cfg.dispatch_geography].get, df_index_reset_with_losses['geography_to'].values)

            imports = df_index_reset.rename(columns={'geography_to':cfg.dispatch_geography})
            exports = df_index_reset_with_losses.rename(columns={'geography_from':cfg.dispatch_geography})
            exports['geography_to'] = 'TRANSMISSION EXPORT TO ' + exports['geography_to']
            imports['geography_from'] = 'TRANSMISSION IMPORT FROM ' + imports['geography_from']
            imports = imports.rename(columns={'geography_from':'DISPATCH_OUTPUT'})
            exports = exports.rename(columns={'geography_to':'DISPATCH_OUTPUT'})
            imports = imports.set_index([cfg.dispatch_geography, 'DISPATCH_OUTPUT', 'weather_datetime'])
            exports = exports.set_index([cfg.dispatch_geography, 'DISPATCH_OUTPUT', 'weather_datetime'])
            # drop any lines that don't have flows this is done to reduce the size of outputs
            imports = imports.groupby(level=[cfg.dispatch_geography, 'DISPATCH_OUTPUT']).filter(lambda x: x.sum() > 0)
            exports = exports.groupby(level=[cfg.dispatch_geography, 'DISPATCH_OUTPUT']).filter(lambda x: x.sum() > 0)
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
            ld_df = -util.df_slice(self.dispatch.ld_df, 0, 'dispatch_feeder')
            if len(ld_df):
                ld_df = util.add_and_set_index(ld_df, 'year', year)
                ld_df.columns = [cfg.calculation_energy_unit.upper()]
                ld_df= self.outputs.clean_df(ld_df)
                util.replace_index_name(ld_df,'DISPATCH_OUTPUT', 'SUPPLY_NODE')
                self.bulk_dispatch = pd.concat([self.bulk_dispatch, ld_df.reorder_levels(self.bulk_dispatch.index.names)])

    def produce_bulk_storage_outputs(self, year):
        # MOVE
        if year in self.dispatch_write_years:
            bulk_df = self.dispatch.storage_df.xs(0, level='dispatch_feeder')
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
        distribution_grid_node =self.nodes[self.distribution_grid_node_id] 
        coefficients = distribution_grid_node.active_coefficients_total.sum().to_frame()
        indexer = util.level_specific_indexer(self.dispatch_feeder_allocation.values, 'year', year)
        a = util.DfOper.mult([coefficients, self.dispatch_feeder_allocation.values.loc[indexer,:], distribution_grid_node.active_supply])     
        b = util.DfOper.mult([self.dispatch_feeder_allocation.values.loc[indexer,:], distribution_grid_node.active_supply])
        self.distribution_losses = util.DfOper.divi([util.remove_df_levels(a,'demand_sector'),util.remove_df_levels(b,'demand_sector')]).fillna(1)
        geography_map_key = distribution_grid_node.geography_map_key if hasattr(distribution_grid_node, 'geography_map_key') and distribution_grid_node.geography_map_key is not None else cfg.cfgfile.get('case','default_geography_map_key')       
        if cfg.dispatch_geography != cfg.primary_geography:
            map_df = cfg.geo.map_df(cfg.primary_geography,cfg.dispatch_geography,normalize_as='intensity',map_key=geography_map_key,eliminate_zeros=False)
            self.distribution_losses =  util.remove_df_levels(DfOper.mult([self.distribution_losses,map_df]),cfg.primary_geography)
    
    def set_transmission_losses(self,year):
        transmission_grid_node =self.nodes[self.transmission_node_id]
        coefficients = transmission_grid_node.active_coefficients_total.sum().to_frame()
        coefficients.columns = [year]
        geography_map_key = transmission_grid_node.geography_map_key if hasattr(transmission_grid_node, 'geography_map_key') and transmission_grid_node.geography_map_key is not None else cfg.cfgfile.get('case','default_geography_map_key')
        if cfg.dispatch_geography != cfg.primary_geography:
            map_df = cfg.geo.map_df(cfg.primary_geography,cfg.dispatch_geography,normalize_as='intensity',map_key=geography_map_key,eliminate_zeros=False)
            self.transmission_losses =  util.remove_df_levels(DfOper.mult([coefficients,map_df]),cfg.primary_geography)
        else:
            self.transmission_losses = coefficients
        self.transmission_losses = util.remove_df_levels(self.transmission_losses,'demand_sector',agg_function='mean')

    def set_net_load_thresholds(self, year):
        # MOVE?
        distribution_grid_node = self.nodes[self.distribution_grid_node_id]
        dist_stock = distribution_grid_node.stock.values.groupby(level=[cfg.primary_geography,'demand_sector']).sum().loc[:,year].to_frame()
        dist_stock = util.remove_df_levels(DfOper.mult([dist_stock, util.df_slice(self.dispatch_feeder_allocation.values,year,'year')]),'demand_sector')
        geography_map_key = distribution_grid_node.geography_map_key if hasattr(distribution_grid_node, 'geography_map_key') and distribution_grid_node.geography_map_key is not None else cfg.cfgfile.get('case','default_geography_map_key')       
        if cfg.dispatch_geography != cfg.primary_geography:
            map_df = cfg.geo.map_df(cfg.primary_geography,cfg.dispatch_geography, normalize_as='total',map_key=geography_map_key,eliminate_zeros=False)
            dist_stock =  util.remove_df_levels(DfOper.mult([dist_stock,map_df]),cfg.primary_geography)
        transmission_grid_node = self.nodes[self.transmission_node_id]
        transmission_stock = transmission_grid_node.stock.values.groupby(level=[cfg.primary_geography]).sum().loc[:,year].to_frame()
        geography_map_key = transmission_grid_node.geography_map_key if hasattr(distribution_grid_node, 'geography_map_key') and transmission_grid_node.geography_map_key is not None else cfg.cfgfile.get('case','default_geography_map_key')       
        if cfg.dispatch_geography != cfg.primary_geography:
            map_df = cfg.geo.map_df(cfg.primary_geography,cfg.dispatch_geography, normalize_as='total', map_key=geography_map_key,eliminate_zeros=False)
            transmission_stock =  util.remove_df_levels(DfOper.mult([transmission_stock,map_df]),cfg.primary_geography)
        self.dispatch.set_thresholds(dist_stock,transmission_stock)
   
   
    def prepare_flexible_load(self,year):
        """Calculates the availability of flexible load for the hourly dispatch. Used for nodes like hydrogen and P2G.
        Args:
            year (int) = year of analysis 
            loop (int or str) = loop identifier
        Sets:
            flexible_load (dict) = dictionary with keys of  supply_node_id, 'energy' or 'capacity', 'geography', zone (i.e. transmission grid
            or distribution grid), and dispatch_feeder and values of a np.array()
        """
        self.flexible_load= util.recursivedict()
        for zone in self.dispatch_zones:
            for node_id in self.electricity_load_nodes[zone]['flexible']:
                node = self.nodes[node_id]
                if hasattr(node.stock, 'coefficients'):
                    indexer =  util.level_specific_indexer(node.stock.coefficients.loc[:,year],'supply_node',[self.electricity_nodes[zone]+[zone]])
                    energy_demand = util.DfOper.mult([util.remove_df_levels(node.stock.values_energy.loc[:,year].to_frame(),['vintage','supply_technology']), util.remove_df_levels(node.stock.coefficients.loc[indexer,year].to_frame(),['vintage','supply_technology','resource_bin'])])
                    capacity = util.DfOper.mult([util.remove_df_levels(node.stock.values.loc[:,year].to_frame(),['vintage','supply_technology']), util.remove_df_levels(node.stock.coefficients.loc[indexer,year].to_frame(),['vintage','supply_technology','resource_bin'])])
                else:
                    indexer =  util.level_specific_indexer(node.active_coefficients_untraded,'supply_node',[self.electricity_nodes[zone]+[zone]])
                    energy_demand =  util.DfOper.mult([node.active_coefficients_untraded, node.active_supply])
                    capacity = util.DfOper.divi([energy_demand,node.capacity_factor.values.loc[:,year].to_frame()])/ util.unit_conversion(unit_to_num='hour', unit_from_num = 'year')[0]
                    capacity.replace([np.nan,np.inf], 0,inplace=True)
                if zone == self.distribution_node_id and 'demand_sector' not in node.stock.values.index.names:
                    #requires energy on the distribution system to be allocated to feeder for dispatch
                    energy_demand = DfOper.mult([energy_demand, node.active_supply.groupby(level=[cfg.primary_geography,'demand_sector']).transform(lambda x: x/x.sum())])
                    capacity = DfOper.mult([capacity, node.active_supply.groupby(level=[cfg.primary_geography,'demand_sector']).transform(lambda x: x/x.sum())])
                #geomap to dispatch geography
                remove_levels = []
                if cfg.dispatch_geography != cfg.primary_geography:
                    geography_map_key = node.geography_map_key if hasattr(node, 'geography_map_key') and node.geography_map_key is not None else cfg.cfgfile.get('case','default_geography_map_key')
                    map_df = cfg.geo.map_df(cfg.primary_geography,cfg.dispatch_geography,normalize_as='total',map_key=geography_map_key, eliminate_zeros=False)
                    energy_demand = DfOper.mult([energy_demand,map_df])
                    capacity = DfOper.mult([capacity,map_df])
                    remove_levels.append(cfg.dispatch_geography)
                if zone == self.distribution_node_id:
                    #specific for distribution node because of feeder allocation requirement
                    indexer = util.level_specific_indexer(self.dispatch_feeder_allocation.values, 'year', year)
                    energy_demand = util.remove_df_levels(util.DfOper.mult([energy_demand, self.dispatch_feeder_allocation.values.loc[indexer, ]]), 'demand_sector')
                    capacity = util.remove_df_levels(util.DfOper.mult([capacity, self.dispatch_feeder_allocation.values.loc[indexer, ]]), 'demand_sector')
                    remove_levels.append('dispatch_feeder')
                    for geography in cfg.dispatch_geographies:
                        for dispatch_feeder in self.dispatch_feeders:
                            indexer = util.level_specific_indexer(energy_demand, [cfg.dispatch_geography, 'supply_node', 'dispatch_feeder'],[geography,zone,dispatch_feeder])
                            self.flexible_load[node.id][geography][zone][dispatch_feeder]['energy']= util.remove_df_levels(energy_demand.loc[indexer,:],remove_levels)
                            indexer = util.level_specific_indexer(capacity, [cfg.dispatch_geography, 'supply_node', 'dispatch_feeder'],[geography,zone,dispatch_feeder])
                            self.flexible_load[node.id][geography][zone][dispatch_feeder]['capacity']= util.remove_df_levels(capacity.loc[indexer,:],remove_levels)
                else:
                    remove_levels.append('demand_sector')
                    for geography in cfg.dispatch_geographies:
                        #feeder is set to 0 for flexible load not on the distribution system
                        indexer = util.level_specific_indexer(energy_demand, [cfg.dispatch_geography, 'supply_node'],[geography,zone])
                        self.flexible_load[node.id][geography][zone][0]['energy']= util.remove_df_levels(energy_demand.loc[indexer,:],remove_levels)
                        indexer = util.level_specific_indexer(capacity,[cfg.dispatch_geography, 'supply_node'],[geography,zone])
                        self.flexible_load[node.id][geography][zone][0]['capacity']= util.remove_df_levels(capacity.loc[indexer,:],remove_levels)
        self.flexible_load = util.freeze_recursivedict(self.flexible_load)

    def prepare_flexible_gen(self,year):
        """Calculates the availability of flexible generation for the hourly dispatch. Used for nodes like hydroelectricity. 
        Args:
            year (int) = year of analysis 
            loop (int or str) = loop identifier
        Sets:
            flexible_gen (dict) = dictionary with keys of  supply_node_id, 'energy' or 'capacity', 'geography', zone (i.e. transmission grid
            or distribution grid), and dispatch_feeder and values of a np.array()
        """
        self.flexible_gen = util.recursivedict()
        for zone in self.dispatch_zones:
            non_thermal_dispatch_nodes = [x for x in self.electricity_gen_nodes[zone]['flexible'] if x not in self.nodes[self.thermal_dispatch_node_id].values.index.get_level_values('supply_node')]
            for node_id in non_thermal_dispatch_nodes:
                node = self.nodes[node_id]
                energy = node.active_supply
                capacity = node.stock.values.loc[:,year].to_frame()
                if zone == self.distribution_node_id and 'demand_sector' not in node.stock.values.index.names:
                    #requires energy on the distribution system to be allocated to feeder for dispatch
                    energy = DfOper.mult([energy, node.active_supply.groupby(level=[cfg.primary_geography,'demand_sector']).transform(lambda x: x/x.sum())])
                    capacity = DfOper.mult([capacity, node.active_supply.groupby(level=[cfg.primary_geography,'demand_sector']).transform(lambda x: x/x.sum())])
                energy = util.remove_df_levels(energy,['vintage', 'supply_technology'])
                capacity = util.remove_df_levels(capacity,['vintage', 'supply_technology'])
                #geomap to dispatch geography
                if cfg.dispatch_geography != cfg.primary_geography:
                    geography_map_key = node.geography_map_key if hasattr(node, 'geography_map_key') and node.geography_map_key is not None else cfg.cfgfile.get('case','default_geography_map_key')
                    map_df = cfg.geo.map_df(cfg.primary_geography,cfg.dispatch_geography,normalize_as='total',map_key=geography_map_key, eliminate_zeros=False)
                    energy = DfOper.mult([energy,map_df])
                    capacity = DfOper.mult([capacity,map_df])
                if zone == self.distribution_node_id:
                    #specific for distribution node because of feeder allocation requirement
                    indexer = util.level_specific_indexer(self.dispatch_feeder_allocation.values, 'year', year)
                    energy = util.remove_df_levels(util.DfOper.mult([energy, self.dispatch_feeder_allocation.values.loc[indexer, ]]), 'demand_sector')
                    capacity = util.remove_df_levels(util.DfOper.mult([capacity, self.dispatch_feeder_allocation.values.loc[indexer, ]]), 'demand_sector')
                    for geography in cfg.dispatch_geographies:
                        for dispatch_feeder in self.dispatch_feeders:
                            indexer = util.level_specific_indexer(energy, cfg.dispatch_geography, geography)
                            remove_list =  ['dispatch_feeder','supply_node']
                            if cfg.primary_geography!=cfg.dispatch_geography:
                                remove_list.append(cfg.dispatch_geography)
                            indexer = util.level_specific_indexer(energy, [cfg.dispatch_geography, 'dispatch_feeder'],[geography,zone,dispatch_feeder])
                            self.flexible_gen[node.id][geography][zone][dispatch_feeder]['energy']= util.remove_df_levels(energy.loc[indexer,:],remove_list)
                            indexer = util.level_specific_indexer(capacity, [cfg.dispatch_geography, 'dispatch_feeder'],[geography,zone,dispatch_feeder])
                            self.flexible_gen[node.id][geography][zone][dispatch_feeder]['capacity']= util.remove_df_levels(capacity.loc[indexer,:],remove_list)
                else:
                    for geography in cfg.dispatch_geographies:
                        #feeder is set to 0 for flexible load not on the distribution system
                        indexer = util.level_specific_indexer(energy, cfg.dispatch_geography, geography)
                        remove_list =  ['demand_sector','supply_node']
                        if cfg.primary_geography!=cfg.dispatch_geography:
                            remove_list.append(cfg.dispatch_geography)
                        self.flexible_gen[node.id][geography][zone][0]['energy'] = util.remove_df_levels(energy.loc[indexer,:],remove_list)
                        indexer = util.level_specific_indexer(capacity,cfg.dispatch_geography, geography)
                        self.flexible_gen[node.id][geography][zone][0]['capacity'] = util.remove_df_levels(capacity.loc[indexer,:],remove_list)
        self.flexible_gen = util.freeze_recursivedict(self.flexible_gen)

    def _help_prepare_non_flexible_load_or_gen(self, energy, year, node, zone):
        energy['dispatch_zone'] = zone
        energy['supply_node'] = node.id # replace supply node with the node id
        energy = energy.set_index(['dispatch_zone', 'supply_node'], append=True)
        if zone == self.distribution_node_id:
            energy = util.DfOper.mult([energy, self.dispatch_feeder_allocation.values.xs(year, level='year')])
        else:
            energy['dispatch_feeder'] = 0
            energy = energy.set_index('dispatch_feeder', append=True)
        energy = util.remove_df_levels(energy, 'demand_sector')

        if cfg.dispatch_geography != cfg.primary_geography:
           #geomap to dispatch geography
            geography_map_key = node.geography_map_key if hasattr(node, 'geography_map_key') and node.geography_map_key is not None else cfg.cfgfile.get('case','default_geography_map_key')
            map_df = cfg.geo.map_df(cfg.primary_geography, cfg.dispatch_geography, normalize_as='total', map_key=geography_map_key, eliminate_zeros=False)
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
            for node_id in self.electricity_load_nodes[zone]['non_flexible']:
                node = self.nodes[node_id]
                indexer = util.level_specific_indexer(node.active_coefficients_untraded,'supply_node',[list(set(self.electricity_nodes[zone]+[zone]))])
                energy = DfOper.mult([node.active_supply, node.active_coefficients_untraded.loc[indexer,:]])
                energy = util.remove_df_levels(energy, ['supply_node', 'efficiency_type']) # supply node is electricity transmission or distribution
                energy = self._help_prepare_non_flexible_load_or_gen(energy, year, node, zone)
                self.non_flexible_load.append(energy) # important that the order of the columns be correct
        if len(self.non_flexible_load):
            self.non_flexible_load = pd.concat(self.non_flexible_load).sort()
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
            non_thermal_dispatch_nodes = [x for x in self.electricity_gen_nodes[zone]['non_flexible'] if x not in
                                            self.nodes[self.thermal_dispatch_node_id].values.index.get_level_values('supply_node')]
            for node_id in non_thermal_dispatch_nodes:
                node = self.nodes[node_id]
                energy = node.active_supply.copy()
                energy = self._help_prepare_non_flexible_load_or_gen(energy, year, node, zone)
                self.non_flexible_gen.append(energy)
        if len(self.non_flexible_gen):
            self.non_flexible_gen = pd.concat(self.non_flexible_gen).sort()
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
        self.set_electricity_gen_nodes(self.nodes[self.distribution_node_id],self.nodes[self.distribution_node_id])
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

            if cfg.cfgfile.get('output_detail', 'keep_dispatch_outputs_in_model').lower() == 'true':
                self.outputs.hourly_dispatch_results = pd.concat([self.outputs.hourly_dispatch_results, self.bulk_dispatch])
            else:
                # we are going to save them as we go along
                result_df = self.outputs.clean_df(self.bulk_dispatch)
                keys = [self.scenario.name.upper(), cfg.timestamp]
                names = ['SCENARIO','TIMESTAMP']
                for key, name in zip(keys, names):
                    result_df = pd.concat([result_df], keys=[key], names=[name])
                Output.write(result_df, 'hourly_dispatch_results.csv', os.path.join(cfg.workingdir, 'dispatch_outputs'))
        self.calculate_thermal_totals(year)
        self.calculate_curtailment(year)
                
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
        embodied_cost_df = embodied_cost_df.reorder_levels([cfg.primary_geography,'demand_sector','supply_node']).to_frame()
        embodied_cost_df.sort(inplace=True)
        self.dispatch_df = embodied_cost_df
        self.thermal_dispatch_nodes = [x for x in set(list(self.nodes[self.thermal_dispatch_node_id].active_coefficients.index.get_level_values('supply_node')))]
        dispatch_resource_list = []
        for node_id in self.thermal_dispatch_nodes:
            stock_values = self.nodes[node_id].stock.values.loc[:,year].to_frame()
            cap_factor_values = self.nodes[node_id].stock.capacity_factor.loc[:,year].to_frame()
            stock_values = stock_values[((stock_values.index.get_level_values('vintage')==year) == True) | ((stock_values[year]>0) == True)]
            stock_values = stock_values[((cap_factor_values[year]>0) == True)]
            resources = [str(x[0]) for x in stock_values.groupby(level = stock_values.index.names).groups.values()] 
            inputs_and_outputs = ['capacity','cost','maintenance_outage_rate','forced_outage_rate','capacity_weights','must_run','gen_cf','generation','stock_changes','thermal_capacity_multiplier']
            node_list = [node_id]
            index = pd.MultiIndex.from_product([cfg.dispatch_geographies, node_list, resources,inputs_and_outputs],names = [cfg.dispatch_geography, 'supply_node','thermal_generators','IO'])
            dispatch_resource_list.append(util.empty_df(index=index,columns=[year],fill_value=0.0))
        self.active_thermal_dispatch_df = pd.concat(dispatch_resource_list)
        self.active_thermal_dispatch_df.sort(inplace=True)
        for node_id in self.thermal_dispatch_nodes:
            node = self.nodes[node_id]
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
                        co2_cost = util.DfOper.mult([emissions_rate, 1-node.rollover_output(tech_class = 'co2_capture', stock_att='exist',year=year)]) * co2_price * util.unit_conversion(unit_from_den='ton',unit_to_den=cfg.cfgfile.get('case','mass_unit'))[0]
                        active_dispatch_costs = util.DfOper.add([node.active_dispatch_costs ,co2_cost])
                    stock_values = node.stock.values.loc[:,year].to_frame()
                    stock_values = stock_values[((stock_values.index.get_level_values('vintage')==year) == True) | ((stock_values[year]>0) == True)]
                    capacity_factor = copy.deepcopy(node.stock.capacity_factor.loc[:,year].to_frame())
                    if cfg.dispatch_geography != cfg.primary_geography:
                        geography_map_key = node.geography_map_key if hasattr(node, 'geography_map_key') and node.geography_map_key is not None else cfg.cfgfile.get('case','default_geography_map_key')
                        int_map_df = cfg.geo.map_df(cfg.primary_geography,cfg.dispatch_geography,  normalize_as='intensity', map_key=geography_map_key, eliminate_zeros=False)
                        tot_map_df = cfg.geo.map_df(cfg.primary_geography, cfg.dispatch_geography, normalize_as='total', map_key=geography_map_key, eliminate_zeros=False).swaplevel(0,1)
                        active_dispatch_costs = util.remove_df_levels(util.DfOper.mult([int_map_df,active_dispatch_costs],fill_value=0.0),cfg.primary_geography).swaplevel(0,cfg.dispatch_geography)
                        active_dispatch_costs = active_dispatch_costs.replace([np.nan,np.inf],0)
                        stock_values = util.DfOper.mult([tot_map_df,stock_values],fill_value=0.0).swaplevel(0,cfg.dispatch_geography).swaplevel(1,cfg.primary_geography)
                        capacity_factor = util.remove_df_levels(util.DfOper.mult([int_map_df, capacity_factor,],fill_value=0.0),cfg.primary_geography).swaplevel(0,cfg.dispatch_geography)
                    groups = [x[0]for x in stock_values.groupby(level=stock_values.index.names).groups.values()]
                    for group in groups:
                        dispatch_geography = group[0]
                        if cfg.primary_geography == cfg.dispatch_geography:
                            geomapped_resource = group
                            resource = group
                        else:
                            geomapped_resource = (group[0],) +group[2:]
                            resource = group[1:]
                        try:
                            self.active_thermal_dispatch_df.loc[(dispatch_geography,node.id,str(resource),'capacity'),year] = stock_values.loc[group].values[0]
                            self.active_thermal_dispatch_df.loc[(dispatch_geography,node.id,str(resource), 'cost'),year] = active_dispatch_costs.loc[geomapped_resource].values[0]
                            self.active_thermal_dispatch_df.loc[(dispatch_geography,node.id,str(resource),'maintenance_outage_rate'),year] = (1- capacity_factor.loc[geomapped_resource].values[0])*.9
                            self.active_thermal_dispatch_df.loc[(dispatch_geography,node.id, str(resource), 'forced_outage_rate'),year]= np.nan_to_num((1- capacity_factor.loc[geomapped_resource].values[0])*.1/(1-self.active_thermal_dispatch_df.loc[(dispatch_geography,node.id,str(resource),'maintenance_outage_rate'),year]))
                            self.active_thermal_dispatch_df.loc[(dispatch_geography,node.id, str(resource), 'thermal_capacity_multiplier'),year] = node.technologies[resource[1]].thermal_capacity_multiplier
                            if hasattr(node,'is_flexible') and node.is_flexible == False:
                                self.active_thermal_dispatch_df.loc[(dispatch_geography,node.id, str(resource), 'must_run'),year] = 1
                        except:
                            pdb.set_trace()
        self.active_thermal_dispatch_df = self.active_thermal_dispatch_df[((np.array([int(x[-6:-2]) for x in self.active_thermal_dispatch_df.index.get_level_values('thermal_generators')])==year) == True) | ((self.active_thermal_dispatch_df.groupby(level=[cfg.dispatch_geography,'thermal_generators']).transform(lambda x: x.sum())[year]>0) == True)]

    def capacity_weights(self,year):
        """sets the share of new capacity by technology and location to resolve insufficient capacity in the thermal dispatch
        Args:
            year (int) = year of analysis
        Sets:
            thermal_dispatch_dict (dict) = set dictionary with keys of dispatch geography, 'capacity_weights', and a tuple thermal resource identifier. Values are the share of new capacity
            by thermal resource identifier in a specified dispatch geography.  
        """
        weights = self.nodes[self.thermal_dispatch_node_id].values.loc[:,year].to_frame().groupby(level=[cfg.primary_geography,'supply_node']).mean()
        if cfg.dispatch_geography != cfg.primary_geography:
            map_df = cfg.geo.map_df(cfg.primary_geography,cfg.dispatch_geography, normalize_as='intensity', eliminate_zeros=False)
            weights = util.DfOper.mult([map_df,weights]).swaplevel(0,cfg.dispatch_geography)
            for dispatch_geography in cfg.dispatch_geographies:
                for node_id in self.thermal_nodes:
                    node = self.nodes[node_id]
                    resources = list(set(util.df_slice(self.active_thermal_dispatch_df, [dispatch_geography, node_id], [cfg.dispatch_geography, 'supply_node']).index.get_level_values('thermal_generators')))
                    for resource in resources:
                        resource = eval(resource)
                        if resource[-1] == year:
                            self.active_thermal_dispatch_df.loc[(dispatch_geography,node.id, str(resource), 'capacity_weights'),year]= (util.df_slice(weights,[dispatch_geography, resource[0], node_id],[cfg.dispatch_geography,cfg.primary_geography,'supply_node']).values * node.active_weighted_sales.loc[resource[0:-1:1],:].values)[0][0]
        else:
            for dispatch_geography in cfg.dispatch_geographies:
                for node_id in self.thermal_nodes:
                    node = self.nodes[node_id]
                    resources = list(set(util.df_slice(self.active_thermal_dispatch_df, [dispatch_geography, node_id], [cfg.dispatch_geography, 'supply_node']).index.get_level_values('thermal_generators')))
                    for resource in resources:
                        resource = eval(resource)
                        if resource[-1] == year and resource[0]== dispatch_geography:
                            self.active_thermal_dispatch_df.loc[(dispatch_geography,node.id, str(resource), 'capacity_weights'),year]= (util.df_slice(weights,[dispatch_geography, node_id],[cfg.dispatch_geography,'supply_node']).values * node.active_weighted_sales.loc[resource[0:-1:1],:].values)[0][0]
    
    
    def calculate_weighted_sales(self,year):
        """sets the anticipated share of sales by technology for capacity additions added in the thermal dispatch. 
        Thermal dispatch inputs determines share by supply_node, so we have to determine the share of technologies for 
        that capacity addition.
        
        Args:
            year (int) = year of analysis
        Sets:
            active_weighted_sales (dataframe) = share of sales by technology for each thermal dispatch node
        """         
        for node_id in self.thermal_nodes:
            node = self.nodes[node_id] 
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
            for tech_id in node.tech_ids:
                weighted_sales[tech_id] = weighted_sales['value']
            weighted_sales = weighted_sales[node.tech_ids]
            weighted_sales*=total
            weighted_sales =  weighted_sales.sum(axis=1).to_frame()
            weighted_sales.columns = ['value']
            weighted_sales *= (np.column_stack(weighted_sales.index.get_level_values('vintage').values).T-vintage_start)
            weighted_sales = util.remove_df_levels(weighted_sales,'vintage')
            weighted_sales = weighted_sales.groupby(level = cfg.primary_geography).transform(lambda x: x/x.sum())
            node.active_weighted_sales = weighted_sales
            node.active_weighted_sales = node.active_weighted_sales.fillna(1/float(len(node.tech_ids)))

    def solve_thermal_dispatch(self, year):
        # MOVE
        """solves the thermal dispatch, updating the capacity factor for each thermal dispatch technology
        and adding capacity to each node based on determination of need"""
        logging.info('      solving thermal dispatch')
        self.calculate_weighted_sales(year)
        self.capacity_weights(year)
        parallel_params = list(zip(cfg.dispatch_geographies,[util.df_slice(self.active_thermal_dispatch_df,x,cfg.dispatch_geography,drop_level=False) for x in cfg.dispatch_geographies],
                                   [cfg.dispatch_geography]*len(cfg.dispatch_geographies),
                                    [util.df_slice(self.bulk_net_load,2,'timeshift_type')]*len(cfg.dispatch_geographies),
                                    [year in self.dispatch_write_years]*len(cfg.dispatch_geographies),
                                   [float(cfg.cfgfile.get('opt', 'operating_reserves'))]*len(cfg.dispatch_geographies),
                                   [cfg.cfgfile.get('opt', 'schedule_maintenance').lower() == 'true']*len(cfg.dispatch_geographies)))

        if cfg.cfgfile.get('case','parallel_process').lower() == 'true':
            dispatch_results = helper_multiprocess.safe_pool(dispatch_generators.run_thermal_dispatch, parallel_params)
        else:
            dispatch_results = []
            for params in parallel_params:
                dispatch_results.append(dispatch_generators.run_thermal_dispatch(params))

        thermal_dispatch_df, detailed_results = zip(*dispatch_results) #both of these are lists by geography
        thermal_dispatch_df = pd.concat(thermal_dispatch_df).sort()
        self.active_thermal_dispatch_df = thermal_dispatch_df

        if year in self.dispatch_write_years:
            for x in detailed_results:
                x['dispatch_by_category'].index = shape.shapes.active_dates_index

            thermal_shape = pd.concat([x['dispatch_by_category'] for x in detailed_results],axis=0,keys=cfg.dispatch_geographies)
            thermal_shape = thermal_shape.stack().to_frame()
            thermal_shape = pd.concat([thermal_shape], keys=[year], names=['year'])
            thermal_shape.index.names = ['year', cfg.dispatch_geography, 'weather_datetime','supply_technology']
            thermal_shape.columns = [cfg.calculation_energy_unit.upper()]
            thermal_shape_dataframe = self.outputs.clean_df(thermal_shape)
            util.replace_index_name(thermal_shape_dataframe,'DISPATCH_OUTPUT','SUPPLY_TECHNOLOGY')
            self.bulk_dispatch = pd.concat([self.bulk_dispatch, -thermal_shape_dataframe.reorder_levels(self.bulk_dispatch.index.names)])

            bulk_marginal_cost = pd.concat([pd.DataFrame(outputs['market_price'], index=shape.shapes.active_dates_index) for outputs in detailed_results],axis=0,keys=cfg.dispatch_geographies)
            bulk_production_cost = pd.concat([pd.DataFrame(outputs['production_cost'], index=shape.shapes.active_dates_index) for outputs in detailed_results],axis=0,keys=cfg.dispatch_geographies)
            bulk_marginal_cost = pd.concat([bulk_marginal_cost], keys=[year], names=['year'])
            bulk_production_cost = pd.concat([bulk_production_cost], keys=[year], names=['year'])
            bulk_marginal_cost.index.names = ['year', cfg.dispatch_geography, 'weather_datetime']
            bulk_production_cost.index.names = ['year', cfg.dispatch_geography, 'weather_datetime']
            # we really don't want this ever to be anything but $/MWh
            bulk_marginal_cost *= util.unit_convert(1, unit_from_den=cfg.calculation_energy_unit,unit_to_den='megawatt_hour')
            bulk_marginal_cost.columns = ["{} / {}".format(cfg.output_currency.upper(), 'MWh')]
            bulk_production_cost.columns = [cfg.output_currency.upper()]
            # bulk_marginal_cost = self.outputs.clean_df(bulk_marginal_cost)
            # bulk_production_cost = self.outputs.clean_df(bulk_production_cost)

            if cfg.cfgfile.get('output_detail', 'keep_dispatch_outputs_in_model').lower() == 'true':
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


        for node_id in self.thermal_dispatch_nodes:
            node = self.nodes[node_id]
            for dispatch_geography in cfg.dispatch_geographies:
                dispatch_df = util.df_slice(self.active_thermal_dispatch_df.loc[:,:],[dispatch_geography,node_id], [cfg.dispatch_geography,'supply_node'],drop_level=False)
                resources = list(set([eval(x) for x in dispatch_df.index.get_level_values('thermal_generators')]))
                for resource in resources:
                    capacity_indexer = util.level_specific_indexer(dispatch_df, ['thermal_generators','IO'], [str(resource),'capacity'])
                    dispatch_capacity_indexer = util.level_specific_indexer(dispatch_df,['thermal_generators','IO'], [str(resource),'stock_changes'])
                    node.stock.dispatch_cap.loc[resource,year] += dispatch_df.loc[dispatch_capacity_indexer,year].values
            node.stock.capacity_factor.loc[:,year] = 0
            for dispatch_geography in cfg.dispatch_geographies:
                dispatch_df = util.df_slice(self.active_thermal_dispatch_df.loc[:,:],[dispatch_geography,node_id], [cfg.dispatch_geography,'supply_node'],drop_level=False)
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
        if year == int(cfg.cfgfile.get('case','current_year')):
            self.curtailment_list = []
        bulk_net_load = util.df_slice(self.bulk_net_load,2,'timeshift_type')
        initial_overgen = copy.deepcopy(bulk_net_load)
        initial_overgen[initial_overgen.values>0]=0
        initial_overgen *= -1
        initial_overgen = initial_overgen.groupby(level=cfg.dispatch_geography).sum()
        bulk_net_load[bulk_net_load.values<0]=0
        curtailment = util.DfOper.add([util.DfOper.subt([self.thermal_totals.sum().to_frame(),bulk_net_load.groupby(level=cfg.dispatch_geography).sum()]),initial_overgen])
        supply = self.nodes[self.bulk_id].active_supply
        if cfg.primary_geography!= cfg.dispatch_geography:
            map_df = cfg.geo.map_df(cfg.primary_geography,cfg.dispatch_geography,normalize_as='total',eliminate_zeros=False)
            supply = util.DfOper.mult([supply,map_df])
        normal_supply = supply.groupby(level=[cfg.dispatch_geography]).transform(lambda x: x/x.sum())
        curtailment = util.DfOper.mult([curtailment,normal_supply])
        if cfg.primary_geography!= cfg.dispatch_geography:
            curtailment = util.remove_df_levels(curtailment,cfg.dispatch_geography)
        curtailment.columns = ['value']
        self.curtailment_list.append(curtailment)
        if year == max(self.dispatch_years):
            keys = self.dispatch_years
            names = ['year']
            self.outputs.s_curtailment = pd.concat(self.curtailment_list,keys=keys, names=names)
            util.replace_index_name(self.outputs.s_curtailment,'sector','demand_sector')
            self.outputs.s_curtailment.columns = [cfg.calculation_energy_unit.upper()]
   
    def update_coefficients_from_dispatch(self,year):
        # MOVE
        self.update_thermal_coefficients(year)
        self.store_active_thermal_df(year)
#        self.update_bulk_coefficients()

    def update_thermal_coefficients(self,year):
        # MOVE
        if cfg.primary_geography != cfg.dispatch_geography:
            map_df = cfg.geo.map_df(cfg.primary_geography,cfg.dispatch_geography,normalize_as='total',eliminate_zeros=False)
            thermal_demand  = util.DfOper.mult([self.nodes[self.thermal_dispatch_node_id].active_supply,map_df])
            thermal_demand = thermal_demand.unstack(cfg.dispatch_geography)
            thermal_demand.columns = thermal_demand.columns.droplevel()
            demand_supply_ratio = util.DfOper.divi([thermal_demand.groupby(level=cfg.primary_geography).sum(),self.thermal_totals.groupby(level=cfg.primary_geography).sum()])
            demand_supply_ratio[demand_supply_ratio>1]=1
            demand_supply_ratio.replace(np.nan,0,inplace=True) 
            df =  self.nodes[self.thermal_dispatch_node_id].active_coefficients_total * 0
            native_thermal = util.DfOper.mult([self.thermal_totals,demand_supply_ratio])
            native_thermal_coefficients = util.DfOper.divi([native_thermal.sum(axis=1).to_frame(),
                                                            self.nodes[self.thermal_dispatch_node_id].active_supply.groupby(level=cfg.primary_geography).sum()]).fillna(0)
            residual_demand = util.DfOper.subt([thermal_demand.groupby(level=cfg.primary_geography).sum(),native_thermal.groupby(level=cfg.primary_geography).sum()])
            residual_demand[residual_demand<0] = 0
            remaining_supply = util.DfOper.subt([self.thermal_totals,native_thermal])
            residual_share = util.DfOper.divi([residual_demand.sum().to_frame(),remaining_supply.sum().to_frame()]).fillna(0)
            residual_share[residual_share>1]=1
            residual_share.replace(np.inf,0,inplace=True)
            residual_supply = copy.deepcopy(remaining_supply)
            excess_supply = copy.deepcopy(remaining_supply)
            excess_supply.loc[:,:] = remaining_supply.values * np.column_stack((1-residual_share).values)
            excess_thermal = excess_supply
            excess_thermal_coefficients = util.DfOper.divi([excess_thermal.sum(axis=1).to_frame(),self.nodes[self.thermal_dispatch_node_id].active_supply.groupby(level=cfg.primary_geography).sum()]).fillna(0)
            residual_supply.loc[:,:] = remaining_supply.values * np.column_stack(residual_share.values)
            undersupply_adjustment = (residual_supply.sum()/residual_demand.sum())
            undersupply_adjustment[undersupply_adjustment>1]=1
            residual_supply_share = residual_supply/residual_supply.sum() * undersupply_adjustment
            residual_supply_share = residual_supply_share.fillna(0)
            util.replace_index_name(residual_supply_share,cfg.primary_geography + "from",cfg.primary_geography)
            residual_supply_share = residual_supply_share.stack().to_frame()
            util.replace_index_name(residual_supply_share,cfg.dispatch_geography)
            residual_demand_stack = residual_demand.stack().to_frame()
            util.replace_index_name(residual_demand_stack,cfg.dispatch_geography)
            residual_thermal = util.remove_df_levels(util.DfOper.mult([residual_supply_share,residual_demand_stack]),cfg.dispatch_geography)
            residual_thermal = residual_thermal.unstack(cfg.primary_geography)
            residual_thermal.columns = residual_thermal.columns.droplevel()
            residual_thermal.loc[:,:] = residual_thermal.values/np.column_stack(self.nodes[self.thermal_dispatch_node_id].active_supply.groupby(level=cfg.primary_geography).sum().T.values).T
            residual_thermal_coefficients = residual_thermal.fillna(0)
            util.replace_index_name(residual_thermal,cfg.primary_geography,cfg.primary_geography + "from")
            for row_sector in self.demand_sectors:
                for col_sector in self.demand_sectors:
                    for row_geo in cfg.geographies:
                        for col_geo in cfg.geographies:
                            if row_sector == col_sector and row_geo == col_geo:
                                native_coeff_row_indexer = util.level_specific_indexer(native_thermal_coefficients,[cfg.primary_geography],[row_geo])
                                excess_coeff_row_indexer = util.level_specific_indexer(excess_thermal_coefficients,[cfg.primary_geography],[row_geo])
                                df_row_indexer = util.level_specific_indexer(df,[cfg.primary_geography,'demand_sector'],[row_geo,row_sector])
                                df_col_indexer = util.level_specific_indexer(df,[cfg.primary_geography,'demand_sector'],[col_geo,col_sector],axis=1)
                                df.loc[df_row_indexer,df_col_indexer] = np.column_stack(df.loc[df_row_indexer,df_col_indexer].values).T + np.column_stack(native_thermal_coefficients.loc[native_coeff_row_indexer,:].values).T
                                df.loc[df_row_indexer,df_col_indexer] = np.column_stack(df.loc[df_row_indexer,df_col_indexer].values).T + np.column_stack(excess_thermal_coefficients.loc[excess_coeff_row_indexer,:].values).T
                            elif row_sector == col_sector:
                                df_row_indexer = util.level_specific_indexer(df,[cfg.primary_geography,'demand_sector'],[row_geo,row_sector])
                                df_col_indexer = util.level_specific_indexer(df,[cfg.primary_geography,'demand_sector'],[col_geo,col_sector],axis=1)
                                residual_coeff_row_indexer = util.level_specific_indexer(residual_thermal_coefficients,[cfg.primary_geography],[row_geo])
                                residual_coeff_col_indexer = util.level_specific_indexer(residual_thermal_coefficients,[cfg.primary_geography],[col_geo],axis=1)
                                df.loc[df_row_indexer,df_col_indexer] = np.column_stack(df.loc[df_row_indexer,df_col_indexer].values).T + np.column_stack(residual_thermal_coefficients.loc[residual_coeff_row_indexer,residual_coeff_col_indexer].values).T
        else:     
            df = util.DfOper.divi([self.thermal_totals,util.remove_df_levels(self.nodes[self.thermal_dispatch_node_id].active_supply,'demand_sector')])
            df = pd.concat([df]*len(self.demand_sectors),keys=self.demand_sectors,names=['demand_sector'])
            df = pd.concat([df]*len(self.demand_sectors),keys=self.demand_sectors,names=['demand_sector'],axis=1)
            df = df.reorder_levels([cfg.primary_geography,'demand_sector','supply_node'])
            df = df.reorder_levels([cfg.primary_geography,'demand_sector'],axis=1)
            df.sort(inplace=True)
            df.sort(inplace=True, axis=1)
            for row_sector in self.demand_sectors:
                for col_sector in self.demand_sectors:
                    if row_sector != col_sector:
                        row_indexer = util.level_specific_indexer(df,'demand_sector',row_sector,axis=0)
                        col_indexer = util.level_specific_indexer(df,'demand_sector',col_sector,axis=1)
                        df.loc[row_indexer,col_indexer] = 0                  
        normalized = df.groupby(level=['demand_sector']).transform(lambda x: x/x.sum())
#        df[df<normalized] = normalized
        bulk_multiplier = df.sum()
        df = normalized
        df.replace([np.inf,np.nan],0,inplace=True)
        for row_geo in cfg.geographies:
            for col_geo in cfg.geographies:
                if row_geo == col_geo:
                    row_indexer = util.level_specific_indexer(df,cfg.primary_geography,row_geo)
                    col_indexer = util.level_specific_indexer(df,cfg.primary_geography,col_geo, axis=1)
                    sliced = df.loc[row_indexer,col_indexer]                    
                    sliced = sliced.clip(lower=1E-7)
                    df.loc[row_indexer,col_indexer] = sliced
        self.nodes[self.thermal_dispatch_node_id].active_coefficients_total = df
        indexer = util.level_specific_indexer(self.nodes[self.bulk_id].values,'supply_node',self.thermal_dispatch_node_id)
        self.nodes[self.bulk_id].values.loc[indexer, year] *= bulk_multiplier.values
        thermal_df = copy.deepcopy(self.nodes[self.bulk_id].values.loc[indexer, year])
        thermal_df[thermal_df>1]=1
        self.nodes[self.bulk_id].values.loc[indexer, year] =0
        #don't normalize these if it's an evolved run. Leave curtailment. Simplifies per-unit accounting
        if cfg.evolved_run == 'false':
            pass
            #self.nodes[self.bulk_id].values.loc[:, year] = util.DfOper.mult([self.nodes[self.bulk_id].values.loc[:, year].to_frame().groupby(level=[cfg.primary_geography,'demand_sector']).transform(lambda x: x/x.sum()),1-util.remove_df_levels(thermal_df,'supply_node').to_frame()],expandable=True)
        self.nodes[self.bulk_id].values.loc[indexer, year] = thermal_df
        self.nodes[self.bulk_id].calculate_active_coefficients(year, 3)

    def store_active_thermal_df(self,year):
        active_thermal_dispatch_df = self.active_thermal_dispatch_df.stack().to_frame()
        util.replace_index_name(active_thermal_dispatch_df,'year')
        self.active_thermal_dispatch_df_list.append(active_thermal_dispatch_df)
        if year == max(self.years):
           self.thermal_dispatch_df = pd.concat(self.active_thermal_dispatch_df_list)
           
    def calculate_thermal_totals(self,year):   
        row_index = pd.MultiIndex.from_product([cfg.geographies, self.thermal_dispatch_nodes], names=[cfg.primary_geography, 'supply_node'])
        col_index = pd.MultiIndex.from_product([cfg.dispatch_geographies],names=[cfg.dispatch_geography])
        df = util.empty_df(index=row_index,columns=col_index)
        for dispatch_geography in cfg.dispatch_geographies:
            for node_id in self.thermal_dispatch_nodes:
                thermal_dispatch_df = util.df_slice(self.active_thermal_dispatch_df,[dispatch_geography,'generation',node_id],[cfg.dispatch_geography,'IO','supply_node'])
                resources = list(set(thermal_dispatch_df.index.get_level_values('thermal_generators')))
                for resource in resources:
                    resource = eval(resource)
                    primary_geography = resource[0]
                    df.loc[(primary_geography,node_id),(dispatch_geography)] += np.nan_to_num(thermal_dispatch_df.loc[str(resource),:].values)
        self.thermal_totals = df

#    def update_bulk_coefficients(self):
#        bulk_load = util.DfOper.add([self.bulk_load.groupby(level=cfg.dispatch_geography).sum(), util.DfOper.mult([util.DfOper.subt([self.distribution_load,self.distribution_gen]),self.distribution_losses]).groupby(level=cfg.dispatch_geography).sum()])
#        thermal_totals = self.thermal_totals.sum().to_frame()
#        
#        bulk_coefficients = DfOper.divi([thermal_totals, bulk_load])
#        if cfg.dispatch_geography != cfg.primary_geography:
#            map_key = cfg.cfgfile.get('case','default_geography_map_key')
#            map_df = cfg.geo.map_df(cfg.dispatch_geography,cfg.primary_geography,map_key, eliminate_zeros=False)
#            bulk_coefficients = DfOper.mult([bulk_coefficients,map_df]).groupby(level=cfg.primary_geography).sum()
#        bulk_coefficients = pd.concat([bulk_coefficients]*len(self.demand_sectors),keys=self.demand_sectors,names=['demand_sector'])
#        bulk_coefficients = bulk_coefficients.reorder_levels([cfg.primary_geography,'demand_sector'])
#        bulk_coefficients = self.add_column_index(bulk_coefficients)
#        bulk_coefficients.sort(inplace=True,axis=1)
#        bulk_coefficients.sort(inplace=True,axis=0)
#        for row_geography in cfg.geographies:
#            for col_geography in cfg.geographies:
#                for row_sector in self.demand_sectors:
#                    for col_sector in self.demand_sectors:
#                        if row_geography != col_geography or row_sector != col_sector:
#                            row_indexer = util.level_specific_indexer(bulk_coefficients, [cfg.primary_geography,'demand_sector'],[row_geography,row_sector])
#                            col_indexer = util.level_specific_indexer(bulk_coefficients, [cfg.primary_geography,'demand_sector'],[col_geography,col_sector])
#                            bulk_coefficients.loc[row_indexer,col_indexer] = 0
#        indexer = util.level_specific_indexer(self.nodes[self.bulk_id].active_coefficients_total,'supply_node', self.thermal_dispatch_node_id)
#        self.nodes[self.bulk_id].active_coefficients_total.loc[indexer,:] = bulk_coefficients.values
#    

        
    def add_column_index(self, data):
         names = ['demand_sector', cfg.primary_geography]
         keys = [self.demand_sectors, cfg.geo.geographies[cfg.primary_geography]]
         data  = copy.deepcopy(data)
         for key,name in zip(keys,names):
             data  = pd.concat([data]*len(key), axis=1, keys=key, names=[name])
         data.columns = data.columns.droplevel(-1)
         return data 
    
#    def geo_map_thermal_coefficients(self,df,old_geography, new_geography, geography_map_key):
#            if old_geography != new_geography:
#                keys=cfg.geo.geographies[new_geography]
#                name = [new_geography]
#                df = pd.concat([df] * len(keys),keys=keys,names=name,axis=1)
#                df.sort(inplace=True,axis=1)
#                df.sort(inplace=True,axis=0)
#                map_df = cfg.geo.map_df(old_geography,new_geography,geography_map_key,eliminate_zeros=False).transpose()
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
                        raise ValueError('StorageNode %s has technologies with two different supply node locations' %node.id)
                if storage_node_location[0] in self.electricity_nodes[zone]+[zone]:
                    capacity= node.stock.values.loc[:,year].to_frame().groupby(level=[cfg.primary_geography,'supply_technology']).sum()
                    efficiency = copy.deepcopy(node.active_dispatch_coefficients)
                    if 'demand_sector' not in capacity.index.names and zone == self.distribution_node_id: 
                        sector_capacity= []
                        for sector in self.demand_sectors:
                            capacity = copy.deepcopy(capacity) * 1/len(self.demand_sectors)  
                            capacity['demand_sector'] = sector
                            sector_capacity.append(capacity)
                        capacity = pd.concat(sector_capacity)
                        capacity.set_index('demand_sector', append=True, inplace=True)
                        keys = self.demand_sectors
                        name = ['demand_sector']
                        efficiency = pd.concat([efficiency]*len(keys),keys=keys,names=name)
                    if cfg.dispatch_geography != cfg.primary_geography:
                        geography_map_key = node.geography_map_key if hasattr(node, 'geography_map_key') and node.geography_map_key is not None else cfg.cfgfile.get('case','default_geography_map_key')
                        map_df = cfg.geo.map_df(cfg.primary_geography,cfg.dispatch_geography,  normalize_as='total', map_key=geography_map_key, eliminate_zeros=False)
                        capacity = DfOper.mult([capacity, map_df],fill_value=0.0)                
                        efficiency = DfOper.divi([util.remove_df_levels(DfOper.mult([efficiency, capacity]), cfg.primary_geography),util.remove_df_levels(capacity,cfg.primary_geography)]).fillna(0)
                        capacity = util.remove_df_levels(capacity, cfg.primary_geography)
                   #creates an empty database to fill with duration values, which are a technology parameter
                    duration = copy.deepcopy(capacity)*0
                    duration = duration.sort()
                    for tech in node.technologies.values():
                        tech_indexer = util.level_specific_indexer(duration,'supply_technology', tech.id)
                        duration.loc[tech_indexer,:] = tech.discharge_duration
                    efficiency = util.remove_df_levels(efficiency,'supply_node')    
                    if zone == self.distribution_node_id:
                        indexer = util.level_specific_indexer(self.dispatch_feeder_allocation.values, 'year', year)
                        capacity = util.DfOper.mult([capacity, self.dispatch_feeder_allocation.values.loc[indexer, ]])
                        duration = DfOper.divi([util.remove_df_levels(DfOper.mult([duration, capacity]),'demand_sector'),util.remove_df_levels(capacity,'demand_sector')]).fillna(0)
                        efficiency = DfOper.divi([util.remove_df_levels(DfOper.mult([efficiency, capacity]),'demand_sector'),util.remove_df_levels(capacity,'demand_sector')]).fillna(1)
                        capacity = util.remove_df_levels(capacity,'demand_sector')
                        for geography in cfg.dispatch_geographies:
                            for dispatch_feeder in self.dispatch_feeders:
                                for technology in node.technologies.keys():
                                    indexer = util.level_specific_indexer(efficiency, [cfg.dispatch_geography, 'dispatch_feeder','supply_technology'],[geography,dispatch_feeder,technology])
                                    self.storage_efficiency_dict[geography][zone][dispatch_feeder][technology] = efficiency.loc[indexer,:].values[0][0]
                                    indexer = util.level_specific_indexer(capacity, [cfg.dispatch_geography, 'dispatch_feeder','supply_technology'],[geography,dispatch_feeder,technology])
                                    self.storage_capacity_dict['power'][geography][zone][dispatch_feeder][technology] = capacity.loc[indexer,:].values[0][0]
                                    indexer = util.level_specific_indexer(duration, [cfg.dispatch_geography, 'dispatch_feeder','supply_technology'],[geography,dispatch_feeder,technology])
                                    self.storage_capacity_dict['duration'][geography][zone][dispatch_feeder][technology] = duration.loc[indexer,:].values[0][0]
                    else:
                        for geography in cfg.dispatch_geographies:
                            for technology in node.technologies.keys():
                                indexer = util.level_specific_indexer(capacity, [cfg.dispatch_geography, 'supply_technology'],[geography,technology])
                                tech_capacity = self.ensure_frame(util.remove_df_levels(capacity.loc[indexer,:], 'demand_sector'))
                                indexer = util.level_specific_indexer(duration, [cfg.dispatch_geography,'supply_technology'],[geography,technology])
                                tech_duration = self.ensure_frame(util.remove_df_levels(duration.loc[indexer,:], 'demand_sector'))
                                indexer = util.level_specific_indexer(efficiency, [cfg.dispatch_geography, 'supply_technology'],[geography,technology])
                                tech_efficiency = self.ensure_frame(util.remove_df_levels(efficiency.loc[indexer,:], 'demand_sector'))
                                if tech_capacity.values[0][0] == 0:
                                    continue
                                else:
                                    self.storage_capacity_dict['power'][geography][zone][0][technology] = tech_capacity.values[0][0]
                                    self.storage_capacity_dict['duration'][geography][zone][0][technology] = tech_duration.values[0][0]
                                    self.storage_efficiency_dict[geography][zone][0][technology] = tech_efficiency.values[0][0]
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
           for node_id in self.electricity_load_nodes[zone]['non_flexible'] + self.electricity_gen_nodes[zone]['non_flexible']:
               self.nodes[node_id].active_shape = self.nodes[node_id].aggregate_electricity_shapes(year, util.remove_df_levels(util.df_slice(self.dispatch_feeder_allocation.values,year,'year'),year))   

    def _helper_shaped_bulk_and_dist(self, year, energy_slice):
        node_ids = list(set(energy_slice.index.get_level_values('supply_node')))
        if year in self.dispatch_write_years:
            # this keeps supply node as a level
            dfs = [util.DfOper.mult((energy_slice.xs(node_id, level='supply_node'), self.nodes[node_id].active_shape.xs(2, level='timeshift_type'))) for node_id in node_ids]
            df = pd.concat(dfs, keys=node_ids, names=['supply_node'])
        else:
            # this removes supply node as a level and is faster
            df = util.DfOper.add([util.DfOper.mult((energy_slice.xs(node_id, level='supply_node'), self.nodes[node_id].active_shape.xs(2, level='timeshift_type'))) for node_id in node_ids], expandable=False, collapsible=False)

        if cfg.primary_geography != cfg.dispatch_geography:
            # because energy_slice had both geographies, we have effectively done a geomap
            df = util.remove_df_levels(df, cfg.primary_geography)
        return df

    def shaped_dist(self, year, load_or_gen_df, generation):
        if load_or_gen_df is not None and self.distribution_node_id in load_or_gen_df.index.get_level_values('dispatch_zone'):
            dist_slice = load_or_gen_df.xs(self.distribution_node_id, level='dispatch_zone')
            df = self._helper_shaped_bulk_and_dist(year, dist_slice)
    
            if year in self.dispatch_write_years:
                df_output = df.copy()
                df_output = DfOper.mult([df_output, self.distribution_losses,self.transmission_losses])
                df_output =  self.outputs.clean_df(df_output)
                util.replace_index_name(df_output,'DISPATCH_OUTPUT','SUPPLY_NODE')
                df_output = df_output.reset_index(level=['DISPATCH_OUTPUT','DISPATCH_FEEDER'])
                df_output['NEW_DISPATCH_OUTPUT'] = df_output['DISPATCH_FEEDER'] + " " + df_output['DISPATCH_OUTPUT']
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
        else:
            return self.distribution_gen * 0

    def shaped_bulk(self, year, load_or_gen_df, generation):
        if load_or_gen_df is not None and self.transmission_node_id in load_or_gen_df.index.get_level_values('dispatch_zone'):
            bulk_slice = util.remove_df_levels(load_or_gen_df.xs(self.transmission_node_id, level='dispatch_zone'), 'dispatch_feeder')
            node_ids = list(set(bulk_slice.index.get_level_values('supply_node')))
            assert not any(['dispatch_feeder' in self.nodes[node_id].active_shape.index.names for node_id in node_ids])
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
#        t = util.time.time()
        final_demand = self.demand_object.aggregate_electricity_shapes(year)
#        t = util.time_stamp(t)
        if year in self.dispatch_write_years:
            self.output_final_demand_for_bulk_dispatch_outputs(final_demand)

#        t = util.time_stamp(t)

        self.distribution_gen = self.shaped_dist(year, self.non_flexible_gen, generation=True)
        #        t = util.time_stamp(t)
        self.distribution_load = util.DfOper.add([final_demand, self.shaped_dist(year, self.non_flexible_load, generation=False)])
#        t = util.time_stamp(t)
        self.bulk_gen = self.shaped_bulk(year, self.non_flexible_gen, generation=True)
#        t = util.time_stamp(t)
        self.bulk_load = self.shaped_bulk(year, self.non_flexible_load, generation=False)
#        t = util.time_stamp(t)
        self.update_net_load_signal()
#        t = util.time_stamp(t)
        
    def output_final_demand_for_bulk_dispatch_outputs(self,final_demand):
        df_output = util.df_slice(final_demand,2,'timeshift_type')
        df_output = DfOper.mult([df_output, self.distribution_losses,self.transmission_losses])
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
        index = pd.MultiIndex.from_product([cfg.geographies, self.all_nodes], names=[cfg.primary_geography, 'supply_node'])
        for node in self.nodes.values():
            supply_indexer = util.level_specific_indexer(self.io_embodied_cost_df, 'supply_node', node.id)     
            if hasattr(node,'calculate_levelized_costs'):
                node.calculate_levelized_costs(year,loop)
            elif hasattr(node,'calculate_costs'):
                node.calculate_costs(year,loop)
            if hasattr(node, 'active_embodied_cost'):
                self.io_embodied_cost_df.loc[supply_indexer, year] = node.active_embodied_cost.values
        for sector in self.demand_sectors:    
            inverse = self.inverse_dict['cost'][year][sector]
            indexer = util.level_specific_indexer(self.io_embodied_cost_df, 'demand_sector', sector)
            cost = np.column_stack(self.io_embodied_cost_df.loc[indexer,year].values).T
            self.cost_dict[year][sector] = pd.DataFrame(cost * inverse.values, index=index, columns=index)

    def calculate_embodied_emissions(self, year):
        """Calculates the embodied emissions for all supply nodes by multiplying each node's
        active_embodied_emissions by the emissions inverse. Result is stored in 
        the Supply instance's 'emissions_dict' attribute"
        
        Args:
            year (int) = year of analysis 
            loop (int or str) = loop identifier
        """       
        self.calculate_emissions(year)
        row_index = pd.MultiIndex.from_product([cfg.geographies, self.all_nodes, self.ghgs], names=[cfg.primary_geography, 'supply_node', 'ghg'])
        col_index =  pd.MultiIndex.from_product([cfg.geographies, self.all_nodes], names=[cfg.primary_geography, 'supply_node'])
        for node in self.nodes.values():
            supply_indexer = util.level_specific_indexer(self.io_embodied_emissions_df, 'supply_node', node.id)     
            if hasattr(node, 'active_embodied_emissions_rate'):
                try:
                    self.io_embodied_emissions_df.loc[supply_indexer, year] = node.active_embodied_emissions_rate.values
                except:
                    pdb.set_trace()
        for sector in self.demand_sectors:    
            inverse = copy.deepcopy(self.inverse_dict['energy'][year][sector])
            keys = self.ghgs
            name = ['ghg']
            inverse = pd.concat([inverse]*len(keys), keys=keys, names=name)
            inverse = inverse.reorder_levels([cfg.primary_geography,'supply_node','ghg'])
            inverse.sort(axis=0,inplace=True)
            indexer = util.level_specific_indexer(self.io_embodied_emissions_df, 'demand_sector', sector)
            emissions = np.column_stack(self.io_embodied_emissions_df.loc[indexer,year].values).T
            self.emissions_dict[year][sector] = pd.DataFrame(emissions * inverse.values,index=row_index,columns=col_index)


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
        df_list = []
        for year in self.years:
            sector_df_list = []
            keys = self.demand_sectors
            name = ['sector']
            idx = pd.IndexSlice
            for sector in self.demand_sectors:
                link_dict[year][sector].loc[:,:] = embodied_dict[year][sector].loc[:,idx[:, self.map_dict.values()]].values
                link_dict[year][sector]= link_dict[year][sector].stack([cfg.primary_geography,'final_energy']).to_frame()
                link_dict[year][sector] = link_dict[year][sector][link_dict[year][sector][0]!=0]
                levels_to_keep = [x for x in link_dict[year][sector].index.names if x in cfg.output_combined_levels]
                sector_df_list.append(link_dict[year][sector].groupby(level=levels_to_keep).sum())     
            year_df = pd.concat(sector_df_list, keys=keys,names=name)
            df_list.append(year_df)
        self.sector_df_list  = sector_df_list     
        self.df_list = df_list
        keys = self.years
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
                df = df.stack([cfg.primary_geography,'supply_node']).to_frame()
                df.index.names = [cfg.primary_geography+'_input','supply_node_input',cfg.primary_geography,'supply_node']
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


    def map_embodied(self, embodied_dict, link_dict):
        """Maps embodied results for supply node to other supply nodes
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
        df_list = []
        for year in self.years:
            sector_df_list = []
            keys = self.demand_sectors
            name = ['sector']
            idx = pd.IndexSlice
            for sector in self.demand_sectors:
                link_dict[year][sector].loc[:,:] = embodied_dict[year][sector].loc[:,idx[:, self.map_dict.values()]].values
                link_dict[year][sector]= link_dict[year][sector].stack([cfg.primary_geography,'final_energy']).to_frame()
#                levels = [x for x in ['supply_node',cfg.primary_geography +'_supply', 'ghg',cfg.primary_geography,'final_energy'] if x in link_dict[year][sector].index.names]
                link_dict[year][sector] = link_dict[year][sector][link_dict[year][sector][0]!=0]
                levels_to_keep = [x for x in link_dict[year][sector].index.names if x in cfg.output_combined_levels]
                sector_df_list.append(link_dict[year][sector].groupby(level=levels_to_keep).sum())
            year_df = pd.concat(sector_df_list, keys=keys,names=name)
            df_list.append(year_df)
        self.sector_df_list  = sector_df_list
        self.df_list = df_list
        keys = self.years
        name = ['year']
        df = pd.concat(df_list,keys=keys,names=name)
        df.columns = ['value']
#       levels = [x for x in ['supply_node',cfg.primary_geography +'_supply', 'ghg',cfg.primary_geography,'final_energy'] if x in df.index.names]
        return df


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
        for year in self.years:
            sector_df_list = []
            keys = self.demand_sectors
            name = ['sector']
            for sector in self.demand_sectors:   
               df = copy.deepcopy(embodied_dict[year][sector]).loc[:,idx[:,supply_nodes]]
               util.replace_column_name(df,'supply_node_export',  'supply_node')
               util.replace_index_name(df, cfg.primary_geography + "_supply", cfg.primary_geography)
               stack_levels =[cfg.primary_geography, "supply_node_export"]
               df = df.stack(stack_levels).to_frame()
               levels_to_keep = [x for x in df.index.names if x in cfg.output_combined_levels+stack_levels]
               df = df.groupby(level=list(set(levels_to_keep+['supply_node']))).sum()
               df = df.groupby(level='supply_node').filter(lambda x: x.sum()!=0)
               sector_df_list.append(df)     
            year_df = pd.concat(sector_df_list, keys=keys,names=name)
            df_list.append(year_df)
        keys = self.years
        name = ['year']
        df = pd.concat(df_list,keys=keys,names=name)
        df.columns = ['value']
        return df

    def calculate_export_result(self, export_result_name, io_dict):
        export_map_df = self.map_embodied_to_export(io_dict)
        export_df = self.io_export_df.stack().to_frame()
        export_df = export_df.groupby(level=['supply_node']).filter(lambda x: x.sum()!=0)
        if cfg.primary_geography+"_supply" in cfg.output_combined_levels:
            export_map_df = export_map_df.groupby(level=['supply_node',cfg.primary_geography+"_supply"]).filter(lambda x: x.sum()>0)
        else:
            export_map_df = export_map_df.groupby(level=['supply_node']).filter(lambda x: x.sum()!=0)
        if export_map_df.empty is False and export_df.empty is False:
            util.replace_index_name(export_df, 'year')
            util.replace_index_name(export_df, 'sector', 'demand_sector')
            util.replace_index_name(export_df,'supply_node_export','supply_node')
            util.replace_column(export_df, 'value') 
            geo_df_list = []
            for geography in cfg.geographies:
                export_map_df_indexer = util.level_specific_indexer(export_map_df,[cfg.primary_geography],[geography])
                export_df_indexer = util.level_specific_indexer(export_df,[cfg.primary_geography],[geography])
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
               col_indexer = util.level_specific_indexer(io_adjusted,'supply_node',node.id, axis=1)
               io_adjusted.loc[:,col_indexer] = 0
        return io_adjusted


                        
    def calculate_coefficients(self, year, loop):
        """Loops through all supply nodes and calculates active coefficients
        Args:
            year (int) = year of analysis 
            loop (int or str) = loop identifier
        """
        for node_id in self.blend_nodes:
            node = self.nodes[node_id]
            node.update_residual(year)
        for node in self.nodes.values():
            if  node.id!=self.thermal_dispatch_node_id:
                node.calculate_active_coefficients(year, loop)
            elif year == int(cfg.cfgfile.get('case','current_year')) and node.id == self.thermal_dispatch_node_id:
                #thermal dispatch node is updated through the dispatch. In the first year we assume equal shares
                #TODO make capacity weighted for better approximation
                node.calculate_active_coefficients(year, loop)
                node.active_coefficients_total[node.active_coefficients_total>0] = 1E-7
                node.active_coefficients_total = node.active_coefficients_total.groupby(level=['demand_sector',cfg.primary_geography]).transform(lambda x: x/x.sum())
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
                elif hasattr(node,'id'):
                    for dict_node in self.nodes.values():
                        if hasattr(dict_node, 'pass_through_dict'):
                            if node.id in dict_node.pass_through_dict.keys():
                                del dict_node.pass_through_dict[node.id]
            for node in self.nodes.values(): 
                if hasattr(node,'pass_through_dict') and node.pass_through_dict == {}:
                    for dict_node in self.nodes.values():
                        if hasattr(dict_node, 'pass_through_dict'):
                            if node.id in dict_node.pass_through_dict.keys():
                                del dict_node.pass_through_dict[node.id]      
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
        if len(cfg.geographies) > 1:
            for node in self.nodes.values():
                if node.id not in self.blend_nodes:
                    #Checks whether a node has information (stocks or potential) that means that demand is not a good proxy for location of supply
                    node.calculate_internal_trades(year, loop)
            for node in self.nodes.values():
                #loops through all nodes checking for excess supply from nodes that are not curtailable, flexible, or exportable
                trade_sub = node.id
                if node.id not in self.blend_nodes:
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
            if node.id not in self.blend_nodes:
                #checks the node for an adjustment factor due to excess throughput requested from a constraiend node
                #Ex. if biomass throughput exceeeds biomass potential by 2x, the adjustment factor passed would be .5
                node.calculate_potential_constraints(year) 
                #Checks whether a constraint was violated
                if node.constraint_violation:
                    #enters a loop to feed that constraint forward in the supply node
                    self.feed_constraints(year, node.id, node.active_constraint_df)
                      
      
      
        
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
           oversupply_factor = node.calculate_oversupply(year,loop) if hasattr(node,'calculate_oversupply') else None 
           if oversupply_factor is not None: 
               if node.is_exportable:
                   #if the node is exportable, excess supply is added to the node's exports
                   excess_supply = DfOper.subt([DfOper.mult([node.active_supply, oversupply_factor]), node.active_supply])
                   node.export.active_values = DfOper.add([node.export.active_values, excess_supply])
               elif node.id in self.nodes[self.thermal_dispatch_node_id].nodes:
                   #excess supply is not possible for thermally dispatched nodes
                   pass
               elif node.id in self.blend_nodes:
                   pass
               elif node.is_curtailable: 
                   #if the node's production is curtailable, then the energy production is adjusted down in the node
                    node.adjust_energy(oversupply_factor,year)
               else:
                   #otherwise, the model enters a loop to feed that constraint forward in the supply node until it can be reconciled at a blend node or exported
                   self.feed_oversupply(year, node.id, oversupply_factor)
                        
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
                self.feed_physical_emissions(year, node.id, node.active_physical_emissions_rate)


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
                  if output_node.id in self.blend_nodes:
                     logging.info("      constrained node %s being reconciled in blend node %s" %(self.nodes[constrained_node].name, output_node.name))
                     indexer = util.level_specific_indexer(output_node.values,'supply_node', constrained_node)
                     try:
                         output_node.values.loc[indexer,year] =  DfOper.mult([output_node.values.loc[indexer, year].to_frame(),constraint_adjustment]).values
                         #flag for the blend node that it has been reconciled and needs to recalculate residual
                         output_node.reconciled = True
                     except:
                         pdb.set_trace()
                     #flag that anything in the supply loop has been reconciled, and so the loop needs to be resolved
                     self.reconciled = True
                  else:
                     #if the output node has the constrained sub as an input, and it is not a blend node, it becomes the constrained sub
                      #in the loop in order to feed the adjustment factor forward to dependent nodes until it terminates at a blend node
                     self.feed_constraints(year, constrained_node=output_node.id, constraint_adjustment=constraint_adjustment)
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
                  if output_node.id in self.blend_nodes and output_node.tradable_geography or isinstance(output_node,ImportNode) or output_node.internal_trades == 'stop':
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
                     self.feed_internal_trades(year, internal_trade_node=output_node.id, internal_trade_adjustment=output_node.active_internal_trade_df)
                  elif output_node.internal_trades == 'feed':
                     #if the output node is set to feed the trades forward, it becomes the trade node while using the original trade node's adjustment factors in order to perpetuate the downstream impacts
                     self.feed_internal_trades(year, internal_trade_node=output_node.id, internal_trade_adjustment=internal_trade_adjustment)
                 
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
                  if output_node.id in self.blend_nodes:
                     # if the output node is a blend node, this is where oversupply is reconciled
#                     print oversupply_node, output_node.id, oversupply_factor
                     indexer = util.level_specific_indexer(output_node.values,'supply_node', oversupply_node)
                     output_node.values.loc[indexer, year] = DfOper.mult([output_node.values.loc[indexer, year].to_frame(),oversupply_factor]).values
                     output_node.reconciled = True
                     self.reconciled=True
                  else:
                      if output_node.is_curtailable or  output_node.id in self.thermal_nodes:
                          #if the output node is curtailable, then the excess supply feed-loop ends and the excess is curtailed within this node. If the node is flexible, excess supply
                          #will be reconciled in the dispatch loop
                          pass
                      elif output_node.is_exportable:
                          #if the output node is exportable, then excess supply is added to the export demand in this node
                          excess_supply = DfOper.subt([DfOper.mult([output_node.active_supply, oversupply_factor]), output_node.active_supply])
                          output_node.export.active_values = DfOper.add([output_node.export.active_values, excess_supply]) 
                      else: 
                          #otherwise, continue the feed-loop until the excess supply can be reconciled
                          self.feed_oversupply(year, oversupply_node = output_node.id, oversupply_factor=oversupply_factor)
 

    def update_io_df(self,year,loop):
        """Updates the io dictionary with the active coefficients of all nodes
        Args:
            year (int) = year of analysis 
        """
        for geography in cfg.geographies:
            #fix for zero energy demand
            if util.df_slice(self.io_total_active_demand_df,geography,cfg.primary_geography).sum().sum()==0:
                for col_node in self.nodes.values():
                    if col_node.supply_type == 'Blend':
                        if col_node.active_coefficients_total is None:
                            continue
                        else:
                            col_indexer = util.level_specific_indexer(col_node.active_coefficients_total,cfg.primary_geography,geography,axis=1)
                            normalized = col_node.active_coefficients_total.loc[:,col_indexer].groupby(level=['demand_sector']).transform(lambda x: x/x.sum())
                            normalized = normalized.replace([np.nan,np.inf],1E-7)
                            col_node.active_coefficients_total.loc[:,col_indexer] = normalized
                            
        for col_node in self.nodes.values():
            if loop == 1 and col_node.id not in self.blend_nodes:
                continue
            elif col_node.active_coefficients_total is None:
               continue
            else:
               for sector in self.demand_sectors:
                    levels = ['supply_node' ]
                    col_indexer = util.level_specific_indexer(self.io_dict[year][sector], levels=levels, elements=[col_node.id])
                    row_nodes = list(map(int,col_node.active_coefficients_total.index.levels[util.position_in_index(col_node.active_coefficients_total,'supply_node')]))
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
                      if isinstance(output_node,ImportNode) and output_node.emissions.data is True:
                         #if the node is an import node, and the emissions intensity is not incremental, the loop stops because the input emissions intensity
                         #overrides the passed through emissions intensity
                          pass
                      else:
                         indexer = util.level_specific_indexer(output_node.active_emissions_coefficients,['supply_node','efficiency_type'], [emissions_node,2])   
                         additional_emissions_rate = output_node.active_emissions_coefficients.loc[indexer,:].values * active_physical_emissions_rate.values
                         output_node.active_pass_through_df += additional_emissions_rate  
#                         output_node.active_pass_through_df.columns = output_node.active_pass_through_df.columns.droplevel(-1)
                         if all(output_node.pass_through_dict.values()):
                             emissions_rate = output_node.active_pass_through_df.groupby(level=['ghg'],axis=0).sum()
                             emissions_rate= emissions_rate.stack([cfg.primary_geography, 'demand_sector']).to_frame()
                             emissions_rate = emissions_rate.reorder_levels([cfg.primary_geography, 'demand_sector', 'ghg'])
                             emissions_rate.sort(inplace=True, axis=0)                                                          
                             keys = [self.demand_sectors,cfg.geographies]
                             names = ['demand_sector', cfg.primary_geography]
                             for key, name in zip(keys, names):
                                 emissions_rate = pd.concat([emissions_rate]*len(key),axis=1,keys=key,names=[name])
                             emissions_rate.sort(inplace=True, axis=0)   
                             emissions_rate.columns = emissions_rate.columns.droplevel(-1)
                             self.feed_physical_emissions(year,output_node.id,emissions_rate)
                             
        
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
        index = pd.MultiIndex.from_product([cfg.geographies, self.all_nodes
                                                                ], names=[cfg.primary_geography,'supply_node'])
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
            self.inverse_dict['energy'][year][sector] = pd.DataFrame(temp, index=index, columns=index)
            temp = solve_IO(active_cost_io.values)
            temp[np.nonzero(active_cost_io.values.sum(axis=1) + self.active_demand.values.flatten()==0)[0]] = 0
            self.inverse_dict['cost'][year][sector] = pd.DataFrame(temp, index=index, columns=index)
            idx = pd.IndexSlice
            self.inverse_dict['energy'][year][sector].loc[idx[:,self.non_storage_nodes],:] = self.inverse_dict['energy'][year][sector].loc[idx[:,self.non_storage_nodes],:]
            self.inverse_dict['cost'][year][sector].loc[idx[:,self.non_storage_nodes],:] = self.inverse_dict['cost'][year][sector].loc[idx[:,self.non_storage_nodes],:] 
        for node in self.nodes.values():
            indexer = util.level_specific_indexer(self.io_supply_df,levels=['supply_node'], elements = [node.id])
            node.active_supply = self.io_supply_df.loc[indexer,year].groupby(level=[cfg.primary_geography, 'demand_sector']).sum().to_frame()
                    
    
    def add_initial_demand_dfs(self, year):
        for node in self.nodes.values():
            node.internal_demand = copy.deepcopy(self.empty_output_df)
            node.export_demand = copy.deepcopy(self.empty_output_df)
            node.internal_demand = copy.deepcopy(self.empty_output_df)

    
    def pass_initial_demand_to_nodes(self, year):
        for node in self.nodes.values():
            indexer = util.level_specific_indexer(self.io_total_active_demand_df,levels=['supply_node'], elements = [node.id])
            node.active_demand = self.io_total_active_demand_df.loc[indexer,:] 
          
    def add_empty_output_df(self):           
        """adds an empty df to node instances"""
        index =  pd.MultiIndex.from_product([cfg.geo.geographies[cfg.primary_geography],
                                                            self.demand_sectors], names=[cfg.primary_geography, 'demand_sector'])
        self.empty_output_df = util.empty_df(index = index, columns = self.years,fill_value = 1E-25)      
        
    def add_io_df(self,attribute_names):
        #TODO only need to run years with a complete demand data set. Check demand dataframe. 
        index =  pd.MultiIndex.from_product([cfg.geo.geographies[cfg.primary_geography],self.demand_sectors, self.all_nodes
                                                                ], names=[cfg.primary_geography,
                                                                 'demand_sector','supply_node'])                                                            
        for attribute_name in util.put_in_list(attribute_names):
            setattr(self, attribute_name, util.empty_df(index = index, columns = self.years))
            
            
    def add_io_embodied_emissions_df(self):
        #TODO only need to run years with a complete demand data set. Check demand dataframe. 
        index =  pd.MultiIndex.from_product([cfg.geo.geographies[cfg.primary_geography],self.demand_sectors, self.all_nodes,self.ghgs,
                                                                ], names=[cfg.primary_geography,
                                                                 'demand_sector', 'supply_node','ghg'])                                                            
        
        setattr(self, 'io_embodied_emissions_df', util.empty_df(index = index, columns = self.years))
            
    def create_inverse_dict(self):
        index = pd.MultiIndex.from_product([cfg.geo.geographies[cfg.primary_geography], self.all_nodes
                                                                ], names=[cfg.primary_geography,'supply_node'])
        df = util.empty_df(index = index, columns = index)
        self.inverse_dict = util.recursivedict()   
        for key in ['energy', 'cost']:
            for year in self.years:
                for sector in util.ensure_iterable_and_not_string(self.demand_sectors):
                    self.inverse_dict[key][year][sector]= df
            
    def create_embodied_cost_and_energy_demand_link(self):
        map_dict = self.map_dict
        keys = sorted(map_dict.items(), key=operator.itemgetter(1))
        keys = [x[0] for x in keys]
        #sorts final energy in the same order as the supply node dataframes
        index = pd.MultiIndex.from_product([cfg.geographies, self.all_nodes], names=[cfg.primary_geography+"_supply",'supply_node'])
        columns = pd.MultiIndex.from_product([cfg.geographies,keys], names=[cfg.primary_geography,'final_energy'])
        self.embodied_cost_link_dict = util.recursivedict()
        self.embodied_energy_link_dict = util.recursivedict()
        for year in self.years:
            for sector in self.demand_sectors:
                self.embodied_cost_link_dict[year][sector] = util.empty_df(index = index, columns = columns)
                self.embodied_energy_link_dict[year][sector] = util.empty_df(index = index, columns = columns)
        
    
    def create_embodied_emissions_demand_link(self):
        map_dict = self.map_dict
        #sorts final energy in the same order as the supply node dataframes
        keys = sorted(map_dict.items(), key=operator.itemgetter(1))
        keys = [x[0] for x in keys]
        index = pd.MultiIndex.from_product([cfg.geographies, self.all_nodes, self.ghgs], names=[cfg.primary_geography+"_supply",'supply_node','ghg'])
        columns = pd.MultiIndex.from_product([cfg.geographies,keys], names=[cfg.primary_geography,'final_energy'])
        self.embodied_emissions_link_dict = util.recursivedict()
        for year in self.years:
            for sector in self.demand_sectors:
                self.embodied_emissions_link_dict[year][sector] = util.empty_df(index = index, columns = columns)
                
                
    def map_demand_to_io(self):
        """maps final energy demand ids to node nodes for IO table demand calculation"""    
        #loops through all final energy types in demand df and adds 
        map_dict = self.map_dict
        self.demand_df = self.demand_object.energy_demand.unstack(level='year')
        # round here to get rid of really small numbers
        self.demand_df = self.demand_df.round()
        self.demand_df.columns = self.demand_df.columns.droplevel()
        for demand_sector, geography, final_energy in self.demand_df.groupby(level = self.demand_df.index.names).groups:
            supply_indexer = util.level_specific_indexer(self.io_demand_df, levels=[cfg.primary_geography, 'demand_sector','supply_node'],elements=[geography, demand_sector, map_dict[final_energy]])
            demand_indexer =  util.level_specific_indexer(self.demand_df, levels = [ 'sector', cfg.primary_geography, 'final_energy'],elements=[demand_sector, geography, final_energy])
            self.io_demand_df.loc[supply_indexer, self.years] = self.demand_df.loc[demand_indexer, self.years].values

                
    def map_export_to_io(self,year, loop):
        """maps specified export nodes for IO table total demand calculation"""    
        for node in self.nodes.values():
            supply_indexer = util.level_specific_indexer(self.io_export_df, 'supply_node', node.id)  
            if loop == 'initial' or loop==1:
                node.export.allocate(node.active_supply, self.demand_sectors, self.years, year, loop)
            self.io_export_df.loc[supply_indexer, year] = node.export.active_values.sort().values

            

class Node(DataMapFunctions):
    def __init__(self, id, supply_type, scenario):
        self.id = id
        self.supply_type = supply_type
        self.scenario = scenario
        for col, att in util.object_att_from_table('SupplyNodes', id):
            setattr(self, col, att)
        self.active_supply= None
        self.reconciled = False
        #all nodes have emissions subclass
        self.emissions = SupplyEmissions(self.id, self.scenario)
        self.shape = self.determine_shape()
        self.workingdir = cfg.workingdir
        self.cfgfile_name = cfg.cfgfile_name
        self.log_name = cfg.log_name

    def determine_shape(self):
        if self.shape_id is not None:
            return shape.shapes.data[self.shape_id]

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
            self.cost.calculate(self.conversion, self.resource_unit)

    def add_total_stock_measures(self, scenario):
        self.total_stocks = {}
        measure_ids = scenario.get_measures('SupplyStockMeasures', self.id)
        for total_stock in measure_ids:
            self.total_stocks[total_stock] = SupplySpecifiedStock(id=total_stock,
                                                                    sql_id_table='SupplyStockMeasures',
                                                                    sql_data_table='SupplyStockMeasuresData',
                                                                    scenario=scenario)
        
    def set_cost_dataframes(self):
        index = pd.MultiIndex.from_product([cfg.geo.geographies[cfg.primary_geography], self.demand_sectors], names=[cfg.primary_geography, 'demand_sector'])
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
        df = util.remove_df_levels(self.stock.values, levels_to_eliminate).sort()
        # stock starts with vintage as an index and year as a column, but we need to stack it for export
        df = df.stack().to_frame()
        util.replace_index_name(df, 'year')
        stock_unit = cfg.calculation_energy_unit + "/" + cfg.cfgfile.get('case','time_step')
        df.columns =  [stock_unit.upper()]
        return df
        
    def format_output_capacity_utilization(self, override_levels_to_keep=None):
        if not hasattr(self, 'capacity_utilization'):
            return None
#        levels_to_keep = cfg.output_supply_levels if override_levels_to_keep is None else override_levels_to_keep
#        levels_to_eliminate = [l for l in self.capacity_utilization.index.names if l not in levels_to_keep]
#        df = util.remove_df_levels(self.capacity_utilization, levels_to_eliminate).sort()
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
        df = util.remove_df_levels(df, levels_to_eliminate).sort()
        cost_unit = cfg.cfgfile.get('case','currency_year_id') + " " + cfg.cfgfile.get('case','currency_name')
        df.columns = [cost_unit.upper()]    
        return df
    
    def format_output_levelized_costs(self, override_levels_to_keep=None):
        if not hasattr(self, 'final_levelized_costs'):
            return None
        levels_to_keep = cfg.output_supply_levels if override_levels_to_keep is None else override_levels_to_keep
        levels_to_eliminate = [l for l in self.final_levelized_costs.index.names if l not in levels_to_keep]
        df = util.remove_df_levels(self.final_levelized_costs, levels_to_eliminate).sort()
        # stock starts with vintage as an index and year as a column, but we need to stack it for export
        df = df.stack().to_frame()
        util.replace_index_name(df, 'year')
        cost_unit = cfg.cfgfile.get('case','currency_year_id') + " " + cfg.cfgfile.get('case','currency_name')
        df.columns = [cost_unit.upper()] 
        return df

    def add_conversion(self):
        """
        adds a dataframe used to convert input values that are not in energy terms, to energy terms
        ex. Biomass input as 'tons' must be converted to energy units using a conversion factor data table
        """
        energy_unit = cfg.calculation_energy_unit
        potential_unit = util.sql_read_table('SupplyPotential', 'unit', supply_node_id=self.id)
            # check to see if unit is in energy terms, if so, no conversion necessary
        if potential_unit is not None:
            if cfg.ureg.Quantity(potential_unit).dimensionality == cfg.ureg.Quantity(energy_unit).dimensionality:
                conversion = None
                resource_unit = None
            else:
                # if the unit is not in energy terms, create a conversion class to convert to energy units
                conversion = SupplyEnergyConversion(self.id, potential_unit)
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
            if self.shape_id is None:
                index = pd.MultiIndex.from_product([cfg.geo.geographies[cfg.primary_geography],[2],shape.shapes.active_dates_index], names=[cfg.primary_geography,'timeshift_type','weather_datetime'])
                energy_shape = shape.shapes.make_flat_load_shape(index)
            else:
                energy_shape = self.shape.values
        elif 'demand_sector' in self.stock.values_energy:
            values_energy = util.remove_df_levels(DfOper.mult([self.stock.values_energy[year],dispatch_feeder_allocation]),'demand_sector')                    
        else:
            values_energy = self.stock.values_energy[year]
        if self.shape_id is None and (hasattr(self, 'technologies') and  np.all([tech.shape_id is None for tech in self.technologies.values()]) or not hasattr(self,'technologies')):
            index = pd.MultiIndex.from_product([cfg.geo.geographies[cfg.primary_geography],[2],shape.shapes.active_dates_index], names=[cfg.primary_geography,'timeshift_type','weather_datetime'])
            energy_shape = shape.shapes.make_flat_load_shape(index)
        # we don't have technologies or none of the technologies have specific shapes
        elif not hasattr(self, 'technologies') or np.all([tech.shape_id is None for tech in self.technologies.values()]):
            if 'resource_bin' in self.shape.values.index.names and 'resource_bin' not in self.stock.values.index.names:
                raise ValueError('Shape for %s has resource bins but the stock in this supply node does not have resource bins as a level' %self.name) 
            elif 'resource_bin' in self.stock.values.index.names and 'resource_bin' not in self.shape.values.index.names:
                energy_shape = self.shape.values
            elif 'resource_bin' in self.stock.values.index.names and 'resource_bin' in self.shape.values.index.names:

                energy_slice = util.remove_df_levels(values_energy, ['vintage', 'supply_technology']).to_frame()
                energy_slice.columns = ['value']
                energy_shape = util.DfOper.mult([energy_slice, self.shape.values])
                energy_shape = util.DfOper.divi([util.remove_df_levels(energy_shape,'resource_bin'), util.remove_df_levels(energy_slice, 'resource_bin')])
                energy_shape = energy_shape.replace(np.nan,0)
            else:
                energy_shape = self.shape.values
        else:
            energy_slice = util.remove_df_levels(values_energy, 'vintage').to_frame()
            energy_slice.columns = ['value']
            techs_with_default_shape = [tech_id for tech_id, tech in self.technologies.items() if tech.shape_id is None]
            techs_with_own_shape = [tech_id for tech_id, tech in self.technologies.items() if tech.shape_id is not None]           
            if techs_with_default_shape:
                energy_slice_default_shape = util.df_slice(energy_slice, techs_with_default_shape, 'supply_technology')
                energy_slice_default_shape = util.remove_df_levels(energy_slice_default_shape, 'supply_technology')
                default_shape_portion = util.DfOper.mult([energy_slice_default_shape, self.shape.values])
                default_shape_portion = util.remove_df_levels(default_shape_portion, ['resource_bin'])
            if techs_with_own_shape:
                energy_slice_own_shape = util.df_slice(energy_slice, techs_with_own_shape, 'supply_technology')
                tech_shapes = pd.concat([self.technologies[tech_id].shape.values for tech_id in techs_with_own_shape],keys=techs_with_own_shape,names=['supply_technology'])
                tech_shape_portion = util.DfOper.mult([energy_slice_own_shape, tech_shapes])
                tech_shape_portion = util.remove_df_levels(tech_shape_portion, ['supply_technology', 'resource_bin'])
            df = util.DfOper.add([default_shape_portion if techs_with_default_shape else None,
                                  tech_shape_portion if techs_with_own_shape else None],
                                  expandable=False, collapsible=False)
            energy_shape = DfOper.divi([df, util.remove_df_levels(energy_slice,['vintage','supply_technology','resource_bin'])])
        try:
            if 'dispatch_constraint' in energy_shape.index.names:
                energy_shape = util.df_slice(energy_shape,1,'dispatch_constraint')
        except:
                pdb.set_trace()

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
        
        if self.shape_id is None or not hasattr(self, 'stock'):
            energy_shape = None
            p_max_shape = None
            p_min_shape = None       
        elif not hasattr(self, 'technologies') or np.all([tech.shape_id is None for tech in self.technologies.values()]):
            if 'dispatch_constraint' not in self.shape.values.index.names:
                if 'resource_bin' in self.shape.values.index.names and 'resource_bin' not in self.stock.values.index.names:
                    raise ValueError('Shape for %s has resource bins but the stock in this supply node does not have resource bins as a level' %self.name)
                elif 'resource_bin' in self.stock.values.index.names and 'resource_bin' not in self.shape.values.index.names:
                    energy_shape = self.shape.values
                elif 'resource_bin' not in self.stock.values.index.names:
                    energy_shape = self.shape.values
                elif 'resource_bin' in self.stock.values.index.names and 'resource_bin' in self.shape.values.index.names:
                    energy_slice = util.remove_df_levels(stock_values_energy[year], ['vintage', 'supply_technology']).to_frame()
                    energy_slice.columns = ['value']
                    energy_shape = util.DfOper.mult([energy_slice, self.shape.values])
                    energy_shape = util.remove_df_levels(energy_shape, 'resource_bin')
                    energy_shape = DfOper.div([energy_shape, util.remove_df_levels(energy_slice,'resource_bin')])
                p_min_shape = None
                p_max_shape = None
            else:
                energy_shape, p_min_shape, p_max_shape,  = self.calculate_disp_constraints_shape(year, stock_values, stock_values_energy)
        else:
            if 'dispatch_constraint' not in self.shape.values.index.names: 
                energy_slice = util.remove_df_levels(self.stock.values_energy[year], 'vintage').to_frame()
                energy_slice.columns = ['value']
                techs_with_default_shape = [tech_id for tech_id, tech in self.technologies.items() if tech.shape_id is None or 'dispatch_constraint' in shape.shapes.data[tech.shape_id].df_index_names]
                techs_with_own_shape = [tech_id for tech_id, tech in self.technologies.items() if tech.shape_id is not None and 'dispatch_constraint' not in shape.shapes.data[tech.shape_id].df_index_names]
                if techs_with_default_shape:
                    energy_slice_default_shape = util.df_slice(energy_slice, techs_with_default_shape, 'supply_technology')
                    energy_slice_default_shape = util.remove_df_levels(energy_slice_default_shape, 'supply_technology')
                    default_shape_portion = util.DfOper.mult([energy_slice_default_shape, self.shape.values])
                    default_shape_portion = util.remove_df_levels(default_shape_portion, 'resource_bin')
                if techs_with_own_shape:
                    energy_slice_own_shape = util.df_slice(energy_slice, techs_with_own_shape, 'supply_technology')
                    tech_shapes = pd.concat([self.technologies[tech_id].shape.values for tech_id in techs_with_own_shape])
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
        if 'resource_bin' in self.shape.values.index.names and 'resource_bin' not in self.stock.values.index.names:
            raise ValueError('Shape for %s has resource bins but the stock in this supply node does not have resource bins as a level' %self.name)
        elif 'resource_bin' in self.stock.values.index.names and 'resource_bin' not in self.shape.values.index.names:
            energy_shape = util.df_slice(self.shape.values,1,'dispatch_constraint')
            p_min_shape = util.df_slice(self.shape.values,2,'dispatch_constraint')
            p_max_shape = util.df_slice(self.shape.values,3,'dispatch_constraint')
        elif 'resource_bin' in self.stock.values.index.names and 'resource_bin' in self.shape.values.index.names:
            energy_slice = util.remove_df_levels(stock_values_energy, ['vintage', 'supply_technology']).to_frame()
            energy_slice.columns = ['value']
            energy_shape = util.DfOper.mult([energy_slice, util.df_slice(self.shape.values,1,'dispatch_constraint')])
            energy_shape = util.remove_df_levels(energy_shape, 'resource_bin')
            energy_shape = DfOper.div([energy_shape, util.remove_df_levels(energy_slice,'resource_bin')])
            capacity_slice = util.remove_df_levels(stock_values, ['vintage', 'supply_technology']).to_frame()
            capacity_slice.columns = ['value']
            p_min_shape = util.DfOper.mult([capacity_slice, util.df_slice(self.shape.values,2,'dispatch_constraint')])
            p_min_shape = util.remove_df_levels(p_min_shape, 'resource_bin')
            p_min_shape = DfOper.div([p_min_shape, util.remove_df_levels(capacity_slice,'resource_bin')])
            p_max_shape = util.DfOper.mult([capacity_slice, util.df_slice(self.shape.values,3,'dispatch_constraint')])
            p_max_shape = util.remove_df_levels(p_max_shape, 'resource_bin')
            p_max_shape = DfOper.div([p_max_shape, util.remove_df_levels(capacity_slice,'resource_bin')])
        else:
            energy_shape = util.df_slice(self.shape.values,1,'dispatch_constraint')
            p_min_shape = util.df_slice(self.shape.values,2,'dispatch_constraint')
            p_max_shape = util.df_slice(self.shape.values,3,'dispatch_constraint')
        return energy_shape, p_min_shape, p_max_shape

    def calculate_active_coefficients(self, year, loop):
        if year == int(cfg.cfgfile.get('case','current_year'))and loop == 'initial' :
            #in the first loop, we take the active coefficients for the year
            throughput = self.active_demand
        else:
            throughput = self.active_supply
        if hasattr(self,'potential') and self.potential.data is True:
            self.potential.remap_to_potential_and_normalize(throughput, year, self.tradable_geography)
            if self.coefficients.data is True:
                filter_geo_potential_normal = util.remove_df_elements(self.potential.active_supply_curve_normal, [x for x in cfg.geo.geographies_unfiltered[cfg.primary_geography]  if x not in cfg.geographies],cfg.primary_geography)
                filter_geo_potential_normal = filter_geo_potential_normal.reset_index().set_index(filter_geo_potential_normal.index.names)
                self.active_coefficients = util.remove_df_levels(util.DfOper.mult([self.coefficients.values.loc[:,year].to_frame(),
                                                    filter_geo_potential_normal]),'resource_bin')
            else:
                self.active_coefficients = None     
        elif self.coefficients.data is True: 
            self.active_coefficients =  self.coefficients.values.groupby(level=[cfg.primary_geography,  'demand_sector', 'efficiency_type','supply_node']).sum().loc[:,year].to_frame()
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
            self.active_emissions_coefficients = self.active_emissions_coefficients.reorder_levels([cfg.primary_geography,'demand_sector', 'supply_node', 'efficiency_type', 'ghg'])
            self.active_emissions_coefficients.sort(inplace=True)
        else:
            self.active_coefficients_total = None
            self.active_emissions_coefficients = None

    def add_column_index(self, data):
         names = ['demand_sector', cfg.primary_geography]
         keys = [self.demand_sectors, cfg.geo.geographies[cfg.primary_geography]]
         data  = copy.deepcopy(data)
         for key,name in zip(keys,names):
             data  = pd.concat([data]*len(key), axis=1, keys=key, names=[name])
         data.columns = data.columns.droplevel(-1)
         return data

    def add_export_measures(self, scenario):
        """
        add all export measures from the scenario to a dictionary
        """
        self.export_measures = []
        ids = scenario.get_measures('SupplyExportMeasures', self.id)
        if len(ids) > 1:
            raise ValueError('model does not currently support multiple active export measures from a single supply node. Turn off an export measure in supply node %s' %self.name)
        for id in ids:
            self.export_measures.append(id)
            self.add_export_measure(id)
        
    def add_export_measure(self, id, **kwargs):
        """Adds measure instances to node"""
        self.export_measure = id
#        if id in self.export_measures:
#            return        
        #self.export_measures.append(id)
        
    def add_exports(self):
        if len(self.export_measures):
            self.export = Export(self.id,measure_id=self.export_measure)
        else:
            self.export = Export(self.id)
                
    def convert_stock(self, stock_name='stock', attr='total'):
        model_energy_unit = cfg.calculation_energy_unit
        model_time_step = cfg.cfgfile.get('case', 'time_step')
        stock = getattr(self,stock_name)
        if stock.time_unit is not None:
            # if a stock has a time_unit, then the unit is energy and must be converted to capacity
            setattr(stock, attr, util.unit_convert(getattr(stock, attr), unit_from_num=stock.capacity_or_energy_unit, unit_from_den=stock.time_unit, 
                                             unit_to_num=model_energy_unit, unit_to_den=model_time_step))
        else:
            # if a stock is a capacity unit, the model must convert the unit type to an energy unit for conversion ()
            try:
                setattr(stock, attr, util.unit_convert(getattr(stock, attr), unit_from_num=cfg.ureg.Quantity(stock.capacity_or_energy_unit)*cfg.ureg.Quantity(model_time_step), unit_from_den=model_time_step,
                                             unit_to_num=model_energy_unit, unit_to_den=model_time_step))
            except:
                pdb.set_trace()

    def calculate_potential_constraints(self, year):
        """calculates the exceedance factor of a node if the node active supply exceeds the potential in the node. This adjustment factor
        is passed to other nodes in the reconcile step"""
        if hasattr(self,'potential') and self.potential.data is True and self.enforce_potential_constraint == True:
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
            geography_map_key = self.geography_map_key if hasattr(self, 'geography_map_key') else cfg.cfgfile.get('case','default_geography_map_key')       
            if self.tradable_geography != cfg.primary_geography:
                map_df = cfg.geo.map_df(self.tradable_geography, cfg.primary_geography, normalize_as='intensity', map_key=geography_map_key, eliminate_zeros=False)
                self.potential_exceedance = util.remove_df_levels(util.DfOper.mult([self.potential_exceedance,map_df]), self.tradable_geography)
            self.active_constraint_df = util.remove_df_elements(self.potential_exceedance, [x for x in cfg.geo.geographies_unfiltered[cfg.primary_geography]  if x not in cfg.geographies],cfg.primary_geography)
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
        if hasattr(self,'potential') and self.potential.data is True:
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
            geography_map_key = self.geography_map_key if hasattr(self, 'geography_map_key') else cfg.cfgfile.get('case','default_geography_map_key')       
            if self.tradable_geography != cfg.primary_geography:
                map_df = cfg.geo.map_df(self.tradable_geography, cfg.primary_geography, normalize_as='intensity', map_key=geography_map_key, eliminate_zeros=False)
                self.potential_exceedance = util.remove_df_levels(util.DfOper.mult([self.potential_exceedance,map_df]), self.tradable_geography)
            self.active_constraint_df = util.remove_df_elements(self.potential_exceedance, [x for x in cfg.geo.geographies_unfiltered[cfg.primary_geography]  if x not in cfg.geographies],cfg.primary_geography)
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
        if self.tradable_geography!= cfg.primary_geography and len(cfg.geographies)>1 :
            if hasattr(self,'potential') and self.potential.data is True or (hasattr(self,'stock') and self.stock.data is True):
                #tradable supply is mapping of active supply to a tradable geography
                try:
                    self.geo_step1 = cfg.geo.map_df(cfg.primary_geography,self.tradable_geography, normalize_as='total', eliminate_zeros=False)
                except:
                    logging.error('self.tradable_geography = {}, primary_geography = {}, id = {}, name = {}'.format(self.tradable_geography, cfg.primary_geography, self.id, self.name))
                    raise

                if hasattr(self,'potential') and self.potential.data is True:
                     df = util.remove_df_elements(self.potential.active_supply_curve, [x for x in cfg.geo.geographies_unfiltered[cfg.primary_geography]  if x not in cfg.geographies],cfg.primary_geography)
                     self.potential_geo = util.DfOper.mult([util.remove_df_levels(df,
                                                                                  [x for x in self.potential.active_supply_curve.index.names if x not in [cfg.primary_geography,'demand_sector']]),
                                                                                    cfg.geo.map_df(cfg.primary_geography,self.tradable_geography,normalize_as='total')])
                     util.replace_index_name(self.potential_geo,cfg.primary_geography + "from", cfg.primary_geography)
                     #if a node has potential, this becomes the basis for remapping
                if hasattr(self,'stock') and hasattr(self.stock,'act_total_energy'):
                    total_stock = util.remove_df_levels(self.stock.act_total_energy, [x for x in self.stock.act_total_energy.index.names if x not in [cfg.primary_geography,'demand_sector']])
                    self.stock_energy_geo = util.DfOper.mult([total_stock,cfg.geo.map_df(cfg.primary_geography,self.tradable_geography, normalize_as='total', eliminate_zeros=False)])
                    util.replace_index_name(self.stock_energy_geo,cfg.primary_geography+ "from", cfg.primary_geography)
                elif  hasattr(self,'stock') and hasattr(self.stock,'act_total'):
                    total_stock = util.remove_df_levels(self.stock.act_total, [x for x in self.stock.act_total.index.names if x not in [cfg.primary_geography,'demand_sector']])
                    self.stock_capacity_geo = util.DfOper.mult([total_stock,cfg.geo.map_df(cfg.primary_geography, self.tradable_geography,eliminate_zeros=False)])
                    util.replace_index_name(self.stock_capacity_geo ,cfg.primary_geography + "from", cfg.primary_geography)
                
                if hasattr(self,'stock_energy_geo') and hasattr(self,'potential_geo'):
                    #this is a special case when we have a stock and specified potential. We want to distribute growth in the stock by potential while maintaing trades to support existing stock. 
                    active_supply = util.remove_df_levels(self.active_supply, [x for x in self.active_supply.index.names if x not in self.stock.act_total_energy.index.names])                
                    total_active_supply = util.remove_df_levels(util.DfOper.mult([active_supply,cfg.geo.map_df(cfg.primary_geography,self.tradable_geography, normalize_as='total', eliminate_zeros=False)]),cfg.primary_geography)
                    total_stock = util.remove_df_levels(self.stock_energy_geo,cfg.primary_geography)
                    stock_share = util.remove_df_levels(util.DfOper.divi([total_stock,total_active_supply]),cfg.primary_geography + "from")
                    stock_share[stock_share>1] = 1
                    stock_geo_step = self.stock_energy_geo.groupby(level=util.ix_excl(self.stock_energy_geo,cfg.primary_geography + "from")).transform(lambda x: x/x.sum()).fillna(0)
                    stock_geo_step = util.DfOper.mult([stock_geo_step, stock_share])
                    potential_share = 1- stock_share
                    potential_geo_step = util.DfOper.subt([self.potential_geo,self.stock_energy_geo])
                    potential_geo_step[potential_geo_step<0]=0
                    potential_geo_step = potential_geo_step.groupby(level=util.ix_excl(self.potential_geo,cfg.primary_geography + "from")).transform(lambda x: x/x.sum()).fillna(0)
                    potential_geo_step = util.DfOper.mult([potential_geo_step, potential_share])
                    self.geo_step2 = util.DfOper.add([stock_geo_step,potential_geo_step])
                elif hasattr(self,'stock_energy_geo'):
                    self.geo_step2 = self.stock_energy_geo.groupby(level=util.ix_excl(self.stock_energy_geo,cfg.primary_geography + "from")).transform(lambda x: x/x.sum()).fillna(0)
                elif hasattr(self,'stock_capacity_geo'):
                    self.geo_step2 = self.stock_capacity_geo.groupby(level=util.ix_excl(self.stock_capacity_geo,cfg.primary_geography + "from")).transform(lambda x: x/x.sum()).fillna(0)
                elif hasattr(self,'potential_geo'):
                    self.geo_step2 = self.potential_geo.groupby(level=util.ix_excl(self.potential_geo,cfg.primary_geography + "from")).transform(lambda x: x/x.sum()).fillna(0)
                self.geomapped_coefficients = util.DfOper.mult([self.geo_step1, self.geo_step2])
                self.geomapped_coefficients = self.geomapped_coefficients.unstack(cfg.primary_geography)
                util.replace_index_name(self.geomapped_coefficients,cfg.primary_geography,cfg.primary_geography + "from")
                self.geomapped_coefficients = util.remove_df_levels(self.geomapped_coefficients,self.tradable_geography)              
                self.geomapped_coefficients.columns = self.geomapped_coefficients.columns.droplevel() 
                self.active_internal_trade_df = pd.concat([self.geomapped_coefficients]*len(self.demand_sectors),axis=1,keys=self.demand_sectors,names=['demand_sector'])
                self.active_internal_trade_df= self.active_internal_trade_df.swaplevel(cfg.primary_geography,'demand_sector',axis=1)
                if 'demand_sector' not in self.active_internal_trade_df.index.names:
                    self.active_internal_trade_df = pd.concat([self.active_internal_trade_df]*len(self.demand_sectors),axis=0,keys=self.demand_sectors,names=['demand_sector'])
                    self.active_internal_trade_df = self.active_internal_trade_df.swaplevel(cfg.primary_geography,'demand_sector',axis=0)
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
                else:
                    pdb.set_trace()
                self.internal_trades = "stop and feed"
            else:
                self.internal_trades = "stop"
        elif self.tradable_geography != cfg.primary_geography:
            #if there is only one geography, there is no trading
            self.internal_trades = "stop"
        elif self.tradable_geography == cfg.primary_geography and self.enforce_tradable_geography:
            #if the tradable geography is set to equal the primary geography, then any trades upstream are stopped at this node
            self.internal_trades = "stop"
        else:
            #otherwise, pass trades upstream to downstream nodes
            self.internal_trades = "feed"


    def calculate_input_emissions_rates(self,year,ghgs):
        "calculates the emissions rate of nodes with emissions"
        if hasattr(self,'emissions') and self.emissions.data is True:
            if hasattr(self,'potential') and self.potential.data is True:
                filter_geo_potential_normal = util.remove_df_elements(self.potential.active_supply_curve_normal, [x for x in cfg.geo.geographies_unfiltered[cfg.primary_geography]  if x not in cfg.geographies],cfg.primary_geography)
                filter_geo_potential_normal = filter_geo_potential_normal.reset_index().set_index(filter_geo_potential_normal.index.names)
                self.active_physical_emissions_rate = DfOper.mult([filter_geo_potential_normal,self.emissions.values_physical.loc[:,year].to_frame()])
                levels = ['demand_sector',cfg.primary_geography,'ghg']
                disallowed_levels = [x for x in self.active_physical_emissions_rate.index.names if x not in levels]
                if len(disallowed_levels):
                    self.active_physical_emissions_rate = util.remove_df_levels(self.active_physical_emissions_rate, disallowed_levels)
                self.active_physical_emissions_rate = util.expand_multi(self.active_physical_emissions_rate, levels_list = [cfg.geographies, self.demand_sectors, self.ghgs],levels_names=[cfg.primary_geography,'demand_sector', 'ghg'])
                self.active_accounting_emissions_rate = DfOper.mult([filter_geo_potential_normal,self.emissions.values_accounting.loc[:,year].to_frame()])
                levels = ['demand_sector',cfg.primary_geography,'ghg']
                disallowed_levels = [x for x in self.active_accounting_emissions_rate.index.names if x not in levels]
                if len(disallowed_levels):
                    self.active_accounting_emissions_rate = util.remove_df_levels(self.active_accounting_emissions_rate, disallowed_levels)
                self.active_accounting_emissions_rate = util.expand_multi(self.active_accounting_emissions_rate, levels_list = [cfg.geographies, self.demand_sectors, self.ghgs], levels_names=[cfg.primary_geography,'demand_sector','ghg'])
            else:
                allowed_indices = ['demand_sector', cfg.primary_geography, 'ghg', 'ghg_type']
                if set(self.emissions.values_physical.index.names).issubset(allowed_indices):
                    self.active_physical_emissions_rate = util.remove_df_levels(self.emissions.values_physical.loc[:,year].to_frame(), 'ghg_type')
                    self.active_physical_emissions_rate = util.expand_multi(self.active_physical_emissions_rate, levels_list = [cfg.geographies, self.demand_sectors, self.ghgs],levels_names=[cfg.primary_geography,'demand_sector', 'ghg'])
                if set(self.emissions.values_accounting.index.names).issubset(allowed_indices):     
                    self.active_accounting_emissions_rate =  util.remove_df_levels(self.emissions.values_accounting.loc[:,year].to_frame(), 'ghg_type')
                    self.active_accounting_emissions_rate = util.expand_multi(self.active_accounting_emissions_rate, levels_list = [cfg.geographies, self.demand_sectors, self.ghgs],levels_names=[cfg.primary_geography,'demand_sector', 'ghg'])
                else:
                    raise ValueError("too many indexes in emissions inputs of node %s" %self.id)
            keys = [self.demand_sectors, cfg.geographies]
            names = ['demand_sector', cfg.primary_geography]
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
            if 1 in self.active_physical_emissions_coefficients.index.get_level_values('efficiency_type'):
                indexer = util.level_specific_indexer(self.active_physical_emissions_coefficients,'efficiency_type', 1)
                combustion_emissions = copy.deepcopy(self.active_physical_emissions_coefficients.loc[indexer,:])
                combustion_emissions.loc[:,:] = self.active_supply.T.values * self.active_physical_emissions_coefficients.loc[indexer,:].values
                self.active_combustion_emissions = combustion_emissions.groupby(level='ghg').sum() 
                self.active_combustion_emissions = self.active_combustion_emissions.unstack(cfg.primary_geography).to_frame()
                if hasattr(self,'active_co2_capture_rate'):
                    self.active_combustion_emissions = DfOper.mult([self.active_combustion_emissions, 1- self.active_co2_capture_rate])
                self.active_combustion_emissions = util.remove_df_levels(self.active_combustion_emissions,'resource_bin')
        if hasattr(self,'active_accounting_emissions_rate'):
            self.active_accounting_emissions = DfOper.mult([self.active_accounting_emissions_rate,self.active_supply])    
        if hasattr(self,'active_accounting_emissions') and hasattr(self,'active_combustion_emissions'):
            self.active_total_emissions = DfOper.add([self.active_accounting_emissions, self.active_combustion_emissions])
        elif hasattr(self,'active_accounting_emissions'):
            self.active_total_emissions = self.active_accounting_emissions
        elif hasattr(self,'active_combustion_emissions'):
            self.active_total_emissions = self.active_combustion_emissions
        
    def calculate_embodied_emissions_rate(self,year):
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
            row_index = pd.MultiIndex.from_product([cfg.geographies, self.demand_sectors, self.nodes], names=[cfg.primary_geography, 'demand_sector', 'supply_node'])
            col_index = pd.MultiIndex.from_product([cfg.geographies, self.demand_sectors], names=[cfg.primary_geography, 'demand_sector'])
            trade_adjustment_df = util.empty_df(index=row_index,columns=col_index,fill_value=0.0)
            trade_adjustment_df.sort(inplace=True, axis=0)
            trade_adjustment_df.sort(inplace=True, axis=1)
            trade_adjustment_groups = trade_adjustment_df.groupby(level=trade_adjustment_df.index.names).groups
            for elements in trade_adjustment_groups.keys():
                row_indexer = util.level_specific_indexer(trade_adjustment_df, trade_adjustment_df.index.names, elements)
                col_indexer = util.level_specific_indexer(trade_adjustment_df,[cfg.primary_geography, 'demand_sector'], elements[:-1], axis=1)
                trade_adjustment_df.loc[row_indexer, col_indexer] = 1.0  
            for year in self.years:      
               self.trade_adjustment_dict[year] = copy.deepcopy(trade_adjustment_df) 
            self.active_trade_adjustment_df = trade_adjustment_df
                 
    def set_internal_trade_dict(self):
        """sets an empty df with a fill value of 1 for internal trades"""
        if self.tradable_geography is not None:
            self.internal_trade_dict = defaultdict(dict)
            index = pd.MultiIndex.from_product([cfg.geographies, self.demand_sectors], names=[cfg.primary_geography, 'demand_sector'])
            internal_trade_df = util.empty_df(index=index,columns=index,fill_value=0.0)
            internal_trade_df.sort(inplace=True, axis=0)
            internal_trade_df.sort(inplace=True, axis=1)
            internal_trade_groups = internal_trade_df.groupby(level=internal_trade_df.index.names).groups
            for elements in internal_trade_groups.keys():
                row_indexer = util.level_specific_indexer(internal_trade_df, internal_trade_df.index.names, elements)
                col_indexer = util.level_specific_indexer(internal_trade_df,[cfg.primary_geography, 'demand_sector'], list(elements), axis=1)
                internal_trade_df.loc[row_indexer, col_indexer] = 1.0  
            for year in self.years:
                self.internal_trade_dict[year] = copy.deepcopy(internal_trade_df)
            self.active_internal_trade_df = internal_trade_df

    def set_pass_through_df_dict(self):    
        """sets an empty df with a fill value of 1 for trade adjustments"""
        self.pass_through_df_dict = defaultdict(dict)
        row_index = pd.MultiIndex.from_product([cfg.geographies, self.demand_sectors, self.ghgs], names=[cfg.primary_geography, 'demand_sector', 'ghg'])
        col_index = pd.MultiIndex.from_product([cfg.geographies, self.demand_sectors], names=[cfg.primary_geography, 'demand_sector'])
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
            self.active_coefficients = self.active_coefficients.sort()
            if 2 in set(self.active_coefficients.index.get_level_values('efficiency_type')):    
                indexer = util.level_specific_indexer(self.active_coefficients,'efficiency_type',2)
                pass_through_subsectors = self.active_coefficients.loc[indexer,:].index.get_level_values('supply_node')
                pass_through_subsectors = [int(x) for x in pass_through_subsectors if node_dict.has_key(x)]                
                self.pass_through_dict = dict.fromkeys(pass_through_subsectors,False)  
            

        
class Export(Abstract):
    def __init__(self,node_id, measure_id=None, **kwargs):
        self.input_type = 'total'
        if measure_id is None:
            self.id = node_id
            self.sql_id_table = 'SupplyExport'
            self.sql_data_table = 'SupplyExportData'
            Abstract.__init__(self, self.id, primary_key='supply_node_id')
        else:
            self.id = measure_id
            self.sql_id_table = 'SupplyExportMeasures'
            self.sql_data_table = 'SupplyExportMeasuresData'
            Abstract.__init__(self, measure_id, primary_key='id', data_id_key='parent_id')
            
    def calculate(self, years, demand_sectors):
        self.years = years
        self.demand_sectors = demand_sectors
        if self.data is True:
            self.remap(lower=None)
            self.convert()
            self.values = util.reindex_df_level_with_new_elements(self.values, cfg.primary_geography, cfg.geographies, fill_value=0.0)
        else:
            self.set_export_df()
            
    def convert(self):        
       self.values = self.values.unstack(level='year')    
       self.values.columns = self.values.columns.droplevel()
       self.values = util.unit_convert(self.values, unit_from_num=self.unit, unit_to_num=cfg.calculation_energy_unit)

    def set_export_df(self):
        """sets an empty df with a fill value of 0"""
        df_index = pd.MultiIndex.from_product([cfg.geographies, self.demand_sectors], names=[cfg.primary_geography, 'demand_sector'])
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
            self.remap(map_from='active_values', map_to='active_values', drivers=active_supply, fill_timeseries=False, current_geography=cfg.primary_geography, driver_geography=cfg.primary_geography)
        self.active_values.replace(np.nan,0,inplace=True)
        self.active_values = self.active_values.reorder_levels([cfg.primary_geography, 'demand_sector'])

           
class BlendNode(Node):
    def __init__(self, id, supply_type, scenario, **kwargs):
        Node.__init__(self, id, supply_type, scenario)
        self.id = id
        self.supply_type = supply_type
        for col, att in util.object_att_from_table('SupplyNodes', id, ):
            setattr(self, col, att)
        self.nodes = util.sql_read_table('BlendNodeInputsData', 'supply_node_id', blend_node_id=id, return_iterable=True)
        #used as a flag in the annual loop for whether we need to recalculate the coefficients
   
            
    def calculate_active_coefficients(self, year, loop):
            self.active_coefficients = self.values.loc[:,year].to_frame()
            self.active_coefficients_total_untraded = util.remove_df_levels(self.active_coefficients,'efficiency_type')       
            self.active_coefficients_untraded = copy.deepcopy(self.active_coefficients) 
            self.active_coefficients_untraded.sort(inplace=True,axis=0)
            self.active_coefficients = self.add_column_index(self.active_coefficients_untraded).T.stack(['supply_node','efficiency_type'])
            self.active_coefficients_total = self.add_column_index(self.active_coefficients_total_untraded).T.stack(['supply_node'])
            self.active_coefficients_total_emissions_rate = copy.deepcopy(self.active_coefficients_total)            
            self.active_coefficients_total = DfOper.mult([self.active_coefficients_total,self.active_trade_adjustment_df])
            keys = [2]
            name = ['efficiency_type']
            active_trade_adjustment_df = pd.concat([self.active_trade_adjustment_df]*len(keys), keys=keys, names=name)
#            active_constraint_adjustment_df = pd.concat([self.active_constraint_adjustment_df]*len(keys), keys=keys, names=name)
            self.active_coefficients = DfOper.mult([self.active_coefficients,active_trade_adjustment_df])
            keys = self.ghgs
            name = ['ghg']
            self.active_emissions_coefficients = pd.concat([self.active_coefficients]*len(keys), keys=keys, names=name)
            self.active_emissions_coefficients = self.active_emissions_coefficients.reorder_levels([cfg.primary_geography, 'demand_sector', 'supply_node', 'efficiency_type', 'ghg'])
            self.active_emissions_coefficients.sort(inplace=True)
            
    def add_blend_measures(self, scenario):
            """
            add all blend measures in a selected scenario to a dictionary
            """
            self.blend_measures = {id: BlendMeasure(id, scenario)
                                   for id in scenario.get_measures('BlendNodeBlendMeasures', self.id)}
            
    def calculate(self):
        #all nodes can have potential conversions. Set to None if no data. 
        self.conversion, self.resource_unit = self.add_conversion()  
        measures = []
        for measure in self.blend_measures.values():
            measure.calculate(self.vintages, self.years)
            measures.append(measure.values)
        if len(measures):
            self.raw_values = util.DfOper.add(measures)
            self.calculate_residual()
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
         self.values = self.raw_values.sort()
         if 'demand_sector' in self.values.index.names:
            self.values = util.reindex_df_level_with_new_elements(self.values,'demand_sector',self.demand_sectors,0)
         if self.residual_supply_node_id in self.values.index.get_level_values('supply_node'):
             indexer = util.level_specific_indexer(self.values, 'supply_node', self.residual_supply_node_id)
             self.values.loc[indexer,:] = 0
         residual = 1-util.remove_df_levels(self.values,['supply_node'])
         residual['supply_node'] = self.residual_supply_node_id
         residual.set_index('supply_node', append=True, inplace=True)
#         residual = residual.reorder_levels(residual_levels+['supply_node'])
         # concatenate values
#         residual = residual.reorder_levels(self.values.index.names)
         self.values = pd.concat([self.values, residual], join='outer', axis=0)
         # remove duplicates where a node is specified and is specified as residual node
         self.values = self.values.groupby(level=self.values.index.names).sum()
         # set negative values to 0
         self.values.loc[self.values['value'] <= 0, 'value'] = 1e-7
         self.expand_blend()
         self.values = self.values.unstack(level='year')    
         self.values.columns = self.values.columns.droplevel()


    def update_residual(self, year):
        """calculates values for residual node in Blend Node dataframe
         ex. if 10% of hydrogen blend is supplied by electrolysis and the rest is unspecified,
         90% of hydrogen blend is allocated to residual node
         """
        # calculates sum of all supply_nodes
        indexer = util.level_specific_indexer(self.values, 'supply_node', self.residual_supply_node_id)
        self.values.loc[indexer,year] = 0
        residual_levels = [x for x in self.values.index.names if x != 'supply_node']
        # residual equals 1-sum of all other specified nodes
        residual = 1-self.values.loc[:,year].to_frame().groupby(level=residual_levels).sum()
        residual['supply_node'] = self.residual_supply_node_id
        residual.set_index('supply_node', append=True, inplace=True)
        residual = residual.reorder_levels(residual_levels+['supply_node'])
        # concatenate values
        residual = residual.reorder_levels(self.values.index.names)
        self.values.loc[indexer,year] = residual
        # remove duplicates where a node is specified and is specified as residual node
        self.values.loc[:,year] = self.values.loc[:,year].groupby(level=self.values.index.names).sum()
        # set negative values to 0
        self.values[self.values <= 0] = 1e-7

    def expand_blend(self):
        #needs a fill value because if a node is not demanding any energy from another node, it still may be supplied, and reconciliation happens via division (can't multiply by 0)
        self.values = util.reindex_df_level_with_new_elements(self.values,'supply_node', self.nodes, fill_value = 1e-7)
        if 'demand_sector' not in self.values.index.names:
            self.values = util.expand_multi(self.values, self.demand_sectors, ['demand_sector'], incremental=True)
        self.values['efficiency_type'] = 2
        self.values.set_index('efficiency_type', append=True, inplace=True)
        self.values = self.values.reorder_levels([cfg.primary_geography,'demand_sector','supply_node','efficiency_type','year'])
        self.values = self.values.sort()
         
    def set_residual(self):
        """creats an empty df with the value for the residual node of 1. For nodes with no blend measures specified"""
        df_index = pd.MultiIndex.from_product([cfg.geo.geographies[cfg.primary_geography], self.demand_sectors, self.nodes, self.years, [2]], names=[cfg.primary_geography, 'demand_sector','supply_node','year','efficiency_type' ])
        self.raw_values = util.empty_df(index=df_index,columns=['value'],fill_value=1e-7)
        indexer = util.level_specific_indexer(self.raw_values, 'supply_node', self.residual_supply_node_id)
        self.raw_values.loc[indexer, 'value'] = 1
        self.raw_values = self.raw_values.unstack(level='year')    
        self.raw_values.columns = self.raw_values.columns.droplevel()
        self.raw_values = self.raw_values.sort()
        self.values = copy.deepcopy(self.raw_values)
        
    
class SupplyNode(Node,StockItem):
    def __init__(self, id, supply_type, scenario, **kwargs):
        Node.__init__(self, id, supply_type, scenario)
        StockItem.__init__(self)
        self.input_type = 'total'
        self.coefficients = SupplyCoefficients(self.id, self.scenario)
        self.potential = SupplyPotential(self.id, self.enforce_potential_constraint, self.scenario)
        self.capacity_factor = SupplyCapacityFactor(self.id, self.scenario)
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
        if self.potential.data is True:
            for name, level in zip(self.potential.raw_values.index.names, self.potential.raw_values.index.levels):
                if (name == 'resource_bin' or name == 'demand_sector') and name not in self.rollover_group_names:
                        if name == 'demand_sector':
                            level = self.demand_sectors
                        self.rollover_group_levels.append(list(level))
                        self.rollover_group_names.append(name)            
        if self.stock.data is True:
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
        if self.id == self.distribution_grid_node_id and 'demand_sector' not in self.rollover_group_names:
            #requires distribution grid node to maintain demand sector resolution in its stocks
            self.rollover_group_levels.append(self.demand_sectors)
            self.rollover_group_names.append('demand_sector')
        self.rollover_group_names = [cfg.primary_geography] + self.rollover_group_names
        self.rollover_group_levels = [cfg.geo.geographies[cfg.primary_geography]] + self.rollover_group_levels
        
    def add_stock(self):
        """add stock instance to node"""
        self.stock = Stock(id=self.id, drivers=None, sql_id_table='SupplyStock', sql_data_table='SupplyStockData', primary_key='supply_node_id', scenario=self.scenario)
        self.stock.input_type = 'total'
        self.stock.unit = cfg.calculation_energy_unit + "/" + cfg.cfgfile.get('case','time_step')
           
    def add_case_stock(self):
       self.case_stock = StockItem()
#       total_stocks = []
#       for stock in self.total_stocks:
#           total_stocks.append(stock)
       if len(self.total_stocks):
            self.case_stock.data = True
            self.case_stock.total = DfOper.add([ x.values for x in self.total_stocks.values()], expandable=False)
#            self.case_stock.total[self.case_stock.total.index.get_level_values('year')<int(cfg.cfgfile.get('case','current_year'))+1] = np.nan
    
    def calculate_stock_measures(self):
        for stock in self.total_stocks.values():
            stock.calculate(self.vintages,self.years)
            stock.convert()

    def calculate_input_stock(self):
        self.stock.years = self.years
        if self.stock.data is True:
            self.stock.remap(map_from='raw_values', map_to='total',fill_timeseries=True,fill_value=np.nan)
            self.convert_stock('stock','total')
            self.stock.total = util.remove_df_levels(self.stock.total,'supply_technology')
#        if hasattr(self.case_stock,'total'):
#            self.case_stock.remap(map_from='raw_values', map_to='total',fill_timeseries=True, fill_value=np.nan)
        if self.stock.data is True and hasattr(self.case_stock,'total'):
            self.convert_stock('case_stock','total')
#           self.case_stock.total.fillna(self.stock.total, inplace=True)
            self.stock.total = self.stock.total[self.stock.total.index.get_level_values('year')<=int(cfg.cfgfile.get('case','current_year'))] 
            self.case_stock.total[self.stock.total.index.get_level_values('year')>int(cfg.cfgfile.get('case','current_year'))]
            self.case_stock.total = pd.concat([self.stock.total,self.case_stock.total])
            self
        elif self.stock.data is False and hasattr(self.case_stock,'total'):
            self.stock = self.case_stock
        elif self.stock.data is False and not hasattr(self.case_stock,'total'):
            index = pd.MultiIndex.from_product(self.rollover_group_levels + [self.years] ,names=self.rollover_group_names + ['year'] )
            self.stock.total = util.empty_df(index=index,columns=['value'],fill_value=np.nan)
        self.stock.total_rollover = copy.deepcopy(self.stock.total)
        self.stock.total = self.stock.total.unstack('year')
        self.stock.total.columns = self.stock.total.columns.droplevel()
        if self.stock.data or hasattr(self.case_stock,'data') and self.case_stock.data == True:
            self.stock.data = True
        
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
                setattr(self.stock, fun, pd.DataFrame(np.array(functions[fun]).T, columns=[self.id]))

    def create_node_rollover_markov_matrices(self):
        vintaged_markov = util.create_markov_vector(self.stock.decay_vintaged.values, self.stock.survival_vintaged.values)
        self.stock.vintaged_markov_matrix = util.create_markov_matrix(vintaged_markov, 1 , len(self.years))
        initial_markov = util.create_markov_vector(self.stock.decay_initial_stock.values, self.stock.survival_initial_stock.values)
        self.stock.initial_markov_matrix = util.create_markov_matrix(initial_markov, 1 , len(self.years))

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
                                     
        for year in [x for x in self.years if x<int(cfg.cfgfile.get('case', 'current_year'))]:
            for elements in self.rollover_groups.keys():
                elements = util.ensure_tuple(elements)
                try:
                    self.rollover_dict[elements].run(1)
                except:
                    logging.error('error encountered in rollover for node ' + str(self.id) + ' in elements '+ str(elements) + ' year ' + str(year))
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
        if self.capacity_factor.data is True:
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
        self.active_dispatch_costs = self.active_dispatch_costs.stack([cfg.primary_geography,'demand_sector'])
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
                self.rollover_dict[elements].initial_stock = np.array(util.ensure_iterable_and_not_string(self.stock.requirement.loc[elements, year]))
        #run the stock rollover for the year and record values                
        for elements in self.rollover_groups.keys():    
            elements = util.ensure_tuple(elements)
            try:
                self.rollover_dict[elements].use_stock_changes = True
                self.rollover_dict[elements].run(1, stock_changes.loc[elements],np.array(self.stock.total_rollover.loc[elements+(year,)]))
            except:
                logging.error('error encountered in rollover for node ' + str(self.id) + ' in elements '+ str(elements) + ' year ' + str(year))
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
        self.stock.values_energy[year] = DfOper.mult([self.stock.values[year].to_frame(), self.capacity_factor.values[year].to_frame()])* util.unit_conversion(unit_from_den=cfg.cfgfile.get('case','time_step'), unit_to_den='year')[0]
        indexer = util.level_specific_indexer(self.stock.sales,'vintage', year)
        self.stock.sales_energy.loc[indexer,:] = DfOper.mult([self.stock.sales.loc[indexer,:], self.capacity_factor.values[year].to_frame()])* util.unit_conversion(unit_from_den=cfg.cfgfile.get('case','time_step'), unit_to_den='year')[0]

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
        self.stock.values_financial_energy[year] = DfOper.mult([self.stock.values_financial[year].to_frame(), self.capacity_factor.values[year].to_frame()])* util.unit_conversion(unit_from_den=cfg.cfgfile.get('case','time_step'), unit_to_den='year')[0]
    
    def calculate_active_coefficients(self,year, loop):
        """calculates the active coefficients"""
        #If a node has no potential data, then it doesn't have a supply curve. Therefore the coefficients are just the specified inputs in that year   
        if year == int(cfg.cfgfile.get('case', 'current_year')) and loop == 'initial':
            #in the initial loop of the supply-side, we only know internal demand
            throughput = self.active_demand
        else:
            #after that, our best representation of throughput is active supply, which is updated in every IO loop 
            throughput = self.active_supply         
        #in the first loop we take a slice of the input node efficiency
        if self.potential.data is False:
            #if the node has no potential data, and therefore no supply curve
            if self.coefficients.data is True:
                #we take the coefficients for the current year
                self.active_coefficients = self.coefficients.values.loc[:,year].to_frame()
            else:
                self.active_coefficients = None
                self.active_coefficients_total = None
        elif self.coefficients.data is True:
            if self.potential.raw_values is not None:
              try:
                  self.potential.remap_to_potential_and_normalize(throughput, year, self.tradable_geography)
              except:
                  pdb.set_trace()
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
              #  coefficient_indexer = util.level_specific_indexer(self.active_coefficients_untraded.sort(), 'supply_node', node)
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
            self.active_emissions_coefficients = self.active_emissions_coefficients.reorder_levels([cfg.primary_geography,'demand_sector', 'supply_node', 'efficiency_type', 'ghg'])
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
        if year == int(cfg.cfgfile.get('case','current_year')) and loop == 'initial':
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
            if year == int(cfg.cfgfile.get('case','current_year')) and loop == 'initial':  
                self.stock.remaining.loc[element_indexer, year] = self.rollover_dict[elements].return_formatted_stock(year_offset=1)                 
            elif year == int(cfg.cfgfile.get('case','current_year')) and loop == 1:
                self.rollover_dict[elements].rewind(1)    
                self.stock.remaining.loc[element_indexer, year] = self.rollover_dict[elements].return_formatted_stock(year_offset=1)             
            elif loop == 1:                
                self.stock.remaining.loc[element_indexer, year] = self.rollover_dict[elements].return_formatted_stock(year_offset=1)             
            else:
                self.rollover_dict[elements].rewind(1)
        self.stock.act_rem_energy = util.DfOper.mult([self.stock.remaining.loc[:,year].to_frame(), self.capacity_factor.values.loc[:,year].to_frame()]) * util.unit_conversion(unit_from_den=cfg.cfgfile.get('case', 'time_step'), unit_to_den='year')[0]
        default_conversion = self.capacity_factor.values.loc[:,year].to_frame() * util.unit_conversion(unit_from_num='year',unit_to_num=cfg.cfgfile.get('case', 'time_step'))[0]
        self.stock.act_energy_capacity_ratio = util.DfOper.divi([self.stock.act_rem_energy.groupby(level=util.ix_excl(self.stock.act_rem_energy,['vintage'])).sum(),
                                    self.stock.remaining.loc[:, year].to_frame().groupby(level=util.ix_excl(self.stock.remaining, ['vintage'])).sum()]).fillna(default_conversion)
        self.stock.act_energy_capacity_ratio[self.stock.act_energy_capacity_ratio==0]= util.unit_conversion(unit_from_num='year',unit_to_num=cfg.cfgfile.get('case', 'time_step'))[0]

    def update_total(self, year):
        """sets the minimum necessary total stock - based on throughput (stock requirement) and total of the specified and remaining stock"""
        self.stock.act_total_energy = util.DfOper.mult([self.stock.total.loc[:,year].to_frame(), self.stock.act_energy_capacity_ratio],fill_value=np.nan)
        self.stock.act_total_energy = self.stock.act_total_energy.fillna(util.remove_df_levels(self.stock.act_rem_energy,'vintage'))   
    
    def update_requirement(self,year):    
        """updates annual stock requirements with the maximum of required stock and specified and remaining natural rolloff. Also
        distributes the necessary stock changes to the available residuals in the supply curve bins if the stock has resource_bin indexers
        """
        previous_year = max(min(self.years),year-1)

        if self.potential.data is False:
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
        if year == int(cfg.cfgfile.get('case','current_year')) and year==min(self.years):
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
        ids = util.sql_read_table('SupplyCost',column_names='id',supply_node_id=self.id,return_iterable=True)
        for id in ids:
            self.add_costs(id)

    def add_costs(self, id, **kwargs):
        """
        add cost object to a supply stock node
        
        """
        if id in self.costs:
            # ToDo note that a node by the same name was added twice
            return
        else:
            self.costs[id] = SupplyCost(id,self.cost_of_capital)

    def calculate_costs(self,year, loop):
        start_year = min(self.years)
        if not hasattr(self,'levelized_costs'):
            index = pd.MultiIndex.from_product(self.rollover_group_levels, names=self.rollover_group_names)
            self.levelized_costs = util.empty_df(index, columns=self.years,fill_value=0.)
            self.embodied_cost = util.empty_df(index, columns=self.years,fill_value=0.)
            self.embodied_cost = util.remove_df_levels(self.embodied_cost,'resource_bin')
        if not hasattr(self,'annual_costs'):
            index = self.stock.sales.index
            self.annual_costs = util.empty_df(index, columns=['value'],fill_value=0.)        
        self.levelized_costs[year] = 0                
        for cost in self.costs.values():
            rev_req = util.DfOper.add([self.calculate_dynamic_supply_costs(cost, year, start_year), self.calculate_static_supply_costs(cost, year, start_year)])
            self.levelized_costs.loc[:,year] += rev_req.values.flatten()
            self.calculate_lump_costs(year, rev_req)
            cost.prev_yr_rev_req = rev_req 
        self.embodied_cost.loc[:,year] = util.DfOper.divi([self.levelized_costs[year].to_frame(), self.throughput],expandable=(False,False)).replace([np.inf,-np.inf,np.nan,-np.nan],[0,0,0,0]).values
        self.active_embodied_cost = util.expand_multi(self.embodied_cost[year].to_frame(), levels_list = [cfg.geo.geographies[cfg.primary_geography], self.demand_sectors],levels_names=[cfg.primary_geography,'demand_sector'])

   
    def calculate_dynamic_supply_costs(self, cost,year,start_year):
        "returns a revenue requirement for the component of costs that is correlated with throughput"
        if cost.data is True:
            #determine increased tariffs due to growth rate (financial/physical stock rati0)
            limited_names = self.rollover_group_names if len(self.rollover_group_names)>1 else self.rollover_group_names[0]
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
                        return util.DfOper.mult([rev_req,growth_mult]) * cost.throughput_correlation  
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
                        return util.DfOper.mult([rev_req,cap_factor_mult,growth_mult]) * cost.throughput_correlation  
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
                    return util.DfOper.mult([rev_req,cap_factor_mult,growth_mult]) * cost.throughput_correlation 
            else:
                raise ValueError("investment cost types not implemented")
            
            
    def calculate_static_supply_costs(self,cost,year,start_year):
       "returns a revenue requirement for the component of costs that is not correlated with throughput"
       first_yr_stock = self.stock.values.groupby(level= self.rollover_group_names).sum()[start_year].to_frame() 
       first_yr_energy = self.stock.values_energy.groupby(level=self.rollover_group_names).sum()[start_year].to_frame()           
       if cost.supply_cost_type == 'tariff':
            tariff = cost.values_level_no_vintage[year].to_frame()           
            if cost.capacity is True:
                rev_req = util.DfOper.mult([tariff,first_yr_stock],expandable=(False,False))[year].to_frame()    
            else:
                rev_req = util.DfOper.mult([tariff,first_yr_energy],expandable=(False,False))[year].to_frame()  
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
        energy_stock = self.stock.values[supply_years] * util.unit_convert(1,unit_from_den='hour', unit_to_den='year')
        self.capacity_utilization = util.DfOper.divi([energy_supply,energy_stock],expandable=False).replace([np.inf,np.nan,-np.nan],[0,0,0])           
        
                  
class SupplyCapacityFactor(Abstract):
    def __init__(self, id, scenario, **kwargs):
        self.id = id
        self.input_type = 'intensity'
        self.sql_id_table = 'SupplyCapacityFactor'
        self.sql_data_table = 'SupplyCapacityFactorData'
        self.scenario = scenario
        Abstract.__init__(self, self.id, 'supply_node_id')
    
    def calculate(self, years, demand_sectors):
        self.years = years
        self.demand_sectors = demand_sectors
        if self.data is True:
            self.remap()
#            self.convert()
            self.values = self.values.unstack('year')
            self.values.columns = self.values.columns.droplevel()


class SupplyPotential(Abstract):
    def __init__(self, id, enforce_potential_constraint, scenario, **kwargs):
        self.id = id
        self.input_type = 'total'
        self.sql_id_table = 'SupplyPotential'
        self.sql_data_table = 'SupplyPotentialData'
        self.enforce_potential_constraint = enforce_potential_constraint
        self.scenario = scenario
        Abstract.__init__(self, self.id, 'supply_node_id')

        
    def calculate(self, conversion, resource_unit):
        if self.data is True:
            self.conversion = conversion
            self.resource_unit=resource_unit
            self.remap(filter_geo=False)
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
#            self.resource_values = util.unit_convert(self.values,unit_from_den=self.time_unit, unit_to_den='year')
#            self.resource_supply_curve = self.resource_values.groupby(level=[cfg.primary_geography]).cumsum()
            self.values = DfOper.mult([self.values, self.conversion.values],fill_value=self.conversion.values.mean().mean())
#            self.supply_curve = util.remove_df_levels(self.values, [x for x in self.values.index.names if x not in [cfg.primary_geography,'resource_bin']])

            self.supply_curve = self.values
        else:
            if util.determ_energy(self.unit):
                self.values = util.unit_convert(self.values, unit_from_num=self.unit, unit_from_den=self.time_unit, unit_to_num=cfg.calculation_energy_unit, unit_to_den='year')
            else:
                raise ValueError('unit is not an energy unit and no resource conversion has been entered in node %s' %self.id)
            self.supply_curve = self.values

    def remap_to_potential(self, active_throughput, year, tradable_geography=None):
        """remaps throughput to potential bins"""    
        #original supply curve represents an annual timeslice
        primary_geography = cfg.primary_geography
        self.active_throughput = active_throughput
        #self.active_throughput[self.active_throughput<=0] = 1E-25
        original_supply_curve = util.remove_df_levels(self.supply_curve.loc[:,year].to_frame().sort(),[x for x in self.supply_curve.loc[:,year].index.names if x not in [primary_geography, 'resource_bin', 'demand_sector']])
        self.active_supply_curve = util.remove_df_levels(original_supply_curve,[x for x in self.supply_curve.loc[:,year].index.names if x not in [primary_geography, 'resource_bin', 'demand_sector']])
        if tradable_geography is not None and tradable_geography!=primary_geography:
                map_df = cfg.geo.map_df(primary_geography,tradable_geography,normalize_as='total',eliminate_zeros=False,filter_geo=False)
                original_supply_curve = util.DfOper.mult([map_df,original_supply_curve])
                self.geo_map(converted_geography=tradable_geography, attr='active_supply_curve', inplace=True, current_geography=primary_geography,filter_geo=False)
                self.geo_map(converted_geography=tradable_geography, attr='active_throughput', inplace=True, current_geography=primary_geography,filter_geo=False)
        self.active_supply_curve = self.active_supply_curve.groupby(level=[x for x in self.active_supply_curve.index.names if x not in 'resource_bin']).cumsum()         
        reindexed_throughput = util.DfOper.none([self.active_throughput,self.active_supply_curve],expandable=(True,False),collapsible=(True,True))           
        self.active_supply_curve = util.expand_multi(self.active_supply_curve, reindexed_throughput.index.levels,reindexed_throughput.index.names)        
        reindexed_throughput = util.DfOper.none([self.active_throughput,self.active_supply_curve],expandable=(True,False),collapsible=(True,True))   
        bin_supply_curve = copy.deepcopy(self.active_supply_curve)        
        try:
            bin_supply_curve[bin_supply_curve>reindexed_throughput] = reindexed_throughput
        except:
            pdb.set_trace()
        self.active_supply_curve = bin_supply_curve.groupby(level=util.ix_excl(bin_supply_curve,'resource_bin')).diff().fillna(bin_supply_curve)
        if tradable_geography is not None and tradable_geography!=primary_geography:
            normalized = original_supply_curve.groupby(level=[tradable_geography,'resource_bin']).transform(lambda x: x/x.sum())
            self.active_supply_curve = util.remove_df_levels(util.DfOper.mult([normalized,self.active_supply_curve]),tradable_geography)
        self.active_supply_curve.columns = ['value']

    def remap_to_potential_and_normalize(self,active_throughput, year,tradable_geography=None) :
        """returns the proportion of the supply curve that is in each bin"""
        self.remap_to_potential(active_throughput, year, tradable_geography)
        self.active_supply_curve_normal= self.active_supply_curve.groupby(level=cfg.primary_geography).transform(lambda x:x/x.sum()).fillna(0.)

    def format_potential_and_supply_for_constraint_check(self,active_supply, tradable_geography, year):
        if tradable_geography == cfg.primary_geography:
            self.active_potential = self.values.loc[:,year].to_frame()
            self.active_geomapped_potential = self.active_potential
            self.active_geomapped_supply = active_supply
        else:
            self.active_potential = self.values.loc[:,year].to_frame()
            self.active_geomapped_potential = self.geo_map(converted_geography=tradable_geography, attr='active_potential', inplace=False, current_geography=cfg.primary_geography, current_data_type='total',filter_geo=False)
            self.active_geomapped_supply = active_supply
            self.active_geomapped_supply = self.geo_map(converted_geography=tradable_geography, attr='active_geomapped_supply', inplace=False, current_geography=cfg.primary_geography, current_data_type='total',filter_geo=False)
        levels = util.intersect(self.active_geomapped_supply.index.names, self.active_geomapped_supply.index.names)
        disallowed_potential_levels = [x for x in self.active_geomapped_potential.index.names if x not in levels]
        disallowed_supply_levels = [x for x in self.active_geomapped_supply.index.names if x not in levels]
        if len(disallowed_potential_levels):
            self.active_geomapped_potential = util.remove_df_levels(self.active_geomapped_potential, disallowed_potential_levels)     
        if len(disallowed_supply_levels):
            self.active_geomapped_supply= util.remove_df_levels(self.active_geomapped_supply, disallowed_supply_levels)       
        return self.active_geomapped_potential, self.active_geomapped_supply

class SupplyCost(Abstract):
    def __init__(self, id, cost_of_capital, **kwargs):
        self.id = id
        self.sql_id_table = 'SupplyCost'
        self.sql_data_table = 'SupplyCostData'
        Abstract.__init__(self, self.id, primary_key='id', data_id_key='parent_id')
        if self.cost_of_capital == None:
            self.cost_of_capital = cost_of_capital
            
    def calculate(self, years, demand_sectors):
        self.years = years
        self.vintages = [years[0]-1] + years 
        self.demand_sectors = demand_sectors
        if self.data is True:
            self.determ_input_type()
            self.remap(lower=None)
            self.convert()
            self.levelize_costs()

    def determ_input_type(self):
        """function that determines whether the input cost is a total or an intensity value"""
        if self.supply_cost_type == 'revenue requirement':
            self.input_type = 'total'
        elif self.supply_cost_type == 'tariff' or self.cost_type == 'investment':
            self.input_type = 'intensity'
        else:
            logging.error("incompatible cost type entry in cost %s" % self.id)
            raise ValueError

    def convert(self):
        """
        convert raw_values to model currency and capacity (energy_unit/time_step)
        """
        self.values = util.currency_convert(self.values, self.currency_id, self.currency_year_id)
        model_energy_unit = cfg.calculation_energy_unit
        model_time_step = cfg.cfgfile.get('case', 'time_step')
        if self.input_type == 'intensity':
            if self.time_unit is not None:
                # if a cost has a time_unit, then the unit is energy and must be converted to capacity
                self.values = util.unit_convert(self.values,
                                                unit_from_den=self.energy_or_capacity_unit,
                                                unit_from_num=self.time_unit, unit_to_den=model_energy_unit,
                                                unit_to_num=model_time_step)
                self.capacity = False
            else:
            # if a cost is a capacity unit, the model must convert the unit type to an energy unit for conversion ()
                if util.determ_energy(self.energy_or_capacity_unit):
                    self.values = util.unit_convert(self.values, unit_from_den =self.energy_or_capacity_unit, unit_to_den=model_energy_unit)
                    self.capacity = False
                else:
                    self.values = util.unit_convert(self.values,
                                                    unit_from_den=cfg.ureg.Quantity(self.energy_or_capacity_unit)*cfg.ureg.Quantity(model_time_step),
                                                    unit_from_num=model_time_step,
                                                    unit_to_den=model_energy_unit,
                                                    unit_to_num=model_time_step)
                    self.capacity = True
        else:
            self.capacity = True

    def levelize_costs(self):
        inflation = float(cfg.cfgfile.get('case', 'inflation_rate'))
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


class SupplyCoefficients(Abstract):
    def __init__(self, id, scenario, **kwargs):
        self.id = id
        self.input_type = 'intensity'
        self.sql_id_table = 'SupplyEfficiency'
        self.sql_data_table = 'SupplyEfficiencyData'
        self.scenario = scenario
        Abstract.__init__(self, self.id, primary_key='id', data_id_key='parent_id')
        
    def calculate(self, years, demand_sectors):
        self.years = years
        self.demand_sectors = demand_sectors
        if self.data is True:
            self.convert()
            self.remap(map_from='values',lower=None)
            self.values = self.values.unstack(level='year')    
            self.values.columns = self.values.columns.droplevel()
            #TODO fix
            if 'demand_sector' not in self.values.index.names:
                keys = self.demand_sectors
                names = ['demand_sector']
                self.values = pd.concat([self.values]*len(keys),keys=keys,names=names)
            self.values = self.values.reorder_levels([x for x in [cfg.primary_geography,'demand_sector', 'efficiency_type', 'supply_node','resource_bin'] if x in self.values.index.names])
            self.values = self.values.sort()
            
    def convert(self):
        """
        return raw_values that are converted to units consistent with output units for 
        normalized efficiency values
        
        """
        self.values = util.unit_convert(self.raw_values, unit_from_num=self.input_unit, unit_to_num=self.output_unit)


class SupplyStockNode(Node):
    def __init__(self, id, supply_type, scenario, **kwargs):
        Node.__init__(self, id, supply_type, scenario)
        for col, att in util.object_att_from_table('SupplyNodes', id):
            setattr(self, col, att)
        self.potential = SupplyPotential(self.id, self.enforce_potential_constraint, self.scenario)
        self.technologies = {}
        self.tech_ids = []
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
        if self.stock.data is True:
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
        if self.potential.data is True:
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
        if self.id == self.distribution_grid_node_id and 'demand_sector' not in self.stock.rollover_group_names:
            #requires distribution grid node to maintain demand sector resolution in its stocks
            self.stock.rollover_group_levels.append(self.demand_sectors)
            self.stock.rollover_group_names.append('demand_sector')
        elif self.id == self.distribution_grid_node_id:
            original_levels = self.stock.rollover_group_levels[self.stock.rollover_group_names.index('demand_sector')]
            new_levels = list(set(original_levels+self.demand_sectors))
            self.stock.rollover_group_levels[self.stock.rollover_group_names.index('demand_sector')] = new_levels
        self.stock.rollover_group_names = [cfg.primary_geography] + self.stock.rollover_group_names
        self.stock.rollover_group_levels = [cfg.geo.geographies[cfg.primary_geography]] + self.stock.rollover_group_levels
        
    def add_stock(self):
        """add stock instance to node"""
        self.stock = Stock(id=self.id, drivers=None,sql_id_table='SupplyStock', sql_data_table='SupplyStockData', primary_key='supply_node_id', scenario=self.scenario)
        self.stock.input_type = 'total'

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
        levels = self.stock.rollover_group_levels + [self.years] + [self.tech_ids]
        names = self.stock.rollover_group_names + ['year'] + ['supply_technology']
        index = pd.MultiIndex.from_product(levels,names=names)
        if self.stock.data is True and 'supply_technology' in self.stock.raw_values.index.names:
            #remap to technology stocks
            self.stock.years = self.years
            self.stock.remap(map_from='raw_values', map_to='technology',fill_timeseries=True, fill_value=np.nan)
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
                    raise ValueError("technology stock indices in node %s do not match input energy system stock data" %self.id)
                else:
                    #if the previous test is passed, we use the reference stock to fill in the Nans of the case stock
                    self.case_stock.technology = self.case_stock.technology.reorder_levels(names)                    
                    self.case_stock.technology = self.case_stock.technology.reindex(index)
                    self.stock.technology = self.case_stock.technology.fillna(self.stock.technology)
            self.stock.technology = self.stock.technology.unstack('year')
            self.stock.technology.columns = self.stock.technology.columns.droplevel() 
            self.stock.technology = util.reindex_df_level_with_new_elements(self.stock.technology,'supply_technology',self.tech_ids)
        elif hasattr(self.case_stock,'technology'):
                # if there are levels in the case specific stock that are not in the rollover groups, we must remove that level from the case stock
                mismatched_levels = [x for x in self.case_stock.technology.index.names if x not in names]
                if len(mismatched_levels):
                    self.case_stock.technology = util.remove_df_levels(self.case_stock.technology,mismatched_levels)
                #if there are still level mismatches, it means the rollover has more levels, which returns an error
                if len([x for x in self.stock.rollover_group_names if x not in self.case_stock.technology.index.names]) :
                    raise ValueError("technology stock levels in node %s do not match other node input data" %self.id)
                else:
                    #if the previous test is passed we reindex the case stock for unspecified technologies
                    self.case_stock.technology = self.case_stock.technology.reorder_levels(names)
                    structure_df = pd.DataFrame(1,index=index,columns=['value'])
                    self.case_stock.technology = self.case_stock.technology.reindex(index)
                    self.stock.technology = self.case_stock.technology
                self.stock.technology = self.stock.technology.unstack('year')
                self.stock.technology.columns = self.stock.technology.columns.droplevel() 
                self.stock.technology = util.reindex_df_level_with_new_elements(self.stock.technology,'supply_technology',self.tech_ids)
        else: 
            levels = self.stock.rollover_group_levels  + [self.tech_ids]
            names = self.stock.rollover_group_names + ['supply_technology']
            index = pd.MultiIndex.from_product(levels,names=names)
            self.stock.technology = util.empty_df(index=index,columns=self.years,fill_value=np.NaN)

        if self.stock.data is True and 'supply_technology' not in self.stock.raw_values.index.names:
            levels = self.stock.rollover_group_levels + [self.years]
            names = self.stock.rollover_group_names + ['year'] 
            index = pd.MultiIndex.from_product(levels,names=names)
            structure_df = pd.DataFrame(1,index=index,columns=['value'])
            self.stock.remap(map_from='raw_values', map_to='total', time_index = self.years,fill_timeseries=True, fill_value=np.nan)
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
                    raise ValueError("total stock indices in node %s do not match input energy system stock data" %self.id)
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
                    raise ValueError("total stock levels in node %s do not match other node input data" %self.id)
                else:
                    self.case_stock.total= self.case_stock.total.reorder_levels(names)                    
                    self.case_stock.total = self.case_stock.total.reindex(index)
                    self.stock.total = self.case_stock.total
                    self.stock.total = self.stock.total.unstack('year')
                    self.stock.total.columns = self.stock.total.columns.droplevel() 
        else:
             index = pd.MultiIndex.from_product(self.stock.rollover_group_levels,names=self.stock.rollover_group_names)
             self.stock.total = util.empty_df(index=index,columns=self.years,fill_value=np.NaN)       
        if self.stock.data or hasattr(self.case_stock,'data') and self.case_stock.data == True:
            self.stock.data = True
        self.max_total()
        self.format_rollover_stocks()
   
    def max_total(self):
        tech_sum = util.remove_df_levels(self.stock.technology,'supply_technology')
#        self.stock.total = self.stock.total.fillna(tech_sum)
        if hasattr(self.stock,'total'):
            self.stock.total[self.stock.total<tech_sum] = tech_sum
        else:
#            self.stock.total = tech_sum 
            self.stock.total = pd.DataFrame(np.nan, tech_sum.index,tech_sum.columns)
                
    def format_rollover_stocks(self):
        #transposed technology stocks are used for entry in the stock rollover function
        self.stock.technology_rollover = self.stock.technology.stack(dropna=False)
        util.replace_index_name(self.stock.technology_rollover,'year')
        self.stock.total_rollover = util.remove_df_levels(self.stock.technology_rollover,'supply_technology')
        self.stock.technology_rollover=self.stock.technology_rollover.unstack('supply_technology')
        for tech_id in self.tech_ids:
            if tech_id not in self.stock.technology_rollover.columns:
                self.stock.technology_rollover[tech_id]=np.nan

    def add_case_stock(self):
       self.case_stock = StockItem()
       tech_stocks = []
       for technology in self.technologies.values():
           for stock in technology.specified_stocks.values():
               if stock.values is not None:
                   stock.values['supply_technology'] = technology.id
                   stock.values.set_index('supply_technology', append=True, inplace=True) 
                   tech_stocks.append(stock.values)
       if len(tech_stocks):
            self.case_stock.data = True
            self.case_stock.technology = util.DfOper.add(tech_stocks, expandable=False)
            self.case_stock.technology[self.case_stock.technology.index.get_level_values('year')<int(cfg.cfgfile.get('case','current_year'))] = np.nan
       total_stocks = []
       for stock in self.total_stocks.values():
            if stock.values is not None:
                self.case_stock.data = True
                total_stocks.append(stock.values)
       if len(total_stocks):    
           self.case_stock.total = DfOper.add(total_stocks, expandable=False)
           self.case_stock.total[self.case_stock.total.index.get_level_values('year')<int(cfg.cfgfile.get('case','current_year'))] = np.nan
#       elif len(tech_stocks):
#           self.case_stock.total = util.remove_df_levels(self.case_stock.technology,'supply_technology')
        
            
    def remap_tech_attrs(self, attr_classes, attr='values'):
        """
        loops through attr_classes (ex. capital_cost, energy, etc.) in order to map technologies
        that reference other technologies in their inputs (i.e. technology A is 150% of the capital cost technology B)
        """
        attr_classes = util.ensure_iterable_and_not_string(attr_classes)
        for technology in self.technologies.keys():
            for attr_class in attr_classes:
                self.remap_tech_attr(technology, attr_class, attr)

    def remap_tech_attr(self, technology, class_name, attr):
        """
        map reference technology values to their associated technology classes
        
        """
        tech_class = getattr(self.technologies[technology], class_name)
        if hasattr(tech_class, 'reference_tech_id'):
            if getattr(tech_class, 'reference_tech_id'):
                ref_tech_id = (getattr(tech_class, 'reference_tech_id'))
                if not self.technologies.has_key(ref_tech_id):
                    raise ValueError("supply node {} has no technology {} to serve as a reference for technology {} in attribute {}".format(self.id, ref_tech_id, technology, class_name))
                ref_tech_class = getattr(self.technologies[ref_tech_id], class_name)
                # converted is an indicator of whether an input is an absolute
                # or has already been converted to an absolute
                if not getattr(ref_tech_class, 'absolute'):
                    # If a technnology hasn't been mapped, recursion is used
                    # to map it first (this can go multiple layers)
                    self.remap_tech_attr(getattr(tech_class, 'reference_tech_id'), class_name, attr)
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
                tech_attributes = vars(getattr(self.technologies[ref_tech_id], class_name))
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
        ids = util.sql_read_table('SupplyTechs',column_names='id',supply_node_id=self.id,return_iterable=True)
        for id in ids:
            self.add_technology(id)

    def add_nodes(self):
        self.nodes = []
        for technology in self.technologies.values():
            if hasattr(technology,'efficiency') and technology.efficiency.raw_values is not None:
                for value in technology.efficiency.values.index.get_level_values('supply_node'):
                    self.nodes.append(value)
        self.nodes = list(set(self.nodes))

    def add_technology(self, id, **kwargs):
        """
        Adds technology instances to node
        """
        if id in self.technologies:
            # ToDo note that a technology was added twice
            return
        self.technologies[id] = SupplyTechnology(id, self.cost_of_capital, self.scenario, **kwargs)
        self.tech_ids.append(id)
        self.tech_ids.sort()
     
    def calculate_stock_measures(self):
        for technology in self.technologies.values():
           for stock in technology.specified_stocks.values():
               stock.calculate(self.vintages,self.years)
               stock.convert()
        for stock in self.total_stocks.values():
            stock.calculate(self.vintages,self.years)
            stock.convert()
    
    def calculate_sales_shares(self):
        for tech in self.tech_ids:
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
        for tech in self.tech_ids:
            technology = self.technologies[tech]
            technology.calculate_sales('reference_sales')
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
            ss_reference = SalesShare.scale_reference_array_to_gap( np.tile(np.eye(len(self.tech_ids)), (len(self.years), 1, 1)), space_for_reference)        
            #sales shares are always 1 with only one technology so the default can be used as a reference
            if len(self.tech_ids)>1 and np.sum(ss_measure)<1:
                reference_sales_shares = False
            else:
                reference_sales_shares = True
        else:
            reference_sales_shares = True
        # return SalesShare.normalize_array(ss_reference+ss_measure, retiring_must_have_replacement=True)
        # todo make retiring_must_have_replacement true after all data has been put in db
        return SalesShare.normalize_array(ss_reference + ss_measure, retiring_must_have_replacement=False),reference_sales_shares                       
    
    def calculate_total_sales_share_after_initial(self, elements, levels):
        ss_measure = self.helper_calc_sales_share(elements, levels, reference=False)
        space_for_reference = 1 - np.sum(ss_measure, axis=1)        
        ss_reference = SalesShare.scale_reference_array_to_gap( np.tile(np.eye(len(self.tech_ids)), (len(self.years), 1, 1)), space_for_reference)        
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
        num_techs = len(self.tech_ids)
        tech_lookup = dict(zip(self.tech_ids, range(num_techs)))
        num_years = len(self.years)
        # ['vintage', 'replacing tech id', 'retiring tech id']
        ss_array = np.empty(shape=(num_years, num_techs))
        ss_array.fill(np.nan)
        # tech_ids must be sorted
        # normalize ss in one of two ways
        if reference:
            for tech_id in self.tech_ids:
                for sales in self.technologies[tech_id].reference_sales.values():
                    repl_index = tech_lookup[tech_id]
                    # technology sales share dataframe may not have all elements of stock dataframe
                    sales.values.index.levels
                    if any([element not in sales.values.index.levels[
                        util.position_in_index(sales.values, level)] for element, level in
                            zip(elements, levels)]):
                        continue
                    ss_array[:, repl_index] = util.df_slice(sales.values, elements, levels).values.T[0]
        else:
            for tech_id in self.tech_ids:
                for sales in self.technologies[tech_id].sales.values():
                    repl_index = tech_lookup[sales.supply_technology_id]
                    # TODO address the discrepancy when a demand tech is specified
                    try:
                        ss_array[:, repl_index] = util.df_slice(sales.values, elements, levels).values.T[0]
                    except:
                        ss_array[:, repl_index] = util.df_slice(sales.values, elements, levels).values.flatten()
        return ss_array

    def helper_calc_sales_share(self, elements, levels, reference, space_for_reference=None):
        num_techs = len(self.tech_ids)
        tech_lookup = dict(zip(self.tech_ids, range(num_techs)))
        num_years = len(self.years)
        # ['vintage', 'replacing tech id', 'retiring tech id']
        ss_array = np.zeros(shape=(num_years, num_techs, num_techs))
        # tech_ids must be sorted
        # normalize ss in one of two ways
        if reference:
            for tech_id in self.tech_ids:
                for sales_share in self.technologies[tech_id].reference_sales_shares.values():
                    if set(sales_share.values.index.names).issubset(self.stock.sales_share_reconcile.index.names) and set(sales_share.values.index.names)!=set(self.stock.sales_share_reconcile.index.names):
                        sales_share.values = DfOper.none([sales_share.values,self.stock.sales_share_reconcile],non_expandable_levels=None)
                    repl_index = tech_lookup[tech_id]
                    reti_index = slice(None)
                    # technology sales share dataframe may not have all elements of stock dataframe
                    ss_array[:, repl_index, reti_index] += util.df_slice(sales_share.values, elements, levels).values
            ss_array = SalesShare.scale_reference_array_to_gap(ss_array, space_for_reference)
        else:
            for tech_id in self.tech_ids:
                for sales_share in self.technologies[tech_id].sales_shares.values():
                    if set(sales_share.values.index.names).issubset(self.stock.sales.index.names) and set(sales_share.values.index.names)!=set(self.stock.sales.index.names):
                        sales_share.values = util.DfOper.none([sales_share.values,util.remove_df_levels(self.stock.sales_exist,'supply_technology')],non_expandable_levels=None)
                    repl_index = tech_lookup[tech_id]
                    repl_index = tech_lookup[sales_share.supply_technology_id]
                    reti_index = tech_lookup[
                        sales_share.replaced_supply_technology_id] if sales_share.replaced_supply_technology_id is not None and tech_lookup.has_key(
                        sales_share.replaced_supply_technology_id) else slice(None)
                    if sales_share.replaced_supply_technology_id is not None and not tech_lookup.has_key(sales_share.replaced_supply_technology_id):
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
            for tech_id in self.tech_ids:
                technology = self.technologies[tech_id]
                functions[fun].append(getattr(technology, fun))
            setattr(self.stock, fun, pd.DataFrame(np.array(functions[fun]).T, columns=self.tech_ids))

    def create_rollover_markov_matrices(self):
        vintaged_markov = util.create_markov_vector(self.stock.decay_vintaged.values,
                                                    self.stock.survival_vintaged.values)
        self.stock.vintaged_markov_matrix = util.create_markov_matrix(vintaged_markov, len(self.tech_ids),
                                                                      len(self.years))

        initial_markov = util.create_markov_vector(self.stock.decay_initial_stock.values, self.stock.survival_initial_stock.values)
        self.stock.initial_markov_matrix = util.create_markov_matrix(initial_markov, len(self.tech_ids),
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
            
            sales_share, initial_sales_share = self.calculate_total_sales_share(elements,
                                                           self.stock.rollover_group_names)  # group is not necessarily the same for this other dataframe
            if np.any(np.isnan(sales_share)):
                raise ValueError('Sales share has NaN values in node ' + str(self.id))
            sales = self.calculate_total_sales(elements, self.stock.rollover_group_names)
            initial_total = util.df_slice(self.stock.total_rollover, elements, self.stock.rollover_group_names).values[0]
            initial_stock, rerun_sales_shares = self.calculate_initial_stock(elements, initial_total, sales_share,initial_sales_share)
            if rerun_sales_shares:
                 sales_share = self.calculate_total_sales_share_after_initial(elements,self.stock.rollover_group_names)
            technology_stock = self.stock.return_stock_slice(elements, self.stock.rollover_group_names,'technology_rollover').values
            self.rollover_dict[elements] = Rollover(vintaged_markov_matrix=self.stock.vintaged_markov_matrix,
                                     initial_markov_matrix=self.stock.initial_markov_matrix,
                                     num_years=len(years), num_vintages=len(years),
                                     num_techs=len(self.tech_ids), initial_stock=initial_stock,
                                     sales_share=sales_share, stock_changes=None, specified_sales=sales,
                                     specified_stock=technology_stock, specified_retirements=None,stock_changes_as_min=True)
#            if self.id == 115:
#                print self.rollover_dict[(64,)].i
#                print self.rollover_dict[(64,)].sales_share[0]
#                print self.rollover_dict[(64,)].initial_stock, self.rollover_dict[(64,)].stock.sum()

        for year in [x for x in self.years if x<int(cfg.cfgfile.get('case', 'current_year'))]:
            for elements in self.rollover_groups.keys():
                elements = util.ensure_tuple(elements)
                try:
                    self.rollover_dict[elements].run(1)
                except:
                    logging.error('error encountered in rollover for node ' + str(self.id) + ' in elements '+ str(elements) + ' year ' + str(year))
                    raise
                stock, stock_new, stock_replacement, retirements, retirements_natural, retirements_early, sales_record, sales_new, sales_replacement = self.rollover_dict[(elements)].return_formatted_outputs(year_offset=0)           
                self.stock.values.loc[elements, year], self.stock.values_new.loc[elements, year], self.stock.values_replacement.loc[
                elements,year] = stock, stock_new, stock_replacement 
                full_levels = [[x] for x in elements] + [self.tech_ids] + [[year]]
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
        if min(self.years) == int(cfg.cfgfile.get('case', 'current_year')) ==year:
            for elements in self.rollover_groups.keys():    
                elements = util.ensure_tuple(elements)
                sales_share, initial_sales_share = self.calculate_total_sales_share(elements,self.stock.rollover_group_names)  # group is not necessarily the same for this other dataframe
                if np.any(np.isnan(sales_share)):
                    raise ValueError('Sales share has NaN values in node ' + str(self.id))
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
                logging.error('error encountered in rollover for node ' + str(self.id) + ' in elements '+ str(elements) + ' year ' + str(year))
                raise
            stock, stock_new, stock_replacement, retirements, retirements_natural, retirements_early, sales_record, sales_new, sales_replacement = self.rollover_dict[(elements)].return_formatted_outputs(year_offset=0)
            self.stock.values.loc[elements, year], self.stock.values_new.loc[elements, year], self.stock.values_replacement.loc[
                elements,year] = stock, stock_new, stock_replacement 
            full_levels = [[x] for x in elements] + [self.tech_ids] + [[year]]
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
                    full_levels = [[x] for x in elements] + [self.tech_ids] + [[year]]
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
        for year in self.years:
            self.stock.capacity_factor.loc[:,year] = self.rollover_output(tech_class='capacity_factor',stock_att='ones',year=year, non_expandable_levels=None,fill_value=1.0)
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
        if year == int(cfg.cfgfile.get('case','current_year')) and loop == 'initial':
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
        self.stock.values_energy.loc[:, year] = DfOper.mult([self.stock.capacity_factor.loc[:,year].to_frame(), self.stock.values.loc[:,year].to_frame()]) * util.unit_conversion(unit_from_den=cfg.cfgfile.get('case','time_step'), unit_to_den='year')[0]

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
                if year == int(cfg.cfgfile.get('case','current_year')) and loop == 1:
                    self.rollover_dict[elements].rewind(1)
                self.stock.remaining.loc[element_indexer, year] = self.rollover_dict[elements].return_formatted_stock(year_offset=1)
            else:
                self.rollover_dict[elements].rewind(1)
                self.stock.preview.loc[element_indexer,year] = self.rollover_dict[elements].return_formatted_stock(year_offset=0)
        self.set_energy_capacity_ratios(year,loop)
   
    def set_energy_capacity_ratios(self,year,loop):
       if loop == 1 or loop == 'initial':
            self.stock.act_rem_energy = DfOper.mult([self.stock.remaining.loc[:,year].to_frame(),self.stock.capacity_factor.loc[:,year].to_frame()]) * util.unit_conversion(unit_from_den=cfg.cfgfile.get('case', 'time_step'), unit_to_den='year')[0]
            exist_cap_factor = self.stock.capacity_factor.loc[:,year].to_frame()
            exist_cap_factor[exist_cap_factor==0]=np.nan
            default_conversion = exist_cap_factor.groupby(level=self.stock.rollover_group_names).mean().fillna(1)*util.unit_conversion(unit_from_num='year',unit_to_num=cfg.cfgfile.get('case', 'time_step'))[0]                
            default_conversion[default_conversion==0] = 1                
            self.stock.act_energy_capacity_ratio = util.DfOper.divi([util.remove_df_levels(self.stock.act_rem_energy,['vintage','supply_technology']),
                                                                    util.remove_df_levels(self.stock.remaining.loc[:, year].to_frame(),['vintage','supply_technology'])]).fillna(default_conversion)
            self.stock.act_energy_capacity_ratio[self.stock.act_energy_capacity_ratio==0] = default_conversion         
       else:
           preview = util.df_slice(self.stock.preview.loc[:,year].to_frame(), year, 'vintage')
           preview_energy = util.DfOper.mult([preview,util.df_slice(self.stock.capacity_factor.loc[:,year].to_frame(),year,'vintage')])*util.unit_conversion(unit_from_den=cfg.cfgfile.get('case', 'time_step'), unit_to_den='year')[0]
           preview = util.remove_df_levels(preview,['vintage','supply_technology'])
           preview_energy = util.remove_df_levels(preview_energy,['vintage','supply_technology'])        
           exist_cap_factor = DfOper.divi([DfOper.mult([self.stock.capacity_factor.loc[:,year].to_frame(),self.stock.values.loc[:,year].to_frame()]).groupby(level=self.stock.rollover_group_names).sum(),self.stock.values.loc[:,year].to_frame().groupby(level=self.stock.rollover_group_names).sum()])
           exist_cap_factor[exist_cap_factor==0]=np.nan          
           default_conversion = exist_cap_factor.fillna(1)*util.unit_conversion(unit_from_num='year',unit_to_num=cfg.cfgfile.get('case', 'time_step'))[0]
           default_conversion[default_conversion==0] = 1   
           self.stock.act_rem_energy = util.DfOper.mult([self.stock.remaining.loc[:,year].to_frame(),self.stock.capacity_factor.loc[:,year].to_frame()]) * util.unit_conversion(unit_from_den=cfg.cfgfile.get('case', 'time_step'), unit_to_den='year')[0]
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
        if self.potential.data is False:
            if self.throughput is not None:
                self.stock.requirement_energy.loc[:,year] = self.throughput
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
            df = util.remove_df_elements(self.potential.values,[x for x in cfg.geo.geographies_unfiltered[cfg.primary_geography] if x not in cfg.geographies],cfg.primary_geography)
            bins = util.DfOper.subt([df[year].to_frame(), self.stock.act_total_energy],expandable=(False,False), collapsible=(True,True))
            bins = bins.reset_index().set_index(bins.index.names)
            bins[bins<0] = 0
            #calculates the supply curve of remaining energy
            bin_supply_curve = bins.groupby(level=[x for x in self.stock.rollover_group_names if x!= 'resource_bin']).cumsum()
            #expands the total energy needed to distribute to mask against the supply curve. Used as a cap on the supply curve. 
            total_residual = util.expand_multi(total_residual,bins.index.levels,bins.index.names)
            bin_supply_curve[bin_supply_curve>total_residual] = total_residual
            try:
                bin_supply_curve = bin_supply_curve.groupby(level=util.ix_excl(bin_supply_curve,'resource_bin')).diff().fillna(bin_supply_curve)
                self.stock.requirement_energy.loc[:,year] = util.DfOper.add([self.stock.act_total_energy, bin_supply_curve])
                self.stock.requirement.loc[:,year] = util.DfOper.divi([self.stock.requirement_energy.loc[:,year].to_frame(),self.stock.act_energy_capacity_ratio])
            except:
                pdb.set_trace()
        if year == int(cfg.cfgfile.get('case','current_year')) and year==min(self.years):
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
#        if self.potential.data is False:    
        self.stock.requirement.loc[:,year] = self.stock.act_total
        if year == int(cfg.cfgfile.get('case','current_year')) and year==min(self.years):
            self.stock.act_stock_changes = self.stock.requirement[year].to_frame()*0
        else:
            #stock changes only equal capacity added from the dispatch
            self.stock.act_stock_changes = util.DfOper.subt([self.stock.requirement.loc[:,year].to_frame(),
                                                        util.remove_df_levels(self.stock.values[previous_year].to_frame(),['vintage','supply_technology'])])
#        else:
#            self.stock.act_stock_changes = DfOper.subt([self.stock.requirement[year].to_frame(),util.remove_df_levels(self.stock.act_rem,'supply_technology')])
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
        tech_dfs = [self.reformat_tech_df(self.stock.sales, tech, tech_class=None, tech_att='book_life_matrix', tech_id=tech.id, year=year) for
            tech in self.technologies.values()]
        tech_df = pd.concat(tech_dfs)
        # initial_stock_df uses the stock values dataframe and removes vintagesot
        initial_stock_df = self.stock.values[min(self.years)]
        # formats tech dfs to match stock df
        initial_tech_dfs = [self.reformat_tech_df(initial_stock_df, tech, tech_class=None, tech_att='initial_book_life_matrix',tech_id=tech.id, year=year) for tech in self.technologies.values()]
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
        
    def  calculate_per_unit_costs(self,year):        
            total_costs = util.remove_df_levels(self.levelized_costs.loc[:,year].to_frame(),['vintage', 'supply_technology'])
            self.embodied_cost.loc[:,year] = DfOper.divi([total_costs, self.active_supply],expandable=(False,False)).replace([np.inf,np.nan,-np.nan],[0,0,0])        
            self.active_embodied_cost = util.expand_multi(self.embodied_cost[year].to_frame(), levels_list = [cfg.geo.geographies[cfg.primary_geography], self.demand_sectors],levels_names=[cfg.primary_geography,'demand_sector'])

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
            self.active_dispatch_costs = self.active_dispatch_costs.stack([cfg.primary_geography,'demand_sector'])
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
        else:
            index = self.rollover_output(tech_class='efficiency',stock_att='values_normal_energy',year=year).index
            self.stock.coefficients = util.empty_df(index, columns=self.years,fill_value=0.)
            self.stock.coefficients.loc[:,year] = self.rollover_output(tech_class='efficiency',stock_att='values_normal_energy',year=year)
        
        if 'supply_node' not in self.stock.coefficients.index.names:
            print ("no efficiency has been input for technologies in the %s supply node" %self.name)
            index = pd.MultiIndex.from_product([self.id,cfg.geographies],names = ['supply_node', cfg.primary_geography],)
            columns = [year]
            self.stock.coefficients = pd.DataFrame(0, index=index, columns = columns)
        if 'demand_sector' not in self.stock.rollover_group_names:
            keys = self.demand_sectors
            name = ['demand_sector']
            self.active_coefficients = util.remove_df_levels(pd.concat([self.stock.coefficients.loc[:,year].to_frame()]*len(keys), keys=keys,names=name).fillna(0),['supply_technology', 'vintage','resource_bin'])
            self.active_coefficients_untraded = copy.deepcopy(self.active_coefficients)
            self.active_coefficients_untraded.sort(inplace=True,axis=0)
            self.active_coefficients_total_untraded = util.remove_df_levels(self.active_coefficients,['efficiency_type']).reorder_levels([cfg.primary_geography,'demand_sector', 'supply_node']).sort().fillna(0)
        else:            
            self.active_coefficients = util.remove_df_levels(self.stock.coefficients.loc[:,year].to_frame().fillna(0),['supply_technology', 'vintage','resource_bin'])
            self.active_coefficients_untraded = copy.deepcopy(self.active_coefficients)
            self.active_coefficients_untraded.sort(inplace=True,axis=0)         
            self.active_coefficients_total_untraded = util.remove_df_levels(self.active_coefficients,['efficiency_type']).reorder_levels([cfg.primary_geography,'demand_sector', 'supply_node']).sort().fillna(0)
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
            self.active_emissions_coefficients = self.active_emissions_coefficients.reorder_levels([cfg.primary_geography,'demand_sector', 'supply_node', 'efficiency_type', 'ghg'])
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
                self.stock.dispatch_coefficients.loc[:,year] = self.rollover_output(tech_class='efficiency',
                                                                             stock_att='exist',year=year)                     
            self.active_dispatch_coefficients = self.stock.dispatch_coefficients.loc[:,year].to_frame()                        
            self.active_dispatch_coefficients= util.remove_df_levels(self.active_dispatch_coefficients,['efficiency_type'])

    def calculate_capacity_utilization(self,energy_supply,supply_years):
        energy_stock = self.stock.values[supply_years] * util.unit_convert(1,unit_from_den='hour', unit_to_den='year')
        self.capacity_utilization = util.DfOper.divi([energy_supply,energy_stock],expandable=False).replace([np.inf,np.nan,-np.nan],[0,0,0])    
        
        
        
    def rollover_output(self, tech_class=None, tech_att='values', stock_att=None, year=None, non_expandable_levels=('year', 'vintage'),fill_value=0.0):
        """ Produces rollover outputs for a node stock based on the tech_att class, att of the class, and the attribute of the stock
        """
        stock_df = getattr(self.stock, stock_att)     
        stock_df = stock_df.sort()
        tech_classes = util.put_in_list(tech_class)
        tech_dfs = []
        for tech_class in tech_classes:
            tech_dfs += ([self.reformat_tech_df(stock_df, tech, tech_class, tech_att, tech.id, year) for tech in
                        self.technologies.values() if
                            hasattr(getattr(tech, tech_class), tech_att) and getattr(getattr(tech, tech_class),tech_att) is not None])
        if len(tech_dfs):
            first_tech_order = tech_dfs[0].index.names
            tech_df = pd.concat([x.reorder_levels(first_tech_order) for x in tech_dfs])
            tech_df = tech_df.reorder_levels([x for x in stock_df.index.names if x in tech_df.index.names]+ [x for x in tech_df.index.names if x not in stock_df.index.names])
            tech_df = tech_df.sort()            
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

    def reformat_tech_df(self, stock_df, tech, tech_class, tech_att, tech_id, year):
        """
        reformat technology dataframes for use in stock-level dataframe operations
        """
        if tech_class is None:
            tech_df = getattr(tech, tech_att)
        else:
            tech_df = getattr(getattr(tech, tech_class), tech_att)         
        if 'supply_technology' not in tech_df.index.names:
            tech_df['supply_technology'] = tech_id
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
    def __init__(self, id, supply_type, scenario, **kwargs):
        SupplyStockNode.__init__(self, id, supply_type, scenario, **kwargs)
    
    def add_technology(self, id, **kwargs):
        """
        Adds technology instances to node
        """
        if id in self.technologies:
            # ToDo note that a technology was added twice
            return
        self.technologies[id] = StorageTechnology(id, self.cost_of_capital, self.scenario, **kwargs)
        self.tech_ids.append(id)
        self.tech_ids.sort()

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
            tech_indexer = util.level_specific_indexer(self.stock.values_financial_new,'supply_technology', tech.id)
            self.stock.values_financial_new_energy.loc[tech_indexer,:] = self.stock.values_financial_new.loc[tech_indexer,year].to_frame() * tech.discharge_duration
            self.stock.values_financial_replacement_energy.loc[tech_indexer,:] = self.stock.values_financial_replacement.loc[tech_indexer,year].to_frame() * tech.discharge_duration
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
        self.active_embodied_cost = util.expand_multi(self.embodied_cost[year].to_frame(), levels_list = [cfg.geo.geographies[cfg.primary_geography], self.demand_sectors],levels_names=[cfg.primary_geography,'demand_sector'])

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
        
        self.stock.values_normal_tech = self.stock.values.loc[:,year].to_frame().groupby(level=[cfg.primary_geography,'supply_technology']).transform(lambda x: x/x.sum())
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
            self.active_dispatch_coefficients = self.stock.dispatch_coefficients.loc[:,year].to_frame().groupby(level=[cfg.primary_geography,'supply_node','supply_technology']).sum()
            self.active_dispatch_coefficients= util.remove_df_levels(self.active_dispatch_coefficients,['efficiency_type'])

        
class ImportNode(Node):
    def __init__(self, id, supply_type, scenario, **kwargs):
        Node.__init__(self,id, supply_type, scenario)
        self.cost = ImportCost(self.id, scenario)
        self.potential = SupplyPotential(self.id, self.enforce_potential_constraint, self.scenario)
        self.coefficients = SupplyCoefficients(self.id, self.scenario)

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
        if hasattr(self,'cost') and self.cost.data is True:
            if hasattr(self,'potential') and self.potential.data is True and self.cost.cost_method == 'average':
                self.active_embodied_cost = self.calculate_avg_costs(year)
            elif hasattr(self,'potential') and self.potential.data is True and self.cost.cost_method == 'marginal': 
                self.active_embodied_cost = self.calculate_marginal_costs(year)
            else:
                allowed_indices = ['demand_sector', cfg.primary_geography]
                if set(self.cost.values.index.names).issubset(allowed_indices):
                    self.active_embodied_cost = self.cost.values.loc[:,year].to_frame()
                    self.active_embodied_cost = util.expand_multi(self.active_embodied_cost, levels_list = [cfg.geo.geographies[cfg.primary_geography], self.demand_sectors],levels_names=[cfg.primary_geography,'demand_sector'])
                else:
                    raise ValueError("too many indexes in cost inputs of node %s" %self.id)
            self.levelized_costs.loc[:,year] = DfOper.mult([self.active_embodied_cost,self.active_supply]).values
    
    def calculate_annual_costs(self,year):
        if hasattr(self,'active_embodied_cost'):
            self.annual_costs.loc[:,year] = DfOper.mult([self.active_embodied_cost,self.active_supply]).values
        if year == int(cfg.cfgfile.get('case', 'end_year')):
            self.final_annual_costs = self.annual_costs


    
    def calculate_avg_costs(self,year):
        filter_geo_potential_normal = util.remove_df_elements(self.potential.active_supply_curve_normal, [x for x in cfg.geo.geographies_unfiltered[cfg.primary_geography] if x not in cfg.geographies],cfg.primary_geography)
        filter_geo_potential_normal = filter_geo_potential_normal.reset_index().set_index(filter_geo_potential_normal.index.names)
        supply_curve = filter_geo_potential_normal
        supply_curve = supply_curve[supply_curve.values>0]
        supply_curve = util.DfOper.mult([util.DfOper.divi([self.potential.values.loc[:,year].to_frame(),
                                                           util.remove_df_levels(self.potential.values.loc[:,year].to_frame(),[x for x in self.potential.values.index.names if x not in ['demand_sector',cfg.primary_geography,'resource_bin']])]),
                                                        supply_curve])
        cost = util.DfOper.mult([supply_curve,self.cost.values.loc[:,year].to_frame()])
        levels = ['demand_sector',cfg.primary_geography]
        cost = cost.groupby(level = [x for x in levels if x in cost.index.names]).sum()
        return  util.expand_multi(cost, levels_list = [cfg.geo.geographies[cfg.primary_geography], self.demand_sectors],
                                                                                                                            levels_names=[cfg.primary_geography,'demand_sector']).replace([np.nan,np.inf],0)
                                                                                                                            
                                                                                                                            
    def calculate_marginal_costs(self,year):
        filter_geo_potential_normal = util.remove_df_elements(self.potential.active_supply_curve_normal, [x for x in cfg.geo.geographies_unfiltered[cfg.primary_geography] if x not in cfg.geographies],cfg.primary_geography)
        filter_geo_potential_normal = filter_geo_potential_normal.reset_index().set_index(filter_geo_potential_normal.index.names)
        supply_curve = filter_geo_potential_normal
        supply_curve = supply_curve[supply_curve.values>0]
        supply_curve = util.DfOper.mult([util.DfOper.divi([self.potential.values.loc[:,year].to_frame(),
                                                           util.remove_df_levels(self.potential.values.loc[:,year].to_frame(),[x for x in self.potential.values.index.names if x not in ['demand_sector',cfg.primary_geography,'resource_bin']])]),
                                                        supply_curve])
        supply_curve[supply_curve.values>0] = 1
        cost = util.DfOper.mult([supply_curve,self.cost.values.loc[:,year].to_frame()])
        levels = ['demand_sector',cfg.primary_geography]
        tradable_levels = ['demand_sector',self.tradable_geography]
        map_df = cfg.geo.map_df(cfg.primary_geography,self.tradable_geography,normalize_as='total',eliminate_zeros=False,filter_geo=False)
        traded_cost = util.DfOper.mult([cost,map_df])
        traded_cost = traded_cost.groupby(level=[x for x in tradable_levels if x in traded_cost.index.names]).transform(lambda x: x.max())
        cost = traded_cost.groupby(level = [x for x in levels if x in cost.index.names]).max()
        return  util.expand_multi(cost, levels_list = [cfg.geo.geographies[cfg.primary_geography], self.demand_sectors],
                                                                                                                            levels_names=[cfg.primary_geography,'demand_sector']).replace([np.nan,np.inf],0)



class ImportCost(Abstract):
    def __init__(self, id, scenario, **kwargs):
        self.id = id
        self.scenario = scenario
        self.input_type = 'intensity'
        self.sql_id_table = 'ImportCost'
        self.sql_data_table = 'ImportCostData'
        Abstract.__init__(self, self.id, 'import_node_id')
        
    def calculate(self, years, demand_sectors):
        self.years = years
        self.demand_sectors = demand_sectors
        if self.data is True:
            self.remap()
            self.convert()

    def convert(self):
        """
        return cost values converted to model energy and currency unit

        """
        self.values = util.currency_convert(self.values, self.currency_id, self.currency_year_id)
        self.values = util.unit_convert(self.values, unit_from_den=self.denominator_unit,
                                        unit_to_den=cfg.calculation_energy_unit)
        self.values = self.values.unstack(level='year')    
        self.values.columns = self.values.columns.droplevel()

          
class PrimaryNode(Node):
    def __init__(self, id, supply_type, scenario, **kwargs):
        Node.__init__(self,id, supply_type, scenario)
        self.potential = SupplyPotential(self.id, self.enforce_potential_constraint, self.scenario)
        self.cost = PrimaryCost(self.id, scenario)
        self.coefficients = SupplyCoefficients(self.id, self.scenario)

    def calculate(self):
        #all nodes can have potential conversions. Set to None if no data. 
        self.conversion, self.resource_unit = self.add_conversion()  
        if self.conversion is not None:
            self.conversion.calculate(self.resource_unit)    
        self.potential.calculate(self.conversion, self.resource_unit)
        self.cost.calculate(self.conversion, self.resource_unit)
        self.emissions.calculate(self.conversion, self.resource_unit)
        self.coefficients.calculate(self.years, self.demand_sectors)
        if self.coefficients.data is True:
            self.nodes = list(set(self.coefficients.values.index.get_level_values('supply_node')))
        self.set_adjustments()
        self.set_pass_through_df_dict()
        self.set_cost_dataframes()
        self.export.calculate(self.years, self.demand_sectors)

    def calculate_levelized_costs(self,year,loop):
        "calculates the embodied costs of nodes with emissions"
        if hasattr(self,'cost') and self.cost.data is True:
            if hasattr(self,'potential') and self.potential.data is True and self.cost.cost_method == 'average':
                self.active_embodied_cost = self.calculate_avg_costs(year)
            elif hasattr(self,'potential') and self.potential.data is True and self.cost.cost_method == 'marginal': 
                self.active_embodied_cost = self.calculate_marginal_costs(year)
            else:
                allowed_indices = ['demand_sector', cfg.primary_geography]
                if set(self.cost.values.index.names).issubset(allowed_indices):
                    self.active_embodied_cost = self.cost.values.loc[:,year].to_frame()
                    self.active_embodied_cost = util.expand_multi(self.active_embodied_cost, levels_list = [cfg.geo.geographies[cfg.primary_geography], self.demand_sectors],levels_names=[cfg.primary_geography,'demand_sector'])
                else:
                    raise ValueError("too many indexes in cost inputs of node %s" %self.id)
            self.levelized_costs.loc[:,year] = DfOper.mult([self.active_embodied_cost,self.active_supply]).values
    
    def calculate_annual_costs(self,year):
        if hasattr(self,'active_embodied_cost'):
            self.annual_costs.loc[:,year] = DfOper.mult([self.active_embodied_cost,self.active_supply]).values
        if year == int(cfg.cfgfile.get('case', 'end_year')):
            self.final_annual_costs = self.annual_costs

    
    def calculate_avg_costs(self,year):
        filter_geo_potential_normal = util.remove_df_elements(self.potential.active_supply_curve_normal, [x for x in cfg.geo.geographies_unfiltered[cfg.primary_geography] if x not in cfg.geographies],cfg.primary_geography)
        filter_geo_potential_normal = filter_geo_potential_normal.reset_index().set_index(filter_geo_potential_normal.index.names)
        supply_curve = filter_geo_potential_normal
        supply_curve = supply_curve[supply_curve.values>=0]
        supply_curve = util.DfOper.mult([util.DfOper.divi([self.potential.values.loc[:,year].to_frame(),
                                                           util.remove_df_levels(self.potential.values.loc[:,year].to_frame(),[x for x in self.potential.values.index.names if x not in ['demand_sector',cfg.primary_geography,'resource_bin']])]),
                                                        supply_curve])
        cost = util.DfOper.mult([supply_curve,self.cost.values.loc[:,year].to_frame()])
        levels = ['demand_sector',cfg.primary_geography]
        cost = cost.groupby(level = [x for x in levels if x in cost.index.names]).sum()
        return  util.expand_multi(cost, levels_list = [cfg.geo.geographies[cfg.primary_geography], self.demand_sectors],
                                                                                                                            levels_names=[cfg.primary_geography,'demand_sector']).replace([np.nan,np.inf],0)
                                                                                                                            
                                                                                                                            
    def calculate_marginal_costs(self,year):
        filter_geo_potential_normal = util.remove_df_elements(self.potential.active_supply_curve_normal, [x for x in cfg.geo.geographies_unfiltered[cfg.primary_geography] if x not in cfg.geographies],cfg.primary_geography)
        filter_geo_potential_normal = filter_geo_potential_normal.reset_index().set_index(filter_geo_potential_normal.index.names)
        supply_curve = filter_geo_potential_normal
        supply_curve = supply_curve[supply_curve.values>0]
        supply_curve = util.DfOper.mult([util.DfOper.divi([self.potential.values.loc[:,year].to_frame(),
                                                           util.remove_df_levels(self.potential.values.loc[:,year].to_frame(),[x for x in self.potential.values.index.names if x not in ['demand_sector',cfg.primary_geography,'resource_bin']])]),
                                                        supply_curve])
        supply_curve[supply_curve.values>0] = 1
        cost = util.DfOper.mult([supply_curve,self.cost.values.loc[:,year].to_frame()])
        levels = ['demand_sector',cfg.primary_geography]
        tradable_levels = ['demand_sector',self.tradable_geography]
        map_df = cfg.geo.map_df(cfg.primary_geography,self.tradable_geography,normalize_as='total',eliminate_zeros=False,filter_geo=False)
        traded_cost = util.DfOper.mult([cost,map_df])
        traded_cost = traded_cost.groupby(level=[x for x in tradable_levels if x in traded_cost.index.names]).transform(lambda x: x.max())
        cost = traded_cost.groupby(level = [x for x in levels if x in cost.index.names]).max()
        return  util.expand_multi(cost, levels_list = [cfg.geo.geographies[cfg.primary_geography], self.demand_sectors],
                                                                                                                            levels_names=[cfg.primary_geography,'demand_sector']).replace([np.nan,np.inf],0)
    

class PrimaryCost(Abstract):
    def __init__(self, id, scenario, node_geography=None, **kwargs):
        self.id = id
        self.scenario = scenario
        self.input_type = 'intensity'
        self.sql_id_table = 'PrimaryCost'
        self.sql_data_table = 'PrimaryCostData'
        Abstract.__init__(self, self.id, 'primary_node_id')
        
    def calculate(self, conversion, resource_unit):
        if self.data is True:
            self.conversion = conversion
            self.resource_unit=resource_unit   
            self.remap()
            self.convert()
                
    def convert(self):    
        self.values = self.values.unstack(level='year')    
        self.values.columns = self.values.columns.droplevel()
        if self.conversion is not None:
            self.energy = util.determ_energy(self.denominator_unit)
            # checks if a conversion dataframe is available
            if self.energy:
                # if input values for cost are in energy terms, converts currency to model
                # currency and converts denominator_units into model energy units. Resource values are
                # (ex. $/ton of biomass) are a result of using conversion dataframe mutliplied by values
                self.values = util.currency_convert(self.values, self.currency_id, self.currency_year_id)
                self.values = util.unit_convert(self.values, unit_from_den=self.denominator_unit,
                                                unit_to_den=cfg.calculation_energy_unit)
#                self.resource_values = DfOper.mult([self.values, self.conversion.values])
            else:
                # if input values for costs are not in energy terms, cost values must be converted to model currency
                # and resource values are a result of unit conversion to the node resource unit.
                # ex. if costs for biomass were in $/kg and the node resource unit was tons, the costs would
                # need to be converted to $/ton. Then, these values can be converted to energy by dividing the
                #  values by the conversion dataframe.
                self.values = util.currency_convert(self.values, self.currency_id, self.currency_year_id)
                self.values = util.unit_convert(self.values, unit_from_den=self.denominator_unit,
                                                         unit_to_den=self.resource_unit)
                self.values = DfOper.divi([self.values, self.conversion.values])
        else:
            # if there is no conversion necessary, a simple conversion to model currency and
            # energy units is effected
            self.values = util.currency_convert(self.values, self.currency_id, self.currency_year_id)
            self.values = util.unit_convert(self.values, unit_from_den=self.denominator_unit,
                                            unit_to_den=cfg.calculation_energy_unit)


class SupplyEmissions(Abstract):
    def __init__(self, id, scenario, **kwargs):
        self.id = id
        self.input_type = 'intensity'
        self.sql_id_table = 'SupplyEmissions'
        self.sql_data_table = 'SupplyEmissionsData'
        self.scenario = scenario
        Abstract.__init__(self, self.id,primary_key='supply_node_id')

    def calculate(self, conversion, resource_unit):
        if self.data is True:
            self.conversion = conversion
            self.resource_unit=resource_unit    
            self.remap(lower=None)
            self.convert()
            self.calculate_physical_and_accounting()
            
    def convert(self):
        self.values = self.values.unstack(level='year')    
        self.values.columns = self.values.columns.droplevel()
        if self.conversion is not None:
            # checks whether a conversion dataframe has been created and the values can
            # be represented in energy and resource terms
            self.energy = util.determ_energy(self.denominator_unit)
            if self.energy:
                # if the input values are in energy terms, the input mass unit and energy units are
                # converted to model mass units and energy units. These values are multiplied by the
                # conversion dataframe to produce resource values
                self.values = util.unit_convert(self.values, unit_from_num=self.mass_unit,
                                                unit_from_den=self.denominator_unit,
                                                unit_to_num=cfg.cfgfile.get('case', "mass_unit"),
                                                unit_to_den=cfg.calculation_energy_unit)
#                    self.resource_values = DfOper.mult([self.values, self.conversion.values])
            else:
                # if the input values are in resource terms, values are converted from input mass and resource units
                # to model units and node resource units. These resource values are divided by the conversion
                # dataframe to produce values.
                self.values = util.unit_convert(self.values, unit_from_num=self.mass_unit,
                                                         unit_from_den=self.denominator_unit,
                                                         unit_to_num=cfg.cfgfile.get('case', "mass_unit"),
                                                         unit_to_den=self.resource_unit)

                self.values = DfOper.divi([self.values, self.conversion.values])                
        else:
            # if there is no conversion, then values are converted to model mass and energy units
            self.values = util.unit_convert(self.values, unit_from_num=self.mass_unit,
                                            unit_from_den=self.denominator_unit,
                                            unit_to_num=cfg.cfgfile.get('case', "mass_unit"),
                                            unit_to_den=cfg.calculation_energy_unit)
        self.ghgs = util.sql_read_table('GreenhouseGases','id', return_iterable=True)
        self.values = util.reindex_df_level_with_new_elements(self.values,'ghg',self.ghgs,fill_value=0.).sort()
      
    def calculate_physical_and_accounting(self):
          """converts emissions intensities for use in physical and accounting emissions calculations"""
          physical_emissions_indexer = util.level_specific_indexer(self.values, 'ghg_type', 1)
          self.values_physical =  self.values.loc[physical_emissions_indexer,:]
          accounting_emissions_indexer = util.level_specific_indexer(self.values, 'ghg_type', 2)
          if 2 in self.values.index.get_level_values('ghg_type'):
              self.values_accounting =  self.values.loc[accounting_emissions_indexer,:]
          else:
              self.values_accounting = self.values_physical * 0


class SupplyEnergyConversion(Abstract):
    def __init__(self, id, resource_unit, **kwargs):
        """
        creates a dataframe of conversion values from energy (i.e. exajoule) to 
        # resource terms (i.e. tons of biomass)
        """
        self.id = id
        self.input_type = 'intensity'
        self.sql_id_table = 'SupplyPotentialConversion'
        self.sql_data_table = 'SupplyPotentialConversionData'
        Abstract.__init__(self, self.id, 'supply_node_id')
        
    def calculate(self, resource_unit):
        if self.data is True:
            self.resource_unit = resource_unit
            self.remap()
            self.values = util.unit_convert(self.values, unit_from_num=self.energy_unit_numerator,
                                        unit_from_den=self.resource_unit_denominator,
                                        unit_to_num=cfg.calculation_energy_unit,
                                        unit_to_den=self.resource_unit)
            self.values = self.values.unstack(level='year')    
            self.values.columns = self.values.columns.droplevel()


