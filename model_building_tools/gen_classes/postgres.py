import os
import gzip
import pandas as pd
import psycopg2
import re
from energyPATHWAYS.database import AbstractDatabase, AbstractTable, Text_mapping_tables, ForeignKey, mkdirs, find_key_col

class PostgresTable(AbstractTable):
    """
    Implementation of AbstractTable based on the postgres database.
    """
    def __init__(self, db, tbl_name, cache_data=False):
        super(PostgresTable, self).__init__(db, tbl_name, cache_data=cache_data)
        self.mapped_cols = {}    # maps original columns with IDs to added columns with strings
        self.renames = {}

    def load_rows(self, key):
        query = 'select * from "{}" where key="{}"'.format(self.name, key)
        tups = self.db.fetchall(query)
        return tups

    def load_all(self, limit=0, prefix='_'):
        if self.cache_data and self.data is not None:
            return self.data

        tbl_name = self.name
        query = """select column_name, data_type from INFORMATION_SCHEMA.COLUMNS 
                   where table_name = '{}' and table_schema = 'public'""".format(tbl_name)
        columns = self.db.fetchcolumn(query)

        query = 'select * from "{}"'.format(tbl_name)
        if limit:
            query += ' limit {}'.format(limit)

        rows = self.db.fetchall(query)
        self.data = pd.DataFrame.from_records(data=rows, columns=columns, index=None)
        rows, cols = self.data.shape
        print("Cached {} rows, {} cols for table '{}'".format(rows, cols, tbl_name))

        self.map_strings()
        return self.data

    def map_strings(self):
        tbl_name = self.name
        df = self.data
        text_maps = self.db.text_maps

        fkeys = ForeignKey.fk_by_parent.get(tbl_name) or []
        for fk in fkeys:
            ftable = fk.foreign_table_name
            text_map = text_maps.get(ftable)

            if text_map is not None:
                str_col = id_col = fk.column_name

                # Special case for SupplyEfficiency (and others?)
                if str_col == 'id':
                    str_col = 'name'
                elif str_col.endswith('_id'):
                    str_col = str_col[:-3]    # strip off "_id"

                # add a column with the corresponding string value
                df[str_col] = df[id_col].map(text_map.get)

                # and record the mapping
                self.mapped_cols[id_col] = str_col

    col_renames = {
        'CurrenciesConversion':
            {'currency_year_id' : 'currency_year'},
        'DispatchFeedersAllocationData':
            {'parent_id' : 'name'},
        'DispatchFeedersAllocation':
            {'id': 'name'},
        'SupplyEfficiency':
            {'id': 'name'},
    }

    def to_csv(self, db_dir, save_ids=False):
        """
        Save the cached data to a CSV file in the given "db", which is just a
        directory named with a ".db" extension, containing CSV "table" files.
        ID columns are not saved unless save_ids is True.

        :param db_dir: (str) the directory in which to write the CSV file
        :param save_ids: (bool) whether to include integer ids in the CSV file
        :return: none
        """
        name = self.name
        data = self.data
        mapped = self.mapped_cols

        renames = self.col_renames.get(name)

        # since we map the originals (to maintain order) we don't include these again
        skip = mapped.values()

        # Save text mapping tables for validation purposes, but drop the id col (unless we're renaming it)
        if name in Text_mapping_tables and not (renames and renames.get('id')) and not save_ids:
            skip.append('id')

        # Swap out str cols for id cols where they exist
        cols_to_save = [mapped.get(col, col) for col in data.columns if col not in skip]

        df = data[cols_to_save]

        if renames:
            print("Renaming columns for {}: {}".format(name, renames))
            df = df.rename(columns=renames)
            self.renames = renames

        # temp fix to make keys unique in these tables
        tables_to_patch = {
            'DemandFuelSwitchingMeasures' : '{name} - {subsector} - {final_energy_from} to {final_energy_to}',
        }

        if name in tables_to_patch:
            df = df.copy()
            key_col = find_key_col(name, cols_to_save)
            template = tables_to_patch[name]

            for idx, row in df.iterrows():
                kwargs = {col: row[col] for col in cols_to_save}
                df.loc[idx, key_col] = template.format(**kwargs)

        # Handle special case for ShapesData. Split this 3.5 GB data file
        # into individual files for each Shape ID (translated to name)
        if name == 'ShapesData':
            dirname = os.path.join(db_dir, 'ShapeData')
            mkdirs(dirname)

            shapes = self.db.get_table('Shapes')
            shape_names = list(shapes.data.name)

            pat1 = re.compile('[\s\(\)-]')
            pat2 = re.compile('__+')

            for shape_name in shape_names:
                shape_name = re.sub(pat1, '_', shape_name)      # convert symbols not usable in python identifiers to "_"
                shape_name = re.sub(pat2, '_', shape_name)      # convert sequences of "_" to a single "_"

                filename = shape_name + '.csv.gz'
                pathname = os.path.join(dirname, filename)
                chunk = df.query('parent == "{}"'.format(shape_name))
                print("Writing {} rows to {}".format(len(chunk), pathname))
                with gzip.open(pathname, 'wb') as f:
                    chunk.to_csv(f, index=None)
        else:
            pathname = os.path.join(db_dir, name + '.csv')
            df.to_csv(pathname, index=None)

            # Also save the "skipped" columns in {table}_IDS.csv
            pathname = os.path.join(db_dir, 'ids', name + '.csv')
            columns = list(set(data.columns) - set(cols_to_save))
            if 'id' in cols_to_save:
                columns.insert(0, 'id')
            df = data[columns]
            df.to_csv(pathname, index=None)


# Selects all foreign key information for current database
ForeignKeyQuery = '''
SELECT
    x.table_name,
    x.column_name,
    y.table_name AS foreign_table_name,
    y.column_name AS foreign_column_name
FROM information_schema.referential_constraints c
JOIN information_schema.key_column_usage x
    ON x.constraint_name = c.constraint_name
JOIN information_schema.key_column_usage y
    ON y.ordinal_position = x.position_in_unique_constraint
    AND y.constraint_name = c.unique_constraint_name
ORDER BY c.constraint_name, x.ordinal_position;
'''

class PostgresDatabase(AbstractDatabase):
    def __init__(self, host='localhost', dbname='pathways', user='postgres', password='',
                 cache_data=False):
        super(PostgresDatabase, self).__init__(table_class=PostgresTable, cache_data=cache_data)

        conn_str = "host='{}' dbname='{}' user='{}'".format(host, dbname, user)
        if password:
            conn_str += " password='{}'".format(password)

        self.con = psycopg2.connect(conn_str)
        self.cur = self.con.cursor()
        self._cache_foreign_keys()

    def _get_tables_of_type(self, tableType):
        query = "select table_name from INFORMATION_SCHEMA.TABLES where table_schema = 'public' and table_type = '{}'".format(tableType)
        result = self.fetchcolumn(query)
        return result

    def get_table_names(self):
        return self._get_tables_of_type('BASE TABLE')

    def get_views(self):
        return self._get_tables_of_type('VIEW')

    def get_columns(self, table):
        query = "select column_name from INFORMATION_SCHEMA.COLUMNS where table_name = '{}' and table_schema = 'public'".format(table)
        result = self.fetchcolumn(query)
        return result

    @classmethod
    def get_database(cls, host='localhost', dbname='pathways', user='postgres', password='',
                     cache_data=False):
        db = cls._get_database(host=host, dbname=dbname, user=user, password=password,
                               cache_data=cache_data)
        db.load_text_mappings()
        return db

    def _cache_foreign_keys(self):
        rows = self.fetchall(ForeignKeyQuery)
        for row in rows:
            ForeignKey(*row)

    def save_foreign_keys(self, pathname):
        rows = self.fetchall(ForeignKeyQuery)
        columns = ['table_name', 'column_name', 'foreign_table_name', 'foreign_column_name']
        df = pd.DataFrame(data=rows, columns=columns)
        df.to_csv(pathname, index=None)

    def fetchone(self, sql):
        self.cur.execute(sql)
        tup = self.cur.fetchone()
        return tup

    def fetchcolumn(self, sql):
        rows = self.fetchall(sql)
        return [row[0] for row in rows]

    def fetchall(self, sql):
        self.cur.execute(sql)
        rows = self.cur.fetchall()
        return rows
