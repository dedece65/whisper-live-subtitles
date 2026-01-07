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
import re
import logging
from faster_whisper import WhisperModel
from urllib import request as urllib_request

# 1. LIMPIEZA DE CONSOLA
warnings.filterwarnings("ignore", category=RuntimeWarning)
logging.getLogger("urllib3").setLevel(logging.ERROR)

class M4ProClient:
    def __init__(self, api_key, source_lang='en', target_lang='es', model_size='distil-medium.en', web_display=False, glossary_id=None, max_time=6.0):
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

        # --- WHISPER INT8, CAMBIAR A FLOAT16 SI VAMOS A USAR GPU ---
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8", cpu_threads=8)
        
        # --- CONFIGURACIÓN PRO ---
        # Palabras clave para guiar a Whisper
        self.initial_prompt = (
            "This is a technical seminar by Bob McCarthy about System Design and Optimization, "
            "hosted by Meyer Sound and RMS Proaudio at Cartuja Center CITE in Seville. "
            "Topics include MAPP 3D prediction, Galileo GALAXY processing, SIM measurements, and FFT analysis. "
            "References to Metallica WorldWired tour, Roskilde Festival, and Focal Press books. "
            "Key concepts: LMBC, splay angles, phase vs frequency, coherence, and sound pressure level (SPL)."
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
        self.max_buffer_duration = max_time
        self.min_words_trigger = 4
        self.amplitude_threshold = 0.015 
        self.overlap_duration = 0.25

        # --- FILTROS ESTADÍSTICOS DE SILENCIO ---
        self.no_speech_threshold = 0.6
        self.max_compression_ratio = 2.4

        # --- NIVEL DE CONFIANZA --- 
        self.min_confidence = 0.70

        # --- MEMORIA DE CONTEXTO ---
        self.context_history = []
        self.max_context_sentences = 3
        

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            print(f"⚠️ Audio callback error: {status}")

        if self.audio_queue.qsize() > 50: 
            while not self.audio_queue.empty():
                try: self.audio_queue.get_nowait()
                except queue.Empty: break
            print("Lag detectado: Saltando audio para sincronizar...")

        self.audio_queue.put(indata.copy())

    def send_to_web(self, text):
        if not self.web_display or not text: return
        try:
            data = json.dumps({'text': text}).encode('utf-8')
            req = urllib_request.Request(self.web_server_url, data=data, headers={'Content-Type': 'application/json'})
            urllib_request.urlopen(req, timeout=0.3)
        except Exception:
            pass

    def clean_text(self, text):
        """Limpia errores comunes de formato de Whisper."""
        text = re.sub(r'\s+([,.?!])', r'\1', text)
        text = re.sub(r'\s+', ' ', text)
        # Eliminar repeticiones de palabras
        text = re.sub(r'\b(\w+)( \1){2,}\b', r'\1', text, flags=re.IGNORECASE)
        return text.strip().capitalize()

    def processing_loop(self):
        while self.is_running:
            try:
                # 1. Recoger audio de la cola
                new_chunks = []
                while not self.audio_queue.empty():
                    new_chunks.append(self.audio_queue.get())
                
                if not new_chunks:
                    time.sleep(0.1)
                    continue

                chunk_concat = np.concatenate(new_chunks).flatten().astype(np.float32)
                
                # Noise Gate simple
                if np.max(np.abs(chunk_concat)) < self.amplitude_threshold:
                    continue 

                self.audio_buffer = np.append(self.audio_buffer, chunk_concat)
                
                # Procesar solo si tenemos audio sustancial (>1.5s)
                buffer_duration = len(self.audio_buffer) / self.sample_rate
                if buffer_duration < 1.2:
                    continue

                # 2. Transcribir con mayor granularidad
                segments, info = self.model.transcribe(
                    self.audio_buffer, 
                    language=self.source_lang,
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=500),
                    initial_prompt=self.initial_prompt,
                    word_timestamps=True,
                    beam_size=1,
                    no_speech_threshold=self.no_speech_threshold,
                    compression_ratio_threshold=self.max_compression_ratio,
                    condition_on_previous_text=True
                )

                valid_segments = []
                for s in segments:
                    if s.no_speech_prob < self.no_speech_threshold and s.compression_ratio < self.max_compression_ratio:
                        valid_segments.append(s)
                
                if not valid_segments:
                    if buffer_duration > 12: self.audio_buffer = np.array([], dtype=np.float32)
                    continue
                
                # Extraemos palabras y su probabilidad media
                words_info = [word for segment in valid_segments for word in segment.words]
                if not words_info:
                    if buffer_duration > 15: self.audio_buffer = np.array([], dtype=np.float32)
                    continue
                
                current_text = " ".join([w.word for w in words_info]).strip()
                
                # Calculamos la confianza media de la frase actual
                if words_info:
                    avg_confidence = sum([w.probability for w in words_info]) / len(words_info)
                else:
                    avg_confidence = 0

                if not current_text or avg_confidence < self.min_confidence:
                    # Si la confianza es muy baja, no procesamos todavía, esperamos más audio
                    continue

                sys.stdout.write(f"\r👂 [Conf: {avg_confidence:.2f}] ({buffer_duration:.1f}s): {current_text[-60:]:>60}")
                sys.stdout.flush()

                # 3. LÓGICA DE SEGMENTACIÓN INTELIGENTE
                last_word_end = words_info[-1].end if words_info else 0
                trailing_silence = buffer_duration - last_word_end
                has_terminal_punc = current_text.endswith(('.', '?', '!', ':'))
                is_natural_pause = trailing_silence > 0.5
                is_meaningful = len(words_info) >= self.min_words_trigger

                should_translate = (
                    (has_terminal_punc and is_natural_pause) or \
                    (is_natural_pause and is_meaningful) or \
                    (buffer_duration > self.max_buffer_duration)
                )

                if should_translate:
                    start_time = time.time()

                    if avg_confidence > self.min_confidence:
                        clean_en = self.clean_text(current_text)

                        t0 = time.time()

                        final_es = self.translate_with_deepl(clean_en)
                        print(f"\n DeepL tardó: {time.time() - t0:.2f}s")
                        #print(f"\n🇬🇧 Contexto previo: {translation_context[-50:] if translation_context else 'None'}")
                        print(f"\n🇬🇧 {clean_en}")
                        print(f"🇪🇸 {final_es}")
                        print("-" * 100)

                        self.send_to_web(final_es)
                    
                    overlap_samples = int(self.overlap_duration * self.sample_rate)
                    self.audio_buffer = self.audio_buffer[-overlap_samples:]
                    print(f"Procesamiento tardó: {time.time() - start_time:.2f}s")

            except Exception as e:
                print(f"⚠️ Error en bucle principal: {e}")
                time.sleep(0.1)

    def translate_with_deepl(self, text):
        if not self.translator: return text
        try:
            context = " ".join(self.context_history)
            res = self.translator.translate_text(
                text,
                source_lang=self.source_lang.upper(),
                target_lang=self.target_lang.upper(),
                glossary=self.glossary_id,
                context=context
            )
            self.context_history.append(text)
            if len(self.context_history) > self.max_context_sentences: self.context_history.pop(0)
            return res.text
        except:
            return text

    def start(self):
        self.is_running = True
        threading.Thread(target=self.processing_loop, daemon=True).start()
        print("\n🎤 Escuchando... (Contexto de Ingeniería Activado)")
        try:
            with sd.InputStream(callback=self.audio_callback, channels=1, samplerate=self.sample_rate, blocksize=int(self.sample_rate * 0.1)):
                while self.is_running: sd.sleep(100)
        except Exception as e:
            print(f"\n\n Error en InputStream: {e}")
            self.stop()
    
    def stop(self):
        self.is_running = False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--glossary-id', type=str)
    parser.add_argument('--web-display', action='store_true')
    parser.add_argument('--model', type=str, default='distil-medium.en')
    parser.add_argument('--max-time', type=float, default=6.0)
    args = parser.parse_args()
    
    api_key = os.getenv('DEEPL_API_KEY')
    client = M4ProClient(api_key, model_size=args.model, web_display=args.web_display, glossary_id=args.glossary_id, max_time=args.max_time)
    try: client.start()
    except KeyboardInterrupt: client.stop()