import sys
import os
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Any

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

@app.get("/", summary="Endpoint para uptime")
async def read_root():
    return {"message": "MiyazakiDB API is up!"}
