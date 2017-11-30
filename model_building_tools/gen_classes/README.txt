The code in this folder holds a few programs and ancilliary files:

1. psql_to_csv.py => text_mappings.py, foreign_keys.csv

- Converts the postgresl database to a CSV-based "database".
- Generates text_mappings.py, which holds a dict mapping table names to a list of column
  names for columns that should be mapped to ints for use in dataframes.
- Generates foreign_keys.csv, which holds data from the postgresql data dictionary that
  is subsequently used to generate classes.

2. genClasses.py => schema.py

- Generates classes to match the database schema, which should be copied to energyPATHWAYS/schema.py.

3. postgres.py

- Database and table classes used by psql_to_csv.py and genClasses.py.

4. alter_tables.sql, foreign_key_updates.sql

- Modify the database to add a name column in DemandServiceLink
- Correct foreign keys to point to the right table, as the FKs are used by the generated classes.

5. Makefile

- Runs all required commands in correct order if files dependencies indicate something is out of date.

6. test_*.py

- Various test programs
