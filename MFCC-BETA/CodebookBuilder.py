import os
import librosa
import numpy as np
from sklearn.cluster import KMeans
import joblib

# === CONFIGURACIÓN ===
AUDIO_DIR = os.path.join(os.path.dirname(__file__), "previews")
N_MFCC = 13           # Número de coeficientes MFCC
N_CLUSTERS = 128      # Número de acoustic words
SAMPLE_RATE = 22050   # Sample rate estándar para librosa

model_dir = os.path.join(os.path.dirname(__file__), "modelK")

# === FUNCIÓN PARA EXTRAER MFCC ===
def extract_mfcc_from_file(file_path, n_mfcc=N_MFCC, sr=SAMPLE_RATE):
    try:
        y, sr = librosa.load(file_path, sr=sr)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
        return mfcc.T  # Cada fila es un frame
    except Exception as e:
        print(f"Error procesando {file_path}: {e}")
        return np.empty((0, n_mfcc))

# === CARGA Y EXTRACCIÓN DE MFCC ===
all_mfccs = []

print("Extrayendo MFCCs de audios...")

for filename in os.listdir(AUDIO_DIR):
    if filename.endswith(".wav") or filename.endswith(".mp3"):
        full_path = os.path.join(AUDIO_DIR, filename)
        mfcc = extract_mfcc_from_file(full_path)
        if mfcc.shape[0] > 0:
            all_mfccs.append(mfcc)

if not all_mfccs:
    raise Exception("No se extrajeron MFCCs de ningún audio. Verifica los archivos.")

# === CONCATENAR TODOS LOS MFCCs ===
all_descriptors = np.vstack(all_mfccs)
print(f"Total de vectores MFCC: {all_descriptors.shape[0]} frames de {N_MFCC} coeficientes")

# === ENTRENAR K-MEANS ===
print(f"Entrenando KMeans con K={N_CLUSTERS}...")
kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42, verbose=1)
kmeans.fit(all_descriptors)

# === GUARDAR EL MODELO ===
output_path = os.path.join(model_dir, "acoustic_codebook.pkl")
joblib.dump(kmeans, output_path)
print(f"Codebook guardado como: {output_path}")
