#!/usr/bin/env python

from __future__ import print_function
import click

from energyPATHWAYS.database import (find_key_col, find_parent_col, mkdirs, MappedCols,
                                     Simple_mapping_tables, Tables_without_classes, Tables_to_ignore)
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

    # if not force and os.path.exists(mergedPath):
    #     mtime = os.path.getmtime(mergedPath)
    #     if os.path.getmtime(parentPath) < mtime and os.path.getmtime(parentPath) < mtime:
    #         print("Already merged table", table_name)
    #         return

    print("Merging", table_name)

    parentDF = _read_csv(parentPath, table_name)
    childDF  = _read_csv(childPath,  child_name)

    # In these cases, the child table already holds the desired result
    if table_name in ['Geographies', 'OtherIndexes']:
        childDF.to_csv(mergedPath, index=None)
        return {'data_table': True}

    key_col = find_key_col(table_name, parentDF.columns)
    par_col = find_parent_col(child_name, childDF.columns)

    if not (key_col and par_col):
        if not key_col:
            print("*** Table {}: key_col not found".format(table_name))

        if not par_col:
            print("*** Table {}: par_col not found".format(table_name))

        return None

    if table_name == 'DemandEnergyDemands': # TBD: debugging
        pass

    if key_col == par_col:
        # if the parent and child match on a column with the same name, we
        # rename the child column before merging so "merge" doesn't rename them.
        new_col = 'CHILD_' + par_col
        childDF.rename(index=str, columns={par_col: new_col}, inplace=True)
        par_col = new_col

    merged = pd.merge(parentDF, childDF, left_on=key_col, right_on=par_col, how='left')

    # Missing child data records show up in the merged DF with the parent column
    # as NaN. We set the rest of the columns from the child record to '_missing'
    child_cols = list(set(childDF.columns) - set([par_col]))
    merged.loc[merged[par_col].isnull(), child_cols] = '_missing'

    # drop the redundant parent column and child id column, if present
    to_drop = [par_col]
    if 'id' in child_cols:
        to_drop.append('id')
        child_cols.remove('id')

    merged.drop(to_drop, axis=1, inplace=True)

    merged.to_csv(mergedPath, index=None)

    md = gen_metadata(key_col, child_cols)
    return md

def gen_metadata(key_col, cols):
    """
    Create the metadata for the merged table
    """
    md = {'key_col' : key_col,
          'df_cols' : cols}

    if 'sensitivity' in cols:
        md['lowcase_cols'] = ['sensitivity']

    drop_cols = []
    for col in ('source', 'notes'):
        if col in cols:
            drop_cols.append(col)

    if drop_cols:
        md['drop_cols'] = drop_cols

    return md

def gen_database_file(metadata_file, metadata, classname):
    classname = classname or os.path.basename(metadata_file).split('.')[0]
    with open(metadata_file, 'w') as f:
        f.write('''from csvdb import CsvMetadata, CsvDatabase
from .text_mappings import MappedCols

_Metadata = [
''')
        for tbl_name in sorted(metadata.keys()):
            md = metadata[tbl_name]
            attrs = ['{!r}'.format(tbl_name)] + (['{}={!r}'.format(key, value) for key, value in md.items()] if md else [])
            spacing = ',\n                '
            f.write('    CsvMetadata({}),\n'.format(spacing.join(attrs)))

        f.write(''']

class {classname}(CsvDatabase):
    def __init__(self, pathname=None, load=True, output_tables=False, compile_sensitivities=False, tables_to_not_load=None):
        super({classname}, self).__init__(
            metadata=_Metadata,  
            pathname=pathname, 
            load=load, 
            mapped_cols=MappedCols,
            output_tables=output_tables, 
            compile_sensitivities=compile_sensitivities, 
            tables_to_not_load=tables_to_not_load, 
            tables_without_classes={without_classes}, 
            tables_to_ignore={ignore})
'''.format(classname=classname, without_classes=Tables_without_classes, ignore=Tables_to_ignore))


@click.command()

@click.option('--dbdir', '-d', type=click.Path(exists=True, file_okay=False), default="database.csvdb",
              help='Path to the database directory. (Default is "database.csvdb")')

@click.option('--outdir', '-o',
              help='Where to write the merged CSV files.')

@click.option('--metadata-file', '-m', default='./_GeneratedDatabase.py',
              help='Path to the python file to create containing metadata and database class. Default is ./_GeneratedDatabase.py')

@click.option('--classname', '-c',
              help='Name of the CsvDatabase subclass to create with generated metadata. Default is basename of metadata-file.')

@click.option('--force/--no-force', default=False,
              help='Force merge regardless of file timestamps')

@click.option('--shapes/--no-shapes', default=True,
              help='Whether to copy the ShapeData directory to the merged database. (Default is --shapes)')


def main(dbdir, outdir, metadata_file, classname, force, shapes):
    csvFiles = glob(os.path.join(dbdir, '*.csv'))
    tables   = map(lambda path: os.path.basename(path)[:-4], csvFiles)
    children = filter(lambda x: x.endswith('Data'), tables)

    mkdirs(outdir)

    metadata = {}

    # exclude = Tables_without_classes + Simple_mapping_tables

    for tbl_name in tables:
        child_name = tbl_name + 'Data'
        if child_name in children:
            md = denormalize(dbdir, outdir, tbl_name, force)
            metadata[tbl_name] = md

        elif not (tbl_name.endswith('Data') or tbl_name in Simple_mapping_tables):
            # Copy files that aren't *Data and that don't have related *Data files,
            # and aren't simple mapping tables, which aren't needed in the csvdb
            basename = tbl_name + '.csv'
            print("Copying", basename)
            src = os.path.join(dbdir, basename)
            dst = os.path.join(outdir, basename)
            shutil.copy2(src, dst)

            df = _read_csv(src, tbl_name)
            cols = list(df.columns)
            key_col = find_key_col(tbl_name, cols)
            # md = gen_metadata(key_col, cols)
            # md['data_table'] = True
            metadata[tbl_name] = {'data_table': True}

    gen_database_file(metadata_file, metadata, classname)

    if shapes:
        src = os.path.join(dbdir,  'ShapeData')
        dst = os.path.join(outdir, 'ShapeData')
        if os.path.exists(dst):
            shutil.rmtree(dst)

        print("Copying ShapeData")
        shutil.copytree(src, dst)

if __name__ == '__main__':
    main()
