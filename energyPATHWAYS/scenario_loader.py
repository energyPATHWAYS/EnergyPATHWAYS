import json
import os
import logging
import itertools
from collections import defaultdict
import config as cfg
import pdb
from .util import csv_read_table

class Scenario():
    MEASURE_CATEGORIES = ("DemandEnergyEfficiencyMeasures",
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
                          "CO2PriceMeasures")

    # These are the columns that various data tables use to refer to the id of their parent table
    # Order matters here; we use the first one that is found in the table. This is because some tables'
    # "true" parent is a subsector/node, but they are further subindexed by technology
    PARENT_COLUMN_NAMES = ('parent', 'subsector', 'supply_node', 'primary_node', 'import_node',
                           'demand_tech', 'demand_technology', 'supply_tech', 'supply_technology')

    def __init__(self, scenario):
        self._id = scenario
        self._bucket_lookup = self._load_bucket_lookup()

        scenario_file = scenario if scenario.endswith('.json') else scenario + '.json'
        path_to_scenario_file = os.path.join(cfg.workingdir, scenario_file)
        with open(path_to_scenario_file) as scenario_data:
            scenario = json.load(scenario_data)

        assert len(scenario) == 1, "More than one scenario found at top level in {}: {}".format(
            path_to_scenario_file, ", ".join(scenario_data.keys)
        )

        # The name of the scenario is just the key at the top of the dictionary hierarchy
        self._name = scenario.keys()[0]

        # Note that the top layer of this dictionary is intentionally NOT a defaultdict, so that we can be sure
        # it has all the keys in MEASURE_CATEGORIES and no other keys, which is useful when measures are requested
        # later (if the user asks for an unknown measure type we get a KeyError rather than silently returning
        # an empty list.)
        self._measures = {category: defaultdict(list) for category in self.MEASURE_CATEGORIES}
        self._sensitivities = defaultdict(dict)
        self._load_measures(scenario)

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

    @classmethod
    def parent_col(cls, data_table):
        """Returns the name of the column in the data table that references the parent table"""

        # These are one-off exceptions to our general preference order for parent columns
        if data_table == 'DemandSalesData':
            return 'demand_technology'

        if data_table == 'SupplyTechsEfficiencyData':
            return 'supply_tech'

        if data_table in ('SupplySalesData', 'SupplySalesShareData'):
            return 'supply_technology'

        cfg.cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
        """, (data_table,))

        cols = [row[0] for row in cfg.cur]
        if not cols:
            raise ValueError("Could not find any columns for table {}. Did you misspell the table "
                             "name?".format(data_table))
        # We do it this way so that we use a column earlier in the PARENT_COLUMN_NAMES list over one that's later
        parent_cols = [col for col in cls.PARENT_COLUMN_NAMES if col in cols]
        if not parent_cols:
            raise ValueError("Could not find any known parent-referencing columns in {}. "
                             "Are you sure it's a table that references a parent table?".format(data_table))
        elif len(parent_cols) > 1:
            logging.debug("More than one potential parent-referencing column was found in {}; "
                          "we are using the first in this list: {}".format(data_table, parent_cols))
        return parent_cols[0]

    def _load_bucket_lookup(self):
        """
        Returns a dictionary matching each measure_id to the combination of subsector/supply_node and technology
        that it applies to. If the measure does not apply to a technology, the second member of tuple is None.
        """
        from .util import table_data

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

    def _load_sensitivities(self, sensitivities):
        if not isinstance(sensitivities, list):
            raise ValueError("The 'Sensitivities' for a scenario should be a list of objects containing "
                             "the keys 'table', 'name' and 'sensitivity'.")

        for sensitivity_spec in sensitivities:
            table = sensitivity_spec['table']
            name = sensitivity_spec['name']
            sensitivity = sensitivity_spec['sensitivity']

            if name in self._sensitivities[table]:
                raise ValueError("Scenario specifies sensitivity for {} {} more than once".format(table, name))

            # Check that the sensitivity actually exists in the database before using it
            # TBD: apparently this translation is wrong since DemandEnergyDemands lacks a 'name' column. Needs Ryan's attention...
            filters = {'sensitivity' : sensitivity, 'name' : name}
            data = csv_read_table(table, **filters)

            if len(data) == 0:
                raise ValueError("Could not find sensitivity '{}' for {} {}.".format(sensitivity, table, name))

            self._sensitivities[table][name] = sensitivity

    def _load_measures(self, tree):
        """
        Finds all measures in the Scenario by recursively scanning the parsed json and organizes them by type
        (i.e. table) and a "bucket_id", which is a tuple of subsector/node id and technology id. If the particular
        measure doesn't applies to a whole subsector/node rather than a technology, the second member of the
        bucket_id tuple will be None.
        """
        for key, subtree in tree.iteritems():
            if key.lower() == 'sensitivities':
                self._load_sensitivities(subtree)

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

    def get_sensitivity(self, table, parent_id):
        sensitivity = self._sensitivities[table].get(parent_id)
        if sensitivity:
            logging.debug("Sensitivity '{}' loaded for {} with parent id {}.".format(sensitivity, table, parent_id))
        return sensitivity

    @property
    def name(self):
        return self._name
