===============
Getting Started
===============

Overview
========

A working EnergyPATHWAYS installation consists of two main parts:

1. The EnergyPATHWAYS python code, and the libraries that it depends upon, which are described under `Dependencies`_ below.
2. Input data, consisting of a `Database`_ describing an energy system and a `Configuration File`_, also described below.

It is possible to use one installation of the python code to run multiple models (e.g. for different states or nations) by creating multiple sets of input data. That is, you will only need to set up part (1) once, and then you can set up part (2) for each energy system that you would like to model.

.. Important::
   To date, no energy system database for EnergyPATHAWAYS has been released publicly, and it is therefore not yet possible to run the model without support from Evolved Energy Research even though the model code is open source. Evolved Energy Research has developed a U.S. energy system database that is available commercially, and is working to develop a freely-available example database to aid users in developing their own energy system models for other regions, but this effort is still in progress. Please direct any inquiries about EnergyPATHWAYS and related databases to `info@evolved.energy`_.

.. _`info@evolved.energy`: mailto:info@evolved.energy

Obtaining EnergyPATHWAYS
========================

To begin, please clone EnergyPATHWAYS from its `GitHub repository`_. If you are unfamiliar with cloning a repository, please see `GitHub's documentation`_ on this topic.

.. _`GitHub repository`: https://github.com/energyPATHWAYS/energyPATHWAYS
.. _`GitHub's documentation`: https://help.github.com/articles/cloning-a-repository/

Dependencies
============

We have now cloned the EnergyPATHWAYS code, but before completing the installation we need to set up an environment containing a Python interpreter and a number of supporting libraries.

.. Note::
   EnergyPATHWAYS requires Python 2.7 to ensure compatibility with certain libraries that have not yet been ported to Python 3. The instructions below will provide you with a python 2.7 environment.

Packages
--------

We recommend setting up your environment for EnergyPATHWAYS using Anaconda, which is both a package manager and a virtual environment manager. To set up the virtual environment, first `download`_ and install Anaconda, open a command prompt and ``cd`` to the directory where you have cloned the EnergyPATHWAYS repository. If you are working on a windows PC enter::

  $ conda env create --name pathways -f environment_pc.yml

Or on a mac enter::

  $ conda env create --name pathways -f environment_mac.yml

(You are, of course, welcome to choose a name other than "pathways" for the environment if you prefer.) This only needs to be done once. Then, in the future, whenever you would like to run EnergyPATHWAYS, first activate the environment you just created by running::

   $ source activate pathways

.. _download: https://www.continuum.io/downloads

Note that you are not required to use Anaconda; you may use any method you like to create a Python environment with the packages from the environment file (``environment_pc.yml`` or ``environment_mac.yml``) installed. However, we have found Anaconda to be the most reliable way to do this across different platforms. In case you do decide to set up your own environment in a different way, please use the package versions specified in the appropriate environment file, and please especially be aware of the following warnings.

.. Warning::
   There is a `known bug`_ in numexpr 2.4.4 that will intermittently lead to incorrect calculations in EnergyPATHWAYS. numexpr is not required for running EnergyPATHWAYS, but is often installed alongside (and automatically used by) NumPy, e.g. in the Anaconda default environment. If you do have numexpr installed, please ensure that you have a version newer (or older) than 2.4.4 before using EnergyPATHWAYS.

.. Warning::
   Issues have been experienced with pandas versions greater than 0.17.1. it is recommended that users run the model with version 0.17.1, as specified in the environment files.

.. _`known bug`: https://github.com/pydata/numexpr/issues/185

Solver
------

The EnergyPATHWAYS electric system dispatch requires an optimization solver that is supported by the pyomo package. If you already have a commercial solver such as CPLEX or Gurobi installed you are welcome to use that, otherwise we recommend `Cbc`_ which is open source and freely downloadable. Cbc appears to be slightly faster than `GLPK`_ at solving the EnergyPATHWAYS dispatch, but GLPK can be used if Cbc is unavailable for some reason.

.. _`Cbc`: https://projects.coin-or.org/Cbc
.. _`GLPK`: https://www.gnu.org/software/glpk/

To install Cbc, see the official `download and install instructions`_. Note that as of this writing, there is no macOS homebrew formula for Cbc, so downloading the macOS binary from the AMPL page linked to from those instructions is the easiest way to get Cbc on a Mac; you will need to move the downloaded ``cbc`` binary to somewhere that is referenced in your environment path, e.g. the ``bin/`` directory under your Anaconda environment directory (which you can find using ``conda env list``), or ``/usr/bin`` if you would like it to be available beyond your conda environment.

.. _`download and install instructions`: https://projects.coin-or.org/Cbc#DownloadandInstall

.. Note::
   On Windows, our experience is that the path to Cbc or GLPK must be `added to your system path manually`_.

.. _`added to your system path manually`: https://www.howtogeek.com/118594/how-to-edit-your-system-path-for-easy-command-line-access/

Once you have a solver in your system path, EnergyPATHWAYS should detect and use it automatically. If you would like to customize the list of solvers that energyPATHAWAYS searches for, see the ``dispatch_solver`` option in the example ``config.INI`` file discussed below.

Installation
============

Once the dependencies are installed, EnergyPATHWAYS can be installed using Python's setuptools. Don't forget to activate your virtual environment in the current session if you haven't already::

    $ source activate pathways

Then from the root directory of your cloned repository (e.g. ``energyPATHWAYS/``)::

    $ python setup.py develop

EnergyPATHWAYS is now installed!

.. Note::
   Setuptools will attempt to install any required packages that are not in your environment when you run ``setup.py``. However, we have found that this method does not reliably install all dependencies on all platforms. For example, users have encountered difficulty installing NumPy and SciPy on macOS this way. This is why we recommend using Anaconda to set up the environment before installing EnergyPATHWAYS, as described under `Packages`_, above.

Data Setup
==========

In addition to installation of the EnergyPATHWAYS package described above, a model cannot be run until input data are provided. The input data consist of two components:

1. A database describing your energy system
2. A configuration file (e.g. ``energyPATHWAYS/model\_runs/us\_model\_example/config.INI``)

These are described in the following subsections.

Database
--------

Pathways currently requires access to an energy system database in a particular format, stored in `PostgreSQL`_. Future versions of EnergyPATHWAYS may support a wider variety of databases and/or input formats. If you are unfamiliar with PostgreSQL, we recommend installing it in the following ways:

.. _PostgreSQL: http://www.postgresql.org/

- Windows: `installers`_
- Mac OS X: `Postgres.app`_
- Linux: your preferred package manager (e.g. apt)

.. _installers: http://www.postgresql.org/download/windows/
.. _Postgres.app: http://postgresapp.com/

As of this writing, EnergyPATHWAYS is being developed and tested against PostgreSQL 9.5.1, but this is subject to change.

As noted in the `Overview`_, you will need to contact Evolved Energy Research to obtain an EnergyPATHWAYS database dump for the nation or state you are interested in. Once you have your PostgreSQL server up and running, we recommend that you place the database dump file in a directory under ``energyPATHWAYS/model_runs`` named after the region you are modeling; for instance, for the U.S. you might save your database dump in ``energyPATHWAYS/model_runs/us_model_example/pathways_us.sql``. Then, using the command line postgres client, you can issue the following commands from the ``energyPATHWAYS/model_runs/us_model_example/`` directory.

.. code:: bash

   $ createdb pathways_us
   $ psql pathways < pathways_us.sql

If you attempt to run these commands and see error messages containing the phrase, ``FATAL:  role "[your username]" does not exist``, this means that postgres does not have a user matching your username. If you are experienced with postgres you may wish to create a user matching your username, but if you are just getting started and not using your postgres database for public-facing purposes, it should be fine just to use the postgres "root" user, which is usually named "postgres". In that case, you can re-enter the commands as follows:

.. code:: bash

   $ createdb -U postgres pathways_us
   $ psql -U postgres pathways < pathways_us.sql

Please note that EnergyPATHWAYS is under development and the database structure is subject to change; if you update to a new version of the code, you may need to update your database as well. Please contact `info@evolved.energy`_ if you have questions or need help with this.

Configuration File
------------------

Finally, in order to run the model you will need to edit the configuration file to reflect the settings you would like to use. Assuming that you are running in the ``us_model_example`` directory, you can open up ``energyPATHWAYS/model_runs/us_model_example/config.INI`` in your favorite text editor.

The most important settings that nearly everyone will need to change are in the ``[database]`` section at the top. These settings tell EnergyPATHWAYS where to find your database and how to connect to it. Update these settings as follows:

  ``pg_host``
    Leave this as "localhost" unless your PostgreSQL server is on a different computer than your Python code, in which case you will need to specify the network address of the database server.

  ``pg_user``
    This will be the username you put after ``-U`` when you ran the ``createdb`` and ``psql`` commands above. If you were able to run the commands without the ``-U``, then this will just be your operating system username.

  ``pg_password``
    The password for the user above. If the user has no password, just leave this line blank after the ``pg_password:``.

  ``pg_database``
    The name of the database you created with ``createdb`` above, e.g. "pathways_us".

You may wish to change other configuration settings, particularly if you are using a model other than the U.S. model. The settings are briefly documented by comments within the example config.INI. If you have questions not answered by those comments, please contact `info@evolved.energy`_.

Running the Model
=================

After installing EnergyPATHWAYS and setting up the necessary input data, the model can be run from the command line::

    $ energyPATHWAYS [options]

To get help on the various command line options, use::

    $ energyPATHWAYS --help

As mentioned above, EnergyPATHWAYS will need access to your configuration file in order to load your database and begin running. By default, EnergyPATHWAYS will assume that the configuration file is called ``config.INI`` and is located in the current directory. If you need to change these assumptions, you can use the ``-c`` and/or ``-p`` command line options, as described in the ``energyPATHWAYS --help`` text.

In most cases, you will at a minimum need to tell EnergyPATHWAYS which scenario to run from the database by using the ``-s`` option to specify its id number. So, for instance, the basic usage to run scenario number 1 would be::

    $ energyPATHWAYS -s 1

Running Unit Tests
==================

.. Warning::
   EnergyPATHWAYS unit tests are currently a work in progress. If you run them you will certainly see failures and errors; these are not indicative of problems with functionality, simply of an unfinished test suite.

The EnergyPATHWAYS unit tests are located in `energyPATHWAYS/tests`. To run all available tests, cd to that directory and enter::

    $ python -m unittest discover

To run one particular file of unit tests, use the same command but substitute the name of the file for "discover" above. However, you must leave the ".py" out of the filename since you are actually naming the python module, not the file. E.g.::

    $ python -m unittest test_df_operation

If you are debugging something and would like to run just a single test to save time, you can use the path to the test method from the module instead of the whole module, e.g.::

    $ python -m unittest test_df_operation.TestDfOperation.test_basic_add
