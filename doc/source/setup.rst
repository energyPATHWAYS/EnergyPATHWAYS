===============
Getting Started
===============

Dependencies
============

EnergyPATHWAYS requires Python 2.7 to ensure compatibility with certain libraries that have not yet been ported to Python 3.

Packages
--------

We recommend setting up your environment for EnergyPATHWAYS using Anaconda, which is both a package manager and a virtual environment manager. To set up the virtual environment, first `download`_ and install Anaconda, open a command prompt and ``cd`` to the directory where you have cloned the EnergyPATHWAYS repository, and enter::

  $ conda env create --name pathways -f environment.yml

(You are, of course, welcome to choose a name other than "pathways" for the environment if you prefer.) This only needs to be done once. Then, in the future, whenever you would like to run energyPATHWAYS, first activate the environment you just created by running::

   $ source activate pathways

.. _download: https://www.continuum.io/downloads

Note that you are not required to use Anaconda; you may use any method you like to create a Python environment with the packages from ``environment.yml`` installed. However, we have found Anaconda to be the most reliable way to do this across different platforms. In case you do decide to set up your own environment in a different way, please use the package versions specified in ``environment.yml``, and please especially be aware of the following warnings.

.. Warning::
   There is a `known bug`_ in numexpr 2.4.4 that will intermittently lead to incorrect calculations in EnergyPATHWAYS. numexpr is not required for running EnergyPATHWAYS, but is often installed alongside (and automatically used by) NumPy, e.g. in the Anaconda default environment. If you do have numexpr installed, please ensure that you have a version newer (or older) than 2.4.4 before using EnergyPATHWAYS.

.. Warning::
   Issues have been experienced with pandas version 0.18.0 and 0.18.1. it is recommended that users run the model with version 0.17.1

.. _`known bug`: https://github.com/pydata/numexpr/issues/185

Solver
------

The EnergyPATHWAYS electric system dispatch requires an optimization solver that is supported by the pyomo package. If you already have a commercial solver such as CPLEX or Gurobi installed you are welcome to use that, otherwise we recommend `Cbc`_ which is open source and freely downloadable. Cbc appears to be slightly faster than `GLPK`_ at solving the EnergyPATHWAYS dispatch, but GLPK can be used if Cbc is unavailable for some reason.

.. _`Cbc`: https://projects.coin-or.org/Cbc
.. _`GLPK`: https://www.gnu.org/software/glpk/

To install Cbc, see the official `download and install instructions`_. Note that as of this writing, there is no macOS homebrew formula for Cbc, so downloading the macOS binary from the AMPL page linked to from those instructions is the easiest way to get Cbc on a Mac; you will need to move the downloaded ``cbc`` binary to somewhere that is referenced in your environment path, e.g. the ``bin/`` directory under your Anaconda environment directory (which you can find using ``conda env list``), or ``/usr/bin`` if you would like it to be available beyond your conda environment.

.. _`download and install instructions`: https://projects.coin-or.org/Cbc#DownloadandInstall

Our experience with Cbc or GLPK is that each must be added to the system path manually on a Windows PC. For instructions on how to add the solvers to your system path, Google “adding a new application to system path windows” or similar and follow the instructions for your version of Windows.

Once you have a solver in your system path, EnergyPATHWAYS should detect and use it automatically. If you would like to customize the list of solvers that energyPATHAWAYS searches for, see the ``dispatch_solver`` option in the example ``config.INI`` file discussed below.

Installation
============

Once the dependencies are installed, EnergyPATHWAYS can be installed using python's setuptools. Don't forget to activate your virtual environment in the current session if you haven't already::

    $ source activate pathways

Then from the root directory of your cloned repository::

    $ python setup.py develop

EnergyPATHWAYS is now installed!

.. Note::
   Setuptools will attempt to install any required packages that are not in your environment when you run ``setup.py``. However, we have found that this method does not reliably install all dependencies on all platforms. For example, users have encountered difficulty installing NumPy and SciPy on macOS this way. This is why we recommend using Anaconda to set up the environment before installing EnergyPATHWAYS, as described under `Packages`_, above.

In addition to installation of the EnergyPATHWAYS package, a model cannot be created until a set of data is supplied. The input data contain two components:

- A database describing your energy system (see below)
- Configuration file (e.g. EnergyPATHWAYS/model runs/us\_model\_example/config.INI)

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

Once you have your PostgreSQL server up and running, we recommend that you place the EnergyPATHWAYS U.S. example model .sql file at ``us_model_example/pathways_us.sql``. Then, using the command line client, you can issue the following commands from the ``energyPATHWAYS/model runs/us_model_example/`` directory. Depending on how your PostgreSQL installation is set up, you may need to provide a username to these commands using the ``-U`` option.

.. code:: bash

   $ createdb pathways
   $ psql pathways < pathways_us.sql

You will then need to edit the database connection parameters at the top of ``energyPATHWAYS/us_model_example/configurations.INI`` so that EnergyPATHWAYS can find your database. Please note that EnergyPATHWAYS is under development and the database structure is subject to change; if you update to a new version of the code, you may need to update your database as well. Presently this requires either starting over with a new U.S. example database, or using a "diff" tool to examine the changes in the ``pathways_us.sql`` file and applying them manually to your database. We are investigating ways to make this process easier.

.. Note::
   The U.S. database for EnergyPATHWAYS developed by Evolved Energy Research is not publicly posted. Inquiries should be directed to `info@evolved.energy`_.

.. _`info@evolved.energy`: mailto:info@evolved.energy

Running the Model
=================

After installing EnergyPATHWAYS, it can be run from the command line::

    $ energyPATHWAYS [options]

It is necessary to point EnergyPATHWAYS to a configuration file in the run directory. This file, along with general model setup, points the model the the correct database. An example (config.INI) is found in the ``us_model_example`` folder.
