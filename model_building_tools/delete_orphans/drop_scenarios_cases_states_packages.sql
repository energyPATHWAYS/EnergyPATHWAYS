-- This script drops tables that are no longer needed now that we are storing
-- scenario specifications in json files.
BEGIN;

DROP VIEW "DemandSalesMeasuresDataView", "DemandStatesView", "SupplyStatesView";

DROP TABLE "BlendNodeBlendMeasurePackagesData";
DROP TABLE "DemandEnergyEfficiencyMeasurePackagesData";
DROP TABLE "DemandFlexibleLoadMeasurePackagesData";
DROP TABLE "DemandFuelSwitchingMeasurePackagesData";
DROP TABLE "DemandSalesShareMeasurePackagesData";
DROP TABLE "DemandServiceDemandMeasurePackagesData";
DROP TABLE "DemandStockMeasurePackagesData";
DROP TABLE "SupplyExportMeasurePackagesData";
DROP TABLE "SupplySalesMeasurePackagesData";
DROP TABLE "SupplySalesShareMeasurePackagesData";
DROP TABLE "SupplyStockMeasurePackagesData";

DROP TABLE "DemandCasesData";
DROP TABLE "SupplyCasesData";

DROP TABLE "DemandStates";
DROP TABLE "SupplyStates";

DROP TABLE "BlendNodeBlendMeasurePackages";
DROP TABLE "DemandEnergyEfficiencyMeasurePackages";
DROP TABLE "DemandFlexibleLoadMeasurePackages";
DROP TABLE "DemandFuelSwitchingMeasurePackages";
DROP TABLE "DemandSalesShareMeasurePackages";
DROP TABLE "DemandServiceDemandMeasurePackages";
DROP TABLE "DemandStockMeasurePackages";
DROP TABLE "SupplyExportMeasurePackages";
DROP TABLE "SupplySalesMeasurePackages";
DROP TABLE "SupplySalesShareMeasurePackages";
DROP TABLE "SupplyStockMeasurePackages";

DROP TABLE "Scenarios";
DROP TABLE "DemandCases";
DROP TABLE "SupplyCases";

COMMIT;