# main.py
import streamlit as st
import pandas as pd
from datetime import datetime
from auth_handler import AuthHandler
from api_client import APIClient

# Configuración de la página
st.set_page_config(
    page_title="Miyazaki DB - Smart Stock",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado (mantén tus estilos existentes)
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
    .auth-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        border: 1px solid #dee2e6;
        border-radius: 10px;
        background-color: #f8f9fa;
    }
    /* ... resto de tus estilos ... */
</style>
""", unsafe_allow_html=True)


class MiyazakiDBApp:
    def __init__(self):
        # Inicializar handlers
        self.auth = AuthHandler()
        self.api = APIClient(auth_handler=self.auth)

        # Inicializar session state
        if 'query_history' not in st.session_state:
            st.session_state.query_history = []
        if 'current_tables' not in st.session_state:
            st.session_state.current_tables = []
        if 'last_uploaded_file_id' not in st.session_state:
            st.session_state.last_uploaded_file_id = None

    def render_auth_screen(self):
        """Pantalla de autenticación"""
        st.markdown("""
        <div class="main-header">
            <h1>🗄️ Miyazaki DB</h1>
            <p>Sistema Inteligente de Gestión de Stock</p>
        </div>
        """, unsafe_allow_html=True)

        # Tabs para Login y Registro
        tab1, tab2 = st.tabs(["🔑 Iniciar Sesión", "📝 Registrarse"])

        with tab1:
            st.markdown('<div class="auth-container">', unsafe_allow_html=True)
            st.subheader("Iniciar Sesión")

            with st.form("login_form"):
                email = st.text_input("Email", placeholder="tu@email.com")
                password = st.text_input("Contraseña", type="password")

                if st.form_submit_button("🔑 Ingresar", type="primary"):
                    if email and password:
                        if self.auth.login_user(email, password):
                            user_info = st.session_state.get('user_info', {})
                            st.success(f"¡Bienvenido {user_info.get('name', 'Usuario')}!")
                            st.rerun()
                        else:
                            st.error("Error al iniciar sesión")
                    else:
                        st.warning("Por favor completa todos los campos")

            st.markdown('</div>', unsafe_allow_html=True)

        with tab2:
            st.markdown('<div class="auth-container">', unsafe_allow_html=True)
            st.subheader("Crear Cuenta")

            with st.form("register_form"):
                name = st.text_input("Nombre completo")
                email = st.text_input("Email", placeholder="tu@email.com")
                password = st.text_input("Contraseña", type="password")
                confirm_password = st.text_input("Confirmar contraseña", type="password")

                if st.form_submit_button("📝 Registrarse", type="primary"):
                    if name and email and password and confirm_password:
                        if password == confirm_password:
                            if self.auth.register_user(name, email, password):
                                st.info("Ahora puedes iniciar sesión")
                        else:
                            st.error("Las contraseñas no coinciden")
                    else:
                        st.warning("Por favor completa todos los campos")

            st.markdown('</div>', unsafe_allow_html=True)

    def render_header(self):
        """Header para usuarios autenticados"""
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown("""
            <div class="main-header">
                <h1>🗄️ Miyazaki DB - Smart Stock</h1>
                <p>Consola avanzada para análisis de datos</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            user_name = st.session_state.get("user_info", {}).get("name", "Usuario")
            st.info(f"👤 {user_name}")

        with col3:
            if st.button("🚪 Cerrar Sesión"):
                self.auth.logout()

    def render_sidebar(self):
        """Sidebar mejorado para backend"""
        st.sidebar.header("📁 Gestión de Archivos")

        # Actualizar lista de tablas
        if st.sidebar.button("🔄 Actualizar Tablas"):
            tables_response = self.api.get_tables()
            tables = tables_response["tables"] if isinstance(tables_response, dict) else tables_response
            st.session_state.current_tables = tables

        # Subir nuevo archivo
        st.sidebar.subheader("📤 Subir Archivo")
        uploaded_file = st.sidebar.file_uploader(
            "Seleccionar archivo",
            type=['csv', 'txt'],
            help="Formatos soportados: CSV, TXT"
        )

        # Paso 1: Subir archivo y guardar file_id
        if uploaded_file and st.sidebar.button("Subir archivo"):
            file_id = self.api.upload_file(uploaded_file)
            if file_id:
                st.session_state.last_uploaded_file_id = file_id
                st.sidebar.success("Archivo subido. Ahora completa los datos para crear la tabla.")

        # Paso 2: Mostrar formulario para crear tabla si ya hay file_id
        if st.session_state.last_uploaded_file_id:
            st.sidebar.markdown("---")
            st.sidebar.subheader("➕ Crear Tabla desde Archivo Subido")
            with st.sidebar.form("create_table_form"):
                table_name = st.text_input("Nombre de tabla")
                index_type = st.selectbox("Tipo de índice", ["", "BTree", "Hash", "RTree"])
                index_column = st.text_input("Columna índice")
                encoding = st.text_input("Codificación", value="utf-8")
                if st.form_submit_button("Crear Tabla"):
                    success = self.api.create_table_from_file(
                        table_name,
                        st.session_state.last_uploaded_file_id,
                        index_type=index_type,
                        index_column=index_column,
                        encoding=encoding
                    )
                    if success:
                        tables_response = self.api.get_tables()
                        tables = tables_response["tables"] if isinstance(tables_response, dict) else tables_response
                        st.session_state.current_tables = tables
                        st.session_state.last_uploaded_file_id = None
                        st.rerun()

        # Lista de tablas
        st.sidebar.subheader("📋 Tablas Disponibles")

        if not hasattr(st.session_state, 'current_tables') or not st.session_state.current_tables:
            tables_response = self.api.get_tables()
            tables = tables_response["tables"] if isinstance(tables_response, dict) else tables_response
            st.session_state.current_tables = tables

        for table in st.session_state.current_tables:
            with st.sidebar.expander(f"📄 {table['name']}"):
                st.write(f"**Filas:** {table['row_count']:,}")
                st.write(f"**Columnas:** {table['columns']}")

                if st.button(f"👁️ Ver esquema", key=f"schema_{table['name']}"):
                    query = f"DESCRIBE {table['name']};"
                    result = self.api.execute_query(query)
                    if result is not None:
                        st.session_state.last_result = result

    def render_query_console(self):
        """Consola de queries conectada al backend"""
        st.header("💻 Consola de Queries")

        col1, col2 = st.columns([3, 1])

        with col1:
            query = st.text_area(
                "Escribir consulta SQL:",
                height=150,
                placeholder="SELECT * FROM tu_tabla WHERE columna = 'valor';",
                help="Escribe tu consulta SQL personalizada aquí"
            )

        with col2:
            st.subheader("🔧 Herramientas")

            # Formato de respuesta
            response_format = st.selectbox("Formato:", ["JSON", "CSV"])

            if st.button("▶️ Ejecutar Query", type="primary"):
                if query.strip():
                    with st.spinner("Ejecutando consulta..."):
                        format_type = "csv" if response_format == "CSV" else "json"
                        result = self.api.execute_query(query, format_type)
                        if result is not None:
                            st.session_state.last_result = result
                            # Agregar al historial
                            st.session_state.query_history.append({
                                'query': query,
                                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                'rows_returned': len(result)
                            })
                else:
                    st.warning("Ingresa una consulta SQL")

            if st.button("🔄 Limpiar Consola"):
                if 'last_result' in st.session_state:
                    del st.session_state.last_result
                st.rerun()

        # Mostrar resultado
        if 'last_result' in st.session_state and st.session_state.last_result is not None:
            st.subheader("📊 Resultado de la Consulta")

            result_df = st.session_state.last_result

            # Métricas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Filas retornadas", len(result_df))
            with col2:
                st.metric("Columnas", len(result_df.columns))
            with col3:
                if not result_df.empty:
                    st.metric("Memoria (KB)", f"{result_df.memory_usage(deep=True).sum() / 1024:.1f}")

            # Tabla de resultados
            st.dataframe(result_df, use_container_width=True, height=400)

            # Exportación
            if not result_df.empty:
                csv = result_df.to_csv(index=False)
                st.download_button(
                    label="📥 Descargar CSV",
                    data=csv,
                    file_name=f"resultado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

    def run(self):
        """Ejecutar aplicación principal"""
        # Verificar autenticación
        if not self.auth.is_authenticated():
            self.render_auth_screen()
            return

        # Aplicación principal para usuarios autenticados
        self.render_header()
        self.render_sidebar()

        # Tabs principales
        tab1, tab2, tab3 = st.tabs(["💻 Consola SQL", "📊 Tablas", "📝 Historial"])

        with tab1:
            self.render_query_console()

        with tab2:
            # Implementa visualizador de tablas usando API
            st.header("🗂️ Visualizador de Tablas")
            st.info("Implementar visualizador conectado al backend")

        with tab3:
            # Historial de queries
            if st.session_state.query_history:
                st.header("📝 Historial de Consultas")
                for i, query_info in enumerate(reversed(st.session_state.query_history[-10:])):
                    with st.expander(f"Query {len(st.session_state.query_history) - i} - {query_info['timestamp']}"):
                        st.code(query_info['query'], language='sql')
                        st.write(f"**Filas retornadas:** {query_info['rows_returned']}")


# Ejecutar aplicación
if __name__ == "__main__":
    app = MiyazakiDBApp()
    app.run()