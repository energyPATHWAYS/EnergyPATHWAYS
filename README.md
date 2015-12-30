# energyPATHWAYS
EnergyPATHWAYS model is a professional, open-source energy and carbon planning tool for use in evaluating long-term, economy-wide greenhouse gas mitigation scenarios.


## Getting Started

energyPATHWAYS can be installed using distutils

`` $ python setup.py develop``

In addition to installation of the energyPATHWAYS package, a model cannot be created until a set of data is supplied. The input data contains three components:
1. A sqlite database populating your energy system (download the U.S. DDPP team's database here <https://www.dropbox.com/s/ow64ghp1cpjujmi/pathways.db?dl=0>)
2. Configuration file (an example is given in energyPATHWAYS/us_model_example)
3. Custom unit definitions (an example is given in energyPATHWAYS/us_model_example)

Also located inside of the us_model_example folder is a script that shows how a pathways model can be made and executed. This documentation will become more developed over time as the energyPATHWAYS tool grows and the user community expands.


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
- Direct emissions calculate locate physical emissions sources and sinks
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
- U.S. energy supply system can be represented very differently than that of a city while allowing the same framework
- Dynamic imports and export flows
- Intelligent geo-locating of energy infrastructure assets
- Supply curve functionality


## Treatise on the energyPATHWAYS Model Approach

This model is a bottom up energy model that takes a unique view on how economy-wide energy models are most useful and how best to design one. Fundamentally energyPATHWAYS is an advanced accounting framework that allows a professional user to construct economy-wide energy infrastructure scenarios. As such, while portions of the model do use linear programming techniques (electricity dispatch), the energyPATHWAYS tool itself is not an optimization and embeds few decision dynamics. This decision has been explicitly made and we view it as a feature for several reasons.

First, most real world energy infrastructure decisions amount to deciding between a limited set of scenarios that are often economically suboptimal and in many cases political. Many economy-wide energy models that use optimization are forced to jump through hoops, for example by adding constraints or by tweaking prices, to try to reflect the scenarios in play. EnergyPATHWAYS, on the other hand, is able to more accurately represent any scenario with ease without having to put the cart before the horse.

Second, as energyPATHWAYS is not an optimization it can be designed to represent faithfully those dynamics in the energy economy, which we believe to be critically important in decarbonized systems, but which optimization models aren’t able to capture. The best example is the interactions between the electricity system and the rest of the economy which we are able to represent using annual 8760 dispatch. Modeling operations in the electricity system with this granularity as part of a larger problem on economy wide optimal investment is simply not possible due to problem size. However, without full dynamics in the electricity system phenomena, such as the need for seasonal energy storage in high wind and solar scenarios, can never be fully represented and important energy system interactions are missed.

Finally, we believe that an enormous amount of the value from modeling deep decarbonization pathways comes from learning through experimenting, which is only possible when decisions are put in the hands of the modeler. Almost all models are wrong; and models that project multiple decades into the future often comically so. True economy wide energy models are also complex, with energyPATHWAYS being no exception, and therefore become a black box to most users. A black box optimization model gives an “answer”, which we know is likely wrong, but makes the underlying dynamics difficult to parse, which would actually be the most valuable result. It is our hope that users find energyPATHWAYS more useful in this endeavor of exploring deep decarbonization pathways to discovering the breakthrough solutions our world needs.