#
# Remake schema and copy it to the source directory.
#
DATABASE = 180728_US
SRCDIR   = ../../energyPATHWAYS
MERGE_DB = /Volumes/RamDisk/merged.db

all : $(SRCDIR)/text_mappings.py $(SRCDIR)/schema.py denormalize

$(SRCDIR)/schema.py: schema.py
	cp -p $< $@

# If any of the files used to generate the classes change, regenerate schema.py
schema.py: genClasses.py $(SRCDIR)/data_object.py $(SRCDIR)/database.py
	./genClasses.py -o $@ -d $(DATABASE) -D

$(SRCDIR)/text_mappings.py: text_mappings.py
	cp -p $< $@

# Probably don't need ids if we're converting all at once
#IDS = --ids
IDS =

LIMIT =
#LIMIT = -l 1000

text_mappings.py : psql_to_csv.py $(SRCDIR)/data_object.py $(SRCDIR)/database.py
	./psql_to_csv.py -d $(DATABASE) $(IDS) $(LIMIT)

denormalize :
	./denormalize.py -d $(DATABASE).db -o $(MERGE_DB)

clean: clean_schema clean_map

clean_all: clean clean_merge

clean_schema:
	rm -f schema.py

clean_map:
	rm -f text_mappings.py

clean_merge:
	rm -rf $(MERGE_DB)
