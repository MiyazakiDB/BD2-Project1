import re
from enum import Enum, auto


class TokenType(Enum):
    # Keywords
    SELECT = auto()
    FROM = auto()
    WHERE = auto()
    CREATE = auto()
    TABLE = auto()
    DROP = auto()
    INSERT = auto()
    INTO = auto()
    VALUES = auto()
    DELETE = auto()
    INDEX = auto()
    ON = auto()
    USING = auto()
    PRIMARY = auto()
    KEY = auto()
    INT = auto()
    FLOAT = auto()
    VARCHAR = auto()
    BOOLEAN = auto()
    BETWEEN = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    
    # Data values
    TRUE = auto()
    FALSE = auto()
    
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
    ASTERISK = auto()
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    
    # Operators
    EQUALS = auto()
    NOT_EQUALS = auto()
    LESS_THAN = auto()
    GREATER_THAN = auto()
    LESS_THAN_EQUALS = auto()
    GREATER_THAN_EQUALS = auto()
    
    # Other
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    EOF = auto()


class Token:
    def __init__(self, token_type, value=None, position=None):
        self.type = token_type
        self.value = value
        self.position = position
    
    def __str__(self):
        if self.value:
            return f"Token({self.type}, '{self.value}')"
        return f"Token({self.type})"


class Scanner:
    def __init__(self, source):
        self.source = source
        self.tokens = []
        self.start = 0
        self.current = 0
        self.line = 1
        
        self.keywords = {
            'SELECT': TokenType.SELECT,
            'FROM': TokenType.FROM,
            'WHERE': TokenType.WHERE,
            'CREATE': TokenType.CREATE,
            'TABLE': TokenType.TABLE,
            'DROP': TokenType.DROP,
            'INSERT': TokenType.INSERT,
            'INTO': TokenType.INTO,
            'VALUES': TokenType.VALUES,
            'DELETE': TokenType.DELETE,
            'INDEX': TokenType.INDEX,
            'ON': TokenType.ON,
            'USING': TokenType.USING,
            'PRIMARY': TokenType.PRIMARY,
            'KEY': TokenType.KEY,
            'INT': TokenType.INT,
            'FLOAT': TokenType.FLOAT,
            'VARCHAR': TokenType.VARCHAR,
            'BOOLEAN': TokenType.BOOLEAN,
            'BETWEEN': TokenType.BETWEEN,
            'AND': TokenType.AND,
            'OR': TokenType.OR,
            'NOT': TokenType.NOT,
            'TRUE': TokenType.TRUE,
            'FALSE': TokenType.FALSE,
            'AVL': TokenType.AVL,
            'ISAM': TokenType.ISAM,
            'HASH': TokenType.HASH,
            'BTREE': TokenType.BTREE,
            'RTREE': TokenType.RTREE,
            'GIN': TokenType.GIN,
            'IVF': TokenType.IVF,
            'ISH': TokenType.ISH,
        }
    
    def scan_tokens(self):
        while not self.is_at_end():
            self.start = self.current
            self.scan_token()
        
        self.tokens.append(Token(TokenType.EOF, None, (self.line, self.current)))
        return self.tokens
    
    def is_at_end(self):
        return self.current >= len(self.source)
    
    def scan_token(self):
        c = self.advance()
        
        if c == ';':
            self.add_token(TokenType.SEMICOLON)
        elif c == ',':
            self.add_token(TokenType.COMMA)
        elif c == '*':
            self.add_token(TokenType.ASTERISK)
        elif c == '(':
            self.add_token(TokenType.LEFT_PAREN)
        elif c == ')':
            self.add_token(TokenType.RIGHT_PAREN)
        elif c == '=':
            self.add_token(TokenType.EQUALS)
        elif c == '<':
            if self.match('='):
                self.add_token(TokenType.LESS_THAN_EQUALS)
            elif self.match('>'):
                self.add_token(TokenType.NOT_EQUALS)
            else:
                self.add_token(TokenType.LESS_THAN)
        elif c == '>':
            if self.match('='):
                self.add_token(TokenType.GREATER_THAN_EQUALS)
            else:
                self.add_token(TokenType.GREATER_THAN)
        elif c == "'":
            self.string()
        elif c.isspace():
            pass  # Ignore whitespace
        elif c.isdigit():
            self.number()
        elif c.isalpha() or c == '_':
            self.identifier()
        else:
            raise ScanError(f"Unexpected character: {c}", self.line, self.current)
    
    def advance(self):
        c = self.source[self.current]
        self.current += 1
        return c
    
    def match(self, expected):
        if self.is_at_end():
            return False
        if self.source[self.current] != expected:
            return False
        
        self.current += 1
        return True
    
    def peek(self):
        if self.is_at_end():
            return '\0'
        return self.source[self.current]
    
    def add_token(self, token_type, value=None):
        text = self.source[self.start:self.current] if value is None else value
        self.tokens.append(Token(token_type, text, (self.line, self.start)))
    
    def string(self):
        while self.peek() != "'" and not self.is_at_end():
            if self.peek() == '\n':
                self.line += 1
            self.advance()
        
        if self.is_at_end():
            raise ScanError("Unterminated string", self.line, self.current)
        
        # Consume the closing "
        self.advance()
        
        # Trim the surrounding quotes
        value = self.source[self.start + 1:self.current - 1]
        self.add_token(TokenType.STRING, value)
    
    def number(self):
        while self.peek().isdigit():
            self.advance()
        
        # Look for a decimal part
        if self.peek() == '.' and self.peek_next().isdigit():
            # Consume the "."
            self.advance()
            
            while self.peek().isdigit():
                self.advance()
        
        value = self.source[self.start:self.current]
        self.add_token(TokenType.NUMBER, float(value) if '.' in value else int(value))
    
    def peek_next(self):
        if self.current + 1 >= len(self.source):
            return '\0'
        return self.source[self.current + 1]
    
    def identifier(self):
        while self.peek().isalnum() or self.peek() == '_':
            self.advance()
        
        text = self.source[self.start:self.current]
        token_type = self.keywords.get(text.upper())
        
        if token_type is None:
            token_type = TokenType.IDENTIFIER
        
        self.add_token(token_type, text)


class ScanError(Exception):
    def __init__(self, message, line, position):
        self.message = message
        self.line = line
        self.position = position
        super().__init__(f"Line {line}, Position {position}: {message}")
