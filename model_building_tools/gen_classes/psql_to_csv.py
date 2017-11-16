#!/usr/bin/env python
from __future__ import print_function
import click
import os
from energyPATHWAYS.database import PostgresDatabase, Text_mapping_tables

# TODO: Move this to util.py?
def mkdirs(newdir, mode=0o770):
    """
    Try to create the full path `newdir` and ignore the error if it already exists.

    :param newdir: the directory to create (along with any needed parent directories)
    :return: nothing
    """
    from errno import EEXIST

    try:
        os.makedirs(newdir, mode)
    except OSError as e:
        if e.errno != EEXIST:
            raise

@click.command()
@click.option('--dbname', '-d', default='pathways',
              help='PostgreSQL database name (default="pathways")')

@click.option('--db-dir', '-D', default=None,
              help='''Directory under which to store CSV "tables". Defaults to the 
              postgres database name with ".db" extension in the current directory.''')

@click.option('--host', '-h', default='localhost',
              help='Host running PostgreSQL (default="localhost")')

@click.option('--user', '-u', default='postgres',
              help='PostgreSQL user name (default="postgres")')

@click.option('--password', '-p', default='',
              help='PostreSQL password (default="")')

def main(dbname, db_dir, host, user, password):
    db = PostgresDatabase(host=host, dbname=dbname, user=user, password=password, cache_data=False)

    db_dir = db_dir or dbname + '.db'
    print("Creating CSV database '%s'" % db_dir)
    mkdirs(db_dir)

    db.load_text_mappings()    # to replace ids with strings

    table_names = db.tables_with_classes(include_on_demand=True)
    table_objs  = [db.get_table(name) for name in table_names]

    geographies = ['Geographies', 'GeographiesData', 'GeographyIntersection', 'GeographyIntersectionData']
    tables_to_skip = Text_mapping_tables + geographies

    for tbl in table_objs:
        tbl.load_all()
        if tbl.name not in tables_to_skip:
            tbl.to_csv(db_dir)

    # Save foreign keys so they can be used by CSV database
    foreign_keys_path = os.path.join(db_dir, 'foreign_keys.csv')
    db.save_foreign_keys(foreign_keys_path)


if __name__ == '__main__':
    main()
