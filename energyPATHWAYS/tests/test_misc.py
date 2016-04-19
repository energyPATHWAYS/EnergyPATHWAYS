import unittest as ut
import energyPATHWAYS as ep
from energyPATHWAYS.util import *
from energyPATHWAYS.data_models.misc import Shape


class MiscTest(ut.TestCase):

    @classmethod
    def setUpClass(cls):
        d = os.path.dirname(os.path.realpath(__file__))
        cfgfile_path = os.path.join(d, 'test_config.INI')
        custom_pint_definitions_path = os.path.join(d, 'unit_defs.txt')
        ep.config.initialize_config(cfgfile_path, custom_pint_definitions_path)

        # we don't want any errant cached Shpaes (e.g. ones that have been processed for a different primary
        # geography) to confuse our test results, so we always process Shapes from scratch here.
        Shape._use_disk_cache = False

    def test_load_shape(self):
        shape_1 = Shape.get(1)
        shape_7 = Shape.get(7)

        # test properties
        self.assertEqual(shape_1.name, 'system load')
        self.assertEqual(shape_7.name, 'hydro')

        # test raw_values
        self.assertEqual(shape_1.raw_values.index.names, [u'nerc region', u'weather_datetime'])
        self.assertAlmostEqual(shape_1.raw_values.sum().value, 4388852681, delta=1.0)

        self.assertEqual(sorted(shape_7.raw_values.index.names),
                         sorted([u'us', u'dispatch_constraint_type', u'week']))
        self.assertAlmostEqual(shape_7.raw_values.sum().value, 36.217518, delta=0.0001)

        # test values
        self.assertEqual(len(shape_1.values), 8760)
        self.assertAlmostEqual(shape_1.values.sum().value, 1.0, delta=0.001)
        # this assumes that the primary_geography is 'us' in your configuration
        self.assertEqual(sorted(shape_1.values.index.names),
                         sorted([u'us', u'timeshift_type', u'weather_datetime']))
        start_date_both = '2011-01-01 00:00:00-05:00'
        self.assertEqual(str(shape_1.values.index[0][2]), start_date_both)
        end_date_both = '2011-12-31 23:00:00-05:00'
        self.assertEqual(str(shape_1.values.index[8759][2]), end_date_both)

        self.assertEqual(len(shape_7.values), 26280)
        # in general normalized year values will sum to ~1.0 as shape 1 did above, but there is an exception where we
        # don't normalize energy constraints, which is why the sum for the hydro shape is so much larger
        self.assertAlmostEqual(shape_7.values.sum().value, 5834.7, delta=0.01)
        # this assumes that the primary_geography is 'us' in your configuration
        self.assertEqual(sorted(shape_7.values.index.names),
                         sorted([u'us', u'dispatch_constraint_type', u'timeshift_type', u'weather_datetime']))
        self.assertEqual(str(shape_7.values.index[0][3]), start_date_both)
        self.assertEqual(str(shape_7.values.index[26279][3]), end_date_both)
