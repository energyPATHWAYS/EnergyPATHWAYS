# -*- coding: utf-8 -*-
"""
Created on Tue Jun 07 22:00:12 2016

@author: ryandrewjones
"""

import pandas as pd
import numpy as np
from energyPATHWAYS import util

# indicies to play with
geographies = range(1,10)
energy_types = range(1,10)
years = range(2000, 2051)
vintages = range(1990, 2051)
housing_types = range(1,5)
technologies = range(1,7)

# dataframes to play with (these are totals), note that the column name is always value, as it is in the rest of the code
index = pd.MultiIndex.from_product((geographies, energy_types, years), names=['census_division', 'energy_type', 'year'])
a_total = pd.DataFrame(index=index, columns=['value'])
a_total['value'] = np.arange(len(a_total))+.5

index = pd.MultiIndex.from_product((geographies, energy_types, technologies, vintages), names=['census_division', 'energy_type', 'technology', 'vintage'])
b_total = pd.DataFrame(index=index, columns=['value'])
b_total['value'] = np.arange(len(b_total))+.5

index = pd.MultiIndex.from_product((geographies, technologies, energy_types), names=['census_division', 'technology', 'energy_type']) # note order of levels doesn't matter
c_total = pd.DataFrame(index=index, columns=['value'])
c_total['value'] = np.arange(len(c_total))+.5

index = pd.MultiIndex.from_product((geographies, housing_types), names=['census_division', 'housing_types'])
d_total = pd.DataFrame(index=index, columns=['value'])
d_total['value'] = np.arange(len(d_total))+.5

# note that we hardly ever have a dataframe that doesn't have geography as one of the levels, this is just for testing when none of the levels match
index = pd.MultiIndex.from_product((technologies, housing_types), names=['technology', 'housing_types'])
e_total = pd.DataFrame(index=index, columns=['value'])
e_total['value'] = np.arange(len(e_total))+.5


# these are intensities
a_inten = a_total.groupby(level=['census_division', 'energy_type']).transform(lambda x: x / x.sum())
b_inten = b_total.groupby(level=['census_division', 'energy_type', 'technology']).transform(lambda x: x / x.sum())
c_inten = c_total.groupby(level=['census_division', 'energy_type']).transform(lambda x: x / x.sum())
d_inten = d_total.groupby(level=['census_division']).transform(lambda x: x / x.sum())


# this is straight forward, they both match, and this should be quite fast
df = util.DfOper.add((a_total, a_total), expandable=(False, False), collapsible=(True, True))
np.testing.assert_almost_equal(df.sum().sum(), a_total.sum().sum()*2)

# order of the index doesn't matter
df_before = util.DfOper.mult((a_total, a_total), expandable=(False, False), collapsible=(True, True))
a_total_new_order = a_total.reorder_levels([0, 2, 1])
# note that now that we have reordered, it is not sorted
df_after = util.DfOper.mult((a_total, a_total_new_order), expandable=(False, False), collapsible=(True, True))
np.testing.assert_almost_equal(df_before.sum().sum(), df_after.sum().sum())

# we can add many together at once
df = util.DfOper.add((a_total,)*5, expandable=True, collapsible=False)
np.testing.assert_almost_equal(df.sum().sum(), a_total.sum().sum()*5)

# here they are both totals, so all we can do is collapse them, the sum before and after should match
df = util.DfOper.add((a_total, b_total), expandable=(False, False), collapsible=(True, True))
np.testing.assert_almost_equal(df.sum().sum(), a_total.sum().sum() + b_total.sum().sum())

# here b has an extra level that is not in c, because c is an intensity, we can expand it over the missing level "vintage" in b
df = util.DfOper.mult((c_inten, b_total), expandable=(True, False), collapsible=(False, True))
np.testing.assert_almost_equal(df.sum().sum(), 73308503.39194776)
# This is the opposite case. Now our intensity dataframe has an extra level, and note that this will raise an error.
try:
    df = util.DfOper.mult((c_total, b_inten), expandable=(False, True), collapsible=(True, False))
except ValueError as e:
    assert e.message=='DataFrame b has extra levels, DataFrame a cannot expand, and DataFrame b cannot collapse'


# here we are dividing two totals to make an intensity. In this case, b has the extra level vintage, and it is necessary to collapse it before they can be divided
df = util.DfOper.divi((c_total, b_total), expandable=(False, False), collapsible=(True, True))
# it happens quite a bit that we go back and forth from totals to intensity when we "clean" the data, as this next part shows
# df is now an intensity
df2 = util.DfOper.mult((b_total, df), expandable=(False, True), collapsible=(True, False))
np.testing.assert_almost_equal(df2.sum().sum(), c_total.sum().sum())

# totals are collapsible, intensities are expandable, and this gives us an error because they each have levels that the other doesn't have. We are at an impasse, so an error is raised.
try:
    df = util.DfOper.mult((a_total, b_inten), expandable=(False, True), collapsible=(True, False))
except ValueError as e:
    assert e.message=='DataFrame b has extra levels, DataFrame a cannot expand, and DataFrame b cannot collapse'

# None is just ignored
df = util.DfOper.divi((None, c_total, None))
assert df is c_total

