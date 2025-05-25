from .scanner import TokenType, Scanner


class ParseError(Exception):
    def __init__(self, token, message):
        self.token = token
        self.message = message
        super().__init__(f"Error at '{token.value}': {message}")


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0
    
    def parse(self):
        statements = []
        while not self.is_at_end():
            statements.append(self.statement())
        return statements
    
    def statement(self):
        if self.match(TokenType.SELECT):
            return self.select_statement()
        elif self.match(TokenType.CREATE):
            if self.check(TokenType.TABLE):
                return self.create_table_statement()
            elif self.check(TokenType.INDEX):
                return self.create_index_statement()
        elif self.match(TokenType.DROP):
            if self.check(TokenType.TABLE):
                return self.drop_table_statement()
            elif self.check(TokenType.INDEX):
                return self.drop_index_statement()
        elif self.match(TokenType.INSERT):
            return self.insert_statement()
        elif self.match(TokenType.DELETE):
            return self.delete_statement()
        
        raise ParseError(self.peek(), "Expected statement.")
    
    def select_statement(self):
        select_list = self.select_list()
        self.consume(TokenType.FROM, "Expected 'FROM' after select list.")
        table = self.consume(TokenType.IDENTIFIER, "Expected table name.").value
        
        condition = None
        if self.match(TokenType.WHERE):
            condition = self.condition()
        
        self.consume(TokenType.SEMICOLON, "Expected ';' after SELECT statement.")
        
        return {
            "type": "SELECT",
            "select_list": select_list,
            "table": table,
            "condition": condition
        }
    
    def select_list(self):
        if self.match(TokenType.ASTERISK):
            return ["*"]
        
        columns = [self.consume(TokenType.IDENTIFIER, "Expected column name.").value]
        while self.match(TokenType.COMMA):
            columns.append(self.consume(TokenType.IDENTIFIER, "Expected column name.").value)
        
        return columns
    
    def create_table_statement(self):
        self.consume(TokenType.TABLE, "Expected 'TABLE' keyword.")
        table_name = self.consume(TokenType.IDENTIFIER, "Expected table name.").value
        
        self.consume(TokenType.LEFT_PAREN, "Expected '(' after table name.")
        columns = self.column_def_list()
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after column definitions.")
        self.consume(TokenType.SEMICOLON, "Expected ';' after CREATE TABLE statement.")
        
        return {
            "type": "CREATE_TABLE",
            "table_name": table_name,
            "columns": columns
        }
    
    def column_def_list(self):
        columns = [self.column_def()]
        while self.match(TokenType.COMMA):
            columns.append(self.column_def())
        
        return columns
    
    def column_def(self):
        column_name = self.consume(TokenType.IDENTIFIER, "Expected column name.").value
        data_type = self.data_type()
        
        primary_key = False
        if self.match(TokenType.PRIMARY):
            self.consume(TokenType.KEY, "Expected 'KEY' after 'PRIMARY'.")
            primary_key = True
        
        return {
            "name": column_name,
            "data_type": data_type,
            "primary_key": primary_key
        }
    
    def data_type(self):
        if self.match(TokenType.INT):
            return {"type": "INT"}
        elif self.match(TokenType.FLOAT):
            return {"type": "FLOAT"}
        elif self.match(TokenType.VARCHAR):
            self.consume(TokenType.LEFT_PAREN, "Expected '(' after VARCHAR.")
            size = self.consume(TokenType.NUMBER, "Expected size for VARCHAR.").value
            self.consume(TokenType.RIGHT_PAREN, "Expected ')' after VARCHAR size.")
            return {"type": "VARCHAR", "size": size}
        elif self.match(TokenType.BOOLEAN):
            return {"type": "BOOLEAN"}
        else:
            raise ParseError(self.peek(), "Expected data type.")
    
    def drop_table_statement(self):
        self.consume(TokenType.TABLE, "Expected 'TABLE' keyword.")
        table_name = self.consume(TokenType.IDENTIFIER, "Expected table name.").value
        self.consume(TokenType.SEMICOLON, "Expected ';' after DROP TABLE statement.")
        
        return {
            "type": "DROP_TABLE",
            "table_name": table_name
        }
    
    def insert_statement(self):
        self.consume(TokenType.INTO, "Expected 'INTO' after INSERT.")
        table_name = self.consume(TokenType.IDENTIFIER, "Expected table name.").value
        
        columns = None
        if self.match(TokenType.LEFT_PAREN):
            columns = self.column_list()
            self.consume(TokenType.RIGHT_PAREN, "Expected ')' after column list.")
        
        self.consume(TokenType.VALUES, "Expected 'VALUES' keyword.")
        self.consume(TokenType.LEFT_PAREN, "Expected '(' after VALUES.")
        values = self.value_list()
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after value list.")
        self.consume(TokenType.SEMICOLON, "Expected ';' after INSERT statement.")
        
        return {
            "type": "INSERT",
            "table_name": table_name,
            "columns": columns,
            "values": values
        }
    
    def column_list(self):
        columns = [self.consume(TokenType.IDENTIFIER, "Expected column name.").value]
        while self.match(TokenType.COMMA):
            columns.append(self.consume(TokenType.IDENTIFIER, "Expected column name.").value)
        
        return columns
    
    def value_list(self):
        values = [self.value()]
        while self.match(TokenType.COMMA):
            values.append(self.value())
        
        return values
    
    def value(self):
        if self.match(TokenType.STRING):
            return {"type": "STRING", "value": self.previous().value}
        elif self.match(TokenType.NUMBER):
            return {"type": "NUMBER", "value": self.previous().value}
        elif self.match(TokenType.TRUE):
            return {"type": "BOOLEAN", "value": True}
        elif self.match(TokenType.FALSE):
            return {"type": "BOOLEAN", "value": False}
        else:
            raise ParseError(self.peek(), "Expected value.")
    
    def delete_statement(self):
        self.consume(TokenType.FROM, "Expected 'FROM' after DELETE.")
        table_name = self.consume(TokenType.IDENTIFIER, "Expected table name.").value
        
        condition = None
        if self.match(TokenType.WHERE):
            condition = self.condition()
        
        self.consume(TokenType.SEMICOLON, "Expected ';' after DELETE statement.")
        
        return {
            "type": "DELETE",
            "table_name": table_name,
            "condition": condition
        }
    
    def create_index_statement(self):
        self.consume(TokenType.INDEX, "Expected 'INDEX' keyword.")
        index_name = self.consume(TokenType.IDENTIFIER, "Expected index name.").value
        self.consume(TokenType.ON, "Expected 'ON' after index name.")
        table_name = self.consume(TokenType.IDENTIFIER, "Expected table name.").value
        
        index_type = None
        if self.match(TokenType.USING):
            index_type = self.index_type()
        
        self.consume(TokenType.LEFT_PAREN, "Expected '(' after table name.")
        columns = self.column_list()
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after column list.")
        self.consume(TokenType.SEMICOLON, "Expected ';' after CREATE INDEX statement.")
        
        return {
            "type": "CREATE_INDEX",
            "index_name": index_name,
            "table_name": table_name,
            "index_type": index_type,
            "columns": columns
        }
    
    def index_type(self):
        if self.match(TokenType.AVL, TokenType.ISAM, TokenType.HASH, TokenType.BTREE,
                      TokenType.RTREE, TokenType.GIN, TokenType.IVF, TokenType.ISH):
            return self.previous().value
        else:
            raise ParseError(self.peek(), "Expected index type.")
    
    def drop_index_statement(self):
        self.consume(TokenType.INDEX, "Expected 'INDEX' keyword.")
        index_name = self.consume(TokenType.IDENTIFIER, "Expected index name.").value
        self.consume(TokenType.SEMICOLON, "Expected ';' after DROP INDEX statement.")
        
        return {
            "type": "DROP_INDEX",
            "index_name": index_name
        }
    
    def condition(self):
        return self.or_condition()
    
    def or_condition(self):
        expr = self.and_condition()
        
        while self.match(TokenType.OR):
            right = self.and_condition()
            expr = {"type": "OR", "left": expr, "right": right}
        
        return expr
    
    def and_condition(self):
        expr = self.not_condition()
        
        while self.match(TokenType.AND):
            right = self.not_condition()
            expr = {"type": "AND", "left": expr, "right": right}
        
        return expr
    
    def not_condition(self):
        if self.match(TokenType.NOT):
            return {"type": "NOT", "operand": self.predicate()}
        return self.predicate()
    
    def predicate(self):
        if self.match(TokenType.LEFT_PAREN):
            expr = self.condition()
            self.consume(TokenType.RIGHT_PAREN, "Expected ')' after condition.")
            return expr
        else:
            return self.simple_condition()
    
    def simple_condition(self):
        column = self.consume(TokenType.IDENTIFIER, "Expected column name.").value
        
        if self.match(TokenType.BETWEEN):
            value1 = self.value()
            self.consume(TokenType.AND, "Expected 'AND' in BETWEEN condition.")
            value2 = self.value()
            
            return {
                "type": "BETWEEN",
                "column": column,
                "value1": value1,
                "value2": value2
            }
        
        operator = self.operator()
        value = self.value()
        
        return {
            "type": "SIMPLE_CONDITION",
            "column": column,
            "operator": operator,
            "value": value
        }
    
    def operator(self):
        if self.match(TokenType.EQUALS):
            return "="
        elif self.match(TokenType.NOT_EQUALS):
            return "<>"
        elif self.match(TokenType.LESS_THAN):
            return "<"
        elif self.match(TokenType.GREATER_THAN):
            return ">"
        elif self.match(TokenType.LESS_THAN_EQUALS):
            return "<="
        elif self.match(TokenType.GREATER_THAN_EQUALS):
            return ">="
        else:
            raise ParseError(self.peek(), "Expected operator.")

    # Helper methods for token handling
    def match(self, *types):
        for token_type in types:
            if self.check(token_type):
                self.advance()
                return True
        return False
    
    def check(self, token_type):
        if self.is_at_end():
            return False
        return self.peek().type == token_type
    
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
    
    def consume(self, token_type, message):
        if self.check(token_type):
            return self.advance()
        
        raise ParseError(self.peek(), message)
