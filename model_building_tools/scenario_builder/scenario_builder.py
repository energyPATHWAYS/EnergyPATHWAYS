# -*- coding: utf-8 -*-

import os
import json
import xlwings as xw
import sys
import pandas as pd
import psycopg2
import numpy as np
from collections import OrderedDict, defaultdict

wb = xw.Book('scenario_builder.xlsm')
sht = wb.sheets.active
con = None
cur = None
directory = os.getcwd()

SENSITIVITIES = {"DemandDriversData":
                     {'side': 'd', 'parent_table': "DemandDrivers"},
                 "DemandTechsCapitalCostNewData":
                     {'side': 'd', 'parent_table': "DemandTechs"},
                 "DemandTechsCapitalCostReplacementData":
                     {'side': 'd', 'parent_table': "DemandTechs"},
                 "DemandTechsMainEfficiencyData":
                     {'side': 'd', 'parent_table': "DemandTechs"},
                 "DemandTechsAuxEfficiencyData":
                     {'side': 'd', 'parent_table': "DemandTechs"},
                 "DemandTechsFixedMaintenanceCostData":
                     {'side': 'd', 'parent_table': "DemandTechs"},
                 "DemandTechsFuelSwitchCostData":
                     {'side': 'd', 'parent_table': "DemandTechs"},
                 "DemandTechsInstallationCostNewData":
                     {'side': 'd', 'parent_table': "DemandTechs"},
                 "DemandTechsInstallationCostReplacementData":
                     {'side': 'd', 'parent_table': "DemandTechs"},
                 "DemandTechsParasiticEnergyData":
                     {'side': 'd', 'parent_table': "DemandTechs"},
                 "PrimaryCostData":
                     {'side': 's', 'parent_table': "SupplyNodes"},
                 "ImportCostData":
                     {'side': 's', 'parent_table': "SupplyNodes"}
                 }

PARENT_COLUMN_NAMES = ('parent_id', 'subsector_id', 'supply_node_id', 'primary_node_id', 'import_node_id',
                       'demand_tech_id', 'demand_technology_id', 'supply_tech_id', 'supply_technology_id')

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


def _get_parent_col(data_table):
    """Returns the name of the column in the data table that references the parent table"""
    cur.execute("""SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s""", (data_table,))

    cols = [row[0] for row in cur]
    if not cols:
        raise ValueError("Could not find any columns for table {}. Did you misspell the table "
                         "name?".format(data_table))
    # We do it this way so that we use a column earlier in the PARENT_COLUMN_NAMES list over one that's later
    parent_cols = [col for col in PARENT_COLUMN_NAMES if col in cols]
    if not parent_cols:
        raise ValueError("Could not find any known parent-referencing columns in {}. "
                         "Are you sure it's a table that references a parent table?".format(data_table))
    elif len(parent_cols) > 1:
        print "More than one potential parent-referencing column was found in {}; we are using the first in this list: {}".format(data_table, parent_cols)
    return parent_cols[0]

def query_all_measures():
    measures = []
    for table in MEASURE_CATEGORIES:
        if table.startswith("Demand"):
            id_name = 'subsector_id'
            parent_name = 'DemandSubsectors'
            side = 'd'
        else:
            id_name = 'blend_node_id' if table == 'BlendNodeBlendMeasures' else 'supply_node_id'
            parent_name = 'SupplyNodes'
            side = 's'
        cur.execute('SELECT "{}"."{}", "{}"."name", "{}"."id", "{}"."name" FROM "{}" INNER JOIN "{}" ON "{}".{} = "{}"."id";'.format(
                table, id_name, parent_name, table, table, table, parent_name, table, id_name, parent_name))
        for row in cur.fetchall():
            measures.append([side, row[0], row[1], table, row[2], row[3]])
    return pd.DataFrame(measures,
                        columns=['side', 'sub-node id', 'sub-node name', 'measure type', 'measure id', 'measure name'])

def _query_name_from_parent(id, data_table):
    parent_table = SENSITIVITIES[data_table]['parent_table']
    parent_table_primary_column = _get_parent_col(parent_table)
    cur.execute('SELECT name FROM "{}" WHERE {}={};'.format(parent_table, parent_table_primary_column, id))
    name = cur.fetchone()
    return name[0] if name else None

def query_all_sensitivities():
    sensitivities = []
    for table in SENSITIVITIES:
        side = SENSITIVITIES[table]['side']
        primary_column = _get_parent_col(table)
        cur.execute('SELECT {}, sensitivity FROM "{}";'.format(primary_column, table))
        unique_sensitivities = set([row for row in cur.fetchall()if row[1]])
        sensitivities += [[side, 'Sensitivities', row[1], table, row[0]] for row in unique_sensitivities]
        # sensitivities += [[side, _query_name_from_parent(row[0], table), table, row[0], row[1]] for row in
        #                   unique_sensitivities]
    return pd.DataFrame(sensitivities,
                        columns=['side', 'sub-node id', 'sub-node name', 'measure type', 'measure id'])


def _pull_measures(json_dict):
    result = []
    for key1, value1 in json_dict.iteritems():
        if type(value1) is dict:
            result += _pull_measures(value1)
        elif key1 in MEASURE_CATEGORIES:
            result += [[v, key1] for v in value1]
    return result


def _pull_measures_df(json_dict, scenario):
    result = _pull_measures(json_dict)
    scenario_measures = pd.DataFrame(result, columns=['measure id', 'measure type'])
    scenario_measures[scenario + '.json'] = 'x'
    return scenario_measures  # this is where we make each measure that is in a scenario show up with an x

def _pull_descriptions(json_dict, sub_node_list):
    result = []
    for key1, value1 in json_dict.iteritems():
        if key1 in sub_node_list:
            if 'description' in value1.keys():  # dollar sign is added to make it sort first
                result += [[sub_node_list[key1]['side'], sub_node_list[key1]['id'], '$description', key1,
                            value1['description']]]
        elif type(value1) is dict:
            result += _pull_descriptions(value1, sub_node_list)
    return result


def _pull_descriptions_df(json_dict, sub_node_list, scenario):
    result = _pull_descriptions(json_dict, sub_node_list)
    scenario_descriptions = pd.DataFrame(result, columns=['side', 'sub-node id', 'measure type', 'sub-node name',
                                                          scenario + '.json'])
    return scenario_descriptions

def _pull_sensitivities(json_dict):
    result = []
    for key1, value1 in json_dict.iteritems():
        if type(value1) is dict:
            result += _pull_sensitivities(value1)
        elif key1 == "Sensitivities":
            result += [(SENSITIVITIES[v['table']]['side'],
                        'Sensitivities',
                        v['table'],
                        v['parent_id'],
                        v['sensitivity'])
                       for v in value1]
    return result

def _pull_sensitivities_df(json_dict, scenario):
    result = _pull_sensitivities(json_dict)
    scenario_sensitivities = pd.DataFrame(result, columns=['side', 'sub-node id', 'measure type', 'measure id', 'sub-node name'])
    scenario_sensitivities[scenario + '.json'] = 'x'
    return scenario_sensitivities

def _inspect_scenario_and_case_names(json_dict, meta_data):
    meta_data['scenario_names'].append(json_dict.keys()[0])
    demand_case, supply_case, demand_description, supply_description, scenario_description = None, None, None, None, None
    for key, value in json_dict.values()[0].items():
        if key.lower().startswith('demand case: ') and type(value) is dict:
            demand_case = key[13:]
            if 'description' in value:
                demand_description = value['description']
        elif key.lower().startswith('supply case: ') and type(value) is dict:
            supply_case = key[13:]
            if 'description' in value:
                supply_description = value['description']
        elif key == 'description':
            scenario_description = value
    meta_data['demand_cases'].append(demand_case)
    meta_data['supply_cases'].append(supply_case)
    meta_data['demand_case_description'].append(demand_description)
    meta_data['supply_case_description'].append(supply_description)
    meta_data['scenario_description'].append(scenario_description)
    return meta_data


def _get_list_of_db_nodes_and_subsectors():
    cur.execute('SELECT name, id FROM "DemandSubsectors";')
    subsectors = [(r[0], {'id': r[1], 'side': 'd'}) for r in cur.fetchall()]
    cur.execute('SELECT name, id FROM "SupplyNodes";')
    nodes = [(r[0], {'id': r[1], 'side': 's'}) for r in cur.fetchall()]
    return dict(subsectors + nodes)


def _get_scenarios_df(scenarios, merge_by_override=None):
    folder = sht.range('scenario_folder').value
    base_path = os.path.join(directory, folder)
    measures_df, description_df, sensitivity_df, meta_data = None, None, None, defaultdict(list)
    sub_node_list = _get_list_of_db_nodes_and_subsectors()
    for scenario in scenarios:
        path = os.path.join(base_path, scenario + '.json')
        if not os.path.isfile(path):
            sht.range('python_msg').value = "error: cannot find path {}".format(path)
            sys.exit()
        json_dict = _load_json(path)
        scenario_measures = _pull_measures_df(json_dict, scenario)
        measures_df = scenario_measures if measures_df is None else pd.merge(measures_df, scenario_measures,
                                                                             how='outer')
        scenario_descriptions = _pull_descriptions_df(json_dict, sub_node_list, scenario)
        description_df = scenario_descriptions if description_df is None else pd.merge(description_df,
                                                                                       scenario_descriptions,
                                                                                       how='outer')
        scenario_sensitivities = _pull_sensitivities_df(json_dict, scenario)
        sensitivity_df = scenario_sensitivities if sensitivity_df is None else pd.merge(sensitivity_df,
                                                                                        scenario_sensitivities,
                                                                                        how='outer')
        meta_data = _inspect_scenario_and_case_names(json_dict, meta_data)

    all_measures = query_all_measures()
    all_sensitivities = query_all_sensitivities()
    merge_by = sht.range('merge_by').value if merge_by_override is None else merge_by_override
    values_m = pd.merge(all_measures, measures_df, how=merge_by)
    values_s = pd.merge(all_sensitivities, sensitivity_df, how=merge_by)
    values = pd.merge(values_m, values_s, how='outer')
    values = pd.merge(values, description_df, how='outer')
    values = values.set_index(['side', 'sub-node id', 'sub-node name', 'measure type', 'measure id', 'measure name'],
                              append=False).sort_index()

    return values, meta_data


def _helper_load_scenarios(scenarios):
    values, meta_data = _get_scenarios_df(scenarios)
    sht.range('values').clear_contents()
    sht.range('values').value = values
    for meta_name in meta_data:
        sht.range(meta_name).clear_contents()
        sht.range(meta_name).value = meta_data[meta_name]
    sht.range('python_msg').value = "sucessfully loaded {} scenarios from folder {}".format(
        len(scenarios), sht.range('scenario_folder').value)


def error_check_scenarios():
    _connect_to_db()
    scenarios = [s for s in sht.range('scenario_list').value if s]
    values, meta_data = _get_scenarios_df(scenarios, merge_by_override='outer')
    bad_index = np.nonzero([(v is None or v is np.NaN) for v in values.index.get_level_values('sub-node id')])[0]
    values = values.iloc[bad_index]
    sht.range('values').clear_contents()
    sht.range('values').value = values
    for meta_name in meta_data:
        sht.range(meta_name).clear_contents()
        sht.range(meta_name).value = meta_data[meta_name]
    if len(bad_index):
        sht.range('python_msg').value = "measures not in the database are displayed below"
    else:
        sht.range('python_msg').value = "all measures were found in the database!"


def load_scenario():
    _connect_to_db()
    scenarios = [wb.app.selection.value]
    _helper_load_scenarios(scenarios)


def load_scenarios():
    _connect_to_db()
    scenarios = [s for s in sht.range('scenario_list').value if s]
    _helper_load_scenarios(scenarios)


def _make_connections():
    global wb, sht, directory
    wb = xw.Book.caller()
    sht = wb.sheets.active
    directory = os.path.dirname(wb.fullname)


def _connect_to_db():
    _make_connections()
    global con, cur
    sht.range('python_msg').clear_contents()
    pg_host = sht.range('pg_host').value
    if not pg_host:
        pg_host = 'localhost'
    pg_user = sht.range('pg_user').value
    pg_password = sht.range('pg_password').value
    pg_database = sht.range('pg_database').value
    conn_str = "host='%s' dbname='%s' user='%s'" % (pg_host, pg_database, pg_user)
    if pg_password:
        conn_str += " password='%s'" % pg_password
    # Open pathways database
    con = psycopg2.connect(conn_str)
    cur = con.cursor()
    sht.range('python_msg').value = "connection to db successful"


def _get_scenario_list():
    folder = sht.range('scenario_folder').value
    path = os.path.join(directory, folder)
    if not os.path.exists(path):
        sht.range('python_msg').value = "error: cannot find path {}".format(path)
        sys.exit()
    # os.path.getmtime(path)
    # http://stackoverflow.com/questions/237079/how-to-get-file-creation-modification-date-times-in-python
    scenarios = sorted([f[:-5] for f in os.listdir(path) if f[-5:] == '.json'])
    return scenarios


def refresh_scenario_list():
    _make_connections()
    sht.range('python_msg').clear_contents()
    scenarios = _get_scenario_list()
    sht.range('scenario_list').clear_contents()
    sht.range('scenario_list').value = [[s] for s in scenarios]  # stack
    sht.range('python_msg').value = "scenario list sucessfully refreshed"


def delete_scenario():
    _make_connections()
    scenario_to_delete = wb.app.selection.value
    folder = sht.range('scenario_folder').value
    path = os.path.join(directory, folder, scenario_to_delete + '.json')
    if not os.path.isfile(path):
        sht.range('python_msg').value = "error: cannot find path {}".format(path)
        sys.exit()
    else:
        os.remove(path)
    sht.range('python_msg').value = "file {} has been deleted".format(scenario_to_delete)
    scenarios = _get_scenario_list()
    sht.range('scenario_list').clear_contents()
    sht.range('scenario_list').value = [[s] for s in scenarios]  # stack


def pop_open_json_file():
    _make_connections()
    folder = sht.range('scenario_folder').value
    file_name = wb.app.selection.value
    path = os.path.join(directory, folder, file_name + '.json')
    try:
        os.startfile(path)
        sht.range('python_msg').value = "JSON opened for file {}".format(file_name)
    except:
        sht.range('python_msg').value = "error: unable to open JSON from path {}".format(path)


def _load_json(path):
    with open(path, 'rb') as infile:
        loaded = json.load(infile)
    return loaded


def save_scenarios():
    _connect_to_db()

    index_count = 6  # first 6 rows are an index
    values = sht.range('values').value
    num_good_columns = sum([v is not None for v in values[0]])
    values = [row[:num_good_columns] for row in values if row[0] is not None]

    num_good_scenarios = num_good_columns - index_count
    meta_data = {}
    meta_data['d'] = dict(zip(range(num_good_scenarios),
                              ['Demand Case: ' + n for n in sht.range('demand_cases').value[:num_good_scenarios]]))
    meta_data['demand_case_description'] = dict(
        zip(range(num_good_scenarios), sht.range('demand_case_description').value[:num_good_scenarios]))
    meta_data['s'] = dict(zip(range(num_good_scenarios),
                              ['Supply Case: ' + n for n in sht.range('supply_cases').value[:num_good_scenarios]]))
    meta_data['supply_case_description'] = dict(
        zip(range(num_good_scenarios), sht.range('supply_case_description').value[:num_good_scenarios]))
    meta_data['scenario_names'] = dict(
        zip(range(num_good_scenarios), sht.range('scenario_names').value[:num_good_scenarios]))
    meta_data['scenario_description'] = dict(
        zip(range(num_good_scenarios), sht.range('scenario_description').value[:num_good_scenarios]))

    # set up JSON structure
    json_files = OrderedDict()
    for s in range(num_good_scenarios):
        json_files[meta_data['scenario_names'][s]] = OrderedDict()
        if meta_data['scenario_description'][s]:
            json_files[meta_data['scenario_names'][s]]["description"] = meta_data['scenario_description'][s]
        json_files[meta_data['scenario_names'][s]][meta_data['d'][s]] = OrderedDict()
        if meta_data['demand_case_description'][s]:
            json_files[meta_data['scenario_names'][s]][meta_data['d'][s]]["description"] = \
                meta_data['demand_case_description'][s]
        json_files[meta_data['scenario_names'][s]][meta_data['s'][s]] = OrderedDict()
        if meta_data['supply_case_description'][s]:
            json_files[meta_data['scenario_names'][s]][meta_data['s'][s]]["description"] = \
                meta_data['supply_case_description'][s]

    for row in values[1:]:
        side, node_id, node_name, measure_type, measure_id, measure_name = row[:index_count]
        x_marks_spot = row[index_count:]
        for s, x in zip(range(num_good_scenarios), x_marks_spot):
            if node_id == 'Sensitivities':
                if x == 'x':
                    if not json_files[meta_data['scenario_names'][s]][meta_data[side][s]].has_key('Sensitivities'):
                        json_files[meta_data['scenario_names'][s]][meta_data[side][s]]['Sensitivities'] = []
                    sensitivity = OrderedDict([('table', measure_type), ('parent_id', measure_id), ('sensitivity', node_name)])
                    json_files[meta_data['scenario_names'][s]][meta_data[side][s]]['Sensitivities'].append(sensitivity)
            elif measure_type == '$description':  # the dollar sign was added when loading to make it sort first in excel
                if x:  # if the description is empty, we just want to skip it
                    if not json_files[meta_data['scenario_names'][s]][meta_data[side][s]].has_key(node_name):
                        json_files[meta_data['scenario_names'][s]][meta_data[side][s]][node_name] = OrderedDict()
                    json_files[meta_data['scenario_names'][s]][meta_data[side][s]][node_name]["description"] = x
            elif x == 'x':  # x means we include the measure in the JSON
                if not json_files[meta_data['scenario_names'][s]][meta_data[side][s]].has_key(node_name):
                    json_files[meta_data['scenario_names'][s]][meta_data[side][s]][node_name] = OrderedDict()
                if not json_files[meta_data['scenario_names'][s]][meta_data[side][s]][node_name].has_key(measure_type):
                    json_files[meta_data['scenario_names'][s]][meta_data[side][s]][node_name][measure_type] = []
                # they will already be in order as we add them
                json_files[meta_data['scenario_names'][s]][meta_data[side][s]][node_name][measure_type].append(int(measure_id))

    write_folder = sht.range('scenario_folder').value
    base_path = os.path.join(directory, write_folder)
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    for header, name, content in zip(values[0][index_count:], json_files.keys(), json_files.values()):
        file_name = header if header[-5:].lower() == '.json' else header + '.json'
        path = os.path.join(base_path, file_name)
        with open(path, 'wb') as outfile:
            json.dump({name: content}, outfile, indent=4, separators=(',', ': '))

    sht.range('python_msg').value = "successfully saved all scenarios!"
