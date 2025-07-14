import streamlit as st
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
from pathlib import Path
import time

# Configuración de la página
st.set_page_config(
    page_title="🎵 Audio Visualizer & Comparator",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === FUNCIONES DE VISUALIZACIÓN ===

def plot_waveform(audio_path, title="Forma de Onda"):
    """🔊 Visualizar forma de onda"""
    y, sr = librosa.load(audio_path, sr=None)
    
    fig, ax = plt.subplots(figsize=(12, 3))
    librosa.display.waveshow(y, sr=sr, ax=ax)
    ax.set_title(title)
    plt.tight_layout()
    return fig

def plot_spectrogram(audio_path, title="Espectrograma"):
    """🎛️ Visualizar espectrograma"""
    y, sr = librosa.load(audio_path, sr=None)
    S = librosa.stft(y)
    S_db = librosa.amplitude_to_db(abs(S))

    fig, ax = plt.subplots(figsize=(12, 4))
    img = librosa.display.specshow(S_db, sr=sr, x_axis='time', y_axis='log', ax=ax)
    fig.colorbar(img, ax=ax, format="%+2.0f dB")
    ax.set_title(title)
    plt.tight_layout()
    return fig

def plot_mel_spectrogram(audio_path, title="Mel-Spectrograma"):
    """🎚️ Visualizar mel-spectrograma"""
    y, sr = librosa.load(audio_path, sr=None)
    S = librosa.feature.melspectrogram(y=y, sr=sr)
    S_db = librosa.power_to_db(S, ref=np.max)

    fig, ax = plt.subplots(figsize=(12, 4))
    img = librosa.display.specshow(S_db, sr=sr, x_axis='time', y_axis='mel', ax=ax)
    fig.colorbar(img, ax=ax, format="%+2.0f dB")
    ax.set_title(title)
    plt.tight_layout()
    return fig

def plot_mfcc(audio_path, title="MFCC"):
    """🎶 Visualizar MFCCs"""
    y, sr = librosa.load(audio_path, sr=None)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)

    fig, ax = plt.subplots(figsize=(12, 4))
    img = librosa.display.specshow(mfcc, sr=sr, x_axis='time', ax=ax)
    fig.colorbar(img, ax=ax)
    ax.set_title(title)
    plt.tight_layout()
    return fig

def compare_mfccs(path1, path2, name1="Audio 1", name2="Audio 2"):
    """🔀 Comparar MFCCs lado a lado"""
    y1, sr1 = librosa.load(path1, sr=None)
    y2, sr2 = librosa.load(path2, sr=None)

    mfcc1 = librosa.feature.mfcc(y=y1, sr=sr1, n_mfcc=13)
    mfcc2 = librosa.feature.mfcc(y=y2, sr=sr2, n_mfcc=13)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
    
    img1 = librosa.display.specshow(mfcc1, sr=sr1, x_axis='time', ax=ax1)
    ax1.set_title(f"MFCC - {name1}")
    fig.colorbar(img1, ax=ax1)

    img2 = librosa.display.specshow(mfcc2, sr=sr2, x_axis='time', ax=ax2)
    ax2.set_title(f"MFCC - {name2}")
    fig.colorbar(img2, ax=ax2)
    
    plt.tight_layout()
    return fig

def compare_spectrograms(path1, path2, name1="Audio 1", name2="Audio 2"):
    """🔀 Comparar espectrogramas lado a lado"""
    y1, sr1 = librosa.load(path1, sr=None)
    y2, sr2 = librosa.load(path2, sr=None)

    S1 = librosa.stft(y1)
    S1_db = librosa.amplitude_to_db(abs(S1))
    
    S2 = librosa.stft(y2)
    S2_db = librosa.amplitude_to_db(abs(S2))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
    
    img1 = librosa.display.specshow(S1_db, sr=sr1, x_axis='time', y_axis='log', ax=ax1)
    ax1.set_title(f"Espectrograma - {name1}")
    fig.colorbar(img1, ax=ax1, format="%+2.0f dB")

    img2 = librosa.display.specshow(S2_db, sr=sr2, x_axis='time', y_axis='log', ax=ax2)
    ax2.set_title(f"Espectrograma - {name2}")
    fig.colorbar(img2, ax=ax2, format="%+2.0f dB")
    
    plt.tight_layout()
    return fig

def get_audio_info(audio_path):
    """📊 Obtener información básica del audio"""
    y, sr = librosa.load(audio_path, sr=None)
    duration = librosa.get_duration(y=y, sr=sr)
    
    # Estimar tempo usando la nueva función de librosa.feature.rhythm
    try:
        tempo_est = librosa.feature.rhythm.tempo(y=y, sr=sr)[0]
        tempo_str = f"{tempo_est:.1f} BPM"
    except Exception:
        tempo_str = "Desconocido"
    return {
        "Duración": f"{duration:.2f} segundos",
        "Sample Rate": f"{sr} Hz",
        "Tamaño": f"{len(y)} muestras",
        "Channels": "Mono (convertido)",
        "Tempo estimado": tempo_str
    }

# === FUNCIONES DE DIRECTORIO ===

def scan_audio_directories():
    """🔍 Escanear directorios de audio disponibles"""
    base_dir = Path(__file__).parent.parent
    
    audio_dirs = {
        "previews": base_dir / "previews",
        "audio_to_see": base_dir / "audio_to_see", 
        "rawdata": base_dir / "rawdata"
    }
    
    available_dirs = {}
    for name, path in audio_dirs.items():
        if path.exists():
            audio_files = list(path.glob("*.wav")) + list(path.glob("*.mp3")) + \
                         list(path.glob("*.flac")) + list(path.glob("*.m4a"))
            if audio_files:
                available_dirs[name] = {
                    "path": path,
                    "files": [f.name for f in audio_files],
                    "count": len(audio_files)
                }
    
    return available_dirs

# === INTERFAZ STREAMLIT ===

def main():
    st.title("🎵 Audio Visualizer & Comparator")
    st.markdown("### Análisis temporal y comparación de audios")
    
    # Sidebar para configuración
    st.sidebar.header("⚙️ Configuración")
    
    # Escanear directorios disponibles
    audio_dirs = scan_audio_directories()
    
    if not audio_dirs:
        st.warning("❌ No se encontraron directorios con archivos de audio. Puedes subir un archivo manualmente:")
        uploaded_file = st.file_uploader("Sube un archivo de audio", type=["wav","mp3","flac","m4a"])
        if uploaded_file is not None:
            # Guardar archivo temporal para análisis
            import tempfile
            suffix = os.path.splitext(uploaded_file.name)[1]
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp.write(uploaded_file.read())
            tmp.close()
            # Procesar análisis individual directamente
            st.audio(tmp.name)
            st.subheader("📊 Información del Audio Subido")
            info = get_audio_info(tmp.name)
            st.json(info)
            st.subheader("📈 Visualizaciones")
            fig1 = plot_waveform(tmp.name, "Forma de Onda")
            st.pyplot(fig1)
            fig2 = plot_spectrogram(tmp.name, "Espectrograma")
            st.pyplot(fig2)
            fig3 = plot_mel_spectrogram(tmp.name, "Mel-Spectrograma")
            st.pyplot(fig3)
            fig4 = plot_mfcc(tmp.name, "MFCC")
            st.pyplot(fig4)
        else:
            st.stop()
        return
    
    # Mostrar directorios disponibles
    st.sidebar.write("📁 **Directorios disponibles:**")
    for dir_name, info in audio_dirs.items():
        st.sidebar.write(f"- **{dir_name}**: {info['count']} archivos")
    
    # Modo de operación
    mode = st.sidebar.selectbox(
        "🎯 Modo de operación",
        ["🔍 Análisis Individual", "⚖️ Comparación de Audios"]
    )
    
    if mode == "🔍 Análisis Individual":
        single_audio_analysis(audio_dirs)
    else:
        audio_comparison(audio_dirs)

def single_audio_analysis(audio_dirs):
    """🔍 Análisis de un solo audio"""
    st.header("🔍 Análisis Individual de Audio")
    
    # Selección de directorio
    selected_dir = st.selectbox(
        "📂 Selecciona directorio",
        list(audio_dirs.keys()),
        format_func=lambda x: f"{x} ({audio_dirs[x]['count']} archivos)"
    )
    
    # Selección de archivo
    selected_file = st.selectbox(
        "🎵 Selecciona archivo",
        audio_dirs[selected_dir]["files"]
    )
    
    if selected_file:
        audio_path = audio_dirs[selected_dir]["path"] / selected_file
        
        # Información del archivo
        st.subheader("📊 Información del Audio")
        info = get_audio_info(str(audio_path))
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Duración", info["Duración"])
            st.metric("Sample Rate", info["Sample Rate"])
        with col2:
            st.metric("Tamaño", info["Tamaño"])
            st.metric("Channels", info["Channels"])
        with col3:
            st.metric("Tempo", info["Tempo estimado"])
        
        # Reproducir audio
        st.subheader("🔊 Reproducir Audio")
        st.audio(str(audio_path))
        
        # Selección de visualizaciones
        st.subheader("📈 Visualizaciones")
        
        viz_options = st.multiselect(
            "Selecciona las visualizaciones que quieres ver:",
            ["🔊 Forma de Onda", "🎛️ Espectrograma", "🎚️ Mel-Spectrograma", "🎶 MFCC"],
            default=["🔊 Forma de Onda", "🎛️ Espectrograma"]
        )
        
        if st.button("🚀 Generar Visualizaciones"):
            with st.spinner("Procesando audio..."):
                progress_bar = st.progress(0)
                
                for i, viz in enumerate(viz_options):
                    if viz == "🔊 Forma de Onda":
                        st.subheader("🔊 Forma de Onda")
                        fig = plot_waveform(str(audio_path), f"Forma de Onda - {selected_file}")
                        st.pyplot(fig)
                        plt.close()
                        
                    elif viz == "🎛️ Espectrograma":
                        st.subheader("🎛️ Espectrograma")
                        fig = plot_spectrogram(str(audio_path), f"Espectrograma - {selected_file}")
                        st.pyplot(fig)
                        plt.close()
                        
                    elif viz == "🎚️ Mel-Spectrograma":
                        st.subheader("🎚️ Mel-Spectrograma")
                        fig = plot_mel_spectrogram(str(audio_path), f"Mel-Spectrograma - {selected_file}")
                        st.pyplot(fig)
                        plt.close()
                        
                    elif viz == "🎶 MFCC":
                        st.subheader("🎶 MFCC")
                        fig = plot_mfcc(str(audio_path), f"MFCC - {selected_file}")
                        st.pyplot(fig)
                        plt.close()
                    
                    progress_bar.progress((i + 1) / len(viz_options))
                
                st.success("✅ ¡Visualizaciones completadas!")

def audio_comparison(audio_dirs):
    """⚖️ Comparación de dos audios"""
    st.header("⚖️ Comparación de Audios")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎵 Audio 1")
        dir1 = st.selectbox(
            "📂 Directorio 1",
            list(audio_dirs.keys()),
            key="dir1"
        )
        file1 = st.selectbox(
            "🎵 Archivo 1",
            audio_dirs[dir1]["files"],
            key="file1"
        )
        
        if file1:
            audio_path1 = audio_dirs[dir1]["path"] / file1
            st.audio(str(audio_path1))
    
    with col2:
        st.subheader("🎵 Audio 2")
        dir2 = st.selectbox(
            "📂 Directorio 2",
            list(audio_dirs.keys()),
            key="dir2"
        )
        file2 = st.selectbox(
            "🎵 Archivo 2",
            audio_dirs[dir2]["files"],
            key="file2"
        )
        
        if file2:
            audio_path2 = audio_dirs[dir2]["path"] / file2
            st.audio(str(audio_path2))
    
    if file1 and file2:
        # Comparación temporal
        st.subheader("⏱️ Comparación Temporal")
        
        comparison_type = st.selectbox(
            "🔀 Tipo de comparación",
            ["🎶 MFCCs", "🎛️ Espectrogramas", "📊 Información Básica"]
        )
        
        if st.button("🚀 Comparar Audios"):
            with st.spinner("Comparando audios..."):
                if comparison_type == "🎶 MFCCs":
                    st.subheader("🎶 Comparación de MFCCs")
                    fig = compare_mfccs(
                        str(audio_path1), str(audio_path2),
                        name1=file1, name2=file2
                    )
                    st.pyplot(fig)
                    plt.close()
                    
                elif comparison_type == "🎛️ Espectrogramas":
                    st.subheader("🎛️ Comparación de Espectrogramas")
                    fig = compare_spectrograms(
                        str(audio_path1), str(audio_path2),
                        name1=file1, name2=file2
                    )
                    st.pyplot(fig)
                    plt.close()
                    
                elif comparison_type == "📊 Información Básica":
                    st.subheader("📊 Comparación de Características")
                    
                    info1 = get_audio_info(str(audio_path1))
                    info2 = get_audio_info(str(audio_path2))
                    
                    comparison_df = pd.DataFrame({
                        file1: list(info1.values()),
                        file2: list(info2.values())
                    }, index=list(info1.keys()))
                    
                    st.dataframe(comparison_df)
                
                st.success("✅ ¡Comparación completada!")

# === PÁGINA PRINCIPAL ===

if __name__ == "__main__":
    main()
