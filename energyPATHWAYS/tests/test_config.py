# -*- coding: utf-8 -*-
__author__ = 'Sam & Michael'

import unittest as ut

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
        pass

if __name__ == '__main__':
    ut.main()