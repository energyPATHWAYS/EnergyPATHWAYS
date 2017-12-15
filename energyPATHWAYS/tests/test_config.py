from __future__ import print_function
import unittest

from energyPATHWAYS.newconfig import getParam, getParamAsBoolean, getParamAsFloat, getParamAsInt, setParam, getConfig, getConfigDict

class TestConfig(unittest.TestCase):
    def setUp(self):
        # This treats missing user config file as not an error
        getConfig(allowMissing=True)

        setParam('default_project', 'mexico')

    def test_string(self):
        project = getParam('default_project')
        print("project: ", project)

        dbpath = getParam('database_path')
        print("database_path:", dbpath)

    def test_int(self):
        year_step = getParamAsInt('year_step')
        print("year_step: %d" % year_step)

    def test_float(self):
        infl_rate = getParamAsFloat('inflation_rate')
        print("inflation_rate: %f" % infl_rate)

    def test_bool(self):
        for_gaus = getParamAsBoolean('include_foreign_gaus')
        print("include_foreign_gaus:", for_gaus)

