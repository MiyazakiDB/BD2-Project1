from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query,APIRouter,Form
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import json

from auth.auth_service import AuthService, get_current_user
from catalog.metadata_catalog import MetadataCatalog
from storage.storage_manager import StorageManager
from query.query_planner import QueryPlanner
from api.schemas import *
from api.responses import *
from utils.metrics import MetricsService

load_dotenv()

app = FastAPI(
    title="BD2 Project API",
    description="Database Management System with Custom Indices",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Services
auth_service = AuthService()
catalog = MetadataCatalog()
storage_manager = StorageManager()
query_planner = QueryPlanner(catalog, storage_manager)
metrics_service = MetricsService()

@app.on_event("startup")
async def startup_event():
    await auth_service.initialize()
    await catalog.initialize()
    await storage_manager.initialize()

# API Router with prefix
api_router = APIRouter()

# Auth endpoints
@api_router.post("/auth/register", response_model=AuthResponse)
async def register(user_data: UserRegister):
    return await auth_service.register(user_data)

@api_router.post("/auth/login", response_model=AuthResponse)
async def login(user_data: UserLogin):
    return await auth_service.login(user_data)

# File management endpoints
@api_router.post("/files/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    return await storage_manager.upload_file(file, current_user["user_id"])

@api_router.get("/files", response_model=List[FileInfo])
async def list_files(current_user: dict = Depends(get_current_user)):
    return await storage_manager.list_user_files(current_user["user_id"])

@api_router.delete("/files/{filename}")
async def delete_file(
    filename: str,
    current_user: dict = Depends(get_current_user)
):
    return await storage_manager.delete_file(filename, current_user["user_id"])

# Table management endpoints
from fastapi import UploadFile, File, Form

@api_router.post("/tables/create", response_model=TableResponse)
async def create_table(
    table_name: str = Form(...),
    columns: str = Form(...),
    has_headers: str = Form("true"),  # Nuevo parámetro
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    # Define el directorio de subida
    upload_dir = "backend/uploads"
    os.makedirs(upload_dir, exist_ok=True)

    # Guarda el archivo en el servidor
    file_path = os.path.join(upload_dir, file.filename)
    
    # Escribir el archivo
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Verificar que el archivo se guardó correctamente
    if not os.path.exists(file_path):
        raise HTTPException(status_code=500, detail=f"Failed to save file {file_path}")

    # Convierte las columnas de JSON a Python
    try:
        columns_data = json.loads(columns)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format for columns")

    # Convertir has_headers string a boolean
    has_headers_bool = has_headers.lower() == "true"

    # Crea el objeto CreateTableRequest con el parámetro has_headers
    table_data = CreateTableRequest(
        table_name=table_name,
        file_name=file_path,
        columns=columns_data,
        has_headers=has_headers_bool  # Agregar este campo
    )
    
    # Llama al método create_table
    return await catalog.create_table(table_data, current_user["user_id"])

@api_router.get("/tables", response_model=List[TableInfo])
async def list_tables(current_user: dict = Depends(get_current_user)):
    return await catalog.list_user_tables(current_user["user_id"])

@api_router.delete("/tables/{table_name}")
async def delete_table(
    table_name: str,
    current_user: dict = Depends(get_current_user)
):
    return await catalog.delete_table(table_name, current_user["user_id"])

@api_router.get("/tables/{table_name}/data")
async def get_table_data(
    table_name: str,
    page: int = Query(1, ge=1),
    current_user: dict = Depends(get_current_user)
):
    try:
        result = await query_planner.get_table_data(table_name, page, current_user["user_id"])
        
        print(f"=== ENDPOINT DEBUG ===")
        print(f"Result type: {type(result)}")
        print(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        data = result.get('data', [])
        print(f"Data type: {type(data)}")
        print(f"Data length: {len(data) if isinstance(data, list) else 'Not a list'}")
        
        print(f"First 3 rows being sent to frontend:")
        for i, row in enumerate(data[:3]):
            print(f"  Row {i}: {row} (type: {type(row)}, length: {len(row) if isinstance(row, list) else 'N/A'})")
        
        columns = result.get('columns', [])
        print(f"Columns: {columns}")
        print(f"=== END ENDPOINT DEBUG ===")
        
        # Asegurar que la respuesta tenga el formato correcto
        formatted_result = {
            "data": data,
            "columns": columns,
            "total_pages": result.get("total_pages", 1),
            "current_page": result.get("current_page", 1),
            "total_rows": result.get("total_rows", 0),
            "page_size": result.get("page_size", 50)
        }
        
        return formatted_result
        
    except Exception as e:
        print(f"Error in get_table_data endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Query execution endpoint
@api_router.post("/query", response_model=QueryResponse)
async def execute_query(
    query_data: QueryRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        print(f"=== QUERY ENDPOINT DEBUG ===")
        print(f"Query: {query_data.query}")
        print(f"User ID: {current_user['user_id']}")
        
        result = await query_planner.execute_query(query_data.query, current_user["user_id"])
        
        print(f"Query result from planner: {result}")
        print(f"Query result type: {type(result)}")
        print(f"Query result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        # PROBLEMA: Asegurar que devolvemos el objeto completo, no solo los datos
        if isinstance(result, dict):
            formatted_result = {
                "columns": result.get("columns", []),
                "data": result.get("data", []),
                "execution_time_ms": result.get("execution_time_ms", 0),
                "page": result.get("page", 1),
                "total_pages": result.get("total_pages", 1),
                "current_page": result.get("current_page", result.get("page", 1)),
                "rows_affected": len(result.get("data", [])),
                "io_operations": result.get("io_operations", 1)
            }
        else:
            # Si result no es un dict, crear estructura válida
            formatted_result = {
                "columns": [],
                "data": result if isinstance(result, list) else [],
                "execution_time_ms": 0,
                "page": 1,
                "total_pages": 1,
                "current_page": 1,
                "rows_affected": len(result) if isinstance(result, list) else 0,
                "io_operations": 1
            }
        
        print(f"Formatted result being sent: {formatted_result}")
        print(f"=== END QUERY ENDPOINT DEBUG ===")
        
        return formatted_result
        
    except Exception as e:
        print(f"Error in query endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Metrics endpoint
@api_router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(current_user: dict = Depends(get_current_user)):
    return await metrics_service.get_user_metrics(current_user["user_id"])

# Mount the API router under /api prefix
app.include_router(api_router, prefix="/api")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
