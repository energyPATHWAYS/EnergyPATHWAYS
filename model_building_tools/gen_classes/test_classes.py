from energyPATHWAYS.database import CsvDatabase, PostgresDatabase
from energyPATHWAYS.schema import load_data_objects

if __name__ == '__main__':
    dbname = '171112_US'

    testPostgres = False

    if testPostgres:
        db = PostgresDatabase.get_database(dbname=dbname, user='rjp', cache_data=True)
    else:
        db = CsvDatabase.get_database(pathname=dbname)

    scenario = 'foo'    # TBD: not yet implemented
    load_data_objects(scenario)

    print("Done.")
