#!/usr/bin/env python3
"""
Backend unificado para búsqueda multimodal sin autenticación
Combina funcionalidades de backend/routers/queries.py y complete_demo.py
"""

import os
import sys
import time
import math
import pickle
import json
from typing import List, Dict, Any, Optional, Union
from collections import defaultdict, Counter

# Añadir ruta al proyecto para importaciones
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Importar funcionalidades del proyecto (sin InvertedIndex, se importa en get_text_index)
try:
    from parser.parser import execute_sql
    from engine.dbmanager import DBManager
    from indexes.multimediatree import MultimediaSequentialIndex, MultimediaInvertedIndex
except ImportError as e:
    print(f"Warning: Could not importar módulos de parsing o multimedia: {e}")
    raise

# Procesador de texto simple sin dependencias externas
import re
def preprocess_text(text):
    text = text.lower()
    tokens = re.findall(r"\w+", text)
    return [t for t in tokens if len(t) > 2]

# Esquemas de datos
class QueryRequest(BaseModel):
    query: str
    offset: int = 0
    limit: int = 50

class QueryResult(BaseModel):
    data: Dict[str, Any]
    total: int
    message: str
    execution_time: float

class TextUploadRequest(BaseModel):
    text: str
    filename: str
    metadata: Optional[Dict[str, Any]] = {}

class SearchRequest(BaseModel):
    query: str
    k: int = 10

class SearchResult(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    total_found: int
    search_time_ms: float

# Inicializar FastAPI
app = FastAPI(title="Buscador Multimodal API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables globales para índices
text_index = None
text_index_path = os.path.join(os.path.dirname(__file__), "text_index")

def get_text_index():
    """Obtener índice de texto (lazy loading)"""
    global text_index
    if text_index is None:
        os.makedirs(text_index_path, exist_ok=True)
        # Importar InvertedIndex aquí para evitar import circular
        from index.inverted_index import InvertedIndex
        text_index = InvertedIndex(text_index_path)
        text_index.load_index()
    return text_index

@app.get("/")
def root():
    return {"message": "Buscador Multimodal API", "status": "running"}

# ===== ENDPOINTS DE TEXTO =====

@app.post("/upload-text")
def upload_text(request: TextUploadRequest):
    """Subir texto como documento"""
    try:
        idx = get_text_index()
        
        # Generar ID único
        doc_id = f"doc_{int(time.time() * 1000)}"
        
        # Agregar documento
        idx.add_document(doc_id, request.text, request.metadata)
        
        return {
            "doc_id": doc_id,
            "filename": request.filename,
            "message": "Documento agregado correctamente"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-file")
def upload_file(file: UploadFile = File(...)):
    """Subir archivo de texto"""
    try:
        if not file.content_type.startswith("text/"):
            raise HTTPException(status_code=400, detail="Solo archivos de texto permitidos")
        
        content = file.file.read().decode('utf-8')
        idx = get_text_index()
        
        doc_id = f"file_{int(time.time() * 1000)}"
        metadata = {"filename": file.filename, "content_type": file.content_type}
        
        idx.add_document(doc_id, content, metadata)
        
        return {
            "doc_id": doc_id,
            "filename": file.filename,
            "message": "Archivo subido correctamente"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=SearchResult)
def search_documents(request: SearchRequest):
    """Buscar documentos por similitud"""
    try:
        idx = get_text_index()
        
        if not idx.is_finalized:
            idx.finalize_index()
        
        start_time = time.time()
        results = idx.search_knn(request.query, k=request.k)
        search_time = (time.time() - start_time) * 1000
        
        formatted_results = []
        for result in results:
            doc_id = result['doc_id']
            score = result['similarity']
            doc_data = result['document']
            metadata = doc_data.get('metadata', {})
            text = doc_data.get('text', '')
            
            formatted_results.append({
                "doc_id": doc_id,
                "filename": metadata.get('filename', f'doc_{doc_id[:8]}'),
                "similarity_score": float(score),
                "text_preview": text[:200] + "..." if len(text) > 200 else text,
                "metadata": metadata
            })
        
        return SearchResult(
            query=request.query,
            results=formatted_results,
            total_found=len(results),
            search_time_ms=search_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/finalize-index")
def finalize_index():
    """Finalizar construcción del índice"""
    try:
        idx = get_text_index()
        result = idx.finalize_index()
        return {"message": result.get("message", "Índice finalizado"), "status": result.get("status", "success")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/index/stats")
def get_index_stats():
    """Obtener estadísticas del índice"""
    try:
        idx = get_text_index()
        
        # Calcular tamaño del índice
        index_size = 0
        if os.path.exists(os.path.join(text_index_path, "inverted_index.pkl")):
            index_size = os.path.getsize(os.path.join(text_index_path, "inverted_index.pkl"))
        
        return {
            "total_documents": idx.total_docs,
            "total_terms": len(idx.index),
            "index_size_mb": round(index_size / (1024 * 1024), 2),
            "is_finalized": idx.is_finalized
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
def get_all_documents():
    """Listar todos los documentos"""
    try:
        idx = get_text_index()
        docs = []
        for doc_id, doc_data in idx.documents.items():
            metadata = doc_data.get('metadata', {})
            docs.append({
                "doc_id": doc_id,
                "filename": metadata.get('filename', f'doc_{doc_id[:8]}'),
                "metadata": metadata
            })
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{doc_id}")
def get_document(doc_id: str):
    """Obtener documento específico"""
    try:
        idx = get_text_index()
        if doc_id not in idx.documents:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        doc_data = idx.documents[doc_id]
        return {
            "doc_id": doc_id,
            "text": doc_data.get('text', ''),
            "metadata": doc_data.get('metadata', {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== ENDPOINTS SQL =====

@app.post("/sql/public", response_model=QueryResult)
def execute_sql_query(request: QueryRequest):
    """Ejecutar consulta SQL sin autenticación"""
    try:
        start = time.time()
        result, message = execute_sql(request.query)
        end = time.time()
        
        result_pagination = {
            'columns': [],
            'records': []
        }
        
        if result is not None:
            result_pagination = {
                'columns': result['columns'],
                'records': result['records'][request.offset:request.offset + request.limit]
            }
            total = len(result['records'])
        else:
            total = 0
        
        return QueryResult(
            data=result_pagination,
            total=total,
            message=message,
            execution_time=end - start
        )
    except Exception as e:
        return QueryResult(
            data={'columns': [], 'records': []},
            total=0,
            message=str(e),
            execution_time=0
        )




# ===== ENDPOINTS MULTIMEDIA =====
@app.post("/sql/multimedia")
def execute_multimedia_query(
    target_table: str = Form(...),
    column_name: str = Form(...),
    limit: int = Form(10),
    method: str = Form("sequential"),
    file: UploadFile = File(...)
):
    """Búsqueda multimedia sin autenticación"""
    try:
        # Guardar archivo temporalmente
        temp_dir = os.path.join(os.path.dirname(__file__), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, file.filename)
        
        with open(temp_path, "wb") as f:
            content = file.file.read()
            f.write(content)
        
        start = time.time()
        
        # Obtener esquema y realizar búsqueda multimedia
        results = []
        try:
            dbm = DBManager()
            schema = dbm.get_table_schema(target_table)
            col = schema.get_column_by_name(column_name)
            
            # Verificar que el método se está usando correctamente
            print(f"🔍 Búsqueda multimedia - Método seleccionado: {method}")
            print(f"📊 Tabla: {target_table}, Columna: {column_name}")
            
            if method == "sequential":
                idx = MultimediaSequentialIndex(schema, col)
                print("📊 Usando MultimediaSequentialIndex para búsqueda")
            else:
                idx = MultimediaInvertedIndex(schema, col)
                print("📊 Usando MultimediaInvertedIndex para búsqueda")
                
            results = idx.similarity_search(temp_path, k=limit)
            
            # Si los resultados no tienen file_path, obtenerlos de la base de datos
            if results:
                from engine.record import RecordFile
                record_file = RecordFile(schema)
                
                enhanced_results = []
                for rec_id, similarity, metadata in results:
                    try:
                        # Leer el registro completo de la base de datos
                        record = record_file.read(rec_id)
                        if record and record.values:
                            # Asumir que la estructura es [id, file_path, title]
                            record_id = record.values[0] if len(record.values) > 0 else rec_id
                            file_path = record.values[1] if len(record.values) > 1 else ""
                            title = record.values[2] if len(record.values) > 2 else f"Record {rec_id}"
                            
                            enhanced_results.append((rec_id, similarity, {
                                "id": record_id,
                                "file_path": file_path,
                                "title": title
                            }))
                        else:
                            # Fallback si no se puede leer el registro
                            enhanced_results.append((rec_id, similarity, metadata))
                    except Exception as e:
                        print(f"❌ Error leyendo registro {rec_id}: {e}")
                        enhanced_results.append((rec_id, similarity, metadata))
                
                results = enhanced_results
                
        except Exception as e:
            print(f"❌ Error en búsqueda principal: {e}")
            # Si falla, usar carpeta local media_queries como fallback
            mq_dir = os.path.join(os.path.dirname(__file__), "media_queries")
            from engine.multimedia import MultimediaSearchEngine
            records = []
            if os.path.isdir(mq_dir):
                for i, fname in enumerate(os.listdir(mq_dir)):
                    path_media = os.path.join(mq_dir, fname)
                    if os.path.isfile(path_media) and fname.lower().endswith(("jpg","png","wav","mp3")):
                        records.append((i, path_media, {"file_path": fname}))
            engine = MultimediaSearchEngine()
            engine.build_index(records)
            results = engine.knn_sequential(temp_path, k=limit)
        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_path):
                os.remove(temp_path)
        # Formatear resultados
        formatted_results = []
        for rec_id, similarity, metadata in results:
            file_path = metadata.get("file_path", metadata.get("filename", ""))
            formatted_results.append({
                "id": rec_id,
                "similarity_score": float(similarity),
                "file_path": file_path,
                **metadata
            })
        # Si no hay resultados, devolver la misma consulta con score 1.0
        if not formatted_results:
            formatted_results = [{
                "id": None,
                "similarity_score": 1.0,
                "file_path": file.filename
            }]
        return {
            "data": formatted_results,
            "total": len(formatted_results),
            "execution_time": time.time() - start,
            "query_file": file.filename
        }
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== ENDPOINT PARA CONSTRUIR EL ÍNDICE MULTIMEDIA =====
@app.post("/multimedia/index")
def build_multimedia_index(
    target_table: str = Form(...),
    column_name: str = Form(...),
    method: str = Form("sequential")
):
    """Construir o actualizar el índice multimedia (codebook)"""
    try:
        print(f"🔨 Construyendo índice multimedia - Método: {method}")
        print(f"📊 Tabla: {target_table}, Columna: {column_name}")
        
        dbm = DBManager()
        schema = dbm.get_table_schema(target_table)
        col = schema.get_column_by_name(column_name)
        
        if method == "sequential":
            print("✅ Creando MultimediaSequentialIndex")
            idx = MultimediaSequentialIndex(schema, col)
        else:
            print("✅ Creando MultimediaInvertedIndex")
            idx = MultimediaInvertedIndex(schema, col)
            
        # Forzar construcción del índice
        idx._build_or_update_index()
        return {"message": f"Índice multimedia ({method}) construido correctamente."}
    except Exception as e:
        print(f"❌ Error construyendo índice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/multimedia/populate")
def populate_multimedia_table(
    target_table: str = Form(...),
    path_column: str = Form(...),
    title_column: str = Form(...),
    extensions: str = Form("wav,mp3,jpg,png"),
    source_directory: str = Form("media_queries"),
    specific_files: str = Form(None)
):
    """Carga todos los archivos de media_queries a la tabla multimedia para pruebas sin indexar inmediatamente."""
    # Determinar directorio fuente (media_queries o img_queries)
    base_dir = os.path.dirname(__file__)
    mq_dir = os.path.join(base_dir, source_directory)
    if not os.path.isdir(mq_dir):
        mq_dir = os.path.join(base_dir, "media_queries")
    dbm = DBManager()
    # Obtener esquema y posición de columnas
    schema = dbm.get_table_schema(target_table)
    # Índice de columnas en TableSchema
    cols = [col.name for col in schema.columns]
    try:
        pk_idx = cols.index(schema.get_primary_key().name)
    except Exception:
        pk_idx = 0
    try:
        path_idx = cols.index(path_column)
    except Exception:
        return JSONResponse(status_code=400, content={"detail": f"Columna ruta '{path_column}' no existe"})
    try:
        title_idx = cols.index(title_column)
    except Exception:
        return JSONResponse(status_code=400, content={"detail": f"Columna título '{title_column}' no existe"})
    # Preparar archivo de registros
    from engine.record import Record, RecordFile
    record_file = RecordFile(schema)
    next_id = record_file.max_id()
    inserted = 0
    errors = []
    exts = [ext.strip().lower() for ext in extensions.split(",")]
    # Recorrer archivos: si se especificaron nombres concretos, usar solo esos
    file_list = []
    if specific_files:
        for fname in specific_files.split(','):
            f = fname.strip()
            if f:
                file_list.append(f)
    else:
        # Tomar todos los archivos que coincidan con extensiones
        for fname in os.listdir(mq_dir):
            if any(fname.lower().endswith(ext) for ext in exts):
                file_list.append(fname)
    
    # Insertar registros
    for fname in file_list:
        file_path = os.path.join(mq_dir, fname)
        if not os.path.isfile(file_path):
            continue
        title = os.path.splitext(fname)[0]
        try:
            # Construir registro
            rec = Record(schema)
            rec.values[pk_idx] = next_id
            rec.values[path_idx] = file_path
            rec.values[title_idx] = title
            # Escribir en data.dat
            record_file.write(rec)
            next_id += 1
            inserted += 1
        except Exception as e:
            errors.append({"file": fname, "error": str(e)})
    return {"inserted": inserted, "errors": errors}

# ===== DASHBOARD (SIMPLIFICADO) =====

@app.get("/sql/dashboard")
def get_dashboard():
    """Dashboard simplificado sin autenticación"""
    try:
        # Estadísticas básicas
        idx = get_text_index()
        
        return {
            "tables": [{"name": "TextDocuments", "id": 1}],  # Mock
            "files": [{"filename": f"doc_{i}.txt", "id": i} for i in range(idx.total_docs)]
        }
    except Exception as e:
        return {"tables": [], "files": []}

if __name__ == "__main__":
    print("🚀 Iniciando Buscador Multimodal API...")
    print("📖 Documentación interactiva: http://localhost:8000/docs")
    
    uvicorn.run(
        "backend:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
