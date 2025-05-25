import re
import os
from typing import Any, List, Dict, Optional
from datetime import datetime
from api.schemas import DataType

class DataValidator:
    """Data validation utilities for different data types"""
    
    @staticmethod
    def validate_sql_identifier(identifier: str) -> bool:
        """Validate SQL identifiers (table names, column names)"""
        if not identifier:
            return False
        
        # SQL identifier rules: start with letter/underscore, contain only alphanumeric and underscore
        pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
        return bool(re.match(pattern, identifier))
    
    @staticmethod
    def validate_file_name(filename: str) -> bool:
        """Validate uploaded file names"""
        if not filename:
            return False
        
        # Check for dangerous characters
        dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in dangerous_chars:
            if char in filename:
                return False
        
        return True
    
    @staticmethod
    def validate_data_type_value(value: Any, data_type: DataType, size: Optional[int] = None) -> bool:
        """Validate if a value matches the expected data type"""
        if value is None:
            return True  # NULL values are generally allowed
        
        try:
            if data_type == DataType.INT:
                int(value)
                return True
            elif data_type == DataType.FLOAT:
                float(value)
                return True
            elif data_type == DataType.DATE:
                DataValidator._validate_date_string(str(value))
                return True
            elif data_type == DataType.VARCHAR:
                str_value = str(value)
                if size and len(str_value) > size:
                    return False
                return True
            elif data_type == DataType.ARRAY_FLOAT:
                if isinstance(value, (list, tuple)):
                    for item in value:
                        float(item)
                    return True
                elif isinstance(value, str):
                    # Try to parse as array string
                    DataValidator._parse_array_string(value)
                    return True
                return False
            else:
                return False
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def _validate_date_string(date_str: str) -> datetime:
        """Validate and parse date string"""
        formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%Y-%m-%d %H:%M:%S',
            '%d/%m/%Y %H:%M:%S',
            '%m/%d/%Y %H:%M:%S'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        raise ValueError(f"Invalid date format: {date_str}")
    
    @staticmethod
    def _parse_array_string(array_str: str) -> List[float]:
        """Parse array string format"""
        # Remove brackets if present
        array_str = array_str.strip()
        if array_str.startswith('[') and array_str.endswith(']'):
            array_str = array_str[1:-1]
        
        # Split by comma and convert to float
        if not array_str.strip():
            return []
        
        return [float(x.strip()) for x in array_str.split(',')]
    
    @staticmethod
    def sanitize_sql_query(query: str) -> str:
        """Basic SQL injection prevention"""
        # Remove potentially dangerous SQL commands
        dangerous_keywords = [
            'DROP', 'CREATE', 'ALTER', 'TRUNCATE', 'EXEC', 'EXECUTE',
            'DECLARE', 'CAST', 'CONVERT', 'UNION', 'INFORMATION_SCHEMA'
        ]
        
        query_upper = query.upper()
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                raise ValueError(f"Query contains forbidden keyword: {keyword}")
        
        return query.strip()
    
    @staticmethod
    def validate_query_syntax(query: str) -> Dict[str, Any]:
        """Basic query syntax validation"""
        query = query.strip()
        if not query:
            raise ValueError("Empty query")
        
        # Check for basic SQL structure
        query_upper = query.upper()
        
        if query_upper.startswith('SELECT'):
            if 'FROM' not in query_upper:
                raise ValueError("SELECT query must contain FROM clause")
        elif query_upper.startswith('INSERT'):
            if 'INTO' not in query_upper or 'VALUES' not in query_upper:
                raise ValueError("INSERT query must contain INTO and VALUES clauses")
        elif query_upper.startswith('UPDATE'):
            if 'SET' not in query_upper:
                raise ValueError("UPDATE query must contain SET clause")
        elif query_upper.startswith('DELETE'):
            if 'FROM' not in query_upper:
                raise ValueError("DELETE query must contain FROM clause")
        else:
            raise ValueError("Unsupported query type")
        
        return {"valid": True, "query_type": query_upper.split()[0]}

class SecurityValidator:
    """Security validation utilities"""
    
    @staticmethod
    def validate_user_access(user_id: int, resource_user_id: int) -> bool:
        """Check if user has access to a resource"""
        return user_id == resource_user_id
    
    @staticmethod
    def validate_file_path(file_path: str, allowed_base_paths: List[str]) -> bool:
        """Validate file path to prevent directory traversal"""
        abs_path = os.path.abspath(file_path)
        
        for base_path in allowed_base_paths:
            abs_base = os.path.abspath(base_path)
            if abs_path.startswith(abs_base):
                return True
        
        return False
    
    @staticmethod
    def validate_file_size(file_size: int, max_size: int) -> bool:
        """Validate file size"""
        return 0 < file_size <= max_size
    
    @staticmethod
    def validate_rate_limit(user_id: int, action: str, limit: int, window_seconds: int) -> bool:
        """Basic rate limiting validation (placeholder)"""
        # This would typically use Redis or similar for tracking
        # For now, just return True
        return True
