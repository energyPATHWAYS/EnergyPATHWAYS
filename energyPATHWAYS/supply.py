__author__ = 'Ben Haley & Ryan Jones'

from config import cfg
from shape import shapes
import util
import pandas as pd
import numpy as np
from datamapfunctions import DataMapFunctions, Abstract
import copy
import time
from util import DfOper
from collections import defaultdict
from supply_measures import BlendMeasure, ExportMeasure, StockMeasure, StockSalesMeasure
from supply_technologies import SupplyTechnology, StorageTechnology
from shared_classes import SalesShare, SpecifiedStock, Stock, StockItem
from rollover import Rollover
from profilehooks import profile, timecall
from solve_io import solve_IO, inv_IO
from dispatch_classes import Dispatch, DispatchFeederAllocation
import inspect
import operator
from shape import shapes, Shape
from collections import defaultdict

# noinspection PyAttributeOutsideInit
           
class Supply(object):

    """This module calculates all supply nodes in an IO loop to calculate energy, 
    emissions, and cost flows through the energy economy
    """    
    
    def __init__(self, outputs_directory, **kwargs):
        """Initializes supply instance"""
        self.demand_sectors = util.sql_read_table('DemandSectors','id')
        self.geographies = cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')]
        self.geography = cfg.cfgfile.get('case', 'primary_geography')
        self.dispatch_geography = cfg.cfgfile.get('case','dispatch_geography')
        self.dispatch_geographies = cfg.geo.geographies[cfg.cfgfile.get('case','dispatch_geography')]
        self.thermal_dispatch_node_id = util.sql_read_table('DispatchConfig', 'thermal_dispatch_node_id')
        self.distribution_node_id = util.sql_read_table('DispatchConfig', 'distribution_node_id')
        self.distribution_grid_node_id = util.sql_read_table('DispatchConfig', 'distribution_grid_node_id')
        self.transmission_node_id = util.sql_read_table('DispatchConfig', 'transmission_node_id')
        self.dispatch_zones = [self.distribution_node_id, self.transmission_node_id]
        self.electricity_nodes = defaultdict(list)
        self.injection_nodes = defaultdict(list)
        self.ghgs = util.sql_read_table('GreenhouseGases','id')
        
        self.dispatch_feeder_allocation = DispatchFeederAllocation(id=1)
        self.dispatch_feeders = list(set(self.dispatch_feeder_allocation.values.index.get_level_values('dispatch_feeder')))
        self.dispatch = Dispatch(self.dispatch_feeders, self.dispatch_geography, self.dispatch_geographies,
                                 cfg.cfgfile.get('opt','stdout_detail'), outputs_directory)
     

     
    def calculate_technologies(self):
        """ initiates calculation of all technology attributes - costs, efficiency, etc.
        """

        tech_classes = ['capital_cost_new', 'capital_cost_replacement', 'installation_cost_new', 'installation_cost_replacement', 'fixed_om', 'variable_om', 'efficiency']
        #storage techs have additional attributes specifying costs for energy (i.e. kWh of energy storage) and discharge capacity (i.e. kW)
        storage_tech_classes = ['installation_cost_new','installation_cost_replacement', 'fixed_om', 'variable_om', 'efficiency', 'capital_cost_new_capacity', 'capital_cost_replacement_capacity',
                                'capital_cost_new_energy', 'capital_cost_replacement_energy']
        for node in self.nodes.values():
            if not hasattr(node, 'technologies'):
                continue

            for technology in node.technologies.values():
                technology.calculate([node.vintages[0] - 1] + node.vintages, node.years)

            if isinstance(technology, StorageTechnology):
                node.remap_tech_attrs(storage_tech_classes)
            else:
                node.remap_tech_attrs(tech_classes)
                    

    def calculate_years(self):
        """
        Determines the period of stock rollover within a node based on the minimum year 
        of specified sales or specified stock. 
        """
        for node in self.nodes.values():
            node.min_year = int(cfg.cfgfile.get('case', 'current_year'))
            attributes = vars(node)    
            for att in attributes:
                obj = getattr(node, att)
                if inspect.isclass(type(obj)) and hasattr(obj, '__dict__') and hasattr(obj, 'data') and obj.data is True:   
                    if 'year' in obj.raw_values.index.names:
                        min_year = min(obj.raw_values.index.get_level_values('year'))
                    elif 'vintage' in obj.raw_values.index.names:
                        min_year = min(obj.raw_values.index.get_level_values('vintage'))
                    else:
                        continue
                    if min_year < node.min_year:
                      node.min_year = min_year             
            if hasattr(node,'technologies'):
                for technology in node.technologies.values():
                    for reference_sales in technology.reference_sales.values():
                           min_year = min(reference_sales.raw_values.index.levels[util.position_in_index(reference_sales.raw_values, 'vintage')])
                           if min_year < node.min_year:
                               node.min_year = min_year
                    for sales in technology.sales.values():
                              min_year = min(sales.raw_values.index.get_level_values('vintage'))
                              min_year = node.min_year
                              if min_year < node.min_year:
                                  node.min_year = min_year
            if hasattr(node,'stock') and node.stock.raw_values is not None:
                    min_year = min(node.stock.raw_values.index.levels[util.position_in_index(node.stock.raw_values, 'year')])
                    if min_year < node.min_year:
                        node.min_year = min_year
            node.years = range(node.min_year,
                                       int(cfg.cfgfile.get('case', 'end_year')) + 1,
                                       int(cfg.cfgfile.get('case', 'year_step')))
            node.vintages = copy.deepcopy(node.years)
        self.years = cfg.cfgfile.get('case','supply_years') 
            
    def initial_calculate(self):
        """Calculates all nodes in years before IO loop"""
        print "calculating supply-side prior to current year"
        self.calculate_technologies()
        self.calculate_blend_nodes()
        self.calculate_primary_nodes()
        self.calculate_import_nodes()
        self.calculate_other_nodes()
        self.calculate_initial_demand()        
        
    def calculate_blend_nodes(self):
        """Performs an initial calculation for all blend nodes"""
        for node in self.nodes.values():
            if isinstance(node, BlendNode):
                node.calculate(node.years, self.demand_sectors, self.ghgs)
                
    def calculate_primary_nodes(self):
        """Performs an initial calculation for all primary nodes"""
        for node in self.nodes.values():
            if isinstance(node, PrimaryNode):
                node.calculate(node.years, self.demand_sectors, self.ghgs)
    
    def calculate_import_nodes(self):
        """Performs an initial calculation for all import nodes"""
        for node in self.nodes.values():
            if isinstance(node, ImportNode):
                node.calculate(node.years, self.demand_sectors, self.ghgs)    
                
    def calculate_other_nodes(self):
        """Performs an initial calculation for all import, conversion, delivery, and storage nodes"""
        for node in self.nodes.values():
            if isinstance(node, SupplyNode) or isinstance(node, SupplyStockNode) or isinstance(node, StorageNode):
                node.calculate(node.years, self.demand_sectors, self.ghgs, self.distribution_grid_node_id)
    
    def create_IO(self):
        """Creates a dictionary with year and demand sector keys to store IO table structure"""
        self.io_dict = util.recursivedict()
        index =  pd.MultiIndex.from_product([self.geographies, self.all_nodes], names=[self.geography,
                                                         'supply_node'])
        for year in self.years:
            for sector in self.demand_sectors:
                self.io_dict[year][sector] = util.empty_df(index = index, columns = index, fill_value=0.0)

        self.io_dict = util.freeze_recursivedict(self.io_dict)

    def add_node_list(self):
        """Adds list of nodes to supply-side"""
        self.nodes = {}
        self.all_nodes = []
        self.blend_nodes = []
        cfg.cur.execute('select id from "SupplyNodes" order by id')
        ids = [id for id in cfg.cur.fetchall()]
        for (id,) in ids:
            self.all_nodes.append(id)

    def add_nodes(self):  
        """Adds node instances for all active supply nodes"""
        for id in self.all_nodes:
            cfg.cur.execute('select supply_type_id from "SupplyNodes" where id=%s', (id,))
            (supply_type_id,) = cfg.cur.fetchone()
            supply_type = util.id_to_name("supply_type_id", supply_type_id)
            cfg.cur.execute('select is_active from "SupplyNodes" where id=%s', (id,))
            (is_active,) = cfg.cur.fetchone()
            if is_active == 1:
                self.add_node(id, supply_type)


    def add_node(self, id, supply_type, **kwargs):
        """Add node to Supply instance
        Args: 
            id (int): supply node id 
            supply_type (str): supply type i.e. 'blend'
        """
        if supply_type == "Blend":
            self.nodes[id] = BlendNode(id, supply_type, **kwargs)
            self.blend_nodes.append(id)
        elif supply_type == "Storage":
            if len(util.sql_read_table('SupplyTechs', 'supply_node_id', supply_node_id=id, return_iterable=True)):          
                self.nodes[id] = StorageNode(id, supply_type, **kwargs)
            else:
                print ValueError('insufficient data in storage node %s' %id)
        elif supply_type == "Import":
            self.nodes[id] = ImportNode(id, supply_type, **kwargs)
        elif supply_type == "Primary":
            self.nodes[id] = PrimaryNode(id, supply_type, **kwargs)
        else:
            if len(util.sql_read_table('SupplyEfficiency', 'id', id=id, return_iterable=True)):          
                self.nodes[id] = SupplyNode(id, supply_type, **kwargs)
            elif len(util.sql_read_table('SupplyTechs', 'supply_node_id', supply_node_id=id, return_iterable=True)):          
                self.nodes[id] = SupplyStockNode(id, supply_type,  **kwargs)
            else:
                print ValueError('insufficient data in supply node %s' %id)
                
    def add_measures(self,case_id):
        """ Adds measures to supply nodes based on case and package inputs"""
        for node in self.nodes.values():  
            node.filter_packages('SupplyCasesData', 'supply_node_id', case_id)
            #all nodes have export measures
            node.add_export_measures()  
            #once measures are loaded, export classes can be initiated
            node.add_exports()
            if node.supply_type == 'Blend':
                node.add_blend_measures()     
            elif isinstance(node, SupplyStockNode) or isinstance(node, StorageNode): 
                for technology in node.technologies.values():                                                        
                    technology.add_sales_measures(node.sales_package_id)
                    technology.add_sales_share_measures(node.sales_share_package_id)
                    technology.add_specified_stock_measures(node.stock_package_id)
            elif isinstance(node, SupplyNode):
                node.add_stock_measure(node.stock_package_id)
        
        
    def calculate(self):
        """Performs all pre-IO loop calculations of supply"""
        self.calculate_years()
        self.add_empty_output_df() 
        self.create_IO()
        self.create_inverse_dict()
        self.cost_dict = util.recursivedict()
        self.emissions_dict = util.recursivedict()
        self.create_embodied_cost_and_energy_demand_link()
        self.create_embodied_emissions_demand_link()
        self.initial_calculate()
        
    def calculate_loop(self):
        """Performs all IO loop calculations""" 
        for year in self.years:
            for loop in ['initial',1,2,3]:
                if year == min(self.years):
                    print "looping through IO calculate for year: " + str(year) + " and loop: "  + str(loop)
                elif loop != 'initial':
                    print "looping through IO calculate for year: " + str(year) + " and loop: "  + str(loop)
                if year == min(self.years):
                    #in the first year of the io loop, we have an initial loop step called 'initial'.
                    #this loop is necessary in order to calculate initial active coefficients. Because we haven't calculated
                    #throughput for all nodes, these coefficients are just proxies in this initial loop
                    if loop == 'initial':
#                        self.initialize_year(year,loop)
                        self.calculate_demand(year,loop)
                        self.pass_initial_demand_to_nodes(year)
                        self.discover_thermal_nodes()
                        self.calculate_stocks(year, loop)
                        self.calculate_coefficients(year,loop)
                        self.bulk_node_id = self.discover_bulk_id()
                        self.discover_thermal_nodes()
                        self.update_io_df(year)
                        self.calculate_io(year,loop)  
                    elif loop  == 1:
                        self.calculate_coefficients(year,loop)
                        self.update_io_df(year)
                        self.calculate_io(year,loop)  
                        self.calculate_stocks(year, loop)
                        self.calculate_coefficients(year,loop)
                    if loop == 2:
                        #sets a flag for whether any reconciliation occurs in the loop
                        #determined in the reconcile function
                        self.reconciled = False
                        self.reconcile_trades(year,loop)
                        if self.reconciled is True:
                            #if reconciliation has occured, we have to recalculate coefficients and resolve the io
    #                        self.calculate_stocks(year, loop)
                            self.calculate_coefficients(year,loop)
                            self.update_io_df(year)
                            self.calculate_io(year, loop)
                        self.reconciled = False
                        self.reconcile_constraints_and_oversupply(year,loop)
                        if self.reconciled is True:
                            self.update_demand(year,loop)
                            #if reconciliation has occured, we have to recalculate coefficients and resolve the io
#                            self.calculate_stocks(year, loop)
                            self.calculate_coefficients(year,loop)
                            self.update_io_df(year)
                            self.calculate_io(year, loop)
                        self.calculate_stocks(year, loop)
                        self.calculate_embodied_costs(year)
                    if loop == 3:
                        self.prepare_dispatch_inputs(year, loop)
                        self.solve_electricity_dispatch(year)
                        self.calculate_coefficients(year,loop)
                        self.update_coefficients_from_dispatch()
                        self.update_io_df(year)
                        self.calculate_io(year, loop)
                        self.calculate_stocks(year,loop)
                        self.calculate_embodied_costs(year)
                        self.calculate_embodied_emissions(year)
                else:
                    if loop == 1:
                        self.initialize_year(year,loop)
                        self.calculate_demand(year,loop)
                        self.update_io_df(year)
                        self.calculate_io(year,loop)  
                        self.calculate_stocks(year, loop)
                        self.calculate_coefficients(year,loop)
                    if loop == 2:
                        #sets a flag for whether any reconciliation occurs in the lo
                        #determined in the reconcile function
                        self.reconciled = False
                        self.reconcile_trades(year,loop)
                        if self.reconciled is True:
                            #if reconciliation has occured, we have to recalculate coefficients and resolve the io
    #                        self.calculate_stocks(year, loop)
                            self.calculate_coefficients(year,loop)
                            self.update_io_df(year)
                            self.calculate_io(year, loop)
                        self.reconciled = False
                        self.reconcile_constraints_and_oversupply(year,loop)
                        if self.reconciled is True:
                            self.update_demand(year,loop)
                            #if reconciliation has occured, we have to recalculate coefficients and resolve the io
    #                        self.calculate_stocks(year, loop)
                            self.calculate_coefficients(year,loop)
                            self.update_io_df(year)
                            self.calculate_io(year, loop)
                        self.calculate_stocks(year, loop)
                        self.calculate_embodied_costs(year)
                    if loop == 3:
                        self.prepare_dispatch_inputs(year, loop)
                        self.solve_electricity_dispatch(year)
                        self.calculate_coefficients(year,loop)
                        self.update_coefficients_from_dispatch()
                        self.update_io_df(year)
                        self.calculate_io(year,loop)
                        self.calculate_stocks(year,loop)
                        self.calculate_embodied_costs(year)
                        self.calculate_embodied_emissions(year)
                        

    def discover_bulk_id(self):
        for node in self.nodes.values():
            if hasattr(node, 'active_coefficients_total') and getattr(node, 'active_coefficients_total') is not None:
                if self.thermal_dispatch_node_id in node.active_coefficients_total.index.get_level_values('supply_node'):
                    self.bulk_id = node.id
                    
    def discover_thermal_nodes(self):
        self.thermal_nodes = []
        for node in self.nodes.values():
            if node.is_flexible and node.id in self.nodes[self.thermal_dispatch_node_id].values.index.get_level_values('supply_node'):
                self.thermal_nodes.append(node.id)
                node.thermal_dispatch_node = True
            else:
                node.thermal_dispatch_node = False
                            
    def calculate_supply_outputs(self):
        print "calculating supply cost link"
        self.cost_demand_link = self.map_embodied_to_demand(self.cost_dict, self.embodied_cost_link_dict)
        print "calculating supply emissions link"
        self.emissions_demand_link = self.map_embodied_to_demand(self.emissions_dict, self.embodied_emissions_link_dict)
        print "calculating supply energy link"
        self.energy_demand_link = self.map_embodied_to_demand(self.inverse_dict['energy'],self.embodied_energy_link_dict)
        self.remove_blend_and_import()
        print "calculate exported costs"
        self.calculate_export_result('export_costs', self.cost_dict)
        print "calculate exported emissions"
        self.calculate_export_result('export_emissions', self.emissions_dict)
        print "calculate emissions rates for demand side"
        self.calculate_demand_emissions_rates()
        
    def remove_blend_and_import(self):
        keep_list = [node.id for node in self.nodes.values() if node.supply_type != 'Blend' and node.supply_type != 'Import']
        indexer = util.level_specific_indexer(self.energy_demand_link,'supply_node',[keep_list])
        self.energy_demand_link = self.energy_demand_link.loc[indexer,:]       
        
    def calculate_demand_emissions_rates(self):
        map_dict = dict(util.sql_read_table('SupplyNodes',['final_energy_link','id']))   
        if None in map_dict.keys():
            del map_dict[None]
        index = pd.MultiIndex.from_product([self.geographies, self.demand_sectors, map_dict.keys(),self.years, self.ghgs], names=[self.geography, 'sector', 'final_energy','year','ghg'])
        self.demand_emissions_rates = util.empty_df(index, ['value'])
        for final_energy, node_id in map_dict.iteritems():
            node = self.nodes[node_id]
            for year in self.years:
                df = node.pass_through_df_dict[year].groupby(level='ghg').sum()
                df = df.stack(level=[self.geography,'demand_sector']).to_frame()
                df = df.reorder_levels([self.geography,'demand_sector','ghg'])
                df.sort(inplace=True)
                emissions_rate_indexer = util.level_specific_indexer(self.demand_emissions_rates,['final_energy','year'],[final_energy,year])
                self.demand_emissions_rates.loc[emissions_rate_indexer,:] = df.values
        for final_energy, node_id in map_dict.iteritems():
            node = self.nodes[node_id] 
            if hasattr(node,'emissions') and hasattr(node.emissions, 'values_physical'):
                if 'demand_sector' not in node.emissions.values_physical.index.names:
                    keys = self.demand_sectors
                    name = ['demand_sector']
                    df = pd.concat([node.emissions.values_physical]*len(keys), keys=keys, names=name)
                df = df.stack('year').to_frame()
                df = df.groupby(level=[self.geography, 'demand_sector', 'year', 'ghg']).sum()
                df = df.reorder_levels([self.geography, 'demand_sector', 'year', 'ghg'])
                idx = pd.IndexSlice
                df = df.loc[idx[:, :, self.years,:],:]
                emissions_rate_indexer = util.level_specific_indexer(self.demand_emissions_rates,['final_energy'],[final_energy])
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
            self.electricity_gen_nodes[zone]['flexible'] = [x for x in self.injection_nodes[zone] if self.nodes[x].is_flexible == 1]
            self.electricity_gen_nodes[zone]['non_flexible'] = [x for x in self.injection_nodes[zone] if self.nodes[x].is_flexible != 1]
        for zone in self.dispatch_zones:
            self.electricity_load_nodes[zone]['flexible'] = [x for x in self.all_electricity_load_nodes[zone] if self.nodes[x].is_flexible == 1]
            self.electricity_load_nodes[zone]['non_flexible'] = [x for x in self.all_electricity_load_nodes[zone] if self.nodes[x].is_flexible != 1]
        self.electricity_gen_nodes = util.freeze_recursivedict(self.electricity_gen_nodes)
        self.electricity_load_nodes = util.freeze_recursivedict(self.electricity_load_nodes)

    def set_electricity_gen_nodes(self, dispatch_zone, node):
        """Determines all nodes that inject electricity onto the grid in a recursive loop
        args:
            dispatch_zone: key for dictionary to indicate whether the generation is at the transmission or distribution level
            node: checks for injection of electricity into this node from conversion nodes
        sets:
            self.injection_nodes = dictionary with dispatch_zone as key and a list of injection nodes as the value
            self.electricity_nodes = dictionary with dispatch_zone as key and a list of all nodes that transfer electricity (i.e. blend nodes, etc.)
        """
        if hasattr(node,'active_coefficients_untraded') and node.active_coefficients_untraded  is not None:
            for input_node_id in list(set(node.active_coefficients_untraded.index.get_level_values('supply_node'))):
                input_node= self.nodes[input_node_id]
                indexer = util.level_specific_indexer(node.active_coefficients_untraded, ['efficiency_type','supply_node'],[2,input_node.id])
                zone = node.active_coefficients_untraded.loc[indexer,:]
                if zone.empty is False:
                    if input_node_id in self.dispatch_zones:
                        #proceeds to next dispatch zone
                        self.set_electricity_gen_nodes(input_node, input_node)
                    elif input_node.supply_type =='Conversion':
                        self.injection_nodes[dispatch_zone.id].append(input_node.id)
                        continue
                    elif input_node.supply_type == 'Storage':
                        continue
                    else:
                        self.electricity_nodes[dispatch_zone.id].append(input_node.id)
                        self.set_electricity_gen_nodes(dispatch_zone, input_node)

    def set_electricity_load_nodes(self):
        """Determines all nodes that demand electricity from the grid
        args:
        sets:
            all_electricity_load_nodes = dictionary with dispatch_zone as key and a list of all nodes that demand electricity from that zone
        """    
        self.all_electricity_load_nodes = defaultdict(list)
        for zone in self.dispatch_zones:
            for node in self.electricity_nodes[zone]+[zone]:
                for load_node in self.nodes.values():
                    if hasattr(load_node,'active_coefficients_untraded')  and load_node.active_coefficients_untraded  is not None:
                        if node in load_node.active_coefficients_untraded.index.get_level_values('supply_node') and load_node not in self.electricity_nodes[zone]+[zone]:
                            if (load_node.supply_type == 'Conversion') and load_node.id not in self.electricity_nodes[zone]:
                                self.all_electricity_load_nodes[zone].append(load_node.id)


    def solve_heuristic_load_and_gen(self, year):
        """solves dispatch shapes for heuristically dispatched nodes (ex. conventional hydro)"""
        def split_and_apply(array, dispatch_periods, fun):
            energy_by_block = np.array_split(array, np.where(np.diff(dispatch_periods)!=0)[0]+1)
            return [fun(block) for block in energy_by_block]     
        self.dispatched_bulk_load = copy.deepcopy(self.bulk_load)*0
        self.dispatched_bulk_gen = copy.deepcopy(self.bulk_gen)*0
        self.dispatched_dist_load = copy.deepcopy(self.distribution_load)*0
        self.dispatched_dist_gen = copy.deepcopy(self.distribution_gen)*0
        for node_id in [x for x in self.dispatch.dispatch_order if x in self.nodes.keys()]:
            node = self.nodes[node_id]
            print "solving dispatch for %s" %node.name
            full_energy_shape, p_min_shape, p_max_shape = node.aggregate_flexible_electricity_shapes(year, util.remove_df_levels(util.df_slice(self.dispatch_feeder_allocation.values,year,'year'),year))
            if node_id in self.flexible_gen.keys():
                lookup = self.flexible_gen
                load = False
            elif node_id in self.flexible_load.keys():
                lookup = self.flexible_load
                load = True
            else:
                continue        
            for geography in lookup[node_id].keys():
                for zone in lookup[node_id][geography].keys():
                    for feeder in lookup[node_id][geography][zone].keys():
                        capacity = lookup[node_id][geography][zone][feeder]['capacity']
                        energy = lookup[node_id][geography][zone][feeder]['energy']
                        dispatch_window = self.dispatch.dispatch_window_dict[self.dispatch.node_config_dict[node_id].dispatch_window_id]
                        dispatch_periods = getattr(shapes.active_dates_index, dispatch_window)
                        num_years = len(dispatch_periods)/8766.
                        if load:
                            energy = copy.deepcopy(energy) *-1
                        if full_energy_shape is not None and 'dispatch_feeder' in full_energy_shape.index.names:
                            energy_shape = util.df_slice(full_energy_shape, feeder, 'dispatch_feeder')     
                        else:
                            energy_shape = full_energy_shape
                        if energy_shape is None:                            
                            energy_budgets = util.remove_df_levels(energy,self.geography).values * np.diff([0]+list(np.where(np.diff(dispatch_periods)!=0)[0]+1)+[len(dispatch_periods)-1])/8766.*num_years
                            energy_budgets = energy_budgets[0]
                        else:
                            hourly_energy = util.remove_df_levels(DfOper.mult([energy,energy_shape]), self.geography).values
                            energy_budgets = split_and_apply(hourly_energy, dispatch_periods, sum)
                        if p_min_shape is None:   
                            p_min = 0.0
                            p_max = capacity.sum().values[0]
                        else:
                            hourly_p_min = util.remove_df_levels(DfOper.mult([capacity,p_min_shape]),self.geography).values
                            p_min = split_and_apply(hourly_p_min, dispatch_periods, np.mean)
                            hourly_p_max = util.remove_df_levels(DfOper.mult([capacity,p_max_shape]),self.geography).values
                            p_max = split_and_apply(hourly_p_max, dispatch_periods, np.mean)                        
                        if zone == self.transmission_node_id:                    
                            net_indexer = util.level_specific_indexer(self.bulk_net_load,self.dispatch_geography, geography)
                            if load:                               
                                self.energy_budgets = energy_budgets
                                self.p_min = p_min
                                self.p_max = p_max
                                indexer = util.level_specific_indexer(self.bulk_load,self.dispatch_geography, geography)   
                                dispatch = np.transpose([Dispatch.dispatch_to_energy_budget(self.bulk_net_load.loc[net_indexer,:].values.flatten(),energy_budgets, dispatch_periods, p_min, p_max)])
                                self.dispatch_result = dispatch                                
                                self.bulk_load.loc[indexer,:] += dispatch
                                self.dispatched_bulk_load.loc[indexer,:] += dispatch
                            else:
                                indexer = util.level_specific_indexer(self.bulk_gen,self.dispatch_geography, geography)
                                dispatch = np.transpose([Dispatch.dispatch_to_energy_budget(self.bulk_net_load.loc[net_indexer,:].values.flatten(),energy_budgets, dispatch_periods, p_min, p_max)])
                                self.bulk_gen.loc[indexer,:] += dispatch
                                self.dispatched_bulk_gen.loc[indexer,:] += dispatch
                        else:
                            if load:
                                indexer = util.level_specific_indexer(self.dist_load,[self.dispatch_geography,'dispatch_feeder'], [geography,feeder])
                                dispatch =  np.transpose([Dispatch.dispatch_to_energy_budget(self.dist_net_load_no_feeders.loc[net_indexer,:].values.flatten(),energy_budgets, dispatch_periods, p_min, p_max)])
                                self.distribution_load.loc[indexer,:] += dispatch
                                self.dispatched_dist_load.loc[indexer,:] += dispatch

                            else:
                                indexer = util.level_specific_indexer(self.dist_gen,[self.dispatch_geography,'dispatch_feeder'], [geography,feeder])
                                dispatch =  np.transpose([Dispatch.dispatch_to_energy_budget(self.dist_net_load_no_feeders.loc[net_indexer,:].values.flatten(),energy_budgets, dispatch_periods, p_min, p_max)])
                                self.distribution_gen.loc[indexer,:] += dispatch
                                self.dispatched_dist_gen.loc[indexer,:] += dispatch
                    self.update_net_load_signal()
           

    def prepare_optimization_inputs(self,year):
        print "preparing optimization inputs"
        self.dispatch.set_timeperiods(shapes.active_dates_index)
        self.dispatch.set_losses(self.distribution_losses)
        self.set_net_load_thresholds(year)
        self.dispatch.set_opt_loads(self.distribution_load,self.distribution_gen,self.bulk_load,self.bulk_gen)
        self.dispatch.set_technologies(self.storage_capacity_dict, self.storage_efficiency_dict, self.thermal_dispatch_dict, 2)
        self.dispatch.set_average_net_loads(self.bulk_net_load)
        self.dispatch.set_opt_result_dfs(year)
     
     
    def set_grid_capacity_factors(self, year):
        max_year = max(self.years)
        distribution_grid_node = self.nodes[self.distribution_grid_node_id]        
        dist_cap_factor = DfOper.divi([self.dist_only_net_load.groupby(level=[self.dispatch_geography,'dispatch_feeder']).mean(),self.dist_only_net_load.groupby(level=[self.dispatch_geography,'dispatch_feeder']).max()])
        geography_map_key = distribution_grid_node.geography_map_key if hasattr(distribution_grid_node, 'geography_map_key') and distribution_grid_node.geography_map_key is not None else cfg.cfgfile.get('case','default_geography_map_key')       
        if self.dispatch_geography != self.geography:    
            map_df = cfg.geo.map_df(self.dispatch_geography, self.geography, geography_map_key, eliminate_zeros=False)
            dist_cap_factor = util.remove_df_levels(DfOper.mult([dist_cap_factor,map_df]),self.dispatch_geography)        
        dist_cap_factor = util.remove_df_levels(DfOper.mult([dist_cap_factor, util.df_slice(self.dispatch_feeder_allocation.values,year, 'year')]),'dispatch_feeder')
        distribution_grid_node.capacity_factor.values.loc[:,year] = dist_cap_factor.values
        distribution_grid_node.capacity_factor.values.loc[:,min(year+1,max_year)] = dist_cap_factor.values
        bulk_flow = DfOper.add([self.dist_net_load_no_feeders,self.bulk_load])
        bulk_cap_factor = DfOper.divi([bulk_flow.groupby(level=self.dispatch_geography).mean(),bulk_flow.groupby(level=self.dispatch_geography).max()]) 
        transmission_grid_node = self.nodes[self.transmission_node_id]        
      
        geography_map_key = transmission_grid_node.geography_map_key if hasattr(transmission_grid_node, 'geography_map_key') and transmission_grid_node.geography_map_key is not None else cfg.cfgfile.get('case','default_geography_map_key')       
        if self.dispatch_geography != self.geography:            
            map_df = cfg.geo.map_df(self.dispatch_geography, self.geography, geography_map_key, eliminate_zeros=False)
            bulk_cap_factor = util.remove_df_levels(DfOper.mult([bulk_cap_factor,map_df]),self.dispatch_geography)       
        transmission_grid_node.capacity_factor.values.loc[:,year] = bulk_cap_factor.values
        transmission_grid_node.capacity_factor.values.loc[:,min(year+1,max_year)] = bulk_cap_factor.values
        
    def solve_storage_and_flex_load_optimization(self,year):
        """prepares, solves, and updates the net load with results from the storage and flexible load optimization""" 
        self.prepare_optimization_inputs(year)
        print "solving storage and dispatchable load optimization"
        self.dispatch.run_optimization()
        for geography in self.dispatch_geographies:
            for feeder in self.dispatch_feeders:
                load_indexer = util.level_specific_indexer(self.distribution_load, [self.dispatch_geography, 'dispatch_feeder','timeshift_type'], [geography, feeder, 2])
                self.distribution_load.loc[load_indexer,: ] += util.df_slice(self.dispatch.dist_storage_df,[geography, feeder, 'charge'], [self.dispatch_geography, 'dispatch_feeder', 'charge_discharge']).values
                self.distribution_load.loc[load_indexer,: ] += util.df_slice(self.dispatch.flex_load_df,[geography, feeder], [self.dispatch_geography, 'dispatch_feeder']).values             
                gen_indexer = util.level_specific_indexer(self.distribution_gen,[self.dispatch_geography, 'dispatch_feeder','timeshift_type'], [geography, feeder, 2])
                self.distribution_gen.loc[gen_indexer,: ] += util.df_slice(self.dispatch.dist_storage_df,[geography, feeder, 'discharge'], [self.dispatch_geography, 'dispatch_feeder', 'charge_discharge']).values
        for geography in self.dispatch_geographies:       
            load_indexer = util.level_specific_indexer(self.bulk_load, [self.dispatch_geography], [geography])
            self.bulk_load.loc[load_indexer,: ] += util.df_slice(self.dispatch.bulk_storage_df,[geography,'charge'], [self.dispatch_geography, 'charge_discharge']).values
            gen_indexer = util.level_specific_indexer(self.bulk_gen, [self.dispatch_geography], [geography])
            self.bulk_gen.loc[gen_indexer,: ] += util.df_slice(self.dispatch.bulk_storage_df,[geography,'discharge'], [self.dispatch_geography, 'charge_discharge']).values    
        self.update_net_load_signal()  
     
    def set_distribution_losses(self,year):
        distribution_grid_node =self.nodes[self.distribution_grid_node_id] 
        coefficients = distribution_grid_node.active_coefficients_total.sum().to_frame()
        indexer = util.level_specific_indexer(self.dispatch_feeder_allocation.values, 'year', year)
        a = util.DfOper.mult([coefficients, self.dispatch_feeder_allocation.values.loc[indexer,:], distribution_grid_node.active_supply])     
        b = util.DfOper.mult([self.dispatch_feeder_allocation.values.loc[indexer,:], distribution_grid_node.active_supply])
        self.distribution_losses = util.DfOper.divi([util.remove_df_levels(a,'demand_sector'),util.remove_df_levels(b,'demand_sector')])
        geography_map_key = distribution_grid_node.geography_map_key if hasattr(distribution_grid_node, 'geography_map_key') and distribution_grid_node.geography_map_key is not None else cfg.cfgfile.get('case','default_geography_map_key')       
        if self.dispatch_geography != self.geography:               
            map_df = cfg.geo.map_df(self.geography,self.dispatch_geography,geography_map_key,eliminate_zeros=False)             
            self.distribution_losses =  util.remove_df_levels(DfOper.mult([self.distribution_losses,map_df]),self.geography)
    
    
    def set_net_load_thresholds(self, year):
        distribution_grid_node = self.nodes[self.distribution_grid_node_id]
        dist_stock = distribution_grid_node.stock.values.groupby(level=[self.geography,'demand_sector']).sum().loc[:,year].to_frame()
        dist_stock = util.remove_df_levels(DfOper.mult([dist_stock, util.df_slice(self.dispatch_feeder_allocation.values,year,'year')]),'demand_sector')
        geography_map_key = distribution_grid_node.geography_map_key if hasattr(distribution_grid_node, 'geography_map_key') and distribution_grid_node.geography_map_key is not None else cfg.cfgfile.get('case','default_geography_map_key')       
        if self.dispatch_geography != self.geography:               
            map_df = cfg.geo.map_df(self.dispatch_geography,self.geography,geography_map_key,eliminate_zeros=False)             
            dist_stock =  util.remove_df_levels(DfOper.mult([dist_stock,map_df]),self.geography)   
        transmission_grid_node = self.nodes[self.transmission_node_id]
        transmission_stock = transmission_grid_node.stock.values.groupby(level=[self.geography]).sum().loc[:,year].to_frame()
        geography_map_key = transmission_grid_node.geography_map_key if hasattr(distribution_grid_node, 'geography_map_key') and transmission_grid_node.geography_map_key is not None else cfg.cfgfile.get('case','default_geography_map_key')       
        if self.dispatch_geography != self.geography:               
            map_df = cfg.geo.map_df(self.dispatch_geography,self.geography,geography_map_key,eliminate_zeros=False)             
            transmission_stock =  util.remove_df_levels(DfOper.mult([transmission_stock,map_df]),self.geography)   
        self.dispatch.set_thresholds(dist_stock,transmission_stock)
   
   
    def prepare_flexible_load(self,year,loop):
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
                if hasattr(node,'coefficients'):
                    coefficients = node.coefficients.values
                else:
                    coefficients = node.stock.coefficients

                indexer = util.level_specific_indexer(node.stock.coefficients.loc[:,year].to_frame(),'supply_node',[self.electricity_nodes[zone]+[zone]])
                energy_demand = DfOper.mult([node.stock.values_energy.loc[:,year].to_frame(), coefficients.loc[indexer,year].to_frame()])
                capacity = DfOper.mult([node.stock.values.loc[:,year].to_frame(), coefficients.loc[indexer,year].to_frame()])
                if zone == self.distribution_node_id and 'demand_sector' not in node.stock.values.index.names:
                    #requires energy on the distribution system to be allocated to feeder for dispatch
                    energy_demand = DfOper.mult([energy_demand, node.active_supply.groupby(level=[self.geography,'demand_sector']).transform(lambda x: x/x.sum())])   
                    capacity = DfOper.mult([capacity, node.active_supply.groupby(level=[self.geography,'demand_sector']).transform(lambda x: x/x.sum())])
                energy_demand = util.remove_df_levels(energy_demand.loc[indexer,:],['vintage', 'supply_technology'])
                capacity = util.remove_df_levels(capacity,['vintage', 'supply_technology'])
                #geomap to dispatch geography
                if self.dispatch_geography != self.geography:    
                    geography_map_key = node.geography_map_key if hasattr(node, 'geography_map_key') and node.geography_map_key is not None else cfg.cfgfile.get('case','default_geography_map_key')
                    map_df = cfg.geo.map_df(self.dispatch_geography,self.geography,geography_map_key, eliminate_zeros=False)
                    energy_demand = DfOper.mult([energy_demand,map_df])
                    capacity = DfOper.mult([capacity,map_df])
                if zone == self.distribution_node_id:
                    #specific for distribution node because of feeder allocation requirement
                    indexer = util.level_specific_indexer(self.dispatch_feeder_allocation.values, 'year', year)
                    energy_demand = util.remove_df_levels(util.DfOper.mult([energy_demand, self.dispatch_feeder_allocation.values.loc[indexer, ]]), 'demand_sector')
                    capacity = util.remove_df_levels(util.DfOper.mult([capacity, self.dispatch_feeder_allocation.values.loc[indexer, ]]), 'demand_sector')
                    for geography in self.dispatch_geographies:
                        for dispatch_feeder in self.dispatch_feeders:
                            indexer = util.level_specific_indexer(energy_demand, [self.dispatch_geography, 'supply_node', 'dispatch_feeder'],[geography,zone,dispatch_feeder])
                            self.flexible_load[node.id][geography][zone][dispatch_feeder]['energy']= util.remove_df_levels(energy_demand.loc[indexer,:],[self.dispatch_geography,'dispatch_feeder'])
                            indexer = util.level_specific_indexer(capacity, [self.dispatch_geography, 'supply_node', 'dispatch_feeder'],[geography,zone,dispatch_feeder])
                            self.flexible_load[node.id][geography][zone][dispatch_feeder]['capacity']= util.remove_df_elements(capacity.loc[indexer,:],[self.dispatch_geography,'dispatch_feeder'])
                else:
                    for geography in self.dispatch_geographies:
                        #feeder is set to 0 for flexible load not on the distribution system
                        indexer = util.level_specific_indexer(energy_demand, [self.dispatch_geography, 'supply_node'],[geography,zone])
                        self.flexible_load[node.id][geography][zone][0]['energy']= util.remove_df_levels(energy_demand.loc[indexer,:],[self.dispatch_geography,'demand_sector'])
                        indexer = util.level_specific_indexer(capacity,[self.dispatch_geography, 'supply_node'],[geography,zone])
                        self.flexible_load[node.id][geography][zone][0]['capacity']= util.remove_df_levels(capacity.loc[indexer,:],[self.dispatch_geography,'demand_sector'])
        self.flexible_load = util.freeze_recursivedict(self.flexible_load)

    def prepare_flexible_gen(self,year,loop):
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


                energy = node.stock.values_energy.loc[:,year].to_frame()
                capacity = node.stock.values.loc[:,year].to_frame()
                if zone == self.distribution_node_id and 'demand_sector' not in node.stock.values.index.names:
                    #requires energy on the distribution system to be allocated to feeder for dispatch
                    energy = DfOper.mult([energy, node.active_supply.groupby(level=[self.geography,'demand_sector']).transform(lambda x: x/x.sum())])   
                    capacity = DfOper.mult([capacity, node.active_supply.groupby(level=[self.geography,'demand_sector']).transform(lambda x: x/x.sum())])
                energy = util.remove_df_levels(energy,['vintage', 'supply_technology'])
                capacity = util.remove_df_levels(capacity,['vintage', 'supply_technology'])
                #geomap to dispatch geography
                if self.dispatch_geography != self.geography:
                    geography_map_key = node.geography_map_key if hasattr(node, 'geography_map_key') and node.geography_map_key is not None else cfg.cfgfile.get('case','default_geography_map_key')
                    map_df = cfg.geo.map_df(self.dispatch_geography,self.geography,geography_map_key, eliminate_zeros=False)
                    energy = DfOper.mult([energy,map_df])
                    capacity = DfOper.mult([capacity,map_df])
                if zone == self.distribution_node_id:
                    #specific for distribution node because of feeder allocation requirement
                    indexer = util.level_specific_indexer(self.dispatch_feeder_allocation.values, 'year', year)
                    energy = util.remove_df_levels(util.DfOper.mult([energy, self.dispatch_feeder_allocation.values.loc[indexer, ]]), 'demand_sector')
                    capacity = util.remove_df_levels(util.DfOper.mult([capacity, self.dispatch_feeder_allocation.values.loc[indexer, ]]), 'demand_sector')
                    for geography in self.dispatch_geographies:
                        for dispatch_feeder in self.dispatch_feeders:
                            indexer = util.level_specific_indexer(energy, [self.dispatch_geography, 'dispatch_feeder'],[geography,zone,dispatch_feeder])
                            self.flexible_gen[node.id][geography][zone][dispatch_feeder]['energy']= util.remove_df_levels(energy.loc[indexer,:],['dispatch_feeder',self.dispatch_geography,'supply_node'])
                            indexer = util.level_specific_indexer(capacity, [self.dispatch_geography, 'dispatch_feeder'],[geography,zone,dispatch_feeder])
                            self.flexible_gen[node.id][geography][zone][dispatch_feeder]['capacity']= util.remove_df_levels(capacity.loc[indexer,:],['dispatch_feeder',self.dispatch_geography,'supply_node'])
                else:
                    for geography in self.dispatch_geographies:
                        #feeder is set to 0 for flexible load not on the distribution system
                        indexer = util.level_specific_indexer(energy, self.dispatch_geography, geography)
                        self.flexible_gen[node.id][geography][zone][0]['energy'] = util.remove_df_levels(energy.loc[indexer,:],['demand_sector',self.dispatch_geography,'supply_node'])
                        indexer = util.level_specific_indexer(capacity,self.dispatch_geography, geography)
                        self.flexible_gen[node.id][geography][zone][0]['capacity'] = util.remove_df_levels(capacity.loc[indexer,:],['demand_sector',self.dispatch_geography,'supply_node'])
        self.flexible_gen = util.freeze_recursivedict(self.flexible_gen)


    def prepare_non_flexible_load(self, year,loop):
        """Calculates the demand from non-flexible load on the supply-side
        Args:
            year (int) = year of analysis 
            loop (int or str) = loop identifier
        Sets:
            non_flexible_load (dict) = dictionary with keys of 'geography', zone (i.e. transmission grid
            or distribution grid), feeder, and node_id,  with values of a dataframe
    
        """
        self.non_flexible_load = util.recursivedict()
        for zone in self.dispatch_zones:
            for node_id in self.electricity_load_nodes[zone]['non_flexible']:
                node = self.nodes[node_id]
                if hasattr(node,'coefficients'):
                    coefficients = node.coefficients.values
                else:
                    coefficients = node.stock.coefficients

                coefficients.sort(inplace=True)
                indexer = util.level_specific_indexer(node.active_coefficients_untraded,'supply_node',[self.electricity_nodes[zone]+[zone]])
#                node.stock.values_energy.sort(inplace=True)
                stock_energy = util.remove_df_levels(node.stock.values_energy.loc[:,year].to_frame(),['vintage', 'supply_technology','efficiency_type'])
                if zone == self.distribution_node_id and 'demand_sector' not in node.stock.values.index.names:
                    #requires energy on the distribution system to be allocated to feeder for dispatch
                    stock_energy = DfOper.mult([stock_energy, node.active_supply.groupby(level=[self.geography]).transform(lambda x: x/x.sum())])   
#                energy = util.remove_df_levels(energy,['vintage', 'supply_technology','efficiency_type''supply_node'])
                energy = DfOper.mult([stock_energy, node.active_coefficients_untraded.loc[indexer,:]])
                energy = util.remove_df_levels(energy,'supply_node')
                if self.dispatch_geography != self.geography:
                   #geomap to dispatch geography
                    geography_map_key = node.geography_map_key if hasattr(node, 'geography_map_key') and node.geography_map_key is not None else cfg.cfgfile.get('case','default_geography_map_key')
                    map_df = cfg.geo.map_df(self.dispatch_geography,self.geography,geography_map_key, eliminate_zeros=False)
                    energy = DfOper.mult([energy,map_df])
                if zone == self.distribution_node_id:
                    #specific for distribution node because of feeder allocation requirement
                    indexer = util.level_specific_indexer(self.dispatch_feeder_allocation.values, 'year', year)
                    energy = util.remove_df_levels(util.DfOper.mult([energy, self.dispatch_feeder_allocation.values.loc[indexer, ]]), 'demand_sector')
                    for geography in self.dispatch_geographies:
                        for dispatch_feeder in self.dispatch_feeders:
                            indexer = util.level_specific_indexer(energy, [self.dispatch_geography, 'dispatch_feeder'],[geography,dispatch_feeder])
                            self.non_flexible_load[geography][zone][node.id][dispatch_feeder]= energy.loc[indexer,:]
                else:
                    for geography in self.dispatch_geographies:
                        #feeder is set to 0 for flexible load not on the distribution system
                        indexer = util.level_specific_indexer(energy, self.dispatch_geography,geography)
                        self.non_flexible_load[geography][zone][node.id][0]= util.remove_df_levels(energy.loc[indexer,:],['demand_sector'])
        self.non_flexible_load = util.freeze_recursivedict(self.non_flexible_load)
                    
    def prepare_non_flexible_gen(self,year,loop):
        """Calculates the supply from non-flexible generation on the supply-side
        Args:
            year (int) = year of analysis 
            loop (int or str) = loop identifier
        Sets:
            non_flexible_load (dict) = dictionary with keys of 'geography', zone (i.e. transmission grid
            or distribution grid), feeder, and node_id,  with values of a dataframe
        """
        self.non_flexible_gen = util.recursivedict()
        for zone in self.dispatch_zones:
            for node_id in self.electricity_gen_nodes[zone]['non_flexible']:
                node = self.nodes[node_id]
                energy_supply = node.stock.values_energy.loc[:,year].to_frame()
                if zone == self.distribution_node_id and 'demand_sector' not in node.stock.values.index.names:
                    #requires energy on the distribution system to be allocated to feeder for dispatch
                    energy_supply= DfOper.mult([energy_supply, node.active_supply.groupby(level=[self.geography,'demand_sector']).transform(lambda x: x/x.sum())])   
                energy_supply = util.remove_df_levels(energy_supply,['vintage', 'supply_technology'])
                #geomap to dispatch geography
                if self.dispatch_geography != self.geography:                
                    geography_map_key = node.geography_map_key if hasattr(node, 'geography_map_key') and node.geography_map_key is not None else cfg.cfgfile.get('case','default_geography_map_key')
                    map_df = cfg.geo.map_df(self.dispatch_geography,self.geography,geography_map_key, eliminate_zeros=False)
                    energy_supply = DfOper.mult([energy_supply,map_df])
                if zone == self.distribution_node_id:
                    #specific for distribution node because of feeder allocation requirement
                    indexer = util.level_specific_indexer(self.dispatch_feeder_allocation.values, 'year', year)
                    energy_supply = util.remove_df_levels(util.DfOper.mult([energy_supply, self.dispatch_feeder_allocation.values.loc[indexer, ]]), 'demand_sector')
                    for geography in self.dispatch_geographies:
                        for dispatch_feeder in self.dispatch_feeders:
                            indexer = util.level_specific_indexer(energy_supply, [self.dispatch_geography, 'dispatch_feeder'],[geography,dispatch_feeder])
                            self.non_flexible_gen[geography][zone][node.id][dispatch_feeder]= energy_supply.loc[indexer,:]
                else:
                    for geography in self.dispatch_geographies:
                        #feeder is set to 0 for flexible load not on the distribution system
                        indexer = util.level_specific_indexer(energy_supply, self.dispatch_geography,geography)
                        self.non_flexible_gen[geography][zone][node.id][0] = util.remove_df_levels(energy_supply.loc[indexer,:],['demand_sector'])

        self.non_flexible_gen = util.freeze_recursivedict(self.non_flexible_gen)

    def prepare_dispatch_inputs(self, year, loop):
        """Calculates supply node parameters needed to run electricity dispatch
        Args:
            year (int) = year of analysis 
            loop (int or str) = loop identifier
        """
        print "initiating electricity dispatch"
        self.set_electricity_gen_nodes(self.nodes[self.distribution_node_id],self.nodes[self.distribution_node_id])
        self.set_electricity_load_nodes()
        self.set_dispatchability()
        self.prepare_non_flexible_gen(year,loop)
        self.prepare_flexible_gen(year,loop)
        self.prepare_non_flexible_load(year,loop)
        self.prepare_flexible_load(year,loop)
        self.prepare_thermal_dispatch_nodes(year,loop)
        self.prepare_electricity_storage_nodes(year,loop)
        self.set_distribution_losses(year)
        self.set_shapes(year)
        self.set_initial_net_load_signals(year)
        
    def solve_electricity_dispatch(self,year):
        """solves heuristic dispatch, optimization dispatch, and thermal dispatch
        Args: 
            year (int) = year of analysis 
        """
        #solves dispatched load and gen on the supply-side for nodes like hydro and H2 electrolysis
        self.solve_heuristic_load_and_gen(year)
        #solves electricity storage and flexible demand load optimization
        self.solve_storage_and_flex_load_optimization(year)
        #updates the grid capacity factors for distribution and transmission grid (i.e. load factors)
        self.set_grid_capacity_factors(year)
        #solves dispatch (stack model) for thermal resource connected to thermal dispatch node
        self.solve_thermal_dispatch(year)        
                
        
    def prepare_thermal_dispatch_nodes(self,year,loop):
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
        embodied_cost_df = embodied_cost_df.reorder_levels([self.geography,'demand_sector','supply_node']).to_frame()
        embodied_cost_df.sort(inplace=True)   
        self.dispatch_df = embodied_cost_df
        self.thermal_dispatch_dict = util.recursivedict()
        self.resource_key_dict = dict() 
        self.group_key_dict = dict()
        self.thermal_dispatch_nodes = [x for x in set(list(self.nodes[self.thermal_dispatch_node_id].active_coefficients.index.get_level_values('supply_node')))]
        for node_id in self.thermal_dispatch_nodes:
            #node is the instance of the class itself
            node = self.nodes[node_id]
            #if the node has the attribute calculate_dispatch_costs it will be included, otherwise it can't be dispatched and is omitted 
            if hasattr(node, 'calculate_dispatch_costs'):
                node.calculate_dispatch_costs(year, embodied_cost_df,loop)
                if hasattr(node,'active_dispatch_costs'):
                    active_dispatch_costs = node.active_dispatch_costs
                    stock_values = node.stock.values.loc[:,year].to_frame()
                    capacity_factor = node.stock.capacity_factor.loc[:,year].to_frame()
                    #values must be geomapped to dispatch geography if geography and dispatch_geography are not the same
                    if self.dispatch_geography != self.geography:
                        geography_map_key = node.geography_map_key if hasattr(node, 'geography_map_key') and node.geography_map_key is not None else cfg.cfgfile.get('case','default_geography_map_key')
                        int_map_df = cfg.geo.map_df(self.geography, self.dispatch_geography, column=geography_map_key, eliminate_zeros=False)
                        tot_map_df = cfg.geo.map_df(self.dispatch_geography,self.geography, column=geography_map_key, eliminate_zeros=False)
                        active_dispatch_costs = util.remove_df_levels(DfOper.mult([active_dispatch_costs, int_map_df],fill_value=0.0),self.geography)
                        stock_values = DfOper.mult([stock_values, tot_map_df],fill_value=0.0)
                        capacity_factor = util.remove_df_levels(DfOper.mult([capacity_factor, int_map_df],fill_value=0.0),self.geography)
                    groups = [x[0] for x in stock_values.groupby(level=stock_values.index.names).groups.values()]
                    #dictionaries used to store the position of index names for the group and resource tuples. Needed to use the tuples in dataframe locs. 
                    self.group_key_dict[node_id] = dict(zip(stock_values.index.names,[stock_values.index.names.index(x) for x in stock_values.index.names]))
                    self.resource_key_dict[node_id] = dict(zip(stock_values.index.names,[stock_values.index.names.index(x)+1 for x in stock_values.index.names]))
                    for group in groups:
                        cap_factor_group = tuple([group[self.group_key_dict[node_id][x]] for x in active_dispatch_costs.index.names])
                        dict_key = (node.id,) + group
                        dispatch_location = group[self.group_key_dict[node_id][self.dispatch_geography]]
                        if stock_values.loc[group].values[0] == 0 and group[self.group_key_dict[node_id]['vintage']]!=year:
                            continue
                        else:
                            self.thermal_dispatch_dict[dispatch_location]['capacity'][dict_key] = stock_values.loc[group].values[0]   
                            self.thermal_dispatch_dict[dispatch_location]['cost'][dict_key] = active_dispatch_costs.loc[cap_factor_group].values[0]
                            self.thermal_dispatch_dict[dispatch_location]['maintenance_outage_rate'][dict_key] = (1- capacity_factor.loc[cap_factor_group].values[0])*.5
                            self.thermal_dispatch_dict[dispatch_location]['forced_outage_rate'][dict_key]= self.thermal_dispatch_dict[dispatch_location]['maintenance_outage_rate'][dict_key]
                            if hasattr(node,'must_run') and node.must_run == 1:
                                self.thermal_dispatch_dict[dispatch_location]['must_run'][dict_key] = 1
                            else:
                                self.thermal_dispatch_dict[dispatch_location]['must_run'][dict_key] = 0
                         
       
       
    def capacity_weights(self,year):
        """sets the share of new capacity by technology and location to resolve insufficient capacity in the thermal dispatch
        Args:
            year (int) = year of analysis
        Sets:
            thermal_dispatch_dict (dict) = set dictionary with keys of dispatch geography, 'capacity_weights', and a tuple thermal resource identifier. Values are the share of new capacity
            by thermal resource identifier in a specified dispatch geography.  
        """
        weights = self.nodes[self.thermal_dispatch_node_id].values.loc[:,year].to_frame().groupby(level=[self.geography,'supply_node']).mean()
        if self.dispatch_geography != self.geography:
            map_df = cfg.geo.map_df(self.geography,self.dispatch_geography, eliminate_zeros=False)
            weights = DfOper.mult([weights,map_df])
        for geography in self.dispatch_geographies:
            for node_id in self.thermal_nodes:
                node = self.nodes[node_id]
                for resource in self.thermal_dispatch_dict[geography]['capacity'].keys():
                    if resource[0] == node_id and resource[self.resource_key_dict[node_id]['vintage']]==year:                 
                        loc_geo = resource[self.resource_key_dict[node_id][self.geography]]
                        indexer_positions = [self.resource_key_dict[node_id][x] for x in node.active_weighted_sales.index.names]
                        sales_weight_indexer =  tuple([resource[x] for x in indexer_positions])
                        self.thermal_dispatch_dict[geography]['capacity_weights'][resource] = (util.df_slice(weights,[loc_geo, geography, node_id],[self.geography,self.dispatch_geography,'supply_node']).values * node.active_weighted_sales.loc[sales_weight_indexer,:].values)[0][0]
                    elif resource[0] == node_id and resource[self.resource_key_dict[node_id]['vintage']]!=year:
                        self.thermal_dispatch_dict[geography]['capacity_weights'][resource] = 0

    
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
            weighted_sales = node.stock.sales[node.stock.sales.index.get_level_values('vintage')<=year]
            weighted_sales *= (np.column_stack(weighted_sales.index.get_level_values('vintage').values).T-vintage_start)
            weighted_sales = util.remove_df_levels(weighted_sales,'vintage')
            weighted_sales = weighted_sales.groupby(level = self.geography ).transform(lambda x: x/x.sum())
            node.active_weighted_sales = weighted_sales
            node.active_weighted_sales = node.active_weighted_sales.fillna(1/float(len(node.tech_ids)))
            
                         
  
    def solve_thermal_dispatch(self,year):
        """solves the thermal dispatch, updating the capacity factor for each thermal dispatch technology
        and adding capacity to each node based on determination of need"""
        print 'solving thermal dispatch'
        self.calculate_weighted_sales(year)
        self.capacity_weights(year)
        for geography in self.dispatch_geographies:
            load = util.df_slice(self.bulk_net_load,geography, self.dispatch_geography)
            months = load.index.get_level_values('weather_datetime').month
            load = load.values.flatten()
            pmaxs = np.array(self.thermal_dispatch_dict[geography]['capacity'].values())
            marginal_costs = np.array(self.thermal_dispatch_dict[geography]['cost'].values())
            MOR = np.array(self.thermal_dispatch_dict[geography]['maintenance_outage_rate'].values())
            FOR = np.array(self.thermal_dispatch_dict[geography]['forced_outage_rate'].values())
            must_runs = np.array(self.thermal_dispatch_dict[geography]['must_run'].values())
            capacity_weights = np.array([self.thermal_dispatch_dict[geography]['capacity_weights'][x] for x in self.thermal_dispatch_dict[geography]['capacity'].keys()])
            maintenance_rates = self.dispatch.schedule_generator_maintenance(load=load,pmaxs=pmaxs,annual_maintenance_rates=MOR,
                                                                             dispatch_periods=months)
            dispatch_results = self.dispatch.generator_stack_dispatch(load=load, pmaxs=pmaxs, marginal_costs=marginal_costs, MOR=maintenance_rates,
                                                                      FOR=FOR, must_runs=must_runs, dispatch_periods=months, capacity_weights=capacity_weights)
            self.thermal_dispatch_dict[geography]['capacity_factor'] = dict(zip(self.thermal_dispatch_dict[geography]['capacity'].keys(),dispatch_results['gen_cf']))
            self.thermal_dispatch_dict[geography]['generation'] = dict(zip(self.thermal_dispatch_dict[geography]['capacity'].keys(),dispatch_results['gen_energies']))
            self.thermal_dispatch_dict[geography]['stock_changes'] = dict(zip(self.thermal_dispatch_dict[geography]['capacity'].keys(),dispatch_results['stock_changes'])) 
            for node_id in set([x[0] for x in self.thermal_dispatch_dict[geography]['capacity_factor'].keys()]):
                resources = [x for x in self.thermal_dispatch_dict[geography]['capacity_factor'].keys() if x[0] == node_id]
                node = self.nodes[node_id]
                for resource in resources:
                    indexer_positions = [self.resource_key_dict[node.id][x] for x in node.stock.values.index.names]
                    stock_indexer = tuple([resource[x] for x in indexer_positions])
                    node.stock.capacity_factor.loc[stock_indexer,year] = self.thermal_dispatch_dict[geography]['capacity_factor'][resource]
                    node.stock.dispatch_cap.loc[stock_indexer,year] = self.thermal_dispatch_dict[geography]['stock_changes'][resource]
    

    def update_coefficients_from_dispatch(self):
        self.calculate_thermal_totals()
        self.update_thermal_coefficients()
        self.update_bulk_coefficients()

    def update_thermal_coefficients(self):
        df = self.thermal_totals.apply(lambda x: x/x.sum())
        df = pd.concat([df]*len(self.demand_sectors),keys=self.demand_sectors,names=['demand_sector'])
        df = pd.concat([df]*len(self.demand_sectors),keys=self.demand_sectors,names=['demand_sector'],axis=1)
        df = df.reorder_levels([self.geography,'demand_sector','supply_node'])
        df.sort(inplace=True)
        for row_sector in self.demand_sectors:
            for col_sector in self.demand_sectors:
                if row_sector != col_sector:
                    row_indexer = util.level_specific_indexer(df,'demand_sector',row_sector,axis=0)
                    col_indexer = util.level_specific_indexer(df,'demand_sector',col_sector,axis=1)
                    df.loc[row_indexer,col_indexer] = 0
        df = self.geo_map_thermal_coefficients(df,self.dispatch_geography,self.geography,cfg.cfgfile.get('case','default_geography_map_key'))
        self.nodes[self.thermal_dispatch_node_id].active_coefficients_total = df
        
    def calculate_thermal_totals(self):   
        row_index = pd.MultiIndex.from_product([self.geographies, self.thermal_dispatch_nodes], names=[self.geography, 'supply_node'])
        col_index = pd.MultiIndex.from_product([self.dispatch_geographies],names=[self.dispatch_geography])
        df = util.empty_df(index=row_index,columns=col_index)
        for geography in self.dispatch_geographies:
            for node_id in self.thermal_dispatch_nodes:
                resources = [x for x in self.thermal_dispatch_dict[geography]['generation'].keys() if x[0] == node_id]
                for resource in resources:
                    location = resource[1]
                    node = resource[0]
                    df.loc[(location,node),(geography)] += self.thermal_dispatch_dict[geography]['generation'][resource]
        self.thermal_totals = df
        
    def update_bulk_coefficients(self):
        bulk_load = util.DfOper.add([self.bulk_load.groupby(level=self.dispatch_geography).sum(), util.DfOper.mult([util.DfOper.subt([self.distribution_load,self.distribution_gen]),self.distribution_losses]).groupby(level=self.dispatch_geography).sum()])
        thermal_totals = self.thermal_totals.sum().to_frame()
        bulk_coefficients = DfOper.divi([thermal_totals, bulk_load])
        if self.dispatch_geography != self.geography:
            map_key = cfg.cfgfile.get('case','default_geography_map_key')
            map_df = cfg.geo.map_df(self.dispatch_geography,self.geography,map_key, eliminate_zeros=False)
            bulk_coefficients = DfOper.mult([bulk_coefficients,map_df]).groupby(level=self.geography).sum()
        bulk_coefficients = pd.concat([bulk_coefficients]*len(self.demand_sectors),keys=self.demand_sectors,names=['demand_sector'])
        bulk_coefficients = bulk_coefficients.reorder_levels([self.geography,'demand_sector'])
        bulk_coefficients = self.add_column_index(bulk_coefficients)
        bulk_coefficients.sort(inplace=True,axis=1)
        bulk_coefficients.sort(inplace=True,axis=0)
        for row_geography in self.geographies:
            for col_geography in self.geographies:
                for row_sector in self.demand_sectors:
                    for col_sector in self.demand_sectors:
                        if row_geography != col_geography or row_sector != col_sector:
                            row_indexer = util.level_specific_indexer(bulk_coefficients, [self.geography,'demand_sector'],[row_geography,row_sector])
                            col_indexer = util.level_specific_indexer(bulk_coefficients, [self.geography,'demand_sector'],[col_geography,col_sector])
                            bulk_coefficients.loc[row_indexer,col_indexer] = 0
        indexer = util.level_specific_indexer(self.nodes[self.bulk_id].active_coefficients_total,'supply_node', self.thermal_dispatch_node_id)
        self.nodes[self.bulk_id].active_coefficients_total.loc[indexer,:] = bulk_coefficients.values
        
        
    def add_column_index(self, data):
         names = ['demand_sector', cfg.cfgfile.get('case','primary_geography')]
         keys = [self.demand_sectors, cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')]]
         data  = copy.deepcopy(data)
         for key,name in zip(keys,names):
             data  = pd.concat([data]*len(key), axis=1, keys=key, names=[name])
         data.columns = data.columns.droplevel(-1)
         return data 
    
    def geo_map_thermal_coefficients(self,df,old_geography, new_geography, geography_map_key):
            if old_geography != new_geography:
                keys=cfg.geo.geographies[new_geography]
                name = [new_geography]
                df = pd.concat([df] * len(keys),keys=keys,names=name,axis=1)
                df.sort(inplace=True,axis=1)
                df.sort(inplace=True,axis=0)
                map_df = cfg.geo.map_df(old_geography,new_geography,geography_map_key,eliminate_zeros=False).transpose()
                names = [x for x in df.index.names if x not in map_df.index.names]
                names.reverse()
                for name in names:
                    keys=list(set(df.index.get_level_values(name)))
                    map_df = pd.concat([map_df]*len(keys),keys=keys,names=[name])
                map_df.index = map_df.index.droplevel(None)
                names = [x for x in df.columns.names if x not in map_df.columns.names]
                names.reverse()
                keys = []
                for name in names:
                    keys = list(set(df.columns.get_level_values(name)))
                    map_df = pd.concat([map_df]*len(keys),keys=keys,names=[name],axis=1)
                map_df=map_df.reorder_levels(df.index.names,axis=0)
                map_df = map_df.reorder_levels(df.columns.names,axis=1)
                map_df.sort(inplace=True,axis=0)
                map_df.sort(inplace=True,axis=1)
                old_geographies = list(set(df.columns.get_level_values(old_geography)))
                new_geographies =list(set(map_df.columns.get_level_values(new_geography)))
                for old in old_geographies:
                    for new in new_geographies:
                        row_indexer = util.level_specific_indexer(df,[new_geography],[new],axis=0)
                        col_indexer = util.level_specific_indexer(df,[old_geography,new_geography],[old,new],axis=1)
                        shape = (df.loc[row_indexer,col_indexer].values.shape)
                        diag = np.ndarray(shape)
                        np.fill_diagonal(diag,1)
                df *= map_df.values
                df = df.groupby(level=util.ix_excl(df,old_geography,axis=1),axis=1).sum()
            return df
      
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
                if hasattr(node,'active_disp_coefficients'):
                    storage_node_location = list(set(node.active_disp_coefficients.index.get_level_values('supply_node')))
                    if len(storage_node_location)>1:
                        raise ValueError('StorageNode %s has technologies with two different supply node locations' %node.id)
                if storage_node_location[0] in self.electricity_nodes[zone]+[zone]:
                    capacity= node.stock.values.loc[:,year].to_frame().groupby(level=[self.geography,'supply_technology']).sum()
                    efficiency = copy.deepcopy(node.active_disp_coefficients)
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
                    if self.dispatch_geography != self.geography:
                        geography_map_key = node.geography_map_key if hasattr(node, 'geography_map_key') and node.geography_map_key is not None else cfg.cfgfile.get('case','default_geography_map_key')
                        map_df = cfg.geo.map_df(self.dispatch_geography,self.geography, column=geography_map_key, eliminate_zeros=False)
                        capacity = DfOper.mult([capacity, map_df],fill_value=0.0)                
                        efficiency = DfOper.divi([util.remove_df_levels(DfOper.mult([efficiency, capacity]), self.geography),util.remove_df_levels(capacity,self.geography)]).fillna(0)                    
                        capacity = util.remove_df_levels(capacity, self.geography)
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
                        efficiency = DfOper.divi([util.remove_df_levels(DfOper.mult([efficiency, capacity]),'demand_sector'),util.remove_df_levels(capacity,'demand_sector')]).fillna(0)
                        capacity = util.remove_df_levels(capacity,'demand_sector')
                        for geography in self.dispatch_geographies:
                                for dispatch_feeder in self.dispatch_feeders:
                                    for technology in node.technologies.keys():
                                        indexer = util.level_specific_indexer(efficiency, [self.dispatch_geography, 'dispatch_feeder','supply_technology'],[geography,dispatch_feeder,technology])
                                        self.storage_efficiency_dict[geography][zone][dispatch_feeder][technology] = efficiency.loc[indexer,:].values[0][0]
                                        indexer = util.level_specific_indexer(capacity, [self.dispatch_geography, 'dispatch_feeder','supply_technology'],[geography,dispatch_feeder,technology])
                                        self.storage_capacity_dict['power'][geography][zone][dispatch_feeder][technology] = capacity.loc[indexer,:].values[0][0]
                                        indexer = util.level_specific_indexer(duration, [self.dispatch_geography, 'dispatch_feeder','supply_technology'],[geography,dispatch_feeder,technology])
                                        self.storage_capacity_dict['duration'][geography][zone][dispatch_feeder][technology] = duration.loc[indexer,:].values[0][0]
                    else:
                        for geography in self.dispatch_geographies:
                            for technology in node.technologies.keys():
                                indexer = util.level_specific_indexer(capacity, [self.dispatch_geography, 'supply_technology'],[geography,technology])
                                tech_capacity = self.ensure_frame(util.remove_df_levels(capacity.loc[indexer,:], 'demand_sector'))
                                indexer = util.level_specific_indexer(duration, [self.dispatch_geography,'supply_technology'],[geography,technology])                               
                                tech_duration = self.ensure_frame(util.remove_df_levels(duration.loc[indexer,:], 'demand_sector'))
                                indexer = util.level_specific_indexer(efficiency, [self.dispatch_geography, 'supply_technology'],[geography,technology])                                
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
           for node_id in self.electricity_load_nodes[zone]['non_flexible'] + self.electricity_gen_nodes[zone]['non_flexible'] :
               self.nodes[node_id].active_shape = self.nodes[node_id].aggregate_electricity_shapes(year, util.remove_df_levels(util.df_slice(self.dispatch_feeder_allocation.values,year,'year'),year))   
        
   
    def shaped_dist(self, year, load_or_gen_dict):
        df_geo = []      
        for geography in self.dispatch_geographies:
            df_node = []
            node_ids = load_or_gen_dict[geography][self.distribution_node_id].keys()
            for node_id in node_ids:
                node = self.nodes[node_id]
                df_feeder = []
                for feeder in self.dispatch_feeders:
                    gen = load_or_gen_dict[geography][self.distribution_node_id][node_id][feeder].groupby(level=self.geography).sum()
                    if 'dispatch_feeder' in node.active_shape.index.names:
                        indexer = util.level_specific_indexer(node.active_shape, 'dispatch_feeder', feeder)
                        shape = node.active_shape.loc[indexer,:]
                    else:
                        shape= node.active_shape
                    df_feeder.append(util.remove_df_levels(util.DfOper.mult([gen,shape]),self.geography))
                df_node.append(pd.concat(df_feeder, keys=self.dispatch_feeders, names=['dispatch_feeder']))
            df_geo.append(DfOper.add(df_node, expandable=False, collapsible=False))
        return pd.concat(df_geo, keys=self.dispatch_geographies, names=[self.dispatch_geography])    
        
    def shaped_bulk(self, year, load_or_gen_dict):
        df_geo = []
        for geography in self.dispatch_geographies:
            df_node = []
            node_ids = load_or_gen_dict[geography][self.transmission_node_id].keys()
            for node_id in node_ids:
                node = self.nodes[node_id]
                gen = load_or_gen_dict[geography][self.transmission_node_id][node_id][0].groupby(level=self.geography).sum()
                if 'dispatch_feeder' in node.active_shape.index.names:
                    shape = util.remove_df_levels(node.active_shape, 'dispatch_feeder')
                else:
                    shape = node.active_shape
                shape = shape.groupby(level=[self.geography, 'timeshift_type']).transform(lambda x: x/x.sum())
                df_node.append(util.remove_df_levels(DfOper.mult([gen,shape]), self.geography))              
            df_geo.append(DfOper.add(df_node))
        return pd.concat(df_geo, keys=self.dispatch_geographies, names=[self.dispatch_geography])
            
    def set_initial_net_load_signals(self,year):
        self.distribution_load = DfOper.add([self.demand_object.aggregate_electricity_shapes(year),self.shaped_dist(year, self.non_flexible_load)])
        self.distribution_gen = self.shaped_dist(year, self.non_flexible_gen)
        self.bulk_gen = self.shaped_bulk(year, self.non_flexible_gen)
        self.bulk_load = self.shaped_bulk(year, self.non_flexible_load)
        self.update_net_load_signal()            
        
        
    def update_net_load_signal(self):    
        self.dist_only_net_load =  DfOper.subt([self.distribution_load,self.distribution_gen])
        self.bulk_only_net_load = DfOper.subt([self.bulk_load,self.bulk_gen])
        self.bulk_net_load = DfOper.add([util.remove_df_levels(DfOper.mult([self.dist_only_net_load,self.distribution_losses]),'dispatch_feeder'),self.bulk_only_net_load])                      
        self.dist_net_load_no_feeders = DfOper.add([DfOper.divi([self.bulk_only_net_load,util.remove_df_levels(self.distribution_losses,'dispatch_feeder',agg_function='mean')]), util.remove_df_levels(self.dist_only_net_load,'dispatch_feeder')])
            
    def calculate_embodied_costs(self, year):
        """Calculates the embodied emissions for all supply nodes by multiplying each node's
        active_embodied_costs by the cost inverse. Result is stored in 
        the Supply instance's 'cost_dict' attribute"
        Args:
            year (int) = year of analysis 
            loop (int or str) = loop identifier
        """
        index = pd.MultiIndex.from_product([self.geographies, self.all_nodes], names=[self.geography, 'supply_node'])
        for node in self.nodes.values():
            supply_indexer = util.level_specific_indexer(self.io_embodied_cost_df, 'supply_node', node.id)     
            if hasattr(node,'calculate_costs'):
                node.calculate_costs(year)
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
        row_index = pd.MultiIndex.from_product([self.geographies, self.all_nodes, self.ghgs], names=[self.geography, 'supply_node', 'ghg'])
        col_index =  pd.MultiIndex.from_product([self.geographies, self.all_nodes], names=[self.geography, 'supply_node'])
        for node in self.nodes.values():
            supply_indexer = util.level_specific_indexer(self.io_embodied_emissions_df, 'supply_node', node.id)     
            if hasattr(node, 'active_embodied_emissions_rate'):
                self.io_embodied_emissions_df.loc[supply_indexer, year] = node.active_embodied_emissions_rate.values
        for sector in self.demand_sectors:    
            inverse = copy.deepcopy(self.inverse_dict['energy'][year][sector])
            keys = self.ghgs
            name = ['ghg']
            inverse = pd.concat([inverse]*len(keys), keys=keys, names=name)
            inverse = inverse.reorder_levels([self.geography,'supply_node','ghg'])
            inverse.sort(axis=0,inplace=True)
            indexer = util.level_specific_indexer(self.io_embodied_emissions_df, 'demand_sector', sector)
            self.test_inverse = inverse
            emissions = np.column_stack(self.io_embodied_emissions_df.loc[indexer,year].values).T
            self.test_emissions = emissions
            self.emissions_dict[year][sector] = pd.DataFrame(emissions * inverse.values,index=row_index,columns=col_index)


    def map_embodied_to_demand(self, embodied_dict,link_dict):
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
        map_dict = dict(util.sql_read_table('SupplyNodes',['final_energy_link','id']))   
        if None in map_dict.keys():
            del map_dict[None]
        df_list = []
        for year in self.years:
            sector_df_list = []
            keys = self.demand_sectors
            name = ['sector']
            idx = pd.IndexSlice
            for sector in self.demand_sectors:
                link_dict[year][sector].loc[:,:] = embodied_dict[year][sector].loc[:,idx[:, map_dict.values()]].values
                link_dict[year][sector]= link_dict[year][sector].stack([self.geography,'final_energy']).to_frame()
#                levels = [x for x in ['supply_node',self.geography +'_supply', 'ghg',self.geography,'final_energy'] if x in link_dict[year][sector].index.names]
                link_dict[year][sector] = link_dict[year][sector][link_dict[year][sector][0]!=0]
                sector_df_list.append(link_dict[year][sector])     
            year_df = pd.concat(sector_df_list, keys=keys,names=name)
            df_list.append(year_df)
        self.sector_df_list  = sector_df_list     
        self.df_list = df_list
        keys = self.years
        name = ['year']
        df = pd.concat(df_list,keys=keys,names=name)
        df.columns = ['value']
#       levels = [x for x in ['supply_node',self.geography +'_supply', 'ghg',self.geography,'final_energy'] if x in df.index.names]
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
        util.replace_index_name(export_df, 'year')
        util.replace_column(export_df, 'value')
        export_df = export_df[export_df['value']!=0]
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
               util.replace_index_name(df, self.geography + "_supply", self.geography)
               stack_levels =[self.geography, "supply_node_export"] 
               df = df.stack(stack_levels).to_frame()
               df = df[df[0]!=0]
               sector_df_list.append(df)     
            year_df = pd.concat(sector_df_list, keys=keys,names=name)
            df_list.append(year_df)
#        self.sector_df_list  = sector_df_list     
#        self.df_list = df_list
        keys = self.years
        name = ['year']
        df = pd.concat(df_list,keys=keys,names=name)
        df.columns = ['value']
#        levels = [x for x in ['supply_node','supply_node_export',self.geography +'_supply',self.geography +'_export',  'ghg'] if x in df.index.names]
#        df = df.groupby(level=levels).filter(lambda x: x.sum()!=0)                 
        return df

    def calculate_export_result(self, export_result_name, io_dict):
        export_map_df = self.map_embodied_to_export(io_dict)
        export_df = self.io_export_df.stack().to_frame()
        export_df = export_df[export_df[0]!=0]
        if export_map_df.empty is False and export_df.empty is False:
            util.replace_index_name(export_df, 'year')
            util.replace_index_name(export_df, 'sector', 'demand_sector')
            util.replace_index_name(export_df,'supply_node_export','supply_node')
            util.replace_column(export_df, 'value') 
            export_result= DfOper.mult([export_df, export_map_df])
        else:
            export_result = None
#        levels = [x for x in ['supply_node','supply_node_export',self.geography +'_supply',self.geography +'_export',  'ghg'] if x in export_result.index.names]
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
            if node.reconciled is True:
                node.update_reconciled_residual(year)
        for node in self.nodes.values():
            node.calculate_active_coefficients(year, loop)
                    
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
        for node in self.nodes.values():         
            if node.id not in self.blend_nodes:
                #Checks whether a node has information (stocks or potential) that means that demand is not a good proxy for location of supply
                node.calculate_internal_trades(year,loop)       
        for node in self.nodes.values():
            #loops through all nodes checking for excess supply from nodes that are not curtailable, flexible, or exportable
            trade_sub = node.id
            if node.id not in self.blend_nodes:
                #Checks whether a node has information that means that demand is not a good proxy for location of supply
                if hasattr(node,'active_internal_trade_df') and node.internal_trades == "stop and feed":
                    #enters a loop to feed that constraint forward in the supply node until it can be reconciled at a blend node or exported
                    self.feed_internal_trades(year, trade_sub, node.active_internal_trade_df)     
                    
        
        
    def reconcile_constraints_and_oversupply(self,year,loop):    
        """Reconciles instances where IO demands exceed a node's potential or demands less than a node's expected level of supply based
        on its existing stock.  To achieve this result, we calculate the expected location of supply and then pass 
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
        for node in self.nodes.values():
            #loops through all nodes checking for excess supply from nodes that are not curtailable, flexible, or exportable
            if node.is_curtailable or node.is_exportable:
                pass
            elif node.is_flexible and node.id in self.nodes[self.thermal_dispatch_node_id].active_coefficients_total.index.get_level_values('supply_node'):
                pass
            elif node.id in self.blend_nodes:
                pass
            else:
                #Checks whether a node has excess supply and returns an adjustment factor if so 
                oversupply_factor = node.calculate_oversupply(year,loop) if hasattr(node,'calculate_oversupply') else None 
                if oversupply_factor is not None:
                    #enters a loop to feed that constraint forward in the supply node until it can be reconciled at a blend node or exported
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
                     indexer = util.level_specific_indexer(output_node.active_constraint_adjustment_df,'supply_node', constrained_node)
                     output_node.active_constraint_adjustment_df.loc[indexer,:] =  constraint_adjustment.values
                     #flag for the blend node that it has been reconciled and needs to recalculate residual
                     output_node.reconciled = True
                     #flag that anything in the supply loop has been reconciled, and so the loop needs to be resolved
                     self.reconciled = True
                  else:
                     #if the output node has the constrained sub as an input, and it is not a blend node, it becomes the constrained sub
                      #in the loop in order to feed the adjustment factor forward to dependent nodes until it terminates at a blend node
                     self.feed_constraints(year, constrained_node=output_node, constraint_adjustment=constraint_adjustment)
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
            if hasattr(output_node, 'active_coefficients_total') and getattr(output_node, 'active_coefficients_total') is not None:
              if internal_trade_node in set(output_node.active_coefficients_total.index.get_level_values('supply_node')):
                  #if this output node is a blend node, the reconciliation happens here. 
                  if output_node.id in self.blend_nodes or isinstance(output_node,ImportNode) or output_node.internal_trades == 'stop':
                     indexer = util.level_specific_indexer(output_node.active_trade_adjustment_df,'supply_node', internal_trade_node)  
                     output_node.active_trade_adjustment_df.loc[indexer, :]  =  internal_trade_adjustment.values
                     self.reconciled = True
                     output_node.reconciled = True
                  elif output_node.internal_trades == 'stop and feed':
                     indexer = util.level_specific_indexer(output_node.active_coefficients_total,'supply_node', internal_trade_node)
                     output_node.active_trade_adjustment_df.loc[indexer, :]  = internal_trade_adjustment.values
                     output_node.reconciled = True
                     self.reconciled = True
                     self.feed_internal_trades(year, internal_trade_node=output_node.id, internal_trade_adjustment=output_node.active_internal_trade_df)
                  elif output_node.internal_trades == 'feed':
                     #if the output node has the internal trade sub as an input, multiply the trades by the coefficients to pass it through to subsequent nodes
                     self.feed_internal_trades(year, internal_trade_node=output_node.id, internal_trade_adjustment=internal_trade_adjustment)
                 
    def feed_oversupply(self, year, oversupply_node, oversupply_adjustment):
        """Propagates oversupply adjustments to downstream nodes 
        Args:
            year (int) = year of analysis 
            oversupply_node (int) = integer id key of supply node that has the capacity to produce more throughput than demanded
            oversupply_adjustment (df) = dataframe of oversupply adjustments to propagate forward
            
        Ex. If demand form wind energy is 1 EJ and the existing stock has the ability to produce 2 EJ, if the node is not flagged as curtailable or exportable,
        the oversupply is propogated to downstream nodes until it reaches a Blend node or a node that is curtailable or exportable. If a node is curtailable, excess supply is ignored
        and the capacity is unutilized. If a node is exportable, excess supply results in exports to demand outside the model. If it reaches a Blend node, blend coefficient values are adjusted 
        and reconciled so that the excess supply is then demanded in the next loop in order to resolve the conflict. 
        """
        
        for output_node in self.nodes.values():
            if hasattr(output_node, 'active_coefficients_total') and getattr(output_node, 'active_coefficients_total') is not None:
                if oversupply_node in set(output_node.active_coefficients_total.index.get_level_values('supply_node')):
                  if output_node.id in self.blend_nodes:
                     indexer = util.level_specific_indexer(output_node.values,'supply_node', oversupply_node)
                     output_node.values.loc[indexer, year] = DfOper.mult([output_node.values.loc[indexer, year].to_frame(),oversupply_adjustment]).values
                     output_node.reconciled = True
                     self.reconciled=True
                  else:
                      if output_node.is_curtailable or output_node.is_flexible:
                          #if the output sector is curtailable, then the excess supply feed-loop ends and the excess is curtailed within this node. If the node is flexible, excess supply
                          #will be reconciled in the dispatch loop
                          pass
                      elif output_node.is_exportable:
                          #if the output node is exportable, then excess supply is added to the export demand in this node
                          excess_supply = DfOper.subt([DfOper.mult([output_node.active_supply, oversupply_adjustment]), output_node.active_supply])
                          output_node.export.active_values = DfOper.add([output_node.export.active_values, excess_supply]) 
                      else: 
                          #otherwise, continue the feed-loop until the excess supply can be reconciled
                          self.feed_oversupply(year, oversupply_node = output_node.id, oversupply_adjustment=oversupply_adjustment)
 

    def update_io_df(self,year):
        """Updates the io dictionary with the active coefficients of all nodes
        Args:
            year (int) = year of analysis 
        """
        for col_node in self.nodes.values():
            if col_node.active_coefficients_total is None:
                continue
            else:
                for sector in self.demand_sectors:
                    levels = ['supply_node' ]
                    col_indexer = util.level_specific_indexer(self.io_dict[year][sector], levels=levels, elements=[col_node.id])
                    row_nodes = list(map(int,col_node.active_coefficients_total.index.levels[util.position_in_index(col_node.active_coefficients_total,'supply_node')]))
                    row_indexer = util.level_specific_indexer(self.io_dict[year][sector], levels=levels, elements=[row_nodes])
                    levels = ['demand_sector','supply_node']   
                    active_row_indexer =  util.level_specific_indexer(col_node.active_coefficients_total, levels=levels, elements=[sector,row_nodes]) 
                    active_col_indexer = util.level_specific_indexer(col_node.active_coefficients_total, levels=['demand_sector'], elements=[sector], axis=1)
                    try:
                        self.io_dict[year][sector].loc[row_indexer, col_indexer] = col_node.active_coefficients_total.loc[active_row_indexer,active_col_indexer].values
                    except:
                        print col_node.id
                        
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
                             emissions_rate= emissions_rate.stack([self.geography, 'demand_sector']).to_frame()
                             emissions_rate = emissions_rate.reorder_levels([self.geography, 'demand_sector', 'ghg'])
                             emissions_rate.sort(inplace=True, axis=0)                                                          
                             keys = [self.demand_sectors,self.geographies]
                             names = ['demand_sector', self.geography]
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
                node.trade_adjustment_dict[previous_year] = node.active_trade_adjustment_df
            if hasattr(node, 'active_constraint_df'):
                node.constraint_dict[previous_year] = node.active_constraint_df
                node.active_constraint_df = node.constraint_dict[year]
            if hasattr(node, 'active_constraint_adjustment_df'):
                node.constraint_adjustment_dict[previous_year] = node.active_constraint_adjustment_df
                node.active_constraint_adjustment_df = node.constraint_adjustment_dict[year]
            if not isinstance(node,SupplyStockNode) and not isinstance(node,StorageNode):
                node.calculate_active_coefficients(year, loop)

                
    
                
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
        self.io_total_active_demand_df = DfOper.add([self.io_demand_df.loc[:,year].to_frame(),self.io_export_df.loc[:,year].to_frame()])
    
    def update_demand(self, year, loop):
        self.map_export_to_io(year, loop)
        self.io_total_active_demand_df = DfOper.add([self.io_demand_df.loc[:,year].to_frame(),self.io_export_df.loc[:,year].to_frame()])
        
    def calculate_io(self, year, loop):
        index = pd.MultiIndex.from_product([self.geographies, self.all_nodes
                                                                ], names=[self.geography,'supply_node'])  
        for sector in self.demand_sectors:
            indexer = util.level_specific_indexer(self.io_total_active_demand_df,'demand_sector', sector)
            self.active_io = self.io_dict[year][sector]
            active_cost_io = self.adjust_for_not_incremental(self.active_io)
            self.active_demand = self.io_total_active_demand_df.loc[indexer,:]
            self.io_supply_df.loc[indexer,year] = solve_IO(self.active_io.values, self.active_demand.values)  
            self.inverse_dict['energy'][year][sector] = pd.DataFrame(solve_IO(self.active_io.values).round(6), index=index, columns=index)
            self.inverse_dict['cost'][year][sector] = pd.DataFrame(solve_IO(active_cost_io.values).round(6), index=index, columns=index)
        for node in self.nodes.values():
            indexer = util.level_specific_indexer(self.io_supply_df,levels=['supply_node'], elements = [node.id])
            node.active_supply = self.io_supply_df.loc[indexer,year].groupby(level=[self.geography, 'demand_sector']).sum().to_frame()

    
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
        index =  pd.MultiIndex.from_product([cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')],
                                                            self.demand_sectors], names=[cfg.cfgfile.get('case','primary_geography'), 'demand_sector']) 
        self.empty_output_df = util.empty_df(index = index, columns = self.years,fill_value = 1E-25)      
        
    def add_io_df(self,attribute_names):
        #TODO only need to run years with a complete demand data set. Check demand dataframe. 
        index =  pd.MultiIndex.from_product([cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')],self.demand_sectors, self.all_nodes
                                                                ], names=[cfg.cfgfile.get('case','primary_geography'),
                                                                 'demand_sector','supply_node'])                                                            
        for attribute_name in util.put_in_list(attribute_names):
            setattr(self, attribute_name, util.empty_df(index = index, columns = self.years))
            
            
    def add_io_embodied_emissions_df(self):
        #TODO only need to run years with a complete demand data set. Check demand dataframe. 
        index =  pd.MultiIndex.from_product([cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')],self.demand_sectors, self.all_nodes,self.ghgs,
                                                                ], names=[cfg.cfgfile.get('case','primary_geography'),
                                                                 'demand_sector', 'supply_node','ghg'])                                                            
        
        setattr(self, 'io_embodied_emissions_df', util.empty_df(index = index, columns = self.years))
            
    def create_inverse_dict(self):
        index = pd.MultiIndex.from_product([cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')], self.all_nodes
                                                                ], names=[cfg.cfgfile.get('case','primary_geography'),'supply_node'])  
        df = util.empty_df(index = index, columns = index)
        self.inverse_dict = util.recursivedict()   
        for key in ['energy', 'cost']:
            for year in self.years:
                for sector in self.demand_sectors:
                    self.inverse_dict[key][year][sector]= df
            
    def create_embodied_cost_and_energy_demand_link(self):
        map_dict = dict(util.sql_read_table('SupplyNodes',['final_energy_link','id']))
        if None in map_dict.keys():
            del map_dict[None]
        keys = sorted(map_dict.items(), key=operator.itemgetter(1))
        keys = [x[0] for x in keys]
            #sorts final energy in the same order as the supply node dataframes
        index = pd.MultiIndex.from_product([self.geographies, self.all_nodes], names=[cfg.cfgfile.get('case','primary_geography')+"_supply",'supply_node'])  
        columns = pd.MultiIndex.from_product([self.geographies,keys], names=[self.geography,'final_energy'])
        self.embodied_cost_link_dict = util.recursivedict()
        self.embodied_energy_link_dict = util.recursivedict()
        for year in self.years:
            for sector in self.demand_sectors:
                self.embodied_cost_link_dict[year][sector] = util.empty_df(index = index, columns = columns)
                self.embodied_energy_link_dict[year][sector] = util.empty_df(index = index, columns = columns)
        
    
    def create_embodied_emissions_demand_link(self):
        map_dict = dict(util.sql_read_table('SupplyNodes',['final_energy_link','id']))
        if None in map_dict.keys():
            del map_dict[None]
        #sorts final energy in the same order as the supply node dataframes
        keys = sorted(map_dict.items(), key=operator.itemgetter(1))
        keys = [x[0] for x in keys]
        index = pd.MultiIndex.from_product([self.geographies, self.all_nodes, self.ghgs], names=[cfg.cfgfile.get('case','primary_geography')+"_supply",'supply_node','ghg'])   
        columns = pd.MultiIndex.from_product([self.geographies,keys], names=[self.geography,'final_energy'])
        self.embodied_emissions_link_dict = util.recursivedict()
        for year in self.years:
            for sector in self.demand_sectors:
                self.embodied_emissions_link_dict[year][sector] = util.empty_df(index = index, columns = columns)
                
                
    def map_demand_to_io(self):
        """maps final energy demand ids to node nodes for IO table demand calculation"""    
        #loops through all final energy types in demand df and adds 
        map_dict = dict(util.sql_read_table('SupplyNodes',['final_energy_link','id']))
        self.demand_df = self.demand_object.energy_demand.unstack(level='year')   
        self.demand_df.columns = self.demand_df.columns.droplevel()       
        for demand_sector, geography, final_energy in self.demand_df.groupby(level = self.demand_df.index.names).groups:        
            supply_indexer = util.level_specific_indexer(self.io_demand_df, levels=[cfg.cfgfile.get('case', 'primary_geography'), 'demand_sector','supply_node'],elements=[geography, demand_sector, map_dict[final_energy]])      
            demand_indexer =  util.level_specific_indexer(self.demand_df, levels = [ 'sector', cfg.cfgfile.get('case', 'primary_geography'), 'final_energy'],elements=[demand_sector, geography, final_energy])  
            self.io_demand_df.loc[supply_indexer, self.years] = self.demand_df.loc[demand_indexer, self.years].values

                
    def map_export_to_io(self,year, loop):
        """maps specified export ubsector nodes for IO table total demand calculation"""    
        for node in self.nodes.values():
            supply_indexer = util.level_specific_indexer(self.io_export_df, 'supply_node', node.id)     
            node.export.allocate(node.active_supply, self.demand_sectors, self.years, year, loop)
            self.io_export_df.loc[supply_indexer, year] = node.export.active_values.values
            

        
class Node(DataMapFunctions):
    def __init__(self, id, supply_type, **kwargs):
        self.id = id    
        self.supply_type = supply_type
        for col, att in util.object_att_from_table('SupplyNodes', id):
            setattr(self, col, att)
        self.geography = cfg.cfgfile.get('case', 'primary_geography')
        self.active_supply=None
        self.reconciled = False
        self.add_conversion()

        if self.tradable_geography is None:
            self.enforce_tradable_geography = False
            self.tradable_geography = self.geography
        else:
            self.enforce_tradable_geography = True
        
        if self.shape_id is not None:
            self.shape = shapes.data[self.shape_id]
            shapes.activate_shape(self.shape_id)

    def add_conversion(self):
        """
        adds a dataframe used to convert input values that are not in energy terms, to energy terms
        ex. Biomass input as 'tons' must be converted to energy units using a conversion factor data table
        """
        energy_unit = cfg.cfgfile.get('case', "energy_unit")
        potential_unit = util.sql_read_table('SupplyPotential', 'unit', supply_node_id=self.id)
            # check to see if unit is in energy terms, if so, no conversion necessary
        if potential_unit is not None:
            if cfg.ureg.Quantity(potential_unit).dimensionality == cfg.ureg.Quantity(energy_unit).dimensionality:
                self.conversion = None
                self.resource_unit = None
            else:
                # if the unit is not in energy terms, create a conversion class to convert to energy units
                self.conversion = SupplyEnergyConversion(self.id, potential_unit)
                self.resource_unit = potential_unit
        else:
            self.conversion = None
            self.resource_unit = None

    def aggregate_electricity_shapes(self, year, dispatch_feeder_allocation):
        """ returns a single shape for a year with supply_technology and resource_bin removed and dispatch_feeder added
        ['dispatch_feeder', 'timeshift_type', 'gau', 'weather_datetime']
        """
        if 'demand_sector' in self.stock.values_energy:
            stock_values_energy = util.remove_df_levels(DfOper.mult([self.stock.values_energy[year],dispatch_feeder_allocation]),'demand_sector')                    
        else:
            stock_values_energy = self.stock.values_energy[year]
        if self.shape_id is None:
            index = pd.MultiIndex.from_product([cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')],[2],shapes.active_dates_index], names=[self.geography,'timeshift_type','weather_datetime'])
            energy_shape = util.empty_df(fill_value=1/float(len(shapes.active_dates_index)),index=index, columns=['value'])
        # we don't have technologies or none of the technologies have specific shapes
        elif not hasattr(self, 'technologies') or np.all([tech.shape_id is None for tech in self.technologies.values()]):
            if 'resource_bins' in self.shape.values.index.names and 'resource_bins' not in self.stock.stock.values.index.names:
                raise ValueError('Shape for %s has resource bins but the stock in this supply node does not have resource bins as a level' %self.name) 
            elif 'resource_bins' in self.stock.values.index.names and 'resource_bins' not in self.shape.index.names:  
                energy_shape = self.shape.values
            elif 'resource_bins' in self.stock.values.index.names and 'resource_bins' in self.shape.index.names:   

                energy_slice = util.remove_df_levels(stock_values_energy, ['vintage', 'supply_technology']).to_frame()
                energy_slice.columns = ['value']
                energy_shape = util.DfOper.mult([energy_slice, self.shape.values])
                energy_shape = util.remove_df_levels(energy_shape, 'resource_bins')
                energy_shape = DfOper.divi(energy_shape, util.remove_df_levels(energy_slice, 'resource_bins'))
            else:
                energy_shape = self.shape.values
        else:
            energy_slice = util.remove_df_levels(stock_values_energy, 'vintage').to_frame()
            energy_slice.columns = ['value']
            techs_with_default_shape = [tech_id for tech_id, tech in self.technologies.items() if tech.shape_id is None]
            techs_with_own_shape = [tech_id for tech_id, tech in self.technologies.items() if tech.shape_id is not None]           
            if techs_with_default_shape:
                energy_slice_default_shape = util.df_slice(energy_slice, techs_with_default_shape, 'supply_technology')
                energy_slice_default_shape = util.remove_df_levels(energy_slice_default_shape, 'supply_technology')
                default_shape_portion = util.DfOper.mult([energy_slice_default_shape, self.shape.values])
                default_shape_portion = util.remove_df_levels(default_shape_portion, 'resource_bins')
            if techs_with_own_shape:
                energy_slice_own_shape = util.df_slice(energy_slice, techs_with_own_shape, 'supply_technology')
                tech_shapes = pd.concat([self.technologies[tech_id].shape.values for tech_id in techs_with_own_shape])
                tech_shape_portion = util.DfOper.mult([energy_slice_own_shape, tech_shapes])
                tech_shape_portion = util.remove_df_levels(tech_shape_portion, 'supply_technology', 'resource_bins')
            df = util.DfOper.add([default_shape_portion if techs_with_default_shape else None,
                                  tech_shape_portion if techs_with_own_shape else None],
                                  expandable=False, collapsible=False)
            energy_shape = DfOper.divi([df, util.remove_df_levels(energy_slice,['vintage','supply_technology','resource_bins'])])
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
                if 'resource_bins' in self.shape.values.index.names and 'resource_bins' not in self.stock.values.index.names:
                    raise ValueError('Shape for %s has resource bins but the stock in this supply node does not have resource bins as a level' %self.name)
                elif 'resource_bins' in self.stock.values.index.names and 'resource_bins' not in self.shape.values.index.names:
                    energy_shape = self.shape.values
                elif 'resource_bins' not in self.stock.values.index.names:
                    energy_shape = self.shape.values
                elif 'resource_bins' in self.stock.values.index.names and 'resource_bins' in self.shape.values.index.names:
                    energy_slice = util.remove_df_levels(stock_values_energy[year], ['vintage', 'supply_technology']).to_frame()
                    energy_slice.columns = ['value']
                    energy_shape = util.DfOper.mult([energy_slice, self.shape.values])
                    energy_shape = util.remove_df_levels(energy_shape, 'resource_bins')
                    energy_shape = DfOper.div([energy_shape, util.remove_df_levels(energy_slice,'resource_bins')])
                p_max_shape = None
                p_min_shape = None
            else:
                energy_shape, p_max_shape, p_min_shape = self.calculate_disp_constraints_shape(year, stock_values, stock_values_energy)
        else:
            if 'dispatch_constraint' not in self.shape.values.index.names: 
                energy_slice = util.remove_df_levels(self.stock.values_energy[year], 'vintage').to_frame()
                energy_slice.columns = ['value']
                techs_with_default_shape = [tech_id for tech_id, tech in self.technologies.items() if tech.shape_id is None or 'dispatch_constraint' in shapes.data[tech.shape_id].df_index_names]
                techs_with_own_shape = [tech_id for tech_id, tech in self.technologies.items() if tech.shape_id is not None and 'dispatch_constraint' not in shapes.data[tech.shape_id].df_index_names]     
                if techs_with_default_shape:
                    energy_slice_default_shape = util.df_slice(energy_slice, techs_with_default_shape, 'supply_technology')
                    energy_slice_default_shape = util.remove_df_levels(energy_slice_default_shape, 'supply_technology')
                    default_shape_portion = util.DfOper.mult([energy_slice_default_shape, self.shape.values])
                    default_shape_portion = util.remove_df_levels(default_shape_portion, 'resource_bins')
                if techs_with_own_shape:
                    energy_slice_own_shape = util.df_slice(energy_slice, techs_with_own_shape, 'supply_technology')
                    tech_shapes = pd.concat([self.technologies[tech_id].shape.values for tech_id in techs_with_own_shape])
                    tech_shape_portion = util.DfOper.mult([energy_slice_own_shape, tech_shapes])
                    tech_shape_portion = util.remove_df_levels(tech_shape_portion, 'supply_technology', 'resource_bins')
                #TODO check with Ryan why this is not exapandable        
                energy_shape = util.DfOper.add([default_shape_portion if techs_with_default_shape else None,
                                  tech_shape_portion if techs_with_own_shape else None],
                                  expandable=False, collapsible=False)
                energy_shape = util.DfOper.divi([energy_shape,util.remove_df_levels(self.stock.values_energy,['vintage','supply_technology','resource_bins'])])
                p_max_shape = None
                p_min_shape = None
            else:
                energy_shape, p_min_shape, p_max_shape,  = self.calculate_disp_constraints_shape(self,year, stock_values, stock_values_energy)                
        return energy_shape,  p_min_shape , p_max_shape
        
    def calculate_disp_constraints_shape(self,year, stock_values, stock_values_energy):
            if 'resource_bins' in self.shape.values.index.names and 'resource_bins' not in self.stock.values.index.names:
                raise ValueError('Shape for %s has resource bins but the stock in this supply node does not have resource bins as a level' %self.name)
            elif 'resource_bins' in self.stock.values.index.names and 'resource_bins' not in self.shape.values.index.names:       
                energy_shape = util.df_slice(self.shape.values,1,'dispatch_constraint')
                p_max_shape = util.df_slice(self.shape.values,2,'dispatch_constraint')
                p_min_shape = util.df_slice(self.shape.values,3,'dispatch_constraint')             
            elif 'resource_bins' in self.stock.values.index.names and 'resource_bins' in self.shape.values.index.names:
                energy_slice = util.remove_df_levels(stock_values_energy, ['vintage', 'supply_technology']).to_frame()
                energy_slice.columns = ['value']
                energy_shape = util.DfOper.mult([energy_slice, util.df_slice(self.shape.values,1,'dispatch_constraint')])
                energy_shape = util.remove_df_levels(energy_shape, 'resource_bins')
                energy_shape = DfOper.div([energy_shape, util.remove_df_levels(energy_slice,'resource_bins')])
                capacity_slice = util.remove_df_levels(stock_values, ['vintage', 'supply_technology']).to_frame()                
                capacity_slice.columns = ['value']
                p_min_shape = util.DfOper.mult([capacity_slice, util.df_slice(self.shape.values,2,'dispatch_constraint')])
                p_min_shape = util.remove_df_levels(p_min_shape, 'resource_bins')
                p_min_shape = DfOper.div([p_min_shape, util.remove_df_levels(capacity_slice,'resource_bins')])
                p_max_shape = util.DfOper.mult([capacity_slice, util.df_slice(self.shape.values,3,'dispatch_constraint')])
                p_max_shape = util.remove_df_levels(p_max_shape, 'resource_bins')
                p_max_shape = DfOper.div([p_max_shape, util.remove_df_levels(capacity_slice,'resource_bins')])
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
                self.active_coefficients = util.remove_df_levels(DfOper.mult([self.coefficients.values.groupby(level=[cfg.cfgfile.get('case', 'primary_geography'),  'demand_sector', 'efficiency_type','supply_node']).sum().loc[:,year].to_frame(),
                                                    self.potential.active_supply_curve_normal]),'resource_bins')
            else:
                self.active_coefficients = None     
        elif self.coefficients.data is True: 
            self.active_coefficients =  self.coefficients.values.groupby(level=[cfg.cfgfile.get('case', 'primary_geography'),  'demand_sector', 'efficiency_type','supply_node']).sum().loc[:,year].to_frame()
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
            self.active_coefficients = DfOper.mult([self.active_coefficients,active_trade_adjustment_df])
            keys = self.ghgs
            name = ['ghg']
            self.active_emissions_coefficients = pd.concat([self.active_coefficients]*len(keys), keys=keys, names=name)
            self.active_emissions_coefficients = self.active_emissions_coefficients.reorder_levels([self.geography,'demand_sector', 'supply_node', 'efficiency_type', 'ghg'])
            self.active_emissions_coefficients.sort(inplace=True)
        else:
            self.active_coefficients_total = None
            self.active_emissions_coefficients = None
        
            
            
    def add_column_index(self, data):
         names = ['demand_sector', cfg.cfgfile.get('case','primary_geography')]
         keys = [self.demand_sectors, cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')]]
         data  = copy.deepcopy(data)
         for key,name in zip(keys,names):
             data  = pd.concat([data]*len(key), axis=1, keys=key, names=[name])
         data.columns = data.columns.droplevel(-1)
         return data
            
    def filter_packages(self, case_data_table, node_key, case_id):
        """filters packages by case"""
        packages = [x for x in util.sql_read_headers(case_data_table) if x not in ['parent_id', 'id', node_key]]
        for package in packages:
            package_id = util.sql_read_table(case_data_table, package, supply_node_id=self.id, parent_id=case_id)
            setattr(self, package, package_id)
    
    def add_export_measures(self):
            """
            add all export measures in a selected package to a dictionary
            """
            self.export_measures = {}
            cfg.cur.execute('select measure_id from "SupplyExportMeasurePackagesData" where package_id=%s',
                                           (self.export_package_id,))
            ids = [id for id in cfg.cur.fetchall()]
            for (id,) in ids:
                self.add_export_measure(id)     
        
    def add_export_measure(self, id, **kwargs):
        """Adds measure instances to node"""
        if id in self.export_measures:
            return
        self.export_measures[id] = ExportMeasure(id)      
        
    def add_exports(self):
        if len(self.export_measures.keys()):
            self.export = Export(self.id,measure_id=self.export_measures.keys())
        else:
            self.export = Export(self.id)
                
    def convert_stock(self, stock_name='stock', attr='total'):
        model_energy_unit = cfg.cfgfile.get('case', 'energy_unit')
        model_time_step = cfg.cfgfile.get('case', 'time_step')
        stock = getattr(self,stock_name)
        if stock.time_unit is not None:
            # if a stock has a time_unit, then the unit is energy and must be converted to capacity
            setattr(stock, attr, util.unit_convert(getattr(stock, attr), unit_from_num=stock.capacity_or_energy_unit, unit_from_den=stock.time_unit, 
                                             unit_to_num=model_energy_unit, unit_to_den=model_time_step))
        else:
            # if a stock is a capacity unit, the model must convert the unit type to an energy unit for conversion ()
            setattr(stock, attr, util.unit_convert(getattr(stock, attr), unit_from_num=cfg.ureg.Quantity(stock.capacity_or_energy_unit)*cfg.ureg.Quantity(model_time_step), unit_from_den=model_time_step, 
                                             unit_to_num=model_energy_unit, unit_to_den=model_time_step))
        setattr(stock, attr, getattr(stock, attr).unstack('year'))
        getattr(stock, attr).columns = getattr(stock, attr).columns.droplevel()   

    def calculate_potential_constraints(self, year):
        """calculates the exceedance factor of a node if the node active supply exceeds the potential in the node. This adjustment factor
        is passed to other nodes in the reconcile step"""
        if hasattr(self,'potential') and self.potential.data is True:
            #geomap potential to the tradable geography. Potential is not exceeded unless it is exceeded in a tradable geography region. 
            active_geomapped_potential, active_geomapped_supply = self.potential.format_potential_and_supply_for_constraint_check(self.active_supply, self.tradable_geography, year)           
            self.potential_exceedance = DfOper.subt([active_geomapped_supply,active_geomapped_potential], expandable = (False,False), collapsible = (True, True))
            #reformat dataframes for a remap
            self.potential_exceedance[self.potential_exceedance<0] = 0
            remap_active = pd.DataFrame(self.potential.active_potential.stack(), columns=['value'])
            util.replace_index_name(remap_active, 'year')
            self.potential_exceedance= pd.DataFrame(self.potential_exceedance.stack(), columns=['value'])
            util.replace_index_name(self.potential_exceedance, 'year')
            #remap excess supply to the active potential to allocate excess
            self.remap(current_geography=self.tradable_geography, fill_timeseries=False, map_from='potential_exceedance',map_to='potential_exceedance', drivers=remap_active, current_data_type='total')
            #divide the potential exceedance by the active supply
            self.potential_exceedance = DfOper.divi([self.potential_exceedance, self.active_supply], expandable = (False,False), collapsible = (True, True))        
            #if less than or equal to 0, then there is no exceedance
            self.potential_exceedance[self.potential_exceedance>1] = 1
            self.potential_exceedance = 1 - self.potential_exceedance
            keys = [self.demand_sectors, cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')]]
            names = ['demand_sector', cfg.cfgfile.get('case','primary_geography')]
            potential_exceedance = copy.deepcopy(self.potential_exceedance)
            for key,name in zip(keys,names):
                potential_exceedance  = pd.concat([potential_exceedance]*len(key), axis=1, keys=key, names=[name])
            self.potential_exceedance = potential_exceedance 
            self.potential_exceedance.columns = self.potential_exceedance.columns.droplevel(-1)      
            self.active_constraint_df = self.potential_exceedance
            if 'demand_sector' not in self.active_constraint_df.index.names:
                keys = self.demand_sectors
                name = ['demand_sector']
                active_constraint_df = pd.concat([self.active_constraint_df]*len(keys), keys=keys, names=name)
                active_constraint_df= active_constraint_df.swaplevel('demand_sector',-1)
                self.active_constraint_df = active_constraint_df
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
        model_geography = cfg.cfgfile.get('case', 'primary_geography')
        if self.tradable_geography!= model_geography and ((hasattr(self,'potential') and self.potential.data) or (hasattr(self,'stock') and self.stock.data)):
            #tradable supply is mapping of active supply to a tradable geography    
            self.geo_step1 = cfg.geo.map_df(self.tradable_geography,cfg.cfgfile.get('case', 'primary_geography'),eliminate_zeros=False)
            if self.potential.data is True:
                 self.geo_step2 = DfOper.mult([util.remove_df_levels(self.potential.active_supply_curve,'resource_bins'),cfg.geo.map_df(cfg.cfgfile.get('case', 'primary_geography'),self.tradable_geography)])
                 util.replace_index_name(self.geo_step2,cfg.cfgfile.get('case', 'primary_geography') + "from", cfg.cfgfile.get('case', 'primary_geography'))         
                 #if a node has potential, this becomes the basis for remapping
            elif self.stock.data is True:
                self.geo_step2 = DfOper.mult([self.stock.total_clean.loc[:,year].to_frame(),cfg.geo.map_df(cfg.cfgfile.get('case', 'primary_geography'),self.tradable_geography, eliminate_zeros=False)])
                util.replace_index_name(self.geo_step2,cfg.cfgfile.get('case', 'primary_geography') + "from", cfg.cfgfile.get('case', 'primary_geography'))  
            self.geo_step2 = self.geo_step2.groupby(level=util.ix_excl(self.geo_step2,cfg.cfgfile.get('case', 'primary_geography') + "from")).transform(lambda x: x/x.sum()).fillna(0)
            self.geomapped_coefficients = DfOper.mult([self.geo_step1, self.geo_step2])     
            self.geomapped_coefficients = self.geomapped_coefficients.unstack(cfg.cfgfile.get('case', 'primary_geography'))
            util.replace_index_name(self.geomapped_coefficients,cfg.cfgfile.get('case', 'primary_geography'),cfg.cfgfile.get('case', 'primary_geography') + "from")
            self.geomapped_coefficients = util.remove_df_levels(self.geomapped_coefficients,self.tradable_geography)              
            self.geomapped_coefficients.columns = self.geomapped_coefficients.columns.droplevel()              
            self.active_internal_trade_df= self.internal_trade_dict[year]                
            ind_dict = dict([(n, i) for i, n in enumerate(self.geomapped_coefficients.index.names)])
            for ind, value in self.geomapped_coefficients.iterrows():
                ind = util.ensure_iterable_and_not_string(ind)
                row_lookup = tuple([ind[ind_dict[n]] if n in ind_dict else slice(None) for n in self.active_internal_trade_df.index.names])
                for c, v in value.iteritems():
                    self.active_internal_trade_df.loc[row_lookup, c] = v
            for sector_row in self.demand_sectors:
                for sector_column in self.demand_sectors:
                    row_indexer = util.level_specific_indexer(self.active_internal_trade_df,'demand_sector', sector_row)
                    col_indexer = util.level_specific_indexer(self.active_internal_trade_df,'demand_sector', sector_column)   
                    if sector_row == sector_column:
                        mult =1 
                    else:
                        mult=0
                    self.active_internal_trade_df.loc[row_indexer, col_indexer] *= mult
            self.internal_trades = "stop and feed"
        elif self.tradable_geography != model_geography:
            self.internal_trades = "stop"
        elif self.tradable_geography == model_geography and self.enforce_tradable_geography:
            self.internal_trades = "stop"
        else:
            self.internal_trades = "feed"


    def calculate_input_emissions_rates(self,year,ghgs):
        self.geographies = cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')]
        self.geography = cfg.cfgfile.get('case','primary_geography')
        "calculates the emissions rate of nodes with emissions"
        if hasattr(self,'emissions') and self.emissions.data is True:
            if hasattr(self,'potential') and self.potential.data is True:
                self.active_physical_emissions_rate = DfOper.mult([self.potential.active_supply_curve_normal,self.emissions.values_physical.loc[:,year].to_frame()])
                levels = ['demand_sector',self.geography,'ghg']
                disallowed_levels = [x for x in self.active_physical_emissions_rate.index.names if x not in levels]
                if len(disallowed_levels):
                    self.active_physical_emissions_rate = util.remove_df_levels(self.active_physical_emissions_rate, disallowed_levels)
                self.active_physical_emissions_rate = util.expand_multi(self.active_physical_emissions_rate, levels_list = [cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')], self.demand_sectors, self.ghgs],levels_names=[cfg.cfgfile.get('case', 'primary_geography'),'demand_sector', 'ghg'])               
                self.active_accounting_emissions_rate = DfOper.mult([self.potential.active_supply_curve_normal,self.emissions.values_accounting.loc[:,year].to_frame()])
                levels = ['demand_sector',cfg.cfgfile.get('case','primary_geography'),'ghg']
                disallowed_levels = [x for x in self.active_accounting_emissions_rate.index.names if x not in levels]
                if len(disallowed_levels):
                    self.active_accounting_emissions_rate = util.remove_df_levels(self.active_accounting_emissions_rate, disallowed_levels)
                self.active_accounting_emissions_rate = util.expand_multi(self.active_accounting_emissions_rate, levels_list = [cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')], self.demand_sectors, self.ghgs], levels_names=[cfg.cfgfile.get('case', 'primary_geography'),'demand_sector','ghg'])
            else:
                allowed_indices = ['demand_sector', self.geography, 'ghg', 'ghg_type']
                if set(self.emissions.values_physical.index.names).issubset(allowed_indices):
                    self.active_physical_emissions_rate = util.remove_df_levels(self.emissions.values_physical.loc[:,year].to_frame(), 'ghg_type')
                    self.active_physical_emissions_rate = util.expand_multi(self.active_physical_emissions_rate, levels_list = [self.geographies, self.demand_sectors, self.ghgs],levels_names=[self.geography,'demand_sector', 'ghg'])
                if set(self.emissions.values_accounting.index.names).issubset(allowed_indices):     
                    self.active_accounting_emissions_rate =  util.remove_df_levels(self.emissions.values_accounting.loc[:,year].to_frame(), 'ghg_type')
                    self.active_accounting_emissions_rate = util.expand_multi(self.active_accounting_emissions_rate, levels_list = [self.geographies, self.demand_sectors, self.ghgs],levels_names=[self.geography,'demand_sector', 'ghg'])
                else:
                    raise ValueError("too many indexes in emissions inputs of node %s" %self.id)
            keys = [self.demand_sectors, self.geographies]
            names = ['demand_sector', self.geography]
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
                if self.active_physical_emissions_coefficients.loc[indexer,:].sum().sum()<>0:
                    combustion_emissions = copy.deepcopy(self.active_physical_emissions_coefficients.loc[indexer,:])
                    combustion_emissions.loc[:,:] = self.active_supply.T.values * self.active_physical_emissions_coefficients.loc[indexer,:].values
                    self.active_combustion_emissions = combustion_emissions.groupby(level='ghg').sum() 
                    self.active_combustion_emissions = self.active_combustion_emissions.unstack(self.geography).to_frame()
                    if hasattr(self,'calculate_co2_capture_rate'):
                        self.calculate_co2_capture_rate(year)
                        self.active_combustion_emissions = DfOper.mult([self.active_combustion_emissions, 1- self.active_co2_capture_rate])
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
        self.set_constraint_adjustment_dict()
        self.set_constraint_dict()

    def set_trade_adjustment_dict(self):
        """sets an empty df with a fill value of 1 for trade adjustments"""
        if hasattr(self,'nodes'):
            self.trade_adjustment_dict = defaultdict(dict)        
            row_index = pd.MultiIndex.from_product([cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')], self.demand_sectors, self.nodes], names=[cfg.cfgfile.get('case','primary_geography'), 'demand_sector', 'supply_node'])
            col_index = pd.MultiIndex.from_product([cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')], self.demand_sectors], names=[cfg.cfgfile.get('case','primary_geography'), 'demand_sector'])
            trade_adjustment_df = util.empty_df(index=row_index,columns=col_index,fill_value=0.0)
            trade_adjustment_df.sort(inplace=True, axis=0)
            trade_adjustment_df.sort(inplace=True, axis=1)
            trade_adjustment_groups = trade_adjustment_df.groupby(level=trade_adjustment_df.index.names).groups
            for elements in trade_adjustment_groups.keys():
                row_indexer = util.level_specific_indexer(trade_adjustment_df, trade_adjustment_df.index.names, elements)
                col_indexer = util.level_specific_indexer(trade_adjustment_df,[cfg.cfgfile.get('case','primary_geography'), 'demand_sector'], elements[:-1], axis=1)            
                trade_adjustment_df.loc[row_indexer, col_indexer] = 1.0  
            for year in self.years:      
               self.trade_adjustment_dict[year] = copy.deepcopy(trade_adjustment_df) 
            self.active_trade_adjustment_df = trade_adjustment_df 
            
    def set_constraint_adjustment_dict(self):
        """sets an empty df with a fill value of 1 for constraint adjustments"""
        if self.supply_type == 'Blend':
            self.constraint_adjustment_dict = defaultdict(dict)        
            row_index = pd.MultiIndex.from_product([cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')], self.demand_sectors, self.nodes], names=[cfg.cfgfile.get('case','primary_geography'), 'demand_sector', 'supply_node'])
            col_index = pd.MultiIndex.from_product([cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')], self.demand_sectors], names=[cfg.cfgfile.get('case','primary_geography'), 'demand_sector'])
            constraint_adjustment_df = util.empty_df(index=row_index,columns=col_index,fill_value=1.0)
            constraint_adjustment_df.sort(inplace=True, axis=0)
            constraint_adjustment_df.sort(inplace=True, axis=1)
            for year in self.years:        
               self.constraint_adjustment_dict[year] = copy.deepcopy(constraint_adjustment_df) 
            self.active_constraint_adjustment_df = constraint_adjustment_df 
                 
    def set_internal_trade_dict(self):
        """sets an empty df with a fill value of 1 for internal trades"""
        if self.tradable_geography is not None:
            self.internal_trade_dict = defaultdict(dict)
            index = pd.MultiIndex.from_product([cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')], self.demand_sectors], names=[cfg.cfgfile.get('case','primary_geography'), 'demand_sector'])
            internal_trade_df = util.empty_df(index=index,columns=index,fill_value=0.0)
            internal_trade_df.sort(inplace=True, axis=0)
            internal_trade_df.sort(inplace=True, axis=1)
            internal_trade_groups = internal_trade_df.groupby(level=internal_trade_df.index.names).groups
            for elements in internal_trade_groups.keys():
                row_indexer = util.level_specific_indexer(internal_trade_df, internal_trade_df.index.names, elements)
                col_indexer = util.level_specific_indexer(internal_trade_df,[cfg.cfgfile.get('case','primary_geography'), 'demand_sector'], list(elements), axis=1)            
                internal_trade_df.loc[row_indexer, col_indexer] = 1.0  
            for year in self.years:
                self.internal_trade_dict[year] = copy.deepcopy(internal_trade_df)
            self.active_internal_trade_df = internal_trade_df 
        
    def set_constraint_dict(self):
        """sets an empty df with a fill value of 1 for potential constraints"""
        if hasattr(self, 'potential') and self.potential.data is True:
            self.constraint_dict = defaultdict(dict)
            index = pd.MultiIndex.from_product([cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')], self.demand_sectors], names=[cfg.cfgfile.get('case','primary_geography'), 'demand_sector'])
            constraint_df= util.empty_df(index=index,columns=index,fill_value=0.0)
            constraint_df.sort(inplace=True, axis=0)
            constraint_df.sort(inplace=True, axis=1)
            for year in self.years:
                self.constraint_dict[year] = copy.deepcopy(constraint_df)
            self.active_constraint_df = constraint_df  
        
    def set_pass_through_df_dict(self):    
        """sets an empty df with a fill value of 1 for trade adjustments"""
        self.pass_through_df_dict = defaultdict(dict)
        row_index = pd.MultiIndex.from_product([cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')], self.demand_sectors, self.ghgs], names=[cfg.cfgfile.get('case','primary_geography'), 'demand_sector', 'ghg'])
        col_index = pd.MultiIndex.from_product([cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')], self.demand_sectors], names=[cfg.cfgfile.get('case','primary_geography'), 'demand_sector'])
        pass_through_df = util.empty_df(index=row_index,columns=col_index,fill_value=0.0)
        pass_through_df.sort(inplace=True, axis=0)
        pass_through_df.sort(inplace=True, axis=1)
        for year in self.years:
            self.pass_through_df_dict[year] = copy.deepcopy(pass_through_df)
        self.active_pass_through_df = pass_through_df  
        
    def update_pass_through_df_dict(self,year):  
        if hasattr(self,'pass_through_df_dict'):
            self.active_pass_through_df = self.pass_through_df_dict[year]
    
    def set_pass_through_dict(self, node_dict):   
        if self.active_coefficients is not None:
            self.active_coefficients = self.active_coefficients.sort()
            if 2 in set(self.active_coefficients.index.get_level_values('efficiency_type')):    
                indexer = util.level_specific_indexer(self.active_coefficients,'efficiency_type',2)
                pass_through_subsectors = self.active_coefficients.loc[indexer,:].index.get_level_values('supply_node')
                pass_through_subsectors = [int(x) for x in pass_through_subsectors if node_dict.has_key(x)]                
                self.pass_through_dict = dict.fromkeys(pass_through_subsectors,False)  
            

        
class  Export(Abstract):
    def __init__(self,node_id, measure_ids=None, **kwargs):
        self.id = node_id
        self.input_type = 'total'
        if measure_ids is None:
            self.sql_id_table = 'SupplyExport'
            self.sql_data_table = 'SupplyExportData'
            Abstract.__init__(self, self.id, primary_key='supply_node_id')
        else:
            self.sql_id_table = 'SupplyExportMeasures'
            self.sql_data_table = 'SupplyExportMeasuresData'
            Abstract.__init__(self, self.id, primary_key='supply_node_id', data_id_key='parent_id', measure_id=measure_ids)
            
    def calculate(self, years, demand_sectors):
        self.years = years
        self.demand_sectors = demand_sectors
        if self.data is True:
            self.remap()
            self.convert()
        else:
            self.set_export_df()
            self.geography = cfg.cfgfile.get('case', 'primary_geography')
            
            
    def convert(self):        
       self.values = self.values.unstack(level='year')    
       self.values.columns = self.values.columns.droplevel()
       self.values = util.unit_convert(self.values, unit_from_num=self.unit, unit_to_num=cfg.cfgfile.get('case','energy_unit'))

    def set_export_df(self):
        """sets an empty df with a fill value of 0"""
        df_index = pd.MultiIndex.from_product([cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')], self.demand_sectors], names=[cfg.cfgfile.get('case','primary_geography'), 'demand_sector'])
        self.values= util.empty_df(index=df_index, columns=self.years, fill_value=0)

    def allocate(self, active_supply, demand_sectors, supply_years, year, loop):
        """Performs sectoral allocation of active export values. In year 1/loop1, this happens equally across sectors. Once throughput is known, it is allocated by throughput"""
        if year == min(supply_years) and loop == 'initial':   
            if 'demand_sector' not in self.values.index.names:
                active_values = []
                for sector in self.demand_sectors:
                    #if we have no active supply, we must allocate exports pro-rate across number of sectors
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
            self.remap(map_from='active_values', map_to='active_values', drivers=active_supply, fill_timeseries=False, current_geography=cfg.cfgfile.get('case', 'primary_geography'))
        self.active_values.replace(np.nan,0,inplace=True)
        self.active_values = self.active_values.reorder_levels([cfg.cfgfile.get('case', 'primary_geography'),'demand_sector'])

           
class BlendNode(Node):
    def __init__(self, id, supply_type, **kwargs):
        Node.__init__(self, id, supply_type)
        self.id = id
        self.supply_type = supply_type
        for col, att in util.object_att_from_table('SupplyNodes', id, ):
            setattr(self, col, att)
        self.nodes = util.sql_read_table('BlendNodeInputsData', 'supply_node_id', blend_node_id=id)
        #used as a flag in the annual loop for whether we need to recalculate the coefficients
   
            
    def calculate_active_coefficients(self, year, loop):
#            if self.reconciled is True:
#            #after the first loop, we have to update the residual calc if the node has been reconciled       
#                self.update_reconciled_residual(year)
            self.active_coefficients = self.values.loc[:,year].to_frame()
            self.active_coefficients_total_untraded = util.remove_df_levels(self.active_coefficients,'efficiency_type')       
            self.active_coefficients_untraded = copy.deepcopy(self.active_coefficients) 
            self.active_coefficients_untraded.sort(inplace=True,axis=0)
            self.active_coefficients = self.add_column_index(self.active_coefficients_untraded)
            self.active_coefficients_total = self.add_column_index(self.active_coefficients_total_untraded)
            self.active_coefficients_total_emissions_rate = copy.deepcopy(self.active_coefficients_total)            
            self.active_coefficients_total = DfOper.mult([self.active_coefficients_total,self.active_trade_adjustment_df, self.active_constraint_adjustment_df])
            keys = [2]
            name = ['efficiency_type']
            active_trade_adjustment_df = pd.concat([self.active_trade_adjustment_df]*len(keys), keys=keys, names=name)
            active_constraint_adjustment_df = pd.concat([self.active_constraint_adjustment_df]*len(keys), keys=keys, names=name)
            self.active_coefficients = DfOper.mult([self.active_coefficients,active_trade_adjustment_df, active_constraint_adjustment_df])
            keys = self.ghgs
            name = ['ghg']
            self.active_emissions_coefficients = pd.concat([self.active_coefficients]*len(keys), keys=keys, names=name)
            self.active_emissions_coefficients = self.active_emissions_coefficients.reorder_levels([self.geography, 'demand_sector', 'supply_node', 'efficiency_type', 'ghg'])
            self.active_emissions_coefficients.sort(inplace=True)
            
    def add_blend_measures(self):
            """
            add all blend measures in a selected package to a dictionary
            """
            self.blend_measures = {}
            cfg.cur.execute('select measure_id from "BlendNodeBlendMeasurePackagesData" where package_id=%s',
                                           (self.blend_package_id,))
            ids = [id for id in cfg.cur.fetchall()]
            for (id,) in ids:
                self.add_blend_measure(id)     
            
    def add_blend_measure(self, id, **kwargs):
        """Adds measure instances to node"""
        if id in self.blend_measures:
            return
        self.blend_measures[id] = BlendMeasure(id)            


            
    def calculate(self, years, demand_sectors, ghgs):
        self.years = years
        self.demand_sectors = demand_sectors
        self.ghgs = ghgs
        measures = []
        for measure in self.blend_measures.values():
            measure.calculate(self.vintages, self.years)
            measures.append(measure.values)
        if len(measures):
            self.values = pd.concat(measures)
            self.calculate_residual()
        else:
            self.set_residual()
        self.set_adjustments()
        self.set_pass_through_df_dict()
        attributes = vars(self)
        for att in attributes:
            obj = getattr(self, att)
            if inspect.isclass(type(obj)) and hasattr(obj, '__dict__') and hasattr(obj, 'calculate'):
                obj.calculate(self.years, self.demand_sectors)
                
    def calculate_residual(self):
         """calculates values for residual node in Blend Node dataframe
         ex. if 10% of hydrogen blend is supplied by electrolysis and the rest is unspecified,
         90% of hydrogen blend is allocated to residual node
         """
         # calculates sum of all supply_nodes
         # residual equals 1-sum of all other specified nodes
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

            
    def update_reconciled_residual(self, year):
        """calculates values for residual node in Blend Node dataframe
         ex. if 10% of hydrogen blend is supplied by electrolysis and the rest is unspecified,
         90% of hydrogen blend is allocated to residual node
         """
        # calculates sum of all supply_nodes
        self.calculate_active_coefficients(year,2)
        indexer = util.level_specific_indexer(self.active_coefficients_total, 'supply_node', self.residual_supply_node_id)    
        remainder = 1- self.active_coefficients_total.sum().to_frame()
        existing_residual = self.active_coefficients_total.loc[indexer,:].sum().to_frame()
        existing_residual.replace(0, 1e-7,inplace=True)
        growth_factor = DfOper.divi([DfOper.add([remainder,existing_residual]), existing_residual])
        indexer = util.level_specific_indexer(self.values.loc[:,year].to_frame(), 'supply_node', self.residual_supply_node_id)
        self.values[self.values <= 0] = 1e-7       
        self.values.loc[indexer,year] = DfOper.mult([self.values.loc[indexer, year].to_frame(), growth_factor]).values
        self.values[self.values <= 0] = 1e-7
         
         
    def expand_blend(self):
        #needs a fill value because if a node is not demanding any energy from another node, it still may be supplied, and reconciliation happens via division (can't multiply by 0)
        self.values = util.reindex_df_level_with_new_elements(self.values,'supply_node', self.nodes, fill_value = 1e-7)
        if 'demand_sector' not in self.values.index.names:
            self.values = util.expand_multi(self.values, self.demand_sectors, ['demand_sector'], incremental=True)
        self.values['efficiency_type'] = 2
        self.values.set_index('efficiency_type', append=True, inplace=True)
        self.values = self.values.reorder_levels([self.geography,'demand_sector','supply_node','efficiency_type','year'])
        self.values = self.values.sort()        
        
         
    def set_residual(self):
        """creats an empty df with the value for the residual node of 1. For nodes with no blend measures specified"""
        df_index = pd.MultiIndex.from_product([cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')], self.demand_sectors, self.nodes, self.years, [2]], names=[cfg.cfgfile.get('case','primary_geography'), 'demand_sector','supply_node','year','efficiency_type' ])
        self.values = util.empty_df(index=df_index,columns=['value'],fill_value=1e-7)
        indexer = util.level_specific_indexer(self.values, 'supply_node', self.residual_supply_node_id)
        self.values.loc[indexer, 'value'] = 1
        self.values = self.values.unstack(level='year')    
        self.values.columns = self.values.columns.droplevel()
        self.values = self.values.sort()
        
    
class SupplyNode(Node,StockItem):
    def __init__(self, id, supply_type, **kwargs):
        Node.__init__(self, id, supply_type)
        StockItem.__init__(self)
        self.input_type = 'total'
        self.coefficients = SupplyCoefficients(self.id)
        self.potential = SupplyPotential(self.id)
        self.capacity_factor = SupplyCapacityFactor(self.id)
        self.costs = {}
        self.create_costs()
        self.add_stock()

    def calculate(self,years, demand_sectors, ghgs, distribution_grid_node_id):
        self.years = years
        self.demand_sectors = demand_sectors
        self.ghgs = ghgs
        self.distribution_grid_node_id = distribution_grid_node_id

        self.set_rollover_groups()
        attributes = vars(self)
        for att in attributes:
            obj = getattr(self, att)
            if inspect.isclass(type(obj)) and hasattr(obj, '__dict__') and hasattr(obj, 'calculate'):
                obj.calculate(self.years, self.demand_sectors)
        for cost in self.costs.values():
            cost.calculate(self.years, self.demand_sectors)
        self.calculate_input_stock()
        self.setup_stock_rollover(self.years)
        if self.coefficients.data is True:
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
                if name == 'resource_bins' or name == 'demand_sector' :
                    self.rollover_group_levels.append(list(level))
                    self.rollover_group_names.append(name)            
        if self.stock.data is True:
            for name, level in zip(self.stock.raw_values.index.names, self.stock.raw_values.index.levels):
                if name == 'resource_bins' or name == 'demand_sector' :
                    self.rollover_group_levels.append(list(level))
                    self.rollover_group_names.append(name)
        for cost in self.costs.keys():
            for name, level in zip(self.costs[cost].raw_values.index.names, self.costs[cost].raw_values.index.levels):
                if name == 'resource_bins' or name == 'demand_sector':
                    self.rollover_group_levels.append(list(level))
                    self.rollover_group_names.append(name)
        if self.id == self.distribution_grid_node_id:
            #requires distribution grid node to maintain demand sector resolution in its stocks
            self.rollover_group_levels.append(self.demand_sectors)
            self.rollover_group_names.append('demand_sector')
        self.rollover_group_names = [cfg.cfgfile.get('case', 'primary_geography')] + self.rollover_group_names
        self.rollover_group_levels = [cfg.geo.geographies[cfg.cfgfile.get('case', 'primary_geography')]] + self.rollover_group_levels

    def add_stock_measure(self, package_id):
        measure_id = util.sql_read_table('SupplyStockMeasurePackagesData', 'measure_id', package_id=package_id, return_iterable=False)
        self.case_stock = Stock(id=measure_id, drivers=None, sql_id_table='SupplyStockMeasures', sql_data_table='SupplyStockMeasuresData', primary_key='id', data_id_key='parent_id')
        
    def add_stock(self):
        """add stock instance to node"""
        self.stock = Stock(id=self.id, drivers=None, sql_id_table='SupplyStock', sql_data_table='SupplyStockData', primary_key='supply_node_id')
        self.stock.input_type = 'total'
           
    def calculate_input_stock(self):
        levels = self.rollover_group_levels 
        names = self.rollover_group_names 
        index = pd.MultiIndex.from_product(levels,names=names)
        self.stock.years = self.years
        if self.stock.data is True:
            self.stock.remap(map_from='raw_values', map_to='total',fill_timeseries=True, interpolation_method=None,extrapolation_method=None, fill_value=np.nan)
            self.stock.remap(map_from='raw_values', map_to='total_clean',fill_timeseries=True)
            self.convert_stock('stock','total')
            self.convert_stock('stock','total_clean')
        if self.case_stock.data is True:
            self.case_stock.remap(map_from='raw_values', map_to='total',fill_timeseries=True, interpolation_method=None,extrapolation_method=None, fill_value=np.nan)
            self.case_stock.remap(map_from='raw_values', map_to='total_clean',fill_timeseries=True)
            self.convert_stock('case_stock','total')
            self.convert_stock('case_stock','total_clean')
        if self.stock.data is True and self.case_stock.data is True:
            self.case_stock.total.fillna(self.stock.total, inplace=True)
            self.stock = self.case_stock
        elif self.stock.data is False and self.case_stock.data is True:
            self.stock = self.case_stock
        elif self.stock.data is False and self.case_stock.data is False:
            self.stock.total = util.empty_df(index=index,columns=self.years,fill_value=np.nan)
             
        
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
        initial_markov = util.create_markov_vector(self.stock.decay_initial_stock.values,
                                                   self.stock.survival_initial_stock.values)
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
            self.rollover_groups = self.stock.total.groupby(level=0).groups
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
        self.stock.retirements = util.empty_df(index=index, columns=['value'])
        self.stock.sales = util.empty_df(index=index, columns=['value'])
        self.rollover_dict = {}
        self.specified_stock = self.stock.total.stack(dropna=False)
        self.setup_financial_stock()
        for elements in self.rollover_groups.keys():
            elements = util.ensure_tuple(elements)
            specified_stock = self.specified_stock.loc[elements].values

            self.rollover_dict[elements] = Rollover(vintaged_markov_matrix=self.stock.vintaged_markov_matrix,
                                     initial_markov_matrix=self.stock.initial_markov_matrix,
                                     num_years=len(years), num_vintages=len(years),
                                     num_techs=1, initial_stock=specified_stock[0],
                                     sales_share=None, stock_changes=None,
                                     specified_stock=specified_stock, specified_retirements=None,stock_changes_as_min=True)
                                     
        for year in [x for x in self.years if x<int(cfg.cfgfile.get('case', 'current_year'))]:
            for elements in self.rollover_groups.keys():
                elements = util.ensure_tuple(elements)
                try:
                    self.rollover_dict[elements].run(1)
                except:
                    print 'error encountered in rollover for node ' + str(self.id) + ' in elements '+ str(elements) + ' year ' + str(year)
                    raise
                stock_total, stock_new, stock_replacement, retirements, retirements_natural, retirements_early, sales_record, sales_new, sales_replacement = self.rollover_dict[(elements)].return_formatted_outputs(year_offset=0)
                self.stock.values.loc[elements,year] = stock_total
                sales_indexer = elements + (year,)
                self.stock.sales.loc[sales_indexer, 'value'] = sales_record
            self.financial_stock(year)
                                     
    def ensure_capacity_factor(self):
        index = pd.MultiIndex.from_product(self.rollover_group_levels, names=self.rollover_group_names)
        columns = self.years
        df = util.empty_df(index=index, columns=pd.Index(columns, dtype='object'),fill_value=1.0)
        if self.capacity_factor.data is True:
            self.capacity_factor.values = DfOper.mult([df,self.capacity_factor.values])
        else:
            self.capacity_factor.values = df
        
    
    def calculate_dispatch_costs(self, year, embodied_cost_df, loop=None):
        if hasattr(self, 'is_flexible') and self.is_flexible:
            self.active_dispatch_costs = copy.deepcopy(self.active_trade_adjustment_df)
            for node in self.active_trade_adjustment_df.index.get_level_values('supply_node'):
                embodied_cost_indexer = util.level_specific_indexer(embodied_cost_df, 'supply_node',node)
                trade_adjustment_indexer = util.level_specific_indexer(self.active_trade_adjustment_df, 'supply_node',node)
                self.active_dispatch_costs.loc[trade_adjustment_indexer,:] = DfOper.mult([self.active_trade_adjustment_df.loc[trade_adjustment_indexer,:],embodied_cost_df.loc[embodied_cost_indexer,:]]).values 
            self.active_dispatch_costs = self.active_dispatch_costs.groupby(level='supply_node').sum()
            self.active_dispatch_costs = self.active_dispatch_costs.stack([self.geography,'demand_sector'])
            self.active_dispatch_costs *= self.active_coefficients_total
            self.active_dispatch_costs = util.reduce_levels(self.active_dispatch_costs, self.rollover_group_names, agg_function='mean')
            self.active_dispatch_costs = DfOper.mult([self.active_dispatch_costs, self.active_dispatch_coefficients])
            self.active_dispatch_costs = util.remove_df_levels(self.active_dispatch_costs, 'supply_node')
            self.active_dispatch_costs = self.active_dispatch_costs.reorder_levels(self.stock.values.index.names)
        
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
                self.rollover_dict[elements].run(1, stock_changes.loc[elements])
            except:
                print 'error encountered in rollover for node ' + str(self.id) + ' in elements '+ str(elements) + ' year ' + str(year)
                raise
            stock_total, stock_new, stock_replacement, retirements, retirements_natural, retirements_early, sales_record, sales_new, sales_replacement = self.rollover_dict[(elements)].return_formatted_outputs(year_offset=0)
            self.stock.values.loc[elements,year] = stock_total
            sales_indexer = elements + (year,)
            self.stock.sales.loc[sales_indexer, 'value'] = sales_record
        self.financial_stock(year)
        self.calculate_energy(year)
        
    def setup_financial_stock(self):
            # creates binary matrix across years and vintages for a technology based on its book life
            self.book_life_matrix = util.book_life_df(self.book_life, self.vintages, self.years)
            # creates a linear decay of initial stock
            self.initial_book_life_matrix = util.initial_book_life_df(self.book_life, self.mean_lifetime, self.vintages, self.years)

    
    def calculate_energy(self, year):
        self.stock.values_energy[year] = DfOper.mult([self.stock.values[year].to_frame(), self.capacity_factor.values[year].to_frame()])* util.unit_conversion(unit_from_den=cfg.cfgfile.get('case','time_step'), unit_to_den='year')[0]

    
    
    def financial_stock(self, year):
        """
        Calculates the amount of stock based on sales and book life
        instead of physical decay
        """
        # stock values in any year equals vintage sales multiplied by book life
        values_financial = DfOper.mult([self.stock.sales, self.book_life_matrix[year].to_frame()])
        # initial stock values in any year equals stock.values multiplied by the initial tech_df
        initial_values_financial = DfOper.mult([self.stock.values[year].to_frame(), self.initial_book_life_matrix[year].to_frame()])
        # sum normal and initial stock values       
        self.stock.values_financial[year] = DfOper.add([values_financial, initial_values_financial[year].to_frame()])
        self.stock.values_financial_energy[year] = DfOper.mult([self.stock.values_financial[year].to_frame(), self.capacity_factor.values[year].to_frame()])* util.unit_conversion(unit_from_den=cfg.cfgfile.get('case','time_step'), unit_to_den='year')[0]

    
    def calculate_active_coefficients(self,year, loop):
        """calculates the active coefficients"""
        #If a node has no potential data, then it doesn't have a supply curve. Therefore the coefficients are just the specified inputs in that year   
        if year == cfg.cfgfile.get('case', 'current_year') and loop == 'initial':
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
                if hasattr(self, 'stock'):
                    stock_normal = self.stock.values.loc[:,year].to_frame().groupby(level=util.ix_excl(self.stock.values,['resource_bins'])).transform(lambda x: x/x.sum())
                    self.active_coefficients = DfOper.mult([self.coefficients.values.loc[:,year].to_frame(), stock_normal])
                
                else:
                    self.remap_to_potential_and_normalize(throughput, year, self.tradable_geography)
                    self.active_coefficients = DfOper.mult([self.coefficients.values.loc[:,year].to_frame(), 
                                                    self.potential.active_supply_curve_normal],
                                                    (False,False),(False,True)).groupby(level='resource_bins').sum()

        else:
            self.active_coefficients = None
            self.active_coefficients_total = None
            self.active_emissions_coefficients = None
        #we multiply the active coefficients by the trade adjustments to account for inter-geography trades
        if self.active_coefficients is not None:      
            self.active_coefficients_total_untraded = util.remove_df_levels(self.active_coefficients,'efficiency_type')     
            self.active_coefficients_total = DfOper.mult([self.active_coefficients_total_untraded, self.active_trade_adjustment_df])
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
#            active_trade_adjustment_df = self.active_trade_adjustment_df.reindex(index = self.active_coefficients_untraded.index,method='bfill')
            self.active_coefficients = DfOper.mult([self.active_coefficients_untraded,active_trade_adjustment_df])
            keys = self.ghgs
            name = ['ghg']
            self.active_emissions_coefficients = pd.concat([self.active_coefficients]*len(keys), keys=keys, names=name)
            self.active_emissions_coefficients = self.active_emissions_coefficients.reorder_levels([self.geography,'demand_sector', 'supply_node', 'efficiency_type', 'ghg'])
            self.active_emissions_coefficients.sort(inplace=True)
    
    def update_stock(self, year, loop):
        """updates the stock in the IO loop"""
        self.determine_throughput(year,loop)
        self.update_remaining_stock(year, loop) 
        self.update_specified(year)
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
        if self.throughput is not None:
            self.throughput = self.throughput.groupby(level=util.ix_incl(self.throughput, self.rollover_group_names)).sum()      
        self.throughput[self.throughput<0]=0
        
    def update_remaining_stock(self,year, loop):
        """calculates the amount of energy throughput from remaining stock (after natural rollover from the previous year)"""  
        for elements in self.rollover_groups.keys():
            elements = util.ensure_tuple(elements)
            element_indexer= util.level_specific_indexer(self.stock.remaining, self.rollover_group_names,elements)
            if year == int(cfg.cfgfile.get('case','current_year')) and loop == 'initial':  
                self.stock.remaining.loc[element_indexer, year] = self.rollover_dict[elements].return_formatted_stock(year_offset=1)                 
                self.stock.act_rem_energy = DfOper.mult([self.stock.remaining.loc[:,year].to_frame(), self.capacity_factor.values.loc[:,year].to_frame()]) * util.unit_conversion(unit_from_den=cfg.cfgfile.get('case', 'time_step'), unit_to_den='year')[0]
                default_conversion = util.unit_conversion(unit_from_num='year',unit_to_num=cfg.cfgfile.get('case', 'time_step'))[0]
                self.stock.act_energy_capacity_ratio = DfOper.divi([self.stock.act_rem_energy.groupby(level=util.ix_excl(self.stock.act_rem_energy,['vintage'])).sum(),
                                            self.stock.remaining.loc[:, year].to_frame().groupby(level=util.ix_excl(self.stock.remaining, ['vintage'])).sum()]).fillna(default_conversion)
            
            elif year == int(cfg.cfgfile.get('case','current_year')) and loop == 1:
                self.rollover_dict[elements].rewind(1)    
                self.stock.remaining.loc[element_indexer, year] = self.rollover_dict[elements].return_formatted_stock(year_offset=1)             
                self.stock.act_rem_energy = DfOper.mult([self.stock.remaining.loc[:,year].to_frame(), self.capacity_factor.values.loc[:,year].to_frame()]) * util.unit_conversion(unit_from_den=cfg.cfgfile.get('case', 'time_step'), unit_to_den='year')[0]
                default_conversion = util.unit_conversion(unit_from_num='year',unit_to_num=cfg.cfgfile.get('case', 'time_step'))[0]
                self.stock.act_energy_capacity_ratio = DfOper.divi([self.stock.act_rem_energy.groupby(level=util.ix_excl(self.stock.act_rem_energy,['vintage'])).sum(),
                                            self.stock.remaining.loc[:, year].to_frame().groupby(level=util.ix_excl(self.stock.remaining, ['vintage'])).sum()]).fillna(default_conversion)
            elif loop == 1:                
                self.stock.remaining.loc[element_indexer, year] = self.rollover_dict[elements].return_formatted_stock(year_offset=1)             
                self.stock.act_rem_energy = DfOper.mult([self.stock.remaining.loc[:,year].to_frame(), self.capacity_factor.values.loc[:,year].to_frame()]) * util.unit_conversion(unit_from_den=cfg.cfgfile.get('case', 'time_step'), unit_to_den='year')[0]
                default_conversion = util.unit_conversion(unit_from_num='year',unit_to_num=cfg.cfgfile.get('case', 'time_step'))[0]
                self.stock.act_energy_capacity_ratio = DfOper.divi([self.stock.act_rem_energy.groupby(level=util.ix_excl(self.stock.act_rem_energy,['vintage'])).sum(),
                                            self.stock.remaining.loc[:, year].to_frame().groupby(level=util.ix_excl(self.stock.remaining, ['vintage'])).sum()]).fillna(default_conversion)
            else:
                self.rollover_dict[elements].rewind(1)

  
    def update_specified(self, year):
        """sets the minimum necessary stock by technology based on remaining stock after natural rollover and specified stock amounts"""    
        self.stock.act_spec_energy = DfOper.mult([self.stock.total.loc[:,year].to_frame(), self.stock.act_energy_capacity_ratio],fill_value=np.nan)
        self.stock.act_spec_or_rem_energy = self.stock.act_spec_energy.fillna(self.stock.act_rem_energy.groupby(level=util.ix_incl(self.stock.act_rem_energy,self.stock.act_spec_energy.index.names)).sum())
        self.stock.act_spec_or_rem = DfOper.divi([self.stock.act_spec_or_rem_energy, self.stock.act_energy_capacity_ratio])

            
    def update_total(self, year):
        """sets the minimum necessary total stock - based on throughput (stock requirement) and total of the specified and remaining stock"""
        if len(self.rollover_group_names)>1:
            self.stock.act_total_energy = self.stock.act_spec_or_rem_energy.groupby(level=self.stock.requirement.index.names).sum()       
        else:
            self.stock.act_total_energy = self.stock.act_spec_or_rem_energy.groupby(level=0).sum() 

    
    def update_requirement(self,year):    
        """updates annual stock requirements with the maximum of required stock and specified and remaining natural rolloff. Also
        distributes the necessary stock changes to the available residuals in the supply curve bins if the stock has resource_bin indexers
        """
        previous_year = max(min(self.years),year-1)
        if self.throughput is not None:
            self.stock.requirement_energy.loc[:,year] = self.throughput
        if self.potential.data is False:
            a = self.stock.requirement_energy.loc[:,year].to_frame()
            b = self.stock.act_total_energy
            a[a<b] = b
            self.stock.requirement_energy.loc[:,year] = a      
            self.stock.requirement.loc[:,year] = DfOper.divi([self.stock.requirement_energy.loc[:,year].to_frame(),self.stock.act_energy_capacity_ratio]).fillna(0) 
        else:
            total_residual = DfOper.subt([self.stock.requirement_energy.loc[:,year], self.stock.act_total_energy],expandable=(False,False), collapsible=(True,True))
            bin_residual = DfOper.subt([self.potential.supply_curve.loc[:, year], self.stock.act_total_energy],expandable=(False,False), collapsible=(True,True))
            bin_residual_supply_curve = bin_residual.cumsum()
            bin_residual_supply_curve[bin_residual_supply_curve>total_residual] = total_residual
            bin_residual_supply_curve = bin_residual_supply_curve.groupby(level=util.ix_excl(bin_residual_supply_curve,'resource_bins')).diff().fillna(bin_residual_supply_curve)
            self.stock.requirement_energy.loc[:,year] = DfOper.add([self.stock.act_total_energy, bin_residual_supply_curve])
            self.stock.requirement.loc[:, year] =  DfOper.divi([self.stock.requirement_energy.loc[:,year].to_frame(),self.stock.act_energy_capacity_ratio]) 
        if year == int(cfg.cfgfile.get('case','current_year')) and year==min(self.years):
            self.stock.act_stock_changes = self.stock.requirement[year]*0
        elif year == int(cfg.cfgfile.get('case','current_year')) and year!=min(self.years):
            self.stock.act_stock_changes = self.stock.requirement[year]- util.remove_df_levels(self.stock.remaining[year],['vintage'])
        else:
            self.stock.act_stock_changes = self.stock.requirement[year] - self.stock.requirement[previous_year]

    def calculate_oversupply(self, year, loop):
        """calculates whether the stock would oversupply the IO requirement and returns an oversupply adjustment factor."""  
        if hasattr(self,'stock'):  
            oversupply_adjustment = DfOper.divi([self.stock.requirement_energy.loc[:,year].to_frame(), self.throughput], expandable=(False,False), collapsible=(False,False)).fillna(1)
            oversupply_adjustment.replace(np.inf,1,inplace=True)
            if (oversupply_adjustment.values>1).any():
                return oversupply_adjustment
            else:
                return None
        else:
            return None
                
    def create_costs(self):
        cfg.cur.execute('select id from "SupplyCost" where supply_node_id=%s', (self.id,))
        ids = [id for id in cfg.cur.fetchall()]
        for (id,) in ids:
            cfg.cur.execute('select is_capital_cost from "SupplyCost" where id=%s', (id,))
            (is_capital_cost,) = cfg.cur.fetchone()
            self.add_costs(id, is_capital_cost)

    def add_costs(self, id, is_capital_cost, **kwargs):
        """
        add cost object to a supply stock node
        
        """
        if id in self.costs:
            # ToDo note that a node by the same name was added twice
            return
        else:
            if is_capital_cost:
                self.costs[id] = SupplyCostCapital(id)
            else:
                self.costs[id] = SupplyCostOther(id)
                
                
    def calculate_costs(self,year):
        start_year = int(cfg.cfgfile.get('case', 'current_year'))
        if not hasattr(self,'total_cost'):
            index = pd.MultiIndex.from_product(self.rollover_group_levels, names=self.rollover_group_names)
            self.total_cost = util.empty_df(index, columns=self.years,fill_value=0.)
            self.embodied_cost = util.empty_df(index, columns=self.years,fill_value=0.)
        for cost in self.costs.values():
            if cost.data is True:
                if cost.capacity is True:
                    stock_values = self.stock.values.groupby(level= self.rollover_group_names+['vintage']).sum()
                    financial_stock_values = self.stock.values_financial.groupby(level= self.rollover_group_names).sum()
                elif cost.capacity is False:
                    stock_values = self.stock.values_energy.groupby(level= self.rollover_group_names).sum()
                    financial_stock_values = self.stock.values_financial_energy.groupby(level= self.rollover_group_names).sum()
                if cost.supply_cost_type == 'tariff' or cost.supply_cost_type == 'investment':
                    initial_stock_values = stock_values[start_year].to_frame()
                    initial_stock_values.columns = [year]
                    initial_cost_values_level = cost.values_level[start_year].to_frame()
                    initial_cost_values_level_no_vintage = cost.values_level_no_vintage[start_year].to_frame()
                    initial_cost_values_level.columns = [year]
                    initial_cost_values_level_no_vintage.columns = [year]
                    initial_financial_stock_values = financial_stock_values[start_year].to_frame()
                    initial_financial_stock_values.columns = [year]
                    if cost.is_capital_cost:
                        self.total_cost[year]  += util.remove_df_levels((DfOper.mult([cost.values_level_no_vintage[year].to_frame(),initial_stock_values])*(1-cost.throughput_correlation))[year],'vintage')
                        self.total_cost[year]  += util.remove_df_levels((DfOper.mult([DfOper.divi([DfOper.mult([initial_cost_values_level_no_vintage,initial_stock_values],non_expandable_levels=None), initial_financial_stock_values],financial_stock_values[year].to_frame(),non_expandable_levels=None)],non_expandable_levels=None)*cost.throughput_correlation)[year],'vintage')
                    else:
                        self.total_cost[year]  += util.remove_df_levels(DfOper.mult([cost.values_level_no_vintage[year].to_frame(),initial_stock_values],non_expandable_levels=None)*(1-cost.throughput_correlation),'vintage')            
                        self.total_cost[year]  += util.remove_df_levels(DfOper.mult([cost.values_level[year].to_frame(), stock_values[year].to_frame()],non_expandable_levels=None)*(cost.throughput_correlation),'vintage') 
                elif cost.supply_cost_type == 'revenue requirement':
                    if cost.is_capital_cost:
                        self.total_cost[year]  += util.remove_df_levels(DfOper.mult([DfOper.divi([cost.values_level[year].to_frame(), stock_values[start_year].to_frame()],non_expandable_levels=None),stock_values[start_year].to_frame()],non_expandable_levels=None)*(1-cost.throughput_correlation),'vintage')
                        self.total_cost[year]  += util.remove_df_levels(DfOper.mult([DfOper.divi([initial_cost_values_level, initial_financial_stock_values],non_expandable_levels=None),financial_stock_values[year].to_frame()],non_expandable_levels=None)*(cost.throughput_correlation),'vintage')
                    else:
                        self.total_cost[year] += cost.values[year].to_frame() *(1-cost.throughput_correlation)
                        self.total_cost[year]  +=  util.remove_df_levels(DfOper.mult([DfOper.divi([initial_cost_values_level, initial_financial_stock_values],non_expandable_levels=None),financial_stock_values[year].to_frame()],non_expandable_levels=None)*(cost.throughput_correlation),'vintage')        
        total_costs = self.total_cost[year].to_frame()
#        total_stock = util.remove_df_levels(self.stock.values_energy.loc[:,year].to_frame(),'vintage')
        self.embodied_cost.loc[:,year] = DfOper.divi([total_costs, self.active_supply],expandable=(False,False)).replace([np.inf,np.nan,-np.nan],[0,0,0])        
        self.active_embodied_cost = util.expand_multi(self.embodied_cost[year].to_frame(), levels_list = [cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')], self.demand_sectors],levels_names=[cfg.cfgfile.get('case', 'primary_geography'),'demand_sector'])

                    
class SupplyCapacityFactor(Abstract):
    def __init__(self, id, **kwargs):
        self.id = id
        self.input_type = 'intensity'
        self.sql_id_table = 'SupplyCapacityFactor'
        self.sql_data_table = 'SupplyCapacityFactorData'
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
    def __init__(self, id, **kwargs):
        self.id = id
        self.input_type = 'total'
        self.sql_id_table = 'SupplyPotential'
        self.sql_data_table = 'SupplyPotentialData'
        Abstract.__init__(self, self.id, 'supply_node_id')

        
    def calculate(self, conversion, resource_unit):
        if self.data is True:
            self.conversion = conversion
            self.resource_unit=resource_unit
            self.remap()
            self.convert()

    def convert(self):
        self.values = self.values.unstack(level='year')
        self.values.columns = self.values.columns.droplevel()
        if self.time_unit is None:
                self.time_unit = 'year'
        if self.conversion is not None:
            # if a conversion is necessary, it means that original input values are in resource and not energy terms
            # this means that they must be copied to resource values and values are the result of
            # multiplying the original values by the conversion dataframe
#            self.resource_values = util.unit_convert(self.values,unit_from_den=self.time_unit, unit_to_den='year')
#            self.resource_supply_curve = self.resource_values.groupby(level=[cfg.cfgfile.get('case', 'primary_geography')]).cumsum()
            self.values = DfOper.mult([self.values, self.conversion.values])
            self.supply_curve = util.remove_df_levels(self.values, [x for x in self.values.index.names if x not in [cfg.cfgfile.get('case', 'primary_geography'),'resource_bins']])
            self.supply_curve = self.supply_curve.groupby(level=[cfg.cfgfile.get('case', 'primary_geography')]).cumsum()
        else:
            if util.determ_energy(self.unit):
                self.values = util.unit_convert(self.values, unit_from_num=self.unit, unit_from_den=self.time_unit, unit_to_num=cfg.cfgfile.get('case', 'energy_unit'), unit_to_den='year')
            else:
                raise ValueError('unit is not an energy unit and no resource conversion has been entered')
            self.supply_curve = self.values.groupby(level=[cfg.cfgfile.get('case', 'primary_geography')]).cumsum()


    def remap_to_potential(self, active_throughput, year, tradable_geography=None):
        """remaps throughput to potential bins"""    
        #original supply curve represents an annual timeslice 
        self.active_throughput = active_throughput    
        self.active_throughput[self.active_throughput<=0] = 1E-25
        original_supply_curve = self.supply_curve.loc[:,year].to_frame().groupby(level=util.ix_incl(self.supply_curve,[cfg.cfgfile.get('case', 'primary_geography'), 'resource_bins', 'demand_sector'])).sum()                
        self.active_supply_curve = copy.deepcopy(original_supply_curve) 
        if tradable_geography is not None:
            self.geo_map(converted_geography=tradable_geography, attr='active_supply_curve', inplace=True, current_geography=cfg.cfgfile.get('case', 'primary_geography'))
            self.geo_map(converted_geography=tradable_geography, attr='active_throughput', inplace=True, current_geography=cfg.cfgfile.get('case', 'primary_geography'))
        reindexed_throughput = DfOper.none([self.active_throughput,self.active_supply_curve],expandable=(True,False),collapsible=(True,True))    
        self.active_supply_curve[self.active_supply_curve>reindexed_throughput] = reindexed_throughput
        self.active_supply_curve =  self.active_supply_curve.groupby(level=util.ix_excl(self.active_supply_curve, 'resource_bins')).diff(1).fillna(reindexed_throughput)
        remap_active = pd.DataFrame(original_supply_curve.stack(), columns=['value'])
        util.replace_index_name(remap_active, 'year')
        self.active_supply_curve = pd.DataFrame(self.active_supply_curve.stack(), columns=['value'])
        util.replace_index_name(self.active_supply_curve, 'year')
        if tradable_geography is not None:
            self.remap(map_from='active_supply_curve', map_to='active_supply_curve', fill_timeseries=False, drivers=remap_active, current_geography=tradable_geography)
        self.active_supply_curve= self.active_supply_curve.unstack('year')
        self.active_supply_curve.columns = self.active_supply_curve.columns.droplevel()


    def remap_to_potential_and_normalize(self,active_throughput, year,tradable_geography=None) :
        """returns the proportion of the supply curve that is in each bin"""
        self.remap_to_potential(active_throughput, year, tradable_geography)
        self.active_supply_curve_normal= self.active_supply_curve.groupby(level=cfg.cfgfile.get('case', 'primary_geography')).transform(lambda x:x/x.sum()).fillna(0.)


    def format_potential_and_supply_for_constraint_check(self,active_supply, tradable_geography, year):
        if tradable_geography == cfg.cfgfile.get('case', 'primary_geography'):
            self.active_potential = self.values.loc[:,year].to_frame()
            self.active_geomapped_potential = self.active_potential
            self.active_geomapped_supply = active_supply
        else:
            self.active_potential = self.values.loc[:,year].to_frame()
            self.active_geomapped_potential = self.geo_map(converted_geography=tradable_geography, attr='active_potential', inplace=False, current_geography=cfg.cfgfile.get('case', 'primary_geography'), current_data_type='total')
            self.active_geomapped_supply = active_supply
            self.active_geomapped_supply = self.geo_map(converted_geography=tradable_geography, attr='active_geomapped_supply', inplace=False, current_geography=cfg.cfgfile.get('case', 'primary_geography'), current_data_type='total')
        levels = util.intersect(self.active_geomapped_supply.index.names, self.active_geomapped_supply.index.names)
        disallowed_potential_levels = [x for x in self.active_geomapped_potential.index.names if x not in levels]
        disallowed_supply_levels = [x for x in self.active_geomapped_supply.index.names if x not in levels]
        if len(disallowed_potential_levels):
            self.active_geomapped_potential = util.remove_df_levels(self.active_geomapped_potential, disallowed_potential_levels)     
        if len(disallowed_supply_levels):
            self.active_geomapped_supply= util.remove_df_levels(self.active_geomapped_supply, disallowed_supply_levels)       
        return self.active_geomapped_potential, self.active_geomapped_supply

class SupplyCost(Abstract):
    def __init__(self, id, **kwargs):
        self.id = id
        self.sql_id_table = 'SupplyCost'
        self.sql_data_table = 'SupplyCostData'
        Abstract.__init__(self, self.id, primary_key='id', data_id_key='parent_id')
        
    def calculate(self, years, demand_sectors):
        self.years = years
        self.vintages = [years[0]-1] + years 
        self.demand_sectors = demand_sectors
        if self.data is True:
            self.determ_input_type()
            if self.supply_cost_type == 'revenue requirement':
                self.remap(converted_geography=self.geography)
            else:
                self.remap()
            self.convert()
            self.levelize_costs()

    def determ_input_type(self):
        """function that determines whether the input cost is a total or an intensity value"""
        if self.supply_cost_type == 'revenue requirement':
            self.input_type = 'total'
        elif self.supply_cost_type == 'tariff' or self.cost_type == 'investment':
            self.input_type = 'intensity'
        else:
            print "incompatible cost type entry in cost %s" % self.id
            raise ValueError

    def convert(self):
        """
        convert raw_values to model currency and capacity (energy_unit/time_step)
        """

        self.values = util.currency_convert(self.values, self.currency_id, self.currency_year_id)
        model_energy_unit = cfg.cfgfile.get('case', 'energy_unit')
        model_time_step = cfg.cfgfile.get('case', 'time_step')
        if self.input_type == 'intensity':
            if self.time_unit is not None:
                # if a cost has a time_unit, then the unit is energy and must be converted to capacity
                self.values = util.unit_convert(self.values, unit_from_den=self.energy_or_capacity_unit,
                                            unit_from_num=self.time_unit, unit_to_den=model_energy_unit,
                                            unit_to_num=model_time_step)
                self.capacity = False
            else:
            # if a cost is a capacity unit, the model must convert the unit type to an energy unit for conversion ()
                if util.determ_energy(self.energy_or_capacity_unit):
                    self.values = util.unit_convert(self.values, unit_from_den =self.energy_or_capacity_unit, unit_to_den=model_energy_unit)
                    self.capacity = False
                else:
                    self.values = util.unit_convert(self.values, unit_from_den =cfg.ureg.Quantity(self.energy_or_capacity_unit)
                                                                           * cfg.ureg.Quantity(model_time_step),
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
            self.values_level_no_vintage = self.values_level
            keys = self.vintages
            name = ['vintage']
            self.values_level= pd.concat([self.values_level_no_vintage]*len(keys), keys=keys, names=name)
            self.values_level = self.values_level.swaplevel('vintage', -1)
            self.values_level = self.values_level.unstack('year')
            self.values_level.columns = self.values_level.columns.droplevel()
            self.values_level_no_vintage = self.values_level_no_vintage.unstack('year')
            self.values_level_no_vintage.columns = self.values_level_no_vintage.columns.droplevel()

class SupplyCostOther(SupplyCost):
    def __init__(self, id, **kwargs):
        SupplyCost.__init__(self, id)


class SupplyCostCapital(SupplyCost):
    def __init__(self, id, **kwargs):
        SupplyCost.__init__(self, id)


class SupplyCoefficients(Abstract):
    def __init__(self, id, **kwargs):
        self.id = id
        self.input_type = 'intensity'
        self.sql_id_table = 'SupplyEfficiency'
        self.sql_data_table = 'SupplyEfficiencyData'
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
            self.values = self.values.reorder_levels([cfg.cfgfile.get('case', 'primary_geography'),'demand_sector', 'efficiency_type', 'supply_node'])
            
    def convert(self):
        """
        return raw_values that are converted to units consistent with output units for 
        normalized efficiency values
        
        """
        self.values = util.unit_convert(self.raw_values, unit_from_num=self.input_unit, unit_to_num=self.output_unit)
    
class SupplyStockNode(Node):
    def __init__(self, id, supply_type,**kwargs):
        Node.__init__(self, id, supply_type)
        for col, att in util.object_att_from_table('SupplyNodes', id):
            setattr(self, col, att)
        if self.tradable_geography is None:
            self.enforce_tradable_geography = False
            self.tradable_geography = cfg.cfgfile.get('case', 'primary_geography')
        else:
            self.enforce_tradable_geography = True
        self.potential = SupplyPotential(self.id)
        self.technologies = {}
        self.tech_ids = []
        self.add_technologies()
        self.add_nodes()
        self.add_stock()

    def calculate_oversupply(self, year, loop):
        """calculates whether the stock would oversupply the IO requirement and returns an oversupply adjustment factor."""  
        if hasattr(self,'stock'):  
            oversupply_adjustment = DfOper.divi([self.stock.requirement_energy.loc[:,year].to_frame(), self.throughput], expandable=(False,False), collapsible=(True,True)).fillna(1)
            oversupply_adjustment.replace(np.inf,1,inplace=True)
            if (oversupply_adjustment.values>1).any():
                return oversupply_adjustment
            else:
                return None
        else:
            return None
    
    
    def set_rollover_groups(self):
        """sets the internal index for use in stock and cost calculations"""
        # determines whether stock rollover needs to occur on demand sector or resource bin index
        self.stock.rollover_group_levels = []
        self.stock.rollover_group_names = []
        if self.stock.data is True:
            for name, level in zip(self.stock.raw_values.index.names, self.stock.raw_values.index.levels):
                if name == 'resource_bins' or name == 'demand_sector' :
                    self.stock.rollover_group_levels.append(list(level))
                    self.stock.rollover_group_names.append(name)                        
        if self.potential.data is True:
            for name, level in zip(self.potential.raw_values.index.names, self.potential.raw_values.index.levels):
                if name == 'resource_bins' or name == 'demand_sector' :
                    self.stock.rollover_group_levels.append(list(level))
                    self.stock.rollover_group_names.append(name)                    
        for technology in self.technologies.values():
            attributes = vars (technology)
            for att in attributes:
                obj = getattr(technology, att)
                if inspect.isclass(type(obj)) and hasattr(obj, '__dict__') and hasattr(obj, 'raw_values') and obj.raw_values is not None:
                    for name, level in zip(obj.raw_values.index.names, obj.raw_values.index.names):
                        if name == 'resource_bins' or name == 'demand_sector':
                            self.stock.rollover_group_levels.append(list(level))
                            self.stock.rollover_group_names.append(name)
        if self.id == self.distribution_grid_node_id:
            #requires distribution grid node to maintain demand sector resolution in its stocks
            self.stock.rollover_group_levels.append(self.demand_sectors)
            self.stock.rollover_group_names.append('demand_sector')
        self.stock.rollover_group_names = [cfg.cfgfile.get('case', 'primary_geography')] + self.stock.rollover_group_names
        self.stock.rollover_group_levels = [cfg.geo.geographies[cfg.cfgfile.get('case', 'primary_geography')]] + self.stock.rollover_group_levels
        
    def add_stock(self):
        """add stock instance to node"""
        self.stock = Stock(id=self.id, drivers=None,sql_id_table='SupplyStock', sql_data_table='SupplyStockData', primary_key='supply_node_id')
        self.stock.input_type = 'total'


    def calculate(self, years, demand_sectors, ghgs, distribution_grid_node_id): 
        self.years = years
        self.demand_sectors = demand_sectors
        self.ghgs = ghgs
        self.distribution_grid_node_id = distribution_grid_node_id
        self.set_rollover_groups()
        attributes = vars(self)
        for att in attributes:
            obj = getattr(self, att)
            if inspect.isclass(type(obj)) and hasattr(obj, '__dict__') and hasattr(obj, 'calculate'):
                obj.calculate(self.years, self.demand_sectors)
        self.calculate_input_stock()
        self.set_adjustments()
        self.set_pass_through_df_dict()
        self.setup_stock_rollover(self.years)


    def calculate_input_stock(self):
        """calculates the specified stocks in a node based on the combination of measure-stocks and reference stocks"""
        self.add_case_stock()
        levels = self.stock.rollover_group_levels + [self.years] + [self.tech_ids]
        names = self.stock.rollover_group_names + ['year'] + ['supply_technology']
        index = pd.MultiIndex.from_product(levels,names=names)
        if self.stock.data is True:
            #remap to specified stocks
            self.stock.years = self.years
            self.stock.remap(map_from='raw_values', map_to='specified',fill_timeseries=True, interpolation_method=None,extrapolation_method=None, fill_value=np.nan)         
            #convert the stock to correct units and unstack years
            #if there's case_specific stock data, we must use that to replace reference specified stocks
            if hasattr(self,'case_stock_specified'):
                # if there are levels in the case specific stock that are not in the reference stock, we must remove that level from the case stock
                mismatched_levels = [x for x in self.case_stock_specified.index.names if x not in self.stock.specified.index.names] 
                if len(mismatched_levels):
                    self.case_stock.specified = self.case_stock_specified.groupby(level=util.ix_excl(self.case_stock_specified, levels=mismatched_levels)).sum()
                #if there are still level mismatches, it means the reference stock has more levels, which returns an error
                if util.difference_in_df_names(self.case_stock_specified, self.stock.specified,return_bool=True):
                    raise ValueError("specified stock indices in node %s do not match input energy system stock data" %self.id)
                else:
                    #if the previous test is passed, we unstack years from the case stock, convert and unstack the reference stock
                    #and use the reference stock to fill in the Nans of the case stock
                    self.case_stock.reindex(index)
                    self.case_stock_specified = self.case_stock_specified.unstack('year')
                    self.case_stock_specified.columns = self.case_stock_specified.columns.droplevel() 
                    self.convert_stock('stock', 'specified')
                    self.stock.specified = self.case_stock_specified.fillna(self.stock.specified)
                    stacked_specified = self.stock.specified.stack()
                    util.replace_column(stacked_specified,'year')
                    self.stock.total_clean = util.remove_df_levels(stacked_specified,'supply_technology')
                    self.stock.clean_timeseries('total_clean', interpolation_method='nearest',extrapolation_method='nearest')
                    self.stock.total_clean = self.stock.total_clean.unstack('year')
                    self.stock.total_clean.columns = self.stock.total_clean.columns.droplevel() 
            else:
                    self.stock.total_clean = util.remove_df_levels(self.stock.specified,'supply_technology')
                    self.stock.clean_timeseries('total_clean', interpolation_method='nearest',extrapolation_method='nearest')             
                    self.convert_stock('stock', 'specified')
                    self.convert_stock('stock','total_clean')
        elif hasattr(self,'case_stock_specified'):
                # if there are levels in the case specific stock that are not in the rollover groups, we must remove that level from the case stock
                mismatched_levels = [x for x in self.case_stock_specified.index.names if x not in names]
                if len(mismatched_levels):
                    self.case_stock_specified = self.case_stock_specified.groupby(level=util.ix_excl(self.case_stock_specified, levels=mismatched_levels)).sum()
                #if there are still level mismatches, it means the rollover has more levels, which returns an error
                if len([x for x in self.stock.rollover_group_names if x not in self.case_stock.specified.index.names]) :
                    raise ValueError("specified stock levels in node %s do not match other node input data" %self.id)
                else:
                    #if the previous test is passed, we unstack years from the case stock
                    self.case_stock_specified = self.case_stock_specified.reindex(index)
                    self.stock.specified = self.case_stock_specified
                    self.stock.total_clean = util.remove_df_levels(self.stock.specified,'supply_technology')
                    self.stock.clean_timeseries('total_clean', interpolation_method='nearest',extrapolation_method='nearest')
                    self.stock.total_clean = self.stock.total_clean.unstack('year')
                    self.stock.total_clean .columns = self.stock.specified.total_clean .droplevel() 
                    self.stock.specified = self.stock.specified.unstack('year')
                    self.stock.specified.columns = self.stock.specified.columns.droplevel() 
                    self.stock.data = True
        else: 
            self.stock.specified = util.empty_df(index=index,columns=['value'],fill_value=np.NaN)
            self.stock.specified = self.stock.specified.unstack('year')
            self.stock.specified.columns = self.stock.specified.columns.droplevel() 
        #transposed specified stocks are used for entry in the stock rollover function
        self.stock.specified_initial = self.stock.specified.stack(dropna=False)
        util.replace_index_name(self.stock.specified_initial,'year')
        self.stock.total_initial = util.remove_df_levels(self.stock.specified_initial,'supply_technology')
        self.stock.specified_initial=self.stock.specified_initial.unstack('supply_technology')
        for tech_id in self.tech_ids:
            if tech_id not in self.stock.specified_initial.columns:
                self.stock.specified_initial[tech_id]=np.nan


    def add_case_stock(self):
       specified_stocks = []
       for technology in self.technologies.values():
           for stock_key in technology.specified_stocks.keys():
               tech_stock = technology.specified_stocks[stock_key].values
               tech_stock['supply_technology'] = technology.id
               tech_stock.set_index('supply_technology', append=True, inplace=True) 
               specified_stocks.append(tech_stock)
       if not all('demand_sector' in specified_stock.index.names for specified_stock in specified_stocks):
           for specified_stock in specified_stocks:
               specified_stock = util.remove_df_levels(specified_stock,'demand_sector')
       if len(specified_stocks):
           self.case_stock_specified = pd.concat(specified_stocks)
   
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
                    raise ValueError("supply node {} has no technology {} to serve as a reference for technology {}".format(self.id, ref_tech_id, technology))
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
                else:
                    new_data = copy.deepcopy(getattr(ref_tech_class, attr))
                tech_attributes = vars(getattr(self.technologies[ref_tech_id], class_name))
                for attribute_name in tech_attributes.keys():
                    if not hasattr(tech_class, attribute_name) or getattr(tech_class, attribute_name) is None:
                        setattr(tech_class, attribute_name,
                                copy.deepcopy(getattr(ref_tech_class, attribute_name)) if hasattr(ref_tech_class,
                                                                                                  attribute_name) else None)
                setattr(tech_class, attr, new_data)
        else:
            pass
        # Now that it has been converted, set indicator to true
        tech_class.absolute = True    
    
    
    def add_technologies(self):
        cfg.cur.execute('select id from "SupplyTechs" where supply_node_id=%s', (self.id,))
        ids = [id for id in cfg.cur.fetchall()]
        for (id,) in ids:
            self.add_technology(id)
            
            
    def add_nodes(self):
        self.nodes = []
        for technology in self.technologies.values():
            if hasattr(technology,'efficiency') and technology.efficiency.raw_values is not None:
                for value in technology.efficiency.raw_values.index.get_level_values('supply_node'):
                    self.nodes.append(value)
        self.nodes = set(self.nodes)
        

    def add_technology(self, id, **kwargs):
        """
        Adds technology instances to node
        """
        if id in self.technologies:
            # ToDo note that a technology was added twice
            return
        self.technologies[id] = SupplyTechnology(id, self.cost_of_capital, **kwargs)
        self.tech_ids.append(id)
        self.tech_ids.sort()
        
    def add_stock_measures(self):
            """
            add all stock measures in a selected package to a dictionary
            """
            self.stock_measures = {}
            cfg.cur.execute('select measure_id from "SupplyStockMeasurePackagesData" where package_id=%s',
                                           (self.stock_package_id,))
            ids = [id for id in cfg.cur.fetchall()]
            for (id,) in ids:
                self.add_stock_measure(id)     
            
    def add_stock_measure(self, id, **kwargs):
        """Adds stock measure instances to node"""
        if id in self.stock_measures:
            return
        self.stock_measures[id] = StockMeasure(id)            

    def add_sales_measures(self):
            """
            add all sales measures in a selected package to a dictionary
            """
            self.sales_measures = {}
            cfg.cur.execute('select measure_id from "SupplySalesMeasurePackagesData" where package_id=%s',
                                           (self.sales_package_id,))
            ids = [id for id in cfg.cur.fetchall()]
            for (id,) in ids:
                self.add_sales_measure(id)     
            
    def add_sales_measure(self, id, **kwargs):
        """Adds sales measure instances to node"""
        if id in self.sales_measures:
            return
        self.sales_measures[id] = StockSalesMeasure(id,'total')            
                        
    def add_sales_share_measures(self):
            """
            add all sales share measures in a selected package to a dictionary
            """
            self.sales_share_measures = {}
            cfg.cur.execute('select measure_id from "SupplySalesShareMeasurePackagesData" where package_id=%s',
                                           (self.sales_share_package_id,))
            ids = [id for id in cfg.cur.fetchall()]
            for (id,) in ids:
                self.add_sales_share_measure(id)     
            
    def add_sales_share_measure(self, id, **kwargs):
        """Adds sales measure instances to node"""
        if id in self.sales_share_measures:
            return
        self.sales_share_measures[id] = StockSalesMeasure(id,'intensity')           
     
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
        ss_reference = self.helper_calc_sales_share(elements, levels, reference=True,
                                                    space_for_reference=space_for_reference)                
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
                    repl_index = tech_lookup[sales.demand_tech_id]
                    # TODO address the discrepancy when a demand tech is specified
                    try:
                        ss_array[:, repl_index] = util.df_slice(sales.values, elements,
                                                                             levels).values.T[0]
                    except:
                        ss_array[:, repl_index] = util.df_slice(sales.values, elements,
                                                                             levels).values.flatten()
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
                    repl_index = tech_lookup[tech_id]
                    reti_index = slice(None)
                    # technology sales share dataframe may not have all elements of stock dataframe
                    sales_share.values.index.levels
                    if any([element not in sales_share.values.index.levels[
                        util.position_in_index(sales_share.values, level)] for element, level in
                            zip(elements, levels)]):
                        continue
                    ss_array[:, repl_index, reti_index] += util.df_slice(sales_share.values, elements, levels)
            ss_array = SalesShare.scale_reference_array_to_gap(ss_array, space_for_reference)
        else:
            for tech_id in self.tech_ids:
                for sales_share in self.technologies[tech_id].sales_shares.values():
                    repl_index = tech_lookup[sales_share.demand_tech_id]
                    reti_index = tech_lookup[
                        sales_share.replaced_supply_technology_id] if sales_share.replaced_supply_technology_id is not None and tech_lookup.has_key(
                        sales_share.replaced_supply_technology_id) else slice(
                        None)
                    # TODO address the discrepancy when a demand tech is specified
                    try:
                        ss_array[:, repl_index, reti_index] += util.df_slice(sales_share.values, elements,
                                                                             levels).values
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
            sales_share = self.calculate_total_sales_share(elements,
                                                           self.stock.rollover_group_names)  # group is not necessarily the same for this other dataframe            
            sales = self.calculate_total_sales(elements, self.stock.rollover_group_names)
            if np.any(np.isnan(sales_share)):
                raise ValueError('Sales share has NaN values in node ' + str(self.id))
            initial_total = util.df_slice(self.stock.total_initial, elements, self.stock.rollover_group_names).values[0]
            initial_stock = Stock.calc_initial_shares(initial_total=initial_total, transition_matrix=sales_share[0],
                                                  num_years=len(self.years))
            if np.any(np.isnan(initial_stock)):
                initial_stock=None

            specified_stock = self.stock.format_specified_stock(elements, self.stock.rollover_group_names,'specified_initial')
            self.rollover_dict[elements] = Rollover(vintaged_markov_matrix=self.stock.vintaged_markov_matrix,
                                     initial_markov_matrix=self.stock.initial_markov_matrix,
                                     num_years=len(years), num_vintages=len(years),
                                     num_techs=len(self.tech_ids), initial_stock=initial_stock,
                                     sales_share=sales_share, stock_changes=None, specified_sales=sales,
                                     specified_stock=specified_stock.values, specified_retirements=None,stock_changes_as_min=True)
        for year in [x for x in self.years if x<int(cfg.cfgfile.get('case', 'current_year'))]:
            for elements in self.rollover_groups.keys():
                elements = util.ensure_tuple(elements)
                try:
                    self.rollover_dict[elements].run(1)
                except:
                    print 'error encountered in rollover for node ' + str(self.id) + ' in elements '+ str(elements) + ' year ' + str(year)
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
            
    def stock_rollover(self,year, loop, stock_changes):     
        if min(self.years) == int(cfg.cfgfile.get('case', 'current_year')):
            for elements in self.rollover_groups.keys():    
                elements = util.ensure_tuple(elements)
                sales_share = self.calculate_total_sales_share(elements,
                                                           self.stock.rollover_group_names)  # group is not necessarily the same for this other dataframe
                if np.any(np.isnan(sales_share)):
                    raise ValueError('Sales share has NaN values in node ' + str(self.id))
                initial_stock = Stock.calc_initial_shares(initial_total=self.stock.requirement.loc[elements, year].values, transition_matrix=sales_share[0],
                                                  num_years=len(self.years))
                self.rollover_dict[elements].initial_stock = initial_stock                     
        for elements in self.rollover_groups.keys():    
            elements = util.ensure_tuple(elements)
            try:
                self.rollover_dict[elements].run(1, stock_changes.loc[elements])
            except:
                print 'error encountered in rollover for node ' + str(self.id) + ' in elements '+ str(elements) + ' year ' + str(year)
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
        if loop!= 'initial':
            self.calculate_actual_stock(year,loop)      
            if not self.thermal_dispatch_node:
                adjustment_factor = self.calculate_adjustment_factor(year)
                for elements in self.rollover_groups.keys():
                    elements = util.ensure_tuple(elements)
                    self.rollover_dict[elements].factor_adjust_current_year(adjustment_factor.loc[elements].values)
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
        self.stock.capacity_factor = util.empty_df(index=index, columns=pd.Index(columns, dtype='object'), fill_value=1.0)
        self.stock.ones = util.empty_df(index=index, columns=pd.Index(columns, dtype='object'), fill_value=1.0)
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
        index = pd.MultiIndex.from_product(full_levels, names=full_names)
        self.stock.retirements = util.empty_df(index=index, columns=['value'])
        self.stock.retirements_early = copy.deepcopy(self.stock.retirements)
        self.stock.retirements_natural = copy.deepcopy(self.stock.retirements)
        self.stock.sales = util.empty_df(index=index, columns=['value'])
        self.stock.sales_new = copy.deepcopy(self.stock.sales)
        self.stock.sales_replacement = copy.deepcopy(self.stock.sales)      

        
    def update_stock(self, year, loop):
        """updates the stock in the IO loop"""
        if self.thermal_dispatch_node:
            self.determine_throughput(year,loop)
            self.update_remaining_stock(year, loop) 
            self.update_specified_dispatch(year)
            self.update_total_dispatch(year)
            self.update_requirement_dispatch(year)
        else:
            self.determine_throughput(year,loop)
            self.update_remaining_stock(year, loop) 
            self.update_specified(year)
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
            self.throughput = self.throughput.groupby(level=self.stock.requirement_energy.index.names).sum()      
        self.throughput[self.throughput<=0] = 0

    def calculate_actual_stock(self,year,loop):
        """used to calculate the actual throughput of built stock. This is used to adjust the stock values if it does not
        match the required throughput in the year."""
#        for elements in self.rollover_groups.keys():
#            self.stock.values.loc[elements, year]
        if loop == 'initial' or loop == 1:         
            self.stock.values_energy.loc[:, year] = self.rollover_output(tech_class='capacity_factor',stock_att='values',year=year) * util.unit_conversion(unit_from_den=cfg.cfgfile.get('case','time_step'), unit_to_den='year')[0]
        else:
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
                self.stock.capacity_factor.loc[:, year] = self.rollover_output(tech_class='capacity_factor',stock_att='ones',year=year)
                self.stock.remaining.loc[element_indexer, year] = self.rollover_dict[elements].return_formatted_stock(year_offset=1)
            else:
                self.rollover_dict[elements].rewind(1)
                self.stock.preview.loc[element_indexer,year] = self.rollover_dict[elements].return_formatted_stock(year_offset=0)
        self.set_energy_capacity_ratios(year,loop)
        
   
    def set_energy_capacity_ratios(self,year,loop):
       if loop == 1 or loop == 'initial':
            self.stock.act_rem_energy = DfOper.mult([self.stock.remaining.loc[:,year].to_frame(),self.stock.capacity_factor.loc[:,year].to_frame()]) * util.unit_conversion(unit_from_den=cfg.cfgfile.get('case', 'time_step'), unit_to_den='year')[0]
            default_conversion = util.unit_conversion(unit_from_num='year',unit_to_num=cfg.cfgfile.get('case', 'time_step'))[0]                
            self.stock.act_energy_capacity_ratio = DfOper.divi([util.remove_df_levels(self.stock.act_rem_energy,['vintage','supply_technology']),
                                                                    util.remove_df_levels(self.stock.remaining.loc[:, year].to_frame(),['vintage','supply_technology'])]).fillna(default_conversion)
            self.stock.act_energy_capacity_ratio[self.stock.act_energy_capacity_ratio==0] = default_conversion         
       else:
           preview = util.df_slice(self.stock.preview.loc[:,year].to_frame(), year, 'vintage')
           preview_energy = DfOper.mult([preview,util.df_slice(self.stock.capacity_factor.loc[:,year].to_frame(),year,'vintage')])*util.unit_conversion(unit_from_den=cfg.cfgfile.get('case', 'time_step'), unit_to_den='year')[0]
           preview = util.remove_df_levels(preview,['vintage','supply_technology'])
           preview_energy = util.remove_df_levels(preview_energy,['vintage','supply_technology'])        
           default_conversion = util.unit_conversion(unit_from_num='year',unit_to_num=cfg.cfgfile.get('case', 'time_step'))[0]
           self.stock.act_rem_energy = DfOper.mult([self.stock.remaining.loc[:,year].to_frame(),self.stock.capacity_factor.loc[:,year].to_frame()]) * util.unit_conversion(unit_from_den=cfg.cfgfile.get('case', 'time_step'), unit_to_den='year')[0]
           self.stock.act_energy_capacity_ratio = DfOper.divi([util.remove_df_levels(self.stock.act_rem_energy,['vintage','supply_technology']),
                                                                    util.remove_df_levels(self.stock.remaining.loc[:, year].to_frame(),['vintage','supply_technology'])]).fillna(default_conversion)
           self.stock.act_energy_capacity_ratio[self.stock.act_energy_capacity_ratio==0] = default_conversion                                                   
           self.stock.preview_energy_capacity_ratio = DfOper.divi([preview_energy,preview]).fillna(self.stock.act_energy_capacity_ratio)

  
    def update_specified(self, year):
        """sets the minimum necessary stock by technology based on remaining stock after natural rollover and specified stock amounts"""    
        self.stock.act_spec_energy = DfOper.mult([self.stock.specified.loc[:,year].to_frame(), self.stock.act_energy_capacity_ratio],fill_value=np.nan)
        self.stock.act_spec_or_rem_energy = self.stock.act_spec_energy.fillna(self.stock.act_rem_energy.groupby(level=self.stock.act_spec_energy.index.names).sum())   
        self.stock.act_spec_or_rem = util.remove_df_levels(DfOper.divi([self.stock.act_spec_or_rem_energy, self.stock.act_energy_capacity_ratio]),'supply_technology')
    
    def update_specified_dispatch(self, year):
        """sets the minimum necessary stock by technology based on remaining stock after natural rollover and specified stock amounts"""    
        self.stock.act_spec = self.stock.specified.loc[:,year].to_frame()
        self.stock.act_rem = (self.stock.remaining.loc[:,year].to_frame().groupby(level=util.ix_incl(self.stock.act_spec,self.stock.act_spec.index.names)).sum())   
        self.stock.act_spec_or_rem = self.stock.act_spec.fillna(self.stock.act_rem)
        self.stock.act_spec_or_rem = DfOper.add([self.stock.act_spec_or_rem,self.stock.dispatch_cap.loc[:,year].to_frame().groupby(level=self.stock.rollover_group_names).sum()])

        
    def update_total(self, year):
        """sets the minimum necessary total stock - based on throughput (stock requirement) and total of the specified and remaining stock"""
        self.stock.act_total_energy = self.stock.act_spec_or_rem_energy.groupby(level=self.stock.requirement.index.names).sum()        

                
    def update_total_dispatch(self, year):
        """sets the minimum necessary total stock - based on throughput (stock requirement) and total of the specified and remaining stock"""
        self.stock.act_total= self.stock.act_spec_or_rem.groupby(level=self.stock.requirement.index.names).sum() 


    def update_requirement(self,year,loop):    
        """updates annual stock requirements with the maximum of required stock and specified and remaining natural rolloff. Also
        distributes the necessary stock changes to the available residuals in the supply curve bins if the stock has resource_bin indexers
        """
        previous_year = max(min(self.years),year-1)
        if self.throughput is not None:
            self.stock.requirement_energy.loc[:,year] = self.throughput
        if self.potential.data is False:
            a = self.stock.requirement_energy.loc[:,year].to_frame()
            b = self.stock.act_total_energy
            a[a<b] = b
            self.stock.requirement_energy.loc[:,year] = a          
            self.stock.requirement.loc[:,year] = DfOper.divi([self.stock.requirement_energy.loc[:,year].to_frame(),self.stock.act_energy_capacity_ratio]) 
        else:
            total_residual = DfOper.subt([self.stock.requirement_energy.loc[:,year], self.stock.act_total_energy],expandable=(False,False), collapsible=(True,True))
            bin_residual = DfOper.subt([self.potential.supply_curve.loc[:, year], self.stock.act_total_energy],expandable=(False,False), collapsible=(True,True))
            bin_residual_supply_curve = bin_residual.cumsum()
            bin_residual_supply_curve[bin_residual_supply_curve>total_residual] = total_residual
            bin_residual_supply_curve = bin_residual_supply_curve.groupby(level=util.ix_excl(bin_residual_supply_curve,'resource_bins')).diff().fillna(bin_residual_supply_curve)
            self.stock.requirement_energy.loc[:,year] = DfOper.add([self.stock.act_total_energy, bin_residual_supply_curve])
            self.stock.requirement.loc[:, year] =  DfOper.divi([self.stock.requirement_energy.loc[:,year].to_frame(),self.stock.act_energy_capacity_ratio]) 
        if year == int(cfg.cfgfile.get('case','current_year')) and year==min(self.years):
            self.stock.act_stock_changes = self.stock.requirement[year].to_frame()*0
        elif year == int(cfg.cfgfile.get('case','current_year')) and year!=min(self.years):
            self.stock.act_stock_changes = DfOper.subt([self.stock.requirement_energy[year].to_frame(),
                                                        util.remove_df_levels(self.stock.act_rem_energy[year].to_frame(),['vintage','supply_technology'])])
        else:
            self.stock.act_stock_changes = DfOper.subt([self.stock.requirement_energy[year].to_frame(),self.stock.requirement_energy[previous_year].to_frame()])
        if loop == 'initial' or loop ==1:
            needed_capacity_ratio = self.stock.act_energy_capacity_ratio
        else:
            needed_capacity_ratio = self.stock.preview_energy_capacity_ratio
        act_positive_stock_changes = DfOper.divi([self.stock.act_stock_changes,needed_capacity_ratio]).fillna(0)
        act_negative_stock_changes = DfOper.divi([self.stock.act_stock_changes,self.stock.act_energy_capacity_ratio]).fillna(0)
        max_retirable = -self.stock.values.loc[:,previous_year].to_frame().groupby(level=self.stock.rollover_group_names).sum() 
        max_retirable.columns = [year]
        act_negative_stock_changes[act_negative_stock_changes<=max_retirable]=max_retirable
        act_positive_stock_changes[act_positive_stock_changes<0] = act_negative_stock_changes
        self.stock.act_stock_changes = act_positive_stock_changes
        self.stock.act_stock_changes = self.stock.act_stock_changes[year]

    def update_requirement_dispatch(self,year):    
        """updates annual stock requirements with the maximum of required stock and specified and remaining natural rolloff. Also
        distributes the necessary stock changes to the available residuals in the supply curve bins if the stock has resource_bin indexers
        """
        previous_year = max(min(self.years),year-1)
        #TODO Flexible Nodes can't have SupplyPotential
#        if self.potential.data is False:    
        self.stock.requirement.loc[:,year] = self.stock.act_total
        if year == int(cfg.cfgfile.get('case','current_year')):
            #stock changes only equal capacity added from the dispatch
            self.stock.act_stock_changes = DfOper.subt([self.stock.requirement.loc[:,year].to_frame(),
                                                        self.stock.values.loc[:,previous_year].to_frame().groupby(level=self.stock.rollover_group_names).sum()])
        else:
            self.stock.act_stock_changes = DfOper.subt([self.stock.requirement[year].to_frame(),self.stock.requirement[previous_year].to_frame()])
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
            
    def calculate_costs(self,year):
        "calculates per-unit costs in a subsector with technologies"
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
            index = pd.MultiIndex.from_product(self.stock.rollover_group_levels, names=self.stock.rollover_group_names)
            self.embodied_cost = util.empty_df(index, columns=self.years,fill_value=0)
         
        self.stock.capital_cost_new.loc[:,year] = self.rollover_output(tech_class='capital_cost_new',tech_att='values_level',
                                                                         stock_att='values_financial_new',year=year)
        self.stock.capital_cost_replacement.loc[:,year] = self.rollover_output(tech_class='capital_cost_replacement',tech_att='values_level',
                                                                         stock_att='values_financial_replacement',year=year)
        self.stock.fixed_om.loc[:,year] =  self.rollover_output(tech_class='fixed_om',tech_att='values_level', stock_att='values',year=year)  
        self.stock.variable_om.loc[:,year] = self.rollover_output(tech_class='variable_om',tech_att='values',
                                                                         stock_att='values_energy',year=year)     
        self.stock.installation_cost_new.loc[:,year] = self.rollover_output(tech_class='installation_cost_new',tech_att='values_level',
                                                                         stock_att='values_financial_new',year=year)
        self.stock.installation_cost_replacement.loc[:,year] = self.rollover_output(tech_class='installation_cost_replacement',tech_att='values_level',
                                                                         stock_att='values_financial_replacement',year=year)                
        self.stock.capital_cost.loc[:,year] = DfOper.add([self.stock.capital_cost_new.loc[:,year].to_frame(), self.stock.capital_cost_replacement.loc[:,year].to_frame()])                                                                                                                     
        self.stock.installation_cost.loc[:,year] = DfOper.add([self.stock.installation_cost_new.loc[:,year].to_frame(), self.stock.installation_cost_replacement.loc[:,year].to_frame()])
        total_costs = util.remove_df_levels(DfOper.add([self.stock.capital_cost.loc[:,year].to_frame(), self.stock.installation_cost.loc[:,year].to_frame(), self.stock.fixed_om.loc[:,year].to_frame(), self.stock.variable_om.loc[:,year].to_frame()]),['vintage', 'supply_technology'])
        self.embodied_cost.loc[:,year] = DfOper.divi([total_costs, self.active_supply],expandable=(False,False)).replace([np.inf,np.nan,-np.nan],[0,0,0])        
        self.active_embodied_cost = util.expand_multi(self.embodied_cost[year].to_frame(), levels_list = [cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')], self.demand_sectors],levels_names=[cfg.cfgfile.get('case', 'primary_geography'),'demand_sector'])

    def calculate_investment(self,year):
        if not hasattr(self.stock,'capital_cost_new_investment'):
            index = self.rollover_output(tech_class='capital_cost_new', tech_att= 'values', stock_att='sales_new',year=year).index
            self.stock.capital_cost_new_investment= util.empty_df(index, columns=['value'],fill_value=0)  
            self.stock.capital_cost_replacement_investment = util.empty_df(index, columns=['value'],fill_value=0)
            self.stock.installation_cost_new_investment = util.empty_df(index, columns=['value'],fill_value=0)
            self.stock.installation_cost_replacement_investment = util.empty_df(index, columns=['value'],fill_value=0)
        indexer = util.level_specific_indexer(self.stock.capital_cost_new_investment,'vintage', year)
        self.stock.capital_cost_new_investment.loc[indexer,:] = self.rollover_output(tech_class='capital_cost_new', tech_att= 'values', stock_att='sales_new',year=year)
        self.stock.capital_cost_replacement_investment.loc[indexer,:] = self.rollover_output(tech_class='capital_cost_replacement', tech_att= 'values', stock_att='sales_replacement',year=year)
        self.stock.installation_cost_new_investment.loc[indexer,:] = self.rollover_output(tech_class='installation_cost_new', tech_att= 'values', stock_att='sales_new',year=year)
        self.stock.installation_cost_replacement_investment.loc[indexer,:] = self.rollover_output(tech_class='installation_cost_new', tech_att= 'values', stock_att='sales_new',year=year)

        if year == max(self.years):
            keys = ['capital_cost_new', 'capital_cost_replacement','installation_cost_new','installation_cost_replacement'
                    'fixed_om', 'variable_om']
            names = keys
            self.investment = pd.concat([self.stock.capital_cost_new, self.stock.capital_cost_replacement, self.stock.installation_cost_new,
                                               self.stock.installation_cost_replacement, self.stock.fixed_om, self.stock.variable_om],keys=keys, names=names)
        
    def calculate_dispatch_costs(self, year, embodied_cost_df, loop=None):
        if hasattr(self, 'is_flexible') and self.is_flexible:
            self.calculate_dispatch_coefficients(year, loop)  
            if not isinstance(self,StorageNode):
                self.active_dispatch_costs = copy.deepcopy(self.active_trade_adjustment_df)
                for node in self.active_trade_adjustment_df.index.get_level_values('supply_node'):
                    embodied_cost_indexer = util.level_specific_indexer(embodied_cost_df, 'supply_node',node)
                    trade_adjustment_indexer = util.level_specific_indexer(self.active_trade_adjustment_df, 'supply_node',node)
                    self.active_dispatch_costs.loc[trade_adjustment_indexer,:] = DfOper.mult([self.active_trade_adjustment_df.loc[trade_adjustment_indexer,:],embodied_cost_df.loc[embodied_cost_indexer,:]]).values 
                self.active_dispatch_costs = self.active_dispatch_costs.groupby(level='supply_node').sum()
                self.active_dispatch_costs = self.active_dispatch_costs.stack([self.geography,'demand_sector'])
                self.active_dispatch_costs = util.reduce_levels(self.active_dispatch_costs, self.stock.rollover_group_names+['supply_node'], agg_function='mean')
                self.active_dispatch_costs = DfOper.mult([self.active_dispatch_costs.to_frame(), self.active_disp_coefficients])
                self.active_dispatch_costs = util.remove_df_levels(self.active_dispatch_costs, 'supply_node')
                self.active_dispatch_costs = self.active_dispatch_costs.reorder_levels(self.stock.values.index.names)               
                self.active_dispatch_costs = DfOper.add([self.active_dispatch_costs,self.rollover_output(tech_class='variable_om', tech_att= 'values', stock_att='ones',year=year)])
    
    
    def stock_normalize(self,year):
        """returns normalized stocks for use in other node calculations"""
        self.stock.values_normal.loc[:,year] = self.stock.values.loc[:,year].to_frame().groupby(level=self.stock.rollover_group_names).transform(lambda x: x / x.sum()).fillna(0)
        self.stock.values_normal_energy.loc[:,year] = DfOper.mult([self.stock.values.loc[:,year].to_frame(), self.stock.capacity_factor.loc[:,year].to_frame()]).groupby(level=self.stock.rollover_group_names).transform(lambda x: x / x.sum()).fillna(0)
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
        if hasattr(self.stock,'coefficients'):
            self.stock.coefficients.loc[:,year] = self.rollover_output(tech_class='efficiency',
                                                                         stock_att='values_normal_energy',year=year)
        else:
            index = self.rollover_output(tech_class='efficiency',stock_att='values_normal_energy',year=year).index
            self.stock.coefficients = util.empty_df(index, columns=self.years,fill_value=0.)
            self.stock.coefficients.loc[:,year] = self.rollover_output(tech_class='efficiency',stock_att='values_normal_energy',year=year)

        if 'demand_sector' not in self.stock.rollover_group_names:
            keys = self.demand_sectors
            name = ['demand_sector']
            self.active_coefficients = util.remove_df_levels(pd.concat([self.stock.coefficients.loc[:,year].to_frame()]*len(keys), keys=keys,names=name).fillna(0),['supply_technology', 'vintage','resource_bins'])              
            self.active_coefficients_untraded = copy.deepcopy(self.active_coefficients)
            self.active_coefficients_untraded.sort(inplace=True,axis=0)
            try:
                self.active_coefficients_total_untraded = util.remove_df_levels(self.active_coefficients,['efficiency_type']).reorder_levels([cfg.cfgfile.get('case','primary_geography'),'demand_sector', 'supply_node']).sort().fillna(0)      
            except:
                print self.id
        else:            
            self.active_coefficients = util.remove_df_levels(self.stock.coefficients.loc[:,year].to_frame().fillna(0),['supply_technology', 'vintage','resource_bins'])              
            self.active_coefficients_total_untraded = util.remove_df_levels(self.active_coefficients,['efficiency_type']).reorder_levels([cfg.cfgfile.get('case','primary_geography'),'demand_sector', 'supply_node']).sort().fillna(0)            
        self.active_coefficients_total = DfOper.mult([self.active_coefficients_total_untraded,self.active_trade_adjustment_df]).fillna(0)
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
        self.active_coefficients = DfOper.mult([self.active_coefficients,active_trade_adjustment_df])
        keys = self.ghgs
        name = ['ghg']
        self.active_emissions_coefficients = pd.concat([self.active_coefficients]*len(keys), keys=keys, names=name)
        self.active_emissions_coefficients = self.active_emissions_coefficients.reorder_levels([self.geography,'demand_sector', 'supply_node', 'efficiency_type', 'ghg'])
        self.active_emissions_coefficients.sort(inplace=True)
        
    def calculate_dispatch_coefficients(self, year,loop):
        """
            Calculates operating costs for all technology/vintage combinations
        """
        
        if hasattr(self, 'is_flexible') and self.is_flexible and loop == 3:
            if hasattr(self.stock,'disp_coefficients'):
                self.stock.disp_coefficients.loc[:,year] = self.rollover_output(tech_class='efficiency',
                                                                             stock_att='exist',year=year)
                                               
            else:
                index = self.rollover_output(tech_class='efficiency',stock_att='exist',year=year).index
                self.stock.disp_coefficients = util.empty_df(index, columns=self.years,fill_value=0)                                                                    
                self.stock.disp_coefficients.loc[:,year] = self.rollover_output(tech_class='efficiency',
                                                                             stock_att='exist',year=year)                     
            self.active_disp_coefficients = self.stock.disp_coefficients.loc[:,year].to_frame()                        
            self.active_disp_coefficients= util.remove_df_levels(self.active_disp_coefficients,['efficiency_type'])
    

        
    def rollover_output(self, tech_class=None, tech_att='values', stock_att=None, year=None, non_expandable_levels=('year', 'vintage')):
        """ Produces rollover outputs for a node stock based on the tech_att class, att of the class, and the attribute of the stock
        """
        stock_df = getattr(self.stock, stock_att)     
        tech_classes = util.put_in_list(tech_class)
        tech_dfs = []
        for tech_class in tech_classes:
            tech_dfs += ([self.reformat_tech_df(stock_df, tech, tech_class, tech_att, tech.id, year) for tech in
                        self.technologies.values() if
                            hasattr(getattr(tech, tech_class), tech_att) and getattr(getattr(tech, tech_class),tech_att) is not None])
        if len(tech_dfs):
            tech_df = pd.concat(tech_dfs)
            tech_df = tech_df.reorder_levels([x for x in stock_df.index.names if x in tech_df.index.names]+ [x for x in tech_df.index.names if x not in stock_df.index.names])
            if year in stock_df.columns.values:
                result_df = DfOper.mult((stock_df.loc[:,year].to_frame(),tech_df), expandable=(True, True), collapsible=(True, False),non_expandable_levels=non_expandable_levels)    
            else:
                vintage_indexer = util.level_specific_indexer(stock_df,'vintage', year)
                result_df = DfOper.mult((stock_df.loc[vintage_indexer,:], tech_df.loc[vintage_indexer,:]), expandable=(True, True), collapsible=(True, False), non_expandable_levels=non_expandable_levels)
            return result_df
        else:  
            if year in stock_df.columns.values:
                return stock_df.loc[:,year].to_frame() * 0  
            else:
                return stock_df* 0 
  

    def reformat_tech_df(self, stock_df, tech, tech_class, tech_att, tech_id, year):
        """
        reformat technoology dataframes for use in stock-level dataframe operations
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
#        else:
#            #tech has a vintage/value structure. We locate the values for the year's vintage
#            indexer = util.level_specific_indexer(tech_df, 'vintage', year)
#            tech_df = tech_df.loc[indexer,:]
        return tech_df


class StorageNode(SupplyStockNode):
    def __init__(self, id, supply_type,**kwargs):
        SupplyStockNode.__init__(self, id, supply_type, **kwargs)
        
    
    def add_technology(self, id, **kwargs):
        """
        Adds technology instances to node
        """
        if id in self.technologies:
            # ToDo note that a technology was added twice
            return
        self.technologies[id] = StorageTechnology(id, self.cost_of_capital, **kwargs)
        self.tech_ids.append(id)
        self.tech_ids.sort()

        
        
        
    def calculate_costs(self,year):
        "calculates per-unit costs in a subsector with technologies"
        if not hasattr(self.stock,'capital_cost_new'):
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
        self.stock.variable_om.loc[:,year] = DfOper.mult([self.rollover_output(tech_class='variable_om',tech_att='values', stock_att='values_normal_energy',year=year), self.active_supply],non_expandable_levels=None).groupby(level=self.stock.variable_om.index.names).sum()      
        self.stock.installation_cost_new.loc[:,year] = self.rollover_output(tech_class='installation_cost_new',tech_att='values_level',
                                                                         stock_att='values_financial_new',year=year)
        self.stock.installation_cost_replacement.loc[:,year] = self.rollover_output(tech_class='installation_cost_replacement',tech_att='values_level',
                                                                         stock_att='values_financial_replacement',year=year)
        self.stock.capital_cost.loc[:,year] = DfOper.add([self.stock.capital_cost_new_energy.loc[:,year].to_frame(), self.stock.capital_cost_replacement_energy.loc[:,year].to_frame(),self.stock.capital_cost_new_capacity.loc[:,year].to_frame(), self.stock.capital_cost_replacement_capacity.loc[:,year].to_frame()])                                                                                                                                                                                                                                     
        self.stock.installation_cost.loc[:,year] = DfOper.add([self.stock.installation_cost_new.loc[:,year].to_frame(), self.stock.installation_cost_replacement.loc[:,year].to_frame()])
        total_costs = util.remove_df_levels(DfOper.add([self.stock.capital_cost.loc[:,year].to_frame(), self.stock.installation_cost.loc[:,year].to_frame(), self.stock.fixed_om.loc[:,year].to_frame(), self.stock.variable_om.loc[:,year].to_frame()]),['vintage', 'supply_technology'])        
        total_costs = util.remove_df_levels(DfOper.add([self.stock.capital_cost.loc[:,year].to_frame(), self.stock.fixed_om.loc[:,year].to_frame(), self.stock.variable_om.loc[:,year].to_frame()]),['vintage', 'supply_technology'])
        total_stock = util.remove_df_levels(self.stock.values_energy.loc[:,year].to_frame(), ['vintage', 'supply_technology'])            
        self.embodied_cost.loc[:,year] = DfOper.divi([total_costs, total_stock])        
        self.active_embodied_cost = util.expand_multi(self.embodied_cost[year].to_frame(), levels_list = [cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')], self.demand_sectors],levels_names=[cfg.cfgfile.get('case', 'primary_geography'),'demand_sector'])


    def calculate_dispatch_coefficients(self, year,loop):
        """
            Calculates operating costs for all technology/vintage combinations
        """
        
        self.stock.values_normal_tech = self.stock.values.loc[:,year].to_frame().groupby(level=[self.geography,'supply_technology']).transform(lambda x: x/x.sum()) 
        self.stock.values_normal_tech.replace(np.inf,0,inplace=True)        
        if loop == 3:
            if hasattr(self.stock,'disp_coefficients'):
                self.stock.disp_coefficients.loc[:,year] = self.rollover_output(tech_class='efficiency',
                                                                             stock_att='values_normal_tech',year=year)                                   
            else:
                index = self.rollover_output(tech_class='efficiency',stock_att='exist',year=year).index
                self.stock.disp_coefficients = util.empty_df(index, columns=self.years,fill_value=0)                                                                    
                self.stock.disp_coefficients.loc[:,year] = self.rollover_output(tech_class='efficiency',
                                                                             stock_att='values_normal_tech',year=year)                     
            self.active_disp_coefficients = self.stock.disp_coefficients.loc[:,year].to_frame().groupby(level=[self.geography,'supply_node','supply_technology']).sum()                     
            self.active_disp_coefficients= util.remove_df_levels(self.active_disp_coefficients,['efficiency_type'])
    



        
class ImportNode(Node):
    def __init__(self, id, supply_type, **kwargs):
        Node.__init__(self,id, supply_type)
        self.cost = ImportCost(self.id)
        self.emissions = SupplyEmissions(self.id)
        self.coefficients = SupplyCoefficients(self.id)
                       
    def calculate(self,years, demand_sectors, ghgs):
        self.years = years
        self.demand_sectors = demand_sectors
        self.ghgs = ghgs
#        self.set_rollover_groups()
        attributes = vars(self)
        for att in attributes:
            obj = getattr(self, att)
            if inspect.isclass(type(obj)) and hasattr(obj, '__dict__') and hasattr(obj, 'calculate'):
                obj.calculate(self.years, self.demand_sectors)
        if self.coefficients.raw_values is not None:
            self.nodes = set(self.coefficients.values.index.get_level_values('supply_node'))
        self.emissions.calculate(self.conversion, self.resource_unit)
        self.set_trade_adjustment_dict()
        self.set_pass_through_df_dict()


    def calculate_costs(self,year):
        "calculates the embodied costs of nodes with emissions"
        if hasattr(self,'cost') and self.cost.data is True:
            if hasattr(self,'potential') and self.potential.data is True:
                self.active_embodied_cost = DfOper.mult([self.potential.active_supply_curve_normal,self.cost.values.loc[:,year].to_frame()])
                levels = ['demand_sector',cfg.cfgfile.get('case','primary_geography')]
                disallowed_levels = [x for x in self.active_embodied_cost.index.names if x not in levels]
                if len(disallowed_levels):
                    self.active_embodied_cost = util.remove_df_levels(self.active_embodied_cost, disallowed_levels)
                self.active_embodied_cost = util.expand_multi(self.active_embodied_cost, levels_list = [cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')], self.demand_sectors],levels_names=[cfg.cfgfile.get('case', 'primary_geography'),'demand_sector'])               
            else:
                allowed_indices = ['demand_sector', cfg.cfgfile.get('case','primary_geography')]
                if set(self.cost.values.index.names).issubset(allowed_indices):
                    self.active_embodied_cost = self.cost.values.loc[:,year].to_frame()
                    self.active_embodied_cost = util.expand_multi(self.active_embodied_cost, levels_list = [cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')], self.demand_sectors],levels_names=[cfg.cfgfile.get('case', 'primary_geography'),'demand_sector'])
                else:
                    raise ValueError("too many indexes in cost inputs of node %s" %self.id)


class ImportCost(Abstract):
    def __init__(self, id, **kwargs):
        self.id = id
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
                                        unit_to_den=cfg.cfgfile.get('case', 'energy_unit'))
        self.values = self.values.unstack(level='year')    
        self.values.columns = self.values.columns.droplevel()


          
class PrimaryNode(Node):
    def __init__(self, id, supply_type,**kwargs):
        Node.__init__(self,id, supply_type)
        self.potential = SupplyPotential(self.id)
        self.cost = PrimaryCost(self.id)
        self.emissions = SupplyEmissions(self.id)
        self.coefficients = SupplyCoefficients(self.id)
        self.geography = cfg.cfgfile.get('case', 'primary_geography')
      

    def calculate(self, years, demand_sectors, ghgs):
            self.years = years
            self.demand_sectors = demand_sectors
            self.ghgs = ghgs
            if self.conversion is not None:
                self.conversion.calculate(self.resource_unit)    
            self.potential.calculate(self.conversion, self.resource_unit)
            self.cost.calculate(self.conversion, self.resource_unit)
            self.emissions.calculate(self.conversion, self.resource_unit)
            self.coefficients.calculate(self.years, self.demand_sectors)
            if self.coefficients.data is True:
                self.nodes = set(self.coefficients.values.index.get_level_values('supply_node'))
            self.set_adjustments()
            self.set_pass_through_df_dict()
            self.export.calculate(self.years, self.demand_sectors)


    def calculate_costs(self,year):
        "calculates the embodied costs of nodes with emissions"
        if hasattr(self,'cost') and self.cost.data is True:
            if hasattr(self,'potential') and self.potential.data is True:
                self.active_embodied_cost = DfOper.mult([self.potential.active_supply_curve_normal,self.cost.values.loc[:,year].to_frame()])
                levels = ['demand_sector',cfg.cfgfile.get('case','primary_geography')]
                disallowed_levels = [x for x in self.active_embodied_cost.index.names if x not in levels]
                if len(disallowed_levels):
                    self.active_embodied_cost = util.remove_df_levels(self.active_embodied_cost, disallowed_levels)
                self.active_embodied_cost = util.expand_multi(self.active_embodied_cost, levels_list = [cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')], self.demand_sectors],levels_names=[cfg.cfgfile.get('case', 'primary_geography'),'demand_sector'])               
            else:
                allowed_indices = ['demand_sector', cfg.cfgfile.get('case','primary_geography')]
                if set(self.cost.values.index.names).issubset(allowed_indices):
                    self.active_embodied_cost = self.cost.values.loc[:,year].to_frame()
                    self.active_embodied_cost = util.expand_multi(self.active_embodied_cost, levels_list = [cfg.geo.geographies[cfg.cfgfile.get('case','primary_geography')], self.demand_sectors],levels_names=[cfg.cfgfile.get('case', 'primary_geography'),'demand_sector'])
                else:
                    raise ValueError("too many indexes in cost inputs of node %s" %self.id)



class PrimaryCost(Abstract):
    def __init__(self, id, node_geography=None, **kwargs):
        self.id = id
        self.node_geography = cfg.cfgfile.get('case', 'primary_geography') if node_geography is None else node_geography
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
                                                unit_to_den=cfg.cfgfile.get('case', 'energy_unit'))
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
                                            unit_to_den=cfg.cfgfile.get('case', "energy_unit"))

    

class SupplyEmissions(Abstract):
    def __init__(self, id, **kwargs):
        self.id = id
        self.input_type = 'intensity'
        self.sql_id_table = 'SupplyEmissions'
        self.sql_data_table = 'SupplyEmissionsData'
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
                                                unit_to_den=cfg.cfgfile.get('case', "energy_unit"))
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
                                            unit_to_den=cfg.cfgfile.get('case', "energy_unit"))
        self.ghgs = util.sql_read_table('GreenhouseGases','id')
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
                                        unit_to_num=cfg.cfgfile.get('case', 'energy_unit'),
                                        unit_to_den=self.resource_unit)
            self.values = self.values.unstack(level='year')    
            self.values.columns = self.values.columns.droplevel()




