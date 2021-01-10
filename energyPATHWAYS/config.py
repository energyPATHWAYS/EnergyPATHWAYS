__author__ = 'Ben Haley & Ryan Jones'

import errno
import ConfigParser
import geomapper
from energyPATHWAYS.util import splitclean, csv_read_table, upper_dict, ensure_iterable
import warnings
from collections import defaultdict
import datetime
import logging
import sys
from pyomo.opt import SolverFactory
import pdb
import os
import platform
from error import ConfigFileError, PathwaysException
from energyPATHWAYS.generated.new_database import EnergyPathwaysDatabase
import unit_converter
# Don't print warnings
warnings.simplefilter("ignore")

# core inputs
workingdir = None

# pickle names
full_model_append_name = '_full_model.p'
demand_model_append_name = '_demand_model.p'
model_error_append_name = '_model_error.p'

# common data inputs
index_levels = None
dnmtr_col_names = ['driver_denominator_1', 'driver_denominator_2']
drivr_col_names = ['driver_1', 'driver_2','driver_3']
tech_classes = ['capital_cost_new', 'capital_cost_replacement', 'installation_cost_new', 'installation_cost_replacement', 'fixed_om', 'variable_om', 'efficiency']
#storage techs have additional attributes specifying costs for energy (i.e. kWh of energy storage) and discharge capacity (i.e. kW)
storage_tech_classes = ['installation_cost_new','installation_cost_replacement', 'fixed_om', 'variable_om', 'efficiency', 'capital_cost_new_capacity', 'capital_cost_replacement_capacity',
                        'capital_cost_new_energy', 'capital_cost_replacement_energy']

# Initiate pint for unit conversions
calculation_energy_unit = None

# run years
years = None
supply_years = None
years_subset = None

# shapes
shape_start_date = None
shape_years = None
date_lookup = None
time_slice_col = None
electricity_energy_type = None
elect_default_shape_key = None
opt_period_length = None
solver_name = None
transmission_constraint = None
filter_dispatch_less_than_x = None
keep_dispatch_outputs_in_model=None

# outputs
output_levels = None
currency_name = None
output_energy_unit = None
output_currency = None
output_demand_levels = None
output_supply_levels = None
output_combined_levels = None
outputs_id_map = defaultdict(dict)
dispatch_write_years = None
timestamp = None

# parallel processing
available_cpus = None

#logging
log_name = None

def initialize_config():
    global available_cpus, cfgfile_name, log_name, log_initialized, index_levels, solver_name, timestamp
    global years, supply_years, workingdir, years_subset
    workingdir = os.getcwd()

    years = range(getParamAsInt('demand_start_year', section='TIME'),
                   getParamAsInt('end_year', section='TIME') + 1,
                   getParamAsInt('year_step', section='TIME'))

    supply_years = range(getParamAsInt('current_year', section='TIME'),
                          getParamAsInt('end_year', section='TIME') + 1,
                          getParamAsInt('year_step', section='TIME'))


    if len(getParam('cod_years_subset', section='COMBINED_OUTPUT_DETAIL')) and getParam('cod_years_subset',section='COMBINED_OUTPUT_DETAIL')!='None':
        years_subset = [int(x.strip()) for x in getParam('cod_years_subset',section='COMBINED_OUTPUT_DETAIL').split(',') ]
    else:
        years_subset = supply_years

    log_name = '{} energyPATHWAYS log.log'.format(str(datetime.datetime.now())[:-4].replace(':', '.'))
    setuplogging()

    init_db()
    init_units()
    geomapper.GeoMapper.get_instance()
    init_date_lookup()
    init_output_parameters()
    unit_converter.UnitConverter.get_instance()
    # used when reading in raw_values from data tables
    index_levels = csv_read_table('IndexLevels', column_names=['index_level', 'data_column_name'])
    solver_name = find_solver()

    available_cpus = getParamAsInt('num_cores', section='CALCULATION_PARAMETERS')
    timestamp = str(datetime.datetime.now().replace(second=0,microsecond=0))

def setuplogging():
    if not os.path.exists(os.path.join(os.getcwd(), 'logs')):
        os.makedirs(os.path.join(os.getcwd(), 'logs'))
    log_path = os.path.join(os.getcwd(), 'logs', log_name)
    log_level = getParam('log_level', section='LOG').upper()
    logging.basicConfig(filename=log_path, level=log_level)
    logger = logging.getLogger()
    if getParamAsBoolean('stdout', 'LOG') and not any(type(h) is logging.StreamHandler for h in logger.handlers):
        soh = logging.StreamHandler(sys.stdout)
        soh.setLevel(log_level)
        logger.addHandler(soh)

def init_db():
    dbdir = getParam('database_path', section='DATABASE')
    EnergyPathwaysDatabase.get_database(dbdir, load=False)

def init_units():
    # Initiate pint for unit conversions
    global calculation_energy_unit

    calculation_energy_unit = getParam('calculation_energy_unit', section='UNITS')


def init_date_lookup():
    global date_lookup, time_slice_col, electricity_energy_type, electricity_energy_type_shape, opt_period_length, transmission_constraint, filter_dispatch_less_than_x, keep_dispatch_outputs_in_model, elect_default_shape_key
    time_slice_col = ['year', 'month', 'week', 'hour', 'day_type']

    # electricity_energy_type_shape = csv_read_table('FinalEnergy', column_names=['shape'], name='electricity')
    electricity_energy_type = 'electricity'
    elect_default_shape_key = csv_read_table('FinalEnergy', column_names=['shape'], name='electricity')

    opt_period_length = getParamAsInt('period_length', section='ELECTRICITY_DISPATCH')
    transmission_constraint = getParam('transmission_constraint', section='ELECTRICITY_DISPATCH')
    transmission_constraint = transmission_constraint if transmission_constraint != "" else None
    filter_dispatch_less_than_x = getParamAsFloat('filter_dispatch_less_than_x', section='ELECTRICITY_DISPATCH')
    keep_dispatch_outputs_in_model = getParamAsBoolean('keep_dispatch_outputs_in_model', section='ELECTRICITY_DISPATCH')
    filter_dispatch_less_than_x = float(filter_dispatch_less_than_x) if filter_dispatch_less_than_x != "" else None

def init_removed_levels():
    global removed_demand_levels
    removed_demand_levels = splitclean(getParam('removed_demand_levels', section='DEMAND_CALCULATION_PARAMETERS'))

def init_output_levels():
    global output_demand_levels, output_supply_levels, output_combined_levels
    output_demand_levels = ['year', 'vintage', 'demand_technology', 'air pollution', geomapper.GeoMapper.demand_primary_geography, 'sector', 'subsector', 'final_energy','other_index_1','other_index_2','cost_type','new/replacement']
    output_supply_levels = ['year', 'vintage', 'supply_technology', geomapper.GeoMapper.supply_primary_geography,  'demand_sector', 'supply_node', 'ghg', 'resource_bin','cost_type']
    output_combined_levels = list(set(output_supply_levels + output_demand_levels) - {geomapper.GeoMapper.demand_primary_geography, geomapper.GeoMapper.supply_primary_geography})
    output_combined_levels = output_combined_levels + [geomapper.GeoMapper.combined_outputs_geography + "_supply", geomapper.GeoMapper.combined_outputs_geography]

    levels_to_remove = set([x[0][4:] for x in _ConfigParser.items('DEMAND_OUTPUT_DETAIL') if x[1].lower()!='true'])
    output_demand_levels = list(set(output_demand_levels) - levels_to_remove)

    levels_to_remove = set([x[0][4:] for x in _ConfigParser.items('SUPPLY_OUTPUT_DETAIL') if x[1].lower()!='true'])
    output_supply_levels = list(set(output_supply_levels) - levels_to_remove)

    levels_to_remove = set([x[0][4:] for x in _ConfigParser.items('COMBINED_OUTPUT_DETAIL') if x[1].lower()!='true'])
    output_combined_levels = list(set(output_combined_levels) - levels_to_remove)


    if not getParamAsBoolean('cod_supply_geography', 'COMBINED_OUTPUT_DETAIL'):
        output_combined_levels.remove(geomapper.GeoMapper.combined_outputs_geography + "_supply")

def table_dict(table_name, columns=['id', 'name'], append=False,
               other_index_id=id, return_iterable=False, return_unique=True):
    df = csv_read_table(table_name, columns,
                        other_index_id=other_index_id,
                        return_iterable=return_iterable,
                        return_unique=return_unique)

    result = upper_dict(df, append=append)
    return result


def init_output_parameters():
    global currency_name, output_currency, output_tco, output_payback, evolved_run, evolved_blend_nodes, evolved_years,\
    rio_supply_run,rio_db_run, rio_geography, rio_feeder_geographies, rio_energy_unit, rio_time_unit, rio_timestep_multiplier, rio_non_zonal_blend_nodes, rio_excluded_technologies, \
    rio_excluded_blends, rio_export_blends, rio_no_negative_blends, rio_excluded_nodes, rio_mass_unit, rio_distance_unit, rio_outflow_products, rio_standard_energy_unit, rio_volume_unit,\
    calculate_costs, calculate_energy, calculate_emissions, rio_opt_demand_subsectors, rio_start_year

    try:
        calculate_costs = getParamAsBoolean("calculate_costs",section='COMBINED_OUTPUT_DETAIL')
        calculate_energy= getParamAsBoolean("calculate_energy", section='COMBINED_OUTPUT_DETAIL')
        calculate_emissions = getParamAsBoolean("calculate_emissions", section='COMBINED_OUTPUT_DETAIL')
    except:
        calculate_costs = True
        calculate_energy = True
        calculate_emissions = True

    currency_name = getParam('currency_name', section='UNITS')
    output_currency = getParam('currency_year', section='UNITS') + ' ' + currency_name
    output_tco = getParamAsBoolean('output_tco', section='DEMAND_CALCULATION_PARAMETERS')
    output_payback = getParamAsBoolean('output_payback', section='DEMAND_CALCULATION_PARAMETERS')
    rio_supply_run = getParamAsBoolean('rio_supply_run', section='RIO')
    rio_db_run = getParamAsBoolean('rio_db_run', section='RIO')
    rio_geography = getParam('rio_geography', section='RIO')
    rio_feeder_geographies = [feeder_geo.strip() for feeder_geo in getParam('rio_feeder_geographies', section='RIO').split(',') if len(feeder_geo)]
    rio_energy_unit = getParam('rio_energy_unit', section='RIO')
    rio_time_unit = getParam('rio_time_unit', section='RIO')
    rio_timestep_multiplier = getParamAsInt('rio_timestep_multiplier', section='RIO')
    # rio_non_zonal_blend_nodes = [g.strip() for g in getParam('rio_non_zonal_blends').split(',') if len(g)]
    rio_non_zonal_blend_nodes = None
    # rio_opt_demand_subsectors = [g.strip() for g in _ConfigParser.get('rio', 'rio_opt_demand_subsectors', section='RIO').split(',') if len(g)]
    rio_opt_demand_subsectors = None
    rio_excluded_technologies = [g.strip() for g in getParam('rio_excluded_technologies', section='RIO').split(',') if len(g)]
    rio_excluded_blends = [g.strip()  for g in getParam('rio_excluded_blends', section='RIO').split(',') if len(g)]
    rio_export_blends = [g.strip()  for g in getParam('rio_export_blends', section='RIO').split(',') if len(g)]
    rio_outflow_products = [g.strip()  for g in getParam('rio_outflow_products', section='RIO').split(',') if len(g)]
    rio_excluded_nodes = [g.strip()  for g in getParam('rio_excluded_nodes', section='RIO').split(',') if len(g)]
    rio_no_negative_blends = [g.strip()  for g in getParam('rio_no_negative_blends', section='RIO').split(',') if len(g)]
    # evolved_run = getParam('evolved','evolved_run').lower()
    # evolved_years = [x for x in ensure_iterable(getParam('evolved', 'evolved_years'))]
    # evolved_blend_nodes = splitclean(getParam('evolved','evolved_blend_nodes'), as_type=int)
    rio_mass_unit = getParam('rio_mass_unit', section='RIO')
    rio_volume_unit = getParam('rio_volume_unit', section='RIO')
    rio_distance_unit = getParam('rio_distance_unit', section='RIO')
    rio_standard_energy_unit = getParam('rio_standard_energy_unit', section='RIO')
    rio_standard_mass_unit = getParam('rio_standard_mass_unit', section='RIO')
    rio_standard_volume_unit = getParam('rio_standard_volume_unit', section='RIO')
    rio_standard_distance_unit = getParam('rio_standard_distance_unit', section='RIO')
    # rio_start_year = getParamAsInt('rio_start_year',section='RIO')
    rio_start_year = None
    init_removed_levels()
    init_output_levels()



def find_solver():
    requested_solvers = [g.strip() for g in getParam('dispatch_solver', section='ELECTRICITY_DISPATCH').split(',') if len(g)]
    solver_name = None
    # inspired by the solver detection code at https://software.sandia.gov/trac/pyomo/browser/pyomo/trunk/pyomo/scripting/driver_help.py#L336
    # suppress logging of warnings for solvers that are not found
    logger = logging.getLogger('pyomo.solvers')
    _level = logger.getEffectiveLevel()
    logger.setLevel(logging.ERROR)
    for requested_solver in requested_solvers:
        logging.debug("Looking for %s solver" % requested_solver)
        if SolverFactory(requested_solver).available(False):
            solver_name = requested_solver
            logging.debug("Using %s solver" % requested_solver)
            break
    # restore logging
    logger.setLevel(_level)

    assert solver_name is not None, "Dispatch could not find any of the solvers requested in your configuration (%s) please see README.md, check your configuration, and make sure you have at least one requested solver installed." % ', '.join(requested_solvers)
    return solver_name

CALCULATION_PARAMETERS_SECTION = 'CALCULATION_PARAMETERS'
PROJ_CONFIG_FILE = 'config.ini'

PlatformName = platform.system()

_ConfigParser = None

_ProjectSection = CALCULATION_PARAMETERS_SECTION


_ReadUserConfig = False

def getSection():
    return _ProjectSection

def configLoaded():
    return bool(_ConfigParser)

def getConfig(reload=False):
    if reload:
        global _ConfigParser
        _ConfigParser = None

    return _ConfigParser or readConfigFiles()

def readConfigFiles():
    global _ConfigParser

    _ConfigParser = ConfigParser.ConfigParser()
    config_path = os.path.join(os.getcwd(), PROJ_CONFIG_FILE)

    if not os.path.isfile(config_path):
        raise IOError(errno.ENOENT, "Unable to load configuration file. "
                                    "Please make sure your configuration file is located at {}, "
                                    "or use the -p and -c command line options to specify a different location. "
                                    "Type `energyPATHWAYS --help` for help on these options.".format(str(config_path)))

    _ConfigParser.read(config_path)

    return _ConfigParser


def setParam(name, value, section=None):
    """
    Set a configuration parameter in memory.

    :param name: (str) parameter name
    :param value: (any, coerced to str) parameter value
    :param section: (str) if given, the name of the section in which to set the value.
       If not given, the value is set in the established project section, or CALCULATION_PARAMETERS
       if no project section has been set.
    :return: value
    """
    section = section or getSection()

    if not _ConfigParser:
        getConfig()

    _ConfigParser.set(section, name, value)
    return value

def getParam(name, section=None, raw=False, raiseError=True):
    """
    Get the value of the configuration parameter `name`. Calls
    :py:func:`getConfig` if needed.

    :param name: (str) the name of a configuration parameters. Note
       that variable names are case-insensitive. Note that environment
       variables are available using the '$' prefix as in a shell.
       To access the value of environment variable FOO, use getParam('$FOO').

    :param section: (str) the name of the section to read from, which
      defaults to the value used in the first call to ``getConfig``,
      ``readConfigFiles``, or any of the ``getParam`` variants.
    :return: (str) the value of the variable, or None if the variable
      doesn't exist and raiseError is False.
    :raises NoOptionError: if the variable is not found in the given
      section and raiseError is True
    """
    section = section or getSection()

    if not section:
        raise PathwaysException('getParam was called without setting "section"')

    if not _ConfigParser:
        getConfig()

    try:
        value = _ConfigParser.get(section, name, raw=raw)

    except ConfigParser.NoSectionError:
        if raiseError:
            raise PathwaysException('getParam: unknown section "%s"' % section)
        else:
            return None

    except ConfigParser.NoOptionError:
        if raiseError:
            raise PathwaysException('getParam: unknown variable "%s"' % name)
        else:
            return None

    return value

_True  = ['t', 'y', 'true',  'yes', 'on',  '1']
_False = ['f', 'n', 'false', 'no',  'off', '0']

def stringTrue(value, raiseError=True):
    value = str(value).lower()

    if value in _True:
        return True

    if value in _False:
        return False

    if raiseError:
        msg = 'Unrecognized boolean value: "{}". Must one of {}'.format(value, _True + _False)
        raise ConfigFileError(msg)
    else:
        return None


def getParamAsBoolean(name, section=None):
    """
    Get the value of the configuration parameter `name`, coerced
    into a boolean value, where any (case-insensitive) value in the
    set ``{'true','yes','on','1'}`` are converted to ``True``, and
    any value in the set ``{'false','no','off','0'}`` is converted to
    ``False``. Any other value raises an exception.
    Calls :py:func:`getConfig` if needed.

    :param name: (str) the name of a configuration parameters.
    :param section: (str) the name of the section to read from, which
      defaults to the value used in the first call to ``getConfig``,
      ``readConfigFiles``, or any of the ``getParam`` variants.
    :return: (bool) the value of the variable
    :raises: :py:exc:`rio.error.ConfigFileError`
    """
    value = getParam(name, section=section)
    result = stringTrue(value, raiseError=False)

    if result is None:
        msg = 'The value of variable "{}", {}, could not converted to boolean.'.format(name, value)
        raise ConfigFileError(msg)

    return result


def getParamAsInt(name, section=None):
    """
    Get the value of the configuration parameter `name`, coerced
    to an integer. Calls :py:func:`getConfig` if needed.

    :param name: (str) the name of a configuration parameters.
    :param section: (str) the name of the section to read from, which
      defaults to the value used in the first call to ``getConfig``,
      ``readConfigFiles``, or any of the ``getParam`` variants.
    :return: (int) the value of the variable
    """
    value = getParam(name, section=section)
    return int(value)

def getParamAsFloat(name, section=None):
    """
    Get the value of the configuration parameter `name` as a
    float. Calls :py:func:`getConfig` if needed.

    :param name: (str) the name of a configuration parameters.
    :param section: (str) the name of the section to read from, which
      defaults to the value used in the first call to ``getConfig``,
      ``readConfigFiles``, or any of the ``getParam`` variants.
    :return: (float) the value of the variable
    """
    value = getParam(name, section=section)
    return float(value)

def getParamAsString(name, section=None):
    """
    Get the value of the configuration parameter `name` as a
    string. Calls :py:func:`getConfig` if needed.

    :param name: (str) the name of a configuration parameters.
    :param section: (str) the name of the section to read from, which
      defaults to the value used in the first call to ``getConfig``,
      ``readConfigFiles``, or any of the ``getParam`` variants.
    :return: (string) the value of the variable
    """
    value = getParam(name, section=section)
    return value
