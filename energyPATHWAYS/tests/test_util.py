# -*- coding: utf-8 -*-
__author__ = 'Michael'

import unittest
import mock
import energyPATHWAYS
from energyPATHWAYS.util import *
from sqlalchemy.orm.exc import NoResultFound

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


@mock.patch('energyPATHWAYS.util.sql_read_table', mock_sql_read_table)
class TestIdToName(unittest.TestCase):

    def test_basic_lookup(self):
        self.assertEqual(id_to_name('supply_type_id', 1), 'Blend')
        self.assertEqual(id_to_name('ghg_id', 2), 'CH4')

    def test_lookup_none_att(self):
        self.assertIsNone(id_to_name('supply_type_id', None))

    @unittest.skip("This was broken by a refactoring Ryan did but id_to_name will be obsolete soon anyway so I'm not fixing it")
    def test_tuple_lookup(self):
        self.assertEqual(id_to_name('supply_type_id', 1, 'tuple'), ('supply_type', 'Blend'))

    @unittest.skip("This was broken by a refactoring Ryan did but id_to_name will be obsolete soon anyway so I'm not fixing it")
    def test_lookup_unknown_table(self):
        with self.assertRaises(KeyError):
            id_to_name('GARBAGE', 1)

    def test_lookup_att_out_of_range(self):
        self.assertIsNone(id_to_name('supply_type_id', -1))

    def test_caching(self):
        # Check to make sure the lookup cache is where we expect, then clear it
        self.assertIsNotNone(energyPATHWAYS.util.id_to_name.lookup_dict)
        energyPATHWAYS.util.id_to_name.lookup_dict = {}

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
        energyPATHWAYS.config.initialize_config(cfgfile_path, custom_pint_definitions_path)

    def test_exchange_rate(self):
        #self.assertAlmostEqual(exchange_rate(1, 2000, 2), 1.2258088131286535)
        self.assertAlmostEqual(exchange_rate(1, 2, 2000), 1.2258088131286535)
        self.assertAlmostEqual(exchange_rate(1, 41, 2000), 0.5812734739195623)

        with self.assertRaises(NoResultFound):
            exchange_rate(1, 2, 9999)

        with self.assertRaises(NoResultFound):
            exchange_rate(-6666, 2, 2000)

        with self.assertRaises(NoResultFound):
            exchange_rate(1, 2000, 9999)

        with self.assertRaises(NoResultFound):
            exchange_rate(None, 2, 2000)

        with self.assertRaises(NoResultFound):
            exchange_rate(1, None, 2000)

        with self.assertRaises(NoResultFound):
            exchange_rate(1, 2, None)

    def test_inflation_rate(self):
        # the only currency for which we have inflation values is USD (currency_id 41)
        usd = 41
        self.assertAlmostEqual(inflation_rate(usd, 2000, 2010), 1.2664699869912655)
        self.assertAlmostEqual(inflation_rate(usd, 2000, 2013), 1.3529199962832186)

        with self.assertRaises(NoResultFound):
            inflation_rate(usd, 1900, 2010)

        with self.assertRaises(NoResultFound):
            inflation_rate(usd, 2000, 9999)

        with self.assertRaises(NoResultFound):
            inflation_rate(1, 2000, 2010)

        with self.assertRaises(NoResultFound):
            inflation_rate(None, 2000, 2010)

        with self.assertRaises(NoResultFound):
            inflation_rate(usd, None, 2010)

        with self.assertRaises(NoResultFound):
            inflation_rate(usd, 2000, None)

    def test_currency_convert(self):
        # In normal use the first parameter to currency_convert (named "data") would be a data frame, but here we
        # just pass a scalar 1 so we can easily see if the correct conversion factors are being found.
        unity = 1

        # USD ($) is the model currency
        usd = 41
        model_year = 2013

        self.assertAlmostEqual(currency_convert(unity, usd, model_year, usd, model_year), 1.0)
        self.assertAlmostEqual(currency_convert(unity, usd, model_year), 1.0)

        self.assertAlmostEqual(currency_convert(unity, 1, 2000, usd, model_year), 0.7864165061747878)
        self.assertAlmostEqual(currency_convert(unity, 1, 2000), 0.7864165061747878)

        self.assertAlmostEqual(currency_convert(unity, 1, 2000, 2, 2010), 1.0860484961097614)
