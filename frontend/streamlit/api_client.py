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

    def upload_file_and_create_table(self, file, table_name: str, **kwargs) -> bool:
        """Subir archivo y crear tabla en el backend"""
        try:
            # Preparar archivos para upload
            files = {"file": (file.name, file, file.type)}

            # Preparar datos del formulario
            form_data = {
                "table_name": table_name,
                "delimiter": kwargs.get("delimiter", ","),
                "encoding": kwargs.get("encoding", "latin-1"),  # Changed default from utf-8 to latin-1
                "index_type": kwargs.get("index_type", ""),
                "index_column": kwargs.get("index_column", ""),
                "has_header": kwargs.get("has_header", True)
            }

            response = requests.post(
                f"{self.base_url}/inventory/create-table-from-file",
                files=files,
                data=form_data,
                headers=self.auth.get_headers()
            )

            if response.status_code == 200:
                st.success(f"✅ Tabla '{table_name}' creada exitosamente")
                return True
            else:
                st.error(f"❌ Error: {response.json().get('detail', 'Error desconocido')}")
                return False

        except Exception as e:
            st.error(f"❌ Error al subir archivo: {str(e)}")
            return False

    def execute_query(self, query: str, format: str = "json") -> Optional[pd.DataFrame]:
        """Ejecutar consulta SQL"""
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
                    # Respuesta CSV
                    csv_data = response.text
                    df = pd.read_csv(io.StringIO(csv_data))
                else:
                    # Respuesta JSON
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