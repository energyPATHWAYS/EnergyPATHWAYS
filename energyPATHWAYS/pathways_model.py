__author__ = 'Ben Haley & Ryan Jones'

import os
from demand import Demand
import util
from outputs import Output
import cPickle as pickle
import time
import shutil
import config as cfg
from supply import Supply
import pandas as pd
import logging
import shape
from datetime import datetime
# from supply import Supply
import smtplib
from profilehooks import timecall
import pdb
from scenario_loader import Scenario
import copy
import numpy as np

class PathwaysModel(object):
    """
    Highest level classification of the definition of an energy system.
    """
    def __init__(self, scenario_id, api_run=False):
        self.scenario_id = scenario_id
        self.scenario = Scenario(self.scenario_id)
        self.api_run = api_run
        self.outputs = Output()
        self.demand = Demand(self.scenario)
        self.supply = None
        self.demand_solved, self.supply_solved = False, False

    def run(self, scenario_id, solve_demand, solve_supply, load_demand, load_supply, export_results, save_models, append_results):
        try:
            if solve_demand and not (load_demand or load_supply):
                self.calculate_demand(save_models)
            
            if not append_results:
                self.remove_old_results()

            if self.demand_solved and export_results and not self.api_run:
                self.export_result_to_csv('demand_outputs')

            if solve_supply and not load_supply:
                if load_demand:
                    # if we are loading the demand, we are changing the supply measures and want to reload our scenarios
                    self.scenario = Scenario(self.scenario_id)
                self.supply = Supply(self.scenario, demand_object=self.demand)
                self.calculate_supply(save_models)

            if self.supply_solved and export_results:
                self.supply.calculate_supply_outputs()
                self.pass_supply_results_back_to_demand()
                self.calculate_combined_results()
                if self.api_run:
                    self.export_results_to_db()
                else:
                    self.export_result_to_csv('supply_outputs')
                    self.export_result_to_csv('combined_outputs')
                    self.export_io()
        except:
            # pickle the model in the event that it crashes
            if save_models:
                Output.pickle(self, file_name=str(scenario_id) + cfg.model_error_append_name, path=cfg.workingdir)
            raise

    def calculate_demand(self, save_models):
        self.demand.setup_and_solve()
        self.demand_solved = True
        if cfg.output_payback == 'true':
            if self.demand.d_all_energy_demand_payback is not None:
                self.calculate_d_payback()
                self.calculate_d_payback_energy()
        if save_models:
            Output.pickle(self, file_name=str(self.scenario_id) + cfg.demand_model_append_name, path=cfg.workingdir)

    def calculate_supply(self, save_models):
        if not self.demand_solved:
            raise ValueError('demand must be solved first before supply')
        logging.info('Configuring energy system supply')
        self.supply.add_nodes()
        self.supply.add_measures()
        self.supply.initial_calculate()
        self.supply.calculated_years = []
        self.supply.calculate_loop(self.supply.years, self.supply.calculated_years)
        self.supply.final_calculate()
        self.supply.concatenate_annual_costs()
        self.supply.calculate_capacity_utilization()
        self.supply_solved = True
        if save_models:
            Output.pickle(self, file_name=str(self.scenario_id) + cfg.full_model_append_name, path=cfg.workingdir)
            # we don't need the demand side object any more, so we can remove it to save drive space
            if os.path.isfile(os.path.join(cfg.workingdir, str(self.scenario_id) + cfg.demand_model_append_name)):
                os.remove(os.path.join(cfg.workingdir, str(self.scenario_id) + cfg.demand_model_append_name))

    def pass_supply_results_back_to_demand(self):
        logging.info("Calculating link to supply")
        self.demand.link_to_supply(self.supply.emissions_demand_link, self.supply.demand_emissions_rates, self.supply.energy_demand_link, self.supply.cost_demand_link)
        if cfg.output_tco == 'true':
            if hasattr(self,'d_energy_tco'):
                self.demand.link_to_supply_tco(self.supply.emissions_demand_link, self.supply.demand_emissions_rates, self.supply.cost_demand_link) 
            else:
               print  "demand side has not been run with tco outputs set to 'true'"
        if cfg.output_payback == 'true':
            if hasattr(self,'demand.d_all_energy_demand_payback'):
                self.demand.link_to_supply_payback(self.supply.emissions_demand_link, self.supply.demand_emissions_rates, self.supply.cost_demand_link) 
            else:
               print  "demand side has not been run with tco outputs set to 'true'"
    
    def calculate_combined_results(self):
        logging.info("Calculating combined emissions results")
        self.calculate_combined_emissions_results()
        logging.info("Calculating combined cost results")
        self.calculate_combined_cost_results()
        logging.info("Calculating combined energy results")
        self.calculate_combined_energy_results()
        if cfg.output_tco == 'true':
            if self.demand.d_energy_tco is not None:
                self.calculate_tco()
        if cfg.output_payback == 'true':
            if self.demand.d_all_energy_demand_payback is not None:
                self.calculate_payback()

    def remove_old_results(self):
        folder_names = ['combined_outputs', 'demand_outputs', 'supply_outputs', 'dispatch_outputs']
        for folder_name in folder_names:
            folder = os.path.join(cfg.workingdir, folder_name)
            if os.path.isdir(folder):
                shutil.rmtree(folder)

    def export_result_to_csv(self, result_name):
        if result_name=='combined_outputs':
            res_obj = self.outputs
        elif result_name=='demand_outputs':
            res_obj = self.demand.outputs
        elif result_name=='supply_outputs':
            res_obj = self.supply.outputs
        else:
            raise ValueError('result_name not recognized')

        for attribute in dir(res_obj):
            if not isinstance(getattr(res_obj, attribute), pd.DataFrame):
                continue

            result_df = getattr(res_obj, 'return_cleaned_output')(attribute)
            keys = [self.scenario.name.upper(), str(datetime.now().replace(second=0, microsecond=0))]
            names = ['SCENARIO','TIMESTAMP']
            for key, name in zip(keys, names):
                result_df = pd.concat([result_df], keys=[key], names=[name])

            if attribute == 'hourly_dispatch_results':
                # Special case for hourly dispatch results where we want to write them outside of supply_outputs
                Output.write(result_df, attribute + '.csv', os.path.join(cfg.workingdir, 'dispatch_outputs'))
            else:
                Output.write(result_df, attribute+'.csv', os.path.join(cfg.workingdir, result_name))

    def export_results_to_db(self):
        scenario_run_id = util.active_scenario_run_id(self.scenario_id)
        # Levelized costs
        costs = self.outputs.c_costs.groupby(level=['SUPPLY/DEMAND', 'YEAR']).sum()
        util.write_output_to_db(scenario_run_id, 1, costs)

        #Energy
        energy = self.outputs.c_energy.xs('FINAL', level='ENERGY ACCOUNTING')\
            .groupby(level=['SECTOR', 'FINAL_ENERGY', 'YEAR']).sum()
        # Energy demand by sector
        util.write_output_to_db(scenario_run_id, 2, energy.groupby(level=['SECTOR', 'YEAR']).sum())
        # Residential Energy by Fuel Type
        util.write_output_to_db(scenario_run_id, 6, energy.xs('RESIDENTIAL', level='SECTOR'))
        # Commercial Energy by Fuel Type
        util.write_output_to_db(scenario_run_id, 8, energy.xs('COMMERCIAL', level='SECTOR'))
        # Transportation Energy by Fuel Type
        util.write_output_to_db(scenario_run_id, 10, energy.xs('TRANSPORTATION', level='SECTOR'))
        # Productive Energy by Fuel Type
        util.write_output_to_db(scenario_run_id, 12, energy.xs('PRODUCTIVE', level='SECTOR'))

        #Emissions
        emissions = self.outputs.c_emissions.xs('DOMESTIC', level='EXPORT/DOMESTIC')\
            .groupby(level=['SECTOR', 'FINAL_ENERGY', 'YEAR']).sum()
        emissions = util.DfOper.mult((emissions, 1-(emissions.abs()<1E-10).groupby(level='FINAL_ENERGY').all())) # get rid of noise
        # Annual emissions by sector
        util.write_output_to_db(scenario_run_id, 3, emissions.groupby(level=['SECTOR', 'YEAR']).sum())
        # Residential Emissions by Fuel Type
        util.write_output_to_db(scenario_run_id, 7, emissions.xs('RESIDENTIAL', level='SECTOR'))
        # Commercial Emissions by Fuel Type
        util.write_output_to_db(scenario_run_id, 9, emissions.xs('COMMERCIAL', level='SECTOR'))
        # Transportation Emissions by Fuel Type
        util.write_output_to_db(scenario_run_id, 11, emissions.xs('TRANSPORTATION', level='SECTOR'))
        # Productive Emissions by Fuel Type
        util.write_output_to_db(scenario_run_id, 13, emissions.xs('PRODUCTIVE', level='SECTOR'))

        # Domestic emissions per capita
        annual_emissions = self.outputs.c_emissions.xs('DOMESTIC', level='EXPORT/DOMESTIC').groupby(level=['YEAR']).sum()
        population_driver = self.demand.drivers[2].values.groupby(level='year').sum().loc[annual_emissions.index]
        population_driver.index.name = 'YEAR'
        factor = 1E6
        df = util.DfOper.divi((annual_emissions, population_driver)) * factor
        df.columns = ['TONNE PER CAPITA']
        util.write_output_to_db(scenario_run_id, 4, df)

        # Electricity supply
        electricity_node_names = [self.supply.nodes[nodeid].name.upper() for nodeid in util.flatten_list(self.supply.injection_nodes.values())]
        df = self.outputs.c_energy.xs('ELECTRICITY', level='FINAL_ENERGY')\
            .xs('EMBODIED', level='ENERGY ACCOUNTING')\
            .groupby(level=['SUPPLY_NODE', 'YEAR']).sum()
        util.write_output_to_db(scenario_run_id, 5, df.loc[electricity_node_names])

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
        keys = ["DOMESTIC","SUPPLY"]
        names = ['EXPORT/DOMESTIC', "SUPPLY/DEMAND"]
        for key,name in zip(keys,names):
           self.embodied_energy_costs_df = pd.concat([self.embodied_energy_costs_df],keys=[key],names=[name])
        #calculte and format direct demand costs
        self.demand_costs_df = self.demand.outputs.return_cleaned_output('d_levelized_costs')
        if self.demand_costs_df is not None:
            levels_to_keep = [x.upper() for x in cfg.output_combined_levels]
            levels_to_keep = [x for x in levels_to_keep if x in self.demand_costs_df.index.names]
            self.demand_costs_df = self.demand_costs_df.groupby(level=levels_to_keep).sum()
            keys = ["DOMESTIC","DEMAND"]
            names = ['EXPORT/DOMESTIC', "SUPPLY/DEMAND"]
            for key,name in zip(keys,names):
                self.demand_costs_df = pd.concat([self.demand_costs_df],keys=[key],names=[name])
        keys = ['EXPORTED', 'SUPPLY-SIDE', 'DEMAND-SIDE']
        names = ['COST TYPE']
        self.outputs.c_costs = util.df_list_concatenate([self.export_costs_df, self.embodied_energy_costs_df, self.demand_costs_df],keys=keys,new_names=names)
        self.outputs.c_costs[self.outputs.c_costs<0]=0
        self.outputs.c_costs= self.outputs.c_costs[self.outputs.c_costs[cost_unit.upper()]!=0]
        
    def calculate_tco(self):
#        self.embodied_emissions_df = self.demand.outputs.return_cleaned_output('demand_embodied_emissions_tco')
#        del self.demand.outputs.demand_embodied_emissions
        #calculte and format direct demand emissions        
#        self.direct_emissions_df = self.demand.outputs.return_cleaned_output('demand_direct_emissions')
##        del self.demand.outputs.demand_direct_emissions
#        emissions = util.DfOper.add([self.embodied_emissions_df,self.direct_emissions_df])
#         #calculate and format export costs
        cost_unit = cfg.cfgfile.get('case','currency_year_id') + " " + cfg.cfgfile.get('case','currency_name')
        initial_vintage = min(cfg.supply_years)
        supply_side_df = self.demand.outputs.demand_embodied_energy_costs_tco
        supply_side_df = supply_side_df[supply_side_df.index.get_level_values('vintage')>=initial_vintage]
        demand_side_df = self.demand.d_levelized_costs_tco
        demand_side_df.columns = ['value']
        demand_side_df = demand_side_df[demand_side_df.index.get_level_values('vintage')>=initial_vintage]
        service_demand_df = self.demand.d_service_demand_tco
        service_demand_df = service_demand_df[service_demand_df.index.get_level_values('vintage')>=initial_vintage]
        keys = ['SUPPLY-SIDE', 'DEMAND-SIDE']
        names = ['COST TYPE']
        self.outputs.c_tco = pd.concat([util.DfOper.divi([supply_side_df,util.remove_df_levels(service_demand_df,'unit')]),
                                        util.DfOper.divi([demand_side_df,util.remove_df_levels(service_demand_df,'unit')])],
                                        keys=keys,names=names) 
        self.outputs.c_tco = self.outputs.c_tco.replace([np.inf,np.nan],0)
        self.outputs.c_tco[self.outputs.c_tco<0]=0        
        for sector in self.demand.sectors.values():
          for subsector in sector.subsectors.values():
                if hasattr(subsector,'service_demand') and hasattr(subsector,'stock'):
                    indexer = util.level_specific_indexer(self.outputs.c_tco,'subsector',subsector.id)
                    self.outputs.c_tco.loc[indexer,'unit'] = subsector.service_demand.unit.upper()
        self.outputs.c_tco = self.outputs.c_tco.set_index('unit',append=True)
        self.outputs.c_tco.columns = [cost_unit.upper()]
        self.outputs.c_tco= self.outputs.c_tco[self.outputs.c_tco[cost_unit.upper()]!=0]
        self.outputs.c_tco = self.outputs.return_cleaned_output('c_tco')
        
        
        
    def calculate_payback(self):
#        self.embodied_emissions_df = self.demand.outputs.return_cleaned_output('demand_embodied_emissions_tco')
#        del self.demand.outputs.demand_embodied_emissions
        #calculte and format direct demand emissions        
#        self.direct_emissions_df = self.demand.outputs.return_cleaned_output('demand_direct_emissions')
##        del self.demand.outputs.demand_direct_emissions
#        emissions = util.DfOper.add([self.embodied_emissions_df,self.direct_emissions_df])
#         #calculate and format export costs
        cost_unit = cfg.cfgfile.get('case','currency_year_id') + " " + cfg.cfgfile.get('case','currency_name')
        initial_vintage = min(cfg.supply_years)
        supply_side_df = self.demand.outputs.demand_embodied_energy_costs_payback
        supply_side_df = supply_side_df[supply_side_df.index.get_level_values('vintage')>=initial_vintage]
        supply_side_df = supply_side_df[supply_side_df.index.get_level_values('year')>=initial_vintage]
        supply_side_df = supply_side_df.sort_index()
        demand_side_df = self.demand.d_annual_costs_payback
        demand_side_df.columns = ['value']
        demand_side_df = demand_side_df[demand_side_df.index.get_level_values('vintage')>=initial_vintage]
        demand_side_df = demand_side_df[demand_side_df.index.get_level_values('year')>=initial_vintage]
        demand_side_df = demand_side_df.reindex(supply_side_df.index).sort_index()
        sales_df = copy.deepcopy(self.demand.outputs.d_sales)
        util.replace_index_name(sales_df,'vintage','year')
        sales_df = sales_df[sales_df.index.get_level_values('vintage')>=initial_vintage]     
        sales_df = util.add_and_set_index(sales_df,'year',cfg.supply_years)
        sales_df.index = sales_df.index.reorder_levels(supply_side_df.index.names)
        sales_df = sales_df.reindex(supply_side_df.index).sort_index()
        keys = ['SUPPLY-SIDE', 'DEMAND-SIDE']
        names = ['COST TYPE']
        self.outputs.c_payback = pd.concat([util.DfOper.divi([supply_side_df, sales_df]), util.DfOper.divi([demand_side_df, sales_df])],keys=keys,names=names)
        self.outputs.c_payback = self.outputs.c_payback[np.isfinite(self.outputs.c_payback.values)]        
        self.outputs.c_payback = self.outputs.c_payback.replace([np.inf,np.nan],0)
        for sector in self.demand.sectors.values():
          for subsector in sector.subsectors.values():
                if hasattr(subsector,'stock') and subsector.sub_type!='link':
                    indexer = util.level_specific_indexer(self.outputs.c_payback,'subsector',subsector.id)
                    self.outputs.c_payback.loc[indexer,'unit'] = subsector.stock.unit.upper()
        self.outputs.c_payback = self.outputs.c_payback.set_index('unit', append=True)
        self.outputs.c_payback.columns = [cost_unit.upper()]
        self.outputs.c_payback['lifetime_year'] = self.outputs.c_payback.index.get_level_values('year')-self.outputs.c_payback.index.get_level_values('vintage')+1    
        self.outputs.c_payback = self.outputs.c_payback.set_index('lifetime_year',append=True)
        self.outputs.c_payback = util.remove_df_levels(self.outputs.c_payback,'year')
        self.outputs.c_payback = self.outputs.c_payback.groupby(level = [x for x in self.outputs.c_payback.index.names if x !='lifetime_year']).transform(lambda x: x.cumsum())
        self.outputs.c_payback = self.outputs.c_payback[self.outputs.c_payback[cost_unit.upper()]!=0]
        self.outputs.c_payback = self.outputs.return_cleaned_output('c_payback')
        
        
    def calculate_d_payback(self):
        cost_unit = cfg.cfgfile.get('case','currency_year_id') + " " + cfg.cfgfile.get('case','currency_name')
        initial_vintage = min(cfg.supply_years)
        demand_side_df = self.demand.d_annual_costs_payback
        demand_side_df.columns = ['value']
        demand_side_df = demand_side_df[demand_side_df.index.get_level_values('vintage')>=initial_vintage]
        demand_side_df = demand_side_df[demand_side_df.index.get_level_values('year')>=initial_vintage]
        sales_df = copy.deepcopy(self.demand.outputs.d_sales)
        util.replace_index_name(sales_df,'vintage','year')
        sales_df = sales_df[sales_df.index.get_level_values('vintage')>=initial_vintage]     
        sales_df = util.add_and_set_index(sales_df,'year',cfg.supply_years)
        sales_df.index = sales_df.index.reorder_levels(demand_side_df.index.names)
        sales_df = sales_df.reindex(demand_side_df.index).sort_index()
        self.demand.outputs.d_payback = util.DfOper.divi([demand_side_df, sales_df])
        self.demand.outputs.d_payback = self.demand.outputs.d_payback[np.isfinite(self.demand.outputs.d_payback.values)]        
        self.demand.outputs.d_payback = self.demand.outputs.d_payback.replace([np.inf,np.nan],0)
        for sector in self.demand.sectors.values():
          for subsector in sector.subsectors.values():
                if hasattr(subsector,'stock') and subsector.sub_type!='link':
                    indexer = util.level_specific_indexer(self.demand.outputs.d_payback,'subsector',subsector.id)
                    self.demand.outputs.d_payback.loc[indexer,'unit'] = subsector.stock.unit.upper()
        self.demand.outputs.d_payback = self.demand.outputs.d_payback.set_index('unit', append=True)
        self.demand.outputs.d_payback.columns = [cost_unit.upper()]
        self.demand.outputs.d_payback['lifetime_year'] = self.demand.outputs.d_payback.index.get_level_values('year')-self.demand.outputs.d_payback.index.get_level_values('vintage')+1    
        self.demand.outputs.d_payback = self.demand.outputs.d_payback.set_index('lifetime_year',append=True)
        self.demand.outputs.d_payback = util.remove_df_levels(self.demand.outputs.d_payback,'year')
        self.demand.outputs.d_payback = self.demand.outputs.d_payback.groupby(level = [x for x in self.demand.outputs.d_payback.index.names if x !='lifetime_year']).transform(lambda x: x.cumsum())
        self.demand.outputs.d_payback = self.demand.outputs.d_payback[self.demand.outputs.d_payback[cost_unit.upper()]!=0]
        self.demand.outputs.d_payback = self.demand.outputs.return_cleaned_output('d_payback')
   
    def calculate_d_payback_energy(self):
        energy_unit = cfg.cfgfile.get('case','calculation_energy_unit')
        initial_vintage = min(cfg.supply_years)
        demand_side_df = self.demand.d_all_energy_demand_payback
        demand_side_df.columns = ['value']
        demand_side_df = demand_side_df[demand_side_df.index.get_level_values('vintage')>=initial_vintage]
        demand_side_df = demand_side_df[demand_side_df.index.get_level_values('year')>=initial_vintage]
        sales_df = copy.deepcopy(self.demand.outputs.d_sales)
        util.replace_index_name(sales_df,'vintage','year')
        sales_df = sales_df[sales_df.index.get_level_values('vintage')>=initial_vintage]     
        sales_df = util.add_and_set_index(sales_df,'year',cfg.supply_years)
#        sales_df.index = sales_df.index.reorder_levels(demand_side_df.index.names)
#        sales_df = sales_df.reindex(demand_side_df.index).sort_index()
        self.demand.outputs.d_payback_energy = util.DfOper.divi([demand_side_df, sales_df])
        self.demand.outputs.d_payback_energy = self.demand.outputs.d_payback_energy[np.isfinite(self.demand.outputs.d_payback_energy.values)]        
        self.demand.outputs.d_payback_energy = self.demand.outputs.d_payback_energy.replace([np.inf,np.nan],0)
        for sector in self.demand.sectors.values():
          for subsector in sector.subsectors.values():
                if hasattr(subsector,'stock') and subsector.sub_type!='link':
                    indexer = util.level_specific_indexer(self.demand.outputs.d_payback_energy,'subsector',subsector.id)
                    self.demand.outputs.d_payback_energy.loc[indexer,'unit'] = subsector.stock.unit.upper()
        self.demand.outputs.d_payback_energy = self.demand.outputs.d_payback_energy.set_index('unit', append=True)
        self.demand.outputs.d_payback_energy.columns = [energy_unit.upper()]
        self.demand.outputs.d_payback_energy['lifetime_year'] = self.demand.outputs.d_payback_energy.index.get_level_values('year')-self.demand.outputs.d_payback_energy.index.get_level_values('vintage')+1    
        self.demand.outputs.d_payback_energy = self.demand.outputs.d_payback_energy.set_index('lifetime_year',append=True)
        self.demand.outputs.d_payback_energy = util.remove_df_levels(self.demand.outputs.d_payback_energy,'year')
        self.demand.outputs.d_payback_energy = self.demand.outputs.d_payback_energy.groupby(level = [x for x in self.demand.outputs.d_payback_energy.index.names if x !='lifetime_year']).transform(lambda x: x.cumsum())
        self.demand.outputs.d_payback_energy = self.demand.outputs.d_payback_energy[self.demand.outputs.d_payback_energy[energy_unit.upper()]!=0]
        self.demand.outputs.d_payback_energy = self.demand.outputs.return_cleaned_output('d_payback_energy')
            
        
    def calculate_combined_emissions_results(self):
        #calculate and format export emissions
        if self.supply.export_emissions is not None:
            setattr(self.outputs,'export_emissions',self.supply.export_emissions)
            if 'supply_geography' not in cfg.output_combined_levels:
                util.remove_df_levels(self.outputs.export_emissions, cfg.primary_geography +'_supply')
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
        self.direct_emissions_df = self.demand.outputs.return_cleaned_output('demand_direct_emissions')
#        del self.demand.outputs.demand_direct_emissions
        keys = ["DOMESTIC","DEMAND"]
        names = ['EXPORT/DOMESTIC', "SUPPLY/DEMAND"]
        for key, name in zip(keys, names):
            self.direct_emissions_df = pd.concat([self.direct_emissions_df], keys=[key], names=[name])
        if cfg.primary_geography+'_supply' in cfg.output_combined_levels:
             keys = self.direct_emissions_df.index.get_level_values(cfg.primary_geography.upper()).values
             names = cfg.primary_geography.upper() +'_SUPPLY'
             self.direct_emissions_df[names] = keys
             self.direct_emissions_df.set_index(names,append=True,inplace=True)
        keys = ['EXPORTED', 'SUPPLY-SIDE', 'DEMAND-SIDE']
        names = ['EMISSIONS TYPE']
        self.outputs.c_emissions = util.df_list_concatenate([self.export_emissions_df, self.embodied_emissions_df, self.direct_emissions_df],keys=keys,new_names = names)
        util.replace_index_name(self.outputs.c_emissions, cfg.primary_geography.upper() +'-EMITTED', cfg.primary_geography.upper() +'_SUPPLY')
        util.replace_index_name(self.outputs.c_emissions, cfg.primary_geography.upper() +'-CONSUMED', cfg.primary_geography.upper())
        self.outputs.c_emissions= self.outputs.c_emissions[self.outputs.c_emissions['VALUE']!=0]
        emissions_unit = cfg.cfgfile.get('case','mass_unit')
        self.outputs.c_emissions.columns = [emissions_unit.upper()]
            
    def calculate_combined_energy_results(self):
         energy_unit = cfg.calculation_energy_unit
         if self.supply.export_costs is not None:
            setattr(self.outputs,'export_energy',self.supply.export_energy)
            self.export_energy = self.outputs.return_cleaned_output('export_energy')
            del self.outputs.export_energy
            util.replace_index_name(self.export_energy, 'FINAL_ENERGY','SUPPLY_NODE_EXPORT')
            keys = ["EXPORT","EMBODIED"]
            names = ['EXPORT/DOMESTIC', 'ENERGY ACCOUNTING']
            for key,name in zip(keys,names):
                self.export_energy = pd.concat([self.export_energy],keys=[key],names=[name])
         else:
            self.export_energy = None
         self.embodied_energy = self.demand.outputs.return_cleaned_output('demand_embodied_energy')
         self.embodied_energy = self.embodied_energy[self.embodied_energy ['VALUE']!=0]
         keys = ['DOMESTIC','EMBODIED']
         names = ['EXPORT/DOMESTIC', 'ENERGY ACCOUNTING']
         for key,name in zip(keys,names):
             self.embodied_energy = pd.concat([self.embodied_energy],keys=[key],names=[name])
         self.final_energy = self.demand.outputs.return_cleaned_output('d_energy')
         self.final_energy = self.final_energy[self.final_energy.index.get_level_values('YEAR')>=int(cfg.cfgfile.get('case','current_year'))]
         keys = ['DOMESTIC','FINAL']
         names = ['EXPORT/DOMESTIC', 'ENERGY ACCOUNTING']
         for key,name in zip(keys,names):
             self.final_energy = pd.concat([self.final_energy],keys=[key],names=[name])
    #         self.outputs.c_energy = pd.concat([self.embodied_energy, self.final_energy],keys=['DROP'],names=['DROP'])
         for name in [x for x in self.embodied_energy.index.names if x not in self.final_energy.index.names]:
             self.final_energy[name] = "N/A"
             self.final_energy.set_index(name,append=True,inplace=True)
         if self.export_energy is not None:
             for name in [x for x in self.embodied_energy.index.names if x not in self.export_energy.index.names]:
                 self.export_energy[name] = "N/A"
                 self.export_energy.set_index(name,append=True,inplace=True)
             self.export_energy = self.export_energy.groupby(level=self.embodied_energy.index.names).sum()
             self.export_energy = self.export_energy.reorder_levels(self.embodied_energy.index.names)
         self.final_energy = self.final_energy.groupby(level=self.embodied_energy.index.names).sum()
         self.final_energy = self.final_energy.reorder_levels(self.embodied_energy.index.names)
         self.outputs.c_energy = pd.concat([self.embodied_energy,self.final_energy,self.export_energy])
         self.outputs.c_energy= self.outputs.c_energy[self.outputs.c_energy['VALUE']!=0]
         self.outputs.c_energy.columns = [energy_unit.upper()]

    def export_io(self):
        io_table_write_step = int(cfg.cfgfile.get('output_detail','io_table_write_step'))
        io_table_years = sorted([min(cfg.supply_years)] + range(max(cfg.supply_years), min(cfg.supply_years), -io_table_write_step))
        df_list = []
        for year in io_table_years:
            sector_df_list = []
            keys = self.supply.demand_sectors
            name = ['sector']
            for sector in self.supply.demand_sectors:
                sector_df_list.append(self.supply.io_dict[year][sector])
            year_df = pd.concat(sector_df_list, keys=keys,names=name)
            year_df = pd.concat([year_df]*len(keys),keys=keys,names=name,axis=1)
            df_list.append(year_df)
        keys = io_table_years
        name = ['year']
        df = pd.concat(df_list,keys=keys,names=name)
        for row_sector in self.supply.demand_sectors:
            for col_sector in self.supply.demand_sectors:
                if row_sector != col_sector:
                    df.loc[util.level_specific_indexer(df,'sector',row_sector),util.level_specific_indexer(df,'sector',col_sector,axis=1)] = 0
        self.supply.outputs.io = df
        result_df = self.supply.outputs.return_cleaned_output('io')
        keys = [self.scenario.name.upper(),str(datetime.now().replace(second=0,microsecond=0))]
        names = ['SCENARIO','TIMESTAMP']
        for key, name in zip(keys,names):
            result_df = pd.concat([result_df], keys=[key],names=[name])
        Output.write(result_df, 's_io.csv', os.path.join(cfg.workingdir, 'supply_outputs'))
#        self.export_stacked_io()

    def export_stacked_io(self):
        df = copy.deepcopy(self.supply.outputs.io)
        df.index.names = [x + '_input'if x!= 'year' else x for x in df.index.names ]
        df = df.stack(level=df.columns.names).to_frame()
        df.columns = ['value']
        self.supply.outputs.stacked_io = df
        result_df = self.supply.outputs.return_cleaned_output('stacked_io')
        keys = [self.scenario.name.upper(),str(datetime.now().replace(second=0,microsecond=0))]
        names = ['SCENARIO','TIMESTAMP']
        for key, name in zip(keys,names):
            result_df = pd.concat([result_df], keys=[key],names=[name])
        Output.write(result_df, 's_stacked_io.csv', os.path.join(cfg.workingdir, 'supply_outputs'))
