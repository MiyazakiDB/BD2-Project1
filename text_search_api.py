#!/usr/bin/env python3
"""
Standalone Text Document Search API
This is a simplified version without authentication for testing purposes
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import time
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append('/workspaces/BD2-Project1')

from backend.text_search.text_document_service import TextDocumentService

# Pydantic models
class TextDocumentUpload(BaseModel):
    text: str
    filename: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class SearchRequest(BaseModel):
    query: str
    k: Optional[int] = 10

class DocumentResponse(BaseModel):
    doc_id: str
    filename: str
    created_at: str
    size: int
    text_preview: str

class SearchResult(BaseModel):
    doc_id: str
    similarity_score: float
    filename: str
    created_at: Optional[str]
    text_preview: str
    full_text: str
    metadata: Dict[str, Any]

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_found: int
    search_time_ms: float

class IndexStats(BaseModel):
    total_documents: int
    total_terms: int
    index_size_mb: float
    documents_list: List[str]

class UploadResponse(BaseModel):
    doc_id: str
    filename: str
    status: str
    message: str

# Initialize FastAPI app
app = FastAPI(
    title="Text Document Search API",
    description="A simple API for indexing and searching text documents using TF-IDF",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize text document service
text_service = TextDocumentService(index_path="./data/text_search_index")

@app.get("/")
async def root():
    """Welcome message and API info"""
    return {
        "message": "Text Document Search API",
        "docs": "/docs",
        "endpoints": {
            "upload_text": "POST /upload-text",
            "upload_file": "POST /upload-file", 
            "search": "POST /search",
            "documents": "GET /documents",
            "get_document": "GET /documents/{doc_id}",
            "delete_document": "DELETE /documents/{doc_id}",
            "index_stats": "GET /index/stats",
            "finalize_index": "POST /finalize-index (save index)"
        }
    }

@app.post("/upload-text", response_model=UploadResponse)
async def upload_text_document(document: TextDocumentUpload):
    """Upload a text document for indexing"""
    try:
        result = text_service.add_document(
            text=document.text,
            filename=document.filename,
            metadata=document.metadata
        )
        
        return UploadResponse(
            doc_id=result['doc_id'],
            filename=result['metadata']['filename'],
            status=result['status'],
            message="Document successfully indexed"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error indexing document: {str(e)}")

@app.post("/upload-file")
async def upload_text_file(file: UploadFile = File(...)):
    """Upload a text file for indexing"""
    try:
        # Check file type
        if not file.filename.endswith(('.txt', '.md', '.csv')):
            raise HTTPException(status_code=400, detail="Only .txt, .md, and .csv files are supported")
        
        # Read file content
        content = await file.read()
        text = content.decode('utf-8')
        
        # Add to index
        result = text_service.add_document(
            text=text,
            filename=file.filename,
            metadata={
                'file_size': len(content),
                'content_type': file.content_type
            }
        )
        
        return UploadResponse(
            doc_id=result['doc_id'],
            filename=result['metadata']['filename'],
            status=result['status'],
            message="File successfully indexed"
        )
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be valid UTF-8 text")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/search", response_model=SearchResponse)
async def search_documents(search_request: SearchRequest):
    """Search for documents using text similarity"""
    try:
        start_time = time.time()
        
        results = text_service.search_documents(
            query=search_request.query,
            k=search_request.k
        )
        
        search_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return SearchResponse(
            query=search_request.query,
            results=results,
            total_found=len(results),
            search_time_ms=round(search_time, 2)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing search: {str(e)}")

@app.get("/documents", response_model=List[DocumentResponse])
async def get_all_documents():
    """Get all indexed documents"""
    try:
        documents = text_service.get_all_documents()
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")

@app.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    """Get a specific document by ID"""
    try:
        document = text_service.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving document: {str(e)}")

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document from the index"""
    try:
        success = text_service.delete_document(doc_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"message": "Document successfully deleted", "doc_id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

@app.post("/finalize-index")
async def finalize_index():
    """Finalize the index (save current state - no TF-IDF transformation)"""
    try:
        # Simply save the current index state without TF-IDF transformation
        # This avoids the complexity and potential issues with TF-IDF finalization
        text_service.save_index()
        return {"message": "Index saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving index: {str(e)}")

@app.get("/index/stats", response_model=IndexStats)
async def get_index_statistics():
    """Get index statistics"""
    try:
        stats = text_service.get_index_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving index stats: {str(e)}")

@app.post("/save-index")
async def save_index():
    """Manually save the current index state"""
    try:
        text_service.save_index()
        return {"message": "Index saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving index: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
