# README - Sistema de Búsqueda Multimedia con KNN

## 📋 Descripción General

Se desarrolla un sistema especializado de búsqueda por similitud para contenido multimedia implementando algoritmos K-Nearest Neighbors (KNN) tanto secuencial como con índice invertido. Esta implementación se enfoca en el procesamiento eficiente de imágenes y audio mediante técnicas avanzadas de extracción de características.

## 🔍 Implementación de Algoritmos KNN

### KNN Secuencial
**Ubicación**: `engine/multimedia.py` - método `knn_sequential()`

Ejecuta búsqueda exhaustiva mediante comparación directa de la consulta con todos los documentos indexados. Utiliza similitud de coseno aplicada sobre histogramas ponderados con TF-IDF para identificar los k vecinos más relevantes.

```python
def knn_sequential(self, query_path: str, k: int = 10) -> List[Tuple[int, float, Dict]]:
    # Extrae características de la consulta
    # Calcula histograma y aplica ponderación TF-IDF
    # Compara con todos los documentos usando similitud de coseno
    # Retorna k vecinos ordenados por similitud descendente
```

### KNN con Índice Invertido
**Ubicación**: `engine/multimedia.py` - método `knn_inverted_index()`

Implementa búsqueda optimizada mediante índice invertido construido sobre palabras visuales y auditivas (codewords). El índice mapea cada característica a los documentos que la contienen, reduciendo significativamente el espacio de búsqueda.

```python
def build_inverted_index(self) -> None:
    # Mapea codeword_idx -> [(doc_idx, weight), ...]
    # Optimiza consultas al filtrar documentos relevantes
    # Acelera búsquedas en datasets grandes
```

## 🎯 Procesamiento Multimedia

### Imágenes
- **Formatos**: JPG, JPEG, PNG, BMP
- **Extractor**: SIFT (Scale-Invariant Feature Transform)
- **Características**: Descriptores robustos invariantes a transformaciones geométricas

### Audio
- **Formatos**: WAV, MP3, OGG
- **Extractor**: MFCC (Mel-Frequency Cepstral Coefficients)
- **Características**: Coeficientes espectrales para análisis tímbrico

## 🏗️ Arquitectura del Sistema

### Motor de Búsqueda (`MultimediaSearchEngine`)
Núcleo del sistema que coordina extracción de características, construcción de vocabulario visual/auditivo y ejecución de algoritmos de búsqueda.

```python
class MultimediaSearchEngine:
    def __init__(self, feature_extractor_method='sift', n_clusters=64):
        self.codebook_builder = CodebookBuilder(n_clusters=n_clusters)
        self.bow = BagOfWords()
        self.inverted_index = {}
        self.weighted_histograms = []
```

### Índices Multimedia (`indexes/multimediatree.py`)
- **`MultimediaSequentialIndex`**: Implementación KNN secuencial para precisión máxima
- **`MultimediaInvertedIndex`**: Implementación KNN invertido para eficiencia escalable
- **Base común**: `MultimediaIndexBase` proporciona funcionalidad compartida

### Integración de Tipos (`engine/model.py`)
```python
class DataType(Enum):
    IMAGE = auto()  # Archivos de imagen
    AUDIO = auto()  # Archivos de audio

class IndexType(Enum):
    MULTIMEDIA_SEQUENTIAL = auto()  # KNN secuencial
    MULTIMEDIA_INVERTED = auto()    # Índice invertido
```

## 🔧 Funciones Principales

### Búsqueda por Similitud
```python
def similarity_search(self, query_path: str, k: int = 10) -> list:
    """
    Ejecuta búsqueda KNN según configuración del índice
    
    Args:
        query_path: Archivo de consulta multimedia
        k: Número de vecinos similares a recuperar
        
    Returns:
        Lista ordenada de (record_id, similitud, metadatos)
    """
```

### Pipeline de Construcción
El sistema automatiza la construcción del índice mediante:
1. Extracción masiva de características multimedia
2. Clustering K-means para generar vocabulario (codebook)
3. Construcción de histogramas Bag-of-Words
4. Aplicación de esquema de ponderación TF-IDF
5. Generación de índice invertido para optimización

## 📊 Optimización y Configuración

### Configuración Adaptativa
```python
# Ajuste dinámico según características del dataset
n_clusters = min(256, total_files // 100)  # Un cluster por cada ~100 archivos
n_clusters = max(2, n_clusters)           # Mínimo 2 clusters garantizado
```

### Métricas de Similitud
- **Similitud de coseno**: Métrica principal para comparación de histogramas normalizados
- **Ponderación TF-IDF**: Amplifica características discriminativas y reduce ruido
- **Normalización L2**: Garantiza comparaciones equitativas entre documentos

## 🧪 Validación y Testing

### Tests de Imágenes (`tests/image/mnist_test.py`)
Valida funcionalidad con dataset MNIST, evaluando extracción SIFT y búsqueda KNN en colecciones de gran escala.

### Tests de Audio (`tests/audio/audio_test.py`)
Verifica extracción MFCC y algoritmos de búsqueda, comparando rendimiento entre métodos secuencial e invertido en archivos de audio diversos.

## 🚀 Análisis de Rendimiento

### KNN Secuencial
- **Complejidad temporal**: O(n) donde n representa documentos totales
- **Uso recomendado**: Datasets pequeños (< 1000 elementos)
- **Ventaja**: Precisión máxima sin pérdida de información

### KNN Índice Invertido
- **Complejidad temporal**: O(log n) en promedio
- **Uso recomendado**: Datasets grandes (> 1000 elementos)
- **Ventaja**: Escalabilidad superior y eficiencia computacional

## 🔗 Integración SQL

El sistema soporta consultas KNN nativas mediante extensiones SQL:

```sql
SELECT * FROM multimedia_table 
WHERE media_column KNN (query_file, k_neighbors);
```

**Parser SQL**: Token KNN reconocido en `parser/scanner.py` para procesamiento de consultas multimedia especializadas.

## 📝 Características Técnicas Destacadas

1. **Robustez**: Manejo comprehensivo de errores durante extracción y validación de formatos
2. **Persistencia**: Serialización eficiente de índices via pickle para reutilización
3. **Escalabilidad**: Configuración automática de parámetros según características del dataset
4. **Flexibilidad**: Soporte multiplataforma para formatos multimedia estándar
5. **Integración**: Conexión seamless con motor de base de datos y arquitectura de índices

## 📊 Métricas de Evaluación

La implementación incluye sistema de timing y logging para análisis de rendimiento, permitiendo evaluación comparativa entre algoritmos KNN secuencial e invertido según características específicas del dataset.

REPOSITORIO: https://github.com/MiyazakiDB/BD2-Project1.git
---

