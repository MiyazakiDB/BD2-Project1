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
    
    async def process_file(self, file_path: str, columns: List[ColumnDefinition], has_headers: bool = True) -> List[List[Any]]:
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.csv':
            return await self._process_csv(file_path, columns, has_headers)
        elif file_ext == '.txt':
            return await self._process_txt(file_path, columns, has_headers)
        elif file_ext == '.dat':
            return await self._process_dat(file_path, columns)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
        


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
    
    
    
    async def _process_csv(self, file_path: str, columns: List[ColumnDefinition], has_headers: bool = True) -> List[List[Any]]:
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
    
    async def _process_txt(self, file_path: str, columns: List[ColumnDefinition], has_headers: bool = True) -> List[List]:
        data = []
        
        print(f"=== PROCESSING TXT FILE ===")
        print(f"File: {file_path}")
        print(f"Has headers: {has_headers}")
        print(f"Expected columns: {[(col.name, col.data_type) for col in columns]}")
        
        # Leer todo el contenido del archivo primero para debug
        with open(file_path, 'r', encoding='utf-8') as f:
            all_content = f.read()
            print(f"File content:\n{all_content}")
        
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            line_num = 0
            skip_first_line = has_headers
            
            async for line in f:
                line_num += 1
                original_line = line
                line = line.strip()
                
                print(f"Line {line_num}: '{line}'")
                
                if not line:  # Skip empty lines
                    print(f"  -> Skipping empty line")
                    continue
                
                # Skip first non-empty line if it has headers
                if skip_first_line:
                    print(f"  -> Skipping header line: '{line}'")
                    skip_first_line = False
                    continue
                    
                # Split by comma (CSV format)
                values = [v.strip() for v in line.split(',')]
                print(f"  -> Split values: {values}")
                
                # Validate number of columns
                if len(values) != len(columns):
                    error_msg = f"Line {line_num}: Expected {len(columns)} columns, got {len(values)}"
                    print(f"  -> ERROR: {error_msg}")
                    raise ValueError(error_msg)
                
                # Type conversion
                processed_row = []
                for i, (value, col) in enumerate(zip(values, columns)):
                    try:
                        processed_value = self._convert_value(value, col.data_type)
                        processed_row.append(processed_value)
                        print(f"    Column '{col.name}': '{value}' -> {processed_value} ({type(processed_value)})")
                    except Exception as e:
                        error_msg = f"Line {line_num}, Column {col.name}: {str(e)}"
                        print(f"    -> ERROR: {error_msg}")
                        raise ValueError(error_msg)
                
                print(f"  -> Final processed row: {processed_row}")
                data.append(processed_row)
    
        print(f"=== FINAL PROCESSED DATA ===")
        print(f"Total rows processed: {len(data)}")
        for i, row in enumerate(data):
            print(f"  Final row {i}: {row}")
        print(f"=== END PROCESSING ===")
        
        return data
    
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
    
    def _convert_value(self, value: str, data_type: str) -> Any:
        """Convert string value to appropriate data type"""
        try:
            if data_type == 'INT':
                return int(value)
            elif data_type == 'FLOAT':
                return float(value)
            elif data_type == 'VARCHAR':
                return str(value)
            elif data_type == 'BOOLEAN':
                return value.lower() in ('true', '1', 'yes', 'on')
            elif data_type == 'DATE':
                from datetime import datetime
                # Try multiple date formats
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                    try:
                        return datetime.strptime(value, fmt).date()
                    except ValueError:
                        continue
                raise ValueError(f"Cannot parse date: {value}")
            else:
                raise ValueError(f"Unsupported data type: {data_type}")
        except Exception as e:
            raise ValueError(f"Cannot convert '{value}' to {data_type}: {str(e)}")
    
    async def save_table_data(self, file_path: str, data: List[List[Any]]):
        """Save processed table data to file as JSON"""
        import json
        import os
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        print(f"=== CORRECT save_table_data ===")
        print(f"File path: {file_path}")
        print(f"Number of rows to save: {len(data)}")
        
        # Mostrar las primeras filas para debug
        for i, row in enumerate(data[:3]): # Muestra solo las primeras 3 filas
            print(f"  Row {i} to save: {row} (type: {type(row)})")
        
        try:
            # Guardar como un array JSON completo
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str) 
                # default=str es un fallback para tipos no serializables, como datetime.date
            
            file_size = os.path.getsize(file_path)
            print(f"Data saved successfully. File size: {file_size} bytes")
            
            # Verificación inmediata del contenido guardado
            with open(file_path, 'r', encoding='utf-8') as f:
                saved_content_preview = f.read(200) # Leer solo los primeros 200 caracteres
            print(f"Verification - saved content preview: {saved_content_preview}...")
            
        except Exception as e:
            print(f"ERROR in save_table_data: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
