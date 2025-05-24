import sys
import os
from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from fastapi.responses import JSONResponse, StreamingResponse
import io
import csv
from typing import Any, Dict, List
from uuid import UUID

from parser.parser import SQLParser, DatabaseManager
from backend.models.user import User
from backend.core.auth.jwt import get_current_user
from backend.core.filestore import file_store
from backend.settings import DATA_DIR

router = APIRouter()

user_db_managers = {}

def get_db_manager(user_id: UUID) -> DatabaseManager:
    user_id_str = str(user_id)
    if user_id_str not in user_db_managers:
        user_db_dir = os.path.join(DATA_DIR, user_id_str, "tables")
        os.makedirs(user_db_dir, exist_ok=True)
        
        user_db_managers[user_id_str] = DatabaseManager(db_directory=user_db_dir)
    
    return user_db_managers[user_id_str]

@router.post("/")
async def execute_sql_query(
    request: Request,
    query: str = Body(...),
    current_user: User = Depends(get_current_user)
):
    db_manager = get_db_manager(current_user.id)
    
    try:
        result = db_manager.execute_query(query)
        
        accept_header = request.headers.get("accept", "").lower()
        
        if isinstance(result, list):
            # For SELECT queries that return rows
            if accept_header == "text/csv":
                # Return as CSV
                if not result:
                    return StreamingResponse(
                        io.StringIO("No data"),
                        media_type="text/csv"
                    )
                
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=result[0].keys())
                writer.writeheader()
                writer.writerows(result)
                
                output.seek(0)
                return StreamingResponse(
                    output,
                    media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=query_result.csv"}
                )
            else:
                # Return as JSON by default
                return JSONResponse(content={"result": result})
        else:
            # For other queries that return status messages
            return {"message": result}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Query execution error: {str(e)}"
        )

@router.post("/create-table-from-file")
async def create_table_from_file(
    table_name: str = Body(...),
    file_id: UUID = Body(...),
    index_type: str = Body(None),
    index_column: str = Body(None),
    encoding: str = Body(None),
    current_user: User = Depends(get_current_user)
):
    # Metada del archivo
    metadata = file_store.get_file_by_id(current_user.id, file_id)
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Construcción de la tabla a partir del archivo
    query = f"CREATE TABLE {table_name} FROM FILE '{metadata['path']}'"
    
    if index_type and index_column:
        query += f" USING INDEX {index_type} ({index_column})"
        
    if encoding:
        query += f" WITH ENCODING '{encoding}'"
    
    db_manager = get_db_manager(current_user.id)
    result = db_manager.execute_query(query)
    
    return {"message": result}


@router.get("/tables")
async def list_tables(current_user: User = Depends(get_current_user)):
    """
    List all tables in the user's database
    """
    try:
        db_manager = get_db_manager(current_user.id)
        
        tables = []
        
        if hasattr(db_manager, '_tables'):
            tables = [
                {
                    "name": table_data.get('original_name', name),
                    "row_count": len(table_data.get('rows', [])),
                    "columns": len(table_data.get('columns', [])),
                }
                for name, table_data in db_manager._tables.items()
            ]
        
        return {"tables": tables}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving tables: {str(e)}"
        )
