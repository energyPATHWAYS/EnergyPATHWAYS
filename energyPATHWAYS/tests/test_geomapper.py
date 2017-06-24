# -*- coding: utf-8 -*-
__author__ = 'Michael'

import unittest
import mock
import cPickle as pickle
import os
import energyPATHWAYS
from energyPATHWAYS.geomapper import GeoMapper


def load_pickle(attr_name):
    return pickle.load(open(os.path.join('test_geomapper_data', attr_name + '.p')))


def read_geography_indices(self):
    for attr in ['geographies', 'timezone_names', 'map_keys', 'geography_names', 'id_to_geography']:
        setattr(self, attr, load_pickle(attr))


def fetch_intersection_ids(self):
    return load_pickle('intersection_ids')


def fetch_geography_data(self):
    return load_pickle('geo_map')

# set up fake config; the following mystery is apparently how you create an object in python
# that can have arbitrary attributes.
# https://stackoverflow.com/questions/2280334/shortest-way-of-creating-an-object-with-arbitrary-attributes-in-python
cfg = type('', (), {})()
cfg.primary_geography_id = 3
cfg.dispatch_geography_id = 1
cfg.primary_subset_id = []
cfg.breakout_geography_id = []
cfg.dispatch_breakout_geography_id = []
cfg.default_geography_map_key = 'Households 2010 (complete count)'
cfg.include_foreign_gaus = False

mock_read_geography_indices = mock.create_autospec(GeoMapper._read_geography_indices, side_effect=read_geography_indices)
mock_fetch_intersection_ids = mock.create_autospec(GeoMapper._fetch_intersection_ids, side_effect=fetch_intersection_ids)
mock_fetch_geography_data = mock.create_autospec(GeoMapper._fetch_geography_data, side_effect=fetch_geography_data)


@mock.patch('energyPATHWAYS.geomapper.cfg', cfg)
class TestGeoMapper(unittest.TestCase):

    # Annoyingly, class-level patches are only applied to "test_*" methods, so we have to
    # re-apply class-level patches to setUp() individually
    @mock.patch('energyPATHWAYS.geomapper.GeoMapper._read_geography_indices', mock_read_geography_indices)
    @mock.patch('energyPATHWAYS.geomapper.GeoMapper._fetch_intersection_ids', mock_fetch_intersection_ids)
    @mock.patch('energyPATHWAYS.geomapper.GeoMapper._fetch_geography_data', mock_fetch_geography_data)
    @mock.patch('energyPATHWAYS.geomapper.cfg', cfg)
    def setUp(self):
        self.gm = GeoMapper()

    def test_shape_geomap_to_timezone(self):
        table = self.gm.map_df('state', 'time zone', normalize_as='intensity')
        col = cfg.default_geography_map_key
        self.assertEqual(table.index.names, ['state', 'time zone'])
        self.assertAlmostEqual(table.loc[4, 125][col], 5.544638e-02)
        # States and time zones intersect in 74 ways (in other words, 22 of our 52 "states" span
        # more than one time zone)
        self.assertEqual(len(table), 74)
        # The sum is 8 because there are 8 time zones, and the proportions assigned to each
        # state within each time zone should sum to 1
        self.assertEqual(table[col].sum(), 8)

    def test_shape_geomap_to_primary_geography(self):
        table = self.gm.map_df('state', 'census division', normalize_as='intensity')
        col = cfg.default_geography_map_key
        self.assertEqual(table.index.names, ['state', 'census division'])
        self.assertAlmostEqual(table.loc[11, 60][col], 1.479370e-02)
        # There are 52 "states" in the model: the usual 50 + Washington DC and Puerto Rico
        # Census division borders always run along state borders (i.e. no states are split
        # across census divisions), so there are 52 intersections between states and census divisions
        self.assertEqual(len(table), 52)
        # The sum is 9 because there are 9 census divisions, and the proportions assigned to each
        # state within each census division should sum to 1
        self.assertEqual(table[col].sum(), 9)
