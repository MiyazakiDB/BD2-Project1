#!/bin/bash

REPO_URL="https://github.com/SweIsHere/previewData.git"
AUDIO_FOLDER="Mainpreviews"              # Carpeta dentro del repo remoto
DEST_FOLDER="./MFCC-BETA/previews"                 # Carpeta local para guardar los audios

# === GUARDAR DIRECTORIO ORIGINAL ===
ORIGINAL_DIR=$(pwd)
echo "📁 Directorio original: $ORIGINAL_DIR"

# === CREAR CARPETA DESTINO EN EL DIRECTORIO ORIGINAL ===
mkdir -p "$ORIGINAL_DIR/$DEST_FOLDER"
echo "✅ Carpeta destino creada: $ORIGINAL_DIR/$DEST_FOLDER"

# === CREAR CARPETA TEMPORAL ===
TEMP_DIR=$(mktemp -d)
echo "📁 Usando carpeta temporal: $TEMP_DIR"

cd "$TEMP_DIR" || exit 1

# === CLONAR SOLO ESTRUCTURA DEL REPO ===
echo "📥 Clonando repositorio..."
git clone --filter=blob:none --no-checkout "$REPO_URL" repo-audios
cd repo-audios || exit 1

# === HABILITAR SPARSE CHECKOUT ===
echo "⚙️ Configurando sparse checkout..."
git sparse-checkout init --cone
git sparse-checkout set "$AUDIO_FOLDER"

# === CHECKOUT DE LOS ARCHIVOS ===
echo "📦 Descargando archivos..."
git checkout

# === VERIFICAR QUE EXISTE LA CARPETA ===
if [ ! -d "$AUDIO_FOLDER" ]; then
    echo "❌ Error: Carpeta '$AUDIO_FOLDER' no encontrada en el repositorio"
    cd "$ORIGINAL_DIR"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# === EXTRAER SOLO LOS AUDIOS (CON RUTA ABSOLUTA) ===
echo "🎵 Copiando archivos de audio..."
COPIED_COUNT=0

# Usar ruta absoluta del directorio original
FULL_DEST_PATH="$ORIGINAL_DIR/$DEST_FOLDER"

for file in "$AUDIO_FOLDER"/*.{mp3,wav,flac,m4a}; do
    if [ -f "$file" ]; then
        if cp "$file" "$FULL_DEST_PATH/"; then
            echo "✅ Copiado: $(basename "$file")"
            ((COPIED_COUNT++))
        else
            echo "⚠️ Error copiando: $(basename "$file")"
        fi
    fi
done

echo "📊 Total de archivos copiados: $COPIED_COUNT"
echo "📁 Destino: $FULL_DEST_PATH"

# === LIMPIAR ===
cd "$ORIGINAL_DIR"
rm -rf "$TEMP_DIR"
echo "🧹 Carpeta temporal eliminada"

# === VERIFICAR RESULTADO ===
if [ $COPIED_COUNT -gt 0 ]; then
    echo "✅ ¡Descarga completada exitosamente!"
    echo "📂 Archivos descargados:"
    ls -1 "$DEST_FOLDER" | head -5
    if [ $(ls -1 "$DEST_FOLDER" | wc -l) -gt 5 ]; then
        echo "..."
        echo "Total: $(ls -1 "$DEST_FOLDER" | wc -l) archivos"
    fi
else
    echo "❌ No se encontraron archivos de audio para copiar"
fi