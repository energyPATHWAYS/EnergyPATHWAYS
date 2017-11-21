#
# Remake schema and copy it to the source directory.
#
DATABASE = 171112_US
SRCDIR   = ../../energyPATHWAYS

all : $(SRCDIR)/schema.py

$(SRCDIR)/schema.py: schema.py
	cp -p schema.py $(SRCDIR)

# If any of the files used to generate the classes change, regenerate schema.py
schema.py: genClasses.py $(SRCDIR)/data_object.py $(SRCDIR)/database.py
	./genClasses.py -o schema.py -d $(DATABASE) -D

clean:
	rm -f schema.py
