# -*- coding: utf-8 -*-
__author__ = 'Michael'

import unittest
import mock
import energyPATHWAYS as ep
from energyPATHWAYS.util import *
from sqlalchemy.orm.exc import NoResultFound
import ipdb


def read_table(table_name, column_names='*', return_unique=False, return_iterable=False, **filters):
    if table_name == 'IDMap' and column_names == 'identifier_id, ref_table':
        return [(u'supply_type_id', u'SupplyTypes'), (u'ghg_id', u'GreenhouseGases')]
    elif table_name == 'SupplyTypes' and column_names == 'id, name':
        return [(1, u'Blend'), (2, u'Conversion'), (3, u'Delivery'), (4, u'Import'), (5, u'Primary'), (6, u'Storage')]
    elif table_name == 'GreenhouseGases' and column_names == 'id, name':
        return [(1, u'CO2'), (2, u'CH4'), (3, u'N2O')]

    # if we've gotten this far without returning, something is amiss
    raise ValueError("Mock doesn't know how to provide this table read: " +
                     str(table_name) + ", " + str(column_names) + ", " + str(filters))

mock_sql_read_table = mock.create_autospec(sql_read_table, side_effect=read_table)

@mock.patch('ep.util.sql_read_table', mock_sql_read_table)
class TestIdToName(unittest.TestCase):

    def test_basic_lookup(self):
        self.assertEqual(id_to_name('supply_type_id', 1), 'Blend')
        self.assertEqual(id_to_name('ghg_id', 2), 'CH4')

    def test_lookup_none_att(self):
        self.assertIsNone(id_to_name('supply_type_id', None))

    def test_tuple_lookup(self):
        self.assertEqual(id_to_name('supply_type_id', 1, 'tuple'), ('supply_type', 'Blend'))

    def test_lookup_unknown_table(self):
        with self.assertRaises(KeyError):
            id_to_name('GARBAGE', 1)

    def test_lookup_att_out_of_range(self):
        self.assertIsNone(id_to_name('supply_type_id', -1))

    def test_caching(self):
        # Check to make sure the lookup cache is where we expect, then clear it
        self.assertIsNotNone(energyPATHWAYS.util.id_to_name.lookup_dict)
        ep.util.id_to_name.lookup_dict = {}

        id_to_name('supply_type_id', 1)
        self.assertTrue(mock_sql_read_table.called, "Database not accessed on first call to id_to_name()")

        mock_sql_read_table.reset_mock()
        id_to_name('ghg_id', 2)
        # the second time everything needed should be cached so there should be no more db calls
        self.assertFalse(mock_sql_read_table.called, "Redundant database access by id_to_name()")

class TestCurrencyConversions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        d = os.path.dirname(os.path.realpath(__file__))
        cfgfile_path = os.path.join(d, 'test_config.INI')
        custom_pint_definitions_path = os.path.join(d, 'unit_defs.txt')
        ep.config.initialize_config(cfgfile_path, custom_pint_definitions_path)

    def test_currency_conversion(self):
        self.assertAlmostEqual(exchange_rate(1, 2000, 2), 1.2258088131286535)
        self.assertAlmostEqual(exchange_rate(1, 2000), 0.5812734739195623)

        with self.assertRaises(NoResultFound):
            exchange_rate(1, 9999)

        with self.assertRaises(NoResultFound):
            exchange_rate(-6666, 2000)

        with self.assertRaises(NoResultFound):
            exchange_rate(1, 2000, 9999)

    def test_inflation_conversion(self):
        # the only currency for which we have inflation values is USD (currency_id 41)
        self.assertAlmostEqual(inflation_rate(41, 2000, 2010), 1.2664699869912655)
        self.assertAlmostEqual(inflation_rate(41, 2000), 1.3529199962832186)

        with self.assertRaises(NoResultFound):
            inflation_rate(1, 2000, 2010)

        with self.assertRaises(NoResultFound):
            inflation_rate(41, 1900)

        with self.assertRaises(NoResultFound):
            inflation_rate(41, 2000, 9999)

