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

# outputs
output_levels = None
currency_name = None
output_energy_unit = None
output_currency = None
output_demand_levels = None
timestamp = None

# parallel processing
available_cpus = None

#logging
log_name = None

def initialize_config():
    global available_cpus, cfgfile_name, log_name, log_initialized, index_levels, solver_name, timestamp
    global years, supply_years, workingdir, years_subset
    workingdir = os.getcwd()

    years = range(2000,
                   getParamAsInt('end_year', section='TIME') + 1,
                   1)

    supply_years = range(getParamAsInt('current_year', section='TIME'),
                          getParamAsInt('end_year', section='TIME') + 1,
                          getParamAsInt('year_step', section='TIME'))



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

    calculation_energy_unit = getParam('energy_unit', section='UNITS')


def init_date_lookup():
    global date_lookup, time_slice_col, electricity_energy_type, elect_default_shape_key
    time_slice_col = ['year', 'month', 'week', 'hour', 'day_type']

    # electricity_energy_type_shape = csv_read_table('FinalEnergy', column_names=['shape'], name='electricity')
    electricity_energy_type = 'electricity'
    elect_default_shape_key = csv_read_table('FinalEnergy', column_names=['shape'], name='electricity')


def init_removed_levels():
    global removed_demand_levels
    removed_demand_levels = splitclean(getParam('removed_demand_levels', section='DEMAND_CALCULATION_PARAMETERS'))

def init_output_levels():
    global output_demand_levels, output_supply_levels, output_combined_levels
    output_demand_levels = ['year', 'vintage', 'demand_technology', 'air pollution', geomapper.GeoMapper.demand_primary_geography, 'sector', 'subsector', 'final_energy','other_index_1','other_index_2','cost_type','new/replacement']

    levels_to_remove = set([x[0][4:] for x in _ConfigParser.items('DEMAND_OUTPUT_DETAIL') if x[1].lower()!='true'])
    output_demand_levels = list(set(output_demand_levels) - levels_to_remove)


def table_dict(table_name, columns=['id', 'name'], append=False,
               other_index_id=id, return_iterable=False, return_unique=True):
    df = csv_read_table(table_name, columns,
                        other_index_id=other_index_id,
                        return_iterable=return_iterable,
                        return_unique=return_unique)

    result = upper_dict(df, append=append)
    return result


def init_output_parameters():
    global currency_name, output_currency, \
    rio_excluded_blends, rio_standard_energy_unit, rio_standard_mass_unit, rio_standard_distance_unit, rio_standard_volume_unit,\
    rio_start_year, rio_mass_blends, rio_distance_blends, rio_volume_blends,rio_flex_load_subsectors, rio_optimizable_subsectors



    currency_name = getParam('currency_name', section='UNITS')
    output_currency = getParam('currency_year', section='UNITS') + ' ' + currency_name
    rio_excluded_blends = [g.strip()  for g in getParam('rio_excluded_blends', section='RIO').split(',') if len(g)]
    rio_mass_blends = [g.strip() for g in getParam('rio_mass_blends', section='RIO').split(',') if len(g)]
    rio_volume_blends = [g.strip() for g in getParam('rio_excluded_blends', section='RIO').split(',') if len(g)]
    rio_distance_blends = [g.strip() for g in getParam('rio_excluded_blends', section='RIO').split(',') if len(g)]

    rio_standard_energy_unit = getParam('rio_standard_energy_unit', section='RIO')
    rio_standard_mass_unit = getParam('rio_standard_mass_unit', section='RIO')
    rio_standard_volume_unit = getParam('rio_standard_volume_unit', section='RIO')
    rio_standard_distance_unit = getParam('rio_standard_distance_unit', section='RIO')
    rio_start_year = getParamAsInt('rio_start_year',section='RIO')
    rio_flex_load_subsectors = [g.strip() for g in getParam('rio_flex_load_subsectors', section='RIO').split(',') if len(g)]
    rio_optimizable_subsectors = [g.strip() for g in getParam('rio_optimizable_subsectors', section='RIO').split(',') if len(g)]

    init_removed_levels()
    init_output_levels()




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
