import sys
import os
import csv
from fastapi import FastAPI, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Any, Optional
import chardet

sys.path.append(os.path.join(os.path.dirname(__file__), '../parser/'))
try:
    from parser import DatabaseManager
except ImportError:
    print("Error: no se encontro el parser")
    sys.exit(1)

class SQLQueryRequest(BaseModel):
    query: str = Field(..., example="SELECT * FROM images WHERE score > 8.0;")

app = FastAPI(
    title="Miyazaki API",
    description="API para interactuar con el sistema de datos multimodal.",
    version="0.1.0"
)

DB_DIRECTORY = "db_data_api"
if not os.path.exists(DB_DIRECTORY):
    os.makedirs(DB_DIRECTORY)
    print(f"directorio para los datos de la API creado en: {DB_DIRECTORY}")

UPLOAD_DIRECTORY = "uploaded_files"
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)
    print(f"directorio para los archivos subidos en: {UPLOAD_DIRECTORY}")

db_manager = DatabaseManager(db_directory=DB_DIRECTORY)

@app.post("/query",
          summary="Ejecutar una query al ParserSQL",
          response_description="El resultado de la query")
async def execute_sql_query(request_body: SQLQueryRequest) -> Any:
    query_string = request_body.query
    if not query_string or not query_string.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query vacia")

    try:
        print(f"query recibida por la API: {query_string}")
        result = db_manager.execute_query(query_string)
        print(f"resultado de la API: {result}")

        if isinstance(result, str) and result.lower().startswith("error:"):
            if "no existe" in result.lower() or "not found" in result.lower() or "no encontrada" in result.lower():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result)
            elif "malformada" in result.lower() or "sintaxis" in result.lower() or "incompleta" in result.lower() or "discrepancia" in result.lower() or "parametro" in result.lower() or "valor/tipo" in result.lower():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result)
            else:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result)

        return {"status": "success", "result": result}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error inesperado en la API para la query '{query_string}': {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Un error inesperado ocurrio: {str(e)}")





# uvicorn python-multipart chardet
ALLOWED_DELIMITERS = [",", ";", "\t", "|", ":"]
@app.post("/upload", summary="Subir un archivo CSV o TXT")
async def upload_file(
    file: UploadFile = File(...),
    delimiter: Optional[str] = Form(","),
    has_header: Optional[bool] = Form(True),
    encoding: Optional[str] = Form(None),
    max_file_size: int = 10 * 1024 * 1024  # Límite de 10MB
):
    if file.content_type not in ["text/csv", "text/plain"]:
        raise HTTPException(status_code=400, detail="Solo se permiten archivos CSV o TXT.")

    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > max_file_size:
        raise HTTPException(status_code=400, detail=f"El archivo excede el tamaño máximo ({max_file_size / 1024 / 1024}MB).")

    filename = os.path.basename(file.filename)
    file_path = os.path.join(UPLOAD_DIRECTORY, filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    try:
        if encoding is None:
            with open(file_path, "rb") as f:
                raw_data = f.read(10000)
                detected = chardet.detect(raw_data)
                encoding = detected["encoding"] or "utf-8"

        if delimiter not in ALLOWED_DELIMITERS:
            raise HTTPException(status_code=400, detail=f"Delimitador no permitido. Use: {ALLOWED_DELIMITERS}")

        with open(file_path, "r", encoding=encoding) as f:
            # Intentar auto-detectar delimitador si el proporcionado falla
            sample = f.read(1024)
            f.seek(0)
            sniffer = csv.Sniffer()
            try:
                dialect = sniffer.sniff(sample)
                if delimiter != dialect.delimiter:
                    print(f"Advertencia: Delimitador detectado es '{dialect.delimiter}', pero se usará '{delimiter}'")
            except csv.Error:
                pass
            reader = csv.reader(f, delimiter=delimiter)
            rows = list(reader)
            header = rows.pop(0) if has_header and rows else None

    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail=f"Error de encoding. Intente con: {encoding}.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar el archivo: {str(e)}")

    return {
        "message": "Archivo subido y procesado exitosamente",
        "filename": filename,
        "encoding": encoding,
        "delimiter": delimiter,
        "header": header,
        "rows_count": len(rows)
    }


@app.get("/", summary="Endpoint para uptime")
async def read_root():
    return {"message": "MiyazakiDB API is up!"}
