import unittest
import energyPATHWAYS
import numpy as np
import pandas as pd
import pylab
import os
import time
from energyPATHWAYS.dispatch_classes import Dispatch
import math
import copy
from ddt import ddt, data, unpack


data_dir = os.path.join(os.getcwd(), 'test_dispatch_data')

load = pd.DataFrame.from_csv(os.path.join(data_dir, 'load.csv'))['Load 2']
load = load.values.flatten()
load*=20000000

dispatch_periods = pd.DataFrame.from_csv(os.path.join(data_dir, 'dispatch_periods.csv'))
dispatch_periods = dispatch_periods['month'].values.flatten()

pmins = np.array([0]*12)
pmaxs = np.array([5000]*12)
energy = np.array([-100000]*12)

test = Dispatch.dispatch_to_energy_budget(load, energy_budgets=energy, dispatch_periods=dispatch_periods, pmins=pmins, pmaxs=pmaxs)

pylab.plot(load)
pylab.plot(load-test)
pylab.plot(test)
