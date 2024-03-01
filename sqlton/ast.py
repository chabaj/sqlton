from itertools import chain
from collections import namedtuple 

Operation = namedtuple('Operation', ('operator', 'a', 'b'))

class __Container:
    def __init__(self, **kwargs):
        self.__attrs = set(kwargs.keys())
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        return f"{type(self).__name__}({', '.join(key + '=' + repr(getattr(self, key)) for key in self.__attrs)})"


class Statement(__Container):
    pass


class Select(Statement):
    pass


class Insert(Statement):
    pass


class Replace(Statement):
    pass


class Update(Statement):
    pass


class Delete(Statement):
    pass


class SelectCore(__Container):
    pass


With = namedtuple('With', ('ctes',))

CommonTableExpression = namedtuple('CommonTableExpression', ('name', 'columns', 'materialized', 'select'))
    
Table = namedtuple('Table', ('name', 'schema_name'), defaults=(None,))

Index = namedtuple('Index', ('table', 'name'))

Column = namedtuple('Column', ('name', 'table'), defaults=(None,))

All = namedtuple('All', ('table',), defaults=(None,))

Alias = namedtuple('Alias', ('original', 'replacement'))

Values = namedtuple('Values', ('values'))
