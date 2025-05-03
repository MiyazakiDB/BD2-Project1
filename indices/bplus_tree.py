import os
from bisect import bisect_left

ORDER = 4  # TODO Grado del B+ Tree (discuss this)

class BPlusTreeLeaf:
    def __init__(self):
        self.keys = []
        self.positions = []
        self.next = None

    def is_full(self):
        return len(self.keys) >= ORDER - 1

    def insert(self, key, position):
        idx = bisect_left(self.keys, key)
        if idx < len(self.keys) and self.keys[idx] == key:
            return  # TODO (Duped key, check if we should ignore or what)
        self.keys.insert(idx, key)
        self.positions.insert(idx, position)

    def delete(self, key):
        try:
            idx = self.keys.index(key)
            del self.keys[idx]
            del self.positions[idx]
            return True
        except ValueError:
            return False

class BPlusTreeInternal:
    def __init__(self):
        self.keys = []
        self.children = []

    def is_full(self):
        return len(self.keys) >= ORDER - 1

class BPlusTreeFile:
    def __init__(self, data_file="data.bin"):
        self.root = BPlusTreeLeaf()
        self.data_file = data_file
        if not os.path.exists(self.data_file):
            open(self.data_file, "wb").close()

    def _append_to_data_file(self, fields):
        packed = ",".join(map(str, fields)).encode("utf-8")
        with open(self.data_file, "ab") as f:
            pos = f.tell()
            f.write(packed + b"\n")
        return pos

    def _read_from_data_file(self, position):
        with open(self.data_file, "rb") as f:
            f.seek(position)
            return f.readline().decode("utf-8").strip()

    def insert(self, key, fields):
        position = self._append_to_data_file(fields)
        promoted = self._insert(self.root, key, position)
        if promoted:
            new_root = BPlusTreeInternal()
            new_root.keys = [promoted[0]]
            new_root.children = [self.root, promoted[1]]
            self.root = new_root

    def _insert(self, node, key, position):
        if isinstance(node, BPlusTreeLeaf):
            node.insert(key, position)
            if node.is_full():
                return self._split_leaf(node)
            return None
        else:
            idx = bisect_left(node.keys, key)
            if idx < len(node.keys) and key >= node.keys[idx]:
                idx += 1
            promoted = self._insert(node.children[idx], key, position)
            if promoted:
                promoted_key, new_node = promoted
                node.keys.insert(idx, promoted_key)
                node.children.insert(idx + 1, new_node)
                if node.is_full():
                    return self._split_internal(node)
            return None

    def _split_leaf(self, leaf):
        mid = len(leaf.keys) // 2
        new_leaf = BPlusTreeLeaf()
        new_leaf.keys = leaf.keys[mid:]
        new_leaf.positions = leaf.positions[mid:]
        leaf.keys = leaf.keys[:mid]
        leaf.positions = leaf.positions[:mid]

        new_leaf.next = leaf.next
        leaf.next = new_leaf
        return new_leaf.keys[0], new_leaf

    def _split_internal(self, node):
        mid = len(node.keys) // 2
        promoted_key = node.keys[mid]
        new_node = BPlusTreeInternal()
        new_node.keys = node.keys[mid + 1:]
        new_node.children = node.children[mid + 1:]
        node.keys = node.keys[:mid]
        node.children = node.children[:mid + 1]
        return promoted_key, new_node

    def search(self, key):
        node = self.root
        while isinstance(node, BPlusTreeInternal):
            idx = bisect_left(node.keys, key)
            if idx < len(node.keys) and key >= node.keys[idx]:
                idx += 1
            node = node.children[idx]
        idx = bisect_left(node.keys, key)
        if idx < len(node.keys) and node.keys[idx] == key:
            return self._read_from_data_file(node.positions[idx])
        return None

    def range_search(self, start, end):
        results = []
        node = self.root
        while isinstance(node, BPlusTreeInternal):
            idx = bisect_left(node.keys, start)
            node = node.children[idx]

        while node:
            for i, key in enumerate(node.keys):
                if start <= key <= end:
                    results.append(self._read_from_data_file(node.positions[i]))
                elif key > end:
                    return results
            node = node.next
        return results

    def delete(self, key):
        node = self.root
        while isinstance(node, BPlusTreeInternal):
            idx = bisect_left(node.keys, key)
            if idx < len(node.keys) and key >= node.keys[idx]:
                idx += 1
            node = node.children[idx]
        return node.delete(key)
