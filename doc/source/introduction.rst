============
Introduction
============

Purpose
=======

EnergyPATHWAYS is the offspring of an analytical approach that has already proven to be a successful strategy to dramatically change the climate policy discussion at the global, national, and subnational levels. The basic insight is that climate policy was stuck in the realm of short-term, incremental changes discussed in abstract and academic terms, and that this failure was reinforced by the analysis and modeling approaches used. The pathways strategy was to force the policy and business worlds to address, head on, the reality that achieving a 2°C limit requires transformation, not incrementalism; that only a long-term perspective on the kind of infrastructure and technology changes required can prevent short-term investments that result in high-emissions lock-in; and that only an analysis that moves past the abstract focus on tons of CO2 along an emissions trajectory to a focus on the energy supply and end use equipment that produces the CO2 would speak to practical decision-makers in the regulatory, business, and investment worlds.

The value of modeling 2050 and beyond is in building a cohesive, internally consistent story with the granularity to engage all parties involved in climate mitigation. Too often we jump straight to mechanisms for achieving climate mitigation (Ex. carbon price) without paying attention to what exactly these policies need to achieve. EnergyPATHWAYS is not a forecasting tool, but instead uses a backcasting approach--starting first with a goal and then working to show what physical infrastructure changes are required to reach that goal and when those changes must happen. This scenario approach allows the model to easily perform “what if” analysis and to reflect the underlying physics of our energy system with sufficient granularity for effective communication.

Background
==========

The earliest form of this model was an Excel tool developed to support the analysis of California’s Global Warming Solutions Act of 2006 (AB 32). Subsequent analyses for California and the U.S. required advances in modeling capabilities, resulting in later versions being developed in Analytica, and at the time named the PATHWAYS model. The desire to create a more flexible platform that could be used at multiple jurisdictional levels and in a variety of energy system contexts encouraged the development of a new platform, renamed EnergyPATHWAYS, that is written in Python with energy system data contained in a postgres database.

PATHWAYS was first developed by the San Francisco consulting company `Energy and Environmental Economics (E3)`_ with ongoing development and support for EnergyPATHWAYS provided by `Evolved Energy Research`_. To date, the work has been funded by private clients, California government, and the Deep Decarbonization Pathways Project (DDPP).

.. _Energy and Environmental Economics (E3): http://ethree.com
.. _Evolved Energy Research: http://evolved.energy

Modeling Approach
=================

Top-down versus Bottom-up
-------------------------

Whole economy energy models generally follow one of two types of modeling approaches: “top-down” or “bottom-up”. Top-down energy models focus on the macro-economy and balance supply and demand across all economic sectors. These models use a stylistic representation of technologies, which change over time due to elasticity (responsiveness to price) assumptions. By contrast, bottom-up energy models contain richer characterizations of technology cost and performance, and technology change depends on the availability and ability of technologies to substitute for each other. These engineering-economic models do not typically include a supply-demand feedback.

Among bottom-up models, the EnergyPATHWAYS can be further contrasted against sectoral models which take a detailed view of a slice of the energy economy (Ex. transportation or electricity). Instead, by modeling all of the energy economy, EnergyPATHWAYS makes it possible to show important dynamics between sectors in a deeply decarbonized energy system.

One approach is not necessarily superior to the other but depends on the type of research question being asked. But, we believe that bottom-up energy models, which track physical flows of energy and their infrastructure, are the best suited to answer the question “How do we deeply decarbonize the energy system?”

Exploration versus Optimization
-------------------------------

Many bottom-up energy models, such as the Energy Information Administration’s National Energy Modeling System (NEMS), are optimization-based. By contrast, energyPATHWAYS incorporates an advanced accounting framework that allows users to construct economy-wide energy infrastructure scenarios by specifying decisions along with other inputs. In other words, EnergyPATHWAYS is a scenario planning tool which allows users to “simulate” the consequences of specific decisions as energy infrastructure evolves over time. While portions of the model do use linear programming techniques (electricity dispatch), the model itself is not optimization-based and embeds few decision dynamics. We explain our rationale for this “exploration” approach below.

First, many real world energy infrastructure decisions amount to deciding between a limited set of scenarios constrained by factors not embedded in the modeling framework. Such scenarios, which may each be economically suboptimal, are difficult or impossible to represent in optimization-based models. On the other hand, EnergyPATHWAYS is designed to explicitly represent scenarios without having to work around the assumptions embedded in an optimization framework.

Second, since EnergyPATHWAYS is not an optimization, it can be designed to represent faithfully those dynamics in the energy economy that we believe to be critically important in decarbonized systems, but which optimization models aren’t able to capture. The best example is the interactions between the electricity system and the rest of the economy which we are able to represent using a time-sequential hourly dispatch. Modeling operations in the electricity system with this granularity as part of a larger problem on economy wide optimal investment is simply not feasible due to problem size. However, without full dynamics in the electricity system, phenomena such as the need for seasonal energy storage in high wind and solar scenarios can never be fully represented, and important energy system interactions are missed.

Finally, we believe that an enormous amount of the value from modeling deep decarbonization pathways comes from learning through experimenting, which is only possible when decisions are put in the hands of the modeler. It is a truism to say that all models are wrong. Economy-wide energy models are also complex, with energyPATHWAYS being no exception, and therefore become a black box to most users. Black box optimization models give a provisional “answer”, but make the underlying dynamics difficult to see, obscuring their most valuable insights. It is our hope that users find energyPATHWAYS to be a refreshingly transparent way of exploring deep decarbonization pathways, and that the model helps you uncover the breakthrough solutions our world needs.

What makes EnergyPATHWAYS different?
====================================

Electricity Sector
------------------

We developed EnergyPATHWAYS because we think that it extends our capability as modelers to answer questions that no other tool can. The most notable distinctions are in the electricity sector. Historically, electricity was treated very simply in many tools. Many of these models were first developed as a result of the oil crisis in the 70s and (1) detail in the electricity sector simply wasn’t relevant or (2) hardware limitations required tradeoffs and precluded detailed modeling because of electricity. Thus, we have economy wide energy models (as enumerated above) that treat electricity simplistically; and separately, we have detailed electricity sector models (see REEDS, PLEXOS, GRIDVIEW, SWITCH, etc.) with no endogenous treatment of energy demand. We think that EnergyPATHWAYS is the first platform to put these approaches together.

We believe this is critical because the electricity sector turns out to be paramount in deep decarbonization for two reasons: (1) Renewables are a leading source for carbon free electricity, but are intermittent and require special treatment and (2) Electrification of end uses that are currently point sources for emissions (Ex. cars, building heating, industrial processes) turns out to be a necessary decarbonization strategy when paired with high renewables, nuclear, or CCS in the electricity sector.

Output Granularity
------------------

Another feature that sets EnergyPATHWAYS apart is the level of granularity that can be achieved. Often, the granularity of research on emissions reductions in energy isn’t sufficient for a compelling positive story can be told. For technologists, annual market size and growth are necessary for true engagement. Sub-national governments want to see results that are geographically relevant for their constituents. And for the general public, service demand cost and lifestyle changes are the important metrics. EnergyPATHWAYS makes each of these outputs possible, which while not solely unique to this platform, has been prioritised to a greater extent in EnergyPATHWAYS than in other modeling platforms.

Model Features
==============

Data Flexibility

- Geography mapping functions allows for synthesis of disparate data sources
- Flexible indexing can support nested layers of data granularity
- Endogenous unit and currency conversion
- Time-series projections
- Multiple Approaches for Energy System Data Population (Ex. 5 options to populate a demand subsector depending on available data)

Comprehensive Accounting

- Calculates energy, cost, and emissions flows from primary supply all the way through final demand
- Calculates capital and infrastructure utilization for all supply subsectors
- Calculates levelized cost and annual investments
- Embodied energy calculations support lifecycle analysis and sophisticated cost allocation
- Direct emissions calculations locate physical emissions sources and sinks
- Framework can also be leveraged for air quality analyses

Hourly electricity dispatch

- Optimization algorithms for electric fuel production (hydrogen electrolysis and power-to-gas); short-duration energy storage, long-duration energy storage; flexible end-use loads

Energy system representation

- Flexible parameterization allows for upscaling and downscaling of represented energy systems
- Can support regional/national/state/municipal analyses
- Can support analyses with widely varying levels of data quality

IO Supply – Side Framework

- Resolves energy flow dependencies
- Allows for flexible configuration of supply-side representation
- U.S. energy supply system can be represented very differently than that of a city while utilizing the same framework
- Dynamic imports and export flows
- Intelligent geo-locating of energy infrastructure assets
- Supply curve functionality

How can I use energyPATHWAYS?
=============================

The core model will be open source in perpetuity while the representations of energy systems created with the model are the IP of those authors and should be contacted directly.

Right now the EnergyPATHWAYS project is still in development and user materials and documentation has lagged model features. Thus, use of the model is best done through direct interaction with Evolved Energy Research, though this should change over time as the user community grows and the documentation is developed.
