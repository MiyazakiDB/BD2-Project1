from parser import parse_sql
from pprint import pprint

def test_parser():
    # Test cases
    test_cases = [
        "SELECT * FROM users;",
        "SELECT id, name FROM products WHERE price > 100;",
        "CREATE TABLE students (id INT PRIMARY KEY, name VARCHAR(50), age INT);",
        "INSERT INTO users (id, name, active) VALUES (1, 'John', TRUE);",
        "DELETE FROM orders WHERE status = 'cancelled';",
        "CREATE INDEX idx_name ON users USING BTREE (name);"
    ]
    
    for sql in test_cases:
        print(f"\nTesting: {sql}")
        try:
            result = parse_sql(sql)
            print("Resultado:")
            pprint(result)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_parser()
