====================
User Guide
====================

.. _scenarios:

Measures & Scenarios
====================

EnergyPATHWAYS operates at its simplest on the level of measures and scenarios. Scenarios are an aggregation of measures, defined here as actions undertaken to change the energy system from a business-as-usual projection.

Demand-Side Measures
--------------------

On the demand side, we employ the following six types of measures:

   **Sales Share Measures** (database table: ``DemandSalesShareMeasures``)
      These measures change the deployment of technologies using the concept of sales shares. If we wanted to change the penetration of electric vehicles (EVs) into the market, we could develop a measure that creates any level of adoption we want.  These measures can be used in any subsectors with technology-level stock representation.

   **Stock Measures** (database table: ``DemandStockMeasures``)
      These measure also change the deployment of technologies using the concept of stock instead of sales. While equipment sales are the equipment put into service in a specific year and thus of a certain vintage, equipment stock are all stocks that are operating in a certain year of a variety of vintages. If we want to say that the sum of all EVs on the road in 2030 will equal 1.5 million, we would do so with a stock measure. These measures can be used in any subsectors with technology-level stock representation.

   **Service Demand Measures** (database table: ``DemandServiceDemandMeasures``)
     These measures alter the projection of service demand in a demand subsector. For example, if we projected a 25% decline in vehicle miles traveled due to land-use and ridesharing policies, we could enter that as a measure here.

   **Energy Efficiency Measures** (database table: ``DemandEnergyEfficiencyMeasures``)
      Energy efficiency measures are used in demand subsectors where we do not have technology and stock-level representation of end-use equipment.  We can change the trajectory of energy demand, however, by implementing generic energy efficiency measures that can achieve energy reductions at a specified cost.

   **Fuel-Switching Measures** (database table: ``DemandFuelSwitchingMeasures``)
      Fuel switching measures are also used in demand subsectors without technology-level representations. We can implement these measures to change the composition of final energy demand. For example, if we wanted to change the final energy type in process heating from pipeline gas to electricity, we could do so with a fuel–switching measure.

   **Flexible Load Measures** (database table: ``DemandFlexibleLoadMeasures``)
      Flexible load measures define the amount of electric load in a subsector that we anticipate can be moved in time. For example, if we wanted 25% of residential electric water heating to be dynamically used to reduce peak loads and facilitate renewable integration, we could achieve that with a flexible load measure.

Supply-Side Measures
--------------------

On the supply-side we have five different types of measures:

   **Sales Share Measures** (database table: ``SupplySalesShareMeasures``)
      These measures control the sales share of technologies within a supply node. For example, if we wanted to have 50% of photovoltaic deployment be fixed-tilt and 50% tracking, we would use a sales share measure.

   **Sales Measures** (database table: ``SupplySalesMeasures``)
      These control the overall level of sales within a node. For example, if we wanted to install 1 GW of fixed-tilt PV in 2030, we would use a sales measure.

   **Stock Measures** (database table: ``SupplyStockMeasures``)
      These measures control the overall level of technology deployment by year. If we wanted to project an overall level of wind deployment by year out to 2050, we would use a stock measure.

   **Blend Measures** (database table: ``BlendNodeBlendMeasures``)
      These measures are used to control the behavior of blend nodes in the model. Blend nodes control flows through the IO matrix by changing the relative proportions of downstream demand that are serviced with different supply nodes. For example, the default for hydrogen production is natural gas steam reformation. If instead we wanted the hydrogen demanded in our energy system to come from 50% steam reformation and 50% electrolysis, we would use a blend measure to define those blending components. These are also used to define things like biofuel percentages in diesel or gasoline.

   **Export Measures** (database table: ``SupplyExportMeasures``)
      Energy systems don’t necessarily just operate to satisfy internal energy service demand. Oftentimes the activity of the energy system is related to external demands for energy products. For example, oil & gas extraction may be related to export opportunities. These measures are used to change these export amounts.

Different types of measures acting on different demand subsectors and supply nodes can be combined to describe a more complex trajectory for an energy system. For instance, we could use a measure to define the sales penetrations of heat pumps, and we could combine that with sales penetrations of electric resistance heaters and electric boilers to create an overall heating electrification package. This could then be combined with, for example, one or more flexible load measures to represent a residential space heating subsector with large amounts of flexible electric demand.

Scenarios
---------

While the content of measures themselves is stored in the energy system PostgreSQL :ref:`database`, the listing of which measures to use in a given scenario is stored in a separate `json`_ file. The json format has several advantages relative to storing scenarios directly in the database:

.. _json: http://www.json.org/

1. It makes it easier to inspect and review the scenario as a whole.
2. Mixing and matching aspects of different scenarios is as simple as copying and pasting.
3. Text files are readily compatible with off-the-shelf version control products (e.g. git), making it easier to track and manage scenarios.

An EnergyPATHWAYS scenario file is essentially an arbitrarily nested set of json objects than terminate in properties that list measures of various types. Below is a simple example.

The first key within the first object (in this case "AEO 2015 Reference" is interpreted as the "name" of the scenario. For consistency, we advise making this similar to the name of the file, but this is not required. It *is* required that the top-level object only have one key, which is essentially the "root" of the scenario; additional scenarios should be placed in different files.

In general, layers of keys and values after the first are not given any special meaning by the EnergyPATHWAYS madel, so you can use any kind of hierarchical organization that is helpful to you. For instance, this example file contains many "description" keys that are purely for human reference. The "commercial general service lighting" key likewise has no special meaning to the model, it's just there to group related measures in a way that is convenient and descriptive for the scenario designer. We do recommend that you divide your scenarios into a Demand Case containing your demand measures and a Supply Case containing your supply measures for ease of mixing and matching, as in the example.

Other than the "root" name, there are only a few keys that are treated specially. If a key matches the name of a Measures table in the database (e.g. ``DemandSalesShareMeasures`` below) the model expects its value to be a list of measure ids from the table that should be applied to this scenario. The value should always be a list, even if it contains only one id. You may reuse the same table name in multiple locations (e.g. to organize your ``DemandSalesShareMeasures`` under labels corresponding to different demand subsectors). Or if you prefer you could list all the ``DemandSalesShareMeasures`` for your scenario in one long list. Note that the database tables that correspond to different measure types are listed in the sections above for reference.

The final key that is interpreted specially is ``Sensitivities``; this key is used to specify that alternative input data should be used for this scenario run. "Sensitivities" are generally considered to be aspects of the modeled future that are outside direct policy control, such as fuel costs, whereas anticipated future policies are covered by Measures. The ``Sensitivities`` key must contain a list of objects. Each object describes a sensitivity to use and has three properties:

   table
      The data table from the database that the sensitivity applies to. As of this writing, ``DemandDriversData``, ``PrimaryCostData`` and ``ImportCostData`` are supported.

   parent_id
      The id of the parent object whose data should be changed for the sensitivity. E.g. if your sensitivity is on ``DemandDriversData`` this will be a demand driver id. If your sensitivity is on ``PrimaryCostData`` or ``ImportCostData``, this will be the supply node id.

   sensitivity
      The name of the sensitivity to use. When loading the model, EnergyPATHWAYS will use the data from ``table`` for the specified ``parent_id`` that contain this value in the ``sensitivity`` column. When no sensitivity is specifid for a particular table and parent_id, EnergyPATHWAYS will load the data that has ``NULL`` in the ``sensitivity`` column.

Of course, the table referenced by the json object must actually contain rows for the specified ``parent_id`` and ``sensitivity`` in order for alternate data to be used. (If no such rows are found, the model will display an error message explaining this when the model is loaded). Your database may already contain sensitivities provided by Evolved Energy Research, or you may wish to add your own; editing the database is covered in the following sections.

.. highlight:: json

The scenario json example::

   {
       "AEO 2015 Reference": {
           "description": "2015 AEO Reference Case",
           "Demand Case: AEO 2015Reference": {
               "commercial general service lighting": {
                   "description": "Reference commercial general service lighting stock rollover consistent with federal standards",
                   "DemandSalesShareMeasures": [
                       240,
                       241,
                       242
                   ]
               },
               "residential building shell": {
                   "description": "Reference projected building shell efficiency",
                   "DemandSalesShareMeasures": [
                       307
                   ]
               }
           },
           "Supply Case: Reference": {
               "Gasoline Blend": {
                   "description": "Reference Ethanol/Gasoline Mix",
                   "BlendNodeBlendMeasures": [
                       1
                   ]
               }
           },
           "Sensitivities": [
               {
                   "table": "DemandDriversData",
                   "parent_id": 1,
                   "sensitivity": "low"
               },
               {
                   "table": "PrimaryCostData",
                   "parent_id": 59,
                   "sensitivity": "high"
               }
           ]
       }
   }

Editing the Model
=================

Editing the Demand Side
-----------------------

If you have analytic needs that go beyond selecting pre-existing measures and sensitivities as outlined above, you may wish to edit the energy system database directly. Changing the demand side of the model can be important to understanding the relative impact of technology deployment to the success (however defined) of a developed pathway. This can be a key tool in developing robustness analysis as many projections of technology development are uncertain. It can also demonstrate conditions under which demand technologies may be cost-effectively deployed and can be a key tool in competitiveness analysis.

For example, while deployment of certain technologies today may not be economic, a variety of changing conditions including those on the grid (high penetrations of renewables and the ability of flexible loads to participate) may change that equation. The ability to model technologies and anticipate their behavior on the system and economics in a variety of scenarios is one of the primary strengths of the EnergyPATHWAYS approach.

Add new demand technology definition or change demand technology parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is a user decision as to whether they would like to add an entire new technology definition or would like to simply alter the parameters of one technology. For quick, one-off analyses of the importance of different technology parameters, it may make sense to simply alter a technology definition (i.e. change its capital costs) and run a case to compare the overall impact of such a technology change. When a user is interested in a wholly new technology that may behave differently than a previously input technology or differ substantively along a variety of potential definitions, then it may make more sense to input a new technology. We will walk through the steps to input a new technology understanding that the only difference for amending a technology is to edit an existing record instead of entering an entirely new one.

1. Add a new technology to the **DemandTechs** table. This will include general parameters like lifetime, associated demand subsector, usage shape (for electric technologies), as well as flexibility parameters (max delay or advance) to inform flexible load potential on the supply-side. For a full list of input parameters and description see:
2. Input efficiency parameters using **DemandTechsMainEfficiency**; **DemandTechsMainEfficiencyData**; **DemandTechsAuxEfficiency**; and **DemandTechsAuxEfficiencyData**; **DemandTechsParasiticEnergy**(Optional); **DemandTechsParasiticEnergyData**; These efficiency inputs can be in almost any unit combination that is consistent with the energy service demand specification. So, for example, if the service demand of light-duty vehicles is in vehicle miles traveled, then the efficiency parameters can be any permutation of distance and energy (ex. Miles/GGE, kilometer/GJ, etc.). **DemandTechsAuxEfficiency** is used for defining technologies that are dual-fuel. For example, plug-in hybrid electric vehicles have an efficiency entry for both the main energy type (electricity) and the auxiliary energy type (gasoline fuels). Parasitic energy is energy associated with the use of equipment unrelated to amount of service demand. So, for example, if there is standby electricity related to a furnace that exists regardless of heating demand, this would be parasitic energy. 
3. Input cost parameters using **DemandTechsCapitalCosts**; **DemandTechsCapitalCostNewData**; **DemandTechsInstallationCost**; **DemandTechsInstallationCostNewData**; **DemandTechsInstallationCostReplacementData**; **DemandTechsFuelSwitchCost**; **DemandTechsFuelSwitchCostData**; **DemandTechsFixedMaintenanceCost**; **DemandTechsFixedMaintenanceCostData**. These inputs allow a user to flexibly define the cost parameters of both owning, installing, and operating demand-side equipment. Capital costs can be input for both new installation (i.e. a new gas furnace in a home) vs. replacement (replacing a gas furnace with a newer vintage on burnout). Installation costs can be input similarly.   Fuel-switching costs add additional flexibility. This cost is assessed when a technology changes from one energy type to another. For example, when a light-duty vehicle goes from a gasoline vehicle to an electric one, we can input the cost of a new home charger. As another example, when a gas water heater changes to a heat pump, we can include any additional wiring costs in this input. Fixed maintenance costs are associated with the ongoing annual operations of a piece of equipment. Tires and oil changes for light-duty vehicles would be examples of O&M costs.

.. raw:: html

    <div style>
		<iframe width="560" height="315" src="https://www.youtube.com/embed/XUrZwRJWyw0" frameborder="0" allowfullscreen></iframe>
    </div>
	

Changing an underlying driver to alter service demand growth
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Changing a demand driver enables you to explore the impacts of certain underlying macroeconomic assumptions (i.e. population) that may be driving projections of energy service demand (i.e. VMTs) that eventually change projections of energy, costs, and emissions. Many service demand projections have underlying linkages with these macroeconomic factors that make these sensitivities interesting. It is important to understand model structure very intimately to ensure that the relationships a user may anticipate between service demand and macroeconomic drivers are being utilized in the database.

.. raw:: html

    <div style>
		<iframe width="560" height="315" src="https://www.youtube.com/embed/hzHJ_ScjLzU" frameborder="0" allowfullscreen></iframe>
    </div>

Changing a projection of service demand
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

While it may be interesting for a user to see the impact of macroeconomic projections, many times it is better to directly change a projection of energy service demand. For example, if we are interested in the effect of VMTs on emissions, it’s likely better to change the VMT projection itself than to change population projections. There are a few ways to change projections of service demand.  The best way to accomplish this is to implement a service demand measure using the **DemandServiceDemandMeasures** and **DemandServiceDemandMeasuresData** table. A service demand measure can be used to alter a trajectory of service demand in any subsector. For example, if we wanted to reduce our VMT by 10% by 2030, we could input a measure that grows the service demand impact from 0% in 2016 to 10% in 2030.

.. raw:: html

    <div style>
		<iframe width="560" height="315" src="https://www.youtube.com/embed/CqMA4BWGJOQ" frameborder="0" allowfullscreen></iframe>
    </div>

Changing demand technology deployment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In addition to defining different technologies, you can vary levels of technology deployment. This can be accomplished either by adding a sales share measure in the table **DemandSalesMeasures** which controls the penetration of a certain technology by vintage (i.e. 50% of light-duty vehicles sold in 2030 are EVs) or by adding a stock measure in the **DemandStockMeasures** table, which controls the overall stock of a certain technology in given years (i.e. by 2030 there are 1.5 million EVs).

Editing the Supply Side
-----------------------

Supply-side variations can take many forms.  Similar to the demand-side, we can alter key supply-side technology parameters like capital costs and efficiency in order to gauge the impact of future technology advances. We can also alter the trajectories of their deployment using a variety of different measure definitions.

Add new supply technology definition or change supply technology parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is a user decision as to whether they would like to add an entire new technology definition or would like to simply alter the parameters of one technology. For quick, one-off analyses of the importance of different technology parameters, it may make sense to simply alter a technology definition (i.e. change its capital costs) and run a case to compare the overall impact of such a technology change. When a user is interested in a wholly new technology that may behave differently than a previously input technology or differ substantively along a variety of potential definitions, then it may make more sense to input a new technology. We will walk through the steps to input a new technology understanding that the only difference for amending a technology is to edit an existing record instead of entering an entirely new one.

1. Add a new technology to the **SupplyTechs** table. This will include general parameters like lifetime, associated supply node, usage or generation shape (for technologies that use or produce electricity).
2. Input efficiency parameters using **SupplyTechsEfficiency**; **SupplyTechsEfficiencyData**; These efficiency inputs can be in almost any unit combination of energy input/energy output. Natural gas power plants, for example, might be input using heat rates (traditionally btu/kWh).  
3. Input cost parameters using **SupplyTechsCapitalCosts**; **SupplyTechsCapitalCostNewData**; **SupplyTechsInstallationCost**; **SupplyTechsInstallationCostNewData**; **SupplyTechsInstallationCostReplacementData**; **SupplyTechsFixedMaintenanceCost**; **SupplyTechsFixedMaintenanceCostData**; **SupplyTechsVariableMaintenanceCosts**; **SupplyTechsVariableMaintenanceCostData**. Many of these inputs have parallels on the demand-side. On the supply-side we have additional variable maintenance cost inputs that are input on a per-unit of energy production basis.
4. Input other performance characteristics using **SupplyTechsCO2Capture**; **SupplyTechsCO2CaptureData**; **SupplyTechsCapacityFactor**; **SupplyTechsCapacityFactorData**. The supply-side has other unique technology characteristics that we do not find on the demand-side. CO2 capture governs the amount of combusted CO2 that sequestered as opposed to those released into the atmosphere. Capacity factor inputs are used to inform maximum potential annual energy production from a given installed capacity. For renewables and other non-dispatchable technologies, this maximum potential can be reduced by curtailment. For thermal resources (like gas power plants) achievement of this maximum is determined economically using an electricity dispatch.

Changing supply technology deployment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There are four different measure types that can change levels of technology deployment on the supply-side. These can broadly be separated into measures that “push” technologies (stock measures and sales measures) and measures that “pull” technologies (blend measures and sales share measures). Stock and sales measures push technologies by placing a specified amount of a technology into service (i.e. 10,000 MW of solar PV). The model then automatically accommodates that stock by changing the grid composition downstream to accommodate that produced energy. Sales share and blend measures work by inducing a demand for a technology on the supply-side. For example, if we specify that 10% of grid electricity should come from solar PV (blend measure) the model will build solar to meet that specification. Sales share measures work within nodes to determine what technology meets that overall demand for the supply node (i.e. new GWh demand for solar PV is met with 50% fixed-tilt and 50% tracking).
