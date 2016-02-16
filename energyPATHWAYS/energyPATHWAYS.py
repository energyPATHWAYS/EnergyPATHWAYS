__author__ = 'Ben Haley & Ryan Jones'

import os
from demand import Demand
from util import ExportMethods
import util
from outputs import Output
import time
from config import cfg
from supply import Supply
import pandas as pd
# from supply import Supply

class PathwaysModel(object):
    """
    Highest level classification of the definition of an energy system.
    Includes the primary geography of the energy system (i.e. country name) as well as the author.
    """
    def __init__(self, db_path, cfgfile_path, custom_pint_definitions_path=None, name=None, author=None):
        self.model_config(db_path, cfgfile_path, custom_pint_definitions_path)
        self.name = cfg.cfgfile.get('case', 'scenario') if name is None else name
        self.author = cfg.cfgfile.get('case', 'author') if author is None else author
        self.demand = Demand()
        self.supply = Supply()
        self.outputs = Output()
        self.geography = cfg.cfgfile.get('case', 'primary_geography')
        

    def model_config(self, db_path, cfgfile_path, custom_pint_definitions_path):
        cfg.init_cfgfile(cfgfile_path)
        cfg.init_db(db_path)
        cfg.init_pint(custom_pint_definitions_path)
        cfg.init_geo()
        cfg.init_shapes()
        cfg.init_outputs_id_map()

    def configure_energy_system(self):
        print 'configuring energy system'
        self.configure_demand()
        self.configure_supply()
        cfg.init_outputs_id_map()

    def populate_energy_system(self):
        self.populate_demand_system()
        self.populate_supply_system()

    def populate_measures(self):
        self.populate_demand_measures()
        self.populate_supply_measures()

    def calculate(self):
        self.calculate_demand_only()
        self.pass_results_to_supply()
        self.calculate_supply()

    def configure_demand(self):
        """Read in and initialize data"""
        # Drivers must come first
        self.demand.add_drivers()

        # Sectors requires drivers be read in
        self.demand.add_sectors()
        for sector in self.demand.sectors.values():
            # print 'configuring the %s sector'  %sector.name
            sector.add_subsectors()
            
    def configure_supply(self):
        self.supply.add_node_list()

    def populate_demand_system(self):
        print 'remapping drivers'
        self.demand.remap_drivers()
        print 'populating energy system data'
        for sector in self.demand.sectors.values():
            print '  '+sector.name+' sector'
            # print 'reading energy system data for the %s sector' %sector.name
            for subsector in sector.subsectors.values():
                print '    '+subsector.name
                subsector.add_energy_system_data()
        self.demand.precursor_dict()

    def populate_supply_system(self):
        self.supply.add_nodes()

    def populate_demand_measures(self):
        for sector in self.demand.sectors.values():
            #            print 'reading %s measures' %sector.name
            for subsector in sector.subsectors.values():
                subsector.add_measures()
        
    def populate_supply_measures(self):      
        self.supply.add_measures()

    def calculate_demand_only(self):
        self.demand.manage_calculations()
        print "aggregating demand results"
        self.demand.aggregate_results()
    
    def calculate_supply(self):
        self.supply.calculate()        
             
    def pass_results_to_supply(self):
        for sector in self.demand.sectors.values():
             sector.aggregate_subsector_energy_for_supply_side()
        self.demand.aggregate_sector_energy_for_supply_side()
        self.supply.demand_df = self.demand.energy_demand
        
    def pass_results_to_demand(self):
        print "calculating link to supply"
        self.demand.link_to_supply(self.supply.emissions_demand_link, self.supply.demand_emissions_rates, self.supply.energy_demand_link, self.supply.cost_demand_link)
    
    def calculate_combined_results(self):
        print "calculating combined emissions results"
        self.calculate_combined_emissions_results()
        print "calculating combined cost results"
        self.calculate_combined_cost_results()
    
    def export_results(self):
        for attribute in dir(self.outputs):
            if isinstance(getattr(self.outputs,attribute),pd.DataFrame):
                result_df = getattr(self.outputs, attribute)
                ExportMethods.writeobj(attribute,result_df,os.path.join(os.getcwd(),'outputs'))
    
    def calculate_combined_cost_results(self):
        #calculate and format export costs
        setattr(self.outputs,'export_costs',self.supply.export_costs)
        self.export_costs_df = self.outputs.return_cleaned_output('export_costs')
        del self.outputs.export_costs
        util.replace_index_name(self.export_costs_df, 'FINAL_ENERGY','SUPPLY_NODE_EXPORT')
        keys = ["EXPORT","SUPPLY"]
        names = ['EXPORT/DOMESTIC', "SUPPLY/DEMAND"]
        for key,name in zip(keys,names):
            self.export_costs_df = pd.concat([self.export_costs_df],keys=[key],names=[name])
        #calculate and format emobodied supply costs
        self.embodied_energy_costs_df = self.demand.outputs.return_cleaned_output('demand_embodied_energy_costs')
        del self.demand.outputs.demand_embodied_energy_costs
        keys = ["DOMESTIC","SUPPLY"]
        names = ['EXPORT/DOMESTIC', "SUPPLY/DEMAND"]
        for key,name in zip(keys,names):
           self.embodied_energy_costs_df = pd.concat([self.embodied_energy_costs_df],keys=[key],names=[name])       
        #calculte and format direct demand emissions        
        self.demand_costs_df= self.demand.outputs.return_cleaned_output('levelized_costs')  
        del self.demand.outputs.levelized_costs
        keys = ["DOMESTIC","DEMAND"]
        names = ['EXPORT/DOMESTIC', "SUPPLY/DEMAND"]
        for key,name in zip(keys,names):
            self.demand_costs_df = pd.concat([self.demand_costs_df],keys=[key],names=[name])      
#        levels_to_keep = cfg.output_levels      
#        levels_to_keep = [x.upper() for x in levels_to_keep]
#        levels_to_keep += names + [self.geography.upper() +'_SUPPLY', 'SUPPLY_NODE']
        keys = ['EXPORTED', 'SUPPLY-SIDE', 'DEMAND-SIDE']
        names = ['COST TYPE']
        self.outputs.costs = util.df_list_concatenate([self.export_costs_df, self.embodied_energy_costs_df, self.demand_costs_df],keys=keys,new_names=names)
        util.replace_index_name(self.outputs.costs, "ENERGY","FINAL_ENERGY")
#        util.replace_index_name(self.outputs.costs, self.geography.upper() +'_EARNED', self.geography.upper() +'_SUPPLY')
#        util.replace_index_name(self.outputs.costs, self.geography.upper() +'_CONSUMED', self.geography.upper())
        self.outputs.costs[self.outputs.costs<0]=0
        self.outputs.costs= self.outputs.costs[self.outputs.costs['VALUE']!=0]
#        self.outputs.costs.sort(inplace=True)       
        
        
    
        
    def calculate_combined_emissions_results(self):
        #calculate and format export emissions
        setattr(self.outputs,'export_emissions',self.supply.export_emissions)
        self.export_emissions_df = self.outputs.return_cleaned_output('export_emissions')
        del self.outputs.export_emissions
        util.replace_index_name(self.export_emissions_df, 'FINAL_ENERGY','SUPPLY_NODE_EXPORT')
        keys = ["EXPORT","SUPPLY"]
        names = ['EXPORT/DOMESTIC', "SUPPLY/DEMAND"]
        for key,name in zip(keys,names):
            self.export_emissions_df = pd.concat([self.export_emissions_df],keys=[key],names=[name])
        #calculate and format emobodied supply emissions
        self.embodied_emissions_df = self.demand.outputs.return_cleaned_output('demand_embodied_emissions')
        del self.demand.outputs.demand_embodied_emissions
        keys = ["DOMESTIC","SUPPLY"]
        names = ['EXPORT/DOMESTIC', "SUPPLY/DEMAND"]
        for key,name in zip(keys,names):
           self.embodied_emissions_df = pd.concat([self.embodied_emissions_df],keys=[key],names=[name])       
        #calculte and format direct demand emissions        
        self.direct_emissions_df= self.demand.outputs.return_cleaned_output('demand_direct_emissions')  
        del self.demand.outputs.demand_direct_emissions
        keys = ["DOMESTIC","DEMAND"]
        names = ['EXPORT/DOMESTIC', "SUPPLY/DEMAND"]
        for key,name in zip(keys,names):
            self.direct_emissions_df = pd.concat([self.direct_emissions_df],keys=[key],names=[name])      
#        levels_to_keep = cfg.output_levels      
#        levels_to_keep = [x.upper() for x in levels_to_keep]
#        levels_to_keep += names + [self.geography.upper() +'_SUPPLY', 'SUPPLY_NODE']
        keys = ['EXPORTED', 'SUPPLY-SIDE', 'DEMAND-SIDE']
        names = ['EMISSIONS TYPE']
        self.outputs.emissions = util.df_list_concatenate([self.export_emissions_df, self.embodied_emissions_df, self.direct_emissions_df],keys=keys,new_names = names)
        util.replace_index_name(self.outputs.emissions, "ENERGY","FINAL_ENERGY")
        util.replace_index_name(self.outputs.emissions, self.geography.upper() +'_EMITTED', self.geography.upper() +'_SUPPLY')
        util.replace_index_name(self.outputs.emissions, self.geography.upper() +'_CONSUMED', self.geography.upper())
        self.outputs.emissions= self.outputs.emissions[self.outputs.emissions['VALUE']!=0]
#        self.outputs.emissions.sort(inplace=True)        
        
    
