from __future__ import print_function

import pandas as pd

df = pd.read_csv("validation-metadata.csv").fillna(value='')

df.loc[df.column_name == 'id', 'column_name'] = 'name'
df.loc[df.foreign_column == 'id', 'foreign_column'] = 'name'

# Remove "_id" from column names
for idx, row in df.iterrows():
    col_name = row.column_name
    if col_name.endswith('_id'):
        df.loc[idx, 'column_name'] = col_name[:-3]

    col_name = row.foreign_column
    if col_name.endswith('_id'):
        df.loc[idx, 'foreign_column'] = col_name[:-3]

# Create and populate "not_null" and "cascade_delete" columns
df['not_null'] = 'FALSE'
df.loc[df.nullable == 'NO', 'not_null'] = 'TRUE'

df['cascade_delete'] = 'FALSE'
df.loc[df.on_del == 'CASCADE', 'cascade_delete'] = 'TRUE'

# Eliminate duplicate rows for which there are table-independent column specification
manualDF = pd.read_csv("manual-validation-info.csv").fillna(value='')

genericCols = manualDF.loc[manualDF.table_name == ''].column_name.unique()

# Drop table-specific entries for columns with table-independent entries only
# if all the "nullable" values are the same, and set the "not_null" value in
# the manualDF to the value found in the postgres metadata.
dropable = []
for col in genericCols:
    values = df.query("column_name == @col").not_null.unique()
    if len(values) == 1:
        dropable.append(col)
        manualDF.loc[manualDF.column_name == col, 'not_null'] = values[0]

df = df.query("column_name not in @dropable").copy()

# Add other columns as empty placeholders
for col in ['linked_column', 'dtype', 'folder', 'additional_valid_inputs']:
    df[col] = ''

df.rename(columns={'foreign_table': 'ref_tbl', 'foreign_column' : 'ref_col'}, inplace=True)

# Re-order columns and drop unneeded ones
cols = ['table_name', 'column_name', 'not_null', 'linked_column', 'dtype', 'folder', 'ref_tbl',
        'ref_col', 'cascade_delete', 'additional_valid_inputs']

df = df[cols]

# Add as many "Unnamed: X" columns as occur in the manualDF
for col in manualDF.columns:
    if col.startswith('Unnamed:'):
        df[col] = ''

df = manualDF.append(df)

prefix = 'Unnamed: '
count = len(prefix)
df.rename(columns=lambda col: '_c_' + col[count:] if col.startswith(prefix) else col, inplace=True)

df.to_csv('merged-validation-data.csv', index=None)
