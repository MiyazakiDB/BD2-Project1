#!/bin/bash

REPO_URL="https://github.com/SweIsHere/previewData.git"
AUDIO_FOLDER="Mainpreviews"              # Carpeta dentro del repo remoto
DEST_FOLDER="./MFCC-BETA/previews"           # Carpeta local para guardar los audios

# === CREAR CARPETA TEMPORAL ===
TEMP_DIR=$(mktemp -d)
echo "Usando carpeta temporal: $TEMP_DIR"

cd "$TEMP_DIR"

# === CLONAR SOLO ESTRUCTURA DEL REPO ===
git clone --filter=blob:none --no-checkout "$REPO_URL" repo-audios
cd repo-audios

# === HABILITAR SPARSE CHECKOUT ===
git sparse-checkout init --cone
git sparse-checkout set "$AUDIO_FOLDER"

# === EXTRAER SOLO LOS AUDIOS ===
mkdir -p "$DEST_FOLDER"
cp "$AUDIO_FOLDER"/*.{mp3,wav} "$DEST_FOLDER" 2>/dev/null

echo "Audios copiados a $DEST_FOLDER"

# === LIMPIAR ===
cd ../
rm -rf "$TEMP_DIR"
echo "🧹 Carpeta temporal eliminada"
