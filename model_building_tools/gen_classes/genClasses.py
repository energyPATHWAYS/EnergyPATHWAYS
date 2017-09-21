#!/usr/bin/env python
from __future__ import print_function
import click
import re
import sys

from energyPATHWAYS.database import SqlDatabase

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

File_header = '''#
# This is a generated file. Manual edits may be lost!
#
import sys
from energyPATHWAYS.error import UnknownDataClass
from energyPATHWAYS.data_object import %s

def class_for_table(tbl_name):
    try:
        module = sys.modules[__name__]  # get ref to our own module object
        cls = getattr(module, tbl_name)
    except AttributeError:
        raise UnknownDataClass(tbl_name)

    return cls

''' % BASE_CLASS


Method_template = """
    @classmethod
    def from_tuple(cls, tup):    
        ({names}) = tup
        
        obj = cls({keywds})
        
        return obj

"""

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
        self.db = SqlDatabase(host, dbname, user, password, cache_data=False)
        self.genSlots = slots
        self.outfile = outfile
        self.linewidth = linewidth
        self.generated = []


    def getTableOfType(self, tableType):
        query = "select table_name from INFORMATION_SCHEMA.TABLES where table_schema = 'public' and table_type = '%s'" % tableType
        result = self.db.fetchcolumn(query)
        return result

    def getColumns(self, table):
        query = "select column_name from INFORMATION_SCHEMA.COLUMNS where table_name = '%s' and table_schema = 'public'" % table
        result = self.db.fetchcolumn(query)
        return result

    def generateClass(self, stream, table):
        cols = self.getColumns(table)

        if not cols or len(cols) < 3:   # don't generate classes for trivial tables
            return

        self.generated.append(table)

        stream.write('class %s(%s):\n' % (table, BASE_CLASS))

        if self.genSlots:
            allNames = BASE_CLASS_SLOTS + cols
            slots = ["'%s'" % name for name in allNames]
            slots = observeLinewidth(slots, self.linewidth)
            stream.write('    __slots__ = [%s]\n\n' % slots)

        params = [col + '=None' for col in cols]
        params = observeLinewidth(params, self.linewidth)

        stream.write('    def __init__(self, %s):\n' % params)
        stream.write('        %s.__init__(self)\n\n' % BASE_CLASS)
        for col in cols:
            stream.write('        self.%s = %s\n' % (col, col))

        keywds = [col + '=' + col for col in cols]
        keywds = observeLinewidth(keywds, self.linewidth, indent=17)
        names  = observeLinewidth(cols, self.linewidth, indent=8)
        stream.write(Method_template.format(names=names, keywds=keywds))

    def generateClasses(self):
        stream = open(self.outfile, 'w') if self.outfile else sys.stdout
        stream.write(File_header)

        tables = self.getTableOfType('BASE TABLE')

        # filter out tables that don't need classes
        tables = filter(lambda name: not any([re.match(pattern, name) for pattern in Patterns_to_ignore]), tables)

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
    obj.generateClasses()


if __name__ == '__main__':
    main()
