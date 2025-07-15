import requests
import json
import os
import matplotlib.pyplot as plt

def compare_vectors(query_vec, other_vec, query_label="Query", other_label="Vecino"):
    plt.figure(figsize=(12, 4))
    plt.bar(range(len(query_vec)), query_vec, alpha=0.6, label=query_label)
    plt.bar(range(len(other_vec)), other_vec, alpha=0.6, label=other_label)
    plt.title("Comparación de vectores (histograma o TF-IDF)")
    plt.legend()
    plt.show()

# === CONFIGURACIÓN ===
API_BASE_URL = "http://localhost:8000"

def test_api():
    """Prueba básica de la API"""
    
    # 1. Verificar salud del sistema
    print("1. Verificando estado del sistema...")
    response = requests.get(f"{API_BASE_URL}/health")
    print(f"Estado: {response.json()}")
    
    # 2. Buscar por archivo local
    print("\n2. Buscando por archivo local...")
    audio_path = os.path.join(os.path.dirname(__file__), "audio_to_see", "The_Strokes_-_Reptilia.wav")
    
    params = {
        "audio_path": audio_path,
        "top_k": 5
    }
    
    response = requests.get(f"{API_BASE_URL}/search/file", params=params)
    
    if response.status_code == 200:
        results = response.json()
        print(f"Archivo consulta: {results['query_filename']}")
        print(f"Tiempo procesamiento: {results['processing_time_seconds']}s")
        print("Resultados:")
        for audio in results['results']:
            print(f"  {audio['rank']}. {audio['filename']} - Similitud: {audio['similarity_score']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return  # Salir si hay error en la búsqueda principal

    # Opcional: visualizar vectores (solo si la API tiene el endpoint /vector)
    try:
        print("\n4. Intentando comparar vectores...")
        
        # Verificar si el endpoint /vector existe
        vector_q_response = requests.get(f"{API_BASE_URL}/vector", params={"audio_path": audio_path, "tfidf": True})
        
        if vector_q_response.status_code == 200 and 'vector' in vector_q_response.json():
            vector_q = vector_q_response.json()["vector"]
            
            # Construir ruta al archivo similar encontrado
            similar_file_path = os.path.join(os.path.dirname(__file__), "previews", results['results'][0]['filename'])
            
            vector_r_response = requests.get(f"{API_BASE_URL}/vector", 
                                        params={"audio_path": similar_file_path, "tfidf": True})
            
            if vector_r_response.status_code == 200 and 'vector' in vector_r_response.json():
                vector_r = vector_r_response.json()["vector"]
                compare_vectors(vector_q, vector_r, query_label="Reptilia", other_label=results['results'][0]['filename'])
            else:
                print("No se pudo obtener el vector del archivo similar")
        else:
            print("Endpoint /vector no disponible o no implementado aún")
            
    except Exception as e:
        print(f"Error al comparar vectores: {e}")
        print("Continuando sin comparación de vectores...")








    # 3. Buscar subiendo archivo
    print("\n3. Buscando por upload...")
    audio_file_path = os.path.join(os.path.dirname(__file__), "audio_to_see", "Bad_Bunny_-_BAILE_INoLVIDABLE_preview.wav")
    
    with open(audio_file_path, 'rb') as f:
        files = {'file': (os.path.basename(audio_file_path), f, 'audio/wav')}
        params = {'top_k': 3}
        
        response = requests.post(f"{API_BASE_URL}/search/upload", files=files, params=params)
        
        if response.status_code == 200:
            results = response.json()
            print(f"Archivo subido: {results['query_filename']}")
            print("Top 3 similares:")
            for audio in results['results']:
                print(f"  {audio['rank']}. {audio['filename']} - {audio['similarity_score']}")
        else:
            print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_api()