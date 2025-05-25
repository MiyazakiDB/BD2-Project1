from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

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

# Auth endpoints
@app.post("/auth/register", response_model=AuthResponse)
async def register(user_data: UserRegister):
    return await auth_service.register(user_data)

@app.post("/auth/login", response_model=AuthResponse)
async def login(user_data: UserLogin):
    return await auth_service.login(user_data)

# File management endpoints
@app.post("/files/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    return await storage_manager.upload_file(file, current_user["user_id"])

@app.get("/files", response_model=List[FileInfo])
async def list_files(current_user: dict = Depends(get_current_user)):
    return await storage_manager.list_user_files(current_user["user_id"])

@app.delete("/files/{filename}")
async def delete_file(
    filename: str,
    current_user: dict = Depends(get_current_user)
):
    return await storage_manager.delete_file(filename, current_user["user_id"])

# Table management endpoints
@app.post("/tables/create", response_model=TableResponse)
async def create_table(
    table_data: CreateTableRequest,
    current_user: dict = Depends(get_current_user)
):
    return await catalog.create_table(table_data, current_user["user_id"])

@app.get("/tables", response_model=List[TableInfo])
async def list_tables(current_user: dict = Depends(get_current_user)):
    return await catalog.list_user_tables(current_user["user_id"])

@app.delete("/tables/{table_name}")
async def delete_table(
    table_name: str,
    current_user: dict = Depends(get_current_user)
):
    return await catalog.delete_table(table_name, current_user["user_id"])

@app.get("/tables/{table_name}/data", response_model=PaginatedDataResponse)
async def get_table_data(
    table_name: str,
    page: int = Query(1, ge=1),
    current_user: dict = Depends(get_current_user)
):
    return await query_planner.get_table_data(table_name, page, current_user["user_id"])

# Query execution endpoint
@app.post("/query", response_model=QueryResponse)
async def execute_query(
    query_data: QueryRequest,
    current_user: dict = Depends(get_current_user)
):
    return await query_planner.execute_query(query_data.query, current_user["user_id"])

# Metrics endpoint
@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics(current_user: dict = Depends(get_current_user)):
    return await metrics_service.get_user_metrics(current_user["user_id"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
