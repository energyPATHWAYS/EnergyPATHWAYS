__author__ = 'ryan & michael'

import config as cfg
import util
import numpy as np
import pandas as pd
from time_series import TimeSeries
from collections import OrderedDict
import os
import copy
import time
from pprint import pprint
from util import DfOper
from sqlalchemy.orm import reconstructor
from sqlalchemy.ext.declarative import declarative_base
import data_source
from datamapfunctions import DataMapFunctions

class DataMapper(DataMapFunctions, object):
    data_tables = {}

    @classmethod
    def get_all_raw_values(cls, data_cls):
        print '[DataMapper] loading all raw values from %s' % data_cls
        cls.data_tables[data_cls] = data_source.fetch_as_df(data_cls)
        return cls.data_tables[data_cls]

    @classmethod
    def get_raw_values(cls, id_):
        if id_ is None:
            raise ValueError('Primary key id required to get raw data')

        # this assumes that the child class has a property called "data" that is a relationship to the data table
        data_cls = cls.data.mapper.class_

        if data_cls not in cls.data_tables:
            cls.get_all_raw_values(data_cls)

        # get the slice of this class' data table that references the requested object id_
        df = cls.data_tables[data_cls].loc[id_]

        # Drop any columns that are unused (all NaN) within the slice
        # Note that we are now working with a copy to avoid inadvertently affecting the underlying
        # data frame for the whole table (that is, data_tables[data_cls])
        df = df.dropna(axis='columns', how='all')

        assert df.notnull().values.all(), "%s contains a null (NaN) value in a column with at least one non-null" \
                                          "value for parent_id %i; for a given parent_id, each column should either" \
                                          "be all null or have no nulls" % (data_cls, id_)

        # any column that doesn't contain the value for the row is an index
        indexes = [col for col in df.columns.values if col != 'value']
        # the index columns may be of type float if they ever contained any NaN values in the original data table,
        # so we will coerce them to int now. Note that this would fail if there were any remaining NaN values in the
        # column, but we screened for that in the assertion above so it should be safe.
        df[indexes] = df[indexes].astype(int)
        df.set_index(indexes, inplace=True)

        return df

    def pretty_index_name(self, index_name):
        """
        Takes a data frame index name and returns a more user-friendly version.
        The main idea is that if we have a column called "gau_id" (the id of a geographical unit) and the geography
        for this object is "census division" we want to label the column "census division" instead of "gau_id".
        We do a similar substitution with columns referring to "other indexes".
        We also trim "_id" off the end of any names ending in that string, so "ghg_id" becomes "ghg"
        Otherwise we just return the original name provided.
        """
        if index_name == 'gau_id':
            return self.geography
        elif index_name == 'oth_1_id':
            return self.other_index_1
        elif index_name == 'oth_2_id':
            return self.other_index_2
        elif index_name.endswith('_id'):
            return index_name[:-3]

        return index_name

    @reconstructor
    def read_timeseries_data(self):
        """reads timeseries data to dataframe from database. Stored in self.raw_values"""
        self.raw_values = self.get_raw_values(self.id)

        self.raw_values.index.names = (self.pretty_index_name(name) for name in self.raw_values.index.names)

        if hasattr(self, 'unit_prefix'):
            self.raw_values = self.raw_values * self.unit_prefix

    # Some shim properties to meet DataMapFunctions' expectation of having e.g. a "geography" property that contains
    # the name of the geography while actually getting the name from a SQLAlchemy relationship. Note that this
    # approach expects subclasses to name their relationships in a specific way (e.g. "_geography").
    # We could obviate these by changing to text primary keys or by updating the code that uses these properties to
    # access whatever.name instead (which is what I'd prefer once we finish transitioning and get rid of
    # DataMapFunctions) but these make things easier during the transition period.
    @property
    def geography(self):
        return self._geography.name

    @property
    def extrapolation_method(self):
        return self._extrapolation_method.name

    @property
    def interpolation_method(self):
        return self._interpolation_method.name

    @property
    def geography_map_key(self):
        return self._geography_map_key.name

    @property
    def input_type(self):
        return self._input_type.name

    @property
    def other_index_1(self):
        return self._other_index_1.name

    @property
    def other_index_2(self):
        return self._other_index_2.name

DataMapper = declarative_base(cls=DataMapper)