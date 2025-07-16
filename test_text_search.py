#!/usr/bin/env python3
"""
Test script for the Text Document Search API
This script demonstrates how to:
1. Add documents to the index
2. Search for similar documents
3. Manage the index
"""

import sys
import os
sys.path.append('/workspaces/BD2-Project1')

from backend.text_search.text_document_service import TextDocumentService

def test_text_search():
    """Test the text document search functionality"""
    
    # Initialize the service
    print("Initializing Text Document Service...")
    service = TextDocumentService(index_path="./test_index")
    
    # Sample documents to index
    documents = [
        {
            "text": "Python is a high-level programming language known for its simplicity and readability. It supports multiple programming paradigms including procedural, object-oriented, and functional programming.",
            "filename": "python_intro.txt",
            "metadata": {"category": "programming", "language": "english"}
        },
        {
            "text": "Machine learning is a subset of artificial intelligence that focuses on algorithms and statistical models. Deep learning uses neural networks with multiple layers to model complex patterns.",
            "filename": "ml_basics.txt", 
            "metadata": {"category": "AI", "language": "english"}
        },
        {
            "text": "FastAPI is a modern, fast web framework for building APIs with Python. It automatically generates interactive API documentation and supports async/await operations.",
            "filename": "fastapi_info.txt",
            "metadata": {"category": "web_framework", "language": "english"}
        },
        {
            "text": "Database systems are designed to store, organize, and retrieve large amounts of data efficiently. SQL is the standard language for relational database management.",
            "filename": "database_basics.txt",
            "metadata": {"category": "database", "language": "english"}
        },
        {
            "text": "El Quijote es una novela escrita por Miguel de Cervantes. La historia sigue las aventuras de Don Quijote de La Mancha, un hidalgo que decide convertirse en caballero andante.",
            "filename": "quijote.txt",
            "metadata": {"category": "literature", "language": "spanish"}
        }
    ]
    
    # Add documents to the index
    print("\nAdding documents to the index...")
    doc_ids = []
    for i, doc in enumerate(documents):
        result = service.add_document(
            text=doc["text"],
            filename=doc["filename"],
            metadata=doc["metadata"]
        )
        doc_ids.append(result["doc_id"])
        print(f"Added document {i+1}: {doc['filename']} -> {result['doc_id']}")
    
    # Finalize the index
    print("\nFinalizing index...")
    service.finalize_and_save_index()
    
    # Get index statistics
    stats = service.get_index_stats()
    print(f"\nIndex Statistics:")
    print(f"- Total documents: {stats['total_documents']}")
    print(f"- Total terms: {stats['total_terms']}")
    print(f"- Index size: {stats['index_size_mb']} MB")
    
    # Test searches
    test_queries = [
        "Python programming language",
        "machine learning neural networks",
        "web framework API",
        "database SQL",
        "Quijote Cervantes",
        "artificial intelligence algorithms"
    ]
    
    print("\n" + "="*50)
    print("SEARCH TESTS")
    print("="*50)
    
    for query in test_queries:
        print(f"\nSearching for: '{query}'")
        results = service.search_documents(query, k=3)
        
        if results:
            print(f"Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result['filename']} (score: {result['similarity_score']})")
                print(f"     Preview: {result['text_preview'][:100]}...")
        else:
            print("No results found.")
    
    # Test document retrieval
    print(f"\n" + "="*50)
    print("DOCUMENT RETRIEVAL TEST")
    print("="*50)
    
    if doc_ids:
        test_doc_id = doc_ids[0]
        doc = service.get_document(test_doc_id)
        if doc:
            print(f"Retrieved document {test_doc_id}:")
            print(f"- Filename: {doc['metadata']['filename']}")
            print(f"- Category: {doc['metadata']['category']}")
            print(f"- Text preview: {doc['text'][:100]}...")
    
    # List all documents
    print(f"\n" + "="*50)
    print("ALL DOCUMENTS")
    print("="*50)
    
    all_docs = service.get_all_documents()
    for doc in all_docs:
        print(f"- {doc['filename']} ({doc['doc_id'][:8]}...)")
    
    print(f"\nTest completed successfully!")
    print(f"Index saved to: {service.index_path}")

if __name__ == "__main__":
    # Download NLTK data if needed
    try:
        import nltk
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
    except Exception as e:
        print(f"Warning: Could not download NLTK data: {e}")
    
    test_text_search()
