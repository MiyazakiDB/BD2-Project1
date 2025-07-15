#!/bin/bash

# Definir directorios
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_URL="https://github.com/Ianskev/mnist_dataset.git"
REPO_DIR="${SCRIPT_DIR}/mnist_dataset"
NUMBERS_DIR="${REPO_DIR}/numbers"

echo "==== Iniciando descarga y configuración del dataset MNIST ===="

# Clonar el repositorio
echo "Clonando repositorio ${REPO_URL}..."
git clone "${REPO_URL}" "${REPO_DIR}"
if [ $? -ne 0 ]; then
    echo "Error: No se pudo clonar el repositorio."
    exit 1
fi

# Crear directorio para las imágenes
mkdir -p "${NUMBERS_DIR}"

# Extraer el dataset MNIST directamente en la carpeta numbers
echo "Extrayendo dataset MNIST en carpeta numbers..."
# Usar la opción -j para ignorar la estructura de directorios del ZIP
unzip -j -q "${REPO_DIR}/numbers.zip" -d "${NUMBERS_DIR}"
if [ $? -ne 0 ]; then
    echo "Error: No se pudo extraer el dataset MNIST."
    exit 1
fi

# Borrar el ZIP después de extraer
echo "Borrando archivo ZIP..."
rm "${REPO_DIR}/numbers.zip"

echo "Archivos preparados correctamente."
echo "Imagen de prueba en: ${REPO_DIR}/test_image"
echo "Dataset MNIST en: ${NUMBERS_DIR}"

# Ejecutar el test
echo "==== Ejecutando prueba de búsqueda en dataset MNIST ===="
cd "${SCRIPT_DIR}"
python "${SCRIPT_DIR}/multimedia/mnist_test.py"

echo "==== Proceso finalizado ====" 