import os
import hashlib
import pickle
import json
import shutil

DEFAULT_BUCKET_SIZE = 4

def hash_key_to_binary_str(key_input, total_hash_length=160):
    key_str = str(key_input)
    sha1_hash = hashlib.sha1(key_str.encode('utf-8')).hexdigest()
    binary_representation = bin(int(sha1_hash, 16))[2:]
    return binary_representation.zfill(total_hash_length)

class Bucket:
    def __init__(self, local_depth: int, size: int = DEFAULT_BUCKET_SIZE):
        self.local_depth = local_depth
        self.entries = []
        self.bucket_size = size

    def is_full(self):
        return len(self.entries) >= self.bucket_size

    def insert(self, key, pos) -> bool:
        if not any(k == key for k, _ in self.entries):
            self.entries.append((key, pos))
            return True
        return False

    def search(self, key):
        for k, pos_val in self.entries:
            if k == key:
                return pos_val
        return None

    def delete(self, key) -> bool:
        for i, (k, _) in enumerate(self.entries):
            if k == key:
                del self.entries[i]
                return True
        return False

    def update_position(self, key, new_pos) -> bool:
        for i, (k, _) in enumerate(self.entries):
            if k == key:
                self.entries[i] = (k, new_pos)
                return True
        return False

    def is_empty(self):
        return len(self.entries) == 0

class DynamicHashFile:
    def __init__(self, data_file="ext_hash_data.jsonl", index_file="ext_hash.idx", bucket_size=DEFAULT_BUCKET_SIZE):
        self.data_file = data_file
        self.index_file = index_file
        self.bucket_size = bucket_size
        self.global_depth = 1
        self.directory = {}
        self._load_index()

        if not os.path.exists(self.data_file):
            with open(self.data_file, "w", encoding="utf-8") as f:
                pass

    def _get_hash_prefix(self, key_or_hash_str, depth):
        if len(key_or_hash_str) == depth:
            return key_or_hash_str
        if len(key_or_hash_str) > depth and key_or_hash_str.count('0') + key_or_hash_str.count('1') == len(key_or_hash_str):
            return key_or_hash_str[:depth]

        full_hash = hash_key_to_binary_str(key_or_hash_str)
        return full_hash[:depth]

    def _save_index(self):
        try:
            with open(self.index_file, "wb") as f:
                pickle.dump((self.global_depth, self.directory, self.bucket_size), f)
        except Exception as e:
            print(f"Error al guardar el indice de hash extensible '{self.index_file}': {e}")

    def _load_index(self):
        if os.path.exists(self.index_file) and os.path.getsize(self.index_file) > 0:
            try:
                with open(self.index_file, "rb") as f:
                    persisted_global_depth, persisted_directory, persisted_bucket_size = pickle.load(f)
                self.global_depth = persisted_global_depth
                self.directory = persisted_directory
                if self.bucket_size != persisted_bucket_size:
                    print(f"Warning: el 'bucket_size' ({self.bucket_size}) difiere del guardado ({persisted_bucket_size}), se usara el valor persistido: {persisted_bucket_size}")
                    self.bucket_size = persisted_bucket_size
                for bucket_ptr in self.directory.values():
                    bucket_ptr.bucket_size = self.bucket_size
                return
            except Exception as e:
                print(f"Error al cargar el indice de hash extensible '{self.index_file}': {e}, se creara uno nuevo")

        self.global_depth = 1
        b0 = Bucket(local_depth=1, size=self.bucket_size)
        b1 = Bucket(local_depth=1, size=self.bucket_size)
        self.directory = {"0": b0, "1": b1}

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
        except Exception as e:
            print(f"Error leyendo desde '{self.data_file}' en posicion {position}: {e}")
            return None

    def _get_bucket_from_key(self, key) -> Bucket:
        dir_hash_prefix = self._get_hash_prefix(key, self.global_depth)
        return self.directory[dir_hash_prefix]

    def insert(self, key, record_data: dict):
        if not isinstance(record_data, dict):
            raise ValueError("record_data debe ser un dict")

        target_bucket_init = self._get_bucket_from_key(key)
        if target_bucket_init.search(key) is not None:
            print(f"Warning: la clave '{key}' ya existe, no se insertara")
            return

        position = self._append_to_data_file(record_data)

        key_to_insert = key
        pos_to_insert = position

        while True:
            bucket_for_key = self._get_bucket_from_key(key_to_insert)

            if not bucket_for_key.is_full():
                bucket_for_key.insert(key_to_insert, pos_to_insert)
                self._save_index()
                return

            if bucket_for_key.local_depth == self.global_depth:
                self._double_directory()

            representative_dir_prefix = self._get_hash_prefix(key_to_insert, self.global_depth)
            self._split_bucket(representative_dir_prefix, bucket_for_key)

    def _double_directory(self):
        new_directory = {}
        for dir_hash_prefix, bucket_ptr in self.directory.items():
            new_directory["0" + dir_hash_prefix] = bucket_ptr
            new_directory["1" + dir_hash_prefix] = bucket_ptr
        self.global_depth += 1
        self.directory = new_directory

    def _split_bucket(self, representative_dir_hash_prefix: str, bucket_to_split: Bucket):
        old_local_depth = bucket_to_split.local_depth
        new_local_depth = old_local_depth + 1

        b0 = Bucket(new_local_depth, size=self.bucket_size)
        b1 = Bucket(new_local_depth, size=self.bucket_size)

        original_entries = list(bucket_to_split.entries)

        for k, p in original_entries:
            key_hash_at_new_depth = self._get_hash_prefix(k, new_local_depth)
            if key_hash_at_new_depth[old_local_depth] == '0':
                b0.insert(k,p)
            else:
                b1.insert(k,p)

        prefix_base = self._get_hash_prefix(representative_dir_hash_prefix, old_local_depth)

        for dir_key_prefix in list(self.directory.keys()):
            if self.directory[dir_key_prefix] == bucket_to_split:
                if dir_key_prefix[old_local_depth] == '0':
                    self.directory[dir_key_prefix] = b0
                else:
                    self.directory[dir_key_prefix] = b1

    def search(self, key) -> dict | None:
        if not self.directory:
            return None
        bucket = self._get_bucket_from_key(key)
        pos = bucket.search(key)
        return self._read_from_data_file(pos) if pos is not None else None

    def update(self, key, new_record_data: dict) -> bool:
        if not isinstance(new_record_data, dict):
            print("Error: new_record_data debe ser un dict")
            return False
        if not self.directory:
            print(f"Error: clave '{key}' no encontrada (hash vacio), no se puede actualizar")
            return False

        bucket = self._get_bucket_from_key(key)
        if bucket.search(key) is None:
            print(f"Error: clave '{key}' no existe, no se puede actualizar")
            return False

        new_pos = self._append_to_data_file(new_record_data)
        updated_in_bucket = bucket.update_position(key, new_pos)

        if updated_in_bucket:
            self._save_index()
            return True
        return False

    def delete(self, key) -> bool:
        if not self.directory:
            return False

        bucket_key_deleted_from = self._get_bucket_from_key(key)
        dir_hash_prefix_for_bucket = self._get_hash_prefix(key, self.global_depth)

        deleted_from_bucket = bucket_key_deleted_from.delete(key)

        if deleted_from_bucket:
            self._attempt_merge_and_shrink(dir_hash_prefix_for_bucket, bucket_key_deleted_from)
            self._save_index()
            return True
        return False

    def _attempt_merge_and_shrink(self, dir_prefix_of_modified_bucket: str, modified_bucket: Bucket):
        while True:
            if self.global_depth == 0:
                break
            if modified_bucket.local_depth <= 0 :
                break
            if modified_bucket.local_depth > self.global_depth:
                break

            prefix_at_local_depth = self._get_hash_prefix(dir_prefix_of_modified_bucket, modified_bucket.local_depth)

            if not prefix_at_local_depth:
                break

            buddy_prefix_at_local_depth = prefix_at_local_depth[:-1] + ('1' if prefix_at_local_depth[-1] == '0' else '0')
            buddy_bucket = None

            found_buddy_dir_key = None
            for d_key in self.directory:
                if self._get_hash_prefix(d_key, modified_bucket.local_depth) == buddy_prefix_at_local_depth:
                    buddy_bucket = self.directory[d_key]
                    found_buddy_dir_key = d_key
                    break

            if buddy_bucket is None or buddy_bucket == modified_bucket:
                break

            can_merge = (
                modified_bucket.local_depth == buddy_bucket.local_depth and
                (len(modified_bucket.entries) + len(buddy_bucket.entries) <= self.bucket_size)
            )
            if not can_merge:
                break

            if prefix_at_local_depth[-1] == '1':
                modified_bucket, buddy_bucket = buddy_bucket, modified_bucket
                dir_prefix_of_modified_bucket = found_buddy_dir_key if found_buddy_dir_key else self._get_hash_prefix(prefix_at_local_depth[:-1] + '0', self.global_depth)

            modified_bucket.entries.extend(buddy_bucket.entries)
            modified_bucket.local_depth -= 1

            merged_bucket_prefix_short = self._get_hash_prefix(dir_prefix_of_modified_bucket, modified_bucket.local_depth)

            for dir_key in list(self.directory.keys()):
                if self._get_hash_prefix(dir_key, modified_bucket.local_depth) == merged_bucket_prefix_short:
                    self.directory[dir_key] = modified_bucket

            shrunk_this_pass = False
            while self.global_depth > 1:
                can_shrink_dir = True
                for b_ptr in set(self.directory.values()):
                    if b_ptr.local_depth >= self.global_depth:
                        can_shrink_dir = False
                        break

                if can_shrink_dir:
                    self.global_depth -= 1
                    new_dir = {}

                    for old_dir_key, bucket_ptr_val in self.directory.items():
                        new_dir_key = old_dir_key[:self.global_depth]
                        new_dir[new_dir_key] = bucket_ptr_val
                    self.directory = new_dir
                    shrunk_this_pass = True
                else:
                    break

            if not shrunk_this_pass and not can_merge:
                pass
            if not can_merge and not shrunk_this_pass:
                break

    def compact_data_file(self):
        print(f"Iniciando compactacion para '{self.data_file}' y su indice hashing extensible '{self.index_file}'...")
        if not self.directory:
            print("El directorio de hash esta vacio.")
            if os.path.exists(self.data_file) and os.path.getsize(self.data_file) > 0:
                try:
                    open(self.data_file, 'w').close()
                except Exception as e:
                    print(f"Error al truncar '{self.data_file}': {e}")
            self._save_index()
            return

        temp_data_file = self.data_file + ".tmp"
        seen_buckets_compact = set() 

        try:
            with open(temp_data_file, "w", encoding="utf-8") as tmp_f:
                for bucket_obj in self.directory.values():
                    if id(bucket_obj) in seen_buckets_compact:
                        continue
                    seen_buckets_compact.add(id(bucket_obj))

                    entries_snapshot = list(bucket_obj.entries)
                    for key_in_bucket, old_pos in entries_snapshot:
                        record = self._read_from_data_file(old_pos)
                        if record:
                            new_pos = tmp_f.tell()
                            tmp_f.write(json.dumps(record) + "\n")
                            bucket_obj.update_position(key_in_bucket, new_pos)
                        else:
                            print(f"Warning: no se pudo leer el registro para la clave '{key_in_bucket}' en pos {old_pos} durante la compactacion")

            shutil.move(temp_data_file, self.data_file)
            print(f"Archivo de datos '{self.data_file}' compactado exitosamente.")
            self._save_index()
            print(f"Indice hashing extensible '{self.index_file}' actualizado (posiciones en buckets).")

        except Exception as e:
            print(f"Error durante la compactacion del hashing extensible: {e}")
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

    def print_structure(self):
        print(f"Profundidad Global: {self.global_depth}")
        print(f"Tamaño del Directorio: {len(self.directory)}")
        print(f"Tamaño del Bucket (configurado): {self.bucket_size}")

        sorted_dir_keys = sorted(self.directory.keys())

        for dir_hash_prefix in sorted_dir_keys:
            bucket = self.directory[dir_hash_prefix]
            print(f"  Directorio['{dir_hash_prefix}'] -> Bucket ID: {id(bucket)} (Prof. Local: {bucket.local_depth})")

        print("\nContenido de Buckets (unicos):")
        seen_buckets_print = set()
        for dir_hash_prefix in sorted_dir_keys:
            bucket = self.directory[dir_hash_prefix]
            if id(bucket) not in seen_buckets_print:
                print(f"  Bucket ID: {id(bucket)} (Prof. Local: {bucket.local_depth}, Lleno: {bucket.is_full()}, Vacio: {bucket.is_empty()})")
                for k,p in bucket.entries:
                    print(f"    - Clave: {k}, Posicion: {p}")
                if not bucket.entries:
                    print("    - (Vacio)")
                seen_buckets_print.add(id(bucket))
