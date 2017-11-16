#!/usr/bin/env python
from __future__ import print_function
import click
import sys

from energyPATHWAYS.database import PostgresDatabase, ForeignKey, Text_mapping_tables
from energyPATHWAYS.data_object import DataObject

#
# This dict provides extra args to include in init method of the classes that are
# the keys. Values are lists of tuples of (varName, defaultValue). The variable
# is emitted as a keyword argument. Provide string values with inner quotes, e.g.,
# ('foo', '"bar"') is emitted as foo="bar".
#
ExtraInitArgs = {
    'SupplyPotential' : [('enforce', 'False')],
}

# TBD: With just ShapesData using slots, requires ~3GB memory to load
# TBD: everything, and > 10 min to load and link. Killed it...
# TBD: Using slots for other tables has little effect; all is dominated
# TBD: by ShapesData.
UseSlots = (
    'ShapesData',               # > 2.8M rows
    'DemandEnergyDemandsData'   # > 85K rows
)

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
    def __init__(self, dbname, host, linewidth, outfile, password, user):
        self.db = PostgresDatabase(host, dbname, user, password, cache_data=False)
        self.outfile = outfile
        self.linewidth = linewidth
        self.generated = []

    def generateClass(self, stream, table):
        db = self.db

        # print("Creating class for %s" % table)
        cols = db.get_columns(table)

        if not cols or len(cols) < 2:   # don't generate classes for trivial tables
            print(" * Skipping trivial table %s" % table)
            return

        mapped_cols = []
        fkeys = ForeignKey.fk_by_parent.get(table) or []
        for fk in fkeys:
            ftable = fk.foreign_table_name
            if ftable in Text_mapping_tables:
                name = fk.column_name

                if name.endswith('_id'):
                    name = name[:-3]    # strip off "_id"

                name = '_' + name       # prepend "_" so it's identifiable when slicing dataframes
                mapped_cols.append(name)

        self.generated.append(table)

        # Using DataObject.__name__ rather than "DataObject" so references
        # to uses of the class will be recognized properly in the IDE.
        base_class = DataObject.__name__

        all_cols = cols + mapped_cols
        stream.write('class %s(%s):\n' % (table, base_class))
        stream.write('    _instances_by_id = {}\n\n')

        if table in UseSlots:
            slots = ["'%s'" % col for col in all_cols]
            slots = observeLinewidth(slots, self.linewidth)
            stream.write('    __slots__ = [%s]\n\n' % slots)

        extraArgs = ExtraInitArgs.get(table, [])

        extra1 = [name + ('=%s' % default  if default else '') for name, default in extraArgs]
        params = extra1 + [col + '=None' for col in cols]
        params = observeLinewidth(params, self.linewidth)

        stream.write('    def __init__(self, scenario, %s):\n' % params)
        stream.write('        %s.__init__(self, scenario)\n' % base_class)
        stream.write('        %s._instances_by_id[id] = self\n\n' % table)
        extra2 = [tup[0] for tup in extraArgs]
        for col in extra2 + cols:
            stream.write('        self.%s = %s\n' % (col, col))

        stream.write('\n        # ints mapped to strings\n')
        for col in mapped_cols:
            stream.write('        self.%s = None\n' % col)

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

        # self.generate_foreign_data_loader(stream, table)


    # def generate_foreign_data_loader(self, stream, table):
    #     """
    #     Generate a method to load all "child" data linked by foreign keys to this "parent" object.
    #     """
    #     pass


    def generateClasses(self):
        stream = open(self.outfile, 'w') if self.outfile else sys.stdout
        with open('boilerplate.py') as header:
            stream.write(header.read())

        self.db.load_text_mappings()    # to replace ids with strings

        # filter out tables that don't need classes
        tables = self.db.tables_with_classes(include_on_demand=True)

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

@click.option('--user', '-u', default='postgres',
              help='PostgreSQL user name (default="postgres")')

@click.option('--foreign-keys', '-f', default=None,
              help='Path to CSV file in which to save foreign key info')

def main(dbname, host, linewidth, outfile, password, user, foreign_keys):
    obj = ClassGenerator(dbname, host, linewidth, outfile, password, user)

    if foreign_keys:
        # Save foreign keys so they can be used by CSV database
        obj.db.save_foreign_keys(foreign_keys)

    obj.generateClasses()


if __name__ == '__main__':
    main()
