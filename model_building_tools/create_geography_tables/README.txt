This script is meant to assist in creating geography tables for the energyPATHWAYS database

It takes as inputs, human readable csvs with mappings between geographies, map keys, and ids as well as a
spacial join table, and produces three formatted tables for input to the database.

To use this script, replace the example data in the inputs folder with your case specific data, and run the script in python.
Results will appear in the outputs folder with names matching the associated database tables.

The produced tables are:
# GeographyIntersection - ids for the GeographyIntersectionData table
# GeographyIntersectionData - table matching intersection_id to a geography element
# GeographyMap - table matching an intersection_id to map keys