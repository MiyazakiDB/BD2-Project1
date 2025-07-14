import os
import sys
import requests
import json
import argparse
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def login(base_url, username, password):
    """
    Inicia sesión en la API y devuelve el token de acceso
    
    Args:
        base_url: URL base de la API
        username: Nombre de usuario
        password: Contraseña
        
    Returns:
        Token de acceso o None si falla
    """
    login_url = f"{base_url}/auth/login"
    
    try:
        response = requests.post(
            login_url,
            data={"username": username, "password": password}
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            print(f"Error al iniciar sesión: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Error de conexión: {e}")
        return None

def upload_multimedia(base_url, token, file_path):
    """
    Sube un archivo multimedia a la API
    
    Args:
        base_url: URL base de la API
        token: Token de acceso
        file_path: Ruta al archivo multimedia
        
    Returns:
        ID del archivo subido o None si falla
    """
    upload_url = f"{base_url}/files/multimedia/upload"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f)}
            response = requests.post(upload_url, headers=headers, files=files)
            
            if response.status_code == 200:
                data = response.json()
                print(f"Archivo subido correctamente: {data['filename']}")
                return data.get("id")
            else:
                print(f"Error al subir archivo: {response.status_code}")
                print(response.text)
                return None
    except Exception as e:
        print(f"Error de conexión: {e}")
        return None

def get_multimedia_files(base_url, token):
    """
    Obtiene la lista de archivos multimedia del usuario
    
    Args:
        base_url: URL base de la API
        token: Token de acceso
        
    Returns:
        Lista de archivos multimedia
    """
    files_url = f"{base_url}/files/multimedia"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(files_url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error al obtener archivos: {response.status_code}")
            print(response.text)
            return []
    except Exception as e:
        print(f"Error de conexión: {e}")
        return []

def execute_sql_query(base_url, token, query):
    """
    Ejecuta una consulta SQL
    
    Args:
        base_url: URL base de la API
        token: Token de acceso
        query: Consulta SQL
        
    Returns:
        Resultado de la consulta
    """
    query_url = f"{base_url}/sql/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": query,
        "offset": 0,
        "limit": 100
    }
    
    try:
        response = requests.post(query_url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error al ejecutar consulta: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Error de conexión: {e}")
        return None

def execute_multimedia_query(base_url, token, query_file_id, target_table, column_name, method="sequential", limit=5):
    """
    Ejecuta una consulta de similitud multimedia
    
    Args:
        base_url: URL base de la API
        token: Token de acceso
        query_file_id: ID del archivo de consulta
        target_table: Tabla objetivo
        column_name: Nombre de la columna multimedia
        method: Método de búsqueda ("sequential" o "inverted")
        limit: Número máximo de resultados
        
    Returns:
        Resultado de la consulta
    """
    query_url = f"{base_url}/sql/multimedia"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query_file_id": query_file_id,
        "target_table": target_table,
        "column_name": column_name,
        "method": method,
        "limit": limit
    }
    
    try:
        response = requests.post(query_url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error al ejecutar consulta multimedia: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Error de conexión: {e}")
        return None

def create_multimedia_table(base_url, token, table_name, column_name, index_type="MULTIMEDIA_SEQUENTIAL"):
    """
    Crea una tabla con una columna multimedia
    
    Args:
        base_url: URL base de la API
        token: Token de acceso
        table_name: Nombre de la tabla
        column_name: Nombre de la columna multimedia
        index_type: Tipo de índice (MULTIMEDIA_SEQUENTIAL o MULTIMEDIA_INVERTED)
    """
    query = f"""
    CREATE TABLE {table_name} (
        id INT,
        {column_name} IMAGE INDEX {index_type},
        description VARCHAR(100)
    );
    """
    
    result = execute_sql_query(base_url, token, query)
    if result:
        print(f"Tabla {table_name} creada correctamente")
        return True
    return False

def insert_multimedia_data(base_url, token, table_name, column_name, file_path, description):
    """
    Inserta datos multimedia en una tabla
    
    Args:
        base_url: URL base de la API
        token: Token de acceso
        table_name: Nombre de la tabla
        column_name: Nombre de la columna multimedia
        file_path: Ruta del archivo multimedia
        description: Descripción del registro
    """
    # Primero subir el archivo
    file_id = upload_multimedia(base_url, token, file_path)
    if not file_id:
        return False
    
    # Obtener la lista de archivos para encontrar la ruta del archivo subido
    files = get_multimedia_files(base_url, token)
    file_path = None
    
    for file in files:
        if file["id"] == file_id:
            file_path = file["file_path"]
            break
    
    if not file_path:
        print("No se pudo obtener la ruta del archivo subido")
        return False
    
    # Insertar en la tabla
    query = f"""
    INSERT INTO {table_name} VALUES (
        {file_id},
        '{file_path}',
        '{description}'
    );
    """
    
    result = execute_sql_query(base_url, token, query)
    if result:
        print(f"Registro insertado correctamente en la tabla {table_name}")
        return True
    return False

def main():
    parser = argparse.ArgumentParser(description="Test de API multimedia")
    parser.add_argument("--url", type=str, default="http://localhost:8000", help="URL base de la API")
    parser.add_argument("--username", type=str, required=True, help="Nombre de usuario")
    parser.add_argument("--password", type=str, required=True, help="Contraseña")
    parser.add_argument("--action", type=str, choices=["create", "insert", "search"], required=True, help="Acción a realizar")
    parser.add_argument("--table", type=str, default="imagenes", help="Nombre de la tabla")
    parser.add_argument("--column", type=str, default="imagen", help="Nombre de la columna multimedia")
    parser.add_argument("--file", type=str, help="Ruta al archivo multimedia")
    parser.add_argument("--description", type=str, default="Imagen de prueba", help="Descripción del archivo")
    parser.add_argument("--query-id", type=int, help="ID del archivo de consulta")
    parser.add_argument("--method", type=str, choices=["sequential", "inverted"], default="sequential", help="Método de búsqueda")
    
    args = parser.parse_args()
    
    # Iniciar sesión
    token = login(args.url, args.username, args.password)
    if not token:
        print("No se pudo iniciar sesión")
        return
    
    # Ejecutar acción seleccionada
    if args.action == "create":
        create_multimedia_table(args.url, token, args.table, args.column)
    
    elif args.action == "insert":
        if not args.file:
            print("Se requiere la ruta del archivo para insertar")
            return
        
        insert_multimedia_data(args.url, token, args.table, args.column, args.file, args.description)
    
    elif args.action == "search":
        if not args.query_id:
            print("Se requiere el ID del archivo de consulta")
            return
        
        result = execute_multimedia_query(args.url, token, args.query_id, args.table, args.column, args.method)
        if result:
            print("\nResultados de la búsqueda:")
            print("-------------------------")
            
            # Mostrar columnas
            columns = result["data"]["columns"]
            print(" | ".join(columns))
            print("-" * 80)
            
            # Mostrar registros
            for record in result["data"]["records"]:
                print(" | ".join(str(val) for val in record))
            
            print(f"\nTiempo de ejecución: {result['execution_time']:.4f} segundos")
            print(f"Archivo de consulta: {result['query_file']}")

if __name__ == "__main__":
    main() 