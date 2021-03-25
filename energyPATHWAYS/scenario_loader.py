import json
import os
import logging
import itertools
from collections import defaultdict
import pdb
import pandas as pd
from energyPATHWAYS.util import csv_read_table
from csvdb.data_object import get_database

from csvdb.error import ScenarioFileError
from csvdb.scenario import AbstractScenario, CsvdbFilter

SCENARIO_FILE = 'runs_key.csv'
INDEX_DIVIDER = '--'

class Scenario(AbstractScenario):
    MEASURE_CATEGORIES = {"DemandEnergyEfficiencyMeasures",
                          "DemandFlexibleLoadMeasures",
                          "DemandFuelSwitchingMeasures",
                          "DemandServiceDemandMeasures",
                          "DemandSalesShareMeasures",
                          "DemandStockMeasures",
                          "BlendNodeBlendMeasures",
                          "SupplyExportMeasures",
                          "SupplySalesMeasures",
                          "SupplySalesShareMeasures",
                          "SupplyStockMeasures",
                          "CO2PriceMeasures"}

    def __init__(self, scenario_name, dirpath=None):
        dirpath = dirpath or os.getcwd()

        self._id = scenario_name
        self._bucket_lookup = self._load_bucket_lookup()

        self._measures = {category: defaultdict(list) for category in self.MEASURE_CATEGORIES}
        self._sensitivities = defaultdict(dict)

        # N.B. self.pathname is set in super's __init__()
        super(Scenario, self).__init__(scenario_name, dirpath, 'csv', filename=SCENARIO_FILE)

    # Required subclass method, called by AbstractScenario
    def load(self):
        df = pd.read_csv(self.pathname, index_col=0)
        df.fillna('', inplace=True)

        # TODO: (RJP) discuss with Ryan. Not sure this is still relevant.
        # Special case where there are no sensitivity columns. We assume the user just
        # wants a sensitivity with all the reference selections.
        if df.shape == 1:
            df['reference'] = ''

        try:
            scenario_data = df[self.name]

        except KeyError:
            raise ScenarioFileError(self.pathname, "Scenario '{}' not found.".format(self.name))

        for key, sens_name in scenario_data.iteritems():
            # TODO (RJP): skip measures with no value in the current sensitivity column?
            if sens_name == '':
                continue

            parts = key.split(INDEX_DIVIDER)
            tbl_name = parts[0]

            if tbl_name in self.MEASURE_CATEGORIES:
                if len(parts) != 3:
                    raise ValueError("Expected measure to have 3 parts delimited by '--', got {}".format(parts))

                idx_value = parts[1]
                tbl_key   = parts[2]
                self._add_measure(tbl_name, tbl_key, idx_value)

            else: # sensitivity scenario
                tbl_key = parts[1]
                constraints = dict([tuple(c.split(':')) for c in parts[2:]])
                sorted_constraints = list((key, constraints[key]) for key in sorted(constraints.keys()))
                self._add_sensitivity(tbl_name, tbl_key, sens_name, sorted_constraints)

    def _add_sensitivity(self, tbl_name, tbl_key, sens_name, constraints):
        obj = CsvdbFilter(tbl_name, tbl_key, sens_name, constraints)
        self.add_filter(obj)

    def _add_measure(self, tbl_name, measure, idx_value):
        try:
            bucket_id = self._bucket_lookup[tbl_name][measure]
        except KeyError:
            raise ValueError(
                "{} scenario wants to use {} {} but no such measure was found in the database.".format(self._id,
                                                                                                       tbl_name,
                                                                                                       measure))
        if measure in self._measures[tbl_name][bucket_id]:
            raise ValueError("Scenario uses {} {} more than once.".format(tbl_name, measure))

        self._measures[tbl_name][bucket_id].append(measure)

    def _load_sensitivity(self, filter):
        db = get_database()

        table       = filter.table_name
        name        = filter.key_value
        sensitivity = filter.sens_value

        if name in self._sensitivities[table]:
            raise ValueError("Scenario specifies sensitivity for {} {} more than once".format(table, name))

        # Check that the sensitivity actually exists in the database before using it
        md = db.table_metadata(table)

        # TODO: (RJP) Why aren't explicit constraints applied here?
        filters = {'sensitivity' : sensitivity, md.key_col : name}
        data = csv_read_table(table, **filters)

        if data is None or len(data) == 0:
            raise ValueError("Could not find sensitivity '{}' for {} {}.".format(sensitivity, table, name))

        self._sensitivities[table][name] = sensitivity

    # Deprecated
    def load_JSON(self):
        with open(self.pathname) as f:
            self.top_dict = top_dict = json.load(f)

        # Each scenario file has a top-level dict with one entry, keyed by scenario
        # name, which matches the basename of the file. We sanity check this.
        if len(top_dict) != 1:
            keys = ", ".join(top_dict.keys())
            raise ScenarioFileError(self.pathname, "Expected one scenario at top level, got: {}".format(keys))

        try:
            scenario_dict = top_dict[self.name]
        except KeyError:
            raise ScenarioFileError(self.pathname, "Scenario file is missing scenario '{}'".format(self.name))

        # set legacy instance variable name (deprecated?)
        self._name = self.name

        # In the second level we have 'Supply Case' and 'Demand Case', and in each there's a 'Sensitivities' list,
        # whose values are of the form:
        #   {'table': 'SupplyExport', 'sensitivity': 'fossil exports 0 by 2030', 'name': 'Coal Primary - Domestic'}
        # which we just combine. Note that the 'name' value is the value for the key col, which may not be "name".

        # This data structure is used by csvdb, but not by _load_measures() and _load_sensitivity(), below.
        # TODO: We could eliminate the redundant parsing, but it may not be worth the trouble for now.
        for subdict in scenario_dict.values():
            for sens in subdict.get('Sensitivities', []):
                obj = CsvdbFilter(sens['table'], sens['name'], sens['sensitivity'])  # no constraints in JSON currently
                self.add_filter(obj)

    @staticmethod
    def _index_col(measure_table):
        """Returns the name of the column that should be used to index the given type of measure"""
        if measure_table.startswith('Demand'):
            return 'subsector'
        elif measure_table == "BlendNodeBlendMeasures":
            return 'blend_node'
        else:
            return 'supply_node'

    @staticmethod
    def _subindex_col(measure_table):
        """Returns the name of the column that subindexes the given type of measure, i.e. the technology id column"""
        if measure_table in ("DemandSalesShareMeasures", "DemandStockMeasures"):
            return 'demand_technology'
        elif measure_table in ("SupplySalesMeasures", "SupplySalesShareMeasures", "SupplyStockMeasures"):
            return 'supply_technology'
        else:
            return None

    def _load_bucket_lookup(self):
        """
        Returns a dictionary matching each measure_id to the combination of subsector/supply_node and technology
        that it applies to. If the measure does not apply to a technology, the second member of tuple is None.
        """
        from energyPATHWAYS.util import table_data

        lookup = defaultdict(dict)

        for table in self.MEASURE_CATEGORIES:
            index_col = self._index_col(table)
            subindex_col = self._subindex_col(table)
            col_names = ['name', index_col] + ([subindex_col] if subindex_col else [])
            num_cols = len(col_names)

            tbl_dict = lookup[table]
            tup_iter = table_data(table, column_names=col_names, as_tup_iter=True)

            for row in tup_iter:
                tbl_dict[row[0]] = (row[1], row[2] if num_cols == 3 else None)

        return lookup

    # Deprecated
    def _load_sensitivities_JSON(self, sensitivities):
        if not isinstance(sensitivities, list):
            raise ValueError("The 'Sensitivities' for a scenario should be a list of objects containing "
                             "the keys 'table', 'name' and 'sensitivity'.")

        db = get_database()

        for sensitivity_spec in sensitivities:
            table       = sensitivity_spec['table']
            name        = sensitivity_spec['name']
            sensitivity = sensitivity_spec['sensitivity']

            if name in self._sensitivities[table]:
                raise ValueError("Scenario specifies sensitivity for {} {} more than once".format(table, name))

            if table != "ShapeData":
                # Check that the sensitivity actually exists in the database before using it
                md = db.table_metadata(table)
                filters = {'sensitivity' : sensitivity, md.key_col : name}
                data = csv_read_table(table, **filters)

                if data is None or len(data) == 0:
                    raise ValueError("Could not find sensitivity '{}' for {} {}.".format(sensitivity, table, name))

            self._sensitivities[table][name] = sensitivity

    # Deprecated
    def _load_measures(self, tree):
        """
        Finds all measures in the Scenario by recursively scanning the parsed json and organizes them by type
        (i.e. table) and a "bucket_id", which is a tuple of subsector/node id and technology id. If the particular
        measure doesn't applies to a whole subsector/node rather than a technology, the second member of the
        bucket_id tuple will be None.
        """
        for key, subtree in tree.iteritems():
            if key.lower() == 'sensitivities':
                self._load_sensitivities_JSON(subtree)

            elif isinstance(subtree, dict):
                self._load_measures(subtree)

            elif key in self.MEASURE_CATEGORIES and isinstance(subtree, list):
                for measure in subtree:
                    try:
                        bucket_id = self._bucket_lookup[key][measure]
                    except KeyError:
                        raise ValueError("{} scenario wants to use {} {} but no such measure was found in the database.".format(self._id, key, measure))

                    if measure in self._measures[key][bucket_id]:
                        raise ValueError("Scenario uses {} {} more than once.".format(key, measure))

                    self._measures[key][bucket_id].append(measure)

            elif not isinstance(subtree, basestring):
                pdb.set_trace()
                raise ValueError("Encountered an uninterpretable non-string leaf node while loading the scenario. "
                                 "The node is '{}: {}'".format(key, subtree))

    def get_measures(self, category, subsector_or_node_id, tech_id=None):
        """
        This method is pretty self-explanatory, but note the implicit validation: If the user requests an unknown
        category, a KeyError will be raised because the top level of this stricture is a regular dict. If they
        request a combination of subsector/supply_node and technology that happens to have no measures for that
        category, an empty list will be returned because the second layer is a defaultdict.

        Note also that if tech_id is None, the only measure_ids returned will be those that pertain to the
        subsector or supply node as a whole, and not to any individual technology.
        """
        measure_ids = self._measures[category][(subsector_or_node_id, tech_id)]

        # Log when measure_ids are found
        if measure_ids:
            log_msg = "{} {} loaded for {} {}".format(
                category, measure_ids, self._index_col(category), subsector_or_node_id
            )
            if tech_id:
                log_msg += " and {} {}".format(self._subindex_col(category), tech_id)
            logging.debug(log_msg)

        return measure_ids

    def all_measure_ids_by_category(self):
        # This list(itertools...) nonsense is just to flatten to a single list from a list-of-lists
        return {category: list(itertools.chain.from_iterable(contents.values()))
                for category, contents in self._measures.iteritems()}
