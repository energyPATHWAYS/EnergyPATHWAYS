import json
import os
import logging
import itertools
from collections import defaultdict
import psycopg2
import pandas as pd
import pdb

# postgres stuff
con = None
cur = None

def init_db(pg_host, pg_database, pg_user, pg_password=None):
    global con, cur

    conn_str = "host='%s' dbname='%s' user='%s'" % (pg_host, pg_database, pg_user)
    if pg_password:
        conn_str += " password='%s'" % pg_password

    # Open pathways database
    con = psycopg2.connect(conn_str)
    cur = con.cursor()

def make_unique(names):
    d = defaultdict(int)

    # Count occurrences of each name
    for id, name in names.iteritems():
        d[name] += 1

    for id, name in names.iteritems():
        if d[name] > 1:
            names[id] = names[id] + ' ({})'.format(id)

    return names

table_by_name = {}

def get_name_for_id(table_name, id, fix_dupes=True):
    '''
    Get the string name of the measure in `table_name` with the given `id`.
    Table data are cached when first read.
    '''
    try:
        names = table_by_name[table_name]
    except KeyError:
        query = 'select id, name from "{}"'.format(table_name)
        cur.execute(query)
        names = pd.Series({tup[0] : tup[1] for tup in cur.fetchall()})
        table_by_name[table_name] = names

        if len(names) != len(names.unique()):
            if fix_dupes:
                names = make_unique(names)

    if id in names:
        return names[id]

    print("Id {} was not found for table {}".format(id, table_name))
    return None

def read_foreign_keys():
    from postgres import ForeignKeyQuery

    cur.execute(ForeignKeyQuery)
    rows = cur.fetchall()
    columns = ['table_name', 'column_name', 'foreign_table_name', 'foreign_column_name']
    df = pd.DataFrame(data=rows, columns=columns)
    return df

#
# A few functions from postgres-era energyPATHWAYS.util
#
def sql_read_table(table_name, column_names='*', return_unique=False, return_iterable=False, **filters):
    """Get data from a table filtering by columns
    key word arguments give column name, column criteria pairs
    example:
        util.sql_read_table('DemandDriversID', 'ID', driver='oil and gas mining VOS')
    """
    if not isinstance(column_names, basestring):
        column_names = ', '.join(column_names)
    distinct = 'DISTINCT ' if return_unique else ''
    query = 'SELECT ' + distinct + column_names + ' FROM "%s"' % table_name
    if len(filters):
        datatypes = sql_get_datatype(table_name, filters.keys())
        list_of_filters = ['"' + col + '"=' + fix_sql_query_type(fil, datatypes[col]) if fil is not None else '"' + col + '"is' + 'NULL' for col, fil in filters.items()]
        if list_of_filters:
            query = query + " where " + " and ".join(list_of_filters)
            cur.execute(query)
            data = [tup[0] if len(tup) == 1 else tup for tup in cur.fetchall()]
        else:
            data = [None]

    else:
        cur.execute(query)
        data = [tup[0] if len(tup) == 1 else tup for tup in cur.fetchall()]
    # pull out the first element if length is 1 and we don't want to return an iterable
    if len(data) == 0 or data == [None]:
        return [] if return_iterable else None
    elif len(data) == 1:
        return data if return_iterable else data[0]
    else:
        return data

def sql_get_datatype(table_name, column_names):
    if isinstance(column_names, basestring):
        column_names = [column_names]
    cur.execute("select column_name, data_type from INFORMATION_SCHEMA.COLUMNS where table_name = %s and table_schema = 'public';", (table_name,))
    table_info = cur.fetchall()
    return dict([tup for tup in table_info if tup[0] in column_names])


def fix_sql_query_type(string, sqltype):
    if sqltype == 'INTEGER':
        return str(string)
    else:
        return "'" + str(string) + "'"

#
# Postgres version of Scenario class
#
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
    PARENT_COLUMN_NAMES = ('parent_id', 'subsector_id', 'supply_node_id', 'primary_node_id', 'import_node_id',
                           'demand_tech_id', 'demand_technology_id', 'supply_tech_id', 'supply_technology_id')

    def __init__(self, scenario_id):
        self._id = scenario_id
        self._bucket_lookup = self._load_bucket_lookup()

        scenario_file = scenario_id if scenario_id.endswith('.json') else scenario_id + '.json'

        with open(scenario_file) as scenario_data:
            scenario = json.load(scenario_data)

        assert len(scenario) == 1, "More than one scenario found at top level in {}: {}".format(
            scenario_file, ", ".join(scenario_data.keys)
        )

        self.scenario = scenario

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

    @classmethod
    def parent_col(cls, data_table):
        """Returns the name of the column in the data table that references the parent table"""
        # These are one-off exceptions to our general preference order for parent columns
        if data_table == 'DemandSalesData':
            return 'demand_technology_id'
        if data_table == 'SupplyTechsEfficiencyData':
            return 'supply_tech_id'
        if data_table in ('SupplySalesData', 'SupplySalesShareData'):
            return 'supply_technology_id'

        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
        """, (data_table,))

        cols = [row[0] for row in cur]
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
        lookup = defaultdict(dict)
        for table in self.MEASURE_CATEGORIES:
            subindex_col = self._subindex_col(table)
            if subindex_col:
                cur.execute('SELECT id, {}, {} FROM "{}";'.format(self._index_col(table), subindex_col, table))
                for row in cur.fetchall():
                    lookup[table][row[0]] = (row[1], row[2])
            else:
                cur.execute('SELECT id, {} FROM "{}";'.format(self._index_col(table), table))
                for row in cur.fetchall():
                    lookup[table][row[0]] = (row[1], None)
        return lookup

    def _load_sensitivities(self, sensitivities):
        if not isinstance(sensitivities, list):
            raise ValueError("The 'Sensitivities' for a scenario should be a list of objects containing "
                             "the keys 'table', 'parent_id' and 'sensitivity'.")
        for sensitivity_spec in sensitivities:
            table = sensitivity_spec['table']
            parent_id = sensitivity_spec['parent_id']
            sensitivity = sensitivity_spec['sensitivity']
            if parent_id in self._sensitivities[table]:
                raise ValueError("Scenario specifies sensitivity for {} {} more than once".format(table, parent_id))

            # Check that the sensitivity actually exists in the database before using it
            cur.execute("""
                        SELECT COUNT(*) AS count
                        FROM "{}"
                        WHERE {} = %s AND sensitivity = %s
                    """.format(table, self.parent_col(table)), (parent_id, sensitivity))
            row_count = cur.fetchone()[0]

            if row_count == 0:
                raise ValueError("Could not find sensitivity '{}' for {} {}.".format(sensitivity, table, parent_id))

            self._sensitivities[table][parent_id] = sensitivity

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
                # pdb.set_trace()
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
