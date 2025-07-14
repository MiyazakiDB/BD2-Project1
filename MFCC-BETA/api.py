from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import tempfile
import shutil
from typing import List, Optional
from pydantic import BaseModel
import uvicorn
from mfccFunction import extract_mfcc_from_file

# Importar tu clase existente
from knn import AudioSimilaritySearcher

# === MODELOS DE RESPUESTA ===
class SimilarAudio(BaseModel):
    filename: str
    similarity_score: float
    rank: int

class SearchResponse(BaseModel):
    query_filename: str
    total_results: int
    results: List[SimilarAudio]
    processing_time_seconds: float

class HealthResponse(BaseModel):
    status: str
    database_size: int
    model_loaded: bool

class VectorResponse(BaseModel):
    filename: str
    vector: List[float]
    vector_type: str
    vector_size: int

# === VARIABLE GLOBAL PARA EL SEARCHER ===
searcher = None

# === LIFESPAN EVENT HANDLER ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global searcher
    try:
        print("🚀 Inicializando sistema de búsqueda...")
        searcher = AudioSimilaritySearcher()
        print("✅ Sistema inicializado correctamente")
    except Exception as e:
        print(f"❌ Error al inicializar: {e}")
        raise
    
    yield
    
    # Shutdown
    print("🛑 Cerrando sistema...")
    searcher = None

# === CONFIGURACIÓN DE LA API ===
app = FastAPI(
    title="Audio Similarity Search API",
    description="API para búsqueda de audios similares usando MFCC y TF-IDF",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS para permitir requests desde frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === ENDPOINTS ===

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Verificar el estado del sistema"""
    return HealthResponse(
        status="healthy" if searcher else "unhealthy",
        database_size=len(searcher.filenames) if searcher else 0,
        model_loaded=searcher is not None
    )

@app.post("/search/upload", response_model=SearchResponse)
async def search_by_upload(
    file: UploadFile = File(...),
    top_k: Optional[int] = Query(10, ge=1, le=100, description="Número de resultados a retornar")
):
    """
    Buscar audios similares subiendo un archivo
    """
    if not searcher:
        raise HTTPException(status_code=503, detail="Sistema no inicializado")
    
    # Validar tipo de archivo
    if not file.filename.lower().endswith(('.wav', '.mp3', '.flac', '.m4a')):
        raise HTTPException(
            status_code=400, 
            detail="Formato no soportado. Use: wav, mp3, flac, m4a"
        )
    
    # Guardar archivo temporal
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Medir tiempo de procesamiento
        import time
        start_time = time.time()
        
        # Buscar similares
        results = searcher.find_similar_audios(temp_path, top_k=top_k)
        
        processing_time = time.time() - start_time
        
        # Formatear respuesta
        similar_audios = [
            SimilarAudio(
                filename=filename,
                similarity_score=round(score, 4),
                rank=i + 1
            )
            for i, (filename, score) in enumerate(results)
        ]
        
        return SearchResponse(
            query_filename=file.filename,
            total_results=len(similar_audios),
            results=similar_audios,
            processing_time_seconds=round(processing_time, 3)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando audio: {str(e)}")
    
    finally:
        # Limpiar archivo temporal
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

@app.get("/vector", response_model=VectorResponse)
async def get_vector_representation(
    audio_path: str = Query(..., description="Ruta del archivo de audio"),
    tfidf: bool = Query(True, description="Retornar vector TF-IDF si True, histograma crudo si False")
):
    """Obtener representación vectorial de un archivo de audio"""
    if not searcher:
        raise HTTPException(status_code=503, detail="Sistema no inicializado")

    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    try:
        # Extraer MFCC
        mfcc = extract_mfcc_from_file(audio_path)
        if mfcc.shape[0] == 0:
            raise HTTPException(status_code=400, detail="No se pudieron extraer características MFCC del audio")

        if tfidf:
            # Usar el método existente para obtener vector TF-IDF
            vector = searcher.audio_to_tfidf_vector(audio_path)
            vector_type = "tfidf"
        else:
            # Crear histograma crudo
            histogram = searcher.create_histogram(mfcc)
            vector = histogram
            vector_type = "histogram"

        return VectorResponse(
            filename=os.path.basename(audio_path),
            vector=vector.tolist(),
            vector_type=vector_type,
            vector_size=len(vector)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando audio: {str(e)}")



@app.get("/search/file", response_model=SearchResponse)
async def search_by_path(
    audio_path: str = Query(..., description="Ruta del archivo de audio"),
    top_k: Optional[int] = Query(10, ge=1, le=100, description="Número de resultados")
):
    """
    Buscar audios similares usando una ruta de archivo local
    """
    if not searcher:
        raise HTTPException(status_code=503, detail="Sistema no inicializado")
    
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    try:
        import time
        start_time = time.time()
        
        results = searcher.find_similar_audios(audio_path, top_k=top_k)
        processing_time = time.time() - start_time
        
        similar_audios = [
            SimilarAudio(
                filename=filename,
                similarity_score=round(score, 4),
                rank=i + 1
            )
            for i, (filename, score) in enumerate(results)
        ]
        
        return SearchResponse(
            query_filename=os.path.basename(audio_path),
            total_results=len(similar_audios),
            results=similar_audios,
            processing_time_seconds=round(processing_time, 3)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando audio: {str(e)}")

@app.get("/database/list")
async def list_database_audios(
    limit: Optional[int] = Query(None, ge=1, description="Límite de resultados"),
    offset: Optional[int] = Query(0, ge=0, description="Offset para paginación")
):
    """
    Listar audios en la base de datos
    """
    if not searcher:
        raise HTTPException(status_code=503, detail="Sistema no inicializado")
    
    filenames = searcher.filenames.tolist()
    
    if limit:
        end_idx = offset + limit
        filenames = filenames[offset:end_idx]
    
    return {
        "total_audios": len(searcher.filenames),
        "returned_count": len(filenames),
        "offset": offset,
        "audios": filenames
    }

@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "message": "Audio Similarity Search API",
        "version": "1.0.0",
        "status": "running",
        "database_loaded": searcher is not None,
        "endpoints": {
            "health": "/health",
            "search_upload": "/search/upload",
            "search_file": "/search/file", 
            "vector": "/vector",
            "database_list": "/database/list",
            "docs": "/docs"
        }
    }

# === EJECUTAR API ===
if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Solo para desarrollo
        log_level="info"
    )