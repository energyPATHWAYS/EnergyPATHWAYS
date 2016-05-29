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
import shape
from datetime import datetime
# from supply import Supply
import smtplib
from profilehooks import timecall



 


class PathwaysModel(object):
    """
    Highest level classification of the definition of an energy system.
    Includes the primary geography of the energy system (i.e. country name) as well as the author.
    """
    def __init__(self, cfgfile_path, custom_pint_definitions_path=None, name=None, author=None):
        self.cfgfile_path = cfgfile_path
        self.custom_pint_definitions_path = custom_pint_definitions_path
        self.model_config(cfgfile_path, custom_pint_definitions_path)
        self.name = cfg.cfgfile.get('case', 'scenario') if name is None else name
        self.author = cfg.cfgfile.get('case', 'author') if author is None else author      
        self.scenario_dict = dict(zip(util.sql_read_table('Scenarios','id', return_iterable=True, is_active=True),
                                  util.sql_read_table('Scenarios','name', return_iterable=True, is_active=True)))
        self.outputs = Output()
        self.geography = cfg.cfgfile.get('case', 'primary_geography')
        

    def model_config(self, cfgfile_path, custom_pint_definitions_path):
        cfg.init_cfgfile(cfgfile_path)
        cfg.init_db()
        cfg.path = custom_pint_definitions_path
        cfg.init_pint(custom_pint_definitions_path)
        cfg.init_geo()
        cfg.init_date_lookup()
        cfg.init_outputs_id_map()

    def configure_energy_system(self):
        print 'configuring energy system'
        self.demand = Demand(self.cfgfile_path, self.custom_pint_definitions_path)
        self.supply = Supply(os.path.join(os.getcwd(),'outputs'),self.cfgfile_path, self.custom_pint_definitions_path)
        self.configure_demand()
        self.configure_supply()

    def populate_energy_system(self):
        self.populate_demand_system()
        self.populate_supply_system()
    
    def populate_shapes(self):
        print 'processing shapes'
        if shape.shapes.rerun:
            shape.shapes.create_empty_shapes()
            shape.shapes.initiate_active_shapes()
            shape.shapes.process_active_shapes()

    def populate_measures(self, scenario_id):
        self.scenario_id = scenario_id
        self.scenario = self.scenario_dict[self.scenario_id]
        self.demand_case_id = util.sql_read_table('Scenarios','demand_case',id=self.scenario_id)
        self.populate_demand_measures()
        self.supply_case_id = util.sql_read_table('Scenarios','supply_case',id=self.scenario_id)
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
#            print 'reading energy system data for the %s sector' %sector.name
            for subsector in sector.subsectors.values():
                print '    '+subsector.name
                subsector.add_energy_system_data()
            sector.precursor_dict()

    def populate_supply_system(self):
        self.supply.add_nodes()

    def populate_demand_measures(self):
        for sector in self.demand.sectors.values():
            #            print 'reading %s measures' %sector.name
            for subsector in sector.subsectors.values():
                subsector.add_measures(self.demand_case_id)
        
    def populate_supply_measures(self):
        self.supply.add_measures(self.supply_case_id)

    def calculate_demand_only(self):
        self.demand.calculate_demand()
        print "aggregating demand results"
        self.demand.aggregate_results()
    
    def calculate_supply(self):
        self.supply.initial_calculate()     
        self.supply.calculate_loop()
        self.supply.final_calculate()
             
    def pass_results_to_supply(self):
        for sector in self.demand.sectors.values():
             sector.aggregate_subsector_energy_for_supply_side()
        self.demand.aggregate_sector_energy_for_supply_side()
        self.supply.demand_object = self.demand
        
    def pass_results_to_demand(self):
        print "calculating link to supply"
        self.demand.link_to_supply(self.supply.emissions_demand_link, self.supply.demand_emissions_rates, self.supply.energy_demand_link, self.supply.cost_demand_link)
    
    def calculate_combined_results(self):
        print "calculating combined emissions results"
        self.calculate_combined_emissions_results()
        print "calculating combined cost results"
        self.calculate_combined_cost_results()
        print "calculating combined energy results"
        self.calculate_combined_energy_results()
    
    def export_results(self):
        for attribute in dir(self.outputs):
            if isinstance(getattr(self.outputs,attribute), pd.DataFrame):
                result_df = getattr(self.outputs, attribute)
                keys = [self.scenario.upper(),str(datetime.now().replace(second=0,microsecond=0))]
                names = ['SCENARIO','TIMESTAMP']
                for key, name in zip(keys,names):
                    result_df = pd.concat([result_df],keys=[key],names=[name])
                ExportMethods.writeobj(attribute,result_df, os.path.join(os.getcwd(),'combined_outputs'), append_results=True)
        for attribute in dir(self.demand.outputs):
            if isinstance(getattr(self.demand.outputs,attribute), pd.DataFrame):
                result_df = self.demand.outputs.return_cleaned_output(attribute)
                keys = [self.scenario.upper(),str(datetime.now().replace(second=0,microsecond=0))]
                names = ['SCENARIO','TIMESTAMP']
                for key, name in zip(keys,names):
                    result_df = pd.concat([result_df],keys=[key],names=[name])
                ExportMethods.writeobj(attribute,result_df, os.path.join(os.getcwd(),'demand_outputs'), append_results=True)
        for attribute in dir(self.supply.outputs):
            if isinstance(getattr(self.supply.outputs,attribute), pd.DataFrame):
                result_df = self.supply.outputs.return_cleaned_output(attribute)
                keys = [self.scenario.upper(),str(datetime.now().replace(second=0,microsecond=0))]
                names = ['SCENARIO','TIMESTAMP']
                for key, name in zip(keys,names):
                    result_df = pd.concat([result_df],keys=[key],names=[name])
                ExportMethods.writeobj(attribute,result_df, os.path.join(os.getcwd(),'supply_outputs'), append_results=True)
        
    def calculate_combined_cost_results(self):
        #calculate and format export costs
        cost_unit = cfg.cfgfile.get('case','currency_year_id') + " " + cfg.cfgfile.get('case','currency_name')
        if self.supply.export_costs is not None:
            setattr(self.outputs,'export_costs',self.supply.export_costs)
            self.export_costs_df = self.outputs.return_cleaned_output('export_costs')
            del self.outputs.export_costs
            util.replace_index_name(self.export_costs_df, 'FINAL_ENERGY','SUPPLY_NODE_EXPORT')
            keys = ["EXPORT","SUPPLY"]
            names = ['EXPORT/DOMESTIC', "SUPPLY/DEMAND"]
            for key,name in zip(keys,names):
                self.export_costs_df = pd.concat([self.export_costs_df],keys=[key],names=[name])
            self.export_costs_df.columns = [cost_unit.upper()]  
        else:
            self.export_costs_df = None
        #calculate and format emobodied supply costs
        self.embodied_energy_costs_df = self.demand.outputs.return_cleaned_output('demand_embodied_energy_costs')
        self.embodied_energy_costs_df.columns = [cost_unit.upper()]  
#        del self.demand.outputs.demand_embodied_energy_costs
        keys = ["DOMESTIC","SUPPLY"]
        names = ['EXPORT/DOMESTIC', "SUPPLY/DEMAND"]
        for key,name in zip(keys,names):
           self.embodied_energy_costs_df = pd.concat([self.embodied_energy_costs_df],keys=[key],names=[name])       
        #calculte and format direct demand costs      
        self.demand_costs_df= self.demand.outputs.return_cleaned_output('levelized_costs') 
        levels_to_keep = [x.upper() for x in cfg.output_combined_levels]
        levels_to_keep = [x for x in levels_to_keep if x in self.demand_costs_df.index.names]
        self.demand_costs_df= self.demand_costs_df.groupby(level=levels_to_keep).sum()
#        del self.demand.outputs.levelized_costs
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
#        util.replace_index_name(self.outputs.costs, self.geography.upper() +'_EARNED', self.geography.upper() +'_SUPPLY')
#        util.replace_index_name(self.outputs.costs, self.geography.upper() +'_CONSUMED', self.geography.upper())
        self.outputs.costs[self.outputs.costs<0]=0
        self.outputs.costs= self.outputs.costs[self.outputs.costs[cost_unit.upper()]!=0]
#        self.outputs.costs.sort(inplace=True)       

    
        
    def calculate_combined_emissions_results(self):
        #calculate and format export emissions
        if self.supply.export_emissions is not None:
            setattr(self.outputs,'export_emissions',self.supply.export_emissions)
            if 'supply_geography' not in cfg.output_combined_levels:
                util.remove_df_levels(self.outputs.export_emissions,self.geography +'_supply')
            self.export_emissions_df = self.outputs.return_cleaned_output('export_emissions')
            del self.outputs.export_emissions
            util.replace_index_name(self.export_emissions_df, 'FINAL_ENERGY','SUPPLY_NODE_EXPORT')
            keys = ["EXPORT","SUPPLY"]
            names = ['EXPORT/DOMESTIC', "SUPPLY/DEMAND"]
            for key,name in zip(keys,names):
                self.export_emissions_df = pd.concat([self.export_emissions_df],keys=[key],names=[name])
        else:
            self.export_emissions_df = None
       #calculate and format emobodied supply emissions
        self.embodied_emissions_df = self.demand.outputs.return_cleaned_output('demand_embodied_emissions')
#        del self.demand.outputs.demand_embodied_emissions
        keys = ["DOMESTIC","SUPPLY"]
        names = ['EXPORT/DOMESTIC', "SUPPLY/DEMAND"]
        for key,name in zip(keys,names):
           self.embodied_emissions_df = pd.concat([self.embodied_emissions_df],keys=[key],names=[name])       
        #calculte and format direct demand emissions        
        self.direct_emissions_df= self.demand.outputs.return_cleaned_output('demand_direct_emissions')  
#        del self.demand.outputs.demand_direct_emissions
        keys = ["DOMESTIC","DEMAND"]
        names = ['EXPORT/DOMESTIC', "SUPPLY/DEMAND"]
        for key,name in zip(keys,names):
            self.direct_emissions_df = pd.concat([self.direct_emissions_df],keys=[key],names=[name])   
        if 'supply_geography' in cfg.output_combined_levels:
            keys = self.direct_emissions_df.index.get_level_values(self.geography.upper()).values
            names = self.geography.upper() +'_SUPPLY'
            self.direct_emissions_df[names] = keys
            self.direct_emissions_df.set_index(names,append=True,inplace=True)
#        levels_to_keep = cfg.output_levels      
#        levels_to_keep = [x.upper() for x in levels_to_keep]
#        levels_to_keep += names + [self.geography.upper() +'_SUPPLY', 'SUPPLY_NODE']
        keys = ['EXPORTED', 'SUPPLY-SIDE', 'DEMAND-SIDE']
        names = ['EMISSIONS TYPE']
        self.outputs.emissions = util.df_list_concatenate([self.export_emissions_df, self.embodied_emissions_df, self.direct_emissions_df],keys=keys,new_names = names)
#        util.replace_index_name(self.outputs.emissions, "ENERGY","FINAL_ENERGY")
        util.replace_index_name(self.outputs.emissions, self.geography.upper() +'_EMITTED', self.geography.upper() +'_SUPPLY')
        util.replace_index_name(self.outputs.emissions, self.geography.upper() +'_CONSUMED', self.geography.upper())
        self.outputs.emissions= self.outputs.emissions[self.outputs.emissions['VALUE']!=0]
        emissions_unit = cfg.cfgfile.get('case','mass_unit')
        self.outputs.emissions.columns = [emissions_unit.upper()]
        
#        self.outputs.emissions.sort(inplace=True)        
            
    def calculate_combined_energy_results(self):
         self.embodied_energy = self.demand.outputs.return_cleaned_output('demand_embodied_energy')
         self.embodied_energy = self.embodied_energy[self.embodied_energy ['VALUE']!=0]
         self.final_energy = self.demand.outputs.return_cleaned_output('energy')
         self.final_energy = self.final_energy[self.final_energy.index.get_level_values('YEAR')>=int(cfg.cfgfile.get('case','current_year'))]  
         self.embodied_energy['ENERGY ACCOUNTING'] = 'EMBODIED'
         self.final_energy['ENERGY ACCOUNTING'] = 'FINAL'
         self.embodied_energy.set_index('ENERGY ACCOUNTING',append=True,inplace=True)
         self.final_energy.set_index('ENERGY ACCOUNTING',append=True,inplace=True)
    #         self.outputs.energy = pd.concat([self.embodied_energy, self.final_energy],keys=['DROP'],names=['DROP'])
         for name in [x for x in self.embodied_energy.index.names if x not in self.final_energy.index.names]:
             self.final_energy[name] = "N/A"
             self.final_energy.set_index(name,append=True,inplace=True)
         self.final_energy = self.final_energy.groupby(level=self.embodied_energy.index.names).sum()
         self.final_energy = self.final_energy.reorder_levels(self.embodied_energy.index.names)
         self.outputs.energy = pd.concat([self.embodied_energy,self.final_energy])
         self.outputs.energy= self.outputs.energy[self.outputs.energy['VALUE']!=0]
         energy_unit = cfg.cfgfile.get('case','energy_unit')
         self.outputs.energy.columns = [energy_unit.upper()]
