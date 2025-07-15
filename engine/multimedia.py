import os
import sys
import numpy as np
import pickle
from typing import List, Dict, Tuple, Union, Optional
import heapq
from collections import Counter
import cv2
import librosa
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import time

class FeatureExtractor:
    """Extracción de características de archivos multimedia (imágenes o audio)"""
    
    @staticmethod
    def extract_features_image(image_path: str, method: str = 'sift') -> np.ndarray:
        """
        Extrae características de una imagen
        
        Args:
            image_path: Ruta al archivo de imagen
            method: Método de extracción ('sift', 'inception', 'resnet')
            
        Returns:
            np.ndarray: Descriptores de características
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Archivo de imagen no encontrado: {image_path}")
        
        if method == 'sift':
            # Usar algoritmo SIFT
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                raise ValueError(f"No se pudo leer la imagen: {image_path}")
                
            sift = cv2.SIFT_create()
            keypoints, descriptors = sift.detectAndCompute(img, None)
            
            # Si no se encuentran características, devolver array vacío
            if descriptors is None:
                return np.array([])
                
            return descriptors
        
        elif method == 'inception' or method == 'resnet':
            raise NotImplementedError(f"Extracción de características con {method} aún no implementada")
        
        else:
            raise ValueError(f"Método de extracción de características desconocido: {method}")
    
    @staticmethod
    def extract_features_audio(audio_path: str, method: str = 'mfcc') -> np.ndarray:
        """
        Extrae características de un archivo de audio
        
        Args:
            audio_path: Ruta al archivo de audio
            method: Método de extracción ('mfcc', 'spectrogram')
            
        Returns:
            np.ndarray: Descriptores de características
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Archivo de audio no encontrado: {audio_path}")
        
        if method == 'mfcc':
            # Cargar archivo de audio
            y, sr = librosa.load(audio_path, sr=None)
            
            # Extraer coeficientes MFCC
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            
            # Transponer para obtener características en filas
            mfccs = mfccs.T
            
            return mfccs
        
        elif method == 'spectrogram':
            y, sr = librosa.load(audio_path, sr=None)
            D = np.abs(librosa.stft(y))
            return D.T
        
        else:
            raise ValueError(f"Método de extracción de características de audio desconocido: {method}")


class CodebookBuilder:
    """Construye un codebook (diccionario visual o acústico) a partir de descriptores de características"""
    
    def __init__(self, n_clusters: int = 100):
        """
        Inicializa el constructor de codebook
        
        Args:
            n_clusters: Número de clusters (palabras clave) en el codebook
        """
        self.n_clusters = n_clusters
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=0)
        self.codebook = None
        self.is_trained = False
    
    def build(self, features_list: List[np.ndarray]) -> np.ndarray:
        """
        Construye el codebook a partir de una lista de arrays de características
        
        Args:
            features_list: Lista de arrays de características de múltiples archivos
            
        Returns:
            np.ndarray: Codebook (centros de clusters)
        """
        # Combinar todas las características en un array
        if not features_list or len(features_list) == 0:
            raise ValueError("Se proporcionó una lista de características vacía")
        
        # Filtrar arrays de características vacíos
        features_list = [f for f in features_list if f is not None and len(f) > 0]
        if not features_list:
            raise ValueError("No se encontraron características válidas en la lista proporcionada")
        
        # Combinar todas las características en un array
        all_features = np.vstack(features_list)
        
        if len(all_features) < self.n_clusters:
            # Si tenemos menos vectores de características que clusters, reducir el número de clusters
            self.n_clusters = max(1, len(all_features) // 2)
            self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=0)
            
        # Ajustar KMeans
        self.kmeans.fit(all_features)
        self.codebook = self.kmeans.cluster_centers_
        self.is_trained = True
        
        return self.codebook
    
    def save(self, path: str):
        """Guardar codebook en archivo"""
        with open(path, 'wb') as f:
            pickle.dump({
                'codebook': self.codebook,
                'n_clusters': self.n_clusters,
                'is_trained': self.is_trained,
                'kmeans': self.kmeans
            }, f)
    
    @staticmethod
    def load(path: str) -> 'CodebookBuilder':
        """Cargar codebook desde archivo"""
        with open(path, 'rb') as f:
            data = pickle.load(f)
            
        cb = CodebookBuilder(n_clusters=data['n_clusters'])
        cb.codebook = data['codebook']
        cb.is_trained = data['is_trained']
        cb.kmeans = data['kmeans']
        return cb


class BagOfWords:
    """Convierte descriptores de características a representación bag-of-words usando un codebook"""
    
    def __init__(self, codebook_builder: CodebookBuilder):
        """
        Inicializa el convertidor de bag of words
        
        Args:
            codebook_builder: Instancia entrenada de constructor de codebook
        """
        if not codebook_builder.is_trained:
            raise ValueError("El codebook no ha sido entrenado")
        
        self.codebook_builder = codebook_builder
        self.document_frequency = None
        self.n_documents = 0
        
    def compute_histogram(self, features: np.ndarray) -> np.ndarray:
        """
        Calcula el histograma de palabras clave para un solo documento
        
        Args:
            features: Descriptores de características
            
        Returns:
            np.ndarray: Histograma (representación bag-of-words)
        """
        if features is None or len(features) == 0:
            # Devuelve un histograma vacío (todos ceros)
            return np.zeros(self.codebook_builder.n_clusters)
        
        # Asignar cada característica al cluster más cercano
        cluster_assignments = self.codebook_builder.kmeans.predict(features)
        
        # Contar ocurrencias de cada cluster
        histogram = np.zeros(self.codebook_builder.n_clusters)
        for cluster_idx in cluster_assignments:
            histogram[cluster_idx] += 1
            
        # Normalizar
        if np.sum(histogram) > 0:
            histogram = histogram / np.sum(histogram)
        
        return histogram
    
    def compute_tf_idf_weights(self, histogram_list: List[np.ndarray]) -> List[np.ndarray]:
        """
        Calcula pesos TF-IDF para una lista de histogramas
        
        Args:
            histogram_list: Lista de histogramas
            
        Returns:
            List[np.ndarray]: Histogramas ponderados por TF-IDF
        """
        n_documents = len(histogram_list)
        if n_documents == 0:
            return []
        
        # Contar frecuencia de documento (en cuántos documentos aparece cada palabra clave)
        self.n_documents = n_documents
        self.document_frequency = np.zeros(self.codebook_builder.n_clusters)
        
        for histogram in histogram_list:
            # Para cada palabra clave, contar si aparece en el documento (binario)
            self.document_frequency += (histogram > 0).astype(int)
        
        # Evitar división por cero
        self.document_frequency = np.maximum(self.document_frequency, 1)
        
        # Calcular IDF
        idf = np.log(n_documents / self.document_frequency)
        
        # Aplicar ponderación TF-IDF a cada histograma
        weighted_histograms = []
        for histogram in histogram_list:
            weighted_histogram = histogram * idf
            weighted_histograms.append(weighted_histogram)
            
        return weighted_histograms


class MultimediaSearchEngine:
    """Motor de búsqueda para archivos multimedia usando KNN e índice invertido"""
    
    def __init__(self, feature_extractor_method: str = 'sift', n_clusters: int = 100):
        """
        Inicializa el motor de búsqueda
        
        Args:
            feature_extractor_method: Método para extracción de características ('sift', 'mfcc')
            n_clusters: Número de clusters (palabras clave) en el codebook
        """
        self.feature_extractor_method = feature_extractor_method
        self.codebook_builder = CodebookBuilder(n_clusters=n_clusters)
        self.bow = None
        
        # Almacenamiento para registros y sus histogramas
        self.records = []  # Lista de tuplas (id, ruta, metadatos)
        self.histograms = []  # Lista de histogramas correspondientes a registros
        self.weighted_histograms = []  # Histogramas ponderados por TF-IDF
        
        # Índice invertido mapeando desde palabra clave a documentos
        self.inverted_index = {}  # {codeword_idx: [(doc_idx, weight), ...]}
        
    def build_index(self, records: List[Tuple[int, str, Dict]]) -> None:
        """
        Construye índice para los registros proporcionados
        
        Args:
            records: Lista de registros (id, ruta, metadatos)
        """
        self.records = records
        
        # Extraer características para todos los registros
        print(f"Extrayendo características para {len(records)} registros...")
        features_list = []
        for record_id, path, _ in records:
            try:
                if path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                    features = FeatureExtractor.extract_features_image(path, self.feature_extractor_method)
                elif path.lower().endswith(('.wav', '.mp3', '.ogg')):
                    features = FeatureExtractor.extract_features_audio(path, self.feature_extractor_method)
                else:
                    print(f"Formato de archivo no soportado: {path}")
                    features = np.array([])
                
                features_list.append(features)
            except Exception as e:
                print(f"Error extrayendo características de {path}: {e}")
                features_list.append(np.array([]))
        
        # Construir codebook
        print("Construyendo codebook...")
        self.codebook_builder.build(features_list)
        self.bow = BagOfWords(self.codebook_builder)
        
        # Calcular histogramas
        print("Calculando histogramas...")
        self.histograms = []
        for features in features_list:
            histogram = self.bow.compute_histogram(features)
            self.histograms.append(histogram)
        
        # Calcular histogramas ponderados por TF-IDF
        print("Calculando pesos TF-IDF...")
        self.weighted_histograms = self.bow.compute_tf_idf_weights(self.histograms)
        
        # Construir índice invertido
        print("Construyendo índice invertido...")
        self.build_inverted_index()
        
    def build_inverted_index(self) -> None:
        """Construye índice invertido a partir de histogramas ponderados"""
        self.inverted_index = {}
        
        # Para cada palabra clave, construir una lista de documentos que la contienen
        for codeword_idx in range(self.codebook_builder.n_clusters):
            self.inverted_index[codeword_idx] = []
            
            # Para cada documento, comprobar si contiene la palabra clave
            for doc_idx, weighted_histogram in enumerate(self.weighted_histograms):
                weight = weighted_histogram[codeword_idx]
                if weight > 0:
                    self.inverted_index[codeword_idx].append((doc_idx, weight))
    
    def knn_sequential(self, query_path: str, k: int = 10) -> List[Tuple[int, float, Dict]]:
        """
        Realiza búsqueda KNN secuencial
        
        Args:
            query_path: Ruta al archivo de consulta
            k: Número de vecinos más cercanos a recuperar
            
        Returns:
            Lista de tuplas (record_id, similitud, metadatos)
        """
        start_time = time.time()
        
        # Extraer características de la consulta
        if query_path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            query_features = FeatureExtractor.extract_features_image(query_path, self.feature_extractor_method)
        elif query_path.lower().endswith(('.wav', '.mp3', '.ogg')):
            query_features = FeatureExtractor.extract_features_audio(query_path, self.feature_extractor_method)
        else:
            raise ValueError(f"Formato de archivo no soportado: {query_path}")
        
        # Calcular histograma para la consulta
        query_histogram = self.bow.compute_histogram(query_features)
        
        # Aplicar ponderación TF-IDF
        if self.bow.document_frequency is not None:
            query_weighted = query_histogram * np.log(self.bow.n_documents / self.bow.document_frequency)
        else:
            query_weighted = query_histogram
        
        # Min heap para los K mejores resultados (usar similitud negativa para comportamiento de max heap)
        heap = []
        
        # Calcular similitud con cada documento
        for i, weighted_histogram in enumerate(self.weighted_histograms):
            # Calcular similitud de coseno
            sim = cosine_similarity([query_weighted], [weighted_histogram])[0][0]
            
            # Actualizar heap
            if len(heap) < k:
                heapq.heappush(heap, (sim, i))
            elif sim > heap[0][0]:
                heapq.heapreplace(heap, (sim, i))
        
        # Ordenar resultados por similitud (descendente)
        results = sorted(heap, reverse=True)
        
        # Formatear resultados
        formatted_results = []
        for sim, idx in results:
            record_id, path, metadata = self.records[idx]
            formatted_results.append((record_id, sim, metadata))
        
        elapsed_time = time.time() - start_time
        print(f"Búsqueda KNN secuencial completada en {elapsed_time:.4f} segundos")
        
        return formatted_results
    
    def knn_inverted_index(self, query_path: str, k: int = 10) -> List[Tuple[int, float, Dict]]:
        """
        Realiza búsqueda KNN utilizando índice invertido
        
        Args:
            query_path: Ruta al archivo de consulta
            k: Número de vecinos más cercanos a recuperar
            
        Returns:
            Lista de tuplas (record_id, similitud, metadatos)
        """
        start_time = time.time()
        
        # Extraer características de la consulta
        if query_path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            query_features = FeatureExtractor.extract_features_image(query_path, self.feature_extractor_method)
        elif query_path.lower().endswith(('.wav', '.mp3', '.ogg')):
            query_features = FeatureExtractor.extract_features_audio(query_path, self.feature_extractor_method)
        else:
            raise ValueError(f"Formato de archivo no soportado: {query_path}")
        
        # Calcular histograma para la consulta
        query_histogram = self.bow.compute_histogram(query_features)
        
        # Aplicar ponderación TF-IDF
        if self.bow.document_frequency is not None:
            query_weighted = query_histogram * np.log(self.bow.n_documents / self.bow.document_frequency)
        else:
            query_weighted = query_histogram
        
        # Acumular puntuaciones de documentos usando índice invertido
        doc_scores = {}
        
        # Para cada palabra clave en la consulta
        for codeword_idx, query_weight in enumerate(query_weighted):
            if query_weight > 0 and codeword_idx in self.inverted_index:
                # Obtener documentos que contienen esta palabra clave
                for doc_idx, doc_weight in self.inverted_index[codeword_idx]:
                    if doc_idx not in doc_scores:
                        doc_scores[doc_idx] = 0
                    # Acumular puntuación ponderada por TF-IDF
                    doc_scores[doc_idx] += query_weight * doc_weight
        
        # Normalizar puntuaciones (aproximación de similitud de coseno)
        for doc_idx in doc_scores:
            # Normalización de coseno aproximada
            query_norm = np.sqrt(np.sum(query_weighted**2))
            doc_norm = np.sqrt(np.sum(self.weighted_histograms[doc_idx]**2))
            if query_norm > 0 and doc_norm > 0:
                doc_scores[doc_idx] /= (query_norm * doc_norm)
        
        # Obtener los K mejores resultados usando un heap
        heap = []
        for doc_idx, score in doc_scores.items():
            if len(heap) < k:
                heapq.heappush(heap, (score, doc_idx))
            elif score > heap[0][0]:
                heapq.heapreplace(heap, (score, doc_idx))
        
        # Ordenar resultados por puntuación (descendente)
        results = sorted(heap, reverse=True)
        
        # Formatear resultados
        formatted_results = []
        for sim, idx in results:
            record_id, path, metadata = self.records[idx]
            formatted_results.append((record_id, sim, metadata))
        
        elapsed_time = time.time() - start_time
        print(f"Búsqueda KNN con índice invertido completada en {elapsed_time:.4f} segundos")
        
        return formatted_results
    
    def save(self, path: str):
        """Guardar motor de búsqueda en archivo"""
        with open(path, 'wb') as f:
            pickle.dump({
                'feature_extractor_method': self.feature_extractor_method,
                'codebook_builder': self.codebook_builder,
                'records': self.records,
                'histograms': self.histograms,
                'weighted_histograms': self.weighted_histograms,
                'inverted_index': self.inverted_index,
                'bow': self.bow
            }, f)
    
    @staticmethod
    def load(path: str) -> 'MultimediaSearchEngine':
        """Cargar motor de búsqueda desde archivo"""
        with open(path, 'rb') as f:
            data = pickle.load(f)
        
        engine = MultimediaSearchEngine(
            feature_extractor_method=data['feature_extractor_method'],
            n_clusters=data['codebook_builder'].n_clusters
        )
        engine.codebook_builder = data['codebook_builder']
        engine.records = data['records']
        engine.histograms = data['histograms']
        engine.weighted_histograms = data['weighted_histograms']
        engine.inverted_index = data['inverted_index']
        engine.bow = data['bow']
        
        return engine 