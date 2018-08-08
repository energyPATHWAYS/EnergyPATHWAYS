
# Remake schema and copy it to the source directory.
#
SRCDIR    = ../../energyPATHWAYS
DBNAME    = 180728_US
CSVDB_DIR = /Volumes/RamDisk/$(DBNAME).db
MERGE_DB  = /Volumes/RamDisk/merged.db

NEW_DB_BASE  = new_database
NEW_DB_FILE  = ../../energyPATHWAYS/$(NEW_DB_BASE).py
NEW_DB_CLASS = EnergyPathwaysDatabase
NEW_DB_OBJ   = energyPATHWAYS.$(NEW_DB_BASE).$(NEW_DB_CLASS)

options:
	@echo "Available targets:"
	@echo "all          Make csvdb, merge, schema"
	@echo "csvdb        Export data from postgres to CSV files"
	@echo "merge        Combine (denormalize) parent and child data files"
	@echo "schema       Generate custom classes for the merged tables"
	@echo "redo         Make clean, all"
	@echo "regen        Make clean_schema, schema"
	@echo "remerge      Make clean_merge, merge"
	@echo "clean        Make clean_schema, clean_csvdb, clean_merge"
	@echo "clean_schema Remove schema.py"
	@echo "clean_csvdb  Remove the unmerged CSV database and text_mappings.py"
	@echo "clean_merge  remove the merged CSV database directory and the generated CsvDatabase subclass"


all : csvdb merge schema 

csvdb : $(CSVDB_DIR)

merge : $(NEW_DB_FILE)

schema : $(SRCDIR)/schema.py


# Probably don't need ids if we're converting all at once
#IDS = --ids
IDS =

LIMIT =
#LIMIT = -l 1000

$(SRCDIR)/text_mappings.py: text_mappings.py
	cp -p $< $@

$(CSVDB_DIR) : psql_to_csv.py $(SRCDIR)/data_object.py $(SRCDIR)/database.py
	./psql_to_csv.py -d $(DBNAME) -D $(CSVDB_DIR) $(IDS) $(LIMIT)

$(NEW_DB_FILE) : $(CSVDB_DIR)
	./denormalize.py -d $(CSVDB_DIR) -o $(MERGE_DB) -m $(NEW_DB_FILE) -c $(NEW_DB_CLASS)

$(SRCDIR)/schema.py: schema.py
	cp -p $< $@

# If any of the files used to generate the classes change, regenerate schema.py
schema.py: $(SRCDIR)/data_object.py $(SRCDIR)/database.py
	genClasses -o $@ -d $(MERGE_DB) -D $(NEW_DB_OBJ)

remerge: clean_merge merge

redo: clean all

regen: clean_schema schema

clean: clean_schema clean_csvdb clean_merge

clean_schema:
	rm -f schema.py

clean_csvdb:
	rm -f text_mappings.py
	rm -rf $(CSVDB_DIR)

clean_merge:
	rm -rf $(MERGE_DB)
	rm $(NEW_DB_FILE)
