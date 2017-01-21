# This script produces SQL that will SELECT then DELETE any unused Cases, Packages and Measures;
# That is, it will delete any Cases that are not used by any Scenarios,
# any Packages that are not used by any Cases,
# and any Measures that are not used by any Packages.
# It does the operations in that order, so when, e.g. a Case is deleted, all "downstream" Packages and Measures
# are deleted as well.
# Cascading constraints in the database should take care of deleting any rows from supporting tables associated with
# the deleted Cases, Packages and Measures.

# To use the script, you can simply pipe the output to psql:
#
# python delete_orphans.py | psql pathways_db_name
#
# (You may need to add additional login parameters to psql.)
# You could also save the SQL to a file and run it from there if you prefer. The SQL won't change unless the database
# table structure changes and someone updates this script. Just do this once:
#
# python delete_orphans.py > delete_orphans.sql
#
# Then do this whenever you'd like to delete:
#
# psql pathways_db_name < delete_orphans.sql
#
# Finally, if you'd like to generate SQL that does a dry run but does not actually delete rows, just pass the "-d"
# switch to this script, e.g.:
#
# python delete_orphans.py -d | psql pathways_db_name
#
# All of the SQL that is run is identical in either case, but with the dry run the transaction is rolled back
# at the end rather than committed.

import click


# Returns SQL queries to delete rows from del_from_table that are not referenced from ref_table
class OrphanChecker:
    def __init__(self, del_from_table, id_col, ref_table, ref_col):
        self.del_from_table = del_from_table
        self.id_col = id_col
        self.ref_table = ref_table
        self.ref_col = ref_col

    def _query_tail(self):
        return 'FROM "%s" WHERE NOT EXISTS(SELECT * FROM "%s" WHERE "%s".%s = "%s".%s);'\
               % (self.del_from_table, self.ref_table, self.del_from_table, self.id_col, self.ref_table, self.ref_col)

    def header(self):
        return "\\echo '\\n%s orphan rows to delete'" % (self.del_from_table)

    def select(self):
        return "SELECT * " + self._query_tail()

    def delete(self):
        return "DELETE   " + self._query_tail()


# Note that the order of this list matters; we need to delete Cases, then Packages, then Measures, otherwise we
# might miss orphans that we create during the process.
orphan_checker_args = [
    # Cases
    ("DemandCases", "id", "Scenarios", "demand_case"),
    ("SupplyCases", "id", "Scenarios", "supply_case"),
    # Packages
    ("BlendNodeBlendMeasurePackages", "id", "SupplyStates", "blend_package_id"),
    ("DemandFuelSwitchingMeasurePackages", "id", "DemandStates", "fuel_switching_package_id"),
    ("DemandFlexibleLoadMeasurePackages", "id", "DemandStates", "flexible_load_package_id"),
    ("DemandServiceDemandMeasurePackages", "id", "DemandStates", "service_demand_package_id"),
    ("DemandStockMeasurePackages", "id", "DemandStates", "stock_package_id"),
    ("DemandEnergyEfficiencyMeasurePackages", "id", "DemandStates", "energy_efficiency_package_id"),
    ("DemandSalesMeasurePackages", "id", "DemandStates", "sales_package_id"),
    ("SupplySalesShareMeasurePackages", "id", "SupplyStates", "sales_share_package_id"),
    ("SupplyExportMeasurePackages", "id", "SupplyStates", "export_package_id"),
    ("SupplySalesMeasurePackages", "id", "SupplyStates", "sales_package_id"),
    ("SupplyStockMeasurePackages", "id", "SupplyStates", "stock_package_id"),
    # Measures
    ("BlendNodeBlendMeasures", "id", "BlendNodeBlendMeasurePackagesData", "measure_id"),
    ("DemandEnergyEfficiencyMeasures", "id", "DemandEnergyEfficiencyMeasurePackagesData", "measure_id"),
    ("DemandFlexibleLoadMeasures", "id", "DemandFlexibleLoadMeasurePackagesData", "measure_id"),
    ("DemandFuelSwitchingMeasures", "id", "DemandFuelSwitchingMeasurePackagesData", "measure_id"),
    ("DemandServiceDemandMeasures", "id", "DemandServiceDemandMeasurePackagesData", "measure_id"),
    ("DemandSalesMeasures", "id", "DemandSalesMeasurePackagesData", "measure_id"),
    ("DemandStockMeasures", "id", "DemandStockMeasurePackagesData", "measure_id"),
    ("SupplyExportMeasures", "id", "SupplyExportMeasurePackagesData", "measure_id"),
    ("SupplySalesMeasures", "id", "SupplySalesMeasurePackagesData", "measure_id"),
    ("SupplySalesShareMeasures", "id", "SupplySalesShareMeasurePackagesData", "measure_id"),
    ("SupplyStockMeasures", "id", "SupplyStockMeasurePackagesData", "measure_id")
]


@click.command()
@click.option('-d', '--dry-run/--no-dry-run', default=False,
              help='Rollback the transaction at the end so no rows are actually deleted.')
def delete_orphans(dry_run):
    click.echo("BEGIN;")
    for args in orphan_checker_args:
        oc = OrphanChecker(*args)
        click.echo(oc.header())
        click.echo(oc.select())
        click.echo(oc.delete())
    if dry_run:
        click.echo("ROLLBACK;")
    else:
        click.echo("COMMIT;")

if __name__ == '__main__':
    delete_orphans()

