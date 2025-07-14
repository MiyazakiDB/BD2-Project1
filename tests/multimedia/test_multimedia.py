import os
import sys
import unittest
import shutil
import numpy as np
import cv2
import librosa
import tempfile
import pickle

# Añadir el directorio raíz al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from engine.multimedia import FeatureExtractor, CodebookBuilder, BagOfWords, MultimediaSearchEngine
from engine.model import TableSchema, Column, DataType, IndexType
from indexes.multimediatree import MultimediaSequentialIndex, MultimediaInvertedIndex

class TestMultimediaFeatureExtraction(unittest.TestCase):
    """Prueba la extracción de características de archivos multimedia"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        # Crear directorio temporal para archivos de prueba
        self.test_dir = tempfile.mkdtemp()
        
        # Crear una imagen de prueba
        self.test_image_path = os.path.join(self.test_dir, 'test_image.jpg')
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        # Dibujar algunas formas para que SIFT tenga puntos de interés
        cv2.rectangle(img, (10, 10), (90, 90), (255, 255, 255), 2)
        cv2.circle(img, (50, 50), 25, (200, 200, 200), -1)
        cv2.imwrite(self.test_image_path, img)
        
        # Crear un archivo de audio de prueba
        self.test_audio_path = os.path.join(self.test_dir, 'test_audio.wav')
        # Generar una señal de audio simple
        sr = 22050  # Tasa de muestreo
        duration = 2.0  # Duración en segundos
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        # Generar una señal de audio con dos frecuencias
        audio = 0.5 * np.sin(2 * np.pi * 440 * t) + 0.5 * np.sin(2 * np.pi * 880 * t)
        # Normalizar
        audio = audio / np.max(np.abs(audio))
        # Guardar como WAV
        librosa.output.write_wav(self.test_audio_path, audio, sr)
    
    def tearDown(self):
        """Limpieza después de las pruebas"""
        # Eliminar directorio temporal y archivos
        shutil.rmtree(self.test_dir)
    
    def test_image_feature_extraction(self):
        """Prueba la extracción de características de imágenes"""
        features = FeatureExtractor.extract_features_image(self.test_image_path)
        self.assertIsInstance(features, np.ndarray)
        self.assertGreater(len(features), 0)  # Debería encontrar al menos algunos puntos clave
    
    def test_audio_feature_extraction(self):
        """Prueba la extracción de características de audio"""
        features = FeatureExtractor.extract_features_audio(self.test_audio_path)
        self.assertIsInstance(features, np.ndarray)
        self.assertGreater(len(features), 0)
        
    def test_invalid_file_path(self):
        """Prueba el manejo de rutas de archivo inválidas"""
        with self.assertRaises(FileNotFoundError):
            FeatureExtractor.extract_features_image("ruta_no_existente.jpg")
        
        with self.assertRaises(FileNotFoundError):
            FeatureExtractor.extract_features_audio("ruta_no_existente.wav")


class TestMultimediaCodebook(unittest.TestCase):
    """Prueba la construcción de codebooks para representación BoW"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        # Crear datos de prueba (descriptores de características simulados)
        self.test_features1 = np.random.rand(20, 128)  # 20 descriptores SIFT simulados
        self.test_features2 = np.random.rand(30, 128)  # 30 descriptores SIFT simulados
    
    def test_codebook_creation(self):
        """Prueba la creación de un codebook"""
        codebook_builder = CodebookBuilder(n_clusters=10)
        codebook = codebook_builder.build([self.test_features1, self.test_features2])
        
        self.assertIsInstance(codebook, np.ndarray)
        self.assertEqual(codebook.shape, (10, 128))  # 10 clusters, 128 dimensiones
        self.assertTrue(codebook_builder.is_trained)
    
    def test_codebook_save_load(self):
        """Prueba guardar y cargar un codebook"""
        codebook_builder = CodebookBuilder(n_clusters=10)
        codebook_builder.build([self.test_features1, self.test_features2])
        
        # Guardar codebook
        save_path = os.path.join(tempfile.gettempdir(), 'test_codebook.pkl')
        codebook_builder.save(save_path)
        
        # Cargar codebook
        loaded_codebook = CodebookBuilder.load(save_path)
        
        self.assertTrue(loaded_codebook.is_trained)
        self.assertEqual(loaded_codebook.n_clusters, 10)
        np.testing.assert_array_equal(loaded_codebook.codebook, codebook_builder.codebook)
        
        # Limpiar
        os.remove(save_path)


class TestMultimediaSearchEngine(unittest.TestCase):
    """Prueba el motor de búsqueda multimedia"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        # Crear directorio temporal para archivos de prueba
        self.test_dir = tempfile.mkdtemp()
        
        # Crear varias imágenes de prueba
        self.image_paths = []
        for i in range(5):
            img_path = os.path.join(self.test_dir, f'test_image_{i}.jpg')
            img = np.zeros((100, 100, 3), dtype=np.uint8)
            # Crear patrones diferentes para cada imagen
            cv2.rectangle(img, (10, 10), (90, 90), (255, 255, 255), 2)
            cv2.circle(img, (50, 50), 10 + i*5, (200, 200, 200), -1)
            cv2.imwrite(img_path, img)
            self.image_paths.append(img_path)
        
        # Crear registros simulados
        self.records = []
        for i, path in enumerate(self.image_paths):
            self.records.append((i, path, {"nombre": f"imagen_{i}", "tamaño": 100 + i*10}))
    
    def tearDown(self):
        """Limpieza después de las pruebas"""
        shutil.rmtree(self.test_dir)
    
    def test_search_engine_creation(self):
        """Prueba la creación del motor de búsqueda"""
        engine = MultimediaSearchEngine(feature_extractor_method='sift', n_clusters=5)
        self.assertEqual(engine.feature_extractor_method, 'sift')
        self.assertEqual(engine.codebook_builder.n_clusters, 5)
    
    def test_index_building(self):
        """Prueba la construcción del índice"""
        engine = MultimediaSearchEngine(feature_extractor_method='sift', n_clusters=5)
        engine.build_index(self.records)
        
        self.assertEqual(len(engine.records), 5)
        self.assertEqual(len(engine.histograms), 5)
        self.assertEqual(len(engine.weighted_histograms), 5)
        self.assertTrue(len(engine.inverted_index) > 0)
    
    def test_sequential_search(self):
        """Prueba la búsqueda KNN secuencial"""
        engine = MultimediaSearchEngine(feature_extractor_method='sift', n_clusters=5)
        engine.build_index(self.records)
        
        # Buscar usando la primera imagen como consulta
        results = engine.knn_sequential(self.image_paths[0], k=3)
        
        self.assertEqual(len(results), 3)
        # La primera imagen debería ser la más similar a sí misma
        self.assertEqual(results[0][0], 0)
    
    def test_inverted_index_search(self):
        """Prueba la búsqueda KNN con índice invertido"""
        engine = MultimediaSearchEngine(feature_extractor_method='sift', n_clusters=5)
        engine.build_index(self.records)
        
        # Buscar usando la primera imagen como consulta
        results = engine.knn_inverted_index(self.image_paths[0], k=3)
        
        self.assertEqual(len(results), 3)
        # La primera imagen debería ser la más similar a sí misma
        self.assertEqual(results[0][0], 0)


class TestMultimediaIndexes(unittest.TestCase):
    """Prueba los índices multimedia"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        # Crear directorio temporal para archivos de prueba
        self.test_dir = tempfile.mkdtemp()
        
        # Crear una imagen de prueba
        self.test_image_path = os.path.join(self.test_dir, 'test_image.jpg')
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.rectangle(img, (10, 10), (90, 90), (255, 255, 255), 2)
        cv2.circle(img, (50, 50), 25, (200, 200, 200), -1)
        cv2.imwrite(self.test_image_path, img)
        
        # Crear esquema de tabla y columna para pruebas
        self.schema = TableSchema("test_table")
        self.column = Column("image_column", DataType.IMAGE, IndexType.MULTIMEDIA_SEQUENTIAL)
        self.schema.add_column(self.column)
        
        # Crear directorio para la tabla de prueba
        os.makedirs(os.path.join("data", "tables", "test_table", "indexes"), exist_ok=True)
    
    def tearDown(self):
        """Limpieza después de las pruebas"""
        shutil.rmtree(self.test_dir)
        # Limpiar directorio de tabla si existe
        table_dir = os.path.join("data", "tables", "test_table")
        if os.path.exists(table_dir):
            shutil.rmtree(table_dir)
    
    def test_sequential_index_creation(self):
        """Prueba la creación de un índice secuencial multimedia"""
        index = MultimediaSequentialIndex(self.schema, self.column)
        self.assertIsNotNone(index.search_engine)
    
    def test_inverted_index_creation(self):
        """Prueba la creación de un índice invertido multimedia"""
        index = MultimediaInvertedIndex(self.schema, self.column)
        self.assertIsNotNone(index.search_engine)


if __name__ == '__main__':
    unittest.main() 