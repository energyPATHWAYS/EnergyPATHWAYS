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
        self.normalize = lambda x: x / (x.sum())

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

    def filter_map_table(self, primary_subset_id=None):
        """
        primary_subset_id is a list of gaus to keep
        """
        primary_subset_id = cfg.primary_subset_id if primary_subset_id is None else []
        if len(primary_subset_id):
            logging.info('filtering geomapping table')
        else:
            return
        
        primary_subset_dict = defaultdict(list)
        for id in primary_subset_id:
            logging.info(' analysis will include the {} {}'.format(self.gau_to_geography[id], self.geography_names[id]))
            primary_subset_dict[self.gau_to_geography[id]].append(id)
        
        def _loc_values(level):
            return self.values.loc[util.level_specific_indexer(self.values, [level], [primary_subset_dict[level]]), :]
        
        join_df = pd.concat([_loc_values(level) for level in primary_subset_dict])
        join_df = join_df.groupby(level=join_df.index.names).first()

        # this is a row that has the remainder for each geography map key after filtering.. it needs to be added as a new row
        remainder = (self.values.sum() - join_df.sum()).to_frame()
        self.remainder = remainder
        # if we don't have a residual, we basically have no filtering and we can stop because it will have no impact
        if (remainder[0]==0).all():
            return
        # -1 indicates remainder
        ind = pd.DataFrame([[self.geographies[n][0] if len(self.geographies[n])==1 else -1 for n in self.values.index.names]], columns=self.values.index.names)
        remainder = ind.join(remainder.transpose()).set_index(self.values.index.names)
#        remainder = pd.concat([pd.DataFrame(ind, index=list(self.values.index.names)), remainder]).transpose().set_index(self.values.index.names)
        
        join_df = pd.concat((join_df, remainder)).sort()
        np.testing.assert_almost_equal(self.values.sum().values, join_df.sum().values, decimal=3)        
        self.values_unfiltered = self.values.copy()
        self.values = join_df
        
        self.update_geographies()

    def update_geographies(self):
        for key in self.geographies:
            self.geographies[key] = sorted(list(set(self.values.index.get_level_values(key)) - set([-1])))

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
        column = cfg.cfgfile.get('case', 'default_geography_map_key') if column is None else column
        table = self.values[column].groupby(level=[supersection]+subsection).sum()
        table = pd.DataFrame(table.groupby(level=supersection).transform(self.normalize))
        
        if reset_index:
            table.reset_index(inplace=True)
        if not eliminate_zeros:
            index=pd.MultiIndex.from_product([self.geographies[subsection[0]],self.geographies[supersection]],names=[subsection[0],supersection])
            table = table.reorder_levels(index.names)
            table = table.reindex(index, fill_value=0.0)
        return table

