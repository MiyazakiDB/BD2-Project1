import os
import librosa
import numpy as np
from sklearn.cluster import KMeans
import joblib
from pathlib import Path
import logging

# === CONFIGURACIÓN ===
AUDIO_DIR = Path(__file__).parent / "previews"
N_MFCC = 13           # Número de coeficientes MFCC
N_CLUSTERS = 128      # Número de acoustic words
SAMPLE_RATE = 22050   # Sample rate estándar para librosa
SUPPORTED_FORMATS = {'.wav', '.mp3'}

model_dir = Path(__file__).parent / "modelK"
model_dir.mkdir(exist_ok=True)  # Crear directorio si no existe

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# === FUNCIÓN PARA EXTRAER MFCC ===
def extract_mfcc_from_file(file_path, n_mfcc=N_MFCC, sr=SAMPLE_RATE):
    """
    Extrae coeficientes MFCC de un archivo de audio.
    
    Args:
        file_path: Ruta al archivo de audio
        n_mfcc: Número de coeficientes MFCC a extraer
        sr: Sample rate para el procesamiento
    
    Returns:
        numpy.ndarray: Array de MFCCs con shape (n_frames, n_mfcc)
    """
    try:
        y, actual_sr = librosa.load(file_path, sr=sr)
        
        # Verificar que el audio tenga contenido
        if len(y) == 0:
            logger.warning(f"Archivo vacío: {file_path}")
            return np.empty((0, n_mfcc))
        
        # Extraer MFCCs
        mfcc = librosa.feature.mfcc(y=y, sr=actual_sr, n_mfcc=n_mfcc)
        
        # Verificar que se extrajeron MFCCs válidos
        if np.any(np.isnan(mfcc)) or np.any(np.isinf(mfcc)):
            logger.warning(f"MFCCs inválidos en: {file_path}")
            return np.empty((0, n_mfcc))
        
        return mfcc.T  # Cada fila es un frame
        
    except Exception as e:
        logger.error(f"Error procesando {file_path}: {e}")
        return np.empty((0, n_mfcc))

# === VALIDACIÓN DE DIRECTORIOS ===
def validate_setup():
    """Valida que los directorios necesarios existan."""
    if not AUDIO_DIR.exists():
        raise FileNotFoundError(f"Directorio de audio no encontrado: {AUDIO_DIR}")
    
    audio_files = list(AUDIO_DIR.glob("*"))
    audio_files = [f for f in audio_files if f.suffix.lower() in SUPPORTED_FORMATS]
    
    if not audio_files:
        raise ValueError(f"No se encontraron archivos de audio en: {AUDIO_DIR}")
    
    logger.info(f"Encontrados {len(audio_files)} archivos de audio")
    return audio_files

# === PROCESAMIENTO PRINCIPAL ===
def main():
    # Validar configuración
    audio_files = validate_setup()
    
    # Extraer MFCCs
    all_mfccs = []
    processed_files = 0
    
    logger.info("Extrayendo MFCCs de audios...")
    
    for file_path in audio_files:
        mfcc = extract_mfcc_from_file(file_path)
        if mfcc.shape[0] > 0:
            all_mfccs.append(mfcc)
            processed_files += 1
            
            # Mostrar progreso cada 10 archivos
            if processed_files % 10 == 0:
                logger.info(f"Procesados {processed_files}/{len(audio_files)} archivos")
    
    if not all_mfccs:
        raise Exception("No se extrajeron MFCCs de ningún audio. Verifica los archivos.")
    
    logger.info(f"MFCCs extraídos exitosamente de {processed_files} archivos")
    
    # Concatenar todos los MFCCs
    all_descriptors = np.vstack(all_mfccs)
    logger.info(f"Total de vectores MFCC: {all_descriptors.shape[0]} frames de {N_MFCC} coeficientes")
    
    # Verificar si hay suficientes datos
    if all_descriptors.shape[0] < N_CLUSTERS:
        logger.warning(f"Pocos datos ({all_descriptors.shape[0]} frames) para {N_CLUSTERS} clusters")
        logger.warning("Considera reducir N_CLUSTERS o añadir más audio")
    
    # Entrenar K-means
    logger.info(f"Entrenando KMeans con K={N_CLUSTERS}...")
    kmeans = KMeans(
        n_clusters=N_CLUSTERS, 
        random_state=42, 
        verbose=1,
        n_init=10,  # Múltiples inicializaciones para mejor convergencia
        max_iter=300  # Límite de iteraciones
    )
    
    kmeans.fit(all_descriptors)
    
    # Mostrar información del clustering
    logger.info(f"Clustering completado. Inercia: {kmeans.inertia_:.2f}")
    
    # Guardar el modelo
    output_path = model_dir / "acoustic_codebook.pkl"
    joblib.dump(kmeans, output_path)
    logger.info(f"Codebook guardado como: {output_path}")
    
    # Guardar información adicional
    info = {
        'n_clusters': N_CLUSTERS,
        'n_mfcc': N_MFCC,
        'sample_rate': SAMPLE_RATE,
        'n_frames': all_descriptors.shape[0],
        'n_files_processed': processed_files,
        'inertia': kmeans.inertia_
    }
    
    info_path = model_dir / "codebook_info.pkl"
    joblib.dump(info, info_path)
    logger.info(f"Información del modelo guardada en: {info_path}")

if __name__ == "__main__":
    main()