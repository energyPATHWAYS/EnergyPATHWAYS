#
# Implement a version of this that reads a CSV file "table" into a DataFrame or dict
# and indexes off the unique id. Could just cache the rows as tuples on first use of
# the table, and then always perform lookups on the cache.
#
from collections import defaultdict
from .database import get_database
from .error import SubclassProtocolError

BASE_CLASS = 'DataObject'

class DataObject(object):
    __slots__ = ['id', 'scenario', 'children_by_fk_col']

    # dict keyed by class object; value is list of instances of the class
    instancesByClass = defaultdict(list)

    def __init__(self, scenario):
        """
        Append self to a list for our subclass
        """
        cls = self.__class__
        self.instancesByClass[cls].append(self)
        self.scenario = scenario
        self.id = None
        self.children_by_fk_col = {}

    def __str__(self):
        return "<%s id=%d>" % (self.__class__.__name__, self.id)

    @classmethod
    def instances(cls):
        """
        Return instances for any subclass of DataObject.
        """
        return DataObject.instancesByClass[cls]

    @classmethod
    def get_instance(cls, id):
        cls._instances_by_id.get(id, None)  # uses each class' internal dict

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
    def from_db(cls, scenario, id, **kwargs):
        tup = cls.get_row(id)
        return cls.from_tuple(scenario, tup, **kwargs)

    @classmethod
    def get_row(cls, id, raise_error=True):
        """
        Get a tuple for the row with the given id in the table associated with this class.
        Expects to find exactly one row with the given id. User must instantiate the database
        prior before calling this method.

        :param id: (int) the unique id of a row in `table`
        :param raise_error: (bool) whether to raise an error or return None if the id
           is not found.
        :return: (tuple) of values in the order the columns are defined in the table
        :raises RowNotFound: if `id` is not present in `table`.
        """
        db = get_database()
        tbl_name = cls.__name__
        return db.get_row_from_table(tbl_name, id, raise_error=raise_error)

    @classmethod
    def from_dataframe(cls, scenario, df, **kwargs):
        nodes = [cls.from_series(scenario, row, **kwargs) for idx, row in df.iterrows()]
        return nodes
