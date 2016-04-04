In general, all you need to do to update your database to the new structure
is to run the migrate.sql script in this directory, like:

psql pathways_database_name < migrate.sql

The other files in this directory help to set up the migration but do not
need to be run directly.