__author__ = 'Ben Haley & Ryan Jones'

from config import cfg
from shape import shapes

import util
from datamapfunctions import DataMapFunctions
import numpy as np
import pandas as pd
from collections import defaultdict
import copy
from collections import defaultdict
from datetime import datetime
from demand_subsector_classes import DemandStock, SubDemand, ServiceEfficiency, ServiceLink
from shared_classes import AggregateStock
from demand_measures import ServiceDemandMeasure, EnergyEfficiencyMeasure, FuelSwitchingMeasure
from demand_technologies import DemandTechnology, SalesShare
from rollover import Rollover
from util import DfOper
from outputs import DemandSideOutput

class Demand(object):
    def __init__(self, **kwargs):
        self.drivers = {}
        self.sectors = {}
        self.case = cfg.cfgfile.get('case', 'demand_case')
        self.case_id = util.sql_read_table('DemandCases', 'id', name=self.case)
        self.outputs = DemandSideOutput()

    def aggregate_results(self):
        output_list = ['energy', 'stock', 'investment_costs', 'levelized_costs']
        for output in output_list:
            setattr(self.outputs, output, self.group_output(output))
            
    def link_to_supply(self, emissions_link, energy_link, cost_link):   
        setattr(self.outputs, 'emissions', self.group_linked_output(emissions_link))
        setattr(self.outputs, 'energy_costs', self.group_linked_output(cost_link))
        setattr(self.outputs, 'embodied_energy', self.group_linked_output(energy_link))

    def group_output(self, output_type, levels_to_keep=None):
        levels_to_keep = cfg.output_levels if levels_to_keep is None else levels_to_keep
        df_list = [sector.group_output(output_type, levels_to_keep) for sector in self.sectors.values()]
        keys = self.sectors.keys()
        new_names = 'sector'
        return util.df_list_concatenate(df_list, keys, new_names, levels_to_keep)
    
    def group_linked_output(self, supply_link, levels_to_keep=None):
        levels_to_keep = cfg.output_levels if levels_to_keep is None else levels_to_keep
        return  DfOper.mult([self.outputs.energy.groupby(level=levels_to_keep).sum(), supply_link])

    def aggregate_sector_energy_for_supply_side(self):
        """Aggregates for the supply side, works with function in sector"""
        names = ['sector', cfg.cfgfile.get('case', 'primary_geography'), 'final_energy', 'year']
        sectors_aggregates = [sector.aggregate_subsector_energy_for_supply_side() for sector in self.sectors.values()]
        self.energy_demand = pd.concat([s for s in sectors_aggregates if len(s)], keys=self.sectors.keys(), names=names)
        
    def add_drivers(self):
        """Loops through driver ids and call create driver function"""
        ids = [id for id in cfg.cur.execute('select id from DemandDrivers')]
        for (id,) in ids:
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
            driver.remap(drivers=base_driver.values)
        else:
            driver.remap()
        # Now that it has been mapped, set indicator to true
        driver.mapped = True
        driver.values.data_type = 'total'

    def add_sectors(self):
        """Loop through sector ids and call add sector function"""
        ids = [id for id in cfg.cur.execute('select id from DemandSectors')]
        for (id,) in ids:
            self.add_sector(id)

    def add_sector(self, id):
        """add sector object to demand"""
        if id in self.sectors:
            # ToDo note that a sector by the same name was added twice
            return
        self.sectors[id] = Sector(id, self.drivers, self.case_id)

    def yield_subsectors(self):
        """ yields subsector class instances from sector and subsector dictionaries"""
        for sector in self.sectors.values():
            for subsector in sector.subsectors.values():
                yield subsector

    def precursor_dict(self):
        """
        determines calculation order based on subsector precursors for service demand drivers or specified stocks
        example: 
            clothes washing can be a service demand precursor for water heating, and so must be solved first. This puts water heating as the 
            key in a dictionary with clothes washing as a value. Function also records the link in the service_precursors dictionary within the same loop. 
        """

        self.subsector_precursors = defaultdict(list)
        self.service_precursors = defaultdict(dict)
        self.stock_precursors = defaultdict(dict)
        for subsector in self.yield_subsectors():
            for service_link in subsector.service_links.values():
                self.subsector_precursors[service_link.linked_subsector_id].append(subsector.id)
                self.service_precursors[service_link.linked_subsector_id]
            if hasattr(subsector, 'technologies'):
                for technology in subsector.technologies.values():
                    linked_tech_id = technology.linked_id
                    for lookup_subsector in self.yield_subsectors():
                        if hasattr(lookup_subsector, 'technologies'):
                            if linked_tech_id in lookup_subsector.technologies.keys():
                                self.subsector_precursors[lookup_subsector.id].append(subsector.id)

    def manage_calculations(self):
        """
        loops through subsectors making sure to calculate subsector precursors
        before calculating subsectors themselves
        """
        for sector in self.sectors.values():
            print 'calculating '+sector.name+' sector'
            for subsector in sector.subsectors.values():
                if subsector.calculated:
                    continue
                # calculate subsector
                self.calculate(subsector)
        
        cfg.outputs_id_map['sector'] = util.upper_dict([(k, v.name) for k, v in self.sectors.items()])
        cfg.outputs_id_map['subsector'] = util.upper_dict(util.flatten_list([[(k, v.name) for k, v in sector.subsectors.items()] for sector in self.sectors.values()]))

    def calculate(self, subsector):
        """ 
        calculates subsector if all precursors have been calculated
        """

        # checks whether the subsector has precursors in the subsector_precursors dictionary
        if self.subsector_precursors.has_key(subsector.id):
            # loops through subsector precursors
            for precursor_id in self.subsector_precursors[subsector.id]:
                # finds subsector in the demand sectors and subsectors
                for sector in self.sectors.values():
                    if precursor_id in sector.subsectors.keys():
                        # precursor is the class instance of the precursor subsector id
                        precursor = self.sectors[sector.id].subsectors[precursor_id]
                        if precursor.calculated:
                            # checks whether the precursor has been calculated. If it has, update the service_precursors dictionary
                            # with the output_service_drivers if applicable. This allows a subsector to output service drivers to multiple
                            # subsectors
                            if precursor.output_service_drivers.has_key(subsector.id):
                                self.service_precursors[subsector.id].update(
                                    {precursor.id: precursor.output_service_drivers[subsector.id]})
                            continue
                        else:
                            self.calculate(precursor)
                            if precursor.output_service_drivers.has_key(subsector.id):
                                # update the service_precursors dictionary
                                # with the output_service_drivers if applicable
                                self.service_precursors[subsector.id].update(
                                    {precursor.id: precursor.output_service_drivers[subsector.id]})
                            # loops through linked technology stocks from the precursor
                            for technology in precursor.output_specified_stocks.keys():
                                if technology in subsector.technologies.keys():
                                    # updates stock_precursor values dictionary with linked specified stocks
                                    self.stock_precursors[subsector.id].update(
                                        {technology: precursor.output_specified_stocks[technology]})
                                    # calculate after precursor loop is complete
        for sector in self.sectors.values():
            if subsector in sector.subsectors.values():
                if subsector.calculated:
                    continue
                else:
                    print '  '+subsector.name
                    # pass service demand and stock preursors to subsector
                    subsector.calculate(self.service_precursors[subsector.id], self.stock_precursors[subsector.id])


class Driver(object, DataMapFunctions):
    def __init__(self, id, **kwargs):
        self.id = id
        self.sql_id_table = 'DemandDrivers'
        self.sql_data_table = 'DemandDriversData'
        self.mapped = False
        for col, att in util.object_att_from_table(self.sql_id_table, id):
            setattr(self, col, att)
        # creates the index_levels dictionary
        DataMapFunctions.__init__(self)
        self.read_timeseries_data()


class Sector(object):
    def __init__(self, id, drivers, case_id, **kwargs):
        self.drivers = drivers
        self.id = id
        self.subsectors = {}
        self.case_id = case_id
        for col, att in util.object_att_from_table('DemandSectors', id):
            setattr(self, col, att)
        self.outputs = DemandSideOutput()

    def add_subsectors(self):
        ids = [id for id in
               cfg.cur.execute('select id from DemandSubsectors where sector_id=? and is_active=1', (self.id,))]
        for (id,) in ids:
            self.add_subsector(id, self.id)

    def add_subsector(self, id, sector_id, **kwargs):
        """Adds subsector object to sector"""
        if id in self.subsectors:
            # ToDo note that a subsector was added twice
            return
        # checks for data and passes to subsector class to determine subsector type
        if id in util.sql_read_table('DemandStock', 'subsector_id', return_iterable=True):
            stock = True
        else:
            stock = False
        if id in util.sql_read_table('DemandServiceDemands', 'subsector_id', return_iterable=True):
            service_demand = True
        else:
            service_demand = False
        if id in util.sql_read_table('DemandEnergyDemands', 'subsector_id', return_iterable=True):
            energy_demand = True
        else:
            energy_demand = False
        if id in util.sql_read_table('DemandServiceEfficiency', 'subsector_id', return_iterable=True):
            service_efficiency = True
        else:
            service_efficiency = False
        self.subsectors[id] = Subsector(id, self.drivers, stock, service_demand, energy_demand, service_efficiency,
                                        self.id, self.case_id)

    def aggregate_subsector_energy_for_supply_side(self):
        """Aggregates for the supply side, works with function in demand"""
        levels_to_keep = [cfg.cfgfile.get('case', 'primary_geography'), 'final_energy', 'year']
        return util.DfOper.add([pd.DataFrame(subsector.energy_forecast.value.groupby(level=levels_to_keep).sum()).sort() for subsector in self.subsectors.values() if hasattr(subsector, 'energy_forecast')])

    def group_output(self, output_type, levels_to_keep=None):
        levels_to_keep = cfg.output_levels if levels_to_keep is None else levels_to_keep
        df_list = [subsector.group_output(output_type, levels_to_keep) for subsector in self.subsectors.values()]
        keys = self.subsectors.keys()
        new_names = 'subsector'
        return util.df_list_concatenate(df_list, keys, new_names, levels_to_keep)


class Subsector(DataMapFunctions):
    def __init__(self, id, drivers, stock, service_demand, energy_demand,
                 service_efficiency, sector_id, case_id, **kwargs):
        self.id = id
        self.drivers = drivers
        # boolean check on data availability to determine calculation steps
        self.has_stock = stock
        self.has_service_demand = service_demand
        self.has_energy_demand = energy_demand
        self.has_service_efficiency = service_efficiency
        self.sector_id = sector_id
        self.case_id = case_id
        for col, att in util.object_att_from_table('DemandSubsectors', id):
            setattr(self, col, att)
        
        self.outputs = DemandSideOutput()
        self.calculated = False

    def add_energy_system_data(self):
        """ 
        populates energy system based on available data and determines 
        subsector type 
        """
        if self.has_stock is True and self.has_service_demand is True:
            self.service_demand = SubDemand(self.id, sql_id_table='DemandServiceDemands',
                                            sql_data_table='DemandServiceDemandsData',
                                            primary_key='demand_service_demand_id',
                                            drivers=self.drivers)
            self.add_stock()
            if self.stock.demand_stock_unit_type == 'equipment':
                self.add_technologies(self.service_demand.unit, self.stock.time_unit)
            else:
                self.add_technologies(self.stock.unit, self.stock.time_unit)
            self.sub_type = 'stock and service'
        elif self.has_stock is True and self.has_energy_demand is True:
            self.energy_demand = SubDemand(self.id, sql_id_table='DemandEnergyDemands',
                                           sql_data_table='DemandEnergyDemandsData',
                                           primary_key='demand_energy_demand_id', drivers=self.drivers)
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
            self.service_demand = SubDemand(self.id, sql_id_table='DemandServiceDemands',
                                            sql_data_table='DemandServiceDemandsData',
                                            primary_key='demand_service_demand_id',
                                            drivers=self.drivers)
            self.service_efficiency = ServiceEfficiency(self.id, self.service_demand.unit)
            self.sub_type = 'service and efficiency'

        elif self.has_service_demand is True and self.has_energy_demand is True:
            self.service_demand = SubDemand(self.id, sql_id_table='DemandServiceDemands',
                                            sql_data_table='DemandServiceDemandsData',
                                            primary_key='demand_service_demand_id',
                                            drivers=self.drivers)
            self.energy_demand = SubDemand(self.id, sql_id_table='DemandEnergyDemands',
                                           sql_data_table='DemandEnergyDemandsData',
                                           primary_key='demand_energy_demand_id',
                                           drivers=self.drivers)
            self.sub_type = 'service and energy'

        elif self.has_energy_demand is True:
            self.energy_demand = SubDemand(self.id, sql_id_table='DemandEnergyDemands',
                                           sql_data_table='DemandEnergyDemandsData',
                                           primary_key='demand_energy_demand_id',
                                           drivers=self.drivers)
            self.sub_type = 'energy'
        else:
            raise ValueError("User has not input enough data")
        self.add_service_links()
        self.calculate_years()


    def filter_packages(self):
        """filters packages by case"""
        packages = [x for x in util.sql_read_headers('DemandCasesData') if x not in ['id', 'subsector_id']]
        for package in packages:
            package_id = util.sql_read_table('DemandCasesData', package, subsector_id=self.id, id=self.case_id)
            setattr(self, package, package_id)


    def add_measures(self):
        """ add measures to subsector based on case and package inputs """
        self.filter_packages()
        self.add_service_demand_measures()
        self.add_energy_efficiency_measures()
        self.add_fuel_switching_measures()
        self.add_stock_measures()

    def add_stock_measures(self):
        """ add specified stock and sales measures to model if the subsector
        is populated with stock data """
        if self.has_stock:
            for tech in self.technologies:
                self.technologies[tech].add_specified_stock_measures(self.stock_package_id)
                self.technologies[tech].add_sales_share_measures(self.sales_package_id)


    def calculate(self, linked_service_demand_drivers=None, linked_stock=None):
        """ subsector calculation function """
        print '    '+'calculating measures'
        self.calculate_measures()
        print '    '+'adding linked inputs'
        self.add_linked_inputs(linked_service_demand_drivers, linked_stock)
        print '    '+'forecasting energy drivers'
        self.project()
        print '    '+'calculating subsector energy demand'
        self.calculate_energy()
        self.project_measure_stocks()
        self.calculated = True
        print '    '+'calculating costs'
        self.calculate_costs()
        print '    '+'processing outputs'
        self.remove_extra_subsector_attributes()

    def add_linked_inputs(self, linked_service_demand_drivers, linked_stock):
        """ adds linked inputs to subsector """
        self.linked_service_demand_drivers = linked_service_demand_drivers
        self.linked_stock = linked_stock
        self.interpolation_method = 'linear_interpolation'
        self.extrapolation_method = 'linear_interpolation'

    def group_output(self, output_type, levels_to_keep=None):
        levels_to_keep = cfg.output_levels if levels_to_keep is None else levels_to_keep
        if output_type=='energy':
            return self.energy_forecast
        elif output_type=='stock':
            return self.stock.values if hasattr(self, 'stock') else None
        elif output_type=='investment_costs':
            return self.format_output_stock_costs('investment', levels_to_keep) if hasattr(self, 'stock') else None
        elif output_type=='levelized_costs':
            return self.format_output_stock_costs('levelized_costs', levels_to_keep) if hasattr(self, 'stock') else None

    def format_output_stock(self, override_levels_to_keep=None):
        if not hasattr(self, 'stock'):
            return None
        levels_to_keep = cfg.output_levels if override_levels_to_keep is None else override_levels_to_keep
        levels_to_eleminate = [l for l in self.stock.values.index.names if l not in levels_to_keep]
        return util.remove_df_levels(self.stock.values, levels_to_eleminate).sort()

    def format_output_stock_costs(self, att, override_levels_to_keep=None):
        """ 
        Formats cost outputs
        """
        if not hasattr(self, 'stock'):
            return None
        cost_dict = getattr(self.stock, att)
        keys, values = zip(*[(a, b) for a, b in util.unpack_dict(cost_dict)])
        keys = util.flatten_list([[tuple(k)]*len(v) for k, v in zip(keys, values)])
        return util.df_list_concatenate(values, keys=keys, new_names=['cost category', 'new/replacement'])

    def calculate_measures(self):
        """calculates measures for use in subsector calculations """
        for measure in self.energy_efficiency_measures.values():
            measure.calculate(self.vintages, self.years, cfg.cfgfile.get('case', 'energy_unit'))
        for measure in self.service_demand_measures.values():
            measure.calculate(self.vintages, self.years, self.service_demand.unit)
        for measure in self.fuel_switching_measures.values():
            measure.calculate(self.vintages, self.years, cfg.cfgfile.get('case', 'energy_unit'))

    def calculate_energy(self):
        """ calculates energy demand for all subsector types"""
        print '      '+'subsector type = '+self.sub_type
        if self.sub_type == 'service and efficiency' or self.sub_type == 'service and energy':
            # sets the service demand forecast equal to initial values
            self.service_demand_forecast = self.service_demand.values
            # calculates the service demand change from service demand measures
            self.service_demand_savings_calc()
            # calculates the energy demand change from fuel swiching measures
            self.fuel_switching_impact_calc()
            # calculates the energy demand change from energy efficiency measures
            self.energy_efficiency_savings_calc()
            # adds an index level of subsector name as technology to the dataframe for use in aggregated outputs
        elif self.sub_type == 'energy':
            # calculates the energy demand change from fuel swiching measures
            self.fuel_switching_impact_calc()
            # calculates the energy demand change from fuel swiching measures
            self.energy_efficiency_savings_calc()
            # adds an index level of subsector name as technology to the dataframe for use in aggregated outputs
        elif self.sub_type == 'stock and service' or self.sub_type == 'stock and energy':
            # initiates the energy calculation for a subsector with a stock
            self.calculate_energy_stock()
            # calculates service demand and stock linkages to pass to other subsectors 
            self.calculate_output_service_drivers()
            self.calculate_output_specified_stocks()

    def calculate_costs(self):
        """ calculates cost outputs for all subsector types """
        if self.sub_type == 'stock and service' or self.sub_type == 'stock and energy':
            self.calculate_costs_stock()
        else:
            self.calculate_costs_measures()

    def calculate_years(self):
        """determines the analysis period within the subsector based on the minimum year
        of all inputs 
        """
        self.calculate_driver_min_year()
        driver_min_year = self.driver_min_year
        if self.sub_type == 'stock and energy':
            tech_min_year = self.calculate_tech_min_year()
            stock_min_year = min(
                self.stock.raw_values.index.levels[util.position_in_index(self.stock.raw_values, 'year')])
            sales_share_min_year = min(
                util.sql_read_table('DemandSalesData', 'vintage', return_iterable=True, subsector_id=self.id))
            energy_min_year = min(self.energy_demand.raw_values.index.levels[
                util.position_in_index(self.energy_demand.raw_values, 'year')])
            self.min_year = min(int(cfg.cfgfile.get('case', 'current_year')), driver_min_year, tech_min_year,
                                stock_min_year, sales_share_min_year, energy_min_year)
        elif self.sub_type == 'stock and service':
            tech_min_year = self.calculate_tech_min_year()
            stock_min_year = min(
                self.stock.raw_values.index.levels[util.position_in_index(self.stock.raw_values, 'year')])
            sales_share_min_year = min(
                util.sql_read_table('DemandSalesData', 'vintage', return_iterable=True, subsector_id=self.id))
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
        self.min_year = max(self.min_year, int(cfg.cfgfile.get('case', 'start_year')))
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
        inititates calculation of all technology attributes - costs, efficiency, etc.
        """
        if hasattr(self, 'technologies'):
            tech_classes = ['capital_cost_new', 'capital_cost_replacement', 'installation_cost_new',
                            'installation_cost_replacement', 'fixed_om', 'fuel_switch_cost', 'efficiency_main',
                            'efficiency_aux']
            tests = defaultdict(list)
            for tech in self.technologies.keys():
                if self.technologies[tech].reference_sales_shares.has_key(1):
                    tests[self.technologies[tech].id].append(self.technologies[tech].reference_sales_shares[1].raw_values.sum().sum() == 0)
                tests[self.technologies[tech].id].append(len(self.technologies[tech].sales_shares) == 0)
                tests[self.technologies[tech].id].append(len(self.technologies[tech].specified_stocks) == 0)
                # Do we have a specified stock in the inputs for this tech?
                if 'technology' in self.stock.raw_values.index.names and tech in util.elements_in_index_level(self.stock.raw_values, 'technology'):
                    tests[self.technologies[tech].id].append(self.stock.raw_values.groupby(level='technology').sum().loc[tech].value==0)
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
        ids = [id for id in
               cfg.cur.execute('select measure_id from DemandEnergyEfficiencyMeasurePackagesData where package_id=?',
                           (self.energy_efficiency_package_id,))]
        for (id,) in ids:
            self.add_energy_efficiency_measure(id, self.cost_of_capital)

    def add_energy_efficiency_measure(self, id, cost_of_capital, **kwargs):
        """Adds measure class instance to subsector"""
        if id in self.energy_efficiency_measures:
            # ToDo note that a technology was added twice
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
                measure.remap(map_from='savings', map_to='savings', drivers=self.energy_forecast)

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
        add all service dmeand measures in a selected package to a dictionary
        """
        self.service_demand_measures = {}
        ids = [id for id in
               cfg.cur.execute('select measure_id from DemandServiceDemandMeasurePackagesData where package_id=?',
                           (self.service_demand_package_id,))]

        for (id,) in ids:
            self.add_service_demand_measure(id, self.cost_of_capital)

    def add_service_demand_measure(self, id, cost_of_capital, **kwargs):
        """Adds measure instances to subsector"""
        if id in self.service_demand_measures:
            return
        self.service_demand_measures[id] = ServiceDemandMeasure(id, cost_of_capital, self.service_demand.unit)

    def service_demand_measure_savings(self):
        """
        calculates measure savings based on the service demand forecast it is being applied to
        i.e. 10% of x = y
        """
        for id in self.service_demand_measures:
            measure = self.service_demand_measures[id]
            if measure.input_type == 'intensity':
                measure.savings = DfOper.mult([measure.savings, self.service_demand_forecast])
            else:
                measure.remap(map_from='savings', map_to='savings', drivers=self.service_demand_forecast)

    def service_demand_savings_calc(self):
        """
        sums and reconciles service demand savings with total available service demand to be saved
        """
        # create an empty df
        self.service_demand_measure_savings()
        self.initial_service_demand_savings = util.empty_df(self.service_demand_forecast.index,
                                                            self.service_demand_forecast.columns.values)
        # add up each measure's savings to return total savings
        for id in self.service_demand_measures:
            measure = self.service_demand_measures[id]
            self.initial_service_demand_savings = DfOper.add([self.initial_service_demand_savings,
                                                              measure.savings])
        # check for savings in excess of demand
        excess_savings = DfOper.subt([self.service_demand_forecast, self.initial_service_demand_savings]) * -1
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
        self.service_demand_forecast = DfOper.subt([self.service_demand_forecast,
                                                    self.service_demand_savings])

    def add_fuel_switching_measures(self):
        """
        add all fuel switching measures in a selected package to a dictionary
        """
        self.fuel_switching_measures = {}
        ids = [id for id in
               cfg.cur.execute('select measure_id from DemandFuelSwitchingMeasurePackagesData where package_id=?',
                           (self.fuel_switching_package_id,))]
        for (id,) in ids:
            self.add_fuel_switching_measure(id, self.cost_of_capital)

    def add_fuel_switching_measure(self, id, cost_of_capital):
        """Adds measure instances to subsector"""
        if id in self.fuel_switching_measures:
            # ToDo note that a technology was added twice
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
        for id in self.fuel_switching_measures:
            measure = self.fuel_switching_measures[id]
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
            for (id,) in self.fuel_switching_savings:
                measure = self.fuel_switching_measures[id]
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
        """loops through subsector technologies and adds technology instances to subsector"""
        self.technologies = {}
        ids = [id for id in cfg.cur.execute('select id from DemandTechs where subsector_id=?', (self.id,))]
        for (id,) in ids:
            self.add_technology(id, self.id, service_demand_unit, stock_time_unit, self.cost_of_capital)
        self.tech_ids = self.technologies.keys()
        self.tech_ids.sort()


    def add_technology(self, id, subsector_id, service_demand_unit, stock_time_unit, cost_of_capital, **kwargs):
        """Adds technology instances to subsector"""
        if id in self.technologies:
            # ToDo note that a technology was added twice
            return
        self.technologies[id] = DemandTechnology(id, subsector_id, service_demand_unit, stock_time_unit, cost_of_capital, **kwargs)

    def remap_tech_attrs(self, attr_classes, attr='values'):
        """
        loops through attr_classes (ex. capital_cost, energy, etc.) in order to map technologies
        that reference other technologies in their inputs (i.e. technology A is 150% of the capital cost technology B)
        """
        attr_classes = util.ensure_iterable_and_not_string(attr_classes)
        for technology in self.technologies.keys():
            for attr_class in attr_classes:
                # It is possible that recursion has converted before we get to an
                # attr_class in the list. If so, continue.
                if getattr(getattr(self.technologies[technology], attr_class), 'converted'):
                    continue
                self.remap_tech_attr(technology, attr_class, attr)

    def remap_tech_attr(self, technology, class_name, attr):
        """
        map reference technology values to their associated technology classes
        
        """
        tech_class = getattr(self.technologies[technology], class_name)
        if hasattr(tech_class, 'reference_tech_id'):
            if getattr(tech_class, 'reference_tech_id'):
                ref_tech_id = (getattr(tech_class, 'reference_tech_id'))
                ref_tech_class = getattr(self.technologies[ref_tech_id], class_name)
                # converted is an indicator of whether an input is an absolute
                # or has already been converted to an absolute
                if not getattr(ref_tech_class, 'converted'):
                    # If a technnology hasn't been mapped, recursion is used
                    # to map it first (this can go multiple layers)
                    self.remap_tech_attr(getattr(tech_class, 'reference_tech_id'), class_name, attr)
                if getattr(tech_class, 'data') is True:
                    tech_data = getattr(tech_class, attr)
                    flipped = getattr(ref_tech_class, 'flipped') if hasattr(ref_tech_class, 'flipped') else False
                    if flipped is True:
                        tech_data = 1 / tech_data
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
        tech_class.converted = True


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
            self.project_service_demand()
            self.project_energy_demand(service_dependent=True)
            self.energy_demand.values = util.unit_convert(self.energy_demand.values,
                                                          unit_from_num=self.energy_demand.unit,
                                                          unit_to_num=cfg.cfgfile.get('case', 'energy_unit'))
            self.energy_forecast = self.energy_demand.values
        elif self.sub_type == 'energy':
            self.project_energy_demand()
            self.energy_demand.values = util.unit_convert(self.energy_demand.values,
                                                          unit_from_num=self.energy_demand.unit,
                                                          unit_to_num=cfg.cfgfile.get('case', 'energy_unit'))
            self.energy_forecast = self.energy_demand.values
        else:
            self.calculate_technologies()
            # determine what levels the service demand forecast has in order to determine
            # what levels to calculate the service demand modifier on i.e. by technology
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
                    self.project_stock()
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
                    self.service_demand.project(map_from='raw_values', fill_timeseries=False)
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
                    time_step_energy = util.unit_convert(self.energy_demand.values, unit_from_den='year',
                                                         unit_to_den=self.stock.time_unit)
                    # divide by capacity factor stock inputs to get a service demand stock
                    # ex. kBtu/hour/capacity factor equals kBtu/hour stock
                    self.stock.remap(map_from='raw_values', map_to='int_values', fill_timeseries=False)
                    _, x = util.difference_in_df_names(time_step_energy, self.stock.int_values)
                    if x:
                        raise ValueError(
                            'energy demand must have the same index levels as stock when stock is specified in capacity factor terms')
                    else:
                        self.stock.int_values = DfOper.divi([time_step_energy, self.stock.int_values])
                    # project energy demand stock
                    self.stock.map_from = 'int_values'
                    self.stock.projected_input_type = 'total'
                    self.project_stock(map_from=self.stock.map_from)
                    self.stock_subset_prep()
                    # remove stock efficiency from energy demand to return service demand
                    self.efficiency_removal()
                    # change the service demand to a per stock_time_unit service demand
                    # ex. kBtu/year to kBtu/hour average service demand
                    time_step_service = util.unit_convert(self.service_demand.values, unit_from_den='year',
                                                          unit_to_den=self.stock.time_unit)
                    # divide by capacity factor stock inputs to get a service demand stock
                    # ex. kBtu/hour/capacity factor equals kBtu/hour stock
                    _, x = util.difference_in_df_names(time_step_service, self.stock.int_values)
                    if x:
                        raise ValueError('service demand must have the same index levels as stock when stock is specified in capacity factor terms')
                    else:
                        self.stock.int_values = DfOper.divi([time_step_service, self.stock.int_values])
                    # stock is by definition service demand dependent
                    self.stock.is_service_demand_dependent = 1
            elif self.stock.demand_stock_unit_type == 'service demand':
                if self.sub_type == 'stock and service':
                    # convert service demand units to stock units
                    self.service_demand.convert_and_remap(self.stock.demand_stock_unit_type, self.stock.unit)
                    self.service_demand.map_from = 'int_values'                    
                    self.min_year = self.min_cal_year(self.service_demand)
                    self.max_year = self.max_cal_year(self.service_demand)
                    self.project_stock()
                    self.stock_subset_prep()
                if self.sub_type == 'stock and energy':
                    # used when we don't have service demand, just energy demand
                    # determine the year range of energy demand inputs
                    self.min_year = self.min_cal_year(self.energy_demand)
                    self.max_year = self.max_cal_year(self.energy_demand)
                    self.project_stock()
                    self.stock_subset_prep()
                    # remove stock efficiency from energy demand to return service demand
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
                self.project_service_demand(map_from=self.service_demand.map_from)
                self.project_stock(map_from=self.stock.map_from, service_dependent=True)
                self.sd_modifier_full()
            elif self.stock.is_service_demand_dependent == 0 and self.service_demand.is_stock_dependent == 1:
                self.project_stock(map_from=self.stock.map_from)
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
        if 'final_energy' in index_names and 'technology' in index_names:
            # TODO review
            self.service_subset = 'final_energy and technology'
        elif 'final_energy' in index_names and 'technology' not in index_names:
            self.service_subset = 'final_energy'
        elif 'final_energy' not in index_names and 'technology' in index_names:
            self.service_subset = 'technology'
        else:
            self.service_subset = None

    def stock_subset_prep(self):
        self.stock.tech_subset_normal = self.stack_and_reduce_years(self.stock.values_normal.groupby(level=util.ix_excl(self.stock.values_normal, 'vintage')).sum(), self.min_year, self.max_year)

        self.stock.tech_subset_normal.fillna(0)
        if self.service_subset == 'final_energy':
            if not hasattr(self.stock, 'values_efficiency_normal'):
                # subsectors with technologies having dual fuel capability do not generally calculate this. Only do so for this specific case.
                self.stock.values_efficiency = pd.concat([self.stock.values_efficiency_main, self.stock.values_efficiency_aux])
                self.stock.values_efficiency_normal = self.stock.values_efficiency.groupby(level=util.ix_excl(self.stock.values_efficiency, ['final_energy', 'technology', 'vintage'])).transform(lambda x: x / x.sum()).fillna(0)
            self.stock.energy_subset_normal = self.stack_and_reduce_years(self.stock.values_efficiency_normal.groupby(
                level=util.ix_excl(self.stock.values_efficiency_normal, ['vintage', 'technology'])).sum(), self.min_year, self.max_year)

    def efficiency_removal(self):
        if self.service_subset is None:
            # base the efficiency conversion on the total stock
            self.convert_energy_to_service('total')
            self.service_demand.map_from = 'int_values'
        elif self.service_subset == 'technology':
            # base the efficiency conversion on individual technology efficiencies
            # if service demand is in technology terms.
            self.convert_energy_to_service('technology')
            self.service_demand.map_from = 'int_values'
        elif self.service_subset == 'final_energy':
            # base the efficiency conversion on efficiencies of equipment with certain final energy types if service
            # if service demand is in final energy terms
            self.convert_energy_to_service('final_energy')
            self.service_demand.map_from = 'int_values'
        else:
            # if service demand is input in technology and energy terms, reduce over
            # the final energy level because it may contradict input utility factors.
            # Then use technology efficiencies to convert to service demand
            self.energy_demand.int_values = self.energy_demand.raw_values.sum(
                util.ix_excl(self.energy_demand.raw_values, ['final_energy']))
            self.convert_energy_to_service('technology')
            self.service_demand.int_values = DfOper.mult([self.service_demand.int_values,
                                                          self.stock.tech_subset])
            self.service_demand.map_from = 'int_values'

    def sd_modifier_full(self):
        """
        calculates the service demand modifier (relation of the share of the service demand
        a technology satisfies vs. the percentage of stock it represents) for subsectors if input service or energy demand
        has a technology or final energy index. Once an initial calculation is made, technology specific service demand modifiers
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
        df_for_indexing = util.empty_df(index=self.stock.values.index, columns=self.stock.values.columns.values, fill_value=1)
        sd_subset = getattr(self.service_demand, self.service_demand.map_from)
        if self.service_subset is None:
            # if there is no service subset, initial service demand modifiers equal 1"
            sd_modifier = df_for_indexing
        elif self.service_subset == 'technology':
            # calculate share of service demand by technology
            sd_subset_normal = sd_subset.groupby(level=util.ix_excl(sd_subset, ['technology'])).transform(lambda x: x / x.sum())
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
            sd_subset = sd_subset.groupby(level=util.ix_excl(sd_subset, ['technology'])).sum()
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
            # group over final energy since this is overspecified with technology utility factors if indices of both
            # technology and energy are present
            sd_subset = sd_subset.groupby(level=util.ix_excl(sd_subset, 'final_energy')).sum()
            # calculate share of service demand by technology
            sd_subset_normal = sd_subset.groupby(level=util.ix_excl(sd_subset, 'technology')).transform(
                lambda x: x / x.sum())
            # calculate service demand modifier by dividing the share of service demand by the share of stock
            sd_modifier = DfOper.divi([sd_subset_normal, self.stock.tech_subset_normal])
            # expand the dataframe to put years as columns
            sd_modifier = self.vintage_year_array_expand(sd_modifier, df_for_indexing, sd_subset)
            sd_modifier.fillna(1, inplace=True)
            # replace any 0's with 1 since zeros indicates no stock in that subset, not a service demand modifier of 0
            sd_modifier[sd_modifier == 0] = 1

        if 'final_energy' in (sd_modifier.index.names):
            # if final energy is in the original sd_modifier definition, we need to convert it to
            # a dataframe that instead has service demand modifiers by technology
            blank_modifier_main = util.empty_df(index=self.stock.tech_subset_normal.index,
                                                columns=self.stock.tech_subset_normal.columns.values, fill_value=1)
            blank_modifier_aux = util.empty_df(index=self.stock.tech_subset_normal.index,
                                               columns=self.stock.tech_subset_normal.columns.values, fill_value=0.)
            # lookup service demand modifiers for each technology in a dataframe of service demand modifiers by energy type
            for tech in self.tech_ids:
                main_energy_id = self.technologies[tech].efficiency_main.final_energy_id
                aux_energy_id = getattr(self.technologies[tech].efficiency_aux, 'final_energy_id') if hasattr(
                    self.technologies[tech].efficiency_aux, 'final_energy_id') else None
                main_utility_factor = self.technologies[tech].efficiency_main.utility_factor
                aux_utility_factor = 1 - main_utility_factor
                main_energy_indexer = util.level_specific_indexer(sd_modifier, 'final_energy', main_energy_id)
                aux_energy_indexer = util.level_specific_indexer(sd_modifier, 'final_energy', aux_energy_id)
                tech_indexer = util.level_specific_indexer(blank_modifier_main, 'technology', tech)
                blank_modifier_main.loc[tech_indexer, :] = sd_modifier.loc[main_energy_indexer, :] * main_utility_factor
                if aux_energy_id is not None:
                    blank_modifier_aux.loc[tech_indexer, :] = sd_modifier.loc[aux_energy_indexer,
                                                              :] * aux_utility_factor
                blank_modifier = DfOper.add([blank_modifier_main, blank_modifier_aux])
            sd_modifier = blank_modifier
            sd_modifier = self.vintage_year_array_expand(sd_modifier, df_for_indexing, sd_subset)
            sd_modifier.fillna(1, inplace=True)
            sd_modifier.sort_index()
            # loop through technologies and add service demand modifiers by technology-specific input (i.e. technology has a
        # a service demand modifier class)
        for tech in self.tech_ids:
            if getattr(getattr(self.technologies[tech], 'service_demand_modifier'), 'empty') is not True:
                tech_modifier = getattr(getattr(self.technologies[tech], 'service_demand_modifier'), 'values')
                tech_modifier = util.expand_multi(tech_modifier, sd_modifier.index.levels, sd_modifier.index.names,
                                                  drop_index='technology').fillna(method='bfill')
                indexer = util.level_specific_indexer(sd_modifier, 'technology', tech)
                sd_modifier.loc[indexer, :] = tech_modifier.values
        # multiply stock by service demand modifiers
        adj_stock_values = DfOper.mult([sd_modifier, self.stock.values])
        # group stock and adjusted stock values
        adj_stock_values = adj_stock_values.groupby(
            level=util.ix_excl(adj_stock_values, exclude=['vintage', 'technology'])).sum()
        stock_values = self.stock.values.groupby(
            level=util.ix_excl(self.stock.values, exclude=['vintage', 'technology'])).sum()
        # if this adds up to more or less than 1, we have to adjust the service demand modifers
        sd_mod_adjustment = DfOper.divi([stock_values, adj_stock_values])
        sd_mod_adjustment.replace([np.inf, -np.inf], 1, inplace=True)
        self.service_demand.modifier = DfOper.mult([sd_modifier, sd_mod_adjustment])

    def calc_tech_survival_functions(self, steps_per_year=1, rollover_threshold=.99):
        self.stock.spy = steps_per_year
        
        for technology in self.technologies.values():
            technology.spy = steps_per_year
            technology.set_survival_parameters()
            technology.set_survival_vintaged()
            technology.set_decay_vintaged()
            technology.set_survival_initial_stock()
            technology.set_decay_initial_stock()
        
        for technology in self.technologies.values():
            if technology.survival_vintaged[1] < rollover_threshold:
                print 'Using monthly stock rollover time steps per year = ' + str(steps_per_year*12)
                self.calc_tech_survival_functions(steps_per_year=steps_per_year*12)

    def calc_measure_survival_functions(self, measures):
        for measure in measures.values():
            measure.set_survival_parameters()
            measure.set_survival_vintaged()
            measure.set_decay_vintaged()
            measure.set_survival_initial_stock()
            measure.set_decay_initial_stock()

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
        util.replace_column_name(df, 'value')
        return df

    def convert_energy_to_service(self, other_index):
        """converts service demand input in energy terms to service terms by dividing by stock efficiencies
        up to the minimum of the current year-1 or the last year of input service demand. 
        """
        self.rollover_efficiency_outputs(other_index)
        eff = copy.deepcopy(self.stock.efficiency[other_index]['all'])
        if other_index == 'technology':
            exclude_index = ['final_energy']
        elif other_index == 'final_energy':
            exclude_index = ['technology']
        else:
            exclude_index = ['final_energy', 'technology']
        exclude_index.append('vintage')
        eff = eff.groupby(
            level=util.ix_excl(self.stock.efficiency[other_index]['all'], exclude=exclude_index)).sum()
        eff = self.stack_and_reduce_years(eff, self.min_year,
                                          self.max_year)
        if hasattr(self.energy_demand, 'map_from') and self.energy_demand.map_from != 'values':
            # if map from is 'values', then energy demand has already been projected. Reprojecting it is redundant and could cause issues with input type vs. values
            self.energy_demand.project(map_from=self.energy_demand.map_from, map_to='values',
                                       additional_drivers=self.stock.total if self.energy_demand.is_stock_dependent else None,
                                       fill_timeseries=False)

        # convert from original energy demand units to model energy demand units for service conversion, because stock efficiency has already been converted in this way
        self.energy_demand.values = util.unit_convert(self.energy_demand.values, unit_from_num=self.energy_demand.unit,
                                                      unit_to_num=cfg.cfgfile.get('case', 'energy_unit'))
        # make a copy of energy demand for use as service demand        
        self.service_demand = copy.deepcopy(self.energy_demand)

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
                exclude = ['vintage', 'technology', 'final_energy']
            elif other_index == 'technology':
                exclude = ['vintage']
            elif other_index == 'final_energy':
                exclude = ['technology', 'vintage']
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
        df = df.loc[:, max_column]
        df = pd.DataFrame(df, columns=[max_column])
        df = df.reindex(df_for_indexing.index, method='ffill')
        for year in self.years:
            df[year] = df[max_column]
        df = df.sort(axis=1)
        if hasattr(df.columns, 'levels'):
            df.columns = df.columns.droplevel()
        return df

    def project_stock(self, map_from='raw_values', service_dependent=False, override=False):
        """
        project stock moving forward includes projecting total and specified stock as well as initiating stock rollover
        If stock has already been projected, it gets reprojected if override is specified.
        """
        self.stock.vintages = self.vintages
        self.stock.years = self.years
        if not self.stock.projected or override:
            self.project_total_stock(map_from, service_dependent)
            self.project_specified_stock(map_from, service_dependent)
            self.stock.set_rollover_groups()
            self.stock.calc_annual_stock_changes()
            self.calc_tech_survival_functions()
            self.calculate_sales_shares()
            self.calculate_specified_stocks()
            self.reconcile_sales_shares()
            self.stock_rollover()
            self.stock.projected = True

    def project_total_stock(self, map_from, service_dependent=False):
        if map_from == 'values':
            current_geography = cfg.cfgfile.get('case', 'primary_geography')
            current_data_type = 'total'
            self.stock.values = self.stock.values.groupby(level=util.ix_excl(self.stock.values, 'vintage')).sum()
            self.stock.values = self.stack_and_reduce_years(self.stock.values, min(self.years), max(self.years))
        elif map_from == 'int_values':
            current_geography = cfg.cfgfile.get('case', 'primary_geography')
            current_data_type = 'total'
        else:
            current_geography = self.stock.geography
            current_data_type = self.stock.input_type
        self.stock.project(map_from=map_from, map_to='total', current_geography=current_geography,
                           additional_drivers=self.service_demand.values if service_dependent else None,
                           current_data_type=current_data_type)
        self.stock.total = util.remove_df_levels(self.stock.total, ['technology', 'final_energy'])

    def project_specified_stock(self, map_from, service_dependent):
        if map_from == 'values' or map_from == 'int_values':
            current_geography = cfg.cfgfile.get('case', 'primary_geography')
        else:
            current_geography = self.stock.geography

        if 'technology' in getattr(self.stock, map_from).index.names:
            self.stock.project(map_from=map_from, map_to='specified', current_geography=current_geography,
                               additional_drivers=self.service_demand.values if service_dependent else None,
                               fill_timeseries=False)
            # Here, we need fill timeseries backwards starting with the first specified stock using total stock as a driver
        else:
            full_names = self.stock.total.index.names + ['technology']
            full_levels = self.stock.total.index.levels + [self.tech_ids]
            index = pd.MultiIndex.from_product(full_levels, names=full_names)
            self.stock.specified = self.stock.total.reindex(index)

        self.remap_linked_stock()
        if self.stock.has_linked_specified:
            # if a stock a specified stock that is linked from other subsectors, we goup by the levels found in the stotal stock of the subsector
            linked_specified = self.stock.linked_specified.groupby(
                level=[x for x in self.stock.total.index.names if x in self.stock.linked_specified.index.names]).sum()
            self.stock.specified = self.stock.specified.sort_index()
            # expand the levels of the subsector's endogenous specified stock so that it includes all years. That's because the linked stock specification will be for all years
            full_levels = [list(self.years) if name == 'year' else list(level) for name, level in
                           zip(self.stock.specified.index.names, self.stock.specified.index.levels)]
            self.stock.specified = self.stock.specified.join(
                pd.DataFrame(index=pd.MultiIndex.from_product(full_levels, names=self.stock.specified.index.names)),
                how='outer').sort_index()
            linked_specified = linked_specified.reindex(index=self.stock.specified.index).sort_index()
            # if a technology isn't specified by a lnk to another subsector, replace it with subsector stock specification
            linked_specified = linked_specified.mask(np.isnan(linked_specified), self.stock.specified)
            # check whether this combination exceeds the total stock
            linked_specified_total_check = util.remove_df_levels(linked_specified, 'technology')
            total_check = DfOper.subt((linked_specified_total_check, self.stock.total))
            total_check[total_check < 0] = 0
            # if the total check fails, normalize all subsector inputs. We normalize the linked stocks as well.
            if total_check.sum().any() > 0:
                specified_normal = linked_specified.groupby(
                    level=util.ix_excl(self.stock.linked_specified, 'technology')).transform(lambda x: x / x.sum())
                stock_reduction = DfOper.mult((specified_normal, total_check))
                linked_specified = DfOper.subt((linked_specified, stock_reduction))
            self.stock.specified = linked_specified

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

    def measure_stock_rollover(self, measures, stock):
        """ Stock rollover function for measures"""
        measures = getattr(self, measures)
        stock = getattr(self, stock)
        self.calc_measure_survival_functions(measures)
        self.create_measure_survival_functions(measures, stock)
        self.create_measure_rollover_markov_matrices(measures, stock)
        levels = stock.rollover_group_names
        rollover_groups = stock.total.groupby(level=levels).groups
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

        for elements in rollover_groups.keys():
            specified_stock = util.df_slice(stock.specified, elements, levels)
            annual_stock_change = util.df_slice(stock.annual_stock_changes, elements, levels)
            self.rollover = Rollover(vintaged_markov_matrix=stock.vintaged_markov_matrix,
                                     initial_markov_matrix=stock.initial_markov_matrix,
                                     num_years=len(self.years), num_vintages=len(self.vintages),
                                     num_techs=len(measures.keys()), initial_stock=None,
                                     sales_share=None, stock_changes=annual_stock_change.values,
                                     specified_stock=specified_stock.values, specified_retirements=None)
            self.rollover.run()
            stock_total, stock_new, stock_replacement, retirements, retirements_natural, retirements_early, sales_record, sales_new, sales_replacement = self.rollover.return_formatted_outputs()
            stock.values.loc[elements], stock.retirements.loc[elements, 'value'] = stock_total, retirements
            stock.sales.loc[elements, 'value'] = sales_record


    def calculate_costs_measures(self):
        if hasattr(self, 'ee_stock'):
            self.ee_stock.levelized_costs = defaultdict(dict)
            self.ee_stock.levelized_costs['unspecified']['all'] = self.rollover_measure_output(
                measures='energy_efficiency_measures', measure_class='cost', measure_att='values_level',
                stock_class='ee_stock',
                stock_att='values')

            self.ee_stock.investment = defaultdict(dict)
            self.ee_stock.investment['unspecified']['all'] = self.rollover_measure_output(
                measures='energy_efficiency_measures', measure_class='cost', measure_att='values',
                stock_class='ee_stock',
                stock_att='sales')
        if hasattr(self, 'fs_stock'):
            self.fs_stock.levelized_costs = defaultdict(dict)
            self.fs_stock.levelized_costs['unspecified']['all'] = self.rollover_measure_output(
                measures='fuel_switching_measures', measure_class='cost', measure_att='values_level',
                stock_class='fs_stock',
                stock_att='values')

            self.fs_stock.investment = defaultdict(dict)
            self.fs_stock.investment['unspecified']['all'] = self.rollover_measure_output(
                measures='fuel_switching_measures', measure_class='cost', measure_att='values', stock_class='fs_stock',
                stock_att='sales')

        if hasattr(self, 'sd_stock'):
            self.sd_stock.levelized_costs = defaultdict(dict)
            self.sd_stock.levelized_costs['unspecified']['all'] = self.rollover_measure_output(
                measures='service_demand_measures', measure_class='cost', measure_att='values_level',
                stock_class='sd_stock',
                stock_att='values')

            self.sd_stock.investment = defaultdict(dict)
            self.sd_stock.investment['unspecified']['all'] = self.rollover_measure_output(
                measures='service_demand_measures', measure_class='cost', measure_att='values', stock_class='sd_stock',
                stock_att='sales')

    def rollover_measure_output(self, measures, measure_class=None, measure_att='values', stock_class=None,
                                stock_att='values',
                                stack_label=None, other_aggregate_levels=None):
        """ Produces rollover outputs for a subsector measure stock
        """

        stock_df = getattr(getattr(self, stock_class), stock_att)
        groupby_level = util.ix_excl(stock_df, ['vintage'])
        # determines index position for technology and final energy element          
        c = util.empty_df(stock_df.index, stock_df.columns.values, fill_value=0.)
        # puts technologies on the appropriate basi         
        measure_dfs = [self.reformat_measure_df(stock_df, measure, measure_class, measure_att, measure.id) for measure
                       in getattr(self, measures).values() if
                       hasattr(measure, measure_class) and getattr(getattr(measure, measure_class),
                                                                   'empty') is not True]
        if len(measure_dfs):
            measure_df = pd.concat(measure_dfs)
            c = DfOper.mult([measure_df, stock_df])
        if stack_label is not None:
            c = c.stack()
            util.replace_index_name(c, stack_label)
            util.replace_column_name(c, 'value')
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
            level_order = [cfg.cfgfile.get('case', 'primary_geography')] + util.ix_excl(measure_df, [
                cfg.cfgfile.get('case', 'primary_geography'), 'vintage']) + ['vintage']
            level_order = [x for x in level_order if x in measure_df.index.names]
            measure_df = measure_df.reorder_levels(level_order)
            return measure_df

    def create_measure_survival_functions(self, measures, stock):
        functions = defaultdict(list)
        for fun in ['survival_vintaged', 'survival_initial_stock', 'decay_vintaged', 'decay_initial_stock']:
            for measure in measures.values():
                functions[fun].append(getattr(measure, fun))
            setattr(stock, fun, pd.DataFrame(np.array(functions[fun]).T, columns=measures.keys()))

    def create_tech_survival_functions(self):
        functions = defaultdict(list)
        for fun in ['survival_vintaged', 'survival_initial_stock', 'decay_vintaged', 'decay_initial_stock']:
            for tech_id in self.tech_ids:
                technology = self.technologies[tech_id]
                functions[fun].append(getattr(technology, fun))
            setattr(self.stock, fun, pd.DataFrame(np.array(functions[fun]).T, columns=self.tech_ids))

    def create_rollover_markov_matrices(self):
        vintaged_markov = util.create_markov_vector(self.stock.decay_vintaged.values, self.stock.survival_vintaged.values)
        self.stock.vintaged_markov_matrix = util.create_markov_matrix(vintaged_markov, len(self.tech_ids), len(self.years), self.stock.spy)

        initial_markov = util.create_markov_vector(self.stock.decay_initial_stock.values, self.stock.survival_initial_stock.values)
        self.stock.initial_markov_matrix = util.create_markov_matrix(initial_markov, len(self.tech_ids), len(self.years), self.stock.spy)

    def create_measure_rollover_markov_matrices(self, measures, stock):
        vintaged_markov = util.create_markov_vector(stock.decay_vintaged.values, stock.survival_vintaged.values)
        stock.vintaged_markov_matrix = util.create_markov_matrix(vintaged_markov, len(measures.keys()), len(self.years))

        initial_markov = util.create_markov_vector(stock.decay_initial_stock.values, stock.survival_initial_stock.values)
        stock.initial_markov_matrix = util.create_markov_matrix(initial_markov, len(measures.keys()), len(self.years))

    def format_specified_stock(self):
        """ formats specified stock and linked specified stocks from other subsectors
        overwrites specified stocks with linked specified stocks"""
        self.stock.specified = util.remove_df_elements(self.stock.specified, cfg.cfgfile.get('data_identifiers', 'all'), 'technology')
        needed_levels = self.stock.rollover_group_levels + [self.tech_ids] + [self.years]
        needed_names = self.stock.rollover_group_names + ['technology'] + ['year']
        groupby_levels = [x for x in self.stock.specified.index.names if x not in needed_names]
        if len(groupby_levels) > 0:
            self.stock.specified = self.stock.specified.groupby(level=util.ix_excl(self.stock.specified, exclude=groupby_levels)).sum()
        index = pd.MultiIndex.from_product(needed_levels, names=needed_names)
        self.stock.specified = self.stock.specified.groupby(level=self.stock.specified.index.names).sum()
        self.stock.specified = self.stock.specified.reindex(index=index).sort_index()
        self.stock.specified = self.stock.specified.unstack(level='technology')

    def remap_linked_stock(self):
        """remap stocks specified in linked subsectors """
        df_concat = self.linked_stock.values()
        if len(df_concat) > 0:
            self.stock.linked_specified = pd.concat(df_concat, axis=0)
            total = util.remove_df_levels(self.stock.total, 'technology')
            self.stock.remap(map_from='linked_specified', map_to='linked_specified', drivers=total,
                             current_geography=cfg.cfgfile.get('case', 'primary_geography'), current_data_type='total',
                             time_index=self.years)
            self.stock.has_linked_specified = True
        else:
            self.stock.has_linked_specified = False

    def additional_service_demand_drivers(self, stock_dependent=False, service_dependent=False):
        """ create a list of additional drivers from linked subsectors """
        additional_drivers = []
        if len(self.linked_service_demand_drivers):
            linked_service_demand_drivers = []
            for driver in self.linked_service_demand_drivers.values():
                linked_service_demand_drivers.append(driver)
            linked_driver = 1 - DfOper.add(linked_service_demand_drivers)
            additional_drivers.append(linked_driver)
        if stock_dependent:
            if len(additional_drivers):
                additional_drivers.append(self.stock.total)
            else:
                additional_drivers = self.stock.total
        if service_dependent:
            if len(additional_drivers):
                additional_drivers.append(self.service_demand.values)
            else:
                additional_drivers = self.service_demand.values
        if len(additional_drivers) == 0:
            additional_drivers = None
        return additional_drivers

    def project_service_demand(self, map_from='raw_values', stock_dependent=False):
        self.service_demand.vintages = self.vintages
        self.service_demand.years = self.years
        if map_from == 'raw_values':
            current_geography = self.service_demand.geography
        else:
            current_geography = cfg.cfgfile.get('case', 'primary_geography')
        self.service_demand.project(map_from=map_from, map_to='values', current_geography=current_geography,
                                    additional_drivers=self.additional_service_demand_drivers(stock_dependent))

    def project_energy_demand(self, map_from='raw_values', stock_dependent=False, service_dependent=False):
        self.energy_demand.vintages = self.vintages
        self.energy_demand.years = self.years
        if map_from == 'raw_values':
            current_geography = self.energy_demand.geography
        else:
            current_geography = cfg.cfgfile.get('case', 'primary_geography')
        self.energy_demand.project(map_from=map_from, map_to='values', current_geography=current_geography,
                                   additional_drivers=self.additional_service_demand_drivers(stock_dependent,
                                                                                             service_dependent))

    def calculate_sales_shares(self):
        for tech in self.tech_ids:
            technology = self.technologies[tech]
            technology.calculate_sales_shares('reference_sales_shares')
            technology.calculate_sales_shares('sales_shares')

    def calculate_specified_stocks(self):
        for technology in self.technologies.values():
            technology.calculate_specified_stocks()

    def reconcile_sales_shares(self):
        needed_sales_share_levels = self.stock.rollover_group_levels + [self.years]
        needed_sales_share_names = self.stock.rollover_group_names + ['vintage']
        for technology in self.technologies.values():
            technology.reconcile_sales_shares('sales_shares', needed_sales_share_levels, needed_sales_share_names)
            technology.reconcile_sales_shares('reference_sales_shares', needed_sales_share_levels,
                                              needed_sales_share_names)

    def calculate_total_sales_share(self, elements, levels):
        ss_measure = self.helper_calc_sales_share(elements, levels, reference=False)
        space_for_reference = 1 - np.sum(ss_measure, axis=1)
        ss_reference = self.helper_calc_sales_share(elements, levels, reference=True,
                                                    space_for_reference=space_for_reference)
        # return SalesShare.normalize_array(ss_reference+ss_measure, retiring_must_have_replacement=True)
        # todo make retiring_must_have_replacement true after all data has been put in db
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
                    # technology sales share dataframe may not have all elements of stock dataframe
                    if any([element not in sales_share.values.index.levels[
                        util.position_in_index(sales_share.values, level)] for element, level in
                            zip(elements, levels)]):
                        continue
                    ss_array[:, repl_index, reti_index] += util.df_slice(sales_share.values, elements, levels).values
            ss_array = SalesShare.scale_reference_array_to_gap(ss_array, space_for_reference)
        else:
            for tech_id in self.tech_ids:
                for sales_share in self.technologies[tech_id].sales_shares.values():
                    repl_index = tech_lookup[sales_share.demand_tech_id]
                    reti_index = tech_lookup[
                        sales_share.replaced_demand_tech_id] if sales_share.replaced_demand_tech_id is not None and tech_lookup.has_key(
                        sales_share.replaced_demand_tech_id) else slice(
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

    def tech_to_energy(self, df, tech_class):
        """
            reformats a dataframe with a technology index to one with a final energy index
            based on a lookup of the final_energy_id by technology class (i.e. aux_efficiency will provide the aux energy type id)
        """
        df = df.copy()
        rename_dict = {}
        for tech in self.technologies.keys():
            if hasattr(getattr(self.technologies[tech], tech_class), 'final_energy_id'):
                rename_dict[tech] = getattr(getattr(self.technologies[tech], tech_class), 'final_energy_id')
            else:
                # if no energy type exists for the technology class, put in 9999 as placeholder
                rename_dict[tech] = 9999
        index = df.index
        tech_position = index.names.index('technology')
        index.set_levels(
            [[rename_dict.get(item, item) for item in names] if i == tech_position else names for i, names in
             enumerate(index.levels)], inplace=True)
        util.replace_index_name(df, 'final_energy', 'technology')
        df = df.reset_index().groupby(df.index.names).sum()
        df = util.remove_df_elements(df, 9999, 'final_energy')
        return df

    def stock_rollover(self):
        """ Stock rollover function."""
        self.format_specified_stock()
        self.create_tech_survival_functions()
        self.create_rollover_markov_matrices()
        levels = self.stock.rollover_group_names
        rollover_groups = self.stock.total.groupby(level=levels).groups
        full_levels = self.stock.rollover_group_levels + [self.technologies.keys()] + [
            [self.vintages[0] - 1] + self.vintages]
        full_names = self.stock.rollover_group_names + ['technology', 'vintage']
        columns = self.years
        index = pd.MultiIndex.from_product(full_levels, names=full_names)
        self.stock.values = util.empty_df(index=index, columns=pd.Index(columns, dtype='object'))
        self.stock.values_new = copy.deepcopy(self.stock.values)
        self.stock.values_replacement = copy.deepcopy(self.stock.values)
        self.stock.values_normal = copy.deepcopy(self.stock.values)
        full_levels = self.stock.rollover_group_levels + [self.technologies.keys()] + [self.vintages]
        index = pd.MultiIndex.from_product(full_levels, names=full_names)
        self.stock.retirements = util.empty_df(index=index, columns=['value'])
        self.stock.retirements_early = copy.deepcopy(self.stock.retirements)
        self.stock.retirements_natural = copy.deepcopy(self.stock.retirements)
        self.stock.sales = util.empty_df(index=index, columns=['value'])
        self.stock.sales_new = copy.deepcopy(self.stock.sales)
        self.stock.sales_replacement = copy.deepcopy(self.stock.sales)

        for elements in rollover_groups.keys():
            elements = util.ensure_tuple(elements)
            sales_share = self.calculate_total_sales_share(elements, levels)  # group is not necessarily the same for this other dataframe
            self.sales_share = sales_share
            if np.any(np.isnan(sales_share)):
                raise ValueError('Sales share has NaN values in subsector ' + str(self.id))

            initial_total = util.df_slice(self.stock.total, elements, levels).values[0]
            initial_stock = DemandStock.calc_initial_shares(initial_total=initial_total, transition_matrix=sales_share[0], num_years=len(self.years))

            specified_stock = self.stock.format_specified_stock(elements, levels)

            annual_stock_change = util.df_slice(self.stock.annual_stock_changes, elements, levels)

            self.rollover = Rollover(vintaged_markov_matrix=self.stock.vintaged_markov_matrix,
                                     initial_markov_matrix=self.stock.initial_markov_matrix,
                                     num_years=len(self.years), num_vintages=len(self.vintages),
                                     num_techs=len(self.tech_ids), initial_stock=initial_stock,
                                     sales_share=sales_share, stock_changes=annual_stock_change.values,
                                     specified_stock=specified_stock.values, specified_retirements=None,
                                     steps_per_year=self.stock.spy)
                                     
            self.rollover.run()
            stock, stock_new, stock_replacement, retirements, retirements_natural, retirements_early, sales_record, sales_new, sales_replacement = self.rollover.return_formatted_outputs()
            self.stock.values.loc[elements], self.stock.values_new.loc[elements], self.stock.values_replacement.loc[
                elements] = stock, stock_new, stock_replacement
            self.stock.retirements.loc[elements, 'value'], self.stock.retirements_natural.loc[elements, 'value'], \
            self.stock.retirements_early.loc[elements, 'value'] = retirements, retirements_natural, retirements_early
            self.stock.sales.loc[elements, 'value'], self.stock.sales_new.loc[elements, 'value'], \
            self.stock.sales_replacement.loc[elements, 'value'] = sales_record, sales_new, sales_replacement
        self.stock_normalize(levels)
        self.fuel_switch_stock_calc()
        self.financial_stock()

    def determine_need_for_aux_efficiency(self):
        """ determines whether auxiliary efficiency calculations are necessary. Used to avoid unneccessary calculations elsewhere """
        utility_factor = []
        for technology in self.technologies.values():
            if technology.efficiency_main.utility_factor == 1:
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
        # normalization of technology stocks (i.e. % by vintage/year)
        self.stock.values_normal_tech = self.stock.values.groupby(
            level=util.ix_excl(self.stock.values, ['vintage'])).transform(lambda x: x / x.sum()).fillna(0)
        self.stock.values_efficiency_main = copy.deepcopy(self.stock.values)

        # this section normalizes stocks used for efficiency calculations. There is a different process if the stock
        # has technologies that use multiple energy types. If it does, it must keep separate dataframes for main and auxiliary efficiency
        self.determine_need_for_aux_efficiency()
        if self.stock.aux:
            self.stock.values_efficiency_aux = copy.deepcopy(self.stock.values)
        for technology in self.technologies.keys():
            technology_class = self.technologies[technology]
            indexer = util.level_specific_indexer(self.stock.values_efficiency_main, 'technology', technology)
            self.stock.values_efficiency_main.loc[indexer, :] = self.stock.values_efficiency_main.loc[indexer,:] * technology_class.efficiency_main.utility_factor
            self.stock.values_efficiency_main.loc[indexer, 'final_energy'] = technology_class.efficiency_main.final_energy_id
            if self.stock.aux:
                self.stock.values_efficiency_aux.loc[indexer, :] = self.stock.values.loc[indexer, :] * (
                    1 - technology_class.efficiency_main.utility_factor)
                if hasattr(technology_class.efficiency_aux, 'final_energy_id'):
                    self.stock.values_efficiency_aux.loc[
                        indexer, 'final_energy'] = technology_class.efficiency_aux.final_energy_id
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
            level=util.ix_excl(self.stock.values_efficiency, ['final_energy', 'technology', 'vintage'])).transform(
            lambda x: x / x.sum()).fillna(0)
        self.stock.values_efficiency_normal_tech = self.stock.values_efficiency.groupby(
            level=util.ix_excl(self.stock.values_efficiency, ['final_energy', 'vintage'])).transform(
            lambda x: x / x.sum()).fillna(0)
        self.stock.values_efficiency_normal_energy = self.stock.values_efficiency.groupby(
            level=util.ix_excl(self.stock.values_efficiency, ['technology', 'vintage'])).transform(
            lambda x: x / x.sum()).fillna(0)

    def set_energy_as_index(self, df):
        """ takes a column with an energy id and makes it an index level """
        df = df.set_index('final_energy', append=True)
        df = df.swaplevel('vintage', 'final_energy')
        util.replace_index_name(df, 'final_energy')
        return df

    def financial_stock(self):
        """
        Calculates the amount of stock based on sales and technology book life
        instead of physical decay
        """
        for tech in self.technologies.values():
            # creates binary matrix across years and vintages for a technology based on its book life
            tech.book_life_matrix = util.book_life_df(tech.book_life, self.vintages, self.years)
            # creates a linear decay of initial stock
            tech.initial_book_life_matrix = util.initial_book_life_df(tech.book_life, self.vintages, self.years)
        # reformat the book_life_matrix dataframes to match the stock dataframe
        # creates a list of formatted tech dataframes and concatenates them
        tech_dfs = [self.reformat_tech_df(self.stock.sales, tech, tech_class=None, tech_att='book_life_matrix', id=tech.id) for
                    tech in self.technologies.values()]
        tech_df = pd.concat(tech_dfs)
        # initial_stock_df uses the stock values dataframe and removes vintagesot
        initial_stock_df = self.stock.values[min(self.years)]
        # formats tech dfs to match stock df
        initial_tech_dfs = [self.reformat_tech_df(initial_stock_df, tech, tech_class=None, tech_att='initial_book_life_matrix',
                            id=tech.id) for tech in self.technologies.values()]
        initial_tech_df = pd.concat(initial_tech_dfs)
        # stock values in any year equals vintage sales multiplied by book life
        self.stock.values_financial_new = DfOper.mult([self.stock.sales_new, tech_df])
        self.stock.values_financial_replacement = DfOper.mult([self.stock.sales_replacement, tech_df])
        # initial stock values in any year equals stock.values multiplied by the initial tech_df
        initial_values_financial_new = DfOper.mult([self.stock.values_new, initial_tech_df])
        initial_values_financial_replacement = DfOper.mult([self.stock.values_replacement, initial_tech_df])
        # sum normal and initial stock values
        self.stock.values_financial_new = DfOper.add([self.stock.values_financial_new, initial_values_financial_new])
        self.stock.values_financial_replacement = DfOper.add([self.stock.values_financial_replacement, initial_values_financial_replacement])

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
        self.stock.levelized_costs['fuel_switching']['new'] = self.rollover_output(tech_class='fuel_switch_cost', tech_att='values_level', stock_att='values_fuel_switch')

        self.stock.investment['capital']['new'] = self.rollover_output(tech_class='capital_cost_new', tech_att='values', stock_att='sales_new')
        self.stock.investment['capital']['replacement'] = self.rollover_output(tech_class='capital_cost_replacement', tech_att='values', stock_att='sales_replacement')
        self.stock.investment['installation']['new'] = self.rollover_output(tech_class='installation_cost_new', tech_att='values', stock_att='sales_new')
        self.stock.investment['installation']['replacement'] = self.rollover_output(tech_class='installation_cost_replacement', tech_att='values', stock_att='sales_replacement')
        self.stock.investment['fuel_switching']['all'] = self.rollover_output(tech_class='fuel_switch_cost', tech_att='values', stock_att='sales_fuel_switch')

    def remove_extra_subsector_attributes(self):
        if hasattr(self, 'stock'):
            delete_list = ['values_financial_new', 'values_financial_replacement', 'values_new',
                           'values_replacement', 'sales_new', 'sales_replacement','sales_fuel_switch']
            for att in delete_list:
                if hasattr(self.stock, att):
                    delattr(self.stock, att)

    def rollover_efficiency_outputs(self, other_index=None):
        """
        Calculate rollover efficiency outputs for the whole stock or stock groups by final energy and technology.
        Efficiency values are all stock-weighted by indexed inputs. Ex. if the other_index input equals 'all', multiplying
        these efficiency values by total service demand would equal total energy. 
        """
        if other_index is not None:
            index = util.ensure_iterable_and_not_string(other_index)
        else:
            index = util.ensure_iterable_and_not_string(['all', 'technology', 'final_energy'])
        index.append('all')
        self.stock.efficiency = defaultdict(dict)
        for element in index:
            if element == 'technology':
                aggregate_level = None
                values_normal = 'values_efficiency_normal_tech'
            elif element == 'final_energy':
                aggregate_level = None
                values_normal = 'values_efficiency_normal_energy'
            elif element == 'all':
                aggregate_level = None
                values_normal = 'values_efficiency_normal'
            elif element == 'total':
                aggregate_level = 'technology'
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
        it to technologies based on technology share. This is used to calculate the additional
        costs of fuel switching for applicable technologies.
        Ex. an EV might have a fuel switching cost that represents the cost of a home charger that is incurred only
        when the charger is installed. 
        """
        fuel_switch_sales = copy.deepcopy(self.stock.sales)
        fuel_switch_retirements = copy.deepcopy(self.stock.retirements)
        for technology in self.technologies.values():
            indexer = util.level_specific_indexer(fuel_switch_sales, 'technology', technology.id)
            fuel_switch_sales.loc[indexer, 'final_energy'] = technology.efficiency_main.final_energy_id
            fuel_switch_retirements.loc[indexer, 'final_energy'] = technology.efficiency_main.final_energy_id
        fuel_switch_sales = fuel_switch_sales.set_index('final_energy', append=True)
        fuel_switch_sales = fuel_switch_sales.swaplevel('vintage', 'final_energy')
        util.replace_index_name(fuel_switch_sales, 'final_energy')
        fuel_switch_retirements = fuel_switch_retirements.set_index('final_energy', append=True)
        fuel_switch_retirements = fuel_switch_retirements.swaplevel('vintage', 'final_energy')
        util.replace_index_name(fuel_switch_retirements, 'final_energy')
        # TODO check that these work!!
        fuel_switch_sales_energy = fuel_switch_sales.groupby(
            level=util.ix_excl(fuel_switch_sales, 'technology')).transform(lambda x: x.sum())
        fuel_switch_retirements_energy = fuel_switch_retirements.groupby(
            level=util.ix_excl(fuel_switch_retirements, 'technology')).transform(lambda x: x.sum())
        new_energy_sales = DfOper.subt([fuel_switch_sales_energy, fuel_switch_retirements_energy])
        new_energy_sales_share_by_technology = fuel_switch_sales.groupby(
            level=util.ix_excl(fuel_switch_sales, 'technology')).transform(lambda x: x / x.sum())
        new_energy_sales_share_by_technology[new_energy_sales_share_by_technology < 0] = 0
        new_energy_sales_by_technology = DfOper.mult([new_energy_sales_share_by_technology, new_energy_sales])

        fuel_switch_sales_share = DfOper.divi([new_energy_sales_by_technology, fuel_switch_sales]).groupby(
            level=util.ix_excl(fuel_switch_sales, 'technology')).sum()
        fuel_switch_sales_share = util.remove_df_levels(fuel_switch_sales_share, 'final_energy')
        self.stock.sales_fuel_switch = DfOper.mult([self.stock.sales, fuel_switch_sales_share])
        self.stock.values_fuel_switch = DfOper.mult([self.stock.values, fuel_switch_sales_share])

    def calculate_parasitic(self):
        """ 
        calculates parasitic energy demand   
        
        """
        self.parasitic_energy = self.rollover_output(tech_class='parasitic_energy', tech_att='values',
                                                     stock_att='values')

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
        self.reformat_service_demand()

    def calculate_output_specified_stocks(self):
        """ calculates specified stocks for use in subsectors with linked technologies
        """
        self.output_specified_stocks = {}
        stock = self.stock.values.groupby(level=util.ix_excl(self.stock.values, 'vintage')).sum()
        stock = stock.stack()
        util.replace_index_name(stock, 'year')
        stock = pd.DataFrame(stock, columns=['value'])
        for technology in self.technologies.values():
            if technology.linked_id is not None:
                indexer = util.level_specific_indexer(stock, 'technology', technology.id)
                tech_values = pd.DataFrame(stock.loc[indexer, :], columns=['value'])
                util.replace_index_label(tech_values, {technology.id: technology.linked_id}, 'technology')
                self.output_specified_stocks[technology.linked_id] = tech_values * technology.stock_link_ratio

    def calculate_service_impact(self):
        """ 
        calculates a normalized service impact for linked technology stocks as a function 
        of demand tech service link data and subsector service link impact specifications.
        
        ex. 
        service efficiency of clothes washing stock for the water heating subsector =
        (1- clothes washing service_demand_share of water heating) +
        (normalized stock service efficiency of clothes washers (i.e. efficiency of hot water usage) * service_demand_share)
        
        This vector can then be multiplied by clothes washing service demand to create an additional driver for water heating         
        
        """
        stock_df = copy.deepcopy(getattr(self.stock, 'values_normal'))
        groupby_level = util.ix_excl(stock_df, ['vintage'])
        stock_rollover_groups = stock_df.groupby(level=groupby_level).groups
        # determines index position for technology and final energy element          
        for id in self.service_links:
            c = copy.deepcopy(stock_df)
            link = self.service_links[id]
            for tech in self.technologies:
                tech_links = self.technologies[tech].service_links
                tech_link = tech_links[id] if tech_links.has_key(id) and tech_links[id].empty is not True else False
                if tech_link is not False:
                    tech_link.values = util.expand_multi(tech_link.values, stock_df.index.levels,
                                                         stock_df.index.names, drop_index=['technology']).fillna(
                        method='bfill')
                    for elements in stock_rollover_groups.keys():
                        elements = util.ensure_tuple(elements)
                        # removes the tech element for technology dataframe indexer
                        tech_elements = util.tuple_subset(elements, groupby_level, ['technology'])
                        # if the technology service efficiency data is not empty, we multiply the normalized stock by
                        # the technology service efficiency. Otherwise we do nothing, which is equivalent to saying
                        # the technology service efficiency is 1.
                        c.loc[elements] = tech_link.values.loc[tech_elements].values * stock_df.loc[elements].values
            # sum over technology and vintage to get a total stock service efficiency
            link.values = c.groupby(level=util.ix_excl(c, ['vintage', 'technology'])).sum()
            # normalize stock service efficiency to calibration year
            values = link.values.as_matrix()
            calibration_values = link.values[link.year].as_matrix()
            calibration_values = np.resize(calibration_values,
                                           (calibration_values.shape[0], len(link.values.columns.values)))
            new_values = 1 - values / calibration_values
            link.new_values = new_values
            # calculate weighted after service efficiency as a function of service demand share
            new_values = (link.service_demand_share * new_values)
            link.values = pd.DataFrame(new_values, link.values.index, link.values.columns.values)

    def reformat_service_demand(self):
        """
        format service demand with year index once calculations are complete
        """
        if 'year' not in self.service_demand.values.index.names:
            self.service_demand.values = pd.DataFrame(self.service_demand.values.stack(), columns=['value'])
            util.replace_index_name(self.service_demand.values, 'year')

    def rollover_output(self, tech_class=None, tech_att='values', stock_att=None,
                        stack_label=None, other_aggregate_levels=None, efficiency=False):
        """ Produces rollover outputs for a subsector stock based on the tech_att class, att of the class, and the attribute of the stock
        ex. to produce levelized costs for all new vehicles, it takes the capital_costs_new class, the 'values_level' attribute, and the 'values'
        attribute of the stock
        """
        stock_df = getattr(self.stock, stock_att)
        groupby_level = util.ix_excl(stock_df, ['vintage'])
        # determines index position for technology and final energy element          
        c = util.empty_df(stock_df.index, stock_df.columns.values, fill_value=0.)
        # puts technologies on the appropriate basis
        tech_class = util.put_in_list(tech_class)  
        tech_dfs = []
        for tech_class in tech_class:
            tech_dfs += ([self.reformat_tech_df(stock_df, tech, tech_class, tech_att, tech.id, efficiency) for tech in
                        self.technologies.values() if
                            hasattr(getattr(tech, tech_class), tech_att) and getattr(tech, tech_class).empty is not True])       
        if len(tech_dfs):
            tech_df = pd.concat(tech_dfs)
            # TODO get rid of reindex by using multindex operation
            tech_df = tech_df.reorder_levels([x for x in stock_df.index.names if x in tech_df.index.names])
            tech_df = tech_df.sort()
            # TODO figure a better way
#            tech_df = util.expand_multi(tech_df, stock_df.index.levels, stock_df.index.names).fillna(method='bfill')
            c = DfOper.mult((tech_df, stock_df), expandable=(True, False), collapsible=(False, True))
        else:
            util.empty_df(stock_df.index, stock_df.columns.values, 0.)

        if stack_label is not None:
            c = c.stack()
            util.replace_index_name(c, stack_label)
            util.replace_column_name(c, 'value')
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
        if 'technology' not in tech_df.index.names:
            tech_df['technology'] = id
            tech_df.set_index('technology', append=True, inplace=True)
        if efficiency is True and 'final_energy' not in tech_df.index.names:
            final_energy_id = getattr(getattr(tech, tech_class), 'final_energy_id')
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
        all_energy = DfOper.mult([self.stock.efficiency['all']['all'], self.service_demand.modifier, self.service_demand.values])
#        all_energy = all_energy.groupby(level=util.ix_excl(all_energy, ['vintage'])).sum()
        self.energy_forecast = DfOper.add([all_energy, self.parasitic_energy])
        self.energy_forecast = pd.DataFrame(self.energy_forecast.stack())
        util.replace_index_name(self.energy_forecast, 'year')
        util.replace_column_name(self.energy_forecast, 'value')
        self.energy_forecast = util.remove_df_elements(self.energy_forecast, 9999, 'final_energy')

