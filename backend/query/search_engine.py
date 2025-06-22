import math
from collections import defaultdict
from backend.utils.text_processing import preprocess_text
from index.inverted_index import InvertedIndex

class SearchEngine:
    def __init__(self, index_path):
        self.index = InvertedIndex(index_path)
        self.index.load_index()

    def search(self, query, top_k=10):
        query_tokens = preprocess_text(query)
        query_term_freq = defaultdict(int)

        # Calculate term frequencies for the query
        for token in query_tokens:
            query_term_freq[token] += 1

        # Calculate query vector norm
        query_norm = math.sqrt(sum((1 + math.log10(freq))**2 for freq in query_term_freq.values()))

        # Calculate cosine similarity for each document
        scores = defaultdict(float)
        for term, freq in query_term_freq.items():
            if term in self.index.index:
                query_tf = 1 + math.log10(freq)
                for doc_id, doc_tf in self.index.index[term]:
                    scores[doc_id] += query_tf * doc_tf

        # Normalize scores by document norms
        for doc_id in scores:
            scores[doc_id] /= (self.index.doc_norms[doc_id] * query_norm)

        # Sort and return top-K results
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
