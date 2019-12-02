from __future__ import print_function

import pandas as pd

metaDF = pd.read_csv("validation-metadata.csv")
commDF = pd.read_csv("column-comments.csv")

# metaDF.set_index(['table_name', 'column_name'], inplace=True)
# commDF.set_index(['table_name', 'column_name'], inplace=True)

# Add comment column
#metaDF['comment'] = ''

df = metaDF.merge(commDF, how='outer', on=['table_name', 'column_name']).fillna(value='')

# Rename columns
df.rename(columns={'foreign_table' : 'referenced_table',
                   'foreign_column': 'referenced_field'}, inplace=True)

# Create and populate "not_null" and "cascade_delete" columns
df['not_null'] = 'NO'
df.loc[df.nullable == 'NO', 'not_null'] = 'YES'

df['cascade_delete'] = 'NO'
df.loc[df.on_del == 'CASCADE', 'cascade_delete'] = 'YES'

# Add other columns as empty placeholders
for col in ['linked_column', 'dtype', 'folder', 'additional_valid_inputs']:
    df[col] = ''

df.drop(['on_del', 'nullable'], axis='columns', inplace=True)

# Re-order columns
cols = ['table_name', 'column_name', 'not_null', 'linked_column', 'dtype', 'folder', 'referenced_table',
        'referenced_field', 'cascade_delete', 'comment', 'additional_valid_inputs']

df = df[cols]
df.to_csv('merged-validation-data.csv', index=None)
