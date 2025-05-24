import streamlit as st
import pandas as pd
import sqlite3
import io
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import tempfile

# Configuración de la página
st.set_page_config(
    page_title="SQL Parser Console",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .query-console {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .file-info {
        background-color: #e7f3ff;
        border-left: 4px solid #007bff;
        padding: 10px;
        margin: 10px 0;
        border-radius: 4px;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 10px;
        border-radius: 4px;
        margin: 10px 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 10px;
        border-radius: 4px;
        margin: 10px 0;
    }
    .stDataFrame {
        border: 1px solid #dee2e6;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


class SQLParserFrontend:
    def __init__(self):
        # Inicializar estado de la sesión
        if 'uploaded_files' not in st.session_state:
            st.session_state.uploaded_files = {}
        if 'query_history' not in st.session_state:
            st.session_state.query_history = []
        if 'current_table' not in st.session_state:
            st.session_state.current_table = None
        if 'db_connection' not in st.session_state:
            st.session_state.db_connection = None

    def setup_database(self):
        """Configurar base de datos en memoria"""
        if st.session_state.db_connection is None:
            st.session_state.db_connection = sqlite3.connect(':memory:', check_same_thread=False)

    def load_file_to_db(self, file, file_name: str, data_type: str):
        """Cargar archivo a la base de datos"""
        try:
            # Determinar el tipo de archivo y leer datos
            if file_name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file_name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
            elif file_name.endswith('.json'):
                df = pd.read_json(file)
            else:
                st.error(f"Formato de archivo no soportado: {file_name}")
                return False

            # Crear nombre de tabla basado en el nombre del archivo
            table_name = os.path.splitext(file_name)[0].replace(' ', '_').replace('-', '_')

            # Cargar datos a SQLite
            df.to_sql(table_name, st.session_state.db_connection, if_exists='replace', index=False)

            # Guardar información del archivo
            st.session_state.uploaded_files[file_name] = {
                'table_name': table_name,
                'data_type': data_type,
                'rows': len(df),
                'columns': list(df.columns),
                'upload_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'dataframe': df
            }

            return True

        except Exception as e:
            st.error(f"Error al cargar archivo {file_name}: {str(e)}")
            return False

    def execute_query(self, query: str):
        """Ejecutar query SQL"""
        try:
            if st.session_state.db_connection is None:
                st.error("No hay conexión a la base de datos")
                return None

            # Ejecutar query
            result = pd.read_sql_query(query, st.session_state.db_connection)

            # Agregar a historial
            st.session_state.query_history.append({
                'query': query,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'rows_returned': len(result)
            })

            return result

        except Exception as e:
            st.error(f"Error ejecutando query: {str(e)}")
            return None

    def export_data(self, data: pd.DataFrame, format_type: str, filename: str):
        """Exportar datos en formato especificado"""
        try:
            if format_type == 'CSV':
                csv_buffer = io.StringIO()
                data.to_csv(csv_buffer, index=False)
                return csv_buffer.getvalue(), 'text/csv'

            elif format_type == 'TXT':
                txt_buffer = io.StringIO()
                data.to_string(txt_buffer, index=False)
                return txt_buffer.getvalue(), 'text/plain'

            else:
                st.error("Formato de exportación no soportado")
                return None, None

        except Exception as e:
            st.error(f"Error al exportar: {str(e)}")
            return None, None

    def render_header(self):
        """Renderizar encabezado principal"""
        st.markdown("""
        <div class="main-header">
            <h1>🗄️ SQL Parser Console</h1>
            <p>Consola avanzada para análisis de datos con SQL personalizado</p>
        </div>
        """, unsafe_allow_html=True)

    def render_sidebar(self):
        """Renderizar barra lateral con gestión de archivos"""
        st.sidebar.header("📁 Gestión de Archivos")

        # Sección de subida de archivos
        st.sidebar.subheader("Subir Nuevos Archivos")

        uploaded_files = st.sidebar.file_uploader(
            "Seleccionar archivos",
            type=['csv', 'xlsx', 'xls', 'json'],
            accept_multiple_files=True,
            help="Formatos soportados: CSV, Excel, JSON"
        )

        # Tipo de datos
        data_type = st.sidebar.selectbox(
            "Tipo de datos:",
            ["Estándar", "Espacial", "Temporal", "Geográfico"],
            help="Especifica el tipo de datos para optimizar el procesamiento"
        )

        # Procesar archivos subidos
        if uploaded_files:
            if st.sidebar.button("🔄 Cargar Archivos"):
                success_count = 0
                for uploaded_file in uploaded_files:
                    if self.load_file_to_db(uploaded_file, uploaded_file.name, data_type):
                        success_count += 1

                if success_count > 0:
                    st.sidebar.success(f"✅ {success_count} archivo(s) cargado(s) exitosamente")
                    st.rerun()

        # Lista de archivos cargados
        st.sidebar.subheader("📋 Archivos Cargados")

        if st.session_state.uploaded_files:
            for filename, info in st.session_state.uploaded_files.items():
                with st.sidebar.expander(f"📄 {filename}"):
                    st.write(f"**Tabla:** {info['table_name']}")
                    st.write(f"**Tipo:** {info['data_type']}")
                    st.write(f"**Filas:** {info['rows']:,}")
                    st.write(f"**Columnas:** {len(info['columns'])}")
                    st.write(f"**Subido:** {info['upload_time']}")

                    if st.button(f"👁️ Ver {filename}", key=f"view_{filename}"):
                        st.session_state.current_table = info['table_name']

                    if st.button(f"🗑️ Eliminar {filename}", key=f"delete_{filename}"):
                        del st.session_state.uploaded_files[filename]
                        st.rerun()
        else:
            st.sidebar.info("No hay archivos cargados")

        # Información de la base de datos
        st.sidebar.subheader("🔗 Estado de la Base de Datos")
        if st.session_state.uploaded_files:
            total_tables = len(st.session_state.uploaded_files)
            total_rows = sum(info['rows'] for info in st.session_state.uploaded_files.values())
            st.sidebar.metric("Tablas cargadas", total_tables)
            st.sidebar.metric("Total de filas", f"{total_rows:,}")

    def render_query_console(self):
        """Renderizar consola de queries"""
        st.header("💻 Consola de Queries")

        # Área de query
        col1, col2 = st.columns([3, 1])

        with col1:
            query = st.text_area(
                "Escribir consulta SQL:",
                height=150,
                placeholder="SELECT * FROM tabla_ejemplo WHERE columna = 'valor';",
                help="Escribe tu consulta SQL personalizada aquí"
            )

        with col2:
            st.subheader("🔧 Herramientas")

            # Botones de acción
            if st.button("▶️ Ejecutar Query", type="primary"):
                if query.strip():
                    with st.spinner("Ejecutando consulta..."):
                        result = self.execute_query(query)
                        if result is not None:
                            st.session_state.last_result = result
                else:
                    st.warning("Ingresa una consulta SQL")

            # Queries de ejemplo
            if st.button("📝 Query de Ejemplo"):
                if st.session_state.uploaded_files:
                    first_table = list(st.session_state.uploaded_files.values())[0]['table_name']
                    example_query = f"SELECT * FROM {first_table} LIMIT 10;"
                    st.text_area("Query de ejemplo:", value=example_query, key="example_query")
                else:
                    st.info("Carga archivos primero")

            if st.button("🔄 Limpiar Consola"):
                st.rerun()

        # Mostrar resultado de la última query
        if 'last_result' in st.session_state and st.session_state.last_result is not None:
            st.subheader("📊 Resultado de la Consulta")

            result_df = st.session_state.last_result

            # Información del resultado
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Filas retornadas", len(result_df))
            with col2:
                st.metric("Columnas", len(result_df.columns))
            with col3:
                if not result_df.empty:
                    st.metric("Memoria (KB)", f"{result_df.memory_usage(deep=True).sum() / 1024:.1f}")

            # Mostrar tabla
            st.dataframe(result_df, use_container_width=True, height=400)

            # Opciones de exportación
            st.subheader("📤 Exportar Resultado")
            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                export_format = st.selectbox("Formato:", ["CSV", "TXT"])

            with col2:
                export_filename = st.text_input("Nombre del archivo:", "resultado_query")

            with col3:
                if st.button("💾 Exportar"):
                    if export_filename:
                        data, mime_type = self.export_data(result_df, export_format, export_filename)
                        if data:
                            file_extension = 'csv' if export_format == 'CSV' else 'txt'
                            st.download_button(
                                label=f"⬇️ Descargar {export_format}",
                                data=data,
                                file_name=f"{export_filename}.{file_extension}",
                                mime=mime_type
                            )
                    else:
                        st.warning("Ingresa un nombre para el archivo")

    def render_table_viewer(self):
        """Renderizar visualizador de tablas"""
        st.header("🗂️ Visualizador de Tablas")

        if not st.session_state.uploaded_files:
            st.info("🔍 No hay tablas disponibles. Sube archivos para comenzar.")
            return

        # Selector de tabla
        table_options = {info['table_name']: filename
                         for filename, info in st.session_state.uploaded_files.items()}

        selected_table = st.selectbox(
            "Seleccionar tabla:",
            options=list(table_options.keys()),
            format_func=lambda x: f"{table_options[x]} ({x})"
        )

        if selected_table:
            # Obtener información de la tabla
            table_info = None
            for filename, info in st.session_state.uploaded_files.items():
                if info['table_name'] == selected_table:
                    table_info = info
                    break

            if table_info:
                # Información de la tabla
                st.markdown(f"""
                <div class="file-info">
                    <h4>📊 {table_options[selected_table]}</h4>
                    <p><strong>Tabla:</strong> {selected_table} | 
                       <strong>Tipo:</strong> {table_info['data_type']} | 
                       <strong>Filas:</strong> {table_info['rows']:,} | 
                       <strong>Columnas:</strong> {len(table_info['columns'])}</p>
                </div>
                """, unsafe_allow_html=True)

                # Pestañas para diferentes vistas
                tab1, tab2, tab3, tab4 = st.tabs(["📋 Datos", "📈 Estadísticas", "🔍 Esquema", "🔧 Acciones"])

                with tab1:
                    # Vista de datos con paginación
                    df = table_info['dataframe']

                    col1, col2, col3 = st.columns([1, 1, 2])
                    with col1:
                        rows_per_page = st.selectbox("Filas por página:", [10, 25, 50, 100], index=1)
                    with col2:
                        total_pages = max(1, (len(df) - 1) // rows_per_page + 1)
                        page = st.number_input("Página:", min_value=1, max_value=total_pages, value=1)
                    with col3:
                        st.write(f"Mostrando página {page} de {total_pages}")

                    # Mostrar datos paginados
                    start_idx = (page - 1) * rows_per_page
                    end_idx = start_idx + rows_per_page
                    st.dataframe(df.iloc[start_idx:end_idx], use_container_width=True)

                with tab2:
                    # Estadísticas descriptivas
                    st.subheader("📊 Estadísticas Descriptivas")

                    # Solo para columnas numéricas
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    if len(numeric_cols) > 0:
                        st.dataframe(df[numeric_cols].describe(), use_container_width=True)
                    else:
                        st.info("No hay columnas numéricas para mostrar estadísticas")

                    # Información general
                    st.subheader("ℹ️ Información General")
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write("**Tipos de datos:**")
                        dtype_counts = df.dtypes.value_counts()
                        for dtype, count in dtype_counts.items():
                            st.write(f"- {dtype}: {count} columnas")

                    with col2:
                        st.write("**Valores nulos:**")
                        null_counts = df.isnull().sum()
                        null_cols = null_counts[null_counts > 0]
                        if len(null_cols) > 0:
                            for col, count in null_cols.items():
                                st.write(f"- {col}: {count} nulos")
                        else:
                            st.write("No hay valores nulos")

                with tab3:
                    # Esquema de la tabla
                    st.subheader("🗂️ Esquema de la Tabla")

                    schema_data = []
                    for col in df.columns:
                        schema_data.append({
                            'Columna': col,
                            'Tipo': str(df[col].dtype),
                            'Nulos': df[col].isnull().sum(),
                            'Únicos': df[col].nunique(),
                            'Ejemplo': str(df[col].iloc[0]) if len(df) > 0 else 'N/A'
                        })

                    schema_df = pd.DataFrame(schema_data)
                    st.dataframe(schema_df, use_container_width=True)

                with tab4:
                    # Acciones disponibles
                    st.subheader("🔧 Acciones Disponibles")

                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button(f"📤 Exportar {selected_table}"):
                            export_format = st.selectbox("Formato de exportación:", ["CSV", "TXT"],
                                                         key="export_format_table")
                            data, mime_type = self.export_data(df, export_format, selected_table)
                            if data:
                                file_extension = 'csv' if export_format == 'CSV' else 'txt'
                                st.download_button(
                                    label=f"⬇️ Descargar {export_format}",
                                    data=data,
                                    file_name=f"{selected_table}.{file_extension}",
                                    mime=mime_type,
                                    key="download_table"
                                )

                    with col2:
                        if st.button(f"🔍 Query Automática"):
                            auto_query = f"SELECT * FROM {selected_table} LIMIT 100;"
                            st.code(auto_query, language='sql')

                            if st.button("▶️ Ejecutar Query Automática"):
                                result = self.execute_query(auto_query)
                                if result is not None:
                                    st.session_state.last_result = result
                                    st.success("Query ejecutada. Ve a la consola para ver resultados.")

    def render_query_history(self):
        """Renderizar historial de queries"""
        if st.session_state.query_history:
            st.header("📝 Historial de Consultas")

            for i, query_info in enumerate(reversed(st.session_state.query_history[-10:])):  # Últimas 10
                with st.expander(f"Query {len(st.session_state.query_history) - i} - {query_info['timestamp']}"):
                    st.code(query_info['query'], language='sql')
                    st.write(f"**Filas retornadas:** {query_info['rows_returned']}")

                    if st.button(f"🔄 Re-ejecutar", key=f"rerun_{i}"):
                        result = self.execute_query(query_info['query'])
                        if result is not None:
                            st.session_state.last_result = result

    def run(self):
        """Ejecutar la aplicación principal"""
        self.setup_database()
        self.render_header()
        self.render_sidebar()

        # Pestañas principales
        tab1, tab2, tab3 = st.tabs(["💻 Consola SQL", "🗂️ Tablas", "📝 Historial"])

        with tab1:
            self.render_query_console()

        with tab2:
            self.render_table_viewer()

        with tab3:
            self.render_query_history()

        # Footer
        st.markdown("---")
        st.markdown(
            "<div style='text-align: center; color: gray;'>"
            "🗄️ SQL Parser Console - Desarrollado con Streamlit"
            "</div>",
            unsafe_allow_html=True
        )


# Ejecutar la aplicación
if __name__ == "__main__":
    app = SQLParserFrontend()
    app.run()