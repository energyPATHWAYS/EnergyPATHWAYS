F__author__ = 'Ben Haley & Ryan Jones'

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

class PathwaysModel(object):
    """
    Highest level classification of the definition of an energy system.
    """
    def __init__(self, scenario_id, api_run=False):
        self.scenario_id = scenario_id
        self.api_run = api_run
        self.scenario = cfg.scenario_dict[self.scenario_id]
        self.demand_case_id = util.sql_read_table('Scenarios', 'demand_case', id=self.scenario_id)
        self.supply_case_id = util.sql_read_table('Scenarios', 'supply_case', id=self.scenario_id)
        self.outputs = Output()
        self.demand = Demand()
        self.supply = Supply(self.scenario, demand_object=self.demand)
        self.demand_solved, self.supply_solved = False, False

    def run(self, scenario_id, solve_demand, solve_supply, save_models, append_results):
        try:
            if solve_demand:
                self.calculate_demand(save_models)
            
            if not append_results:
                self.remove_old_results()
            if hasattr(self, 'demand_solved') and self.demand_solved and not self.api_run:
                self.export_result_to_csv('demand_outputs')

            if solve_supply:
                self.calculate_supply(save_models)

            if hasattr(self, 'supply_solved') and self.supply_solved:
                self.supply.calculate_supply_outputs()
                self.pass_supply_results_back_to_demand()
                self.calculate_combined_results()
                if self.api_run:
                    self.export_results_to_db()
                else:
                    self.export_result_to_csv('supply_outputs')
                    self.export_result_to_csv('combined_outputs')
        except:
            # pickle the model in the event that it crashes
            with open(os.path.join(cfg.workingdir, str(scenario_id) + '_model_error.p'), 'wb') as outfile:
                pickle.dump(self, outfile, pickle.HIGHEST_PROTOCOL)
            raise

    def calculate_demand(self, save_models):
        logging.info('Configuring energy system demand')

        self.demand.add_subsectors()
        self.demand.add_measures(self.demand_case_id)
        self.demand.calculate_demand()
        logging.info("Aggregating demand results")
        self.demand.aggregate_results()
        self.demand_solved = True
        if save_models:
            with open(os.path.join(cfg.workingdir, str(self.scenario_id) + '_model.p'), 'wb') as outfile:
                pickle.dump(self, outfile, pickle.HIGHEST_PROTOCOL)

    def calculate_supply(self, save_models):
        if not self.demand_solved:
            raise ValueError('demand must be solved first before supply')
        logging.info('Configuring energy system supply')

        self.supply.add_nodes()
        self.supply.add_measures(self.supply_case_id)
        self.supply.initial_calculate()
        self.supply.calculate_loop()
        self.supply.final_calculate()
        self.supply.concatenate_annual_costs()
        self.supply.calculate_capacity_utilization()
        self.supply_solved = True
        if save_models:
            with open(os.path.join(cfg.workingdir, str(self.scenario_id) + '_full_model_run.p'), 'wb') as outfile:
                pickle.dump(self, outfile, pickle.HIGHEST_PROTOCOL)

    def pass_supply_results_back_to_demand(self):
        logging.info("Calculating link to supply")
        self.demand.link_to_supply(self.supply.emissions_demand_link, self.supply.demand_emissions_rates, self.supply.energy_demand_link, self.supply.cost_demand_link)
    
    def calculate_combined_results(self):
        logging.info("Calculating combined emissions results")
        self.calculate_combined_emissions_results()
        logging.info("Calculating combined cost results")
        self.calculate_combined_cost_results()
        logging.info("Calculating combined energy results")
        self.calculate_combined_energy_results()

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
            keys = [self.scenario.upper(),str(datetime.now().replace(second=0, microsecond=0))]
            names = ['SCENARIO','TIMESTAMP']
            for key, name in zip(keys, names):
                result_df = pd.concat([result_df], keys=[key], names=[name])
            
            Output.write(result_df, attribute+'.csv', os.path.join(cfg.workingdir, result_name))

    def export_results_to_db(self):
        scenario_run_id = util.active_scenario_run_id(self.scenario_id)

        # Energy demand
        df = self.outputs.energy.groupby(level=['FINAL_ENERGY', 'YEAR']).sum()
        util.write_output_to_db(scenario_run_id, 3, df)

        # Annual costs
        df = self.outputs.costs.groupby(level=['SECTOR', 'YEAR']).sum()
        util.write_output_to_db(scenario_run_id, 4, df)

        # Annual emissions
        df = self.outputs.emissions.groupby(level=['SECTOR', 'YEAR']).sum()
        util.write_output_to_db(scenario_run_id, 5, df)

        # Electricity supply
        df = self.outputs.energy.xs('ELECTRICITY', level='FINAL_ENERGY')\
            .groupby(level=['SUPPLY_NODE', 'YEAR']).sum()
        util.write_output_to_db(scenario_run_id, 13, df)

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
#        levels_to_keep += names + [cfg.primary_geography.upper() +'_SUPPLY', 'SUPPLY_NODE']
        keys = ['EXPORTED', 'SUPPLY-SIDE', 'DEMAND-SIDE']
        names = ['COST TYPE']
        self.outputs.costs = util.df_list_concatenate([self.export_costs_df, self.embodied_energy_costs_df, self.demand_costs_df],keys=keys,new_names=names)
#        util.replace_index_name(self.outputs.costs, cfg.primary_geography.upper() +'_EARNED', cfg.primary_geography.upper() +'_SUPPLY')
#        util.replace_index_name(self.outputs.costs, cfg.primary_geography.upper() +'_CONSUMED', cfg.primary_geography.upper())
        self.outputs.costs[self.outputs.costs<0]=0
        self.outputs.costs= self.outputs.costs[self.outputs.costs[cost_unit.upper()]!=0]
#        self.outputs.costs.sort(inplace=True)
        
    def calculate_combined_emissions_results(self):
        #calculate and format export emissions
        if self.supply.export_emissions is not None:
            setattr(self.outputs,'export_emissions',self.supply.export_emissions)
            if 'supply_geography' not in cfg.output_combined_levels:
                util.remove_df_levels(self.outputs.export_emissions,cfg.primary_geography +'_supply')
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
            keys = self.direct_emissions_df.index.get_level_values(cfg.primary_geography.upper()).values
            names = cfg.primary_geography.upper() +'_SUPPLY'
            self.direct_emissions_df[names] = keys
            self.direct_emissions_df.set_index(names,append=True,inplace=True)
#        levels_to_keep = cfg.output_levels      
#        levels_to_keep = [x.upper() for x in levels_to_keep]
#        levels_to_keep += names + [cfg.primary_geography.upper() +'_SUPPLY', 'SUPPLY_NODE']
        keys = ['EXPORTED', 'SUPPLY-SIDE', 'DEMAND-SIDE']
        names = ['EMISSIONS TYPE']
        self.outputs.emissions = util.df_list_concatenate([self.export_emissions_df, self.embodied_emissions_df, self.direct_emissions_df],keys=keys,new_names = names)
#        util.replace_index_name(self.outputs.emissions, "ENERGY","FINAL_ENERGY")
        util.replace_index_name(self.outputs.emissions, cfg.primary_geography.upper() +'_EMITTED', cfg.primary_geography.upper() +'_SUPPLY')
        util.replace_index_name(self.outputs.emissions, cfg.primary_geography.upper() +'_CONSUMED', cfg.primary_geography.upper())
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

    def return_io(self):
        dfs = []
        keys = self.supply.demand_sectors
        names = ['demand_sector']
        for sector in self.supply.demand_sectors:
            dfs.append(self.supply.io_dict[2050][sector])
        df = pd.concat(dfs,keys=keys,names=names)
        df = pd.concat([df]*len(keys),keys=keys,names=names,axis=1)
        for row_sector in self.supply.demand_sectors:
            for col_sector in self.supply.demand_sectors:
                if row_sector != col_sector:
                    df.loc[util.level_specific_indexer(df,'demand_sector',row_sector),util.level_specific_indexer(df,'demand_sector',col_sector,axis=1)] = 0
        self.supply.outputs.io = df
        result_df = self.supply.outputs.return_cleaned_output('io')
        keys = [self.scenario.upper(),str(datetime.now().replace(second=0,microsecond=0))]
        names = ['SCENARIO','TIMESTAMP']
        for key, name in zip(keys,names):
            result_df = pd.concat([result_df], keys=[key],names=[name])
        result_df.to_csv(os.path.join(cfg.workingdir,'supply_outputs', 'io.csv'), header=True, mode='ab')