import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../parser'))

try:
    from parser import DatabaseManager
except ImportError:
    print("Error: no se pudo importar DatabaseManager.")
    sys.exit(1)

def setup_test_environment(db_dir="db_data_test"):
    if not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir)
            print(f"Directorio de prueba '{db_dir}' creado.")
        except OSError as e:
            print(f"Error creando directorio de prueba '{db_dir}': {e}")
            return None

    csv_path = os.path.join(db_dir, "sample_customers.csv")
    try:
        with open(csv_path, "w") as f:
            f.write("id,name,city\n")
            f.write("1,John Doe,New York\n")
            f.write("2,Jane Smith,London\n")
            f.write("3,Linus Torvalds,Helsinki\n")
        print(f"Archivo CSV de prueba creado en '{csv_path}'.")
    except IOError as e:
        print(f"Error creando archivo CSV de prueba '{csv_path}': {e}")

    return db_dir

def run_tests(db_manager):
    print("\n--- Tests ---")

    test_queries_create = [
        "CREATE TABLE images (id INT PRIMARY KEY, name VARCHAR(100), creationDate DATE, score FLOAT);",
        "CREATE TABLE products (prod_id INT PRIMARY KEY, category TEXT, price INT, stock INT INDEX stock_idx);",
        "CREATE TABLE empty_table (colA TEXT);"
    ]
    for q in test_queries_create:
        print(f"\nEjecutando: {q}")
        print(f"Resultado: {db_manager.execute_query(q)}")

    # NOTE: actual data loading is still a TODO in DatabaseManager
    q_create_from_file = f"CREATE TABLE customers_from_file FROM FILE '{os.path.join(db_manager.db_directory, 'sample_customers.csv')}' USING INDEX HASH(\"id\");"
    print(f"\nEjecutando: {q_create_from_file}")
    print(f"Resultado: {db_manager.execute_query(q_create_from_file)}")

    test_queries_insert = [
        "INSERT INTO images (id, name, creationDate, score) VALUES (1, 'sunset.jpg', '2024-01-15', 8.5);",
        "INSERT INTO images VALUES (2, 'mountain.png', '2024-02-10', 9.1);",
        "INSERT INTO images VALUES (3, 'beach.gif', '2024-03-20', 7.0);",
        "INSERT INTO images VALUES (4, 'forest.bmp', '2024-04-05', 8.5);",
        "INSERT INTO images VALUES (5, 'city.tiff', '2024-05-12', 6.5);",
        "INSERT INTO products VALUES (101, 'Electronics', 500, 10);",
        "INSERT INTO products VALUES (102, 'Books', 25, 150);",
        "INSERT INTO products (prod_id, category, price, stock) VALUES (103, 'Electronics', 1200, 5);",
        "INSERT INTO products VALUES (104, 'Home Goods', 75, 30);",
        "INSERT INTO products VALUES (105, 'Books', 30, 120);"
    ]
    for q in test_queries_insert:
        print(f"Ejecutando: {q} -> {db_manager.execute_query(q)}")

    test_queries_insert_errors = [
         "INSERT INTO images VALUES (1, 'duplicate_pk.jpg', '2024-01-01', 5.0);", # Duplicate PK
         "INSERT INTO products (prod_id, category) VALUES (106, 'Toys');", # Mismatched values/columns
         "INSERT INTO products VALUES (107, 'Tools', 'not_an_int', 50);", # Wrong data type
         "INSERT INTO non_existent_table VALUES (1);" # Table does not exist
    ]
    print("\n--- Testing INSERT con errores ---")
    for q in test_queries_insert_errors:
        print(f"Ejecutando: {q} -> {db_manager.execute_query(q)}")

    print("\n--- Testing SELECT con WHERE avanzado ---")
    test_queries_select = [
        "SELECT * FROM images WHERE score > 8.0;",
        "SELECT name, score FROM images WHERE score >= 8.5 AND id < 4;",
        "SELECT id, name FROM images WHERE (score = 8.5 AND id > 1) OR name = 'beach.gif';",
        "SELECT * FROM images WHERE name = 'nonexistent.jpg' OR (score < 7.0 AND id = 5);",
        "SELECT * FROM products WHERE category = 'Books' AND (price < 30 OR stock > 130);",
        "SELECT * FROM products WHERE category = 'Electronics' AND price BETWEEN 400 AND 600;",
        "SELECT * FROM products WHERE stock BETWEEN 100 AND 200;",
        "SELECT * FROM images WHERE id = 1 OR id = 2 OR id = 3;",
        "SELECT * FROM images WHERE (id = 1 OR id = 2) AND score > 9.0;"
    ]
    for q_select in test_queries_select:
        print(f"\nEjecutando: {q_select}")
        results = db_manager.execute_query(q_select)
        if isinstance(results, str) and results.startswith("Error"):
            print(f"Resultado: {results}")
        elif isinstance(results, list):
            print(f"Resultados ({len(results)} filas):")
            for row in results:
                print(f"  {row}")
        else:
            print(f"Resultado inesperado: {results}")

    test_queries_select_errors = [
        "SELECT non_existent_col FROM images;",
        "SELECT * FROM non_existent_table;",
        "SELECT * FROM images WHERE non_existent_col > 5;",
        "SELECT * FROM products WHERE price BETWEEN 'a' AND 'z';"
    ]
    print("\n--- Testing SELECT con errores ---")
    for q in test_queries_select_errors:
        print(f"Ejecutando: {q} -> {db_manager.execute_query(q)}")

    print("\n--- Testing DELETE ---")
    q_delete_complex = "DELETE FROM images WHERE (score < 7.5 AND name = 'beach.gif') OR id = 5;"
    print(f"\nEjecutando: {q_delete_complex}")
    print(f"Resultado: {db_manager.execute_query(q_delete_complex)}")

    print("\nImagenes despues de DELETE complejo:")
    results = db_manager.execute_query("SELECT * FROM images;")
    for row in results if isinstance(results, list) else []:
        print(f"  {row}")

    q_delete_all = "DELETE FROM products WHERE category = 'Home Goods';"
    print(f"\nEjecutando: {q_delete_all}")
    print(f"Resultado: {db_manager.execute_query(q_delete_all)}")

    print("\nProductos despues de DELETE Home Goods:")
    results = db_manager.execute_query("SELECT * FROM products;")
    for row in results if isinstance(results, list) else []:
        print(f"  {row}")

    print("\n--- Testing DROP TABLE ---")
    print("Ejecutando: DROP TABLE empty_table;") # PASS
    print(f"Resultado: {db_manager.execute_query('DROP TABLE empty_table;')}")
    print("Ejecutando: SELECT * FROM empty_table;") # FAIL
    print(f"Resultado: {db_manager.execute_query('SELECT * FROM empty_table;')}")
    print("Ejecutando: DROP TABLE non_existent_table;") # FAIL
    print(f"Resultado: {db_manager.execute_query('DROP TABLE non_existent_table;')}")

if __name__ == "__main__":
    test_db_directory = "datos"

    if os.path.exists(test_db_directory):
        import shutil
        try:
            shutil.rmtree(test_db_directory)
            print(f"Directorio de prueba anterior '{test_db_directory}' eliminado.")
        except OSError as e:
            print(f"Error eliminando directorio de prueba anterior '{test_db_directory}': {e}")

    actual_test_db_dir = setup_test_environment(test_db_directory)

    if actual_test_db_dir:
        db_manager_instance = DatabaseManager(db_directory=actual_test_db_dir)
        run_tests(db_manager_instance)
        print("\n--------------------")
        print(f"Los datos de prueba se guardaron en: '{os.path.abspath(actual_test_db_dir)}'")
    else:
        print("No se pudo configurar el entorno de prueba. Pruebas abortadas.")
