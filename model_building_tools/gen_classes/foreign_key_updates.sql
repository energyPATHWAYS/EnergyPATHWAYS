alter table "CO2PriceMeasures" drop constraint "CO2PriceMeasures_supply_node_id_fkey";
alter table "CO2PriceMeasures"
  add constraint "CO2PriceMeasures_supply_node_id_fkey"
  foreign key (supply_node_id) references "SupplyNodes"(id);

alter table "DemandEnergyDemandsData" drop constraint "DemandEnergyDemandsData_demand_technology_id_fkey";
alter table "DemandEnergyDemandsData"
  add constraint "DemandEnergyDemandsData_demand_technology_id_fkey"
  foreign key (demand_technology_id) references "DemandTechs"(id);

alter table "DemandSalesData" drop constraint "DemandSalesData_subsector_id_fkey";
alter table "DemandSalesData"
  add constraint "DemandSalesData_subsector_id_fkey"
  foreign key (subsector_id) references "DemandSubsectors"(id);

alter table "DemandServiceDemandsData" drop constraint "DemandServiceDemandsData_subsector_id_fkey";
alter table "DemandServiceDemandsData"
  add constraint "DemandServiceDemandsData_subsector_id_fkey"
  foreign key (subsector_id) references "DemandSubsectors"(id);

alter table "DemandStockData" drop constraint "DemandStockData_subsector_id_fkey";
alter table "DemandStockData"
  add constraint "DemandStockData_subsector_id_fkey"
  foreign key (subsector_id) references "DemandSubsectors"(id);

alter table "DemandTechsAuxEfficiencyData" drop constraint "DemandTechsAuxEfficiencyData_demand_technology_id_fkey";
alter table "DemandTechsAuxEfficiencyData"
  add constraint "DemandTechsAuxEfficiencyData_demand_technology_id_fkey"
  foreign key (demand_technology_id) references "DemandTechs"(id);

alter table "DemandTechsCapitalCostNewData" drop constraint "DemandTechsCapitalCostNewData_demand_technology_id_fkey";
alter table "DemandTechsCapitalCostNewData"
  add constraint "DemandTechsCapitalCostNewData_demand_technology_id_fkey"
  foreign key (demand_technology_id) references "DemandTechs"(id);

alter table "DemandTechsCapitalCostReplacementData" drop constraint "DemandTechsCapitalCostReplacementData_demand_technology_id_fkey";
alter table "DemandTechsCapitalCostReplacementData"
  add constraint "DemandTechsCapitalCostReplacementData_demand_technology_id_fkey"
  foreign key (demand_technology_id) references "DemandTechs"(id);

alter table "DemandTechsFixedMaintenanceCostData" drop constraint "DemandTechsFixedMaintenanceCostData_demand_technology_id_fkey";
alter table "DemandTechsFixedMaintenanceCostData"
  add constraint "DemandTechsFixedMaintenanceCostData_demand_technology_id_fkey"
  foreign key (demand_technology_id) references "DemandTechs"(id);

alter table "DemandTechsFuelSwitchCostData" drop constraint "DemandTechsFuelSwitchCostData_demand_technology_id_fkey";
alter table "DemandTechsFuelSwitchCostData"
  add constraint "DemandTechsFuelSwitchCostData_demand_technology_id_fkey"
  foreign key (demand_technology_id) references "DemandTechs"(id);

alter table "DemandTechsInstallationCostNewData" drop constraint "DemandTechsInstallationCostNewData_demand_technology_id_fkey";
alter table "DemandTechsInstallationCostNewData"
  add constraint "DemandTechsInstallationCostNewData_demand_technology_id_fkey"
  foreign key (demand_technology_id) references "DemandTechs"(id);

alter table "DemandTechsInstallationCostReplacementData" drop constraint "DemandTechsInstallationCostReplacementData_demand_technology_id_fkey";
alter table "DemandTechsInstallationCostReplacementData"
  add constraint "DemandTechsInstallationCostReplacementData_demand_technology_id_fkey"
  foreign key (demand_technology_id) references "DemandTechs"(id);

alter table "DemandTechsMainEfficiencyData" drop constraint "DemandTechsMainEfficiencyData_demand_technology_id_fkey";
alter table "DemandTechsMainEfficiencyData"
  add constraint "DemandTechsMainEfficiencyData_demand_technology_id_fkey"
  foreign key (demand_technology_id) references "DemandTechs"(id);

alter table "DemandTechsParasiticEnergyData" drop constraint "DemandTechsParasiticEnergyData_demand_technology_id_fkey";
alter table "DemandTechsParasiticEnergyData"
  add constraint "DemandTechsParasiticEnergyData_demand_technology_id_fkey"
  foreign key (demand_technology_id) references "DemandTechs"(id);

alter table "DemandTechsServiceDemandModifierData" drop constraint "DemandTechsServiceDemandModifierData_demand_technology_id_fkey";
alter table "DemandTechsServiceDemandModifierData"
  add constraint "DemandTechsServiceDemandModifierData_demand_technology_id_fkey"
  foreign key (demand_technology_id) references "DemandTechs"(id);

alter table "DemandTechsServiceLinkData" drop constraint "DemandTechsServiceLinkData_parent_id_fkey";
alter table "DemandTechsServiceLinkData"
  add constraint "DemandTechsServiceLinkData_parent_id_fkey"
  foreign key (parent_id) references "DemandTechsServiceLink"(id);

/*  alter table "DispatchFeedersAllocationData" drop constraint "DispatchFeedersAllocationData_parent_id_fkey"; */
alter table "DispatchFeedersAllocationData"
  add constraint "DispatchFeedersAllocationData_parent_id_fkey"
  foreign key (parent_id) references "DispatchFeedersAllocation"(id);

alter table "DispatchFeedersAllocationData"
  add constraint "DispatchFeedersAllocationData_dispatch_feeder_id_fkey"
  foreign key (dispatch_feeder_id) references "DispatchFeeders"(id);

alter table "ImportCostData" drop constraint "ImportCostData_import_node_id_fkey";
alter table "ImportCostData"
  add constraint "ImportCostData_import_node_id_fkey"
  foreign key (import_node_id) references "SupplyNodes"(id);

/* alter table "ImportCost" drop constraint "ImportCost_cost_method_id_fkey"; */
alter table "ImportCost"
  add constraint "ImportCost_cost_method_id_fkey"
  foreign key (cost_method_id) references "ImportPrimaryCostMethod"(id);

alter table "PrimaryCostData" drop constraint "PrimaryCostData_primary_node_id_fkey";
alter table "PrimaryCostData"
  add constraint "PrimaryCostData_primary_node_id_fkey"
  foreign key (primary_node_id) references "SupplyNodes"(id);

alter table "StorageTechsCapacityCapitalCostNewData" drop constraint "StorageTechsCapacityCapitalCostNewData_supply_tech_id_fkey";
alter table "StorageTechsCapacityCapitalCostNewData"
  add constraint "StorageTechsCapacityCapitalCostNewData_supply_tech_id_fkey"
  foreign key (supply_tech_id) references "SupplyTechs"(id);

alter table "StorageTechsCapacityCapitalCostReplacementData" drop constraint "StorageTechsCapacityCapitalCostReplacementData_supply_tech_id_fkey";
alter table "StorageTechsCapacityCapitalCostReplacementData"
  add constraint "StorageTechsCapacityCapitalCostReplacementData_supply_tech_id_fkey"
  foreign key (supply_tech_id) references "SupplyTechs"(id);

/* All the keys for this table are misnamed, but this one points to the wrong foreign table, so we fix only this */
alter table "StorageTechsDurationData" drop constraint "StorageTechsCapacityCapitalCostNewData_copy_supply_tech_id_fkey";
alter table "StorageTechsDurationData"
  add constraint "StorageTechsDurationData_supply_tech_id_fkey"
  foreign key (supply_tech_id) references "SupplyTechs"(id);

alter table "StorageTechsEnergyCapitalCostNewData" drop constraint "StorageTechsEnergyCapitalCostNewData_supply_tech_id_fkey";
alter table "StorageTechsEnergyCapitalCostNewData"
  add constraint "StorageTechsEnergyCapitalCostNewData_supply_tech_id_fkey"
  foreign key (supply_tech_id) references "SupplyTechs"(id);

alter table "StorageTechsEnergyCapitalCostReplacementData" drop constraint "StorageTechsEnergyCapitalCostReplacementData_supply_tech_id_fkey";
alter table "StorageTechsEnergyCapitalCostReplacementData"
  add constraint "StorageTechsEnergyCapitalCostReplacementData_supply_tech_id_fkey"
  foreign key (supply_tech_id) references "SupplyTechs"(id);

alter table "SupplyCapacityFactorData" drop constraint "SupplyCapacityFactorData_supply_node_id_fkey";
alter table "SupplyCapacityFactorData"
  add constraint "SupplyCapacityFactorData_supply_node_id_fkey"
  foreign key (supply_node_id) references "SupplyNodes"(id);

alter table "SupplyEfficiencyData" drop constraint "SupplyEfficiencyData_parent_id_fkey";
alter table "SupplyEfficiencyData"
  add constraint "SupplyEfficiencyData_parent_id_fkey"
  foreign key (parent_id) references "SupplyNodes"(id);

alter table "SupplyEmissionsData" drop constraint "SupplyEmissionsData_supply_node_id_fkey";
alter table "SupplyEmissionsData"
  add constraint "SupplyEmissionsData_supply_node_id_fkey"
  foreign key (supply_node_id) references "SupplyNodes"(id);

alter table "SupplyExportData" drop constraint "SupplyExportData_supply_node_id_fkey";
alter table "SupplyExportData"
  add constraint "SupplyExportData_supply_node_id_fkey"
  foreign key (supply_node_id) references "SupplyNodes"(id);

alter table "SupplyPotentialConversionData" drop constraint "SupplyPotentialConversionData_supply_node_id_fkey";
alter table "SupplyPotentialConversionData"
  add constraint "SupplyPotentialConversionData_supply_node_id_fkey"
  foreign key (supply_node_id) references "SupplyNodes"(id);

alter table "SupplyPotentialData" drop constraint "SupplyPotentialData_supply_node_id_fkey";
alter table "SupplyPotentialData"
  add constraint "SupplyPotentialData_supply_node_id_fkey"
  foreign key (supply_node_id) references "SupplyNodes"(id);

alter table "SupplySalesData" drop constraint "SupplySalesData_supply_node_id_fkey";
alter table "SupplySalesData"
  add constraint "SupplySalesData_supply_node_id_fkey"
  foreign key (supply_node_id) references "SupplyNodes"(id);

alter table "SupplySalesShareData" drop constraint "SupplySalesShareData_supply_node_id_fkey";
alter table "SupplySalesShareData"
  add constraint "SupplySalesShareData_supply_node_id_fkey"
  foreign key (supply_node_id) references "SupplyNodes"(id);

alter table "SupplyStockData" drop constraint "SupplyStockData_supply_node_id_fkey";
alter table "SupplyStockData"
  add constraint "SupplyStockData_supply_node_id_fkey"
  foreign key (supply_node_id) references "SupplyNodes"(id);

alter table "SupplyTechsCO2CaptureData" drop constraint "SupplyTechsCO2CaptureData_supply_tech_id_fkey";
alter table "SupplyTechsCO2CaptureData"
  add constraint "SupplyTechsCO2CaptureData_supply_tech_id_fkey"
  foreign key (supply_tech_id) references "SupplyTechs"(id);

alter table "SupplyTechsCapacityFactorData" drop constraint "SupplyTechsCapacityFactorData_supply_tech_id_fkey";
alter table "SupplyTechsCapacityFactorData"
  add constraint "SupplyTechsCapacityFactorData_supply_tech_id_fkey"
  foreign key (supply_tech_id) references "SupplyTechs"(id);

alter table "SupplyTechsCapitalCostNewData" drop constraint "SupplyTechsCapitalCostNewData_supply_tech_id_fkey";
alter table "SupplyTechsCapitalCostNewData"
  add constraint "SupplyTechsCapitalCostNewData_supply_tech_id_fkey"
  foreign key (supply_tech_id) references "SupplyTechs"(id);

alter table "SupplyTechsCapitalCostReplacementData" drop constraint "SupplyTechsCapitalCostReplacementData_supply_tech_id_fkey";
alter table "SupplyTechsCapitalCostReplacementData"
  add constraint "SupplyTechsCapitalCostReplacementData_supply_tech_id_fkey"
  foreign key (supply_tech_id) references "SupplyTechs"(id);

alter table "SupplyTechsEfficiencyData" drop constraint "SupplyTechsEfficiencyData_supply_tech_id_fkey";
alter table "SupplyTechsEfficiencyData"
  add constraint "SupplyTechsEfficiencyData_supply_tech_id_fkey"
  foreign key (supply_tech_id) references "SupplyTechs"(id);

alter table "SupplyTechsEfficiency" drop constraint "SupplyTechsEfficiency_reference_tech_id_fkey";
alter table "SupplyTechsEfficiency"
  add constraint "SupplyTechsEfficiency_reference_tech_id_fkey"
  foreign key (reference_tech_id) references "SupplyTechs"(id);

alter table "SupplyTechsFixedMaintenanceCostData" drop constraint "SupplyTechsFixedMaintenanceCostData_supply_tech_id_fkey";
alter table "SupplyTechsFixedMaintenanceCostData"
  add constraint "SupplyTechsFixedMaintenanceCostData_supply_tech_id_fkey"
  foreign key (supply_tech_id) references "SupplyTechs"(id);

alter table "SupplyTechsInstallationCostNewData" drop constraint "SupplyTechsInstallationCostNewData_supply_tech_id_fkey";
alter table "SupplyTechsInstallationCostNewData"
  add constraint "SupplyTechsInstallationCostNewData_supply_tech_id_fkey"
  foreign key (supply_tech_id) references "SupplyTechs"(id);

alter table "SupplyTechsInstallationCostReplacementData" drop constraint "SupplyTechsInstallationCostReplacementData_supply_tech_id_fkey";
alter table "SupplyTechsInstallationCostReplacementData"
  add constraint "SupplyTechsInstallationCostReplacementData_supply_tech_id_fkey"
  foreign key (supply_tech_id) references "SupplyTechs"(id);

alter table "SupplyTechsVariableMaintenanceCostData" drop constraint "SupplyTechsVariableMaintenanceCostData_supply_tech_id_fkey";
alter table "SupplyTechsVariableMaintenanceCostData"
  add constraint "SupplyTechsVariableMaintenanceCostData_supply_tech_id_fkey"
  foreign key (supply_tech_id) references "SupplyTechs"(id);
