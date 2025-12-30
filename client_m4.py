#!/usr/bin/env python3
"""
Cliente Whisper PRO - Con Contexto de Ingeniería y Buffer Inteligente.
Soluciona: Fragmentación de frases, alucinaciones ($) y errores de vocabulario.
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
from faster_whisper import WhisperModel
from urllib import request as urllib_request

# 1. LIMPIEZA DE CONSOLA (Ocultar warnings matemáticos irrelevantes)
warnings.filterwarnings("ignore", category=RuntimeWarning)

class M4ProClient:
    def __init__(self, api_key, source_lang='en', target_lang='es', model_size='small', web_display=False, glossary_id=None):
        print("🚀 Inicializando Whisper PRO (Ingeniería de Sonido)...")
        
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

        # --- WHISPER INT8 ---
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        
        # --- CONFIGURACIÓN PRO ---
        # Palabras clave para guiar a Whisper y evitar "$360,000"
        self.initial_prompt = "Audio engineering technical class. Vocabulary: Phase shift, 360 degrees, wavelength, comb filtering, linear frequency, logarithmic display, polarity, milliseconds, spiral function, magnitude."
        
        self.web_server_url = "http://localhost:5000/subtitle"
        self.web_display = web_display
        self.source_lang = source_lang
        self.target_lang = target_lang
        
        # --- AUDIO ---
        self.sample_rate = 16000
        self.audio_queue = queue.Queue()
        self.is_running = False
        self.audio_buffer = np.array([], dtype=np.float32)
        
        # --- CONTROL DE FLUJO ---
        self.max_buffer_duration = 10.0  # Aguantar más tiempo para formar frases
        self.min_sentence_length = 20    # No traducir si hay menos de X caracteres (evita "And then.")
        self.amplitude_threshold = 0.015 

    def audio_callback(self, indata, frames, time_info, status):
        self.audio_queue.put(indata.copy())

    def send_to_web(self, text):
        if not self.web_display or not text: return
        try:
            data = json.dumps({'text': text}).encode('utf-8')
            req = urllib_request.Request(self.web_server_url, data=data, headers={'Content-Type': 'application/json'})
            urllib_request.urlopen(req, timeout=0.5)
        except: pass

    def processing_loop(self):
        while self.is_running:
            try:
                # 1. Recoger Audio
                new_chunks = []
                while not self.audio_queue.empty():
                    new_chunks.append(self.audio_queue.get())
                
                if not new_chunks:
                    time.sleep(0.05)
                    continue

                chunk_concat = np.concatenate(new_chunks).flatten().astype(np.float32)
                
                # Noise Gate simple
                if np.max(np.abs(chunk_concat)) < self.amplitude_threshold:
                    continue 

                self.audio_buffer = np.append(self.audio_buffer, chunk_concat)
                
                # Procesar solo si tenemos audio sustancial (>1.5s)
                buffer_duration = len(self.audio_buffer) / self.sample_rate
                if buffer_duration < 1.5:
                    continue

                # 2. Transcribir con CONTEXTO
                # initial_prompt es la clave para arreglar "Wavelin" y "$360,000"
                segments, _ = self.model.transcribe(
                    self.audio_buffer, 
                    language=self.source_lang,
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=700), # Menos sensible a pausas cortas
                    initial_prompt=self.initial_prompt,
                    condition_on_previous_text=False
                )
                
                current_text = " ".join([s.text for s in segments]).strip()
                
                if not current_text: continue

                # Filtro de alucinaciones
                if current_text.lower() in ["thank you.", "subtitles by", "copyright", "okay."]:
                    self.audio_buffer = np.array([], dtype=np.float32)
                    continue

                sys.stdout.write(f"\r👂 ({buffer_duration:.1f}s): {current_text[-70:]}")
                sys.stdout.flush()

                # 3. LÓGICA DE "FRASE COMPLETA" MEJORADA
                # Criterios para traducir:
                # A. Termina en puntuación Y es suficientemente larga (evita traducir "And.")
                # B. El buffer es demasiado grande (> 10s), hay que soltarlo ya.
                
                ends_punctuation = current_text.endswith(('.', '?', '!'))
                is_long_enough = len(current_text) > self.min_sentence_length
                force_timeout = buffer_duration > self.max_buffer_duration
                
                should_translate = (ends_punctuation and is_long_enough) or force_timeout

                if should_translate:
                    print(f"\n⚡ TRADUCIENDO: {current_text}")
                    
                    final_es = current_text
                    if self.translator:
                        try:
                            # Contexto para DeepL: Unir frases previas si es necesario
                            res = self.translator.translate_text(
                                current_text, 
                                source_lang=self.source_lang, 
                                target_lang=self.target_lang, 
                                glossary=self.glossary_id
                            )
                            final_es = res.text
                        except Exception as e:
                            print(f"Error DeepL: {e}")
                    
                    print(f"🇪🇸 {final_es}\n" + "-"*40)
                    self.send_to_web(final_es)
                    
                    # Limpieza
                    self.audio_buffer = np.array([], dtype=np.float32)

            except Exception as e:
                print(f"\n❌ Error: {e}")
                self.audio_buffer = np.array([], dtype=np.float32)

    def start(self):
        self.is_running = True
        threading.Thread(target=self.processing_loop).start()
        print("\n🎤 Escuchando... (Contexto de Ingeniería Activado)")
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
    client = M4ProClient(api_key, model_size=args.model, web_display=args.web_display, glossary_id=args.glossary_id)
    try: client.start()
    except KeyboardInterrupt: client.stop()