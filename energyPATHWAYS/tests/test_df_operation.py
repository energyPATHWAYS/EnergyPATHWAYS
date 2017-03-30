# -*- coding: utf-8 -*-
"""
Created on Tue Jun 07 22:00:12 2016

@author: ryandrewjones
"""

import unittest
import pandas as pd
import numpy as np
import numpy.testing as npt
from energyPATHWAYS import util

class TestDfOperation(unittest.TestCase):

    # indicies to play with
    GEOGRAPHIES = range(1, 10)
    ENERGY_TYPES = range(1, 10)
    YEARS = range(2000, 2051)
    VINTAGES = range(1990, 2051)
    HOUSING_TYPES = range(1, 5)
    TECHNOLOGIES = range(1, 7)

    def setUp(self):
        # dataframes to play with (these are totals), note that the column name is always value,
        # as it is in the rest of the code
        index = pd.MultiIndex.from_product((self.GEOGRAPHIES, self.ENERGY_TYPES, self.YEARS),
                                           names=['census_division', 'energy_type', 'year'])
        self.a_total = pd.DataFrame(index=index, columns=['value'])
        self.a_total['value'] = np.arange(len(self.a_total))+.5
    
        index = pd.MultiIndex.from_product((self.GEOGRAPHIES, self.ENERGY_TYPES, self.TECHNOLOGIES, self.VINTAGES),
                                           names=['census_division', 'energy_type', 'technology', 'vintage'])
        self.b_total = pd.DataFrame(index=index, columns=['value'])
        self.b_total['value'] = np.arange(len(self.b_total))+.5
    
        # note order of levels doesn't matter
        index = pd.MultiIndex.from_product((self.GEOGRAPHIES, self.TECHNOLOGIES, self.ENERGY_TYPES),
                                           names=['census_division', 'technology', 'energy_type'])
        self.c_total = pd.DataFrame(index=index, columns=['value'])
        self.c_total['value'] = np.arange(len(self.c_total))+.5
    
        index = pd.MultiIndex.from_product((self.GEOGRAPHIES, self.HOUSING_TYPES),
                                           names=['census_division', 'housing_types'])
        self.d_total = pd.DataFrame(index=index, columns=['value'])
        self.d_total['value'] = np.arange(len(self.d_total))+.5

        self.b_inten = self.b_total.groupby(
            level=['census_division', 'energy_type', 'technology']
        ).transform(lambda x: x / x.sum())

    def test_basic_add(self):
        # this is straight forward, they both match, and this should be quite fast
        df = util.DfOper.add((self.a_total, self.a_total), expandable=(False, False), collapsible=(True, True))
        npt.assert_almost_equal(df.sum().sum(), self.a_total.sum().sum()*2)

    def test_mult_after_index_reorder(self):
        # order of the index doesn't matter
        df_before = util.DfOper.mult((self.a_total, self.a_total), expandable=(False, False), collapsible=(True, True))
        a_total_new_order = self.a_total.reorder_levels([0, 2, 1])
        # note that now that we have reordered, it is not sorted
        df_after = util.DfOper.mult((self.a_total, a_total_new_order),
                                    expandable=(False, False), collapsible=(True, True))
        npt.assert_almost_equal(df_before.sum().sum(), df_after.sum().sum())

    def test_add_many(self):
        # we can add many together at once
        df = util.DfOper.add((self.a_total,)*5, expandable=True, collapsible=False)
        npt.assert_almost_equal(df.sum().sum(), self.a_total.sum().sum()*5)

    def test_collapse(self):
        # here they are both totals, so all we can do is collapse them, the sum before and after should match
        df = util.DfOper.add((self.a_total, self.b_total), expandable=(False, False), collapsible=(True, True))
        npt.assert_almost_equal(df.sum().sum(), self.a_total.sum().sum() + self.b_total.sum().sum())

    def test_expand(self):
        # here b has an extra level that is not in c, because c is an intensity
        # we can expand it over the missing level "vintage" in b
        c_inten = self.c_total.groupby(level=['census_division', 'energy_type']).transform(lambda x: x / x.sum())
        df = util.DfOper.mult((c_inten, self.b_total), expandable=(True, False), collapsible=(False, True))
        npt.assert_almost_equal(df.sum().sum(), 73308503.39194776, decimal=6)

    def test_cant_expand(self):
        # This is the opposite case. Now our intensity dataframe has an extra level, and note that this will raise an error.
        with self.assertRaises(ValueError) as context_manager:
            util.DfOper.mult((self.c_total, self.b_inten), expandable=(False, True), collapsible=(True, False))

        self.assertEqual(context_manager.exception.message,
                         'DataFrame b has extra levels, DataFrame a cannot expand, and DataFrame b cannot collapse')

    def test_divide_totals_to_make_intensity(self):
        # here we are dividing two totals to make an intensity.
        # In this case, b has the extra level vintage, and it is necessary to collapse it before they can be divided
        df = util.DfOper.divi((self.c_total, self.b_total), expandable=(False, False), collapsible=(True, True))
        # it happens quite a bit that we go back and forth from totals to intensity when we "clean" the data,
        # as this next part shows
        # df is now an intensity
        df2 = util.DfOper.mult((self.b_total, df), expandable=(False, True), collapsible=(True, False))
        npt.assert_almost_equal(df2.sum().sum(), self.c_total.sum().sum())

    def test_incompatible_total_and_intensity(self):
        # totals are collapsible, intensities are expandable, and this gives us an error because they each have levels
        # that the other doesn't have. We are at an impasse, so an error is raised.
        with self.assertRaises(ValueError) as context_manager:
            util.DfOper.mult((self.c_total, self.b_inten), expandable=(False, True), collapsible=(True, False))

        self.assertEqual(context_manager.exception.message,
                         'DataFrame b has extra levels, DataFrame a cannot expand, and DataFrame b cannot collapse')

    def test_ignore_none(self):
        # None is just ignored
        df = util.DfOper.divi((None, self.c_total, None))
        self.assertIs(df, self.c_total)
