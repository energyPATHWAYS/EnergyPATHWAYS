# -*- coding: utf-8 -*-
__author__ = 'Sam & Michael'

import unittest as ut

import mock
from energyPATHWAYS.demand import Demand
import energyPATHWAYS as ep
from energyPATHWAYS.util import *

from profile_tools import * # profile(), timer()

class DemandTest(ut.TestCase):
    
    @classmethod
    def setUpClass(cls):
        d = os.path.dirname(os.path.realpath(__file__))
        cfgfile_path = os.path.join(d, 'test_config.INI')
        custom_pint_definitions_path = os.path.join(d, 'unit_defs.txt')
        ep.config.initialize_config(cfgfile_path, custom_pint_definitions_path)

    def setUp(self):
        pass # see class setup

    def tearDown(self):
        pass

    def test_demand_config(self):

        with timer('Initializing demand'): # about 53s
            demand = Demand()

        print dir(demand)
        print 'demand sectors'
        print demand.sectors

        print 'service precusors'
        print demand.service_precursors

        print 'stock precursors'
        print demand.stock_precursors

        print 'subsector precursors'
        print demand.subsector_precursors

        # TODO: figure out what to assert here
        # obviously want to check for specific sectors, subsectors, measures, etc. but all are database dependent
        # Since htis is running against the US model at the moment, we can check for US-specific items.
        # Would be useful to have repr defined for Sector, SubSector, Measure, etc. so prints make more sense.

        # with timer('Running demand'): # about 80s
        #     print 'Demand calculations'
        #     demand.manage_calculations()
        #     print "aggregating demand results"
        #     demand.aggregate_results()

if __name__ == '__main__':
    ut.main()