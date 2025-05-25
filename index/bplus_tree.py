import os
import pickle
import json
import shutil
from bisect import bisect_left, bisect_right

DEFAULT_ORDER = 4

class BPlusTreeNode:
    def __init__(self, parent=None):
        self.parent = parent
        self.keys = []

    def is_full(self, order):
        return len(self.keys) >= order

    def is_underflow(self, order, is_root):
        if is_root:
            return not self.is_leaf() and len(self.keys) < 1
        return len(self.keys) < (order // 2)

    def is_leaf(self):
        return isinstance(self, BPlusTreeLeaf)

class BPlusTreeLeaf(BPlusTreeNode):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.positions = []
        self.next_leaf = None
        self.prev_leaf = None

    def insert(self, key, position):
        idx = bisect_left(self.keys, key)
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

class BPlusTreeInternal(BPlusTreeNode):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.children = []

class BPlusTreeFile:
    def __init__(self, data_file="bplus_data.jsonl", index_file="bplus_index.bpt", order=DEFAULT_ORDER):
        self.data_file = data_file
        self.index_file = index_file

        self.order = order
        self.root = None
        self._load_index()

        if not os.path.exists(self.data_file):
            with open(self.data_file, "w", encoding="utf-8") as f:
                pass

    def _save_index(self):
        if self.root is None:
            print("Warning: intentandp guardar un indice con root None")
            if os.path.exists(self.index_file):
                try:
                    os.remove(self.index_file)
                except OSError as e:
                    print(f"Error al eliminar el archivo de indice para root None: {e}")
            return

        data_to_pickle = (self.order, self.root)
        with open(self.index_file, "wb") as f:
            pickle.dump(data_to_pickle, f)

    def _load_index(self):
        if os.path.exists(self.index_file) and os.path.getsize(self.index_file) > 0:
            try:
                with open(self.index_file, "rb") as f:
                    persisted_order, persisted_root = pickle.load(f)

                if self.order != persisted_order:
                    print(f"Warning: el 'order' ({self.order}) al inicializar B+ Tree File difiere del 'order' ({persisted_order}) en el archivo de indice '{self.index_file}', se usara el 'order' del archivo de indice")
                    self.order = persisted_order
                self.root = persisted_root
            except Exception as e:
                print(f"Error: no se pudo cargar el archivo de indice B+ Tree '{self.index_file}'. Error: {e}.")
                self.root = BPlusTreeLeaf()
        else:
            self.root = BPlusTreeLeaf()

    def _append_to_data_file(self, record_data: dict) -> int:
        record_json = json.dumps(record_data)
        with open(self.data_file, "a", encoding="utf-8") as f:
            pos = f.tell()
            f.write(record_json + "\n")
        return pos

    def _read_from_data_file(self, position: int) -> dict | None:
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                f.seek(position)
                line = f.readline()
                if line:
                    return json.loads(line.strip())
        except FileNotFoundError:
            print(f"Error: el archivo de datos '{self.data_file}' no fue encontrado")
        except json.JSONDecodeError:
            print(f"Error: no se pudo decodificar JSON en la posicion {position} del archivo '{self.data_file}'")
        except Exception as e:
            print(f"Un error inesperado ocurrio al leer el archivo de datos: {e}")
        return None

    def _find_leaf(self, key) -> BPlusTreeLeaf:
        node = self.root
        while not node.is_leaf():
            idx = bisect_right(node.keys, key)
            node = node.children[idx]
        return node

    def search(self, key) -> dict | None:
        if self.root is None or (self.root.is_leaf() and not self.root.keys):
            return None
        leaf = self._find_leaf(key)
        idx = bisect_left(leaf.keys, key)
        if idx < len(leaf.keys) and leaf.keys[idx] == key:
            return self._read_from_data_file(leaf.positions[idx])
        return None

    def insert(self, key, record_data: dict):
        if not isinstance(record_data, dict):
            raise ValueError("record_data debe ser un dict")

        if self.root is None:
             self.root = BPlusTreeLeaf()

        leaf = self._find_leaf(key)
        idx = bisect_left(leaf.keys, key)
        if idx < len(leaf.keys) and leaf.keys[idx] == key:
            print(f"Warning: la clave '{key}' ya existe en el B+ Tree, no se insertara")
            return

        position = self._append_to_data_file(record_data)
        leaf.insert(key, position)

        if leaf.is_full(self.order):
            self._split_node(leaf)
        self._save_index()

    def _split_node(self, node):
        mid_idx = self.order // 2

        if node.is_leaf():
            new_sibling_leaf = BPlusTreeLeaf(parent=node.parent)
            new_sibling_leaf.keys = node.keys[mid_idx:]
            new_sibling_leaf.positions = node.positions[mid_idx:]

            node.keys = node.keys[:mid_idx]
            node.positions = node.positions[:mid_idx]

            new_sibling_leaf.next_leaf = node.next_leaf
            if node.next_leaf:
                node.next_leaf.prev_leaf = new_sibling_leaf
            node.next_leaf = new_sibling_leaf
            new_sibling_leaf.prev_leaf = node

            promoted_key = new_sibling_leaf.keys[0]
            self._insert_in_parent(node, promoted_key, new_sibling_leaf)
        else:
            promoted_key = node.keys[mid_idx]

            new_sibling_internal = BPlusTreeInternal(parent=node.parent)
            new_sibling_internal.keys = node.keys[mid_idx + 1:]
            new_sibling_internal.children = node.children[mid_idx + 1:]
            for child in new_sibling_internal.children:
                child.parent = new_sibling_internal

            node.keys = node.keys[:mid_idx]
            node.children = node.children[:mid_idx + 1]

            self._insert_in_parent(node, promoted_key, new_sibling_internal)

    def _insert_in_parent(self, left_child, key_to_insert, right_child):
        parent = left_child.parent
        if parent is None:
            new_root = BPlusTreeInternal()
            new_root.keys = [key_to_insert]
            new_root.children = [left_child, right_child]
            left_child.parent = new_root
            right_child.parent = new_root
            self.root = new_root
            return

        idx = bisect_left(parent.keys, key_to_insert)
        parent.keys.insert(idx, key_to_insert)
        parent.children.insert(idx + 1, right_child)

        if parent.is_full(self.order):
            self._split_node(parent)

    def update(self, key, new_record_data: dict) -> bool:
        if not isinstance(new_record_data, dict):
            print("Error: new_record_data debe ser un dict")
            return False
        if self.root is None or (self.root.is_leaf() and not self.root.keys):
            print(f"Error: la clave '{key}' no existe (arbol vacio), no se puede actualizar")
            return False

        leaf = self._find_leaf(key)
        idx = bisect_left(leaf.keys, key)

        if idx < len(leaf.keys) and leaf.keys[idx] == key:
            old_position = leaf.positions[idx]
            new_position = self._append_to_data_file(new_record_data)
            leaf.positions[idx] = new_position
            self._save_index()
            return True
        else:
            print(f"Error: la clave '{key}' no existe en el B+ Tree, no se puede actualizar")
            return False

    def delete(self, key_to_delete):
        if self.root is None or (self.root.is_leaf() and not self.root.keys):
            print(f"Warning: clave '{key_to_delete}' no encontrada (arbol vacio)")
            return False

        leaf_node = self._find_leaf(key_to_delete)
        if not leaf_node.delete_key(key_to_delete):
            print(f"Warning: clave '{key_to_delete}' no encontrada en la hoja para eliminar")
            return False

        self._handle_underflow(leaf_node)
        self._save_index()
        return True

    def _handle_underflow(self, node):
        if node == self.root:
            if not node.is_leaf() and len(node.children) == 1:
                self.root = node.children[0]
                self.root.parent = None
            return

        if not node.is_underflow(self.order, is_root=False):
            return

        parent = node.parent
        child_idx = parent.children.index(node)

        if child_idx > 0:
            left_sibling = parent.children[child_idx - 1]
            if len(left_sibling.keys) > (self.order // 2):
                self._borrow_from_left_sibling(node, left_sibling, parent, child_idx)
                return

        if child_idx < len(parent.children) - 1:
            right_sibling = parent.children[child_idx + 1]
            if len(right_sibling.keys) > (self.order // 2):
                self._borrow_from_right_sibling(node, right_sibling, parent, child_idx)
                return

        if child_idx > 0:
            left_sibling = parent.children[child_idx - 1]
            self._merge_with_sibling(left_sibling, node, parent, child_idx - 1)
        else:
            right_sibling = parent.children[child_idx + 1]
            self._merge_with_sibling(node, right_sibling, parent, child_idx)

    def _borrow_from_left_sibling(self, node, left_sibling, parent, node_idx_in_parent_children):
        parent_key_idx = node_idx_in_parent_children - 1

        if node.is_leaf():
            borrowed_key = left_sibling.keys.pop(-1)
            borrowed_pos = left_sibling.positions.pop(-1)
            node.keys.insert(0, borrowed_key)
            node.positions.insert(0, borrowed_pos)
            parent.keys[parent_key_idx] = node.keys[0]
        else:
            node.keys.insert(0, parent.keys[parent_key_idx])
            parent.keys[parent_key_idx] = left_sibling.keys.pop(-1)
            borrowed_child = left_sibling.children.pop(-1)
            borrowed_child.parent = node
            node.children.insert(0, borrowed_child)

    def _borrow_from_right_sibling(self, node, right_sibling, parent, node_idx_in_parent_children):
        parent_key_idx = node_idx_in_parent_children

        if node.is_leaf():
            borrowed_key = right_sibling.keys.pop(0)
            borrowed_pos = right_sibling.positions.pop(0)
            node.keys.append(borrowed_key)
            node.positions.append(borrowed_pos)
            parent.keys[parent_key_idx] = right_sibling.keys[0]
        else:
            node.keys.append(parent.keys[parent_key_idx])
            parent.keys[parent_key_idx] = right_sibling.keys.pop(0)
            borrowed_child = right_sibling.children.pop(0)
            borrowed_child.parent = node
            node.children.append(borrowed_child)

    def _merge_with_sibling(self, left_node_of_merge, right_node_of_merge, parent, parent_key_idx_between_nodes):
        if left_node_of_merge.is_leaf():
            left_node_of_merge.keys.extend(right_node_of_merge.keys)
            left_node_of_merge.positions.extend(right_node_of_merge.positions)
            left_node_of_merge.next_leaf = right_node_of_merge.next_leaf
            if right_node_of_merge.next_leaf:
                right_node_of_merge.next_leaf.prev_leaf = left_node_of_merge
        else:
            left_node_of_merge.keys.append(parent.keys[parent_key_idx_between_nodes])
            left_node_of_merge.keys.extend(right_node_of_merge.keys)
            left_node_of_merge.children.extend(right_node_of_merge.children)
            for child in right_node_of_merge.children:
                child.parent = left_node_of_merge

        del parent.keys[parent_key_idx_between_nodes]
        del parent.children[parent_key_idx_between_nodes + 1]

    def range_search(self, start_key, end_key) -> list[dict]:
        results = []
        if self.root is None or (self.root.is_leaf() and not self.root.keys):
            return results

        leaf = self._find_leaf(start_key)
        while leaf:
            for i, key_in_leaf in enumerate(leaf.keys):
                if key_in_leaf > end_key:
                    return results
                if key_in_leaf >= start_key:
                    record = self._read_from_data_file(leaf.positions[i])
                    if record:
                        results.append(record)
            leaf = leaf.next_leaf
        return results

    def compact_data_file(self):
        print(f"Iniciando compactacion para '{self.data_file}' y su indice B+ Tree '{self.index_file}'...")
        if self.root is None or (self.root.is_leaf() and not self.root.keys):
            print("El arbol B+ esta vacio o la raiz es una hoja vacía.")
            if os.path.exists(self.data_file) and os.path.getsize(self.data_file) > 0:
                try:
                    open(self.data_file, 'w').close()
                    print(f"Archivo de datos '{self.data_file}' truncado.")
                except Exception as e:
                    print(f"Error al truncar '{self.data_file}': {e}")
            self._save_index()
            return

        temp_data_file = self.data_file + ".tmp"
        try:
            with open(temp_data_file, "w", encoding="utf-8") as tmp_f:
                current_leaf = self.root
                while not current_leaf.is_leaf():
                    if not current_leaf.children:
                        print("Error: nodo interno sin hijos encontrado durante la busqueda de la primera hoja para compactar")
                        self._save_index()
                        return
                    current_leaf = current_leaf.children[0]

                if not current_leaf.is_leaf():
                    print("Error: no se pudo encontrar la primera hoja para la compactacion.")
                    self._save_index()
                    return

                while current_leaf:
                    for i in range(len(current_leaf.keys)):
                        key = current_leaf.keys[i]
                        old_pos = current_leaf.positions[i]
                        record = self._read_from_data_file(old_pos)
                        if record:
                            new_pos = tmp_f.tell()
                            tmp_f.write(json.dumps(record) + "\n")
                            current_leaf.positions[i] = new_pos
                        else:
                            print(f"Warning: No se pudo leer el registro para la clave '{key}' en pos {old_pos} durante la compactacion")
                    current_leaf = current_leaf.next_leaf

            shutil.move(temp_data_file, self.data_file)
            print(f"Archivo de datos '{self.data_file}' compactado exitosamente.")
            self._save_index()
            print(f"Indice B+ Tree '{self.index_file}' actualizado con nuevas posiciones.")

        except Exception as e:
            print(f"Error durante la compactacion del B+ Tree: {e}")
            if os.path.exists(temp_data_file):
                try:
                    os.remove(temp_data_file)
                except OSError as e_rm:
                    print(f"Error eliminando archivo temporal '{temp_data_file}': {e_rm}")
        finally:
            if os.path.exists(temp_data_file):
                try:
                    os.remove(temp_data_file)
                except OSError as e_rm_fin:
                    print(f"Error eliminando archivo temporal '{temp_data_file}' en finally: {e_rm_fin}")

    def print_tree(self, node=None, level=0, prefix="Root:"):
        if node is None:
            node = self.root
            if node is None:
                print(f"{prefix} (Arbol No Inicializado/Vacio)")
                return
            if node.is_leaf() and not node.keys:
                print(f"{prefix} (Arbol Vacio - Hoja Raiz Unica)")
                return

        indent = " " * (level * 4)
        parent_info = f"(Parent Keys: {node.parent.keys if node.parent else 'None'})" if level > 0 else ""

        if node.is_leaf():
            print(f"{indent}{prefix} Leaf Keys: {node.keys} {parent_info} Prev: {node.prev_leaf.keys[0] if node.prev_leaf and node.prev_leaf.keys else 'None'}, Next: {node.next_leaf.keys[0] if node.next_leaf and node.next_leaf.keys else 'None'}")
        else:
            print(f"{indent}{prefix} Internal Keys: {node.keys} {parent_info}")
            for i, child in enumerate(node.children):
                child_prefix = "->"
                self.print_tree(child, level + 1, f"Child {i} {child_prefix}")
