import json
import struct
from typing import Any, Union, List, Dict, Optional, Tuple
from datetime import datetime, date
from enum import Enum
from api.schemas import DataType

class TypeSystem:
    """Enhanced type system for data serialization and validation"""
    
    def __init__(self):
        self.serializers = {
            DataType.INT: self._serialize_int,
            DataType.FLOAT: self._serialize_float,
            DataType.DATE: self._serialize_date,
            DataType.VARCHAR: self._serialize_varchar,
            DataType.ARRAY_FLOAT: self._serialize_array_float
        }
        
        self.deserializers = {
            DataType.INT: self._deserialize_int,
            DataType.FLOAT: self._deserialize_float,
            DataType.DATE: self._deserialize_date,
            DataType.VARCHAR: self._deserialize_varchar,
            DataType.ARRAY_FLOAT: self._deserialize_array_float
        }
    
    def serialize_value(self, value: Any, data_type: DataType) -> bytes:
        """Serialize a value to bytes for storage"""
        if value is None:
            return b'\x00'  # NULL marker
        
        serializer = self.serializers.get(data_type)
        if not serializer:
            raise ValueError(f"No serializer for type {data_type}")
        
        data = serializer(value)
        return b'\x01' + data  # Non-NULL marker + data
    
    def deserialize_value(self, data: bytes, data_type: DataType) -> Any:
        """Deserialize bytes back to value"""
        if not data or data[0:1] == b'\x00':
            return None
        
        if data[0:1] != b'\x01':
            raise ValueError("Invalid serialized data format")
        
        deserializer = self.deserializers.get(data_type)
        if not deserializer:
            raise ValueError(f"No deserializer for type {data_type}")
        
        return deserializer(data[1:])
    
    def _serialize_int(self, value: int) -> bytes:
        return struct.pack('<q', int(value))  # 8-byte signed integer
    
    def _deserialize_int(self, data: bytes) -> int:
        return struct.unpack('<q', data)[0]
    
    def _serialize_float(self, value: float) -> bytes:
        return struct.pack('<d', float(value))  # 8-byte double
    
    def _deserialize_float(self, data: bytes) -> float:
        return struct.unpack('<d', data)[0]
    
    def _serialize_date(self, value: Union[str, date, datetime]) -> bytes:
        if isinstance(value, str):
            # Parse string to date
            try:
                dt = datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                try:
                    dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    raise ValueError(f"Invalid date format: {value}")
        elif isinstance(value, datetime):
            dt = value
        elif isinstance(value, date):
            dt = datetime.combine(value, datetime.min.time())
        else:
            raise ValueError(f"Cannot serialize date from type {type(value)}")
        
        # Serialize as timestamp
        timestamp = int(dt.timestamp())
        return struct.pack('<q', timestamp)
    
    def _deserialize_date(self, data: bytes) -> str:
        timestamp = struct.unpack('<q', data)[0]
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime('%Y-%m-%d')
    
    def _serialize_varchar(self, value: str) -> bytes:
        str_bytes = str(value).encode('utf-8')
        length = len(str_bytes)
        return struct.pack('<I', length) + str_bytes  # 4-byte length + string
    
    def _deserialize_varchar(self, data: bytes) -> str:
        length = struct.unpack('<I', data[:4])[0]
        return data[4:4+length].decode('utf-8')
    
    def _serialize_array_float(self, value: Union[List[float], str]) -> bytes:
        if isinstance(value, str):
            # Parse string representation
            if value.startswith('[') and value.endswith(']'):
                value = value[1:-1]
            float_list = [float(x.strip()) for x in value.split(',') if x.strip()]
        elif isinstance(value, (list, tuple)):
            float_list = [float(x) for x in value]
        else:
            raise ValueError(f"Cannot serialize array from type {type(value)}")
        
        # Serialize as: count (4 bytes) + floats (8 bytes each)
        count = len(float_list)
        data = struct.pack('<I', count)
        for f in float_list:
            data += struct.pack('<d', f)
        return data
    
    def _deserialize_array_float(self, data: bytes) -> List[float]:
        count = struct.unpack('<I', data[:4])[0]
        float_list = []
        offset = 4
        for _ in range(count):
            float_val = struct.unpack('<d', data[offset:offset+8])[0]
            float_list.append(float_val)
            offset += 8
        return float_list
    
    def get_type_size(self, data_type: DataType, value: Any = None) -> int:
        """Get the storage size for a data type"""
        if data_type == DataType.INT:
            return 8
        elif data_type == DataType.FLOAT:
            return 8
        elif data_type == DataType.DATE:
            return 8
        elif data_type == DataType.VARCHAR:
            if value is not None:
                return 4 + len(str(value).encode('utf-8'))
            return -1  # Variable length
        elif data_type == DataType.ARRAY_FLOAT:
            if value is not None:
                if isinstance(value, (list, tuple)):
                    return 4 + (len(value) * 8)
                elif isinstance(value, str):
                    # Estimate based on string length
                    return 4 + (len(value.split(',')) * 8)
            return -1  # Variable length
        else:
            return -1
    
    def convert_for_comparison(self, value1: Any, value2: Any, data_type: DataType) -> Tuple[Any, Any]:
        """Convert values to comparable types"""
        if data_type == DataType.INT:
            return int(value1), int(value2)
        elif data_type == DataType.FLOAT:
            return float(value1), float(value2)
        elif data_type == DataType.DATE:
            # Convert to datetime objects for comparison
            def parse_date(val):
                if isinstance(val, str):
                    try:
                        return datetime.strptime(val, '%Y-%m-%d')
                    except ValueError:
                        return datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
                return val
            return parse_date(value1), parse_date(value2)
        elif data_type == DataType.VARCHAR:
            return str(value1), str(value2)
        elif data_type == DataType.ARRAY_FLOAT:
            # For arrays, compare as lists
            def parse_array(val):
                if isinstance(val, str):
                    if val.startswith('[') and val.endswith(']'):
                        val = val[1:-1]
                    return [float(x.strip()) for x in val.split(',') if x.strip()]
                return list(val)
            return parse_array(value1), parse_array(value2)
        else:
            return value1, value2
    
    def format_for_display(self, value: Any, data_type: DataType) -> str:
        """Format value for display purposes"""
        if value is None:
            return "NULL"
        
        if data_type == DataType.INT:
            return str(int(value))
        elif data_type == DataType.FLOAT:
            return f"{float(value):.6f}".rstrip('0').rstrip('.')
        elif data_type == DataType.DATE:
            if isinstance(value, str):
                return value
            elif isinstance(value, datetime):
                return value.strftime('%Y-%m-%d')
            elif isinstance(value, date):
                return value.strftime('%Y-%m-%d')
            else:
                return str(value)
        elif data_type == DataType.VARCHAR:
            return str(value)
        elif data_type == DataType.ARRAY_FLOAT:
            if isinstance(value, (list, tuple)):
                formatted_floats = [f"{f:.6f}".rstrip('0').rstrip('.') for f in value]
                return f"[{', '.join(formatted_floats)}]"
            else:
                return str(value)
        else:
            return str(value)
