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
    def __init__(self, parent_table, data_table):
        self.parent_table = parent_table
        self.data_table = data_table

    def _table_dict(self):
        return {'parent': self.parent_table, 'data': self.data_table}

    def other_index_disagreement_check(self):
        return textwrap.dedent("""
            \\echo '\\n%(data)s with "other index" values not found in parent %(parent)s other_index'
            SELECT "%(parent)s".id AS "%(parent)s.id",
                "%(parent)s".other_index_1_id AS "%(parent)s.other_index_1",
                "%(data)s".id AS "%(data)s.id",
                "%(data)s".oth_1_id AS "%(data)s.oth_1_id"
            FROM "%(parent)s"
            JOIN "%(data)s" ON "%(parent)s".id = "%(data)s".parent_id
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
            SELECT "%(parent)s".id AS "%(parent)s.id"
            FROM "%(parent)s"
            WHERE NOT EXISTS (
              SELECT *
              FROM "%(data)s"
              WHERE "%(data)s".parent_id = "%(parent)s".id
            );
        """ % self._table_dict())

    def header(self):
        return "\\echo '\\nChecking %s and %s'" % (self.parent_table, self.data_table)


table_pairs = [
    ('DemandDrivers', 'DemandDriversData')
]


@click.command()
def check_database():
    for args in table_pairs:
        ic = IntegrityChecker(*args)
        click.echo(ic.other_index_disagreement_check())
        click.echo(ic.parent_without_data_check())

if __name__ == '__main__':
    check_database()

