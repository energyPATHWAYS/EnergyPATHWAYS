# -*- coding: utf-8 -*-
"""
Created on Wed Apr 08 10:12:52 2015

@author: Ben Haley & Ryan Jones

Contains unclassified global functions

"""

import config
import pint
import sqlite3 as sqlite
import pandas as pd
import os
import numpy as np
from time_series import TimeSeries
from collections import defaultdict, OrderedDict, MutableSet
import time
import csv
import inspect
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

from scipy.special import gamma

def upper_dict(query,append=None):
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


def object_att_from_table(tablename, id, primary_key='id'):
    table_headers = [h for h in sql_read_headers(tablename) if h != primary_key]
    attributes = sql_read_table(tablename, column_names=table_headers, **dict([(primary_key, id)]))
    if not len(table_headers):
        list_of_tuples = []
    elif len(table_headers) == 1:
        list_of_tuples = [(table_headers[0], attributes)]
    else:
        list_of_tuples = zip(table_headers, attributes)
    for t in list_of_tuples:
        try:
            add_tuple = id_to_name(t[0], t[1], 'tuple')
            list_of_tuples.append(add_tuple)
        except:
            pass
    return list_of_tuples


def tuple_subset(tup, header, head_to_remove):
    if len(tup) != len(header):
        raise ValueError('Length of header must match the length of tuple')
    head_to_remove = [x for x in head_to_remove if x in header]
    index_to_remove = [header.index(e) for e in head_to_remove]
    return tuple([t for i, t in enumerate(tup) if i not in index_to_remove])


def id_to_name(col, att, return_type='item'):
    keys = sql_read_table('IDMap', 'identifier_id')
    id_dict = {}
    for k in keys:
        value = sql_read_table('IDMap', 'ref_table', identifier_id=k)
        id_dict[k] = value
    if 'name' in sql_read_headers(id_dict[col]):
        new_att = sql_read_table(id_dict[col], 'name', id=att)
    else:
        new_att = att
    new_col = col[:-3]
    if return_type == 'tuple':
        return (new_col, new_att)
    elif return_type == 'item':
        return new_att


def empty_df(index, columns, fill_value=0.0, data_type=None):
    df = pd.DataFrame(fill_value, index=index, columns=columns).sort_index()
    df.data_type = data_type
    return df


def sql_read_table(table_name, column_names='*', return_unique=False, return_iterable=False, **filters):
    """Get data from a table filtering by columns
    key word arguments give column name, column criteria pairs

    example:
        util.sql_read_table('DemandDriversID', 'ID', driver='oil and gas mining VOS')
    """
    if not isinstance(column_names, basestring):
        column_names = ', '.join(column_names)
    query = 'select ' + column_names + ' from %s' % table_name
    if len(filters):
        datatypes = sql_get_datatype(table_name, filters.keys())
        list_of_filters = ['"' + col + '"=' + fix_sql_query_type(fil, datatypes[col]) for col, fil in filters.items() if
                           fil is not None]
        if list_of_filters == []:
            data = [None]
        else:
            query = query + " where " + " and ".join(list_of_filters)
            data = [tup[0] if len(tup) == 1 else tup for tup in config.cfg.cur.execute(query)]
    else:
        data = [tup[0] if len(tup) == 1 else tup for tup in config.cfg.cur.execute(query)]
    if return_unique:
        data = list(set(data))
    # pull out the first element if length is 1 and we don't want to return an iterable
    if len(data) == 0 or data == [None]:
        return [] if return_iterable else None
    elif len(data) == 1:
        return data if return_iterable else data[0]
    else:
        return data


def sql_get_datatype(table_name, column_names):
    if isinstance(column_names, basestring):
        column_names = [column_names]
    table_info_cur = config.cfg.cur.execute("PRAGMA table_info(%s)" % table_name)
    table_info = table_info_cur.fetchall()
    return dict([(tup[1], tup[2]) for tup in table_info if tup[1] in column_names])


def fix_sql_query_type(string, sqltype):
    if sqltype == 'INTEGER':
        return str(string)
    else:
        return "'" + str(string) + "'"


def sql_read_dataframe(table_name, index_column_name=None, data_column_names='*', **filters):
    """
    Read data and create a dataframe
    Example:
        data = util.sql_read_dataframe('DemandDrivers', index_column_name='year', data_column_names='value',
                                        ID=1, gau='total', dau='single-family', add='total')
    """
    if not isinstance(index_column_name, basestring):
        if len(index_column_name) > 1:
            raise ValueError("Only one index_column_name should be given")
        else:
            index_column_name = index_column_name[0]

    if data_column_names == '*':
        data_column_names = [n for n in sql_read_headers(table_name) if n != index_column_name]
    if (not isinstance(data_column_names, list)) and (not isinstance(data_column_names, tuple)):
        data_column_names = [data_column_names]

    data = sql_read_table(table_name, column_names=data_column_names, **filters)
    if index_column_name is not None:
        index = sql_read_table(table_name, column_names=index_column_name, **filters)
        if (not len(index)) or (not len(data)):
            raise ValueError('sql_read_dataframe returned empty data')

        data_frame = pd.DataFrame(data=data, index=index, columns=data_column_names)
        data_frame.sort_index(inplace=True)
    else:
        data_frame = pd.DataFrame(data=data, columns=data_column_names)

    return data_frame


def sql_read_headers(table_name):
    table_info_cur = config.cfg.cur.execute("PRAGMA table_info(%s)" % table_name)
    table_info = table_info_cur.fetchall()
    # return list of all column headers
    return [tup[1] for tup in table_info]


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
                quant_from = config.cfg.ureg.Quantity(unit_from)
            try:
                unit_to.magnitude()
                quant_to = unit_to
            except:
                quant_to = config.cfg.ureg.Quantity(unit_to)
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
    currency_to = config.cfg.cfgfile.get('case', 'currency_id') if currency_to is None else currency_to
    currency_from_values = sql_read_table('CurrenciesConversion', 'value', currency_id=currency_from,
                                          currency_year_id=currency_from_year)
    currency_from_value = np.asarray(currency_from_values).mean()
    currency_to_values = sql_read_table('CurrenciesConversion', 'value', currency_id=currency_to,
                                        currency_year_id=currency_from_year)
    currency_to_value = np.asarray(currency_to_values).mean()
    return currency_to_value / currency_from_value


def inflation_rate(currency, currency_from_year, currency_to_year=None):
    """calculate inflation rate between two years in a specified currency"""
    currency_to_year = config.cfg.cfgfile.get('case', 'currency_year_id') if currency_to_year is None else currency_to_year
    currency_from_values = sql_read_table('InflationConversion', 'value', currency_id=currency,
                                          currency_year_id=currency_from_year)
    currency_from_value = np.asarray(currency_from_values).mean()
    currency_to_values = sql_read_table('InflationConversion', 'value', currency_id=currency,
                                        currency_year_id=currency_to_year)
    currency_to_value = np.asarray(currency_to_values).mean()
    return currency_to_value / currency_from_value


def currency_convert(data, currency_from, currency_from_year):
    """converts cost data in original currency specifications (currency,year) to model currency and year"""
    currency_to, currency_to_year = config.cfg.cfgfile.get('case', 'currency_id'), config.cfg.cfgfile.get('case', 'currency_year_id')
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
                c = exchange_rate(currency_from=41, currency_from_year=currency_to_year
                                  , currency_to=currency_to)
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
        print "error"
        flipped = False
        factor = 1
    if flipped:
        return 1 / data * factor
    else:
        return data * factor


def geo_table(cur):
    """
    update GeographyMapKey column indexes in pathways.db when new geography or map key is added
    """
    table_info_query = "PRAGMA table_info(GeographyMap)"
    table_info_cur = cur.execute(table_info_query)
    table_info = table_info_cur.fetchall()
    # return list of all column headers except 'name'
    db_column_headers = [tup[1] for tup in table_info]
    geography_query = 'select "geography" from Geographies'
    geography_column = cur.execute(geography_query)
    geographies = [tup[0] for tup in list(set(geography_column))]
    map_key_query = 'select "geography_map_key" from GeographyMapKeys'
    map_key_cur = cur.execute(map_key_query)
    map_keys = [tup[0] for tup in list(set(map_key_cur))]
    for geography in geographies:
        # add column names for geographies identified in Geographies table
        if geography not in db_column_headers:
            add_geography_query = 'ALTER TABLE GeographyMap ADD COLUMN "%s" TEXT' % geography
            cur.execute(add_geography_query)
    for key in map_keys:
        # add column names for map_keys identified in GeographyMapKeys table
        if key not in db_column_headers:
            add_map_key_query = 'ALTER TABLE GeographyMap ADD COLUMN "%s" REAL' % key
            cur.execute(add_map_key_query)


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


def df_slice(df, elements, levels):
    elements, levels = ensure_iterable_and_not_string(elements), ensure_iterable_and_not_string(levels)
    if len(elements) != len(levels):
        raise ValueError(
            'Number of elements ' + str(len(elements)) + ' must match the number of levels ' + str(len(levels)))
    # remove elements if they are not in the df
    elements, levels = zip(*[(e, l) for e, l in zip(elements, levels) if l in df.index.names])
    if len(levels):
        return df.xs(elements, level=levels)
    else:
        return None


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
        else:
            raise ValueError('unknown agg function specified')
    else:
        return data


def remove_df_elements(data, elements, level):
    if level in data.index.names:
        return data.drop(put_in_list(elements), level=level)
    else:
        return data


#def multindex_operation_list(df_list, operation, how='left', return_col_name='value', drop_indices=None):
#    if not len(df_list):
#        return None
#
#    if len(df_list) == 1:
#        return df_list[0]
#
#    # multiply lists recursively
#    a = df_list[0]
#    for b in df_list[1:]:
#        a = multindex_operation(a, b, operation, how=how, return_col_name=return_col_name, drop_indices=drop_indices)
#    return a


def level_specific_indexer(df, levels, elements, axis=0):
    elements, levels = ensure_iterable_and_not_string(elements), ensure_iterable_and_not_string(levels)
    if len(elements) != len(levels):
        raise ValueError(
            'Number of elements ' + str(len(elements)) + ' must match the number of levels ' + str(len(levels)))
    if axis == 0:
        names = df.index.names
    else:
        names = df.columns.names
    indexer = [slice(None)] * len(names)
    for level, element in zip(levels, elements):
        if axis == 0:
            indexer[df.index.names.index(level)] = ensure_iterable_and_not_string(element)
        if axis == 1:
            indexer[df.columns.names.index(level)] = ensure_iterable_and_not_string(element) 
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

def expand_multi(a, levels_list, levels_names, how='outer', incremental=False, drop_index=None):
    """
    creates an additional layer in a mutlilevel index, repeating values from all other previous
    indexes
    """
    
    drop_index = ensure_iterable_and_not_string(drop_index)
    if set(levels_names) != set(a.index.names):
        if incremental:
            levels_list = [ensure_iterable_and_not_string(levels_list)]
            for name, level in zip(a.index.names, a.index.levels):
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
        common_headers = intersect(a.index.names, expand.index.names)
        levels_names = expand.index.names
        expand = expand.reset_index()
        a = a.reset_index()
        a = pd.merge(a, expand, on=common_headers, how=how)
        a = a.set_index(levels_names).sort_index()
    return a


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


class ExportMethods:
    def __init__(self):
        pass

    def writeself(self, write_directory):
        ExportMethods.writeobj(ExportMethods.get_name(self, default='None'), self, write_directory)

    @staticmethod
    def get_name(obj, default=None):
        if hasattr(obj, 'long_name'):
            return getattr(obj, 'long_name')
        elif hasattr(obj, 'name'):
            return getattr(obj, 'name')
        else:
            return default
            
    @staticmethod        
    def checkexistormakedir(path):
        '''Checks to see if a directory exists, and creates it if not
        '''
        if not _os.path.exists(path):
            _os.makedirs(path)

    @staticmethod
    def writeobj(name, obj, write_directory, append_results=False):
        ExportMethods.checkexistormakedir(write_directory)
        if is_numeric(obj) or type(obj) == str:
            ExportMethods.csvwrite(os.path.join(write_directory, 'vars.csv'), [[name, obj]], writetype='ab')
        elif (type(obj) == dict) or (type(obj) == defaultdict):  # or (type(obj) == OrderedDict):
            ExportMethods.writedict(name, obj, write_directory)
        elif type(obj) == list or type(obj) == tuple:
            ExportMethods.writelist(name, obj, write_directory)
        elif type(obj) == pd.core.frame.DataFrame:
            ExportMethods.writedataframe(name, obj, write_directory, append_results)
        elif inspect.isclass(type(obj)) and hasattr(obj, '__dict__'):
            ExportMethods.writeclass(name, obj, write_directory)

    @staticmethod
    def writelist(name, obj, write_directory):
        csv_elements = [item for item in obj if is_numeric(item) or type(item) == str]
        ExportMethods.csvwrite(os.path.join(write_directory, 'vars.csv'), [[name] + csv_elements], writetype='ab')


    @staticmethod
    def writedict(name, obj, write_directory):
        new_directory = os.path.join(write_directory, name)
        for key, value in obj.items():
            try:
                if value:
                    ExportMethods.writeobj(key, value, new_directory)
            except:
                ExportMethods.writeobj(key, value, new_directory)

    @staticmethod
    def writedataframe(name, obj, write_directory, append_results):
        if os.path.exists(os.path.join(write_directory, name + '.csv')) and append_results:
            obj.to_csv(os.path.join(write_directory, name + '.csv'), header=False, mode='a')
        else:
           obj.to_csv(os.path.join(write_directory, name + '.csv'))


    @staticmethod
    def writeclass(name, obj, write_directory):
        if name == 'drivers':
            return
        new_name = ExportMethods.get_name(obj, default=name)
        new_name = str(new_name)
        new_directory = os.path.join(write_directory, new_name)
        attnames = [attname for attname in vars(obj) if not attname.startswith('_')]
        atts = [getattr(obj, attname) for attname in attnames]
        for attname, att in zip(attnames, atts):
            ExportMethods.writeobj(attname, att, new_directory)

    @staticmethod
    def csvwrite(path, data, writetype='ab'):
        '''Writes a CSV from a series of data
        '''
        with open(path, writetype) as outfile:
            csv_writer = csv.writer(outfile, delimiter=',')
            for row in data:
                if is_iterable(row):
                    csv_writer.writerow(row)
                else:
                    csv_writer.writerow([row])

    @staticmethod
    def plotdf(data, kind='area', x_axis='vintage', stack_level=None, group_function='sum'):
        if stack_level is not None and stack_level in data.index.names:
            if group_function == 'sum':
                temp = data.groupby(level=(stack_level, x_axis)).sum()
            elif group_function == 'mean':
                temp = data.groupby(level=(stack_level, x_axis)).mean()
            else:
                raise ValueError()
            levels = temp.index.names
            stack_level_i = levels.index(stack_level)
            temp.unstack(level=stack_level_i).plot(stacked=True, kind=kind, figsize=(15, 9.3),
                                                   colormap=matplotlib.cm.Set2)
        else:
            if group_function == 'sum':
                temp = data.groupby(level=x_axis).sum()
            elif group_function == 'mean':
                temp = data.groupby(level=x_axis).mean()
            else:
                raise ValueError()
            temp.plot(stacked=False, kind=kind, figsize=(15, 9.3), colormap=matplotlib.cm.Set2)


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
    maximum_remaining = .5 * book_life/float(mean_lifetime)
    for i, year in enumerate(years):
        for vintage in [vintages[0]]:
            # TODO Ryan, better assumption about remaining useful/book life?
            # Assumes that the stock at time 0 is 50% depreciated
            exist[0, i] = max(maximum_remaining * 1 - ((year-vintage)/float(book_life)),0)
    df = pd.DataFrame(exist, index=vintages, columns=years)
    df.index.rename('vintage', inplace=True)
    df.columns.names = [None]
    return df


def convert_age(self, reverse, vintages, years, attr_from='values', attr_to='values'):
    """
    Broadcasts vintage values that decay over time to year columns
    """
    if hasattr(self, 'age_growth_or_decay') and self.age_growth_or_decay is not None:
        decay = decay_growth_df(self.age_growth_or_decay_type, self.age_growth_or_decay, reverse, vintages, years)
        # decay = expand_multi(decay, getattr(self,attr_from).index.levels, getattr(self,attr_from).index.names)
        decay.data_type = 'total'
        setattr(self, attr_to,
                DfOper.mult([decay, getattr(self, attr_from)]))
    else:
        decay = decay_growth_df(None, None, False, vintages, years)
        # decay = expand_multi(decay, getattr(self,attr_from).groupyby(level=ix_excl(getattr(self,attr_from), 'vintage')).sum().index.levels,  getattr(self,attr_from).groupyby(level=ix_excl(getattr(self,attr_from), 'vintage')).sum().index.names)
        decay.data_type = 'total'
        setattr(self, attr_to, DfOper.mult([decay, getattr(self, attr_from)]))


def create_markov_matrix(markov_vector, num_techs, num_years, steps_per_year=1):
    markov_matrix = np.zeros((num_techs, num_years*steps_per_year + 1, num_years*steps_per_year))
    for i in range(int(num_years*steps_per_year)):
        markov_matrix[:, :-i - 1, i] = np.transpose(markov_vector[i:-1])
    markov_matrix[:, -1, :] = markov_matrix[:, -2, :]
    return np.cumprod(markov_matrix, axis=2)


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
        if not len(df_iter):
            return pd.DataFrame()
        expandable = DfOper.fill_default_char(expandable, len(df_iter))
        collapsible = DfOper.fill_default_char(collapsible, len(df_iter))
        c = df_iter[0]  # .copy()
        for i, b in enumerate(df_iter[1:]):
            c = DfOper._df_operation(c, b, '+', join, fill_value,
                                     a_can_collapse=collapsible[i], a_can_expand=expandable[i],
                                     b_can_collapse=collapsible[i + 1], b_can_expand=expandable[i + 1],
                                     non_expandable_levels=non_expandable_levels)
        return c

    @staticmethod
    def mult(df_iter, expandable=True, collapsible=True, join=None, fill_value=0, non_expandable_levels=('year', 'vintage')):
        if not len(df_iter):
            return pd.DataFrame()
        expandable = DfOper.fill_default_char(expandable, len(df_iter))
        collapsible = DfOper.fill_default_char(collapsible, len(df_iter))
        c = df_iter[0]  # .copy()
        for i, b in enumerate(df_iter[1:]):
            c = DfOper._df_operation(c, b, '*', join, fill_value,
                                     a_can_collapse=collapsible[i], a_can_expand=expandable[i],
                                     b_can_collapse=collapsible[i + 1], b_can_expand=expandable[i + 1],
                                     non_expandable_levels=non_expandable_levels)
        return c

    @staticmethod
    def divi(df_iter, expandable=True, collapsible=True, join=None, fill_value=0, non_expandable_levels=('year', 'vintage')):
        if not len(df_iter):
            return pd.DataFrame()
        expandable = DfOper.fill_default_char(expandable, len(df_iter))
        collapsible = DfOper.fill_default_char(collapsible, len(df_iter))
        c = df_iter[0]  # .copy()
        for i, b in enumerate(df_iter[1:]):
            c = DfOper._df_operation(c, b, '/', join, fill_value,
                                     a_can_collapse=collapsible[i], a_can_expand=expandable[i],
                                     b_can_collapse=collapsible[i + 1], b_can_expand=expandable[i + 1],
                                     non_expandable_levels=non_expandable_levels)
        return c

    @staticmethod
    def subt(df_iter, expandable=True, collapsible=True, join=None, fill_value=0, non_expandable_levels=('year', 'vintage')):
        if not len(df_iter):
            return pd.DataFrame()
        expandable = DfOper.fill_default_char(expandable, len(df_iter))
        collapsible = DfOper.fill_default_char(collapsible, len(df_iter))
        c = df_iter[0]  # .copy()
        for i, b in enumerate(df_iter[1:]):
            c = DfOper._df_operation(c, b, '-', join, fill_value,
                                     a_can_collapse=collapsible[i], a_can_expand=expandable[i],
                                     b_can_collapse=collapsible[i + 1], b_can_expand=expandable[i + 1],
                                     non_expandable_levels=non_expandable_levels)
        return c
    
    
    @staticmethod
    def none(df_iter, expandable=True, collapsible=True, join=None, fill_value=0, non_expandable_levels=('year', 'vintage')):
        if not len(df_iter):
            return pd.DataFrame()
        expandable = DfOper.fill_default_char(expandable, len(df_iter))
        collapsible = DfOper.fill_default_char(collapsible, len(df_iter))
        c = df_iter[0]  # .copy()
        for i, b in enumerate(df_iter[1:]):
            c = DfOper._df_operation(c, b, None, join, fill_value,
                                     a_can_collapse=collapsible[i], a_can_expand=expandable[i],
                                     b_can_collapse=collapsible[i + 1], b_can_expand=expandable[i + 1],
                                     non_expandable_levels=non_expandable_levels)
        return c

    @staticmethod
    def repl(df_iter, expandable=True, collapsible=True, join=None, fill_value=0, non_expandable_levels=('year', 'vintage')):
        if not len(df_iter):
            return pd.DataFrame()
        expandable = DfOper.fill_default_char(expandable, len(df_iter))
        collapsible = DfOper.fill_default_char(collapsible, len(df_iter))
        c = df_iter[0]  # .copy()
        for i, b in enumerate(df_iter[1:]):
            c = DfOper._df_operation(c, b, 'replace', join, fill_value,
                                     a_can_collapse=collapsible[i], a_can_expand=expandable[i],
                                     b_can_collapse=collapsible[i + 1], b_can_expand=expandable[i + 1],
                                     non_expandable_levels=non_expandable_levels)
        return c


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

        new_a, new_b = DfOper._account_for_mismatched_elements(a, b, fill_value, a_can_collapse, a_can_expand,
                                                               b_can_collapse, b_can_expand, non_expandable_levels)

        # multi index level differences
        names_a_not_in_b, names_b_not_in_a = difference_in_df_names(new_a, new_b)
        if not names_a_not_in_b and not names_b_not_in_a:
            join = join if join is not None else ('outer' if fill_value is not None else 'left')
            new_a, new_b = new_a.align(reorder_b_to_match_a(new_b, new_a), join=join, fill_value=fill_value, axis=0,
                                       copy=False)
            return DfOper._operate(new_a, new_b, action)
        else:
            new_a, new_b = DfOper._merge_then_separate_for_operation(new_a, new_b, join, fill_value, a_can_collapse,
                                                                     a_can_expand, b_can_collapse, b_can_expand)
            return DfOper._operate(new_a, new_b, action)

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
        new_a = a.groupby(level=common_names).sum() if (len(
            names_a_not_in_b) > 0 and not b_can_expand) and a_can_collapse else a
        new_b = b.groupby(level=common_names).sum() if (len(
            names_b_not_in_a) > 0 and not a_can_expand) and b_can_collapse else b

        # Reindex so that elements within levels match
        if fill_value is not None:
            new_a, new_b = DfOper._reindex_dfs_so_elements_match(new_a, new_b, level_names=common_names,
                                                                 how='intersect')

        # pd.concat([a]*2, keys=['mon', 'tue'], name='weekday')

        # Default for join is left unless b has more columns, then we assume we want to join on it
        if join is None:
            join = 'right' if len(b.columns) > len(a.columns) else 'left'

        c = pd.merge(new_a.reset_index(), new_b.reset_index(), how=join, on=common_names, suffixes=["_a", "_b"])

        new_index = [x for x in c.columns.tolist() if (x not in merged_a_cols) and (x not in merged_b_cols)]
        # This next bit of code helps return the levels in a familiar order
        alen, blen = float(len(a_names) - 1), float(len(b_names) - 1)
        alen, blen = max(alen, 1), max(blen, 1)  # avoid error from dividing by zero
        average_location = [a_names.index(cand) / alen if cand in a_names else b_names.index(cand) / blen for cand in
                            new_index]
        new_index = [new_index[ni] for ni in np.argsort(average_location)]

        new_a, new_b = c[new_index + merged_a_cols], c[new_index + merged_b_cols]

        new_a.set_index(new_index, inplace=True)
        new_b.set_index(new_index, inplace=True)

        new_a.sort(inplace=True)
        new_b.sort(inplace=True)

        new_a.rename(columns=dict(zip(merged_a_cols, a_cols)), inplace=True)
        new_b.rename(columns=dict(zip(merged_b_cols, b_cols)), inplace=True)

        if fill_value is not None:
            new_a.fillna(fill_value, inplace=True)
            new_b.fillna(fill_value, inplace=True)

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
        if set(new_elements) == set(df.index.levels[index_i]):
            return df
        const_labels = OrderedSet([tuple([z if i != index_i else -1 for i, z in enumerate(lab)]) for lab in zip(*df.index.labels)])
        new_labels = flatten_list([[tuple([z if i != index_i else n for i, z in enumerate(lab)]) for n in range(len(new_elements))] for lab in const_labels])
        full_elements = [new_elements if name == level_name else level for name, level in zip(df.index.names, df.index.levels)]
#        try:
        return df.reindex(index=pd.MultiIndex(levels=full_elements, labels=zip(*new_labels), names=df.index.names), fill_value=fill_value)
#        except:
#            print df
#            print full_elements
#            print zip(*new_labels)
#            print df.index.names

    else:
        return df.reindex(index=pd.Index(new_elements, name=df.index.name), fill_value=fill_value)

def find_weibul_beta(mean_lifetime, lifetime_variance):
    """http://interstat.statjournals.net/YEAR/2000/articles/0010001.pdf"""
    if lifetime_variance == 0:
        return config.cfg.weibul_coeff_of_var['beta'][-1]
    else:
        mean_to_std = mean_lifetime / (lifetime_variance ** .5)
        return config.cfg.weibul_coeff_of_var['beta'][nearest_index(config.cfg.weibul_coeff_of_var['mean/std'], mean_to_std)]


def add_and_set_index(df, index, value):
    df[index] = value
    df = df.set_index(index, append=True)
    replace_index_name(df, index)
    return df
    

def determ_energy(unit):
    """
    determines whether a unit is an energy unit
    
    """
    # TODO check if static method appropriate
    if config.cfg.ureg.Quantity(unit).dimensionality == config.cfg.ureg.Quantity(config.cfg.cfgfile.get('case', 'energy_unit')).dimensionality:
        return True


def sum_chunk(x, chunk_size, axis=-1):
    """http://stackoverflow.com/questions/18582544/sum-parts-of-numpy-array"""
    shape = x.shape
    if axis < 0:
        axis += x.ndim
    
    shape = shape[:axis] + (shape[axis]/chunk_size, chunk_size) + shape[axis+1:]
    return np.sum(x.reshape(shape), axis=axis+1)

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

