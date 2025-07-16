from pydantic import BaseModel
from typing import Optional, List, Dict, Any

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
