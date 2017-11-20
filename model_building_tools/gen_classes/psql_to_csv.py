#!/usr/bin/env python
from __future__ import print_function
import click
import os
from energyPATHWAYS.database import PostgresDatabase, Tables_to_ignore, mkdirs

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

@click.option('--limit', '-l', type=int, default=0,
              help='Limit the number of rows read (useful for debugging; default=0, which means unlimited)')

def main(dbname, db_dir, host, user, password, limit):
    db = PostgresDatabase(host=host, dbname=dbname, user=user, password=password, cache_data=False)

    db_dir = db_dir or dbname + '.db'
    print("Creating CSV database '%s'" % db_dir)
    mkdirs(db_dir)

    db.load_text_mappings()    # to replace ids with strings

    #table_names = db.tables_with_classes(include_on_demand=True)

    tables_to_skip = Tables_to_ignore + ['GeographyIntersection', 'GeographyIntersectionData']
    table_names = [name for name in db.get_tables_names() if name not in tables_to_skip]
    table_objs  = [db.get_table(name) for name in table_names]

    if limit:
        print("\n*** Limiting reads to %d rows per table! ***\n" % limit)

    for tbl in table_objs:
        tbl.load_all(limit=limit)
        tbl.to_csv(db_dir)

    # Save foreign keys so they can be used by CSV database
    foreign_keys_path = os.path.join(db_dir, 'foreign_keys.csv')
    db.save_foreign_keys(foreign_keys_path)


if __name__ == '__main__':
    main()
