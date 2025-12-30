#!/usr/bin/env python3
"""
Cliente Whisper SEMÁNTICO - Prioridad: COHERENCIA Y COMPRENSIÓN.
Espera a tener una 'idea completa' antes de traducir.
Usa análisis de texto para cortar en comas, puntos o conjunciones.
"""

import numpy as np
import sounddevice as sd
import queue
import threading
import sys
import os
import argparse
import deepl
import time
import json
import warnings
import re
from faster_whisper import WhisperModel
from urllib import request as urllib_request

warnings.filterwarnings("ignore")

class SemanticClient:
    def __init__(self, api_key, source_lang='en', target_lang='es', model_size='small', web_display=False, glossary_id=None):
        print("🚀 Inicializando Whisper SEMÁNTICO (Modo Profesor)...")
        
        # --- DEEPL ---
        self.translator = None
        if api_key:
            try:
                self.translator = deepl.Translator(api_key)
                self.glossary_id = glossary_id
                if glossary_id:
                    print(f"   ✅ Glosario ID: {glossary_id}")
            except Exception as e:
                print(f"   ❌ Error DeepL: {e}")

        # --- WHISPER ---
        # Usamos beam_size=5 para mayor precisión en la puntuación (clave para saber dónde cortar)
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        
        # Prompt diseñado para forzar puntuación correcta y vocabulario
        self.initial_prompt = (
            "Technical audio engineering seminar. "
            "Sentences must end with punctuation. "
            "Terms: Phase shift, 360 degrees, wavelength, comb filtering, polarity, "
            "milliseconds, spiral function, magnitude response, coherence, FFT, subwoofer array."
        )
        
        self.web_server_url = "http://localhost:5000/subtitle"
        self.web_display = web_display
        self.source_lang = source_lang
        self.target_lang = target_lang
        
        # --- AUDIO ---
        self.sample_rate = 16000
        self.audio_queue = queue.Queue()
        self.is_running = False
        self.audio_buffer = np.array([], dtype=np.float32)
        
        # --- BUFFERS DE TEXTO ---
        self.text_accumulator = ""  # Texto crudo de Whisper acumulándose
        
        # --- PARÁMETROS SEMÁNTICOS ---
        self.min_sentence_length = 15  # Caracteres mínimos para considerar traducir
        self.max_latency_gap = 5.0     # Si pasan 5s sin puntuación, forzar corte inteligente
        self.last_send_time = time.time()

    def audio_callback(self, indata, frames, time_info, status):
        self.audio_queue.put(indata.copy())

    def send_to_web(self, text):
        if not self.web_display or not text: return
        try:
            data = json.dumps({'text': text}).encode('utf-8')
            req = urllib_request.Request(self.web_server_url, data=data, headers={'Content-Type': 'application/json'})
            urllib_request.urlopen(req, timeout=0.2) 
        except: pass

    def is_semantic_break(self, text, time_elapsed):
        """
        Decide si el texto actual es una 'idea completa' digna de ser traducida.
        Retorna: (Bool: Enviar?, String: Texto a enviar, String: Remanente para el buffer)
        """
        text = text.strip()
        if len(text) < self.min_sentence_length:
            return False, "", text

        # 1. Prioridad: Final de frase claro (. ? !)
        if text.endswith(('.', '?', '!')):
            return True, text, ""

        # 2. Prioridad: Comas o pausas largas SI el texto ya es largo
        # (Esto ayuda a no esperar 15 segundos si el ponente hace frases subordinadas)
        if time_elapsed > 2.5 and len(text.split()) > 8:
            # Buscar la última coma o conjunción fuerte
            match = re.search(r'([,])\s', text)
            if match:
                split_idx = match.start() + 1
                to_send = text[:split_idx].strip()
                remainder = text[split_idx:].strip()
                return True, to_send, remainder
        
        # 3. Emergencia: Ha pasado mucho tiempo sin puntuación (Pánico)
        if time_elapsed > self.max_latency_gap:
            # Cortar en el último espacio disponible
            last_space = text.rfind(' ')
            if last_space != -1:
                return True, text[:last_space], text[last_space:].strip()
            else:
                return True, text, "" # Enviar todo aunque sea una palabra larguísima

        return False, "", text

    def processing_loop(self):
        while self.is_running:
            try:
                # 1. Recoger audio (Bloques pequeños para reactividad)
                new_chunks = []
                while not self.audio_queue.empty():
                    new_chunks.append(self.audio_queue.get())
                
                if not new_chunks:
                    time.sleep(0.02)
                    continue

                chunk_concat = np.concatenate(new_chunks).flatten().astype(np.float32)
                
                # Noise Gate suave
                if np.max(np.abs(chunk_concat)) > 0.01:
                    self.audio_buffer = np.append(self.audio_buffer, chunk_concat)
                
                # Procesar cada vez que tengamos > 0.6s de audio nuevo en el buffer total
                # O si el buffer es muy grande
                buffer_duration = len(self.audio_buffer) / self.sample_rate
                
                if buffer_duration < 1.0:
                    continue

                # 2. Transcribir Buffer COMPLETO (re-evaluando el contexto)
                # Al procesar todo el buffer cada vez, Whisper puede corregir "The face" por "The phase"
                # cuando escucha la siguiente palabra "shift".
                segments, _ = self.model.transcribe(
                    self.audio_buffer, 
                    language=self.source_lang,
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=400),
                    initial_prompt=self.initial_prompt,
                    beam_size=5 # Mayor calidad para detectar puntuación
                )
                
                current_transcription = " ".join([s.text for s in segments]).strip()
                
                # Visualización de lo que Whisper está "pensando" (inestable)
                sys.stdout.write(f"\r🧠 Pensando: {current_transcription[-60:]}")
                sys.stdout.flush()

                # 3. ANÁLISIS SEMÁNTICO
                time_since_last = time.time() - self.last_send_time
                should_send, text_to_translate, remainder = self.is_semantic_break(current_transcription, time_since_last)

                if should_send:
                    print(f"\n💡 IDEA COMPLETADA: {text_to_translate}")
                    
                    # Traducir
                    final_es = text_to_translate
                    if self.translator:
                        try:
                            res = self.translator.translate_text(
                                text_to_translate, 
                                source_lang=self.source_lang, 
                                target_lang=self.target_lang, 
                                glossary=self.glossary_id
                            )
                            final_es = res.text
                        except Exception as e:
                            print(f"Error DeepL: {e}")

                    print(f"🇪🇸 {final_es}\n" + "-"*40)
                    self.send_to_web(final_es)
                    
                    # RESET INTELIGENTE
                    # Guardamos el "resto" (lo que iba después de la coma) en el buffer de texto
                    # Pero en audio, es difícil cortar exacto.
                    # Estrategia: Limpiar audio buffer y confiar en el VAD para la siguiente frase.
                    # Si había remanente (remainder), lo ideal sería inyectarlo como prompt, 
                    # pero para simplificar y evitar bucles, limpiamos todo.
                    # La coherencia > 2.5s suele ser suficiente.
                    
                    self.audio_buffer = np.array([], dtype=np.float32)
                    self.last_send_time = time.time()
                
                # Si el buffer crece demasiado sin sentido (>7s), forzar limpieza para evitar lag infinito
                if buffer_duration > 8.0:
                     self.audio_buffer = np.array([], dtype=np.float32)

            except Exception as e:
                print(f"\n❌ Error: {e}")
                self.audio_buffer = np.array([], dtype=np.float32)

    def start(self):
        self.is_running = True
        threading.Thread(target=self.processing_loop).start()
        print("\n🎤 Escuchando... (Modo Semántico: Esperando ideas completas)")
        with sd.InputStream(callback=self.audio_callback, channels=1, samplerate=self.sample_rate):
            while self.is_running: sd.sleep(100)
    
    def stop(self):
        self.is_running = False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--glossary-id', type=str)
    parser.add_argument('--web-display', action='store_true')
    parser.add_argument('--model', type=str, default='small')
    args = parser.parse_args()
    
    api_key = os.getenv('DEEPL_API_KEY')
    client = SemanticClient(api_key, model_size=args.model, web_display=args.web_display, glossary_id=args.glossary_id)
    try: client.start()
    except KeyboardInterrupt: client.stop()