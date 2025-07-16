import os
import sys
import pickle
import numpy as np
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.model import TableSchema, Column, DataType, IndexType
from engine import utils
from engine.record import RecordFile
from engine.multimedia import MultimediaSearchEngine

# Clase base para índices multimedia
class MultimediaIndexBase:
    def __init__(self, schema: TableSchema, column: Column):
        self.schema = schema
        self.column = column
        
        if column.data_type != DataType.IMAGE and column.data_type != DataType.AUDIO:
            raise ValueError(f"El índice multimedia solo puede aplicarse a columnas de tipo IMAGE o AUDIO, no a {column.data_type}")
        
        # Definir el método de extracción de características según el tipo de datos
        if column.data_type == DataType.IMAGE:
            self.feature_method = 'sift'  # Por defecto para imágenes
        else:
            self.feature_method = 'mfcc'  # Por defecto para audio
        
        # Ruta para guardar los archivos de índice
        self.index_dir = f"{utils.get_tables_dir()}/{schema.table_name}/indexes"
        os.makedirs(self.index_dir, exist_ok=True)
        
        self.index_file = f"{self.index_dir}/{column.name}_multimedia_index.pkl"
        self.search_engine = None
        
        # Inicializar el motor de búsqueda si existe el archivo de índice
        if os.path.exists(self.index_file):
            self._load()
        else:
            self._initialize()
    
    def _initialize(self):
        """Inicializa un nuevo motor de búsqueda"""
        self.search_engine = MultimediaSearchEngine(feature_extractor_method=self.feature_method)
    
    def _load(self):
        """Carga el motor de búsqueda desde un archivo"""
        try:
            self.search_engine = MultimediaSearchEngine.load(self.index_file)
        except Exception as e:
            print(f"Error al cargar índice multimedia: {e}")
            self._initialize()
    
    def _save(self):
        """Guarda el motor de búsqueda en un archivo"""
        if self.search_engine:
            self.search_engine.save(self.index_file)
    
    def _get_all_records(self) -> list:
        """Obtiene todos los registros de la tabla con sus rutas multimedia"""
        record_file = RecordFile(self.schema)
        max_id = record_file.max_id()
        
        # Encontrar el índice de nuestra columna multimedia
        col_index = -1
        for i, col in enumerate(self.schema.columns):
            if col.name == self.column.name:
                col_index = i
                break
        
        if col_index == -1:
            raise ValueError(f"Columna {self.column.name} no encontrada en el esquema")
        
        # Recopilar registros
        records = []
        for pos in range(max_id):
            record = record_file.read(pos)
            if record:
                # Obtener la ruta del archivo multimedia desde el registro
                media_path = record.values[col_index]
                
                # Recopilar metadatos del registro
                metadata = {}
                for i, col in enumerate(self.schema.columns):
                    if i != col_index:  # Omitir la columna multimedia
                        metadata[col.name] = record.values[i]
                
                records.append((pos, media_path, metadata))
        
        return records
    
    def _build_or_update_index(self):
        """Construye o actualiza el índice de búsqueda multimedia"""
        records = self._get_all_records()
        
        if not records:
            print("No se encontraron registros para indexar")
            return
        
        # Construir índice con todos los registros
        self.search_engine.build_index(records)
        
        # Guardar el índice en el archivo
        self._save()
    
    def insert(self, pos: int, val: any):
        """
        Inserta un nuevo registro en el índice
        
        Este método reconstruye todo el índice cuando los datos cambian.
        Es costoso pero asegura precisión. Un enfoque más optimizado sería
        agregar actualizaciones incrementales.
        """
        self._build_or_update_index()
    
    def search(self, key) -> list[int]:
        """
        La búsqueda directa no es aplicable para índices multimedia
        Este método existe solo por compatibilidad con la interfaz de índices
        """
        return []
    
    def rangeSearch(self, ini, end) -> list[int]:
        """
        La búsqueda por rango no es aplicable para índices multimedia
        Este método existe solo por compatibilidad con la interfaz de índices
        """
        return []
    
    def getAll(self) -> list[int]:
        """Obtiene todos los IDs de registros en este índice"""
        if not self.search_engine:
            return []
        
        return [record_id for record_id, _, _ in self.search_engine.records]
    
    def clear(self):
        """Limpia el índice"""
        if os.path.exists(self.index_file):
            os.remove(self.index_file)
        self._initialize()


class MultimediaSequentialIndex(MultimediaIndexBase):
    """Búsqueda KNN secuencial para datos multimedia"""
    
    def __init__(self, schema: TableSchema, column: Column):
        super().__init__(schema, column)
        
        # Sobreescribir ruta del archivo de índice
        self.index_file = f"{self.index_dir}/{column.name}_multimedia_sequential_index.pkl"
        
        # Inicializar o cargar
        if os.path.exists(self.index_file):
            self._load()
        else:
            self._initialize()
    
    def similarity_search(self, query_path: str, k: int = 10) -> list:
        """
        Realiza búsqueda por similitud usando KNN secuencial
        
        Args:
            query_path: Ruta al archivo de consulta
            k: Número de vecinos más cercanos a recuperar
            
        Returns:
            Lista de tuplas (record_id, similitud, metadatos)
        """
        # Construir o actualizar índice si no tiene registros
        if not getattr(self.search_engine, 'records', None):
            self._build_or_update_index()

        if not self.search_engine or not getattr(self.search_engine, 'records', None):
            return []
        
        try:
            return self.search_engine.knn_sequential(query_path, k)
        except Exception as e:
            print(f"Error durante la búsqueda por similitud: {e}")
            return []


class MultimediaInvertedIndex(MultimediaIndexBase):
    """Búsqueda KNN con índice invertido para datos multimedia"""
    
    def __init__(self, schema: TableSchema, column: Column):
        super().__init__(schema, column)
        
        # Sobreescribir ruta del archivo de índice
        self.index_file = f"{self.index_dir}/{column.name}_multimedia_inverted_index.pkl"
        
        # Inicializar o cargar
        if os.path.exists(self.index_file):
            self._load()
        else:
            self._initialize()
    
    def similarity_search(self, query_path: str, k: int = 10) -> list:
        """
        Realiza búsqueda por similitud usando índice invertido
        
        Args:
            query_path: Ruta al archivo de consulta
            k: Número de vecinos más cercanos a recuperar
            
        Returns:
            Lista de tuplas (record_id, similitud, metadatos)
        """
        if not self.search_engine:
            # Si no hay motor de búsqueda, intentar construir índice
            self._build_or_update_index()
        
        if not self.search_engine or not self.search_engine.records:
            return []
        
        try:
            return self.search_engine.knn_inverted_index(query_path, k)
        except Exception as e:
            print(f"Error durante la búsqueda por similitud: {e}")
            return [] 