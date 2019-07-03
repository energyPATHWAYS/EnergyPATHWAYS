The code in this folder holds a few programs and ancillary files:

1. psql_to_csv.py => text_mappings.py, foreign_keys.csv

- Converts the postgresql database to a CSV-based "database".
- Generates text_mappings.py, which holds a dict mapping table names to a list of column
  names for columns that should be mapped to ints for use in dataframes.
- Generates foreign_keys.csv, which holds data from the postgresql data dictionary that
  is subsequently used to generate classes.

2. genClasses => schema.py

*** NOTE: with the elimination of postgres, the genClasses.py here is replaced by csvdb's genClasses. ***

- Generates classes to match the database schema, which should be copied to energyPATHWAYS/schema.py.

genClasses --outfile=schema.py \
           --data-superclass=energyPATHWAYS.data_object.DataObject \
           --dbdir=/Volumes/RamDisk/merged.db \
           --database-class=energyPATHWAYS.generated.new_database.EnergyPathwaysDatabase

3. postgres.py

- Database and table classes used by psql_to_csv.py

4. alter_tables.sql, foreign_key_updates.sql

- Modify the database to add a name column in DemandServiceLink
- Correct foreign keys to point to the right table, as the FKs are used by the generated classes.

5. Makefile

- Runs all required commands in correct order if file dependencies indicate something is out of date.

6. test_*.py

- Various test programs

============================

To regenerate the schema and text mappings:

  python psql_to_csv.py -d 180728_US --ids
  python genClasses.py  -d 180728_US -D -o schema.py


python psql_to_csv.py -d 190317_MX -D C:\github\EP_MX_db\MX.db
python denormalize.py -d C:\github\EP_MX_db\MX.db -o C:\github\test\merged.db -m "" -c EnergyPathwaysDatabase --no-shapes

python update_json.py C:\github\EP_runs\IADB_csv\high_tech-high_mode_switch.json -d 190317_MX --no-backup
python update_json.py C:\github\EP_runs\IADB_csv\low_tech-high_mode_switch.json -d 190317_MX --no-backup
python update_json.py C:\github\EP_runs\IADB_csv\high_tech-low_mode_switch.json -d 190317_MX --no-backup
python update_json.py C:\github\EP_runs\IADB_csv\high_tech-high_mode_switch.json -d 190317_MX --no-backup

python psql_to_csv.py -d 190220_SDGE -D C:\github\test\190220_SDGE.db
python denormalize.py -d C:\github\test\190220_SDGE.db -o C:\github\test\merged.db -m "" -c EnergyPathwaysDatabase --no-shapes
genClasses -o schema.py -d C:\github\EP_US_db\180728_US.db -D energyPATHWAYS.generated.new_database.EnergyPathwaysDatabase -c energyPATHWAYS.data_object.DataObject
genClasses -o schema.py -d C:\github\test\merged.db -D energyPATHWAYS.generated.new_database.EnergyPathwaysDatabase -c energyPATHWAYS.data_object.DataObject
cp -p schema.py ../../energyPATHWAYS/generated/schema.py