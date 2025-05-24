import os
import pickle
import json
import math
import shutil
from bisect import bisect_left, insort_left

DATA_BLOCK_FACTOR = 5
INDEX_BLOCK_FACTOR = 7
ISAM_DATA_FILE = "isam_data.jsonl"
ISAM_INDEX_FILE = "isam_index.pkl"
ISAM_META_FILE = "isam_meta.pkl"

class ISAMPage:
    def __init__(self):
        self.entries = []

    def is_full(self, factor):
        return len(self.entries) >= factor

    def is_underflow(self, factor):
        return len(self.entries) < math.ceil(factor / 2)

    def get_max_key(self):
        return self.entries[-1][0] if self.entries else None

class ISAMDataPage(ISAMPage):
    def __init__(self):
        super().__init__()
        self.overflow_ptr = None

    def insert(self, key, position):
        insort_left(self.entries, (key, position))

    def search(self, key):
        for k, pos in self.entries:
            if k == key:
                return pos
            if k > key:
                break
        return None

    def delete(self, key):
        for i, (k, _) in enumerate(self.entries):
            if k == key:
                del self.entries[i]
                return True
        return False

class ISAMOverflowPage(ISAMDataPage):
    def __init__(self):
        super().__init__()
        self.next_overflow_ptr = None

class ISAMIndexPage(ISAMPage):
    def __init__(self):
        super().__init__()

    def find_child_ptr(self, key):
        if not self.entries:
            return None

        keys = [k for k, p in self.entries]
        idx = bisect_left(keys, key)
        if idx < len(keys):
            return self.entries[idx][1]
        else:
            return self.entries[-1][1]

class ISAMFile:
    def __init__(self, data_file=ISAM_DATA_FILE, index_file=ISAM_INDEX_FILE, meta_file=ISAM_META_FILE, data_bf=DATA_BLOCK_FACTOR, index_bf=INDEX_BLOCK_FACTOR):
        self.data_file = data_file
        self.index_file = index_file
        self.meta_file = meta_file
        self.data_bf = data_bf
        self.index_bf = index_bf

        self.data_pages = []
        self.overflow_pages = []
        self.index_pages = []
        self.root_ptr = None

        self._load_or_initialize()

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
                return json.loads(line.strip()) if line else None
        except Exception as e:
            print(f"Error leyendo ISAM data: {e}")
            return None

    def _save_all(self):
        try:
            with open(self.index_file, "wb") as f:
                pickle.dump((self.data_pages, self.overflow_pages, self.index_pages), f)
            with open(self.meta_file, "wb") as f:
                pickle.dump(self.root_ptr, f)
        except Exception as e:
            print(f"Error fatal guardando ISAM: {e}")

    def _load_all(self):
        if not os.path.exists(self.index_file) or not os.path.exists(self.meta_file):
            return False
        try:
            with open(self.index_file, "rb") as f:
                self.data_pages, self.overflow_pages, self.index_pages = pickle.load(f)
            with open(self.meta_file, "rb") as f:
                self.root_ptr = pickle.load(f)
            return True
        except Exception as e:
            print(f"Error cargando ISAM ({e}), se reiniciara")
            return False

    def _load_or_initialize(self):
        if not self._load_all():
            print("Inicializando nuevo ISAM...")
            self.data_pages = [ISAMDataPage()]
            self.overflow_pages = []
            l1_page = ISAMIndexPage()
            l1_page.entries.append((float('inf'), 0))
            self.index_pages = [l1_page]
            root_page = ISAMIndexPage()
            root_page.entries.append((float('inf'), 0))
            self.index_pages.append(root_page)
            self.root_ptr = 1

            open(self.data_file, "w").close()
            self._save_all()
        else:
            print("Indice ISAM cargado exitosamente")

    def _get_page(self, ptr, page_type='index'):
        if page_type == 'index':
            return self.index_pages[ptr]
        if page_type == 'data':
            return self.data_pages[ptr]
        if page_type == 'overflow':
            return self.overflow_pages[ptr]
        raise ValueError(f"Tipo de pagina desconocida: {page_type}")

    def _add_page(self, page_obj, page_type='index'):
        if page_type == 'index':
            self.index_pages.append(page_obj)
            return len(self.index_pages) - 1
        if page_type == 'data':
            self.data_pages.append(page_obj)
            return len(self.data_pages) - 1
        if page_type == 'overflow':
            self.overflow_pages.append(page_obj)
            return len(self.overflow_pages) - 1
        raise ValueError(f"Tipo de pagina desconocida: {page_type}")

    def _find_data_page_ptr(self, key):
        root = self._get_page(self.root_ptr, 'index')

        l1_ptr = root.find_child_ptr(key)
        if l1_ptr is None:
            raise RuntimeError("Error de indice: L1 Ptr nulo")
        l1_page = self._get_page(l1_ptr, 'index')

        data_ptr = l1_page.find_child_ptr(key)
        if data_ptr is None:
            raise RuntimeError("Error de indice: Data Ptr nulo")

        return data_ptr

    def insert(self, key, record_data: dict):
        if self.search(key) is not None:
            print(f"Warning: clave {key} ya existe, no se insertara")
            return

        position = self._append_to_data_file(record_data)
        data_ptr = self._find_data_page_ptr(key)
        data_page = self._get_page(data_ptr, 'data')

        if not data_page.is_full(self.data_bf):
            data_page.insert(key, position)
            print(f"Clave {key} insertada en DataPage {data_ptr}")
        else:
            print(f"DataPage {data_ptr} llena, usando overflow para {key}")
            ov_ptr = data_page.overflow_ptr
            if ov_ptr is None:
                op = ISAMOverflowPage()
                op.insert(key, position)
                new_ov_ptr = self._add_page(op, 'overflow')
                data_page.overflow_ptr = new_ov_ptr
            else:
                while True:
                    op = self._get_page(ov_ptr, 'overflow')
                    if not op.is_full(self.data_bf):
                        op.insert(key, position)
                        break
                    elif op.next_overflow_ptr is None:
                        new_op = ISAMOverflowPage()
                        new_op.insert(key, position)
                        new_ov_ptr = self._add_page(new_op, 'overflow')
                        op.next_overflow_ptr = new_ov_ptr
                        break
                    else:
                        ov_ptr = op.next_overflow_ptr

        self._save_all()

    def search(self, key) -> dict | None:
        try:
            data_ptr = self._find_data_page_ptr(key)
        except RuntimeError:
            print("Error buscando la pagina, es posible que el indice este vacio o dañado")
            return None

        data_page = self._get_page(data_ptr, 'data')

        pos = data_page.search(key)
        if pos is not None:
            return self._read_from_data_file(pos)

        ov_ptr = data_page.overflow_ptr
        while ov_ptr is not None:
            op = self._get_page(ov_ptr, 'overflow')
            pos = op.search(key)
            if pos is not None:
                return self._read_from_data_file(pos)
            ov_ptr = op.next_overflow_ptr

        return None

    def delete(self, key):
        data_ptr = self._find_data_page_ptr(key)
        data_page = self._get_page(data_ptr, 'data')

        if data_page.delete(key):
            print(f"Clave {key} eliminada de DataPage {data_ptr}")
            self._save_all()
            return True

        ov_ptr = data_page.overflow_ptr
        while ov_ptr is not None:
            op = self._get_page(ov_ptr, 'overflow')
            if op.delete(key):
                print(f"Clave {key} eliminada de OverflowPage {ov_ptr}")
                self._save_all()
                return True
            ov_ptr = op.next_overflow_ptr

        print(f"Warning: Clave {key} no encontrada para eliminar")
        return False

    def update(self, key, new_record_data: dict) -> bool:
        data_ptr = self._find_data_page_ptr(key)
        data_page = self._get_page(data_ptr, 'data')

        def _update_in_page(page, k_search, new_pos):
            for i, (k, pos) in enumerate(page.entries):
                if k == k_search:
                    page.entries[i] = (k, new_pos)
                    return True
            return False

        new_position = self._append_to_data_file(new_record_data)

        if _update_in_page(data_page, key, new_position):
            print(f"Clave {key} actualizada en DataPage {data_ptr}")
            self._save_all()
            return True

        ov_ptr = data_page.overflow_ptr
        while ov_ptr is not None:
            op = self._get_page(ov_ptr, 'overflow')
            if _update_in_page(op, key, new_position):
                print(f"Clave {key} actualizada en OverflowPage {ov_ptr}")
                self._save_all()
                return True
            ov_ptr = op.next_overflow_ptr

        print(f"Error: clave {key} no encontrada para actualizar")
        return False

    def get_all_records_sorted(self):
        all_recs = []
        for dp_idx, data_page in enumerate(self.data_pages):
            all_recs.extend(data_page.entries)
            ov_ptr = data_page.overflow_ptr
            while ov_ptr is not None:
                op = self._get_page(ov_ptr, 'overflow')
                all_recs.extend(op.entries)
                ov_ptr = op.next_overflow_ptr

        all_recs.sort()

        return [(k, self._read_from_data_file(p)) for k, p in all_recs if p is not None]

    def bulk_load(self, sorted_records: list):
        print("Iniciando Bulk Load...")
        if not sorted_records:
            print("No hay datos para cargar")
            return

        open(self.data_file, "w").close()
        self.data_pages = []
        self.overflow_pages = []
        self.index_pages = []

        current_data_page = ISAMDataPage()
        self.data_pages.append(current_data_page)

        for key, record_data in sorted_records:
            pos = self._append_to_data_file(record_data)
            if current_data_page.is_full(self.data_bf):
                current_data_page = ISAMDataPage()
                self.data_pages.append(current_data_page)
            current_data_page.insert(key, pos)

        print(f"Creadas {len(self.data_pages)} paginas de datos")

        current_l1_page = ISAMIndexPage()
        self.index_pages.append(current_l1_page)
        l1_pointers = [0]

        for i, dp in enumerate(self.data_pages):
            max_key = dp.get_max_key()
            if current_l1_page.is_full(self.index_bf):
                current_l1_page = ISAMIndexPage()
                ptr = self._add_page(current_l1_page, 'index')
                l1_pointers.append(ptr)
            current_l1_page.entries.append((max_key, i))

        print(f"Creadas {len(l1_pointers)} paginas de indice Nivel 1")

        root_page = ISAMIndexPage()
        self.root_ptr = self._add_page(root_page, 'index')

        for l1_ptr in l1_pointers:
            l1_page = self._get_page(l1_ptr, 'index')
            max_key = l1_page.get_max_key()
            if root_page.is_full(self.index_bf):
                 raise RuntimeError("Raiz llena! Se necesitaria un Nivel 3")
            root_page.entries.append((max_key, l1_ptr))

        print(f"Creada pagina raiz (Nivel 2) con {len(root_page.entries)} entradas")

        self._save_all()
        print("Bulk Load completado y guardado")

    def reorganize(self):
        print("Iniciando reorganizacion ISAM...")
        all_records = self.get_all_records_sorted()
        if not all_records:
            print("No hay registros para reorganizar")
            self._load_or_initialize()
            return

        valid_records = [(k, r) for k, r in all_records if r is not None]

        temp_data_file = self.data_file + ".tmp"
        try:
            shutil.copy(self.data_file, temp_data_file)
            self.bulk_load(valid_records)
            os.remove(temp_data_file)
            print("Reorganizacion completada")
        except Exception as e:
            print(f"Error durante la reorganizacion: {e}")
            if os.path.exists(temp_data_file):
                print("Intentando restaurar desde backup...")
                shutil.move(temp_data_file, self.data_file)
                self._load_all()
        finally:
            if os.path.exists(temp_data_file):
                os.remove(temp_data_file)

    def print_structure(self):
        if self.root_ptr is None:
            print("indice vacio")
            return

        print(f"Puntero Raiz (Nivel 2): {self.root_ptr}")
        root = self._get_page(self.root_ptr)
        print(f"  Root Entries ({len(root.entries)}): {root.entries}")

        l1_ptrs = set(p for k, p in root.entries)
        for l1_ptr in sorted(l1_ptrs):
            l1 = self._get_page(l1_ptr)
            print(f"  L1 Page Ptr: {l1_ptr}")
            print(f"    L1 Entries ({len(l1.entries)}): {l1.entries}")

            dp_ptrs = set(p for k, p in l1.entries)
            for dp_ptr in sorted(dp_ptrs):
                dp = self._get_page(dp_ptr, 'data')
                print(f"    Data Page Ptr: {dp_ptr}")
                print(f"      DP Entries ({len(dp.entries)}): {dp.entries}")
                ov_ptr = dp.overflow_ptr
                ov_count = 0
                while ov_ptr is not None:
                    ov_count += 1
                    ov = self._get_page(ov_ptr, 'overflow')
                    print(f"      Overflow Page Ptr {ov_ptr} (OV{ov_count})")
                    print(f"        OV Entries ({len(ov.entries)}): {ov.entries}")
                    ov_ptr = ov.next_overflow_ptr
