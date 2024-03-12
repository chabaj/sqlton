from math import e
from re import match
from itertools import product as _product
from functools import partial
from sly import Lexer as _Lexer, Parser as _Parser
from sqlton.ast import With, Select, SelectCore, Delete, Insert, Replace, Update, Operation, Table, Index, All, Column, Alias, Values, CommonTableExpression

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
              SELECT, VALUES, INSERT, REPLACE, UPDATE, DELETE, SET,
              DISTINCT, ALL,
              UNION, EXCEPT, INTERSECT,
              FROM, INTO,
              ON, NATURAL, INNER, JOIN, LEFT, RIGHT,
              WHERE, GROUP, BY, HAVING,
              AND, OR, 
              IN, IS,
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
              DEFAULT,
              INTEGER,
              NUMERIC,
              CHAR,
              CLOB,
              DOUB,
              FLOA,
              REAL,
              TEXT,
              DECIMAL}

    CURRENT_TIMESTAMP = insensitive("CURRENT_TIMESTAMP")
    CURRENT_DATE = insensitive("CURRENT_DATE")
    CURRENT_TIME = insensitive("CURRENT_TIME")
    MATERIALIZED = insensitive("MATERIALIZED")
    RETURNING = insensitive("RETURNING")
    INTERSECT = insensitive("INTERSECT")
    RECURSIVE = insensitive("RECURSIVE")
    DISTINCT = insensitive("DISTINCT")
    ROLLBACK = insensitive("ROLLBACK")
    INTEGER = insensitive("INTEGER")
    NUMERIC = insensitive("NUMERIC")
    BETWEEN = insensitive("BETWEEN")
    COLLATE = insensitive("COLLATE")
    DEFAULT = insensitive("DEFAULT")
    INDEXED = insensitive("INDEXED")
    DECIMAL = insensitive("DECIMAL")
    REPLACE = insensitive("REPLACE")
    NATURAL = insensitive("NATURAL")
    DELETE = insensitive("DELETE")
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

    CHAR = insensitive("CHAR")
    CLOB = insensitive("CLOB")
    DOUB = insensitive("DOUB")
    FLOA = insensitive("FLOA")
    REAL = insensitive("REAL")
    TEXT = insensitive("TEXT")
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
    
    @_(r'([a-zA-Z_]\w*)',
       r'(`[^`]*`)')
    def IDENTIFIER(self, t):
       if t.value[0] == '`' and t.value[-1] == '`':
           t.value = t.value[1:-1]
       return t

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
    start = 'statement_list'
    
    precedence = (
        ('left', SEMICOLON),
        ('left', COMMA),
        ('left', UNION),
        ('left', INTERSECT),
        ('left', EXCEPT),
        ('left', CROSS, NATURAL, FULL, RIGHT, LEFT, JOIN),
        ('left', USING, ON),
        ('left', OR),
        ('left', AND),
        ('left', EQUAL, DIFFERENCE, LESS_OR_EQUAL, MORE_OR_EQUAL, LESS, MORE, MATCH, LIKE, GLOB),
        ('left', PLUS, MINUS),
        ('left', MULTIPLICATION, DIVISION),
        ('left', IN),
        ('left', NOT),
        ('right', UNOT),
        ('right', UPLUS),
        ('right', UMINUS),
        ('right', UALL),
    )


    @_('_statement_list SEMICOLON',
       '_statement_list')
    def statement_list(self, p):
        return p._statement_list
        
    @_('_statement_list SEMICOLON statement')
    def _statement_list(self, p):
        return (*p._statement_list, p.statement)
    
    @_('statement')
    def _statement_list(self, p):
        return (p.statement,)

    @_('delete', 'insert', 'select', 'update')
    def statement(self, p):
        item = p[0]
        
        if isinstance(item, Operation):
            return Select(select_core=item)
        
        return item
    
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
                 *product(('select_core',),
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
                         values=p.select_core if hasattr(p, 'select_core') else None,
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
                ('AS IDENTIFIER', 'AS STRING_LITERAL', None)))
    def insert_target(self, p):
        table = Table(p[0])
        
        if hasattr(p, 'DOT'):
            table = Table(p[2], p[0])

        if hasattr(p, 'AS'):
            table = Alias(table, p[-1])
        
        return table

    @_(*product((None, 'with_clause'),
                ('UPDATE',),
                (None, 'alternative'),
                ('insert_target SET assignment_list',),
                (None, 'FROM table_list'),
                (None, 'where'),
                (None, 'returning_clause')))
    def update(self, p):
        return Update(with_clause=p.with_clause if hasattr(p, 'with_clause') else None,
                      alternative=p.alternative if hasattr(p, 'alternative') else None,
                      target=p.insert_target,
                      assignments=p.assignment_list,
                      tables=p.table_list if hasattr(p, 'table_list') else None,
                      where=p.where if hasattr(p, 'where') else None,
                      returns=p.returning_clause if hasattr(p, 'returning_clause') else None)

    @_(*product(('with_clause', None),
                ('DELETE FROM table',),
                (None, 'where',),
                (None, 'returning_clause')))
    def delete(self, p):
        return Delete(with_clause=p.with_clause if hasattr(p, 'with_clause') else None,
                      target=p.table,
                      where=p.where if hasattr(p, 'where') else None,
                      returns=p.returning_clause if hasattr(p, 'returning_clause') else None)
    
    
    @_(*product(('OR',),
                ('ABORT', 'FAIL', 'IGNORE', 'REPLACE', 'ROLLBACK')))
    def alternative(self, p):
        return (p[1] if hasattr(p, 'OR') else None)
    
    @_('assignment')
    def assignment_list(self, p):
        return (p.assignment,)
        
    @_('assignment COMMA assignment_list')
    def assignment_list(self, p):
        return (p.assignment, *p.assignment_list)
    
    @_(*product(('LP column_name_list RP EQUAL',),
                ('expr_boolean', 'expr_numeric', 'expr_string', 'expr_null', 'column', 'call')))
    def assignment(self, p):
        return (p.column_name_list, p[-1])

    @_(*product(('IDENTIFIER EQUAL',),
                ('expr_boolean', 'expr_numeric', 'expr_string', 'expr_null', 'column', 'call')))
    def assignment(self, p):
        return ((p.IDENTIFIER,), p[-1])
    
        
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
        return (p.cte, *p.cte_list)
    
    @_(*product(('IDENTIFIER',),
                ('LP column_name_list RP', None),
                ('AS',),
                ('NOT MATERIALIZED', 'MATERIALIZED', None),
                ('LP select RP',)))
    def cte(self, p):
        materialized = None

        if hasattr(p, 'MATERIALIZED'):
            materialized = not hasattr(p, 'NOT')
        
        return CommonTableExpression(p.IDENTIFIER, p.column_name_list, materialized, p.select)

    @_('IDENTIFIER')
    def column_name_list(self, p):
        return (p.IDENTIFIER,)

    @_('IDENTIFIER COMMA column_name_list')
    def column_name_list(self, p):
        return (p.IDENTIFIER, *p.column_name_list)

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

    @_('VALUES row_list')
    def select_core(self, p):
        return Values(p.row_list)

    @_('LP expr_list RP')
    def row_list(self, p):
        return (p.expr_list,)

    @_('LP expr_list RP COMMA row_list')
    def row_list(self, p):
        return (p.expr_list, *p.row_list)
    

    @_(*product(('select',),
                ('UNION ALL',
                 'UNION', 'INTERSECT', 'EXCEPT'),
                ('select %prec UALL',)))
    def select(self, p):
        return Operation(tuple(p[index].upper()
                               for index
                               in range(1, len(p) - 1)),
                         p[0], p[-1])
    
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
        return (p.result_column, *p.result_column_list)

    @_('IDENTIFIER DOT IDENTIFIER DOT MULTIPLICATION')
    def result_column(self, p):
        return All(Table(p[2], p[0]))

    @_('IDENTIFIER DOT MULTIPLICATION')
    def result_column(self, p):
        return All(Table(p[0]))

    @_('MULTIPLICATION')
    def result_column(self, p):
        return All()

    @_('expr_boolean', 'expr_numeric', 'expr_string', 'expr_null', 'column', 'call')
    def result_column(self, p):
        return p[0]

    @_(*product(('expr_boolean', 'expr_numeric', 'expr_string', 'expr_null', 'column', 'call'),
                (None, 'AS'),
                ('IDENTIFIER', 'STRING_LITERAL')))
    def result_column(self, p):
        return Alias(p[0], p[-1])

    @_('table')
    def table_list(self, p):
        return (p.table,)

    @_('table COMMA table_list')
    def table_list(self, p):
        return (p.table, *p.table_list)

    @_(*product(('IDENTIFIER DOT IDENTIFIER', 'IDENTIFIER'),
                ('AS', None),
                ('IDENTIFIER', 'STRING_LITERAL', None),
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

    @_(*product(('LP select RP',),
                ('AS IDENTIFIER', 'AS STRING_LITERAL', 'IDENTIFIER', 'STRING_LITERAL', None)))
    def table(self, p):
        if hasattr(p, 'IDENTIFIER'):
            return Alias(p.select, p.IDENTIFIER)
        if hasattr(p, 'STRING_LITERAL'):
            return Alias(p.select, p.STRING_LITERAL)
        return p.select

    @_('LP table_list RP')
    def table(self, p):
        return p.table_list

    @_(*product(('table',),
                (None,
                 'CROSS',
                 *product(('NATURAL', None),
                          ('LEFT', 'RIGHT', 'FULL',),
                          ('OUTER', None)),
                 *product(('NATURAL', None),
                          ('INNER',))),
                ('JOIN table',),
                ('ON expr_boolean',
                 'USING LP column_name_list RP',
                 None)))
    def table(self, p):
        operator = ('JOIN',)

        if hasattr(p, 'NATURAL'):
            operator = (*operator, 'NATURAL')
            
        for direction in ('LEFT', 'RIGHT', 'FULL'):
            if hasattr(p, direction):
                operator = (*operator, direction)

        for location in ('OUTER', 'INNER'):
            if hasattr(p, location):
                operator = (*operator, location)
        
        constraint = None
        
        if hasattr(p, 'ON'):
            constraint = ('ON', p.expr_boolean)
        elif hasattr(p, 'USING'):
            constraint = ('USING', p.column_name_list)

        return Operation((*operator, constraint),
                         p.table0, p.table1)
    
    @_(*product(('WHERE',),
                ('expr_boolean', 'expr_numeric', 'expr_string', 'expr_null', 'column', 'call')))
    def where(self, p):
        return p.expr_boolean

    @_('GROUP BY expr_list')
    def group(self, p):
        return p.expr_list

    @_(*product(('HAVING',),
                ('expr_boolean', 'expr_numeric', 'expr_string', 'expr_null', 'column', 'call')))
    def having(self, p):
        return p.expr_boolean

    @_('ORDER BY ordering_term_list')
    def order_by(self, p):
        return p.ordering_term_list

    @_('ordering_term')
    def ordering_term_list(self, p):
        return (p.ordering_term,)

    @_('ordering_term COMMA ordering_term_list')
    def ordering_term_list(self, p):
        return (p.ordering_term, *p.ordering_term_list)

    @_(*product(('expr_string', 'column', 'call'),
                (None, 'ASC', 'DESC'),
                (None, 'NULLS FIRST', 'NULLS LAST')))
    def ordering_term(self, p):
        return (p[0],
                p.ASC.upper() if hasattr(p, 'ASC') else (p.DESC.upper() if hasattr(p, 'DESC') else None),
                ('FIRST' if hasattr(p, 'FIRST') else 'LAST') if hasattr(p, 'NULLS') else None)


    # # TODO: .. complex
    # # @_('WINDOW ...')
    # # def window(self, p):
    # #     return ...

    @_(*product(('LIMIT',),
                ('expr_numeric', 'call', 'column'),
                (None, *product(('OFFSET', 'COMMA'),
                                ('expr_numeric', 'call', 'column')))))
    def limit(self, p):
        if hasattr(p, 'OFFSET'):
            return (p[1], p[3])
        elif hasattr(p, 'COMMA'):
            return (p[3], p[1])
        else:
            return (p[1], 0)

    @_(*product(('expr_boolean', 'expr_numeric', 'expr_string', 'expr_null', 'column', 'call'),
                ('COMMA expr_list',)))
    def expr_list(self, p):
        return (p[0], *p.expr_list)

    @_('expr_boolean', 'expr_numeric', 'expr_string', 'expr_null', 'column', 'call')
    def expr_list(self, p):
        return (p[0],)
    
    @_('LP expr_boolean RP')
    def expr_boolean(self, p):
        return p[1]

    @_('LP expr_numeric RP')
    def expr_numeric(self, p):
        return p[1]

    @_('LP expr_string RP')
    def expr_string(self, p):
        return p[1]

    @_('LP expr_null RP')
    def expr_null(self, p):
        return p[1]
    
    @_('BOOLEAN_LITERAL')
    def expr_boolean(self, p):
        return p[0]
    
    @_('NUMERIC_LITERAL')
    def expr_numeric(self, p):
        return p[0]

    @_('STRING_LITERAL')
    def expr_string(self, p):
        return p[0]
       
    @_('NULL_LITERAL')
    def expr_null(self, p):
        return p[0]

    @_(*product(('expr_string', 'call', 'column'),
                (' COLLATE IDENTIFIER',)))
    def expr_string(self, p):
        return Operation(('COLLATE',), p[0], p.IDENTIFIER)
    
    @_(*product(('expr_numeric', 'call', 'column'),
                ('BETWEEN',),
                ('expr_numeric', 'call', 'column'),
                ('AND',),
                ('expr_numeric', 'call', 'column')))
    def expr_boolean(self, p):
        return Operation(('AND',),
                         Operation(('MORE_OR_EQUAL',),
                                   p[2], p[0]),
                         Operation(('LESS_OR_EQUAL',),
                                   p[4], p[0]))

    @_(*product(('expr_numeric', 'call', 'column'),
                ('NOT BETWEEN',),
                ('expr_numeric', 'call', 'column'),
                ('AND',),
                ('expr_numeric', 'call', 'column'),
                ('%prec UNOT',)))
    def expr_boolean(self, p):
        return Operation(('AND',),
                         Operation(('LESS',), p[3], p[0]),
                         Operation(('MORE',), p[5], p[0]))
    
    @_(*product(('expr_boolean', 'expr_numeric', 'expr_string', 'expr_null', 'column', 'call'),
                (None, 'NOT'),
                ('IN LP select RP',)))
    def expr_boolean(self, p):
        if hasattr(p, 'NOT'):
            operator = ('NOT', 'IN')
        else:
            operator = ('IN',)
        
        return Operation(operator,
                         p[0], p.select)

    @_(*product(('expr_boolean', 'expr_numeric', 'expr_string', 'expr_null', 'column', 'call'),
                (None, 'NOT'),
                ('IN LP expr_list RP',)))
    def expr_boolean(self, p):
        if hasattr(p, 'NOT'):
            operator = ('NOT', 'IN')
        else:
            operator = ('IN',)
        
        return Operation(operator, p[0], p.expr_list)

    def expr_binary(self, p):
        return Operation(tuple(p[index].upper()
                               for index in range(1, len(p) - 1)),
                         p[0],
                         p[-1])
    
    @_(*product(('expr_boolean', 'expr_numeric', 'expr_string', 'expr_null',
                 'column', 'call'),
                ('EQUAL', 'DIFFERENCE'),
                ('expr_boolean', 'expr_numeric', 'expr_string', 'expr_null',
                 'column', 'call')))
    def expr_boolean(self, p):
        return self.expr_binary(p)

    @_(*product(('expr_boolean', 'expr_numeric', 'expr_string', 'expr_null',
                 'column', 'call'),
                ('IS',),
                ('NOT', None),
                ('NULL_LITERAL',)))
    def expr_boolean(self, p):
        return Operation(('!=' if hasattr(p, 'NOT') else '=',),
                         p[0],
                         None)
    
    @_(*product(('expr_numeric', 'column', 'call'),
                ('LESS_OR_EQUAL', 'MORE_OR_EQUAL',
                 'LESS', 'MORE'),
                ('expr_numeric', 'column', 'call')))
    def expr_boolean(self, p):
        return self.expr_binary(p)
    
    @_(*product(('expr_string', 'column', 'call'),
                 product(('NOT', None),
                         ('LIKE', 'GLOB', 'REGEXP', 'MATCH')),
                ('expr_string', 'column', 'call'),
                ('%prec UNOT',)))
    def expr_boolean(self, p):
        return self.expr_binary(p)


    @_(*product(('expr_boolean', 'column', 'call'),
                ('AND', 'OR'),
                ('expr_boolean', 'column', 'call')))
    def expr_boolean(self, p):
        return self.expr_binary(p)
    
    @_(*product(('expr_numeric', 'column', 'call'),
                ('MULTIPLICATION', 'DIVISION', 'PLUS', 'MINUS'),
                ('expr_numeric', 'column', 'call')))
    def expr_numeric(self, p):
        return self.expr_binary(p)

    @_('IDENTIFIER DOT IDENTIFIER DOT IDENTIFIER')
    def column(self, p):
        return Column(p[4], Table(p[2], p[0]))
    
    @_('IDENTIFIER DOT IDENTIFIER')
    def column(self, p):
        return Column(p[2], Table(p[0]))

    @_('IDENTIFIER')
    def column(self, p):
        return Column(p[0])

    @_('LP column RP')
    def column(self, p):
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

    @_('FILTER LP where RP')
    def filter_clause(self, p):
        return p.where
    
    # TODO: over_clause
    @_('IDENTIFIER LP arguments RP',
       'IDENTIFIER LP arguments RP filter_clause',
       #'IDENTIFIER LP arguments RP over_clause',
       #'IDENTIFIER LP arguments RP filter_clause over_clause')
       )
    def call(self, p):
        parameter = p.arguments
        
        if hasattr(p, 'filter_clause'):
            parameter |= {'filter': p.filter_clause}
        else:
            parameter |= {'filter': None}
        
        return Operation(('CALL',),
                         p.IDENTIFIER,
                         parameter)

    @_('LP call RP')
    def call(self, p):
        return p[1]

    def cast(self, p, kind):
        return Operation(('CAST',), p[2], kind)
    
    @_(*product(('CAST LP',),
                ('expr_boolean', 'expr_numeric', 'expr_string', 'expr_null', 'column', 'call'),
                ('AS',),
                ('CHAR', 'CLOB', 'TEXT'),
                ('RP',)))
    def expr_string(self, p):
        return self.cast(p, str)

    @_(*product(('CAST LP',),
                ('expr_boolean', 'expr_numeric', 'expr_string', 'expr_null', 'column', 'call'),
                ('AS',),
                ('REAL', 'FLOA', 'DOUB', 'INTEGER', 'DECIMAL', 'NUMERIC'),
                ('RP',)))
    def expr_numeric(self, p):
        return self.cast(p,
                         int if hasattr(p, 'INTEGER') else str)

    @_(*product(('CAST LP',),
                ('expr_boolean', 'expr_numeric', 'expr_string', 'expr_null', 'column', 'call'),
                ('AS',),
                ('NULL_LITERAL',),
                ('RP',)))
    def expr_null(self, p):
        return self.cast(p[2], None)

    @_('EXISTS LP select RP')
    def expr_boolean(self, p):
        return Operation(('EXISTS',), None, p.select)
    
    @_('NOT expr_boolean %prec UNOT')
    def expr_boolean(self, p):
        return Operation(('NOT',), None, p[1])

    @_('PLUS expr_numeric %prec UPLUS')
    def expr_numeric(self, p):
        return p[1]

    @_('MINUS expr_numeric %prec UMINUS')
    def expr_numeric(self, p):
        return Operation(('MINUS',), None, p[1])

    @_('CURRENT_TIMESTAMP',
       'CURRENT_TIME',
       'CURRENT_DATE')
    def expr_string(self, p):
        return Operation(('CALL',),
                         p[0],
                         {'arguments': (),
                          'distinct': False,
                          'order_by': ()})

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
