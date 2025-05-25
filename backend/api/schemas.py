from pydantic import BaseModel, EmailStr
from typing import List, Optional, Any, Dict
from datetime import datetime
from enum import Enum

class DataType(str, Enum):
    INT = "INT"
    FLOAT = "FLOAT"
    DATE = "DATE"
    VARCHAR = "VARCHAR"
    ARRAY_FLOAT = "ARRAY[FLOAT]"

class IndexType(str, Enum):
    AVL = "AVL"
    HASH = "HASH"
    BTREE = "BTREE"
    GIN = "GIN"
    ISAM = "ISAM"
    RTREE = "RTREE"
    IVF = "IVF"
    ISH = "ISH"

# Auth schemas
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    username: str

# Table schemas
class ColumnDefinition(BaseModel):
    name: str
    data_type: DataType
    size: Optional[int] = None  # For VARCHAR(n)
    index_type: Optional[IndexType] = None

class CreateTableRequest(BaseModel):
    table_name: str
    file_name: str
    columns: List[ColumnDefinition]

class TableInfo(BaseModel):
    name: str
    columns: List[ColumnDefinition]
    row_count: int
    created_at: datetime

class TableResponse(BaseModel):
    message: str
    table_name: str
    rows_inserted: int

# File schemas
class FileInfo(BaseModel):
    filename: str
    size: int
    uploaded_at: datetime

class FileUploadResponse(BaseModel):
    filename: str
    message: str

# Query schemas
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    columns: List[str]
    data: List[List[Any]]
    execution_time_ms: float
    io_operations: int
    rows_affected: int
    total_pages: int
    current_page: int

class PaginatedDataResponse(BaseModel):
    columns: List[str]
    data: List[List[Any]]
    total_rows: int
    current_page: int
    total_pages: int
    page_size: int

# Metrics schemas
class MetricsResponse(BaseModel):
    total_queries: int
    avg_execution_time_ms: float
    total_io_operations: int
    buffer_cache_hit_ratio: float
    active_tables: int
