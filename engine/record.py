import struct
import os
import sys
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_path not in sys.path:
    sys.path.append(root_path)

from engine.model import DataType, TableSchema
from engine import utils
import logger

class Record:
    def __init__(self, schema : TableSchema, values = None):
        self.schema = schema
        self.values = [None] * len(schema.columns) if values is None else values
        self.logger = logger.CustomLogger("RECORD")
        self.RECORD_FORMAT = ""
        self.MAX_VARCHAR = 512
        self.RECORD_SIZE = 0
        self.calculate_format()
    
    def calculate_format(self):
        record_format = ""
        record_size = 0
        
        for column in self.schema.columns:
            match column.data_type:
                case DataType.INT:
                    record_format += "i"
                    record_size += struct.calcsize("i")
                case DataType.FLOAT:
                    record_format += "f"
                    record_size += struct.calcsize("f")
                case DataType.VARCHAR:
                    varchar_length = column.varchar_length
                    record_format += f"{varchar_length}s"
                    record_size += struct.calcsize(f"{varchar_length}s")
                case DataType.DATE:
                    record_format += "I"
                    record_size += struct.calcsize("I")
                case DataType.BOOL:
                    record_format += "?"
                    record_size += struct.calcsize("?")
                case DataType.POINT:
                    record_format += "ff"
                    record_size += struct.calcsize("ff")
                case DataType.IMAGE:
                    # Store path to image file as VARCHAR
                    record_format += f"{self.MAX_VARCHAR}s"
                    record_size += struct.calcsize(f"{self.MAX_VARCHAR}s")
                case DataType.AUDIO:
                    # Store path to audio file as VARCHAR
                    record_format += f"{self.MAX_VARCHAR}s"
                    record_size += struct.calcsize(f"{self.MAX_VARCHAR}s")
                case _:
                    raise ValueError(f"Unsupported data type: {column.data_type}")
        
        record_format += "?"  # For deleted flag
        record_size += struct.calcsize("?")
        
        self.RECORD_FORMAT = record_format
        self.RECORD_SIZE = record_size
    
    def pack(self) -> bytes:
        packed_values = []
        
        for i, column in enumerate(self.schema.columns):
            match column.data_type:
                case DataType.INT:
                    packed_values.append(self.values[i])
                case DataType.FLOAT:
                    packed_values.append(self.values[i])
                case DataType.VARCHAR:
                    packed_values.append(self.values[i].encode())
                case DataType.DATE:
                    packed_values.append(self.values[i])
                case DataType.BOOL:
                    packed_values.append(self.values[i])
                case DataType.POINT:
                    packed_values.append(self.values[i][0])  # x coordinate
                    packed_values.append(self.values[i][1])  # y coordinate
                case DataType.IMAGE | DataType.AUDIO:
                    # Store path to multimedia file
                    path = self.values[i]
                    if isinstance(path, str):
                        packed_values.append(path.encode())
                    else:
                        packed_values.append(b'')  # Empty string if no path
        
        packed_values.append(False)  # Not deleted
        
        return struct.pack(self.RECORD_FORMAT, *packed_values)
    
    @staticmethod
    def unpack(schema : TableSchema, record_bytes : bytes) -> 'Record':
        record = Record(schema)
        
        values = []
        offset = 0
        
        for column in schema.columns:
            match column.data_type:
                case DataType.INT:
                    value, = struct.unpack_from("i", record_bytes, offset)
                    values.append(value)
                    offset += struct.calcsize("i")
                case DataType.FLOAT:
                    value, = struct.unpack_from("f", record_bytes, offset)
                    values.append(value)
                    offset += struct.calcsize("f")
                case DataType.VARCHAR:
                    varchar_length = column.varchar_length
                    value, = struct.unpack_from(f"{varchar_length}s", record_bytes, offset)
                    values.append(value.decode().strip('\x00'))
                    offset += struct.calcsize(f"{varchar_length}s")
                case DataType.DATE:
                    value, = struct.unpack_from("I", record_bytes, offset)
                    values.append(value)
                    offset += struct.calcsize("I")
                case DataType.BOOL:
                    value, = struct.unpack_from("?", record_bytes, offset)
                    values.append(value)
                    offset += struct.calcsize("?")
                case DataType.POINT:
                    x, y = struct.unpack_from("ff", record_bytes, offset)
                    values.append((x, y))
                    offset += struct.calcsize("ff")
                case DataType.IMAGE | DataType.AUDIO:
                    # Unpack path to multimedia file
                    value, = struct.unpack_from(f"{record.MAX_VARCHAR}s", record_bytes, offset)
                    values.append(value.decode().strip('\x00'))
                    offset += struct.calcsize(f"{record.MAX_VARCHAR}s")
        
        deleted, = struct.unpack_from("?", record_bytes, offset)
        
        record.values = values
        return record

class RecordFile:
    def __init__(self, schema: TableSchema):
        self.schema = schema
        self.EMPTY_RECORD = b'\0'
        self.logger = logger.CustomLogger("RECORD_FILE")
        
        # Create path if it doesn't exist
        path = utils.get_tables_dir()
        os.makedirs(path, exist_ok=True)
        
        # Create table directory if it doesn't exist
        self.table_path = f"{path}/{schema.table_name}"
        os.makedirs(self.table_path, exist_ok=True)
        
        # Path to data file
        self.filename = f"{self.table_path}/data.dat"
        if not os.path.exists(self.filename):
            open(self.filename, "wb").close()
            
        # Create a sample record to calculate record size
        self.record = Record(schema)
        self.RECORD_SIZE = self.record.RECORD_SIZE
    
    def max_id(self) -> int:
        """Get the maximum possible ID based on file size"""
        file_size = os.path.getsize(self.filename)
        return file_size // self.RECORD_SIZE
    
    def read(self, pos : int) -> Record:
        """Read a record at the given position"""
        if pos < 0:
            self.logger.error(f"Invalid position: {pos}")
            return None
        
        # Open the file for reading
        try:
            with open(self.filename, "rb") as file:
                # Seek to the position
                file.seek(pos * self.RECORD_SIZE)
                
                # Read the record
                record_bytes = file.read(self.RECORD_SIZE)
                
                # If no record or record is smaller than expected
                if not record_bytes or len(record_bytes) < self.RECORD_SIZE:
                    self.logger.error(f"No record at position: {pos}")
                    return None
                
                # Check if record is deleted
                deleted = struct.unpack_from("?", record_bytes, self.RECORD_SIZE - 1)[0]
                if deleted:
                    self.logger.error(f"Record at position {pos} is deleted")
                    return None
                
                # Unpack the record
                record = Record.unpack(self.schema, record_bytes)
                return record
        except Exception as e:
            self.logger.error(f"Error reading record at position {pos}: {e}")
            return None
    
    def write(self, record : Record, pos : int = None) -> int:
        """Write a record to the file, either at the given position or at the end"""
        # Pack the record
        packed_record = record.pack()
        
        # Open the file for writing
        with open(self.filename, "r+b") as file:
            # If position is not specified, write at the end
            if pos is None:
                file.seek(0, 2)  # Seek to end of file
                pos = file.tell() // self.RECORD_SIZE
            else:
                file.seek(pos * self.RECORD_SIZE)
            
            # Write the record
            file.write(packed_record)
            
            # Return the position where the record was written
            return pos
    
    def delete(self, pos : int) -> bool:
        """Mark a record as deleted"""
        if pos < 0:
            self.logger.error(f"Invalid position: {pos}")
            return False
        
        try:
            with open(self.filename, "r+b") as file:
                # Seek to the position of the deleted flag
                file.seek(pos * self.RECORD_SIZE + self.RECORD_SIZE - 1)
                
                # Write the deleted flag
                file.write(struct.pack("?", True))
                
                return True
        except Exception as e:
            self.logger.error(f"Error deleting record at position {pos}: {e}")
            return False

