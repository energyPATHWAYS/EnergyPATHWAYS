#!/usr/bin/env python
from __future__ import print_function
import click
import sys

from csvdb.database import CsvDatabase
from energyPATHWAYS.data_object import DataObject
from postgres import PostgresDatabase, find_key_col

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

StartOfFile = '''#
# This is a generated file. Manual edits may be lost!
#
import sys
from energyPATHWAYS.error import UnknownDataClass
from energyPATHWAYS.data_object import DataObject

_Module = sys.modules[__name__]  # get ref to our own module object

def class_for_table(tbl_name):
    try:
        cls = getattr(_Module, tbl_name)
    except AttributeError:
        raise UnknownDataClass(tbl_name)

    return cls

'''

class ClassGenerator(object):
    def __init__(self, dbdir, dbname, host, linewidth, outfile, password, user):
        if dbdir:
            db = CsvDatabase.get_database(dbdir, load=False)
        else:
            db = PostgresDatabase.get_database(host, dbname, user, password, cache_data=False)

        self.db = db
        self.outfile = outfile
        self.linewidth = linewidth
        self.generated = []
        self.tables = None
        self.all_tables = db.get_table_names()

    def generateClass(self, stream, table):
        db = self.db

        # print("Creating class for {}".format(table))
        cols = db.get_columns(table)

        self.generated.append(table)

        # Using DataObject.__name__ rather than "DataObject" so references
        # the class will be found in the IDE.
        base_class = DataObject.__name__

        stream.write('class {}({}):\n'.format(table, base_class))
        stream.write('    _instances_by_key = {}\n')

        key_col = find_key_col(table, cols)
        if not key_col:
            raise Exception("Failed to guess key col in {}; columns are: {}".format(table, cols))

        stream.write('    _key_col = "{}"\n'.format(key_col))  # save as a class variable
        col_strs = map(lambda s: '"{}"'.format(s), cols)
        stream.write('    _cols = [{}]\n'.format(observeLinewidth(col_strs, self.linewidth, indent=12)))
        stream.write('    _table_name = "{}"\n'.format(table))

        data_table = table + 'Data'
        if data_table not in self.all_tables:
            data_table = ''
        stream.write('    _data_table_name = {!r}\n'.format(str(data_table) or None))
        stream.write('\n')

        # TBD: unnecessary?
        extraArgs = ExtraInitArgs.get(table, [])
        extra1 = [name + ('={}'.format(default) if default else '') for name, default in extraArgs]

        params = extra1 + [col + '=None' for col in cols]
        params = observeLinewidth(params, self.linewidth)

        extra2 = [tup[0] for tup in extraArgs]

        stream.write('    def __init__(self, {}, scenario):\n'.format(key_col))
        stream.write('        {}.__init__(self, {}, scenario)\n'.format(base_class, key_col))
        stream.write('\n')
        stream.write('        {}._instances_by_key[self._key] = self\n'.format(table))
        stream.write('\n')

        for col in extra2 + cols:
            stream.write('        self.{col} = None\n'.format(col=col))

        stream.write('\n')

        stream.write('    def set_args(self, scenario, {}):\n'.format(params))

        for col in extra2 + cols:
            stream.write('        self.{col} = {col}\n'.format(col=col))

        stream.write('\n')
        stream.write('        self.load_child_data(scenario)\n')

        extra3 = [('kwargs.get("{}", {})'.format(name, default if default else "None")) for name, default in extraArgs]
        args  = extra3 + [col + '=' + col for col in cols]
        args  = observeLinewidth(args, self.linewidth, indent=17)
        names = observeLinewidth(cols, self.linewidth, indent=8)

        template = """
    def init_from_tuple(self, tup, scenario, **kwargs):    
        ({names}) = tup

        self.set_args(scenario, {args})

"""
        stream.write(template.format(names=names, args=args))


    def generateClasses(self):
        stream = open(self.outfile, 'w') if self.outfile else sys.stdout

        stream.write(StartOfFile)

        db = self.db

        # filter out tables that don't need classes
        tables = self.tables = db.tables_with_classes(include_on_demand=True)

        for name in tables:
            self.generateClass(stream, name)

        sys.stderr.write('Generated {} classes\n'.format(len(self.generated)))
        if stream != sys.stdout:
            stream.close()


@click.command()
@click.option('--dbfile', '-D', is_flag=True,
              help='''\
Use the CSV database rather than PostgreSQL. If this option is used, \
the --dbname option can be a full pathname. If the dbname doesn't end \
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

    dbdir = dbname + ('' if dbname.endswith('.db') else '.db') if dbfile else None

    obj = ClassGenerator(dbdir, dbname, host, linewidth, outfile, password, user)
    obj.generateClasses()


if __name__ == '__main__':
    main()
