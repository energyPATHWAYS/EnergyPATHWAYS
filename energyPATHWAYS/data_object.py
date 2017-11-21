from collections import defaultdict
from .database import get_database, find_parent_col
from .error import SubclassProtocolError

BASE_CLASS = 'DataObject'

class DataObject(object):
    # dict keyed by class object; value is list of instances of the class
    instancesByClass = defaultdict(list)

    _instances_by_key = {}  # here for completeness; shadowed in generated subclasses

    def __init__(self, scenario, key, data_table_name):
        """
        Append self to a list for our subclass
        """
        cls = self.__class__
        self.instancesByClass[cls].append(self)
        self.scenario = scenario
        self._key = key
        self._data_table_name = data_table_name
        self._child_data = None
        self.children_by_fk_col = {}

    def __str__(self):
        return "<{} {}='{}'>".format(self.__class__.__name__, self._key_col, self._key)

    @classmethod
    def instances(cls):
        """
        Return instances for any subclass of DataObject.
        """
        return DataObject.instancesByClass[cls]

    @classmethod
    def get_instance(cls, key):
        cls._instances_by_key.get(key, None)  # uses each class' internal dict

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):
        """
        Generated method
        """
        raise SubclassProtocolError(cls, 'from_tuple')

    # TBD: test this
    @classmethod
    def from_series(cls, scenario, series, **kwargs):
        return cls.from_tuple(scenario, tuple(series), **kwargs)

    @classmethod
    def from_db(cls, scenario, key, **kwargs):
        tup = cls.get_row(key)
        obj = cls.from_tuple(scenario, tup, **kwargs)
        obj.load_child_data()
        return obj

    @classmethod
    def get_row(cls, key, raise_error=True):
        """
        Get a tuple for the row with the given id in the table associated with this class.
        Expects to find exactly one row with the given id. User must instantiate the database
        prior before calling this method.

        :param key: (str) the unique id of a row in `table`
        :param raise_error: (bool) whether to raise an error or return None if the id
           is not found.
        :return: (tuple) of values in the order the columns are defined in the table
        :raises RowNotFound: if `id` is not present in `table`.
        """
        db = get_database()
        tbl_name = cls.__name__
        tup = db.get_row_from_table(tbl_name, cls._key_col, key, raise_error=raise_error)
        return tup

    @classmethod
    def from_dataframe(cls, scenario, df, **kwargs):
        nodes = [cls.from_series(scenario, row, **kwargs) for idx, row in df.iterrows()]
        return nodes

    # TBD: decide whether the default should be copy=True or False
    def load_child_data(self, copy=True):
        """
        If self._data_table is not None, load the data corresponding to this object
        in a DataFrame as self._child_data

        :param id: (.database.CsvDatabase) the database object
        :param copy: (bool) whether to copy the slice from the child table's DF
        :return: none
        """
        db = get_database()

        if self._data_table_name:
            child_tbl = db.get_table(self._data_table_name)
            parent_col = find_parent_col(self._data_table_name, child_tbl.data.columns)
            slice = child_tbl.data.query("{} == '{}'".format(parent_col, self._key))
            self._child_data = slice.copy() if copy else slice
