## Start of boilerplate.py ##

import sys
from energyPATHWAYS.error import UnknownDataClass
from energyPATHWAYS.data_object import DataObject
from energyPATHWAYS.database import get_database

_Module = sys.modules[__name__]  # get ref to our own module object

def class_for_table(tbl_name):
    try:
        cls = getattr(_Module, tbl_name)
    except AttributeError:
        raise UnknownDataClass(tbl_name)

    return cls

def load_data_objects(scenario, load_children=True):

    db = get_database()

    table_names = db.tables_with_classes()
    table_objs  = [db.get_table(name) for name in table_names]

    for tbl in table_objs:
        name = tbl.name
        cls = class_for_table(name)
        tbl.load_data_object(cls, scenario)

    if load_children:
        missing = {}
        for tbl in table_objs:
            tbl.link_children(missing)

    print("Done loading data objects")

## End of boilerplate.py ##

