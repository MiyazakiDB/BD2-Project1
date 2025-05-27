import re
import time
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from catalog.metadata_catalog import MetadataCatalog
from storage.storage_manager import StorageManager
from indices.index_interface import IndexInterface
from api.schemas import QueryResponse, PaginatedDataResponse
from api.responses import ResponseFormatter
from utils.metrics import MetricsService
from utils.logger import get_logger


logger = get_logger(__name__)

class QueryPlanner:
    def __init__(self, catalog: MetadataCatalog, storage_manager: StorageManager):
        self.catalog = catalog
        self.storage_manager = storage_manager
        self.metrics = MetricsService()
        self.index_interface = IndexInterface()
        # Asegúrate de que storage_manager use la misma ruta base
        self.data_dir = "./data"  # Agregar esta línea si no existe
        
    async def execute_query(self, query: str, user_id: int) -> Dict[str, Any]:
        """Execute SQL query and return results"""
        import time
        
        start_time = time.time()
        
        try:
            print(f"=== EXECUTE QUERY DEBUG ===")
            print(f"Query: {query}")
            print(f"User ID: {user_id}")
            
            # Parse the query
            parsed_query = self._parse_query(query)
            print(f"Parsed query: {parsed_query}")
            
            # Execute based on query type
            if parsed_query["type"] == "SELECT":
                result = await self._execute_select(parsed_query, user_id)
            elif parsed_query["type"] == "INSERT":
                result = await self._execute_insert(parsed_query, user_id)
            elif parsed_query["type"] == "UPDATE":
                result = await self._execute_update(parsed_query, user_id)
            elif parsed_query["type"] == "DELETE":
                result = await self._execute_delete(parsed_query, user_id)
            else:
                raise ValueError(f"Unsupported query type: {parsed_query['type']}")
            
            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000
            
            # IMPORTANTE: Asegurar que devolvemos estructura completa
            if isinstance(result, dict):
                result["execution_time_ms"] = execution_time
                print(f"Final result (dict): {result}")
            else:
                # Si result no es dict, crear estructura válida
                result = {
                    "columns": [],
                    "data": result if isinstance(result, list) else [],
                    "execution_time_ms": execution_time,
                    "page": 1,
                    "total_pages": 1,
                    "current_page": 1,
                    "rows_affected": len(result) if isinstance(result, list) else 0,
                    "io_operations": 1
                }
                print(f"Final result (converted): {result}")
        
            print(f"=== END EXECUTE QUERY DEBUG ===")
            
            return result
            
        except Exception as e:
            print(f"Error executing query: {str(e)}")
            raise ValueError(f"Query execution failed: {str(e)}")
    
    def _parse_query(self, query: str) -> Dict[str, Any]:
        query = query.upper().strip()
        
        if query.startswith("SELECT"):
            return self._parse_select(query)
        elif query.startswith("INSERT"):
            return self._parse_insert(query)
        elif query.startswith("DELETE"):
            return self._parse_delete(query)
        elif query.startswith("UPDATE"):
            return self._parse_update(query)
        else:
            raise ValueError("Unsupported query type")
    
    def _parse_select(self, query: str) -> Dict[str, Any]:
        # Remove SELECT keyword and normalize
        query_without_select = query[6:].strip()  # Remove "SELECT"

        print(f"=== PARSE SELECT DEBUG ===")
        print(f"Original query: {query}")
        print(f"Query without SELECT: {query_without_select}")

        # Find FROM clause
        from_match = re.search(r'\bFROM\s+(\w+)', query_without_select, re.IGNORECASE)
        if not from_match:
            raise ValueError("Missing FROM clause in SELECT statement")

        table_name = from_match.group(1).lower()
        print(f"Table name: {table_name}")

        # Extract column list (everything before FROM)
        columns_part = query_without_select[:from_match.start()].strip()
        if columns_part == "*":
            columns = ["*"]
        else:
            columns = [col.strip().lower() for col in columns_part.split(",")]

        print(f"Columns: {columns}")

        # Parse optional clauses (WHERE, ORDER BY, LIMIT)
        remaining_query = query_without_select[from_match.end():].strip()

        where_conditions = None
        order_by = None
        limit = None

        # --- MEJORAR AQUÍ ---
        # Extraer WHERE, ORDER BY y LIMIT de forma robusta
        where_clause = None
        order_by_clause = None
        limit_clause = None

        # Busca WHERE
        where_match = re.search(r'\bWHERE\s+(.+?)(?=\s+ORDER\s+BY|\s+LIMIT|$)', remaining_query, re.IGNORECASE)
        if where_match:
            where_clause = where_match.group(1).strip()

        # Busca ORDER BY
        order_match = re.search(r'\bORDER\s+BY\s+(\w+)', remaining_query, re.IGNORECASE)
        if order_match:
            order_by_clause = order_match.group(1).lower()

        # Busca LIMIT
        limit_match = re.search(r'\bLIMIT\s+(\d+)', remaining_query, re.IGNORECASE)
        if limit_match:
            limit_clause = int(limit_match.group(1))

        if where_clause:
            where_conditions = self._parse_where_clause(where_clause)
        else:
            where_conditions = []

        result = {
            "type": "SELECT",
            "table": table_name,
            "columns": columns,
            "where": where_conditions,
            "order_by": order_by_clause,
            "limit": limit_clause
        }

        print(f"Parsed result: {result}")
        print(f"=== END PARSE SELECT DEBUG ===")

        return result
    
    def _parse_where_clause(self, where_clause: str) -> List[Dict[str, Any]]:
        conditions = []
        # Soporta BETWEEN
        between_match = re.match(r"(\w+)\s+BETWEEN\s+(.+)\s+AND\s+(.+)", where_clause, re.IGNORECASE)
        if between_match:
            column, start, end = between_match.groups()
            start_val = self._convert_value(start.strip())
            end_val = self._convert_value(end.strip())
            print(f"DEBUG PARSED BETWEEN: {column} BETWEEN {start_val} ({type(start_val)}) AND {end_val} ({type(end_val)})")
            conditions.append({
                "column": column.lower(),
                "operator": "BETWEEN",
                "value": [start_val, end_val],
                "logical_op": None
            })
            return conditions
        # Soporta condiciones normales
        parts = re.split(r'\s+(AND|OR)\s+', where_clause, flags=re.IGNORECASE)
        for i in range(0, len(parts), 2):
            condition_str = parts[i].strip()
            operator_match = re.match(r'(\w+)\s*(=|!=|<|>|<=|>=)\s*(.+)', condition_str)
            if operator_match:
                column, operator, value = operator_match.groups()
                value = value.strip().strip("'\"")
                conditions.append({
                    "column": column.lower(),
                    "operator": operator,
                    "value": self._convert_value(value),
                    "logical_op": parts[i+1].upper() if i+1 < len(parts) else None
                })
        return conditions
    
    def _convert_value(self, value: str) -> Any:
        # Try to convert to appropriate type
        if value.upper() == "NULL":
            return None
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value
    
    def _parse_insert(self, query: str) -> Dict[str, Any]:
        """Parse INSERT query"""
        # INSERT INTO table (col1, col2) VALUES (val1, val2)
        insert_pattern = r"INSERT\s+INTO\s+(\w+)\s*\(([^)]+)\)\s+VALUES\s*\(([^)]+)\)"
        match = re.match(insert_pattern, query, re.IGNORECASE)
        
        if not match:
            raise ValueError("Invalid INSERT syntax. Expected: INSERT INTO table (columns) VALUES (values)")
        
        table, columns_str, values_str = match.groups()
        
        # Parse columns
        columns = [col.strip() for col in columns_str.split(",")]
        
        # Parse values
        values = []
        for value in values_str.split(","):
            value = value.strip()
            # Remove quotes if present
            if (value.startswith("'") and value.endswith("'")) or (value.startswith('"') and value.endswith('"')):
                values.append(value[1:-1])
            else:
                values.append(value)
    
        return {
            "type": "INSERT",
            "table": table.lower(),
            "columns": columns,
            "values": values
        }
    
    def _parse_delete(self, query: str) -> Dict[str, Any]:
        # DELETE FROM table WHERE conditions
        delete_pattern = r"DELETE\s+FROM\s+(\w+)(?:\s+WHERE\s+(.+?))?"
        match = re.match(delete_pattern, query, re.IGNORECASE)
        
        if not match:
            raise ValueError("Invalid DELETE syntax")
        
        table, where_clause = match.groups()
        
        return {
            "type": "DELETE",
            "table": table.lower(),
            "where": self._parse_where_clause(where_clause) if where_clause else None
        }
    
    def _parse_update(self, query: str) -> Dict[str, Any]:
        # UPDATE table SET column=value WHERE conditions
        update_pattern = r"UPDATE\s+(\w+)\s+SET\s+(.+?)(?:\s+WHERE\s+(.+?))?"
        match = re.match(update_pattern, query, re.IGNORECASE)
        
        if not match:
            raise ValueError("Invalid UPDATE syntax")
        
        table, set_clause, where_clause = match.groups()
        
        # Parse SET clause
        set_conditions = {}
        for assignment in set_clause.split(","):
            col_val = assignment.strip().split("=")
            if len(col_val) == 2:
                column = col_val[0].strip()
                value = col_val[1].strip().strip("'\"")
                set_conditions[column] = self._convert_value(value)
        
        return {
            "type": "UPDATE",
            "table": table.lower(),
            "set": set_conditions,
            "where": self._parse_where_clause(where_clause) if where_clause else None
        }
    

    async def _execute_select(self, parsed_query: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Execute SELECT query"""
        table_name = parsed_query["table"]
        requested_columns = parsed_query["columns"]
        where_conditions = parsed_query.get("where")
        order_by = parsed_query.get("order_by")
        limit = parsed_query.get("limit")
        
        # Get table metadata
        table_metadata = self.catalog.get_table_metadata(table_name, user_id)
        if not table_metadata:
            raise ValueError(f"Table {table_name} not found")
        
        # Get data file path
        data_file_path = table_metadata.get("data_file")
        if not data_file_path or not os.path.exists(data_file_path):
            raise ValueError(f"Data file not found for table {table_name}")
        
        # Load table data
        table_data = await self._load_table_data(data_file_path)
        
        # Get column names from metadata
        all_columns = [col["name"] for col in table_metadata["columns"]]
        
        # Determine which columns to select
        if requested_columns == ["*"]:
            selected_columns = all_columns
            column_indices = list(range(len(all_columns)))
        else:
            selected_columns = []
            column_indices = []
            for col in requested_columns:
                col = col.strip().lower()
                if col in all_columns:
                    selected_columns.append(col)
                    column_indices.append(all_columns.index(col))
                else:
                    raise ValueError(f"Column {col} not found in table {table_name}")
        
        # Apply WHERE conditions if present
        filtered_data = table_data
        if where_conditions:
            filtered_data = await self._apply_where_conditions(
                table_data, where_conditions, table_metadata, user_id
            )
        
        # Select only requested columns
        result_data = []
        for row in filtered_data:
            selected_row = [row[i] for i in column_indices]
            result_data.append(selected_row)
        
        # Apply ORDER BY (simplified implementation)
        if order_by:
            order_column = order_by.strip().lower()
            if order_column in selected_columns:
                order_index = selected_columns.index(order_column)
                result_data.sort(key=lambda x: x[order_index] if x[order_index] is not None else "")
        
        # Apply LIMIT
        if limit:
            result_data = result_data[:limit]
        
        # Preparar respuesta con todos los campos requeridos
        return {
            "columns": selected_columns,
            "data": result_data,
            "page": 1,
            "total_pages": 1,
            "current_page": 1,
            "rows_affected": len(result_data),
            "io_operations": 1
        }


    async def _load_table_data(self, file_path: str) -> List[List]:
    
    
        print(f"=== LOADING TABLE DATA ===")
        print(f"File: {file_path}")
        
        try:
            # Leer el archivo completo de una vez
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                print(f"Raw content preview: {content[:200]}...")
                
                # Parsear el contenido completo como JSON
                data = json.loads(content)
                print(f"Parsed JSON type: {type(data)}")
                
                if not isinstance(data, list):
                    raise ValueError(f"Expected JSON array, got {type(data)}")
                    
                # Verificar estructura
                print(f"Number of rows: {len(data)}")
                for i, row in enumerate(data[:3]):
                    print(f"Row {i}: {row}")
                
                return data
                
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {str(e)}")
            print(f"Content that failed to parse: {content[:500]}")
            raise ValueError(f"Failed to parse JSON data: {str(e)}")
            
        except Exception as e:
            print(f"Error loading table data: {str(e)}")
            raise ValueError(f"Failed to load table data: {str(e)}")
    
    
    
    async def _apply_where_conditions(
        self, data: List[List[Any]], conditions: List[Dict[str, Any]], 
        table_metadata: Dict[str, Any], user_id: int
    ) -> List[List[Any]]:
        columns = [col["name"] for col in table_metadata["columns"]]
        filtered_data = []

        # Intenta usar índices si están disponibles
        for cond in conditions:
            col = cond["column"]
            op = cond["operator"]
            if col in table_metadata.get("indices", {}) and op in ("=", "BETWEEN"):
                try:
                    # Usar índice
                    index_info = table_metadata["indices"][col]
                    index_type = index_info["type"]
                    index_name = f"{table_metadata['user_id']}_{table_metadata['name']}_{col}_{index_info['type'].lower()}"
                    index = self.index_interface.get_index(index_name)
                    if not index:
                        # Cargar el índice si no está en memoria
                        index_file = index_info["path"]
                        index = self.index_interface.load_index(index_type, index_name, index_file)
                
                    # Buscar filas usando el índice
                    if op == "=":
                        row_indices = index.search(cond["value"])
                        if not isinstance(row_indices, list):
                            row_indices = [row_indices] if row_indices is not None else []
                    elif op == "BETWEEN":
                        start, end = cond["value"]
                        row_indices = index.range_search(start, end)
                    else:
                        row_indices = []

                    # Filtrar data por índices encontrados
                    filtered_data = [data[i] for i in row_indices if i is not None and i < len(data)]
                    return filtered_data  # Retorna los datos filtrados por el índice
                except Exception as e:
                    # Si falla el índice, imprime un log y continúa con evaluación normal
                    print(f"Warning: Could not use index for column {col}. Error: {str(e)}")
                    break  # Salir del bucle y usar evaluación normal

        # Si no hay índice aplicable o falló, usar el método normal
        for row in data:
            if await self._evaluate_conditions(row, conditions, columns, table_metadata, user_id):
                filtered_data.append(row)

        return filtered_data
    


    def _evaluate_condition(self, row_value: Any, operator: str, condition_value: Any) -> bool:
        # Añadir logs para debug
        print(f"DEBUG EVALUATE: {row_value} ({type(row_value)}) {operator} {condition_value} ({type(condition_value)})")
    
        if operator == "=":
            return str(row_value) == str(condition_value)  # Comparación robusta como strings
        elif operator == "!=":
            return str(row_value) != str(condition_value)  # Comparación robusta como strings
        elif operator == "<":
            # Intentar comparación numérica si es posible
            try:
                if isinstance(row_value, (int, float)) and not isinstance(condition_value, (int, float)):
                    condition_value = float(condition_value)
                elif not isinstance(row_value, (int, float)) and isinstance(condition_value, (int, float)):
                    row_value = float(row_value)
                return row_value < condition_value
            except (ValueError, TypeError):
                # Fallback a comparación de strings
                return str(row_value) < str(condition_value)
        elif operator == ">":
            # Mismo enfoque que para "<"
            try:
                if isinstance(row_value, (int, float)) and not isinstance(condition_value, (int, float)):
                    condition_value = float(condition_value)
                elif not isinstance(row_value, (int, float)) and isinstance(condition_value, (int, float)):
                    row_value = float(row_value)
                return row_value > condition_value
            except (ValueError, TypeError):
                return str(row_value) > str(condition_value)
        elif operator == "<=":
            # Mismo enfoque
            try:
                if isinstance(row_value, (int, float)) and not isinstance(condition_value, (int, float)):
                    condition_value = float(condition_value)
                elif not isinstance(row_value, (int, float)) and isinstance(condition_value, (int, float)):
                    row_value = float(row_value)
                return row_value <= condition_value
            except (ValueError, TypeError):
                return str(row_value) <= str(condition_value)
        elif operator == ">=":
            # Mismo enfoque
            try:
                if isinstance(row_value, (int, float)) and not isinstance(condition_value, (int, float)):
                    condition_value = float(condition_value)
                elif not isinstance(row_value, (int, float)) and isinstance(condition_value, (int, float)):
                    row_value = float(row_value)
                return row_value >= condition_value
            except (ValueError, TypeError):
                return str(row_value) >= str(condition_value)
        elif operator == "BETWEEN":
            # Tratamiento especial para BETWEEN
            try:
                start, end = condition_value
                print(f"DEBUG BETWEEN: {start} ({type(start)}) AND {end} ({type(end)})")
            
                # Si row_value es numérico, intenta convertir start y end
                if isinstance(row_value, (int, float)):
                    try:
                        start = float(start)
                        end = float(end)
                    except (ValueError, TypeError):
                        # Si la conversión falla, convierte todo a string
                        row_value = str(row_value)
                        start = str(start)
                        end = str(end)
                else:
                    # Si row_value no es numérico, convierte todo a string
                    row_value = str(row_value)
                    start = str(start)
                    end = str(end)
            
                print(f"DEBUG AFTER CONVERSION: {row_value} ({type(row_value)}) BETWEEN {start} ({type(start)}) AND {end} ({type(end)})")
                result = start <= row_value <= end
                print(f"DEBUG RESULT: {result}")
                return result
            except Exception as e:
                print(f"DEBUG ERROR IN BETWEEN: {str(e)}")
                # Último recurso: intenta como strings
                try:
                    start, end = condition_value
                    return str(start) <= str(row_value) <= str(end)
                except:
                    return False
        else:
            raise ValueError(f"Unsupported operator: {operator}")
        
    
    async def _evaluate_conditions(
        self, row: List[Any], conditions: List[Dict[str, Any]], 
        columns: List[str], table_metadata: Dict[str, Any], user_id: int
    ) -> bool:
        
        if not conditions:
            return True
        
        result = True
        for i, condition in enumerate(conditions):
            column_name = condition["column"]
            
            if column_name not in columns:
                raise ValueError(f"Column {column_name} not found")
            
            column_index = columns.index(column_name)
            row_value = row[column_index]
            condition_value = condition["value"]
            operator = condition["operator"]
            
            # Check if we can use an index
            if column_name in table_metadata.get("indices", {}):
                condition_result = await self._evaluate_with_index(
                    table_metadata, column_name, operator, condition_value, user_id
                )
            else:
                condition_result = self._evaluate_condition(row_value, operator, condition_value)
            
            # Handle logical operators
            if i == 0:
                result = condition_result
            else:
                prev_condition = conditions[i-1]
                if prev_condition.get("logical_op") == "AND":
                    result = result and condition_result
                elif prev_condition.get("logical_op") == "OR":
                    result = result or condition_result
        
        return result
    
    
    
    async def _evaluate_with_index(
        self, table_metadata: Dict[str, Any], column_name: str, 
        operator: str, value: Any, user_id: int
    ) -> bool:
        # Use index for evaluation (placeholder implementation)
        index_info = table_metadata["indices"][column_name]
        index_type = index_info["type"]
        
        # This would interface with your existing index implementations
        # For now, fall back to regular evaluation
        return True
    
    

    async def get_table_data(self, table_name: str, page: int, user_id: int) -> dict:
        table_metadata = self.catalog.get_table_metadata(table_name, user_id)
        if not table_metadata:
            raise ValueError(f"Table {table_name} not found")
        
        data_file_path = table_metadata.get("data_file")
        if not data_file_path or not os.path.exists(data_file_path):
            raise ValueError(f"Data file not found for table {table_name}")
        
        table_data = await self._load_table_data(data_file_path)
        
        # Paginate results
        page_size = 50
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_data = table_data[start_idx:end_idx]
        
        # Convertir columnas a formato correcto
        column_names = [col["name"] for col in table_metadata["columns"]]
        
        return {
            "data": paginated_data,
            "columns": column_names,
            "total_pages": (len(table_data) + page_size - 1) // page_size,
            "current_page": page,
            "total_rows": len(table_data),
            "page_size": page_size
        }

    
    
    async def _execute_insert(self, parsed_query: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Execute INSERT query"""
        table_name = parsed_query["table"]
        columns = parsed_query["columns"]
        values = parsed_query["values"]
        
        print(f"=== EXECUTING INSERT ===")
        print(f"Table: {table_name}")
        print(f"Columns: {columns}")
        print(f"Values: {values}")
        
        # Get table metadata
        table_metadata = self.catalog.get_table_metadata(table_name, user_id)
        if not table_metadata:
            raise ValueError(f"Table {table_name} not found")
        
        # Get data file path
        data_file_path = table_metadata.get("data_file")
        if not data_file_path:
            raise ValueError(f"Data file path not found for table {table_name}")
        
        # Load existing table data
        if os.path.exists(data_file_path):
            existing_data = await self._load_table_data(data_file_path)
        else:
            existing_data = []
    
        # Get column definitions from metadata
        table_columns = [col["name"].lower() for col in table_metadata["columns"]]
        column_types = {col["name"].lower(): col["data_type"] for col in table_metadata["columns"]}
    
        print(f"Table columns: {table_columns}")
        print(f"Column types: {column_types}")
    
        # Validate columns in INSERT
        for col in columns:
            if col.lower() not in table_columns:
                raise ValueError(f"Column '{col}' does not exist in table '{table_name}'")
    
        # Validate number of values matches number of columns
        if len(values) != len(columns):
            raise ValueError(f"Number of values ({len(values)}) does not match number of columns ({len(columns)})")
    
        # Convert and validate values according to column types
        converted_row = []
        for i, col in enumerate(table_columns):
            if col in [c.lower() for c in columns]:
                # Find the value for this column
                col_index = [c.lower() for c in columns].index(col)
                value = values[col_index]
            
                # Convert value to appropriate type
                data_type = column_types[col]
                try:
                    converted_value = self._convert_value_for_insert(value, data_type)
                    converted_row.append(converted_value)
                except Exception as e:
                    raise ValueError(f"Error converting value '{value}' for column '{col}' (type {data_type}): {str(e)}")
            else:
                # Column not provided in INSERT, use default value (NULL or appropriate default)
                converted_row.append(None)
    
        print(f"Converted row: {converted_row}")
    
        # Add the new row to existing data
        existing_data.append(converted_row)
    
        # Save updated data back to file
        await self._save_table_data(data_file_path, existing_data)
    
        print(f"=== INSERT COMPLETED ===")
    
        return {
            "columns": ["message"],
            "data": [["INSERT completed successfully. 1 row affected."]],
            "page": 1,
            "total_pages": 1,
            "current_page": 1,
            "rows_affected": 1,
            "io_operations": 1
        }

    def _convert_value_for_insert(self, value: str, data_type: str) -> Any:
        """Convert string value to appropriate data type for INSERT"""
        try:
            if value.upper() == 'NULL':
                return None
            
            if data_type == 'INT':
                return int(value)
            elif data_type == 'FLOAT':
                return float(value)
            elif data_type == 'VARCHAR':
                # Remove quotes if present
                if (value.startswith("'") and value.endswith("'")) or (value.startswith('"') and value.endswith('"')):
                    return value[1:-1]
                return str(value)
            elif data_type == 'BOOLEAN':
                return value.lower() in ('true', '1', 'yes', 'on')
            elif data_type == 'DATE':
                from datetime import datetime
                # Try multiple date formats but return as string for JSON compatibility
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                    try:
                        parsed_date = datetime.strptime(value, fmt)
                        return parsed_date.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
                raise ValueError(f"Cannot parse date: {value}")
            else:
                raise ValueError(f"Unsupported data type: {data_type}")
        except Exception as e:
            raise ValueError(f"Cannot convert '{value}' to {data_type}: {str(e)}")

    async def _save_table_data(self, file_path: str, data: List[List[Any]]):
        """Save table data to file"""
        import json
        import os
    
        print(f"=== SAVING TABLE DATA ===")
        print(f"File: {file_path}")
        print(f"Number of rows to save: {len(data)}")
    
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
            print(f"Data saved successfully")
        
        except Exception as e:
            print(f"Error saving table data: {str(e)}")
            raise ValueError(f"Failed to save table data: {str(e)}")


