from .scanner import Scanner, TokenType, Token, ScanError
from .parser import Parser, ParseError

def parse_sql(sql_string):
    """
    Parse a SQL string and return the abstract syntax tree.
    
    Args:
        sql_string: The SQL string to parse.
        
    Returns:
        A list of parsed SQL statements.
        
    Raises:
        ScanError: If an error occurs during scanning.
        ParseError: If an error occurs during parsing.
    """
    scanner = Scanner(sql_string)
    tokens = scanner.scan_tokens()
    
    parser = Parser(tokens)
    return parser.parse()
