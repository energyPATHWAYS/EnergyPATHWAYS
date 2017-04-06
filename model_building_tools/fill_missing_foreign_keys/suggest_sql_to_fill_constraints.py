

import csv
import os
import pandas as pd

directory = os.getcwd()

existing_constraints = pd.DataFrame.from_csv(os.path.join(directory, 'existing_constraints.csv'), index_col=None)
columns = pd.DataFrame.from_csv(os.path.join(directory, 'columns.csv'), index_col=None)
tables = pd.DataFrame.from_csv(os.path.join(directory, 'tables.csv'), index_col=None)
good_tables = list(tables['Table'].values)

constraints = {}
for i, row in existing_constraints.iterrows():
    child_table, child_column = row['Child Column'].split('.')
    parent_table, parent_column = row['Parent Column'].split('.')

    if child_column in constraints:
        if constraints[child_column]['parent_table'] != parent_table or constraints[child_column]['parent_column'] != parent_column:
            constraints[child_column]['keep_me'] = False
            if child_column not in ['measure_id', 'package_id', 'parent_id']:
                print 'for table {} child_column {}, expected table {} and got {}, expected column {} and got {}'.format(
                    child_table, child_column, constraints[child_column]['parent_table'], parent_table, constraints[child_column]['parent_column'], parent_column)
        else:
            constraints[child_column]['child_tables'].append(child_table)
    else:
        constraints[child_column] = {}
        constraints[child_column]['child_tables'] = []
        constraints[child_column]['child_tables'].append(child_table)
        constraints[child_column]['parent_table'] = parent_table
        constraints[child_column]['parent_column'] = parent_column
        constraints[child_column]['keep_me'] = True

for key in constraints.keys():
    if constraints[key]['keep_me'] == False:
        del constraints[key]

sql_queries = []
for i, row in columns.iterrows():
    table, column = row['Table'], row['Column']
    if (column not in constraints) or (constraints[column]['keep_me'] == False) or (table in constraints[column]['child_tables']) or (table not in good_tables):
        continue
    sql_queries.append('ALTER TABLE "public"."{}" ADD FOREIGN KEY ("{}") REFERENCES "public"."{}" ("{}");'.format(
        table, column, constraints[column]['parent_table'], constraints[column]['parent_column']))

with open(os.path.join(directory, 'new_sql_constraints.csv'), 'wb') as outfile:
    csvwriter = csv.writer(outfile, delimiter=',')
    for row in sql_queries:
        csvwriter.writerow([row])






