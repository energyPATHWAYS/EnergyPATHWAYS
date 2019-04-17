# -*- coding: utf-8 -*-
"""
Created on Wed Apr 08 10:12:52 2015

@author: Ben Haley & Ryan Jones

Contains unclassified global functions

"""

import config as cfg
from .error import ColumnNotFound
import pint
import pandas as pd
import os
import numpy as np
from time_series import TimeSeries
from collections import defaultdict, OrderedDict, MutableSet
import time
import csv
import matplotlib
from matplotlib import cm
import os as _os
#matplotlib.style.use('ggplot')
import math
import scipy.special
import copy
from profilehooks import profile, timecall
import functools
import itertools
import decimal
import psycopg2
import logging
import pdb
from operator import mul

from csvdb.data_object import get_database
from csvdb.utils import filter_query

from psycopg2.extensions import register_adapter, AsIs

def makedirs_if_needed(path):
    '''Checks to see if a directory exists, and creates it if not
    '''
    if not os.path.exists(path):
        os.makedirs(path)

class DateTimeLookup:
    dates = {}

    @classmethod
    def lookup(cls, series):
        """
        This is a faster approach to datetime parsing.
        For large data, the same dates are often repeated. Rather than
        re-parse these, we store all unique dates, parse them, and
        use a lookup to convert all dates.
        """
        cls.dates.update({date: pd.to_datetime(date) for date in series.unique() if not cls.dates.has_key(date)})
        return series.apply(lambda v: cls.dates[v])

def splitclean(s, delim=',', allow_empties=False, as_type=None):
    """
    Split a delimited string (default is comma-delimited) into elements that are
    stripped of surrounding whitespace. Filter out empty strings unless `allow_empties`
    is True.

    :param s: (str) the string to split
    :param delim: (str) the delimiter to split on
    :param allow_empties: (bool) whether to allow empty strings in the result
    :param as_type: (class or type) a type to convert all elements to
    :return: (list of str) the resulting substrings
    """
    result = [item.strip() for item in s.split(delim) if (allow_empties or len(item))]

    if as_type:
        result = map(as_type, result)

    return result

def addapt_numpy_float64(numpy_float64):
  return AsIs(numpy_float64)
register_adapter(np.int64, addapt_numpy_float64)

def loop_geo_multiply(df1, df2, geo_label, geographies, levels_to_keep=None):
    geography_df_list = []
    for geography in geographies:
        if geography in df2.index.get_level_values(geo_label):
            supply_indexer = level_specific_indexer(df2, [geo_label], [geography])
            demand_indexer = level_specific_indexer(df1, [geo_label], [geography])
            demand_df = df1.loc[demand_indexer, :]
            demand_df = demand_df.round(12)
            demand_df = demand_df[demand_df.values!=0]
            supply_df =  df2.loc[supply_indexer, :]
            supply_df = supply_df.round(12)
            supply_df = supply_df[supply_df.values != 0]
            geography_df = DfOper.mult([demand_df,supply_df])
            geography_df_list.append(geography_df)
    df = pd.concat(geography_df_list)
    if levels_to_keep:
        filtered_ltk = [x for x in levels_to_keep if x in df.index.names]
        df = df.groupby(level=filtered_ltk).sum()
    return df

def add_to_df_index(df, names, keys):
    for key, name in zip(keys, names):
        df = pd.concat([df], keys=[key], names=[name])
    return df

def percent_larger(a, b):
    return (a - b) / a

def percent_different(a, b):
    return abs(a - b) / a

def freeze_recursivedict(recursivedict):
    recursivedict = dict(recursivedict)
    for key, value in recursivedict.items():
        if isinstance(value, defaultdict):
            recursivedict[key] = freeze_recursivedict(value)
    return recursivedict

def upper_dict(query, append=None):
    id_dict = {} if query is None else dict([(id, name.upper()) for id, name in (query if is_iterable(query[0]) else [query])])
    for key,value in id_dict.iteritems():
        if append is not None:
            id_dict[key] = value + append
    return id_dict

def df_list_concatenate(df_list, keys, new_names, levels_to_keep=None):
    new_names = put_in_list(new_names)
    #remove any elements in the list that are not pandas df
    df_list = [df for df in df_list if type(df) is pd.core.frame.DataFrame]

    df_names_set = set(flatten_list([df.index.names if df.index.nlevels>1 else [df.index.name] for df in df_list]))
    levels_to_keep = levels_to_keep if levels_to_keep is not None else list(df_names_set)

    #add missing levels
    for df in df_list:
        starting_names = df.index.names if df.index.nlevels>1 else df.index.name
        missing_names = list(set(levels_to_keep) - set(starting_names) - set(new_names))
        for missing_name in missing_names:
            df[missing_name] = "N/A"
        df.set_index(missing_names, append=True, inplace=True)

    #aggregate extra levels and order
    df_list = [df.groupby(level=list(set(levels_to_keep)-set(new_names)), sort=False).sum() for df in df_list]

    if len(df_list)==0:
        return None
    else:
        df = pd.concat(df_list, keys=keys, names=new_names).sort()

    #eliminate any new_names we picked up that are not in levels_to_keep, also reorder levels
    return df.groupby(level=levels_to_keep, sort=False).sum()

def order_of_magnitude_difference(df_numerator, df_denominator):
    return 10**int(round(np.log10(df_numerator.mean().mean())-np.log10(df_denominator.mean().mean())))

def time_stamp(t):
    """Prints the difference between the parameter and current time. This is useful for timing program execution if timestamps are periodicly saved.
    Parameters:
        a: float

    Returns:
        current time: float
    """
    print "%(time).6f seconds to execute \n" % {"time": time.time() - t}
    return time.time()


def recursivedict():
    """recursivedict creates a dictionary of any depth"""
    return defaultdict(recursivedict)


def is_iterable(some_object):
    """
    Checks to see if an object is iterable.

    Args:
        s (string)

    Returns:
        Boolean
    """
    try:
        iter(some_object)
        return True
    except:
        return False


def object_att_from_table(tablename, id, primary_key='name'):
    db = get_database()
    tbl = db.get_table(tablename)

    table_headers = [h for h in tbl.get_columns() if h != primary_key]
    # table_headers = [h for h in sql_read_headers(tablename) if h != primary_key]

    if not len(table_headers):
        return []

    attributes = csv_read_table(tablename, column_names=table_headers, **{primary_key : id})
    if attributes is None:
        return None
    native_tuples = [(table_headers, attributes)] if len(table_headers)==1 else zip(table_headers, attributes)

    named_tuples = []
    for t in native_tuples:
        col_name = id_to_name(id_col=t[0], id_num=t[1], return_type='tuple')
        if col_name is not None:
            named_tuples.append(col_name)
    return native_tuples + named_tuples


def tuple_subset(tup, header, head_to_remove):
    if len(tup) != len(header):
        raise ValueError('Length of header must match the length of tuple')
    head_to_remove = [x for x in head_to_remove if x in header]
    index_to_remove = [header.index(e) for e in head_to_remove]
    return tuple([t for i, t in enumerate(tup) if i not in index_to_remove])


def id_to_name(id_col, id_num, return_type='item'):
    if not hasattr(id_to_name, 'lookup_dict'):
        id_to_name.lookup_dict = {}
        # the lookup cache hasn't been populated yet, so take a time out to populate it
        for _id_col, _table in csv_read_table('IDMap', 'identifier_id, ref_table'):
            id_to_name.lookup_dict[_id_col] = {}
            for _id_num, _name in csv_read_table(_table, 'id, name', return_iterable=True):
                id_to_name.lookup_dict[_id_col][_id_num] = _name

    if id_to_name.lookup_dict.has_key(id_col):
        name = id_to_name.lookup_dict[id_col].get(id_num)
        col = id_col[:-3]
    else:
        return None

    if return_type == 'item':
        return name
    elif return_type == 'tuple':
        return (col, name)

def empty_df(index, columns, fill_value=0.0, data_type=None):
    df = pd.DataFrame(fill_value, index=index, columns=columns).sort_index()
    df.data_type = data_type
    return df

def verify_columns(table_name, df, column_names, raise_error=True):
    unknown = set(column_names) - set(df.columns)

    if unknown and raise_error:
        raise ColumnNotFound(table_name, list(unknown))

    return len(unknown) == 0


def table_data(table_name, column_names=None, as_tup_iter=False):
    """
    Get the DataFrame holding the data for the given table_name. The
    database must have already been opened (with explicit path) so that
    the call here returns the singleton instance.

    :param table_name: (str) the name of a table
    :param column_names: (list of str) the columns to return
    :param as_tup_iter: (bool) if True, return a tuple iterator, else a DataFrame
    :return: the DataFrame or tuple iterator providing the selected data
    """
    db = get_database()
    tbl = db.get_table(table_name)
    df = tbl.data

    if column_names:
        verify_columns(table_name, df, column_names)
        df = df[column_names]

    return df.itertuples(index=False, name=None) if as_tup_iter else df

def csv_read_table(table_name, column_names=None, return_unique=False, return_iterable=False, **filters):
    """
    Get data from a table filtering by columns.
    Key word arguments give column name, column criteria pairs.

    Example:
        util.csv_read_table('DemandDrivers', 'name', driver='oil and gas mining VOS')
    """
    db  = get_database()
    tbl = db.get_table(table_name)
    df  = tbl.data

    if filters:
        verify_columns(table_name, df, filters.keys())
        df = filter_query(df, filters)

    if column_names:
        verify_columns(table_name, df, column_names)
        df = df[column_names]

    if return_unique:
        df.drop_duplicates(inplace=True)

    rows, cols = df.shape
    if rows == 0:
        data = [None]

    elif cols == 1:
        data = df.iloc[:, 0].tolist()

    else:
        data = list(df.itertuples(index=False, name=None))

    # pull out the first element if length is 1 and we don't want to return an iterable
    if len(data) == 0 or data == [None]:
        return [] if return_iterable else None

    elif len(data) == 1:
        return data if return_iterable else data[0]

    else:
        return data

# Deprecated
# def sql_read_table(table_name, column_names=None, return_unique=False, return_iterable=False, **filters):
#     from csvdb.data_object import get_database
#
#     db  = get_database()
#     tbl = db.get_table(table_name)
#     df  = tbl.data
#
#     unknown = set(column_names) - set(df.columns)
#     if unknown:
#         raise ColumnNotFound(table_name, list(unknown))
#
#     cols = df[column_names] if column_names else df
#
#     distinct = 'DISTINCT ' if return_unique else ''
#     query = 'SELECT ' + distinct + column_names + ' FROM "%s"' % table_name
#
#     if len(filters):
#         datatypes = sql_get_datatype(table_name, filters.keys())
#         list_of_filters = ['"' + col + '"=' + fix_sql_query_type(fil, datatypes[col]) if fil is not None else '"' + col + '"is' + 'NULL' for col, fil in filters.items()]
#         if list_of_filters:
#             query = query + " where " + " and ".join(list_of_filters)
#             cfg.cur.execute(query)
#             data = [tup[0] if len(tup) == 1 else tup for tup in cfg.cur.fetchall()]
#         else:
#             data = [None]
#
#     else:
#         cfg.cur.execute(query)
#         data = [tup[0] if len(tup) == 1 else tup for tup in cfg.cur.fetchall()]
#     # pull out the first element if length is 1 and we don't want to return an iterable
#     if len(data) == 0 or data == [None]:
#         return [] if return_iterable else None
#     elif len(data) == 1:
#         return data if return_iterable else data[0]
#     else:
#         return data
#
#
# def sql_get_datatype(table_name, column_names):
#     if isinstance(column_names, basestring):
#         column_names = [column_names]
#     cfg.cur.execute("select column_name, data_type from INFORMATION_SCHEMA.COLUMNS where table_name = %s and table_schema = 'public';", (table_name,))
#     table_info = cfg.cur.fetchall()
#     return dict([tup for tup in table_info if tup[0] in column_names])
#
#
# def fix_sql_query_type(string, sqltype):
#     if sqltype == 'INTEGER':
#         return str(string)
#     else:
#         return "'" + str(string) + "'"
#
#
# def sql_read_dataframe(table_name, index_column_name=None, data_column_names='*', **filters):
#     """
#     Read data and create a dataframe
#     Example:
#         data = util.sql_read_dataframe('DemandDrivers', index_column_name='year', data_column_names='value',
#                                         ID=1, gau='total', dau='single-family', add='total')
#     """
#     if not isinstance(index_column_name, basestring):
#         if len(index_column_name) > 1:
#             raise ValueError("Only one index_column_name should be given")
#         else:
#             index_column_name = index_column_name[0]
#
#     if data_column_names == '*':
#         data_column_names = [n for n in sql_read_headers(table_name) if n != index_column_name]
#     if (not isinstance(data_column_names, list)) and (not isinstance(data_column_names, tuple)):
#         data_column_names = [data_column_names]
#
#     data = csv_read_table(table_name, column_names=data_column_names, **filters)
#     if index_column_name is not None:
#         index = csv_read_table(table_name, column_names=index_column_name, **filters)
#         if (not len(index)) or (not len(data)):
#             raise ValueError('sql_read_dataframe returned empty data')
#
#         data_frame = pd.DataFrame(data=data, index=index, columns=data_column_names)
#         data_frame.sort_index(inplace=True)
#     else:
#         data_frame = pd.DataFrame(data=data, columns=data_column_names)
#
#     return data_frame


def sql_read_headers(table_name):
    cfg.cur.execute("select column_name from INFORMATION_SCHEMA.COLUMNS where table_name = %s and table_schema = 'public';", (table_name,))
    table_info = cfg.cur.fetchall()
    # return list of all column headers
    return [tup[0] for tup in table_info]

def sql_read_dict(table_name, key_col, value_col):
    """
    Returns two columns of a table as a dictionary.
    Memoizes the results so each dictionary is only loaded from the database once.
    """
    memo_key = (table_name, key_col, value_col)
    try:
        return sql_read_dict.memo[memo_key]
    except KeyError:
        data = csv_read_table(table_name, column_names=(key_col, value_col))
        sql_read_dict.memo[memo_key] = {row[0]: row[1] for row in data}
        return sql_read_dict.memo[memo_key]
sql_read_dict.memo = {}

def active_scenario_run_id(scenario_id):
    query = """
                SELECT public_runs.scenario_runs.id
                FROM public_runs.scenario_runs
                JOIN public_runs.scenario_run_statuses
                  ON public_runs.scenario_runs.status_id = public_runs.scenario_run_statuses.id
                WHERE public_runs.scenario_runs.scenario_id = %s
                  AND public_runs.scenario_run_statuses.finished = FALSE
            """

    cfg.cur.execute(query, (scenario_id,))
    assert cfg.cur.rowcount == 1, \
        "Expected 1 active scenario run for scenario %i but found %i." % (scenario_id, cfg.cur.rowcount)
    return cfg.cur.fetchone()[0]


def active_user_email(scenario_id):
    query = """
                SELECT email
                FROM shared.users
                JOIN "Scenarios" ON "Scenarios".user_id = shared.users.id
                WHERE "Scenarios".id = %s
            """

    cfg.cur.execute(query, (scenario_id,))
    if cfg.cur.rowcount == 0:
        return None
    else:
        return cfg.cur.fetchone()[0]


def scenario_name(scenario_id):
    query = 'SELECT name FROM "Scenarios" WHERE id = %s'
    cfg.cur.execute(query, (scenario_id,))
    return cfg.cur.fetchone()[0]


def update_status(scenario_id, status_id):
    """Update the status of the active run for the current scenario in the database"""
    # FIXME: See api/models.py ScenarioRunStatus for the valid status_ids. I'm reluctant to import those constants here
    # at this time because I don't want the dependencies of that file (e.g. sqlalchemy) to become dependencies
    # of the main model yet.
    scenario_run_id = active_scenario_run_id(scenario_id)

    assert 3 <= status_id <= 6, "update_status() only understands status_ids between 3 and 6, inclusive."
    end_time_update = ', end_time = now()' if status_id >= 4 else ''

    cfg.cur.execute("UPDATE public_runs.scenario_runs SET status_id = %s%s WHERE id = %s",
                    (status_id, psycopg2.extensions.AsIs(end_time_update), scenario_run_id))
    cfg.con.commit()


def write_output_to_db(scenario_run_id, output_type_id, output_df, keep_cut_off=0.001):
    # For output_type_ids, see api/models.py. I am reluctant to import that file here because I don't want its
    # dependencies (e.g. SQLAlchemy) to become dependencies of the main model yet.
    output_df = output_df.reset_index().set_index(output_df.index.names)
    if output_df.index.nlevels > 1:
        index = pd.MultiIndex.from_product(output_df.index.levels, names=output_df.index.names)
        output_df = output_df.reindex(index, fill_value=0)
        if 'YEAR' in output_df.index.names:
            sums = output_df.groupby(level=[l for l in output_df.index.names if l!='YEAR']).sum()
            keep = list(sums.index[np.nonzero((sums > keep_cut_off * sums.sum()).values.flatten())])
            output_df = output_df.loc[keep]

    df = output_df.reset_index()
    if len(df.columns)==3:
        assert df.columns[1].lower() == 'year', \
        "Output data frame is expected to have three columns (or columns and indexes)" \
        "corresponding to (series, year, value) in the output_data table."
    elif len(df.columns)==2:
        df.columns[0].lower() == 'year', \
        "Output data frame is expected to have two columns (or columns and indexes)" \
        "corresponding to (year, value) in the output_data table."
    else:
        raise ValueError('Output data frame is expected to have either two or three columns')

    unit = df.columns[-1]
    cfg.cur.execute("""INSERT INTO public_runs.outputs (scenario_run_id, output_type_id, unit)
                       VALUES (%s, %s, %s) RETURNING id""", (scenario_run_id, output_type_id, unit))
    output_id = cfg.cur.fetchone()[0]

    if len(df.columns)==3:
        values_str = ','.join(cfg.cur.mogrify("(%s,%s,%s,%s)", (output_id, row[0], row[1], row[2]))
                              for row in df.itertuples(index=False))
        cfg.cur.execute("INSERT INTO public_runs.output_data (parent_id, series, year, value) VALUES " + values_str)
    elif len(df.columns)==2:
        values_str = ','.join(cfg.cur.mogrify("(%s,%s,%s)", (output_id, row[0], row[1]))
                              for row in df.itertuples(index=False))
        cfg.cur.execute("INSERT INTO public_runs.output_data (parent_id, year, value) VALUES " + values_str)

    cfg.con.commit()


def unpack_dict(dictionary, _keys=None, return_items=True):
    if not isinstance(dictionary, dict):
        raise TypeError('unpack_dict takes a dictionary as an argument')

    if return_items:
        for key, value in dictionary.items():
            combined_key = put_in_list(_keys) + put_in_list(key) if _keys is not None else put_in_list(key)
            if isinstance(value, dict):
                for t in unpack_dict(value, combined_key):
                    yield t
            else:
                yield [combined_key, value]
    else:
        for value in dictionary.values():
            if isinstance(value, dict):
                for value2 in unpack_dict(value):
                    yield value2
            else:
                yield value


def unit_conversion_factor(unit_from, unit_to):
    """return data converted from unit_from to unit_to"""
    if unit_from is None or unit_to is None:
        return 1
    else:
        if unit_from == unit_to:
            # if unit_from and unit_to are equal then no conversion is necessary
            return 1.
        else:
            try:
                unit_from.magnitude()
                quant_from = unit_from
            except:
                try:
                    quant_from = cfg.ureg.Quantity(unit_from)
                except:
                    pdb.set_trace()
            try:
                unit_to.magnitude()
                quant_to = unit_to
            except:
                quant_to = cfg.ureg.Quantity(unit_to)
            if quant_from.dimensionality == quant_to.dimensionality:
                # return conversion factor
                return quant_from.to(quant_to).magnitude
            else:
                # if the dimensionality of unit_from and unit_too (i.e. length to energy) are
                # not equal, then raise ValueError
                error_text = "%s not convertible to %s" % (unit_from, unit_to)
                raise ValueError(error_text)


def exchange_rate(currency_from, currency_from_year, currency_to=None):
    """calculate exchange rate between two specified currencies"""
    try:
        currency_to_name = cfg.cfgfile.get('case', 'currency_name') if currency_to is None else csv_read_table('Currencies', column_names='name', id=currency_to)
        currency_to = csv_read_table('Currencies', column_names='id', name=currency_to_name)
        currency_from_values = csv_read_table('CurrenciesConversion', 'value', currency_id=currency_from, currency_year_id=currency_from_year)
        currency_from_value = np.asarray(currency_from_values).mean()
        currency_to_values = csv_read_table('CurrenciesConversion', 'value', currency_id=currency_to, currency_year_id=currency_from_year)
        currency_to_value = np.asarray(currency_to_values).mean()
    except:
        pdb.set_trace()
    return currency_to_value / currency_from_value


def inflation_rate(currency, currency_from_year, currency_to_year=None):
    """calculate inflation rate between two years in a specified currency"""
    currency_to_year = cfg.cfgfile.get('case', 'currency_year_id') if currency_to_year is None else currency_to_year
    currency_from_values = csv_read_table('InflationConversion', 'value', currency_id=currency,
                                          currency_year_id=currency_from_year)
    currency_from_value = np.asarray(currency_from_values).mean()
    currency_to_values = csv_read_table('InflationConversion', 'value', currency_id=currency,
                                        currency_year_id=currency_to_year)
    currency_to_value = np.asarray(currency_to_values).mean()
    return currency_to_value / currency_from_value


def currency_convert(data, currency_from, currency_from_year):
    """converts cost data in original currency specifications (currency,year) to model currency and year"""
    currency_to_name, currency_to_year = cfg.cfgfile.get('case', 'currency_name'), int(cfg.cfgfile.get('case', 'currency_year_id'))
    currency_to = csv_read_table('Currencies', column_names='id', name=currency_to_name)
    # inflate in original currency and then exchange in model currency year

    try:
        a = inflation_rate(currency_from, currency_from_year)
        b = exchange_rate(currency_from, currency_to_year)
        data *= a * b
        return data
    except:
        try:
            # convert to model currency in original currency year and then inflate to model currency year
            a = exchange_rate(currency_from, currency_from_year)
            b = inflation_rate(currency_to, currency_from_year)
            return data * a * b
        except:
            try:
                # use a known inflation data point of the USD. Exchange from original currency to USD
                # in original currency year. Inflate to model currency year. Exchange to model currency in model currency year.
                a = exchange_rate(currency_from, currency_from_year, currency_to=41)
                b = inflation_rate(currency=41, currency_from_year=currency_from_year)
                c = exchange_rate(currency_from=41, currency_from_year=currency_to_year, currency_to=currency_to)
                return data * a * b * c
            except:
                raise ValueError(
                    "currency conversion failed. Make sure that the data in InflationConvert and CurrencyConvert can support this conversion")


def unit_conversion(unit_from_num=None, unit_from_den=None, unit_to_num=None, unit_to_den=None):
    # try to see if we need to flip the units to make them convertable
    if unit_from_num is None and unit_to_num is None:
        numerator_factor = 1
        denominator_factor = unit_conversion_factor(unit_from_den, unit_to_den)
        flipped = False
    elif unit_from_den is None and unit_to_den is None:
        denominator_factor = 1
        numerator_factor = unit_conversion_factor(unit_from_num, unit_to_num)
        flipped = False
    else:
        try:
            numerator_factor = unit_conversion_factor(unit_from_num, unit_to_num)
            denominator_factor = unit_conversion_factor(unit_from_den, unit_to_den)
            flipped = False
        except ValueError:
            asdf
            pdb.set_trace()
            numerator_factor = unit_conversion_factor(unit_from_den, unit_to_num)
            denominator_factor = unit_conversion_factor(unit_from_num, unit_to_den)
            flipped = True
    return numerator_factor / denominator_factor, flipped


def unit_convert(data, unit_from_num=None, unit_from_den=None, unit_to_num=None, unit_to_den=None):
    """return data converted from unit_from to unit_to"""
    if (unit_from_num is not None) and (unit_to_num is not None) and (unit_from_den is not None) and (
                unit_to_den is not None):
        # we have two unit ratios
        factor, flipped = unit_conversion(unit_from_num, unit_from_den, unit_to_num, unit_to_den)
    elif (unit_from_num is not None) and (unit_to_num is not None):
        # units in the numerator
        if (unit_from_den is not None) or (unit_to_den is not None):
            # can't have units in just one other denominator
            raise ValueError('error converting a single unit to a ratio of units')
        factor, flipped = unit_conversion(unit_from_num=unit_from_num, unit_to_num=unit_to_num)
    elif (unit_from_den is not None) and (unit_to_den is not None):
        # units in the denominator
        if (unit_from_num is not None) or (unit_to_num is not None):
            # can't have units in just one other numerator
            raise ValueError('error converting a single unit to a ratio of units')
        factor, flipped = unit_conversion(unit_to_den=unit_to_den, unit_from_den=unit_from_den)
    elif (unit_from_num is not None) and (unit_to_den is not None):
        # units in the numerator of the first and denominator of the second
        factor, flipped = unit_conversion(unit_to_den, unit_from_num)
    elif (unit_from_den is not None) and (unit_to_num is not None):
        # units in the denominator of the first and numerator of the second
        factor, flipped = unit_conversion(unit_to_num, unit_from_den)
    else:
        raise ValueError('unit unable to be converted')
        flipped = False
        factor = 1
    if flipped:
        return 1 / data * factor
    else:
        return data * factor

def ensure_iterable_and_not_string(obj):
    if isinstance(obj, basestring):
        return [obj]
    else:
        try:
            iter(obj)
            return list(obj)
        except TypeError:
            return [obj]


def ensure_tuple(obj):
    if isinstance(obj, tuple):
        return obj
    else:
        return (obj,)


def df_slice(df, elements, levels, drop_level=True, reset_index=False, return_none=False):
    if df is None:
        return None
    elements, levels = ensure_iterable_and_not_string(elements), ensure_iterable_and_not_string(levels)
    if not len(levels):
        return None
    if len(elements) != len(levels) and len(levels) > 1:
        raise ValueError('Number of elements ' + str(len(elements)) + ' must match the number of levels ' + str(len(levels)))

    # special case where we use a different method to handle multiple elements
    if len(levels) == 1 and len(elements) > 1:
        df =  df.reset_index().loc[df.reset_index()[levels[0]].isin(elements)].set_index(df.index.names)
    else:
        # remove levels if they are not in the df
        elements, levels = zip(*[(e, l) for e, l in zip(elements, levels) if l in df.index.names])
        result = df.xs(elements, level=levels, drop_level=drop_level)
        df = result.reset_index().set_index(result.index.names) if reset_index else result
    if not len(df) and return_none:
        return None
    else:
        return df


def intersect(a, b):
    """ return the intersection of two lists """
    return list(set(a) & set(b))


def put_in_list(obj):
    if isinstance(obj, basestring) or isinstance(obj, pd.DataFrame):
        return [obj]
    else:
        try:
            iter(obj)
            return list(obj)
        except:
            return [obj]

def reduce_levels(df, allowed_levels, total_label=None, agg_function='sum'):
    reduce_levels = [x for x in df.index.names if x not in allowed_levels]
    if len(reduce_levels):
        return remove_df_levels(df, reduce_levels, total_label, agg_function)

def remove_df_levels(data, levels, total_label=None, agg_function='sum'):
    levels = [l for l in put_in_list(levels) if l in data.index.names]
    if not len(levels):
        return data
    if data.index.nlevels > 1:
        levels_to_keep = [l for l in data.index.names if l not in levels]
        group_slice = tuple([total_label if ((l in levels) and (total_label in e)) else slice(None)
        for l, e in zip(data.index.names, data.index.levels)])
        if total_label in group_slice:
            data = data.loc[group_slice]
        if agg_function == 'sum':
            return data.groupby(level=levels_to_keep).sum()
        elif agg_function =='mean':
            return data.groupby(level=levels_to_keep).mean()

        elif agg_function == 'max':
            return data.groupby(level=levels_to_keep).max()
        elif agg_function == 'min':
            return data.groupby(level=levels_to_keep).min()
        else:
            raise ValueError('unknown agg function specified')
    else:
        return data


def remove_df_elements(data, elements, level):
    if level in data.index.names:
        elements_to_keep = list(set(data.index.get_level_values(level)) - set(put_in_list(elements)))
        return reindex_df_level_with_new_elements(data, level, elements_to_keep)
    else:
        return data

def level_specific_indexer(df, levels, elements, axis=0):
    elements, levels = ensure_iterable_and_not_string(elements), ensure_iterable_and_not_string(levels)
    if len(elements) != len(levels):
        raise ValueError('Number of elements ' + str(len(elements)) + ' must match the number of levels ' + str(len(levels)))
    if axis == 0:
        names = df.index.names
    else:
        names = df.columns.names
    indexer = [slice(None)] * len(names)
    for level, element in zip(levels, elements):
        if axis == 0:
#            indexer[df.index.names.index(level)] = ensure_iterable_and_not_string(element)
            indexer[df.index.names.index(level)] = element
        if axis == 1:
#            indexer[df.columns.names.index(level)] = ensure_iterable_and_not_string(element)
            indexer[df.columns.names.index(level)] = element
    indexer = tuple(indexer)
    return indexer

def multi_merge(df_list):
    a = df_list[0]
    index_names = [x for x in a.index.names]
    for b in df_list[1:]:
        for name in b.index.names:
            if name not in index_names:
                index_names.append(b.index.names)
        common_headers = intersect(index_names, b.index.names)
        a = pd.merge(a, b.reset_index(), how='outer', on=common_headers)
    a.set_index(index_names, inplace=True)
    return a

def position_in_index(df, level_name):
    " return position in index of an index name in a dataframes multilevel index"
    return df.index.names.index(level_name)

def elements_in_index_level(df, level_name):
    return df.index.levels[position_in_index(df, level_name)]

def replace_index_name(df, replace_label, label=None):
    " Use replace_label to replace specified index label"
    df.index.names = [replace_label if x == label else x for x in df.index.names]


def ix_excl(df, exclude=None,axis=0):
    exclude = ensure_iterable_and_not_string(exclude)
    if axis == 0:
        return [x for x in df.index.names if x not in exclude]
    if axis == 1:
        return [x for x in df.columns.names if x not in exclude]


def ix_incl(df, include=None):
    include = ensure_iterable_and_not_string(include)
    include = [x for x in include if x in df.index.names]
    return include


def replace_column_name(df, replace_labels, labels=None):
    " Use replace_label to replace specified name label"
    if df.columns.dtype == 'O' and np.all(df.columns.names==[None]):
        #dct = dict(zip(ensure_iterable_and_not_string(replace_labels),ensure_iterable_and_not_string(labels)))
        #df.rename(columns=dct,inplace=True)
        df.columns = [replace_labels if x == labels else x for x in df.columns]
    elif df.columns.dtype == 'O' and np.all(df.columns==[None]):
        df.columns.names = [replace_labels if x == labels else x for x in df.columns.names]
    else:
        if not isinstance(replace_labels,basestring):
            for replace_label in replace_labels:
                    index = replace_labels.index(replace_label)
                    df.columns.names = [replace_label if x == labels[index]  else x for x in df.columns.names]
        else:
            df.columns.names = [replace_labels if x == labels else x for x in df.columns.names]

def replace_column(df, replace_labels, labels=None):
    " Use replace_label to replace specified name label"
    if not isinstance(replace_labels,basestring):
        for replace_label in replace_labels:
                index = replace_labels.index(replace_label)
                df.columns = [replace_label if x == labels[index]  else x for x in df.columns.names]
    else:
        df.columns= [replace_labels if x == labels else x for x in df.columns.names]

def expand_multi(df, levels_list, levels_names, how='outer', incremental=False, drop_index=None):
    """
    creates an additional layer in a mutlilevel index, repeating values from all other previous
    indexes
    """
    drop_index = ensure_iterable_and_not_string(drop_index)
    if incremental:
        levels_list = [ensure_iterable_and_not_string(levels_list)]
        for name, level in zip(df.index.names, df.index.levels):
            if name == drop_index:
                pass
            else:
                levels_names.append(name)
                levels_list.append(list(level))
    else:
        unfrozen_levels = []
        unfrozen_names = []
        for name, level in zip(levels_names, levels_list):
            if name in drop_index:
                pass
            else:
                unfrozen_levels.append([int(x) for x in level])
                unfrozen_names.append(name)
        levels_list = unfrozen_levels
        levels_names = unfrozen_names
    expand = pd.DataFrame(index=pd.MultiIndex.from_product(levels_list, names=levels_names),dtype='int64')
    common_headers = intersect(df.index.names, expand.index.names)
    levels_names = expand.index.names
    expand = expand.reset_index()
    df = df.reset_index()
    df = pd.merge(df, expand, on=common_headers, how=how)
    df = df.set_index(levels_names).sort_index()
    return df


def is_numeric(obj):
    """
    Checks to see object is numeric.

    Args:
        obj (object)

    Returns:
        Boolean
    """
    try:
        float(obj)
        return True
    except:
        return False

def decay_growth_df(extrap_type, rate, reverse, vintages, years):
    if reverse:
        rate = -rate
    vintages = np.asarray(vintages)
    years = np.asarray(years)
    ages = np.zeros((len(vintages), len(years)))
    for i, vintage in enumerate(vintages):
        ages[i] = years - vintage
    if extrap_type == 'linear':
        fill = (1 + (rate * ages))
        fill = np.triu(fill, k=(min(vintages)-min(years)))
    elif extrap_type == 'exponential':
        fill = ((1 + rate) ** ages)
        fill = np.triu(fill, k=(min(vintages)-min(years)))
    elif extrap_type is None:
        exist = np.ones((len(vintages), len(years)))
        fill = np.triu(exist, k=(min(vintages)-min(years)))
    df = pd.DataFrame(fill, index=vintages, columns=years)
    df.index.rename('vintage', inplace=True)
    df.columns.names = [None]
    df.data_type = 'intensity'
    return df


def book_life_df(book_life, vintages, years):
    vintages = np.asarray(vintages)
    years = np.asarray(years)
    exist = np.ones((len(years), len(vintages)))
    lower_exist = np.triu(exist, k=(min(years) - min(vintages)))
    upper_exist = np.triu(exist, k=book_life)
    df = pd.DataFrame(np.subtract(lower_exist, upper_exist), index=vintages, columns=years)
    df.index.rename('vintage', inplace=True)
    df.columns.names = [None]
    return df


def initial_book_life_df(book_life, mean_lifetime, vintages, years):
    """ creates a linear decay from initial year to mid-year of book life
    """
    years = np.asarray(years)
    vintages = np.asarray(vintages)
    vintages = np.concatenate(((min(vintages) - 1,), vintages))
    exist = np.zeros((len(vintages), len(years)))
    maximum_remaining = book_life/float(mean_lifetime)
    for i, year in enumerate(years):
        for vintage in [vintages[0]]:
            exist[0, i] = max(maximum_remaining * 1 - ((year-vintage)/float(book_life)),0)
    df = pd.DataFrame(exist, index=vintages, columns=years)
    df.index.rename('vintage', inplace=True)
    df.columns.names = [None]
    return df


def convert_age(self, reverse, vintages, years, attr_from='values', attr_to='values'):
    """
    Broadcasts vintage values that decay over time to year columns
    """

    df = getattr(self,attr_from)
    index_order = df.index.names
    if hasattr(self, 'age_growth_or_decay') and self.age_growth_or_decay is not None:
        decay = decay_growth_df(self.age_growth_or_decay_type, self.age_growth_or_decay, reverse, vintages, years)
        # decay = expand_multi(decay, getattr(self,attr_from).index.levels, getattr(self,attr_from).index.names)
        decay.data_type = 'total'
        setattr(self, attr_to,
                DfOper.mult([decay, df]).reorder_levels(index_order))
    else:
        decay = decay_growth_df(None, None, False, vintages, years)
        # decay = expand_multi(decay, getattr(self,attr_from).groupyby(level=ix_excl(getattr(self,attr_from), 'vintage')).sum().index.levels,  getattr(self,attr_from).groupyby(level=ix_excl(getattr(self,attr_from), 'vintage')).sum().index.names)
        decay.data_type = 'total'
        setattr(self, attr_to, DfOper.mult([decay, df]).reorder_levels(index_order))


def create_markov_matrix(markov_vector, num_techs, num_years, steps_per_year=1):
    markov_matrix = np.zeros((num_techs, num_years*steps_per_year + 1, num_years*steps_per_year))
    for i in range(int(num_years*steps_per_year)):
        markov_matrix[:, :-i - 1, i] = np.transpose(markov_vector[i:-1])
    markov_matrix[:, -1, :] = markov_matrix[:, -2, :]
    if len(range(int(num_years*steps_per_year)))>1:
        markov_matrix[:, :, -1] = 0
    return np.cumprod(markov_matrix, axis=2)

def vintage_year_matrix(years,vintages):
    index = pd.MultiIndex.from_product([years,vintages],names=['year','vintage'])
    data = index.get_level_values('year')==index.get_level_values('vintage')
    df = pd.DataFrame(data,index=index,columns = ['value'])
    return df


def create_markov_vector(decay_function, survival_function):
    markov_vector = 1 - decay_function[1:, :] / survival_function[:-1, :]
    markov_vector[survival_function[:-1, :] == 0] = 0
    return np.vstack((markov_vector, markov_vector[-1]))


def mean_weibul_factor(beta):
    """ beta is shape parameter of weibul
    http://reliawiki.org/index.php/The_Weibull_Distribution
    """
    return scipy.special.gamma(1 + 1. / beta)


def median_weibul_factor(beta):
    """ beta is shape parameter of weibul
    http://reliawiki.org/index.php/The_Weibull_Distribution
    """
    return (np.log(2)) ** (1. / beta)


def std_weibul_factor(beta):
    """ beta is shape parameter of weibul
    http://reliawiki.org/index.php/The_Weibull_Distribution
    """
    return ((scipy.special.gamma(1 + 2. / beta)) - (scipy.special.gamma(1 + 1. / beta) ** 2)) ** .5


def create_weibul_coefficient_of_variation(smallest_beta=.02, largest_beta=250, resolution=0.01):
    """ beta is shape parameter of weibull https://en.wikipedia.org/wiki/Weibull_distribution
        beta < 1 indicates that the failure rate decreases over time. This happens if there is significant "infant mortality",
        or defective items failing early and the failure rate decreasing over time as the defective items are weeded out
        of the population.

        beta = 1 indicates that the failure rate is constant over time. This might suggest random external events
        are causing mortality, or failure.

        beta > 1 indicates that the failure rate increases with time. This happens if there is an "aging" process,
        or parts that are more likely to fail as time goes on.
    """
    # mean is almost always higher than median
    beta = np.arange(smallest_beta, largest_beta + resolution, resolution)
    mean, median, std = mean_weibul_factor(beta), median_weibul_factor(beta), std_weibul_factor(beta)
    weibul_coeff_of_var = {}
    weibul_coeff_of_var['beta'] = beta
    weibul_coeff_of_var['mean/std'] = mean / std
    weibul_coeff_of_var['median/mean'] = median / mean
    weibul_coeff_of_var['median/std'] = median / std
    return weibul_coeff_of_var


def nearest_index(array, value):
    return (np.abs(array - value)).argmin()


def replace_index_label(df, dct, level_name):
    index = df.index
    level = position_in_index(df, level_name)
    index.set_levels([[dct.get(item, item) for item in names] if i == level else names
                      for i, names in enumerate(index.levels)], inplace=True)


def difference_in_df_elements(a, b, ignore_levels=None, return_bool=True):
    """ Look in common data frame level names for differences in elements
    return two dictionaries with key as common level and value as differences
    """
    a_names = a.index.names if a.index.nlevels > 1 else [a.index.name]
    b_names = b.index.names if b.index.nlevels > 1 else [b.index.name]
    common_levels = list(set(a_names) & set(b_names))
    elements_a_not_in_b, elements_b_not_in_a = {}, {}
    for cl in common_levels:
        if ignore_levels is not None and cl in ignore_levels:
            continue
        a_elements, b_elements = get_elements_from_level(a, cl), get_elements_from_level(b, cl)
        if len(list(set(a_elements) - set(b_elements))):
            elements_a_not_in_b[cl] = list(set(a_elements) - set(b_elements))
        if len(list(set(b_elements) - set(a_elements))):
            elements_b_not_in_a[cl] = list(set(b_elements) - set(a_elements))
    if return_bool:
        return True if elements_a_not_in_b else False, True if elements_b_not_in_a else False
    else:
        return elements_a_not_in_b, elements_b_not_in_a


def difference_in_df_names(a, b, return_bool=True):
    """ Look at data frame level names for differences
    return two lists with names in a not in b and names in b not in a
    """
    a_names = a.index.names if a.index.nlevels > 1 else [a.index.name]
    b_names = b.index.names if b.index.nlevels > 1 else [b.index.name]
    names_a_not_in_b = list(set(a_names) - set(b_names))
    names_b_not_in_a = list(set(b_names) - set(a_names))
    if return_bool:
        return True if names_a_not_in_b else False, True if names_b_not_in_a else False
    else:
        return names_a_not_in_b, names_b_not_in_a


# def difference_in_df_names(a, b, return_bool=True):
# """ Look at data frame level names for differences
# return two lists with names in a not in b and names in b not in a
# """
# a_names = a.index.names if a.index.nlevels>1 else [a.index.name]
# b_names = b.index.names if b.index.nlevels>1 else [b.index.name]
# names_a_not_in_b = True if list(set(a_names)-set(b_names)) else False
# names_b_not_in_a = True if list(set(b_names)-set(a_names)) else False
# if return_bool:
# return True if names_a_not_in_b else False, True if names_b_not_in_a else False
# else:
# return names_a_not_in_b, names_b_not_in_a

def rotate(l, x):
  return l[-x:] + l[:-x]


def reorder_b_to_match_a(b, a):
    # levels match, but b needs to be reordered
    if a.index.names == b.index.names:
        return b
    else:
        order_for_b = [position_in_index(b, cl) for cl in a.index.names if cl in b.index.names]
        return b.reorder_levels(order_for_b)


def get_elements_from_level(df, level_name):
    names = df.index.names if df.index.nlevels > 1 else [df.index.name]
    return [] if level_name not in names else (
        df.index.levels[position_in_index(df, level_name)] if df.index.nlevels > 1 else df.index)


class DfOper:
    @staticmethod
    def add(df_iter, expandable=True, collapsible=True, join=None, fill_value=0, non_expandable_levels=('year', 'vintage')):
        return DfOper._operation_helper(df_iter, '+', expandable, collapsible, join, fill_value, non_expandable_levels)

    @staticmethod
    def mult(df_iter, expandable=True, collapsible=True, join=None, fill_value=0, non_expandable_levels=('year', 'vintage')):
        return DfOper._operation_helper(df_iter, '*', expandable, collapsible, join, fill_value, non_expandable_levels)

    @staticmethod
    def divi(df_iter, expandable=True, collapsible=True, join=None, fill_value=0, non_expandable_levels=('year', 'vintage')):
        return DfOper._operation_helper(df_iter, '/', expandable, collapsible, join, fill_value, non_expandable_levels)

    @staticmethod
    def subt(df_iter, expandable=True, collapsible=True, join=None, fill_value=0, non_expandable_levels=('year', 'vintage')):
        return DfOper._operation_helper(df_iter, '-', expandable, collapsible, join, fill_value, non_expandable_levels)

    @staticmethod
    def none(df_iter, expandable=True, collapsible=True, join=None, fill_value=0, non_expandable_levels=('year', 'vintage')):
        return DfOper._operation_helper(df_iter, None, expandable, collapsible, join, fill_value, non_expandable_levels)

    @staticmethod
    def repl(df_iter, expandable=True, collapsible=True, join=None, fill_value=0, non_expandable_levels=('year', 'vintage')):
        return DfOper._operation_helper(df_iter, 'replace', expandable, collapsible, join, fill_value, non_expandable_levels)

    @staticmethod
    def _operation_helper(df_iter, opr, expandable=True, collapsible=True, join=None, fill_value=0, non_expandable_levels=('year', 'vintage')):
        if not len(df_iter):
            return None
        expandable = DfOper.fill_default_char(expandable, len(df_iter))
        collapsible = DfOper.fill_default_char(collapsible, len(df_iter))
        return_df = None
        for i, df in enumerate(df_iter):
            if df is None:
                continue
            return_df = df if return_df is None else \
                        DfOper._df_operation(return_df, df, opr, join, fill_value,
                                             a_can_collapse=collapsible[i-1], a_can_expand=expandable[i-1],
                                             b_can_collapse=collapsible[i], b_can_expand=expandable[i],
                                             non_expandable_levels=non_expandable_levels)
        return return_df

    @staticmethod
    def fill_default_char(char, num):
        char = put_in_list(char)
        if len(char) == 1:
            return [char[0]] * num
        elif len(char) != num:
            raise ValueError('Number of data_types must equal the number of DataFrames')
        else:
            return char

    @staticmethod
    def _df_operation(a, b, action, join, fill_value, a_can_collapse, a_can_expand, b_can_collapse, b_can_expand, non_expandable_levels):
        # First check for errors
        DfOper._raise_errors(a, b, action, a_can_collapse, a_can_expand, b_can_collapse, b_can_expand)

        new_a, new_b = DfOper._account_for_mismatched_elements(a, b, fill_value, a_can_collapse, a_can_expand, b_can_collapse, b_can_expand, non_expandable_levels)

        # multi index level differences
        names_a_not_in_b, names_b_not_in_a = difference_in_df_names(new_a, new_b)
        if not names_a_not_in_b and not names_b_not_in_a:
            join = join if join is not None else ('outer' if fill_value is not None else 'left')
            new_a, new_b = new_a.align(reorder_b_to_match_a(new_b, new_a), join=join, fill_value=fill_value, axis=0,
                                       copy=False)
            return DfOper._operate(new_a, new_b, action)
        else:
            # if quick_merge: # this is still a work in progress
            #     new_a, new_b = DfOper._quick_merge_using_concat(new_a, new_b, join, fill_value, a_can_collapse, a_can_expand, b_can_collapse, b_can_expand)
            # else:
            new_a, new_b = DfOper._merge_then_separate_for_operation(new_a, new_b, join, fill_value, a_can_collapse, a_can_expand, b_can_collapse, b_can_expand)
            return DfOper._operate(new_a, new_b, action)

    # @staticmethod
    # def _quick_merge_using_concat(a, b, join, fill_value, a_can_collapse, a_can_expand, b_can_collapse, b_can_expand):
    #     names_a_not_in_b, names_b_not_in_a = difference_in_df_names(a, b, return_bool=False)
    #
    #     a_names = a.index.names if a.index.nlevels > 1 else [a.index.name]
    #     b_names = b.index.names if b.index.nlevels > 1 else [b.index.name]
    #     common_names = list(set(a_names) & set(b_names))
    #     # Eliminate levels for one when the other is not expandable
    #     new_a = a.groupby(level=common_names).sum() if (len(names_a_not_in_b) > 0 and not b_can_expand) and a_can_collapse else a
    #     new_b = b.groupby(level=common_names).sum() if (len(names_b_not_in_a) > 0 and not a_can_expand) and b_can_collapse else b
    #
    #     # we need to add names_b_not_in_a to a
    #     for missing_name in names_b_not_in_a:
    #         missing_elements = sorted(new_b.index.get_level_values(missing_name).unique())
    #         new_a = pd.concat([new_a]*len(missing_elements), keys=missing_elements, names=[missing_name])
    #         # TODO in the documentation there seems to be a way to do this without a for loop, but I haven't figured it out. Below is the start of the effort.
    #         # missing_elements = [tuple(sorted(b.index.get_level_values(missing_name).unique())) for missing_name in names_b_not_in_a]
    #         # num_repeats = reduce(mul, [len(me) for me in missing_elements], 1)
    #         # a = pd.concat([a] * num_repeats, keys=tuple(missing_elements), names=names_b_not_in_a+new_a.index.names)
    #
    #     # we need to add names_a_not_in_b to b
    #     for missing_name in names_a_not_in_b:
    #         missing_elements = sorted(new_a.index.get_level_values(missing_name).unique())
    #         new_b = pd.concat([new_b]*len(missing_elements), keys=missing_elements, names=[missing_name])
    #
    #     # join = join if join is not None else ('outer' if fill_value is not None else 'left')
    #     # new_a, new_b = new_a.align(reorder_b_to_match_a(new_b, new_a), join=join, fill_value=fill_value, axis=0, copy=False)
    #     new_b = reorder_b_to_match_a(new_b, new_a)
    #     return new_a, new_b

    @staticmethod
    def _operate(a, b, action):
        col = b.columns if len(b.columns) > len(a.columns) else a.columns
        if action == '*':
            return pd.DataFrame(a.values * b.values, index=a.index, columns=col)
        elif action == '/':
            return pd.DataFrame(a.values / b.values, index=a.index, columns=col)
        elif action == '+':
            return pd.DataFrame(a.values + b.values, index=a.index, columns=col)
        elif action == '-':
            return pd.DataFrame(a.values - b.values, index=a.index, columns=col)
        elif action == None:
            return pd.DataFrame(a.values, index=a.index, columns=col)
        elif action == 'replace':
            return pd.DataFrame(b.values, index=a.index, columns=col)

    @staticmethod
    def _raise_errors(a, b, action, a_can_collapse, a_can_expand, b_can_collapse, b_can_expand):
        a_names = a.index.names if a.index.nlevels > 1 else [a.index.name]
        b_names = b.index.names if b.index.nlevels > 1 else [b.index.name]
        if (None in a_names) or (None in b_names):
            raise ValueError('All DataFrame index levels must be named for df_operation')
        # multi index level differences
        names_a_not_in_b, names_b_not_in_a = difference_in_df_names(a, b)

        # Missmatched levels
        if (names_b_not_in_a and not a_can_expand) and not b_can_collapse:
            raise ValueError('DataFrame b has extra levels, DataFrame a cannot expand, and DataFrame b cannot collapse')
        if (names_a_not_in_b and not b_can_expand) and not a_can_collapse:
            raise ValueError('DataFrame a has extra levels, DataFrame b cannot expand, and DataFrame a cannot collapse')

    @staticmethod
    def _reindex_dfs_so_elements_match(a, b, level_names, how):
        """ This is necessary because if we fill, we don't want to fill over years or vintages
        Clean timeseries is used to fill holes in years/vintages
        how is intersect or union
        """

        def reindex_one_level(a, b, level_name, how):
            a_elements, b_elements = get_elements_from_level(a, level_name), get_elements_from_level(b, level_name)
            if how == 'union':
                common_elements = list(set(a_elements) & set(b_elements))
            elif how == 'intersect':
                common_elements = list(set(a_elements) | set(b_elements))

            a_not_in_b, b_not_in_a = list(set(a_elements) - set(b_elements)), list(set(b_elements) - set(a_elements))
            if how == 'union':
                new_a = reindex_df_level_with_new_elements(a, level_name, common_elements) if len(a_not_in_b) else a
                new_b = reindex_df_level_with_new_elements(b, level_name, common_elements) if len(b_not_in_a) else b
            elif how == 'intersect':
                new_a = reindex_df_level_with_new_elements(a, level_name, common_elements) if (
                    len(a_not_in_b) or len(b_not_in_a)) else a
                new_b = reindex_df_level_with_new_elements(b, level_name, common_elements) if (
                    len(a_not_in_b) or len(b_not_in_a)) else b
            return new_a, new_b

        a_names = a.index.names if a.index.nlevels > 1 else [a.index.name]
        b_names = b.index.names if b.index.nlevels > 1 else [b.index.name]

        new_a, new_b = a, b
        for level_name in put_in_list(level_names):
            if (level_name not in a_names) or (level_name not in b_names):
                continue
            new_a, new_b = reindex_one_level(new_a, new_b, level_name, how)

        return new_a, new_b

    @staticmethod
    def _account_for_mismatched_elements(a, b, fill_value, a_can_collapse, a_can_expand, b_can_collapse, b_can_expand, non_expandable_levels):
        # Difference in the elements within layers
        elements_a_not_in_b, elements_b_not_in_a = difference_in_df_elements(a, b)
        if (elements_a_not_in_b or elements_b_not_in_a) and non_expandable_levels is not None:
            # Make 'year' and 'vintage' match between dataframes
            new_a, new_b = DfOper._reindex_dfs_so_elements_match(a, b, level_names=non_expandable_levels, how='union')

            # After year and vintage match, do we have others that don't match?
            elements_a_not_in_b, elements_b_not_in_a = difference_in_df_elements(new_a, new_b, return_bool=False)
            if fill_value is None:
                if elements_a_not_in_b:
                    if not a_can_collapse:
                        raise ValueError(
                            'No fill value specified for missing elements in b and DataFrame a cannot be collapsed')
                    new_a = remove_df_levels(new_a, elements_a_not_in_b.keys())

                if elements_b_not_in_a:
                    if not b_can_collapse:
                        raise ValueError(
                            'No fill value specified for missing elements in a and DataFrame b cannot be collapsed')
                    new_b = remove_df_levels(new_b, elements_b_not_in_a.keys())

            return new_a, new_b
        else:
            return a, b

    @staticmethod
    def _merge_then_separate_for_operation(a, b, join, fill_value, a_can_collapse, a_can_expand, b_can_collapse,
                                           b_can_expand):
        a_names = a.index.names if a.index.nlevels > 1 else [a.index.name]
        b_names = b.index.names if b.index.nlevels > 1 else [b.index.name]

        common_names = list(set(a_names) & set(b_names))
        names_a_not_in_b, names_b_not_in_a = list(set(a_names) - set(b_names)), list(set(b_names) - set(a_names))
        if not len(common_names):
            raise ValueError('DataFrames have no common index level names for a merge')
        a_cols, b_cols = a.columns.values, b.columns.values
        merged_a_cols = [str(col) + "_a" if col in b_cols else col for col in a_cols]
        merged_b_cols = [str(col) + "_b" if col in a_cols else col for col in b_cols]

        # Eliminate levels for one when the other is not expandable
        new_a = a.groupby(level=common_names).sum() if (len(names_a_not_in_b) > 0 and not b_can_expand) and a_can_collapse else a
        new_b = b.groupby(level=common_names).sum() if (len(names_b_not_in_a) > 0 and not a_can_expand) and b_can_collapse else b

        # Reindex so that elements within levels match
        if fill_value is not None:
            new_a, new_b = DfOper._reindex_dfs_so_elements_match(new_a, new_b, level_names=common_names, how='intersect')

        # Default for join is left unless b has more columns, then we assume we want to join on it
        if join is None:
            join = 'right' if len(b.columns) > len(a.columns) else 'left'

        c = pd.merge(new_a.reset_index(), new_b.reset_index(), how=join, on=common_names, suffixes=["_a", "_b"])

        new_index = [x for x in c.columns.tolist() if (x not in merged_a_cols) and (x not in merged_b_cols)]
        # This next bit of code helps return the levels in a familiar order
        alen, blen = float(len(a_names) - 1), float(len(b_names) - 1)
        alen, blen = max(alen, 1), max(blen, 1)  # avoid error from dividing by zero
        average_location = [a_names.index(cand) / alen if cand in a_names else b_names.index(cand) / blen for cand in new_index]
        new_index = [new_index[ni] for ni in np.argsort(average_location)]
        c = c.set_index(new_index).sort()
        # new_a, new_b = c[new_index + merged_a_cols], c[new_index + merged_b_cols]
        new_a, new_b = c[merged_a_cols], c[merged_b_cols]
        # new_a = new_a.set_index(new_index).sort()
        # new_b = new_b.set_index(new_index).sort()

        # new_a.sort(inplace=True)
        # new_b.sort(inplace=True)

        new_a = new_a.rename(columns=dict(zip(merged_a_cols, a_cols)))
        new_b = new_b.rename(columns=dict(zip(merged_b_cols, b_cols)))

        if fill_value is not None:
            new_a = new_a.fillna(fill_value)
            new_b = new_b.fillna(fill_value)

        return new_a, new_b


class OrderedSet(MutableSet):
    def __init__(self, iterable=None):
        self.end = end = []
        end += [None, end, end]  # sentinel node for doubly linked list
        self.map = {}  # key --> [key, prev, next]
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.map)

    def __contains__(self, key):
        return key in self.map

    def add(self, key):
        if key not in self.map:
            end = self.end
            curr = end[1]
            curr[2] = end[1] = self.map[key] = [key, curr, end]

    def discard(self, key):
        if key in self.map:
            key, prev, next = self.map.pop(key)
            prev[2] = next
            next[1] = prev

    def __iter__(self):
        end = self.end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self.end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def pop(self, last=True):
        if not self:
            raise KeyError('set is empty')
        key = self.end[1][0] if last else self.end[2][0]
        self.discard(key)
        return key

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return set(self) == set(other)


def flatten_list(list_to_flatten):
    """Returns a list with sublists removed"""
    return [item for sublist in list_to_flatten for item in sublist]

def reindex_df_level_with_new_elements(df, level_name, new_elements, fill_value=np.nan):
    if (df.index.nlevels > 1 and level_name not in df.index.names) or (df.index.nlevels == 1 and level_name != df.index.name):
        return df
    if df.index.nlevels > 1:
        index_i = df.index.names.index(level_name)
        const_labels = OrderedSet([tuple([z if i != index_i else -1 for i, z in enumerate(lab)]) for lab in zip(*df.index.labels)])
        new_labels = flatten_list([[tuple([z if i != index_i else n for i, z in enumerate(lab)]) for n in range(len(new_elements))] for lab in const_labels])
        full_elements = [new_elements if name == level_name else level for name, level in zip(df.index.names, df.index.levels)]
        temp = df.reindex(index=pd.MultiIndex(levels=full_elements, labels=zip(*new_labels), names=df.index.names), fill_value=fill_value)
        return temp.reset_index().set_index(temp.index.names).sort()
    else:
        temp = df.reindex(index=pd.Index(new_elements, name=df.index.name), fill_value=fill_value)
        return temp.reset_index().set_index(temp.index.names).sort()

def find_weibul_beta(mean_lifetime, lifetime_variance):
    """http://interstat.statjournals.net/YEAR/2000/articles/0010001.pdf"""
    if lifetime_variance == 0:
        return cfg.weibul_coeff_of_var['beta'][-1]
    else:
        mean_to_std = mean_lifetime / (lifetime_variance ** .5)
        return cfg.weibul_coeff_of_var['beta'][nearest_index(cfg.weibul_coeff_of_var['mean/std'], mean_to_std)]


def add_and_set_index(df, name, elements, index_location=None):
    name, elements = ensure_iterable_and_not_string(name), ensure_iterable_and_not_string(elements)
    return_df = pd.concat([df]*len(elements), keys=elements, names=name).sort_index()
    if index_location:
        return_df = return_df.swaplevel(-1, index_location).sort_index()
    return return_df

def determ_energy(unit):
    """
    determines whether a unit is an energy unit

    """
    # TODO check if static method appropriate
    if cfg.ureg.Quantity(unit).dimensionality == cfg.ureg.Quantity(cfg.calculation_energy_unit).dimensionality:
        return True


def sum_chunk(x, chunk_size, axis=-1):
    """http://stackoverflow.com/questions/18582544/sum-parts-of-numpy-array"""
    shape = x.shape
    if axis < 0:
        axis += x.ndim
    shape = shape[:axis] + (shape[axis]/chunk_size, chunk_size) + shape[axis+1:]
    return np.sum(x.reshape(shape), axis=axis+1)


def mean_chunk(x, chunk_size, axis=-1):
    """http://stackoverflow.com/questions/18582544/sum-parts-of-numpy-array"""
    shape = x.shape
    if axis < 0:
        axis += x.ndim
    shape = shape[:axis] + (shape[axis]/chunk_size, chunk_size) + shape[axis+1:]
    return np.mean(x.reshape(shape), axis=axis+1)

def sum_chunk_vintage(x, chunk_size, axis=-1):
    """Reshapes and sum the rows after 1 and then appends the first row after"""
    shape = x.shape
    slice_index = tuple([slice(None) if e!=axis else slice(1, s) for e, s in enumerate(shape)])
    residual_index = tuple([slice(None) if e!=axis else 0 for e, s in enumerate(shape)])

    if axis < 0:
        axis += x.ndim

    residual_shape = shape[:axis] + (1,) + shape[axis+1:]
    shape = shape[:axis] + ((shape[axis]-1)/chunk_size, chunk_size) + shape[axis+1:]
    return np.concatenate((x[residual_index].reshape(residual_shape), np.sum(x[slice_index].reshape(shape), axis=axis+1)), axis=axis)

