# This script produces SQL that will alert you to problems with agreement between "parent" tables and "data" tables.

# To use the script, you can simply pipe the output to psql:
#
# python check_database.py | psql pathways_db_name
#
# (You may need to add additional login parameters to psql.)
# You could also save the SQL to a file and run it from there if you prefer. The SQL won't change unless the database
# table structure changes and someone updates this script. Just do this once:
#
# python check_database.py > check_database.sql
#
# Then do this whenever you'd like to check on your database:
#
# psql pathways_db_name < check_database.sql


import click
import textwrap


class IntegrityChecker:
    def __init__(self, data_table, data_column, parent_table, parent_column, has_oth_1):
        self.data_table = data_table
        self.data_column = data_column
        self.parent_table = parent_table
        self.parent_column = parent_column
        self.has_oth_1 = has_oth_1

    def _table_dict(self):
        return {'data': self.data_table,
                'data_col': self.data_column,
                'parent': self.parent_table,
                'parent_col': self.parent_column
                }

    def other_index_disagreement_check(self):
        if not self.has_oth_1:
            return None

        return textwrap.dedent("""
            \\echo '\\n%(data)s with "other index" values not found in parent %(parent)s other_index'
            SELECT "%(parent)s".%(parent_col)s AS "%(parent)s.%(parent_col)s",
                "%(parent)s".other_index_1_id AS "%(parent)s.other_index_1",
                "%(data)s".id AS "%(data)s.id",
                "%(data)s".oth_1_id AS "%(data)s.oth_1_id"
            FROM "%(parent)s"
            JOIN "%(data)s" ON "%(parent)s".%(parent_col)s = "%(data)s".%(data_col)s
            WHERE "%(parent)s".other_index_1_id IS NOT NULL
            AND NOT EXISTS (
              SELECT *
              FROM "OtherIndexesData"
              WHERE "OtherIndexesData".other_index_id = "%(parent)s".other_index_1_id
                AND "OtherIndexesData".id = "%(data)s".oth_1_id
            );
        """ % self._table_dict())

    def parent_without_data_check(self):
        return textwrap.dedent("""
            \\echo '\\n%(parent)s without any %(data)s'
            SELECT "%(parent)s".%(parent_col)s AS "%(parent)s.%(parent_col)s"
            FROM "%(parent)s"
            WHERE NOT EXISTS (
              SELECT *
              FROM "%(data)s"
              WHERE "%(data)s".%(data_col)s = "%(parent)s".%(parent_col)s
            );
        """ % self._table_dict())

    def header(self):
        return "\\echo '\\nChecking %s and %s'" % (self.parent_table, self.data_table)


table_pairs = [
    ('BlendNodeBlendMeasuresData', 'parent_id', 'BlendNodeBlendMeasures', 'id', False),
    ('DemandDriversData', 'parent_id', 'DemandDrivers', 'id', True),
    ('DemandEnergyDemandsData', 'subsector_id', 'DemandEnergyDemands', 'subsector_id', True),
    ('DemandEnergyEfficiencyMeasuresCostData', 'parent_id', 'DemandEnergyEfficiencyMeasuresCost', 'parent_id', True),
    ('DemandEnergyEfficiencyMeasuresData', 'parent_id', 'DemandEnergyEfficiencyMeasures', 'id', True),
    ('DemandFlexibleLoadMeasuresData', 'parent_id', 'DemandFlexibleLoadMeasures', 'id', True),
    ('DemandFuelSwitchingMeasuresCostData', 'parent_id', 'DemandFuelSwitchingMeasuresCost', 'parent_id', True),
    ('DemandFuelSwitchingMeasuresEnergyIntensityData', 'parent_id', 'DemandFuelSwitchingMeasuresEnergyIntensity',
     'parent_id', True),
    ('DemandFuelSwitchingMeasuresImpactData', 'parent_id', 'DemandFuelSwitchingMeasuresImpact', 'parent_id', True),
    ('DemandSalesData', 'subsector_id', 'DemandSales', 'subsector_id', True),
    ('DemandSalesMeasuresData', 'parent_id', 'DemandSalesMeasures', 'id', True),
    ('DemandServiceDemandMeasuresCostData', 'parent_id', 'DemandServiceDemandMeasuresCost', 'parent_id', True),
    ('DemandServiceDemandMeasuresData', 'parent_id', 'DemandServiceDemandMeasures', 'id', True),
    ('DemandServiceDemandsData', 'subsector_id', 'DemandServiceDemands', 'subsector_id', True),
    ('DemandServiceEfficiencyData', 'subsector_id', 'DemandServiceEfficiency', 'subsector_id', True),
    ('DemandStockData', 'subsector_id', 'DemandStock', 'subsector_id', True),
    ('DemandStockMeasuresData', 'parent_id', 'DemandStockMeasures', 'id', True),
    ('DemandTechsAuxEfficiencyData', 'demand_technology_id', 'DemandTechsAuxEfficiency', 'demand_technology_id', True),
    ('DemandTechsCapitalCostNewData', 'demand_technology_id', 'DemandTechsCapitalCost', 'demand_technology_id', True),
    ('DemandTechsCapitalCostReplacementData', 'demand_technology_id', 'DemandTechsCapitalCost', 'demand_technology_id',
     True),
    ('DemandTechsFixedMaintenanceCostData', 'demand_technology_id', 'DemandTechsFixedMaintenanceCost',
     'demand_technology_id', True),
    (
    'DemandTechsFuelSwitchCostData', 'demand_technology_id', 'DemandTechsFuelSwitchCost', 'demand_technology_id', True),
    (
    'DemandTechsInstallationCostNewData', 'demand_technology_id', 'DemandTechsInstallationCost', 'demand_technology_id',
    True),
    ('DemandTechsInstallationCostReplacementData', 'demand_technology_id', 'DemandTechsInstallationCost',
     'demand_technology_id', True),
    (
    'DemandTechsMainEfficiencyData', 'demand_technology_id', 'DemandTechsMainEfficiency', 'demand_technology_id', True),
    ('DemandTechsParasiticEnergyData', 'demand_technology_id', 'DemandTechsParasiticEnergy', 'demand_technology_id',
     True),
    ('DemandTechsServiceDemandModifierData', 'demand_technology_id', 'DemandTechsServiceDemandModifier',
     'demand_technology_id', True),
    ('DemandTechsServiceLinkData', 'parent_id', 'DemandTechsServiceLink', 'id', True),
    ('ImportCostData', 'import_node_id', 'ImportCost', 'import_node_id', False),
    ('PrimaryCostData', 'primary_node_id', 'PrimaryCost', 'primary_node_id', True),
    ('ShapesData', 'parent_id', 'Shapes', 'id', False),
    ('StorageTechsCapacityCapitalCostNewData', 'supply_tech_id', 'StorageTechsCapacityCapitalCost', 'supply_tech_id',
     True),
    ('StorageTechsCapacityCapitalCostReplacementData', 'supply_tech_id', 'StorageTechsCapacityCapitalCost',
     'supply_tech_id', True),
    ('StorageTechsEnergyCapitalCostNewData', 'supply_tech_id', 'StorageTechsEnergyCapitalCost', 'supply_tech_id', True),
    (
    'StorageTechsEnergyCapitalCostReplacementData', 'supply_tech_id', 'StorageTechsEnergyCapitalCost', 'supply_tech_id',
    True),
    ('SupplyCapacityFactorData', 'supply_node_id', 'SupplyCapacityFactor', 'supply_node_id', False),
    ('SupplyCostData', 'parent_id', 'SupplyCost', 'id', False),
    ('SupplyEfficiencyData', 'supply_node_id', 'SupplyEfficiency', 'id', False),
    ('SupplyEmissionsData', 'supply_node_id', 'SupplyEmissions', 'supply_node_id', True),
    ('SupplyExportData', 'supply_node_id', 'SupplyExport', 'supply_node_id', True),
    ('SupplyExportMeasuresData', 'parent_id', 'SupplyExportMeasures', 'id', True),
    ('SupplyPotentialConversionData', 'supply_node_id', 'SupplyPotentialConversion', 'supply_node_id', True),
    ('SupplyPotentialData', 'supply_node_id', 'SupplyPotential', 'supply_node_id', True),
    ('SupplySalesData', 'supply_node_id', 'SupplySales', 'supply_node_id', False),
    ('SupplySalesMeasuresData', 'parent_id', 'SupplySalesMeasures', 'id', True),
    ('SupplySalesShareData', 'supply_node_id', 'SupplySalesShare', 'supply_node_id', False),
    ('SupplySalesShareMeasuresData', 'parent_id', 'SupplySalesShareMeasures', 'id', True),
    ('SupplyStockData', 'supply_node_id', 'SupplyStock', 'supply_node_id', False),
    ('SupplyStockMeasuresData', 'parent_id', 'SupplyStockMeasures', 'id', True),
    ('SupplyTechsCapacityFactorData', 'supply_tech_id', 'SupplyTechsCapacityFactor', 'supply_tech_id', True),
    ('SupplyTechsCapitalCostNewData', 'supply_tech_id', 'SupplyTechsCapitalCost', 'supply_tech_id', False),
    ('SupplyTechsCapitalCostReplacementData', 'supply_tech_id', 'SupplyTechsCapitalCost', 'supply_tech_id', False),
    ('SupplyTechsCO2CaptureData', 'supply_tech_id', 'SupplyTechsCO2Capture', 'supply_tech_id', False),
    ('SupplyTechsEfficiencyData', 'supply_tech_id', 'SupplyTechsEfficiency', 'supply_tech_id', False),
    ('SupplyTechsFixedMaintenanceCostData', 'supply_tech_id', 'SupplyTechsFixedMaintenanceCost', 'supply_tech_id',
     False),
    ('SupplyTechsInstallationCostNewData', 'supply_tech_id', 'SupplyTechsInstallationCost', 'supply_tech_id', False),
    ('SupplyTechsInstallationCostReplacementData', 'supply_tech_id', 'SupplyTechsInstallationCost', 'supply_tech_id',
     False),
    ('SupplyTechsVariableMaintenanceCostData', 'supply_tech_id', 'SupplyTechsVariableMaintenanceCost', 'supply_tech_id',
     False)
]


@click.command()
def check_database():
    for args in table_pairs:
        ic = IntegrityChecker(*args)
        click.echo(ic.other_index_disagreement_check())
        click.echo(ic.parent_without_data_check())

if __name__ == '__main__':
    check_database()

