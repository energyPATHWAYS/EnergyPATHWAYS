import unittest as ut
import energyPATHWAYS as ep
from energyPATHWAYS.util import *
from energyPATHWAYS.shape import Shape as OldShape, shapes
from energyPATHWAYS.data_models.misc import Shape as NewShape
from energyPATHWAYS.data_models.data_source import fetch, fetch_as_dict
from profile_tools import timer
import ipdb
import cProfile

class MiscTest(ut.TestCase):

    @classmethod
    def setUpClass(cls):
        d = os.path.dirname(os.path.realpath(__file__))
        cfgfile_path = os.path.join(d, 'test_config.INI')
        custom_pint_definitions_path = os.path.join(d, 'unit_defs.txt')
        ep.config.initialize_config(cfgfile_path, custom_pint_definitions_path)

    def test_load_shape(self):
        with ipdb.launch_ipdb_on_exception():
            shapes.create_empty_shapes()
            shapes.data[1] = OldShape(id=1)
            shapes.activate_shape(1)
            shapes.data[7] = OldShape(id=7)
            shapes.activate_shape(7)
            shapes.initiate_active_shapes()
            shapes.process_active_shapes()

            # old_shapes = {}
            # with timer('Loading shapes with old method'):
            #     for i in range(1, 32):
            #         old_shapes[i] = OldShape(id=i)
            #         old_shapes[i].read_timeseries_data()

            #with timer('Loading shapes with new method'):
            #    new_shapes = fetch_as_dict(NewShape)
            #new_shape_1 = new_shapes[1]

            # this is just to prime loading all the raw_values for ShapesData into the DataMapper so as not to
            # bias the profile by including database access
            #fetch(NewShape, id=2)[0]
            #cProfile.runctx("new_shape_1 = fetch(NewShape, id=1)[0]", globals(), locals(), "load_shape_1.profile")
            new_shape_1 = fetch(NewShape, id=1)[0]

            name = 'system load'
            self.assertEqual(shapes.data[1].name, name)
            self.assertEqual(new_shape_1.name, name)

            # test raw_values

            index_names = [u'nerc region', u'weather_datetime']
            self.assertEqual(shapes.data[1].raw_values.index.names, index_names)
            self.assertEqual(new_shape_1.raw_values.index.names, index_names)

            sum = 4388852681
            self.assertAlmostEqual(shapes.data[1].raw_values.sum().value, sum, delta=1.0)
            self.assertAlmostEqual(new_shape_1.raw_values.sum().value, sum, delta=1.0)

            #cProfile.runctx("new_shape_7 = fetch(NewShape, id=7)[0]", globals(), locals(), "load_shape_7.profile")
            new_shape_7 = fetch(NewShape, id=7)[0]

            name = 'hydro'
            self.assertEqual(shapes.data[7].name, name)
            self.assertEqual(new_shape_7.name, name)

            index_names = sorted([u'us', u'dispatch_constraint_type', u'week'])
            self.assertEqual(sorted(shapes.data[7].raw_values.index.names), index_names)
            self.assertEqual(sorted(new_shape_7.raw_values.index.names), index_names)

            sum = 36.217518
            self.assertAlmostEqual(shapes.data[7].raw_values.sum().value, sum, delta=0.0001)
            self.assertAlmostEqual(new_shape_7.raw_values.sum().value, sum, delta=0.0001)

            # test values

            len_1 = 8760
            self.assertEqual(len(shapes.data[1].values), len_1)
            self.assertEqual(len(new_shape_1.values), len_1)

            sum_1 = 1.0
            self.assertAlmostEqual(shapes.data[1].values.sum().value, sum_1, delta=0.001)
            self.assertAlmostEqual(new_shape_1.values.sum().value, sum_1, delta=0.001)

            index_names_1 = sorted([u'us', u'timeshift_type', u'weather_datetime'])
            self.assertEqual(sorted(shapes.data[1].values.index.names), index_names_1)
            self.assertEqual(sorted(new_shape_1.values.index.names), index_names_1)

            start_date_both = '2011-01-01 00:00:00-05:00'
            self.assertEqual(str(shapes.data[1].values.index[0][2]), start_date_both)
            self.assertEqual(str(new_shape_1.values.index[0][2]), start_date_both)

            end_date_both = '2011-12-31 23:00:00-05:00'
            self.assertEqual(str(shapes.data[1].values.index[8759][2]), end_date_both)
            self.assertEqual(str(new_shape_1.values.index[8759][2]), end_date_both)

            len_7 = 26280
            self.assertEqual(len(shapes.data[7].values), len_7)
            self.assertEqual(len(new_shape_7.values), len_7)

            sum_7 = 5834.7
            self.assertAlmostEqual(shapes.data[7].values.sum().value, sum_7, delta=0.01)
            self.assertAlmostEqual(new_shape_7.values.sum().value, sum_7, delta=0.01)

            index_names_7 = sorted([u'us', u'dispatch_constraint_type', u'timeshift_type', u'weather_datetime'])
            self.assertEqual(sorted(shapes.data[7].values.index.names), index_names_7)
            self.assertEqual(sorted(new_shape_7.values.index.names), index_names_7)

            self.assertEqual(str(shapes.data[7].values.index[0][3]), start_date_both)
            self.assertEqual(str(new_shape_7.values.index[0][3]), start_date_both)

            self.assertEqual(str(shapes.data[7].values.index[26279][3]), end_date_both)
            self.assertEqual(str(new_shape_7.values.index[26279][3]), end_date_both)

            #ipdb.set_trace()