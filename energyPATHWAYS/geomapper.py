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
import pdb

class GeoMapper:
    def __init__(self):
        self.geographies = OrderedDict()
        self.geography_names = dict(util.sql_read_table('GeographiesData', ['id', 'name'], return_unique=True, return_iterable=True)) # this is used for outputs
        self.timezone_names = {}
        self.map_keys = []
        self.read_geography_indicies()
        self.gau_to_geography = dict(util.flatten_list([(v, k) for v in vs] for k, vs in self.geographies.iteritems()))
        self.id_to_geography = dict((k, v) for k, v in util.sql_read_table('Geographies'))
        self.read_geography_data()
        self._create_composite_geography_levels()
        self.geographies_unfiltered = copy.copy(self.geographies) # keep a record
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
                ORDER BY "GeographyIntersection".id
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
        self.values['intersection_id'] = sorted(util.sql_read_table('GeographyIntersection'))
        self.values = self.values.set_index('intersection_id', append=True)
        # sortlevel sorts all of the indicies so that we can slice the dataframe
        self.values = self.values.sort()
        self.values.replace(0,1e-10,inplace=True)
        self.values = self.values.groupby(level=[x for x in self.values.index.names if x not in ['intersection_id']]).first()

    def log_geo(self):
        """
        get a positional index in self.values (geomap table) that describes the primary_subset geography
        """
        logging.info('Primary geography is {}'.format(self.id_to_geography[cfg.primary_geography_id]))
        logging.info('Dispatch geography is {}'.format(self.id_to_geography[cfg.dispatch_geography_id]))
        if cfg.primary_subset_id:
            logging.info('Geomap table will be filtered')
            for id in cfg.primary_subset_id:
                logging.info(' analysis will include the {} {}'.format(self.gau_to_geography[id], self.geography_names[id]))
        
        if cfg.breakout_geography_id:
            logging.info('Breakout geographies will be used')
            for id in cfg.breakout_geography_id:
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
        self.filtered_values = self.values.iloc[self._get_iloc_geo_subset(self.values)]
        for key in self.geographies:
            self.geographies[key] = list(set(self.filtered_values.index.get_level_values(key)))
            self.geographies[key].sort()
    
    def _normalize(self, table, levels):
        if table.index.nlevels>1:
            table = table.groupby(level=levels).transform(lambda x: x / (x.sum()))
        else:
            table[:] = 1
        return table

    def _create_composite_geography_level(self, new_level_name, base_geography, breakout_geography_id):
        base_gaus = np.array(self.values.index.get_level_values(base_geography), dtype=int)
        impacted_gaus = set()
        for id in breakout_geography_id:
            index = np.nonzero(self.values.index.get_level_values(self.gau_to_geography[id])==id)[0]
            impacted_gaus = impacted_gaus | set(base_gaus[index])
            base_gaus[index] = id

#        if any(impacted in breakout_geography_id for impacted in impacted_gaus):
#            raise ValueError('breakout geographies in config cannot overlap geographically')
        
        self.values[new_level_name] = base_gaus
        self.values = self.values.set_index(new_level_name, append=True)
        # add to self.geographies
        self.geographies[new_level_name] = list(set(self.values.index.get_level_values(new_level_name)))
        # update geography names for outputs
        self.geography_names.update(dict(zip(impacted_gaus, ['other ' + self.geography_names[impacted_gau] for impacted_gau in impacted_gaus])))

        
    def _create_composite_geography_levels(self):
        """
        Potential to create one for primary geography and one for dispatch geography
        """
        primary_geography_name = self.get_primary_geography_name()
        if cfg.breakout_geography_id and (primary_geography_name not in self.values.index.names):
            self._create_composite_geography_level(primary_geography_name, self.id_to_geography[cfg.primary_geography_id], cfg.breakout_geography_id)
        
        dispatch_geography_name = self.get_dispatch_geography_name()
        if cfg.dispatch_breakout_geography_id and (dispatch_geography_name not in self.values.index.names):
            self._create_composite_geography_level(dispatch_geography_name, self.id_to_geography[cfg.dispatch_geography_id], cfg.dispatch_breakout_geography_id)
        
    def map_df(self, current_geography, converted_geography, normalize_as='total', map_key=None, reset_index=False,
               eliminate_zeros=True, primary_subset_id='from config', geomap_data='from self',filter_geo=True):
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
        if primary_subset_id=='from config' and filter_geo:
            primary_subset_id = cfg.primary_subset_id
        elif (primary_subset_id is None) or (primary_subset_id is False) or (not filter_geo):
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
            df = df.sort_index()
            df = df.loc[indexer, :]
            return df.reset_index().set_index(df.index.names).sort()
        else:
            return df

    def make_new_geography_name(self, base_geography, breakout_ids=None):
        if breakout_ids:
            dct = dict(util.sql_read_table('GeographiesData', ['id', 'name'],return_unique=True, return_iterable=True))   
            base_geography += " and " + "| ".join([dct[id] for id in breakout_ids])
#            base_geography +=' with breakout ids {}'.format(sorted(util.ensure_iterable_and_not_string(breakout_ids)))
        return base_geography

    def get_primary_geography_name(self):
        return self.make_new_geography_name(self.id_to_geography[cfg.primary_geography_id],
                                            cfg.breakout_geography_id)

    def get_dispatch_geography_name(self):
        return self.make_new_geography_name(self.id_to_geography[cfg.dispatch_geography_id],
                                            cfg.dispatch_breakout_geography_id)

    def get_native_current_foreign_gaus(self, df, current_geography):
        native_gaus = set(self.geographies_unfiltered[current_geography])
        current_gaus = set(df.index.get_level_values(current_geography))
        foreign_gaus = current_gaus - native_gaus
        return native_gaus, current_gaus, foreign_gaus

    def incorporate_foreign_gaus(self, df, current_geography, data_type, map_key, keep_oth_index_over_oth_gau=False,zero_out_negatives=True):
        native_gaus, current_gaus, foreign_gaus = self.get_native_current_foreign_gaus(df, current_geography)
        
        # we don't have any foreign gaus
        if not foreign_gaus or not cfg.include_foreign_gaus:
            return df, current_geography
        
        if 'year' in df.index.names:
            y_or_v = 'year' 
        elif 'vintage' in df.index.names:
            y_or_v = 'vintage'
        else:
            raise ValueError('df must either have year or vintage to incorporate foreign gaus')
            
        index_with_nans = [df.index.names[i] for i in set(np.nonzero([np.isnan(row) for row in df.index.get_values()])[1])]
        # if we have an index with nan, that typically indicates that one of the foreign gaus didn't have all the index levels
        # if this is the case, we have two options (1) get rid of the other index (2) ignore the foreign gau
        if index_with_nans and (keep_oth_index_over_oth_gau or data_type=='intensity'):
            return self.filter_foreign_gaus(df, current_geography), current_geography
        else:
            assert (y_or_v not in index_with_nans) and (current_geography not in index_with_nans)
            # we need to eliminate levels with nan before moving on
            df = util.remove_df_levels(df, index_with_nans)
        
        base_gaus = np.array(self.values.index.get_level_values(current_geography), dtype=int)
        for id in foreign_gaus:
            foreign_geography = self.gau_to_geography[id]
            index = np.nonzero(self.values.index.get_level_values(self.gau_to_geography[id])==id)[0]
            impacted_gaus = list(set(base_gaus[index]))
            base_gaus[index] = id
            if any(impacted in foreign_gaus for impacted in impacted_gaus):
                raise ValueError('foreign gaus in the database cannot overlap geographically')
            
            # if the data_type is a total, we need to net out the total from the neighboring
            if data_type=='total':
                # we first need to do a clean time series
                # then we need to allocate out and subtract
                allocation = self.map_df(foreign_geography, current_geography, map_key=map_key, primary_subset_id=[id])
                foreign_gau_slice = util.df_slice(df, id, current_geography, drop_level=False, reset_index=True)
                foreign_gau_slice.index = foreign_gau_slice.index.rename(foreign_geography, level=current_geography)
                allocated_foreign_gau_slice = util.DfOper.mult((foreign_gau_slice, allocation))
                allocated_foreign_gau_slice = util.remove_df_levels(allocated_foreign_gau_slice, foreign_geography)
                indexer = util.level_specific_indexer(df,current_geography,[impacted_gaus])
                impacted_gaus_slice = df.loc[indexer,:].reset_index().set_index(df.index.names)
                impacted_gau_years = list(impacted_gaus_slice.index.get_level_values(y_or_v).values)
                new_impacted_gaus = util.DfOper.subt((impacted_gaus_slice, allocated_foreign_gau_slice), fill_value=np.nan, non_expandable_levels=[])
                new_impacted_gaus = new_impacted_gaus.reorder_levels(df.index.names).sort()
                if new_impacted_gaus.min().min() < 0:
                    if not zero_out_negatives:
                        raise ValueError('Negative values resulted from subtracting the foreign gau from the base gaus. This is the resulting dataframe: {}'.format(new_impacted_gaus))
                    else:
                        new_impacted_gaus[new_impacted_gaus<0] = 0
                if new_impacted_gaus.isnull().all().value:
                    pdb.set_trace()
                    raise ValueError('Year or vitages did not overlap between the foreign gaus and impacted gaus')
                indexer = util.level_specific_indexer(df, [current_geography, y_or_v], [impacted_gaus, impacted_gau_years])
                df.loc[indexer, :] = new_impacted_gaus.loc[indexer, :]
        
        assert not any([any(np.isnan(row)) for row in df.index.get_values()])
        new_geography_name = self.make_new_geography_name(current_geography, list(foreign_gaus))
        df.index = df.index.rename(new_geography_name, level=current_geography)
        if new_geography_name not in self.geographies:
            self.add_new_geography(new_geography_name, base_gaus)
        return df, new_geography_name

    def add_new_geography(self, new_geography_name, base_gaus):
        self.values[new_geography_name] = base_gaus
        self.values = self.values.set_index(new_geography_name, append=True)
        # add to self.geographies
        self.geographies_unfiltered[new_geography_name] = sorted(list(set(self.values.index.get_level_values(new_geography_name))))
        self._update_geographies_after_subset()
        self.geographies[new_geography_name] = sorted(list(set(self.filtered_values.index.get_level_values(new_geography_name))))

    def filter_foreign_gaus(self, df, current_geography, foreign_gaus=None):
        """ Remove foreign gaus from the dataframe
        """
        ncf = self.get_native_current_foreign_gaus(df, current_geography)
        foreign_gaus = ncf[2] if foreign_gaus is None else foreign_gaus
        current_gaus = ncf[1]
        assert len(foreign_gaus - current_gaus) == 0
        
        if not foreign_gaus:
            return df
        
        # if the index has nans, we need to be careful about data types
        index_with_nans_before = [df.index.names[i] for i in set(np.nonzero([np.isnan(row) for row in df.index.get_values()])[1])]
        indexer = util.level_specific_indexer(df, current_geography, [list(current_gaus-foreign_gaus)])
        index_names = df.index.names
        df = df.loc[indexer]
        index_with_nans_after = [df.index.names[i] for i in set(np.nonzero([np.isnan(row) for row in df.index.get_values()])[1])]
        df = df.reset_index()
        index_without_nans_anymore = list(set(index_with_nans_before) - set(index_with_nans_after))
        df[index_without_nans_anymore] = df[index_without_nans_anymore].values.astype(int)
        df = df.set_index(index_names)
        # we shouldn't have any nans (or anything but integers in the index)
        if tuple(sorted(foreign_gaus)) == tuple(sorted(ncf[2])):
            assert not any([any(np.isnan(row)) for row in df.index.get_values()])
        return df
        
        
