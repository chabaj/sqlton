from sqlton.parser import Lexer, Parser

def parse(statement):
    lexer = Lexer()

    tokens = lexer.tokenize(statement)
    parser = Parser()
    
    return parser.parse(tokens)
