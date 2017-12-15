To understand how the config system is intended to work, I recommend reviewing
the documentation for pygcam's config system, from which this is derived. See
http://pygcam.readthedocs.io/en/master/config.html

General principles
------------------

1. A user has a single pathways config file that potentially has configuration
   info for multiple projects.

2. The config is stored in the user's home directory and need only contain the
   changes the user wishes to make from default values. A user can have a
   distinct config file on different systems, e.g., on a desktop and cluster,
   with pathnames and other settings appropriate to each environment.

3. Shared settings (if needed) can be stored in a "site" config file. This may
   not be relevant for PATHWAYS, but there was no reason to remove the capability.

4. There are also platform-specific files that can contain settings that differ
   by platform. These are stored in Windows.ini, Darwin.ini (for Mac), and Linux.ini,
   all in the energyPATHWAYS/etc directory. For now, these are all empty apart from
   a comment. Again, this may not be needed here, but the capability existed in
   pygcam and there's no reason to remove it. Might come in handy.

5. All settings in system.ini, site.ini, {Platform}.ini should be made in the
   [DEFAULT] section only, leaving other section names available for specific
   projects to modify specific config variables while inheriting all defaults.

6. Whenever a config parameter is added to the code, the variable must be added
   added to system.ini, ensuring that no variable is undefined. Whenever possible,
   a reasonable default should be specified.


Steps for converting to the new config system
---------------------------------------------

1. Ensure that all parameters are defined in system.ini
2. Ensure that all parameters have unique names
3. Create ~/pathways.ini for testing
4. Replace all calls like

        cfg.cfgfile.get(section, varname)

   to
        getParam(varname) # substituting new unique name if needed

5. Replace calls to cfg.cfgfile.get wrapped in calls to int, float, or bool
   with calls to getParamAsInt, getParamAsFloat, or getParamAsBoolean.

6. Replace calls to cfgfile.set(section, varname, value) with calls to
   setParam(varname, value)

7. Add click option for project to operate on, overriding "default_project",
   and remove the option to set the path the config file.


Example user config file
------------------------

A user config file might be something like this:


 [DEFAULT]
 # Values that the user wants to apply to all (or most) projects

 default_project: us

 log_level: info
 log_console_format: %%(name)s: %%(message)s

 dispatch_solver: my_special_solver


 [us]
 # Settings for the "us" project
 log_level: warn; .database:info, .demand:debug


 [mexico]
 # Settings for the "mexico" project
 log_level: info, .supply:debug, .run:debug

 database_dir: F:\some\network\location
 database_name: mx_energypathways_db

 primary_geography: mexico

 calculation_energy_unit: EJ

 inflation_rate: 0.03




