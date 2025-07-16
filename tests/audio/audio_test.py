import os
import sys
import numpy as np
import tempfile
import shutil
import librosa
import soundfile as sf
import glob

# Añadir el directorio raíz al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from engine.multimedia import FeatureExtractor, CodebookBuilder, MultimediaSearchEngine

def test_feature_extraction():
    """Prueba la extracción de características de archivos de audio"""
    # Crear directorio temporal
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Crear un archivo de audio de prueba (tono simple)
        test_audio_path = os.path.join(temp_dir, 'test_audio.wav')
        sr = 22050  # Frecuencia de muestreo
        duration = 1  # Duración en segundos
        
        # Generar un tono simple (sinusoide)
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        tone = 0.5 * np.sin(2 * np.pi * 440 * t)  # Tono A4 (440 Hz)
        
        # Guardar como archivo WAV
        sf.write(test_audio_path, tone, sr)
        
        # Extraer características
        features = FeatureExtractor.extract_features_audio(test_audio_path)
        
        # Verificar que se hayan extraído características
        if features is None or len(features) == 0:
            print("ERROR: No se extrajeron características del audio")
            return False
        
        print(f"Éxito: Se extrajeron {len(features)} características del audio")
        return True
    
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False
    
    finally:
        # Limpiar
        shutil.rmtree(temp_dir)

def test_codebook_creation():
    """Prueba la creación de un codebook para audio"""
    try:
        # Crear datos de prueba (descriptores de características simulados)
        test_features1 = np.random.rand(20, 13)  # 20 vectores MFCC simulados
        test_features2 = np.random.rand(30, 13)  # 30 vectores MFCC simulados
        
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

def extract_audio_features_with_fallback(audio_path):
    """
    Intenta extraer características de audio con manejo de errores y alternativas
    """
    try:
        # Intentar extraer características normalmente
        return FeatureExtractor.extract_features_audio(audio_path)
    except Exception as e:
        try:
            # Normalizar la ruta (Windows puede tener problemas con backslashes)
            normalized_path = os.path.normpath(audio_path)
            return FeatureExtractor.extract_features_audio(normalized_path)
        except Exception as e:
            # Si sigue fallando, devolver un array vacío
            return np.array([])

def test_audio_search_with_previews():
    """Compara un archivo de audio específico con el conjunto de audios de prueba"""
    # Rutas de archivos - usar os.path para normalizar las rutas
    test_audio_path = os.path.normpath("datasets/previews_dataset/test_audio")
    audio_dataset_path = os.path.normpath("datasets/previews_dataset/previews")
    
    try:
        # Buscar el archivo de audio de prueba (cualquier archivo en el directorio raíz)
        test_files = []
        for ext in ['*.wav', '*.mp3', '*.ogg']:
            test_files.extend(glob.glob(os.path.join(test_audio_path, ext)))
        
        if not test_files:
            print(f"ERROR: No se encontraron archivos de audio de prueba en {test_audio_path}")
            return False
            
        # Usar el primer archivo como consulta
        test_audio_file = test_files[0]
        print(f"Usando archivo de audio para consulta: {test_audio_file}")
        
        # Verificar que el directorio del dataset existe
        if not os.path.exists(audio_dataset_path):
            print(f"ERROR: El directorio de audios de prueba no existe en {audio_dataset_path}")
            return False
            
        # Obtener todos los archivos de audio del dataset
        print("Buscando archivos de audio en el dataset...")
        audio_files = []
        for ext in ['*.wav', '*.mp3', '*.ogg']:
            audio_files.extend(glob.glob(os.path.join(audio_dataset_path, '**', ext), recursive=True))
        
        total_files = len(audio_files)
        print(f"Se encontraron {total_files} archivos de audio en el dataset")
        
        if total_files == 0:
            print("ERROR: No se encontraron archivos de audio en el dataset")
            return False
            
        # Crear registros para el motor de búsqueda
        print("Preparando registros para el motor de búsqueda...")
        records = []
        valid_features = []
        
        for i, path in enumerate(audio_files):
            # Extraer el nombre del archivo sin la extensión para usarlo como metadato
            filename = os.path.basename(path)
            name_without_ext = os.path.splitext(filename)[0]
            
            # Intentar extraer características (con manejo de errores)
            features = extract_audio_features_with_fallback(path)
            
            # Solo agregar registros con características válidas
            if features is not None and len(features) > 0:
                records.append((i, path, {"nombre": name_without_ext}))
                valid_features.append(features)
            
            # Mostrar progreso cada 100 archivos
            if i % 100 == 0 and i > 0:
                print(f"Procesados {i}/{total_files} archivos de audio...")
        
        # Verificar si hay suficientes registros con características válidas
        if len(records) == 0 or len(valid_features) == 0:
            print("ERROR: No se pudieron extraer características válidas de ningún archivo")
            return False
            
        # Crear motor de búsqueda
        print("\nCreando motor de búsqueda multimedia para audio...")
        n_clusters = min(64, len(valid_features) // 2)  # Un cluster por cada ~2 archivos, máximo 64
        
        # Asegurarse de que haya al menos 2 clusters
        n_clusters = max(2, n_clusters)
        
        engine = MultimediaSearchEngine(feature_extractor_method='mfcc', n_clusters=n_clusters)
        
        # Construir índice con los registros válidos
        try:
            print(f"Construyendo índice con {n_clusters} clusters...")
            engine.build_index(records)
            
            # Verificar que se haya construido el índice
            if len(engine.records) < 1 or len(engine.histograms) < 1:
                print("ERROR: No se pudo construir el índice correctamente")
                return False
                
            # Extraer características de consulta (con manejo de errores)
            query_features = extract_audio_features_with_fallback(test_audio_file)
            
            if query_features is None or len(query_features) == 0:
                print("ERROR: No se pudieron extraer características del archivo de consulta")
                return False
                
            # Realizar búsqueda
            print("Realizando búsqueda de los 5 archivos de audio más similares...")
            k = min(5, len(engine.records))  # No pedir más resultados de los que hay
            results = engine.knn_sequential(test_audio_file, k=k)
            
            # Verificar resultados
            if len(results) < 1:
                print("ERROR: La búsqueda no devolvió resultados")
                return False
                
            # Mostrar resultados
            print("\nResultados de la búsqueda:")
            print(f"Audio de consulta: {test_audio_file}")
            print("\nAudios más similares del dataset:")
            for i, (record_id, similarity, metadata) in enumerate(results):
                audio_path = audio_files[record_id]
                print(f"#{i+1}: ID={record_id}, Similitud={similarity:.4f}, Nombre={metadata.get('nombre', 'N/A')}")
                print(f"   Ruta: {audio_path}")
                
            # También probar la búsqueda con índice invertido si hay suficientes registros
            if len(engine.records) >= 5:
                print("\nRealizando búsqueda con índice invertido...")
                results_inverted = engine.knn_inverted_index(test_audio_file, k=k)
                
                print("\nResultados de la búsqueda con índice invertido:")
                for i, (record_id, similarity, metadata) in enumerate(results_inverted):
                    audio_path = audio_files[record_id]
                    print(f"#{i+1}: ID={record_id}, Similitud={similarity:.4f}, Nombre={metadata.get('nombre', 'N/A')}")
            
            return True
            
        except Exception as e:
            print(f"ERROR durante la construcción del índice o búsqueda: {str(e)}")
            return False
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def run_all_tests():
    """Ejecuta todas las pruebas de audio"""
    print("=== Prueba de extracción de características de audio ===")
    test_feature_extraction()
    
    print("\n=== Prueba de creación de codebook para audio ===")
    test_codebook_creation()
    
    print("\n=== Prueba de búsqueda en dataset de audio ===")
    test_audio_search_with_previews()

if __name__ == "__main__":
    # Ejecutar todas las pruebas
    run_all_tests() 