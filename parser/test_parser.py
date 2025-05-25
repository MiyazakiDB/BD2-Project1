from parser import parse_sql
from pprint import pprint

def test_parser():
    # Test cases
    test_cases = [
        """CREATE TABLE ventas (
    id INT PRIMARY KEY,
    producto VARCHAR(50),
    cantidad INT,
    precio FLOAT,
    fecha VARCHAR(20)
);
CREATE INDEX ventas_id_idx ON ventas USING BTREE (id);
DROP INDEX ventas_fecha_idx;
""",
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
