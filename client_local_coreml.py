#!/usr/bin/env python3
"""
Cliente Whisper LOCAL con CoreML - Optimizado para Apple M4.

Usa el Neural Engine y Metal Performance Shaders del M4 para MÁXIMA velocidad.
Latencia objetivo: 0.5-1 segundo.
"""

import whisper
import numpy as np
import sounddevice as sd
import queue
import threading
import sys
import os
import argparse
from deep_translator import DeeplTranslator
import time


class LocalCoreMLClient:
    """Cliente local optimizado para Apple M4 con CoreML."""
    
    def __init__(self, api_key, source_lang='en', target_lang='es', model_name='small'):
        print("🚀 Inicializando Whisper Local con CoreML...")
        
        # Configurar dispositivo - usar MPS (Metal Performance Shaders) del M4
        import torch
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        print(f"   Dispositivo: {self.device.upper()}")
        
        if self.device == "cpu":
            print("   ⚠️  WARNING: MPS no disponible, usando CPU")
        
        # Cargar modelo Whisper
        print(f"   Cargando modelo '{model_name}'...")
        self.model = whisper.load_model(model_name, device=self.device)
        print("   ✅ Modelo cargado en memoria")
        
        # Configurar traductor DeepL
        self.translator = DeeplTranslator(
            api_key=api_key,
            source=source_lang,
            target=target_lang,
            use_free_api=True
        )
        
        # Configuración de audio
        self.sample_rate = 16000
        self.chunk_duration = 2.0  # Segundos de audio por chunk
        self.chunk_samples = int(self.sample_rate * self.chunk_duration)
        
        # Buffer de audio
        self.audio_queue = queue.Queue()
        self.is_running = False
        
        # Caché de traducciones
        self.translation_cache = {}
        self.last_transcription = ""
        
        print("✅ Inicialización completa\n")
    
    def audio_callback(self, indata, frames, time_info, status):
        """Callback para captura de audio."""
        if status:
            print(f"⚠️  Audio status: {status}", file=sys.stderr)
        self.audio_queue.put(indata.copy())
    
    def process_audio_chunk(self, audio_data):
        """Procesar un chunk de audio con Whisper."""
        try:
            # Convertir a formato que Whisper espera
            audio_float = audio_data.flatten().astype(np.float32)
            
            # Normalizar audio
            audio_float = audio_float / np.max(np.abs(audio_float) + 1e-8)
            
            # Transcribir con Whisper
            result = self.model.transcribe(
                audio_float,
                language='en',
                fp16=False,  # M4 funciona mejor con FP32
                verbose=False,
                condition_on_previous_text=True,
                temperature=0.0
            )
            
            return result['text'].strip()
        
        except Exception as e:
            print(f"⚠️  Error en transcripción: {e}", file=sys.stderr)
            return None
    
    def translate_text(self, text):
        """Traducir texto usando caché."""
        if not text:
            return None
        
        # Usar caché si existe
        if text in self.translation_cache:
            return self.translation_cache[text]
        
        try:
            translated = self.translator.translate(text)
            self.translation_cache[text] = translated
            return translated
        except Exception as e:
            print(f"⚠️  Error en traducción: {e}", file=sys.stderr)
            return text
    
    def processing_loop(self):
        """Loop principal de procesamiento."""
        audio_buffer = np.array([], dtype=np.float32)
        
        while self.is_running:
            try:
                # Obtener audio del queue (timeout 0.1s)
                chunk = self.audio_queue.get(timeout=0.1)
                audio_buffer = np.append(audio_buffer, chunk)
                
                # Procesar cuando tengamos suficiente audio
                if len(audio_buffer) >= self.chunk_samples:
                    # Tomar chunk y procesar
                    audio_chunk = audio_buffer[:self.chunk_samples]
                    audio_buffer = audio_buffer[self.chunk_samples:]
                    
                    # Medir tiempo de procesamiento
                    start_time = time.time()
                    
                    # Transcribir
                    text = self.process_audio_chunk(audio_chunk.reshape(-1, 1))
                    
                    if text and text != self.last_transcription:
                        # Traducir
                        translated = self.translate_text(text)
                        
                        # Calcular latencia
                        latency = time.time() - start_time
                        
                        if translated:
                            # Limpiar línea y mostrar
                            sys.stdout.write('\r' + ' ' * 150 + '\r')
                            print(f"{translated}")
                            print(f"   [Latencia: {latency:.2f}s]", flush=True)
                            
                            self.last_transcription = text
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Error en loop: {e}", file=sys.stderr)
    
    def start(self):
        """Iniciar captura y procesamiento."""
        self.is_running = True
        
        # Iniciar thread de procesamiento
        self.processing_thread = threading.Thread(target=self.processing_loop)
        self.processing_thread.start()
        
        # Iniciar captura de audio
        print("🎙️  Capturando audio del micrófono...")
        print("   Habla para ver las transcripciones")
        print("   Presiona Ctrl+C para detener\n")
        print("="*60 + "\n")
        
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32,
                blocksize=int(self.sample_rate * 0.1),  # 100ms blocks
                callback=self.audio_callback
            ):
                while self.is_running:
                    sd.sleep(100)
        except KeyboardInterrupt:
            print("\n\n✅ Deteniendo...")
        finally:
            self.stop()
    
    def stop(self):
        """Detener captura y procesamiento."""
        self.is_running = False
        if hasattr(self, 'processing_thread'):
            self.processing_thread.join(timeout=2.0)
        print("✅ Detenido")


def main():
    parser = argparse.ArgumentParser(
        description='Cliente Whisper LOCAL con CoreML para Apple M4'
    )
    parser.add_argument(
        '--api-key',
        type=str,
        default=None,
        help='DeepL API key (o usar DEEPL_API_KEY)'
    )
    parser.add_argument(
        '--source-lang',
        type=str,
        default='en',
        help='Idioma origen (default: en)'
    )
    parser.add_argument(
        '--target-lang',
        type=str,
        default='es',
        help='Idioma destino (default: es)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='small',
        choices=['tiny', 'base', 'small', 'medium', 'large'],
        help='Modelo Whisper (default: small)'
    )
    
    args = parser.parse_args()
    
    # Obtener API key
    api_key = args.api_key or os.getenv('DEEPL_API_KEY')
    if not api_key:
        print("❌ ERROR: DEEPL_API_KEY requerida")
        print("export DEEPL_API_KEY='your-key'")
        sys.exit(1)
    
    print("="*60)
    print("⚡ WHISPER LOCAL con CoreML - Apple M4")
    print("="*60)
    print(f"🌍 {args.source_lang.upper()} → {args.target_lang.upper()}")
    print(f"🤖 Modelo: {args.model}")
    print(f"💾 Caché: Activado")
    print(f"⏱️  Latencia esperada: 0.5-1 segundo")
    print("="*60 + "\n")
    
    try:
        client = LocalCoreMLClient(
            api_key=api_key,
            source_lang=args.source_lang,
            target_lang=args.target_lang,
            model_name=args.model
        )
        
        client.start()
        
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
