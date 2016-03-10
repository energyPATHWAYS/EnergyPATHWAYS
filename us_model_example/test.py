# -*- coding: utf-8 -*-
"""
Created on Mon Mar 07 14:33:35 2016

@author: Ben
"""

# -*- coding: utf-8 -*-
"""
Created on Fri Mar 04 10:23:57 2016

@author: Ben
"""
import types
import copy
import numpy as np
from collections import defaultdict
from energyPATHWAYS import util
import pandas as pd
import os 
import pickle

directory = os.getcwd()


def calculate_combined_energy_results(self):
     self.embodied_energy = self.demand.outputs.return_cleaned_output('demand_embodied_energy')
     self.final_energy = self.demand.outputs.return_cleaned_output('demand_embodied_energy')
     keys = ['EMBODIED','FINAL']
     name = ['ENERGY ACCOUNTING']
     self.outputs.energy = pd.concat([self.embodied_energy,self.final_energy],keys=keys, names=name)