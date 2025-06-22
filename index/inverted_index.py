import os
import math
from collections import defaultdict
from backend.utils.text_processing import preprocess_text

class InvertedIndex:
    def __init__(self, index_path):
        self.index_path = index_path
        self.index = defaultdict(list)
        self.doc_norms = {}
        self.total_docs = 0  # Total number of documents
        self.term_doc_freq = defaultdict(int)  # Document frequency for each term

    def add_document(self, doc_id, text):
        tokens = preprocess_text(text)
        term_freq = defaultdict(int)

        # Calculate term frequencies
        for token in tokens:
            term_freq[token] += 1

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
        for term, postings in self.index.items():
            idf = math.log10(self.total_docs / self.term_doc_freq[term])
            self.index[term] = [(doc_id, tf * idf) for doc_id, tf in postings]

        self.save_index()

    def save_index(self):
        with open(os.path.join(self.index_path, 'inverted_index.txt'), 'w') as f:
            for term, postings in self.index.items():
                postings_str = ' '.join(f"{doc_id}:{tf}" for doc_id, tf in postings)
                f.write(f"{term} {postings_str}\n")

        with open(os.path.join(self.index_path, 'doc_norms.txt'), 'w') as f:
            for doc_id, norm in self.doc_norms.items():
                f.write(f"{doc_id} {norm}\n")

    def load_index(self):
        self.index = defaultdict(list)
        self.doc_norms = {}

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
