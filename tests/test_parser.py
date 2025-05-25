import unittest
import sys
import os
# Add the parent directory to sys.path to find the parser module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from parser.scanner import Scanner, TokenType, Token
from parser.parser import Parser
from parser.ast import *

class ParserTest(unittest.TestCase):
    def test_select_statement(self):
        # Test basic SELECT
        sql = "SELECT * FROM users;"
        ast = self.parse_sql(sql)
        
        self.assertEqual(len(ast), 1)
        stmt = ast[0]
        self.assertIsInstance(stmt, SelectStmt)
        self.assertEqual(stmt.columns, ["*"])
        self.assertEqual(stmt.table_name.name, "users")
        self.assertIsNone(stmt.where)
        
        # Test SELECT with columns
        sql = "SELECT id, name, email FROM users;"
        ast = self.parse_sql(sql)
        
        self.assertEqual(len(ast), 1)
        stmt = ast[0]
        self.assertEqual(len(stmt.columns), 3)
        self.assertEqual(stmt.columns[0].name, "id")
        self.assertEqual(stmt.columns[1].name, "name")
        self.assertEqual(stmt.columns[2].name, "email")
        
        # Test SELECT with WHERE
        sql = "SELECT * FROM users WHERE id = 5;"
        ast = self.parse_sql(sql)
        
        self.assertEqual(len(ast), 1)
        stmt = ast[0]
        self.assertIsNotNone(stmt.where)
        self.assertIsInstance(stmt.where, BinaryExpr)
        self.assertEqual(stmt.where.left.name, "id")
        self.assertEqual(stmt.where.right.value, 5)
    
    def test_create_table_statement(self):
        sql = """
        CREATE TABLE students (
            id INT PRIMARY KEY,
            name VARCHAR(100),
            age INT,
            active BOOLEAN
        );
        """
        ast = self.parse_sql(sql)
        
        self.assertEqual(len(ast), 1)
        stmt = ast[0]
        self.assertIsInstance(stmt, CreateTableStmt)
        self.assertEqual(stmt.table_name.name, "students")
        self.assertEqual(len(stmt.columns), 4)
        
        # Check primary key column
        self.assertEqual(stmt.columns[0].name.name, "id")
        self.assertEqual(stmt.columns[0].data_type.type_name, "INT")
        self.assertTrue(stmt.columns[0].primary_key)
        
        # Check VARCHAR column with size
        self.assertEqual(stmt.columns[1].name.name, "name")
        self.assertEqual(stmt.columns[1].data_type.type_name, "VARCHAR")
        self.assertEqual(stmt.columns[1].data_type.params[0], 100)
        
        # Check INT column
        self.assertEqual(stmt.columns[2].name.name, "age")
        self.assertEqual(stmt.columns[2].data_type.type_name, "INT")
        self.assertFalse(stmt.columns[2].primary_key)
        
        # Check BOOLEAN column
        self.assertEqual(stmt.columns[3].name.name, "active")
        self.assertEqual(stmt.columns[3].data_type.type_name, "BOOLEAN")
        self.assertFalse(stmt.columns[3].primary_key)
    
    def test_insert_statement(self):
        sql = "INSERT INTO users (name, email) VALUES ('John', 'john@example.com');"
        ast = self.parse_sql(sql)
        
        self.assertEqual(len(ast), 1)
        stmt = ast[0]
        self.assertIsInstance(stmt, InsertStmt)
        self.assertEqual(stmt.table_name.name, "users")
        self.assertEqual(len(stmt.columns), 2)
        self.assertEqual(stmt.columns[0].name, "name")
        self.assertEqual(stmt.columns[1].name, "email")
        self.assertEqual(len(stmt.values), 2)
        self.assertEqual(stmt.values[0].value, "John")
        self.assertEqual(stmt.values[1].value, "john@example.com")
        
        # Test without columns
        sql = "INSERT INTO users VALUES ('John', 'john@example.com');"
        ast = self.parse_sql(sql)
        
        self.assertEqual(len(ast), 1)
        stmt = ast[0]
        self.assertIsInstance(stmt, InsertStmt)
        self.assertEqual(stmt.table_name.name, "users")
        self.assertIsNone(stmt.columns)
        self.assertEqual(len(stmt.values), 2)
    
    def test_delete_statement(self):
        sql = "DELETE FROM users WHERE id = 5;"
        ast = self.parse_sql(sql)
        
        self.assertEqual(len(ast), 1)
        stmt = ast[0]
        self.assertIsInstance(stmt, DeleteStmt)
        self.assertEqual(stmt.table_name.name, "users")
        self.assertIsNotNone(stmt.where)
        self.assertIsInstance(stmt.where, BinaryExpr)
        self.assertEqual(stmt.where.left.name, "id")
        self.assertEqual(stmt.where.right.value, 5)
        
        # Test without WHERE
        sql = "DELETE FROM users;"
        ast = self.parse_sql(sql)
        
        self.assertEqual(len(ast), 1)
        stmt = ast[0]
        self.assertIsInstance(stmt, DeleteStmt)
        self.assertEqual(stmt.table_name.name, "users")
        self.assertIsNone(stmt.where)
    
    def test_create_index_statement(self):
        sql = "CREATE INDEX idx_name ON users USING BTREE (id, name);"
        ast = self.parse_sql(sql)
        
        self.assertEqual(len(ast), 1)
        stmt = ast[0]
        self.assertIsInstance(stmt, CreateIndexStmt)
        self.assertEqual(stmt.index_name.name, "idx_name")
        self.assertEqual(stmt.table_name.name, "users")
        self.assertEqual(stmt.index_type, "BTREE")
        self.assertEqual(len(stmt.columns), 2)
        self.assertEqual(stmt.columns[0].name, "id")
        self.assertEqual(stmt.columns[1].name, "name")
        
        # Test without USING clause
        sql = "CREATE INDEX idx_name ON users (id, name);"
        ast = self.parse_sql(sql)
        
        self.assertEqual(len(ast), 1)
        stmt = ast[0]
        self.assertIsInstance(stmt, CreateIndexStmt)
        self.assertIsNone(stmt.index_type)
    
    def test_drop_statements(self):
        # Test DROP TABLE
        sql = "DROP TABLE users;"
        ast = self.parse_sql(sql)
        
        self.assertEqual(len(ast), 1)
        stmt = ast[0]
        self.assertIsInstance(stmt, DropTableStmt)
        self.assertEqual(stmt.table_name.name, "users")
        
        # Test DROP INDEX
        sql = "DROP INDEX idx_name;"
        ast = self.parse_sql(sql)
        
        self.assertEqual(len(ast), 1)
        stmt = ast[0]
        self.assertIsInstance(stmt, DropIndexStmt)
        self.assertEqual(stmt.index_name.name, "idx_name")
    
    def test_complex_conditions(self):
        # Test AND condition
        sql = "SELECT * FROM users WHERE age > 18 AND active = TRUE;"
        ast = self.parse_sql(sql)
        
        stmt = ast[0]
        self.assertIsInstance(stmt.where, BinaryExpr)
        self.assertEqual(stmt.where.operator, TokenType.AND)
        
        # Test OR condition
        sql = "SELECT * FROM users WHERE age > 18 OR name = 'admin';"
        ast = self.parse_sql(sql)
        
        stmt = ast[0]
        self.assertIsInstance(stmt.where, BinaryExpr)
        self.assertEqual(stmt.where.operator, TokenType.OR)
        
        # Test BETWEEN condition
        sql = "SELECT * FROM users WHERE age BETWEEN 18 AND 30;"
        ast = self.parse_sql(sql)
        
        stmt = ast[0]
        self.assertIsInstance(stmt.where, BetweenExpr)
        self.assertEqual(stmt.where.column.name, "age")
        self.assertEqual(stmt.where.lower.value, 18)
        self.assertEqual(stmt.where.upper.value, 30)
        
        # Test IN condition
        sql = "SELECT * FROM users WHERE role IN ('admin', 'editor', 'user');"
        ast = self.parse_sql(sql)
        
        stmt = ast[0]
        self.assertIsInstance(stmt.where, InExpr)
        self.assertEqual(stmt.where.column.name, "role")
        self.assertEqual(len(stmt.where.values), 3)
        self.assertEqual(stmt.where.values[0].value, "admin")
        
        # Test NOT condition
        sql = "SELECT * FROM users WHERE NOT active = TRUE;"
        ast = self.parse_sql(sql)
        
        stmt = ast[0]
        self.assertIsInstance(stmt.where, UnaryExpr)
        self.assertEqual(stmt.where.operator, TokenType.NOT)
    
    def parse_sql(self, sql):
        scanner = Scanner(sql)
        tokens = scanner.scan_tokens()
        parser = Parser(tokens)
        return parser.parse()

if __name__ == "__main__":
    unittest.main()
