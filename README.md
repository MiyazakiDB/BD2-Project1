# MiyazakiDB - Sistema de Gestión de Base de Datos Multimodal

![Proyecto de Base de Datos](https://img.shields.io/badge/Base_de_Datos-Proyecto-blue)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)
![React](https://img.shields.io/badge/React-18.2+-blue)

## 📋 Reporte Técnico

**MiyazakiDB** es un sistema de gestión de base de datos (SGBD) multimodal desarrollado como proyecto académico que implementa técnicas avanzadas de indexación, búsqueda y procesamiento de datos multimedia. El sistema está diseñado para manejar eficientemente datos textuales, imágenes y audio mediante estructuras de datos especializadas y algoritmos de búsqueda por similitud.

### 🎯 Objetivos del Proyecto

- Implementar un SGBD con soporte para datos multimodales (texto, imagen, audio)
- Desarrollar múltiples estructuras de indexación (AVL, B+Tree, Hash Extensible, R-Tree, ISAM)
- Crear un sistema de búsqueda por similitud usando TF-IDF y algoritmos KNN
- Diseñar una arquitectura completa con backend FastAPI y frontend React

## 🏗️ Arquitectura del Sistema

### Componentes Principales

#### 1. **Motor de Base de Datos** (`/engine`)
- **DBManager**: Gestor principal que implementa el patrón Singleton para operaciones CRUD
- **Model**: Define esquemas de tablas, tipos de datos y tipos de índices
- **Record**: Manejo de registros y archivos de datos
- **Multimedia**: Motor de búsqueda para contenido multimedia

#### 2. **Estructuras de Indexación** (`/indexes`)
- **AVL Tree**: Árbol auto-balanceado para búsquedas eficientes
- **B+Tree**: Índice optimizado para rangos con factor de bloque configurable
- **Hash Extensible**: Tabla hash dinámica para acceso directo
- **R-Tree**: Índice espacial para datos geométricos
- **ISAM**: Índice secuencial indexado para acceso ordenado
- **Índices Multimedia**: Especializados para búsqueda KNN en imágenes y audio

#### 3. **Analizador SQL** (`/parser`)
- **Scanner**: Analizador léxico para tokens SQL
- **Parser**: Analizador sintáctico que construye AST
- **Interpreter**: Ejecutor de consultas SQL

#### 4. **API Backend** (`/backend`)
- **FastAPI**: Framework web asíncrono para APIs REST
- **Autenticación**: Sistema JWT para seguridad
- **Routers**: Endpoints especializados para archivos, consultas y autenticación
- **Búsqueda de Texto**: API completa para indexación y búsqueda de documentos

#### 5. **Frontend** (`/frontend`)
- **React**: Interfaz web interactiva
- **Componentes Modulares**: Auth, Files, Query, Metrics, Tables
- **Visualización**: Gráficos y métricas de rendimiento

## 🔧 Características Técnicas

### Tipos de Datos Soportados
```python
class DataType(Enum):
    INT = auto()
    FLOAT = auto()
    VARCHAR = auto()
    DATE = auto()
    BOOL = auto()
    POINT = auto()
    IMAGE = auto()    # Archivos de imagen
    AUDIO = auto()    # Archivos de audio
```

### Tipos de Índices Implementados
```python
class IndexType(Enum):
    AVL = auto()                      # Árbol AVL
    ISAM = auto()                     # ISAM
    HASH = auto()                     # Hash Extensible
    BTREE = auto()                    # B+Tree
    RTREE = auto()                    # R-Tree
    MULTIMEDIA_SEQUENTIAL = auto()     # KNN Secuencial
    MULTIMEDIA_INVERTED = auto()       # Índice Invertido
```

### Búsqueda Multimedia
- **Extracción de Características**: SIFT para imágenes, MFCC para audio
- **Algoritmo KNN**: Búsqueda de k vecinos más cercanos
- **Métricas de Similitud**: Distancia euclidiana y coseno

### Búsqueda de Texto
- **Índice Invertido**: Implementación custom con TF-IDF
- **Preprocesamiento**: Tokenización, eliminación de stopwords, stemming
- **Soporte Multiidioma**: Español e inglés
- **Búsqueda por Similitud**: Coseno similarity con ranking

## 📊 Rendimiento y Optimización

### Complejidades Temporales
- **AVL Tree**: O(log n) para búsqueda, inserción y eliminación
- **B+Tree**: O(log n) con factor de bloque optimizado para E/S
- **Hash Extensible**: O(1) promedio para operaciones básicas
- **R-Tree**: O(log n) para consultas espaciales

### Optimizaciones Implementadas
- **Lazy Loading**: Carga diferida de índices
- **Caching**: Almacenamiento en memoria de nodos frecuentes
- **Serialización Binaria**: Uso de pickle para persistencia eficiente
- **Vectorización**: NumPy para operaciones matemáticas

## 🚀 Instalación y Configuración

### Requisitos del Sistema
- Python 3.8+
- Node.js 16+
- pip y npm
- Espacio en disco: 500MB mínimo

### Instalación Rápida

1. **Clonar repositorio**
   ```bash
   git clone https://github.com/MiyazakiDB/BD2-Project1.git
   cd BD2-Project1
   ```

2. **Configurar entorno Python**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```

3. **Configurar frontend**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Inicializar sistema**
   ```bash
   # Backend
   python backend/main.py
   
   # Frontend (nueva terminal)
   cd frontend && npm start
   ```

### Configuración de NLTK (para búsqueda de texto)
```bash
python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt')"
```

## 🧪 Pruebas y Demos

### Pruebas de Multimedia
```bash
# Prueba con dataset MNIST
python tests/image/mnist_test.py

# Prueba con archivos de audio
python tests/audio/audio_test.py
```

### Demo de Búsqueda de Texto
```bash
# API standalone
python text_search_api.py

# Demo completo
python complete_demo.py
```

### Pruebas de Índices
```bash
# Prueba específica de AVL
python -c "from indexes.avltree import AVLTree; # test code"

# Prueba de B+Tree
python -c "from indexes.bplustree import BPlusTree; # test code"
```

## 📈 Casos de Uso

### 1. Base de Datos Multimedia
```sql
CREATE TABLE multimedia_content (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    image_path IMAGE INDEX MULTIMEDIA_SEQUENTIAL,
    audio_path AUDIO INDEX MULTIMEDIA_INVERTED
);

-- Búsqueda por similitud de imagen
SELECT * FROM multimedia_content 
WHERE image_path <-> '/path/to/query_image.jpg' 
LIMIT 5;
```

### 2. Sistema de Documentos
```python
# Indexar documento
client.upload_text(
    text="Contenido del documento",
    metadata={"categoria": "tecnologia"}
)

# Buscar documentos similares
results = client.search("consulta de búsqueda", k=10)
```

### 3. Análisis Geoespacial
```sql
CREATE TABLE locations (
    id INT PRIMARY KEY,
    name VARCHAR(50),
    coordinates POINT INDEX RTREE
);
```

## 🔍 Métricas de Rendimiento

### Benchmarks de Índices
- **Inserción**: AVL vs B+Tree vs Hash
- **Búsqueda**: Comparación de tiempos de respuesta
- **Memoria**: Utilización por tipo de índice
- **E/O**: Operaciones de disco por consulta

### Métricas de Búsqueda Multimedia
- **Precisión**: Relevancia de resultados KNN
- **Recall**: Cobertura de búsqueda
- **Tiempo de Respuesta**: Latencia por consulta
- **Throughput**: Consultas por segundo

## 👥 Equipo de Desarrollo

**Grupo 5 - Base de Datos 2**
- Implementación de estructuras de datos avanzadas
- Desarrollo de algoritmos de búsqueda multimedia
- Diseño de arquitectura web full-stack
- Optimización de rendimiento y pruebas

## 📝 Documentación Adicional

- [`TEXT_SEARCH_README.md`](TEXT_SEARCH_README.md): Documentación detallada de búsqueda de texto
- [`tests/README.md`](tests/README.md): Guía de pruebas multimedia
- [`/engine`](engine/): Documentación del motor de base de datos
- [`/indexes`](indexes/): Implementación de estructuras de indexación

## 🔗 Enlaces de Interés

- **Documentación API**: `http://localhost:8000/docs` (Swagger UI)
- **Interfaz Web**: `http://localhost:3000`
- **API de Búsqueda**: `http://localhost:8001` (Standalone)

---

*Este proyecto demuestra la implementación práctica de conceptos avanzados de bases de datos, incluyendo indexación multidimensional, búsqueda por similitud y procesamiento de datos multimodales en un entorno de producción web.*
