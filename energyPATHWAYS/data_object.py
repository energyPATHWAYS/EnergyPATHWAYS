from collections import defaultdict
from .database import get_database, find_parent_col
from .error import SubclassProtocolError
from .text_mappings import MappedCols

DropStrCols = True

class StringMap(object):
    """
    A simple class to map strings to integer IDs and back again.
    """
    instance = None

    @classmethod
    def getInstance(cls):
        if not cls.instance:
            cls.instance = cls()

        return cls.instance

    def __init__(self):
        self.txt_to_id = {}     # maps text to integer id
        self.id_to_txt = {}     # maps id back to text
        self.next_id = 1        # the next id to assign

    def store(self, txt):
        # If already known, return it
        id = self.get_id(txt, raise_error=False)
        if id is not None:
            return id

        id = self.next_id
        self.next_id += 1

        self.txt_to_id[txt] = id
        self.id_to_txt[id] = txt
        return id

    def get_id(self, txt, raise_error=True):
        return self.txt_to_id[txt] if raise_error else (None if id is None else self.txt_to_id.get(txt, None))

    def get_txt(self, id, raise_error=True):
        return self.id_to_txt[id] if raise_error else (None if id is None else self.id_to_txt.get(id, None))


BASE_CLASS = 'DataObject'

class DataObject(object):
    # dict keyed by class object; value is list of instances of the class
    instancesByClass = defaultdict(list)

    _instances_by_key = {}  # here for completeness; shadowed in generated subclasses
    _table_name = None      # ditto
    _data_table_name = None # ditto

    def __init__(self, key, scenario):
        """
        Append self to a list for our subclass
        """
        cls = self.__class__
        self.instancesByClass[cls].append(self)
        self.scenario = scenario
        self._key = key
        self._child_data = None
        self.children_by_fk_col = {}

    def __str__(self):
        return "<{} {}='{}'>".format(self.__class__._table_name, self._key_col, self._key)

    @classmethod
    def instances(cls):
        """
        Return instances for any subclass of DataObject.
        """
        return DataObject.instancesByClass[cls]

    @classmethod
    def get_instance(cls, key):
        cls._instances_by_key.get(key, None)  # uses each class' internal dict

    def init_from_tuple(self, tup, scenario, **kwargs):
        """
        Generated method
        """
        raise SubclassProtocolError(self.__class__, 'init_from_tuple')

    def init_from_series(self, series, scenario, **kwargs):
        self.init_from_tuple(tuple(series), scenario, **kwargs)

    def init_from_db(self, key, scenario, **kwargs):
        tup = self.__class__.get_row(key)
        self.init_from_tuple(tup, scenario, **kwargs)

    # deprecated?
    # @classmethod
    # def from_tuple(cls, scenario, tup, **kwargs):
    #     """
    #     Generated method
    #     """
    #     raise SubclassProtocolError(cls, 'from_tuple')
    #
    # @classmethod
    # def from_series(cls, scenario, series, **kwargs):
    #     return cls.from_tuple(scenario, tuple(series), **kwargs)
    #
    # @classmethod
    # def from_db(cls, scenario, key, **kwargs):
    #     tup = cls.get_row(key)
    #     obj = cls.from_tuple(scenario, tup, **kwargs)
    #     return obj
    #
    # @classmethod
    # def from_dataframe(cls, scenario, df, **kwargs):
    #     nodes = [cls.from_series(scenario, row, **kwargs) for idx, row in df.iterrows()]
    #     return nodes
    #
    # @classmethod
    # def load_all(cls):
    #     db = get_database()
    #     tbl_name = cls.__name__
    #     tbl = db.get_table(tbl_name)
    #     nodes = cls.from_dataframe(tbl.data)
    #     return nodes

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
        tup = db.get_row_from_table(cls._table_name, cls._key_col, key, raise_error=raise_error)
        return tup

    # TBD: decide whether the default should be copy=True or False
    def load_child_data(self, copy=True):
        """
        If self._data_table_name is set, load the data corresponding to this object
        in a DataFrame as self._child_data

        :param id: (.database.CsvDatabase) the database object
        :param copy: (bool) whether to copy the slice from the child table's DF
        :return: none
        """
        db = get_database()

        if self._data_table_name:
            child_tbl = db.get_table(self._data_table_name)
            parent_col = find_parent_col(self._data_table_name, child_tbl.data.columns)
            query = "{} == '{}'".format(parent_col, self._key)
            slice = child_tbl.data.query(query)

            # TBD: discuss with Ryan & Ben whether to operate on the whole child_data DF or just copy slices
            slice = slice.copy(deep=True) if copy else slice
            self.map_strings(slice)
            self._child_data = slice

    def map_strings(self, df):
        tbl_name = self._data_table_name

        mapper = StringMap.getInstance()
        str_cols = MappedCols.get(tbl_name, [])

        for col in str_cols:
            # Ensure that all values are in the StringMap
            values = df[col].unique()
            for value in values:
                mapper.store(value)

            # mapped column "foo" becomes "foo_id"
            id_col = col + '_id'

            # Force string cols to str and replace 'nan' with None
            df[col] = df[col].astype(str)
            df.loc[df[col] == 'nan', col] = None

            # create a column with integer ids
            df[id_col] = df[col].map(lambda txt: mapper.get_id(txt, raise_error=False))

        if DropStrCols:
            df.drop(str_cols, axis=1, inplace=True)
