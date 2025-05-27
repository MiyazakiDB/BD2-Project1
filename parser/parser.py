from .scanner import TokenType
from .ast import *

class ParserError(Exception):
    pass

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0
    
    def parse(self):
        """Parse a sequence of SQL statements."""
        statements = []
        
        while not self.is_at_end():
            statements.append(self.statement())
            self.consume(TokenType.SEMICOLON, "Expect ';' after statement.")
            
        return statements
    
    def statement(self):
        """Parse a single SQL statement."""
        if self.match(TokenType.SELECT):
            return self.select_statement()
        elif self.match(TokenType.CREATE):
            if self.check(TokenType.TABLE):
                self.advance()
                return self.create_table_statement()
            elif self.check(TokenType.INDEX):
                self.advance()
                return self.create_index_statement()
            else:
                raise ParserError(f"Expected 'TABLE' or 'INDEX' after 'CREATE' at line {self.peek().line}")
        elif self.match(TokenType.DROP):
            if self.check(TokenType.TABLE):
                self.advance()
                return self.drop_table_statement()
            elif self.check(TokenType.INDEX):
                self.advance()
                return self.drop_index_statement()
            else:
                raise ParserError(f"Expected 'TABLE' or 'INDEX' after 'DROP' at line {self.peek().line}")
        elif self.match(TokenType.INSERT):
            return self.insert_statement()
        elif self.match(TokenType.DELETE):
            return self.delete_statement()
        else:
            raise ParserError(f"Expected statement at line {self.peek().line}")
    
    def select_statement(self):
        columns = self.select_list()
        
        self.consume(TokenType.FROM, "Expect 'FROM' after select columns.")
        table_name = self.identifier()
        
        where_clause = None
        if self.match(TokenType.WHERE):
            where_clause = self.condition()
            
        return SelectStmt(columns, table_name, where_clause)
    
    def select_list(self):
        if self.match(TokenType.ASTERISK):
            return ["*"]
            
        columns = []
        columns.append(self.identifier())
        
        while self.match(TokenType.COMMA):
            columns.append(self.identifier())
            
        return columns
    
    def create_table_statement(self):
        table_name = self.identifier()
        
        self.consume(TokenType.LPAREN, "Expect '(' after table name.")
        columns = self.column_def_list()
        self.consume(TokenType.RPAREN, "Expect ')' after column definitions.")
        
        return CreateTableStmt(table_name, columns)
    
    def column_def_list(self):
        columns = []
        columns.append(self.column_def())
        
        while self.match(TokenType.COMMA):
            columns.append(self.column_def())
            
        return columns
    
    def column_def(self):
        name = self.identifier()
        data_type = self.data_type()
        
        primary_key = False
        index_type = None
        
        if self.match(TokenType.PRIMARY):
            self.consume(TokenType.KEY, "Expect 'KEY' after 'PRIMARY'.")
            primary_key = True
            
        if self.match(TokenType.INDEX):
            index_type = self.index_type()
            
        return ColumnDef(name, data_type, primary_key, index_type)
    
    def data_type(self):
        if self.match(TokenType.INT):
            return DataType("INT")
        elif self.match(TokenType.FLOAT):
            return DataType("FLOAT")
        elif self.match(TokenType.VARCHAR):
            self.consume(TokenType.LPAREN, "Expect '(' after VARCHAR.")
            size = self.consume(TokenType.NUMBER, "Expect number for VARCHAR size.").literal
            self.consume(TokenType.RPAREN, "Expect ')' after VARCHAR size.")
            return DataType("VARCHAR", [size])
        elif self.match(TokenType.BOOLEAN):
            return DataType("BOOLEAN")
        elif self.match(TokenType.DATE):
            return DataType("DATE")
        elif self.match(TokenType.ARRAY):
            self.consume(TokenType.LBRACKET, "Expect '[' after ARRAY.")
            element_type = self.data_type()
            self.consume(TokenType.RBRACKET, "Expect ']' after array element type.")
            return DataType("ARRAY", [element_type])
        else:
            raise ParserError(f"Expected data type at line {self.peek().line}")
    
    def index_type(self):
        if self.match(TokenType.AVL):
            return "AVL"
        elif self.match(TokenType.ISAM):
            return "ISAM"
        elif self.match(TokenType.HASH):
            return "HASH"
        elif self.match(TokenType.BTREE):
            return "BTREE"
        elif self.match(TokenType.RTREE):
            return "RTREE"
        elif self.match(TokenType.GIN):
            return "GIN"
        elif self.match(TokenType.IVF):
            return "IVF"
        elif self.match(TokenType.ISH):
            return "ISH"
        else:
            raise ParserError(f"Expected index type at line {self.peek().line}")

    def create_index_statement(self):
        index_name = self.identifier()
        
        self.consume(TokenType.ON, "Expect 'ON' after index name.")
        table_name = self.identifier()
        
        index_type = None
        if self.match(TokenType.USING):
            index_type = self.index_type()
            
        self.consume(TokenType.LPAREN, "Expect '(' before column list.")
        columns = self.column_list()
        self.consume(TokenType.RPAREN, "Expect ')' after column list.")
        
        return CreateIndexStmt(index_name, table_name, columns, index_type)

    def drop_table_statement(self):
        table_name = self.identifier()
        return DropTableStmt(table_name)
        
    def drop_index_statement(self):
        index_name = self.identifier()
        return DropIndexStmt(index_name)
        
    def insert_statement(self):
        self.consume(TokenType.INTO, "Expect 'INTO' after INSERT.")
        table_name = self.identifier()
        
        columns = None
        if self.match(TokenType.LPAREN):
            columns = self.column_list()
            self.consume(TokenType.RPAREN, "Expect ')' after column list.")
            
        self.consume(TokenType.VALUES, "Expect 'VALUES' after table name or column list.")
        self.consume(TokenType.LPAREN, "Expect '(' after 'VALUES'.")
        values = self.value_list()
        self.consume(TokenType.RPAREN, "Expect ')' after values.")
        
        return InsertStmt(table_name, columns, values)
        
    def delete_statement(self):
        self.consume(TokenType.FROM, "Expect 'FROM' after DELETE.")
        table_name = self.identifier()
        
        where_clause = None
        if self.match(TokenType.WHERE):
            where_clause = self.condition()
            
        return DeleteStmt(table_name, where_clause)
    
    def column_list(self):
        columns = []
        columns.append(self.identifier())
        
        while self.match(TokenType.COMMA):
            columns.append(self.identifier())
            
        return columns
        
    def value_list(self):
        values = []
        values.append(self.value())
        
        while self.match(TokenType.COMMA):
            values.append(self.value())
            
        return values
        
    def value(self):
        if self.match(TokenType.STRING):
            return LiteralExpr(self.previous().literal)
        elif self.match(TokenType.NUMBER):
            return LiteralExpr(self.previous().literal)
        elif self.match(TokenType.TRUE):
            return LiteralExpr(True)
        elif self.match(TokenType.FALSE):
            return LiteralExpr(False)
        elif self.match(TokenType.LPAREN):  # For coordinate values
            x = self.consume(TokenType.NUMBER, "Expect number for X coordinate").literal
            self.consume(TokenType.COMMA, "Expect ',' between X and Y coordinates")
            y = self.consume(TokenType.NUMBER, "Expect number for Y coordinate").literal
            self.consume(TokenType.RPAREN, "Expect ')' after coordinates")
            return CoordinateExpr(x, y)
        else:
            raise ParserError(f"Expected value at line {self.peek().line}")

    def condition(self):
        return self.or_condition()
    
    def or_condition(self):
        expr = self.and_condition()
        
        while self.match(TokenType.OR):
            operator = self.previous().type
            right = self.and_condition()
            expr = BinaryExpr(expr, operator, right)
            
        return expr
        
    def and_condition(self):
        expr = self.not_condition()
        
        while self.match(TokenType.AND):
            operator = self.previous().type
            right = self.not_condition()
            expr = BinaryExpr(expr, operator, right)
            
        return expr
        
    def not_condition(self):
        if self.match(TokenType.NOT):
            operator = self.previous().type
            right = self.predicate()
            return UnaryExpr(operator, right)
        
        return self.predicate()
        
    def predicate(self):
        if self.match(TokenType.LPAREN):
            expr = self.condition()
            self.consume(TokenType.RPAREN, "Expect ')' after condition.")
            return GroupingExpr(expr)
            
        return self.simple_condition()
        
    def simple_condition(self):
        column = self.identifier()
        
        if self.match(TokenType.BETWEEN):
            lower = self.value()
            self.consume(TokenType.AND, "Expect 'AND' in BETWEEN expression.")
            upper = self.value()
            return BetweenExpr(column, lower, upper)
            
        elif self.match(TokenType.IN):
            self.consume(TokenType.LPAREN, "Expect '(' after IN.")
            values = self.value_list()
            self.consume(TokenType.RPAREN, "Expect ')' after value list.")
            return InExpr(column, values)
            
        # Match the exact token type names from the scanner module
        elif self.match(TokenType.EQUALS, TokenType.NOT_EQUALS, 
                         TokenType.LESS_THAN, TokenType.LESS_EQUALS, 
                         TokenType.GREATER_THAN, TokenType.GREATER_EQUALS):
            operator = self.previous().type
            right = self.value()
            return BinaryExpr(column, operator, right)
            
        raise ParserError(f"Expected condition operator at line {self.peek().line}")

    def match(self, *types):
        for type in types:
            if self.check(type):
                self.advance()
                return True
        return False
    
    def check(self, type):
        if self.is_at_end():
            return False
        return self.peek().type == type
    
    def advance(self):
        if not self.is_at_end():
            self.current += 1
        return self.previous()
    
    def is_at_end(self):
        return self.peek().type == TokenType.EOF
    
    def peek(self):
        return self.tokens[self.current]
    
    def previous(self):
        return self.tokens[self.current - 1]
    
    def consume(self, type, message):
        if self.check(type):
            return self.advance()
        raise ParserError(f"{message} at line {self.peek().line}")
    
    def identifier(self):
        token = self.consume(TokenType.IDENTIFIER, "Expect identifier.")
        return Identifier(token.lexeme)