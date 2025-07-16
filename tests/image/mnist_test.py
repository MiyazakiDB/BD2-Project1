import os
import sys
import cv2
import numpy as np
import tempfile
import shutil
import glob

# Añadir el directorio raíz al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from engine.multimedia import FeatureExtractor, CodebookBuilder, MultimediaSearchEngine

def test_feature_extraction():
    """Prueba la extracción de características de imágenes"""
    # Crear directorio temporal
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Crear una imagen de prueba
        test_image_path = os.path.join(temp_dir, 'test_image.jpg')
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        # Dibujar algunas formas para que SIFT tenga puntos de interés
        cv2.rectangle(img, (10, 10), (90, 90), (255, 255, 255), 2)
        cv2.circle(img, (50, 50), 25, (200, 200, 200), -1)
        cv2.imwrite(test_image_path, img)
        
        # Extraer características
        features = FeatureExtractor.extract_features_image(test_image_path)
        
        # Verificar que se hayan extraído características
        if features is None or len(features) == 0:
            print("ERROR: No se extrajeron características de la imagen")
            return False
        
        print(f"Éxito: Se extrajeron {len(features)} características de la imagen")
        return True
    
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False
    
    finally:
        # Limpiar
        shutil.rmtree(temp_dir)

def test_codebook_creation():
    """Prueba la creación de un codebook"""
    try:
        # Crear datos de prueba (descriptores de características simulados)
        test_features1 = np.random.rand(20, 128)  # 20 descriptores SIFT simulados
        test_features2 = np.random.rand(30, 128)  # 30 descriptores SIFT simulados
        
        # Crear codebook
        codebook_builder = CodebookBuilder(n_clusters=10)
        codebook = codebook_builder.build([test_features1, test_features2])
        
        # Verificar que se haya creado el codebook
        if codebook is None or not codebook_builder.is_trained:
            print("ERROR: No se pudo crear el codebook")
            return False
        
        print(f"Éxito: Se creó un codebook con {codebook_builder.n_clusters} clusters")
        return True
    
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def test_mnist_search():
    """Compara una imagen específica con el dataset MNIST"""
    # Rutas de archivos
    test_image_path = r"datasets\mnist_dataset\test_image\test_image.jpg"
    mnist_dataset_path = r"datasets\mnist_dataset\numbers"
    
    try:
        # Verificar que la imagen de prueba existe
        if not os.path.exists(test_image_path):
            print(f"ERROR: La imagen de prueba no existe en {test_image_path}")
            return False
            
        # Verificar que el directorio del dataset existe
        if not os.path.exists(mnist_dataset_path):
            print(f"ERROR: El directorio del dataset MNIST no existe en {mnist_dataset_path}")
            return False
            
        # Obtener todas las imágenes del dataset
        print("Buscando imágenes en el dataset MNIST...")
        mnist_images = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif']:
            mnist_images.extend(glob.glob(os.path.join(mnist_dataset_path, '**', ext), recursive=True))
        
        total_images = len(mnist_images)
        print(f"Se encontraron {total_images} imágenes en el dataset MNIST")
        
        if total_images == 0:
            print("ERROR: No se encontraron imágenes en el dataset MNIST")
            return False
            
        # Crear registros para el motor de búsqueda
        print("Preparando registros para el motor de búsqueda...")
        records = []
        for i, path in enumerate(mnist_images):
            # Extraer el nombre del archivo sin la extensión para usarlo como metadato
            filename = os.path.basename(path)
            name_without_ext = os.path.splitext(filename)[0]
            records.append((i, path, {"nombre": name_without_ext}))
            
            # Mostrar progreso cada 1000 imágenes
            if i % 1000 == 0 and i > 0:
                print(f"Procesadas {i}/{total_images} imágenes...")
        
        # Crear motor de búsqueda
        print("\nCreando motor de búsqueda multimedia...")
        # Usar un número adecuado de clusters para un dataset grande
        n_clusters = min(256, total_images // 100)  # Un cluster por cada ~100 imágenes, máximo 256
        engine = MultimediaSearchEngine(feature_extractor_method='sift', n_clusters=n_clusters)
        
        # Construir índice
        print(f"Construyendo índice con {n_clusters} clusters...")
        engine.build_index(records)
        
        # Verificar que se haya construido el índice
        if len(engine.records) != total_images or len(engine.histograms) != total_images:
            print("ERROR: No se pudo construir el índice correctamente")
            return False
            
        # Realizar búsqueda con índice invertido (más eficiente para grandes datasets)
        print("Realizando búsqueda de las 10 imágenes más similares...")
        k = 10  # Buscar las 10 imágenes más similares
        results = engine.knn_inverted_index(test_image_path, k=k)
        
        # Verificar resultados
        if len(results) < 1:
            print("ERROR: La búsqueda no devolvió resultados")
            return False
            
        # Mostrar resultados
        print("\nResultados de la búsqueda:")
        print(f"Imagen de consulta: {test_image_path}")
        print("\nImágenes más similares del dataset MNIST:")
        for i, (record_id, similarity, metadata) in enumerate(results):
            img_path = mnist_images[record_id]
            print(f"#{i+1}: ID={record_id}, Similitud={similarity:.4f}, Nombre={metadata.get('nombre', 'N/A')}")
            print(f"   Ruta: {img_path}")
            
        return True
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def run_all_tests():
    """Ejecuta todas las pruebas"""
    print("=== Prueba de extracción de características ===")
    test_feature_extraction()
    
    print("\n=== Prueba de creación de codebook ===")
    test_codebook_creation()
    
    print("\n=== Prueba de búsqueda en dataset MNIST ===")
    test_mnist_search()

if __name__ == "__main__":
    # Ejecutar todas las pruebas
    run_all_tests()