import psycopg2.extras
import json
import re
from collections import OrderedDict, Callable
import energyPATHWAYS.config as cfg

class DefaultOrderedDict(OrderedDict):
    # Source: http://stackoverflow.com/a/6190500/562769
    def __init__(self, default_factory=None, *a, **kw):
        if (default_factory is not None and
           not isinstance(default_factory, Callable)):
            raise TypeError('first argument must be callable')
        OrderedDict.__init__(self, *a, **kw)
        self.default_factory = default_factory

    def __getitem__(self, key):
        try:
            return OrderedDict.__getitem__(self, key)
        except KeyError:
            return self.__missing__(key)

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        self[key] = value = self.default_factory()
        return value

    def __reduce__(self):
        if self.default_factory is None:
            args = tuple()
        else:
            args = self.default_factory,
        return type(self), args, None, None, self.items()

    def copy(self):
        return self.__copy__()

    def __copy__(self):
        return type(self)(self.default_factory, self)

    def __deepcopy__(self, memo):
        import copy

cfg.init_cfgfile('../../model_runs/us_model_example/config.INI')
cfg.init_db()
cur = cfg.con.cursor(cursor_factory=psycopg2.extras.DictCursor)

DEMAND = 'Demand'
SUPPLY = 'Supply'
SIDES = [DEMAND, SUPPLY]

package_data_tables = {DEMAND: {
                            "energy_efficiency_package_id": "DemandEnergyEfficiencyMeasurePackages",
                            "flexible_load_package_id": "DemandFlexibleLoadMeasurePackages",
                            "fuel_switching_package_id": "DemandFuelSwitchingMeasurePackages",
                            "service_demand_package_id": "DemandServiceDemandMeasurePackages",
                            "sales_package_id": "DemandSalesShareMeasurePackages",
                            "stock_package_id": "DemandStockMeasurePackages"
                       },
                       SUPPLY: {
                           "blend_package_id": "BlendNodeBlendMeasurePackages",
                           "export_package_id": "SupplyExportMeasurePackages",
                           "sales_package_id": "SupplySalesMeasurePackages",
                           "sales_share_package_id": "SupplySalesShareMeasurePackages",
                           "stock_package_id": "SupplyStockMeasurePackages"
                       }
}

# Prepare a nested lookup for which measure_ids go with which packages
packages = {DEMAND: DefaultOrderedDict(lambda: DefaultOrderedDict(list)),
            SUPPLY: DefaultOrderedDict(lambda: DefaultOrderedDict(list))}
for side in SIDES:
    for table in package_data_tables[side].values():
        cur.execute("""
          SELECT "{0}".id, "{0}".name, ARRAY_AGG("{0}Data".measure_id) AS measure_ids
          FROM "{0}" JOIN "{0}Data" ON "{0}".id = "{0}Data".package_id
          GROUP BY "{0}".id, "{0}".name
        """.format(table,))
        for row in cur.fetchall():
            leaf = packages[side][table][row['id']] = row['measure_ids']

# Queries
queries = {DEMAND: """
    SELECT "Scenarios".id AS scenario_id, "Scenarios".name AS scenario_name,
           "Scenarios".description AS scenario_description,
           "DemandCases".id AS demand_case_id, "DemandCases".name AS demand_case_name,
           "DemandSubsectors".name AS sector_or_node_name,
           "DemandStates".*
    FROM "Scenarios"
    JOIN "DemandCases" ON "DemandCases".id = "Scenarios".demand_case
    JOIN "DemandCasesData" ON "DemandCasesData".demand_case_id = "DemandCases".id
    JOIN "DemandStates" ON "DemandStates".id = "DemandCasesData".demand_state_id
    JOIN "DemandSubsectors" ON "DemandSubsectors".id = "DemandStates".subsector_id;
"""}
queries[SUPPLY] = queries[DEMAND].replace('DemandSubsectors', 'SupplyNodes').replace('subsector_id',
                  'supply_node_id').replace('demand', 'supply').replace('Demand', 'Supply')

# Populate hierarachical data structure for scenarios
scenarios = DefaultOrderedDict(lambda: DefaultOrderedDict(DefaultOrderedDict))

for side in SIDES:
    cur.execute(queries[side])
    case_name_col = "{}_case_name".format(side.lower(),)
    for row in cur.fetchall():
        # Yes, this value is unnecessarily set repeatedly (one time for each State within the Scenario)
        # but it's not worth optimizing
        scenarios[row['scenario_name']]['description'] = row['scenario_description']

        state = OrderedDict({'description': row['description']})
        for id_col, table_name in package_data_tables[side].iteritems():
            if row[id_col] is not None:
                state[table_name.replace('Packages', 's')] = sorted(packages[side][table_name][row[id_col]])
        case_key = "{} Case: {}".format(side, row[case_name_col])
        scenarios[row['scenario_name']][case_key][row['sector_or_node_name']] = state

# Output to json
for name, content in scenarios.iteritems():
    file_name = re.sub('[./\s]+', '_', name).lower() + '.json'
    print "Writing {}".format(file_name,)
    with open(file_name, 'w') as outfile:
        json.dump({name: content}, outfile, indent=4, separators=(',', ': ')) # sort_keys=True,
