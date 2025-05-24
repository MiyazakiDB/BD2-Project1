import sys
import os
from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from fastapi.responses import JSONResponse, StreamingResponse
import io
import csv
from typing import Any, Dict, List
from uuid import UUID

# Import your existing parser
from parser.parser import SQLParser, DatabaseManager
from backend.models.user import User
from backend.core.auth.jwt import get_current_user
from backend.core.filestore import file_store
from backend.settings import DATA_DIR

router = APIRouter()

# Create user-specific database managers
user_db_managers = {}

def get_db_manager(user_id: UUID) -> DatabaseManager:
    user_id_str = str(user_id)
    if user_id_str not in user_db_managers:
        # Create a user-specific directory for database files
        user_db_dir = os.path.join(DATA_DIR, user_id_str, "tables")
        os.makedirs(user_db_dir, exist_ok=True)
        
        # Initialize a database manager for this user
        user_db_managers[user_id_str] = DatabaseManager(db_directory=user_db_dir)
    
    return user_db_managers[user_id_str]

@router.post("/")
async def execute_sql_query(
    request: Request,
    query: str = Body(...),
    current_user: User = Depends(get_current_user)
):
    # Get user-specific database manager
    db_manager = get_db_manager(current_user.id)
    
    # Execute query
    try:
        result = db_manager.execute_query(query)
        
        # Check Accept header for preferred response format
        accept_header = request.headers.get("accept", "").lower()
        
        # Handle results based on type
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
    current_user: User = Depends(get_current_user)
):
    # Metada del archivo
    metadata = file_store.get_file_by_id(current_user.id, file_id)
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Construcción de la tbla a partir del archivo
    query = f"CREATE TABLE {table_name} FROM FILE '{metadata['path']}'"
    
    # Add index information if provided
    if index_type and index_column:
        query += f" USING INDEX {index_type} ({index_column})"
    
    # Execute query
    db_manager = get_db_manager(current_user.id)
    result = db_manager.execute_query(query)
    
    return {"message": result}
