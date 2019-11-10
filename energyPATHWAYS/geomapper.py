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
from csvdb.data_object import get_database
from time_series import TimeSeries

class GeoMapper:
    _instance = None
    _global_geography = 'global'
    _global_gau = 'all'

    geography_to_gau = None
    geography_to_gau_unfiltered = None
    gau_to_geography = None

    base_demand_primary_geography = None
    base_supply_primary_geography = None
    base_dispatch_geography = None
    base_disagg_geography = None

    demand_primary_geography = None
    supply_primary_geography = None
    dispatch_geography = None
    disagg_geography = None
    combined_outputs_geography = None

    primary_subset = None
    breakout_geography = None
    dispatch_breakout_geography = None
    disagg_breakout_geography = None

    cfg_gau_subset = None

    include_foreign_gaus = None
    default_geography_map_key = None

    # todo these need to eventually map to integers
    dispatch_geographies = None
    demand_geographies = None
    supply_geographies = None
    combined_geographies = None

    @classmethod
    def get_instance(cls, database_path=None):
        if cls._instance is None:
            cls._instance = GeoMapper(database_path)
        return cls._instance

    def __init__(self, database_path=None):
        data, map_keys, geography_to_gau, gau_to_geography = self.read_geography_data(database_path)
        self.data = data
        self.map_keys = map_keys
        GeoMapper.geography_to_gau = geography_to_gau
        GeoMapper.gau_to_geography = gau_to_geography

        GeoMapper.breakout_geography = [g.lstrip().rstrip() for g in cfg.getParam('breakout_geography').split(',') if len(g)]

        GeoMapper.base_demand_primary_geography = cfg.getParam('demand_primary_geography')
        GeoMapper.breakout_geography = util.splitclean(cfg.getParam('breakout_geography'))
        GeoMapper.demand_primary_geography = self.make_new_geography_name(GeoMapper.base_demand_primary_geography, GeoMapper.breakout_geography)

        GeoMapper.base_supply_primary_geography = cfg.getParam('supply_primary_geography')
        GeoMapper.supply_primary_geography = self.make_new_geography_name(GeoMapper.base_supply_primary_geography, GeoMapper.breakout_geography)

        GeoMapper.base_dispatch_geography = cfg.getParam('dispatch_geography')
        GeoMapper.dispatch_breakout_geography = util.splitclean(cfg.getParam('dispatch_breakout_geography'))
        GeoMapper.dispatch_geography = self.make_new_geography_name(GeoMapper.base_dispatch_geography, GeoMapper.dispatch_breakout_geography)

        GeoMapper.base_disagg_geography = cfg.getParam('disagg_geography')
        GeoMapper.disagg_breakout_geography = util.splitclean(cfg.getParam('disagg_breakout_geography'))
        GeoMapper.disagg_geography = self.make_new_geography_name(GeoMapper.base_disagg_geography, GeoMapper.disagg_breakout_geography)

        combined_outputs_geography_side = cfg.getParam('combined_outputs_geography_side')
        assert combined_outputs_geography_side.lower() == 'demand' or combined_outputs_geography_side.lower() == 'supply'
        GeoMapper.combined_outputs_geography = GeoMapper.demand_primary_geography if combined_outputs_geography_side.lower() == 'demand' else GeoMapper.supply_primary_geography

        GeoMapper.primary_subset = util.splitclean(cfg.getParam('primary_subset'))
        GeoMapper.include_foreign_gaus = cfg.getParamAsBoolean('include_foreign_gaus')
        GeoMapper.default_geography_map_key = cfg.getParam('default_geography_map_key')

        self._create_composite_geography_levels()
        GeoMapper.geography_to_gau_unfiltered = copy.copy(self.geography_to_gau)

        GeoMapper.cfg_gau_subset = [g.lstrip().rstrip() for g in cfg.getParam('primary_subset').split(',') if len(g)]
        if GeoMapper.cfg_gau_subset:
            self._update_geographies_after_subset()

        GeoMapper.demand_geographies = self.geography_to_gau[GeoMapper.demand_primary_geography]
        GeoMapper.supply_geographies = self.geography_to_gau[GeoMapper.supply_primary_geography]
        GeoMapper.dispatch_geographies = self.geography_to_gau[GeoMapper.dispatch_geography]
        GeoMapper.combined_geographies = self.geography_to_gau[GeoMapper.combined_outputs_geography]

    def read_geography_data(self, database_path):
        db = get_database(database_path)
        geographies_table = db.get_table("Geographies").data
        global_geographies = pd.DataFrame([[GeoMapper._global_geography, GeoMapper._global_gau]], columns=['geography', 'gau'])
        geographies_table = pd.concat((geographies_table, global_geographies))
        assert len(geographies_table['gau']) == len(geographies_table['gau'].unique())

        gau_to_geography = dict(zip(geographies_table['gau'].values, geographies_table['geography'].values))
        geography_to_gau = {}
        for k, v in gau_to_geography.iteritems():
            geography_to_gau[v] = geography_to_gau.get(v, [])
            geography_to_gau[v].append(k)

        data = db.get_table("GeographiesSpatialJoin").data
        data[GeoMapper._global_geography] = GeoMapper._global_gau
        data = data.set_index(list(geographies_table['geography'].unique())).sort_index()
        map_keys = util.flatten_list(db.get_table("GeographyMapKeys").data.values)

        map_keys_not_in_data = [mk for mk in map_keys if mk not in data.columns]
        if map_keys_not_in_data:
            logging.warning('The following map keys were not found in the spatial join table: {}'.format(map_keys_not_in_data))
        data_cols_not_in_map_keys = [mk for mk in data.columns if mk not in map_keys]
        if data_cols_not_in_map_keys:
            logging.warning('Extra spatial join table columns were found that are not in map keys: {}'.format(data_cols_not_in_map_keys))

        return data, map_keys, geography_to_gau, gau_to_geography

    def log_geo(self):
        """
        get a positional index in self.values (geomap table) that describes the primary_subset geography
        """
        logging.info('Demand primary geography is {}'.format(GeoMapper.demand_primary_geography))
        logging.info('Supply primary geography is {}'.format(GeoMapper.supply_primary_geography))
        logging.info('Dispatch geography is {}'.format(GeoMapper.dispatch_geography))
        if GeoMapper.primary_subset:
            logging.info('Geomap table will be filtered')
            for gau in GeoMapper.primary_subset:
                logging.info(' analysis will include the {} {}'.format(self.gau_to_geography[gau], gau))

        if GeoMapper.breakout_geography:
            logging.info('Breakout geographies will be used')
            for gau in GeoMapper.breakout_geography:
                logging.info(' analysis will include the {} {}'.format(self.gau_to_geography[gau], gau))

    def _get_iloc_geo_subset(self, df, primary_subset=None):
        """
        get a positional index in self.data (geomap table) that describes the primary_subset geography
        """
        primary_subset = GeoMapper.cfg_gau_subset if primary_subset is None else primary_subset
        if primary_subset:
            return list(set(np.concatenate([np.nonzero(df.index.get_level_values(self.gau_to_geography[id])==id)[0] for id in primary_subset if id in self.gau_to_geography])))
        else:
            return range(len(df))

    def _update_geographies_after_subset(self):
        self.filtered_values = self.data.iloc[self._get_iloc_geo_subset(self.data)]
        for key in self.geography_to_gau:
            self.geography_to_gau[key] = list(set(self.filtered_values.index.get_level_values(key)))
            self.geography_to_gau[key].sort()

    def _normalize(self, table, levels):
        if table.index.nlevels>1:
            table = table.groupby(level=levels).transform(lambda x: x / (x.sum()))
            table = table.fillna(0)
        else:
            table[:] = 1
        return table

    def _create_composite_geography_level(self, new_level_name, base_geography, breakout_geography):
        base_gaus = np.array(self.data.index.get_level_values(base_geography))
        impacted_gaus = set()
        for gau in breakout_geography:
            index = np.nonzero(self.data.index.get_level_values(self.gau_to_geography[gau]) == gau)[0]
            impacted_gaus = impacted_gaus | set(base_gaus[index])
            base_gaus[index] = gau

        #        if any(impacted in breakout_geography_id for impacted in impacted_gaus):
        #            raise ValueError('breakout geographies in config cannot overlap geographically')

        self.data[new_level_name] = base_gaus
        self.data = self.data.set_index(new_level_name, append=True)
        # add to self.geographies
        self.geography_to_gau[new_level_name] = list(set(self.data.index.get_level_values(new_level_name)))


    def _create_composite_geography_levels(self):
        """
        Potential to create one for primary geography and one for dispatch geography
        """
        if GeoMapper.breakout_geography and (GeoMapper.demand_primary_geography not in self.data.index.names):
            self._create_composite_geography_level(GeoMapper.demand_primary_geography, GeoMapper.base_demand_primary_geography, GeoMapper.breakout_geography)

        if GeoMapper.breakout_geography and (GeoMapper.supply_primary_geography not in self.data.index.names):
            self._create_composite_geography_level(GeoMapper.supply_primary_geography, GeoMapper.base_supply_primary_geography, GeoMapper.breakout_geography)

        if GeoMapper.disagg_breakout_geography and (GeoMapper.disagg_geography not in self.data.index.names):
            self._create_composite_geography_level(GeoMapper.disagg_geography, GeoMapper.base_disagg_geography, GeoMapper.disagg_breakout_geography)

        if GeoMapper.dispatch_breakout_geography and (GeoMapper.dispatch_geography not in self.data.index.names):
            self._create_composite_geography_level(GeoMapper.dispatch_geography, GeoMapper.base_dispatch_geography, GeoMapper.dispatch_breakout_geography)


    def map_df(self, current_geography, converted_geography, normalize_as='total', map_key=None, reset_index=False,
               eliminate_zeros=True, primary_subset='from config', geomap_data='from self', filter_geo=True, active_gaus=None):
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
        assert normalize_as=='total' or normalize_as=='intensity', "normalize_as is {} and must be either total or intensity".format(normalize_as)
        geomap_data = self.data if geomap_data=='from self' else geomap_data
        map_key = cfg.getParam('default_geography_map_key') if map_key is None else map_key
        table = geomap_data[map_key].to_frame()

        if primary_subset == 'from config' and filter_geo:
            table = table.iloc[self._get_iloc_geo_subset(table, GeoMapper.cfg_gau_subset)]

        if active_gaus is not None:
            iloc_subset = self._get_iloc_geo_subset(table, list(active_gaus))
            # if we have a gau filter that doesn't intersect with the active gaus, it can happen that we have no overlaps
            # in this instance, we just want to zero the table todo: how will this work with intensities?
            if len(iloc_subset):
                table = table.iloc[iloc_subset]
            else:
                table[:] = 0

        current_geography = util.ensure_iterable(current_geography)
        converted_geography = util.ensure_iterable(converted_geography)
        union_geo = list(set(current_geography) | set(converted_geography))

        table = table.groupby(level=union_geo).sum()
        if normalize_as=='total':
            table = self._normalize(table, current_geography)

        if normalize_as=='intensity':
            table = self._normalize(table, converted_geography)

        if reset_index:
            table = table.reset_index()

        if not eliminate_zeros:
            index = pd.MultiIndex.from_product(table.index.levels, names=table.index.names)
            table = table.reorder_levels(index.names)
            table = table.reindex(index, fill_value=0.0)

        return table

    @staticmethod
    def reorder_df_geo_left_year_right(df, current_geography):
        if 'year' in df.index.names:
            y_or_v = ['year']
        elif 'vintage' in df.index.names:
            y_or_v = ['vintage']
        else:
            y_or_v = []
        new_order = [current_geography] + [l for l in df.index.names if l not in [current_geography] + y_or_v] + y_or_v
        mapped_data = df.reorder_levels(new_order)
        return mapped_data

    @classmethod
    def geo_map(cls, df, current_geography, converted_geography, current_data_type, geography_map_key=None, fill_value=0.,filter_geo=True, remove_current_geography=True):
        if current_geography==converted_geography:
            return df
        assert current_geography in df.index.names
        geography_map_key = geography_map_key or GeoMapper.default_geography_map_key
        propper_length = np.product([len(set(df.index.get_level_values(x))) for x in df.index.names])
        if len(df) != propper_length and current_data_type == 'intensity' and len([name for name in df.index.names if name not in ['year', 'vintage', current_geography]])>0:
            # special case were if we don't have full geography coverage on all our index levels an implied fill value of zero causes issues
            # the solution is to groupby any extra levels and do a geomap for each group separately
            levels = [name for name in df.index.names if name not in ['year', 'vintage', current_geography]]
            groups = df.groupby(level=levels).groups
            map_df = []
            for elements in groups.keys():
                slice = util.df_slice(df, elements, levels)
                active_gaus = slice.index.get_level_values(current_geography).unique()
                slice_map_df = cls.get_instance().map_df(current_geography, converted_geography, normalize_as=current_data_type,
                                     map_key=geography_map_key, filter_geo=filter_geo, active_gaus=active_gaus)
                map_df.append(slice_map_df)
            map_df = pd.concat(map_df, keys=groups.keys(), names=levels)
        else:
            # create dataframe with map from one geography to another
            active_gaus = df.index.get_level_values(current_geography).unique()
            map_df = cls.get_instance().map_df(current_geography, converted_geography, normalize_as=current_data_type,
                                 map_key=geography_map_key, filter_geo=filter_geo, active_gaus=active_gaus)

        mapped_data = util.DfOper.mult([df, map_df], fill_value=fill_value)
        if remove_current_geography:
            mapped_data = util.remove_df_levels(mapped_data, current_geography)
        if hasattr(mapped_data.index, 'swaplevel'):
            mapped_data = GeoMapper.reorder_df_geo_left_year_right(mapped_data, converted_geography)
        return mapped_data.sort_index()

    def filter_extra_geos_from_df(self, df):
        # we have a subset geography and should remove the data that is completely outside of the breakout
        if GeoMapper.cfg_gau_subset:
            levels = [n for n in df.index.names if n in self.geography_to_gau]
            elements = [self.geography_to_gau[n] for n in levels]
            indexer = util.level_specific_indexer(df, levels=levels, elements=elements)
            df = df.sort_index()
            df = df.loc[indexer, :]
            return df.reset_index().set_index(df.index.names).sort_index()
        else:
            return df

    def make_new_geography_name(self, base_geography, gau_breakout=None):
        if gau_breakout:
            base_geography += " breaking out " + ", ".join(gau_breakout)
        return base_geography

    def get_native_current_foreign_gaus(self, df, current_geography):
        native_gaus = set(self.geography_to_gau_unfiltered[current_geography])
        current_gaus = set(df.index.get_level_values(current_geography))
        foreign_gaus = current_gaus - native_gaus
        return native_gaus, current_gaus, foreign_gaus

    def _update_dataframe_totals_after_foreign_gau(self, df, current_geography, foreign_geography, impacted_gaus, foreign_gau, map_key, zero_out_negatives):
        y_or_v = GeoMapper._get_df_time_index_name(df)
        # we first need to do a clean time series
        # then we need to allocate out and subtract
        indexer = util.level_specific_indexer(df, current_geography, [impacted_gaus])
        impacted_gaus_slice = df.loc[indexer, :].reset_index().set_index(df.index.names)

        foreign_gau_slice = util.df_slice(df, foreign_gau, current_geography, drop_level=False, reset_index=True)
        foreign_gau_slice.index = foreign_gau_slice.index.rename(foreign_geography, level=current_geography)
        foreign_gau_years = foreign_gau_slice.dropna().index.get_level_values(y_or_v).unique()
        all_years = sorted(df.index.get_level_values(y_or_v).unique())

        impacted_gaus_slice_reduced_years = util.df_slice(impacted_gaus_slice, foreign_gau_years, y_or_v, drop_level=False, reset_index=True)
        foreign_gau_slice_reduced_years = util.df_slice(foreign_gau_slice, foreign_gau_years, y_or_v, drop_level=False, reset_index=True)

        # do the allocation, take the ratio of foreign to native, do a clean timeseries, then reconstitute the foreign gau data over all years
        allocation = self.map_df(foreign_geography, current_geography, map_key=map_key, primary_subset=[foreign_gau])
        allocated_foreign_gau_slice = util.DfOper.mult((foreign_gau_slice_reduced_years, allocation), fill_value=np.nan)
        allocated_foreign_gau_slice = allocated_foreign_gau_slice.reorder_levels([-1]+range(df.index.nlevels))
        ratio_allocated_to_impacted = util.DfOper.divi((allocated_foreign_gau_slice, impacted_gaus_slice_reduced_years), fill_value=np.nan, non_expandable_levels=[])
        ratio_allocated_to_impacted.iloc[np.nonzero(impacted_gaus_slice_reduced_years.values==0)] = 0
        ratio_allocated_to_impacted = ratio_allocated_to_impacted.dropna().reset_index().set_index(ratio_allocated_to_impacted.index.names)

        clean_ratio = TimeSeries.clean(data=ratio_allocated_to_impacted, newindex=all_years, time_index_name=y_or_v, interpolation_method='linear_interpolation', extrapolation_method='nearest')

        allocated_foreign_gau_slice_all_years = util.DfOper.mult((clean_ratio, impacted_gaus_slice), fill_value=np.nan, non_expandable_levels=[])
        allocated_foreign_gau_slice_new_geo = util.remove_df_levels(allocated_foreign_gau_slice_all_years, foreign_geography)
        allocated_foreign_gau_slice_foreign_geo = util.remove_df_levels(allocated_foreign_gau_slice_all_years, current_geography)
        allocated_foreign_gau_slice_foreign_geo.index = allocated_foreign_gau_slice_foreign_geo.index.rename(current_geography, level=foreign_geography)

        # update foreign GAUs after clean timeseries
        allocated_gau_years = list(allocated_foreign_gau_slice_foreign_geo.index.get_level_values(y_or_v).values)
        allocated_foreign_gau_slice_foreign_geo = allocated_foreign_gau_slice_foreign_geo.reorder_levels(df.index.names).sort()
        afgsfg = allocated_foreign_gau_slice_foreign_geo # to give it a shorter name
        afgsfg = afgsfg.reindex(index=pd.MultiIndex.from_product(afgsfg.index.levels, names=afgsfg.index.names), fill_value=np.nan)
        indexer = util.level_specific_indexer(afgsfg, [current_geography, y_or_v], [foreign_gau, allocated_gau_years])

        df.loc[indexer, :] = afgsfg.loc[indexer, :]

        new_impacted_gaus = util.DfOper.subt((impacted_gaus_slice, allocated_foreign_gau_slice_new_geo), fill_value=np.nan, non_expandable_levels=[])
        new_impacted_gaus = new_impacted_gaus.reorder_levels(df.index.names).sort()
        if new_impacted_gaus.min().min() < 0:
            if not zero_out_negatives:
                raise ValueError(
                    'Negative values resulted from subtracting the foreign gau from the base gaus. This is the resulting dataframe: {}'.format(new_impacted_gaus))
            else:
                new_impacted_gaus[new_impacted_gaus < 0] = 0
        if new_impacted_gaus.isnull().all().value:
            pdb.set_trace()
            raise ValueError('Year or vitages did not overlap between the foreign gaus and impacted gaus')

        # update native GAUs after netting out foreign gaus
        impacted_gau_years = [int(x) for x in impacted_gaus_slice.index.get_level_values(y_or_v).values]
        indexer = util.level_specific_indexer(df, [current_geography, y_or_v], [impacted_gaus, impacted_gau_years])
        try:
            df.loc[indexer, :] = new_impacted_gaus.loc[indexer, :]
        except:
            pdb.set_trace()

        return df

    @staticmethod
    def _get_df_time_index_name(df):
        if 'year' in df.index.names:
            return 'year'
        elif 'vintage' in df.index.names:
            return 'vintage'
        else:
            raise ValueError('df must either have year or vintage to incorporate foreign gaus')

    @staticmethod
    def _add_missing_level_elements_to_foreign_gaus(df, current_geography):
        y_or_v = GeoMapper._get_df_time_index_name(df)
        for index_name in df.index.names:
            if index_name == current_geography or index_name == y_or_v:
                continue
            needed_elements = list(set(df.index.get_level_values(index_name)))
            df = util.reindex_df_level_with_new_elements(df, index_name, needed_elements)
        df = df.fillna(0).sort()
        return df

    def incorporate_foreign_gaus(self, df, current_geography, data_type, map_key, keep_oth_index_over_oth_gau=False, zero_out_negatives=True):
        native_gaus, current_gaus, foreign_gaus = self.get_native_current_foreign_gaus(df, current_geography)
        # we don't have any foreign gaus
        if not foreign_gaus or not cfg.getParamAsBoolean('include_foreign_gaus'):
            return df, current_geography

        y_or_v = GeoMapper._get_df_time_index_name(df)

        index_with_nans = [df.index.names[i] for i in set(np.nonzero([[ri is np.nan for ri in row] for row in df.index.get_values()])[1])]
        # if we have an index with nan, that typically indicates that one of the foreign gaus didn't have all the index levels
        # if this is the case, we have two options (1) ignore the foreign gau (2) get rid of the other index
        if index_with_nans and (keep_oth_index_over_oth_gau or data_type=='intensity'):
            return self.filter_foreign_gaus(df, current_geography), current_geography
        else:
            assert (y_or_v not in index_with_nans) and (current_geography not in index_with_nans)
            # we need to eliminate levels with nan before moving on
            df = util.remove_df_levels(df, index_with_nans)

        # add missing level indicies for foreign gaus, this must be done before we fill in years because we use a fill value of zero
        df = self._add_missing_level_elements_to_foreign_gaus(df, current_geography)

        # we need all the index level combinations to have all years for this to work correctly
        df_no_foreign_gaus = self.filter_foreign_gaus(df, current_geography)
        df_years = sorted(list(set(df_no_foreign_gaus.index.get_level_values(y_or_v).values)))
        df = util.reindex_df_level_with_new_elements(df, y_or_v, df_years)

        base_gaus = np.array(self.data.index.get_level_values(current_geography))
        for foreign_gau in foreign_gaus:
            foreign_geography = self.gau_to_geography[foreign_gau]
            index = np.nonzero(self.data.index.get_level_values(self.gau_to_geography[foreign_gau])==foreign_gau)[0]
            impacted_gaus = list(set(base_gaus[index]))
            base_gaus[index] = foreign_gau
            if any(impacted in foreign_gaus for impacted in impacted_gaus):
                raise ValueError('foreign gaus in the database cannot overlap geographically')

            # if the data_type is a total, we need to net out the total
            if data_type=='total':
                df = self._update_dataframe_totals_after_foreign_gau(df, current_geography, foreign_geography, impacted_gaus, foreign_gau, map_key, zero_out_negatives)
            elif data_type == 'intensity':
                logging.debug('Foreign GAUs with intensities is not yet implemented, totals will not be conserved')

        assert not any([any([ri is np.nan for ri in row]) for row in df.index.get_values()])
        new_geography_name = self.make_new_geography_name(current_geography, list(foreign_gaus))
        df.index = df.index.rename(new_geography_name, level=current_geography)
        if new_geography_name not in self.geography_to_gau:
            self.add_new_geography(new_geography_name, base_gaus)
        # df = GeoMapper.reorder_level_names_after_incorporating_foreign_gaus(df, new_geography_name, y_or_v)
        return df, new_geography_name

    def add_new_geography(self, new_geography_name, base_gaus):
        self.data[new_geography_name] = base_gaus
        self.data = self.data.set_index(new_geography_name, append=True)
        # add to self.geography_to_gau
        self.geography_to_gau_unfiltered[new_geography_name] = sorted(list(set(self.data.index.get_level_values(new_geography_name))))
        self._update_geographies_after_subset()
        self.geography_to_gau[new_geography_name] = sorted(list(set(self.filtered_values.index.get_level_values(new_geography_name))))

    def filter_foreign_gaus(self, df, current_geography, foreign_gaus=None):
        """ Remove foreign gaus from the dataframe
        """
        ncf = self.get_native_current_foreign_gaus(df, current_geography)
        foreign_gaus = ncf[2] if foreign_gaus is None else foreign_gaus
        current_gaus = ncf[1]

        if not foreign_gaus:
            return df

        indexer = util.level_specific_indexer(df, current_geography, [list(current_gaus-foreign_gaus)])
        index_names = df.index.names
        df = df.loc[indexer,].reset_index().set_index(index_names).sort_index()
        return df