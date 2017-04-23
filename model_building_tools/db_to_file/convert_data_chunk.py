import csv
import click
import psycopg2.extras
import energyPATHWAYS.config as cfg
from energyPATHWAYS.scenario_loader import Scenario

cfg.init_cfgfile('../../model_runs/us_model_example/config.INI')
cfg.init_db()
cur = cfg.cur
dict_cur = cfg.con.cursor(cursor_factory=psycopg2.extras.DictCursor)


class DataTableChunk:
    """
    A DataTableChunk is all the rows in a single data table that are associated with a single parent_id.
    In other words, the contents of one reasonably compact CSV file.
    """

    # Note that the order matters here; if we find one of the longer suffixes, we want to drop those first, and
    # only assume that the suffix is a simple 'Data' if we don't find anything earlier in the list.
    SUFFIXES = ('NewData', 'RelpacementData', 'Data')

    # This tells us what id:name lookup table to use for a given column name
    LOOKUP_MAP = {
        'gau_id': 'GeographiesData',
        'oth_1_id': 'OtherIndexesData',
        'oth_2_id': 'OtherIndexesData',
        'final_energy': 'FinalEnergy',
        'final_energy_id': 'FinalEnergy',
        'demand_tech_id': 'DemandTechs',
        'demand_technology_id': 'DemandTechs',
        'supply_tech_id': 'SupplyTechs',
        'supply_technology_id': 'SupplyTechs',
        'efficiency_type_id': 'EfficiencyTypes',
        'supply_node_id': 'SupplyNodes',
        'demand_sector_id': 'DemandSectors',
        'ghg_type_id': 'GreenhouseGasEmissionsType',
        'ghg_id': 'GreenhouseGases',
        'dispatch_feeder_id': 'DispatchFeeders',
        'dispatch_constraint_id': 'DispatchConstraintTypes',
        'day_type_id': 'DayType',
        'timeshift_type_id': 'FlexibleLoadShiftTypes'
    }

    # This holds lookup tables that are static for our purposes, so can be shared at the class level
    # (no sense in going back to the database for these lookup tables for each individual chunk)
    lookups = {}

    @classmethod
    def name_for(cls, table, id):
        """Look up the name for a common item like a geographical unit or an other index value"""
        try:
            return cls.lookups[table][id]
        except KeyError:
            cur.execute('SELECT id, name FROM "{}"'.format(table))
            cls.lookups[table] = {row[0]: row[1] for row in cur.fetchall()}
            return cls.lookups[table][id]

    def __init__(self, table, parent_id):
        self.table = table
        self.parent_id = parent_id
        self.parent_col = Scenario.parent_col(table)

    def parent_table(self):
        """Strip "Data", etc. off the end to get the name of the parent table to this data table"""
        for suffix in self.SUFFIXES:
            if self.table.endswith(suffix):
                return self.table[:-len(suffix)]
        raise ValueError("{} does not match any of the known suffixes for a data table".format(self.table))

    def id_col_of_parent(self):
        """Some tables identify their members by something more elaborate than 'id', e.g. 'demand_tech_id'"""
        if self.parent_table() == 'SupplyEfficiency':
            return 'id'

        parent_col = self.parent_col
        if parent_col.endswith('tech_id') or parent_col.endswith('node_id') or\
           parent_col.endswith('technology_id') or parent_col == 'subsector_id':
            return parent_col

        return 'id'

    def parent_row(self):
        """Gets the row from the parent table identified by the supplied parent_id"""
        dict_cur.execute('SELECT * FROM "{}" WHERE {} = {}'.format(
            self.parent_table(), self.id_col_of_parent(), self.parent_id
        ))
        return dict_cur.fetchone()

    def header(self, cols, parent_row):
        """Constructs a header row for the csv based on the columns in the table and contents of the parent row"""
        out = []
        for col in cols:
            if col == 'gau_id':
                out.append(self.name_for('Geographies', parent_row['geography_id']))
            elif col == 'oth_1_id':
                out.append(self.name_for('OtherIndexes', parent_row['other_index_1_id']))
            elif col == 'oth_2_id':
                out.append(self.name_for('OtherIndexes', parent_row['other_index_2_id']))
            else:
                out.append(col)
        return out

    def write_csv(self, filename=None):
        if filename is None:
            filename = "{}_{}.csv".format(self.table, self.parent_id)

        parent_row = self.parent_row()
        cur.execute('SELECT * FROM "{}" WHERE {} = {}'.format(self.table, self.parent_col, self.parent_id))
        if cur.rowcount == 0:
            raise ValueError("No data found for {} with parent_id {}".format(self.table, self.parent_id))
        cols = [desc[0] for desc in cur.description]
        rows = cur.fetchall()

        # Any column that's empty in the first row is one that this chunk doesn't use, so we'll skip it.
        # (Columns must be always used or never used within a given chunk.)
        skip_indexes = set(i for i, val in enumerate(rows[0]) if val is None)
        skip_indexes.add(cols.index('id'))
        skip_indexes.add(cols.index(self.parent_col))

        header_cols = [col for i, col in enumerate(cols) if i not in skip_indexes]
        header = self.header(header_cols, parent_row)

        with open(filename, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)

            for row in rows:
                csv_row = []
                for i, val in enumerate(row):
                    if i in skip_indexes:
                        continue
                    if cols[i] in self.LOOKUP_MAP:
                        csv_row.append(self.name_for(self.LOOKUP_MAP[cols[i]], val))
                    else:
                        csv_row.append(val)

                writer.writerow(csv_row)


@click.command()
@click.argument('mode', type=click.Choice(['export', 'import']))
@click.argument('table')
@click.argument('parent_id', type=click.INT)
@click.option('-f', '--filename', type=click.Path(), help='Filename to export to, defaults to {table}_{parent_id}.csv')
def convert(mode, table, parent_id, filename):
    if mode == 'import':
        raise NotImplementedError("Importing from CSV is not yet implemented.")

    chunk = DataTableChunk(table, parent_id)
    chunk.write_csv(filename)


if __name__ == '__main__':
    convert()








