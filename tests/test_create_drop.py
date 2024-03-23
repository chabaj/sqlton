from sqlton import parse
from sqlton.ast import Select, SelectCore, Table, All

def test_create():
    query = 'create table t (a integer, b text, c)'
    ast, = parse(query)
    
    print(ast)


def test_drop():
    query = 'drop table t'
    ast, = parse(query)
    print(ast)


def main():
    for key, value in globals().items():
        if key.startswith('test_'):
            value()
