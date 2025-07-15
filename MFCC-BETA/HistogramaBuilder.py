import os
import numpy as np
import librosa
import joblib
from scipy.spatial.distance import cdist
from sklearn.preprocessing import normalize
from tqdm import tqdm
import pandas as pd
from pathlib import Path
import logging

# === CONFIGURACIÓN ===
AUDIO_DIR = Path(__file__).parent / "previews"
model_dir = Path(__file__).parent / "modelK"
CODEBOOK_PATH = model_dir / "acoustic_codebook.pkl"
N_MFCC = 13
SAMPLE_RATE = 22050
SUPPORTED_FORMATS = {'.wav', '.mp3', '.flac', '.m4a'}

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# === CARGAR EL CODEBOOK ===
def load_codebook():
    """Carga el codebook previamente entrenado."""
    if not CODEBOOK_PATH.exists():
        raise FileNotFoundError(f"Codebook no encontrado en: {CODEBOOK_PATH}")
    
    logger.info("Cargando codebook...")
    kmeans = joblib.load(CODEBOOK_PATH)
    N_CLUSTERS = kmeans.n_clusters
    logger.info(f"Codebook cargado: {N_CLUSTERS} clusters, {kmeans.cluster_centers_.shape[1]} dimensiones")
    return kmeans, N_CLUSTERS

# === FUNCIÓN PARA OBTENER HISTOGRAMA MEJORADA ===
def get_histogram(mfcc, codebook, method='euclidean'):
    """
    Calcula histograma de acoustic words para un archivo de audio.
    
    Args:
        mfcc: Array de MFCCs (n_frames, n_mfcc)
        codebook: Centroides del K-means
        method: Métrica de distancia ('euclidean', 'cosine', 'manhattan')
    
    Returns:
        np.array: Histograma normalizado
    """
    if mfcc.shape[0] == 0:
        return np.zeros(len(codebook))
    
    # Calcular distancias y asignar a clusters
    distances = cdist(mfcc, codebook, metric=method)
    cluster_ids = np.argmin(distances, axis=1)
    
    # Crear histograma
    hist, _ = np.histogram(cluster_ids, bins=np.arange(len(codebook) + 1))
    
    return hist.astype(np.float64)

# === FUNCIÓN PARA EXTRAER MFCC ===
def extract_mfcc_from_file(file_path, n_mfcc=N_MFCC, sr=SAMPLE_RATE):
    """Extrae MFCCs de un archivo de audio con validación."""
    try:
        y, actual_sr = librosa.load(file_path, sr=sr)
        
        if len(y) == 0:
            logger.warning(f"Archivo vacío: {file_path}")
            return np.empty((0, n_mfcc))
        
        mfcc = librosa.feature.mfcc(y=y, sr=actual_sr, n_mfcc=n_mfcc)
        
        # Verificar MFCCs válidos
        if np.any(np.isnan(mfcc)) or np.any(np.isinf(mfcc)):
            logger.warning(f"MFCCs inválidos en: {file_path}")
            return np.empty((0, n_mfcc))
        
        return mfcc.T  # Cada fila es un frame
        
    except Exception as e:
        logger.error(f"Error procesando {file_path}: {e}")
        return np.empty((0, n_mfcc))

# === PROCESAR TODOS LOS AUDIOS ===
def process_audio_files(kmeans, N_CLUSTERS):
    """Procesa todos los archivos de audio y genera histogramas."""
    audio_files = [f for f in AUDIO_DIR.glob("*") if f.suffix.lower() in SUPPORTED_FORMATS]
    
    if not audio_files:
        raise ValueError(f"No se encontraron archivos de audio en: {AUDIO_DIR}")
    
    audio_histograms = []
    audio_filenames = []
    failed_files = []
    
    logger.info(f"Procesando {len(audio_files)} archivos de audio...")
    
    for file_path in tqdm(sorted(audio_files), desc="Construyendo histogramas"):
        try:
            mfcc = extract_mfcc_from_file(file_path)
            if mfcc.shape[0] > 0:
                hist = get_histogram(mfcc, kmeans.cluster_centers_)
                audio_histograms.append(hist)
                audio_filenames.append(file_path.name)
            else:
                failed_files.append(file_path.name)
                logger.warning(f"No se pudieron extraer MFCCs válidos de: {file_path.name}")
        except Exception as e:
            failed_files.append(file_path.name)
            logger.error(f"Error procesando {file_path.name}: {e}")
    
    if not audio_histograms:
        raise Exception("No se procesaron archivos de audio exitosamente")
    
    logger.info(f"Procesados exitosamente: {len(audio_histograms)} archivos")
    if failed_files:
        logger.warning(f"Archivos fallidos: {len(failed_files)}")
    
    return np.array(audio_histograms, dtype=np.float64), audio_filenames

# === CALCULAR TF-IDF ===
def calculate_tf_idf(audio_histograms, smoothing=1e-8):
    """
    Calcula TF-IDF para los histogramas de audio.
    
    Args:
        audio_histograms: Array de histogramas (N_audios, N_clusters)
        smoothing: Factor de suavizado para evitar división por cero
    
    Returns:
        tuple: (tf_idf, tf, idf)
    """
    N_DOCS = len(audio_histograms)
    
    # === CALCULAR TF ===
    logger.info("Calculando TF...")
    nd = np.sum(audio_histograms, axis=1, keepdims=True)  # suma de cada histograma
    
    # Evitar división por cero
    nd_safe = np.where(nd == 0, 1, nd)
    tf = audio_histograms / nd_safe
    
    # === CALCULAR IDF ===
    logger.info("Calculando IDF...")
    ni = np.count_nonzero(audio_histograms > 0, axis=0)  # en cuántos audios aparece cada codeword
    
    # Suavizado para evitar log(0) y división por cero
    ni_smoothed = np.where(ni == 0, smoothing, ni)
    idf = np.log(N_DOCS / ni_smoothed)
    
    # === APLICAR TF-IDF ===
    logger.info("Aplicando TF-IDF...")
    tf_idf = tf * idf
    
    # Información estadística
    logger.info(f"TF stats - Min: {tf.min():.6f}, Max: {tf.max():.6f}, Mean: {tf.mean():.6f}")
    logger.info(f"IDF stats - Min: {idf.min():.6f}, Max: {idf.max():.6f}, Mean: {idf.mean():.6f}")
    logger.info(f"TF-IDF stats - Min: {tf_idf.min():.6f}, Max: {tf_idf.max():.6f}, Mean: {tf_idf.mean():.6f}")
    
    return tf_idf, tf, idf

# === FUNCIÓN PRINCIPAL ===
def main():
    """Función principal que ejecuta todo el proceso."""
    try:
        # Cargar codebook
        kmeans, N_CLUSTERS = load_codebook()
        
        # Procesar archivos de audio
        audio_histograms, audio_filenames = process_audio_files(kmeans, N_CLUSTERS)
        
        # Calcular TF-IDF
        tf_idf, tf, idf = calculate_tf_idf(audio_histograms)
        
        # === GUARDAR RESULTADOS ===
        model_dir.mkdir(exist_ok=True)
        
        # TF-IDF sin normalizar
        df_tfidf = pd.DataFrame(tf_idf)
        df_tfidf.insert(0, "filename", audio_filenames)
        tfidf_path = model_dir / "audio_histograms_tfidf.csv"
        df_tfidf.to_csv(tfidf_path, index=False)
        logger.info(f"TF-IDF guardado en: {tfidf_path}")
        
        # TF-IDF normalizado L2 (opcional pero recomendado)
        tf_idf_normalized = normalize(tf_idf, norm='l2')
        df_tfidf_norm = pd.DataFrame(tf_idf_normalized)
        df_tfidf_norm.insert(0, "filename", audio_filenames)
        tfidf_norm_path = model_dir / "audio_histograms_tfidf_normalized.csv"
        df_tfidf_norm.to_csv(tfidf_norm_path, index=False)
        logger.info(f"TF-IDF normalizado guardado en: {tfidf_norm_path}")
        
        # Guardar histogramas raw
        df_raw = pd.DataFrame(audio_histograms)
        df_raw.insert(0, "filename", audio_filenames)
        raw_path = model_dir / "audio_histograms_raw.csv"
        df_raw.to_csv(raw_path, index=False)
        logger.info(f"Histogramas raw guardados en: {raw_path}")
        
        # Guardar estadísticas
        stats = {
            'n_files': len(audio_filenames),
            'n_clusters': N_CLUSTERS,
            'tf_idf_shape': tf_idf.shape,
            'avg_nonzero_per_file': np.mean(np.count_nonzero(tf_idf, axis=1)),
            'sparsity': np.mean(tf_idf == 0) * 100  # Porcentaje de zeros
        }
        
        stats_path = model_dir / "histogram_stats.pkl"
        joblib.dump(stats, stats_path)
        logger.info(f"Estadísticas guardadas en: {stats_path}")
        
        # Mostrar resumen
        logger.info(f"\n=== RESUMEN ===")
        logger.info(f"Archivos procesados: {stats['n_files']}")
        logger.info(f"Dimensiones TF-IDF: {stats['tf_idf_shape']}")
        logger.info(f"Promedio de palabras no-cero por archivo: {stats['avg_nonzero_per_file']:.2f}")
        logger.info(f"Esparsidad: {stats['sparsity']:.2f}%")
        
        logger.info("Proceso completado exitosamente!")
        
    except Exception as e:
        logger.error(f"Error durante el procesamiento: {e}")
        raise

if __name__ == "__main__":
    main()