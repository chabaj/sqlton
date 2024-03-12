from sqlton import parse
from sqlton.ast import Replace, Insert


def test_insert():
    ast, = parse('insert into table (a, b) values (1, 2), (3, "4")')
    print(ast)


def test_insert_select():
    ast, = parse('insert into table (a, b) select a,b from another_table')
    print(ast)


def test_insert_default():
    ast, = parse('insert into table (a, b) default values')
    print(ast)

def test_replace_default():
    ast, = parse('replace into table (a, b) default values')
    print(ast)
