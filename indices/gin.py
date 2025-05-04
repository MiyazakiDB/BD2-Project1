import os
import pickle  # TODO would like to migrate to something secure like MessagePack
import re
from collections import defaultdict

class GINIndex:
    def __init__(self, index_file="gin_index.pkl", data_file="data.bin"):
        self.inverted_index = defaultdict(set)
        self.index_file = index_file
        self.data_file = data_file
        if os.path.exists(self.index_file):
            with open(self.index_file, "rb") as f:
                self.inverted_index = pickle.load(f)

    def _tokenize(self, text):
        return re.findall(r"\w+", text.lower())

    def index_record(self, record_id, name):
        tokens = self._tokenize(name)
        for token in tokens:
            self.inverted_index[token].add(record_id)

    def remove_record(self, record_id, name):
        tokens = self._tokenize(name)
        for token in tokens:
            self.inverted_index[token].discard(record_id)
            if not self.inverted_index[token]:
                del self.inverted_index[token]

    def search(self, query, mode="and"):
        tokens = self._tokenize(query)
        sets = [self.inverted_index.get(token, set()) for token in tokens]
        if not sets:
            return set()
        return set.intersection(*sets) if mode == "and" else set.union(*sets)

    def get_records(self, record_ids):
        results = []
        with open(self.data_file, "rb") as f:
            for line in f:
                if not line.strip():
                    continue
                record = line.decode("utf-8").strip()
                record_id = int(record.split(",")[0])
                if record_id in record_ids:
                    results.append(record)
        return results

    def index_existing_file(self):
        with open(self.data_file, "rb") as f:
            for line in f:
                if not line.strip():
                    continue
                record = line.decode("utf-8").strip()
                parts = record.split(",")
                if len(parts) < 2:
                    continue
                record_id = int(parts[0])
                name = parts[1]
                self.index_record(record_id, name)

    def save(self):
        with open(self.index_file, "wb") as f:
            pickle.dump(self.inverted_index, f)
