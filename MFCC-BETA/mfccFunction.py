import librosa
import numpy as np

def extract_mfcc_from_file(file_path): 
    n_mfcc = 13
    sr = 22050   
    try:
        y, sr = librosa.load(file_path, sr=sr)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
        return mfcc.T  # Cada fila es un frame
    except Exception as e:
        print(f"Error procesando {file_path}: {e}")
        return np.empty((0, n_mfcc))




