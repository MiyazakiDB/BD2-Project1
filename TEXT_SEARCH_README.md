# Text Document Search API

A powerful text document indexing and search system built with FastAPI and a custom inverted index implementation. This system allows you to upload text documents and perform similarity-based searches using TF-IDF scoring.

## Features

- **Text Document Indexing**: Upload text content or files for automatic indexing
- **K-NN Similarity Search**: Find similar documents using cosine similarity with TF-IDF weights
- **Pickle Storage**: Efficient binary storage of the inverted index
- **RESTful API**: Complete REST API with interactive documentation
- **Multi-language Support**: Supports Spanish and English text processing
- **File Upload**: Support for .txt, .md, and .csv files
- **Real-time Search**: Fast search responses with timing metrics

## Technology Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **NLTK**: Natural language processing and text preprocessing
- **TF-IDF**: Term Frequency-Inverse Document Frequency scoring
- **Inverted Index**: Custom implementation for efficient text search
- **Pickle**: Binary serialization for fast index loading/saving

## Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd BD2-Project1
```

2. **Set up Python virtual environment**:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
```

3. **Install dependencies**:
```bash
pip install fastapi uvicorn python-multipart nltk requests pydantic
```

4. **Download NLTK data**:
```bash
python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt'); nltk.download('punkt_tab')"
```

## Quick Start

### 1. Start the API Server

```bash
# Using the standalone API (recommended for testing)
python text_search_api.py

# Or using uvicorn directly
uvicorn text_search_api:app --reload --host 0.0.0.0 --port 8001
```

The API will be available at:
- **API Base**: http://localhost:8001
- **Interactive Docs**: http://localhost:8001/docs
- **OpenAPI Schema**: http://localhost:8001/openapi.json

### 2. Upload Documents

**Upload text content**:
```bash
curl -X POST "http://localhost:8001/upload-text" \\
-H "Content-Type: application/json" \\
-d '{
  "text": "FastAPI is a modern web framework for Python",
  "filename": "fastapi_intro.txt",
  "metadata": {"category": "programming"}
}'
```

**Upload text files**:
```bash
curl -X POST "http://localhost:8001/upload-file" \\
-F "file=@sample_texts/fastapi_intro.txt"
```

### 3. Search Documents

```bash
curl -X POST "http://localhost:8001/search" \\
-H "Content-Type: application/json" \\
-d '{
  "query": "Python web framework",
  "k": 5
}'
```

### 4. Finalize Index

```bash
curl -X POST "http://localhost:8001/finalize-index"
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information and endpoints |
| POST | `/upload-text` | Upload text content for indexing |
| POST | `/upload-file` | Upload text file for indexing |
| POST | `/search` | Search for similar documents |
| GET | `/documents` | Get all indexed documents |
| GET | `/documents/{doc_id}` | Get specific document by ID |
| DELETE | `/documents/{doc_id}` | Delete document from index |
| POST | `/finalize-index` | Finalize index (calculate TF-IDF) |
| GET | `/index/stats` | Get index statistics |
| POST | `/save-index` | Save current index state |

## Usage Examples

### Python Client

```python
from api_client_demo import TextSearchAPIClient

# Initialize client
client = TextSearchAPIClient("http://localhost:8001")

# Upload document
result = client.upload_text(
    text="Python is a programming language",
    filename="python_intro.txt",
    metadata={"category": "programming"}
)

# Search documents
results = client.search("Python programming", k=5)
for result in results['results']:
    print(f"{result['filename']}: {result['similarity_score']}")
```

### Complete Demo

Run the complete demonstration:

```bash
python complete_demo.py
```

This will:
1. Start the API server
2. Upload sample documents
3. Perform various searches
4. Show performance metrics
5. Demonstrate all API features

### Simple Test

Test the core functionality without the API:

```bash
python test_text_search.py
```

## File Structure

```
BD2-Project1/
├── text_search_api.py          # Standalone FastAPI application
├── complete_demo.py            # Complete demonstration script
├── api_client_demo.py          # API client example
├── test_text_search.py         # Core functionality test
├── indexes/
│   └── inverted_index.py       # Inverted index implementation
├── backend/
│   ├── text_search/
│   │   ├── text_document_service.py  # Document management service
│   │   ├── api.py              # API endpoints (for main app)
│   │   └── schemas.py          # Pydantic models
│   └── utils/
│       └── text_processing.py  # Text preprocessing utilities
├── sample_texts/               # Sample text files
└── data/                      # Index storage directory
```

## How It Works

### 1. Text Preprocessing
- Tokenization using NLTK
- Stopword removal (Spanish/English)
- Stemming using Snowball Stemmer
- Normalization (lowercase, remove punctuation)

### 2. Inverted Index
- Each document is processed into tokens
- TF (Term Frequency) is calculated using log normalization: `1 + log10(freq)`
- IDF (Inverse Document Frequency): `log10(total_docs / docs_containing_term)`
- Document vectors are normalized using Euclidean norm

### 3. Search Process
- Query is preprocessed the same way as documents
- Query vector is constructed using TF-IDF weights
- Cosine similarity is calculated between query and all documents
- Results are ranked by similarity score

### 4. Storage
- Index is stored as a pickle file for fast loading
- Text files are also saved for debugging/inspection
- Document metadata is preserved with full text

## Performance

- **Index Size**: Typically <1MB for hundreds of documents
- **Search Speed**: <10ms for most queries
- **Memory Usage**: Minimal - index loaded once into memory
- **Scalability**: Suitable for thousands of documents

## Example Search Results

```json
{
  "query": "Python programming language",
  "results": [
    {
      "doc_id": "abc123...",
      "similarity_score": 0.8542,
      "filename": "python_basics.txt",
      "text_preview": "Python is a high-level programming language...",
      "metadata": {"category": "programming"}
    }
  ],
  "total_found": 1,
  "search_time_ms": 5.23
}
```

## Configuration

### Text Processing
- Language: Spanish/English (configurable in `text_processing.py`)
- Stemming: Snowball stemmer
- Stopwords: NLTK stopwords corpus

### Index Parameters
- TF calculation: `1 + log10(frequency)`
- IDF calculation: `log10(total_docs / doc_frequency)`
- Similarity: Cosine similarity
- Storage: Pickle + text files

## Troubleshooting

### Common Issues

1. **NLTK Data Missing**:
```bash
python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt_tab')"
```

2. **Port Already in Use**:
```bash
# Use a different port
uvicorn text_search_api:app --port 8002
```

3. **Import Errors**:
Make sure you're in the correct directory and virtual environment is activated.

4. **Search Returns No Results**:
- Ensure documents are finalized: `POST /finalize-index`
- Check that documents contain relevant terms
- Try broader search queries

### Debug Mode

Enable debug logging by modifying the service initialization:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Sample Data Zip

zip with password: pirata
contents inside are for educational porpuses, non of the developers of this project are responsible for copyright infringment, if a piece of copyrighted material is found, please report it in issues and it will be removed promptly.

## License

This project is part of the BD2-Project1 academic assignment.

## Contact

For questions or issues, please refer to the project documentation or create an issue in the repository.
