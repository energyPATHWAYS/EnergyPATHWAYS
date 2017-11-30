from energyPATHWAYS.database import CsvDatabase
from energyPATHWAYS.schema import load_data_objects

if __name__ == '__main__':
    dbname = '171112_US'

    testPostgres = False

    db = CsvDatabase.get_database(pathname=dbname)
    scenario = 'foo'    # TBD: not yet implemented
    load_data_objects(scenario)

    print("Done.")
