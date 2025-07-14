import os
import numpy as np
import pandas as pd
import joblib
import heapq
from scipy.spatial.distance import cdist
from sklearn.metrics.pairwise import cosine_similarity
from mfccFunction import extract_mfcc_from_file

# === CONFIGURACIÓN ===
model_dir = r"C:\Users\tokio\OneDrive\Escritorio\BD2-Project1\MFCC-BETA\modelK"
CODEBOOK_PATH = os.path.join(model_dir, "acoustic_codebook.pkl")
TFIDF_CSV_PATH = os.path.join(model_dir, "audio_histograms_tfidf.csv")


class AudioSimilaritySearcher:
    def __init__(self):
        """Inicializa el buscador cargando el codebook y los histogramas TF-IDF"""
        print("Cargando codebook...")
        self.kmeans = joblib.load(CODEBOOK_PATH)
        self.n_clusters = self.kmeans.n_clusters
        
        print("Cargando histogramas TF-IDF...")
        self.df_tfidf = pd.read_csv(TFIDF_CSV_PATH)
        self.filenames = self.df_tfidf['filename'].values
        self.tfidf_vectors = self.df_tfidf.drop('filename', axis=1).values
        
        # Calcular estadísticas IDF del dataset para nuevos audios
        self._calculate_idf_stats()
        
        print(f"Sistema listo - {len(self.filenames)} audios en la base de datos")
    
    def _calculate_idf_stats(self):
        """Calcula estadísticas IDF para aplicar a nuevos audios"""
        # Convertir TF-IDF de vuelta a histogramas raw para obtener IDF
        self.n_docs = len(self.tfidf_vectors)
        
      
        non_zero_counts = np.count_nonzero(self.tfidf_vectors > 0, axis=0)
        self.idf_vector = np.log(self.n_docs / np.maximum(non_zero_counts, 1))
    
    def get_histogram_from_mfcc(self, mfcc):
        """
        Convierte MFCC a histograma usando tu lógica exacta de HistogramaBuilder
        """
        if mfcc.shape[0] == 0:
            return np.zeros(self.n_clusters)
        
        # Tu lógica exacta del HistogramaBuilder
        distances = cdist(mfcc, self.kmeans.cluster_centers_, metric='euclidean')
        cluster_ids = np.argmin(distances, axis=1)
        hist, _ = np.histogram(cluster_ids, bins=np.arange(self.n_clusters + 1))
        
        return hist
    
    def audio_to_tfidf_vector(self, audio_path):
        """
        Convierte un archivo de audio a vector TF-IDF usando tu proceso exacto
        """
        print(f"Extrayendo MFCC de: {os.path.basename(audio_path)}")
        
        # Usar tu función de extracción MFCC
        mfcc = extract_mfcc_from_file(audio_path)
        
        if mfcc.shape[0] == 0:
            print("Error: No se pudo extraer MFCC del audio")
            return None
        
        # Obtener histograma usando tu función exacta
        audio_histogram = self.get_histogram_from_mfcc(mfcc)
        
        # === CALCULAR TF  ===
        nd = np.sum(audio_histogram)  # suma del histograma
        if nd > 0:
            tf = audio_histogram / nd  # TF = n_i,d / n_d
        else:
            tf = audio_histogram.astype(np.float64)
        
        # === APLICAR TF-IDF (tu lógica exacta) ===
        tf_idf = tf * self.idf_vector
        
        return tf_idf
    
    def find_similar_audios(self, query_audio_path, top_k=None):
        """
        Encuentra audios similares usando similitud coseno
        
        Args:
            query_audio_path: Ruta del audio de consulta
            top_k: Número de resultados a retornar (None = todos)
        
        Returns:
            Lista de tuplas (filename, similarity_score) ordenada por similitud
        """
        # Convertir audio query a vector TF-IDF
        query_vector = self.audio_to_tfidf_vector(query_audio_path)
        
        if query_vector is None:
            return []
        
        print("Calculando similitudes coseno...")
        
        # Calcular similitud coseno con todos los audios en la base de datos
        similarities = cosine_similarity([query_vector], self.tfidf_vectors)[0]
        
        # Crear max-heap usando similaridades negativas (porque heapq es min-heap)
        heap = []
        for i, similarity in enumerate(similarities):
            # Usar similaridad negativa para simular max-heap
            heapq.heappush(heap, (-similarity, self.filenames[i], similarity))
        
        # Extraer resultados ordenados por similitud (mayor a menor)
        results = []
        total_results = len(heap) if top_k is None else min(top_k, len(heap))
        
        for _ in range(total_results):
            if heap:
                neg_sim, filename, similarity = heapq.heappop(heap)
                results.append((filename, similarity))
        
        return results

def search_similar_audios(query_audio_path, top_k=None):
    """
    Función helper para búsqueda de audios similares
    
    Args:
        query_audio_path: Ruta del audio de consulta
        top_k: Número de resultados a retornar (None = todos)
    
    Returns:
        Lista de tuplas (filename, similarity_score)
    """
    searcher = AudioSimilaritySearcher()
    return searcher.find_similar_audios(query_audio_path, top_k)

# === EJEMPLO DE USO ===
if __name__ == "__main__":
    # Ejemplo de uso
    query_path = r"C:\Users\tokio\OneDrive\Escritorio\BD2-Project1\MFCC-BETA\audio_to_see\The_Strokes_-_Reptilia.wav"
    
    # Buscar los 10 audios más similares
    resultados = search_similar_audios(query_path, top_k=10)
    
    print(f"\nAudios más similares a {os.path.basename(query_path)}:")
    print("-" * 70)
    
    for i, (filename, similarity) in enumerate(resultados, 1):
        print(f"{i:2d}. {filename:<50} | Similitud: {similarity:.4f}")
    
    # Buscar todos los audios similares
    print(f"\n--- Estadísticas generales ---")
    todos_resultados = search_similar_audios(query_path)
    print(f"Total de audios comparados: {len(todos_resultados)}")
    
    if todos_resultados:
        max_sim = max(sim for _, sim in todos_resultados)
        min_sim = min(sim for _, sim in todos_resultados)
        avg_sim = np.mean([sim for _, sim in todos_resultados])
        print(f"Similitud máxima: {max_sim:.4f}")
        print(f"Similitud mínima: {min_sim:.4f}")
        print(f"Similitud promedio: {avg_sim:.4f}")