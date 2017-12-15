"""
.. Logging support.
   This module allows modules to register themselves for logging which is
   turned on after the app reads configuration information. Modules call
   logger = pathways.log.getLogger(__name__) as a top-level statement, evaluated
   at load time. This returns the logger, which may not yet be configured.
   When the configuration file has been read, all registered loggers are
   initialized, and all subsequently registered loggers are initialized
   upon instantiation.

.. Copyright (c) 2016-2018 Richard Plevin
   See the https://opensource.org/licenses/MIT for license details.
"""
import os
import logging
from .newconfig import getParam, getParamAsBoolean, configLoaded

PKGNAME = __name__.split('.')[0]

_Loggers    = {}      # loggers created herein, keyed by module or package name
_LogLevels  = None    # log levels keyed by module or package name

_verbose    = False   # whether debug msgs should print

# Can't use this module to debug itself
def _debug(msg):
    if _verbose:
        print(msg)

# Note: 'traitlets' library uses root logger, which we don't want to enable here
def _createPkgLogger(dotspec):
    pkgName = dotspec.split('.')[0]

    if pkgName and pkgName not in _Loggers:
        _debug('_createPkgLogger("%s") from %s' % (pkgName, dotspec))
        logger = getLogger(pkgName)
        logger.propagate = False

def getLogger(name):
    '''
    Register a logger, which will be set up after the configuration
    file is read.

    :param name: the name of the logger, conventionally passed as __name__.
    :return: a logging logger instance
    '''
    _debug('getLogger("%s")' % name)

    try:
        logger = _Loggers[name]

    except KeyError:
        logger = logging.getLogger(name)
        logger.propagate = True             # set to False for explicitly named modules
        _Loggers[name] = logger

    _configureLogger(name)
    _createPkgLogger(name)

    return logger

def parseLevels(levelStr=None):
    """
    Get log levels for pathways as a whole or for indicated modules individually.
    Modules starting with a '.' are interpreted to be in pathways, i.e., ".config"
    is equivalent to "pathways.config".
    Example: LogLevel = WARNING, .tool:DEBUG, .utils:INFO, .mcs.util:INFO, my_plugin:DEBUG

    :param levelStr: a comma-delimited string of module:logLevel values. If
        no ':' is present, the value is treated as the default logLevel for pathways.
        If levelStr is None, the value of the variable 'LogLevel' is used.
    :return: (dict) of log levels, keyed by module names
    """
    def splitAndStrip(s, delim):
        items = map(str.strip, map(str, s.split(delim)))
        return items

    result = {}

    levelStr = levelStr or getParam('log_level')

    levels = splitAndStrip(levelStr, ',')
    for level in levels:
        if ':' in level:
            module, lvl = splitAndStrip(level, ':')
            # if '.' not in module or module[0] == '.':
            #     module = PKGNAME + '.' + (module[1:] if module[0] == '.' else module)
            if module[0] == '.':
                module = PKGNAME + module
        else:
            module = PKGNAME
            lvl = level.strip()

        result[module] = lvl.upper()

    return result

def _mkdirs(newdir, mode=0o770):
    """
    Try to create the full path `newdir` and ignore the error if it already exists.
    """
    from errno import EEXIST

    try:
        os.makedirs(newdir, mode)
    except OSError as e:
        if e.errno != EEXIST:
            raise

def _addHandler(logger, formatStr, logFile=None):
    if logFile:
        _mkdirs(os.path.dirname(logFile))

    handler = logging.FileHandler(logFile, mode='a') if logFile else logging.StreamHandler()
    handler.setFormatter(logging.Formatter(formatStr))
    logger.addHandler(handler)
    _debug("Added %s log handler for '%s'" % ('file' if logFile else 'console', logger.name))

def _configureLogger(name, force=False):
    try:
        logger = _Loggers[name]
    except KeyError:
        # add unknown logger names
        logger = getLogger(name)
        _debug("Added unknown logger name '%s'" % name)

    # If not forcing, skip loggers that already have handlers installed
    if not force and logger.handlers:
        return

    global _LogLevels
    if not _LogLevels:
        setLogLevels(getParam('log_level') or 'WARN')

    if name in _LogLevels:
        level = _LogLevels[name]
        _debug("Configuring %s, level=%s" % (name, level))
        logger.setLevel(level)
    else:
        parent = logger.parent
        # Handle case of user plugins, which aren't in the energyPATHWAYS
        # package but we'd like them to default to the 'pathways' loglevel
        if isinstance(parent, logging.RootLogger):
            parent = getLogger(PKGNAME)

        logger.setLevel(parent.level)

    logger.propagate = False

    # flush and remove all handlers
    for handler in logger.handlers:

        if not isinstance(handler, logging.NullHandler):
            handler.flush()
        logger.removeHandler(handler)

    logConsole = getParamAsBoolean('log_console')
    if logConsole:
        consoleFormat = getParam('log_console_format')
        _addHandler(logger, consoleFormat)

    logFile = getParam('log_file')
    if logFile:
        fileFormat = getParam('log_file_format')
        _addHandler(logger, fileFormat, logFile=logFile)

    if not logger.handlers:
        logger.addHandler(logger, logging.NullHandler())
        _debug("Added NullHandler to root logger")


def configureLogs(force=False):
    '''
    Do basicConfig setup and configure package loggers based on the information
    in the config instance given. Unless force == True, loggers with handlers will
    not be reconfigured.

    :param force: (bool) if True, reconfigure the logs even if already configured.
    :return: none
    '''
    if not configLoaded() or not _Loggers:
        return

    # First configure explicitly named modules
    explicit = _LogLevels.keys()
    for name in explicit:
        _configureLogger(name, force=force)

    # Next do all the implicit ones, setting their log levels
    # to their parent log levels and setting propagate to False.
    for name in _Loggers.keys():
        if name not in explicit:
            _configureLogger(name, force=force)

def setLogLevels(levelStr):
    '''
    Set the logging level string, which can define levels for packages and/or modules.
    Must call configureLogs(force=True) afterwards. Level string can be a single level,
    which is used as the default for all modules, or module-specific settings, e.g.,
    "WARNING, .tool:DEBUG, .utils:INFO, .mcs.util:INFO, my_plugin:DEBUG"

    :param levelStr: (str) comma-delimited module:LEVEL pairs, or just a single LEVEL
    :return: none
    '''
    global _LogLevels
    _LogLevels = parseLevels(levelStr)
