#!/usr/bin/env python
#
# TBD: features to consider
# - file of regex transformations to perform on names
# - tables to skip
# - dict of superclasses keyed by table name
# - call super(classname, self).__init__(id=id)?
# - gen any classmethods?
#
from __future__ import print_function
import click
import psycopg2
import re
import sys

BASE_CLASS = 'DataObject'
BASE_CLASS_SLOTS = []       # add base class ivar names here if using __slots__

Patterns_to_ignore = [
    '.*Type(s)?$'       # anything ending in Type or Types
    'CleaningMethods',
    'Currencies',
    'CurrenciesConversion',
    'CurrencyYears',
    'DayHour',
    'DayType',
    'Definitions',
    'GreenhouseGases',
    'IDMap',
    'IndexLevels',
    'InflationConversion',
    'Month',
    'OptPeriods',
    'ShapesUnits',
    'StockDecayFunctions',
    'StockRolloverMethods',
    'TimeZones',
    'YearHour',
    'DispatchConfig',
    'DispatchFeeders',
    'DispatchFeedersData',
    'DispatchNodeConfig',
    'DispatchNodeData',
    'DispatchWindows'
]

Method_template = """
    @classmethod
    def from_tuple(cls, tup):    
        ({names}) = tup
        
        obj = cls({keywds})
        
        return obj

"""

# Deprecated
def cleanupName(name, removeBlanks=True, lower=False):
    original = name
    if removeBlanks:
        name = name.replace(' ', '')    # remove blanks
    else:
        name = name.replace(' ', '_')

    name = name.replace('-', '_')

    if lower:
        name = name.lower()

    if original != name:
        print("Changed '%s' to '%s'" % (original, name))

    return name

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
        conn_str = "host='%s' dbname='%s' user='%s'" % (host, dbname, user)
        if password:
            conn_str += " password='%s'" % password

        self.con = psycopg2.connect(conn_str)
        self.cur = self.con.cursor()

        self.genSlots = slots
        self.outfile = outfile
        self.linewidth = linewidth

        self.stream  = open(outfile, 'w') if outfile else sys.stdout

        self.generated = []

        self.stream.write('''#
# This is a generated file. Manual edits may be lost!
#
from energyPATHWAYS.data_object import %s

''' % BASE_CLASS)

    def close(self):
        if self.outfile:
            self.stream.close()

    def getTableOfType(self, tableType):
        query = "select table_name from INFORMATION_SCHEMA.TABLES where table_schema = 'public' and table_type = '%s'" % tableType
        self.cur.execute(query)
        # result = [cleanupName(tup[0]) for tup in self.cur.fetchall()]
        result = [tup[0] for tup in self.cur.fetchall()]
        return result

    def getColumns(self, table):
        query = "select column_name, data_type from INFORMATION_SCHEMA.COLUMNS where table_name = '%s' and table_schema = 'public'" % table
        self.cur.execute(query)
        # result = [cleanupName(tup[0], removeBlanks=False, lower=True) for tup in self.cur.fetchall()]
        result = [tup[0] for tup in self.cur.fetchall()]
        return result

    def generateClass(self, table):
        cols = self.getColumns(table)

        if not cols or len(cols) < 3:   # don't generate classes for trivial tables
            return

        self.generated.append(table)

        out = self.stream
        out.write('class %s(%s):\n' % (table, BASE_CLASS))

        if self.genSlots:
            allNames = BASE_CLASS_SLOTS + cols
            slots = ["'%s'" % name for name in allNames]
            slots = observeLinewidth(slots, self.linewidth)
            out.write('    __slots__ = [%s]\n\n' % slots)

        params = [col + '=None' for col in cols]
        params = observeLinewidth(params, self.linewidth)

        out.write('    def __init__(self, %s):\n' % params)
        out.write('        %s.__init__(self)\n\n' % BASE_CLASS)
        for col in cols:
            out.write('        self.%s = %s\n' % (col, col))

        keywds = [col + '=' + col for col in cols]
        keywds = observeLinewidth(keywds, self.linewidth, indent=17)
        names  = observeLinewidth(cols, self.linewidth, indent=8)
        out.write(Method_template.format(names=names, keywds=keywds))

    def generateClasses(self):
        tables = self.getTableOfType('BASE TABLE')

        # filter out tables that don't need classes
        tables = filter(lambda name: not any([re.match(pattern, name) for pattern in Patterns_to_ignore]), tables)

        for name in sorted(tables):
            self.generateClass(name)

        sys.stderr.write('Generated %d classes\n' % len(self.generated))


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
    obj.generateClasses()
    obj.close()


if __name__ == '__main__':
    main()
