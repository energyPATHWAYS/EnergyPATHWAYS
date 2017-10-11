#!/usr/bin/env python
from __future__ import print_function
import click
import sys

from energyPATHWAYS.database import PostgresDatabase, get_database

BASE_CLASS = 'DataObject'
BASE_CLASS_SLOTS = []       # add base class ivar names here if using __slots__

# Parent_id_colnames = (
#     'parent_id', 'supply_tech_id', 'supply_node_id', 'demand_technology_id',
#     'intersection_id', 'import_node_id', 'other_index_id', 'primary_node_id'
# )
#
# def parent_id_colname(tbl):
#     """
#     Determine the name of the column identifying the parent record for `tbl`.
#     """
#
#     # From Michael's code
#     # if data_table == 'DemandSalesData':
#     #     return 'demand_technology_id'
#     # if data_table == 'SupplyTechsEfficiencyData':
#     #     return 'supply_tech_id'
#     # if data_table in ('SupplySalesData', 'SupplySalesShareData'):
#     #     return 'supply_technology_id'
#
#     cols = tbl.data.columns
#     for col in Parent_id_colnames:
#         if col in cols:
#             return col
#
#     return None

#
# This dict provides extra args to include in init method of the classes that are
# the keys. Values are lists of tuples of (varName, defaultValue). The variable
# is emitted as a keyword argument. Provide string values with inner quotes, e.g.,
# ('foo', '"bar"') is emitted as foo="bar".
#
ExtraInitArgs = {
    'SupplyPotential' : [('enforce', 'False')],
}

def observeLinewidth(args, linewidth, indent=16):
    processed = ''
    unprocessed = ', '.join(args)
    spaces = ' ' * indent

    while len(unprocessed) > linewidth:
        pos = unprocessed[:linewidth].rfind(',')   # find last comma before linewidth
        processed += unprocessed[:pos + 1] + '\n' + spaces
        unprocessed = unprocessed[pos + 1:]

    processed += unprocessed
    return processed


class ClassGenerator(object):
    def __init__(self, dbname, host, linewidth, outfile, password, slots, user):
        self.db = PostgresDatabase(host, dbname, user, password, cache_data=False)
        self.genSlots = slots
        self.outfile = outfile
        self.linewidth = linewidth
        self.generated = []

    def generateClass(self, stream, table):
        # print("Creating class for %s" % table)
        cols = self.db.get_columns(table)

        if not cols or len(cols) < 2:   # don't generate classes for trivial tables
            # print(" * Skipping trivial table %s" % table)
            return

        self.generated.append(table)

        stream.write('class %s(%s):\n' % (table, BASE_CLASS))
        stream.write('    _instances_by_id = {}\n\n')

        if self.genSlots:
            allNames = BASE_CLASS_SLOTS + cols
            slots = ["'%s'" % name for name in allNames]
            slots = observeLinewidth(slots, self.linewidth)
            stream.write('    __slots__ = [%s]\n\n' % slots)

        extraArgs = ExtraInitArgs.get(table, [])

        extra1 = [name + ('=%s' % default  if default else '') for name, default in extraArgs]
        params = extra1 + [col + '=None' for col in cols]
        params = observeLinewidth(params, self.linewidth)

        stream.write('    def __init__(self, scenario, %s):\n' % params)
        stream.write('        %s.__init__(self, scenario)\n' % BASE_CLASS)
        stream.write('        %s._instances_by_id[id] = self\n\n' % table)
        extra2 = [tup[0] for tup in extraArgs]
        for col in extra2 + cols:
            stream.write('        self.%s = %s\n' % (col, col))

        extra3 = [('kwargs.get("%s", %s)' % (name, default if default else "None")) for name, default in extraArgs]
        args  = extra3 + [col + '=' + col for col in cols]
        args  = observeLinewidth(args, self.linewidth, indent=17)
        names = observeLinewidth(cols, self.linewidth, indent=8)

        template = """
    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        ({names}) = tup

        obj = cls(scenario, {args})

        return obj

"""
        stream.write(template.format(names=names, args=args))

        self.generate_foreign_data_loader(stream, table)


    def generate_foreign_data_loader(self, stream, table):
        """
        Generate a method to load all "child" data linked by foreign keys to this "parent" object.
        """
        pass

    def generateClasses(self):
        stream = open(self.outfile, 'w') if self.outfile else sys.stdout
        with open('boilerplate.py') as header:
            stream.write(header.read())

        # filter out tables that don't need classes
        tables = self.db.tables_with_classes()

        for name in sorted(tables):
            self.generateClass(stream, name)

        sys.stderr.write('Generated %d classes\n' % len(self.generated))
        if stream != sys.stdout:
            stream.close()


@click.command()
@click.option('--dbname', '-d', default='pathways',
              help='PostgreSQL database name (default="pathways")')

@click.option('--host', '-h', default='localhost',
              help='Host running PostgreSQL (default="localhost")')

@click.option('--linewidth', '-l', default=90, type=int,
              help='Maximum line width (default=90)')

@click.option('--outfile', '-o', default='',
              help='File to create (defaults writes to stdout)')

@click.option('--password', '-p', default='',
              help='PostreSQL password (default="")')

@click.option('--slots/--no-slots', default=False,
              help='Generate __slots__ for all classes (default=--no-slots)')

@click.option('--user', '-u', default='postgres',
              help='PostgreSQL user name (default="postgres")')

def main(dbname, host, linewidth, outfile, password, slots, user):
    obj = ClassGenerator(dbname, host, linewidth, outfile, password, slots, user)

    # Save foreign keys so they can be used by CSV database
    obj.db.save_foreign_keys('foreign_keys.csv')

    obj.generateClasses()


if __name__ == '__main__':
    main()
