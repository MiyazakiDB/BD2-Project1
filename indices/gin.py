import os
import pickle  # TODO would like to migrate to something secure like MessagePack
import re
from collections import defaultdict

class GINIndex:
    def __init__(self, index_file="gin_index.pkl"):
        self.inverted_index = defaultdict(set)
        self.index_file = index_file
        if os.path.exists(self.index_file):
            with open(self.index_file, "rb") as f:
                self.inverted_index = pickle.load(f)

    def _tokenize(self, text):
        return re.findall(r"\w+", text.lower())

    def index_record(self, record_id, text_field):
        tokens = self._tokenize(text_field)
        for token in tokens:
            self.inverted_index[token].add(record_id)

    def remove_record(self, record_id, text_field):
        tokens = self._tokenize(text_field)
        for token in tokens:
            if record_id in self.inverted_index[token]:
                self.inverted_index[token].remove(record_id)
            if not self.inverted_index[token]:
                del self.inverted_index[token]

    def search(self, query_tokens, mode="and"):
        token_sets = [self.inverted_index.get(token, set()) for token in self._tokenize(query_tokens)]
        if not token_sets:
            return set()
        return set.intersection(*token_sets) if mode == "and" else set.union(*token_sets)

    def save(self):
        with open(self.index_file, "wb") as f:
            pickle.dump(self.inverted_index, f)

