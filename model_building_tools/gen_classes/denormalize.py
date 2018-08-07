#!/usr/bin/env python

from __future__ import print_function
import click

from energyPATHWAYS.database import find_key_col, find_parent_col, mkdirs, MappedCols
from glob import glob
import os
import pandas as pd
import shutil

def _read_csv(pathname, tbl_name):
    # Avoid reading empty strings as nan
    str_cols = MappedCols.get(tbl_name, [])
    converters = {col: str for col in str_cols}
    converters['sensitivity'] = str

    df = pd.read_csv(pathname, index_col=None, converters=converters)
    return df

def denormalize(dbdir, outdir, table_name, force):
    child_name = table_name + 'Data'
    parentPath = os.path.join(dbdir,  table_name + '.csv')
    childPath  = os.path.join(dbdir,  child_name + '.csv')
    mergedPath = os.path.join(outdir, table_name + '.csv')

    if not force and os.path.exists(mergedPath):
        mtime = os.path.getmtime(mergedPath)
        if os.path.getmtime(parentPath) < mtime and os.path.getmtime(parentPath) < mtime:
            print("Already merged table", table_name)
            return

    print("Merging", table_name)

    parentDF = _read_csv(parentPath, table_name)
    childDF  = _read_csv(childPath,  child_name)

    # In these cases, the child table already holds the desired result
    if table_name in ['Geographies', 'OtherIndexes']:
        childDF.to_csv(mergedPath, index=None)
        return

    key_col = find_key_col(table_name, parentDF.columns)
    par_col = find_parent_col(child_name, childDF.columns)

    if not (key_col and par_col):
        if not key_col:
            print("*** Table {}: key_col not found".format(table_name))

        if not par_col:
            print("*** Table {}: par_col not found".format(table_name))

        return

    par_col_set   = set(parentDF.columns)
    child_col_set = set(childDF.columns) - set([par_col])

    overlap = par_col_set.intersection(child_col_set)
    if overlap:
        if len(overlap) > 1:
            print("Table {}: Can't handle more than one overlap column".format(table_name))
            return

        overlap_col = overlap.pop()
        if force:
            print("*** Table {} and data both have col {}".format(table_name, overlap_col))
        new_col = 'CHILD_' + overlap_col
        childDF.rename(index=str, columns={overlap_col: new_col}, inplace=True)
        if overlap_col == par_col:
            par_col = overlap_col

    merged = pd.merge(parentDF, childDF, left_on=key_col, right_on=par_col, how='left')

    # Missing child data records show up in the merged DF with the parent column
    # as NaN. We set the rest of the columns from the child record to '_missing'
    child_cols = list(child_col_set)
    merged.loc[merged[par_col].isnull(), child_cols] = '_missing'

    # drop the redundant parent column
    merged.drop(par_col, axis=1, inplace=True)

    merged.to_csv(mergedPath, index=None)


@click.command()

@click.option('--dbdir', '-d', type=click.Path(exists=True, file_okay=False), default="database.csvdb",
              help='Path to the database directory. (Default is "database.csvdb")')

@click.option('--outdir', '-o',
              help='Where to write the merged CSV files.')

@click.option('--force/--no-force', default=False,
              help='Force merge regardless of file timestamps')


def main(dbdir, outdir, force):
    csvFiles = glob(os.path.join(dbdir, '*.csv'))
    tables   = map(lambda path: os.path.basename(path)[:-4], csvFiles)
    children = filter(lambda x: x.endswith('Data'), tables)

    mkdirs(outdir)

    for parent_name in tables:
        child_name = parent_name + 'Data'
        if child_name in children:
            denormalize(dbdir, outdir, parent_name, force)

        elif not parent_name.endswith('Data'):
            # Copy files that aren't *Data and that don't have related *Data files
            basename = parent_name + '.csv'
            print("Copying", basename)
            src = os.path.join(dbdir, basename)
            dst = os.path.join(outdir, basename)
            shutil.copy2(src, dst)

if __name__ == '__main__':
    main()
