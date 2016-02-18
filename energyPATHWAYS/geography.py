__author__ = 'ryan'

import config
import pandas as pd
import os
import copy
import util

class Geography:
    def __init__(self):
        self.geographies = {}
        self.geography_names = {}
        self.timezone_names = {}
        self.map_keys = []

        self.read_geography_indicies()

        names = self.geographies.keys()
        iterables = self.geographies.values()
        # values is the actual container for the data
        self.values = pd.DataFrame(0, index=pd.MultiIndex.from_product(iterables, names=names), columns=self.map_keys)
        # sortlevel sorts all of the indicies so that we can slice the dataframe
        self.values.sortlevel(0, inplace=True)

        self.read_geography_data()
        self.normalize = lambda x: x / (x.sum())


    def read_geography_indicies(self):
        geo_key = util.sql_read_table('Geographies', column_names='name',return_iterable=True)
        for key in geo_key:
            self.geographies[key] = []

        for geography_id, name, id in util.sql_read_table('GeographiesData', column_names=['geography_id', 'name', 'id'],return_iterable=True):
            geography_name = util.id_to_name('geography_id', geography_id)
            self.geographies[geography_name].append(id)
            self.geography_names[id] = name

        for id, name in util.sql_read_table('TimeZones', column_names=['id', 'name']):
            self.timezone_names[id] = name

        for map_key in util.sql_read_table('GeographyMapKeys', 'name',return_iterable=True):
            self.map_keys.append(map_key)

    def read_geography_data(self):
        # df2.loc[('kentucky', 'total', 'east north central', 'western interconnection'), 'households']
        headers = util.sql_read_headers('GeographyMap')

        # colmap and rowmap are used in ordering the data when read from the sql table
        colmap = []
        for col in self.map_keys:
            colmap.append(headers.index(col))
        rowmap = []
        for row in self.geographies.keys():
            rowmap.append(headers.index(row))
        for row in util.sql_read_table('GeographyMap', return_iterable=True):
            self.values.loc[tuple([row[i] for i in rowmap]), tuple(self.map_keys)] = [row[i] for i in colmap]

    def map_df(self, subsection, supersection, column=None, reset_index=False, eliminate_zeros=True):
        """ main function that maps geographies to one another
        Two options for two overlapping areas
            (A u B) / A     (A is supersection)
            (A u B) / B     (B is supersection)

        Examples:
            self.map_df('households', subsection=('state'), supersection=('census division'))
            "what fraction of each census division is in each state"

            self.map_df('households', subsection=('census division'), supersection=('state'))
            "what fraction of each state is in each census division
        """
        subsection = util.ensure_iterable_and_not_string(subsection)
        column = config.cfg.cfgfile.get('case', 'default_geography_map_key') if column is None else column
        table = self.values[column].groupby(level=[supersection]+subsection).sum()
        table = pd.DataFrame(table.groupby(level=supersection).transform(self.normalize))
        
        if reset_index or eliminate_zeros:
            names = table.index.names
            table.reset_index(inplace=True)
        if eliminate_zeros:
            table = table[table[column]>0]
        if not reset_index and eliminate_zeros:
            table.set_index(names, inplace=True)
        
        return table

