#!/usr/bin/env python3
"""
Complete Demo Script for Text Document Search API
This script demonstrates the full workflow of the text search system:
1. Starting the API server
2. Adding documents (text and files)
3. Searching with different queries
4. Managing documents
5. Index operations
"""

import requests
import json
import time
import subprocess
import signal
import os
import sys
from typing import Optional
import threading

class TextSearchDemo:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.server_process = None
        
    def start_server(self):
        """Start the FastAPI server"""
        print("🚀 Starting Text Search API server...")
        
        # Start the server in the background
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "text_search_api:app", 
            "--host", "0.0.0.0", 
            "--port", "8001"
        ]
        
        self.server_process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            cwd="/workspaces/BD2-Project1"
        )
        
        # Wait for server to start
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{self.base_url}/", timeout=2)
                if response.status_code == 200:
                    print("✅ Server started successfully!")
                    return True
            except requests.exceptions.RequestException:
                time.sleep(1)
                print(f"⏳ Waiting for server... ({attempt + 1}/{max_attempts})")
        
        print("❌ Failed to start server")
        return False
    
    def stop_server(self):
        """Stop the FastAPI server"""
        if self.server_process:
            print("🛑 Stopping server...")
            self.server_process.terminate()
            self.server_process.wait()
    
    def upload_text(self, text: str, filename: str, metadata: Optional[dict] = None):
        """Upload text document"""
        data = {
            "text": text,
            "filename": filename,
            "metadata": metadata or {}
        }
        
        response = self.session.post(f"{self.base_url}/upload-text", json=data)
        return response.json()
    
    def upload_file(self, file_path: str):
        """Upload text file"""
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'text/plain')}
            response = self.session.post(f"{self.base_url}/upload-file", files=files)
        return response.json()
    
    def search(self, query: str, k: int = 5):
        """Search documents"""
        data = {"query": query, "k": k}
        response = self.session.post(f"{self.base_url}/search", json=data)
        return response.json()
    
    def get_documents(self):
        """Get all documents"""
        response = self.session.get(f"{self.base_url}/documents")
        return response.json()
    
    def get_document(self, doc_id: str):
        """Get specific document"""
        response = self.session.get(f"{self.base_url}/documents/{doc_id}")
        return response.json()
    
    def delete_document(self, doc_id: str):
        """Delete document"""
        response = self.session.delete(f"{self.base_url}/documents/{doc_id}")
        return response.json()
    
    def finalize_index(self):
        """Finalize index"""
        response = self.session.post(f"{self.base_url}/finalize-index")
        return response.json()
    
    def get_index_stats(self):
        """Get index statistics"""
        response = self.session.get(f"{self.base_url}/index/stats")
        return response.json()
    
    def print_separator(self, title: str):
        """Print a nice separator"""
        print(f"\n{'='*60}")
        print(f" {title}")
        print(f"{'='*60}")
    
    def print_search_results(self, results: dict):
        """Pretty print search results"""
        print(f"🔍 Query: '{results['query']}'")
        print(f"⏱️  Search time: {results['search_time_ms']}ms")
        print(f"📊 Found {results['total_found']} results:")
        
        for i, result in enumerate(results['results'], 1):
            print(f"\n  {i}. 📄 {result['filename']}")
            print(f"     💯 Similarity: {result['similarity_score']:.4f}")
            print(f"     📝 Preview: {result['text_preview'][:100]}...")
    
    def run_demo(self):
        """Run the complete demo"""
        try:
            # Start server
            if not self.start_server():
                return
            
            self.print_separator("TEXT DOCUMENT SEARCH API DEMO")
            
            # Sample documents to add
            documents = [
                {
                    "text": "Python is a high-level programming language known for its simplicity and readability. It supports multiple programming paradigms including object-oriented, procedural, and functional programming.",
                    "filename": "python_basics.txt",
                    "metadata": {"category": "programming", "language": "python"}
                },
                {
                    "text": "Machine learning is a subset of artificial intelligence that focuses on algorithms and statistical models. Neural networks and deep learning have revolutionized the field.",
                    "filename": "ml_overview.txt",
                    "metadata": {"category": "AI", "field": "machine_learning"}
                },
                {
                    "text": "FastAPI is a modern, fast web framework for building APIs with Python. It provides automatic validation, serialization, and interactive documentation using OpenAPI.",
                    "filename": "fastapi_guide.txt",
                    "metadata": {"category": "web_framework", "technology": "python"}
                },
                {
                    "text": "Database systems are designed to store, organize, and retrieve large amounts of data efficiently. SQL is the standard language for relational databases like PostgreSQL and MySQL.",
                    "filename": "database_intro.txt",
                    "metadata": {"category": "database", "type": "relational"}
                },
                {
                    "text": "Natural language processing (NLP) is a branch of AI that helps computers understand and process human language. It involves tasks like text classification, sentiment analysis, and language translation.",
                    "filename": "nlp_basics.txt",
                    "metadata": {"category": "AI", "field": "nlp"}
                }
            ]
            
            # Upload documents
            self.print_separator("📤 UPLOADING DOCUMENTS")
            doc_ids = []
            
            for doc in documents:
                result = self.upload_text(doc["text"], doc["filename"], doc["metadata"])
                doc_ids.append(result["doc_id"])
                print(f"✅ Uploaded: {doc['filename']} -> {result['doc_id'][:8]}...")
            
            # Upload files if they exist
            sample_files = [
                "/workspaces/BD2-Project1/sample_texts/fastapi_intro.txt",
                "/workspaces/BD2-Project1/sample_texts/machine_learning.txt"
            ]
            
            for file_path in sample_files:
                if os.path.exists(file_path):
                    result = self.upload_file(file_path)
                    doc_ids.append(result["doc_id"])
                    print(f"✅ Uploaded file: {result['filename']} -> {result['doc_id'][:8]}...")
            
            # Finalize index
            self.print_separator("🔧 FINALIZING INDEX")
            finalize_result = self.finalize_index()
            print(f"✅ {finalize_result['message']}")
            
            # Show index statistics
            stats = self.get_index_stats()
            print(f"\n📊 Index Statistics:")
            print(f"   📚 Total documents: {stats['total_documents']}")
            print(f"   🔤 Total terms: {stats['total_terms']}")
            print(f"   💾 Index size: {stats['index_size_mb']} MB")
            
            # Test searches
            self.print_separator("🔍 SEARCH DEMONSTRATIONS")
            
            search_queries = [
                "Python programming language",
                "machine learning artificial intelligence",
                "web framework FastAPI",
                "database SQL PostgreSQL",
                "natural language processing",
                "neural networks deep learning",
                "API documentation OpenAPI"
            ]
            
            for query in search_queries:
                print(f"\n{'-'*40}")
                results = self.search(query, k=3)
                self.print_search_results(results)
                time.sleep(1)  # Small delay for readability
            
            # Document management demo
            self.print_separator("📋 DOCUMENT MANAGEMENT")
            
            # List all documents
            all_docs = self.get_documents()
            print(f"📚 All indexed documents ({len(all_docs)} total):")
            for doc in all_docs:
                print(f"   📄 {doc['filename']} ({doc['doc_id'][:8]}...)")
            
            # Get specific document
            if doc_ids:
                print(f"\n📖 Retrieving specific document:")
                specific_doc = self.get_document(doc_ids[0])
                print(f"   ID: {doc_ids[0][:8]}...")
                print(f"   Filename: {specific_doc['metadata']['filename']}")
                print(f"   Content preview: {specific_doc['text'][:100]}...")
            
            # Semantic search examples
            self.print_separator("🧠 SEMANTIC SEARCH EXAMPLES")
            
            semantic_queries = [
                "How to build web applications?",
                "What are AI algorithms?",
                "Programming with Python",
                "Data storage and retrieval"
            ]
            
            for query in semantic_queries:
                print(f"\n{'-'*40}")
                results = self.search(query, k=2)
                self.print_search_results(results)
                time.sleep(1)
            
            # Performance test
            self.print_separator("⚡ PERFORMANCE TEST")
            
            performance_queries = [
                "machine learning",
                "Python programming",
                "web framework",
                "database systems",
                "artificial intelligence"
            ]
            
            total_time = 0
            for query in performance_queries:
                start_time = time.time()
                results = self.search(query, k=5)
                end_time = time.time()
                
                search_time = (end_time - start_time) * 1000
                total_time += search_time
                
                print(f"🔍 '{query}' -> {results['total_found']} results in {search_time:.2f}ms")
            
            avg_time = total_time / len(performance_queries)
            print(f"\n📊 Average search time: {avg_time:.2f}ms")
            
            # Final stats
            final_stats = self.get_index_stats()
            self.print_separator("📈 FINAL STATISTICS")
            print(f"✅ Demo completed successfully!")
            print(f"📚 Documents indexed: {final_stats['total_documents']}")
            print(f"🔤 Terms in vocabulary: {final_stats['total_terms']}")
            print(f"💾 Index size: {final_stats['index_size_mb']} MB")
            print(f"🌐 API running at: {self.base_url}")
            print(f"📖 Interactive docs: {self.base_url}/docs")
            
            # Keep server running
            print(f"\n🔄 Server will continue running...")
            print(f"   Visit {self.base_url}/docs for interactive API documentation")
            print(f"   Press Ctrl+C to stop the server")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print(f"\n👋 Shutting down...")
        
        except Exception as e:
            print(f"❌ Error during demo: {e}")
        
        finally:
            self.stop_server()

def main():
    """Main function"""
    print("🎯 Text Document Search API - Complete Demo")
    print("=" * 50)
    
    # Change to the correct directory
    os.chdir("/workspaces/BD2-Project1")
    
    # Check if virtual environment is activated
    python_path = sys.executable
    if ".venv" not in python_path:
        print("⚠️  Warning: Virtual environment not detected")
        print(f"Current Python: {python_path}")
        
        # Try to use the virtual environment python
        venv_python = "/workspaces/BD2-Project1/.venv/bin/python"
        if os.path.exists(venv_python):
            print(f"🔄 Switching to virtual environment...")
            os.execv(venv_python, [venv_python] + sys.argv)
    
    # Run the demo
    demo = TextSearchDemo()
    demo.run_demo()

if __name__ == "__main__":
    main()
