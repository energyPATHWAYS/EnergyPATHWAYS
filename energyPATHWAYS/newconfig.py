'''
.. Copyright (c) 2016 Richard Plevin
   See the https://opensource.org/licenses/MIT for license details.

   Configuration files are read in this order:
   1. ./project.ini is read only to determine the location of the database.
   2. energyPATHWAYS/etc/system.ini is read into the main config object
   3. energyPATHWAYS/etc/{platform}.ini is read into the main config object
   4. A "site" config file is read from $PATHWAYS_SITE_CONFIG, if defined
   5. {database}/database.ini is read into the main config object top of parameters from system.ini
   6. ./project.ini values are applied to the main config object, have the final say.
   At this time, there is no ~/pathways.ini file or the equivalent, though this option exists.
'''
from __future__ import print_function
import os
import platform
from pkg_resources import resource_string
from backports import configparser
from .error import ConfigFileError, PathwaysException

# TODO: add configparser to requirements in setup.py, *.yml

DEFAULT_SECTION = 'DEFAULT'
USR_CONFIG_FILE  = 'pathways.ini'
PROJ_CONFIG_FILE = 'project.ini'
DB_CONFIG_FILE   = 'database.ini'

PlatformName = platform.system()

_ConfigParser = None

_ProjectSection = DEFAULT_SECTION


_ReadUserConfig = False

def getSection():
    return _ProjectSection

def setSection(section):
    """
    Set the name of the default config file section to read from.

    :param section: (str) a config file section name.
    :return: none
    """
    global _ProjectSection
    _ProjectSection = section

def configLoaded():
    return bool(_ConfigParser)

def getConfig(reload=False, allowMissing=True, includeEnvironment=False):
    """
    Return the configuration object. If one has been created already via
    `readConfigFiles`, it is returned; otherwise a new one is created
    and the configuration files are read. Applications generally do not
    need to use this object directly since the single instance is stored
    internally and referenced by the other API functions.

    :param: reload (bool) if True, instantiate a new global ConfigParser.
    :param: allowMissing (bool) if True, a missing config file is not
       treated as an error. This is used only when generating documentation,
       e.g., on readthedocs.org.
    :return: a `ConfigParser` instance.
    """
    if reload:
        global _ConfigParser
        _ConfigParser = None

    return _ConfigParser or readConfigFiles(allowMissing=allowMissing,
                                            includeEnvironment=includeEnvironment)

def _readConfigResourceFile(filename, package='energyPATHWAYS', raiseError=True):
    try:
        data = resource_string(package, filename)
    except IOError:
        if raiseError:
            raise
        else:
            return None

    data = unicode(data)
    _ConfigParser.read_string(data, source=filename)
    return data

def getHomeDir():
    if PlatformName == 'Windows':
        # HOME exists on all Unix-like systems; for Windows it's HOMEPATH or HOMESHARE.
        # If set, we use PATHWAYS_HOME to identify the folder with the config file;
        # otherwise, we use HOMESHARE if set, or HOMEPATH, in that order.
        env = os.environ
        homedir = env.get('PATHWAYS_HOME') or env.get('HOMESHARE') or env.get('HOMEPATH')
        drive, path = os.path.splitdrive(homedir)
        drive = drive or env.get('HOMEDRIVE') or 'C:'
        home = os.path.realpath(drive + path)
        home = home.replace('\\', '/')            # avoids '\' quoting issues
    else:
        home = os.getenv('HOME')

    return home


def userConfigPath():
    path = os.path.join(getHomeDir(), USR_CONFIG_FILE)
    return path

def _getParser():
    # Strict mode prevents duplicate sections, which we do not restrict
    parser = configparser.ConfigParser(comment_prefixes=('#'),
                                       strict=False,
                                       empty_lines_in_values=False)
    home = getHomeDir()
    parser.set(DEFAULT_SECTION, 'Home', home)
    parser.set(DEFAULT_SECTION, 'User', os.getenv('USER', 'unknown'))

    return parser

def _getProjectConfig():
    """
    Read project.ini from current directory to obtain database_path
    """
    parser = _getParser()

    try:
        with open(PROJ_CONFIG_FILE) as f:
            parser.read_file(f)
            return parser

    except Exception as e:
        raise ConfigFileError("Failed to read {}: {}".format(PROJ_CONFIG_FILE, e))

def _getDatabasePath(parser):
    try:
        database_path = parser.get(DEFAULT_SECTION, 'database_path')
    except configparser.NoOptionError:
        raise ConfigFileError("project.ini must define 'database_path'")

    if not database_path:
        raise ConfigFileError("project.ini must define 'database_path' as a valid directory name")

    if not os.path.lexists(database_path):
        raise ConfigFileError("project.ini defines database_path as '{}', which does not exist".format(database_path))

    return database_path

def _readConfig(pathname, allowMissing=True):
    try:
        with open(pathname) as f:
            _ConfigParser.read_file(f)

    except IOError:
        if not allowMissing:
            if not os.path.lexists(pathname):
                raise ConfigFileError("Missing configuration file '{}'".format(pathname))
            else:
                raise ConfigFileError("Can't read configuration file '{}'".format(pathname))

def _readSiteConfig():
    siteConfig = os.getenv('PATHWAYS_SITE_CONFIG')
    if siteConfig:
        try:
            _readConfig(siteConfig, allowMissing=False)
        except Exception as e:
            print("WARNING: Failed to read site config file: '{}'".format(e))

def readConfigFiles(allowMissing=False, includeEnvironment=False):
    """
    Read the pathways configuration files, starting with ``pygcam/etc/system.ini``,
    followed by ``pathways/etc/{platform}.ini`` if present. If the environment variable
    ``PATHWAYS_SITE_CONFIG`` is defined, its value should be a config file, which is
    read next. Finally, the user's config file, ``~/.pathways.ini``, is read. Each
    successive file overrides values for any variable defined in an earlier file.

    :param allowMissing: (bool) if True, don't treat a missing user config file as an error.
    :param includeEnvironment: (bool) if True, environment variables are loaded into the
       configuration dictionary prefixed by '$'.
    :return: a populated ConfigParser instance
    """
    global _ConfigParser

    _ConfigParser = _getParser()

    # don't force keys to lower-case: variable names are case sensitive
    _ConfigParser.optionxform = lambda option: option

    if includeEnvironment:
        # Create vars from environment variables as '$' + variable name, as in the shell
        for name, value in os.environ.iteritems():
            value = value.replace(r'%', r'%%')
            _ConfigParser.set(DEFAULT_SECTION, '$' + name, value)

    # Initialize config parser with default values
    _readConfigResourceFile('etc/system.ini')

    # Read platform-specific defaults, if defined. No error if file is missing.
    _readConfigResourceFile('etc/%s.ini' % PlatformName, raiseError=False)

    _readSiteConfig()

    # Read ./project.ini into a separate parser to get database path only (error if not present)
    projectParser = _getProjectConfig()
    database_path = _getDatabasePath(projectParser)

    # Read database.ini into _ConfigParser
    dbConfigPath = os.path.join(database_path, DB_CONFIG_FILE)
    _readConfig(dbConfigPath)

    # Update config parser using raw values from project.ini, which we read earlier
    for key, value in projectParser.items(DEFAULT_SECTION, raw=True):
        setParam(key, value, DEFAULT_SECTION)

    if _ReadUserConfig:
        # User customizations are stored in ~/pathways.ini
        usrConfigPath = userConfigPath()
        _readConfig(usrConfigPath, allowMissing=allowMissing)

    # Dynamically set (if not defined) 'project_name' in each section, holding the
    # section (i.e., project) name. If user has set this, the value is unchanged.
    projectNameVar = 'project_name'
    for section in getSections():
        if not (_ConfigParser.has_option(section, projectNameVar) and   # var must exist
                _ConfigParser.get(section, projectNameVar)):            # and not be blank
            _ConfigParser.set(section, projectNameVar, section)

    projectName = getParam('default_project', section=DEFAULT_SECTION)
    if projectName:
        setSection(projectName)

    return _ConfigParser

def getSections():
    return _ConfigParser.sections()

def getConfigDict(section=DEFAULT_SECTION, raw=False):
    """
    Return all variables defined in `section` as a dictionary.

    :param section: (str) the name of a section in the config file
    :param raw: (bool) whether to return raw or interpolated values.
    :return: (dict) all variables defined in the section (which includes
       those defined in DEFAULT.)
    """
    d = {key : value for key, value in _ConfigParser.items(section, raw=raw)}
    return d

def setParam(name, value, section=None):
    """
    Set a configuration parameter in memory.

    :param name: (str) parameter name
    :param value: (any, coerced to str) parameter value
    :param section: (str) if given, the name of the section in which to set the value.
       If not given, the value is set in the established project section, or DEFAULT
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

    except configparser.NoSectionError:
        if raiseError:
            raise PathwaysException('getParam: unknown section "%s"' % section)
        else:
            return None

    except configparser.NoOptionError:
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
    :raises: :py:exc:`pathways.error.ConfigFileError`
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

