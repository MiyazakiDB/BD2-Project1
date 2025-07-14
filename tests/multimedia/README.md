# Tests de Funcionalidad Multimedia

Este directorio contiene pruebas y demostraciones para la funcionalidad de búsqueda multimedia implementada en el sistema.

## Estructura de archivos

- `test_multimedia.py`: Pruebas unitarias para los componentes multimedia
- `demo_multimedia.py`: Script de demostración para búsqueda de imágenes similares
- `api_test.py`: Script para probar la API de multimedia

## Requisitos

Asegúrate de tener instaladas todas las dependencias:

```bash
pip install -r ../../requirements.txt
```

## Ejecutar pruebas unitarias

Para ejecutar las pruebas unitarias:

```bash
python -m unittest tests/multimedia/test_multimedia.py
```

## Demostración de búsqueda multimedia

El script `demo_multimedia.py` permite crear imágenes de prueba y realizar búsquedas de similitud:

### Crear imágenes de prueba:

```bash
python tests/multimedia/demo_multimedia.py --create
```

### Realizar búsqueda secuencial:

```bash
python tests/multimedia/demo_multimedia.py --method sequential
```

### Realizar búsqueda con índice invertido:

```bash
python tests/multimedia/demo_multimedia.py --method inverted
```

### Opciones adicionales:

- `--dir`: Directorio para imágenes de prueba (predeterminado: "./multimedia/test_images")
- `--query`: Índice de la imagen a usar como consulta (predeterminado: 0)
- `--k`: Número de resultados a mostrar (predeterminado: 3)

## Pruebas de la API

El script `api_test.py` permite probar la API de multimedia:

### Crear una tabla multimedia:

```bash
python tests/multimedia/api_test.py --username usuario --password contraseña --action create --table imagenes --column imagen
```

### Insertar un archivo multimedia:

```bash
python tests/multimedia/api_test.py --username usuario --password contraseña --action insert --table imagenes --column imagen --file ruta/a/imagen.jpg --description "Descripción de la imagen"
```

### Realizar búsqueda por similitud:

```bash
python tests/multimedia/api_test.py --username usuario --password contraseña --action search --table imagenes --column imagen --query-id 1 --method sequential
```

### Opciones adicionales:

- `--url`: URL base de la API (predeterminado: "http://localhost:8000")
- `--method`: Método de búsqueda ("sequential" o "inverted")

## Flujo de trabajo completo

1. Inicia el servidor backend:

```bash
cd backend
python main.py
```

2. Crea una tabla multimedia:

```bash
python tests/multimedia/api_test.py --username usuario --password contraseña --action create
```

3. Crea algunas imágenes de prueba:

```bash
python tests/multimedia/demo_multimedia.py --create
```

4. Inserta las imágenes en la base de datos:

```bash
python tests/multimedia/api_test.py --username usuario --password contraseña --action insert --file multimedia/test_images/test_image_0.jpg
```

5. Realiza una búsqueda por similitud:

```bash
python tests/multimedia/api_test.py --username usuario --password contraseña --action search --query-id 1
```

## Ejemplos de consultas SQL

También puedes usar el operador de similitud `<->` directamente en consultas SQL:

```sql
SELECT * FROM imagenes WHERE imagen <-> 'ruta/a/imagen_consulta.jpg' LIMIT 5;
```

Esta consulta devolverá los 5 registros más similares a la imagen de consulta. 