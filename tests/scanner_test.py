import sys
import os
import unittest

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parser.scanner import Scanner, TokenType, Token

class ScannerTest(unittest.TestCase):
    def test_simple_select(self):
        query = "SELECT * FROM users;"
        scanner = Scanner(query)
        tokens = scanner.scan_tokens()
        
        # Check token types (excluding EOF)
        token_types = [token.type for token in tokens[:-1]]
        expected_types = [
            TokenType.SELECT,
            TokenType.ASTERISK,
            TokenType.FROM,
            TokenType.IDENTIFIER,
            TokenType.SEMICOLON
        ]
        self.assertEqual(token_types, expected_types)
        self.assertEqual(tokens[-2].lexeme, ";")
    
    def test_create_table(self):
        query = "CREATE TABLE students (id INT PRIMARY KEY, name VARCHAR, age INT);"
        scanner = Scanner(query)
        tokens = scanner.scan_tokens()
        
        # Verify specific tokens
        self.assertEqual(tokens[0].type, TokenType.CREATE)
        self.assertEqual(tokens[1].type, TokenType.TABLE)
        self.assertEqual(tokens[2].type, TokenType.IDENTIFIER)
        self.assertEqual(tokens[2].lexeme, "students")
        self.assertEqual(tokens[3].type, TokenType.LPAREN)
        self.assertEqual(tokens[4].type, TokenType.IDENTIFIER)
        self.assertEqual(tokens[5].type, TokenType.INT)
        self.assertEqual(tokens[6].type, TokenType.PRIMARY)
        self.assertEqual(tokens[7].type, TokenType.KEY)
    
    def test_create_index(self):
        query = "CREATE INDEX idx_name ON users USING btree;"
        scanner = Scanner(query)
        tokens = scanner.scan_tokens()
        
        token_types = [token.type for token in tokens[:-1]]
        expected_types = [
            TokenType.CREATE,
            TokenType.INDEX,
            TokenType.IDENTIFIER,
            TokenType.ON,
            TokenType.IDENTIFIER,
            TokenType.USING,
            TokenType.BTREE,
            TokenType.SEMICOLON
        ]
        self.assertEqual(token_types, expected_types)
    
    def test_where_clause(self):
        query = "SELECT * FROM products WHERE price > 100 AND category = 'electronics';"
        scanner = Scanner(query)
        tokens = scanner.scan_tokens()
        
        # Check specific tokens in the WHERE clause
        where_index = next(i for i, t in enumerate(tokens) if t.type == TokenType.WHERE)
        self.assertEqual(tokens[where_index + 1].type, TokenType.IDENTIFIER)
        self.assertEqual(tokens[where_index + 2].type, TokenType.GREATER_THAN)
        self.assertEqual(tokens[where_index + 3].type, TokenType.NUMBER)
        self.assertEqual(tokens[where_index + 3].literal, 100)
        self.assertEqual(tokens[where_index + 4].type, TokenType.AND)
        self.assertEqual(tokens[where_index + 7].type, TokenType.STRING)
        self.assertEqual(tokens[where_index + 7].literal, "electronics")
    
    def test_number_literals(self):
        query = "SELECT * FROM table WHERE id = 123 OR price = 45.67;"
        scanner = Scanner(query)
        tokens = scanner.scan_tokens()
        
        # Find the tokens with NUMBER type
        number_tokens = [t for t in tokens if t.type == TokenType.NUMBER]
        self.assertEqual(len(number_tokens), 2)
        self.assertEqual(number_tokens[0].literal, 123)
        self.assertEqual(number_tokens[1].literal, 45.67)
    
    def test_string_literals(self):
        query = "INSERT INTO users VALUES ('John', \"Doe\");"
        scanner = Scanner(query)
        tokens = scanner.scan_tokens()
        
        # Find the tokens with STRING type
        string_tokens = [t for t in tokens if t.type == TokenType.STRING]
        self.assertEqual(len(string_tokens), 2)
        self.assertEqual(string_tokens[0].literal, "John")
        self.assertEqual(string_tokens[1].literal, "Doe")

if __name__ == "__main__":
    unittest.main()
