import os
import numpy as np
import pandas as pd
import joblib
from scipy.spatial.distance import cdist
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize
from pathlib import Path
from mfccFunction import extract_mfcc_from_file

# === CONFIGURACIÓN ===
model_dir = Path(__file__).parent / "modelK"
CODEBOOK_PATH = model_dir / "acoustic_codebook.pkl"
TFIDF_CSV_PATH = model_dir / "audio_histograms_tfidf_normalized.csv"

class AudioSimilaritySearcher:
    def __init__(self):
        """Inicializa el buscador cargando el codebook y los histogramas TF-IDF"""
        self._load_codebook()
        self._load_tfidf_data()
        self._estimate_idf_from_tfidf()
    
    def _load_codebook(self):
        """Carga el modelo K-means entrenado"""
        if not CODEBOOK_PATH.exists():
            raise FileNotFoundError(f"Codebook no encontrado: {CODEBOOK_PATH}")
        
        self.kmeans = joblib.load(CODEBOOK_PATH)
        self.n_clusters = self.kmeans.n_clusters
    
    def _load_tfidf_data(self):
        """Carga los vectores TF-IDF de la base de datos"""
        if not TFIDF_CSV_PATH.exists():
            raise FileNotFoundError(f"Archivo TF-IDF no encontrado: {TFIDF_CSV_PATH}")
        
        self.df_tfidf = pd.read_csv(TFIDF_CSV_PATH)
        self.filenames = self.df_tfidf['filename'].values
        self.tfidf_vectors = self.df_tfidf.drop('filename', axis=1).values
    
    def _estimate_idf_from_tfidf(self):
        """Estima el vector IDF desde los datos TF-IDF existentes"""
        doc_frequencies = np.count_nonzero(self.tfidf_vectors > 0, axis=0)
        n_docs = len(self.tfidf_vectors)
        self.idf_vector = np.log(n_docs / np.maximum(doc_frequencies, 1))
    
    def get_histogram_from_mfcc(self, mfcc):
        """
        Convierte MFCC a histograma usando la misma lógica del entrenamiento
        """
        if mfcc.shape[0] == 0:
            return np.zeros(self.n_clusters, dtype=np.float64)
        
        distances = cdist(mfcc, self.kmeans.cluster_centers_, metric='euclidean')
        cluster_ids = np.argmin(distances, axis=1)
        hist, _ = np.histogram(cluster_ids, bins=np.arange(self.n_clusters + 1))
        
        return hist.astype(np.float64)
    
    def audio_to_tfidf_vector(self, audio_path):
        """
        Convierte un archivo de audio a vector TF-IDF normalizado
        """
        mfcc = extract_mfcc_from_file(audio_path)
        
        if mfcc.shape[0] == 0:
            return None
        
        audio_histogram = self.get_histogram_from_mfcc(mfcc)
        
        # === CALCULAR TF ===
        nd = np.sum(audio_histogram)
        if nd > 0:
            tf = audio_histogram / nd
        else:
            tf = audio_histogram.astype(np.float64)
        
        # === APLICAR TF-IDF ===
        tf_idf = tf * self.idf_vector
        
        # === NORMALIZACIÓN L2 ===
        tf_idf_normalized = normalize([tf_idf], norm='l2')[0]
        
        return tf_idf_normalized
    
    def find_similar_audios(self, query_audio_path, top_k=None, similarity_threshold=0.0):
        """
        Encuentra audios similares usando similitud coseno
        """
        query_vector = self.audio_to_tfidf_vector(query_audio_path)
        
        if query_vector is None:
            return []
        
        similarities = cosine_similarity([query_vector], self.tfidf_vectors)[0]
        
        results = []
        for i, similarity in enumerate(similarities):
            if similarity >= similarity_threshold:
                results.append((self.filenames[i], similarity))
        
        results.sort(key=lambda x: x[1], reverse=True)
        
        if top_k is not None:
            results = results[:top_k]
        
        return results

def search_similar_audios(query_audio_path, top_k=None, similarity_threshold=0.0):
    """
    Función helper para búsqueda de audios similares
    """
    searcher = AudioSimilaritySearcher()
    return searcher.find_similar_audios(query_audio_path, top_k, similarity_threshold)

# === EJEMPLO DE USO ===
if __name__ == "__main__":
    query_path = Path(__file__).parent / "audio_to_see" / "Tainy, Bad Bunny - MOJABI GHOST.mp3"
    
    if not query_path.exists():
        print(f"Error: Archivo no encontrado - {query_path}")
        exit(1)
    
    try:
        searcher = AudioSimilaritySearcher()
        
        resultados = searcher.find_similar_audios(query_path, top_k=10, similarity_threshold=0.0)
        
        for i, (filename, similarity) in enumerate(resultados, 1):
            print(f"{i:2d}. {filename:<50} | Similitud: {similarity:.4f}")
        
    except Exception as e:
        print(f"Error: {e}")