import unittest as ut
import energyPATHWAYS as ep
import os
from energyPATHWAYS.geomapper import GeoMapper
from collections import OrderedDict
import ipdb


class GeoMapperTest(ut.TestCase):
    @classmethod
    def setUpClass(cls):
        d = os.path.dirname(os.path.realpath(__file__))
        cfgfile_path = os.path.join(d, 'test_config.INI')
        custom_pint_definitions_path = os.path.join(d, 'unit_defs.txt')
        cls.model = ep.PathwaysModel(cfgfile_path, custom_pint_definitions_path)

    def test_geography_loading(self):
        geo = GeoMapper()

        self.assertEqual(geo.geographies['electricity interconnection'], [1, 2, 3])

        self.assertEqual(geo.timezone_names[123], 'US/Alaska')
        self.assertEqual(geo.timezone_names[129], 'US/Pacific')

        self.assertEqual(geo.map_keys[0], '2015 Total Households (ESRI)')

        self.assertEqual(geo.values.index.names[0], 'electricity interconnection')

        self.assertEqual(geo.values.columns.values[0], '2015 Total Households (ESRI)')

        self.assertAlmostEqual(geo.values['2015 Total Households (ESRI)'].sum(), 120557507.0)

        self.assertEqual(len(geo.values), 155)

        #ipdb.set_trace()

