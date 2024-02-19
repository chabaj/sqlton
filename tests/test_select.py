from sqlton import parse
from sqlton.ast import Select, SelectCore, Table, All

def test_select():
    query = 'select * from person'
    print(query)
    ast = parse(query)
    
    assert isinstance(ast, Select)
    assert isinstance(ast.select_core, SelectCore)
    assert isinstance(ast.select_core.table_list[0], Table)
    assert ast.select_core.table_list[0].name == 'person'
    assert ast.select_core.table_list[0].schema_name is None
    assert ast.select_core.reduction is None
    assert isinstance(ast.select_core.result_column_list[0], All)
    assert ast.select_core.result_column_list[0].table is None
    
    print(ast)


def test_select_where():
    query = 'select * from person where person.name like "A%"'
    print(query)
    ast = parse(query)
    print(ast)


def test_select_join():
    query = '''select *
               from person
                    LEFT OUTER JOIN telefon
                    RIGHT JOIN home, troll
            '''
    print(query)
    ast = parse(query)
    print(ast)


def test_select_order_by():
    query = '''select *
               from person
               ORDER BY family_name ASC NULLS LAST,
                        fist_name ASC NULLS LAST'''
    print(query)
    ast = parse(query)
    print(ast)


def test_select_call_function_upper():
    query = '''select upper(family_name)
               from person'''
    print(query)
    ast = parse(query)
    print(ast)


def test_select_call_function_concat():
    query = '''select upper(family_name, ',', first_name)
               from person'''
    print(query)
    ast = parse(query)
    print(ast)

def test_select_regexp():
    query = '''select person.family_name, person.first_name
               from person
               where family_name not regexp '\\w+(\\s+\\w+)+' '''
    print(query)
    ast = parse(query)
    print(ast)


def main():
    for key, value in globals().items():
        if key.startswith('test_'):
            value()
