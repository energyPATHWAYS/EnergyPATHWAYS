# energyPATHWAYS

EnergyPATHWAYS model is a professional, open-source energy and carbon planning tool for use in evaluating long-term, economy-wide greenhouse gas mitigation scenarios.

## Getting Started

### Dependencies

EnergyPATHWAYS requires Python 2.7 to ensure compatibility with certain libraries that have not yet been ported to Python 3.

#### Packages

EnergyPATHWAYS will attempt to install any necessary packages that are not in your environment when you run `setup.py` (see below). However, we have found that the script is not always successful installing all dependencies on all platforms (for example, users have encountered difficulty installing NumPy and SciPy on OS X this way). Therefore we recommend that you install the packages using a manager such as [Anaconda](https://www.continuum.io/downloads) or `pip` instead. EnergyPATHWAYS has been developed primarily within Anaconda and the default Anaconda environment provides many of the necessary packages. If you wish to install the dependencies in a different way, please see the `install_requires` list in `setup.py` for an up to date list.

**_Warning_**: there is a [known bug](https://github.com/pydata/numexpr/issues/185) in numexpr 2.4.4 that will intermittently lead to incorrect calculations in energyPATHWAYS. numexpr is not required for running energyPATHWAYS, but is often installed alongside (and automatically used by) NumPy, e.g. in the Anaconda default environment. If you do have numexpr installed, please ensure that you have a version newer (or older) than 2.4.4 before using energyPATHWAYS.

#### Solver

The energyPATHWAYS electric system dispatch requires an optimization solver that is supported by the pyomo package. If you already have a commercial solver such as CPLEX or Gurobi installed you are welcome to use that, otherwise we recommend either [Cbc](https://projects.coin-or.org/Cbc) or [GLPK](https://www.gnu.org/software/glpk/), which are both open source and freely downloadable. Cbc appears to be slightly faster than GLPK at solving the energyPATHWAYS dispatch. 

To install Cbc, see the official [download and install instructions](https://projects.coin-or.org/Cbc#DownloadandInstall). Note that as of this writing, there is no OS X homebrew formula for Cbc, so downloading the OS X binary from the AMPL page linked to from those instructions is the easiest way to get Cbc on a Mac; you will need to move the downloaded `cbc` binary to somewhere that is referenced in your environment path (e.g. your Anaconda environment directory, or `/usr/bin`, etc.).

To install GLPK on Windows, see [these instructions](https://en.wikibooks.org/wiki/GLPK/Windows_executables). Note that "the archive from Sourceforge" referred to can be found at the [winglpk Sourceforge site](https://sourceforge.net/projects/winglpk/); use the green "download" button to get the latest version. OS X and Linux users will likely find it easiest to install GLPK using a package manager. On OS X you can use [macports](https://www.macports.org/) (run `port install glpk` after installing macports) or [homebrew](http://brew.sh/) (`brew install homebrew/science/glpk`). On Linux you can [use your usual package manager](https://en.wikibooks.org/wiki/GLPK/Linux_packages).

Our experience with COIN or GLPK is that each must be added to the system path manually on a PC. For instructions on how to add the solvers to your system path, Google “adding a new application to system path windows” or similar and follow the instructions for your version of Windows.

Once you have a solver in your system path, energyPATHWAYS should detect and use it automatically. If you would like to customize the list of solvers that energyPATHAWAYS searches for, see the `dispatch_solver` option in the example configurations.INI file discussed below.

### Installation

energyPATHWAYS can be installed using distutils

`` $ python setup.py develop``

In addition to installation of the energyPATHWAYS package, a model cannot be created until a set of data is supplied. The input data contain three components:

- A sqlite database populating your energy system ([download](https://www.dropbox.com/s/1gyin06dmwn0ww8/pathways.db?dl=0) the U.S. DDPP team's database)
- Configuration file (e.g. energyPATHWAYS/us\_model\_example/configurations.INI)
- Custom unit definitions (e.g. energyPATHWAYS/us\_model\_example/unit_defs.txt)

Also located inside of the us\_model\_example folder is a script (main.py) that shows how a pathways model can be created and executed; after running the script, look in the output/ subdirectory for your results (it will be created if it doesn't exist). This documentation will become more developed over time as the energyPATHWAYS tool grows and the user community expands.


## Background

Energy and Environmental Economics, Inc. first constructed PATHWAYS models to support long-term energy transformation analysis in both the U.S. and California

- This was originally an Excel platform
- Later versions required more advanced software (Analytica)
- Finally, the desire to create a more flexible platform that could be used at multiple jurisdiction levels and in a variety of energy system contexts encouraged the development of the new EnergyPATHWAYS platform in Python

This is the offline developer version of the energyPATHWAYS model. An online version is under development and anticipated spring, 2016.
The online version will increase model ease of use by:
- Improving data entry
- Allowing for easy team-based model development
- Leveraging data as part of a larger deep decarbonization sharing platform (technology, macroeconomic drivers, etc.)


## energyPATHWAYS Model Features

**Data Flexibility**

- Geography mapping functions allows for synthesis of disparate data sources
- Flexible indexing can support nested layers of data granularity
- Endogenous unit and currency conversion
- Time-series projections
- Multiple Approaches for Energy System Data Population (Ex. 5 options to populate a demand subsector depending on available data)

**Comprehensive Accounting**

- Calculates energy, cost, and emissions flows from primary supply all the way through final demand
- Calculates capital and infrastructure utilization for all supply subsectors
- Calculates levelized cost and annual investments
- Embodied energy calculations support lifecycle analysis and sophisticated cost allocation
- Direct emissions calculations locate physical emissions sources and sinks
- Framework can also be leveraged for air quality analyses

**Hourly electricity dispatch**

- Optimization algorithms for electric fuel production (hydrogen electrolysis and power-to-gas); short-duration energy storage, long-duration energy storage; flexible end-use loads

**Energy system representation**

- Flexible parameterization allows for upscaling and downscaling of represented energy systems
- Can support regional/national/state/municipal analyses
- Can support analyses with widely varying levels of data quality

**IO Supply –Side Framework**

- Resolves energy flow dependencies
- Allows for flexible configuration of supply-side representation 
- U.S. energy supply system can be represented very differently than that of a city while utilizing the same framework
- Dynamic imports and export flows
- Intelligent geo-locating of energy infrastructure assets
- Supply curve functionality


## The energyPATHWAYS Approach: Exploration Versus Optimization

EnergyPATHWAYS is a bottom-up energy model that takes a unique view on the value provided by economy-wide models and how best to design one. Fundamentally energyPATHWAYS is an advanced accounting framework that allows a professional user to construct economy-wide energy infrastructure scenarios. As such, while portions of the model do use linear programming techniques (e.g. electricity dispatch), the energyPATHWAYS tool itself is not an optimization and embeds few decision dynamics. We have made this decision explicitly and view it as a feature for several reasons.

First, many real world energy infrastructure decisions amount to deciding between a limited set of scenarios that are economically suboptimal and politically constrained. Many economy-wide energy models that use optimization are forced to jump through hoops, for example by adding constraints or by tweaking prices, to try to reflect the scenarios in play. EnergyPATHWAYS, on the other hand, is able to more accurately represent any scenario without having to work around the assumptions embedded in an optimization framework.

Second, as energyPATHWAYS is not an optimization it can be designed to represent faithfully those dynamics in the energy economy that we believe to be critically important in decarbonized systems, but which optimization models aren’t able to capture. The best example is the interactions between the electricity system and the rest of the economy which we are able to represent using annual 8760 hour dispatch. Modeling operations in the electricity system with this granularity as part of a larger problem on economy wide optimal investment is simply not feasible due to problem size. However, without full dynamics in the electricity system, phenomena such as the need for seasonal energy storage in high wind and solar scenarios can never be fully represented, and important energy system interactions are missed.

Finally, we believe that an enormous amount of the value from modeling deep decarbonization pathways comes from learning through experimenting, which is only possible when decisions are put in the hands of the modeler. Almost all models are wrong; and models that project multiple decades into the future often comically so. True economy-wide energy models are also complex, with energyPATHWAYS being no exception, and therefore become a black box to most users. Black box optimization models give a provisional “answer”, but make the underlying dynamics difficult to see, which can obscure their most valuable insights. It is our hope that users find energyPATHWAYS to be a refreshingly transparent way of exploring deep decarbonization pathways, and that it helps you to uncover the breakthrough solutions our world needs.


## License
EnergyPathways is released under the MIT License (MIT). See the LICENSE file for further details.
