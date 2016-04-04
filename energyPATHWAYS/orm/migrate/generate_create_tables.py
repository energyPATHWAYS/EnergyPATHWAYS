"""
Generate SQL to create all the tables needed in the new database structure. Use it like:
> python generate_create_tables.py > create_tables.sql
"""

# this should populate DataMapper.metadata
# order matters, so system tables go first
from energyPATHWAYS.data_models.system import *
#from energyPATHWAYS.data_models.geography import *
#from energyPATHWAYS.data_models.demand import *

from sqlalchemy.schema import CreateTable
from energyPATHWAYS.data_models.data_source import Base

# Note that the sorted_tables is critical here to get the create tables to come out in order of their
# foreign key dependencies. If for some reason that turns out not to be sufficient it looks like there
# are also ways to separate out the table and constraint creation.
for table in Base.metadata.sorted_tables:
    # It is possible to tack on a .complie(engine) here to get postgres-flavored SQL; see:
    # http://stackoverflow.com/questions/2128717/sqlalchemy-printing-raw-sql-from-create
    # I don't see any reason to do that presently since there's nothing postgres-specific about our DDL,
    # just noting it in case it comes up.
    print str(CreateTable(table)).strip() + ';\n'
