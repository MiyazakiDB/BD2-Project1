# api_client.py
import streamlit as st
import requests
import pandas as pd
from typing import Dict, List, Optional
import io


class APIClient:
    def __init__(self, base_url: str = "http://localhost:8000", auth_handler=None):
        self.base_url = base_url
        self.auth = auth_handler

    def upload_file(self, file) -> Optional[str]:
        """Sube un archivo y retorna el file_id"""
        try:
            files = {"file": (file.name, file, file.type)}
            response = requests.post(
                f"{self.base_url}/files/",
                files=files,
                headers=self.auth.get_headers()
            )
            if response.status_code == 200:
                data = response.json()
                # Ajusta esto según la respuesta real de tu backend
                file_id = data.get("file_id") or data.get("id")
                if file_id:
                    st.success("Archivo subido correctamente.")
                    return file_id
                else:
                    st.error("No se recibió file_id del backend.")
                    return None
            else:
                st.error(f"❌ Error al subir archivo: {response.text}")
                return None
        except Exception as e:
            st.error(f"❌ Error al subir archivo: {str(e)}")
            return None

    def create_table_from_file(self, table_name: str, file_id: str, index_type: str = "", index_column: str = "", encoding: str = "utf-8") -> bool:
        """Crea una tabla a partir de un archivo subido"""
        try:
            payload = {
                "table_name": table_name,
                "file_id": file_id,
                "index_type": index_type,
                "index_column": index_column,
                "encoding": encoding
            }
            response = requests.post(
                f"{self.base_url}/inventory/create-table-from-file",
                json=payload,
                headers=self.auth.get_headers()
            )
            if response.status_code == 200:
                st.success(f"✅ Tabla '{table_name}' creada exitosamente")
                return True
            else:
                st.error(f"❌ Error: {response.json().get('detail', 'Error desconocido')}")
                return False
        except Exception as e:
            st.error(f"❌ Error al crear tabla: {str(e)}")
            return False

    def execute_query(self, query: str, format: str = "json") -> Optional[pd.DataFrame]:
        """Ejecutar consulta SQL"""
        if not query or not isinstance(query, str) or not query.strip():
            st.error("Debes ingresar una consulta SQL.")
            return None
        try:
            headers = self.auth.get_headers()
            if format == "csv":
                headers["Accept"] = "text/csv"

            response = requests.post(
                f"{self.base_url}/inventory/",
                data={"query": query},
                headers=headers
            )

            if response.status_code == 200:
                if format == "csv":
                    csv_data = response.text
                    df = pd.read_csv(io.StringIO(csv_data))
                else:
                    data = response.json()
                    if "result" in data and data["result"]:
                        df = pd.DataFrame(data["result"])
                    else:
                        df = pd.DataFrame()
                return df
            else:
                st.error(f"❌ Error en query: {response.json().get('detail', 'Error desconocido')}")
                return None

        except Exception as e:
            st.error(f"❌ Error ejecutando query: {str(e)}")
            return None

    def get_tables(self) -> List[Dict]:
        """Obtener lista de tablas del usuario"""
        try:
            response = requests.get(
                f"{self.base_url}/inventory/tables",
                headers=self.auth.get_headers()
            )
            if response.status_code == 200:
                return response.json()
            else:
                st.error("❌ Error obteniendo tablas")
                return []
        except Exception as e:
            st.error(f"❌ Error de conexión: {str(e)}")
            return []