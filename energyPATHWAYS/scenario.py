import json
import os
from collections import defaultdict
from csvdb.error import ScenarioFileError
from csvdb.scenario import AbstractScenario, CsvdbFilter

class Scenario(AbstractScenario):
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

    def __init__(self, scenario_name, dirpath=None):
        dirpath = dirpath or os.path.abspath(os.curdir)
        super(Scenario, self).__init__(scenario_name, dirpath, 'json')

        self._measures = {category: defaultdict(list) for category in self.MEASURE_CATEGORIES}
        self._sensitivities = defaultdict(dict)

        self._load_measures(scenario_name)


    def load(self):
        with open(self.pathname) as f:
            top_dict = json.load(f)

        # Each scenario file has a top-level dict with one entry, keyed by scenario
        # name, which matches the basename of the file. We sanity check this.
        if len(top_dict) != 1:
            keys = ", ".join(top_dict.keys())
            raise ScenarioFileError(self.pathname, "Expected one scenario at top level, got: {}".format(keys))

        try:
            scenario_dict = top_dict[self.name]
        except KeyError:
            raise ScenarioFileError(self.pathname, "Scenario file is missing scenario '{}'".format(self.name))

        # In the second level we have 'Supply Case' and 'Demand Case', and in each there's a 'Sensitivities' list,
        # whose values are of the form:
        #   {'table': 'SupplyExport', 'sensitivity': 'fossil exports 0 by 2030', 'name': 'Coal Primary - Domestic'}
        # which we just combine. Note that the 'name' value is the value for the key col, which may not be "name".

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

