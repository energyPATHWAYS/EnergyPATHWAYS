#
# Error classes
#

class PathwaysException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class RowNotFound(PathwaysException):
    def __init__(self, table, id):
        msg = "Row not found for id %d in table '%s'" % (id, table)
        super(RowNotFound, self).__init__(msg)


class DuplicateRowsFound(PathwaysException):
    def __init__(self, table, id):
        msg = "Duplicate rows found for id %d in table '%s'" % (id, table)
        super(DuplicateRowsFound, self).__init__(msg)


class UnknownDataClass(PathwaysException):
    def __init__(self, classname):
        msg = 'Unknown data classname "%s"' % classname
        super(UnknownDataClass, self).__init__(msg)


class SubclassProtocolError(PathwaysException):
    def __init__(self, cls, method):
        msg = 'Class "%s" fails to implement method "%s"' % (cls.__name__, method)
        super(SubclassProtocolError, self).__init__(msg)
