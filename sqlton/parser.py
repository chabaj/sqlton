from math import e
from re import match
from itertools import product as _product, chain
from functools import partial
from sly import Lexer as _Lexer, Parser as _Parser
from sqlton.ast import With, Select, SelectCore, Insert, Replace, Update, Operation, Table, Index, All, Column, Alias, Values, CommonTableExpression

def insensitive(word):
    return (''.join(f'({character.lower()}|{character.upper()})'
                   for character in word) +
            r'(?!\w)')

def product(*variations):
    for entry in _product(*variations):
        yield ' '.join(part
                       for part in entry
                       if part is not None)

decimal_number = r'((?P<mantis>([\+-]?\d+(\.\d+)?)|(\.\d+))((e|E)(?P<exponent>[\+-]?\d+))?)'

class Lexer(_Lexer):
    tokens = {RETURNING, IDENTIFIER, COMMA, SEMICOLON, LP, RP, DOT,
              EQUAL, DIFFERENCE,
              LESS_OR_EQUAL, MORE_OR_EQUAL,
              LESS, MORE,
              MULTIPLICATION, DIVISION, PLUS, MINUS,
              NUMERIC_LITERAL,
              STRING_LITERAL,
              BOOLEAN_LITERAL,
              NULL_LITERAL,
              CURRENT_TIME,
              CURRENT_DATE,
              CURRENT_TIMESTAMP,
              WITH, AS, RECURSIVE, NOT, MATERIALIZED,
              SELECT, VALUES, INSERT, REPLACE, UPDATE, SET,
              DISTINCT, ALL,
              UNION, EXCEPT, INTERSECT,
              FROM, INTO,
              ON, NATURAL, INNER, JOIN, LEFT, RIGHT,
              WHERE, GROUP, BY, HAVING,
              AND, OR, 
              IN,
              IS,
              LIKE,
              GLOB,
              REGEXP,
              MATCH,
              EXISTS,
              BETWEEN,
              INDEXED,
              FILTER,
              CAST,
              ORDER, ASC, DESC, COLLATE, NULLS, FIRST, LAST,
              LIMIT, OFFSET, FULL, OUTER, CROSS,
              USING,
              FAIL, ROLLBACK, ABORT, IGNORE,
              DEFAULT}

    CURRENT_TIMESTAMP = insensitive("CURRENT_TIMESTAMP")
    CURRENT_DATE = insensitive("CURRENT_DATE")
    CURRENT_TIME = insensitive("CURRENT_TIME")
    MATERIALIZED = insensitive("MATERIALIZED")
    RETURNING = insensitive("RETURNING")
    INTERSECT = insensitive("INTERSECT")
    RECURSIVE = insensitive("RECURSIVE")
    DISTINCT = insensitive("DISTINCT")
    ROLLBACK = insensitive("ROLLBACK")
    BETWEEN = insensitive("BETWEEN")
    COLLATE = insensitive("COLLATE")
    DEFAULT = insensitive("DEFAULT")
    INDEXED = insensitive("INDEXED")
    REPLACE = insensitive("REPLACE")
    NATURAL = insensitive("NATURAL")
    UPDATE = insensitive("UPDATE")
    IGNORE = insensitive("IGNORE")
    EXCEPT = insensitive("EXCEPT")
    HAVING = insensitive("HAVING")
    SELECT = insensitive("SELECT")
    INSERT = insensitive("INSERT")
    VALUES = insensitive("VALUES")
    OFFSET = insensitive("OFFSET")
    REGEXP = insensitive("REGEXP")
    FILTER = insensitive("FILTER")
    EXISTS = insensitive("EXISTS")
    MATCH = insensitive("MATCH")
    FIRST = insensitive("FIRST")
    ABORT = insensitive("ABORT")
    GROUP = insensitive("GROUP")
    INNER = insensitive("INNER")
    LIMIT = insensitive("LIMIT")
    NULLS = insensitive("NULLS")
    ORDER = insensitive("ORDER")
    OUTER = insensitive("OUTER")
    RIGHT = insensitive("RIGHT")
    UNION = insensitive("UNION")
    USING = insensitive("USING")
    WHERE = insensitive("WHERE")

    ignore = ' \t'

    @_(r'((\r?\n)|\r)+')
    def ignore_newline(self, t):
        self.lineno += max(t.value.count('\n'), t.value.count('\r'))

    @_(*(insensitive(word)
         for word in ('true', 'false')))
    def BOOLEAN_LITERAL(self, t):
        t.value = (t.value.lower() == 'true')
        return t
        
    @_(insensitive('NULL'))
    def NULL_LITERAL(self, t):
        t.value = None
        return t

    FAIL = insensitive("FAIL")
    INTO = insensitive("INTO")
    DESC = insensitive("DESC")
    FROM = insensitive("FROM")
    FULL = insensitive("FULL")
    JOIN = insensitive("JOIN")
    LAST = insensitive("LAST")
    LEFT = insensitive("LEFT")
    WITH = insensitive("WITH")
    LIKE = insensitive("LIKE")
    GLOB = insensitive("GLOB")
    CAST = insensitive("CAST")
    ALL = insensitive("ALL")
    SET = insensitive("SET")
    AND = insensitive("AND")
    ASC = insensitive("ASC")
    NOT = insensitive("NOT")
    AS = insensitive("AS")
    BY = insensitive("BY")
    ON = insensitive("ON")
    OR = insensitive("OR")
    IN = insensitive("IN")
    IS = insensitive("IS")
    
    IDENTIFIER = r'[a-zA-Z_]\w*'

    COMMA = r','
    SEMICOLON = r';'
    DOT = r'\.'
    LP = r'\('
    RP = r'\)'

    DIFFERENCE = r'(<>)|(!=)'
    LESS_OR_EQUAL = r'<='
    MORE_OR_EQUAL = r'>='
    EQUAL = r'='
    LESS = r'<'
    MORE = r'>'
    PLUS = r'\+'
    MINUS = r'-'
    MULTIPLICATION = r'\*'
    DIVISION = r'/'
    
    @_(decimal_number,
       r'0x[\dA-Fa-f]+')
    def NUMERIC_LITERAL(self, t):
        if t.value.startswith('0x'):
            t.value = int(t.value[2:], 16)
            return t
        
        value = t.value
        if t.value.startswith('.'):
            value = '0' + t.value

        groups = {key:((int if not '.' in value else float)(value)
                       if value is not None
                       else 0)
                  for key, value
                  in match(decimal_number, value).groupdict().items()}

        t.value = groups['mantis']
        
        if 'exponent' in groups.keys() and groups.get('exponent') != 0:
            t.value *= (e ** groups.get('exponent'))
        
        return t
        
    @_(r'"[^"]*"',
       r'\'[^\']*\'')
    def STRING_LITERAL(self, t):
        t.value = t.value[1:-1]
        return t


class Parser(_Parser):
    tokens = Lexer.tokens
    start = 'statement'
    precedence = (('left', EQUAL, DIFFERENCE, LESS_OR_EQUAL, MORE_OR_EQUAL, LESS, MORE),
                  ('left', PLUS, MINUS),
                  ('left', MULTIPLICATION, DIVISION))


    @_('statement SEMICOLON',
       'statement')
    def statement_list(self, p):
        return (p.statement)

    @_('statement SEMICOLON statement_list')
    def statement_list(self, p):
        return tuple(chain((p.statement,), p.statement_list))
    
    @_('insert', 'select', 'update')
    def statement(self, p):
        return p[0]
    
    @_(*product(('with_clause', None),
                ('select_core',),
                ('order_by', None),
                ('limit', None)))
    def select(self, p):
        kwargs = dict((key.lower(), getattr(p, key))
                      for key in p._namemap.keys())
        return Select(**kwargs)

    # TODO: upsert close
    @_(*product(('with_clause', None),
                ('insert_directive INTO',),
                ('insert_target',),
                ('LP column_name_list RP', None),
                ('DEFAULT VALUES',
                 *product(('values', 'select'),
                          #(None, 'upsert_clause')
                          )),
                (None, 'returning_clause')
                ))
    def insert(self, p):
        insert_directive = p.insert_directive

        directive = insert_directive[0]
        Directive = {'INSERT':Insert,
                     'REPLACE':Replace}[directive]
        alternative = insert_directive[1] if len(insert_directive) > 1 else None
        
        return Directive(with_clause=p.with_clause if hasattr(p, 'with_clause') else None,
                         alternative=alternative,
                         target=p.insert_target,
                         columns=p.column_name_list if hasattr(p, 'column_name_list') else (All(),),
                         values=p.values if hasattr(p, 'values') else (p.select if hasattr(p, 'select') else None),
                         upsert=p.upsert_clause if hasattr(p, 'upsert_clause') else None,
                         returns=p.returning_clause if hasattr(p, 'returning_clause') else None)

    @_('REPLACE',
       *product(('INSERT',),
                (None,
                 *product(('OR',),
                          ('ABORT', 'FAIL', 'IGNORE', 'REPLACE', 'ROLLBACK')))))
    def insert_directive(self, p):
        if len(p) == 1:
            return (p[0].upper(),)
        
        return (p[0].upper(), p[-1].upper())

    @_(*product(('IDENTIFIER DOT', None),
                ('IDENTIFIER',),
                ('AS IDENTIFIER', None)))
    def insert_target(self, p):
        table = Table(p[0])
        
        if hasattr(p, 'DOT'):
            table = Table(p[2], p[0])

        if hasattr(p, 'AS'):
            table = Alias(table, p[-1])
        
        return table

    @_(*product(('with_clause', None),
                ('UPDATE alternative insert_target SET assignment_list',),
                (None, 'FROM table_list'),
                (None, 'where'),
                (None, 'returning_clause')))
    def update(self, p):
        return Update(with_clause=p.with_clause if hasattr(p, 'with_clause') else None,
                      alternative=p.alternative,
                      target=p.insert_target,
                      assignments=p.assignment_list,
                      tables=p.table_list if hasattr(p, 'table_list') else None,
                      where=p.where if hasattr(p, 'where') else None,
                      returns=p.returning_clause if hasattr(p, 'returning_clause') else None)

    @_('',
       *product(('OR',),
                ('ABORT', 'FAIL', 'IGNORE', 'REPLACE', 'ROLLBACK')))
    def alternative(self, p):
        return (p[1] if hasattr(p, 'OR') else None)
    
    @_('assignment')
    def assignment_list(self, p):
        return (p.assignment,)
        
    @_('assignment COMMA assignment_list')
    def assignment_list(self, p):
        return (p.assignment, *p.assignment_list)
    
    @_('LP column_name_list RP EQUAL expr')
    def assignment(self, p):
        return (p.column_name_list, p.expr)

    @_('IDENTIFIER EQUAL expr')
    def assignment(self, p):
        return ((p.IDENTIFIER,), p.expr)
    
        
    @_('RETURNING result_column_list')
    def returning_clause(self, p):
        return p.result_column_list


    @_(*product(('WITH',),
                ('RECURSIVE', None),
                ('cte_list',)))
    def with_clause(self, p):
        return With(p.cte_list)

    @_('cte')
    def cte_list(self, p):
        return (p.cte,)

    @_('cte COMMA cte_list')
    def cte_list(self, p):
        return tuple(chain((p.cte,), p.cte_list))
    
    @_(*product(('IDENTIFIER',),
                ('LP column_name_list RP', None),
                ('AS',),
                ('NOT MATERIALIZED', 'MATERIALIZED', None),
                ('LP select_core RP',)))
    def cte(self, p):
        materialized = None

        if hasattr(p, 'MATERIALIZED'):
            materialized = not hasattr(p, 'NOT')
        
        return CommonTableExpression(p.IDENTIFIER, materialized, p.select_core)

    @_('IDENTIFIER')
    def column_name_list(self, p):
        return (p.IDENTIFIER,)

    @_('IDENTIFIER COMMA column_name_list')
    def column_name_list(self, p):
        return tuple(chain((p.IDENTIFIER,), p.column_name_list))

    @_(*product(('SELECT',),
                ('reduction',),
                ('result_column_list',),
                ('FROM',),
                ('table_list',),
                (None, 'where'),
                (None, 'group'),
                (None, 'having'),
                #(None, 'window')
                ))
    def select_core(self, p):
        kwargs = dict((key.lower(), getattr(p, key))
                      for key in p._namemap.keys()
                      if key not in ('SELECT', 'FROM'))
        return SelectCore(**kwargs)

    @_('values')
    def select_core(self, p):
        return p.values
    
    @_('VALUES row_list')
    def values(self, p):
        return Values(p.row_list)

    @_('LP expr_list RP')
    def row_list(self, p):
        return (p.expr_list,)

    @_('LP expr_list RP COMMA row_list')
    def row_list(self, p):
        return tuple(chain((p.expr_list,), p.row_list))
    

    @_('select_core set_operator select_core')
    def select_core(self, p):
        return Operation(p.set_operator, p[0], p[2])

    @_('UNION ALL',
       'UNION',
       'INTERSECT',
       'EXCEPT')
    def set_operator(self, p):
        return tuple(p[index].upper()
                     for index
                     in range(len(p)))
    
    @_('DISTINCT',
       'ALL',
       '')
    def reduction(self, p):
        return (p[0].upper() if len(p) else None)

    @_('result_column')
    def result_column_list(self, p):
        return (p[0],)

    @_('result_column COMMA result_column_list')
    def result_column_list(self, p):
        return tuple(chain((p.result_column,), p.result_column_list))

    @_('IDENTIFIER DOT IDENTIFIER DOT MULTIPLICATION')
    def result_column(self, p):
        return All(Table(p[2], p[0]))

    @_('IDENTIFIER DOT MULTIPLICATION')
    def result_column(self, p):
        return All(Table(p[0]))

    @_('MULTIPLICATION')
    def result_column(self, p):
        return All()

    @_('expr')
    def result_column(self, p):
        return p[0]

    @_(*product(('expr',),
                (None, 'AS'),
                ('IDENTIFIER', 'STRING_LITERAL')))
    def result_column(self, p):
        return Alias(p.expr, p[-1])

    @_('table')
    def table_list(self, p):
        return (p.table,)

    @_('table COMMA table_list')
    def table_list(self, p):
        return tuple(chain((p.table,), p.table_list))

    @_(*product(('IDENTIFIER DOT IDENTIFIER', 'IDENTIFIER'),
                ('AS', None),
                ('IDENTIFIER', None),
                ('INDEXED BY IDENTIFIER', 'NOT INDEXED', None)
                ))
    def table(self, p):
        schema_name = None
        alias = None
        index_name = None
        table_name = None

        if hasattr(p, 'DOT'):
            schema_name = p[0]
            table_name = p[2]
        else:
            table_name = p[0]
        

        if hasattr(p, 'AS'):
            if schema_name:
                alias = p[4]
            else:
                alias = p[2]
        else:
            if schema_name and table_name:
                offset = 3
            else:
                offset = 1

            if len(p) > offset:
                if not hasattr(p, 'INDEXED') or not p[offset] in ('INDEXED', 'NOT'):
                    alias = p[offset]

        if hasattr(p, 'INDEXED') and hasattr(p, 'BY'):
            index_name = p[-1]

        table = Table(table_name, schema_name)

        if index_name is not None:
            table = Index(table, index_name)
        
        if alias is not None:
            table = Alias(table, alias)

        return table

    # @_(*product(('IDENTIFIER DOT', None),
    #             ('table_function_name LP expr_list RP',),
    #             ('AS', None),
    #             ('table_alias',)))
    # def table(self, p):
    #     return Function(**p)

    @_(*product(('LP select_core RP',),
                ('AS IDENTIFIER', 'IDENTIFIER', None)))
    def table(self, p):
        if hasattr(p, 'IDENTIFIER'):
            return Alias(p.select_core, p.IDENTIFIER)
        return p.select_core

    @_('LP table_list RP')
    def table(self, p):
        return p.table_list

    @_('table join_operation')
    def table(self, p):
        return Operation(p.join_operation[0], p.table, p.join_operation[1])

    @_('join_operator table join_constraint')
    def join_operation(self, p):
        return (('JOIN', *p.join_operator, p.join_constraint), p.table)

    @_('JOIN',
       'CROSS JOIN',
       *product(('NATURAL', None),
                ('LEFT', 'RIGHT', 'FULL',),
                ('OUTER', None),
                ('JOIN',)),
       *product(('NATURAL', None),
                ('INNER',),
                ('JOIN',)))
    def join_operator(self, p):
        return tuple(p[index].upper()
                     for index
                     in range(len(p))
                     if p[index].upper() != 'JOIN')

    @_('ON expr')
    def join_constraint(self, p):
        return ('ON', p.expr)

    @_('USING LP column_name_list RP')
    def join_constraint(self, p):
        return ('USING', p.column_name_list)

    @_('')
    def join_constraint(self, p):
        return None
    
    @_('WHERE expr')
    def where(self, p):
        return p.expr

    @_('GROUP BY expr_list')
    def group(self, p):
        return p.expr_list

    @_('HAVING expr')
    def having(self, p):
        return p.expr

    @_('ORDER BY ordering_term_list')
    def order_by(self, p):
        return p.ordering_term_list

    @_('ordering_term')
    def ordering_term_list(self, p):
        return (p.ordering_term,)

    @_('ordering_term COMMA ordering_term_list')
    def ordering_term_list(self, p):
        return tuple(chain((p.ordering_term,),
                           p.ordering_term_list))

    @_(*product(('expr',),
                ('COLLATE IDENTIFIER', None),
                (None, 'ASC', 'DESC'),
                (None, 'NULLS FIRST', 'NULLS LAST')))
    def ordering_term(self, p):
        return (p.expr,
                p.IDENTIFIER if hasattr(p, 'COLLATE') else None,
                p.ASC.upper() if hasattr(p, 'ASC') else (p.DESC.upper() if hasattr(p, 'DESC') else None),
                ('FIRST' if hasattr(p, 'FIRST') else 'LAST') if hasattr(p, 'NULLS') else None)


    # # TODO: .. complex
    # # @_('WINDOW ...')
    # # def window(self, p):
    # #     return ...

    @_('LIMIT expr',
       'LIMIT expr OFFSET expr',
       'LIMIT expr COMMA expr')
    def limit(self, p):
        if hasattr(p, 'OFFSET'):
            return (p[1], p[3])
        elif hasattr(p, 'COMMA'):
            return (p[3], p[1])
        else:
            return (p[1], 0)

    @_('expr COMMA expr_list')
    def expr_list(self, p):
        return tuple(chain((p.expr,), p.expr_list))

    @_('expr')
    def expr_list(self, p):
        return (p.expr,)
    
    @_('LP expr RP')
    def expr(self, p):
        return p[1]

    @_('NUMERIC_LITERAL',
       'STRING_LITERAL',
       'BOOLEAN_LITERAL',
       'NULL_LITERAL')
    def expr(self, p):
        return p[0]

    @_('expr COLLATE IDENTIFIER')
    def expr(self, p):
        return ('COLLATE', p.expr, p.IDENTIFIER)
    
    @_('expr BETWEEN expr AND expr')
    def expr(self, p):
        return Operation(('AND',), Operation(('MORE_OR_EQUAL',), p[2], p[0]), Operation(('LESS_OR_EQUAL',), p[4], p[0]))

    @_('expr NOT BETWEEN expr AND expr')
    def expr(self, p):
        return Operation(('AND',), Operation(('LESS',), p[3], p[0]), Operation(('MORE',), p[5], p[0]))
    
    @_('expr binary_operator expr')
    def expr(self, p):
        if p.binary_operator[0] == 'NOT':
            return Operation(('NOT',), None, Operation((p.binary_operator[1],), p[0], p[-1]))
        else:
            return Operation(p.binary_operator, p[0], p[-1])

    @_('unary_operator expr')
    def expr(self, p):
        return Operation(p.unary_operator, None, p[-1])
    
    @_('IDENTIFIER DOT IDENTIFIER DOT IDENTIFIER')
    def column(self, p):
        return Column(p[4], Table(p[2], p[0]))
    
    @_('IDENTIFIER DOT IDENTIFIER')
    def column(self, p):
        return Column(p[2], Table(p[0]))

    @_('IDENTIFIER')
    def column(self, p):
        return Column(p[0])

    @_('column')
    def expr(self, p):
        return p.column


    @_(*product(('DISTINCT', None),
                ('expr_list',),
                ('order_by', None)))
    def arguments(self, p):
        return {'arguments': p.expr_list,
                'distinct': hasattr(p, 'DISTINCT'),
                'order_by': (p.order_by
                             if hasattr(p, 'order_by')
                             else ())}

    @_('MULTIPLICATION')
    def arguments(self, p):
        return {'arguments': All(),
                'distinct': False,
                'order_by': ()}

    @_('')
    def arguments(self, p):
        return {'arguments': (),
                'distinct': False,
                'order_by': ()}

    @_('FILTER LP WHERE expr RP')
    def filter_clause(self, p):
        return p.expr
    
    # TODO: over_clause
    @_('IDENTIFIER LP arguments RP',
       'IDENTIFIER LP arguments RP filter_clause',
       #'IDENTIFIER LP arguments RP over_clause',
       #'IDENTIFIER LP arguments RP filter_clause over_clause')
       )
    def expr(self, p):
        parameter = p.arguments
        
        if hasattr(p, 'filter_clause'):
            parameter |= {'filter': p.filter_clause}
        else:
            parameter |= {'filter': None}
        
        return Operation(('CALL',),
                         p.IDENTIFIER,
                         parameter)

    @_('CAST LP expr AS IDENTIFIER RP')
    def expr(self, p):
        return Operation(('CAST',),
                         p.expr,
                         p.IDENTIFIER)

    @_('EXISTS LP select RP')
    def expr(self, p):
        return Operation(('EXISTS',),
                         p.select)
    
    # todo solve order of operators
    @_('EQUAL',
       'DIFFERENCE',
       'LESS_OR_EQUAL', 'MORE_OR_EQUAL',
       'LESS', 'MORE',
       'MULTIPLICATION',
       'DIVISION',
       'PLUS',
       'MINUS',
       'AND',
       'OR',
       'IN',
       'LIKE',
       'GLOB',
       'REGEXP',
       'MATCH')
    def binary_operator(self, p): 
       return tuple(p._namemap.keys())

    @_(*product(('NOT',),
                ('IN', 'LIKE', 'GLOB', 'REGEXP', 'MATCH')))
    def binary_operator(self, p):
       return ('NOT', p[1].upper())
    
    @_('PLUS',
       'MINUS',
       'NOT')
    def unary_operator(self, p):
        return (p[0].upper(),)

if __name__ == '__main__':
    from sys import argv
    lexer = Lexer()

    tokens = list(lexer.tokenize(argv[-1]))
    #'select pertson.firstname, person.surname, person.birthdate\nfrom person\nwhere age >= 11.5 and age < 18')
    
    # for token in tokens:
    #     print(token)
        
    parser = Parser()

    ast = parser.parse(iter(tokens))
    print(ast)
