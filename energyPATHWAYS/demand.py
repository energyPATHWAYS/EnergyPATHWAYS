__author__ = 'Ben Haley & Ryan Jones'

import config as cfg
import shape
import util
from datamapfunctions import DataMapFunctions
import numpy as np
import pandas as pd
from collections import defaultdict
import copy
from datetime import datetime
from demand_subsector_classes import DemandStock, SubDemand, ServiceEfficiency, ServiceLink
from shared_classes import AggregateStock
from demand_measures import ServiceDemandMeasure, EnergyEfficiencyMeasure, FuelSwitchingMeasure, FlexibleLoadMeasure
from demand_technologies import DemandTechnology, SalesShare
from rollover import Rollover
from util import DfOper
from outputs import Output
import dispatch_classes
import energyPATHWAYS.helper_multiprocess as helper_multiprocess
#from pathos.multiprocessing import Pool, cpu_count
from multiprocessing import Pool, cpu_count
import pdb
import logging
import time

class Demand(object):
    def __init__(self):
        self.drivers = {}
        self.sectors = {}
        self.outputs = Output()
        self.default_electricity_shape = shape.shapes.data[cfg.electricity_energy_type_shape_id] if shape.shapes.data else None
        self.feeder_allocation_class = dispatch_classes.DispatchFeederAllocation(1)
        self.feeder_allocation_class.values.index = self.feeder_allocation_class.values.index.rename('sector', 'demand_sector')
        self.electricity_reconciliation = None

    def add_subsectors(self):
        """Read in and initialize data"""
        # Drivers must come first
        self.add_drivers()
        # Sectors requires drivers be read in
        self.add_sectors()

        logging.info('Remapping drivers')
        self.remap_drivers()
        logging.info('Populating energy system data')
        for sector in self.sectors.values():
            logging.info('  '+sector.name+' sector')
            if cfg.cfgfile.get('case','parallel_process').lower() == 'true':
                pool = Pool(processes=cpu_count())
                subsectors = pool.map(helper_multiprocess.subsector_populate, sector.subsectors.values())
                pool.close()
                pool.join()
                sector.subsectors = dict(zip(sector.subsectors.keys(), subsectors))
            else:
                for subsector in sector.subsectors.values():
                    subsector.add_energy_system_data()
            sector.make_precursor_dict()

    def add_measures(self, demand_case_id):
        logging.info('Adding demand measures')
        for sector in self.sectors.values():
            for subsector in sector.subsectors.values():
                subsector.add_measures(demand_case_id)

    @staticmethod
    def geomap_to_dispatch_geography(df):
        """ maps a dataframe to another geography using relational GeographyMapdatabase table
        """
        if cfg.primary_geography==cfg.dispatch_geography:
            return df
        geography_map_key = cfg.cfgfile.get('case', 'default_geography_map_key')
        # create dataframe with map from one geography to another
        map_df = cfg.geo.map_df(cfg.primary_geography,cfg.dispatch_geography, normalize_as='total', map_key=geography_map_key)
        levels = ['timeshift_type', cfg.dispatch_geography, 'dispatch_feeder', 'weather_datetime']
        return util.DfOper.mult([df, map_df]).groupby(level=levels).sum()

    def aggregate_electricity_shapes(self, year, geomap_to_dispatch_geography=True):
        """ Final levels that will always return from this function
        ['timeshift_type', 'gau', 'dispatch_feeder', 'weather_datetime']
        """
#        t = util.time.time()
#        if cfg.cfgfile.get('case','parallel_process').lower() == 'true':
#            pool = Pool(processes=cfg.cpu_count())
#            b = pool.map(helper_multiprocess.aggregate_sector_shapes, [(sector, year) for sector in self.sectors.values()])
#            pool.close()
#            pool.join()
#        else:
        b = [sector.aggregate_inflexible_electricity_shape(year) for sector in self.sectors.values()]
#        t = util.time_stamp(t)
        a = [self.shape_from_subsectors_with_no_shape(year)]
#        t = util.time_stamp(t)
        agg_load = util.DfOper.add(a+b, expandable=False, collapsible=False)
#        t = util.time_stamp(t)
        agg_load = util.DfOper.mult((agg_load, self.electricity_reconciliation))
#        t = util.time_stamp(t)
        agg_load = pd.concat([agg_load]*3, keys=[1,2,3], names=['timeshift_type'])
#        t = util.time_stamp(t)
        agg_load = util.DfOper.add([sector.aggregate_flexible_electricity_shape(year) for sector in self.sectors.values()]+[agg_load], expandable=False, collapsible=False)
#        t = util.time_stamp(t)
        df = self.geomap_to_dispatch_geography(agg_load) if geomap_to_dispatch_geography else agg_load
#        t = util.time_stamp(t)
        return df

    def electricity_energy_slice(self, year, subsector_slice):
        if not hasattr(self, 'ele_energy_helper'):
            indexer = util.level_specific_indexer(self.outputs.energy, levels=['year', 'final_energy'], elements=[[year], [cfg.electricity_energy_type_id]])
            self.ele_energy_helper = self.outputs.energy.loc[indexer].groupby(level=('subsector', 'sector', cfg.primary_geography)).sum()
        feeder_allocation = self.feeder_allocation_class.values.xs(year, level='year')
        return util.remove_df_levels(util.DfOper.mult((feeder_allocation,
                                                       self.ele_energy_helper.loc[subsector_slice].groupby(level=('sector', cfg.primary_geography)).sum())), 'sector')

    def shape_from_subsectors_with_no_shape(self, year):
        """ Final levels that will always return from this function
        ['gau', 'dispatch_feeder', 'weather_datetime']
        """
        subsectors_map = defaultdict(list)
        shapes_map = {}
        for sector in self.sectors.values():
            subsectors_map[sector.id if hasattr(sector, 'shape') else None] += sector.get_subsectors_with_no_shape(year)
            shapes_map[sector.id] = sector.shape.values.xs(2, level='timeshift_type') if hasattr(sector, 'shape') else None
        shapes_map[None] = self.default_electricity_shape.values.xs(2, level='timeshift_type')
        df = util.DfOper.add([util.DfOper.mult((self.electricity_energy_slice(year, subsectors_map[id]), shapes_map[id])) for id in subsectors_map])
        del self.ele_energy_helper
        return df

    def create_electricity_reconciliation(self):
        # weather_year is the year for which we have top down load data
        weather_year = int(np.round(np.mean(shape.shapes.active_dates_index.year)))
        
        # the next four lines create the top down load shape in the weather_year
        levels_to_keep = [cfg.primary_geography, 'year', 'final_energy']
        temp_energy = self.group_output('energy', levels_to_keep=levels_to_keep, specific_years=weather_year)
        top_down_energy = util.remove_df_levels(util.df_slice(temp_energy, cfg.electricity_energy_type_id, 'final_energy'), levels='year')
        top_down_shape = top_down_energy * util.df_slice(self.default_electricity_shape.values, 2, 'timeshift_type')
        
        # this calls the functions that create the bottom up load shape for the weather_year
        bottom_up_shape = self.aggregate_electricity_shapes(weather_year, geomap_to_dispatch_geography=False)
        bottom_up_shape = util.df_slice(bottom_up_shape, 2, 'timeshift_type')
        bottom_up_shape = util.remove_df_levels(bottom_up_shape, 'dispatch_feeder')
        
        # at this point we have a top down and bottom up estimates for the load shape across all demand
        # to get the reconciliation we divide one by the other
        self.electricity_reconciliation = util.DfOper.divi((top_down_shape, bottom_up_shape))
        # the final step is to pass the reconciliation result down to subsectors. It becomes a pre-multiplier on all of the subsector shapes
        self.pass_electricity_reconciliation()
        self.pass_default_shape()

    def pass_electricity_reconciliation(self):
        """ This function threads the reconciliation factors into sectors and subsectors
            it is necessary to do it like this because we need the reconciliation at the lowest level to apply reconciliation before
            load shifting.
        """
        for sector in self.sectors:
            self.sectors[sector].pass_electricity_reconciliation(self.electricity_reconciliation)

    def pass_default_shape(self):
        for sector in self.sectors:
            self.sectors[sector].set_default_shape(self.default_electricity_shape)

    def aggregate_drivers(self):
        def remove_na_levels(df):
            if df is None:
                return None
            levels_with_na_only = [name for level, name in zip(df.index.levels, df.index.names) if list(level)==[u'N/A']]
            return util.remove_df_levels(df, levels_with_na_only).sort_index()
        df_list = []
        for driver in self.drivers.values():
            df = driver.values
            df['unit'] = driver.unit_base
            df.set_index('unit',inplace=True,append=True)
            df_list.append(df)
        df=util.df_list_concatenate(df_list,
                                     keys=[x.id for x in self.drivers.values()],new_names='driver',levels_to_keep=['driver','unit']+cfg.output_demand_levels)
        df = remove_na_levels(df) # if a level only as N/A values, we should remove it from the final outputs
        setattr(self.outputs, 'driver', df)
    
    def aggregate_results(self):
        def remove_na_levels(df):
            if df is None:
                return None
            levels_with_na_only = [name for level, name in zip(df.index.levels, df.index.names) if list(level)==[u'N/A']]
            return util.remove_df_levels(df, levels_with_na_only).sort_index()
        output_list = ['energy', 'stock', 'sales','annual_costs', 'levelized_costs', 'service_demand']
        unit_flag = [False, True, False, False, True, True]
        for output_name, include_unit in zip(output_list,unit_flag):
            df = self.group_output(output_name, include_unit=include_unit)
            df = remove_na_levels(df) # if a level only as N/A values, we should remove it from the final outputs
            setattr(self.outputs, output_name, df)
        self.aggregate_drivers()

        # this may be redundant with the above code
        for sector in self.sectors.values():
            sector.aggregate_subsector_energy_for_supply_side()
        self.aggregate_sector_energy_for_supply_side()
            
    def link_to_supply(self, embodied_emissions_link, direct_emissions_link, energy_link, cost_link):
        logging.info("linking supply emissions to energy demand")
        setattr(self.outputs, 'demand_embodied_emissions', self.group_linked_output(embodied_emissions_link))
        logging.info("calculating direct demand emissions")
        setattr(self.outputs, 'demand_direct_emissions',self.group_linked_output(direct_emissions_link) )
        logging.info("linking supply costs to energy demand")
        setattr(self.outputs, 'demand_embodied_energy_costs', self.group_linked_output(cost_link))
        logging.info("linking supply energy to energy demand")
        setattr(self.outputs, 'demand_embodied_energy', self.group_linked_output(energy_link))

    def group_output(self, output_type, levels_to_keep=None, include_unit=False, specific_years=None):
        levels_to_keep = cfg.output_demand_levels if levels_to_keep is None else levels_to_keep
        levels_to_keep = list(set(levels_to_keep + ['unit'])) if include_unit else levels_to_keep
        dfs = [sector.group_output(output_type, levels_to_keep, include_unit, specific_years) for sector in self.sectors.values()]
        if all([df is None for df in dfs]) or not len(dfs):
            return None
        dfs, keys = zip(*[(df, key) for df, key in zip(dfs, self.sectors.keys()) if df is not None])
        new_names = 'sector'
        return util.df_list_concatenate(dfs, keys, new_names, levels_to_keep)

    def group_linked_output(self, supply_link, levels_to_keep=None):
        levels_to_keep = cfg.output_combined_levels if levels_to_keep is None else levels_to_keep
        levels_to_keep = [x for x in levels_to_keep if x in self.outputs.energy.index.names]
        demand_df = self.outputs.energy.groupby(level=levels_to_keep).sum()
        demand_df = demand_df[demand_df.index.get_level_values('year')>=int(cfg.cfgfile.get('case','current_year'))]
        geography_df_list = []
        for geography in cfg.geographies:
            if geography in supply_link.index.get_level_values(cfg.primary_geography):
                supply_indexer = util.level_specific_indexer(supply_link, [cfg.primary_geography], [geography])
                demand_indexer = util.level_specific_indexer(demand_df, [cfg.primary_geography], [geography])
                supply_df = supply_link.loc[supply_indexer, :]
                geography_df =  util.DfOper.mult([demand_df.loc[demand_indexer,:], supply_df])
                geography_df_list.append(geography_df)
        df = pd.concat(geography_df_list)      
        return df
        
    def aggregate_sector_energy_for_supply_side(self):
        """Aggregates for the supply side, works with function in sector"""
        names = ['sector', cfg.primary_geography, 'final_energy', 'year']
        sectors_aggregates = [sector.aggregate_subsector_energy_for_supply_side() for sector in self.sectors.values()]
        self.energy_demand = pd.concat([s for s in sectors_aggregates if s is not None], keys=self.sectors.keys(), names=names)
        
    def add_drivers(self):
        """Loops through driver ids and call create driver function"""
        ids = util.sql_read_table('DemandDrivers',column_names='id',return_iterable=True)
        for id in ids:
            self.add_driver(id)

    def add_driver(self, id):
        """add driver object to demand"""
        if id in self.drivers:
            # ToDo note that a driver by the same name was added twice
            return
        self.drivers[id] = Driver(id)

    def remap_drivers(self):
        """
        loop through demand drivers and remap geographically
        """
        for driver in self.drivers.values():
            # It is possible that recursion has mapped before we get to a driver in the list. If so, continue.
            if driver.mapped:
                continue
            self.remap_driver(driver)

    def remap_driver(self, driver):
        """mapping of a demand driver to its base driver"""
        # base driver may be None
        base_driver_id = driver.base_driver_id
        if base_driver_id:
            base_driver = self.drivers[base_driver_id]
            # mapped is an indicator variable that records whether a driver has been mapped yet
            if not base_driver.mapped:
                # If a driver hasn't been mapped, recursion is uesd to map it first (this can go multiple layers)
                self.remap_driver(base_driver)
            driver.remap(drivers=base_driver.values, filter_geo=False)
        else:
            driver.remap(filter_geo=False)
        # Now that it has been mapped, set indicator to true
        driver.mapped = True
        driver.values.data_type = 'total'

    def add_sectors(self):
        """Loop through sector ids and call add sector function"""
        ids = util.sql_read_table('DemandSectors',column_names='id',return_iterable=True)
        for id in ids:
            self.sectors[id] = Sector(id, self.drivers)
            self.sectors[id].add_subsectors()

    def calculate_demand(self):
        logging.info('Calculating demand')
        for sector in self.sectors.values():
            logging.info('  {} sector'.format(sector.name))
            sector.manage_calculations()
        logging.info("Aggregating demand results")
        self.aggregate_results()
        logging.info('Creating electricity shape reconciliation')
        self.create_electricity_reconciliation()


class Driver(object, DataMapFunctions):
    def __init__(self, id):
        self.id = id
        self.sql_id_table = 'DemandDrivers'
        self.sql_data_table = 'DemandDriversData'
        self.mapped = False
        for col, att in util.object_att_from_table(self.sql_id_table, id):
            setattr(self, col, att)
        # creates the index_levels dictionary
        DataMapFunctions.__init__(self, data_id_key='parent_id')
        self.read_timeseries_data()


class Sector(object):
    def __init__(self, id, drivers):
        self.drivers = drivers
        self.id = id
        self.subsectors = {}
        for col, att in util.object_att_from_table('DemandSectors', id):
            setattr(self, col, att)
        self.outputs = Output()
        if self.shape_id is not None:
            self.shape = shape.shapes.data[self.shape_id]
        self.stock_subsector_ids = util.sql_read_table('DemandStock', 'subsector_id', return_iterable=True)
        self.service_demand_subsector_ids = util.sql_read_table('DemandServiceDemands', 'subsector_id', return_iterable=True)
        self.energy_demand_subsector_ids = util.sql_read_table('DemandEnergyDemands', 'subsector_id', return_iterable=True)
        self.service_efficiency_ids = util.sql_read_table('DemandServiceEfficiency', 'subsector_id', return_iterable=True)
        feeder_allocation_class = dispatch_classes.DispatchFeederAllocation(1)
        # FIXME: This next line will fail if we don't have a feeder allocation for each demand_sector
        self.feeder_allocation = util.df_slice(feeder_allocation_class.values, id, 'demand_sector')
        self.electricity_reconciliation = None
        self.workingdir = cfg.workingdir
        self.cfgfile_name = cfg.cfgfile_name
        self.pint_definitions_file = cfg.pint_definitions_file
        self.log_name = cfg.log_name

    def add_subsectors(self):
        ids = util.sql_read_table('DemandSubsectors',column_names='id',sector_id=self.id, is_active=True, return_iterable=True)
        for id in ids:
            stock = True if id in self.stock_subsector_ids else False
            service_demand = True if id in self.service_demand_subsector_ids else False
            energy_demand = True if id in self.energy_demand_subsector_ids else False
            service_efficiency = True if id in self.service_efficiency_ids else False
            self.subsectors[id] = Subsector(id, self.drivers, stock, service_demand, energy_demand, service_efficiency)

    def make_precursor_dict(self):
        """
        determines calculation order based on subsector precursors for service demand drivers or specified stocks
        example: 
            clothes washing can be a service demand precursor for water heating, and so must be solved first. This puts water heating as the 
            key in a dictionary with clothes washing as a value. Function also records the link in the service_precursors dictionary within the same loop. 
        """

        self.subsector_precursors = defaultdict(list)
        self.service_precursors = defaultdict(dict)
        self.stock_precursors = defaultdict(dict)
        for subsector in self.subsectors.values():
            for service_link in subsector.service_links.values():
                self.subsector_precursors[service_link.linked_subsector_id].append(subsector.id)
                self.service_precursors[service_link.linked_subsector_id]
            if hasattr(subsector, 'technologies'):
                for demand_technology in subsector.technologies.values():
                    linked_tech_id = demand_technology.linked_id
                    for lookup_subsector in self.subsectors.values():
                        if hasattr(lookup_subsector, 'technologies'):
                            if linked_tech_id in lookup_subsector.technologies.keys():
                                self.subsector_precursors[lookup_subsector.id].append(subsector.id)

    def manage_calculations(self):
        """
        loops through subsectors making sure to calculate subsector precursors
        before calculating subsectors themselves
        """
        precursors = set(util.flatten_list(self.subsector_precursors.values()))
        self.calculate_precursors(precursors)
        self.calculate_links(self.subsectors.keys(), precursors)
        
        if cfg.cfgfile.get('case','parallel_process').lower() == 'true':
            pool = Pool(processes=cfg.available_cpus)
            subsectors = pool.map(helper_multiprocess.subsector_calculate, self.subsectors.values())
            pool.close()
            pool.join()
            self.subsectors = dict(zip(self.subsectors.keys(), subsectors))
        else:
            for subsector in self.subsectors.values():
                if not subsector.calculated:
                    subsector.calculate()
                             
        #clear the calculations for the next scenario loop
        for subsector in self.subsectors.values():
            subsector.calculated = False

    def calculate_precursors(self, precursors):
        """ 
        calculates subsector if all precursors have been calculated
        """
        # checks whether the subsector has precursors in the subsector_precursors dictionary
        for id in precursors:
            subsector = self.subsectors[id]
            if self.subsector_precursors.has_key(subsector.id):
                # loops through subsector precursors
                for precursor_id in self.subsector_precursors[subsector.id]:
                    # finds subsector in the demand sectors and subsectors
                        if precursor_id in self.subsectors.keys():
                            # precursor is the class instance of the precursor subsector id
                            precursor = self.subsectors[precursor_id]
                            if precursor.calculated:
                                # checks whether the precursor has been calculated. If it has, update the service_precursors dictionary
                                # with the output_service_drivers if applicable. This allows a subsector to output service drivers to multiple
                                # subsectors
                                if precursor.output_service_drivers.has_key(subsector.id):
                                    self.service_precursors[subsector.id].update(
                                        {precursor.id: precursor.output_service_drivers[subsector.id]})
                                for demand_technology in precursor.output_demand_technology_stocks.keys():
                                    if demand_technology in subsector.technologies.keys():
                                        # updates stock_precursor values dictionary with linked demand_technology stocks
                                        self.stock_precursors[subsector.id].update(
                                            {demand_technology: precursor.output_demand_technology_stocks[demand_technology]})
                            else:
                                self.calculate_precursors(precursor)
            subsector.linked_service_demand_drivers = self.service_precursors[subsector.id]
            subsector.linked_stock = self.stock_precursors[subsector.id]
            subsector.calculate()

    def calculate_links(self,all_subsectors, precursors):
        for subsector_id in all_subsectors:
            subsector = self.subsectors[subsector_id]
            for precursor_id in precursors:
                precursor = self.subsectors[precursor_id]
                if precursor.output_service_drivers.has_key(subsector.id):
                    self.service_precursors[subsector.id].update(
                            {precursor.id: precursor.output_service_drivers[subsector.id]})
                for demand_technology in precursor.output_demand_technology_stocks.keys():
                    if hasattr(subsector,'technologies') and demand_technology in subsector.technologies.keys():
                        # updates stock_precursor values dictionary with linked demand_technology stocks
                        self.stock_precursors[subsector.id].update(
                            {demand_technology: precursor.output_demand_technology_stocks[demand_technology]})
            subsector.linked_service_demand_drivers = self.service_precursors[subsector.id]
            subsector.linked_stock = self.stock_precursors[subsector.id]

    def aggregate_subsector_energy_for_supply_side(self):
        """Aggregates for the supply side, works with function in demand"""
        levels_to_keep = [cfg.primary_geography, 'final_energy', 'year']
        return util.DfOper.add([pd.DataFrame(subsector.energy_forecast.value.groupby(level=levels_to_keep).sum()).sort_index() for subsector in self.subsectors.values() if hasattr(subsector, 'energy_forecast')])

    def group_output(self, output_type, levels_to_keep=None, include_unit=False, specific_years=None):
        levels_to_keep = cfg.output_demand_levels if levels_to_keep is None else levels_to_keep
        levels_to_keep = list(set(levels_to_keep + ['unit'])) if include_unit else levels_to_keep
        dfs = [subsector.group_output(output_type, levels_to_keep, specific_years) for subsector in self.subsectors.values()]
        if all([df is None for df in dfs]) or not len(dfs):
            return None
        dfs, keys = zip(*[(df, key) for df, key in zip(dfs, self.subsectors.keys()) if df is not None])
        new_names = 'subsector'
        return util.df_list_concatenate(dfs, keys, new_names, levels_to_keep)

    def get_subsectors_with_no_shape(self, year):
        """ Returns only subsectors that have electricity consumption
        """
        return [sub.id for sub in self.subsectors.values() if (sub.has_electricity_consumption(year) and not sub.has_shape() and not sub.has_flexible_load(year))]

    def aggregate_inflexible_electricity_shape(self, year):
        """ Final levels that will always return from this function
        ['gau', 'dispatch_feeder', 'weather_datetime']
        """
        subsectors_with_shape_only = [sub.id for sub in self.subsectors.values() if (sub.has_electricity_consumption(year) and sub.has_shape() and not sub.has_flexible_load(year))]
        return self.aggregate_electricity_shape(year, ids=subsectors_with_shape_only) if len(subsectors_with_shape_only) else None

    def aggregate_flexible_electricity_shape(self, year):
        """ Final levels that will always return from this function
        ['timeshift_type', 'gau', 'dispatch_feeder', 'weather_datetime']
        """
        subsectors_with_flex = [sub for sub in self.subsectors.values() if (sub.has_electricity_consumption(year) and sub.has_flexible_load(year))]
        if len(subsectors_with_flex):
            return self.aggregate_electricity_shape(year, ids=subsectors_with_flex).reorder_levels(['timeshift_type', cfg.primary_geography, 'dispatch_feeder', 'weather_datetime'])
        else:
            return None

    def aggregate_electricity_shape(self, year, ids=None):
        agg_shape = util.DfOper.add([self.subsectors[id].aggregate_electricity_shapes(year) for id in (self.subsectors.keys() if ids is None else ids)], expandable=False, collapsible=False)
        return util.DfOper.mult((self.feeder_allocation.xs(year, level='year'), agg_shape))

#self.electricity_reconciliation

    def pass_electricity_reconciliation(self, electricity_reconciliation):
        """ This function threads the reconciliation factors into sectors and subsectors
            it is necessary to do it like this because we need the reconciliation at the lowest level to apply reconciliation before
            load shifting.
        """
        self.electricity_reconciliation = electricity_reconciliation
        for subsector in self.subsectors.values():
            subsector.electricity_reconciliation = electricity_reconciliation

    def set_default_shape(self, default_shape):
        if self.shape_id is None:
            self.default_shape = default_shape
            active_shape = default_shape
        else:
            active_shape = self.shape
        for subsector in self.subsectors:
            self.subsectors[subsector].set_default_shape(active_shape, self.max_lead_hours, self.max_lag_hours)

class Subsector(DataMapFunctions):
    def __init__(self, id, drivers, stock, service_demand, energy_demand, service_efficiency):
        self.id = id
        self.drivers = drivers
        self.workingdir = cfg.workingdir
        self.cfgfile_name = cfg.cfgfile_name
        self.pint_definitions_file = cfg.pint_definitions_file
        self.log_name = cfg.log_name
        # boolean check on data availability to determine calculation steps
        self.has_stock = stock
        self.has_service_demand = service_demand
        self.has_energy_demand = energy_demand
        self.has_service_efficiency = service_efficiency
        for col, att in util.object_att_from_table('DemandSubsectors', id):
            setattr(self, col, att)
        
        self.outputs = Output()
        self.calculated = False
        if self.shape_id is not None:
            self.shape = shape.shapes.data[self.shape_id]
        self.shapes_weather_year = int(np.round(np.mean(shape.shapes.active_dates_index.year)))
        self.electricity_reconciliation = None

    def set_default_shape(self, default_shape, default_max_lead_hours, default_max_lag_hours):
        self.default_shape = default_shape if self.shape_id is None else None
        self.default_max_lead_hours = default_max_lead_hours if hasattr(self, 'max_lead_hours') else None
        self.default_max_lag_hours = default_max_lag_hours if hasattr(self, 'max_lag_hours') else None

    def has_shape(self):
        if (self.shape_id is not None) or\
           (hasattr(self, 'technologies') and np.any([tech.shape_id is not None for tech in self.technologies.values()])):
            return True
        else:
            return False

    def has_flexible_load(self, year):
        return True if (hasattr(self, 'flexible_load_measure') and self.flexible_load_measure.values.xs(year, level='year')>0) else False

    def has_electricity_consumption(self, year):
        return hasattr(self,'energy_forecast') and cfg.electricity_energy_type_id in util.get_elements_from_level(self.energy_forecast, 'final_energy')

    def get_electricity_consumption(self, year, keep_technology=False):
        """ Returns with primary geography level
        """
        if self.has_electricity_consumption(year):
            group_level = [cfg.primary_geography, 'technology'] if (keep_technology and hasattr(self, 'technologies')) else cfg.primary_geography
            return self.energy_forecast.xs([cfg.electricity_energy_type_id, year], level=['final_energy', 'year']).groupby(level=group_level).sum()
        else:
            return None

    def aggregate_electricity_shapes(self, year):
        """ Final levels that will always return from this function
        ['gau', 'weather_datetime'] or ['timeshift_type', 'gau', 'weather_datetime']
        """
        active_shape = self.shape if hasattr(self, 'shape') else self.default_shape
        active_max_lead_hours = self.max_lead_hours if hasattr(self, 'max_lead_hours') is not None else self.default_max_lead_hours
        active_max_lag_hours = self.max_lag_hours if hasattr(self, 'max_lag_hours') is not None else self.default_max_lag_hours

        # if none of the technologies have shapes, great! we can avoid having to aggregate each one separately
        if not hasattr(self, 'technologies') or np.all([tech.shape_id is None for tech in self.technologies.values()]):
            energy_slice = self.get_electricity_consumption(year)
            if energy_slice is None:
                return None
            
            if hasattr(self, 'flexible_load_measure'):
                percent_flexible = self.flexible_load_measure.values.xs(year, level='year')
                # first step is to make the three shifted profiles
                flex = shape.Shape.produce_flexible_load(util.DfOper.mult((active_shape.values, self.electricity_reconciliation)),
                                                         percent_flexible=percent_flexible, hr_delay=active_max_lag_hours, hr_advance=active_max_lead_hours)
                return util.DfOper.mult((flex, energy_slice))
            else:
                return util.DfOper.mult((active_shape.values.xs(2, level='timeshift_type'), energy_slice))

        # some technologies have their own shapes, so we need to aggregate from that level
        else:
            raise ValueError("demand_technology shapes are not fully implemented")
            energy_slice = energy_slice.groupby(level=[cfg.primary_geography, 'demand_technology']).sum()
            
            demand_technology_shapes = pd.concat([tech.get_shape(default_shape=active_shape) for tech in self.technologies.values()],
                                           keys=self.technologies.keys(), names=['demand_technology'])
            # here we might have a problem because some of the demand_technology shapes had flex load others didn't, this could lead to NaN
            # it might be possible to simply fill with 2, which would be the native shape
            return util.remove_df_levels(util.DfOper.mult((energy_slice, technology_shapes)), levels='demand_technology')

    def add_energy_system_data(self):
        """ 
        populates energy system based on available data and determines 
        subsector type 
        """
        logging.info('    '+self.name)
        
        if self.has_stock is True and self.has_service_demand is True:
            self.service_demand = SubDemand(self.id, sql_id_table='DemandServiceDemands', sql_data_table='DemandServiceDemandsData', drivers=self.drivers)
            self.add_stock()
            if self.stock.demand_stock_unit_type == 'equipment':
                self.add_technologies(self.service_demand.unit, self.stock.time_unit)
            else:
                self.add_technologies(self.stock.unit, self.stock.time_unit)
            self.sub_type = 'stock and service'
        elif self.has_stock is True and self.has_energy_demand is True:
            self.energy_demand = SubDemand(self.id, sql_id_table='DemandEnergyDemands', sql_data_table='DemandEnergyDemandsData', drivers=self.drivers)
            self.add_stock()
            if self.stock.demand_stock_unit_type == 'equipment':
                # service demand unit is equal to the energy demand unit for equipment stocks
                # where no additional service demand information is given in the form of stock units

                self.add_technologies(self.energy_demand.unit, self.stock.time_unit)
            else:
                # service demand unit is equal to the stock unit for stock input types
                # of capacity factor and service demand
                # Ex. if a stock unit was 1000 cubic feet per minute, we know that the service demand is
                # cubic feet
                self.add_technologies(self.stock.unit, self.stock.time_unit)
            self.sub_type = 'stock and energy'
        elif self.has_service_demand is True and self.has_service_efficiency is True:
            self.service_demand = SubDemand(self.id, sql_id_table='DemandServiceDemands', sql_data_table='DemandServiceDemandsData', drivers=self.drivers)
            self.service_efficiency = ServiceEfficiency(self.id, self.service_demand.unit)
            self.sub_type = 'service and efficiency'

        elif self.has_service_demand is True and self.has_energy_demand is True:
            self.service_demand = SubDemand(self.id, sql_id_table='DemandServiceDemands', sql_data_table='DemandServiceDemandsData', drivers=self.drivers)
            self.energy_demand = SubDemand(self.id, sql_id_table='DemandEnergyDemands', sql_data_table='DemandEnergyDemandsData', drivers=self.drivers)
            self.sub_type = 'service and energy'
        elif self.has_energy_demand is True:
            self.energy_demand = SubDemand(self.id, sql_id_table='DemandEnergyDemands', sql_data_table='DemandEnergyDemandsData', drivers=self.drivers)
            self.sub_type = 'energy'
            
        elif self.has_stock is True:
            self.sub_type = 'link'  
            self.add_stock()
            if self.stock.demand_stock_unit_type == 'equipment':
                # service demand unit is equal to the energy demand unit for equipment stocks
                # where no additional service demand information is given in the form of stock units

                self.add_technologies(None, None)
            else:
                raise ValueError("A subsector that has no service demand must have its stock input as equipment")
        else:
            raise ValueError("User has not input enough data")
        self.add_service_links()
        self.calculate_years()

    def filter_packages(self, case_id):
        """filters packages by case"""
        col_names = util.sql_read_headers('DemandCasesData')

        query = """
                    SELECT "DemandCasesData".*
                    FROM "DemandCasesData"
                    JOIN "DemandCasesDemandCasesData"
                      ON "DemandCasesDemandCasesData".demand_case_data_id = "DemandCasesData".id
                    WHERE "DemandCasesData".subsector_id = %s
                      AND "DemandCasesDemandCasesData".demand_case_id = %s
                """

        cfg.cur.execute(query, (self.id, case_id))
        if cfg.cur.rowcount > 1:
            pdb.set_trace()
        assert cfg.cur.rowcount <= 1,\
            "More than one DemandCasesData row found for subsector %i, case %i." % (self.id, case_id)
        result = cfg.cur.fetchone()
        logging.info("    Loading packages for " + str(self.name))
        for idx, col_name in enumerate(col_names):
            if col_name.endswith('package_id'):
                val = result[idx] if result else None
                logging.debug('  Setting %s to %s' % (col_name, "None" if val is None else str(val)))
                setattr(self, col_name, val)

    def add_measures(self, case_id):
        """ add measures to subsector based on case and package inputs """
        self.filter_packages(case_id)
        self.add_service_demand_measures()
        self.add_energy_efficiency_measures()
        self.add_fuel_switching_measures()
        self.add_stock_measures()
        self.add_flexible_load_measures()

    def add_stock_measures(self):
        """ add specified stock and sales measures to model if the subsector
        is populated with stock data """
        if self.has_stock:
            for tech in self.technologies:
                self.technologies[tech].add_specified_stock_measures(self.stock_package_id)
                self.technologies[tech].add_sales_share_measures(self.sales_package_id)

    def calculate(self):
        logging.info("    calculating" + " " +  self.name)
        logging.debug('      '+'calculating measures')
        self.calculate_measures()
        logging.debug('      '+'adding linked inputs')
        self.add_linked_inputs(self.linked_service_demand_drivers, self.linked_stock)
        logging.debug('      '+'forecasting energy drivers')
        self.project()
        logging.debug('      '+'calculating subsector energy demand')
        self.calculate_energy()
        self.project_measure_stocks()
        self.calculated = True
        logging.debug('      '+'calculating costs')
        self.calculate_costs()
        logging.debug('      '+'processing outputs')
        self.remove_extra_subsector_attributes()

    def add_linked_inputs(self, linked_service_demand_drivers, linked_stock):
        """ adds linked inputs to subsector """
        self.linked_service_demand_drivers = linked_service_demand_drivers
        self.linked_stock = linked_stock
        self.interpolation_method = 'linear_interpolation'
        self.extrapolation_method = 'linear_interpolation'

    def group_output(self, output_type, levels_to_keep=None, specific_years=None):
        levels_to_keep = cfg.output_demand_levels if levels_to_keep is None else levels_to_keep
        if output_type=='energy':
            # a subsector type link would be something like building shell, which does not have an energy demand
            if self.sub_type != 'link':
                return_array = self.energy_forecast
            else:
                return None
        elif output_type=='stock':
            return_array = self.format_output_stock(levels_to_keep)
        elif output_type=='sales':
            return_array = self.format_output_sales(levels_to_keep)
        elif output_type=='annual_costs':
            return_array =  self.format_output_costs('annual_costs', levels_to_keep)
        elif output_type=='levelized_costs':
            return_array = self.format_output_costs('levelized_costs', levels_to_keep)
        elif output_type=='service_demand':
            return_array = self.format_output_service_demand(levels_to_keep)

        return util.df_slice(return_array, specific_years, 'year', drop_level=False) if specific_years else return_array

    def format_output_service_demand(self, override_levels_to_keep):
        if not hasattr(self, 'service_demand'):
            return None
        if hasattr(self.service_demand,'modifier'):
            service_demand_normal = util.DfOper.mult([self.service_demand.modifier,self.stock.values]).groupby(level=self.stock.rollover_group_names).transform(lambda x: x/x.sum())
            df = util.DfOper.mult([service_demand_normal,self.service_demand.values])
        else:
            df = self.service_demand.values
        levels_to_keep = cfg.output_demand_levels if override_levels_to_keep is None else override_levels_to_keep
        levels_to_eliminate = [l for l in df.index.names if l not in levels_to_keep]
        df = util.remove_df_levels(df,levels_to_eliminate).sort_index()
        df = df.stack().to_frame()
        util.replace_column_name(df,'value')
        util.replace_index_name(df, 'year')
        df = util.add_and_set_index(df, 'unit', self.service_demand.unit.upper(), index_location=-2)
        df.columns = ['value']
        return df
    
    def format_output_sales(self, override_levels_to_keep):
        if not hasattr(self, 'stock'):
            return None
        levels_to_keep = cfg.output_supply_levels if override_levels_to_keep is None else override_levels_to_keep
        levels_to_eliminate = [l for l in self.stock.sales.index.names if l not in levels_to_keep]
        df = self.stock.sales
        util.replace_index_name(df, 'year','vintage')
        df = util.remove_df_levels(df, levels_to_eliminate).sort_index()
        df = util.add_and_set_index(df, 'unit', self.stock.unit.upper(), -2)
        return df

    def format_output_stock(self, override_levels_to_keep=None):
        if not hasattr(self, 'stock'):
            return None
        levels_to_keep = cfg.output_demand_levels if override_levels_to_keep is None else override_levels_to_keep
        levels_to_eleminate = [l for l in self.stock.values.index.names if l not in levels_to_keep]
        df = util.remove_df_levels(self.stock.values, levels_to_eleminate).sort_index()
        # stock starts with vintage as an index and year as a column, but we need to stack it for export
        df = df.stack().to_frame()
        util.replace_column_name(df,'value')
        util.replace_index_name(df, 'year')
        index_location = -3 if ('year' in levels_to_keep and 'vintage' in levels_to_keep) else -2
        df = util.add_and_set_index(df, 'unit', self.stock.unit.upper(), index_location)
        df.columns = ['value']
        return df
        
    def format_output_measure_costs(self, att, override_levels_to_keep=None):
        measure_types = [x for x in ['ee_stock','fs_stock','sd_stock'] if hasattr(self,x)]
        if len(measure_types):
            df_list = []
            for measure_type in measure_types:
                df = getattr(getattr(self,measure_type),att)['unspecified']
                if list(df.columns) != ['value']:
                    df = df.stack().to_frame()
                    df.columns = ['value']
                    util.replace_index_name(df, 'year')
                    if df.sum().values ==0:
                        continue
                    df = df[df.values>0]
                else:
                    util.replace_index_name(df, 'year','vintage')
                    df = df[df.values>0]
                df_list.append(df)
            if len(df_list):
                keys = measure_types
                names = ['measure_types']
                df = pd.concat(df_list,keys=keys,names=names)
                unit = cfg.cfgfile.get('case','currency_year_id') + " " + cfg.cfgfile.get('case','currency_name')
                df.columns = [unit]
                return df
            else:
                return None
        else:
            return None
        
    def format_output_costs(self,att,override_levels_to_keep=None):
        stock_costs = self.format_output_stock_costs(att, override_levels_to_keep)
        measure_costs = self.format_output_measure_costs(att, override_levels_to_keep)   
        cost_list = []
        for cost in [stock_costs, measure_costs]:
            if cost is not None:
                cost_list.append(cost)
        if len(cost_list) == 0:
            return None
        if len(cost_list) == 1:
            return cost_list[0]
        else:
            keys = ['stock', 'measure']
            names = ['cost_type']
            return util.df_list_concatenate(cost_list,keys=keys,new_names=names)
  
    def format_output_stock_costs(self, att, override_levels_to_keep=None):
        """ 
        Formats cost outputs
        """
        if not hasattr(self, 'stock'):
            return None
        cost_dict = getattr(self.stock, att)
        keys, values = zip(*[(a, b) for a, b in util.unpack_dict(cost_dict)])
        keys = util.flatten_list([[tuple(k)]*len(v) for k, v in zip(keys, values)])
        values = list(values)
        for index, value in enumerate(values):
            if list(value.columns) != ['value']:
                value = value.stack().to_frame()
                value.columns = ['value']
                util.replace_index_name(value, 'year')
                values[index] = value
            else:
                util.replace_index_name(value, 'year','vintage')
        df = util.df_list_concatenate(values, keys=keys, new_names=['cost category', 'new/replacement'], levels_to_keep=override_levels_to_keep)
        unit = cfg.cfgfile.get('case','currency_year_id') + " " + cfg.cfgfile.get('case','currency_name')
        df.columns = [unit]        
        return df

    def calculate_measures(self):
        """calculates measures for use in subsector calculations """
        for measure in self.energy_efficiency_measures.values():
            measure.calculate(self.vintages, self.years, cfg.calculation_energy_unit)
        for measure in self.service_demand_measures.values():
            if hasattr(self,'stock') and self.stock.demand_stock_unit_type == 'service demand' and hasattr(self,'service_demand'):
                #service demand will be converted to stock unit, so measure must be converted to stock unit
                measure.calculate(self.vintages, self.years, self.stock.unit)
            elif hasattr(self,'service_demand'):
                measure.calculate(self.vintages, self.years, self.service_demand.unit)
            elif hasattr(self,'energy_demand'):
                measure.calculate(self.vintages, self.years, self.energy_demand.unit)
            else:
                raise ValueError("service demand measure has been created for a subsector which doesn't have an energy demand or service demand")
        for measure in self.fuel_switching_measures.values():
            measure.calculate(self.vintages, self.years, cfg.calculation_energy_unit)

    def calculate_energy(self):
        """ calculates energy demand for all subsector types"""
        logging.debug('      '+'subsector type = '+self.sub_type)
        if self.sub_type == 'service and efficiency' or self.sub_type == 'service and energy':
            # sets the service demand forecast equal to initial values
            # calculates the energy demand change from fuel swiching measures
            self.fuel_switching_impact_calc()
            # calculates the energy demand change from energy efficiency measures
            self.energy_efficiency_savings_calc()
            # adds an index level of subsector name as demand_technology to the dataframe for use in aggregated outputs
        elif self.sub_type == 'energy':
            # calculates the energy demand change from fuel swiching measures
            self.fuel_switching_impact_calc()
            # calculates the energy demand change from fuel swiching measures
            self.energy_efficiency_savings_calc()
            # adds an index level of subsector name as demand_technology to the dataframe for use in aggregated outputs
        elif self.sub_type == 'stock and service' or self.sub_type == 'stock and energy':
            # initiates the energy calculation for a subsector with a stock
            self.calculate_energy_stock()
            # calculates service demand and stock linkages to pass to other subsectors 
            self.calculate_output_service_drivers()
            self.calculate_output_demand_technology_stocks()
        elif self.sub_type == 'link':
            self.calculate_output_service_drivers()
            self.calculate_output_demand_technology_stocks()

    def calculate_costs(self):
        """ calculates cost outputs for all subsector types """
        if hasattr(self,'stock'):
            self.calculate_costs_stock()
        self.calculate_costs_measures()

    def calculate_years(self):
        """determines the analysis period within the subsector based on the minimum year
        of all inputs 
        """
#        self.calculate_driver_min_year()
        driver_min_year = 9999
        if self.sub_type == 'stock and energy':
            tech_min_year = self.calculate_tech_min_year()
            stock_min_year = min(
                self.stock.raw_values.index.levels[util.position_in_index(self.stock.raw_values, 'year')])
            sales_share = util.sql_read_table('DemandSalesData', 'vintage', return_iterable=True, subsector_id=self.id)            
            if len(sales_share):                
                sales_share_min_year = min(sales_share)
            else:
                sales_share_min_year = 9999
            energy_min_year = min(self.energy_demand.raw_values.index.levels[
                util.position_in_index(self.energy_demand.raw_values, 'year')])
            self.min_year = min(int(cfg.cfgfile.get('case', 'current_year')), driver_min_year, tech_min_year,
                                stock_min_year, sales_share_min_year, energy_min_year)
        elif self.sub_type == 'stock and service':
            tech_min_year = self.calculate_tech_min_year()
            stock_min_year = min(
                self.stock.raw_values.index.levels[util.position_in_index(self.stock.raw_values, 'year')])
            sales_share = util.sql_read_table('DemandSalesData', 'vintage', return_iterable=True, subsector_id=self.id)            
            if len(sales_share):                
                sales_share_min_year = min(sales_share)
            else:
                sales_share_min_year = 9999
            service_min_year = min(self.service_demand.raw_values.index.levels[
                util.position_in_index(self.service_demand.raw_values, 'year')])
            self.min_year = min(int(cfg.cfgfile.get('case', 'current_year')), driver_min_year, tech_min_year,
                                stock_min_year, sales_share_min_year, service_min_year)
        elif self.sub_type == 'service and efficiency':
            service_min_year = min(self.service_demand.raw_values.index.levels[
                util.position_in_index(self.service_demand.raw_values, 'year')])
            service_efficiency_min_year = min(self.service_demand.raw_values.index.levels[
                util.position_in_index(self.service_demand.raw_values, 'year')])
            self.min_year = min(int(cfg.cfgfile.get('case', 'current_year')), driver_min_year, service_min_year,
                                service_efficiency_min_year)
        elif self.sub_type == 'service and energy':
            service_min_year = min(self.service_demand.raw_values.index.levels[
                util.position_in_index(self.service_demand.raw_values, 'year')])
            energy_min_year = min(self.energy_demand.raw_values.index.levels[
                util.position_in_index(self.energy_demand.raw_values, 'year')])
            self.min_year = min(int(cfg.cfgfile.get('case', 'current_year')), driver_min_year, service_min_year,
                                energy_min_year)
        elif self.sub_type == 'energy':
            energy_min_year = min(self.energy_demand.raw_values.index.levels[
                util.position_in_index(self.energy_demand.raw_values, 'year')])
            self.min_year = min(int(cfg.cfgfile.get('case', 'current_year')), driver_min_year, energy_min_year)
            
        elif self.sub_type == 'link':
            tech_min_year = self.calculate_tech_min_year()
            stock_min_year = min(
                self.stock.raw_values.index.levels[util.position_in_index(self.stock.raw_values, 'year')])
            sales_share = util.sql_read_table('DemandSalesData', 'vintage', return_iterable=True, subsector_id=self.id)             
            if len(sales_share):                
                sales_share_min_year = min(sales_share)
            else:
                sales_share_min_year = 9999
            self.min_year = min(int(cfg.cfgfile.get('case', 'current_year')), driver_min_year, tech_min_year,
                                    stock_min_year, sales_share_min_year)
        self.min_year = max(self.min_year, int(cfg.cfgfile.get('case', 'demand_start_year')))
        self.min_year = min(self.shapes_weather_year, self.min_year)
        self.min_year = int(int(cfg.cfgfile.get('case', 'year_step'))*round(float(self.min_year)/int(cfg.cfgfile.get('case', 'year_step'))))
        self.years = range(self.min_year, int(cfg.cfgfile.get('case', 'end_year')) + 1,
                           int(cfg.cfgfile.get('case', 'year_step')))
        
        self.vintages = self.years


    def calculate_tech_min_year(self):
        """
        calculates the minimum input years of all subsector technologies
        """
        min_years = []
        if hasattr(self, 'technologies'):
            for tech in self.technologies:
                min_years.append(self.technologies[tech].min_year)
            return min(min_years)


    def calculate_driver_min_year(self):
        """
        calculates the minimum input years of all subsector drivers
        """
        min_years = []
        if self.has_stock:
            for driver in self.stock.drivers.values():
                min_years.append(min(driver.raw_values.index.levels[util.position_in_index(driver.raw_values, 'year')]))
        if self.has_energy_demand:
            for driver in self.energy_demand.drivers.values():
                min_years.append(min(driver.raw_values.index.levels[util.position_in_index(driver.raw_values, 'year')]))
        if self.has_service_demand:
            for driver in self.service_demand.drivers.values():
                min_years.append(min(driver.raw_values.index.levels[util.position_in_index(driver.raw_values, 'year')]))
        if len(min_years):
            self.driver_min_year = min(min_years)
        else:
            self.driver_min_year = 9999


    def calculate_technologies(self):
        """ 
        inititates calculation of all demand_technology attributes - costs, efficiency, etc.
        """
        if hasattr(self, 'technologies'):
            tech_classes = ['capital_cost_new', 'capital_cost_replacement', 'installation_cost_new',
                            'installation_cost_replacement', 'fixed_om', 'fuel_switch_cost', 'efficiency_main',
                            'efficiency_aux']
            tests = defaultdict(list)
            for tech in self.technologies.keys():
                if tech in util.sql_read_table('DemandTechs', 'linked_id'):
                    tests[self.technologies[tech].id].append(False)
                if self.technologies[tech].reference_sales_shares.has_key(1):
                    tests[self.technologies[tech].id].append(self.technologies[tech].reference_sales_shares[1].raw_values.sum().sum() == 0)
                tests[self.technologies[tech].id].append(len(self.technologies[tech].sales_shares) == 0)
                tests[self.technologies[tech].id].append(len(self.technologies[tech].specified_stocks) == 0)
                # Do we have a specified stock in the inputs for this tech?
                if 'demand_technology' in self.stock.raw_values.index.names and tech in util.elements_in_index_level(self.stock.raw_values, 'demand_technology'):
                    tests[self.technologies[tech].id].append(self.stock.raw_values.groupby(level='demand_technology').sum().loc[tech].value==0)
                for tech_class in tech_classes:
                    if hasattr(getattr(self.technologies[tech], tech_class), 'reference_tech_id') and getattr(getattr(self.technologies[tech], tech_class), 'reference_tech_id') is not None:
                        tests[getattr(getattr(self.technologies[tech], tech_class), 'reference_tech_id')].append(False)
            for tech in self.technologies.keys():
                if all(tests[tech]):
                    self.tech_ids.remove(tech)
                    del self.technologies[tech]
                else:
                    self.technologies[tech].calculate([self.vintages[0] - 1] + self.vintages, self.years)
            self.remap_tech_attrs(tech_classes)


    def add_energy_efficiency_measures(self):
        """
        add all energy efficiency measures in a selected package to a dictionary
        """
        self.energy_efficiency_measures = {}
        ids = util.sql_read_table("DemandEnergyEfficiencyMeasurePackagesData",column_names='measure_id',package_id=self.energy_efficiency_package_id,return_iterable=True)
        for id in ids:
            self.add_energy_efficiency_measure(id, self.cost_of_capital)

    def add_energy_efficiency_measure(self, id, cost_of_capital, **kwargs):
        """Adds measure class instance to subsector"""
        if id in self.energy_efficiency_measures:
            # ToDo note that a demand_technology was added twice
            return
        self.energy_efficiency_measures[id] = EnergyEfficiencyMeasure(id, cost_of_capital)

    def energy_efficiency_measure_savings(self):
        """
        calculates measure savings for measures input as intensity
        based on the energy forecast it is being applied to i.e. 10% of x = y
        """
        for measure in self.energy_efficiency_measures.values():
            if measure.input_type == 'intensity':
                measure.savings = DfOper.mult([measure.values, self.energy_forecast])
            else:
                measure.remap(map_from='values', map_to='savings', drivers=self.energy_forecast)

    def energy_efficiency_savings_calc(self):
        """
        sums and reconciles energy efficiency savings with total available energy to be saved
        """
        # create an empty df
        self.energy_efficiency_measure_savings()
        self.initial_energy_efficiency_savings = util.empty_df(self.energy_forecast.index,
                                                               self.energy_forecast.columns.values)
        # add up each measure's savings to return total savings
        for id in self.energy_efficiency_measures:
            measure = self.energy_efficiency_measures[id]
            self.initial_energy_efficiency_savings = DfOper.add([self.initial_energy_efficiency_savings,
                                                                 measure.savings])
        # check for savings in excess of demand
        excess_savings = DfOper.subt([self.energy_forecast, self.initial_energy_efficiency_savings]) * -1
        excess_savings[excess_savings < 0] = 0
        # if any savings in excess of demand, adjust all measure savings down
        if excess_savings.sum()['value'] == 0:
            self.energy_efficiency_savings = self.initial_energy_efficiency_savings
        else:
            self.energy_efficiency_savings = DfOper.subt([self.initial_energy_efficiency_savings,
                                                          excess_savings])
            impact_adjustment = self.energy_efficiency_savings / self.initial_energy_efficiency_savings
            for measure in self.energy_efficiency_measures.values():
                measure.savings = DfOper.mult([measure.savings, impact_adjustment])
        self.energy_forecast = DfOper.subt([self.energy_forecast, self.energy_efficiency_savings])

    def add_service_demand_measures(self):
        """
        add all service demand measures in a selected package to a dictionary
        """
        self.service_demand_measures = {}
        ids = util.sql_read_table("DemandServiceDemandMeasurePackagesData",column_names='measure_id',package_id=self.service_demand_package_id,return_iterable=True)
        for id in ids:
            self.add_service_demand_measure(id, self.cost_of_capital)

    def add_service_demand_measure(self, id, cost_of_capital, **kwargs):
        """Adds measure instances to subsector"""
        if id in self.service_demand_measures:
            return
        self.service_demand_measures[id] = ServiceDemandMeasure(id, cost_of_capital)

    def service_demand_measure_savings(self):
        """
        calculates measure savings based on the service demand forecast it is being applied to
        i.e. 10% of x = y
        """
        for id in self.service_demand_measures:
            measure = self.service_demand_measures[id]
            if measure.input_type == 'intensity':
                measure.savings = DfOper.mult([measure.values,self.service_demand.values])
            else:
                measure.remap(map_from='values', map_to='savings', drivers=self.service_demand.values)

    def service_demand_savings_calc(self):
        """
        sums and reconciles service demand savings with total available service demand to be saved
        """
        # create an empty df
        self.service_demand_measure_savings()
        self.initial_service_demand_savings = util.empty_df(self.service_demand.values.index,
                                                            self.service_demand.values.columns.values)
        # add up each measure's savings to return total savings
        for id in self.service_demand_measures:
            measure = self.service_demand_measures[id]
            self.initial_service_demand_savings = DfOper.add([self.initial_service_demand_savings,
                                                              measure.savings])
        # check for savings in excess of demand
        excess_savings = DfOper.subt([self.service_demand.values, self.initial_service_demand_savings]) * -1
        excess_savings[excess_savings < 0] = 0
        # if any savings in excess of demand, adjust all measure savings down
        if excess_savings.sum()['value'] == 0:
            self.service_demand_savings = self.initial_service_demand_savings
        else:
            self.service_demand_savings = DfOper.subt([self.initial_service_demand_savings, excess_savings])
            impact_adjustment = self.service_demand_savings / self.initial_service_demand_savings
            for id in self.service_demand_measures:
                measure = self.service_demand_measures[id]
                measure.savings = DfOper.mult([measure.savings, impact_adjustment])
        self.service_demand.values = DfOper.subt([self.service_demand.values,
                                                    self.service_demand_savings])

    def add_flexible_load_measures(self):
        """
        add all flexible load measures in a selected package to a dictionary
        """
        if self.flexible_load_package_id is not None:
            id = util.sql_read_table("DemandFlexibleLoadMeasurePackagesData",column_names='measure_id',package_id=self.flexible_load_package_id,return_iterable=False)
            self.flexible_load_measure = FlexibleLoadMeasure(id)

    def add_fuel_switching_measures(self):
        """
        add all fuel switching measures in a selected package to a dictionary
        """
        self.fuel_switching_measures = {}
        ids = util.sql_read_table("DemandFuelSwitchingMeasurePackagesData",column_names='measure_id',package_id=self.fuel_switching_package_id,return_iterable=True)
        for id in ids:
            self.add_fuel_switching_measure(id, self.cost_of_capital)

    def add_fuel_switching_measure(self, id, cost_of_capital):
        """Adds measure instances to subsector"""
        if id in self.fuel_switching_measures:
            # ToDo note that a demand_technology was added twice
            return
        self.fuel_switching_measures[id] = FuelSwitchingMeasure(id, cost_of_capital)

    def fuel_switching_measure_impacts(self):
        """
        calculates measure impact in energy terms for measures defined as intensity. For measures defined
        as totals, the measure is remapped to the energy forecast. 
        """
        for measure in self.fuel_switching_measures.values():
            indexer = util.level_specific_indexer(self.energy_forecast, 'final_energy', measure.final_energy_from_id)
            if measure.impact.input_type == 'intensity':
                measure.impact.savings = DfOper.mult([measure.impact.values,
                                                      self.energy_forecast.loc[indexer, :]])
            else:
                measure.impact.remap(map_from='values', map_to='savings', drivers=self.energy_forecast.loc[indexer, :])
            measure.impact.additions = DfOper.mult([measure.impact.savings, measure.energy_intensity.values])
            util.replace_index_label(measure.impact.additions,
                                     {measure.final_energy_from_id: measure.final_energy_to_id},
                                     level_name='final_energy')

    def fuel_switching_impact_calc(self):
        """
        sums and reconciles fuel switching impacts with total available energy to be saved
        """
        # create an empty df
        self.fuel_switching_measure_impacts()
        self.initial_fuel_switching_savings = util.empty_df(self.energy_forecast.index,
                                                            self.energy_forecast.columns.values)
        self.fuel_switching_additions = util.empty_df(self.energy_forecast.index, self.energy_forecast.columns.values)
        # add up each measure's savings to return total savings
        for measure in self.fuel_switching_measures.values():
            self.initial_fuel_switching_savings = DfOper.add([self.initial_fuel_switching_savings,
                                                              measure.impact.savings])
            self.fuel_switching_additions = DfOper.add([self.fuel_switching_additions,
                                                        measure.impact.additions])
        # check for savings in excess of demand

        fs_savings = DfOper.subt([self.energy_forecast, self.initial_fuel_switching_savings])
        excess_savings = DfOper.add([self.fuel_switching_additions, fs_savings]) * -1
        excess_savings[excess_savings < 0] = 0
        # if any savings in excess of demand, adjust all measure savings down
        if excess_savings.sum()['value'] == 0:
            self.fuel_switching_savings = self.initial_fuel_switching_savings
        else:
            self.fuel_switching_savings = DfOper.subt([self.initial_fuel_switching_savings, excess_savings])
            impact_adjustment = self.fuel_switching_savings / self.initial_fuel_switching_savings
            for measure in self.fuel_switching_measures.values():
                measure.impact.savings = DfOper.mult([measure.impact.savings, impact_adjustment])
        self.energy_forecast = DfOper.subt([self.energy_forecast, self.fuel_switching_savings])
        self.energy_forecast = DfOper.add([self.energy_forecast, self.fuel_switching_additions])

    def add_service_links(self):
        """ loops through service demand links and adds service demand link instance to subsector"""
        self.service_links = {}
        link_ids = util.sql_read_table('DemandServiceLink', 'id', subsector_id=self.id)
        if link_ids is not None:
            for link_id in util.ensure_iterable_and_not_string(link_ids):
                self.add_service_link(link_id)

    def add_service_link(self, link_id):
        """add service demand link object to subsector"""
        if link_id in self.service_links:
            # ToDo note that a service link by the same name was added twice
            return
        self.service_links[link_id] = ServiceLink(link_id)

    def add_stock(self):
        """add stock instance to subsector"""
        self.stock = DemandStock(id=self.id, drivers=self.drivers)

    def add_technologies(self, service_demand_unit, stock_time_unit):
        """loops through subsector technologies and adds demand_technology instances to subsector"""
        self.technologies = {}
        ids = util.sql_read_table("DemandTechs",column_names='id',subsector_id=self.id, return_iterable=True)
        for id in ids:
            self.add_demand_technology(id, self.id, service_demand_unit, stock_time_unit, self.cost_of_capital)
        self.tech_ids = self.technologies.keys()
        self.tech_ids.sort()


    def add_demand_technology(self, id, subsector_id, service_demand_unit, stock_time_unit, cost_of_capital, **kwargs):
        """Adds demand_technology instances to subsector"""
        if id in self.technologies:
            # ToDo note that a demand_technology was added twice
            return
        self.technologies[id] = DemandTechnology(id, subsector_id, service_demand_unit, stock_time_unit, cost_of_capital, **kwargs)

    def remap_tech_attrs(self, attr_classes, attr='values'):
        """
        loops through attr_classes (ex. capital_cost, energy, etc.) in order to map technologies
        that reference other technologies in their inputs (i.e. demand_technology A is 150% of the capital cost demand_technology B)
        """
        attr_classes = util.ensure_iterable_and_not_string(attr_classes)
        for demand_technology in self.technologies.keys():
            for attr_class in attr_classes:
                # It is possible that recursion has converted before we get to an
                # attr_class in the list. If so, continue.
#                  if getattr(getattr(self.technologies[demand_technology], attr_class), 'absolute'):
#                      continue
                self.remap_tech_attr(demand_technology, attr_class, attr)
                
    def remap_tech_attr(self, demand_technology, class_name, attr):
        """
        map reference demand_technology values to their associated demand_technology classes
        
        """
        tech_class = getattr(self.technologies[demand_technology], class_name)
        if hasattr(tech_class, 'reference_tech_id'):
            if getattr(tech_class, 'reference_tech_id'):
                ref_tech_id = (getattr(tech_class, 'reference_tech_id'))
                ref_tech_class = getattr(self.technologies[ref_tech_id], class_name)
                # converted is an indicator of whether an input is an absolute
                # or has already been converted to an absolute
                if not getattr(ref_tech_class, 'absolute'):
                    # If a technnology hasn't been mapped, recursion is used
                    # to map it first (this can go multiple layers)
                    self.remap_tech_attr(getattr(tech_class, 'reference_tech_id'), class_name, attr)
                if tech_class.raw_values is not None:
                    tech_data = getattr(tech_class, attr)
                    flipped = getattr(ref_tech_class, 'flipped') if hasattr(ref_tech_class, 'flipped') else False
                    if flipped is True:
                        tech_data = 1 / tech_data
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
        else:
            pass
        # Now that it has been converted, set indicator to true
        tech_class.absolute = True


    def project_measure_stocks(self):
        """ projects the 'stock' of measures for use in cost calculation """
        if self.sub_type == 'service and efficiency' or self.sub_type == 'service and energy':
            self.project_sd_measure_stock()
            self.project_ee_measure_stock()
            self.project_fs_measure_stock()
        elif self.sub_type == 'energy':
            self.project_ee_measure_stock()
            self.project_fs_measure_stock()
        else:
            self.project_sd_measure_stock()


    def project(self):
        """"projects subsector data based on subsector types"""
        if self.sub_type == 'service and efficiency':
            self.project_service_demand()
            self.service_efficiency.calculate(self.vintages, self.years)
            self.energy_forecast = DfOper.mult([self.service_demand.values, self.service_efficiency.values])
        elif self.sub_type == 'service and energy':
            self.project_service_demand(service_dependent=True)
            self.project_energy_demand(service_dependent=True)
            self.energy_demand.values = util.unit_convert(self.energy_demand.values,
                                                          unit_from_num=self.energy_demand.unit,
                                                          unit_to_num=cfg.calculation_energy_unit)
            self.energy_forecast = self.energy_demand.values
        elif self.sub_type == 'energy':
            self.project_energy_demand()
            self.energy_demand.values = util.unit_convert(self.energy_demand.values,
                                                          unit_from_num=self.energy_demand.unit,
                                                          unit_to_num=cfg.calculation_energy_unit)
            self.energy_forecast = self.energy_demand.values 
        elif self.sub_type == 'link':
            self.calculate_technologies()
            self.project_stock()
        elif self.sub_type == 'stock and service' or self.sub_type == 'stock and energy':
            self.calculate_technologies()
            # determine what levels the service demand forecast has in order to determine
            # what levels to calculate the service demand modifier on i.e. by demand_technology
            # or by final energy
            self.determine_service_subset()
            if self.stock.demand_stock_unit_type == 'equipment':
                if self.sub_type == 'stock and energy':
                    # determine the year range of energy demand inputs
                    self.min_year = self.min_cal_year(self.energy_demand)
                    self.max_year = self.max_cal_year(self.energy_demand)
                    # project the stock and prepare a subset for use in calculating
                    # the efficiency of the stock during the years in which we have
                    # energy demand inputs
                    self.project_stock(stock_dependent=self.energy_demand.is_stock_dependent)
                    self.stock_subset_prep()
                    self.energy_demand.project(map_from='raw_values', fill_timeseries=False)
                    # divide by the efficiency of the stock to return service demand values
                    self.efficiency_removal()
                elif self.sub_type == 'stock and service':
                    # determine the year range of service demand inputs
                    self.min_year = self.min_cal_year(self.service_demand)
                    self.max_year = self.max_cal_year(self.service_demand)
            elif self.stock.demand_stock_unit_type == 'capacity factor':
                if self.sub_type == 'stock and service':
                    # determine the year range of service demand inputs
                    self.min_year = self.min_cal_year(self.service_demand)
                    self.max_year = self.max_cal_year(self.service_demand)
                    # project the service demand
                    self.service_demand.project(map_from='raw_values', fill_timeseries=False, service_dependent=self.stock.is_service_demand_depedent)
                    # service demand is projected, so change map from to values
                    self.service_demand.map_from = 'values'
                    # change the service demand to a per stock_time_unit service demand
                    # ex. kBtu/year to kBtu/hour average service demand
                    time_step_service = util.unit_convert(self.service_demand.values, unit_from_den='year',
                                                          unit_to_den=self.stock.time_unit)
                    # divide by capacity factor stock inputs to get a service demand stock
                    # ex. kBtu/hour/capacity factor equals kBtu/hour stock
                    self.stock.remap(map_from='raw_values', map_to='int_values', fill_timeseries=False)
                    _, x = util.difference_in_df_names(time_step_service, self.stock.int_values)
                    if x:
                        raise ValueError('service demand must have the same index levels as stock when stock is specified in capacity factor terms')
                    else:
                        self.stock.int_values = DfOper.divi([time_step_service, self.stock.int_values])
                    # change map_from to int_values, which is an intermediate value, not yet final
                    self.stock.map_from = 'int_values'
                    # stock is by definition service demand dependent
                    self.stock.is_service_demand_dependent = 1
                else:
                    # used when we don't have service demand, just energy demand
                    # determine the year range of energy demand inputs
                    self.min_year = self.min_cal_year(self.energy_demand)
                    self.max_year = self.max_cal_year(self.energy_demand)
                    self.energy_demand.project(map_from='raw_values', fill_timeseries=False)
                    self.energy_demand.map_from = 'values'
                    # change the energy demand to a per stock_time_unit energy demand
                    # ex. kBtu/year to kBtu/hour average service demand
                    time_step_energy = util.unit_convert(self.energy_demand.values, unit_from_den='year',unit_to_den=self.stock.time_unit)
                    # divide by capacity factor stock inputs to get a service demand stock
                    # ex. kBtu/hour/capacity factor equals kBtu/hour stock
                    self.stock.remap(map_from='raw_values', map_to='int_values', fill_timeseries=False)
                    _, x = util.difference_in_df_names(time_step_energy, self.stock.int_values)
                    if x:
                        raise ValueError(
                            'energy demand must have the same index levels as stock when stock is specified in capacity factor terms')
                    else:
                        self.stock.int_values = DfOper.divi([time_step_energy, self.stock.int_values],expandable=(False,True),collapsible=(True,False))*1E6
                    # project energy demand stock
                    self.stock.map_from = 'int_values'
                    self.stock.projected_input_type = 'total'
                    self.project_stock(map_from=self.stock.map_from,stock_dependent = self.energy_demand.is_stock_dependent)
                    self.stock.projected = False
                    self.stock_subset_prep()
                    # remove stock efficiency from energy demand to return service demand
                    self.efficiency_removal()
                    # change the service demand to a per stock_time_unit service demand
                    # ex. kBtu/year to kBtu/hour average service demand
                    time_step_service = util.unit_convert(self.service_demand.int_values, unit_from_den='year', unit_to_den=self.stock.time_unit)
                    # divide by capacity factor stock inputs to get a service demand stock
                    # ex. kBtu/hour/capacity factor equals kBtu/hour stock
                    _, x = util.difference_in_df_names(time_step_service, self.stock.int_values)
                    if x:
                        raise ValueError('service demand must have the same index levels as stock when stock is specified in capacity factor terms')
                    else:
                        self.stock.remap(map_from='raw_values', map_to='int_values', fill_timeseries=False)
                        self.stock.int_values = DfOper.divi([time_step_service, self.stock.int_values],expandable=(False,True),collapsible=(True,False))
                    # stock is by definition service demand dependent
                    self.stock.is_service_demand_dependent = 1
            elif self.stock.demand_stock_unit_type == 'service demand':
                if self.sub_type == 'stock and service':
                    # convert service demand units to stock units
                    self.service_demand.int_values = util.unit_convert(self.service_demand.raw_values, unit_from_num=self.service_demand.unit, unit_to_num=self.stock.unit)
                    self.service_demand.remap(map_from='int_values',map_to='int_values',fill_timeseries=False)
                    self.service_demand.unit = self.stock.unit
                    self.service_demand.current_data_type = self.service_demand.input_type
                    self.service_demand.projected = False
                    self.service_demand.map_from = 'int_values'                    
                    self.min_year = self.min_cal_year(self.service_demand)
                    self.max_year = self.max_cal_year(self.service_demand)
                    self.project_stock(stock_dependent=self.service_demand.is_stock_dependent)
                    self.stock_subset_prep()
                if self.sub_type == 'stock and energy':
                    # used when we don't have service demand, just energy demand
                    # determine the year range of energy demand inputs   
                    self.min_year = self.min_cal_year(self.energy_demand)
                    self.max_year = self.max_cal_year(self.energy_demand)
                    self.energy_demand.project(map_from='raw_values', fill_timeseries=False)
                    self.energy_demand.map_from = 'values'
                    self.project_stock(stock_dependent = self.energy_demand.is_stock_dependent)
                    self.stock_subset_prep()
                    # remove stock efficiency from energy demand to- return service demand
                    self.efficiency_removal()

            else:
                raise ValueError("incorrect demand stock unit type specification")
            # some previous steps have required some manipulation of initial raw values and the starting point
            # for projection will be a different 'map_from' variable
            self.stock.map_from = self.stock.map_from if hasattr(self.stock, 'map_from') else 'raw_values'
            # service demand has not been projected by default, so starting point, by default, is 'raw values
            self.service_demand.map_from = self.service_demand.map_from if hasattr(self.service_demand,
                                                                                   'map_from') else 'raw_values'
            if self.stock.is_service_demand_dependent == 0 and self.service_demand.is_stock_dependent == 0:
                self.project_stock(map_from=self.stock.map_from)
                self.project_service_demand(map_from=self.service_demand.map_from)
                self.sd_modifier_full()
            elif self.stock.is_service_demand_dependent == 1 and self.service_demand.is_stock_dependent == 0:
                self.project_service_demand(map_from=self.service_demand.map_from,service_dependent=True)
                self.project_stock(map_from=self.stock.map_from, service_dependent=True)
                self.sd_modifier_full()
            elif self.stock.is_service_demand_dependent == 0 and self.service_demand.is_stock_dependent == 1:
                self.project_stock(map_from=self.stock.map_from,stock_dependent=True)
                self.project_service_demand(map_from=self.service_demand.map_from, stock_dependent=True)
                self.sd_modifier_full()
            else:
                raise ValueError(
                    "stock and service demands both specified as dependent on each other in subsector %s" % self.id)
            self.service_demand.values = self.service_demand.values.groupby(
                level=self.stock.rollover_group_names + ['year']).sum()


    def determine_service_subset(self):
        if self.has_service_demand is not False:
            attr = 'service_demand'
        else:
            attr = 'energy_demand'
        demand = getattr(self, attr)
        index_names = demand.raw_values.index.names
        if 'final_energy' in index_names and 'demand_technology' in index_names:
            # TODO review
            self.service_subset = 'final_energy and demand_technology'
        elif 'final_energy' in index_names and 'demand_technology' not in index_names:
            self.service_subset = 'final_energy'
        elif 'final_energy' not in index_names and 'demand_technology' in index_names:
            self.service_subset = 'demand_technology'
        else:
            self.service_subset = None

    def stock_subset_prep(self):
        self.stock.tech_subset_normal = self.stack_and_reduce_years(self.stock.values_normal.groupby(level=util.ix_excl(self.stock.values_normal, 'vintage')).sum(), self.min_year, self.max_year)

        self.stock.tech_subset_normal.fillna(0)
        if self.service_subset == 'final_energy':
            if not hasattr(self.stock, 'values_efficiency_normal'):
                # subsectors with technologies having dual fuel capability do not generally calculate this. Only do so for this specific case.
                self.stock.values_efficiency = pd.concat([self.stock.values_efficiency_main, self.stock.values_efficiency_aux])
                self.stock.values_efficiency_normal = self.stock.values_efficiency.groupby(level=util.ix_excl(self.stock.values_efficiency, ['final_energy', 'demand_technology', 'vintage'])).transform(lambda x: x / x.sum()).fillna(0)
            self.stock.energy_subset_normal = self.stack_and_reduce_years(self.stock.values_efficiency_normal.groupby(
                level=util.ix_excl(self.stock.values_efficiency_normal, ['vintage', 'demand_technology'])).sum(), self.min_year, self.max_year)

    def efficiency_removal(self):
        if self.service_subset is None:
            # base the efficiency conversion on the total stock
            self.convert_energy_to_service('all')
            self.service_demand.map_from = 'int_values'
        elif self.service_subset == 'demand_technology':
            # base the efficiency conversion on individual demand_technology efficiencies
            # if service demand is in demand_technology terms.
            self.convert_energy_to_service('demand_technology')
            self.service_demand.map_from = 'int_values'
        elif self.service_subset == 'final_energy':
            # base the efficiency conversion on efficiencies of equipment with certain final energy types if service
            # if service demand is in final energy terms
            self.convert_energy_to_service('final_energy')
            self.service_demand.map_from = 'int_values'
        else:
            # if service demand is input in demand_technology and energy terms, reduce over
            # the final energy level because it may contradict input utility factors.
            # Then use demand_technology efficiencies to convert to service demand
            self.energy_demand.int_values = self.energy_demand.raw_values.sum(
                util.ix_excl(self.energy_demand.raw_values, ['final_energy']))
            self.convert_energy_to_service('demand_technology')
            self.service_demand.int_values = DfOper.mult([self.service_demand.int_values,
                                                          self.stock.tech_subset])
            self.service_demand.map_from = 'int_values'

    def sd_modifier_full(self):
        """
        calculates the service demand modifier (relation of the share of the service demand
        a demand_technology satisfies vs. the percentage of stock it represents) for subsectors if input service or energy demand
        has a demand_technology or final energy index. Once an initial calculation is made, demand_technology specific service demand modifiers
        can be applied. sd_modifiers are multiplied by the normalized stock and then must normalize to 1 in every year (i.e. the amount of 
        service demand that a stock satisfies in any year must equal the service demand projection)
        
        Tech - A : 50% of Stock
        Tech - B : 50% of Stock
        
        Tech - A: 25% of Service Demand
        Tech - B: 75% of Service Demand
        
        Tech - A: sd_modifier = .5
        Tech - B: sd_modifier = 1.5 
        
        service demand = .5 * .5 + 1.5 * .5 = 100%
        """
        self.stock_subset_prep()
        df_for_indexing = util.empty_df(index=self.stock.values_efficiency.index, columns=self.stock.values.columns.values, fill_value=1)
        sd_subset = getattr(self.service_demand, self.service_demand.map_from)
        if self.service_subset is None:
            # if there is no service subset, initial service demand modifiers equal 1"
            sd_modifier = df_for_indexing
        elif self.service_subset == 'demand_technology':
            # calculate share of service demand by demand_technology
            sd_subset_normal = sd_subset.groupby(level=util.ix_excl(sd_subset, ['demand_technology'])).transform(lambda x: x / x.sum())
            # calculate service demand modifier by dividing the share of service demand by the share of stock
            sd_modifier = DfOper.divi([sd_subset_normal, self.stock.tech_subset_normal])
            # expand the dataframe to put years as columns
            sd_modifier = self.vintage_year_array_expand(sd_modifier, df_for_indexing, sd_subset)
            sd_modifier.fillna(1, inplace=True)
            sd_modifier.sort_index()
            # replace any 0's with 1 since zeros indicates no stock in that subset, not a service demand modifier of 0
            sd_modifier[sd_modifier == 0] = 1
        elif self.service_subset == 'final_energy':
            # calculate share of service demand by final energy
            sd_subset = sd_subset.groupby(level=util.ix_excl(sd_subset, ['demand_technology'])).sum()
            sd_subset_normal = sd_subset.groupby(level=util.ix_excl(sd_subset, ['final_energy'])).transform(
                lambda x: x / x.sum())
            # calculate service demand modifier by dividing the share of service demand by the share of stock
            sd_modifier = DfOper.divi([sd_subset_normal, self.stock.energy_subset_normal])
            # expand the dataframe to put years as columns
            sd_modifier = self.vintage_year_array_expand(sd_modifier, df_for_indexing, sd_subset)
            sd_modifier.fillna(1, inplace=True)
            # replace any 0's with 1 since zeros indicates no stock in that subset, not a service demand modifier of 0
            sd_modifier[sd_modifier == 0] = 1

        else:
            # group over final energy since this is overspecified with demand_technology utility factors if indices of both
            # demand_technology and energy are present
            sd_subset = sd_subset.groupby(level=util.ix_excl(sd_subset, 'final_energy')).sum()
            # calculate share of service demand by demand_technology
            sd_subset_normal = sd_subset.groupby(level=util.ix_excl(sd_subset, 'demand_technology')).transform(
                lambda x: x / x.sum())
            # calculate service demand modifier by dividing the share of service demand by the share of stock
            sd_modifier = DfOper.divi([sd_subset_normal, self.stock.tech_subset_normal])
            # expand the dataframe to put years as columns
            sd_modifier = self.vintage_year_array_expand(sd_modifier, df_for_indexing, sd_subset)
            sd_modifier.fillna(1, inplace=True)
            # replace any 0's with 1 since zeros indicates no stock in that subset, not a service demand modifier of 0
            sd_modifier[sd_modifier == 0] = 1
#
#        if 'final_energy' in (sd_modifier.index.names):
#            # if final energy is in the original sd_modifier definition, we need to convert it to
#            # a dataframe that instead has service demand modifiers by demand_technology
#            blank_modifier_main = util.empty_df(index=self.stock.tech_subset_normal.index,
#                                                columns=self.stock.tech_subset_normal.columns.values, fill_value=1)
#            blank_modifier_aux = util.empty_df(index=self.stock.tech_subset_normal.index,
#                                               columns=self.stock.tech_subset_normal.columns.values, fill_value=0.)
#            # lookup service demand modifiers for each demand_technology in a dataframe of service demand modifiers by energy type
#            for tech in self.tech_ids:
#                main_energy_id = self.technologies[tech].efficiency_main.final_energy_id
#                aux_energy_id = getattr(self.technologies[tech].efficiency_aux, 'final_energy_id') if hasattr(
#                    self.technologies[tech].efficiency_aux, 'final_energy_id') else None
#                main_utility_factor = self.technologies[tech].efficiency_main.utility_factor
#                aux_utility_factor = 1 - main_utility_factor
#                main_energy_indexer = util.level_specific_indexer(sd_modifier, 'final_energy', main_energy_id)
#                aux_energy_indexer = util.level_specific_indexer(sd_modifier, 'final_energy', aux_energy_id)
#                tech_indexer = util.level_specific_indexer(blank_modifier_main, 'demand_technology', tech)
#                blank_modifier_main.loc[tech_indexer, :] = sd_modifier.loc[main_energy_indexer, :] * main_utility_factor
#                if aux_energy_id is not None:
#                    blank_modifier_aux.loc[tech_indexer, :] = sd_modifier.loc[aux_energy_indexer,
#                                                              :] * aux_utility_factor
#                blank_modifier = DfOper.add([blank_modifier_main, blank_modifier_aux])
#            sd_modifier = blank_modifier
#            sd_modifier = self.vintage_year_array_expand(sd_modifier, df_for_indexing, sd_subset)
#            sd_modifier.fillna(1, inplace=True)
#            sd_modifier.sort_index()
            # loop through technologies and add service demand modifiers by demand_technology-specific input (i.e. demand_technology has a
        # a service demand modifier class)
        for tech in self.tech_ids:
            if self.technologies[tech].service_demand_modifier.raw_values is not None:
                tech_modifier = getattr(getattr(self.technologies[tech], 'service_demand_modifier'), 'values')
                tech_modifier = util.expand_multi(tech_modifier, sd_modifier.index.levels, sd_modifier.index.names,
                                                  drop_index='demand_technology').fillna(method='bfill')
                indexer = util.level_specific_indexer(sd_modifier, 'demand_technology', tech)
                sd_modifier.loc[indexer, :] = tech_modifier.values
        # multiply stock by service demand modifiers
        stock_values = DfOper.mult([sd_modifier, self.stock.values_efficiency]).groupby(level=self.stock.rollover_group_names).sum()
#        # group stock and adjusted stock values
        adj_stock_values = self.stock.values_efficiency.groupby(level=self.stock.rollover_group_names).sum()
#        stock_values = self.stock.values.groupby(
#            level=util.ix_excl(self.stock.values, exclude=['vintage', 'demand_technology'])).sum()
#        # if this adds up to more or less than 1, we have to adjust the service demand modifers
        sd_mod_adjustment = DfOper.divi([stock_values, adj_stock_values])
        sd_mod_adjustment.replace([np.inf, -np.inf, np.nan], 1, inplace=True)
        self.sd_modifier = sd_modifier
        self.sd_mod_adjustment = sd_mod_adjustment
        self.service_demand.modifier = DfOper.divi([sd_modifier, sd_mod_adjustment])

    def calc_tech_survival_functions(self, steps_per_year=1, rollover_threshold=.99):
        self.stock.spy = steps_per_year
        for demand_technology in self.technologies.values():
            demand_technology.spy = steps_per_year
            demand_technology.set_survival_parameters()
            demand_technology.set_survival_vintaged()
            demand_technology.set_decay_vintaged()
            demand_technology.set_survival_initial_stock()
            demand_technology.set_decay_initial_stock()
        
        for demand_technology in self.technologies.values():
            if demand_technology.survival_vintaged[1] < rollover_threshold:
                logging.debug('       increasing stock rollover time steps per year to {} to account for short lifetimes of equipment'.format(str(steps_per_year*2)))
                self.calc_tech_survival_functions(steps_per_year=steps_per_year*2)

    def calc_measure_survival_functions(self, measures, stock, steps_per_year=1, rollover_threshold=.99):

        stock.spy = steps_per_year
        for measure in measures.values():
            measure.spy = steps_per_year
            measure.set_survival_parameters()
            measure.set_survival_vintaged()
            measure.set_decay_vintaged()
            measure.set_survival_initial_stock()
            measure.set_decay_initial_stock()
        for measure in measures.values():
            if measure.survival_vintaged[1] < rollover_threshold:
                self.calc_measure_survival_functions(measures, stock, steps_per_year=steps_per_year*2)

    def max_cal_year(self, demand):
        """finds the maximum year to calibrate service demand input in energy terms 
        back to service terms (i.e. without efficiency)
        """
        current_year = datetime.now().year - 1
        year_position = util.position_in_index(getattr(demand, 'raw_values'), 'year')
        year_position = getattr(demand, 'raw_values').index.names.index('year')
        max_service_year = getattr(demand, 'raw_values').index.levels[year_position].max()
        return min(current_year, max_service_year)

    def min_cal_year(self, demand):
        """finds the maximum year to calibrate service demand input in energy terms 
        back to service terms (i.e. without efficiency)
        """
        current_year = datetime.now().year - 1
        year_position = util.position_in_index(getattr(demand, 'raw_values'), 'year')
        year_position = getattr(demand, 'raw_values').index.names.index('year')
        min_service_year = getattr(demand, 'raw_values').index.levels[year_position].min()
        return min(current_year, min_service_year)

    @staticmethod
    def stack_and_reduce_years(df, min_year, max_year):
        """
        converts efficiency outputs with year across columns back to year multindex level. 
        Reduces years from full projection back to original specifications.             

        """
        df = df.copy()

        if min_year == max_year:
            years = [min_year]
        else:
            years = range(min_year, max_year+1)
        df = df.ix[:, years]
        df = pd.DataFrame(df.stack())
        util.replace_index_name(df, 'year')
        util.replace_column(df, 'value')
        return df

    def convert_energy_to_service(self, other_index):
        """converts service demand input in energy terms to service terms by dividing by stock efficiencies
        up to the minimum of the current year-1 or the last year of input service demand. 
        """
        self.rollover_efficiency_outputs(other_index)
        eff = copy.deepcopy(self.stock.efficiency[other_index]['all'])
        if other_index == 'demand_technology':
            exclude_index = ['final_energy']
        elif other_index == 'final_energy':
            exclude_index = ['demand_technology']
        else:
            exclude_index = ['final_energy', 'demand_technology']
        exclude_index.append('vintage')
        eff = eff.groupby(
            level=util.ix_excl(self.stock.efficiency[other_index]['all'], exclude=exclude_index)).sum()
        eff = self.stack_and_reduce_years(eff, self.min_year,
                                          self.max_year)
        self.energy_demand.values = util.unit_convert(self.energy_demand.values, unit_from_num=self.energy_demand.unit,
                                                      unit_to_num=cfg.calculation_energy_unit)
        # make a copy of energy demand for use as service demand        
        self.service_demand = self.energy_demand
        self.service_demand.raw_values = self.service_demand.values
        self.service_demand.int_values = DfOper.divi([self.service_demand.raw_values, eff])
        self.service_demand.int_values.replace([np.inf, -np.inf], 1, inplace=True)

    def output_efficiency_stock(self):
        """ reduces efficiency result for output and deletes efficiency dictionary"""
        for other_index in self.stock.efficiency.keys():
            for key in self.stock.efficiency[other_index].keys():
                if key == 'all':
                    self.loop_stock_efficiency(other_index)


    def loop_stock_efficiency(self, other_index):
        for other_index in self.stock.efficiency.keys():
            if other_index == 'all':
                exclude = ['vintage', 'demand_technology', 'final_energy']
            elif other_index == 'demand_technology':
                exclude = ['vintage']
            elif other_index == 'final_energy':
                exclude = ['demand_technology', 'vintage']
            else:
                raise ValueError('unknown key in stock efficiency dictionary')
            efficiency = self.stock.efficiency[other_index]['all']
            efficiency = efficiency.groupby(level=util.ix_excl(efficiency, exclude)).sum()
            efficiency = pd.DataFrame(efficiency.stack(), columns=['value'])
            util.replace_index_name(efficiency, 'year')
            attribute = 'efficiency_' + other_index
            setattr(self.stock_outputs, attribute, efficiency)

    def vintage_year_array_expand(self, df, df_for_indexing, sd_subset):
        """creates a dataframe with years as columns instead of an index"""
        level_values = sd_subset.index.get_level_values(level='year')
        max_column = max(level_values)
        df = df.unstack(level='year')
        df.columns = df.columns.droplevel()
        df = df.loc[:, max_column].to_frame()
        for column in self.years:
            df[column] = df[max_column]
        df = util.DfOper.mult([df,df_for_indexing])
        df = df.sort(axis=1)
        if hasattr(df.columns, 'levels'):
            df.columns = df.columns.droplevel()
        return df

    def project_stock(self, map_from='raw_values', service_dependent=False,stock_dependent=False, override=False):
        """
        project stock moving forward includes projecting total and demand_technology stock as well as initiating stock rollover
        If stock has already been projected, it gets reprojected if override is specified.
        """
        self.stock.vintages = self.vintages
        self.stock.years = self.years
        if not self.stock.projected or override:
            self.project_total_stock(map_from, service_dependent,stock_dependent)
            self.calculate_specified_stocks()
            self.project_demand_technology_stock(map_from, service_dependent)
            self.stock.set_rollover_groups()
            self.stock.calc_annual_stock_changes()
            self.calc_tech_survival_functions()
            self.calculate_sales_shares()
            self.reconcile_sales_shares()
            self.stock_rollover()
            self.stock.projected = True

    def project_total_stock(self, map_from, service_dependent=False, stock_dependent = False):
        if map_from == 'values':
            current_geography = cfg.primary_geography
            current_data_type = 'total'
            self.stock.values = self.stock.values.groupby(level=util.ix_excl(self.stock.values, 'vintage')).sum()
            self.stock.values = self.stack_and_reduce_years(self.stock.values, min(self.years), max(self.years))
            projected  = True
        elif map_from == 'int_values':
            current_geography = cfg.primary_geography
            current_data_type = self.stock.current_data_type if hasattr(self.stock, 'current_data_type')  else 'total'
            projected = False
        else:
            current_geography = self.stock.geography
            current_data_type = self.stock.input_type
            projected = False
        self.stock.project(map_from=map_from, map_to='total', current_geography=current_geography,
                           additional_drivers=self.additional_drivers(stock_or_service='stock',service_dependent=service_dependent),
                           current_data_type=current_data_type, projected=projected)
        self.stock.total = util.remove_df_levels(self.stock.total, ['demand_technology', 'final_energy'])
        self.stock.total = self.stock.total.swaplevel('year',-1)
        if stock_dependent:
            self.stock.project(map_from=map_from, map_to='total_unfiltered', current_geography=current_geography,
                           additional_drivers=self.additional_drivers(stock_or_service='stock',service_dependent=service_dependent),
                           current_data_type=current_data_type, projected=projected,filter_geo=False)
            self.stock.total = util.remove_df_levels(self.stock.total, ['demand_technology', 'final_energy'])
            self.stock.total = self.stock.total.swaplevel('year',-1)

    def project_demand_technology_stock(self, map_from, service_dependent):
        if map_from == 'values' or map_from == 'int_values':
            current_geography = cfg.primary_geography
            current_data_type = 'total'
            projected = True
        else:
            current_geography = self.stock.geography
            current_data_type = self.stock.input_type
            projected = False
            
        if 'demand_technology' in getattr(self.stock, map_from).index.names:
            self.stock.project(map_from=map_from, map_to='technology', current_geography=current_geography,
                               additional_drivers=self.service_demand.values if service_dependent else None, interpolation_method=None,extrapolation_method=None,
                               fill_timeseries=True,fill_value=np.nan,current_data_type=current_data_type,projected=projected)
            self.stock.technology = self.stock.technology.swaplevel('year',-1)
            self.stock.technology = util.reindex_df_level_with_new_elements(self.stock.technology,'demand_technology',self.tech_ids,fill_value=np.nan)
            self.stock.technology.sort(inplace=True)
        else:
            full_names = self.stock.total.index.names + ['demand_technology']
            full_levels = self.stock.total.index.levels + [self.tech_ids]
            index = pd.MultiIndex.from_product(full_levels, names=full_names)
            self.stock.technology = self.stock.total.reindex(index)
        self.remap_linked_stock()
        if self.stock.has_linked_demand_technology:
            # if a stock a demand_technology stock that is linked from other subsectors, we goup by the levels found in the stotal stock of the subsector
            full_names = [x for x in self.stock.total.index.names]
            full_names.insert(-1,'demand_technology')
            linked_demand_technology = self.stock.linked_demand_technology.groupby(
                level=[x for x in self.stock.linked_demand_technology.index.names if x in full_names]).sum()
            linked_demand_technology = linked_demand_technology.reorder_levels(full_names)
            linked_demand_technology.sort(inplace=True)
            self.stock.technology = self.stock.technology.reorder_levels(full_names)
            self.stock.technology.sort(inplace=True)
            # expand the levels of the subsector's endogenous demand_technology stock so that it includes all years. That's because the linked stock specification will be for all years
            linked_demand_technology = linked_demand_technology[linked_demand_technology.index.get_level_values('year')>=min(self.years)]
            linked_demand_technology = util.DfOper.none([linked_demand_technology,self.stock.technology],fill_value=np.nan)
            # if a demand_technology isn't demand_technology by a lnk to another subsector, replace it with subsector stock specification
            linked_demand_technology = linked_demand_technology.mask(np.isnan(linked_demand_technology), self.stock.technology)
            # check whether this combination exceeds the total stock
            linked_demand_technology_total_check = util.remove_df_levels(linked_demand_technology, 'demand_technology')
            total_check = util.DfOper.subt((linked_demand_technology_total_check, self.stock.total))
            total_check[total_check < 0] = 0
            # if the total check fails, normalize all subsector inputs. We normalize the linked stocks as well.
            if total_check.sum().any() > 0:
                demand_technology_normal = linked_demand_technology.groupby(
                    level=util.ix_excl(linked_demand_technology, 'demand_technology')).transform(lambda x: x / x.sum())
                stock_reduction = DfOper.mult((demand_technology_normal, total_check))
                linked_demand_technology = DfOper.subt((linked_demand_technology, stock_reduction))
            self.stock.technology = linked_demand_technology
        for demand_technology in self.technologies.values():
            if len(demand_technology.specified_stocks):
               for specified_stock in demand_technology.specified_stocks.values():
                   specified_stock.remap(map_from='values', current_geography = cfg.primary_geography, drivers=self.stock.total)
                   self.stock.technology.sort(inplace=True)
                   indexer = util.level_specific_indexer(self.stock.technology,'demand_technology',demand_technology.id)
                   df = util.remove_df_levels(self.stock.technology.loc[indexer,:],'demand_technology')
                   df = df.reorder_levels([x for x in self.stock.technology.index.names if x not in ['demand_technology']])
                   df.sort(inplace=True)
                   specified_stock.values = specified_stock.values.reorder_levels([x for x in self.stock.technology.index.names if x not in ['demand_technology']])
                   df.sort(inplace=True)
                   specified_stock.values.sort(inplace=True)
                   specified_stock.values = specified_stock.values.fillna(df)
                   self.stock.technology.loc[indexer,:] = specified_stock.values.values
        self.max_total()
    
    def max_total(self):
        tech_sum = util.remove_df_levels(self.stock.technology,'demand_technology')
#        self.stock.total = self.stock.total.fillna(tech_sum)
        self.stock.total.sort(inplace=True)
        self.stock.total[self.stock.total<tech_sum] = tech_sum    

                  

    def project_ee_measure_stock(self):
        """ 
        adds a MeasureStock class to the subsector and specifies stocks based on energy efficiency measure savings i.e. an energy efficiency
        measure that saves 1 EJ would represent an energy efficiency stock of 1 EJ
        """
        measure_dfs = [self.reformat_measure_df(map_df=self.energy_forecast, measure=measure, measure_class=None, 
                       measure_att='savings', id=measure.id) for measure in self.energy_efficiency_measures.values()]
        if len(measure_dfs):
            self.ee_stock = AggregateStock()
            measure_df = pd.concat(measure_dfs)
            self.ee_stock.specified = measure_df.unstack('measure')
            self.ee_stock.total = measure_df.groupby(level=util.ix_excl(measure_df, 'measure')).sum()
            self.ee_stock.set_rollover_groups()
            self.ee_stock.calc_annual_stock_changes()
            self.measure_stock_rollover('energy_efficiency_measures', 'ee_stock')

    def project_fs_measure_stock(self):
        """ 
        adds a MeasureStock class to the subsector and specifies stocks based on fuel switching  measure impact i.e. a fuel switching measure
        that switches 1 EJ from one final energy to another would represent a fuel switching stock of 1 EJ
        """
        measure_dfs = [self.reformat_measure_df(map_df=self.energy_forecast, measure=measure, measure_class='impact',
                                                measure_att='savings', id=measure.id) for measure in
                       self.fuel_switching_measures.values()]
        if len(measure_dfs):
            self.fs_stock = AggregateStock()
            measure_df = pd.concat(measure_dfs)
            self.fs_stock.specified = measure_df.unstack('measure')
            self.fs_stock.total = measure_df.groupby(level=util.ix_excl(measure_df, 'measure')).sum()
            self.fs_stock.set_rollover_groups()
            self.fs_stock.calc_annual_stock_changes()
            self.measure_stock_rollover('fuel_switching_measures', 'fs_stock')

    def project_sd_measure_stock(self):
        """ 
        adds a MeasureStock class to the subsector and specifies stocks based on service demand impact
        i.e. a service demand measure that reduces 1M millions of LDV travel would represent a 
        service demand measure stock of 1M VMTs
        """

        measure_dfs = [self.reformat_measure_df(map_df=self.service_demand.values, measure=measure, measure_class=None,
                                                measure_att='savings', id=measure.id) for measure in
                       self.service_demand_measures.values()]
        if len(measure_dfs):
            self.sd_stock = AggregateStock()
            measure_df = pd.concat(measure_dfs)
            self.sd_stock.specified = measure_df.unstack('measure')
            self.sd_stock.total = measure_df.groupby(level=util.ix_excl(measure_df, 'measure')).sum()
            self.sd_stock.set_rollover_groups()
            self.sd_stock.calc_annual_stock_changes()
            self.measure_stock_rollover('service_demand_measures', 'sd_stock')

    def measure_stock_rollover(self, measures_name, stock_name):
        """ Stock rollover function for measures"""
        measures = getattr(self, measures_name)
        stock = getattr(self, stock_name)
        self.calc_measure_survival_functions(measures, stock)
        self.create_measure_survival_functions(measures, stock)
        self.create_measure_rollover_markov_matrices(measures, stock)
        levels = stock.rollover_group_names
        if len(levels) == 1:
            rollover_groups = util.remove_df_levels(stock.total,'year').groupby(level=levels[0]).groups
        else:
            rollover_groups = util.remove_df_levels(stock.total,'year').groupby(level=levels).groups
        full_levels = stock.rollover_group_levels + [measures.keys()] + [
            [self.vintages[0] - 1] + self.vintages]
        full_names = stock.rollover_group_names + ['measure', 'vintage']
        columns = self.years
        index = pd.MultiIndex.from_product(full_levels, names=full_names)
        stock.values = util.empty_df(index=index, columns=pd.Index(columns, dtype='object'))
        full_levels = stock.rollover_group_levels + [measures.keys()] + [self.vintages]
        index = pd.MultiIndex.from_product(full_levels, names=full_names)
        stock.retirements = util.empty_df(index=index, columns=['value'])
        stock.sales = util.empty_df(index=index, columns=['value'])
        if not any([x.cost.data for x in measures.values()]):
            #no need to do stock rollover if there are no costs
            return
        for elements in rollover_groups.keys():
            specified_stock = util.df_slice(stock.specified, elements, levels)
            if np.all(specified_stock.sum().values==0):
                continue
            annual_stock_change = util.df_slice(stock.annual_stock_changes, elements, levels)
            self.rollover = Rollover(vintaged_markov_matrix=stock.vintaged_markov_matrix,
                                     initial_markov_matrix=stock.initial_markov_matrix,
                                     num_years=len(self.years), num_vintages=len(self.vintages),
                                     num_techs=len(measures.keys()), initial_stock=None,
                                     sales_share=None, stock_changes=annual_stock_change.values,
                                     specified_stock=specified_stock.values, specified_retirements=None,
                                     exceedance_tolerance=0.1)
            if abs(annual_stock_change.sum().values)!=0:
                self.rollover.run()
                stock_total, stock_new, stock_replacement, retirements, retirements_natural, retirements_early, sales_record, sales_new, sales_replacement = self.rollover.return_formatted_outputs()
                stock.values.loc[elements], stock.retirements.loc[elements, 'value'] = stock_total, retirements
                stock.sales.loc[elements, 'value'] = sales_record


    def calculate_costs_measures(self):
        if hasattr(self, 'ee_stock'):
            self.ee_stock.levelized_costs = defaultdict(dict)
            self.ee_stock.levelized_costs['unspecified'] = self.rollover_measure_output(
                measures='energy_efficiency_measures', measure_class='cost', measure_att='values_level',
                stock_class='ee_stock',
                stock_att='values')
            self.ee_stock.annual_costs = defaultdict(dict)
            self.ee_stock.annual_costs['unspecified']= self.rollover_measure_output(
                measures='energy_efficiency_measures', measure_class='cost', measure_att='values',
                stock_class='ee_stock',
                stock_att='sales')
        if hasattr(self, 'fs_stock'):
            self.fs_stock.levelized_costs = defaultdict(dict)
            self.fs_stock.levelized_costs['unspecified']= self.rollover_measure_output(
                measures='fuel_switching_measures', measure_class='cost', measure_att='values_level',
                stock_class='fs_stock',
                stock_att='values')

            self.fs_stock.annual_costs = defaultdict(dict)
            self.fs_stock.annual_costs['unspecified'] = self.rollover_measure_output(
                measures='fuel_switching_measures', measure_class='cost', measure_att='values', stock_class='fs_stock',
                stock_att='sales')

        if hasattr(self, 'sd_stock'):
            self.sd_stock.levelized_costs = defaultdict(dict)
            self.sd_stock.levelized_costs['unspecified']= self.rollover_measure_output(
                measures='service_demand_measures', measure_class='cost', measure_att='values_level',
                stock_class='sd_stock',
                stock_att='values')

            self.sd_stock.annual_costs = defaultdict(dict)
            self.sd_stock.annual_costs['unspecified']= self.rollover_measure_output(
                measures='service_demand_measures', measure_class='cost', measure_att='values', stock_class='sd_stock',
                stock_att='sales')

    def rollover_measure_output(self, measures, measure_class=None, measure_att='values', stock_class=None,
                                stock_att='values',
                                stack_label=None, other_aggregate_levels=None):
        """ Produces rollover outputs for a subsector measure stock
        """

        stock_df = getattr(getattr(self, stock_class), stock_att)
        groupby_level = util.ix_excl(stock_df, ['vintage'])
        # determines index position for demand_technology and final energy element
        c = util.empty_df(stock_df.index, stock_df.columns.values, fill_value=0.)
        # puts technologies on the appropriate basi         
        measure_dfs = [self.reformat_measure_df(stock_df, measure, measure_class, measure_att, measure.id) for measure
                       in getattr(self, measures).values() if
                       hasattr(measure, measure_class) and getattr(getattr(measure, measure_class),
                                                                   'raw_values') is not None]
        if len(measure_dfs):
            measure_df = pd.concat(measure_dfs)
            c = DfOper.mult([measure_df, stock_df])
        if stack_label is not None:
            c = c.stack()
            util.replace_index_name(c, stack_label)
            util.replace_column(c, 'value')
        if other_aggregate_levels is not None:
            groupby_level = util.ix_excl(c, other_aggregate_levels)
            c = c.groupby(level=groupby_level).sum()
        # TODO fix
        if 'final_energy' in c.index.names:
            c = util.remove_df_elements(c, 9999, 'final_energy')
        return c

    def reformat_measure_df(self, map_df, measure, measure_class, measure_att, id):
        """
        reformat measure dataframes for use in stock-level dataframe operations
        """
        if measure_class is None:
            measure_df = getattr(measure, measure_att)
        else:
            measure_class = getattr(measure, measure_class)
            measure_df = getattr(measure_class, measure_att) if hasattr(measure_class, measure_att) else None
        if measure_df is None:
            return
        else:
            measure_df['measure'] = id
            measure_df.set_index('measure', append=True, inplace=True)
            level_order = [cfg.primary_geography] + util.ix_excl(measure_df, [
                cfg.primary_geography, 'vintage']) + ['vintage']
            level_order = [x for x in level_order if x in measure_df.index.names]
            measure_df = measure_df.reorder_levels(level_order)
            return measure_df

    def create_measure_survival_functions(self, measures, stock):
        functions = defaultdict(list)
        try:
            for fun in ['survival_vintaged', 'survival_initial_stock', 'decay_vintaged', 'decay_initial_stock']:
                for measure in measures.values():
                    functions[fun].append(getattr(measure, fun))
                setattr(stock, fun, pd.DataFrame(np.array(functions[fun]).T, columns=measures.keys()))
        except:
            pdb.set_trace()

    def create_tech_survival_functions(self):
        functions = defaultdict(list)
        for fun in ['survival_vintaged', 'survival_initial_stock', 'decay_vintaged', 'decay_initial_stock']:
            for tech_id in self.tech_ids:
                demand_technology = self.technologies[tech_id]
                functions[fun].append(getattr(demand_technology, fun))
            setattr(self.stock, fun, pd.DataFrame(np.array(functions[fun]).T, columns=self.tech_ids))

    def create_rollover_markov_matrices(self):
        vintaged_markov = util.create_markov_vector(self.stock.decay_vintaged.values, self.stock.survival_vintaged.values)
        self.stock.vintaged_markov_matrix = util.create_markov_matrix(vintaged_markov, len(self.tech_ids), len(self.years), self.stock.spy)

        initial_markov = util.create_markov_vector(self.stock.decay_initial_stock.values, self.stock.survival_initial_stock.values)
        self.stock.initial_markov_matrix = util.create_markov_matrix(initial_markov, len(self.tech_ids), len(self.years), self.stock.spy)
    def create_measure_rollover_markov_matrices(self, measures, stock):
        vintaged_markov = util.create_markov_vector(stock.decay_vintaged.values, stock.survival_vintaged.values)
        stock.vintaged_markov_matrix = util.create_markov_matrix(vintaged_markov, len(measures.keys()), len(self.years),stock.spy)

        initial_markov = util.create_markov_vector(stock.decay_initial_stock.values, stock.survival_initial_stock.values)
        stock.initial_markov_matrix = util.create_markov_matrix(initial_markov, len(measures.keys()), len(self.years),stock.spy)

    def format_demand_technology_stock(self):
        """ formats demand_technology stock and linked demand_technology stocks from other subsectors
        overwrites demand_technology stocks with linked demand_technology stocks"""
        needed_names = self.stock.rollover_group_names + ['demand_technology'] + ['year']
        groupby_levels = [x for x in self.stock.technology.index.names if x  in needed_names]
        if len(groupby_levels) > 0:
            self.stock.technology = self.stock.technology.groupby(level=groupby_levels).sum()
        self.stock.technology = util.reindex_df_level_with_new_elements(self.stock.technology,'demand_technology',self.tech_ids)
        self.stock.technology = self.stock.technology.unstack(level='demand_technology')


    def remap_linked_stock(self):
        """remap stocks specified in linked subsectors """
        df_concat = self.linked_stock.values()
        if len(df_concat) > 0:
            self.stock.linked_demand_technology = pd.concat(df_concat, axis=0)
            if np.all(np.isnan(self.stock.technology.values)):
                subsector_stock = util.remove_df_levels(self.stock.total, 'demand_technology')
            else:
                subsector_stock = util.remove_df_levels(self.stock.technology,'year')
            self.stock.remap(map_from='linked_demand_technology', map_to='linked_demand_technology', drivers=subsector_stock,
                             current_geography=cfg.primary_geography, current_data_type='total',
                             time_index=self.years)   
            self.stock.linked_demand_technology[self.stock.linked_demand_technology==0]=np.nan
            self.stock.has_linked_demand_technology = True
        else:
            self.stock.has_linked_demand_technology = False

    def additional_drivers(self, stock_or_service = None,stock_dependent=False, service_dependent=False):
        """ create a list of additional drivers from linked subsectors """
        additional_drivers = []
        if stock_or_service == 'service':
            if len(self.linked_service_demand_drivers):
                linked_service_demand_drivers = []
                for driver in self.linked_service_demand_drivers.values():
                    linked_service_demand_drivers.append(driver)
                linked_driver = 1 - DfOper.add(linked_service_demand_drivers)
                additional_drivers.append(linked_driver)
        if stock_dependent:
            if len(additional_drivers):
                additional_drivers.append(self.stock.total_unfiltered)
            else:
                additional_drivers = self.stock.total_unfiltered
        if service_dependent:
            if len(additional_drivers):
                additional_drivers.append(self.service_demand.values_unfiltered)
            else:
                additional_drivers = self.service_demand.values_unfiltered
        if len(additional_drivers) == 0:
            additional_drivers = None
        return additional_drivers

    def project_service_demand(self, map_from='raw_values', stock_dependent=False, service_dependent=False):
        self.service_demand.vintages = self.vintages
        self.service_demand.years = self.years
        if map_from == 'raw_values':
            current_geography = self.service_demand.geography
            current_data_type = self.service_demand.input_type
            projected = False
        elif map_from == 'int_values':
            current_geography = cfg.primary_geography
            current_data_type = self.service_demand.current_data_type if hasattr(self.service_demand, 'current_data_type')  else 'total'
            projected =  False
        else:
            current_geography = cfg.primary_geography
            current_data_type =  'total'
            projected =  True
        self.service_demand.project(map_from=map_from, map_to='values', current_geography=current_geography,
                                    additional_drivers=self.additional_drivers(stock_or_service='service',stock_dependent=stock_dependent),current_data_type=current_data_type,projected=projected)
        if service_dependent:
            self.service_demand.project(map_from=map_from, map_to='values_unfiltered', current_geography=current_geography,
                                    additional_drivers=self.additional_drivers(stock_or_service='stock',stock_dependent=stock_dependent),current_data_type=current_data_type,projected=projected,filter_geo=False)


        self.service_demand_forecast = self.service_demand.values
        # calculates the service demand change from service demand measures
        self.service_demand_savings_calc()

    def project_energy_demand(self, map_from='raw_values', stock_dependent=False, service_dependent=False):
        self.energy_demand.vintages = self.vintages
        self.energy_demand.years = self.years
        if map_from == 'raw_values':
            current_geography = self.energy_demand.geography
            current_data_type = self.energy_demand.input_type
            projected = False
        elif map_from == 'int_values':
            current_geography = cfg.primary_geography
            current_data_type = self.energy_demand.current_data_type if hasattr(self.energy_demand, 'current_data_type')  else 'total'
            projected =  False
        else:
            current_geography = cfg.primary_geography
            current_data_type =  'total'
            projected =  True

        self.energy_demand.project(map_from=map_from, map_to='values', current_geography=current_geography,
                                   additional_drivers=self.additional_drivers(stock_or_service='service',stock_dependent=stock_dependent,
                                                                                            service_dependent=service_dependent),current_data_type=current_data_type, projected=projected)

    def calculate_sales_shares(self):
        for tech in self.tech_ids:
            demand_technology = self.technologies[tech]
            demand_technology.calculate_sales_shares('reference_sales_shares')
            demand_technology.calculate_sales_shares('sales_shares')

    def calculate_specified_stocks(self):
        for demand_technology in self.technologies.values():
            demand_technology.calculate_specified_stocks()

    def reconcile_sales_shares(self):
        needed_sales_share_levels = self.stock.rollover_group_levels + [self.years]
        needed_sales_share_names = self.stock.rollover_group_names + ['vintage']
        for demand_technology in self.technologies.values():
            demand_technology.reconcile_sales_shares('sales_shares', needed_sales_share_levels, needed_sales_share_names)
            demand_technology.reconcile_sales_shares('reference_sales_shares', needed_sales_share_levels,
                                              needed_sales_share_names)

    def calculate_total_sales_share(self, elements, levels):
        ss_measure = self.helper_calc_sales_share(elements, levels, reference=False)
        space_for_reference = 1 - np.sum(ss_measure, axis=1)
        ss_reference = self.helper_calc_sales_share(elements, levels, reference=True,
                                                    space_for_reference=space_for_reference)
        
        if np.sum(ss_reference)==0:
            ss_reference = SalesShare.scale_reference_array_to_gap( np.tile(np.eye(len(self.tech_ids)), (len(self.years), 1, 1)), space_for_reference)        
            #sales shares are always 1 with only one demand_technology so the default can be used as a reference
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
           #sales shares are always 1 with only one demand_technology so the default can be used as a reference
        return SalesShare.normalize_array(ss_reference + ss_measure, retiring_must_have_replacement=False)


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
                    # demand_technology sales share dataframe may not have all elements of stock dataframe
                    if any([element not in sales_share.values.index.levels[
                        util.position_in_index(sales_share.values, level)] for element, level in
                            zip(elements, levels)]):
                        continue
                    ss_array[:, repl_index, reti_index] += util.df_slice(sales_share.values, elements, levels).values
            ss_array = SalesShare.scale_reference_array_to_gap(ss_array, space_for_reference)                          
        else:
            for tech_id in self.tech_ids:
                for sales_share in self.technologies[tech_id].sales_shares.values():
                    repl_index = tech_lookup[sales_share.demand_technology_id]
                    if sales_share.replaced_demand_tech_id is not None and not tech_lookup.has_key(sales_share.replaced_demand_tech_id):
                            #if you're replacing a demand tech that doesn't have a sales share or stock in the model, this is zero and so we continue the loop
                            continue
                    reti_index = tech_lookup[
                        sales_share.replaced_demand_tech_id] if sales_share.replaced_demand_tech_id is not None and tech_lookup.has_key(
                        sales_share.replaced_demand_tech_id) else slice(
                        None)
                    # TODO address the discrepancy when a demand tech is specified
                    try:
                        ss_array[:, repl_index, reti_index] += util.df_slice(sales_share.values, elements, levels).values
                    except:
                        ss_array[:, repl_index, reti_index] += util.df_slice(sales_share.values, elements, levels).values.flatten()
                        
            ss_array = SalesShare.cap_array_at_1(ss_array)
        return ss_array

    def tech_to_energy(self, df, tech_class):
        """
            reformats a dataframe with a demand_technology index to one with a final energy index
            based on a lookup of the final_energy_id by demand_technology class (i.e. aux_efficiency will provide the aux energy type id)
        """
        df = df.copy()
        rename_dict = {}
        for tech in self.technologies.keys():
            if hasattr(getattr(self.technologies[tech], tech_class), 'final_energy_id'):
                rename_dict[tech] = getattr(getattr(self.technologies[tech], tech_class), 'final_energy_id')
            else:
                # if no energy type exists for the demand_technology class, put in 9999 as placeholder
                rename_dict[tech] = 9999
        index = df.index
        tech_position = index.names.index('demand_technology')
        index.set_levels(
            [[rename_dict.get(item, item) for item in names] if i == tech_position else names for i, names in
             enumerate(index.levels)], inplace=True)
        util.replace_index_name(df, 'final_energy', 'demand_technology')
        df = df.reset_index().groupby(df.index.names).sum()
        df = util.remove_df_elements(df, 9999, 'final_energy')
        return df


    def tech_sd_modifier(self):
            sd_modifier = util.empty_df(index=self.stock.values.index, columns=self.stock.values.columns.values, fill_value=1)
            for tech in self.tech_ids:
                if self.technologies[tech].service_demand_modifier.raw_values is not None:
                    tech_modifier = getattr(getattr(self.technologies[tech], 'service_demand_modifier'), 'values')
                    tech_modifier = util.expand_multi(tech_modifier, sd_modifier.index.levels, sd_modifier.index.names,
                                                      drop_index='demand_technology').fillna(method='bfill')
                    indexer = util.level_specific_indexer(sd_modifier, 'demand_technology', tech)
                    sd_modifier.loc[indexer, :] = tech_modifier.values
            self.tech_sd_modifier = sd_modifier


    def calculate_service_modified_sales(self,elements,levels,sales_share):
        sd_modifier = copy.deepcopy(self.tech_sd_modifier)
        sd_modifier = sd_modifier[sd_modifier>0]
        service_modified_sales = util.df_slice(sd_modifier,elements,levels,drop_level=False)
        service_modified_sales=service_modified_sales.groupby(level=levels+['demand_technology','vintage']).mean().mean(axis=1).to_frame()
        service_modified_sales = service_modified_sales.swaplevel('demand_technology','vintage')
        service_modified_sales.sort(inplace=True)
        service_modified_sales = service_modified_sales.unstack('demand_technology').values
        service_modified_sales = np.array([np.outer(i, 1./i).T for i in service_modified_sales])[1:]
        sales_share *= service_modified_sales
        return sales_share
        
    def stock_rollover(self):
        """ Stock rollover function."""
        self.format_demand_technology_stock()
        self.create_tech_survival_functions()
        self.create_rollover_markov_matrices()
        rollover_groups = self.stock.total.groupby(level=self.stock.rollover_group_names).groups
        full_levels = self.stock.rollover_group_levels + [self.technologies.keys()] + [
            [self.vintages[0] - 1] + self.vintages]
        full_names = self.stock.rollover_group_names + ['demand_technology', 'vintage']
        columns = self.years
        index = pd.MultiIndex.from_product(full_levels, names=full_names)
        self.stock.values = util.empty_df(index=index, columns=pd.Index(columns, dtype='object'))
        self.stock.values_new = copy.deepcopy(self.stock.values)
        self.stock.values_replacement = copy.deepcopy(self.stock.values)
        full_levels = self.stock.rollover_group_levels + [self.technologies.keys()] + [self.vintages]
        index = pd.MultiIndex.from_product(full_levels, names=full_names)
        self.stock.retirements = util.empty_df(index=index, columns=['value'])
        self.stock.retirements_early = copy.deepcopy(self.stock.retirements)
        self.stock.retirements_natural = copy.deepcopy(self.stock.retirements)
        self.stock.sales = util.empty_df(index=index, columns=['value'])
        self.stock.sales_new = copy.deepcopy(self.stock.sales)
        self.stock.sales_replacement = copy.deepcopy(self.stock.sales)
        if self.stock.is_service_demand_dependent and self.stock.demand_stock_unit_type == 'equipment':        
            self.tech_sd_modifier()        
        for elements in rollover_groups.keys():
            elements = util.ensure_tuple(elements)
            #returns sales share and a flag as to whether the sales share can be used to parameterize initial stock. 
            sales_share, initial_sales_share = self.calculate_total_sales_share(elements, self.stock.rollover_group_names)  # group is not necessarily the same for this other dataframe
            if np.any(np.isnan(sales_share)):
                raise ValueError('Sales share has NaN values in subsector ' + str(self.id))

            initial_stock, rerun_sales_shares = self.calculate_initial_stock(elements,sales_share,initial_sales_share)
            
            if rerun_sales_shares:
               sales_share =  self.calculate_total_sales_share_after_initial(elements, self.stock.rollover_group_names)
               
            if self.stock.is_service_demand_dependent and self.stock.demand_stock_unit_type == 'equipment':
                sales_share = self.calculate_service_modified_sales(elements,self.stock.rollover_group_names,sales_share)

            demand_technology_stock = self.stock.return_stock_slice(elements, self.stock.rollover_group_names)

            annual_stock_change = util.df_slice(self.stock.annual_stock_changes, elements, self.stock.rollover_group_names)

            self.rollover = Rollover(vintaged_markov_matrix=self.stock.vintaged_markov_matrix,
                                     initial_markov_matrix=self.stock.initial_markov_matrix,
                                     num_years=len(self.years), num_vintages=len(self.vintages),
                                     num_techs=len(self.tech_ids), initial_stock=initial_stock,
                                     sales_share=sales_share, stock_changes=annual_stock_change.values,
                                     specified_stock=demand_technology_stock.values, specified_retirements=None,
                                     steps_per_year=self.stock.spy)                        
            self.rollover.run()
            stock, stock_new, stock_replacement, retirements, retirements_natural, retirements_early, sales_record, sales_new, sales_replacement = self.rollover.return_formatted_outputs()
            self.stock.values.loc[elements], self.stock.values_new.loc[elements], self.stock.values_replacement.loc[
                elements] = stock, stock_new, stock_replacement
            self.stock.retirements.loc[elements, 'value'], self.stock.retirements_natural.loc[elements, 'value'], \
            self.stock.retirements_early.loc[elements, 'value'] = retirements, retirements_natural, retirements_early
            self.stock.sales.loc[elements, 'value'], self.stock.sales_new.loc[elements, 'value'], \
            self.stock.sales_replacement.loc[elements, 'value'] = sales_record, sales_new, sales_replacement
        self.stock_normalize(self.stock.rollover_group_names)
        self.financial_stock()
        if self.sub_type != 'link':
            self.fuel_switch_stock_calc()


    def calculate_initial_stock(self,elements, sales_share, initial_sales_share):    
        initial_total = util.df_slice(self.stock.total, elements, self.stock.rollover_group_names).values[0]
        demand_technology_years = self.stock.technology.sum(axis=1)[self.stock.technology.sum(axis=1)>0].index.get_level_values('year')
        if len(demand_technology_years):
             min_demand_technology_year = min(demand_technology_years)
        else:
             min_demand_technology_year = None
        #Best way is if we have all demand_technology stocks specified
        if (np.nansum(self.stock.technology.loc[elements,:].values[0])/self.stock.total.loc[elements,:].values[0])>.99:
            initial_stock = self.stock.technology.loc[elements,:].values[0]
            rerun_sales_shares = False
        #Second best way is if we have all demand_technology stocks specified in some year before the current year
        elif min_demand_technology_year is not None and min_demand_technology_year<=int(cfg.cfgfile.get('case','current_year')) and np.nansum(self.stock.technology.loc[elements+(min_demand_technology_year,),:].values)==self.stock.total.loc[elements+(min_demand_technology_year,),:].values:
            initial_stock = self.stock.technology.loc[elements+(min_demand_technology_year,),:].values/np.nansum(self.stock.technology.loc[elements+(min_demand_technology_year,),:].values) * initial_total
            rerun_sales_shares = False
        #Third best way is if we have an initial sales share
        elif initial_sales_share:                
            initial_stock = self.stock.calc_initial_shares(initial_total=initial_total, 
                                                           transition_matrix=sales_share[0], num_years=len(self.years))
            rerun_sales_shares = True
            ss_measure = self.helper_calc_sales_share(elements,self.stock.rollover_group_names,reference=False)
            if np.sum(ss_measure) == 0:
                for i in range(1,len(sales_share)):
                    if np.any(sales_share[0]!=sales_share[i]):
                        rerun_sales_shares=False
        #Fourth best way is if we have specified some technologies in the initial year, even if not all
        elif min_demand_technology_year:
            initial_stock = self.stock.technology.loc[elements+(min_demand_technology_year,),:].values/np.nansum(self.stock.technology.loc[elements+(min_demand_technology_year,),:].values) * initial_total
            rerun_sales_shares = False
        else:
            raise ValueError('user has not input stock data with technologies or sales share data so the model cannot determine the demand_technology composition of the initial stock in subsector %s' %self.id)
        return initial_stock, rerun_sales_shares
        


    def determine_need_for_aux_efficiency(self):
        """ determines whether auxiliary efficiency calculations are necessary. Used to avoid unneccessary calculations elsewhere """
        utility_factor = []       
        for demand_technology in self.technologies.values():
            if demand_technology.efficiency_main.utility_factor == 1:
                utility_factor.append(False)
            else:
                utility_factor.append(True)
        if any(utility_factor):
            self.stock.aux = True
        else:
            self.stock.aux = False


    def stock_normalize(self, levels):
        """returns normalized stocks for use in other subsector calculations"""
        # normalization of complete stock
        self.stock.values_normal = self.stock.values.groupby(level=levels).transform(lambda x: x / x.sum())
        # normalization of demand_technology stocks (i.e. % by vintage/year)
        self.stock.values_normal_tech = self.stock.values.groupby(
            level=util.ix_excl(self.stock.values, ['vintage'])).transform(lambda x
            : x / x.sum()).fillna(0)
        self.stock.values_efficiency_main = copy.deepcopy(self.stock.values)

        # this section normalizes stocks used for efficiency calculations. There is a different process if the stock
        # has technologies that use multiple energy types. If it does, it must keep separate dataframes for main and auxiliary efficiency
        if self.sub_type != 'link':
            self.determine_need_for_aux_efficiency()
            if self.stock.aux:
                self.stock.values_efficiency_aux = copy.deepcopy(self.stock.values)
            for demand_technology in self.technologies.keys():
                demand_technology_class = self.technologies[demand_technology]
                indexer = util.level_specific_indexer(self.stock.values_efficiency_main, 'demand_technology', demand_technology)
                self.stock.values_efficiency_main.loc[indexer, :] = self.stock.values_efficiency_main.loc[indexer,:] * demand_technology_class.efficiency_main.utility_factor
                self.stock.values_efficiency_main.loc[indexer, 'final_energy'] = demand_technology_class.efficiency_main.final_energy_id
                if self.stock.aux:
                    self.stock.values_efficiency_aux.loc[indexer, :] = self.stock.values.loc[indexer, :] * (
                        1 - demand_technology_class.efficiency_main.utility_factor)
                    if hasattr(demand_technology_class.efficiency_aux, 'final_energy_id'):
                        self.stock.values_efficiency_aux.loc[
                            indexer, 'final_energy'] = demand_technology_class.efficiency_aux.final_energy_id
                    else:
                        self.stock.values_efficiency_aux.loc[indexer, 'final_energy'] = 9999
            if self.stock.aux:
                self.stock.values_efficiency = pd.concat([self.stock.values_efficiency_aux, self.stock.values_efficiency_main])
            else:
                # if there is no auxiliary efficiency, efficiency main becomes used for total efficiency
                self.stock.values_efficiency = self.stock.values_efficiency_main
            self.stock.values_efficiency = self.set_energy_as_index(self.stock.values_efficiency)
            self.stock.values_efficiency = self.stock.values_efficiency.reset_index().groupby(
                self.stock.values_efficiency.index.names).sum()
            # normalize dataframe for efficiency calculations
            # self.stock.values_efficiency = pd.concat([self.stock.values_efficiency_main, self.stock.values_efficiency_aux])
            self.stock.values_efficiency_normal = self.stock.values_efficiency.groupby(
                level=util.ix_excl(self.stock.values_efficiency, ['final_energy', 'demand_technology', 'vintage'])).transform(
                lambda x: x / x.sum()).fillna(0)
            self.stock.values_efficiency_normal_tech = self.stock.values_efficiency.groupby(
                level=util.ix_excl(self.stock.values_efficiency, ['final_energy', 'vintage'])).transform(
                lambda x: x / x.sum()).fillna(0)
            self.stock.values_efficiency_normal_energy = self.stock.values_efficiency.groupby(
                level=util.ix_excl(self.stock.values_efficiency, ['demand_technology', 'vintage'])).transform(
                lambda x: x / x.sum()).fillna(0)

    def set_energy_as_index(self, df):
        """ takes a column with an energy id and makes it an index level """
        df = df.set_index('final_energy', append=True)
        df = df.swaplevel('vintage', 'final_energy')
        util.replace_index_name(df, 'final_energy')
        return df

    def financial_stock(self):
        """
        Calculates the amount of stock based on sales and demand_technology book life
        instead of physical decay
        """
        for tech in self.technologies.values():
            # creates binary matrix across years and vintages for a demand_technology based on its book life
            tech.book_life_matrix = util.book_life_df(tech.book_life, self.vintages, self.years)
            # creates a linear decay of initial stock
            tech.initial_book_life_matrix = util.initial_book_life_df(tech.book_life, tech.mean_lifetime, self.vintages, self.years)
        # reformat the book_life_matrix dataframes to match the stock dataframe
        # creates a list of formatted tech dataframes and concatenates them
        tech_dfs = [self.reformat_tech_df(self.stock.sales, tech, tech_class=None, tech_att='book_life_matrix', id=tech.id) for tech in self.technologies.values()]
        tech_df = pd.concat(tech_dfs)
        # initial_stock_df uses the stock values dataframe and removes vintagesot
        initial_stock_df = self.stock.values[min(self.years)]
        # formats tech dfs to match stock df
        initial_tech_dfs = [self.reformat_tech_df(initial_stock_df, tech, tech_class=None, tech_att='initial_book_life_matrix',id=tech.id) for tech in self.technologies.values()]
        initial_tech_df = pd.concat(initial_tech_dfs)
        # stock values in any year equals vintage sales multiplied by book life
        self.stock.values_financial_new = util.DfOper.mult([self.stock.sales_new, tech_df])
        self.stock.values_financial_replacement = util.DfOper.mult([self.stock.sales_replacement, tech_df])
        # initial stock values in any year equals stock.values multiplied by the initial tech_df
        initial_values_financial_new = util.DfOper.mult([self.stock.values_new, initial_tech_df],non_expandable_levels=('year'))
        initial_values_financial_replacement = util.DfOper.mult([self.stock.values_replacement, initial_tech_df],non_expandable_levels=('year'))
        # sum normal and initial stock values
        self.stock.values_financial_new = util.DfOper.add([self.stock.values_financial_new, initial_values_financial_new],non_expandable_levels=('year'))
        self.stock.values_financial_replacement = util.DfOper.add([self.stock.values_financial_replacement, initial_values_financial_replacement],non_expandable_levels=('year'))
        self.stock.values_financial = util.DfOper.add([self.stock.values_financial_new,self.stock.values_financial_replacement])
    
    def calculate_costs_stock(self):
        """
        produce equipment cost outputs based on stock rollover values and equipment specifications
        """
        self.stock.levelized_costs['capital']['new'] = self.rollover_output(tech_class='capital_cost_new', tech_att='values_level', stock_att='values_financial_new')
        self.stock.levelized_costs['capital']['replacement'] = self.rollover_output(tech_class='capital_cost_replacement', tech_att='values_level', stock_att='values_financial_replacement')
        self.stock.levelized_costs['fixed_om']['new'] = self.rollover_output(tech_class='fixed_om', tech_att='values', stock_att='values_new')
        self.stock.levelized_costs['fixed_om']['replacement'] = self.rollover_output(tech_class='fixed_om', tech_att='values', stock_att='values_replacement')
        self.stock.levelized_costs['installation']['new'] = self.rollover_output(tech_class='installation_cost_new', tech_att='values_level', stock_att='values_financial_new')
        self.stock.levelized_costs['installation']['replacement'] = self.rollover_output(tech_class='installation_cost_replacement', tech_att='values_level', stock_att='values_financial_replacement')
        if self.sub_type != 'link':
            self.stock.levelized_costs['fuel_switching']['new'] = self.rollover_output(tech_class='fuel_switch_cost', tech_att='values_level', stock_att='values_fuel_switch')
        self.stock.annual_costs['capital']['new'] = self.rollover_output(tech_class='capital_cost_new', tech_att='values', stock_att='sales_new')
        self.stock.annual_costs['capital']['replacement'] = self.rollover_output(tech_class='capital_cost_replacement', tech_att='values', stock_att='sales_replacement')
        self.stock.annual_costs['installation']['new'] = self.rollover_output(tech_class='installation_cost_new', tech_att='values', stock_att='sales_new')
        self.stock.annual_costs['installation']['replacement'] = self.rollover_output(tech_class='installation_cost_replacement', tech_att='values', stock_att='sales_replacement')
        if self.sub_type != 'link':
            self.stock.annual_costs['fuel_switching']['all'] = self.rollover_output(tech_class='fuel_switch_cost', tech_att='values', stock_att='sales_fuel_switch',)

    def remove_extra_subsector_attributes(self):
        if hasattr(self, 'stock'):
            delete_list = ['values_financial_new', 'values_financial_replacement', 'values_new',
                           'values_replacement', 'sales_new', 'sales_replacement','sales_fuel_switch']
            delete_list = []
            for att in delete_list:
                if hasattr(self.stock, att):
                    delattr(self.stock, att)

    def rollover_efficiency_outputs(self, other_index=None):
        """
        Calculate rollover efficiency outputs for the whole stock or stock groups by final energy and demand_technology.
        Efficiency values are all stock-weighted by indexed inputs. Ex. if the other_index input equals 'all', multiplying
        these efficiency values by total service demand would equal total energy. 
        """
        if other_index is not None:
            index = util.ensure_iterable_and_not_string(other_index)
        else:
            index = util.ensure_iterable_and_not_string(['all', 'demand_technology', 'final_energy'])
        index.append('all')
        self.stock.efficiency = defaultdict(dict)
        for element in index:
            if element == 'demand_technology':
                aggregate_level = None
                values_normal = 'values_efficiency_normal_tech'
            elif element == 'final_energy':
                aggregate_level = None
                values_normal = 'values_efficiency_normal_energy'
            elif element == 'all':
                aggregate_level = None
                values_normal = 'values_efficiency_normal'
            elif element == 'total':
                aggregate_level = 'demand_technology'
                values_normal = 'values_efficiency_normal'
            if self.stock.aux:
                self.stock.efficiency[element]['all'] = self.rollover_output(tech_class=['efficiency_main','efficiency_aux'],
                                                                             stock_att=values_normal,
                                                                             other_aggregate_levels=aggregate_level, efficiency=True)
            else:
                self.stock.efficiency[element]['all'] = self.rollover_output(tech_class='efficiency_main',
                                                                             stock_att=values_normal,
                                                                             other_aggregate_levels=aggregate_level, efficiency=True)

    def fuel_switch_stock_calc(self):
        """ 
        Calculates the amount of stock that has switched energy type and allocates 
        it to technologies based on demand_technology share. This is used to calculate the additional
        costs of fuel switching for applicable technologies.
        Ex. an EV might have a fuel switching cost that represents the cost of a home charger that is incurred only
        when the charger is installed. 
        """
        fuel_switch_sales = copy.deepcopy(self.stock.sales)
        fuel_switch_retirements = copy.deepcopy(self.stock.retirements)
        for demand_technology in self.technologies.values():
            indexer = util.level_specific_indexer(fuel_switch_sales, 'demand_technology', demand_technology.id)
            fuel_switch_sales.loc[indexer, 'final_energy'] = demand_technology.efficiency_main.final_energy_id
            fuel_switch_retirements.loc[indexer, 'final_energy'] = demand_technology.efficiency_main.final_energy_id
        fuel_switch_sales = fuel_switch_sales.set_index('final_energy', append=True)
        fuel_switch_sales = fuel_switch_sales.swaplevel('vintage', 'final_energy')
        util.replace_index_name(fuel_switch_sales, 'final_energy')
        fuel_switch_retirements = fuel_switch_retirements.set_index('final_energy', append=True)
        fuel_switch_retirements = fuel_switch_retirements.swaplevel('vintage', 'final_energy')
        util.replace_index_name(fuel_switch_retirements, 'final_energy')
        # TODO check that these work!!
        fuel_switch_sales_energy = util.remove_df_levels(fuel_switch_sales, 'demand_technology')
        fuel_switch_retirements_energy = util.remove_df_levels(fuel_switch_retirements, 'demand_technology')
        new_energy_sales = DfOper.subt([fuel_switch_sales_energy, fuel_switch_retirements_energy])
        new_energy_sales[new_energy_sales<0]=0
        new_energy_sales_share_by_demand_technology = fuel_switch_sales.groupby(level=util.ix_excl(fuel_switch_sales, 'demand_technology')).transform(lambda x: x / x.sum())
#        new_energy_sales_share_by_demand_technology[new_energy_sales_share_by_demand_technology < 0] = 0
        new_energy_sales_by_demand_technology = DfOper.mult([new_energy_sales_share_by_demand_technology, new_energy_sales])
        fuel_switch_sales_share = DfOper.divi([new_energy_sales_by_demand_technology, fuel_switch_sales]).replace(np.nan,0)
#        .groupby(level=util.ix_excl(fuel_switch_sales, 'demand_technology')).sum()
        fuel_switch_sales_share = util.remove_df_levels(fuel_switch_sales_share, 'final_energy')
        self.stock.sales_fuel_switch = DfOper.mult([self.stock.sales, fuel_switch_sales_share])       
        self.stock.values_fuel_switch = DfOper.mult([self.stock.values_financial, fuel_switch_sales_share])

    def calculate_parasitic(self):
        """ 
        calculates parasitic energy demand   
        
        """
        self.parasitic_energy = self.rollover_output(tech_class='parasitic_energy', tech_att='values',
                                                     stock_att='values',stock_expandable=True)

    def calculate_output_service_drivers(self):
        """ calculates service drivers for use in linked subsectors
        """
        self.calculate_service_impact()
        self.output_service_drivers = {}
        for link in self.service_links.values():
            df = link.values
            df = pd.DataFrame(df.stack(), columns=['value'])
            util.replace_index_name(df, 'year')
            self.output_service_drivers[link.linked_subsector_id] = df
#        self.reformat_service_demand()

    def calculate_output_demand_technology_stocks(self):
        """ calculates demand_technology stocks for use in subsectors with linked technologies
        """
        self.output_demand_technology_stocks = {}
        stock = self.stock.values.groupby(level=util.ix_excl(self.stock.values, 'vintage')).sum()
        stock = stock.stack()
        util.replace_index_name(stock, 'year')
        stock = pd.DataFrame(stock, columns=['value'])
        for demand_technology in self.technologies.values():
            if demand_technology.linked_id is not None:
                indexer = util.level_specific_indexer(stock, 'demand_technology', demand_technology.id)
                tech_values = pd.DataFrame(stock.loc[indexer, :], columns=['value'])
                util.replace_index_label(tech_values, {demand_technology.id: demand_technology.linked_id}, 'demand_technology')
                self.output_demand_technology_stocks[demand_technology.linked_id] = tech_values * demand_technology.stock_link_ratio

    def calculate_service_impact(self):
        """ 
        calculates a normalized service impact for linked demand_technology stocks as a function
        of demand tech service link data and subsector service link impact specifications.
        
        ex. 
        service efficiency of clothes washing stock for the water heating subsector =
        (1- clothes washing service_demand_share of water heating) +
        (normalized stock service efficiency of clothes washers (i.e. efficiency of hot water usage) * service_demand_share)
        
        This vector can then be multiplied by clothes washing service demand to create an additional driver for water heating         
        
        """
        for id in self.service_links:
            link = self.service_links[id]
            link.values = self.rollover_output_dict(tech_dict='service_links',tech_dict_key=id, tech_att='values', stock_att='values_normal')
#            # sum over demand_technology and vintage to get a total stock service efficiency
            link.values = util.remove_df_levels(link.values,['demand_technology', 'vintage'])
            # normalize stock service efficiency to calibration year
            values = link.values.as_matrix()
            calibration_values = link.values[link.year].as_matrix()
            calibration_values = np.column_stack(calibration_values).T
            new_values = 1 - (values / calibration_values)
            # calculate weighted after service efficiency as a function of service demand share
            new_values = (link.service_demand_share * new_values) 
            link.values = pd.DataFrame(new_values, link.values.index, link.values.columns.values)
            link.values.replace([np.inf,-np.inf,np.nan],[0,0,0],inplace=True)
   
    def reformat_service_demand(self):
        """
        format service demand with year index once calculations are complete
        """
        if hasattr(self,'service_demand') and 'year' not in self.service_demand.values.index.names:
            self.service_demand.values = pd.DataFrame(self.service_demand.values.stack(), columns=['value'])
            util.replace_index_name(self.service_demand.values, 'year')

    def rollover_output(self, tech_class=None, tech_att='values', stock_att=None,
                        stack_label=None, other_aggregate_levels=None, efficiency=False, stock_expandable=False):
        """ Produces rollover outputs for a subsector stock based on the tech_att class, att of the class, and the attribute of the stock
        ex. to produce levelized costs for all new vehicles, it takes the capital_costs_new class, the 'values_level' attribute, and the 'values'
        attribute of the stock
        """
        
        
        stock_df = getattr(self.stock, stock_att)
        groupby_level = util.ix_excl(stock_df, ['vintage'])
        # determines index position for demand_technology and final energy element
        c = util.empty_df(stock_df.index, stock_df.columns.values, fill_value=0.)
        # puts technologies on the appropriate basis
        tech_class = util.put_in_list(tech_class)  
        tech_dfs = []
        for tech_class in tech_class:
            tech_dfs += ([self.reformat_tech_df(stock_df, tech, tech_class, tech_att, tech.id, efficiency) for tech in
                        self.technologies.values() if
                            hasattr(getattr(tech, tech_class), tech_att) and getattr(tech, tech_class).raw_values is not None])       
        if len(tech_dfs):
            tech_df = util.DfOper.add(tech_dfs)
            tech_df = tech_df.reorder_levels([x for x in stock_df.index.names if x in tech_df.index.names]+[x for x in tech_df.index.names if x not in stock_df.index.names])
            tech_df = tech_df.sort_index()
            c = util.DfOper.mult((tech_df, stock_df), expandable=(True, stock_expandable), collapsible=(False, True))
        else:
            util.empty_df(stock_df.index, stock_df.columns.values, 0.)

        if stack_label is not None:
            c = c.stack()
            util.replace_index_name(c, stack_label)
            util.replace_column(c, 'value')
        if other_aggregate_levels is not None:
            groupby_level = util.ix_excl(c, other_aggregate_levels)
            c = c.groupby(level=groupby_level).sum()
        # TODO fix
        if 'final_energy' in c.index.names:
            c = util.remove_df_elements(c, 9999, 'final_energy')
        return c
        
        
        
    def rollover_output_dict(self, tech_dict=None, tech_dict_key=None, tech_att='values', stock_att=None,
                        stack_label=None, other_aggregate_levels=None, efficiency=False,fill_value=0.0):
        """ Produces rollover outputs for a subsector stock based on the tech_att class, att of the class, and the attribute of the stock
        ex. to produce levelized costs for all new vehicles, it takes the capital_costs_new class, the 'values_level' attribute, and the 'values'
        attribute of the stock
        """
               
        stock_df = getattr(self.stock, stock_att)
        groupby_level = util.ix_excl(stock_df, ['vintage'])
        # determines index position for demand_technology and final energy element
        c = util.empty_df(stock_df.index, stock_df.columns.values, fill_value=fill_value)
        # puts technologies on the appropriate basis
        tech_dfs = []
        tech_dfs += ([self.reformat_tech_df_dict(stock_df = stock_df, tech=tech, tech_dict=tech_dict,
                                                 tech_dict_key=tech_dict_key, tech_att=tech_att, id=tech.id, efficiency=efficiency) for tech in self.technologies.values()
                            if getattr(tech,tech_dict).has_key(tech_dict_key)])
        if len(tech_dfs):
            tech_df = util.DfOper.add(tech_dfs)
            tech_df = tech_df.reorder_levels([x for x in stock_df.index.names if x in tech_df.index.names]+[x for x in tech_df.index.names if x not in stock_df.index.names])
            tech_df = tech_df.sort_index()
        # TODO figure a better way
            c = DfOper.mult((tech_df, stock_df), expandable=(True, False), collapsible=(False, True))
        else:
            util.empty_df(stock_df.index, stock_df.columns.values, 0.)
        if stack_label is not None:
            c = c.stack()
            util.replace_index_name(c, stack_label)
            util.replace_column(c, 'value')
        if other_aggregate_levels is not None:
            groupby_level = util.ix_excl(c, other_aggregate_levels)
            c = c.groupby(level=groupby_level).sum()
        # TODO fix
        if 'final_energy' in c.index.names:
            c = util.remove_df_elements(c, 9999, 'final_energy')
        return c

    def reformat_tech_df(self, stock_df, tech, tech_class, tech_att, id, efficiency=False):
        """
        reformat technoology dataframes for use in stock-level dataframe operations
        """
        if tech_class is None:
            tech_df = getattr(tech, tech_att)
        else:
            tech_df = getattr(getattr(tech, tech_class), tech_att)
        if 'demand_technology' not in tech_df.index.names:
            tech_df['demand_technology'] = id
            tech_df.set_index('demand_technology', append=True, inplace=True)
        if efficiency is True and 'final_energy' not in tech_df.index.names:
            final_energy_id = getattr(getattr(tech, tech_class), 'final_energy_id')
            tech_df['final_energy'] = final_energy_id
            tech_df.set_index('final_energy', append=True, inplace=True)
        return tech_df

    def reformat_tech_df_dict(self, stock_df, tech, tech_dict, tech_dict_key, tech_att, id, efficiency=False):
        """
        reformat technoology dataframes for use in stock-level dataframe operations
        """
        if getattr(tech,tech_dict).has_key(tech_dict_key):
            tech_df = getattr(getattr(tech,tech_dict)[tech_dict_key],tech_att)
            if 'demand_technology' not in tech_df.index.names:
                tech_df['demand_technology'] = id
                tech_df.set_index('demand_technology', append=True, inplace=True)
            if efficiency is True and 'final_energy' not in tech_df.index.names:
                final_energy_id = getattr(getattr(tech,tech_dict)[tech_dict_key], 'final_energy_id')
                tech_df['final_energy'] = final_energy_id
                tech_df.set_index('final_energy', append=True, inplace=True)
            return tech_df

    def calculate_energy_stock(self):
        """
        calculate subsector energy forecasts based on main and auxiliary efficiency and service demand as well 
        as parasitic energy
        """
        self.rollover_efficiency_outputs()
        self.calculate_parasitic()
        self.service_demand.values = self.service_demand.values.unstack('year')
        self.service_demand.values.columns = self.service_demand.values.columns.droplevel()
        all_energy = util.DfOper.mult([self.stock.efficiency['all']['all'],self.service_demand.modifier, self.service_demand.values]) 
        self.energy_forecast = util.DfOper.add([all_energy, self.parasitic_energy])
        self.energy_forecast = pd.DataFrame(self.energy_forecast.stack())
        util.replace_index_name(self.energy_forecast, 'year')
        util.replace_column(self.energy_forecast, 'value')
        self.energy_forecast = util.remove_df_elements(self.energy_forecast, 9999, 'final_energy')





