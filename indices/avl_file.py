import os

class AVLNode:
    def __init__(self, key, position):
        self.key = key
        self.position = position
        self.left = None
        self.right = None
        self.height = 1

class AVLFile:
    def __init__(self, data_file="data.bin"):
        self.root = None
        self.data_file = data_file
        if not os.path.exists(self.data_file):
            open(self.data_file, "wb").close()

    def _height(self, node):
        return node.height if node else 0

    def _balance(self, node):
        if node:
            return self._height(node.left) - self._height(node.right)
        else:
            return 0

    def _rotate_right(self, y):
        x = y.left
        temp = x.right
        x.right = y
        y.left = temp
        y.height = max(self._height(y.left), self._height(y.right)) + 1
        x.height = max(self._height(x.left), self._height(x.right)) + 1
        return x

    def _rotate_left(self, x):
        y = x.right
        temp = y.left
        y.left = x
        x.right = temp
        x.height = max(self._height(x.left), self._height(x.right)) + 1
        y.height = max(self._height(y.left), self._height(y.right)) + 1
        return y

    def insert(self, key, fields):
        pos = self._append_to_data_file(fields)
        self.root = self._insert(self.root, key, pos)

    def _insert(self, node, key, position):
        if not node:
            return AVLNode(key, position)
        if key < node.key:
            node.left = self._insert(node.left, key, position)
        elif key > node.key:
            node.right = self._insert(node.right, key, position)
        else:
            return node  # TODO (Duped key, check if we should ignore or what)

        node.height = 1 + max(self._height(node.left), self._height(node.right))
        balance = self._balance(node)

        if balance > 1 and key < node.left.key:
            return self._rotate_right(node)
        if balance < -1 and key > node.right.key:
            return self._rotate_left(node)
        if balance > 1 and key > node.left.key:
            node.left = self._rotate_left(node.left)
            return self._rotate_right(node)
        if balance < -1 and key < node.right.key:
            node.right = self._rotate_right(node.right)
            return self._rotate_left(node)

        return node

    def _append_to_data_file(self, fields):
        packed = ",".join(map(str, fields)).encode("utf-8")
        with open(self.data_file, "ab") as f:
            pos = f.tell()
            f.write(packed + b"\n")
        return pos

    def search(self, key):
        node = self._search(self.root, key)
        if node:
            return self._read_from_data_file(node.position)
        return None

    def _search(self, node, key):
        if node is None or node.key == key:
            return node
        if key < node.key:
            return self._search(node.left, key)
        else:
            return self._search(node.right, key)

    def _read_from_data_file(self, position):
        with open(self.data_file, "rb") as f:
            f.seek(position)
            return f.readline().decode("utf-8").strip()

    def range_search(self, start, end):
        results = []
        self._range_search(self.root, start, end, results)
        return results

    def _range_search(self, node, start, end, results):
        if not node:
            return
        if start < node.key:
            self._range_search(node.left, start, end, results)
        if start <= node.key <= end:
            results.append(self._read_from_data_file(node.position))
        if end > node.key:
            self._range_search(node.right, start, end, results)

    def delete(self, key):
        self.root = self._delete(self.root, key)

    def _delete(self, node, key):
        if not node:
            return node
        if key < node.key:
            node.left = self._delete(node.left, key)
        elif key > node.key:
            node.right = self._delete(node.right, key)
        else:
            # Caso: nodo con 0 o 1 hijo
            if not node.left:
                return node.right
            elif not node.right:
                return node.left
            # Caso: dos hijos → obtener sucesor in-order
            temp = self._get_min(node.right)
            node.key = temp.key
            node.position = temp.position
            node.right = self._delete(node.right, temp.key)

        node.height = 1 + max(self._height(node.left), self._height(node.right))
        balance = self._balance(node)

        if balance > 1 and self._balance(node.left) >= 0:
            return self._rotate_right(node)
        if balance > 1 and self._balance(node.left) < 0:
            node.left = self._rotate_left(node.left)
            return self._rotate_right(node)
        if balance < -1 and self._balance(node.right) <= 0:
            return self._rotate_left(node)
        if balance < -1 and self._balance(node.right) > 0:
            node.right = self._rotate_right(node.right)
            return self._rotate_left(node)

        return node

    def _get_min(self, node):
        while node.left:
            node = node.left
        return node
