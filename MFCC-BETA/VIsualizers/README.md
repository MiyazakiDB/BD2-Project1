# 🎵 Audio Visualizer & Comparator

## 📋 Instrucciones de Instalación y Uso

### 🔧 Dependencias necesarias

```bash
pip install streamlit librosa matplotlib numpy pandas
```

### 🚀 Cómo ejecutar la aplicación Streamlit

1. **Navegar al directorio:**
```bash
cd C:\Users\Holbi\Desktop\BD2-Project1\MFCC-BETA\VIsualizers
```

2. **Ejecutar la aplicación:**
```bash
streamlit run audio_visualizer_app.py
```

3. **Abrir en el navegador:**
- La aplicación se abrirá automáticamente en `http://localhost:8501`
- Si no se abre, ve manualmente a esa URL

### 📁 Estructura de directorios soportada

La aplicación escanea automáticamente estos directorios:

```
MFCC-BETA/
├── previews/          ← Archivos de audio principales
├── audio_to_see/      ← Archivos de prueba
├── rawdata/           ← Datos sin procesar
└── VIsualizers/
    ├── audio_visualizer_app.py    ← Aplicación Streamlit
    ├── spectrogram.py             ← Funciones de visualización
    └── spectrograms_output/       ← PNG generados
```

### 🎯 Funcionalidades disponibles

#### 🔍 Análisis Individual
- **Información del audio**: Duración, sample rate, tempo, etc.
- **Reproducción**: Escuchar el audio directamente
- **Visualizaciones**:
  - 🔊 Forma de onda (amplitud vs tiempo)
  - 🎛️ Espectrograma (frecuencia vs tiempo)
  - 🎚️ Mel-Spectrograma (perceptual)
  - 🎶 MFCC (características para ML)

#### ⚖️ Comparación de Audios
- **Comparación lado a lado** de dos audios
- **Tipos de comparación**:
  - 🎶 MFCCs comparados
  - 🎛️ Espectrogramas comparados
  - 📊 Información básica comparada

### 📊 Uso programático (sin interfaz)

También puedes usar las funciones directamente desde Python:

```python
from VIsualizers.spectrogram import *

# Visualizar un solo audio
audio_path = "../audio_to_see/The_Strokes_-_Reptilia.wav"
plot_all_audio_visualizations(audio_path)

# Comparar dos audios
audio1 = "../previews/cancion1.wav"
audio2 = "../previews/cancion2.wav"
compare_mfccs(audio1, audio2, "Canción 1", "Canción 2")
compare_spectrograms(audio1, audio2, "Canción 1", "Canción 2")
```

### 🎵 Formatos soportados

- ✅ WAV (.wav)
- ✅ MP3 (.mp3)
- ✅ FLAC (.flac)
- ✅ M4A (.m4a)

### 🔧 Resolución de problemas

**Error: "No se encontraron directorios"**
- Asegúrate de tener archivos de audio en las carpetas `previews/`, `audio_to_see/` o `rawdata/`

**Error: "Module not found"**
- Instala las dependencias: `pip install streamlit librosa matplotlib`

**La aplicación no se abre**
- Verifica que no haya otro proceso usando el puerto 8501
- Usa `streamlit run audio_visualizer_app.py --server.port 8502` para cambiar puerto

### 🎨 Características de la interfaz

- **Sidebar**: Configuración y selección de archivos
- **Modo responsivo**: Se adapta a diferentes tamaños de pantalla
- **Progreso visual**: Barras de progreso durante el procesamiento
- **Audio embebido**: Reproducir archivos directamente en la interfaz
- **Comparación temporal**: Análisis lado a lado en tiempo real

### 💡 Tips de uso

1. **Para mejores resultados**: Usa archivos WAV sin comprimir
2. **Rendimiento**: Los archivos más cortos se procesan más rápido
3. **Comparaciones**: Compara audios de similar duración para mejor visualización
4. **Guardado**: Los gráficos se pueden descargar con clic derecho → "Guardar imagen"

¡Disfruta analizando y comparando tus audios! 🎧
