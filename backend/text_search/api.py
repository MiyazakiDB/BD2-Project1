from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from fastapi.security import HTTPBearer
import time
import io
from typing import List

from backend.text_search.text_document_service import TextDocumentService
from backend.text_search.schemas import (
    TextDocumentUpload, SearchRequest, SearchResponse, 
    DocumentResponse, IndexStats, UploadResponse
)
from backend.auth.auth_service import get_current_user

router = APIRouter(prefix="/text-search", tags=["Text Search"])
security = HTTPBearer()

# Initialize text document service
text_service = TextDocumentService()

@router.post("/upload-text", response_model=UploadResponse)
async def upload_text_document(
    document: TextDocumentUpload,
    current_user = Depends(get_current_user)
):
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

@router.post("/upload-file")
async def upload_text_file(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
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

@router.post("/search", response_model=SearchResponse)
async def search_documents(
    search_request: SearchRequest,
    current_user = Depends(get_current_user)
):
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

@router.get("/documents", response_model=List[DocumentResponse])
async def get_all_documents(current_user = Depends(get_current_user)):
    """Get all indexed documents"""
    try:
        documents = text_service.get_all_documents()
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")

@router.get("/documents/{doc_id}")
async def get_document(
    doc_id: str,
    current_user = Depends(get_current_user)
):
    """Get a specific document by ID"""
    try:
        document = text_service.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving document: {str(e)}")

@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    current_user = Depends(get_current_user)
):
    """Delete a document from the index"""
    try:
        success = text_service.delete_document(doc_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"message": "Document successfully deleted", "doc_id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

@router.post("/finalize-index")
async def finalize_index(current_user = Depends(get_current_user)):
    """Finalize the index (calculate TF-IDF weights and save)"""
    try:
        text_service.finalize_and_save_index()
        return {"message": "Index finalized and saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finalizing index: {str(e)}")

@router.get("/index/stats", response_model=IndexStats)
async def get_index_statistics(current_user = Depends(get_current_user)):
    """Get index statistics"""
    try:
        stats = text_service.get_index_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving index stats: {str(e)}")

@router.post("/save-index")
async def save_index(current_user = Depends(get_current_user)):
    """Manually save the current index state"""
    try:
        text_service.save_index()
        return {"message": "Index saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving index: {str(e)}")
