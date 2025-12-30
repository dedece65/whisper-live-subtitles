#!/usr/bin/env python3
"""
Cliente Whisper M4 FINAL - Con Noise Gate y Protección de Audio.
Soluciona: RuntimeWarnings, Hallucinations ("Thank you") y Crash de DeepL.
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
from faster_whisper import WhisperModel
from urllib import request as urllib_request

class M4FinalClient:
    def __init__(self, api_key, source_lang='en', target_lang='es', model_size='small', web_display=False, glossary_id=None):
        print("🚀 Inicializando Whisper M4 (Blindado)...")
        
        # VALIDACIÓN DEEP L
        self.translator = None
        if api_key:
            try:
                self.translator = deepl.Translator(api_key)
                # Limpieza preventiva del ID del glosario
                if glossary_id and glossary_id.endswith(":fx"):
                    print("⚠️  AVISO: Se ha detectado ':fx' en el glossary_id. Eliminándolo automáticamente.")
                    glossary_id = glossary_id.replace(":fx", "")
                
                self.glossary_id = glossary_id
                print(f"   ✅ DeepL conectado. Glosario ID: {glossary_id if glossary_id else 'NO'}")
            except Exception as e:
                print(f"   ❌ Error conectando DeepL: {e}")
        
        # WHISPER INT8
        # compute_type="int8" es vital para velocidad en M4
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        print(f"   ✅ Modelo '{model_size}' cargado.")

        self.source_lang = source_lang
        self.target_lang = target_lang
        self.web_display = web_display
        self.web_server_url = "http://localhost:5000/subtitle"
        
        # AUDIO CONFIG
        self.sample_rate = 16000
        self.audio_queue = queue.Queue()
        self.is_running = False
        
        # BUFFER Y UMBRALES
        self.audio_buffer = np.array([], dtype=np.float32)
        self.max_buffer_duration = 7.0 
        
        # NOISE GATE (Importante para evitar "Thank you")
        self.amplitude_threshold = 0.01  # Si el audio no supera esto, es silencio
        self.silence_counter = 0

    def audio_callback(self, indata, frames, time_info, status):
        if status: 
            # Ignoramos underflows leves
            if "Input overflow" not in str(status):
                print(f"Audio Status: {status}", file=sys.stderr)
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
                # 1. GESTIÓN DE COLA (Evitar lag)
                new_audio_chunks = []
                while not self.audio_queue.empty():
                    new_audio_chunks.append(self.audio_queue.get())
                
                if not new_audio_chunks:
                    time.sleep(0.05)
                    continue

                # 2. CONCATENAR Y VERIFICAR NIVEL (NOISE GATE)
                chunk_concat = np.concatenate(new_audio_chunks).flatten().astype(np.float32)
                
                # Calcular amplitud máxima del chunk actual
                max_amp = np.max(np.abs(chunk_concat))
                
                # Si es silencio absoluto o ruido de fondo muy bajo, lo ignoramos para no ensuciar el buffer
                if max_amp < self.amplitude_threshold:
                    # Opcional: Si llevamos mucho silencio, limpiamos el buffer antiguo
                    self.silence_counter += 1
                    if self.silence_counter > 20: # ~2 segundos de silencio
                        self.audio_buffer = np.array([], dtype=np.float32)
                        self.silence_counter = 0
                        sys.stdout.write("\r🔇 Silencio detectado (Buffer limpiado)      ")
                        sys.stdout.flush()
                    continue
                
                self.silence_counter = 0 # Reset si hay audio
                self.audio_buffer = np.append(self.audio_buffer, chunk_concat)
                
                # Procesar solo si hay > 1 segundo acumulado
                buffer_duration = len(self.audio_buffer) / self.sample_rate
                if buffer_duration < 1.0:
                    continue

                # 3. TRANSCRIPCIÓN PROTEGIDA
                # Normalización segura para evitar "divide by zero"
                # (Faster-whisper lo hace internamente, pero si entra basura falla)
                if np.max(np.abs(self.audio_buffer)) == 0:
                    self.audio_buffer = np.array([], dtype=np.float32)
                    continue

                segments, info = self.model.transcribe(
                    self.audio_buffer, 
                    language=self.source_lang,
                    beam_size=5,
                    vad_filter=True, # VAD activado
                    vad_parameters=dict(min_silence_duration_ms=500),
                    condition_on_previous_text=False # Evita bucles de alucinación
                )
                
                current_text = " ".join([s.text for s in segments]).strip()
                
                if not current_text:
                    continue
                
                # Filtro Anti-Hallucination (Si repite lo mismo, ignorar)
                if current_text.lower() in ["thank you.", "thank you", "okay.", "subtitles by"]:
                    sys.stdout.write(f"\r👻 Alucinación ignorada: {current_text}")
                    sys.stdout.flush()
                    self.audio_buffer = np.array([], dtype=np.float32) # Matar el buffer culpable
                    continue

                sys.stdout.write(f"\r👂 Buffer ({buffer_duration:.1f}s): {current_text[-60:]}")
                sys.stdout.flush()

                # 4. DECISIÓN DE TRADUCCIÓN
                is_complete = current_text.endswith(('.', '?', '!'))
                is_too_long = buffer_duration > self.max_buffer_duration
                
                if is_complete or is_too_long:
                    print(f"\n⚡ ENVIANDO A DEEPL: {current_text}")
                    
                    final_es = current_text
                    if self.translator:
                        try:
                            # Contexto extra para DeepL
                            res = self.translator.translate_text(
                                current_text, 
                                source_lang=self.source_lang, 
                                target_lang=self.target_lang,
                                glossary=self.glossary_id
                            )
                            final_es = res.text
                        except Exception as e:
                            print(f"❌ Error DeepL: {e}")
                            if "glossary" in str(e).lower():
                                print("   SUGERENCIA: Revisa que el ID del glosario sea correcto y coincida con el par de idiomas (EN->ES).")

                    print(f"🇪🇸 {final_es}\n" + "-"*40)
                    self.send_to_web(final_es)
                    self.audio_buffer = np.array([], dtype=np.float32)

            except Exception as e:
                print(f"\n❌ Error Loop: {e}")
                # Si falla, limpiar buffer para no atascarse
                self.audio_buffer = np.array([], dtype=np.float32)

    def start(self):
        self.is_running = True
        t = threading.Thread(target=self.processing_loop)
        t.start()
        
        print("\n🎤 Grabando... (Asegúrate de que el micro input del Mac es correcto)")
        with sd.InputStream(callback=self.audio_callback, channels=1, samplerate=self.sample_rate):
            while self.is_running:
                sd.sleep(100)
    
    def stop(self):
        self.is_running = False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--api-key', type=str)
    parser.add_argument('--glossary-id', type=str)
    parser.add_argument('--model', type=str, default='small')
    parser.add_argument('--web-display', action='store_true')
    
    args = parser.parse_args()
    api_key = args.api_key or os.getenv('DEEPL_API_KEY')
    
    client = M4FinalClient(
        api_key=api_key, 
        model_size=args.model, 
        web_display=args.web_display, 
        glossary_id=args.glossary_id
    )
    try:
        client.start()
    except KeyboardInterrupt:
        client.stop()