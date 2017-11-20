#!/usr/bin/env python
from __future__ import print_function
import click
import sys

from energyPATHWAYS.database import PostgresDatabase, CsvDatabase, find_key_col
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
    def __init__(self, dbdir, dbname, host, linewidth, outfile, password, user):
        if dbdir:
            db = CsvDatabase.get_database(dbdir)
        else:
            db = PostgresDatabase.get_database(host, dbname, user, password, cache_data=False)

        self.db = db
        self.outfile = outfile
        self.linewidth = linewidth
        self.generated = []
        self.tables = None
        self.all_tables = db.get_tables_names()

    def generateClass(self, stream, table):
        db = self.db

        # print("Creating class for %s" % table)
        cols = db.get_columns(table)

        self.generated.append(table)

        # Using DataObject.__name__ rather than "DataObject" so references
        # to uses of the class will be recognized properly in the IDE.
        base_class = DataObject.__name__

        stream.write('class %s(%s):\n' % (table, base_class))
        stream.write('    _instances_by_key = {}\n')

        key_col = find_key_col(cols)
        if not key_col:
            raise Exception("Failed to guess key col in {}; columns are: {}".format(table, cols))

        stream.write('    _key_col = "{}"\n'.format(key_col))  # save as a class variable
        stream.write('\n')

        # TBD: unnecessary?
        extraArgs = ExtraInitArgs.get(table, [])
        extra1 = [name + ('=%s' % default  if default else '') for name, default in extraArgs]

        params = extra1 + [col + '=None' for col in cols]
        params = observeLinewidth(params, self.linewidth)

        data_table = table + 'Data'
        if data_table not in self.all_tables:
            data_table = ''

        stream.write('    def __init__(self, scenario, %s):\n' % params)
        stream.write('\n')
        stream.write('        {}.__init__(self, scenario, key={}, data_table_name="{}")\n'.format(base_class, key_col, data_table))
        stream.write('        {}._instances_by_key[self._key] = self\n'.format(table))
        stream.write('\n')

        extra2 = [tup[0] for tup in extraArgs]
        for col in extra2 + cols:
            stream.write('        self.{col} = {col}\n'.format(col=col))

        # stream.write('\n        # ints mapped to strings\n')
        # for col in mapped_cols:
        #     stream.write('        self.%s = None\n' % col)

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


    def generateClasses(self):
        stream = open(self.outfile, 'w') if self.outfile else sys.stdout

        with open('boilerplate.py') as header:
            stream.write(header.read())

        db = self.db
        stream.write('\nfrom energyPATHWAYS.data_object import DataObject\n\n')

        # filter out tables that don't need classes
        tables = self.tables = db.tables_with_classes(include_on_demand=True)

        for name in tables:
            self.generateClass(stream, name)

        sys.stderr.write('Generated %d classes\n' % len(self.generated))
        if stream != sys.stdout:
            stream.close()


@click.command()
@click.option('--dbfile', '-D', is_flag=True,
              help='''Use the CSV database rather than PostgreSQL. If this option is 
              used, the --dbname option can be a full pathname. If the dbname doesn't end
              in ".db", this suffix is added. Default is therefore "pathways.db"''')

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

def main(dbfile, dbname, host, linewidth, outfile, password, user):

    if dbfile:
        dbdir = dbname + ('' if dbname.endswith('.db') else '.db')

    obj = ClassGenerator(dbdir, dbname, host, linewidth, outfile, password, user)
    obj.generateClasses()


if __name__ == '__main__':
    main()
