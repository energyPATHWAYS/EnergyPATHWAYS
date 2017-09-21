from __future__ import print_function
import pandas as pd
import sys

from energyPATHWAYS.database import SqlDatabase, CsvDatabase, forget_database

from schema import BlendNodeBlendMeasures, BlendNodeBlendMeasuresData, class_for_table

pd.set_option('display.width', 200)

def test_with_db(db):
    print("\n******\nUsing db %s\n******\n" % db)

    obj = BlendNodeBlendMeasures.from_db(1)
    print(obj)
    print('')

    try:
        obj = BlendNodeBlendMeasures.from_db(1000)
        print(obj)
    except Exception as e:
        sys.stderr.write("\n%s\n\n" % e)

    print('')

    obj = BlendNodeBlendMeasuresData.from_db(11963)
    print(obj)

    cls = class_for_table('CO2PriceMeasures')
    obj = cls.from_db(1)
    print(obj)

db = SqlDatabase.get_database(dbname='170817_US', user='rjp', cache_data=True)
test_with_db(db)

forget_database()

db = CsvDatabase.get_database(pathname='/Users/rjp/Projects/EvolvedEnergy/us_pathways.db')
test_with_db(db)

