import os
import numpy as np
import librosa
import joblib
from scipy.spatial.distance import cdist
from tqdm import tqdm
import pandas as pd

# === CONFIGURACIÓN ===
AUDIO_DIR = r"C:\Users\tokio\OneDrive\Escritorio\BD2-Project1\MFCC-BETA\previews"
model_dir = r"C:\Users\tokio\OneDrive\Escritorio\BD2-Project1\MFCC-BETA\modelK"
CODEBOOK_PATH = os.path.join(model_dir, "acoustic_codebook.pkl")
N_MFCC = 13
SAMPLE_RATE = 22050

# === CARGAR EL CODEBOOK ===
print("Cargando codebook...")
kmeans = joblib.load(CODEBOOK_PATH)
N_CLUSTERS = kmeans.n_clusters

# === FUNCIÓN PARA OBTENER HISTOGRAMA  ===
def get_histogram(mfcc, codebook):
    distances = cdist(mfcc, codebook, metric='euclidean')
    cluster_ids = np.argmin(distances, axis=1)
    hist, _ = np.histogram(cluster_ids, bins=np.arange(N_CLUSTERS + 1))
    return hist 

# === PROCESAR TODOS LOS AUDIOS ===
audio_histograms = []
audio_filenames = []

print("Construyendo histogramas (raw TF)...")
for filename in tqdm(sorted(os.listdir(AUDIO_DIR))):
    if filename.endswith(".wav") or filename.endswith(".mp3"):
        path = os.path.join(AUDIO_DIR, filename)
        try:
            y, sr = librosa.load(path, sr=SAMPLE_RATE)
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC).T
            if mfcc.shape[0] > 0:
                hist = get_histogram(mfcc, kmeans.cluster_centers_)
                audio_histograms.append(hist)
                audio_filenames.append(filename)
        except Exception as e:
            print(f"Error procesando {filename}: {e}")

audio_histograms = np.array(audio_histograms, dtype=np.float64)  # (N_audios, N_clusters)
N_DOCS = len(audio_histograms)


# === CALCULAR TF ===
print("Calculando TF...")
nd = np.sum(audio_histograms, axis=1, keepdims=True)  # suma de cada histograma
tf = np.divide(audio_histograms, nd, where=(nd != 0))  # TF = n_i,d / n_d

# === CALCULAR IDF MANUAL ===
print("Calculando IDF...")
ni = np.count_nonzero(audio_histograms > 0, axis=0)  # en cuántos audios aparece cada codeword
idf = np.log(N_DOCS / ni)  # vector de IDF

# === APLICAR TF-IDF ===
print("Aplicando TF-IDF...")
tf_idf = tf * idf  

# === GUARDAR TF-IDF SIN NORMALIZAR ===
df_tfidf = pd.DataFrame(tf_idf)
df_tfidf.insert(0, "filename", audio_filenames)
tfidf_path = os.path.join(model_dir, "audio_histograms_tfidf.csv")
df_tfidf.to_csv(tfidf_path, index=False)

print(f"Proceso completado - TF-IDF guardado en: {tfidf_path}")
