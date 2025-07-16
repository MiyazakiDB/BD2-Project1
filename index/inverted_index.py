import os
import sys
import math
import pickle
from collections import defaultdict, Counter

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import re

def preprocess_text(text):
    # Fallback simple de tokenización
    text = text.lower()
    tokens = re.findall(r"\w+", text)
    return [t for t in tokens if len(t) > 2]

class InvertedIndex:
    def __init__(self, index_path):
        self.index_path = index_path
        self.index = defaultdict(list)
        self.doc_norms = {}
        self.total_docs = 0  # Total number of documents
        self.term_doc_freq = defaultdict(int)  # Document frequency for each term
        self.documents = {}  # Store document metadata
        self.is_finalized = False  # Track if index has been finalized

    def add_document(self, doc_id, text, metadata=None):
        tokens = preprocess_text(text)
        term_freq = defaultdict(int)

        # Calculate term frequencies
        for token in tokens:
            term_freq[token] += 1

        # Store document metadata
        self.documents[doc_id] = {
            'text': text,
            'metadata': metadata or {},
            'token_count': len(tokens)
        }

        # Update document frequency for each term
        for term in term_freq.keys():
            self.term_doc_freq[term] += 1

        # Add terms to the index and calculate TF weights
        for term, freq in term_freq.items():
            tf = 1 + math.log10(freq)
            self.index[term].append((doc_id, tf))

        # Calculate and store the document norm
        norm = math.sqrt(sum((1 + math.log10(freq))**2 for freq in term_freq.values()))
        self.doc_norms[doc_id] = norm

        self.total_docs += 1

    def finalize_index(self):
        # Only finalize if not already finalized and if we have documents
        if self.is_finalized:
            return {"status": "already_finalized", "message": "Index is already finalized"}
            
        if self.total_docs == 0:
            return {"status": "no_documents", "message": "No documents to finalize"}
            
        try:
            # Convert TF weights to TF-IDF weights
            for term, postings in self.index.items():
                if self.total_docs <= 2:
                    # For very small collections, IDF doesn't work well, so use minimum IDF
                    idf = 1.0  # Minimum IDF to avoid zero weights
                else:
                    # Standard IDF calculation with smoothing
                    idf = math.log10((self.total_docs + 1) / (self.term_doc_freq[term] + 1))
                    # Ensure minimum IDF to avoid zero weights
                    idf = max(idf, 0.1)
                    
                self.index[term] = [(doc_id, tf * idf) for doc_id, tf in postings]

            # Recalculate document norms with TF-IDF weights
            self._recalculate_doc_norms()
            
            self.is_finalized = True
            self.save_index()
            
            return {"status": "success", "message": "Index finalized successfully"}
            
        except Exception as e:
            # If finalization fails, restore the original state
            self.is_finalized = False
            return {"status": "error", "message": f"Finalization failed: {str(e)}"}
    
    def _recalculate_doc_norms(self):
        """Recalculate document norms using TF-IDF weights"""
        # Reset doc norms
        self.doc_norms = {}
        
        # For each document, calculate norm using TF-IDF weights
        for doc_id in self.documents:
            norm_squared = 0
            for term, postings in self.index.items():
                for posting_doc_id, weight in postings:
                    if posting_doc_id == doc_id:
                        norm_squared += weight ** 2
                        break
                        
            self.doc_norms[doc_id] = math.sqrt(norm_squared)

    def save_index(self):
        # Save as pickle for binary storage
        index_data = {
            'index': dict(self.index),
            'doc_norms': self.doc_norms,
            'total_docs': self.total_docs,
            'term_doc_freq': dict(self.term_doc_freq),
            'documents': self.documents,
            'is_finalized': self.is_finalized
        }
        
        pickle_path = os.path.join(self.index_path, 'inverted_index.pkl')
        with open(pickle_path, 'wb') as f:
            pickle.dump(index_data, f)
        
        # Also save as text for debugging/inspection
        with open(os.path.join(self.index_path, 'inverted_index.txt'), 'w') as f:
            for term, postings in self.index.items():
                postings_str = ' '.join(f"{doc_id}:{tf}" for doc_id, tf in postings)
                f.write(f"{term} {postings_str}\n")

        with open(os.path.join(self.index_path, 'doc_norms.txt'), 'w') as f:
            for doc_id, norm in self.doc_norms.items():
                f.write(f"{doc_id} {norm}\n")

    def load_index(self):
        pickle_path = os.path.join(self.index_path, 'inverted_index.pkl')
        
        if os.path.exists(pickle_path):
            # Load from pickle
            with open(pickle_path, 'rb') as f:
                index_data = pickle.load(f)
            
            self.index = defaultdict(list, index_data['index'])
            self.doc_norms = index_data['doc_norms']
            self.total_docs = index_data['total_docs']
            self.term_doc_freq = defaultdict(int, index_data['term_doc_freq'])
            self.documents = index_data.get('documents', {})
            self.is_finalized = index_data.get('is_finalized', False)
        else:
            # Fallback to text files
            self.index = defaultdict(list)
            self.doc_norms = {}
            self.documents = {}
            self.is_finalized = False

            try:
                with open(os.path.join(self.index_path, 'inverted_index.txt'), 'r') as f:
                    for line in f:
                        parts = line.strip().split()
                        term = parts[0]
                        postings = [tuple(map(float, p.split(':'))) for p in parts[1:]]
                        self.index[term] = postings

                with open(os.path.join(self.index_path, 'doc_norms.txt'), 'r') as f:
                    for line in f:
                        doc_id, norm = line.strip().split()
                        self.doc_norms[int(doc_id)] = float(norm)
            except FileNotFoundError:
                pass  # Index doesn't exist yet
    
    def search_knn(self, query_text, k=10):
        """
        Search for k nearest neighbors using cosine similarity
        """
        if not self.index:
            return []
        
        # Preprocess query
        query_tokens = preprocess_text(query_text)
        query_term_freq = Counter(query_tokens)
        
        # Calculate query vector
        query_vector = {}
        for term, freq in query_term_freq.items():
            if term in self.index:
                tf = 1 + math.log10(freq)
                if self.is_finalized:
                    # Index already contains TF-IDF, so we need TF-IDF for query too
                    if self.total_docs <= 2:
                        # For very small collections, use minimum IDF
                        idf = 1.0
                    else:
                        # Use the same smoothing as in finalize_index
                        idf = math.log10((self.total_docs + 1) / (self.term_doc_freq[term] + 1))
                        idf = max(idf, 0.1)
                    query_vector[term] = tf * idf
                else:
                    # Index contains only TF, so use only TF for query
                    query_vector[term] = tf
        
        # Calculate query norm
        query_norm = math.sqrt(sum(weight**2 for weight in query_vector.values()))
        
        if query_norm == 0:
            return []
        
        # Calculate cosine similarity with all documents
        scores = defaultdict(float)
        
        for term, query_weight in query_vector.items():
            for doc_id, doc_weight in self.index[term]:
                scores[doc_id] += query_weight * doc_weight
        
        # Normalize by document norms
        for doc_id in scores:
            if doc_id in self.doc_norms and self.doc_norms[doc_id] > 0:
                scores[doc_id] = scores[doc_id] / (query_norm * self.doc_norms[doc_id])
        
        # Sort by similarity and return top k
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for doc_id, similarity in sorted_docs[:k]:
            result = {
                'doc_id': doc_id,
                'similarity': similarity,
                'document': self.documents.get(doc_id, {})
            }
            results.append(result)
        
        return results
    
    def get_document(self, doc_id):
        """Get document by ID"""
        return self.documents.get(doc_id)
    
    def get_all_documents(self):
        """Get all documents"""
        return self.documents
    
    def delete_document(self, doc_id):
        """Delete a document from the index"""
        if doc_id not in self.documents:
            return False
        
        # Remove from documents
        del self.documents[doc_id]
        
        # Remove from index
        terms_to_remove = []
        for term, postings in self.index.items():
            self.index[term] = [(did, tf) for did, tf in postings if did != doc_id]
            if not self.index[term]:
                terms_to_remove.append(term)
        
        # Remove empty terms
        for term in terms_to_remove:
            del self.index[term]
            if term in self.term_doc_freq:
                del self.term_doc_freq[term]
        
        # Remove from doc_norms
        if doc_id in self.doc_norms:
            del self.doc_norms[doc_id]
        
        self.total_docs -= 1
        return True
