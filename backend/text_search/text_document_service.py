import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from index.inverted_index import InvertedIndex

class TextDocumentService:
    def __init__(self, index_path="./data/text_index"):
        self.index_path = index_path
        Path(self.index_path).mkdir(parents=True, exist_ok=True)
        
        self.inverted_index = InvertedIndex(self.index_path)
        self.load_index()
    
    def load_index(self):
        """Load existing index from disk"""
        try:
            self.inverted_index.load_index()
        except Exception as e:
            print(f"Warning: Could not load existing index: {e}")
    
    def add_document(self, text, filename=None, metadata=None):
        """Add a new text document to the index"""
        doc_id = str(uuid.uuid4())
        
        # Prepare metadata
        doc_metadata = {
            'filename': filename or f"document_{doc_id}",
            'created_at': datetime.now().isoformat(),
            'size': len(text)
        }
        if metadata:
            doc_metadata.update(metadata)
        
        # Add to index
        self.inverted_index.add_document(doc_id, text, doc_metadata)
        
        return {
            'doc_id': doc_id,
            'metadata': doc_metadata,
            'status': 'indexed'
        }
    
    def search_documents(self, query, k=10):
        """Search for documents using k-NN similarity"""
        if not query.strip():
            return []
        
        results = self.inverted_index.search_knn(query, k)
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_result = {
                'doc_id': result['doc_id'],
                'similarity_score': round(result['similarity'], 4),
                'filename': result['document']['metadata'].get('filename', 'Unknown'),
                'created_at': result['document']['metadata'].get('created_at'),
                'text_preview': result['document']['text'][:200] + "..." if len(result['document']['text']) > 200 else result['document']['text'],
                'full_text': result['document']['text'],
                'metadata': result['document']['metadata']
            }
            formatted_results.append(formatted_result)
        
        return formatted_results
    
    def get_document(self, doc_id):
        """Get a specific document by ID"""
        doc = self.inverted_index.get_document(doc_id)
        if not doc:
            return None
        
        return {
            'doc_id': doc_id,
            'text': doc['text'],
            'metadata': doc['metadata']
        }
    
    def get_all_documents(self):
        """Get all documents"""
        all_docs = self.inverted_index.get_all_documents()
        
        formatted_docs = []
        for doc_id, doc_data in all_docs.items():
            formatted_doc = {
                'doc_id': doc_id,
                'filename': doc_data['metadata'].get('filename', 'Unknown'),
                'created_at': doc_data['metadata'].get('created_at'),
                'size': doc_data['metadata'].get('size', 0),
                'text_preview': doc_data['text'][:200] + "..." if len(doc_data['text']) > 200 else doc_data['text']
            }
            formatted_docs.append(formatted_doc)
        
        return formatted_docs
    
    def delete_document(self, doc_id):
        """Delete a document from the index"""
        success = self.inverted_index.delete_document(doc_id)
        if success:
            self.save_index()
        return success
    
    def finalize_and_save_index(self):
        """Finalize the index and save to disk"""
        result = self.inverted_index.finalize_index()
        return result
    
    def save_index(self):
        """Save current index state"""
        self.inverted_index.save_index()
        return True
    
    def get_index_stats(self):
        """Get statistics about the index"""
        return {
            'total_documents': self.inverted_index.total_docs,
            'total_terms': len(self.inverted_index.index),
            'index_size_mb': self._get_index_size(),
            'documents_list': list(self.inverted_index.documents.keys())
        }
    
    def _get_index_size(self):
        """Calculate index size in MB"""
        try:
            pickle_path = os.path.join(self.index_path, 'inverted_index.pkl')
            if os.path.exists(pickle_path):
                size_bytes = os.path.getsize(pickle_path)
                return round(size_bytes / (1024 * 1024), 2)
        except:
            pass
        return 0
