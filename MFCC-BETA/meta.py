import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3

def leer_metadatos(mp3_path):
    audio = MP3(mp3_path, ID3=ID3)
    tags = audio.tags

    return {
        "title": tags.get('TIT2').text[0] if 'TIT2' in tags else None,
        "artist": tags.get('TPE1').text[0] if 'TPE1' in tags else None,
        "album": tags.get('TALB').text[0] if 'TALB' in tags else None,
        "genre": tags.get('TCON').text[0] if 'TCON' in tags else None
    }





# === EJEMPLO DE USO ===
if __name__ == "__main__":
    # Usar audio de la carpeta audio_to_see como ejemplo
    ejemplo_audio = os.path.join(os.path.dirname(__file__), "audio_to_see", "The_Strokes_-_Reptilia.wav")
    
    if os.path.exists(ejemplo_audio):
        info = leer_metadatos(ejemplo_audio)
        nuevo_nombre = f"{info['artist']} - {info['title']} - {info['genre']}.wav"
        print(f"Nuevo nombre del archivo: {nuevo_nombre}")
    else:
        print("Archivo de ejemplo no encontrado. Coloca un audio en la carpeta 'audio_to_see' para probar.")