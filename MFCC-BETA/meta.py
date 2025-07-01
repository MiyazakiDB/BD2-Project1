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





info = leer_metadatos("C:/Users/tokio/OneDrive/Escritorio/Pruebin/The Strokes - Reptilia.mp3")
nuevo_nombre = f"{info['artist']} - {info['title']} - {info['genre']} .mp3"


print(f"Nuevo nombre del archivo: {nuevo_nombre}")