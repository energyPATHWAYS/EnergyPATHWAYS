from energyPATHWAYS.database import CsvDatabase, PostgresDatabase
from energyPATHWAYS.schema import load_data_objects

if __name__ == '__main__':
    testPostgres = True

    if testPostgres:
        db = PostgresDatabase.get_database(dbname='170817_US', user='rjp', cache_data=True)
    else:
        db = CsvDatabase.get_database(pathname='/Users/rjp/Projects/EvolvedEnergy/us_pathways.db')

    scenario = 'foo'
    load_data_objects(scenario)
    print("Done.")
