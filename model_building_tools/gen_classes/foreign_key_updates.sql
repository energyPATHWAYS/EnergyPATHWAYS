alter table "CO2PriceMeasures" drop constraint if exists "CO2PriceMeasures_supply_node_id_fkey";
alter table "CO2PriceMeasures"
  add constraint "CO2PriceMeasures_supply_node_id_fkey"
  foreign key (supply_node_id) references "SupplyNodes"(id);

alter table "DemandEnergyDemandsData" drop constraint if exists "DemandEnergyDemandsData_demand_technology_id_fkey";
alter table "DemandEnergyDemandsData"
  add constraint "DemandEnergyDemandsData_demand_technology_id_fkey"
  foreign key (demand_technology_id) references "DemandTechs"(id);

alter table "DemandSalesData" drop constraint if exists "DemandSalesData_subsector_id_fkey";
alter table "DemandSalesData"
  add constraint "DemandSalesData_subsector_id_fkey"
  foreign key (subsector_id) references "DemandSubsectors"(id);

alter table "DemandServiceDemandsData" drop constraint if exists "DemandServiceDemandsData_subsector_id_fkey";
alter table "DemandServiceDemandsData"
  add constraint "DemandServiceDemandsData_subsector_id_fkey"
  foreign key (subsector_id) references "DemandSubsectors"(id);

alter table "DemandStockData" drop constraint if exists "DemandStockData_subsector_id_fkey";
alter table "DemandStockData"
  add constraint "DemandStockData_subsector_id_fkey"
  foreign key (subsector_id) references "DemandSubsectors"(id);

alter table "DemandTechsAuxEfficiencyData" drop constraint if exists "DemandTechsAuxEfficiencyData_demand_technology_id_fkey";
alter table "DemandTechsAuxEfficiencyData"
  add constraint "DemandTechsAuxEfficiencyData_demand_technology_id_fkey"
  foreign key (demand_technology_id) references "DemandTechs"(id);

alter table "DemandTechsCapitalCostNewData" drop constraint if exists "DemandTechsCapitalCostNewData_demand_technology_id_fkey";
alter table "DemandTechsCapitalCostNewData"
  add constraint "DemandTechsCapitalCostNewData_demand_technology_id_fkey"
  foreign key (demand_technology_id) references "DemandTechs"(id);

alter table "DemandTechsCapitalCostReplacementData" drop constraint if exists "DemandTechsCapitalCostReplacementData_demand_technology_id_fkey";
alter table "DemandTechsCapitalCostReplacementData"
  add constraint "DemandTechsCapitalCostReplacementData_demand_technology_id_fkey"
  foreign key (demand_technology_id) references "DemandTechs"(id);

alter table "DemandTechsFixedMaintenanceCostData" drop constraint if exists "DemandTechsFixedMaintenanceCostData_demand_technology_id_fkey";
alter table "DemandTechsFixedMaintenanceCostData"
  add constraint "DemandTechsFixedMaintenanceCostData_demand_technology_id_fkey"
  foreign key (demand_technology_id) references "DemandTechs"(id);

alter table "DemandTechsFuelSwitchCostData" drop constraint if exists "DemandTechsFuelSwitchCostData_demand_technology_id_fkey";
alter table "DemandTechsFuelSwitchCostData"
  add constraint "DemandTechsFuelSwitchCostData_demand_technology_id_fkey"
  foreign key (demand_technology_id) references "DemandTechs"(id);

alter table "DemandTechsInstallationCostNewData" drop constraint if exists "DemandTechsInstallationCostNewData_demand_technology_id_fkey";
alter table "DemandTechsInstallationCostNewData"
  add constraint "DemandTechsInstallationCostNewData_demand_technology_id_fkey"
  foreign key (demand_technology_id) references "DemandTechs"(id);

alter table "DemandTechsInstallationCostReplacementData" drop constraint if exists "DemandTechsInstallationCostReplacementData_demand_technology_id_fkey";
alter table "DemandTechsInstallationCostReplacementData"
  add constraint "DemandTechsInstallationCostReplacementData_demand_technology_id_fkey"
  foreign key (demand_technology_id) references "DemandTechs"(id);

alter table "DemandTechsMainEfficiencyData" drop constraint if exists "DemandTechsMainEfficiencyData_demand_technology_id_fkey";
alter table "DemandTechsMainEfficiencyData"
  add constraint "DemandTechsMainEfficiencyData_demand_technology_id_fkey"
  foreign key (demand_technology_id) references "DemandTechs"(id);

alter table "DemandTechsParasiticEnergyData" drop constraint if exists "DemandTechsParasiticEnergyData_demand_technology_id_fkey";
alter table "DemandTechsParasiticEnergyData"
  add constraint "DemandTechsParasiticEnergyData_demand_technology_id_fkey"
  foreign key (demand_technology_id) references "DemandTechs"(id);

alter table "DemandTechsServiceDemandModifierData" drop constraint if exists "DemandTechsServiceDemandModifierData_demand_technology_id_fkey";
alter table "DemandTechsServiceDemandModifierData"
  add constraint "DemandTechsServiceDemandModifierData_demand_technology_id_fkey"
  foreign key (demand_technology_id) references "DemandTechs"(id);

/*  alter table "DispatchFeedersAllocationData" drop constraint if exists "DispatchFeedersAllocationData_parent_id_fkey"; */
alter table "DispatchFeedersAllocationData"
  add constraint "DispatchFeedersAllocationData_parent_id_fkey"
  foreign key (parent_id) references "DispatchFeedersAllocation"(id);

alter table "DispatchFeedersAllocationData"
  add constraint "DispatchFeedersAllocationData_dispatch_feeder_id_fkey"
  foreign key (dispatch_feeder_id) references "DispatchFeeders"(id);

alter table "ImportCostData" drop constraint if exists "ImportCostData_import_node_id_fkey";
alter table "ImportCostData"
  add constraint "ImportCostData_import_node_id_fkey"
  foreign key (import_node_id) references "SupplyNodes"(id);

alter table "PrimaryCostData" drop constraint if exists "PrimaryCostData_primary_node_id_fkey";
alter table "PrimaryCostData"
  add constraint "PrimaryCostData_primary_node_id_fkey"
  foreign key (primary_node_id) references "SupplyNodes"(id);

alter table "StorageTechsCapacityCapitalCostNewData" drop constraint if exists "StorageTechsCapacityCapitalCostNewData_supply_tech_id_fkey";
alter table "StorageTechsCapacityCapitalCostNewData"
  add constraint "StorageTechsCapacityCapitalCostNewData_supply_tech_id_fkey"
  foreign key (supply_tech_id) references "SupplyTechs"(id);

alter table "StorageTechsCapacityCapitalCostReplacementData" drop constraint if exists "StorageTechsCapacityCapitalCostReplacementData_supply_tech_id_fkey";
alter table "StorageTechsCapacityCapitalCostReplacementData"
  add constraint "StorageTechsCapacityCapitalCostReplacementData_supply_tech_id_fkey"
  foreign key (supply_tech_id) references "SupplyTechs"(id);

alter table "StorageTechsEnergyCapitalCostNewData" drop constraint if exists "StorageTechsEnergyCapitalCostNewData_supply_tech_id_fkey";
alter table "StorageTechsEnergyCapitalCostNewData"
  add constraint "StorageTechsEnergyCapitalCostNewData_supply_tech_id_fkey"
  foreign key (supply_tech_id) references "SupplyTechs"(id);

alter table "StorageTechsEnergyCapitalCostReplacementData" drop constraint if exists "StorageTechsEnergyCapitalCostReplacementData_supply_tech_id_fkey";
alter table "StorageTechsEnergyCapitalCostReplacementData"
  add constraint "StorageTechsEnergyCapitalCostReplacementData_supply_tech_id_fkey"
  foreign key (supply_tech_id) references "SupplyTechs"(id);

alter table "SupplyCapacityFactorData" drop constraint if exists "SupplyCapacityFactorData_supply_node_id_fkey";
alter table "SupplyCapacityFactorData"
  add constraint "SupplyCapacityFactorData_supply_node_id_fkey"
  foreign key (supply_node_id) references "SupplyNodes"(id);

alter table "SupplyEfficiencyData" drop constraint if exists "SupplyEfficiencyData_parent_id_fkey";
alter table "SupplyEfficiencyData"
  add constraint "SupplyEfficiencyData_parent_id_fkey"
  foreign key (parent_id) references "SupplyNodes"(id);

alter table "SupplyEmissionsData" drop constraint if exists "SupplyEmissionsData_supply_node_id_fkey";
alter table "SupplyEmissionsData"
  add constraint "SupplyEmissionsData_supply_node_id_fkey"
  foreign key (supply_node_id) references "SupplyNodes"(id);

alter table "SupplyExportData" drop constraint if exists "SupplyExportData_supply_node_id_fkey";
alter table "SupplyExportData"
  add constraint "SupplyExportData_supply_node_id_fkey"
  foreign key (supply_node_id) references "SupplyNodes"(id);

alter table "SupplyPotentialConversionData" drop constraint if exists "SupplyPotentialConversionData_supply_node_id_fkey";
alter table "SupplyPotentialConversionData"
  add constraint "SupplyPotentialConversionData_supply_node_id_fkey"
  foreign key (supply_node_id) references "SupplyNodes"(id);

alter table "SupplyPotentialData" drop constraint if exists "SupplyPotentialData_supply_node_id_fkey";
alter table "SupplyPotentialData"
  add constraint "SupplyPotentialData_supply_node_id_fkey"
  foreign key (supply_node_id) references "SupplyNodes"(id);

alter table "SupplySalesData" drop constraint if exists "SupplySalesData_supply_node_id_fkey";
alter table "SupplySalesData"
  add constraint "SupplySalesData_supply_node_id_fkey"
  foreign key (supply_node_id) references "SupplyNodes"(id);

alter table "SupplySalesShareData" drop constraint if exists "SupplySalesShareData_supply_node_id_fkey";
alter table "SupplySalesShareData"
  add constraint "SupplySalesShareData_supply_node_id_fkey"
  foreign key (supply_node_id) references "SupplyNodes"(id);

alter table "SupplyStockData" drop constraint if exists "SupplyStockData_supply_node_id_fkey";
alter table "SupplyStockData"
  add constraint "SupplyStockData_supply_node_id_fkey"
  foreign key (supply_node_id) references "SupplyNodes"(id);

alter table "SupplyTechsCO2CaptureData" drop constraint if exists "SupplyTechsCO2CaptureData_supply_tech_id_fkey";
alter table "SupplyTechsCO2CaptureData"
  add constraint "SupplyTechsCO2CaptureData_supply_tech_id_fkey"
  foreign key (supply_tech_id) references "SupplyTechs"(id);

alter table "SupplyTechsCapacityFactorData" drop constraint if exists "SupplyTechsCapacityFactorData_supply_tech_id_fkey";
alter table "SupplyTechsCapacityFactorData"
  add constraint "SupplyTechsCapacityFactorData_supply_tech_id_fkey"
  foreign key (supply_tech_id) references "SupplyTechs"(id);

alter table "SupplyTechsCapitalCostNewData" drop constraint if exists "SupplyTechsCapitalCostNewData_supply_tech_id_fkey";
alter table "SupplyTechsCapitalCostNewData"
  add constraint "SupplyTechsCapitalCostNewData_supply_tech_id_fkey"
  foreign key (supply_tech_id) references "SupplyTechs"(id);

alter table "SupplyTechsCapitalCostReplacementData" drop constraint if exists "SupplyTechsCapitalCostReplacementData_supply_tech_id_fkey";
alter table "SupplyTechsCapitalCostReplacementData"
  add constraint "SupplyTechsCapitalCostReplacementData_supply_tech_id_fkey"
  foreign key (supply_tech_id) references "SupplyTechs"(id);

alter table "SupplyTechsEfficiencyData" drop constraint if exists "SupplyTechsEfficiencyData_supply_tech_id_fkey";
alter table "SupplyTechsEfficiencyData"
  add constraint "SupplyTechsEfficiencyData_supply_tech_id_fkey"
  foreign key (supply_tech_id) references "SupplyTechs"(id);

alter table "SupplyTechsEfficiency" drop constraint if exists "SupplyTechsEfficiency_reference_tech_id_fkey";
alter table "SupplyTechsEfficiency"
  add constraint "SupplyTechsEfficiency_reference_tech_id_fkey"
  foreign key (reference_tech_id) references "SupplyTechs"(id);

alter table "SupplyTechsFixedMaintenanceCostData" drop constraint if exists "SupplyTechsFixedMaintenanceCostData_supply_tech_id_fkey";
alter table "SupplyTechsFixedMaintenanceCostData"
  add constraint "SupplyTechsFixedMaintenanceCostData_supply_tech_id_fkey"
  foreign key (supply_tech_id) references "SupplyTechs"(id);

alter table "SupplyTechsInstallationCostNewData" drop constraint if exists "SupplyTechsInstallationCostNewData_supply_tech_id_fkey";
alter table "SupplyTechsInstallationCostNewData"
  add constraint "SupplyTechsInstallationCostNewData_supply_tech_id_fkey"
  foreign key (supply_tech_id) references "SupplyTechs"(id);

alter table "SupplyTechsInstallationCostReplacementData" drop constraint if exists "SupplyTechsInstallationCostReplacementData_supply_tech_id_fkey";
alter table "SupplyTechsInstallationCostReplacementData"
  add constraint "SupplyTechsInstallationCostReplacementData_supply_tech_id_fkey"
  foreign key (supply_tech_id) references "SupplyTechs"(id);

alter table "SupplyTechsVariableMaintenanceCostData" drop constraint if exists "SupplyTechsVariableMaintenanceCostData_supply_tech_id_fkey";
alter table "SupplyTechsVariableMaintenanceCostData"
  add constraint "SupplyTechsVariableMaintenanceCostData_supply_tech_id_fkey"
  foreign key (supply_tech_id) references "SupplyTechs"(id);
