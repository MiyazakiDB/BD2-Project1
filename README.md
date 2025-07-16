## INTRODUCCIÓN:

El dominio de datos de este sistema abarca **archivos multimedia** de tres tipos principales: **imágenes**, **audio** y **texto**.

- **Imágenes**: Fotografías, ilustraciones, capturas, diagramas, etc., en formatos como JPG, PNG.
- **Audio**: Grabaciones de voz, música, sonidos ambientales, podcasts, etc., en formatos como WAV, MP3.
- **Texto**: Documentos, artículos, descripciones, notas, archivos TXT.

Cada tipo de dato posee características propias y requiere técnicas de procesamiento y representación distintas para su análisis y recuperación eficiente.

---

### Justificación de la necesidad de una base de datos multimodal para recuperación por contenido

En la actualidad, los sistemas de información deben gestionar y recuperar datos provenientes de **múltiples modalidades** (texto, imágenes, audio) de manera integrada. Una base de datos multimodal permite:

- **Almacenamiento estructurado y eficiente** de diferentes tipos de datos en un mismo sistema, facilitando la gestión y consulta conjunta.
- **Recuperación por contenido**: Permite buscar archivos no solo por metadatos (nombre, fecha, etc.), sino por su contenido intrínseco (similitud visual, acústica o semántica).
- **Consultas avanzadas**: Los usuarios pueden realizar búsquedas como "imágenes similares a esta", "audios parecidos a este fragmento" o "documentos relacionados con este texto", lo que no es posible en bases de datos tradicionales.
- **Integración de técnicas de machine learning** para extracción de características y comparación, mejorando la precisión y relevancia de los resultados.
- **Escalabilidad y flexibilidad**: Facilita la incorporación de nuevos tipos de datos y algoritmos de búsqueda, adaptándose a necesidades cambiantes.

## BACKEND

## **Construcción del índice invertido en memoria secundaria**

### **Implementación en #multimediatree.py**

## 1. Extracción de características de archivos multimedia

```python
def build_index(self, records: List[Tuple[int, str, Dict]]) -> None:
    # Extraer características para todos los registros
    features_list = []
    for record_id, path, _ in records:
        if path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            features = FeatureExtractor.extract_features_image(path, 'sift')
        elif path.lower().endswith(('.wav', '.mp3', '.ogg')):
            features = FeatureExtractor.extract_features_audio(path, 'mfcc')
        features_list.append(features)

```

## **2. Construcción del Codebook (Visual Vocabulary)**

```python
# Construir codebook usando K-Means clustering
self.codebook_builder.build(features_list)
self.bow = BagOfWords(self.codebook_builder)

# Calcular histogramas (Bag-of-Words)
self.histograms = []
for features in features_list:
    histogram = self.bow.compute_histogram(features)
    self.histograms.append(histogram)
```

## **3. Ponderación TF-IDF y construcción del índice invertido**

```python
def build_inverted_index(self) -> None:
    """Construye índice invertido a partir de histogramas ponderados"""
    self.inverted_index = {}
    
    # Para cada palabra clave (cluster), construir lista de documentos
    for codeword_idx in range(self.codebook_builder.n_clusters):
        self.inverted_index[codeword_idx] = []
        
        # Para cada documento, verificar si contiene la palabra clave
        for doc_idx, weighted_histogram in enumerate(self.weighted_histograms):
            weight = weighted_histogram[codeword_idx]
            if weight > 0:
                self.inverted_index[codeword_idx].append((doc_idx, weight))
```

## **4. Persistencia en memoria secundaria**

```python
def save(self, path: str):
    """Guardar motor de búsqueda en archivo"""
    with open(path, 'wb') as f:
        pickle.dump({
            'codebook_builder': self.codebook_builder,
            'records': self.records,
            'histograms': self.histograms,
            'weighted_histograms': self.weighted_histograms,
            'inverted_index': self.inverted_index,  # ← Índice invertido
            'bow': self.bow
        }, f)
```

## **Ejecución eficiente de consultas utilizando similitud del coseno**

```python
def knn_inverted_index(self, query_path: str, k: int = 10):
    # 1. Extraer características de la consulta
    query_features = FeatureExtractor.extract_features_image(query_path, self.feature_extractor_method)
    
    # 2. Convertir a histograma ponderado
    query_histogram = self.bow.compute_histogram(query_features)
    query_weighted = query_histogram * np.log(self.bow.n_documents / self.bow.document_frequency)
    
    # 3. Acumular puntuaciones usando índice invertido
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
```

- **Normalización coseno y ranking**

```python
    # Normalizar puntuaciones (similitud de coseno)
    for doc_idx in doc_scores:
        query_norm = np.sqrt(np.sum(query_weighted**2))
        doc_norm = np.sqrt(np.sum(self.weighted_histograms[doc_idx]**2))
        if query_norm > 0 and doc_norm > 0:
            doc_scores[doc_idx] /= (query_norm * doc_norm)
    
    # Obtener los K mejores resultados
    heap = []
    for doc_idx, score in doc_scores.items():
        if len(heap) < k:
            heapq.heappush(heap, (score, doc_idx))
        elif score > heap[0][0]:
            heapq.heapreplace(heap, (score, doc_idx))
```

### **Ventajas de eficiencia:**

1. **Poda temprana**: Solo evalúa documentos que comparten palabras clave con la consulta
2. **Complejidad reducida**: O(log n) vs O(n) del método secuencial
3. **Cálculo optimizado**: Acumulación directa de puntuaciones TF-IDF

## **Explicación del mecanismo de construcción de índices invertidos en PostgreSQL**

### **1. Índice GIN (Generalized Inverted Index)**

PostgreSQL implementa índices invertidos mediante **GIN**, especialmente para:

- Búsquedas de texto completo (`tsvector`)
- Arrays
- Tipos de datos complejos

### **2. Construcción paso a paso en PostgreSQL**

```sql
-- Crear tabla con columna de texto
CREATE TABLE documentos (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(255),
    contenido TEXT,
    contenido_tsvector TSVECTOR
);

-- Poblar la columna tsvector (preprocesado de texto)
UPDATE documentos 
SET contenido_tsvector = to_tsvector('spanish', contenido);

-- Crear índice GIN
CREATE INDEX idx_documentos_gin 
ON documentos 
USING GIN (contenido_tsvector);
```

### **3. Estructura interna del índice GIN**

GIN Index Structure:
┌─────────────────┐
│   Root Page     │
├─────────────────┤
│ Entry Tree      │  ← Árbol B+ de términos
│ - palabra1      │
│ - palabra2      │

│ - palabra3      │
├─────────────────┤
│ Posting Tree    │  ← Listas de documentos por término
│ palabra1 → [1,5,9,...]
│ palabra2 → [2,3,7,...]
│ palabra3 → [1,4,8,...]
└─────────────────┘

### **4. Proceso de construcción**

```sql
-- PostgreSQL internamente hace esto:

-- 1. Análisis del texto (tokenización, stemming)
SELECT to_tsvector('spanish', 'Los gatos negros corren rápidamente');
-- Resultado: 'gat':1 'negr':2 'corr':3 'rapid':4

-- 2. Para cada término, crear entrada en el índice
INSERT INTO gin_index_entries VALUES ('gat', [doc_ids]);
INSERT INTO gin_index_entries VALUES ('negr', [doc_ids]);
-- etc.

-- 3. Organizar en árbol B+ para acceso eficiente
```

### **5. Consulta eficiente con índice GIN**

```sql
-- Búsqueda usando el operador @@
SELECT id, titulo 
FROM documentos 
WHERE contenido_tsvector @@ to_tsquery('spanish', 'gatos & negros');

-- PostgreSQL internamente:
-- 1. Busca 'gatos' en Entry Tree → obtiene posting list
-- 2. Busca 'negros' en Entry Tree → obtiene posting list  
-- 3. Hace intersección de listas (operador &)
-- 4. Devuelve documentos resultantes
```

### **6. Ranking con similitud**

```sql
-- PostgreSQL puede calcular ranking de relevancia
SELECT id, titulo,
       ts_rank(contenido_tsvector, to_tsquery('spanish', 'gatos & negros')) as ranking
FROM documentos 
WHERE contenido_tsvector @@ to_tsquery('spanish', 'gatos & negros')
ORDER BY ranking DESC;
```

## Índice Invertido para Descriptores Locales

**Construcción del Bag of Visual/Acoustic Words e Implementación de Búsqueda KNN**

## **Proceso de Construcción del Bag of Words**

### **Extracción de Características**

El proceso comienza con la extracción de características usando la clase **`FeatureExtractor`** multimedia.py:14-16 . Para imágenes, utiliza el algoritmo SIFT que extrae descriptores de 128 dimensiones multimedia.py:32-45 . Para audio, emplea MFCC que genera coeficientes de 13 dimensiones multimedia.py:68-78 .

```python
from sklearn.metrics.pairwise import cosine_similarity
import os
import cv2
import librosa
import numpy as np

class FeatureExtractor:
    """Extracción de características de archivos multimedia (imágenes o audio)"""

    @staticmethod
    def extract_features_image(image_path: str, method: str = 'sift') -> np.ndarray:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Archivo de imagen no encontrado: {image_path}")
        
        if method == 'sift':
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                raise ValueError(f"No se pudo leer la imagen: {image_path}")
            sift = cv2.SIFT_create()
            keypoints, descriptors = sift.detectAndCompute(img, None)
            return descriptors if descriptors is not None else np.array([])
        elif method in ['inception', 'resnet']:
            raise NotImplementedError(f"Extracción de características con {method} aún no implementada")
    
    @staticmethod
    def extract_features_audio(audio_path: str, method: str = 'mfcc') -> np.ndarray:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Archivo de audio no encontrado: {audio_path}")
        
        if method == 'mfcc':

```

```python
from sklearn.cluster import KMeans
from typing import List

class CodebookBuilder:
    def __init__(self, n_clusters: int = 100):
        self.n_clusters = n_clusters
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=0)
        self.codebook = None
        self.is_trained = False

    def build(self, features_list: List[np.ndarray]) -> np.ndarray:
        if not features_list:
            raise ValueError("Se proporcionó una lista de características vacía")
        features_list = [f for f in features_list if f is not None and len(f) > 0]
        if not features_list:
            raise ValueError("No se encontraron características válidas")
        
        all_features = np.vstack(features_list)
        if len(all_features) < self.n_clusters:
            self.n_clusters = max(1, len(all_features) // 2)
            self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=0)
        
        self.kmeans.fit(all_features)
        self.codebook = self.kmeans.cluster_centers_
        self.is_trained = True
        return self.codebook

    def save(self, path: str):
        # Placeholder para guardar el codebook
        pass

```

```python
class BagOfWords:
    def __init__(self, codebook_builder: CodebookBuilder):
        if not codebook_builder.is_trained:
            raise ValueError("El codebook no ha sido entrenado")
        self.codebook_builder = codebook_builder
        self.document_frequency = None
        self.n_documents = 0

    def compute_histogram(self, features: np.ndarray) -> np.ndarray:
        if features is None or len(features) == 0:
            return np.zeros(self.codebook_builder.n_clusters)
        cluster_assignments = self.codebook_builder.kmeans.predict(features)
        histogram = np.zeros(self.codebook_builder.n_clusters)
        for cluster_idx in cluster_assignments:
            histogram[cluster_idx] += 1
        return histogram / np.sum(histogram) if np.sum(histogram) > 0 else histogram

    def compute_tf_idf_weights(self, histogram_list: List[np.ndarray]) -> List[np.ndarray]:
        n_documents = len(histogram_list)
        if n_documents == 0:
            return []
        self.n_documents = n_documents
        self.document_frequency = np.zeros(self.codebook_builder.n_clusters)
        for histogram in histogram_list:
            self.document_frequency += (histogram > 0).astype(int)
        self.document_frequency = np.maximum(self.document_frequency, 1)
        idf = np.log(n_documents / self.document_frequency)
        return [histogram * idf for histogram in histogram_list]

```

```python
from typing import List, Tuple, Dict
import heapq
import time

class MultimediaSearchEngine:
    def __init__(self, feature_extractor_method: str = 'sift', n_clusters: int = 100):
        self.feature_extractor_method = feature_extractor_method
        self.codebook_builder = CodebookBuilder(n_clusters=n_clusters)
        self.bow = None
        self.records = []  # (id, ruta, metadatos)
        self.histograms = []
        self.weighted_histograms = []
        self.inverted_index = {}

    def build_index(self, records: List[Tuple[int, str, Dict]]) -> None:
        self.records = records
        features_list = []
        for _, path, _ in records:
            if path.endswith(('.jpg', '.png')):
                features = FeatureExtractor.extract_features_image(path, self.feature_extractor_method)
            elif path.endswith(('.wav', '.mp3')):
                features = FeatureExtractor.extract_features_audio(path, self.feature_extractor_method)
            else:
                continue
            features_list.append(features)
        
        self.codebook_builder.build(features_list)
        self.bow = BagOfWords(self.codebook_builder)
        self.histograms = [self.bow.compute_histogram(f) for f in features_list]
        self.weighted_histograms = self.bow.compute_tf_idf_weights(self.histograms)
        print("Construyendo índice invertido...")
        self.build_inverted_index()

    def build_inverted_index(self) -> None:
        self.inverted_index = {}
        for codeword_idx in range(self.codebook_builder.n_clusters):
            self.inverted_index[codeword_idx] = []
            for doc_idx, weighted_hist in enumerate(self.weighted_histograms):
                weight = weighted_hist[codeword_idx]
                if weight > 0:
                    self.inverted_index[codeword_idx].append((doc_idx, weight))

```

```python
    def knn_sequential(self, query_path: str, k: int = 10) -> List[Tuple[int, float, Dict]]:
        start_time = time.time()
        if query_path.endswith(('.jpg', '.png')):
            query_features = FeatureExtractor.extract_features_image(query_path, self.feature_extractor_method)
        elif query_path.endswith(('.wav', '.mp3')):
            query_features = FeatureExtractor.extract_features_audio(query_path, self.feature_extractor_method)
        else:
            raise ValueError("Formato no soportado")
        query_hist = self.bow.compute_histogram(query_features)
        if self.bow.document_frequency is not None:
            query_weighted = query_hist * np.log(self.bow.n_documents / self.bow.document_frequency)
        else:
            query_weighted = query_hist

        heap = []
        for i, weighted_hist in enumerate(self.weighted_histograms):
            sim = cosine_similarity([query_weighted], [weighted_hist])[0][0]
            if len(heap) < k:
                heapq.heappush(heap, (sim, i))
            elif sim > heap[0][0]:
                heapq.heapreplace(heap, (sim, i))
        results = sorted(heap, reverse=True)
        print(f"Búsqueda KNN secuencial completada en {time.time() - start_time:.4f} segundos")
        return [(self.records[i][0], sim, self.records[i][2]) for sim, i in results]

```

```python
    def knn_inverted_index(self, query_path: str, k: int = 10) -> List[Tuple[int, float, Dict]]:
        start_time = time.time()
        if query_path.endswith(('.jpg', '.png')):
            query_features = FeatureExtractor.extract_features_image(query_path, self.feature_extractor_method)
        elif query_path.endswith(('.wav', '.mp3')):
            query_features = FeatureExtractor.extract_features_audio(query_path, self.feature_extractor_method)
        else:
            raise ValueError("Formato no soportado")
        query_hist = self.bow.compute_histogram(query_features)
        if self.bow.document_frequency is not None:
            query_weighted = query_hist * np.log(self.bow.n_documents / self.bow.document_frequency)
        else:
            query_weighted = query_hist

        doc_scores = {}
        for codeword_idx, query_weight in enumerate(query_weighted):
            if query_weight > 0 and codeword_idx in self.inverted_index:
                for doc_idx, doc_weight in self.inverted_index[codeword_idx]:
                    doc_scores[doc_idx] = doc_scores.get(doc_idx, 0) + query_weight * doc_weight
        for doc_idx in doc_scores:
            qn = np.linalg.norm(query_weighted)
            dn = np.linalg.norm(self.weighted_histograms[doc_idx])
            if qn > 0 and dn > 0:
                doc_scores[doc_idx] /= (qn * dn)

        heap = []
        for doc_idx, score in doc_scores.items():
            if len(heap) < k:
                heapq.heappush(heap, (score, doc_idx))
            elif score > heap[0][0]:
                heapq.heapreplace(heap, (score, doc_idx))

        results = sorted(heap, reverse=True)
        print(f"Búsqueda KNN con índice invertido completada en {time.time() - start_time:.4f} segundos")
        return [(self.records[i][0], sim, self.records[i][2]) for sim, i in results]

```

### **Construcción del Codebook**

La clase **`CodebookBuilder`** implementa K-means clustering para crear el vocabulario visual/acústico multimedia.py:89-102 . El proceso combina todas las características extraídas en una matriz única y aplica clustering multimedia.py:114-136 . Los centros de clusters resultantes forman el codebook que actúa como diccionario de palabras visuales/acústicas.

```python
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
```

```python
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
```

### **Generación de Histogramas**

La clase **`BagOfWords`** convierte los descriptores de características en representaciones de histograma multimedia.py:161-176 . Cada característica se asigna al cluster más cercano y se cuenta la frecuencia de cada palabra clave multimedia.py:178-204 . El sistema también implementa ponderación TF-IDF para mejorar la discriminación multimedia.py:206-240 .

```python
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
       
```

```python
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
```

```python
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
```

## **Diseño de la Técnica de Indexación**

### **Estructura del Motor de Búsqueda**

El **`MultimediaSearchEngine`** organiza los descriptores mediante dos estructuras principales multimedia.py:243-264 :

```python
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

```

- **Almacenamiento directo**: Arrays de histogramas para búsqueda secuencial
- **Índice invertido**: Mapeo de palabras clave a documentos para búsqueda optimizada

### **Construcción del Índice Invertido**

El índice invertido se construye mapeando cada palabra clave del codebook a los documentos que la contienen multimedia.py:313-325 . Esta estructura permite acceso directo a documentos relevantes durante la búsqueda, evitando comparaciones exhaustivas.

```python
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
```

### **Integración con el Sistema de Base de Datos**

Las clases **`MultimediaSequentialIndex`** y **`MultimediaInvertedIndex`** integran el motor de búsqueda con el esquema de base de datos multimediatree.py:144-157 y multimediatree.py:184-197 . Estas clases manejan la persistencia del índice y la sincronización con los datos de la tabla.

```python
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
```

```python
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
```

## **Implementación de Búsqueda KNN**

### **Búsqueda Secuencial**

El método **`knn_sequential`** implementa búsqueda exhaustiva comparando el histograma de consulta con todos los histogramas indexados multimedia.py:327-383

```python
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
```

Utiliza similitud de coseno y un heap para mantener los k mejores resultados multimedia.py:357-372 .

```python
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
```

### **Búsqueda con Índice Invertido**

El método **`knn_inverted_index`** optimiza la búsqueda utilizando el índice invertido multimedia.py:385-456

```python
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
```

 Solo procesa documentos que comparten palabras clave con la consulta, acumulando puntuaciones ponderadas multimedia.py:415-435 .

```python
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
        
```

### **Comparación de Rendimiento**

La búsqueda secuencial tiene complejidad O(n) pero garantiza resultados óptimos, mientras que la búsqueda indexada ofrece complejidad promedio O(log n) con resultados aproximados mnist_test.py:128-131 y audio_test.py:202-204.

```python
    # Realizar búsqueda con índice invertido (más eficiente para grandes datasets)
        print("Realizando búsqueda de las 10 imágenes más similares...")
        k = 10  # Buscar las 10 imágenes más similares
        results = engine.knn_inverted_index(test_image_path, k=k)
```

```python
 if len(engine.records) >= 5:
                print("\nRealizando búsqueda con índice invertido...")
                results_inverted = engine.knn_inverted_index(test_audio_file, k=k)
```

## **Análisis del Impacto de la Maldición de la Dimensionalidad y Estrategias para Mitigarla**

## **Impacto de la Maldición de la Dimensionalidad**

### **Características de Alta Dimensión en el Sistema**

El sistema de MiyazakiDB maneja características de alta dimensión que son susceptibles a la maldición de la dimensionalidad :

**Para imágenes**: Los descriptores SIFT generan vectores de 128 dimensiones por keypoint multimedia.py:32-45 . Una imagen típica puede generar cientos o miles de keypoints, creando un espacio de características extremadamente disperso.

```python
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
```

**Para audio**: Los coeficientes MFCC extraen 13 dimensiones por frame temporal multimedia.py:68-78 . Con múltiples frames por archivo de audio, el espacio dimensional se expande significativamente.

```python
 if method == 'mfcc':
# Cargar archivo de audio
            y, sr = librosa.load(audio_path, sr=None)

# Extraer coeficientes MFCC
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)

# Transponer para obtener características en filas
            mfccs = mfccs.T

            return mfccs
```

## **Estrategias de Mitigación Implementadas**

### **1. Reducción Dimensional mediante Clustering**

**Bag of Words como Técnica de Cuantización**

El sistema implementa una estrategia fundamental de reducción dimensional a través del **`CodebookBuilder`** multimedia.py:89-102 :

```python
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
```

- **K-means clustering**: Agrupa características similares en clusters, reduciendo el espacio dimensional de miles de descriptores individuales a un vocabulario fijo de **`n_clusters`** palabras visuales/acústicas.

- **Cuantización adaptativa**: El sistema ajusta automáticamente el número de clusters cuando hay insuficientes características multimedia.py:126-129 .

```python
    if len(all_features) < self.n_clusters:
# Si tenemos menos vectores de características que clusters, reducir el número de clusters
            self.n_clusters = max(1, len(all_features) // 2)
            self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=0)
```

### **2. Representación Histográfica Normalizada**

**Conversión a Espacio de Características Fijo**

La clase **`BagOfWords`** transforma descriptores de longitud variable en histogramas de dimensión fija multimedia.py:178-204 :

```python
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
```

- **Normalización L1**: Los histogramas se normalizan para sumar 1, creando distribuciones de probabilidad que son más robustas a variaciones de escala.
- **Manejo de características vacías**: El sistema maneja graciosamente casos donde no se pueden extraer características, devolviendo histogramas de ceros.

### **3. Ponderación TF-IDF para Discriminación**

**Mejora de la Relevancia Semántica**

El sistema implementa ponderación TF-IDF para mitigar el problema de características comunes que dominan el espacio multimedia.py:206-240 :

```python
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
```

- **Inverse Document Frequency**: Reduce el peso de palabras visuales/acústicas que aparecen frecuentemente en muchos documentos.
- **Term Frequency**: Mantiene la importancia relativa de características dentro de cada documento.

## FRONTEND: Interfaz Gráfica con Streamlit

La aplicación utiliza **Streamlit** para ofrecer una experiencia interactiva, dividida en varias vistas y páginas:

### 1. Navegación y Estructura

- **Sidebar**
• Selector de modo: **SQL**, **Multimedia**, **Texto**.
• Parámetros globales: tabla y columna multimedia, método de indexado, Top-K.
- **Multi-page Layout**
• `app.py` → Vista principal (SQL genérico, búsqueda multimedia y texto).
• `audio_visualizer_app.py` → **Audio Visualizer & Comparator** con waveform, espectrograma, MFCCs y comparación lado a lado.

### 2. Modo SQL

- Área de texto para consultas arbitrarias.
- Ejemplos rápidos con un click.
- Visualización de resultados en `st.dataframe()`.
- Métricas: total registros, mensaje y tiempo de ejecución.

### 3. Modo Multimedia

- **Selección de archivo**
– De carpeta local (`media_queries` ó `img_queries`)
– O subida directa con drag & drop.
- **Población de tabla** (“Será Multimedia”): inserta todos los archivos de la carpeta correspondiente.
- **Construcción de índice** 🔧: secuencial o invertido.
- **Búsqueda y reproducción** 🔍
– Envío del archivo de consulta al backend
– Resultados en tabla y reproducción con `st.audio()` (audio) o `st.image()` (imágenes)

### 4. Modo Texto

- Inserción de documentos vía textarea o subida de fichero.
- Construcción y finalización de índice de texto.
- Búsqueda con parámetros Top-K y despliegue de snippets.

### 5. Audio Visualizer & Comparator

- **Waveform** básica e interactiva con marcadores de tiempo.
- **Espectrograma**, **Mel-spectrograma** y **MFCC**.
- Comparación Lado a Lado de dos audios: MFCCs, espectrogramas o métricas básicas.
- Controles de ventana y zoom para análisis detallado.

---

**Tecnologías:** Streamlit · pandas · requests · librosa · matplotlib

### 📚 Mini-Manual de Usuario

🚀 Inicio Rápido
Paso 1: Ejecutar la Aplicación

```python
# Desde el directorio raf/
streamlit run app.py
```

### **Paso 2: Acceso a la Aplicación**

1. Abrir navegador web
2. La interfaz principal se cargará automáticamente

### **📋 Funcionalidades Principales**

### **1. Gestión de Archivos Multimedia**

**Subir Archivos:**

```python
# Interfaz para subir archivos
uploaded_file = st.file_uploader(
    "Selecciona archivo multimedia",
    type=['jpg', 'jpeg', 'png', 'wav', 'mp3', 'ogg']
)
```

**Funciones disponibles:**

- ✅ Subir imágenes (JPG, PNG, BMP)
- ✅ Subir audio (WAV, MP3, OGG)
- ✅ Vista previa automática
- ✅ Validación de formato

### **2. Visualización de Audio**

**Audio Visualizer (`pages/audio_visualizer_app.py`):**

def create_audio_visualizer():
st.title("🎵 Visualizador de Audio")

```python
# Upload de archivo de audio
audio_file = st.file_uploader("Subir archivo de audio", type=['wav', 'mp3'])

if audio_file:
    # Mostrar reproductor
    st.audio(audio_file)

    # Análisis espectral
    show_spectrogram(audio_file)
    show_mfcc_features(audio_file)

```

**Características del Visualizador:**

- 🎵 Reproductor de audio integrado
- 📈 Espectrograma en tiempo real
- 🔊 Análisis MFCC
- 📊 Gráficos interactivos con Plotly

### **🔧 Operaciones Paso a Paso**

### **Operación 1: Subir y Indexar Archivo Multimedia**

1. **Seleccionar Página Principal**
    - Usar sidebar para navegar a "Subir Multimedia"
2. **Subir Archivo**

```python
# Widget de subida
uploaded_file = st.file_uploader(
    "📁 Arrastra tu archivo aquí",
    type=['jpg', 'jpeg', 'png', 'wav', 'mp3']
)
```

1. **Confirmación**
    - Sistema muestra vista previa
    - Confirmar tipo de archivo detectado
    - Hacer clic en "Indexar Archivo"
2. **Resultado**
    - Barra de progreso durante indexación
    - Mensaje de confirmación
    - Archivo disponible para consultas

### **Operación 2: Realizar Búsqueda por Similitud**

1. **Ir a Panel de Consultas**
    - Sidebar → "Consultas SQL"
2. **Escribir Consulta**

```sql
SELECT id, filename 
FROM multimedia 
WHERE image_column <-> 'C:/ruta/consulta.jpg' 
LIMIT 5;
```

1. **Ejecutar**
    - Botón "▶️ Ejecutar Consulta"
    - Resultados aparecen en tabla interactiva
2. **Analizar Resultados**
    - Tabla con columnas de similitud
    - Opción de descargar resultados
    - Vista previa de archivos encontrados

### **Operación 3: Visualizar Características de Audio**

1. **Navegar a Audio Visualizer**
    - Sidebar → "Visualizador de Audio"
2. **Cargar Archivo**
    - Drag & drop de archivo de audio
    - O usar file_uploader
3. **Explorar Visualizaciones**
    - **Espectrograma**: Frecuencias vs tiempo
    - **MFCC**: Coeficientes cepstrales
    - **Waveform**: Forma de onda temporal

### **⚙️ Configuraciones Avanzadas**

### **Configuración de Índices**

```python
# Panel de configuración
index_type = st.selectbox(
    "Tipo de Índice",
    ["Secuencial", "Invertido"]
)

similarity_threshold = st.slider(
    "Umbral de Similitud",
    0.0, 1.0, 0.7
)
```

**Parámetros de Búsqueda**

```python
# Configuración K-NN
k_neighbors = st.number_input(
    "Número de vecinos (K)",
    min_value=1, max_value=50, value=10
)

# Método de características
feature_method = st.radio(
    "Método de Extracción",
    ["SIFT", "ORB", "MFCC", "Spectrogram"]
)
```

## **Capturas de Pantalla del Sistema**

![Image](https://github.com/user-attachments/assets/ac21ba61-4185-439c-aea1-64ccac60d8ce)
![Image](https://github.com/user-attachments/assets/d7f6ddb3-ff1a-4c98-99fb-b68295c2dc2c)