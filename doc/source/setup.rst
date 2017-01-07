===============
Getting Started
===============

Dependencies
============

EnergyPATHWAYS requires Python 2.7 to ensure compatibility with certain libraries that have not yet been ported to Python 3.

Packages
--------

EnergyPATHWAYS will attempt to install any necessary packages that are not in your environment when you run ``setup.py`` (see below). However, we have found that the script is not always successful installing all dependencies on all platforms (for example, users have encountered difficulty installing NumPy and SciPy on OS X this way). Therefore we recommend that you install the packages using a manager such as `Anaconda`_ or ``pip`` instead. EnergyPATHWAYS has been developed primarily within Anaconda and the default Anaconda environment provides many of the necessary packages. If you wish to install the dependencies in a different way, please see the ``install_requires`` list in ``setup.py`` for an up to date list.

.. _Anaconda: https://www.continuum.io/downloads

.. Warning::
   There is a `known bug`_ in numexpr 2.4.4 that will intermittently lead to incorrect calculations in EnergyPATHWAYS. numexpr is not required for running EnergyPATHWAYS, but is often installed alongside (and automatically used by) NumPy, e.g. in the Anaconda default environment. If you do have numexpr installed, please ensure that you have a version newer (or older) than 2.4.4 before using EnergyPATHWAYS.

.. Warning::
   Issues have been experienced with pandas version 0.18.0 and 0.18.1. it is recommended that users run the model with version 0.17.1

.. _`known bug`: https://github.com/pydata/numexpr/issues/185

Solver
------

The EnergyPATHWAYS electric system dispatch requires an optimization solver that is supported by the pyomo package. If you already have a commercial solver such as CPLEX or Gurobi installed you are welcome to use that, otherwise we recommend `Cbc`_ which is open source and freely downloadable. Cbc appears to be slightly faster than GLPK at solving the EnergyPATHWAYS dispatch.

.. _`Cbc`: https://projects.coin-or.org/Cbc

To install Cbc, see the official `download and install instructions`_. Note that as of this writing, there is no OS X homebrew formula for Cbc, so downloading the OS X binary from the AMPL page linked to from those instructions is the easiest way to get Cbc on a Mac; you will need to move the downloaded ``cbc`` binary to somewhere that is referenced in your environment path (e.g. your Anaconda environment directory, or ``/usr/bin``, etc.).

.. _`download and install instructions`: https://projects.coin-or.org/Cbc#DownloadandInstall

Our experience with COIN or GLPK is that each must be added to the system path manually on a PC. For instructions on how to add the solvers to your system path, Google “adding a new application to system path windows” or similar and follow the instructions for your version of Windows.

Once you have a solver in your system path, EnergyPATHWAYS should detect and use it automatically. If you would like to customize the list of solvers that energyPATHAWAYS searches for, see the ``dispatch_solver`` option in the example configurations.INI file discussed below.

Installation
============

EnergyPATHWAYS can be installed using distutils::

    $ python setup.py develop

In addition to installation of the EnergyPATHWAYS package, a model cannot be created until a set of data is supplied. The input data contain three components:

- A database describing your energy system (see below)
- Configuration file (e.g. EnergyPATHWAYS/us\_model\_example/configurations.INI)
- Custom unit definitions (e.g. EnergyPATHWAYS/us\_model\_example/unit_defs.txt)

Database Setup
==============

Pathways currently requires access to an energy system database in a particular format, stored in `PostgreSQL`_. (As noted in ``setup.py``, the psycopg2 package is therefore also required so that python can connect to PostgreSQL.) Future versions of EnergyPATHWAYS may support a wider variety of databases and/or input formats. If you are unfamiliar with PostgreSQL, we recommend installing it in the following ways:

.. _PostgreSQL: http://www.postgresql.org/

- Windows: `installers`_
- Mac OS X: `Postgres.app`_
- Linux: your preferred package manager (e.g. apt)

.. _installers: http://www.postgresql.org/download/windows/
.. _Postgres.app: http://postgresapp.com/

As of this writing, EnergyPATHWAYS is being developed and tested against PostgreSQL 9.5.1, but this is subject to change.

Once you have your PostgreSQL server up and running, you can load the EnergyPATHWAYS U.S. example model from ``energyPATHWAYS/us_model_example/pathways_us.sql``. Using the command line client, you can issue the following commands from the ``energyPATHWAYS/us_model_example/`` directory. Depending on how your PostgreSQL installation is set up, you may need to provide a username to these commands using the ``-U`` option.

.. code:: bash

   $ createdb pathways
   $ psql pathways < pathways_us.sql

You will then need to edit the database connection parameters at the top of ``energyPATHWAYS/us_model_example/configurations.INI`` so that EnergyPATHWAYS can find your database. Please note that EnergyPATHWAYS is under development and the database structure is subject to change; if you update to a new version of the code, you may need to update your database as well. Presently this requires either starting over with a new U.S. example database, or using git to examine the changes in the ``pathways_us.sql`` file and applying them manually to your database. We are investigating ways to make this process easier.

Also note that the U.S. database for EnergyPATHWAYS developed by Evolved Energy Research is not publicly posted. Inquiries should be directed to `info@evolved.energy`_.

.. _`info@evolved.energy`: mailto:info@evolved.energy

Running the Model
=================

After installing EnergyPATHWAYS, it can be run from the command line::

    $ EnergyPATHWAYS [options]

It is necessary to point EnergyPATHWAYS to a configuration file in the run directory. This file, among general model setup, points the model the the correct database. An example (config.INI) is found in the ``us_model_example`` folder.
