# -*- coding: utf-8 -*-
__author__ = 'Sam & Michael'

from ConfigParser import ConfigParser
import unittest as ut

from  energyPATHWAYS.orm import dbConf
from energyPATHWAYS.config import ConfigFromDB
from energyPATHWAYS.util import *
from energyPATHWAYS.data_models import data_source
data_source.init(dbConf.conf)

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


class ConfigTest(ut.TestCase):
    
    @classmethod
    def setUpClass(cls):
        d = os.path.dirname(os.path.realpath(__file__))
        cls.us_cfgfile_path = os.path.join(d,'../../us_model_example/configurations.INI')
        cls.us_cfg = ConfigParser()
        cls.us_cfg.read(cls.us_cfgfile_path)

    def setUp(self):
        pass # see class setup

    def tearDown(self):
        pass

    def test_config_from_db(self):
        for section in self.us_cfg.sections():
            print '[%s]' % section
            for key, value in self.us_cfg.items(section):
                print '  %s : %s' % (key, value)

    def tezt_save_config_to_db(self):
        db_cfg = ConfigFromDB()
        db_cfg.read(self.us_cfgfile_path)
        self.db_cfg.saveToDB()

    def test_load_config_from_db(self):
        db_cfg = ConfigFromDB()
        db_cfg.loadFromDB()
        for section in self.us_cfg.sections():
            print '[%s]' % section
            for key, value in self.us_cfg.items(section):
                db_value = db_cfg.get(section,key)
                assert(value == db_value)



if __name__ == '__main__':
    ut.main()