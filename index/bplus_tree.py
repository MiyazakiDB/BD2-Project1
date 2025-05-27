import struct
import os
import json
from bisect import bisect_left, bisect_right

DEFAULT_ORDER = 4
KEY_FORMAT = 'i'
HEADER_SIZE = 4

class BPlusTreeNode:
    def __init__(self, order, is_leaf=False, parent_pos=-1, pos=-1):
        self.order = order
        self.parent_pos = parent_pos
        self.pos = pos
        self.keys = []
        self.is_leaf = is_leaf

    def is_full(self):
        return len(self.keys) >= self.order - 1

    def is_underflow(self):
        return len(self.keys) < (self.order - 1) // 2

    def is_root(self):
        return self.parent_pos == -1

class BPlusTreeLeaf(BPlusTreeNode):
    def __init__(self, order, parent_pos=-1, pos=-1):
        super().__init__(order, is_leaf=True, parent_pos=parent_pos, pos=pos)
        self.pointers = []
        self.next_leaf_pos = -1
        self.prev_leaf_pos = -1

    def insert(self, key, position):
        idx = bisect_left(self.keys, key)
        self.keys.insert(idx, key)
        self.pointers.insert(idx, position)

    def delete_key_and_pointer(self, key):
        try:
            idx = self.keys.index(key)
            del self.keys[idx]
            del self.pointers[idx]
            return True
        except ValueError:
            return False

class BPlusTreeInternal(BPlusTreeNode):
    def __init__(self, order, parent_pos=-1, pos=-1):
        super().__init__(order, is_leaf=False, parent_pos=parent_pos, pos=pos)
        self.pointers = []

class NodeManager:
    def __init__(self, index_file_path, order, key_format='i'):
        self.index_file_path = index_file_path
        self.order = order
        self.key_format = key_format
        self.key_size = struct.calcsize(key_format)
        self.empty_key = 0 if key_format == 'i' else 0.0

        self.node_struct_format_base = f"<i i i i i {(order - 1)}{key_format} {order}i"
        self.node_size_unpadded = struct.calcsize(self.node_struct_format_base)

        self.node_size = self.node_size_unpadded
        self.node_struct_format = self.node_struct_format_base

        self.file = None
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.index_file_path):
            self.open_file('wb')
            self.write_header(-1)
            self.close_file()

    def open_file(self, mode='rb+'):
        if self.file is None or self.file.closed:
            if mode == 'rb+' and not os.path.exists(self.index_file_path):
                self._ensure_file_exists()
            self.file = open(self.index_file_path, mode)

    def close_file(self):
        if self.file and not self.file.closed:
            self.file.flush()
            os.fsync(self.file.fileno())
            self.file.close()
            self.file = None

    def read_header(self):
        self.open_file('rb')
        self.file.seek(0)
        data = self.file.read(HEADER_SIZE)
        return struct.unpack("<i", data)[0]

    def write_header(self, root_pos):
        self.open_file('rb+')
        self.file.seek(0)
        self.file.write(struct.pack("<i", root_pos))

    def _pack_node(self, node: BPlusTreeNode):
        keys_to_pack = list(node.keys)
        while len(keys_to_pack) < self.order - 1:
            keys_to_pack.append(self.empty_key)

        pointers_to_pack = []
        pointers_to_pack = list(node.pointers)

        while len(pointers_to_pack) < self.order:
            pointers_to_pack.append(-1)

        next_l = node.next_leaf_pos if node.is_leaf else -1
        prev_l = node.prev_leaf_pos if node.is_leaf else -1

        packed_data = struct.pack(
            self.node_struct_format,
            1 if node.is_leaf else 0,
            len(node.keys),
            node.parent_pos,
            next_l,
            prev_l,
            *keys_to_pack,
            *pointers_to_pack
        )
        return packed_data

    def _unpack_node(self, data: bytes, pos: int) -> BPlusTreeNode:
        unpacked = struct.unpack(self.node_struct_format, data)
        is_leaf_val, actual_size, parent_pos, next_leaf_pos, prev_leaf_pos = unpacked[:5]

        keys_from_struct = list(unpacked[5 : 5 + self.order - 1])
        pointers_from_struct = list(unpacked[5 + self.order - 1 : 5 + self.order - 1 + self.order])
        active_keys = keys_from_struct[:actual_size]

        if is_leaf_val == 1:
            node = BPlusTreeLeaf(self.order, parent_pos, pos)
            node.pointers = pointers_from_struct[:actual_size]
            node.next_leaf_pos = next_leaf_pos
            node.prev_leaf_pos = prev_leaf_pos
        else:
            node = BPlusTreeInternal(self.order, parent_pos, pos)
            node.pointers = pointers_from_struct[:actual_size + 1]

        node.keys = active_keys
        return node

    def read_node(self, pos: int) -> BPlusTreeNode | None:
        if pos == -1:
            return None
        self.open_file('rb')
        offset = HEADER_SIZE + pos * self.node_size
        self.file.seek(offset)
        data = self.file.read(self.node_size)
        if not data or len(data) < self.node_size:
            raise IOError(f"Error: No se pudo leer el nodo completo en la posicion {pos}. Se esperaban {self.node_size} bytes, se obtuvieron {len(data)}.")
        return self._unpack_node(data, pos)

    def write_node(self, node: BPlusTreeNode) -> int:
        self.open_file('rb+')
        if node.pos == -1:
            self.file.seek(0, 2)
            offset_from_start = self.file.tell()
            node.pos = (offset_from_start - HEADER_SIZE) // self.node_size
        else:
            offset_from_start = HEADER_SIZE + node.pos * self.node_size
            self.file.seek(offset_from_start)

        packed_data = self._pack_node(node)
        self.file.write(packed_data)
        return node.pos

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_file()

class BPlusTree:
    def __init__(self, data_file="data.jsonl", index_file="index.bpt", order=DEFAULT_ORDER, key_format=KEY_FORMAT):
        self.data_file_path = data_file
        self.order = order
        self.node_manager = NodeManager(index_file, order, key_format)

        if not os.path.exists(self.data_file_path):
            with open(self.data_file_path, "w", encoding="utf-8") as f:
                pass

    def _append_to_data_file(self, record_data: dict) -> int:
        record_json = json.dumps(record_data)
        with open(self.data_file_path, "a", encoding="utf-8") as f:
            pos = f.tell()
            f.write(record_json + "\n")
        return pos

    def _read_from_data_file(self, position: int) -> dict | None:
        try:
            with open(self.data_file_path, "r", encoding="utf-8") as f:
                f.seek(position)
                line = f.readline()
                if line:
                    return json.loads(line.strip())
        except Exception as e:
            print(f"Error leyendo archivo de datos en {position}: {e}")
        return None

    def _find_leaf_pos(self, key):

        with self.node_manager as nm:
            root_pos = nm.read_header()
            if root_pos == -1:
                return -1

            current_node_pos = root_pos
            while True:
                node = nm.read_node(current_node_pos)
                if node.is_leaf:
                    return current_node_pos

                idx = bisect_right(node.keys, key)
                current_node_pos = node.pointers[idx]
                if current_node_pos == -1:
                    raise Exception("Puntero a hijo vacio encontrado en nodo interno.")

    def search(self, key) -> dict | None:
        leaf_pos = self._find_leaf_pos(key)
        if leaf_pos == -1:
            return None

        with self.node_manager as nm:
            leaf = nm.read_node(leaf_pos)

            idx = bisect_left(leaf.keys, key)
            if idx < len(leaf.keys) and leaf.keys[idx] == key:
                return self._read_from_data_file(leaf.pointers[idx])
        return None

    def insert(self, key, record_data: dict):
        if not isinstance(record_data, dict):
            raise ValueError("record_data debe ser un dict")

        data_position = self._append_to_data_file(record_data)

        with self.node_manager as nm:
            root_pos = nm.read_header()
            if root_pos == -1:
                root_leaf = BPlusTreeLeaf(self.order)
                root_leaf.insert(key, data_position)
                new_root_pos = nm.write_node(root_leaf)
                nm.write_header(new_root_pos)
                return

            leaf_pos = self._find_leaf_pos(key)
            leaf = nm.read_node(leaf_pos)

            idx_check = bisect_left(leaf.keys, key)
            if idx_check < len(leaf.keys) and leaf.keys[idx_check] == key:
                print(f"Warning: La clave '{key}' ya existe. No se insertara.")
                return

            leaf.insert(key, data_position)
            if not leaf.is_full():
                nm.write_node(leaf)
                return

            nm.write_node(leaf)
            self._split_node(leaf_pos, nm)

    def _split_node(self, node_to_split_pos, nm):
        node = nm.read_node(node_to_split_pos)
        mid_idx = (self.order -1) // 2
        if node.is_leaf:
            new_sibling_leaf = BPlusTreeLeaf(self.order, parent_pos=node.parent_pos)
            new_sibling_leaf.keys = node.keys[mid_idx:]
            new_sibling_leaf.pointers = node.pointers[mid_idx:]

            node.keys = node.keys[:mid_idx]
            node.pointers = node.pointers[:mid_idx]

            new_sibling_pos = nm.write_node(new_sibling_leaf)
            new_sibling_leaf.pos = new_sibling_pos
            new_sibling_leaf.next_leaf_pos = node.next_leaf_pos
            new_sibling_leaf.prev_leaf_pos = node.pos

            if node.next_leaf_pos != -1:
                original_next_node = nm.read_node(node.next_leaf_pos)
                original_next_node.prev_leaf_pos = new_sibling_pos
                nm.write_node(original_next_node)

            node.next_leaf_pos = new_sibling_pos
            nm.write_node(node)
            nm.write_node(new_sibling_leaf)
            promoted_key = new_sibling_leaf.keys[0]
            self._insert_in_parent(node.pos, promoted_key, new_sibling_pos, nm)
        else:
            promoted_key = node.keys[mid_idx]
            new_sibling_internal = BPlusTreeInternal(self.order, parent_pos=node.parent_pos)
            new_sibling_internal.keys = node.keys[mid_idx + 1:]
            new_sibling_internal.pointers = node.pointers[mid_idx + 1:]

            node.keys = node.keys[:mid_idx]
            node.pointers = node.pointers[:mid_idx + 1]

            new_sibling_pos = nm.write_node(new_sibling_internal)
            new_sibling_internal.pos = new_sibling_pos
            for child_pos in new_sibling_internal.pointers:
                if child_pos != -1:
                    child_node = nm.read_node(child_pos)
                    child_node.parent_pos = new_sibling_pos
                    nm.write_node(child_node)

            nm.write_node(node)
            nm.write_node(new_sibling_internal)

            self._insert_in_parent(node.pos, promoted_key, new_sibling_pos, nm)

    def _insert_in_parent(self, left_child_pos, key_to_insert, right_child_pos, nm):
        left_child_node = nm.read_node(left_child_pos)
        parent_pos = left_child_node.parent_pos
        if parent_pos == -1:
            new_root = BPlusTreeInternal(self.order)
            new_root.keys = [key_to_insert]
            new_root.pointers = [left_child_pos, right_child_pos]

            new_root_pos = nm.write_node(new_root)
            nm.write_header(new_root_pos)

            left_child_node.parent_pos = new_root_pos
            nm.write_node(left_child_node)
            right_child_node = nm.read_node(right_child_pos)
            right_child_node.parent_pos = new_root_pos
            nm.write_node(right_child_node)
            return

        parent_node = nm.read_node(parent_pos)
        idx_insert = bisect_left(parent_node.keys, key_to_insert)
        parent_node.keys.insert(idx_insert, key_to_insert)
        parent_node.pointers.insert(idx_insert + 1, right_child_pos)
        if not parent_node.is_full():
            nm.write_node(parent_node)
            return

        nm.write_node(parent_node)
        self._split_node(parent_pos, nm)

    def delete(self, key):
        with self.node_manager as nm:
            leaf_pos = self._find_leaf_pos(key)
            if leaf_pos == -1:
                print(f"Warning: Clave '{key}' no encontrada para eliminar.")
                return False

            leaf = nm.read_node(leaf_pos)
            if not leaf.delete_key_and_pointer(key):
                print(f"Warning: Clave '{key}' no encontrada en la hoja {leaf_pos}.")
                return False

            if leaf.is_root() and len(leaf.keys) == 0:
                nm.write_header(-1)
                return True

            nm.write_node(leaf)
            if leaf.is_underflow() and not leaf.is_root():
                self._handle_underflow(leaf.pos, nm)

        return True

    def _handle_underflow(self, node_pos, nm):
        node = nm.read_node(node_pos)
        if node.is_root():
            if not node.is_leaf and len(node.keys) == 0 and node.pointers:
                new_root_pos = node.pointers[0]
                if new_root_pos != -1:
                    new_root_node = nm.read_node(new_root_pos)
                    new_root_node.parent_pos = -1
                    nm.write_node(new_root_node)
                nm.write_header(new_root_pos)
            return

        if not node.is_underflow():
            return

        parent_node = nm.read_node(node.parent_pos)
        try:
            child_idx_in_parent = parent_node.pointers.index(node_pos)
        except ValueError:
            raise Exception(f"Error critico: Nodo {node_pos} no encontrado como hijo de {node.parent_pos}")

        min_keys_required = (self.order - 1) // 2
        if child_idx_in_parent > 0:
            left_sibling_pos = parent_node.pointers[child_idx_in_parent - 1]
            left_sibling_node = nm.read_node(left_sibling_pos)
            if len(left_sibling_node.keys) > min_keys_required:
                self._borrow_from_left(node, left_sibling_node, parent_node, child_idx_in_parent, nm)
                return

        if child_idx_in_parent < len(parent_node.pointers) - 1:
            right_sibling_pos = parent_node.pointers[child_idx_in_parent + 1]
            right_sibling_node = nm.read_node(right_sibling_pos)
            if len(right_sibling_node.keys) > min_keys_required:
                self._borrow_from_right(node, right_sibling_node, parent_node, child_idx_in_parent, nm)
                return

        if child_idx_in_parent > 0:
            left_sibling_to_merge_pos = parent_node.pointers[child_idx_in_parent - 1]
            left_sibling_to_merge_node = nm.read_node(left_sibling_to_merge_pos)
            self._merge_nodes(left_sibling_to_merge_node, node, parent_node, child_idx_in_parent - 1, nm)
        else:
            right_sibling_to_merge_pos = parent_node.pointers[child_idx_in_parent + 1]
            right_sibling_to_merge_node = nm.read_node(right_sibling_to_merge_pos)
            self._merge_nodes(node, right_sibling_to_merge_node, parent_node, child_idx_in_parent, nm)

    def _borrow_from_left(self, node_in_underflow, left_sibling, parent, child_idx_of_node_in_underflow, nm):
        parent_key_separator_idx = child_idx_of_node_in_underflow - 1
        if node_in_underflow.is_leaf:
            borrowed_key = left_sibling.keys.pop(-1)
            borrowed_data_ptr = left_sibling.pointers.pop(-1)
            node_in_underflow.keys.insert(0, borrowed_key)
            node_in_underflow.pointers.insert(0, borrowed_data_ptr)
            parent.keys[parent_key_separator_idx] = node_in_underflow.keys[0]
        else:
            key_from_parent = parent.keys[parent_key_separator_idx]
            node_in_underflow.keys.insert(0, key_from_parent)
            parent.keys[parent_key_separator_idx] = left_sibling.keys.pop(-1)
            borrowed_child_ptr = left_sibling.pointers.pop(-1)
            node_in_underflow.pointers.insert(0, borrowed_child_ptr)
            if borrowed_child_ptr != -1:
                moved_child_node = nm.read_node(borrowed_child_ptr)
                moved_child_node.parent_pos = node_in_underflow.pos
                nm.write_node(moved_child_node)

        nm.write_node(node_in_underflow)
        nm.write_node(left_sibling)
        nm.write_node(parent)

    def _borrow_from_right(self, node_in_underflow, right_sibling, parent, child_idx_of_node_in_underflow, nm):
        parent_key_separator_idx = child_idx_of_node_in_underflow
        if node_in_underflow.is_leaf:
            borrowed_key = right_sibling.keys.pop(0)
            borrowed_data_ptr = right_sibling.pointers.pop(0)
            node_in_underflow.keys.append(borrowed_key)
            node_in_underflow.pointers.append(borrowed_data_ptr)
            parent.keys[parent_key_separator_idx] = right_sibling.keys[0]
        else:
            key_from_parent = parent.keys[parent_key_separator_idx]
            node_in_underflow.keys.append(key_from_parent)
            parent.keys[parent_key_separator_idx] = right_sibling.keys.pop(0)
            borrowed_child_ptr = right_sibling.pointers.pop(0)
            node_in_underflow.pointers.append(borrowed_child_ptr)
            if borrowed_child_ptr != -1:
                moved_child_node = nm.read_node(borrowed_child_ptr)
                moved_child_node.parent_pos = node_in_underflow.pos
                nm.write_node(moved_child_node)

        nm.write_node(node_in_underflow)
        nm.write_node(right_sibling)
        nm.write_node(parent)

    def _merge_nodes(self, left_node_of_merge, right_node_to_be_merged, parent_node, parent_key_separator_idx, nm):
        if not left_node_of_merge.is_leaf:
            key_from_parent = parent_node.keys.pop(parent_key_separator_idx)
            left_node_of_merge.keys.append(key_from_parent)

        left_node_of_merge.keys.extend(right_node_to_be_merged.keys)
        left_node_of_merge.pointers.extend(right_node_to_be_merged.pointers)

        if left_node_of_merge.is_leaf:
            left_node_of_merge.next_leaf_pos = right_node_to_be_merged.next_leaf_pos
            if right_node_to_be_merged.next_leaf_pos != -1:
                node_after_merged_right = nm.read_node(right_node_to_be_merged.next_leaf_pos)
                node_after_merged_right.prev_leaf_pos = left_node_of_merge.pos
                nm.write_node(node_after_merged_right)

        if not left_node_of_merge.is_leaf:
            num_pointers_from_right = len(right_node_to_be_merged.pointers)
            start_idx_of_moved_pointers = len(left_node_of_merge.pointers) - num_pointers_from_right
            for i in range(start_idx_of_moved_pointers, len(left_node_of_merge.pointers)):
                child_pos = left_node_of_merge.pointers[i]
                if child_pos != -1:
                    child_node = nm.read_node(child_pos)
                    child_node.parent_pos = left_node_of_merge.pos
                    nm.write_node(child_node)

        del parent_node.pointers[parent_key_separator_idx + 1]

        nm.write_node(left_node_of_merge)
        nm.write_node(parent_node)

        if parent_node.is_underflow():
            self._handle_underflow(parent_node.pos, nm)

    def range_search(self, start_key, end_key) -> list[dict]:
        results = []
        current_leaf_pos = self._find_leaf_pos(start_key)
        if current_leaf_pos == -1:
            return results

        with self.node_manager as nm:
            while current_leaf_pos != -1:
                leaf = nm.read_node(current_leaf_pos)
                for i, key_in_leaf in enumerate(leaf.keys):
                    if key_in_leaf > end_key:
                        return results
                    if key_in_leaf >= start_key:
                        record = self._read_from_data_file(leaf.pointers[i])
                        if record:
                            results.append(record)
                current_leaf_pos = leaf.next_leaf_pos
        return results

    def print_tree(self, node_pos=None, level=0):
        with self.node_manager as nm:
            if node_pos is None and level == 0:
                node_pos = nm.read_header()
                if node_pos == -1:
                    print("Arbol vacio.")
                    return
                print("--- Estructura del Arbol B+ ---")

            if node_pos == -1:
                return

            node = nm.read_node(node_pos)
            indent = "  " * level
            type_str = "Hoja" if node.is_leaf else "Interno"
            parent_str = f"(Padre:{node.parent_pos})" if node.parent_pos != -1 else "(Raiz)"

            leaf_links_str = ""
            if node.is_leaf:
                leaf_links_str = f"(Prev:{node.prev_leaf_pos}, Next:{node.next_leaf_pos})"

            print(f"{indent}[L{level} {type_str} @{node.pos} {parent_str} {leaf_links_str}] Claves: {node.keys}")
            if node.is_leaf:
                print(f"{indent}  Punteros Datos: {node.pointers}")
            else:
                print(f"{indent}  Punteros Hijos: {node.pointers}")

            if not node.is_leaf:
                for child_pos in node.pointers:
                    if child_pos != -1:
                        self.print_tree_recursive_helper(child_pos, level + 1, nm)

    def print_tree_recursive_helper(self, node_pos, level, nm):
        if node_pos == -1:
            return
        node = nm.read_node(node_pos)
        indent = "  " * level
        type_str = "Hoja" if node.is_leaf else "Interno"
        parent_str = f"(Padre:{node.parent_pos})" if node.parent_pos != -1 else "(Raiz)"

        leaf_links_str = ""
        if node.is_leaf:
            leaf_links_str = f"(Prev:{node.prev_leaf_pos}, Next:{node.next_leaf_pos})"

        print(f"{indent}[L{level} {type_str} @{node.pos} {parent_str} {leaf_links_str}] Claves: {node.keys}")
        if node.is_leaf:
            print(f"{indent}  Punteros Datos: {node.pointers}")
        else:
            print(f"{indent}  Punteros Hijos: {node.pointers}")

        if not node.is_leaf:
            for child_pos in node.pointers:
                if child_pos != -1:
                    self.print_tree_recursive_helper(child_pos, level + 1, nm)
