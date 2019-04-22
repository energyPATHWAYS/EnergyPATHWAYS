alter table "DemandTechsAuxEfficiency" drop constraint if exists "DemandTechsAuxEfficiency_reference_tech_id_fkey";
alter table "DemandTechsAuxEfficiency"
  add constraint "DemandTechsAuxEfficiency_reference_tech_id_fkey"
  foreign key (reference_tech_id) references "DemandTechs"(id);

alter table "DemandTechsCapitalCost" drop constraint if exists "DemandTechsCapitalCost_reference_tech_id_fkey";
alter table "DemandTechsCapitalCost"
  add constraint "DemandTechsCapitalCost_reference_tech_id_fkey"
  foreign key (reference_tech_id) references "DemandTechs"(id);

alter table "DemandTechsFixedMaintenanceCost" drop constraint if exists "DemandTechsFixedMaintenanceCost_reference_tech_id_fkey";
alter table "DemandTechsFixedMaintenanceCost"
  add constraint "DemandTechsFixedMaintenanceCost_reference_tech_id_fkey"
  foreign key (reference_tech_id) references "DemandTechs"(id);

alter table "DemandTechsFuelSwitchCost" drop constraint if exists "DemandTechsFuelSwitchCost_reference_tech_id_fkey";
alter table "DemandTechsFuelSwitchCost"
  add constraint "DemandTechsFuelSwitchCost_reference_tech_id_fkey"
  foreign key (reference_tech_id) references "DemandTechs"(id);

alter table "DemandTechsInstallationCost" drop constraint if exists "DemandTechsInstallationCost_reference_tech_id_fkey";
alter table "DemandTechsInstallationCost"
  add constraint "DemandTechsInstallationCost_reference_tech_id_fkey"
  foreign key (reference_tech_id) references "DemandTechs"(id);

alter table "DemandTechsMainEfficiency" drop constraint if exists "DemandTechsMainEfficiency_reference_tech_id_fkey";
alter table "DemandTechsMainEfficiency"
  add constraint "DemandTechsMainEfficiency_reference_tech_id_fkey"
  foreign key (reference_tech_id) references "DemandTechs"(id);

alter table "DemandTechsParasiticEnergy" drop constraint if exists "DemandTechsParasiticEnergy_reference_tech_id_fkey";
alter table "DemandTechsParasiticEnergy"
  add constraint "DemandTechsParasiticEnergy_reference_tech_id_fkey"
  foreign key (reference_tech_id) references "DemandTechs"(id);

-- N.B. has reference_id rather than reference_tech_id
alter table "DemandTechsServiceLink" drop constraint if exists "DemandTechsServiceLink_reference_id_fkey";
alter table "DemandTechsServiceLink"
  add constraint "DemandTechsServiceLink_reference_id_fkey"
  foreign key (reference_id) references "DemandServiceLink"(id);

alter table "SupplyTechsCapacityFactor" drop constraint if exists "SupplyTechsCapacityFactor_reference_tech_id_fkey";
alter table "SupplyTechsCapacityFactor"
  add constraint "SupplyTechsCapacityFactor_reference_tech_id_fkey"
  foreign key (reference_tech_id) references "SupplyTechs"(id);

alter table "SupplyTechsCapitalCost" drop constraint if exists "SupplyTechsCapitalCost_reference_tech_id_fkey";
alter table "SupplyTechsCapitalCost"
  add constraint "SupplyTechsCapitalCost_reference_tech_id_fkey"
  foreign key (reference_tech_id) references "SupplyTechs"(id);

alter table "SupplyTechsCO2Capture" drop constraint if exists "SupplyTechsCO2Capture_reference_tech_id_fkey";
alter table "SupplyTechsCO2Capture"
  add constraint "SupplyTechsCO2Capture_reference_tech_id_fkey"
  foreign key (reference_tech_id) references "SupplyTechs"(id);

alter table "SupplyTechsEfficiency" drop constraint if exists "SupplyTechsEfficiency_reference_tech_id_fkey";
alter table "SupplyTechsEfficiency"
  add constraint "SupplyTechsEfficiency_reference_tech_id_fkey"
  foreign key (reference_tech_id) references "SupplyTechs"(id);

alter table "SupplyTechsFixedMaintenanceCost" drop constraint if exists "SupplyTechsFixedMaintenanceCost_reference_tech_id_fkey";
alter table "SupplyTechsFixedMaintenanceCost"
  add constraint "SupplyTechsFixedMaintenanceCost_reference_tech_id_fkey"
  foreign key (reference_tech_id) references "SupplyTechs"(id);

alter table "SupplyTechsInstallationCost" drop constraint if exists "SupplyTechsInstallationCost_reference_tech_id_fkey";
alter table "SupplyTechsInstallationCost"
  add constraint "SupplyTechsInstallationCost_reference_tech_id_fkey"
  foreign key (reference_tech_id) references "SupplyTechs"(id);

alter table "SupplyTechsFixedMaintenanceCost" drop constraint if exists "SupplyTechsFixedMaintenanceCost_reference_tech_id_fkey";
alter table "SupplyTechsFixedMaintenanceCost"
  add constraint "SupplyTechsFixedMaintenanceCost_reference_tech_id_fkey"
  foreign key (reference_tech_id) references "SupplyTechs"(id);

alter table "SupplyTechsVariableMaintenanceCost" drop constraint if exists "SupplyTechsVariableMaintenanceCost_reference_tech_id_fkey";
alter table "SupplyTechsVariableMaintenanceCost"
  add constraint "SupplyTechsVariableMaintenanceCost_reference_tech_id_fkey"
  foreign key (reference_tech_id) references "SupplyTechs"(id);

alter table "StorageTechsCapacityCapitalCost" drop constraint if exists "StorageTechsCapacityCapitalCost_reference_tech_id_fkey";
alter table "StorageTechsCapacityCapitalCost"
  add constraint "StorageTechsCapacityCapitalCost_reference_tech_id_fkey"
  foreign key (reference_tech_id) references "SupplyTechs"(id);

alter table "StorageTechsDuration" drop constraint if exists "StorageTechsDuration_reference_tech_id_fkey";
alter table "StorageTechsDuration"
  add constraint "StorageTechsDuration_reference_tech_id_fkey"
  foreign key (reference_tech_id) references "SupplyTechs"(id);

alter table "StorageTechsEnergyCapitalCost" drop constraint if exists "StorageTechsEnergyCapitalCost_reference_tech_id_fkey";
alter table "StorageTechsEnergyCapitalCost"
  add constraint "StorageTechsEnergyCapitalCost_reference_tech_id_fkey"
  foreign key (reference_tech_id) references "SupplyTechs"(id);

alter table "DispatchTransmissionConstraint" drop constraint if exists "DispatchTransmissionConstraint_hurdle_currency_year_id_fkey";
alter table "DispatchTransmissionConstraint"
  add constraint "DispatchTransmissionConstraint_hurdle_currency_year_id_fkey"
  foreign key (hurdle_currency_year_id) references "CurrencyYears"(id);

alter table "DispatchTransmissionConstraint" drop constraint if exists "DispatchTransmissionConstraint_hurdle_currency_id_fkey";
alter table "DispatchTransmissionConstraint"
  add constraint "DispatchTransmissionConstraint_hurdle_currency_id_fkey"
  foreign key (hurdle_currency_id) references "Currencies"(id);
