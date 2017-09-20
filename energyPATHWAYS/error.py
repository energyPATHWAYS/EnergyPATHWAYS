#
# Error classes
#

class PathwaysException(Exception):
    pass

class RowNotFound(PathwaysException):
    def __init__(self, table, id):
        self.table = table
        self.id    = id

    def __str__(self):
        return "<RowNotFound table=%s id=%d>" % (self.table, self.id)

class DuplicateRowsFound(PathwaysException):
    def __init__(self, table, id):
        self._table_name = table
        self.id = id

    def __str__(self):
        return "<DuplicateRowsFound table=%s id=%d>" % (self.table, self.id)


class SubclassProtocolError(PathwaysException):
    pass
