# -*- coding: utf-8 -*-
__author__ = 'Sam & Michael'

import unittest as ut

import mock
from energyPATHWAYS.demand import Demand
import energyPATHWAYS as ep
from energyPATHWAYS.util import *

from profile_tools import * # profile(), timer()

# Note: for now I recommend running this test with only a representative sample of subsectors active for speed reasons.
# Eventually we will be able to decouple these tests from the U.S. example database and this will no longer be a
# concern. To use the recommended subset:
# UPDATE "DemandSubsectors" SET is_active = FALSE;
# UPDATE "DemandSubsectors" SET is_active = TRUE WHERE id IN (72, 37, 10, 16);
#
# If/when you want to reset things back to the original example state, you can use:
# UPDATE "DemandSubsectors" SET is_active = TRUE;
# UPDATE "DemandSubsectors" SET is_active = FALSE WHERE id IN (13, 14, 32);

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

        # To start with, we're just testing around DemandDrivers
        # and relying on the data in the existing us example database
        self.assertEqual(len(demand.drivers), 34)

        # load up a couple of example drivers and make sure their properties and data match expectations
        # households depends on population and has an oth_index_1 but only has data for 2009
        households = demand.drivers[1]
        self.assertEqual(households.name, "households")
        self.assertEqual(households.geography_map_key.name, 'households')
        self.assertEqual(households.base_driver_id, 2)
        self.assertEqual(households.other_index_1_id, 1)
        self.assertEqual(households.raw_values.index.names, [u'census division', u'housing types', u'year'])
        self.assertEqual(households.raw_values.index.get_level_values('housing types').unique().tolist(), [28, 29, 30])
        self.assertEqual(households.raw_values.columns.values.tolist(), ['value'])
        self.assertEqual(len(households.raw_values), 27)
        self.assertEqual(households.raw_values.sum().value, 113616229.0)

        # population does not depend on anything and has no oth_indexes but has data for many years
        population = demand.drivers[2]
        self.assertEqual(population.name, "population")
        self.assertEqual(population.geography_map_key.name, 'households')
        self.assertIsNone(population.base_driver_id)
        self.assertIsNone(population.other_index_1_id)
        self.assertEqual(population.raw_values.index.names, [u'census division', u'year'])
        self.assertEqual(population.raw_values.index.get_level_values('census division').unique().tolist(), [56, 57, 58, 59, 60, 61, 62, 63, 64])
        self.assertEqual(population.raw_values.columns.values.tolist(), ['value'])
        self.assertEqual(len(population.raw_values), 459)
        self.assertEqual(population.raw_values.sum().value, 16327762200.0)

        self.assertEqual(households.base_driver, population)

        # TODO: figure out what else to assert here
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