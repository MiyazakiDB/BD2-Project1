from fastapi import APIRouter, Depends, HTTPException
import time
import sys
import os

# Añadir el directorio raíz a sys.path para importaciones
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from parser.parser import execute_sql
from backend.schemas import QueryRequest, QueryResult, MultimediaQueryRequest, MultimediaQueryResult
from backend.utils.auth import get_current_active_user
from backend.database import User, Table, File, get_db
from sqlalchemy.orm import Session
from engine.model import TableSchema, DataType, IndexType, Column
from engine.dbmanager import DBManager
from indexes.multimediatree import MultimediaSequentialIndex, MultimediaInvertedIndex

router = APIRouter(prefix="/sql", tags=["queries"])

@router.post("/", response_model=QueryResult)
def execute_query(
    query_request: QueryRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint para ejecutar consultas SQL generales.
    Procesa la consulta, la ejecuta y devuelve los resultados paginados.
    También maneja la creación de tablas en la base de datos del usuario.
    """
    query_lower = query_request.query.lower().strip()
    
    try:
        start = time.time()
        result, message = execute_sql(query_request.query)
        end = time.time()
        
        if query_lower.startswith("create table") and "successfully" in message.lower():
            table_name = query_lower.split("create table")[1].split("(")[0].strip()
            
            existing_table = db.query(Table).filter(
                Table.user_id == current_user.id,
                Table.name == table_name
            ).first()
            
            if not existing_table:
                db_table = Table(
                    name=table_name,
                    user_id=current_user.id
                )
                db.add(db_table)
                db.commit()
        
    except Exception as e:
        end = time.time()
        result, message = None, str(e)
    
    result_pagination = {
        'columns': [],
        'records': []
    }
    
    if result is not None:
        result_pagination = {
            'columns': result['columns'],
            'records': result['records'][query_request.offset:query_request.offset + query_request.limit]
        }
        total = len(result['records'])
    else:
        total = 0
    
    return {
        'data': result_pagination,
        'total': total,
        'message': message,
        'execution_time': end - start
    }

@router.post("/multimedia", response_model=MultimediaQueryResult)
def execute_multimedia_query(
    query_request: MultimediaQueryRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint para ejecutar consultas de similitud multimedia.
    Permite buscar registros similares a un archivo multimedia (imagen o audio)
    utilizando índices especializados.
    """
    
    try:
        # Obtener el archivo de consulta
        query_file = db.query(File).filter(
            File.id == query_request.query_file_id,
            File.user_id == current_user.id
        ).first()
        
        if not query_file:
            raise HTTPException(status_code=404, detail="Archivo de consulta no encontrado")
        
        # Verificar si el archivo es multimedia
        if not query_file.file_type or query_file.file_type not in ['image', 'audio']:
            raise HTTPException(status_code=400, detail="El archivo de consulta no es un archivo multimedia")
        
        # Obtener la ruta del archivo
        query_file_path = query_file.file_path
        
        # Obtener el esquema de la tabla
        db_manager = DBManager()
        table_schema = db_manager.get_table_schema(query_request.target_table)
        
        # Obtener la columna
        column = table_schema.get_column_by_name(query_request.column_name)
        
        if not column:
            raise HTTPException(
                status_code=404, 
                detail=f"Columna {query_request.column_name} no encontrada en la tabla {query_request.target_table}"
            )
        
        # Verificar si la columna es de tipo multimedia
        if column.data_type != DataType.IMAGE and column.data_type != DataType.AUDIO:
            raise HTTPException(
                status_code=400,
                detail=f"La columna {query_request.column_name} no es de tipo multimedia"
            )
        
        # Verificar si la columna tiene un índice multimedia
        if column.index_type not in [IndexType.MULTIMEDIA_SEQUENTIAL, IndexType.MULTIMEDIA_INVERTED]:
            raise HTTPException(
                status_code=400,
                detail=f"La columna {query_request.column_name} no tiene un índice multimedia"
            )
        
        # Obtener el índice apropiado
        if query_request.method == "sequential" or column.index_type == IndexType.MULTIMEDIA_SEQUENTIAL:
            index = MultimediaSequentialIndex(table_schema, column)
        else:
            index = MultimediaInvertedIndex(table_schema, column)
        
        # Ejecutar la consulta
        start_time = time.time()
        results = index.similarity_search(query_file_path, query_request.limit)
        elapsed_time = time.time() - start_time
        
        # Procesar resultados
        columns = [col.name for col in table_schema.columns]
        records = []
        
        for record_id, similarity, metadata in results:
            # Agregar el puntaje de similitud a los metadatos
            metadata["similarity_score"] = round(similarity, 4)
            
            # Convertir metadatos a una lista en el mismo orden que las columnas
            record_values = []
            for col_name in columns:
                if col_name in metadata:
                    record_values.append(metadata[col_name])
                else:
                    record_values.append(None)
            
            records.append(record_values)
        
        # Agregar similarity_score a las columnas
        if "similarity_score" not in columns:
            columns.append("similarity_score")
        
        return {
            'data': {
                'columns': columns,
                'records': records
            },
            'total': len(records),
            'execution_time': elapsed_time,
            'query_file': query_file.filename
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tables")
def list_user_tables(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Devuelve la lista de tablas del usuario actual"""
    tables = db.query(Table).filter(Table.user_id == current_user.id).all()
    return [{"id": table.id, "name": table.name, "created_at": table.created_at} for table in tables]

@router.get("/dashboard")
def get_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Devuelve información del panel de control del usuario,
    incluyendo sus tablas y archivos
    """
    tables = db.query(Table).filter(Table.user_id == current_user.id).all()
    files = db.query(File).filter(File.user_id == current_user.id).all()
    
    return {
        "tables": [{"id": table.id, "name": table.name} for table in tables],
        "files": [{"id": file.id, "filename": file.filename} for file in files]
    }
