__author__ = 'ryan'

import config as cfg
import pandas as pd
import util
from collections import OrderedDict
import textwrap
import data_models.data_source as data_source
from data_models.geography import Geography, GeographiesDatum, GeographyIntersection, GeographyMapKey
from data_models.system import TimeZone


class GeoMapper:
    def __init__(self):
        self.geographies = OrderedDict()
        self.geography_names = {}
        self.timezone_names = {}
        self.map_keys = []

        self.read_geography_indicies()
        self.read_geography_data()
        self.normalize = lambda x: x / (x.sum())


    def read_geography_indicies(self):
        session = data_source.Session()

        geo_data = session.query(Geography.name, GeographiesDatum.id).join(GeographiesDatum).\
            order_by(Geography.id, GeographiesDatum.id).all()

        for row in geo_data:
            try:
                self.geographies[row[0]].append(row[1])
            except KeyError:
                self.geographies[row[0]] = [row[1]]

        self.timezone_names = data_source.fetch_as_lookup(TimeZone)

        map_key_data = session.query(GeographyMapKey.name).order_by(GeographyMapKey.id).all()
        self.map_keys = [name for (name,) in map_key_data]

    def read_geography_data(self):
        session = data_source.Session()
        expected_rows = session.query(GeographyIntersection).count()

        # TODO: (MAC) remove this once migration is complete; it is needed for the following query to work while
        # we are migrating
        session.execute("SET search_path TO migrated")

        # This query pulls together the geography map from its constituent tables. Its rows look like:
        # intersection_id, [list of geographical units that define intersection],
        # [list of values for map keys for this intersection]
        # Note that those internal lists are specifically being drawn out in the order of their Geographies and
        # GeographyMapKeys, respectively, so that they are in the same order as the expected dataframe indexes
        # and column headers
        #
        # I am leaving this as raw SQL for now because doing it without ARRAY_AGG seems too complex to be worth it.
        # SQLAlchemy 1.1 (the "development" version as of this writing) appears to have much better support for
        # array_agg, so once 1.1 becomes stable we should consider porting this into SQLAlchemy syntax
        map = session.execute(textwrap.dedent("""\
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
        """)).fetchall()

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

