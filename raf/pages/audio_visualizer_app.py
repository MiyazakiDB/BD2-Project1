import streamlit as st
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
from pathlib import Path

# === CONFIGURACIÓN INICIAL DE STREAMLIT ===
st.set_page_config(
    page_title="🎵 Audio Visualizer & Comparator",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/MiyazakiDB/BD2-Project1',
        'Report a bug': None,
        'About': "# 🎵 Audio Visualizer & Comparator\nAnálisis temporal y comparación de audios con MFCC y espectrogramas.\n\nDesarrollado para BD2-Project1"
    }
)

# Configuración de matplotlib para Streamlit
plt.style.use('default')
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'

# Ocultar warning de deprecated functions
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

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
    base_dir = Path(__file__).resolve().parent.parent

    
    # DEBUG: Mostrar información de rutas
    st.sidebar.write("🔍 **DEBUG - Información de rutas:**")
    st.sidebar.write(f"📁 Archivo actual: `{Path(__file__)}`")
    st.sidebar.write(f"📁 Directorio base: `{base_dir}`")
    st.sidebar.write(f"📁 Directorio base absoluto: `{base_dir.absolute()}`")
    st.sidebar.markdown("---")
    
    audio_dirs = {
    "media_queries": base_dir / "media_queries",
    "rawdata": base_dir / "rawdata"
}
    
    available_dirs = {}
    
    # DEBUG: Verificar cada directorio
    st.sidebar.write("🔍 **DEBUG - Verificación de directorios:**")
    for name, path in audio_dirs.items():
        st.sidebar.write(f"📂 **{name}:**")
        st.sidebar.write(f"   Ruta: `{path}`")
        st.sidebar.write(f"   Absoluta: `{path.absolute()}`")
        st.sidebar.write(f"   Existe: {path.exists()}")
        
        if path.exists():
            # Buscar archivos de audio
            wav_files = list(path.glob("*.wav"))
            mp3_files = list(path.glob("*.mp3"))
            flac_files = list(path.glob("*.flac"))
            m4a_files = list(path.glob("*.m4a"))
            
            all_audio_files = wav_files + mp3_files + flac_files + m4a_files
            
            st.sidebar.write(f"   WAV: {len(wav_files)} archivos")
            st.sidebar.write(f"   MP3: {len(mp3_files)} archivos")
            st.sidebar.write(f"   FLAC: {len(flac_files)} archivos")
            st.sidebar.write(f"   M4A: {len(m4a_files)} archivos")
            st.sidebar.write(f"   **Total: {len(all_audio_files)} archivos**")
            
            # Mostrar algunos nombres de archivos si existen
            if all_audio_files:
                st.sidebar.write("   Ejemplos:")
                for i, file in enumerate(all_audio_files[:3]):  # Mostrar solo los primeros 3
                    st.sidebar.write(f"   - {file.name}")
                if len(all_audio_files) > 3:
                    st.sidebar.write(f"   - ... y {len(all_audio_files) - 3} más")
                
                available_dirs[name] = {
                    "path": path,
                    "files": [f.name for f in all_audio_files],
                    "count": len(all_audio_files)
                }
            else:
                st.sidebar.write("   ❌ No se encontraron archivos de audio")
        else:
            st.sidebar.write("   ❌ El directorio no existe")
        
        st.sidebar.write("---")
    
    # DEBUG: Resultado final
    st.sidebar.write("🎯 **DEBUG - Resultado final:**")
    st.sidebar.write(f"Directorios disponibles: {len(available_dirs)}")
    for name, info in available_dirs.items():
        st.sidebar.write(f"- {name}: {info['count']} archivos")
    
    return available_dirs

# === INICIALIZACIÓN DE STREAMLIT ===

def init_streamlit():
    """Inicializar estado de la sesión de Streamlit"""
    # Inicializar variables de estado si no existen
    if 'audio_loaded' not in st.session_state:
        st.session_state.audio_loaded = False
    
    if 'current_audio_path' not in st.session_state:
        st.session_state.current_audio_path = None
    
    if 'analysis_mode' not in st.session_state:
        st.session_state.analysis_mode = "🔍 Análisis Individual"
    
    if 'show_advanced' not in st.session_state:
        st.session_state.show_advanced = False

# === INTERFAZ STREAMLIT ===

def main():
    # Inicializar Streamlit
    init_streamlit()
    
    # Header principal
    st.title("🎵 Audio Visualizer & Comparator")
    st.markdown("### Análisis temporal y comparación de audios")
    
    # Mostrar información del sistema
    with st.expander("ℹ️ Información del Sistema", expanded=False):
        st.markdown("""
        **🎯 Funciones disponibles:**
        - 🔍 Análisis individual de audios
        - ⚖️ Comparación lado a lado
        - 🎵 Visualizador interactivo con navegación temporal
        - 📊 Múltiples tipos de visualización (Waveform, Spectrograma, MFCC, etc.)
        
        **📁 Formatos soportados:** WAV, MP3, FLAC, M4A
        """)
    
    # Sidebar para configuración
    st.sidebar.header("⚙️ Configuración")
    st.sidebar.markdown("---")
    
    # Escanear directorios disponibles
    audio_dirs = scan_audio_directories()
    
    # DEBUG: Mostrar resultado del escaneo
    st.write("🔍 **DEBUG - Resultado del escaneo:**")
    if audio_dirs:
        st.success(f"✅ Se encontraron {len(audio_dirs)} directorios con archivos de audio")
        for name, info in audio_dirs.items():
            st.write(f"- **{name}**: {info['count']} archivos en `{info['path']}`")
    else:
        st.error("❌ No se encontraron directorios con archivos de audio")
        st.write("**Posibles causas:**")
        st.write("1. Los directorios no existen")
        st.write("2. Los directorios existen pero están vacíos") 
        st.write("3. Los archivos no tienen las extensiones esperadas (.wav, .mp3, .flac, .m4a)")
        st.write("4. Problema con las rutas relativas")
    
    if not audio_dirs:
        # Si no se detectan audios en previews o audio_to_see, mostrar rutas donde agregar archivos
        base_dir = Path(__file__).parent  # CORRECCIÓN: mismo nivel que VIsualizers
        dir1 = base_dir / "media_queries"
        st.warning("❌ No se encontraron archivos de audio en las carpetas configuradas.")
        st.info("💡 Coloca archivos de audio en la siguiente ruta:")
        st.code(f"{dir1}")      

        
        # Botón para crear directorios si no existen
        if st.button("🛠️ Crear directorios faltantes"):
            created = []
            for name, path in [("media_queries", dir1)]:
                if not path.exists():
                    try:
                        path.mkdir(parents=True, exist_ok=True)
                        created.append(name)
                        st.success(f"✅ Directorio '{name}' creado en: {path}")
                    except Exception as e:
                        st.error(f"❌ Error creando directorio '{name}': {e}")
                else:
                    st.info(f"ℹ️ Directorio '{name}' ya existe")
            
            if created:
                st.success("🎉 ¡Directorios creados! Ahora coloca tus archivos de audio en ellos y recarga la página.")
                st.experimental_rerun()
        
        st.info("También puedes subir un archivo manualmente a continuación:")
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
            [
                "🔊 Forma de Onda", 
                "🎵 Forma de Onda Interactiva", 
                " Forma de Onda con Marcadores",
                "📊 Forma de Onda por Segmentos",
                "🎛️ Espectrograma",
                "🎚️ Mel-Spectrograma", 
                "🎶 MFCC"
            ],
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
                        
                    elif viz == " Forma de Onda Interactiva":
                        st.subheader("🎵 Forma de Onda Interactiva")
                        fig, stats = plot_interactive_waveform(str(audio_path), f"Forma de Onda Interactiva - {selected_file}")
                        st.pyplot(fig)
                        plt.close()
                        
                        # Mostrar estadísticas del segmento
                        st.info("📊 **Estadísticas del segmento:**")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Duración", f"{stats['segment_duration']:.2f}s")
                            st.metric("Máx. Amplitud", f"{stats['max_amplitude']:.3f}")
                        with col2:
                            st.metric("Mín. Amplitud", f"{stats['min_amplitude']:.3f}")
                            st.metric("Media", f"{stats['mean_amplitude']:.3f}")
                        with col3:
                            st.metric("RMS", f"{stats['rms']:.3f}")
                            st.metric("Muestras", stats['samples_shown'])
                        
                    elif viz == "🎯 Forma de Onda con Marcadores":
                        st.subheader("🎯 Forma de Onda con Marcadores de Tiempo")
                        fig = plot_waveform_with_markers(str(audio_path), f"Forma de Onda con Marcadores - {selected_file}")
                        st.pyplot(fig)
                        plt.close()
                        
                    elif viz == "📊 Forma de Onda por Segmentos":
                        st.subheader("📊 Forma de Onda por Segmentos")
                        segment_duration = st.selectbox(
                            "Duración de cada segmento (segundos):",
                            [2, 5, 10, 15, 30],
                            index=1,
                            key="segment_duration"
                        )
                        fig = plot_waveform_segments(str(audio_path), segment_duration, f"Segmentos - {selected_file}")
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

def plot_interactive_waveform(audio_path, title="Forma de Onda Interactiva"):
    """🎵 Visualizador interactivo de forma de onda con navegación temporal"""
    y, sr = librosa.load(audio_path, sr=None)
    duration = librosa.get_duration(y=y, sr=sr)
    
    # Crear controles de tiempo
    st.subheader("🎛️ Control de Tiempo")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        start_time = st.slider(
            "⏪ Tiempo inicio (segundos)", 
            0.0, 
            max(0.0, duration - 1.0), 
            0.0, 
            step=0.1,
            key="start_time"
        )
    
    with col2:
        window_size = st.selectbox(
            "⏳ Ventana de tiempo",
            [1, 2, 5, 10, 15, 30],
            index=2,
            key="window_size"
        )
    
    with col3:
        zoom_level = st.selectbox(
            "🔍 Nivel de zoom",
            ["Normal", "2x", "4x", "8x"],
            index=0,
            key="zoom_level"
        )
    
    # Calcular ventana de tiempo
    end_time = min(start_time + window_size, duration)
    start_sample = int(start_time * sr)
    end_sample = int(end_time * sr)
    
    # Extraer segmento de audio
    y_segment = y[start_sample:end_sample]
    time_axis = np.linspace(start_time, end_time, len(y_segment))
    
    # Aplicar zoom
    zoom_factor = {"Normal": 1, "2x": 2, "4x": 4, "8x": 8}[zoom_level]
    if zoom_factor > 1:
        zoom_samples = len(y_segment) // zoom_factor
        mid_point = len(y_segment) // 2
        zoom_start = max(0, mid_point - zoom_samples // 2)
        zoom_end = min(len(y_segment), mid_point + zoom_samples // 2)
        y_segment = y_segment[zoom_start:zoom_end]
        time_axis = time_axis[zoom_start:zoom_end]
    
    # Crear el gráfico
    fig, ax = plt.subplots(figsize=(15, 6))
    ax.plot(time_axis, y_segment, linewidth=0.5, alpha=0.8)
    ax.set_xlabel('Tiempo (segundos)')
    ax.set_ylabel('Amplitud')
    ax.set_title(f'{title} - {start_time:.1f}s a {end_time:.1f}s (Zoom: {zoom_level})')
    ax.grid(True, alpha=0.3)
    
    # Estadísticas del segmento
    ax.axhline(y=np.max(y_segment), color='red', linestyle='--', alpha=0.7, label=f'Máx: {np.max(y_segment):.3f}')
    ax.axhline(y=np.min(y_segment), color='blue', linestyle='--', alpha=0.7, label=f'Mín: {np.min(y_segment):.3f}')
    ax.axhline(y=np.mean(y_segment), color='green', linestyle='--', alpha=0.7, label=f'Media: {np.mean(y_segment):.3f}')
    ax.legend()
    
    plt.tight_layout()
    return fig, {
        "segment_duration": end_time - start_time,
        "max_amplitude": np.max(y_segment),
        "min_amplitude": np.min(y_segment),
        "mean_amplitude": np.mean(y_segment),
        "rms": np.sqrt(np.mean(y_segment**2)),
        "samples_shown": len(y_segment)
    }

def plot_waveform_with_markers(audio_path, title="Forma de Onda con Marcadores"):
    """🎯 Visualizador de forma de onda con marcadores de tiempo cada segundo"""
    y, sr = librosa.load(audio_path, sr=None)
    duration = librosa.get_duration(y=y, sr=sr)
    time_axis = np.linspace(0, duration, len(y))
    
    fig, ax = plt.subplots(figsize=(15, 6))
    ax.plot(time_axis, y, linewidth=0.3, alpha=0.8, color='blue')
    
    # Agregar marcadores cada segundo
    for second in range(int(duration) + 1):
        ax.axvline(x=second, color='red', linestyle='--', alpha=0.5, linewidth=1)
        ax.text(second, ax.get_ylim()[1] * 0.9, f'{second}s', 
                rotation=90, fontsize=8, alpha=0.7)
    
    # Marcadores cada 10 segundos más prominentes
    for ten_sec in range(0, int(duration) + 1, 10):
        ax.axvline(x=ten_sec, color='darkred', linestyle='-', alpha=0.8, linewidth=2)
        ax.text(ten_sec, ax.get_ylim()[1] * 0.95, f'{ten_sec}s', 
                rotation=0, fontsize=10, fontweight='bold', alpha=0.9)
    
    ax.set_xlabel('Tiempo (segundos)')
    ax.set_ylabel('Amplitud')
    ax.set_title(f'{title} - Duración total: {duration:.2f}s')
    ax.grid(True, alpha=0.2)
    
    plt.tight_layout()
    return fig

def plot_waveform_segments(audio_path, segment_duration=5, title="Forma de Onda por Segmentos"):
    """📊 Visualizador que divide la canción en segmentos de tiempo específico"""
    y, sr = librosa.load(audio_path, sr=None)
    duration = librosa.get_duration(y=y, sr=sr)
    
    # Calcular número de segmentos
    num_segments = int(np.ceil(duration / segment_duration))
    
    # Crear subplots
    fig, axes = plt.subplots(num_segments, 1, figsize=(15, 3 * num_segments))
    if num_segments == 1:
        axes = [axes]
    
    for i in range(num_segments):
        start_time = i * segment_duration
        end_time = min((i + 1) * segment_duration, duration)
        
        start_sample = int(start_time * sr)
        end_sample = int(end_time * sr)
        
        y_segment = y[start_sample:end_sample]
        time_axis = np.linspace(start_time, end_time, len(y_segment))
        
        axes[i].plot(time_axis, y_segment, linewidth=0.5)
        axes[i].set_title(f'Segmento {i+1}: {start_time:.1f}s - {end_time:.1f}s')
        axes[i].set_xlabel('Tiempo (segundos)')
        axes[i].set_ylabel('Amplitud')
        axes[i].grid(True, alpha=0.3)
        
        # Estadísticas del segmento
        rms = np.sqrt(np.mean(y_segment**2))
        axes[i].text(0.02, 0.95, f'RMS: {rms:.3f}', transform=axes[i].transAxes, 
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
    
    plt.tight_layout()
    return fig

# === PUNTO DE ENTRADA PRINCIPAL ===
# Ejecutar la interfaz al cargar la página en Streamlit
main()

