#
# Implement a version of this that reads a CSV file "table" into a DataFrame or dict
# and indexes off the unique id. Could just cache the rows as tuples on first use of
# the table, and then always perform lookups on the cache.
#
from .database import get_database
from .error import SubclassProtocolError

class DataObject(object):

    def __init__(self):
        pass

    @classmethod
    def from_tuple(cls, id):
        raise SubclassProtocolError(cls, 'from_tuple')

    @classmethod
    def from_db(cls, id):
        tup = cls.get_row(id)
        return cls.from_tuple(tup)

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
