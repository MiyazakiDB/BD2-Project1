import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np

# 1. Cargar audio
y, sr = librosa.load(librosa.ex('trumpet'))  # esto es un ejemplo de audio de una trompeta de la liberia

# 2. Mostrar la señal de audio
plt.figure(figsize=(10, 3))
librosa.display.waveshow(y, sr=sr)
plt.title('Señal de audio (tiempo)')
plt.xlabel('Tiempo (s)')
plt.ylabel('Amplitud')
plt.tight_layout()
plt.show()

# 3. Espectrograma (magnitud del STFT)
D = np.abs(librosa.stft(y))  # Short-Time Fourier Transform,  usa n_fft=2048 por defecto
plt.figure(figsize=(10, 4))
librosa.display.specshow(librosa.amplitude_to_db(D, ref=np.max),
                         sr=sr, y_axis='log', x_axis='time')
plt.title('Espectrograma')
plt.colorbar(format='%+2.0f dB')
plt.tight_layout()
plt.show()

# 4. Espectrograma Mel
S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=40, fmax=8000)
plt.figure(figsize=(10, 4))
librosa.display.specshow(librosa.power_to_db(S, ref=np.max),
                         x_axis='time', y_axis='mel', sr=sr, fmax=8000)
plt.title('Espectrograma Mel')
plt.colorbar(format='%+2.0f dB')
plt.tight_layout()
plt.show()

# 5. MFCCs
mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
# visualizar - process
plt.figure(figsize=(10, 4))
librosa.display.specshow(mfccs, x_axis='time')
plt.title('MFCCs')
plt.ylabel('Coeficiente #')
plt.colorbar()
plt.tight_layout()
plt.show()



# Imprimir forma de la matriz
print("Forma de los MFCCs:", mfccs.shape)  # (13, N_frames)

# Imprimir los coeficientes redondeados para lectura más clara
np.set_printoptions(precision=2, suppress=True)
print("Coeficientes MFCC (matriz):")
print(mfccs)
print("Shape de los MFCCs:", mfccs.shape)

print("MFCCs del primer frame:")
print(mfccs[:, 229])  # vector columna 
