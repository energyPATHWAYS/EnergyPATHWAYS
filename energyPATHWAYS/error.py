#
# Error classes
#

class PathwaysException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

class RowNotFound(PathwaysException):
    def __init__(self, table, key):
        msg = "Row not found for key {} in table '{}'".format(key, table)
        super(RowNotFound, self).__init__(msg)


class DuplicateRowsFound(PathwaysException):
    def __init__(self, table, key):
        msg = "Duplicate rows found for key {} in table '{}'".format(key, table)
        super(DuplicateRowsFound, self).__init__(msg)


class UnknownDataClass(PathwaysException):
    def __init__(self, classname):
        msg = 'Unknown data classname "{}"'.format(classname)
        super(UnknownDataClass, self).__init__(msg)

class MissingParentIdColumn(PathwaysException):
    def __init__(self, table):
        msg = 'Table "{}" has no known parent ID column'.format(table)
        super(MissingParentIdColumn, self).__init__(msg)

class SubclassProtocolError(PathwaysException):
    def __init__(self, cls, method):
        msg = 'Class "{}" fails to implement method "{}"'.format(cls.__name__, method)
        super(SubclassProtocolError, self).__init__(msg)
