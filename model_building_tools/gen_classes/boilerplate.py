## Start of boilerplate.py ##

import sys
from energyPATHWAYS.error import UnknownDataClass
from energyPATHWAYS.data_object import DataObject
from energyPATHWAYS.database import get_database, ForeignKey

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

    fk_by_parent = ForeignKey.fk_by_parent

    for tbl in table_objs:
        name = tbl.name
        cls = class_for_table(name)
        tbl.data_class = cls
        df = tbl.load_all()
        print("Loaded %d rows for %s" % (df.shape[0], name))

        # This is inefficient for Postgres since we go from list(tuple)->DataFrame->Series->tuple,
        # but eventually, for the CSV "database", it's just DataFrame->Series->tuple
        for _, row in df.iterrows():
            cls.from_series(scenario, row)  # adds itself to the classes _instances_by_id dict

            # could load children at this point, assuming all tables are cached when first encountered

    if load_children:
        # After loading all "direct" data, link child records via foreign keys
        for parent_tbl in table_objs:
            parent_tbl_name = parent_tbl.name
            parent_cls = parent_tbl.data_class

            for parent_obj in parent_cls.instances():
                fkeys = fk_by_parent[parent_tbl_name]

                for fk in fkeys:
                    parent_col      = fk.column_name
                    child_tbl_name  = fk.foreign_table_name
                    child_col_name  = fk.foreign_column_name

                    child_tbl = db.get_table(child_tbl_name)
                    child_cls = child_tbl.data_class

                    if not child_cls:
                        print("** Skipping missing child class '%s'" % child_tbl_name)
                        continue

                    # create and save a list of all matching data class instances with matching ids
                    children = [obj for obj in child_cls.instances() if getattr(obj, child_col_name) == getattr(parent_obj, parent_col)]
                    parent_tbl.children_by_fk_col[parent_col] = children

    print("Done loading data objects")

## End of boilerplate.py ##

