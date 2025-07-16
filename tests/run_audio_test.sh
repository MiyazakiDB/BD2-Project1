#!/bin/bash

# Definir directorios
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATASETS_DIR="${SCRIPT_DIR}/datasets"
REPO_URL="https://github.com/Ianskev/previews_dataset.git"
REPO_DIR="${DATASETS_DIR}/previews_dataset"
TEST_AUDIO_DIR="${REPO_DIR}/test_audio"
PREVIEWS_DIR="${REPO_DIR}/previews"

# Crear directorio datasets si no existe
mkdir -p "${DATASETS_DIR}"

echo "==== Iniciando descarga y configuración del dataset de audio ===="
echo ""

# Verificar si el repositorio ya está clonado
if [ -d "${REPO_DIR}" ]; then
    echo "El repositorio ${REPO_DIR} ya existe. Se omitirá la clonación."
else
    # Clonar el repositorio con protección de hooks desactivada
    echo "Clonando repositorio ${REPO_URL}..."
    GIT_CLONE_PROTECTION_ACTIVE=false git clone "${REPO_URL}" "${REPO_DIR}"
    if [ $? -ne 0 ]; then
        # Verificar si la clonación parcial ocurrió y el directorio existe
        if [ ! -d "${REPO_DIR}" ] || [ ! -d "${REPO_DIR}/test_audio" ]; then
            echo "Error: No se pudo clonar el repositorio."
            exit 1
        else
            echo "El repositorio se clonó parcialmente, intentando continuar..."
        fi
    fi
fi

# Crear directorio para las previews
mkdir -p "${PREVIEWS_DIR}"

# Verificar si el ZIP existe y moverlo a la carpeta previews
if [ -f "${REPO_DIR}/previews.zip" ]; then
    echo "Moviendo previews.zip a la carpeta previews..."
    mv "${REPO_DIR}/previews.zip" "${PREVIEWS_DIR}/"
    
    # Verificar si se movió correctamente
    if [ -f "${PREVIEWS_DIR}/previews.zip" ]; then
        echo "Extrayendo archivo previews.zip en la carpeta previews..."
        # Extraer el ZIP en la carpeta previews
        unzip -o -q "${PREVIEWS_DIR}/previews.zip" -d "${PREVIEWS_DIR}"
        if [ $? -ne 0 ]; then
            echo "Error: No se pudo extraer el archivo de previews."
            exit 1
        fi
        
        # Borrar el ZIP después de extraer
        echo "Borrando archivo ZIP..."
        rm "${PREVIEWS_DIR}/previews.zip"
    else
        echo "Error: No se pudo mover el archivo previews.zip"
        exit 1
    fi
elif [ -f "${PREVIEWS_DIR}/previews.zip" ]; then
    # Si el ZIP ya está en la carpeta previews
    echo "Extrayendo archivo previews.zip en la carpeta previews..."
    unzip -o -q "${PREVIEWS_DIR}/previews.zip" -d "${PREVIEWS_DIR}"
    if [ $? -ne 0 ]; then
        echo "Error: No se pudo extraer el archivo de previews."
        exit 1
    fi
    
    # Borrar el ZIP después de extraer
    echo "Borrando archivo ZIP..."
    rm "${PREVIEWS_DIR}/previews.zip"
else
    echo "No se encontró el archivo previews.zip. Verificando si los directorios necesarios existen..."
    
    if [ ! -d "${TEST_AUDIO_DIR}" ]; then
        echo "Error: No se encontró el directorio test_audio"
        exit 1
    fi
    
    if [ ! "$(ls -A "${PREVIEWS_DIR}" 2>/dev/null)" ]; then
        echo "Advertencia: La carpeta previews está vacía"
    else
        echo "La carpeta previews contiene archivos"
    fi
fi

echo "Archivos preparados correctamente."
echo "Audio de prueba en: ${TEST_AUDIO_DIR}"
echo "Dataset de previews en: ${PREVIEWS_DIR}"

# Ejecutar el test
echo "==== Ejecutando prueba de búsqueda en dataset de audio ===="
cd "${SCRIPT_DIR}"
python "${SCRIPT_DIR}/audio/audio_test.py"

echo "==== Proceso finalizado ====" 