from __future__ import print_function
import pandas as pd
import sys

from energyPATHWAYS.database import CsvDatabase
from energyPATHWAYS.schema import DemandStock, class_for_table

pd.set_option('display.width', 200)

dbname   = '171112_US'
scenario = 'foo'            # TBD: not yet implemented

def test_with_db(db):
    print("Using db {}".format(db))

    obj = DemandStock.from_db(scenario, 'commercial cooking')
    print(obj)
    print('')

    try:
        obj = DemandStock.from_db(scenario, 'commercial space heating')
        print(obj)
    except Exception as e:
        sys.stderr.write("\n%s\n\n" % e)

    print('')

    cls = class_for_table('DemandSales')
    obj = cls.from_db(scenario, 'residential lighting')
    print(obj)

db = CsvDatabase.get_database(pathname=dbname)
test_with_db(db)
