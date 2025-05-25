import unittest
import sys
import os
# Add the parent directory to sys.path to find the parser module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from parser.scanner import Scanner
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
        # This requires implementing the insert_statement method in the Parser class
        sql = "INSERT INTO users (name, email) VALUES ('John', 'john@example.com');"
        # Uncomment when implemented:
        # ast = self.parse_sql(sql)
        # self.assertIsInstance(ast[0], InsertStmt)
    
    def test_delete_statement(self):
        # This requires implementing the delete_statement method in the Parser class
        sql = "DELETE FROM users WHERE id = 5;"
        # Uncomment when implemented:
        # ast = self.parse_sql(sql)
        # self.assertIsInstance(ast[0], DeleteStmt)
    
    def parse_sql(self, sql):
        scanner = Scanner(sql)
        tokens = scanner.scan_tokens()
        parser = Parser(tokens)
        return parser.parse()

if __name__ == "__main__":
    unittest.main()
