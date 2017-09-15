# -*- coding: utf-8 -*-

# WARNING: If you try to import something that isn't in your python path,
# xlwings will fail silently when called from Excel (at least on Excel 2016 for Mac)!
import os
import subprocess
import traceback
import json
import string
from datetime import datetime
import platform
import xlwings as xw
import sys
import pandas as pd
import psycopg2
import psycopg2.extras
import numpy as np
from collections import OrderedDict, defaultdict
import csv
import time

class PathwaysLookupError(KeyError):
    def __init__(self, val, table, col):
        message = "Save failed: '{}' is not a valid value for {}.{}".format(val, table, col)

        # Call the base class constructor with the parameters it needs
        super(PathwaysLookupError, self).__init__(message)

class SequenceError(Exception):
    pass

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    elif exc_type == PathwaysLookupError:
        _msg(str(exc_value).strip('"'))
        return

    exception_lines = [[line] for line in traceback.format_exception(exc_type, exc_value, exc_traceback)]
    exception_lines.insert(0, ["Python encountered an exception at {}".format(datetime.now().strftime('%c'))])
    wb.sheets['exception'].cells.value = exception_lines
    wb.sheets['exception'].activate()

    _msg("Python encountered an exception; see 'exception' worksheet.")

sys.excepthook = handle_exception

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
                     {'side': 's', 'parent_table': "SupplyNodes"},
                 "DemandEnergyDemandsData":
                     {'side': 'd', 'parent_table': "DemandSubsectors"},
                 "SupplyPotentialData":
                     {'side': 's', 'parent_table': "SupplyNodes"},
                 "SupplyEmissionsData":
                     {'side': 's', 'parent_table': "SupplyNodes"},
                 "StorageTechsCapacityCapitalCostNewData":
                     {'side': 's', 'parent_table': "SupplyTechs"}
                 }

PARENT_COLUMN_NAMES = ('parent_id', 'subsector_id', 'supply_node_id', 'primary_node_id', 'import_node_id',
                       'demand_tech_id', 'demand_technology_id', 'supply_tech_id', 'supply_technology_id')

MEASURE_CATEGORIES = ("CO2PriceMeasures",
                      "DemandEnergyEfficiencyMeasures",
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

SENSITIVTY_LABEL = 'sensitivity'

def _msg(message):
    wb.sheets['scenarios'].range('python_msg').value = message

def _clear_msg():
    wb.sheets['scenarios'].range('python_msg').clear_contents()
    wb.sheets['exception'].clear_contents()

def _get_columns(table):
    cur.execute("""SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s""", (table,))
    cols = [row[0] for row in cur]
    assert cols, "Could not find any columns for table {}. Did you misspell the table name?".format(table)
    return cols

def _get_parent_col(data_table):
    """Returns the name of the column in the data table that references the parent table"""
    # These are one-off exceptions to our general preference order for parent columns
    if data_table == 'DemandSalesData':
        return 'demand_technology_id'
    if data_table == 'SupplyTechsEfficiencyData':
        return 'supply_tech_id'
    if data_table in ('SupplySalesData', 'SupplySalesShareData'):
        return 'supply_technology_id'

    cols = _get_columns(data_table)

    # We do it this way so that we use a column earlier in the PARENT_COLUMN_NAMES list over one that's later
    parent_cols = [col for col in PARENT_COLUMN_NAMES if col in cols]
    if not parent_cols:
        raise ValueError("Could not find any known parent-referencing columns in {}. "
                         "Are you sure it's a table that references a parent table?".format(data_table))
    return parent_cols[0]

def _get_id_col_of_parent(parent_table):
    """Some tables identify their members by something more elaborate than 'id', e.g. 'demand_tech_id'"""
    return 'id' if 'id' in _get_columns(parent_table) else _get_parent_col(parent_table)

def _get_config(key):
    try:
        return _get_config.config.get(key, None)
    except AttributeError:
        _get_config.config = dict()
        for line in open(os.path.join(directory, 'scenario_builder_config.txt'), 'r'):
            k, v = (part.strip() for part in line.split(':', 2))
            # This "if v" is here because if v is the empty string we don't want to store a value for this config
            # option; it should be gotten as "None"
            if v:
                _get_config.config[k] = v
        return _get_config.config.get(key, None)

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
        parent_table = SENSITIVITIES[table]['parent_table']
        parent_pri_col = _get_id_col_of_parent(parent_table)
        cur.execute("""
            SELECT DISTINCT "{table}".{pri_col}, "{parent}".name, sensitivity
            FROM "{table}"
            JOIN "{parent}" ON "{table}".{pri_col} = "{parent}".{parent_pri_col}
            WHERE sensitivity IS NOT NULL;
        """.format(table=table, pri_col=primary_column, parent=parent_table, parent_pri_col=parent_pri_col))
        unique_sensitivities = cur.fetchall()
        sensitivities += [[side, row[0], row[1], table, SENSITIVTY_LABEL, row[2]] for row in unique_sensitivities]
    return pd.DataFrame(sensitivities,
                        columns=['side', 'sub-node id', 'sub-node name', 'measure type', 'measure id', 'measure name'])


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
                        v['parent_id'],
                        v['table'],
                        'sensitivity',
                        v['sensitivity'])
                       for v in value1]
    return result

def _pull_sensitivities_df(json_dict, scenario):
    result = _pull_sensitivities(json_dict)
    scenario_sensitivities = pd.DataFrame(result, columns=['side', 'sub-node id', 'measure type', 'measure id', 'measure name'])
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
            _msg("error: cannot find path {}".format(path))
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
    values_s = values_s.set_index(['side', 'sub-node id', 'sub-node name', 'measure type', 'measure id', 'measure name'],
                                  append=False).sort_index(level=['measure type', 'sub-node id', 'measure name'])
    values = pd.merge(values_m, description_df, how='outer')
    values = values.set_index(['side', 'sub-node id', 'sub-node name', 'measure type', 'measure id', 'measure name'],
                              append=False).sort_index()
    values = values.append(values_s)

    return values, meta_data


def _helper_load_scenarios(scenarios):
    values, meta_data = _get_scenarios_df(scenarios)
    sht.range('values').clear_contents()
    sht.range('values').value = values
    for meta_name in meta_data:
        sht.range(meta_name).clear_contents()
        sht.range(meta_name).value = meta_data[meta_name]
    _msg("sucessfully loaded {} scenarios from folder {}".format(len(scenarios), sht.range('scenario_folder').value))

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
        _msg("measures not in the database are displayed below")
    else:
        _msg("all measures were found in the database!")

def load_scenario():
    _connect_to_db()
    scenarios = [wb.app.selection.value]
    _helper_load_scenarios(scenarios)

def load_scenarios():
    _connect_to_db()
    scenarios = [s for s in sht.range('scenario_list').value if s]
    _helper_load_scenarios(scenarios)

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

# Adapted from https://github.com/skywind3000/terminal/blob/master/terminal.py
def darwin_osascript(script):
    for line in script:
        # print line
        pass
    if type(script) == type([]):
        script = '\n'.join(script)
    p = subprocess.Popen(['/usr/bin/osascript'], shell=False,
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    p.stdin.write(script)
    p.stdin.flush()
    p.stdin.close()
    text = p.stdout.read()
    p.stdout.close()
    code = p.wait()
    # print text
    return code, text

# Adapted from https://github.com/skywind3000/terminal/blob/master/terminal.py
def run_on_darwin(command, working_dir):
    command = ' '.join(command)
    command = 'cd "{}"; '.format(working_dir) + command
    command = command.replace('\\', '\\\\')
    command = command.replace('"', '\\"')
    command = command.replace("'", "\\'")
    osascript = [
        'tell application "Terminal"',
        '  do script "%s"' % command,
        '  activate',
        'end tell'
    ]
    return darwin_osascript(osascript)

def run_on_windows(command, working_dir):
    os.chdir(working_dir)
    command = ["start", "cmd", "/k"] + command
    subprocess.call(command, shell=True);

def start_energypathways():
    _connect_to_db()
    folder = sht.range('scenario_folder_controls').value
    working_dir = os.path.join(directory, folder)
    base_args = ['EnergyPATHWAYS']
    if _get_config('conda_env'):
        base_args = ['source', 'activate', _get_config('conda_env') + ';'] + base_args
    if sht.range('configINI_name').value != 'config.INI':
        base_args += ['-c', sht.range('configINI_name').value]
    if sht.range('ep_load_demand').value is True:
        base_args.append('-ld')
    if sht.range('ep_load_supply').value is True:
        base_args.append('-ls')
    if sht.range('ep_solve_demand').value is False:
        base_args.append('--no_solve_demand')
    if sht.range('ep_solve_supply').value is False:
        base_args.append('--no_solve_supply')
    if sht.range('ep_export_results').value is False:
        base_args.append('--no_export_results')
    if sht.range('ep_clear_results').value is True:
        base_args.append('--clear_results')
    if sht.range('ep_save_models').value is False:
        base_args.append('--no_save_models')

    scenarios = [s for s in sht.range('scenario_list_controls').value if s]
    ep_cmd_window_count = int(sht.range('ep_cmd_window_count').value)
    run = run_on_darwin if platform.system() == 'Darwin' else run_on_windows
    for scenario_chunk in np.array_split(scenarios, ep_cmd_window_count):
        args = base_args + [val for pair in zip(['-s']*len(scenario_chunk), scenario_chunk) for val in pair]
        run(args, working_dir)
        time.sleep(.5)
    _msg("sucessfully launched {} scenarios".format(len(scenarios)))

def load_config():
    _make_connections()
    _clear_msg()
    sht.range('configINI').clear_contents()
    folder = sht.range('scenario_folder_controls').value
    config_name = sht.range('configINI_name').value
    path = os.path.join(directory, folder, config_name)
    if not os.path.isfile(path):
        _msg("error: cannot find file {}".format(path))
        sys.exit()
    config = []
    with open(path, 'rb') as infile:
        for row in infile:
            split_row = row.rstrip().replace('=', ':').split(':')
            split_row = [split_row[0].rstrip(), split_row[1].lstrip()] if len(split_row)==2 else split_row+['']
            config.append(split_row)
    sht.range('configINI').value = config
    _msg("sucessfully loaded config file")

def is_strnumeric(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def save_config():
    _make_connections()
    folder = sht.range('scenario_folder_controls').value
    config_name = sht.range('configINI_name').value
    path = os.path.join(directory, folder, config_name)
    if not os.path.exists(os.path.join(directory, folder)):
        os.makedirs(os.path.join(directory, folder))
    config = [row for row in sht.range('configINI').value if (row is not None and row[0] is not None and row[0]!='')]
    with open(path, 'wb') as outfile:
        csvwriter = csv.writer(outfile, delimiter=':')
        for i, row in enumerate(config):
            if row[1] is None:
                if row[0][0]=='#' or row[0][0]=='[':
                    csvwriter.writerow([row[0]])
                else:
                    csvwriter.writerow((row[0],''))
            else:
                key, value = row
                value = ('True' if value else 'False') if type(value) is bool else value
                value = str(int(value)) if is_strnumeric(str(value)) and (int(value) - value == 0) else str(value)
                csvwriter.writerow([key, ' ' + value])
            next_row = config[i + 1] if i + 1 < len(config) else None
            if next_row is not None and next_row[0][0]=='[' and next_row[0][-1]==']':
                csvwriter.writerow([])
    _msg("sucessfully saved config file")

def _make_connections():
    global wb, sht, directory
    wb = xw.Book.caller()
    sht = wb.sheets.active
    directory = os.path.dirname(wb.fullname)

def _connect_to_db():
    _make_connections()
    global con, cur
    _clear_msg()
    pg_host = _get_config('pg_host')
    if not pg_host:
        pg_host = 'localhost'
    pg_user = _get_config('pg_user')
    pg_password = _get_config('pg_password')
    pg_database = _get_config('pg_database')
    conn_str = "host='%s' dbname='%s' user='%s'" % (pg_host, pg_database, pg_user)
    if pg_password:
        conn_str += " password='%s'" % pg_password
    # Open pathways database
    con = psycopg2.connect(conn_str)
    cur = con.cursor()
    _msg("connection to db successful")


def _get_scenario_list(scenario_folder_range):
    folder = sht.range(scenario_folder_range).value
    path = os.path.join(directory, folder)
    if not os.path.exists(path):
        _msg("error: cannot find path {}".format(path))
        sys.exit()
    # os.path.getmtime(path)
    # http://stackoverflow.com/questions/237079/how-to-get-file-creation-modification-date-times-in-python
    scenarios = sorted([f[:-5] for f in os.listdir(path) if f[-5:] == '.json'])
    return scenarios


def refresh_scenario_list():
    _make_connections()
    _clear_msg()
    scenarios = _get_scenario_list('scenario_folder')
    sht.range('scenario_list').clear_contents()
    sht.range('scenario_list').value = [[s] for s in scenarios]  # stack
    _msg("scenario list successfully refreshed")

def refresh_scenario_list_controls():
    _make_connections()
    _clear_msg()
    scenarios = _get_scenario_list('scenario_folder_controls')
    sht.range('scenario_list_controls').clear_contents()
    sht.range('scenario_list_controls').value = [[s] for s in scenarios]  # stack
    _msg("scenario list successfully refreshed")

def delete_scenario():
    _make_connections()
    scenario_to_delete = wb.app.selection.value
    folder = sht.range('scenario_folder').value
    path = os.path.join(directory, folder, scenario_to_delete + '.json')
    if not os.path.isfile(path):
        _msg("error: cannot find path {}".format(path))
        sys.exit()
    else:
        os.remove(path)
    _msg("file {} has been deleted".format(scenario_to_delete))
    scenarios = _get_scenario_list()
    sht.range('scenario_list').clear_contents()
    sht.range('scenario_list').value = [[s] for s in scenarios]  # stack


def pop_open_json_file():
    _make_connections()
    folder = sht.range('scenario_folder').value
    file_name = wb.app.selection.value
    path = os.path.join(directory, folder, file_name + '.json')
    try:
        # http://stackoverflow.com/questions/17317219/is-there-an-platform-independent-equivalent-of-os-startfile
        if sys.platform == "win32":
            os.startfile(path)
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, path])
        _msg("JSON opened for file {}".format(file_name))
    except:
        _msg("error: unable to open JSON from path {}".format(path))


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
            if measure_id == SENSITIVTY_LABEL:
                if x == 'x':
                    if not json_files[meta_data['scenario_names'][s]][meta_data[side][s]].has_key('Sensitivities'):
                        json_files[meta_data['scenario_names'][s]][meta_data[side][s]]['Sensitivities'] = []
                    sensitivity = OrderedDict([('table', measure_type), ('parent_id', int(node_id)), ('sensitivity', measure_name)])
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

    _msg("successfully saved all scenarios!")

##############
# Table CRUD #
##############

MEASURE_SHEET_DESCRIPTION_STR = 'C1:C2'
MEASURE_PARENT_NAME_RANGE_STR = 'C5'
MEASURE_PARENT_DATA_RANGE_STR = 'B7:C32'
MEASURE_SUBTABLE_NAME_RANGE_STR = 'F5'
MEASURE_SUBTABLE_DATA_RANGE_STR = 'E7:F32'
MEASURE_DATA_TABLE_NAME_RANGE_STR = 'I5'
# Note that measure data is limited to 1,000 rows; more than that may display, but beyond that will not save!
MEASURE_DATA_RANGE_STR = 'H6:P1012'
PYTHON_MSG_LABEL_STR = 'B3'
PYTHON_MSG_STR = 'C3'
MEASURE_DESCRIPTION_LABEL_STR = 'B1:B2'
PARENT_TABLE_LABEL_STR = 'B5'
SUBTABLE_LABEL_STR = 'E5'
DATA_TABLE_LABEL_STR = 'H5'
PARENT_TABLE_HEADERS_STR = 'B6:F6'
OPTIONS_LABEL_STR = 'R5'
OPTIONS_COLUMN_HEADER_STR = 'S5'
OPTIONS_COLUMN_STR = 'S6:S1006'
FIRST_MEASURE_SHEET = 2
MEASURE_SHEET_COUNT = 3

SUBNODE_COL = 7
MEASURE_TABLE_COL = 9
MEASURE_ID_COL = 10
MEASURE_NAME_COL = 11
# This tells us any special associated subtables.
# "None" means include the usual parent-table-with-"Data"-on-the-end table.
MEASURE_SUBTABLES = {
    'DemandFuelSwitchingMeasures': (
        'DemandFuelSwitchingMeasuresCost',
        'DemandFuelSwitchingMeasuresEnergyIntensity',
        'DemandFuelSwitchingMeasuresImpact'
    ),
    'DemandServiceDemandMeasures': (None, 'DemandServiceDemandMeasuresCost'),
    'DemandEnergyEfficiencyMeasures': (None, 'DemandEnergyEfficiencyMeasuresCost')
}

# This tells us what id:name lookup table to use for a given column name
LOOKUP_MAP = {
    'gau_id': 'GeographiesData',
    'oth_1_id': 'OtherIndexesData',
    'oth_2_id': 'OtherIndexesData',
    'final_energy': 'FinalEnergy',
    'final_energy_id': 'FinalEnergy',
    'final_energy_from_id': 'FinalEnergy',
    'final_energy_to_id': 'FinalEnergy',
    'demand_tech_id': 'DemandTechs',
    'demand_technology_id': 'DemandTechs',
    'supply_tech_id': 'SupplyTechs',
    'supply_technology_id': 'SupplyTechs',
    'efficiency_type_id': 'EfficiencyTypes',
    'supply_node_id': 'SupplyNodes',
    'blend_node_id': 'SupplyNodes',
    'import_node_id': 'SupplyNodes',
    'demand_sector_id': 'DemandSectors',
    'ghg_type_id': 'GreenhouseGasEmissionsType',
    'ghg_id': 'GreenhouseGases',
    'dispatch_feeder_id': 'DispatchFeeders',
    'dispatch_constraint_id': 'DispatchConstraintTypes',
    'day_type_id': 'DayType',
    'timeshift_type_id': 'FlexibleLoadShiftTypes',
    'subsector_id': 'DemandSubsectors',
    'geography_id': 'Geographies',
    'other_index_1_id': 'OtherIndexes',
    'other_index_2_id': 'OtherIndexes',
    'replaced_demand_tech_id': 'DemandTechs',
    'input_type_id': 'InputTypes',
    'interpolation_method_id': 'CleaningMethods',
    'extrapolation_method_id': 'CleaningMethods',
    'stock_decay_function_id': 'StockDecayFunctions',
    'currency_id': 'Currencies',
    'demand_tech_efficiency_types': 'DemandTechEfficiencyTypes',
    'definition_id': 'Definitions',
    'demand_tech_unit_type_id': 'DemandTechUnitTypes',
    'shape_id': 'Shapes',
    'linked_id': 'DemandTechs',
    'supply_type_id': 'SupplyTypes',
    'tradable_geography_id': 'Geographies'
}

# These hold lookup tables that are static for our purposes, so can be shared at the module level
# (no sense in going back to the database for these lookup tables for each individual chunk)
name_lookups = {}
id_lookups = {}

def _lookup_for(table, key_col='id', filter_col=None, filter_value=None):
    """
    Provides dictionaries of id: name or key_col: id from a table, depending on which column is specified as the
    key_col. Optionally filters the table by another column first, which is needed when we're only interested
    in, e.g. the geographical units within a particular geography.
    """
    if key_col == 'id':
        fields = 'id, name'
    else:
        fields = '{}, id'.format(key_col)
    query = 'SELECT {} FROM "{}"'.format(fields, table)
    if filter_col:
        query += ' WHERE {} = %s'.format(filter_col)
        cur.execute(query, (filter_value,))
    else:
        cur.execute(query)
    rows = cur.fetchall()
    keys = [row[0] for row in rows]
    if len(keys) != len(set(keys)):
        filter_str = ", filtering on {} = {}".format(filter_col, filter_value) if filter_col else ''
        raise ValueError("Duplicate keys creating lookup for {} using key column {}{}.".format(
            table, key_col, filter_str
        ))
    return {row[0]: row[1] for row in rows}

def _name_for(table, id):
    """Look up the name for a common item like a geographical unit or an other index value"""
    try:
        return name_lookups[table][id]
    except KeyError:
        name_lookups[table] = _lookup_for(table)
        return name_lookups[table][id]

def _id_for(table, name):
    """
    Look up the id of an item by its name.

    Note that this does NOT do any filtering of the source table, so if you need to make sure the lookup is only
    done on a subset of the table (e.g., because different subsets may re-use the same name), you'll need to
    use lookup_for() directly
    """
    try:
        return id_lookups[table][name]
    except KeyError:
        id_lookups[table] = _lookup_for(table, 'name')
        return id_lookups[table][name]

def _data_header(cols, parent_dict):
    """Constructs a header row for the worksheet based on the columns in the table and contents of the parent row"""
    out = []
    for col in cols:
        if col == 'gau_id':
            out.append(parent_dict['geography_id'])
        elif col == 'oth_1_id':
            out.append(parent_dict['other_index_1_id'])
        elif col == 'oth_2_id':
            out.append(parent_dict['other_index_2_id'])
        else:
            out.append(col)
    return out

def _load_parent_row(table, parent_id):
    parent_id_col = _get_id_col_of_parent(table)
    parent_query = 'SELECT * FROM "{}" WHERE {} = %s'.format(table, parent_id_col)
    cur.execute(parent_query, (parent_id,))
    parent_col_names = [desc[0] for desc in cur.description]
    row = cur.fetchone()
    values = []
    if row:
        for i, val in enumerate(row):
            if val and parent_col_names[i] in LOOKUP_MAP:
                values.append(_name_for(LOOKUP_MAP[parent_col_names[i]], val))
            elif val in (True, False):
                values.append(str(val))
            else:
                values.append(val)
        return zip(parent_col_names, values)

def _clear_measure_sheet_contents():
    for measure_sheet_index in range(FIRST_MEASURE_SHEET, FIRST_MEASURE_SHEET + MEASURE_SHEET_COUNT):
        sheet = wb.sheets[measure_sheet_index]
        sheet.clear_contents()
        sheet.range(PYTHON_MSG_LABEL_STR).value = 'PYTHON MSG'
        sheet.range(PYTHON_MSG_STR).formula = '=python_msg'
        sheet.range(MEASURE_DESCRIPTION_LABEL_STR).value = [['Measure Description:'], ['Data Table Description:']]
        sheet.range(PARENT_TABLE_LABEL_STR).value = 'Parent Table:'
        sheet.range(SUBTABLE_LABEL_STR).value = 'Sub Table:'
        sheet.range(DATA_TABLE_LABEL_STR).value = 'Data Table:'
        sheet.range(PARENT_TABLE_HEADERS_STR).value = ['Column Name', 'Value', None, 'Column Name', 'Value']
        sheet.range(OPTIONS_LABEL_STR).value = 'Options:'

    wb.sheets[FIRST_MEASURE_SHEET + 1].name = '(no data)'
    # Sheet names can't be identical, thus the trailing space
    wb.sheets[FIRST_MEASURE_SHEET + 2].name = '(no data) '

def _load_measure_sheet(measure_sheet, table, parent_id, parent_data, subtable=None, data_table=None):
    # Assumption: all of the measure data sheets have had their contents cleared before entering this function
    sheet_description_range = measure_sheet.range(MEASURE_SHEET_DESCRIPTION_STR)
    parent_name_range = measure_sheet.range(MEASURE_PARENT_NAME_RANGE_STR)
    parent_data_range = measure_sheet.range(MEASURE_PARENT_DATA_RANGE_STR)
    subtable_name_range = measure_sheet.range(MEASURE_SUBTABLE_NAME_RANGE_STR)
    subtable_data_range = measure_sheet.range(MEASURE_SUBTABLE_DATA_RANGE_STR)
    data_table_name_range = measure_sheet.range(MEASURE_DATA_TABLE_NAME_RANGE_STR)
    data_range = measure_sheet.range(MEASURE_DATA_RANGE_STR)

    # Extract some useful info from the parent_data
    parent_dict = dict(parent_data)

    # Show user the name of the data table, within the sheet and in the worksheet name itself
    if data_table is None:
        data_table = subtable + 'Data' if subtable else table + 'Data'
    # Populate metadata about table and data for parent object
    title = "{} for {} #{}".format(data_table, table, parent_id)
    if 'name' in parent_dict:
        title += ', "{}"'.format(parent_dict['name'])
    cur.execute("""
        SELECT obj_description(pg_class.oid)
        FROM pg_class
        JOIN pg_namespace ON pg_namespace.oid = pg_class.relnamespace
        WHERE relkind = 'r'
          AND nspname = 'public'
          AND relname = %s;
    """, (data_table,))
    table_desc = cur.fetchone()[0]
    sheet_description_range.value = [[title], [table_desc]]
    parent_name_range.value = table
    parent_data_range.value = parent_data
    # Excel worksheet names are limited to 31 characters; this takes the rightmost 31 characters,
    # then strips any dangling word endings off the beginning
    measure_sheet.name = data_table[-31:].lstrip(string.ascii_lowercase)
    # This might seem a little redundant, but we need it for saving later on
    data_table_name_range.value = data_table

    # Load subtable "parent" information
    if subtable:
        subtable_name_range.value = subtable
        subtable_data = _load_parent_row(subtable, parent_id)
        if subtable_data:
            subtable_data_range.value = subtable_data
            # If there's a subtable we overwrite the previous parent_dict with the subtable's values because the
            # subtable is what will have, e.g. the geography_id for the data table
            parent_dict = dict(subtable_data)
        else:
            # If there was no data in the subtable, there won't be (or shouldn't be!) any data in the data table,
            # so we can abort.
            subtable_data_range.value = ['(no data found in this table for this measure or sensitivity)']
            return
    else:
        subtable_name_range.value = '(N/A)'

    # Populate time series data
    parent_col = _get_parent_col(data_table)
    data_query = 'SELECT * FROM "{}" WHERE {} = %s'.format(data_table, parent_col)
    cur.execute(data_query, (parent_id,))
    data_col_names = [desc[0] for desc in cur.description]
    rows = cur.fetchall()

    if len(rows):
        # Any column that's empty in the first row is one that this chunk doesn't use, so we'll skip it.
        # (Columns must be always used or never used within a given chunk -- "sensitivity" is the one exception.)
        skip_indexes = set(i for i, val in enumerate(rows[0]) if val is None and data_col_names[i] != 'sensitivity')
        skip_indexes.add(data_col_names.index('id'))
        skip_indexes.add(data_col_names.index(parent_col))

        header_cols = [col for i, col in enumerate(data_col_names) if i not in skip_indexes]
        data = []

        for row in rows:
            xl_row = []
            for i, val in enumerate(row):
                if i in skip_indexes:
                    continue
                if data_col_names[i] in LOOKUP_MAP:
                    xl_row.append(_name_for(LOOKUP_MAP[data_col_names[i]], val))
                else:
                    xl_row.append(val)
            data.append(xl_row)

        data.sort()
        data.insert(0, _data_header(header_cols, parent_dict))
        data_range.value = data
    else:
        # TODO: instead of doing nothing, try to populate column headers for the data table so the user can enter data
        pass

def load_measure():
    _connect_to_db()
    _clear_measure_sheet_contents()

    # Handle the row differently depending on whether it's a sensitivity or not
    if sht.range((wb.app.selection.row, MEASURE_ID_COL)).value == SENSITIVTY_LABEL:
        data_table = sht.range((wb.app.selection.row, MEASURE_TABLE_COL)).value
        table = SENSITIVITIES[data_table]['parent_table']
        for suffix in ('NewData', 'ReplacementData', 'Data'):
            if data_table.endswith(suffix):
                subtable = data_table[:-len(suffix)]
                break
        parent_id = int(sht.range((wb.app.selection.row, SUBNODE_COL)).value)
        parent_data = _load_parent_row(table, parent_id)
        _load_measure_sheet(wb.sheets[FIRST_MEASURE_SHEET], table, parent_id, parent_data, subtable, data_table)
        _msg("Sensitivity loaded")
    else:
        table = sht.range((wb.app.selection.row, MEASURE_TABLE_COL)).value
        parent_id = int(sht.range((wb.app.selection.row, MEASURE_ID_COL)).value)
        parent_data = _load_parent_row(table, parent_id)

        measure_sheet_offset = 0
        subtables = MEASURE_SUBTABLES.get(table, [None])
        for subtable in subtables:
            _load_measure_sheet(wb.sheets[FIRST_MEASURE_SHEET + measure_sheet_offset], table, parent_id, parent_data, subtable)
            measure_sheet_offset += 1
        _msg("{} measure data sheet(s) loaded".format(measure_sheet_offset))

    wb.sheets[FIRST_MEASURE_SHEET].activate()

def _fix_sequence(table):
    print table
    con.rollback()
    seq_fix_query = """
      SELECT setval(pg_get_serial_sequence('"{table}"', 'id'), MAX(id))
      FROM "{table}";
    """.format(table=table)
    cur.execute(seq_fix_query)

def _duplicate_rows(table, old_parent_id, new_parent_id=None):
    pri_col = _get_id_col_of_parent(table)
    # If there's no new_parent_id yet, this must be the top parent table that we're duplicating
    parent_col = _get_parent_col(table)
    copy_key_col = parent_col if new_parent_id else pri_col
    cols_to = []
    cols_from = []
    for col in _get_columns(table):
        if col == pri_col and pri_col != parent_col:
            continue
        cols_to.append(col)
        if col == 'name':
            cols_from.append("COALESCE('copy of ' || name, 'copy of unnamed measure #' || id)")
        elif col == parent_col and new_parent_id:
            cols_from.append(str(new_parent_id))
        else:
            cols_from.append(col)

    query = """
        INSERT INTO "{table}" ({cols_to})
        SELECT {cols_from}
        FROM "{table}"
        WHERE {copy_key_col} = %s
        RETURNING {pri_col}
        """.format(table=table, cols_to=', '.join(cols_to), cols_from=', '.join(cols_from),
                   copy_key_col=copy_key_col, pri_col=pri_col)

    try:
        cur.execute(query, (old_parent_id,))
    except psycopg2.IntegrityError as e:
        _fix_sequence(table)
        raise SequenceError

    inserted_id = cur.fetchone()[0]
    return inserted_id

# This is the method that actually duplicates the measure; it's separate from duplicate_measure()
# so that we don't keep reconnecting to the database if we need to retry due to a sequence problem
def _duplicate_measure(retries=0):
    table = sht.range((wb.app.selection.row, MEASURE_TABLE_COL)).value
    parent_id = int(sht.range((wb.app.selection.row, MEASURE_ID_COL)).value)
    parent_dict = dict(_load_parent_row(table, parent_id))
    try:
        new_parent_id = _duplicate_rows(table, parent_id)

        subtables = MEASURE_SUBTABLES.get(table, [None])
        for subtable in subtables:
            if subtable is None:
                _duplicate_rows(table + 'Data', parent_id, new_parent_id)
            else:
                old_subparent_row = _load_parent_row(subtable, parent_id)
                # Occasionally it happens that a subtable doesn't have any data for a particular measure,
                # so we need this "if" to guard against trying to copy None
                if old_subparent_row:
                    old_subparent_id = dict(old_subparent_row)[_get_id_col_of_parent(subtable)]
                    new_subparent_id = _duplicate_rows(subtable, parent_id, new_parent_id)
                    _duplicate_rows(subtable + 'Data', old_subparent_id, new_subparent_id)
    except SequenceError:
        # We had to fix a sequence in one of the tables. This means our transaction got rolled back,
        # any data we previously inserted is gone and we need to start over
        assert retries <= 10, "duplicate_measures() seems to be stuck in a sequence-fixing loop; aborting."
        _duplicate_measure(retries + 1)

    con.commit()
    _msg("Duplicated {} #{}. Compare scenarios with 'merge by: left' to see the new measure.".format(table, parent_id))


def duplicate_measure():
    if sht.range((wb.app.selection.row, MEASURE_ID_COL)).value == SENSITIVTY_LABEL:
        _msg("Can't duplicate sensitivities, only measures")
        return

    _connect_to_db()
    _duplicate_measure()

def _parent_data_to_dict(parent_data):
    """Make a dict out of the column names and values for the parent data, discarding any unused rows"""
    parent_dict = {}
    for (col, val) in parent_data:
        if col:
            parent_dict[col] = val
    return parent_dict

def _update_parent_table(parent_table, parent_dict):
    update_cols = []
    update_vals = []

    id_col_of_parent = _get_id_col_of_parent(parent_table)
    if id_col_of_parent in LOOKUP_MAP:
        parent_id = _id_for(LOOKUP_MAP[id_col_of_parent], parent_dict[id_col_of_parent])
    else:
        parent_id = parent_dict[id_col_of_parent]

    for col, val in parent_dict.iteritems():
        if col != id_col_of_parent:
            update_cols.append(col)
            if val is None or val == '':
                update_vals.append(None)
            elif col in LOOKUP_MAP:
                try:
                    update_vals.append(_id_for(LOOKUP_MAP[col], val))
                except KeyError:
                    raise PathwaysLookupError(val, parent_table, col)
            else:
                update_vals.append(val)

    val_placeholder = ', '.join(["%s"] * len(update_vals))
    parent_update_query = 'UPDATE "{}" SET ({}) = ({}) WHERE {} = %s'.format(
        parent_table, ', '.join(update_cols), val_placeholder, id_col_of_parent
    )
    cur.execute(parent_update_query, update_vals + [parent_id])

def save_measure_sheet():
    assert hasattr(psycopg2.extras, 'execute_values'), "Scenario builder requires psycopg2 version 2.7 or greater " \
                                                       "in order to save data; please use conda or pip to upgrade " \
                                                       "your psycopg2 package"

    _connect_to_db()
    top_parent_name = sht.range(MEASURE_PARENT_NAME_RANGE_STR).value
    parent_data_range = sht.range(MEASURE_PARENT_DATA_RANGE_STR)
    subtable_name = sht.range(MEASURE_SUBTABLE_NAME_RANGE_STR).value
    subtable_data_range = sht.range(MEASURE_SUBTABLE_DATA_RANGE_STR)
    data_table_name_range = sht.range(MEASURE_DATA_TABLE_NAME_RANGE_STR)
    data_range = sht.range(MEASURE_DATA_RANGE_STR)

    top_parent_dict = _parent_data_to_dict(parent_data_range.value)
    subtable_dict = _parent_data_to_dict(subtable_data_range.value)
    id_col_of_parent = _get_id_col_of_parent(top_parent_name)
    parent_id = top_parent_dict[id_col_of_parent]
    # To get the effective parent row for the data table, we use the "nearest" table -- that is, use the subtable
    # if there is one, otherwise use the top level parent
    parent_dict = subtable_dict or top_parent_dict
    data_table = data_table_name_range.value

    # Load the measure data into a list of lists, discarding unused rows and columns
    measure_data = data_range.value
    used_cols = set(i for i, val in enumerate(measure_data[0]) if val)
    measure_data = [[val for i, val in enumerate(row) if i in used_cols] for row in measure_data if any(row)]
    if not measure_data:
        _msg("Save failed: could not find measure data to save")
        return
    header = measure_data.pop(0)

    # Convert the column names shown in Excel back to the actual database column names
    db_cols = [_get_parent_col(data_table)]
    for col in header:
        if col == parent_dict['geography_id']:
            db_cols.append('gau_id')
            # Note: This will now accept foreign GAUs by not filtering by geography_id with creating the geographies_data id lookup.
			# It is possible because the name column of GeographiesData is itself unique. This feature is for advanced users only.
            geographies_data = _lookup_for('GeographiesData', 'name')
        elif 'other_index_1_id' in parent_dict and parent_dict['other_index_1_id'] and col == parent_dict['other_index_1_id']:
            db_cols.append('oth_1_id')
            other_index_1_data = _lookup_for('OtherIndexesData', 'name', 'other_index_id',
                                             _id_for('OtherIndexes', parent_dict['other_index_1_id']))
        elif 'other_index_2_id' in parent_dict and parent_dict['other_index_2_id'] and col == parent_dict['other_index_2_id']:
            db_cols.append('oth_2_id')
            other_index_2_data = _lookup_for('OtherIndexesData', 'name', 'other_index_id',
                                             _id_for('OtherIndexes', parent_dict['other_index_2_id']))
        else:
            db_cols.append(col)

    # Convert the text values shown in the data table back into database ids
    db_rows = []
    for row in measure_data:
        db_row = [parent_id]
        for i, val in enumerate(row):
            # + 1 here because we need to skip past the parent_id column
            col = db_cols[i + 1]
            if col == 'gau_id':
                try:
                    db_row.append(geographies_data[val])
                except KeyError:
                    raise PathwaysLookupError(val, data_table, parent_dict['geography_id'])
            elif col == 'oth_1_id':
                try:
                    db_row.append(other_index_1_data[val])
                except KeyError:
                    raise PathwaysLookupError(val, data_table, parent_dict['other_index_1_id'])
            elif col == 'oth_2_id':
                try:
                    db_row.append(other_index_2_data[val])
                except KeyError:
                    raise PathwaysLookupError(val, data_table, parent_dict['other_index_2_id'])
            elif col in LOOKUP_MAP:
                try:
                    db_row.append(_id_for(LOOKUP_MAP[col], val))
                except KeyError:
                    raise PathwaysLookupError(val, data_table, col)
            else:
                db_row.append(val)
        db_rows.append(db_row)

    # Clean out the old data from the data table for this parent_id
    del_query = 'DELETE FROM "{}" WHERE {} = %s'.format(data_table, db_cols[0])
    cur.execute(del_query, (parent_id,))

    # Insert the new data from the worksheet
    ins_query = 'INSERT INTO "{}" ({}) VALUES %s'.format(data_table, ', '.join(db_cols))

    try:
        # This requires psycopg2 >=2.7
        psycopg2.extras.execute_values(cur, ins_query, db_rows)
    except psycopg2.IntegrityError:
        _fix_sequence(data_table)
        # Now redo the delete and insert that we were originally trying to do
        cur.execute(del_query, (parent_id,))
        psycopg2.extras.execute_values(cur, ins_query, db_rows)

    # Update the parent tables
    _update_parent_table(top_parent_name, top_parent_dict)
    if subtable_dict:
        _update_parent_table(subtable_name, subtable_dict)

    con.commit()

    _msg('Successfully saved {} for parent_id {}'.format(data_table, int(parent_id)))

def _range_contains(container, cell):
    # Check if cell is inside container. "Cell" may actually be a multi-cell range, in which case we're just
    # checking the top-left cell, not looking at its entire extent.
    return (container.column <= cell.column <= container.last_cell.column and
            container.row <= cell.row <= container.last_cell.row)

def _replace_options(msg, new_header=None, new_options=None):
    _msg(msg)
    # Replaces the contents of the options area. If no header or options are passed in, they're just cleared
    header = sht.range(OPTIONS_COLUMN_HEADER_STR)
    options = sht.range(OPTIONS_COLUMN_STR)

    if new_header:
        header.value = new_header
    else:
        header.clear_contents()

    options.clear_contents()
    if new_options:
        options.value = [[option] for option in new_options]


def get_options():
    _connect_to_db()
    parent_data_range = sht.range(MEASURE_PARENT_DATA_RANGE_STR)
    subtable_data_range = sht.range(MEASURE_SUBTABLE_DATA_RANGE_STR)
    data_table_range = sht.range(MEASURE_DATA_RANGE_STR)
    selection = wb.app.selection
    lookup = None

    inside_range = None
    if _range_contains(parent_data_range, selection):
        inside_range = 'parent'
    elif _range_contains(subtable_data_range, selection):
        inside_range = 'subtable'
    elif _range_contains(data_table_range, selection):
        inside_range = 'data'

    if inside_range:
        if inside_range == 'data':
            table = sht.range(MEASURE_DATA_TABLE_NAME_RANGE_STR).value
            lookup_col = sht.range((data_table_range.row, selection.column)).value
            if not lookup_col:
                _replace_options("Select a column with a column name at the top to get options.")
                return
            top_parent_dict = _parent_data_to_dict(parent_data_range.value)
            subtable_dict = _parent_data_to_dict(subtable_data_range.value)
            # To get the effective parent row for the data table, we use the "nearest" table -- that is, use the subtable
            # if there is one, otherwise use the top level parent
            parent_dict = subtable_dict or top_parent_dict

            # Special case lookups if the "column" isn't a real column but rather a value from the parent
            # table's geography or other index
            if lookup_col == parent_dict['geography_id']:
				# because using foreign GAUs is an advanced feature and we have 1000s of geographies in the model,
				# it makes sense here to still filter by geography_id even though it will technically support foreign GAUs as an input.
                lookup = _lookup_for('GeographiesData', 'name', 'geography_id',
                                     _id_for('Geographies', parent_dict['geography_id']))
            elif 'other_index_1_id' in parent_dict and parent_dict['other_index_1_id'] and lookup_col == parent_dict[
                'other_index_1_id']:
                lookup = _lookup_for('OtherIndexesData', 'name', 'other_index_id',
                                                 _id_for('OtherIndexes', parent_dict['other_index_1_id']))
            elif 'other_index_2_id' in parent_dict and parent_dict['other_index_2_id'] and lookup_col == parent_dict[
                'other_index_2_id']:
                lookup = _lookup_for('OtherIndexesData', 'name', 'other_index_id',
                                                 _id_for('OtherIndexes', parent_dict['other_index_2_id']))
        else:
            if inside_range == 'parent':
                lookup_xl_col = parent_data_range.column
                table = sht.range(MEASURE_PARENT_NAME_RANGE_STR).value
            else:
                lookup_xl_col = subtable_data_range.column
                table = sht.range(MEASURE_SUBTABLE_NAME_RANGE_STR).value
            lookup_col = sht.range((selection.row, lookup_xl_col)).value

            if not lookup_col:
                _replace_options("Select a row containing a column name to get options.")
                return

        qualified_col = "{}.{}".format(table, lookup_col)

        if not lookup:
            # We haven't already retrieved the lookup table due to one of the special cases above
            try:
                lookup_table = LOOKUP_MAP[lookup_col]
            except KeyError:
                _replace_options("No preset options to show for {}.".format(qualified_col))
                return
            lookup = _lookup_for(lookup_table, 'name')

        options = sorted(lookup.keys())
        _replace_options("Options loaded for {}".format(qualified_col), qualified_col, options)

    else:
        _replace_options("To get options select a row within a table.")


def delete_measure():
    _connect_to_db()
    table = sht.range((wb.app.selection.row, MEASURE_TABLE_COL)).value

    if sht.range((wb.app.selection.row, MEASURE_ID_COL)).value == SENSITIVTY_LABEL:
        parent_id = int(sht.range((wb.app.selection.row, SUBNODE_COL)).value)
        parent_col = _get_parent_col(table)
        sensitivity = sht.range((wb.app.selection.row, MEASURE_NAME_COL)).value
        query = 'DELETE FROM "{}" WHERE {} = %s AND sensitivity = %s'.format(table, parent_col)
        cur.execute(query, (parent_id, sensitivity))
        deleted_count = cur.rowcount
        con.commit()
        _msg('{} "{}" rows deleted from {} #{}'.format(deleted_count, sensitivity, table, parent_id))
    else:
        parent_id = int(sht.range((wb.app.selection.row, MEASURE_ID_COL)).value)
        parent_id_col = _get_id_col_of_parent(table)
        query = 'DELETE FROM "{}" WHERE {} = %s'.format(table, parent_id_col)
        cur.execute(query, (parent_id,))
        deleted_count = cur.rowcount
        if deleted_count == 1:
            con.commit()
            _msg("{} #{} deleted.".format(table, parent_id))
        else:
            con.rollback()
            raise IOError("Canceling deletion because {} measures would have been deleted.".format(deleted_count))


# This tricksiness enables us to debug from the command line, e.g. using ipdb
if __name__ == '__main__':
    xw.Book('scenario_builder.xlsm').set_mock_caller()
    import ipdb
    with ipdb.launch_ipdb_on_exception():
        # This is just an example; call whatever you're trying to debug here
        delete_measure()
