__author__ = 'Ben Haley & Ryan Jones'

import os
from demand import Demand
from util import ExportMethods
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
        self.supply.add_nodes()

    def populate_demand_system(self):
        print 'remapping drivers'
        self.demand.remap_drivers()
        print 'populating energy system data'
        for sector in self.demand.sectors.values():
            print '  '+sector.name+' sector'
            for subsector in sector.subsectors.values():
                print '    '+subsector.name
                subsector.add_energy_system_data()
        self.demand.precursor_dict()

    def populate_supply_system(self):
        self.supply.add_energy_system_data()

    def populate_demand_measures(self):
        for sector in self.demand.sectors.values():
            for subsector in sector.subsectors.values():
                subsector.add_measures()
        
    def populate_supply_measures(self):      
        self.supply.add_measures()

    def calculate_demand_only(self):
        self.demand.manage_calculations()
    
    def calculate_supply(self):
        self.supply.calculate()        
             
    def pass_results_to_supply(self):
        for sector in self.demand.sectors.values():
             sector.aggregate_subsector_energy_for_supply_side()
        self.demand.aggregate_sector_energy_for_supply_side()
        self.supply.demand_df = self.demand.energy_demand
        
    def pass_results_to_demand(self):
        self.demand.aggregate_results()
        self.demand.link_to_supply(self.supply.emissions_demand_link, self.supply.energy_demand_link, self.supply.cost_demand_link)
        
    def export_results(self, specified_directory=None):
        if specified_directory is None:
            specified_directory = os.path.join(os.getcwd())
        else:
            specified_directory = os.path.join(specified_directory)
        attributes = dir(self.demand.outputs)
        for att in attributes: 
            if isinstance(getattr(self.demand.outputs,att),pd.core.frame.DataFrame):
                output = self.demand.outputs.return_cleaned_output(att)
                ExportMethods.writedataframe(att, output,specified_directory)
