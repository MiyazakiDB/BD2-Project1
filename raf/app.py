import os
import streamlit as st
import time
import requests
import pandas as pd

# Configuración
API_URL = "http://localhost:8000"

st.title("MiyazakiDB")
mode = st.sidebar.radio("Modo", ["SQL", "Multimedia", "Texto"])

# ===== MODO SQL =====
if mode == "SQL":
    st.header("Consulta SQL genérica")

    # Ejemplos rápidos
    st.subheader("Ejemplos Rápidos")
    ejemplos = [
        "SELECT * FROM Audio LIMIT 5;",
        "SELECT * FROM Images LIMIT 5;",
        "DELETE FROM Images WHERE file_path LIKE '%media_queries%';",
        "DELETE FROM Images WHERE file_path LIKE '%.wav' OR file_path LIKE '%.mp3';",
        "SELECT COUNT(*) FROM Images;",
        "CREATE TABLE Images (id INTEGER PRIMARY KEY, file_path IMAGE, title VARCHAR(255));",
        "CREATE TABLE test (id INT, name TEXT);",
        "INSERT INTO test VALUES (1, 'ejemplo');"
    ]
    query = "SELECT * FROM your_table LIMIT 10;"
    for ej in ejemplos:
        if st.button(ej, key=ej):
            query = ej

    query = st.text_area("Consulta SQL", value=query)
    offset = st.number_input("Offset", min_value=0, value=0)
    limit = st.number_input("Limit", min_value=1, value=10)
    if st.button("Ejecutar SQL"):
        t0 = time.time()
        r = requests.post(f"{API_URL}/sql/public", json={"query": query, "offset": offset, "limit": limit})
        dt = time.time() - t0
        if r.ok:
            data = r.json()
            df = pd.DataFrame(data.get("data", {}).get("records", []))
            if not df.empty:
                st.dataframe(df)
            st.write(f"Total: {data.get('total')} registros")
            st.write(f"Mensaje: {data.get('message')}")
            st.write(f"Tiempo: {dt:.3f} s")
        else:
            st.error(r.text)

# ===== MODO TEXTO =====
elif mode == "Texto":
    st.header("Búsqueda de Texto")
    
    # Subir texto
    st.subheader("Agregar Documentos")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Pegar Texto:**")
        text_input = st.text_area("Texto del documento", height=100)
        filename = st.text_input("Nombre del archivo", "documento.txt")
        if st.button("Agregar Texto"):
            if text_input:
                r = requests.post(f"{API_URL}/upload-text", json={
                    "text": text_input,
                    "filename": filename,
                    "metadata": {"source": "streamlit"}
                })
                if r.ok:
                    st.success(f"✅ Documento agregado: {r.json()['doc_id'][:8]}...")
                else:
                    st.error(r.text)
    
    with col2:
        st.write("**Subir Archivo:**")
        uploaded_file = st.file_uploader("Archivo de texto", type=["txt", "md"])
        if uploaded_file and st.button("Subir Archivo"):
            files = {"file": (uploaded_file.name, uploaded_file, "text/plain")}
            r = requests.post(f"{API_URL}/upload-file", files=files)
            if r.ok:
                st.success(f"✅ Archivo subido: {r.json()['doc_id'][:8]}...")
            else:
                st.error(r.text)
    
    # Finalizar índice
    if st.button("🔧 Finalizar Índice"):
        r = requests.post(f"{API_URL}/finalize-index")
        if r.ok:
            st.success(r.json()["message"])
        else:
            st.error(r.text)
    
    # Estadísticas
    try:
        r = requests.get(f"{API_URL}/index/stats")
        if r.ok:
            stats = r.json()
            col1, col2, col3 = st.columns(3)
            col1.metric("Documentos", stats["total_documents"])
            col2.metric("Términos", stats["total_terms"])
            col3.metric("Tamaño (MB)", f"{stats['index_size_mb']:.2f}")
    except:
        pass
    
    # Búsqueda
    st.subheader("Buscar Documentos")
    search_query = st.text_input("Consulta de búsqueda")
    k = st.number_input("Top-K resultados", min_value=1, max_value=20, value=5)
    
    if st.button("🔍 Buscar") and search_query:
        r = requests.post(f"{API_URL}/search", json={"query": search_query, "k": k})
        if r.ok:
            results = r.json()
            st.write(f"**Resultados para:** {results['query']}")
            st.write(f"**Tiempo:** {results['search_time_ms']:.1f} ms")
            
            for i, result in enumerate(results["results"], 1):
                with st.expander(f"{i}. {result['filename']} (Score: {result['similarity_score']:.4f})"):
                    st.write(result["text_preview"])
                    if result.get("metadata"):
                        st.json(result["metadata"])
        else:
            st.error(r.text)

# ===== MODO MULTIMEDIA =====
else:  # Multimedia
    st.header("Búsqueda Multimedia")

    # (Demo de archivos eliminado; usar subida propia en selección)

    # Carpetas locales separadas por tipo de multimedia
    LOCAL_MEDIA_DIR = os.path.abspath(os.path.join(os.getcwd(), "media_queries"))
    LOCAL_IMG_DIR = os.path.abspath(os.path.join(os.getcwd(), "img_queries"))
    
    # Definir variables principales fuera de los bloques condicionales
    tbl = st.text_input("Tabla multimedia", "Multimedia")
    col = st.text_input("Columna multimedia", "file_path")
    
    # Detectar qué tipo de archivo se busca basado en la tabla seleccionada
    is_image_table = tbl.lower() in ["images", "image"]
    
    # Seleccionar directorio y archivos apropiados según el tipo de tabla
    if is_image_table:
        query_dir = LOCAL_IMG_DIR
        dir_name = "img_queries"
        file_extensions = ("jpg", "png")
        st.info(f"📁 Modo imágenes: usando directorio `{dir_name}`")
    else:
        query_dir = LOCAL_MEDIA_DIR
        dir_name = "media_queries"
        file_extensions = ("wav", "mp3")
        st.info(f"📁 Modo multimedia: usando directorio `{dir_name}`")
    
    # Opciones de archivos disponibles según el tipo
    opciones = ["-- Subir archivo --"]
    if os.path.isdir(query_dir):
        opciones += [f for f in os.listdir(query_dir) if f.lower().endswith(file_extensions)]
    
    seleccionado = st.selectbox(f"Archivo consulta local ({dir_name})", opciones)

    upload = None
    if seleccionado == "-- Subir archivo --":
        upload = st.file_uploader("Subir archivo multimedia", type=["jpg","png","wav","mp3"])
        if upload:
            st.write("**Preview del archivo subido:**")
            if upload.name.lower().endswith(('jpg','png')):
                st.image(upload, width=200)
            else:
                st.audio(upload)
    else:
        # Usar directorio apropiado según el tipo de tabla
        path = os.path.join(query_dir, seleccionado)
        
        # Mostrar preview del archivo seleccionado
        st.write("**Preview del archivo seleccionado:**")
        if seleccionado.lower().endswith(('jpg','png')):
            if os.path.exists(path):
                st.image(path, width=200)
            else:
                st.error(f"❌ Archivo no encontrado: {path}")
        else:
            if os.path.exists(path):
                st.audio(path)
            else:
                st.error(f"❌ Archivo no encontrado: {path}")
    
    # Botones de población en columnas
    col1, col2 = st.columns(2)
    
    with col1:
        # Botón para poblar la tabla automáticamente con el directorio correcto
        if st.button("🗂️ Será Multimedia"):
            if is_image_table:
                st.info(f"Poblando tabla '{tbl}' con archivos de img_queries/...")
                source_dir = "img_queries"
            else:
                st.info(f"Poblando tabla '{tbl}' con archivos de media_queries/...")
                source_dir = "media_queries"
                
            resp = requests.post(
                f"{API_URL}/multimedia/populate",
                data={
                    "target_table": tbl, 
                    "path_column": col, 
                    "title_column": "title",
                    "source_directory": source_dir
                }
            )
            if resp.ok:
                result = resp.json()
                st.success(f"✅ Insertados: {result.get('inserted',0)} registros")
                st.info(f"📁 Origen: {source_dir}/ directory")
                errors = result.get('errors', [])
                if errors:
                    st.warning(f"⚠️ Errores: {errors}")
            else:
                st.error(f"❌ Error: {resp.text}")
    
    method = st.selectbox("Método", ["sequential", "inverted"])
    topk = st.number_input("Top-K", min_value=1, value=5)

    # Botón para construir el índice multimedia (codebook)
    if st.button("🔧 Finalizar Índice Multimedia"):
        st.info(f"Construyendo índice {method} para tabla '{tbl}', columna '{col}'...")
        # Determinar directorio fuente para el índice
        source_dir = "img_queries" if is_image_table else "media_queries"
        
        # Debug: mostrar datos que se envían
        request_data = {
            "target_table": tbl,
            "column_name": col,
            "method": method,
            "source_directory": source_dir
        }
        st.write(f"**Debug - Datos enviados al backend:**")
        st.json(request_data)
        
        r = requests.post(
            f"{API_URL}/multimedia/index",
            data=request_data
        )
        if r.ok:
            st.success(r.json().get("message", "Índice multimedia construido"))
        else:
            st.error(f"Error: {r.text}")
            st.error(f"Status: {r.status_code}")

    # ===== Botón de búsqueda multimedia =====
    if st.button("🔍 Buscar Multimedia"):
        file_to_send = None
        filename = ""
        
        if seleccionado != "-- Subir archivo --":
            # Usar directorio correcto basado en la tabla
            path = os.path.join(query_dir, seleccionado)
                
            with open(path, "rb") as f:
                file_content = f.read()
            file_to_send = ("file", (seleccionado, file_content))
            filename = seleccionado
        elif upload:
            file_to_send = ("file", (upload.name, upload.getvalue()))
            filename = upload.name
        else:
            st.warning("Selecciona o sube un archivo primero")
            st.stop()

        # Enviar búsqueda
        data = {"target_table": tbl, "column_name": col, "limit": topk, "method": method}
        files = {file_to_send[0]: file_to_send[1]}
        
        t0 = time.time()
        r = requests.post(f"{API_URL}/sql/multimedia", files=files, data=data)
        dt = time.time() - t0
        
        if r.ok:
            res = r.json()
            st.write(f"**Archivo consulta:** {filename}")
            st.write(f"**Método usado:** {method}")
            
            results = res.get("data", [])
            if results:
                df = pd.DataFrame(results)
                st.dataframe(df)
                
                st.subheader("🎵 Reproducir Resultados")
                
                # Mostrar previews si están disponibles
                for i, (_, row_data) in enumerate(df.iterrows(), 1):
                    # Acceder correctamente a los datos de la fila
                    media_path = (row_data.get(col) or 
                                row_data.get('file_path') or 
                                row_data.get('path'))
                    
                    title = row_data.get('title', f'Resultado {i}')
                    
                    st.write(f"**{i}. {title}**")
                    
                    # Determinar el directorio base según el tipo de tabla
                    is_image_table = tbl.lower() in ["images", "image"]
                    base_dir = LOCAL_IMG_DIR if is_image_table else LOCAL_MEDIA_DIR
                    dir_prefix = "img_queries/" if is_image_table else "media_queries/"
                    
                    # Si la ruta es relativa y contiene el prefijo, eliminarlo
                    if media_path.startswith(dir_prefix):
                        media_path = media_path[len(dir_prefix):]
                    
                    # Si file_path está vacío o es relativo, construir la ruta completa
                    if not media_path or media_path == "" or not os.path.isabs(media_path):
                        # Para Images, usar img_queries; para otros, media_queries
                        if media_path and not os.path.isabs(media_path):
                            # Si es una ruta relativa, construir la ruta completa
                            media_path = os.path.join(base_dir, media_path)
                        elif title and title != f'Resultado {i}':
                            # Intentar reconstruir la ruta basada en el título
                            if is_image_table:
                                # Para imágenes, usar formato img_X.jpg
                                if title.startswith("img_") and title.endswith(".jpg"):
                                    media_path = os.path.join(base_dir, title)
                                else:
                                    # Intentar extraer número del título
                                    import re
                                    match = re.search(r'img_(\d+)', title)
                                    if match:
                                        img_num = match.group(1)
                                        media_path = os.path.join(base_dir, f"img_{img_num}.jpg")
                            else:
                                # Mapeo de títulos a archivos conocidos para audio
                                title_to_file = {
                                    "Bad Bunny – BAILE INOlVIDABLE": "Bad_Bunny_-_BAILE_INoLVIDABLE_preview.wav",
                                    "Geto Boys – Bring It On": "Geto_Boys_-_Bring_It_On_preview.wav", 
                                    "Halestorm – Freak Like Me": "Halestorm_-_Freak_Like_Me_preview.wav"
                                }
                                
                                if title in title_to_file:
                                    filename_local = title_to_file[title]
                                    media_path = os.path.join(base_dir, filename_local)
                                    st.info(f"🔧 Reconstruyendo ruta: {filename_local}")
                    
                    if media_path and isinstance(media_path, str) and media_path.strip():
                        try:
                            # Para archivos de audio
                            if filename.lower().endswith(('wav','mp3')):
                                if os.path.exists(media_path):
                                    st.audio(media_path)
                                    st.success(f"✅ Reproduciendo: {os.path.basename(media_path)}")
                                else:
                                    st.error(f"❌ No se encontró el archivo: {media_path}")
                            # Para imágenes  
                            elif filename.lower().endswith(('jpg','png')) or is_image_table:
                                if os.path.exists(media_path):
                                    st.image(media_path, width=200)
                                    st.success(f"✅ Mostrando: {os.path.basename(media_path)}")
                                else:
                                    st.error(f"❌ No se encontró la imagen: {media_path}")
                            else:
                                st.write(f"📁 Archivo: `{media_path}`")
                        except Exception as e:
                            st.error(f"❌ Error al mostrar: {str(e)}")
                    else:
                        st.warning(f"⚠️ No se pudo determinar la ruta del archivo para '{title}'")
                        
                    st.divider()
            else:
                st.info("No se encontraron resultados similares")
        else:
            st.error(f"Error: {r.text}")

# Footer
st.sidebar.markdown("---")
st.sidebar.info("🚀 Backend unificado en puerto 8000")

