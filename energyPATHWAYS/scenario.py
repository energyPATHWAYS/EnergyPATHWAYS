import json
import os
from csvdb.error import ScenarioFileError
from csvdb.scenario import AbstractScenario, CsvdbFilter

class Scenario(AbstractScenario):
    def __init__(self, scenario_name, dirpath=None):
        dirpath = dirpath or os.path.abspath(os.curdir)
        super(Scenario, self).__init__(scenario_name, dirpath, 'json')

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
