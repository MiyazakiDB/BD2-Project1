import os
import hashlib

BUCKET_SIZE = 4

def hash_key(key, depth):
    return format(int(hashlib.sha1(str(key).encode()).hexdigest(), 16), 'b')[-depth:]

class Bucket:
    def __init__(self, local_depth):
        self.local_depth = local_depth
        self.entries = []

    def is_full(self):
        return len(self.entries) >= BUCKET_SIZE

    def insert(self, key, pos):
        if not any(k == key for k, _ in self.entries):
            self.entries.append((key, pos))

    def search(self, key):
        for k, pos in self.entries:
            if k == key:
                return pos
        return None

    def delete(self, key):
        for i, (k, _) in enumerate(self.entries):
            if k == key:
                del self.entries[i]
                return True
        return False

    def is_empty(self):
        return len(self.entries) == 0

class DynamicHashFile:
    def __init__(self, data_file="data.bin"):
        self.global_depth = 1
        self.data_file = data_file
        self.directory = {"0": Bucket(1), "1": Bucket(1)}
        if not os.path.exists(self.data_file):
            open(self.data_file, "wb").close()

    def _append_to_data_file(self, fields):
        packed = ",".join(map(str, fields)).encode("utf-8")
        with open(self.data_file, "ab") as f:
            pos = f.tell()
            f.write(packed + b"\n")
        return pos

    def _read_from_data_file(self, pos):
        with open(self.data_file, "rb") as f:
            f.seek(pos)
            return f.readline().decode("utf-8").strip()

    def _get_bucket(self, key):
        h = hash_key(key, self.global_depth)
        return self.directory[h], h

    def insert(self, key, fields):
        pos = self._append_to_data_file(fields)
        bucket, h = self._get_bucket(key)
        if not bucket.is_full():
            bucket.insert(key, pos)
            return

        if bucket.local_depth == self.global_depth:
            self._double_directory()

        self._split_bucket(h)
        self.insert(key, fields)

    def _double_directory(self):
        self.global_depth += 1
        new_directory = {}
        for h, bucket in self.directory.items():
            new_directory["0" + h] = bucket
            new_directory["1" + h] = bucket
        self.directory = new_directory

    def _split_bucket(self, hash_prefix):
        old_bucket = self.directory[hash_prefix]
        new_depth = old_bucket.local_depth + 1
        bucket0 = Bucket(new_depth)
        bucket1 = Bucket(new_depth)

        for k, pos in old_bucket.entries:
            new_hash = hash_key(k, new_depth)
            (bucket0 if new_hash[-1] == "0" else bucket1).entries.append((k, pos))

        for h in list(self.directory):
            if self.directory[h] is old_bucket:
                self.directory[h] = bucket1 if h[-1] == "1" else bucket0

    def search(self, key):
        bucket, _ = self._get_bucket(key)
        pos = bucket.search(key)
        return self._read_from_data_file(pos) if pos is not None else None

    def delete(self, key):
        bucket, h = self._get_bucket(key)
        deleted = bucket.delete(key)
        if deleted:
            self.try_merge_buckets(h)
        return deleted

    def try_merge_buckets(self, hash_prefix):
        bucket = self.directory[hash_prefix]
        if bucket.local_depth == 1:
            return

        sibling_hash = hash_prefix[:-1] + ("1" if hash_prefix[-1] == "0" else "0")
        sibling = self.directory.get(sibling_hash)

        if sibling and sibling is not bucket and bucket.local_depth == sibling.local_depth:
            if bucket.is_empty() and sibling.is_empty():
                new_bucket = Bucket(bucket.local_depth - 1)
                for h in list(self.directory):
                    if self.directory[h] in [bucket, sibling] and h[:new_bucket.local_depth] == hash_prefix[:new_bucket.local_depth]:
                        self.directory[h] = new_bucket

                if all(b.local_depth < self.global_depth for b in set(self.directory.values())):
                    self._shrink_directory()

    def _shrink_directory(self):
        self.global_depth -= 1
        self.directory = {
            h[-self.global_depth:]: b for h, b in self.directory.items()
            if len(h) == self.global_depth + 1
        }
