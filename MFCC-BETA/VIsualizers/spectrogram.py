import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import os

def plot_spectrogram(audio_path, title="Espectrograma"):
    y, sr = librosa.load(audio_path, sr=None)
    S = librosa.stft(y)
    S_db = librosa.amplitude_to_db(abs(S))

    plt.figure(figsize=(10, 4))
    librosa.display.specshow(S_db, sr=sr, x_axis='time', y_axis='log')
    plt.colorbar(format="%+2.0f dB")
    plt.title(title)
    plt.tight_layout()
    plt.show()

def plot_mel_spectrogram(audio_path, title="Mel-Spectrograma"):
    """🔊 Visualizar mel-spectrograma - más perceptual"""
    y, sr = librosa.load(audio_path, sr=None)
    S = librosa.feature.melspectrogram(y=y, sr=sr)
    S_db = librosa.power_to_db(S, ref=np.max)

    plt.figure(figsize=(10, 4))
    librosa.display.specshow(S_db, sr=sr, x_axis='time', y_axis='mel')
    plt.colorbar(format="%+2.0f dB")
    plt.title(title)
    plt.tight_layout()
    plt.show()

def plot_mfcc(audio_path, title="MFCC"):
    """🧠 Visualizar MFCCs - coeficientes cepstrales de Mel"""
    y, sr = librosa.load(audio_path, sr=None)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)

    plt.figure(figsize=(10, 4))
    librosa.display.specshow(mfcc, sr=sr, x_axis='time')
    plt.colorbar()
    plt.title(title)
    plt.tight_layout()
    plt.show()

def plot_waveform(audio_path, title="Forma de Onda"):
    """📉 Visualizar forma de onda - amplitud vs tiempo"""
    y, sr = librosa.load(audio_path, sr=None)

    plt.figure(figsize=(10, 2))
    librosa.display.waveshow(y, sr=sr)
    plt.title(title)
    plt.tight_layout()
    plt.show()

def compare_mfccs(path1, path2, name1="Audio 1", name2="Audio 2"):
    """🔀 Comparar MFCCs de dos audios lado a lado"""
    y1, sr1 = librosa.load(path1, sr=None)
    y2, sr2 = librosa.load(path2, sr=None)

    mfcc1 = librosa.feature.mfcc(y=y1, sr=sr1, n_mfcc=13)
    mfcc2 = librosa.feature.mfcc(y=y2, sr=sr2, n_mfcc=13)

    plt.figure(figsize=(12, 5))
    
    plt.subplot(1, 2, 1)
    librosa.display.specshow(mfcc1, sr=sr1, x_axis='time')
    plt.title(f"MFCC - {name1}")
    plt.colorbar()

    plt.subplot(1, 2, 2)
    librosa.display.specshow(mfcc2, sr=sr2, x_axis='time')
    plt.title(f"MFCC - {name2}")
    plt.colorbar()
    
    plt.tight_layout()
    plt.show()

def compare_spectrograms(path1, path2, name1="Audio 1", name2="Audio 2"):
    """🔀 Comparar espectrogramas de dos audios lado a lado"""
    y1, sr1 = librosa.load(path1, sr=None)
    y2, sr2 = librosa.load(path2, sr=None)

    S1 = librosa.stft(y1)
    S1_db = librosa.amplitude_to_db(abs(S1))
    
    S2 = librosa.stft(y2)
    S2_db = librosa.amplitude_to_db(abs(S2))

    plt.figure(figsize=(12, 5))
    
    plt.subplot(1, 2, 1)
    librosa.display.specshow(S1_db, sr=sr1, x_axis='time', y_axis='log')
    plt.title(f"Espectrograma - {name1}")
    plt.colorbar(format="%+2.0f dB")

    plt.subplot(1, 2, 2)
    librosa.display.specshow(S2_db, sr=sr2, x_axis='time', y_axis='log')
    plt.title(f"Espectrograma - {name2}")
    plt.colorbar(format="%+2.0f dB")
    
    plt.tight_layout()
    plt.show()

def plot_all_audio_visualizations(audio_path):
    """🛠️ Mostrar todas las visualizaciones de un audio"""
    print(f"🔎 Visualizando: {audio_path}")
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    
    plot_waveform(audio_path, f"🔊 Forma de Onda - {base_name}")
    plot_spectrogram(audio_path, f"🎛️ Espectrograma - {base_name}")
    plot_mel_spectrogram(audio_path, f"🎚️ Mel-Spectrograma - {base_name}")
    plot_mfcc(audio_path, f"🎶 MFCC - {base_name}")

def save_spectrogram_png(audio_path, output_path=None, title=None):
    """
    Genera y guarda un espectrograma como archivo PNG
    """
    # Cargar audio
    y, sr = librosa.load(audio_path, sr=None)
    S = librosa.stft(y)
    S_db = librosa.amplitude_to_db(abs(S))
    
    # Configurar el plot
    plt.figure(figsize=(12, 6))
    librosa.display.specshow(S_db, sr=sr, x_axis='time', y_axis='log')
    plt.colorbar(format="%+2.0f dB")
    
    # Título
    if title is None:
        title = f"Espectrograma - {os.path.basename(audio_path)}"
    plt.title(title)
    plt.tight_layout()
    
    # Guardar
    if output_path is None:
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        output_path = f"{base_name}_spectrogram.png"
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()  # Cerrar para no mostrar
    print(f"✅ Espectrograma guardado: {output_path}")
    return output_path

def generar_espectrogramas():
    """
    Genera espectrogramas PNG de 2 canciones de la carpeta previews
    """
    # Ruta relativa a la carpeta previews
    previews_dir = os.path.join(os.path.dirname(__file__), "..", "previews")
    
    # Crear carpeta de salida al mismo nivel que spectrogram.py
    output_dir = os.path.join(os.path.dirname(__file__), "spectrograms_output")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"📁 Buscando archivos en: {os.path.abspath(previews_dir)}")
    print(f"💾 Guardando espectrogramas en: {os.path.abspath(output_dir)}")
    
    # Verificar si existe la carpeta
    if not os.path.exists(previews_dir):
        print(f"❌ Error: La carpeta {previews_dir} no existe")
        print("💡 Usa esta ruta para colocar tus archivos de audio:")
        print(f"   {os.path.abspath(previews_dir)}")
        return
    
    # Buscar archivos de audio
    audio_extensions = ('.wav', '.mp3', '.flac', '.m4a')
    audio_files = [f for f in os.listdir(previews_dir) 
                   if f.lower().endswith(audio_extensions)]
    
    if len(audio_files) == 0:
        print("❌ No se encontraron archivos de audio en la carpeta previews")
        print("💡 Coloca archivos .wav, .mp3, .flac o .m4a en:")
        print(f"   {os.path.abspath(previews_dir)}")
        return
    
    # Tomar las primeras 2 canciones
    songs_to_process = audio_files[:400]
    
    print(f"🎵 Procesando {len(songs_to_process)} canciones:")
    for i, song in enumerate(songs_to_process, 1):
        print(f"   {i}. {song}")
    
    # Generar espectrogramas
    for song in songs_to_process:
        audio_path = os.path.join(previews_dir, song)
        
        try:
            # Nombre del archivo de salida dentro de la carpeta spectrograms_output
            base_name = os.path.splitext(song)[0]
            output_path = os.path.join(output_dir, f"{base_name}_spectrogram.png")
            
            print(f"\n🔄 Procesando: {song}")
            save_spectrogram_png(
                audio_path=audio_path,
                output_path=output_path,
                title=f"Espectrograma - {base_name}"
            )
            
        except Exception as e:
            print(f"❌ Error procesando {song}: {e}")
    
    print(f"\n🎉 ¡Procesamiento completado!")
    print(f"📂 Los archivos PNG se guardaron en: {os.path.abspath(output_dir)}")

if __name__ == "__main__":
    generar_espectrogramas()


