import csv
import os
import json
import pandas as pd
from typing import List, Any, Dict
from datetime import datetime
from api.schemas import ColumnDefinition, DataType
import aiofiles

class FileProcessor:
    def __init__(self):
        self.type_validators = {
            DataType.INT: self._validate_int,
            DataType.FLOAT: self._validate_float,
            DataType.DATE: self._validate_date,
            DataType.VARCHAR: self._validate_varchar,
            DataType.ARRAY_FLOAT: self._validate_array_float
        }
    
    async def process_file(self, file_path: str, columns: List[ColumnDefinition]) -> List[List[Any]]:
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.csv':
            return await self._process_csv(file_path, columns)
        elif file_ext == '.txt':
            return await self._process_txt(file_path, columns)
        elif file_ext == '.dat':
            return await self._process_dat(file_path, columns)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
    
    async def _process_csv(self, file_path: str, columns: List[ColumnDefinition]) -> List[List[Any]]:
        processed_data = []
        
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
            
        csv_reader = csv.reader(content.splitlines())
        headers = next(csv_reader, None)
        
        if not headers:
            raise ValueError("CSV file is empty or has no headers")
        
        for row_num, row in enumerate(csv_reader, start=2):
            if len(row) != len(columns):
                raise ValueError(f"Row {row_num}: Expected {len(columns)} columns, got {len(row)}")
            
            processed_row = []
            for i, (value, column) in enumerate(zip(row, columns)):
                try:
                    validated_value = self._validate_and_convert(value, column)
                    processed_row.append(validated_value)
                except ValueError as e:
                    raise ValueError(f"Row {row_num}, Column {i+1} ({column.name}): {str(e)}")
            
            processed_data.append(processed_row)
        
        return processed_data
    
    async def _process_txt(self, file_path: str, columns: List[ColumnDefinition]) -> List[List[Any]]:
        processed_data = []
        
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            async for line_num, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                
                # Assume tab or space separated
                values = line.split('\t') if '\t' in line else line.split()
                
                if len(values) != len(columns):
                    raise ValueError(f"Line {line_num}: Expected {len(columns)} values, got {len(values)}")
                
                processed_row = []
                for i, (value, column) in enumerate(zip(values, columns)):
                    try:
                        validated_value = self._validate_and_convert(value, column)
                        processed_row.append(validated_value)
                    except ValueError as e:
                        raise ValueError(f"Line {line_num}, Column {i+1} ({column.name}): {str(e)}")
                
                processed_data.append(processed_row)
        
        return processed_data
    
    async def _process_dat(self, file_path: str, columns: List[ColumnDefinition]) -> List[List[Any]]:
        # Assume DAT files are JSON format or binary format
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            try:
                content = await f.read()
                data = json.loads(content)
                
                processed_data = []
                for row_num, row_data in enumerate(data, start=1):
                    if isinstance(row_data, list):
                        values = row_data
                    elif isinstance(row_data, dict):
                        values = [row_data.get(col.name, '') for col in columns]
                    else:
                        raise ValueError(f"Unsupported data format in row {row_num}")
                    
                    if len(values) != len(columns):
                        raise ValueError(f"Row {row_num}: Expected {len(columns)} values, got {len(values)}")
                    
                    processed_row = []
                    for i, (value, column) in enumerate(zip(values, columns)):
                        try:
                            validated_value = self._validate_and_convert(value, column)
                            processed_row.append(validated_value)
                        except ValueError as e:
                            raise ValueError(f"Row {row_num}, Column {i+1} ({column.name}): {str(e)}")
                    
                    processed_data.append(processed_row)
                
                return processed_data
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON format in DAT file")
    
    def _validate_and_convert(self, value: str, column: ColumnDefinition) -> Any:
        if value.strip() == '':
            return None
        
        validator = self.type_validators.get(column.data_type)
        if not validator:
            raise ValueError(f"Unsupported data type: {column.data_type}")
        
        return validator(value, column)
    
    def _validate_int(self, value: str, column: ColumnDefinition) -> int:
        try:
            return int(value)
        except ValueError:
            raise ValueError(f"Invalid integer: {value}")
    
    def _validate_float(self, value: str, column: ColumnDefinition) -> float:
        try:
            return float(value)
        except ValueError:
            raise ValueError(f"Invalid float: {value}")
    
    def _validate_date(self, value: str, column: ColumnDefinition) -> str:
        try:
            # Try common date formats
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']:
                try:
                    parsed_date = datetime.strptime(value, fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            raise ValueError(f"Invalid date format: {value}")
        except ValueError:
            raise ValueError(f"Invalid date: {value}")
    
    def _validate_varchar(self, value: str, column: ColumnDefinition) -> str:
        if column.size and len(value) > column.size:
            raise ValueError(f"String too long: maximum {column.size} characters")
        return value
    
    def _validate_array_float(self, value: str, column: ColumnDefinition) -> List[float]:
        try:
            # Expect format like "[1.0, 2.0, 3.0]" or "1.0,2.0,3.0"
            if value.startswith('[') and value.endswith(']'):
                value = value[1:-1]
            
            parts = [x.strip() for x in value.split(',')]
            return [float(x) for x in parts if x]
        except ValueError:
            raise ValueError(f"Invalid array format: {value}")
    
    async def save_table_data(self, file_path: str, data: List[List[Any]]):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save as JSON for easy reading
        serialized_data = []
        for row in data:
            serialized_row = []
            for value in row:
                if isinstance(value, (list, tuple)):
                    serialized_row.append(list(value))
                else:
                    serialized_row.append(value)
            serialized_data.append(serialized_row)
        
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(serialized_data, indent=2))
