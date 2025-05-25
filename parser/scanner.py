from enum import Enum, auto

class TokenType(Enum):
    # Keywords
    SELECT = auto()
    FROM = auto()
    WHERE = auto()
    CREATE = auto()
    DROP = auto()
    TABLE = auto()
    INDEX = auto()
    INSERT = auto()
    DELETE = auto()
    INTO = auto()
    VALUES = auto()
    PRIMARY = auto()
    KEY = auto()
    USING = auto()
    INT = auto()
    FLOAT = auto()
    VARCHAR = auto()
    BOOLEAN = auto()
    DATE = auto()
    ARRAY = auto()
    ON = auto()
    TRUE = auto()
    FALSE = auto()
    BETWEEN = auto()
    IN = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    
    # Index types
    AVL = auto()
    ISAM = auto()
    HASH = auto()
    BTREE = auto()
    RTREE = auto()
    GIN = auto()
    IVF = auto()
    ISH = auto()
    
    # Symbols
    SEMICOLON = auto()
    COMMA = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    ASTERISK = auto()
    
    # Operators
    EQUALS = auto()
    NOT_EQUALS = auto()
    LESS_THAN = auto()
    GREATER_THAN = auto()
    LESS_EQUALS = auto()
    GREATER_EQUALS = auto()
    
    # Data
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    
    # Special
    EOF = auto()

class Token:
    def __init__(self, token_type, lexeme, literal=None, line=0):
        self.type = token_type
        self.lexeme = lexeme
        self.literal = literal
        self.line = line
    
    def __repr__(self):
        return f"Token({self.type}, '{self.lexeme}', {self.literal}, {self.line})"

class Scanner:
    def __init__(self, source):
        self.source = source
        self.tokens = []
        self.start = 0
        self.current = 0
        self.line = 1
        
        self.keywords = {
            "select": TokenType.SELECT,
            "from": TokenType.FROM,
            "where": TokenType.WHERE,
            "create": TokenType.CREATE,
            "drop": TokenType.DROP,
            "table": TokenType.TABLE,
            "index": TokenType.INDEX,
            "insert": TokenType.INSERT,
            "delete": TokenType.DELETE,
            "into": TokenType.INTO,
            "values": TokenType.VALUES,
            "primary": TokenType.PRIMARY,
            "key": TokenType.KEY,
            "using": TokenType.USING,
            "int": TokenType.INT,
            "float": TokenType.FLOAT,
            "varchar": TokenType.VARCHAR,
            "boolean": TokenType.BOOLEAN,
            "date": TokenType.DATE,
            "array": TokenType.ARRAY,
            "on": TokenType.ON,
            "true": TokenType.TRUE,
            "false": TokenType.FALSE,
            "between": TokenType.BETWEEN,
            "in": TokenType.IN,
            "and": TokenType.AND,
            "or": TokenType.OR,
            "not": TokenType.NOT,
            
            # Index types
            "avl": TokenType.AVL,
            "isam": TokenType.ISAM,
            "hash": TokenType.HASH,
            "btree": TokenType.BTREE,
            "rtree": TokenType.RTREE,
            "gin": TokenType.GIN,
            "ivf": TokenType.IVF,
            "ish": TokenType.ISH
        }
    
    def scan_tokens(self):
        while not self.is_at_end():
            self.start = self.current
            self.scan_token()
            
        self.tokens.append(Token(TokenType.EOF, "", None, self.line))
        return self.tokens
    
    def scan_token(self):
        c = self.advance()
        
        if c == ';':
            self.add_token(TokenType.SEMICOLON)
        elif c == ',':
            self.add_token(TokenType.COMMA)
        elif c == '(':
            self.add_token(TokenType.LPAREN)
        elif c == ')':
            self.add_token(TokenType.RPAREN)
        elif c == '[':
            self.add_token(TokenType.LBRACKET)
        elif c == ']':
            self.add_token(TokenType.RBRACKET)
        elif c == '*':
            self.add_token(TokenType.ASTERISK)
        elif c == '=':
            self.add_token(TokenType.EQUALS)
        elif c == '<':
            if self.match('='):
                self.add_token(TokenType.LESS_EQUALS)
            elif self.match('>'):
                self.add_token(TokenType.NOT_EQUALS)
            else:
                self.add_token(TokenType.LESS_THAN)
        elif c == '>':
            if self.match('='):
                self.add_token(TokenType.GREATER_EQUALS)
            else:
                self.add_token(TokenType.GREATER_THAN)
        elif c in [' ', '\r', '\t']:
            # Ignore whitespace
            pass
        elif c == '\n':
            self.line += 1
        elif c == '"' or c == "'":
            self.string(c)
        elif self.is_digit(c):
            self.number()
        elif self.is_alpha(c):
            self.identifier()
        else:
            # Error handling can be added here
            print(f"Unexpected character: {c} at line {self.line}")
    
    # Helper methods
    def is_at_end(self):
        return self.current >= len(self.source)
    
    def advance(self):
        self.current += 1
        return self.source[self.current - 1]
    
    def match(self, expected):
        if self.is_at_end() or self.source[self.current] != expected:
            return False
        self.current += 1
        return True
    
    def peek(self):
        if self.is_at_end():
            return '\0'
        return self.source[self.current]
    
    def peek_next(self):
        if self.current + 1 >= len(self.source):
            return '\0'
        return self.source[self.current + 1]
    
    def is_alpha(self, c):
        return ('a' <= c <= 'z') or ('A' <= c <= 'Z') or c == '_'
    
    def is_digit(self, c):
        return '0' <= c <= '9'
    
    def is_alphanumeric(self, c):
        return self.is_alpha(c) or self.is_digit(c)
    
    def identifier(self):
        while self.is_alphanumeric(self.peek()):
            self.advance()
            
        text = self.source[self.start:self.current].lower()
        token_type = self.keywords.get(text, TokenType.IDENTIFIER)
        self.add_token(token_type)
    
    def number(self):
        while self.is_digit(self.peek()):
            self.advance()
            
        # Look for decimal part
        if self.peek() == '.' and self.is_digit(self.peek_next()):
            self.advance()  # Consume the "."
            
            while self.is_digit(self.peek()):
                self.advance()
                
        value = float(self.source[self.start:self.current])
        if value.is_integer():
            value = int(value)
        self.add_token(TokenType.NUMBER, value)
    
    def string(self, quote):
        while self.peek() != quote and not self.is_at_end():
            if self.peek() == '\n':
                self.line += 1
            self.advance()
            
        if self.is_at_end():
            print(f"Unterminated string at line {self.line}")
            return
            
        # Consume closing quote
        self.advance()
        
        # Get string value without quotes
        value = self.source[self.start+1:self.current-1]
        self.add_token(TokenType.STRING, value)
    
    def add_token(self, token_type, literal=None):
        text = self.source[self.start:self.current]
        self.tokens.append(Token(token_type, text, literal, self.line))