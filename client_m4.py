#!/usr/bin/env python3

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
        # Palabras clave para guiar a Whisper
        self.initial_prompt = (
            "This is a professional technical lecture about audio engineering and sound physics. "
            "Terminology: Phase shift, 360°, wavelength, comb filtering, polarity, millisecond, "
            "Fast Fourier Transform, SPL, decibels, Ohm's law, impedance."
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
        
        # --- CONTROL DE FLUJO ---
        self.max_buffer_duration = 10.0  # Aguantar más tiempo para formar frases
        self.min_sentence_length = 20    # No traducir si hay menos de X caracteres (evita "And then.")
        self.amplitude_threshold = 0.015 

        # --- NIVEL DE CONFIANZA --- 
        self.min_confidence = 0.7

        # --- MEMORIA DE CONTEXTO ---
        self.context_history = []
        self.max_context_sentences = 3
        

    def audio_callback(self, indata, frames, time_info, status):
        self.audio_queue.put(indata.copy())

    def send_to_web(self, text):
        if not self.web_display or not text: return
        try:
            data = json.dumps({'text': text}).encode('utf-8')
            req = urllib_request.Request(self.web_server_url, data=data, headers={'Content-Type': 'application/json'})
            urllib_request.urlopen(req, timeout=0.5)
        except: pass

    def clean_text(self, text):
        """Limpia errores comunes de formato de Whisper."""
        import re
        # Elimina espacios antes de comas, puntos o signos de interrogación
        text = re.sub(r'\s+([,.?!])', r'\1', text)
        # Corrige dobles espacios
        text = re.sub(r'\s+', ' ', text)
        # Asegura que la primera letra sea mayúscula
        text = text.strip().capitalize()
        return text

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

                # 2. Transcribir con mayor granularidad
                segments, info = self.model.transcribe(
                    self.audio_buffer, 
                    language=self.source_lang,
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=600),
                    initial_prompt=self.initial_prompt,
                    word_timestamps=True,
                    beam_size=5
                )
                
                # Extraemos palabras y su probabilidad media
                words_info = []
                for segment in segments:
                    for word in segment.words:
                        words_info.append(word)

                current_text = " ".join([w.word for w in words_info]).strip()
                
                # Calculamos la confianza media de la frase actual
                if words_info:
                    avg_confidence = sum([w.probability for w in words_info]) / len(words_info)
                else:
                    avg_confidence = 0

                if not current_text or avg_confidence < self.min_confidence:
                    # Si la confianza es muy baja, no procesamos todavía, esperamos más audio
                    continue

                sys.stdout.write(f"\r👂 [Conf: {avg_confidence:.2f}] ({buffer_duration:.1f}s): {current_text}")
                sys.stdout.flush()

                # 3. LÓGICA DE "SMART SEGMENTATION"
                # Analizar el último segmento para ver si hay un cierre natural
                # Buscamos si el último "chunk" termina en silencio significativo
                # 'info.duration' es el tiempo total procesado en este ciclo
                # 'segments' contiene los tiempos de inicio/fin
                
                last_word_end = words_info[-1].end if words_info else 0
                trailing_silence = buffer_duration - last_word_end

                # 1. ¿Hay un punto/pregunta al final?
                has_terminal_punc = current_text.endswith(('.', '?', '!', ':'))
                
                # 2. ¿Hay un silencio tras la última palabra > 0.8s (un respiro claro)?
                is_natural_pause = trailing_silence > 0.5
                
                # 3. ¿La frase es lo suficientemente larga para tener sentido (mín. 4 palabras)?
                is_meaningful = len(words_info) > 4

                # El disparador: Si hay puntuación Y pausa, O si la pausa es muy larga, O timeout de seguridad
                should_translate = (has_terminal_punc and is_natural_pause) or \
                                 (is_natural_pause and is_meaningful) or \
                                 (buffer_duration > self.max_buffer_duration)

                if should_translate:
                    current_text = self.clean_text(current_text)
                    
                    # 1. PREPARAR CONTEXTO (Fase 2.1)
                    # Unimos las frases anteriores para que DeepL entienda el hilo conductor
                    translation_context = " ".join(self.context_history)
                    
                    final_es = current_text
                    if self.translator:
                        try:
                            # 2. TRADUCCIÓN CON MEMORIA
                            # El parámetro 'context' ayuda a mantener género, número y terminología
                            res = self.translator.translate_text(
                                current_text, 
                                source_lang=self.source_lang, 
                                target_lang=self.target_lang, 
                                glossary=self.glossary_id,
                                context=translation_context # <--- La clave de la Fase 2
                            )
                            final_es = res.text
                            
                            # 3. ACTUALIZAR HISTORIAL
                            # Guardamos la frase original (inglés) para la siguiente traducción
                            self.context_history.append(current_text)
                            if len(self.context_history) > self.max_context_sentences:
                                self.context_history.pop(0) # Mantener solo las últimas N
                                
                        except Exception as e:
                            print(f"❌ Error DeepL: {e}")
                    
                    print(f"\n🇬🇧 Contexto previo: {translation_context[-50:] if translation_context else 'None'}")
                    print(f"🇪🇸 {final_es}")
                    print("-" * 50)
                    
                    self.send_to_web(final_es)
                    self.audio_buffer = np.array([], dtype=np.float32)

            except Exception as e:
                print(f"⚠️ Error en bucle principal: {e}")
                time.sleep(0.1)

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