import os
import pickle
import json
import shutil

class AVLNode:
    def __init__(self, key, position):
        self.key = key
        self.position = position
        self.left = None
        self.right = None
        self.height = 1

class AVLFile:
    def __init__(self, data_file="data.bin", index_file="avl_index.idx"):
        self.data_file = data_file
        self.index_file = index_file
        self.root = None
        self._load_index()

        if not os.path.exists(self.data_file):
            with open(self.data_file, "w", encoding="utf-8") as f:
                pass

    def _save_index(self):
        if self.root is None and os.path.exists(self.index_file):
            try:
                os.remove(self.index_file)
            except OSError as e:
                print(f"Error eliminando el archivo de indice vacio '{self.index_file}': {e}")
            return
        if self.root is not None:
            with open(self.index_file, "wb") as f:
                pickle.dump(self.root, f)

    def _load_index(self):
        if os.path.exists(self.index_file) and os.path.getsize(self.index_file) > 0:
            try:
                with open(self.index_file, "rb") as f:
                    self.root = pickle.load(f)
            except (pickle.UnpicklingError, EOFError, AttributeError, ImportError) as e:
                print(f"Warning: no se cargo el index file '{self.index_file}', se creara uno nuevo. Error: {e}")
                self.root = None
        else:
            self.root = None

    def _height(self, node):
        return node.height if node else 0

    def _balance(self, node):
        return self._height(node.left) - self._height(node.right) if node else 0

    def _rotate_right(self, y):
        x = y.left
        temp = x.right
        x.right = y
        y.left = temp
        y.height = 1 + max(self._height(y.left), self._height(y.right))
        x.height = 1 + max(self._height(x.left), self._height(x.right))
        return x

    def _rotate_left(self, x):
        y = x.right
        temp = y.left
        y.left = x
        x.right = temp
        x.height = 1 + max(self._height(x.left), self._height(x.right))
        y.height = 1 + max(self._height(y.left), self._height(y.right))
        return y

    def _get_min(self, node):
        current = node
        while current.left is not None:
            current = current.left
        return current

    def insert(self, key, record_data: dict):
        if not isinstance(record_data, dict):
            raise ValueError("record_data debe ser un dict")

        if self._search_node(self.root, key):
            print(f"Warning: la clave '{key}' ya existe, no se insertara el registro duplicado")
            return

        position = self._append_to_data_file(record_data)
        self.root = self._insert_node(self.root, key, position)
        self._save_index()

    def _insert_node(self, node, key, position):
        if not node:
            return AVLNode(key, position)
        if key < node.key:
            node.left = self._insert_node(node.left, key, position)
        elif key > node.key:
            node.right = self._insert_node(node.right, key, position)
        else:
            return node

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

    def _append_to_data_file(self, record_data: dict) -> int:
        record_json = json.dumps(record_data)
        with open(self.data_file, "a", encoding="utf-8") as f:
            pos = f.tell()
            f.write(record_json + "\n")
        return pos

    def search(self, key) -> dict | None:
        node = self._search_node(self.root, key)
        if node:
            return self._read_from_data_file(node.position)
        return None

    def _search_node(self, node, key) -> AVLNode | None:
        if node is None or node.key == key:
            return node
        if key < node.key:
            return self._search_node(node.left, key)
        else:
            return self._search_node(node.right, key)

    def update(self, key, new_record_data: dict) -> bool:
        if not isinstance(new_record_data, dict):
            print("Error: new_record_data debe ser un dict")
            return False

        node_to_update = self._search_node(self.root, key)
        if not node_to_update:
            print(f"Error: la clave '{key}' no existe, no se puede actualizar")
            return False

        new_position = self._append_to_data_file(new_record_data)
        node_to_update.position = new_position
        self._save_index()
        print(f"Registro con clave '{key}' actualizado (nueva posicion: {new_position})")
        return True

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
            print(f"Error: no se pudo decodificar JSON en la posicion {position} del archivo '{self.data_file}'. Linea: '{line.strip()[:100]}...'")
        except Exception as e:
            print(f"un error inesperado ocurrio al leer el archivo de datos en pos {position}: {e}")
        return None

    def range_search(self, start_key, end_key) -> list[dict]:
        results_positions = []
        self._range_search(self.root, start_key, end_key, results_positions)
        records = []
        for pos in results_positions:
            record = self._read_from_data_file(pos)
            if record:
                records.append(record)
        return records

    def _range_search(self, node, start_key, end_key, positions_list):
        if not node:
            return
        if start_key < node.key:
            self._range_search(node.left, start_key, end_key, positions_list)
        if start_key <= node.key <= end_key:
            positions_list.append(node.position)
        if end_key > node.key:
            self._range_search(node.right, start_key, end_key, positions_list)

    def delete(self, key):
        node_exists = self._search_node(self.root, key)
        if not node_exists:
            print(f"Warning: clave '{key}' no encontrada, no se puede eliminar")
            return

        self.root = self._delete_node(self.root, key)
        print(f"Registro con clave '{key}' eliminado del indice")
        self._save_index()

    def _delete_node(self, node, key):
        if not node:
            return node

        if key < node.key:
            node.left = self._delete_node(node.left, key)
        elif key > node.key:
            node.right = self._delete_node(node.right, key)
        else:
            if not node.left:
                return node.right
            elif not node.right:
                return node.left
            temp = self._get_min(node.right)
            node.key = temp.key
            node.position = temp.position
            node.right = self._delete_node(node.right, temp.key)

        if node is None:
            return node

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

    # Utilidades

    def compact_data_file(self):
        print(f"Iniciando compactacion para '{self.data_file}' y su indice '{self.index_file}'...")
        if self.root is None:
            print("El arbol AVL esta vacio.")
            if os.path.exists(self.data_file):
                try:
                    open(self.data_file, 'w').close()
                    print(f"Archivo de datos '{self.data_file}' truncado ya que el indice esta vacio.")
                except Exception as e:
                    print(f"Error al truncar '{self.data_file}': {e}")
            if os.path.exists(self.index_file):
                try:
                    os.remove(self.index_file)
                    print(f"Archivo de indice '{self.index_file}' eliminado.")
                except Exception as e:
                    print(f"Error al eliminar '{self.index_file}': {e}")
            return

        temp_data_file = self.data_file + ".tmp"
        
        nodes_in_order = []
        def _collect_nodes_inorder(node):
            if node:
                _collect_nodes_inorder(node.left)
                nodes_in_order.append(node)
                _collect_nodes_inorder(node.right)
        
        _collect_nodes_inorder(self.root)

        if not nodes_in_order:
            print("No hay nodos en el arbol para compactar. Revisar consistencia.")
            if os.path.exists(self.data_file):
                open(self.data_file, 'w').close()
            if os.path.exists(self.index_file):
                os.remove(self.index_file)
            return

        try:
            with open(temp_data_file, "w", encoding="utf-8") as tmp_f:
                for node in nodes_in_order:
                    record = self._read_from_data_file(node.position)
                    if record:
                        new_pos = tmp_f.tell()
                        tmp_f.write(json.dumps(record) + "\n")
                        node.position = new_pos
                    else:
                        print(f"Warning: no se pudo leer el registro para la clave '{node.key}' en la posicion {node.position} durante la compactacion. Este nodo podria eliminarse o el indice podria estar desactualizado.")

            shutil.move(temp_data_file, self.data_file)
            print(f"Archivo de datos '{self.data_file}' compactado exitosamente.")

            self._save_index()
            print(f"Indice '{self.index_file}' actualizado con nuevas posiciones.")

        except Exception as e:
            print(f"Error durante la compactacion: {e}")
            if os.path.exists(temp_data_file):
                try:
                    os.remove(temp_data_file)
                except OSError as e_rm:
                    print(f"Error eliminando archivo temporal '{temp_data_file}': {e_rm}")
        finally:
            if os.path.exists(temp_data_file):
                try:
                    os.remove(temp_data_file)
                    print(f"Archivo temporal '{temp_data_file}' limpiado despues de un error o finalizacion.")
                except OSError as e_rm_fin:
                    print(f"Error eliminando archivo temporal '{temp_data_file}' en finally: {e_rm_fin}")

    def print_tree(self):
        self._print_tree_recursive(self.root, "", True)

    def _print_tree_recursive(self, node, indent, last):
        if node is not None:
            print(indent, end="")
            if last:
                print("R----", end="")
                indent += "     "
            else:
                print("L----", end="")
                indent += "|    "
            balance_factor = self._balance(node)
            print(f"{node.key} (Pos:{node.position}, H:{node.height}, B:{balance_factor})")
            self._print_tree_recursive(node.left, indent, False)
            self._print_tree_recursive(node.right, indent, True)
