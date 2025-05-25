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
        
    async def execute_query(self, query: str, user_id: int) -> QueryResponse:
        start_time = time.time()
        initial_io = self.storage_manager.get_io_operations()
        
        try:
            # Parse query
            parsed_query = self._parse_query(query.strip())
            
            # Execute based on query type
            if parsed_query["type"] == "SELECT":
                result = await self._execute_select(parsed_query, user_id)
            elif parsed_query["type"] == "INSERT":
                result = await self._execute_insert(parsed_query, user_id)
            elif parsed_query["type"] == "DELETE":
                result = await self._execute_delete(parsed_query, user_id)
            elif parsed_query["type"] == "UPDATE":
                result = await self._execute_update(parsed_query, user_id)
            else:
                raise ValueError(f"Unsupported query type: {parsed_query['type']}")
            
            execution_time = (time.time() - start_time) * 1000
            io_operations = self.storage_manager.get_io_operations() - initial_io
            
            await self.metrics.record_query(execution_time, io_operations)
            
            return ResponseFormatter.format_query_response(
                columns=result["columns"],
                data=result["data"],
                execution_time=execution_time,
                io_operations=io_operations,
                page=result.get("page", 1)
            )
            
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            execution_time = (time.time() - start_time) * 1000
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
        # Basic SELECT parser
        # SELECT columns FROM table WHERE conditions ORDER BY column LIMIT n
        
        select_pattern = r"SELECT\s+(.+?)\s+FROM\s+(\w+)(?:\s+WHERE\s+(.+?))?(?:\s+ORDER\s+BY\s+(.+?))?(?:\s+LIMIT\s+(\d+))?"
        match = re.match(select_pattern, query, re.IGNORECASE | re.DOTALL)
        
        if not match:
            raise ValueError("Invalid SELECT syntax")
        
        columns_str, table, where_clause, order_by, limit = match.groups()
        
        columns = [col.strip() for col in columns_str.split(",")] if columns_str != "*" else ["*"]
        
        parsed = {
            "type": "SELECT",
            "columns": columns,
            "table": table.lower(),
            "where": self._parse_where_clause(where_clause) if where_clause else None,
            "order_by": order_by.strip() if order_by else None,
            "limit": int(limit) if limit else None
        }
        
        return parsed
    
    def _parse_where_clause(self, where_clause: str) -> List[Dict[str, Any]]:
        # Simple WHERE parser for conditions like: column = value, column > value, etc.
        conditions = []
        
        # Split by AND/OR (simplified)
        parts = re.split(r'\s+(AND|OR)\s+', where_clause, flags=re.IGNORECASE)
        
        for i in range(0, len(parts), 2):
            condition_str = parts[i].strip()
            operator_match = re.match(r'(\w+)\s*(=|!=|<|>|<=|>=)\s*(.+)', condition_str)
            
            if operator_match:
                column, operator, value = operator_match.groups()
                # Remove quotes from string values
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
        # INSERT INTO table (columns) VALUES (values)
        insert_pattern = r"INSERT\s+INTO\s+(\w+)\s*\((.+?)\)\s*VALUES\s*\((.+?)\)"
        match = re.match(insert_pattern, query, re.IGNORECASE)
        
        if not match:
            raise ValueError("Invalid INSERT syntax")
        
        table, columns_str, values_str = match.groups()
        columns = [col.strip() for col in columns_str.split(",")]
        values = [val.strip().strip("'\"") for val in values_str.split(",")]
        
        return {
            "type": "INSERT",
            "table": table.lower(),
            "columns": columns,
            "values": [self._convert_value(val) for val in values]
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
        table_name = parsed_query["table"]
        table_metadata = self.catalog.get_table_metadata(table_name, user_id)
        
        if not table_metadata:
            raise ValueError(f"Table {table_name} not found")
        
        # Load table data
        data_file_path = os.path.join(self.storage_manager.data_dir, table_metadata["data_file"])
        table_data = await self._load_table_data(data_file_path)
        
        # Apply WHERE conditions
        if parsed_query["where"]:
            table_data = await self._apply_where_conditions(
                table_data, parsed_query["where"], table_metadata, user_id
            )
        
        # Select columns
        columns = [col["name"] for col in table_metadata["columns"]]
        if parsed_query["columns"] != ["*"]:
            column_indices = []
            for col_name in parsed_query["columns"]:
                try:
                    column_indices.append(columns.index(col_name))
                except ValueError:
                    raise ValueError(f"Column {col_name} not found")
            
            columns = parsed_query["columns"]
            table_data = [[row[i] for i in column_indices] for row in table_data]
        
        # Apply ORDER BY
        if parsed_query["order_by"]:
            order_column = parsed_query["order_by"]
            if order_column in columns:
                col_index = columns.index(order_column)
                table_data.sort(key=lambda row: row[col_index] if row[col_index] is not None else "")
        
        # Apply LIMIT
        if parsed_query["limit"]:
            table_data = table_data[:parsed_query["limit"]]
        
        return {
            "columns": columns,
            "data": table_data
        }
    
    async def _apply_where_conditions(
        self, data: List[List[Any]], conditions: List[Dict[str, Any]], 
        table_metadata: Dict[str, Any], user_id: int
    ) -> List[List[Any]]:
        
        columns = [col["name"] for col in table_metadata["columns"]]
        filtered_data = []
        
        for row in data:
            if await self._evaluate_conditions(row, conditions, columns, table_metadata, user_id):
                filtered_data.append(row)
        
        return filtered_data
    
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
    
    def _evaluate_condition(self, row_value: Any, operator: str, condition_value: Any) -> bool:
        if operator == "=":
            return row_value == condition_value
        elif operator == "!=":
            return row_value != condition_value
        elif operator == "<":
            return row_value < condition_value
        elif operator == ">":
            return row_value > condition_value
        elif operator == "<=":
            return row_value <= condition_value
        elif operator == ">=":
            return row_value >= condition_value
        else:
            raise ValueError(f"Unsupported operator: {operator}")
    
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
    
    async def _load_table_data(self, file_path: str) -> List[List[Any]]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            logger.error(f"Failed to load table data from {file_path}: {str(e)}")
            raise ValueError(f"Failed to load table data: {str(e)}")
    
    async def get_table_data(self, table_name: str, page: int, user_id: int) -> PaginatedDataResponse:
        table_metadata = self.catalog.get_table_metadata(table_name, user_id)
        
        if not table_metadata:
            raise ValueError(f"Table {table_name} not found")
        
        # Load table data
        data_file_path = os.path.join(self.storage_manager.data_dir, table_metadata["data_file"])
        table_data = await self._load_table_data(data_file_path)
        
        columns = [col["name"] for col in table_metadata["columns"]]
        
        return ResponseFormatter.format_table_data(columns, table_data, page)
    
    async def _execute_insert(self, parsed_query: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        # Placeholder for INSERT implementation
        return {
            "columns": ["message"],
            "data": [["INSERT not yet implemented"]]
        }
    
    async def _execute_delete(self, parsed_query: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        # Placeholder for DELETE implementation
        return {
            "columns": ["message"],
            "data": [["DELETE not yet implemented"]]
        }
    
    async def _execute_update(self, parsed_query: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        # Placeholder for UPDATE implementation
        return {
            "columns": ["message"],
            "data": [["UPDATE not yet implemented"]]
        }
