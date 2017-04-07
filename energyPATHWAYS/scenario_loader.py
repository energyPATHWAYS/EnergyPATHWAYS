import json
import os
import logging
from collections import defaultdict
import config as cfg


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
                          "SupplyStockMeasures")

    def __init__(self, scenario_id):
        self._id = scenario_id
        self._bucket_lookup = self._load_bucket_lookup()

        path_to_scenario_file = os.path.join(cfg.workingdir, scenario_id + '.json')
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
            return 'subsector_id'
        elif measure_table == "BlendNodeBlendMeasures":
            return 'blend_node_id'
        else:
            return 'supply_node_id'

    @staticmethod
    def _subindex_col(measure_table):
        """Returns the name of the column that subindexes the given type of measure, i.e. the technology id column"""
        if measure_table in ("DemandSalesShareMeasures", "DemandStockMeasures"):
            return 'demand_technology_id'
        elif measure_table in ("SupplySalesMeasures", "SupplySalesShareMeasures", "SupplyStockMeasures"):
            return 'supply_technology_id'
        else:
            return None

    def _load_bucket_lookup(self):
        """
        Returns a dictionary matching each measure_id to the combination of subsector/supply_node and technology
        that it applies to. If the measure does not apply to a technology, the second member of tuple is None.
        """
        lookup = defaultdict(dict)
        for table in self.MEASURE_CATEGORIES:
            subindex_col = self._subindex_col(table)
            if subindex_col:
                cfg.cur.execute('SELECT id, {}, {} FROM "{}";'.format(self._index_col(table), subindex_col, table))
                for row in cfg.cur.fetchall():
                    lookup[table][row[0]] = (row[1], row[2])
            else:
                cfg.cur.execute('SELECT id, {} FROM "{}";'.format(self._index_col(table), table))
                for row in cfg.cur.fetchall():
                    lookup[table][row[0]] = (row[1], None)
        return lookup

    def _load_measures(self, tree):
        """
        Finds all measures in the Scenario by recursively scanning the parsed json and organizes them by type
        (i.e. table) and a "bucket_id", which is a tuple of subsector/node id and technology id. If the particular
        measure doesn't applies to a whole subsector/node rather than a technology, the second member of the
        bucket_id tuple will be None.
        """
        for key, subtree in tree.iteritems():
            if key.lower() == 'sensitivities':
                if not isinstance(subtree, list):
                    raise ValueError("The 'Sensitivities' for a scenario should be a list of objects containing "
                                     "the keys 'table', 'parent_id' and 'sensitivity'.")
                for sensitivity_spec in subtree:
                    # TODO: Would be good to have some validation here that this sensitivity actually exists,
                    # it's just a bit tricky to track down the right parent_id column here
                    table = sensitivity_spec['table']
                    parent_id = sensitivity_spec['parent_id']
                    sensitivity = sensitivity_spec['sensitivity']
                    if parent_id in self._sensitivities[table]:
                        raise ValueError("Scenario specifies sensitivity for {} {} more than once".format(table, parent_id))
                    self._sensitivities[table][parent_id] = sensitivity
            elif isinstance(subtree, dict):
                self._load_measures(subtree)
            elif key in self.MEASURE_CATEGORIES and isinstance(subtree, list):
                for measure in subtree:
                    try:
                        bucket_id = self._bucket_lookup[key][measure]
                    except KeyError:
                        logging.exception("{} scenario wants to use {} {} but no such measure was found "
                                          "in the database.".format(self._id, key, measure))
                        raise
                    if measure in self._measures[key][bucket_id]:
                        raise ValueError("Scenario uses {} {} more than once.".format(key, measure))
                    self._measures[key][bucket_id].append(measure)
            elif not isinstance(subtree, basestring):
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

    def get_sensitivity(self, table, parent_id):
        sensitivity = self._sensitivities[table].get(parent_id)
        if sensitivity:
            logging.debug("Sensitivity {} loaded for {} with parent id {}.".format(sensitivity, table, parent_id))
        return sensitivity

    @property
    def name(self):
        return self._name
