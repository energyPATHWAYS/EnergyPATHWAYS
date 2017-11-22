#
# Remake schema and copy it to the source directory.
#
DATABASE = 171112_US
SRCDIR   = ../../energyPATHWAYS

all : $(SRCDIR)/schema.py $(SRCDIR)/text_mappings.py


$(SRCDIR)/schema.py: schema.py
	cp -p $< $@

# If any of the files used to generate the classes change, regenerate schema.py
schema.py: genClasses.py $(SRCDIR)/data_object.py $(SRCDIR)/database.py
	./genClasses.py -o $@ -d $(DATABASE) -D


$(SRCDIR)/text_mappings.py: text_mappings.py
	cp -p $< $@

text_mappings.py : psql_to_csv.py $(SRCDIR)/data_object.py $(SRCDIR)/database.py
	psql_to_csv.py -d $(DATABASE)


clean: clean_schema clean_map

clean_schema:
	rm -f schema.py

clean_map:
	rm -f text_mappings.py
