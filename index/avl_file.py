import os
import struct
import json
import shutil

class AVLNode:
    KEY_FORMAT = 'i'
    NODE_FORMAT = KEY_FORMAT + 'iiii'
    NODE_SIZE = struct.calcsize(NODE_FORMAT)

    def __init__(self, key: int, data_file_pos: int, left_file_pos: int = -1, right_file_pos: int = -1, height: int = 0):
        self.key = key
        self.data_file_pos = data_file_pos
        self.left_file_pos = left_file_pos   
        self.right_file_pos = right_file_pos 
        self.height = height

    def pack(self) -> bytes:
        return struct.pack(self.NODE_FORMAT, self.key, self.data_file_pos, self.left_file_pos, self.right_file_pos, self.height)

    @classmethod
    def unpack(cls, byte_data: bytes) -> 'AVLNode':
        if len(byte_data) != cls.NODE_SIZE:
            raise ValueError(f"Longitud de byte data {len(byte_data)} no coincide con tamaño de nodo {cls.NODE_SIZE}")
        
        key, data_pos, left_pos, right_pos, height = struct.unpack(cls.NODE_FORMAT, byte_data)
        return cls(key, data_pos, left_pos, right_pos, height)

    def __repr__(self):
        return (f"AVLNode(K:{self.key}, D:{self.data_file_pos}, L:{self.left_file_pos}, R:{self.right_file_pos}, H:{self.height})")


class AVLFile_Disk:
    HEADER_FORMAT = 'i' 
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    def __init__(self, index_file_path: str):
        self.index_file_path = index_file_path
        self.NODE_SIZE = AVLNode.NODE_SIZE 
        
        if not os.path.exists(self.index_file_path) or os.path.getsize(self.index_file_path) < self.HEADER_SIZE:
            with open(self.index_file_path, 'wb') as f:
                initial_root_pos = -1 
                f.write(struct.pack(self.HEADER_FORMAT, initial_root_pos))

    def _open_file(self, mode='rb+'):
        return open(self.index_file_path, mode)

    def read_root_pos(self) -> int:
        try:
            with self._open_file('rb') as f:
                f.seek(0)
                header_data = f.read(self.HEADER_SIZE)
                if len(header_data) < self.HEADER_SIZE:
                    print(f"Warning: Encabezado de archivo de indice incompleto en {self.index_file_path}. Re inicializando raiz a -1.")
                    self.write_root_pos(-1)
                    return -1
                return struct.unpack(self.HEADER_FORMAT, header_data)[0]
        except FileNotFoundError:
            print(f"Warning: Archivo de indice {self.index_file_path} no encontrado. Creando uno nuevo con raiz -1.")
            self.write_root_pos(-1)
            return -1

    def write_root_pos(self, root_file_pos: int):
        with self._open_file('rb+') as f:
            f.seek(0)
            f.write(struct.pack(self.HEADER_FORMAT, root_file_pos))

    def read_node(self, node_file_pos: int) -> Optional[AVLNode]:
        if node_file_pos == -1:
            return None
        
        try:
            with self._open_file('rb') as f:
                offset = self.HEADER_SIZE + node_file_pos * self.NODE_SIZE
                f.seek(offset)
                node_data = f.read(self.NODE_SIZE)
                
                if not node_data or len(node_data) < self.NODE_SIZE:
                    print(f"Error: Al leer nodo en posicion {node_file_pos} de {self.index_file_path}. Datos insuficientes.")
                    return None
                return AVLNode.unpack(node_data)
        except FileNotFoundError:
            print(f"Error: Archivo de indice {self.index_file_path} no encontrado al intentar leer nodo en pos {node_file_pos}.")
            return None
        except Exception as e:
            print(f"Error inesperado leyendo nodo en pos {node_file_pos}: {e}")
            return None

    def write_node(self, node_obj: AVLNode, node_file_pos: int):
        if node_file_pos < 0:
            raise ValueError("Posicion de archivo de nodo invalida para escritura.")
        with self._open_file('rb+') as f:
            offset = self.HEADER_SIZE + node_file_pos * self.NODE_SIZE
            f.seek(offset)
            f.write(node_obj.pack())

    def append_node(self, node_obj: AVLNode) -> int:
        with self._open_file('rb+') as f:
            f.seek(0, os.SEEK_END)
            current_file_size = f.tell()
            
            if current_file_size < self.HEADER_SIZE:
                new_node_pos = 0
                offset = self.HEADER_SIZE
            else:
                num_existing_nodes = (current_file_size - self.HEADER_SIZE) // self.NODE_SIZE
                if (current_file_size - self.HEADER_SIZE) % self.NODE_SIZE != 0:
                    print(f"Warning: Tamaño de archivo de indice {self.index_file_path} no es multiplo de NODE_SIZE + HEADER_SIZE.")
                new_node_pos = num_existing_nodes
                offset = self.HEADER_SIZE + new_node_pos * self.NODE_SIZE
            
            f.seek(offset)
            f.write(node_obj.pack())
            return new_node_pos

class AVLTree_Disk:
    def __init__(self, data_file_path="data_avl.jsonl", index_file_path="avl_disk_index.idx"):
        self.data_file_path = data_file_path
        self.index_manager = AVLFile_Disk(index_file_path)

        if not os.path.exists(self.data_file_path):
            with open(self.data_file_path, "w", encoding="utf-8") as f:
                pass

    def _append_to_data_file(self, record_data: dict) -> int:
        record_json = json.dumps(record_data)
        with open(self.data_file_path, "a", encoding="utf-8") as f:
            pos = f.tell()
            f.write(record_json + "\n")
        return pos

    def _read_from_data_file(self, position: int) -> Optional[dict]:
        if position == -1:
            return None

        try:
            with open(self.data_file_path, "r", encoding="utf-8") as f:
                f.seek(position)
                line = f.readline()
                if line:
                    return json.loads(line.strip())
        except FileNotFoundError:
            print(f"Error: El archivo de datos '{self.data_file_path}' no fue encontrado")
        except json.JSONDecodeError:
            line_content = "N/A"
            try:
                with open(self.data_file_path, "r", encoding="utf-8") as f_err:
                    f_err.seek(position)
                    line_content = f_err.readline().strip()[:100]
            except:
                pass
            print(f"Error: No se pudo decodificar JSON en la posicion {position} del archivo '{self.data_file_path}'. Linea: '{line_content}...'")
        except Exception as e:
            print(f"Un error inesperado ocurrio al leer el archivo de datos en pos {position}: {e}")
        return None

    def _get_node_height(self, node_pos: int) -> int:
        if node_pos == -1:
            return -1 
        node = self.index_manager.read_node(node_pos)
        return node.height if node else -1

    def _update_node_height_and_write(self, node_pos: int):
        if node_pos == -1:
            return
        node = self.index_manager.read_node(node_pos)
        if not node:
            return

        left_h = self._get_node_height(node.left_file_pos)
        right_h = self._get_node_height(node.right_file_pos)
        new_height = 1 + max(left_h, right_h)
        
        if node.height != new_height:
            node.height = new_height
            self.index_manager.write_node(node, node_pos)

    def _get_balance_factor(self, node_pos: int) -> int:
        if node_pos == -1:
            return 0
        node = self.index_manager.read_node(node_pos)
        if not node:
            return 0 
        return self._get_node_height(node.left_file_pos) - self._get_node_height(node.right_file_pos)

    def _rotate_right(self, y_pos: int) -> int:
        y_node = self.index_manager.read_node(y_pos)
        if not y_node or y_node.left_file_pos == -1:
            return y_pos

        x_pos = y_node.left_file_pos
        x_node = self.index_manager.read_node(x_pos)
        if not x_node:
            return y_pos 

        t2_pos = x_node.right_file_pos
        x_node.right_file_pos = y_pos
        y_node.left_file_pos = t2_pos

        self._update_node_height_and_write(y_pos)
        self._update_node_height_and_write(x_pos)
        return x_pos

    def _rotate_left(self, x_pos: int) -> int:
        x_node = self.index_manager.read_node(x_pos)
        if not x_node or x_node.right_file_pos == -1:
            return x_pos

        y_pos = x_node.right_file_pos
        y_node = self.index_manager.read_node(y_pos)
        if not y_node:
            return x_pos

        t2_pos = y_node.left_file_pos
        y_node.left_file_pos = x_pos
        x_node.right_file_pos = t2_pos

        self._update_node_height_and_write(x_pos)
        self._update_node_height_and_write(y_pos)
        return y_pos

    def _insert_recursive(self, current_node_pos: int, key_to_insert: int, data_file_pos_to_insert: int) -> int:
        if current_node_pos == -1:
            new_node = AVLNode(key_to_insert, data_file_pos_to_insert, height=0)
            return self.index_manager.append_node(new_node)

        current_node = self.index_manager.read_node(current_node_pos)
        if not current_node:
            raise Exception(f"Error critico: No se pudo leer el nodo en la posicion {current_node_pos} durante la insercion.")

        if key_to_insert < current_node.key:
            current_node.left_file_pos = self._insert_recursive(current_node.left_file_pos, key_to_insert, data_file_pos_to_insert)
        elif key_to_insert > current_node.key:
            current_node.right_file_pos = self._insert_recursive(current_node.right_file_pos, key_to_insert, data_file_pos_to_insert)
        else:
            return current_node_pos 

        self._update_node_height_and_write(current_node_pos)
        balance = self._get_balance_factor(current_node_pos)
        new_subtree_root_pos = current_node_pos

        if balance > 1:
            left_child_node = self.index_manager.read_node(current_node.left_file_pos)
            if left_child_node and key_to_insert < left_child_node.key: # LL
                new_subtree_root_pos = self._rotate_right(current_node_pos)
            else: # LR
                current_node.left_file_pos = self._rotate_left(current_node.left_file_pos)
                self.index_manager.write_node(current_node, current_node_pos)
                new_subtree_root_pos = self._rotate_right(current_node_pos)
        elif balance < -1:
            right_child_node = self.index_manager.read_node(current_node.right_file_pos)
            if right_child_node and key_to_insert > right_child_node.key: # RR
                new_subtree_root_pos = self._rotate_left(current_node_pos)
            else: # RL
                current_node.right_file_pos = self._rotate_right(current_node.right_file_pos)
                self.index_manager.write_node(current_node, current_node_pos)
                new_subtree_root_pos = self._rotate_left(current_node_pos)

        if new_subtree_root_pos == current_node_pos:
            self.index_manager.write_node(current_node, current_node_pos)

        return new_subtree_root_pos

    def insert(self, key: int, record_data: dict):
        if not isinstance(record_data, dict):
            raise ValueError("record_data debe ser un dict")

        if self.search_key_pos(key) is not None:
             print(f"Warning: La clave '{key}' ya existe, no se insertara.")
             return

        data_file_pos = self._append_to_data_file(record_data)
        
        current_root_pos = self.index_manager.read_root_pos()
        new_root_pos = self._insert_recursive(current_root_pos, key, data_file_pos)
        
        if new_root_pos != current_root_pos:
            self.index_manager.write_root_pos(new_root_pos)
    
    def _search_recursive(self, current_node_pos: int, key_to_find: int) -> Optional[int]:
        if current_node_pos == -1:
            return None
        node = self.index_manager.read_node(current_node_pos)
        if not node:
            return None

        if key_to_find == node.key:
            return node.data_file_pos
        elif key_to_find < node.key:
            return self._search_recursive(node.left_file_pos, key_to_find)
        else:
            return self._search_recursive(node.right_file_pos, key_to_find)

    def search_key_pos(self, key: int) -> Optional[int]:
        current_root_pos = self.index_manager.read_root_pos()
        return self._search_recursive(current_root_pos, key)

    def search(self, key: int) -> Optional[dict]:
        data_file_pos = self.search_key_pos(key)
        return self._read_from_data_file(data_file_pos) if data_file_pos is not None else None

    def _get_min_value_node_pos_and_node(self, current_node_pos: int) -> Tuple[Optional[int], Optional[AVLNode]]:
        current_pos = current_node_pos
        node = None
        while current_pos != -1:
            node = self.index_manager.read_node(current_pos)
            if not node or node.left_file_pos == -1:
                break
            current_pos = node.left_file_pos
        return current_pos, node

    def _delete_recursive(self, current_node_pos: int, key_to_delete: int) -> int:
        if current_node_pos == -1:
            return -1 

        current_node = self.index_manager.read_node(current_node_pos)
        if not current_node:
            return -1

        if key_to_delete < current_node.key:
            current_node.left_file_pos = self._delete_recursive(current_node.left_file_pos, key_to_delete)
        elif key_to_delete > current_node.key:
            current_node.right_file_pos = self._delete_recursive(current_node.right_file_pos, key_to_delete)
        else: 
            if current_node.left_file_pos == -1:
                return current_node.right_file_pos 
            elif current_node.right_file_pos == -1:
                return current_node.left_file_pos

            temp_succ_pos, temp_succ_node = self._get_min_value_node_pos_and_node(current_node.right_file_pos)
            if not temp_succ_node:
                 raise Exception("Sucesor no encontrado en eliminacion.")

            current_node.key = temp_succ_node.key
            current_node.data_file_pos = temp_succ_node.data_file_pos
            current_node.right_file_pos = self._delete_recursive(current_node.right_file_pos, temp_succ_node.key)
        
        self._update_node_height_and_write(current_node_pos) 
        
        balance = self._get_balance_factor(current_node_pos)
        new_subtree_root_pos = current_node_pos

        if balance > 1:
            left_child_node = self.index_manager.read_node(current_node.left_file_pos)
            if left_child_node and self._get_balance_factor(current_node.left_file_pos) >= 0: # LL
                new_subtree_root_pos = self._rotate_right(current_node_pos)
            else: # LR
                current_node.left_file_pos = self._rotate_left(current_node.left_file_pos)
                self.index_manager.write_node(current_node, current_node_pos)
                new_subtree_root_pos = self._rotate_right(current_node_pos)
        elif balance < -1:
            right_child_node = self.index_manager.read_node(current_node.right_file_pos)
            if right_child_node and self._get_balance_factor(current_node.right_file_pos) <= 0: # RR
                new_subtree_root_pos = self._rotate_left(current_node_pos)
            else: # RL
                current_node.right_file_pos = self._rotate_right(current_node.right_file_pos)
                self.index_manager.write_node(current_node, current_node_pos)
                new_subtree_root_pos = self._rotate_left(current_node_pos)
        else:
            self.index_manager.write_node(current_node, current_node_pos)
            
        return new_subtree_root_pos

    def delete(self, key: int):
        current_root_pos = self.index_manager.read_root_pos()
        if self.search_key_pos(key) is None:
            print(f"Warning: Clave '{key}' no encontrada, no se puede eliminar.")
            return

        new_root_pos = self._delete_recursive(current_root_pos, key)
        
        if new_root_pos != current_root_pos:
            self.index_manager.write_root_pos(new_root_pos)
        
    def update(self, key: int, new_record_data: dict) -> bool:
        if not isinstance(new_record_data, dict):
            print("Error: new_record_data debe ser un dict")
            return False

        def _find_node_pos_recursive(current_node_idx_pos: int, key_to_find: int) -> Optional[int]:
            if current_node_idx_pos == -1:
                return None
            node = self.index_manager.read_node(current_node_idx_pos)
            if not node:
                return None

            if key_to_find == node.key:
                return current_node_idx_pos
            elif key_to_find < node.key:
                return _find_node_pos_recursive(node.left_file_pos, key_to_find)
            else:
                return _find_node_pos_recursive(node.right_file_pos, key_to_find)

        root_pos = self.index_manager.read_root_pos()
        node_to_update_idx_pos = _find_node_pos_recursive(root_pos, key)

        if node_to_update_idx_pos is None:
            print(f"Error: La clave '{key}' no existe, no se puede actualizar.")
            return False

        new_data_file_position = self._append_to_data_file(new_record_data)
        
        node_to_update_obj = self.index_manager.read_node(node_to_update_idx_pos)
        if node_to_update_obj:
            node_to_update_obj.data_file_pos = new_data_file_position
            self.index_manager.write_node(node_to_update_obj, node_to_update_idx_pos)
            return True
        else:
            print(f"Error critico: No se pudo leer el nodo en pos {node_to_update_idx_pos} para actualizar.")
            return False

    def range_search(self, start_key: int, end_key: int) -> list[dict]:
        results_data_positions = []
        current_root_pos = self.index_manager.read_root_pos()
        
        def _collect_in_range(node_pos: int, sk: int, ek: int, positions_list: list):
            if node_pos == -1:
                return
            node = self.index_manager.read_node(node_pos)
            if not node:
                return

            if sk is None or node.key > sk:
                _collect_in_range(node.left_file_pos, sk, ek, positions_list)
            
            if (sk is None or node.key >= sk) and (ek is None or node.key <= ek):
                positions_list.append(node.data_file_pos)

            if ek is None or node.key < ek:
                _collect_in_range(node.right_file_pos, sk, ek, positions_list)

        _collect_in_range(current_root_pos, start_key, end_key, results_data_positions)
        
        records = []
        for pos in results_data_positions: 
            record = self._read_from_data_file(pos)
            if record:
                records.append(record)
        return records

    def compact_data_file(self):
        print(f"Iniciando compactacion para '{self.data_file_path}' y actualizando indice '{self.index_manager.index_file_path}'...")
        current_root_pos = self.index_manager.read_root_pos()
        if current_root_pos == -1:
            print("El arbol AVL esta vacio.")
            if os.path.exists(self.data_file_path) and os.path.getsize(self.data_file_path) > 0:
                try:
                    open(self.data_file_path, 'w').close()
                except Exception as e:
                    print(f"Error al truncar '{self.data_file_path}': {e}")
            return

        temp_data_file = self.data_file_path + ".tmp_compact"
        nodes_to_update_info: List[Tuple[int, int, int]] = []

        def _collect_nodes_inorder_for_compact(node_idx_pos):
            if node_idx_pos == -1:
                return
            node = self.index_manager.read_node(node_idx_pos)
            if not node:
                return
            
            _collect_nodes_inorder_for_compact(node.left_file_pos)
            nodes_to_update_info.append( (node_idx_pos, node.key, node.data_file_pos) )
            _collect_nodes_inorder_for_compact(node.right_file_pos)
        
        _collect_nodes_inorder_for_compact(current_root_pos)

        if not nodes_to_update_info:
            print("No hay nodos en el arbol para compactar (o raiz es -1 y ya se manejo).")
            return

        try:
            new_data_positions_map: Dict[int, int] = {} 
            sorted_nodes_info = sorted(nodes_to_update_info, key=lambda x: x[2]) 

            with open(temp_data_file, "w", encoding="utf-8") as tmp_f:
                for _, _, old_data_pos in sorted_nodes_info:
                    if old_data_pos in new_data_positions_map: 
                        continue
                    record = self._read_from_data_file(old_data_pos)
                    if record:
                        new_pos_in_tmp_data_file = tmp_f.tell()
                        tmp_f.write(json.dumps(record) + "\n")
                        new_data_positions_map[old_data_pos] = new_pos_in_tmp_data_file
                    else:
                        print(f"Warning: No se pudo leer registro en pos {old_data_pos} durante compactacion.")
            
            for node_idx_file_pos, _, old_data_file_pos in nodes_to_update_info:
                if old_data_file_pos in new_data_positions_map:
                    node_to_update = self.index_manager.read_node(node_idx_file_pos)
                    if node_to_update:
                        if node_to_update.data_file_pos == old_data_file_pos:
                             node_to_update.data_file_pos = new_data_positions_map[old_data_file_pos]
                             self.index_manager.write_node(node_to_update, node_idx_file_pos)

            if os.path.exists(self.data_file_path):
                os.remove(self.data_file_path)
            shutil.move(temp_data_file, self.data_file_path)
            print(f"Archivo de datos '{self.data_file_path}' compactado exitosamente.")

        except Exception as e:
            print(f"Error durante la compactacion: {e}")
            if os.path.exists(temp_data_file):
                os.remove(temp_data_file)
        finally:
            if os.path.exists(temp_data_file): 
                try:
                    os.remove(temp_data_file)
                except OSError:
                    pass

    def print_tree(self):
        print("--- Estructura de AVL Disk Tree ---")
        root_pos = self.index_manager.read_root_pos()
        print(f"Posicion Raiz: {root_pos}")
        self._print_tree_recursive_disk(root_pos, "", True)

    def _print_tree_recursive_disk(self, node_pos, indent, last):
        if node_pos == -1:
            return
        
        node = self.index_manager.read_node(node_pos)
        if node is None:
            print(f"{indent}Error: No se pudo leer nodo en posicion {node_pos}")
            return

        print(indent, end="")
        current_indent = indent
        if last:
            print("R----", end="")
            current_indent += "     "
        else:
            print("L----", end="")
            current_indent += "|    "
        
        print(f"Pos:{node_pos} Key:{node.key} (D:{node.data_file_pos}, H:{node.height}, L:{node.left_file_pos}, R:{node.right_file_pos})")

        self._print_tree_recursive_disk(node.left_file_pos, current_indent, False)
        self._print_tree_recursive_disk(node.right_file_pos, current_indent, True)
