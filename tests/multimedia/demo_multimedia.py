import os
import sys
import argparse
import cv2
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from engine.multimedia import FeatureExtractor, CodebookBuilder, BagOfWords, MultimediaSearchEngine
from engine.model import TableSchema, Column, DataType, IndexType
from indexes.multimediatree import MultimediaSequentialIndex, MultimediaInvertedIndex

def create_test_images(output_dir, num_images=5):
    """
    Crea imágenes de prueba con diferentes patrones
    
    Args:
        output_dir: Directorio donde guardar las imágenes
        num_images: Número de imágenes a crear
    
    Returns:
        Lista de rutas a las imágenes creadas
    """
    os.makedirs(output_dir, exist_ok=True)
    image_paths = []
    
    for i in range(num_images):
        img_path = os.path.join(output_dir, f'test_image_{i}.jpg')
        
        # Crear imagen base
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        
        # Añadir formas con variaciones
        # Rectángulo exterior
        cv2.rectangle(img, (20, 20), (180, 180), (255, 255, 255), 2)
        
        # Círculo central con tamaño variable
        radius = 20 + i * 10
        cv2.circle(img, (100, 100), radius, (0, 0, 255), -1)
        
        # Líneas diagonales
        cv2.line(img, (20, 20), (100, 100), (0, 255, 0), 2)
        cv2.line(img, (180, 20), (100, 100), (255, 0, 0), 2)
        
        # Texto
        cv2.putText(img, f"Test {i}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.5, (255, 255, 0), 1, cv2.LINE_AA)
        
        # Guardar imagen
        cv2.imwrite(img_path, img)
        image_paths.append(img_path)
        
        print(f"Creada imagen de prueba: {img_path}")
    
    return image_paths

def demo_multimedia_search(image_dir, query_image_idx=0, method="sequential", k=3):
    """
    Demuestra la búsqueda multimedia
    
    Args:
        image_dir: Directorio con imágenes
        query_image_idx: Índice de la imagen a usar como consulta
        method: Método de búsqueda ("sequential" o "inverted")
        k: Número de resultados a mostrar
    """
    # Obtener todas las imágenes en el directorio
    image_files = [f for f in os.listdir(image_dir) 
                  if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
    
    if not image_files:
        print(f"No se encontraron imágenes en {image_dir}")
        return
    
    # Crear registros para el motor de búsqueda
    records = []
    for i, filename in enumerate(image_files):
        path = os.path.join(image_dir, filename)
        # Metadatos simulados
        metadata = {
            "nombre": filename,
            "id": i,
            "tamaño": os.path.getsize(path)
        }
        records.append((i, path, metadata))
    
    # Seleccionar imagen de consulta
    if query_image_idx >= len(image_files):
        query_image_idx = 0
    
    query_path = os.path.join(image_dir, image_files[query_image_idx])
    print(f"Usando imagen de consulta: {query_path}")
    
    # Crear motor de búsqueda
    print("Creando motor de búsqueda multimedia...")
    engine = MultimediaSearchEngine(feature_extractor_method='sift', n_clusters=min(20, len(records)))
    
    # Construir índice
    print("Construyendo índice...")
    engine.build_index(records)
    
    # Realizar búsqueda
    print(f"Realizando búsqueda {method}...")
    if method == "sequential":
        results = engine.knn_sequential(query_path, k=k)
    else:
        results = engine.knn_inverted_index(query_path, k=k)
    
    # Mostrar resultados
    print("\nResultados de la búsqueda:")
    print("-------------------------")
    
    # Mostrar las imágenes con matplotlib
    fig, axes = plt.subplots(1, k+1, figsize=(15, 4))
    
    # Mostrar imagen de consulta
    query_img = cv2.imread(query_path)
    query_img = cv2.cvtColor(query_img, cv2.COLOR_BGR2RGB)
    axes[0].imshow(query_img)
    axes[0].set_title("Consulta")
    axes[0].axis('off')
    
    # Mostrar resultados
    for i, (record_id, similarity, metadata) in enumerate(results):
        if i < k:
            result_path = records[record_id][1]
            print(f"#{i+1}: ID={record_id}, Similitud={similarity:.4f}, Nombre={metadata.get('nombre', 'N/A')}")
            
            # Mostrar imagen
            result_img = cv2.imread(result_path)
            result_img = cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB)
            axes[i+1].imshow(result_img)
            axes[i+1].set_title(f"Sim: {similarity:.4f}")
            axes[i+1].axis('off')
    
    plt.tight_layout()
    plt.show()

def main():
    parser = argparse.ArgumentParser(description="Demostración de búsqueda multimedia")
    parser.add_argument("--create", action="store_true", help="Crear imágenes de prueba")
    parser.add_argument("--dir", type=str, default="./multimedia/test_images", 
                        help="Directorio para imágenes de prueba")
    parser.add_argument("--query", type=int, default=0, 
                        help="Índice de la imagen a usar como consulta")
    parser.add_argument("--method", type=str, choices=["sequential", "inverted"], 
                        default="sequential", help="Método de búsqueda")
    parser.add_argument("--k", type=int, default=3, 
                        help="Número de resultados a mostrar")
    
    args = parser.parse_args()
    
    # Crear directorio de imágenes si no existe
    os.makedirs(args.dir, exist_ok=True)
    
    # Crear imágenes de prueba si se solicita
    if args.create:
        create_test_images(args.dir)
    
    # Ejecutar demostración
    demo_multimedia_search(args.dir, args.query, args.method, args.k)

if __name__ == "__main__":
    main() 