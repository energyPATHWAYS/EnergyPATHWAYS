__author__ = 'ryan'

import config as cfg
import pandas as pd
import numpy as np
import os
import copy
import util
from collections import OrderedDict, defaultdict
import textwrap
import logging

class GeoMapper:
    def __init__(self):
        self.geographies = OrderedDict()
        self.geography_names = dict(util.sql_read_table('GeographiesData', ['id', 'name'], return_unique=True, return_iterable=True))
        self.timezone_names = {}
        self.map_keys = []

        self.read_geography_indicies()
        self.gau_to_geography = dict(util.flatten_list([(v, k) for v in vs] for k, vs in self.geographies.iteritems()))
        self.id_to_geography = dict((k, v) for k, v in util.sql_read_table('Geographies'))
        self.read_geography_data()
        self._update_geographies_after_subset()

    def read_geography_indicies(self):
        cfg.cur.execute(textwrap.dedent("""\
            SELECT "Geographies".name, ARRAY_AGG("GeographiesData".id) AS geography_data_ids
            FROM "Geographies"
            JOIN "GeographiesData" ON "Geographies".id = "GeographiesData".geography_id
            GROUP BY "Geographies".id
            ORDER BY "Geographies".id;
        """))

        for row in cfg.cur.fetchall():
            self.geographies[row[0]] = row[1]
        for value in self.geographies.values():
            value.sort()
        for id, name in util.sql_read_table('TimeZones', column_names=['id', 'name']):
            self.timezone_names[id] = name
        cfg.cur.execute('SELECT name FROM "GeographyMapKeys" ORDER BY id')
        self.map_keys = [name for (name,) in cfg.cur.fetchall()]

    def read_geography_data(self):
        cfg.cur.execute('SELECT COUNT(*) FROM "GeographyIntersection"')
        expected_rows = cfg.cur.fetchone()[0]

        # This query pulls together the geography map from its constituent tables. Its rows look like:
        # intersection_id, [list of geographical units that define intersection],
        # [list of values for map keys for this intersection]
        # Note that those internal lists are specifically being drawn out in the order of their Geographies and
        # GeographyMapKeys, respectively, so that they are in the same order as the expected dataframe indexes
        # and column headers
        cfg.cur.execute(textwrap.dedent("""\
            SELECT intersections.id,
                   intersections.intersection,
                   ARRAY_AGG("GeographyMap".value ORDER BY "GeographyMap".geography_map_key_id) AS values
            FROM
            (
                SELECT "GeographyIntersection".id,
                       ARRAY_AGG("GeographyIntersectionData".gau_id ORDER BY "GeographiesData".geography_id) AS intersection
                FROM "GeographyIntersection"
                JOIN "GeographyIntersectionData"
                     ON "GeographyIntersectionData".intersection_id = "GeographyIntersection".id
                JOIN "GeographiesData"
                     ON "GeographyIntersectionData".gau_id = "GeographiesData".id
                GROUP BY "GeographyIntersection".id
            ) AS intersections

            JOIN "GeographyMap" ON "GeographyMap".intersection_id = intersections.id
            GROUP BY intersections.id, intersections.intersection;
        """))

        map = cfg.cur.fetchall()
        assert len(map) == expected_rows, "Expected %i rows in the geography map but found %i" % (expected_rows, len(map))

        # convert the query results into a list of indexes and a list of data (column values) that can be used
        # to construct a data frame
        expected_layers = len(self.geographies)
        expected_values = len(self.map_keys)
        index = []
        data = []
        for row in map:
            id_, intersection, values = row
            assert len(intersection) == expected_layers, "Expected each geography map row to have %i geographic layers but row id %i has %i" % (expected_layers, id_, len(intersection))
            assert len(values) == expected_values, "Expected each geography map row to have %i data values but row id %i has %i" % (expected_values, id_, len(values))
            index.append(tuple(intersection))
            data.append(values)

        # construct the data frame
        names = self.geographies.keys()
        # values is the actual container for the data
        self.values = pd.DataFrame(data, index=pd.MultiIndex.from_tuples(index, names=names), columns=self.map_keys)
        # sortlevel sorts all of the indicies so that we can slice the dataframe
        self.values.sortlevel(0, inplace=True)

    def log_geo_subset(self, primary_subset_id=None):
        """
        get a positional index in self.values (geomap table) that describes the primary_subset geography
        """
        primary_subset_id = cfg.primary_subset_id if primary_subset_id is None else primary_subset_id
        if primary_subset_id:
            logging.info('Filtering geomapping table')
            for id in primary_subset_id:
                logging.info(' analysis will include the {} {}'.format(self.gau_to_geography[id], self.geography_names[id]))

    def _get_iloc_geo_subset(self, df, primary_subset_id=None):
        """
        get a positional index in self.values (geomap table) that describes the primary_subset geography
        """
        primary_subset_id = cfg.primary_subset_id if primary_subset_id is None else primary_subset_id
        if primary_subset_id:
            return list(set(np.concatenate([np.nonzero(df.index.get_level_values(self.gau_to_geography[id])==id)[0] for id in primary_subset_id])))
        else:
            return range(len(df))
    
    def _update_geographies_after_subset(self):
        self.geographies_unfiltered = copy.copy(self.geographies) # keep a record
        filtered_geomap = self.values.iloc[self._get_iloc_geo_subset(self.values)]
        for key in self.geographies:
            self.geographies[key] = list(set(filtered_geomap.index.get_level_values(key)))

    def _normalize(self, table, levels):
        if table.index.nlevels>1:
            table = table.groupby(level=levels).transform(lambda x: x / (x.sum()))
        else:
            table[:] = 1
        return table

    def create_composite_geography_levels(self):
        pass

    def map_df(self, current_geography, converted_geography, normalize_as='total', map_key=None, reset_index=False, eliminate_zeros=True, primary_subset_id='from config', geomap_data='from self'):
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
        assert normalize_as=='total' or normalize_as=='intensity'
        geomap_data = self.values if geomap_data=='from self' else geomap_data
        if primary_subset_id=='from config':
            primary_subset_id = cfg.primary_subset_id
        elif primary_subset_id is None or primary_subset_id is False:
            primary_subset_id = []
        
        subset_geographies = set(cfg.geo.gau_to_geography[id] for id in primary_subset_id)
        current_geography = util.ensure_iterable_and_not_string(current_geography)
        converted_geography = util.ensure_iterable_and_not_string(converted_geography)
        union_geo = list(subset_geographies | set(current_geography) | set(converted_geography))
        level_to_remove = list(subset_geographies - set(current_geography) - set(converted_geography))
        map_key = cfg.cfgfile.get('case', 'default_geography_map_key') if map_key is None else map_key
        
        table = geomap_data[map_key].groupby(level=union_geo).sum().to_frame()
        if normalize_as=='total':
            table = self._normalize(table, current_geography)
        if primary_subset_id:
            # filter the table
            table = table.iloc[self._get_iloc_geo_subset(table, primary_subset_id)]
            table = util.remove_df_levels(table, level_to_remove)
            table = table.reset_index().set_index(table.index.names)
        if normalize_as=='intensity':
            table = self._normalize(table, converted_geography)
        
        if reset_index:
            table = table.reset_index()

        if not eliminate_zeros:
            index = pd.MultiIndex.from_product(table.index.levels, names=table.index.names)
            table = table.reorder_levels(index.names)
            table = table.reindex(index, fill_value=0.0)
            
        return table
        
    def filter_extra_geos_from_df(self, df):
        # we have a subset geography and should remove the data that is completely outside of the breakout
        if cfg.primary_subset_id:
            levels = [n for n in df.index.names if n in self.geographies]
            elements = [self.geographies[n] for n in levels]
            indexer = util.level_specific_indexer(df, levels=levels, elements=elements)
            df = df.loc[indexer, :]
            return df.reset_index().set_index(df.index.names).sort()
        else:
            return df