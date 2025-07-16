#!/bin/bash

# Definir directorios
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATASETS_DIR="${SCRIPT_DIR}/datasets"
REPO_URL="https://github.com/Ianskev/mnist_dataset.git"
REPO_DIR="${DATASETS_DIR}/mnist_dataset"
NUMBERS_DIR="${REPO_DIR}/numbers"

# Crear directorio datasets si no existe
mkdir -p "${DATASETS_DIR}"

echo "==== Iniciando descarga y configuración del dataset MNIST ===="
echo ""

# Verificar si el repositorio ya está clonado
if [ -d "${REPO_DIR}" ]; then
    echo "El repositorio ${REPO_DIR} ya existe. Se omitirá la clonación."
else
    # Clonar el repositorio
    echo "Clonando repositorio ${REPO_URL}..."
    git clone "${REPO_URL}" "${REPO_DIR}"
    if [ $? -ne 0 ]; then
        echo "Error: No se pudo clonar el repositorio."
        exit 1
    fi
fi

# Crear directorio para las imágenes
mkdir -p "${NUMBERS_DIR}"

# Verificar si existe el archivo ZIP y extraerlo siempre que numbers tenga menos de 10 archivos
if [ -f "${REPO_DIR}/numbers.zip" ] && [ $(find "${NUMBERS_DIR}" -type f | wc -l) -lt 10 ]; then
    echo "Extrayendo dataset MNIST en carpeta numbers..."
    # Limpiar el directorio numbers en caso tenga archivos parciales
    rm -rf "${NUMBERS_DIR:?}"/*
    
    # Extraer el archivo ZIP
    unzip -o -j -q "${REPO_DIR}/numbers.zip" -d "${NUMBERS_DIR}"
    
    # Verificar si la extracción fue exitosa
    if [ $? -eq 0 ] && [ -n "$(ls -A "${NUMBERS_DIR}" 2>/dev/null)" ]; then
        echo "Extracción completada correctamente."
        # Borrar el ZIP después de extraer exitosamente
        rm "${REPO_DIR}/numbers.zip"
        echo "Archivo ZIP eliminado."
    else
        echo "Error: Falló la extracción del dataset MNIST."
    fi
else
    if [ -n "$(ls -A "${NUMBERS_DIR}" 2>/dev/null)" ]; then
        echo "El dataset MNIST ya está extraído en ${NUMBERS_DIR}."
        
        # Si el ZIP sigue existiendo, eliminarlo
        if [ -f "${REPO_DIR}/numbers.zip" ]; then
            echo "Eliminando archivo ZIP redundante..."
            rm "${REPO_DIR}/numbers.zip"
        fi
    else
        echo "Advertencia: No se encontró el archivo numbers.zip en el repositorio."
    fi
fi

echo "Archivos preparados correctamente."
echo "Imagen de prueba en: ${REPO_DIR}/test_image"
echo "Dataset MNIST en: ${NUMBERS_DIR}"

# Ejecutar el test
echo "==== Ejecutando prueba de búsqueda en dataset MNIST ===="
cd "${SCRIPT_DIR}"
python "${SCRIPT_DIR}/image/mnist_test.py"

echo "==== Proceso finalizado ====" 