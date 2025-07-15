#!/usr/bin/env python3
"""
API Client for Text Document Search
This script demonstrates how to use the REST API endpoints
Updated version that works with the standalone API
"""

import requests
import json
import time
import os
from typing import Dict, List

class TextSearchAPIClient:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def upload_text(self, text: str, filename: str = None, metadata: Dict = None) -> Dict:
        """Upload text document for indexing"""
        data = {
            "text": text,
            "filename": filename,
            "metadata": metadata or {}
        }
        
        response = self.session.post(
            f"{self.base_url}/upload-text",
            json=data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Upload failed: {response.text}")
    
    def upload_file(self, file_path: str) -> Dict:
        """Upload text file for indexing"""
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.split('/')[-1], f, 'text/plain')}
            response = self.session.post(
                f"{self.base_url}/upload-file",
                files=files
            )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"File upload failed: {response.text}")
    
    def search(self, query: str, k: int = 10) -> Dict:
        """Search for documents"""
        data = {
            "query": query,
            "k": k
        }
        
        response = self.session.post(
            f"{self.base_url}/search",
            json=data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Search failed: {response.text}")
    
    def get_documents(self) -> List[Dict]:
        """Get all documents"""
        response = self.session.get(f"{self.base_url}/documents")
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Get documents failed: {response.text}")
    
    def get_document(self, doc_id: str) -> Dict:
        """Get specific document"""
        response = self.session.get(f"{self.base_url}/documents/{doc_id}")
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Get document failed: {response.text}")
    
    def delete_document(self, doc_id: str) -> Dict:
        """Delete document"""
        response = self.session.delete(f"{self.base_url}/documents/{doc_id}")
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Delete document failed: {response.text}")
    
    def finalize_index(self) -> Dict:
        """Finalize the index"""
        response = self.session.post(f"{self.base_url}/finalize-index")
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Finalize index failed: {response.text}")
    
    def get_index_stats(self) -> Dict:
        """Get index statistics"""
        response = self.session.get(f"{self.base_url}/index/stats")
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Get stats failed: {response.text}")

def demo_api():
    """Demonstrate the API usage"""
    client = TextSearchAPIClient()
    
    print("Text Document Search API Demo")
    print("="*40)
    
    # Sample documents
    documents = [
        {
            "text": "FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.6+ based on standard Python type hints.",
            "filename": "fastapi_overview.txt",
            "metadata": {"category": "web_framework", "technology": "python"}
        },
        {
            "text": "Machine learning is a method of data analysis that automates analytical model building. It is a branch of artificial intelligence based on the idea that systems can learn from data.",
            "filename": "ml_introduction.txt", 
            "metadata": {"category": "AI", "field": "machine_learning"}
        },
        {
            "text": "PostgreSQL is a powerful, open source object-relational database system with over 30 years of active development.",
            "filename": "postgresql_info.txt",
            "metadata": {"category": "database", "type": "relational"}
        }
    ]
    
    try:
        # Upload documents
        print("\\n1. Uploading documents...")
        doc_ids = []
        for doc in documents:
            result = client.upload_text(
                text=doc["text"],
                filename=doc["filename"],
                metadata=doc["metadata"]
            )
            doc_ids.append(result["doc_id"])
            print(f"   Uploaded: {doc['filename']} -> {result['doc_id'][:8]}...")
        
        # Finalize index
        print("\\n2. Finalizing index...")
        client.finalize_index()
        print("   Index finalized.")
        
        # Get statistics
        print("\\n3. Index statistics:")
        stats = client.get_index_stats()
        print(f"   Total documents: {stats['total_documents']}")
        print(f"   Total terms: {stats['total_terms']}")
        print(f"   Index size: {stats['index_size_mb']} MB")
        
        # Search tests
        print("\\n4. Search tests:")
        queries = [
            "Python web framework",
            "machine learning data analysis",
            "database PostgreSQL"
        ]
        
        for query in queries:
            print(f"\\n   Query: '{query}'")
            results = client.search(query, k=2)
            print(f"   Found {results['total_found']} results in {results['search_time_ms']}ms:")
            
            for i, result in enumerate(results['results'], 1):
                print(f"     {i}. {result['filename']} (score: {result['similarity_score']})")
        
        # List all documents
        print("\\n5. All documents:")
        all_docs = client.get_documents()
        for doc in all_docs:
            print(f"   - {doc['filename']} ({doc['doc_id'][:8]}...)")
        
        print("\\nDemo completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\\nMake sure the API server is running:")
        print("python text_search_api.py")

if __name__ == "__main__":
    demo_api()
