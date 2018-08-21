#!/usr/bin/env python
from __future__ import print_function
import pandas as pd

from energyPATHWAYS.database import CsvDatabase
from energyPATHWAYS.schema import class_for_table

pd.set_option('display.width', 200)

dbname   = '171112_US'
scenario = 'foo'            # TBD: not yet implemented

def test_with_db(db):
    for tbl_name in db.tables_with_classes():
        print("\n*** {} ***".format(tbl_name))

        tbl = db.get_table(tbl_name)    # CsvTable instance

        data = tbl.data
        rows = len(data)
        if not rows:
            print("No data in {}".format(tbl_name))
            continue

        rowNum = min(3, rows-1)
        print("Grabbing key for row {}".format(rowNum))
        row = data.iloc[rowNum]     # grab a row from the table

        cls = class_for_table(tbl_name) # DataObject
        key_col = cls._key_col
        key = row[key_col]
        print("Key for row {} in {} is '{}'".format(rowNum, cls.__name__, key))

        try:
            if tbl_name == 'DispatchFeedersAllocation':
                pass    # just to set breakpoint for a specific table

            obj = cls(key, scenario)
            obj.init_from_db(key, scenario)

        except Exception as e:
            print("\n>>> {}\n".format(e))
            continue

        print('\nInstance:')
        for col in tbl.data.columns:
            print('    {}: {}'.format(col, getattr(obj, col)))

def main():
    db = CsvDatabase.get_database(pathname=dbname)
    print("Using db {}".format(db))
    test_with_db(db)

if __name__ == '__main__':
    main()
