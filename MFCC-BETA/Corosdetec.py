import os
import librosa
import numpy as np
import matplotlib.pyplot as plt
from pydub import AudioSegment
from collections import Counter
from scipy.signal import find_peaks

# === CONFIGURACIÓN ===
# Ejemplo: usar audio de la carpeta audio_to_see
ruta_audio = os.path.join(os.path.dirname(__file__), "audio_to_see", "Bad_Bunny_-_BAILE_INoLVIDABLE_preview.wav")
salida_audio = "coro_Bad Bunny_refinado.wav"


# === PASO 1: Cargar audio ===
def cargar_audio(ruta, sr=22050):
    y, sr = librosa.load(ruta, sr=sr)
    print(f"Audio cargado: duracion = {len(y)/sr:.2f} segundos")
    return y, sr

# === PASO 2: Análisis multi-criterio ===
def analizar_segmentos_completo(y, sr, ventana_s=20, hop_s=5):
    """Análisis completo: energía, repetición y características espectrales"""
    frame_length = 2048
    hop_length = 512
    
    # 1. Calcular energía (RMS)
    rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
    
    # 2. Calcular características espectrales
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=hop_length)
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop_length)[0]
    chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=hop_length)
    
    # 3. Calcular tempo y beats
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop_length)
    
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)
    
    ventana_frames = int(ventana_s * sr / hop_length)
    hop_frames = int(hop_s * sr / hop_length)
    
    segmentos = []
    
    print(f"Analizando segmentos (ventana: {ventana_s}s, salto: {hop_s}s)...")
    
    for i in range(0, len(rms) - ventana_frames, hop_frames):
        inicio_frame = i
        fin_frame = i + ventana_frames
        
        # Métricas del segmento
        energia_promedio = np.mean(rms[inicio_frame:fin_frame])
        energia_varianza = np.var(rms[inicio_frame:fin_frame])
        
        # Características espectrales
        mfcc_seg = mfcc[:, inicio_frame:fin_frame]
        centroid_promedio = np.mean(spectral_centroid[inicio_frame:fin_frame])
        chroma_seg = chroma[:, inicio_frame:fin_frame]
        
        # Estabilidad tonal (coros suelen ser más estables)
        estabilidad_tonal = 1.0 / (1.0 + np.var(chroma_seg))
        
        # Tiempo del segmento
        inicio_s = librosa.frames_to_time(inicio_frame, sr=sr, hop_length=hop_length)
        fin_s = librosa.frames_to_time(fin_frame, sr=sr, hop_length=hop_length)
        
        segmento = {
            'inicio_s': inicio_s,
            'fin_s': fin_s,
            'inicio_frame': inicio_frame,
            'fin_frame': fin_frame,
            'energia_promedio': energia_promedio,
            'energia_varianza': energia_varianza,
            'centroid_promedio': centroid_promedio,
            'estabilidad_tonal': estabilidad_tonal,
            'mfcc': mfcc_seg,
            'chroma': chroma_seg
        }
        
        segmentos.append(segmento)
    
    return segmentos, rms, times, tempo

# === PASO 3: Detectar similitudes (coros se repiten) ===
def calcular_similitudes(segmentos, umbral_similitud=0.7):
    """Calcula similitudes entre segmentos para encontrar repeticiones"""
    n_segmentos = len(segmentos)
    similitudes = np.zeros((n_segmentos, n_segmentos))
    
    print("Calculando similitudes entre segmentos...")
    
    for i in range(n_segmentos):
        for j in range(i + 1, n_segmentos):
            seg1 = segmentos[i]
            seg2 = segmentos[j]
            
            # Similitud basada en MFCC
            try:
                if seg1['mfcc'].shape[1] == seg2['mfcc'].shape[1]:
                    corr_mfcc = np.corrcoef(seg1['mfcc'].flatten(), seg2['mfcc'].flatten())[0, 1]
                    if np.isnan(corr_mfcc):
                        corr_mfcc = 0
                else:
                    corr_mfcc = 0
                
                # Similitud basada en chroma (armonía)
                if seg1['chroma'].shape[1] == seg2['chroma'].shape[1]:
                    corr_chroma = np.corrcoef(seg1['chroma'].flatten(), seg2['chroma'].flatten())[0, 1]
                    if np.isnan(corr_chroma):
                        corr_chroma = 0
                else:
                    corr_chroma = 0
                
                # Similitud combinada
                similitud = (corr_mfcc * 0.7 + corr_chroma * 0.3)
                similitudes[i, j] = similitud
                similitudes[j, i] = similitud
                
            except:
                similitudes[i, j] = 0
                similitudes[j, i] = 0
    
    return similitudes

# === PASO 4: Scoring multi-criterio ===
def calcular_score_coro(segmentos, similitudes):
    """Calcula un score para cada segmento basado en múltiples criterios"""
    scores = []
    
    for i, seg in enumerate(segmentos):
        # 1. Score de repetición (cuántas veces aparece similar)
        repeticiones = np.sum(similitudes[i, :] > 0.6)
        score_repeticion = repeticiones / len(segmentos)
        
        # 2. Score de energía (normalizado)
        energias = [s['energia_promedio'] for s in segmentos]
        energia_normalizada = seg['energia_promedio'] / max(energias)
        
        # 3. Score de posición (coros suelen estar en el tercio medio)
        posicion_relativa = seg['inicio_s'] / segmentos[-1]['fin_s']
        if 0.25 <= posicion_relativa <= 0.75:
            score_posicion = 1.0
        elif 0.15 <= posicion_relativa <= 0.85:
            score_posicion = 0.7
        else:
            score_posicion = 0.3
        
        # 4. Score de estabilidad tonal
        estabilidades = [s['estabilidad_tonal'] for s in segmentos]
        estabilidad_normalizada = seg['estabilidad_tonal'] / max(estabilidades)
        
        # 5. Score de varianza energética (coros suelen tener varianza moderada)
        varianzas = [s['energia_varianza'] for s in segmentos]
        varianza_normalizada = 1.0 - (seg['energia_varianza'] / max(varianzas))
        
        # Score combinado con pesos
        score_total = (
            score_repeticion * 0.35 +      # Más peso a repetición
            energia_normalizada * 0.25 +   # Energía importante pero no dominante
            score_posicion * 0.15 +        # Posición en la canción
            estabilidad_normalizada * 0.15 + # Estabilidad tonal
            varianza_normalizada * 0.10     # Varianza energética
        )
        
        scores.append({
            'indice': i,
            'score_total': score_total,
            'score_repeticion': score_repeticion,
            'energia_normalizada': energia_normalizada,
            'score_posicion': score_posicion,
            'repeticiones': repeticiones,
            'inicio_s': seg['inicio_s'],
            'fin_s': seg['fin_s']
        })
    
    return sorted(scores, key=lambda x: x['score_total'], reverse=True)

# === PASO 5: Expandir segmento a duración deseada ===
def expandir_segmento(mejor_segmento, segmentos_originales, duracion_objetivo=90):
    """Expande el mejor segmento a la duración objetivo"""
    idx = mejor_segmento['indice']
    seg_original = segmentos_originales[idx]
    
    inicio_actual = seg_original['inicio_s']
    fin_actual = seg_original['fin_s']
    duracion_actual = fin_actual - inicio_actual
    
    print(f"Segmento original: {inicio_actual:.2f}s - {fin_actual:.2f}s ({duracion_actual:.2f}s)")
    
    if duracion_actual >= duracion_objetivo:
        return inicio_actual, fin_actual
    
    # Expandir hacia ambos lados
    expansion_necesaria = duracion_objetivo - duracion_actual
    expansion_cada_lado = expansion_necesaria / 2
    
    nuevo_inicio = max(0, inicio_actual - expansion_cada_lado)
    nuevo_fin = fin_actual + expansion_cada_lado
    
    # Ajustar si se sale del audio
    duracion_total = segmentos_originales[-1]['fin_s']
    if nuevo_fin > duracion_total:
        nuevo_fin = duracion_total
        nuevo_inicio = max(0, nuevo_fin - duracion_objetivo)
    
    duracion_final = nuevo_fin - nuevo_inicio
    print(f"Segmento expandido: {nuevo_inicio:.2f}s - {nuevo_fin:.2f}s ({duracion_final:.2f}s)")
    
    return nuevo_inicio, nuevo_fin

# === PASO 6: Exportar con fade ===
def exportar_coro_refinado(path, inicio_s, fin_s, salida):
    """Exporta el coro con fade in/out"""
    print(f"Exportando segmento: {inicio_s:.2f}s - {fin_s:.2f}s")
    
    audio = AudioSegment.from_file(path)
    fragmento = audio[inicio_s * 1000: fin_s * 1000]
    
    # Aplicar fade suave
    fade_duration = min(1000, len(fragmento) // 10)  # Max 1 segundo o 10% del fragmento
    fragmento = fragmento.fade_in(fade_duration).fade_out(fade_duration)
    
    fragmento.export(salida, format="wav")
    print(f"Coro refinado exportado: {salida}")

# === PASO 7: Visualización mejorada ===
def visualizar_analisis(y, sr, segmentos, scores, mejor_idx, inicio_final, fin_final, rms, times):
    """Visualización completa del análisis"""
    plt.figure(figsize=(16, 12))
    
    # Subplot 1: Waveform con segmentos
    plt.subplot(4, 1, 1)
    tiempo_audio = np.linspace(0, len(y) / sr, len(y))
    plt.plot(tiempo_audio, y, alpha=0.6, color='gray')
    
    # Mostrar top 3 candidatos
    colores = ['red', 'orange', 'yellow']
    for i, score in enumerate(scores[:3]):
        seg = segmentos[score['indice']]
        color = colores[i] if i < 3 else 'blue'
        alpha = 0.5 if i == 0 else 0.3
        plt.axvspan(seg['inicio_s'], seg['fin_s'], alpha=alpha, color=color, 
                   label=f"Candidato {i+1} (score: {score['score_total']:.3f})")
    
    # Segmento final seleccionado
    plt.axvspan(inicio_final, fin_final, alpha=0.7, color='darkred', 
               label='Coro final expandido')
    
    plt.title('Análisis de Candidatos a Coro')
    plt.xlabel('Tiempo (s)')
    plt.ylabel('Amplitud')
    plt.legend()
    
    # Subplot 2: RMS Energy
    plt.subplot(4, 1, 2)
    plt.plot(times, rms, color='blue', alpha=0.8)
    plt.axvspan(inicio_final, fin_final, alpha=0.3, color='red')
    plt.title('Energía RMS')
    plt.xlabel('Tiempo (s)')
    plt.ylabel('RMS')
    
    # Subplot 3: Scores por segmento
    plt.subplot(4, 1, 3)
    indices = [s['indice'] for s in scores]
    scores_totales = [s['score_total'] for s in scores]
    tiempos_inicio = [segmentos[s['indice']]['inicio_s'] for s in scores]
    
    plt.scatter(tiempos_inicio, scores_totales, c=scores_totales, cmap='viridis', s=50)
    plt.colorbar(label='Score')
    plt.title('Score de cada segmento')
    plt.xlabel('Tiempo de inicio (s)')
    plt.ylabel('Score total')
    
    # Subplot 4: Desglose del mejor score
    plt.subplot(4, 1, 4)
    mejor_score = scores[0]
    categorias = ['Repetición', 'Energía', 'Posición', 'Estabilidad']
    valores = [
        mejor_score['score_repeticion'],
        mejor_score['energia_normalizada'],
        mejor_score['score_posicion'],
        0.5  # Placeholder para estabilidad
    ]
    
    plt.bar(categorias, valores, color=['red', 'blue', 'green', 'orange'])
    plt.title(f'Desglose del mejor candidato (Score total: {mejor_score["score_total"]:.3f})')
    plt.ylabel('Score normalizado')
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.show()

# === MAIN REFINADO PARA 30 SEGUNDOS ===
if __name__ == "__main__":
    print("=== DETECTOR DE CORO REFINADO - 30 SEGUNDOS ===")
    
    # Cargar audio
    y, sr = cargar_audio(ruta_audio)
    
    # Análisis completo - ventanas más pequeñas para mejor precisión en 30s
    segmentos, rms, times, tempo = analizar_segmentos_completo(y, sr, ventana_s=12, hop_s=2)
    print(f"Detectados {len(segmentos)} segmentos para análisis")
    
    # Calcular similitudes
    similitudes = calcular_similitudes(segmentos)
    
    # Calcular scores
    scores = calcular_score_coro(segmentos, similitudes)
    
    # Mostrar top candidatos
    print("\nTop 5 candidatos a coro:")
    for i, score in enumerate(scores[:5]):
        seg = segmentos[score['indice']]
        print(f"  {i+1}. Tiempo: {seg['inicio_s']:.1f}s-{seg['fin_s']:.1f}s, "
              f"Score: {score['score_total']:.3f}, "
              f"Repeticiones: {score['repeticiones']}")
    
    # Seleccionar mejor candidato
    mejor_candidato = scores[0]
    mejor_idx = mejor_candidato['indice']
    
    # Expandir a 30 segundos
    inicio_final, fin_final = expandir_segmento(mejor_candidato, segmentos, duracion_objetivo=30)
    
    # Exportar
    exportar_coro_refinado(ruta_audio, inicio_final, fin_final, salida_audio)
    
    # Visualizar
    #visualizar_analisis(y, sr, segmentos, scores, mejor_idx, inicio_final, fin_final, rms, times)
    
    print("Análisis completado!")