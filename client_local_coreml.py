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
import deepl
import time
import json
from urllib import request as urllib_request, error as urllib_error

# Deshabilitar barras de progreso de tqdm (usadas por Whisper)
import warnings
warnings.filterwarnings("ignore")
os.environ["TQDM_DISABLE"] = "1"

# Monkey-patch tqdm para deshabilitarla completamente
class DummyTqdm:
    def __init__(self, *args, **kwargs):
        pass
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def update(self, *args, **kwargs):
        pass
    def close(self):
        pass
    def set_description(self, *args, **kwargs):
        pass

import sys
sys.modules['tqdm'] = type(sys)('tqdm')
sys.modules['tqdm'].tqdm = DummyTqdm
sys.modules['tqdm.auto'] = type(sys)('tqdm.auto')
sys.modules['tqdm.auto'].tqdm = DummyTqdm


class LocalCoreMLClient:
    """Cliente local optimizado para Apple M4 con CoreML."""
    
    def __init__(self, api_key, source_lang='en', target_lang='es', model_name='small', web_display=False, glossary_id=None, sentence_mode=False, transcribe_only=False):
        print("🚀 Inicializando Whisper Local con CoreML...")
        
        # NOTA: openai-whisper tiene problemas con MPS (sparse tensors)
        # Usamos CPU, que en M4 es MUCHO más rápido que en Intel
        # Ver: https://github.com/openai/whisper/issues/1121
        self.device = "cpu"
        print(f"   Dispositivo: CPU (optimizado para Apple Silicon)")
        print(f"   ℹ️  M4 CPU > Docker CPU genérico")
        
        # Cargar modelo Whisper
        print(f"   Cargando modelo '{model_name}'...")
        self.model = whisper.load_model(model_name, device=self.device)
        print("   ✅ Modelo cargado en memoria") 
        
        # Configurar traductor DeepL (biblioteca oficial)
        self.transcribe_only = transcribe_only
        if not transcribe_only:
            self.translator = deepl.Translator(api_key)
            self.source_lang = source_lang
            self.target_lang = target_lang
            self.glossary_id = glossary_id
            if glossary_id:
                print(f"   📚 Glosario activado: {glossary_id}")
        else:
            print("   🎤 Modo solo transcripción (sin traducción)")
        
        # Configuración de audio
        self.sample_rate = 16000
        self.chunk_duration = 1.5  # Segundos de audio por chunk
        self.chunk_samples = int(self.sample_rate * self.chunk_duration)
        
        # Buffer de audio
        self.audio_queue = queue.Queue()
        self.is_running = False
        
        # Caché de traducciones
        self.translation_cache = {}
        self.last_transcription = ""
        
        # Modo de traducción por frases completas
        self.sentence_mode = sentence_mode
        self.sentence_buffer = ""  # Buffer para acumular texto hasta frase completa
        self.minimum_words_per_sentence = 5  # Mínimo de palabras para considerar frase completa
        if sentence_mode:
            print(f"   📝 Modo de frases completas: Activado (mín. {self.minimum_words_per_sentence} palabras)")
        
        # Configuración web display
        self.web_display = web_display
        self.web_server_url = "http://localhost:5000/subtitle"
        if web_display:
            print(f"🌐 Web Display: Activado (→ {self.web_server_url})")
        
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
            
            # Suprimir COMPLETAMENTE stderr (donde tqdm escribe)
            # Guardar stderr original
            stderr_backup = sys.stderr
            
            try:
                # Redirigir stderr a /dev/null
                sys.stderr = open(os.devnull, 'w')
                
                # Transcribir con Whisper
                result = self.model.transcribe(
                    audio_float,
                    language='en',
                    fp16=False,  # M4 funciona mejor con FP32
                    verbose=False,
                    condition_on_previous_text=True,
                    temperature=0.0
                )
            finally:
                # Restaurar stderr
                sys.stderr.close()
                sys.stderr = stderr_backup
            
            return result['text'].strip()
        
        except Exception as e:
            # Asegurarse de restaurar stderr en caso de error
            if sys.stderr != stderr_backup:
                sys.stderr.close()
                sys.stderr = stderr_backup
            print(f"⚠️  Error en transcripción: {e}", file=sys.stderr)
            return None
    
    def translate_text(self, text):
        """Traducir texto usando caché y glosario (si está configurado)."""
        if not text:
            return None
        
        # Usar caché si existe
        if text in self.translation_cache:
            return self.translation_cache[text]
        
        try:
            # Traducir con la biblioteca oficial de DeepL
            result = self.translator.translate_text(
                text,
                source_lang=self.source_lang,
                target_lang=self.target_lang,
                glossary=self.glossary_id  # Usar glosario si está configurado
            )
            translated = result.text
            self.translation_cache[text] = translated
            return translated
        except Exception as e:
            print(f"⚠️  Error en traducción: {e}", file=sys.stderr)
            return text
    
    def send_to_web(self, text):
        """Enviar subtítulo al servidor web."""
        if not self.web_display or not text:
            return
        
        try:
            data = json.dumps({'text': text}).encode('utf-8')
            req = urllib_request.Request(
                self.web_server_url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            urllib_request.urlopen(req, timeout=1)
        except (urllib_error.URLError, urllib_error.HTTPError) as e:
            # Silencioso: no mostrar error si el servidor no está disponible
            pass
        except Exception as e:
            pass
    
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
                        if self.transcribe_only:
                            # Modo solo transcripción: mostrar texto sin traducir
                            sys.stdout.write('\r' + ' ' * 150 + '\r')
                            print(f"🎤 {text}")
                            sys.stdout.flush()
                            self.last_transcription = text
                        elif self.sentence_mode:
                            # Modo frases completas: acumular hasta detectar fin de frase
                            self.sentence_buffer += " " + text if self.sentence_buffer else text
                            
                            # Detectar fin de frase: puntuación + mínimo de palabras
                            word_count = len(self.sentence_buffer.split())
                            has_punctuation = text.rstrip().endswith(('.', '!', '?'))
                            has_enough_words = word_count >= self.minimum_words_per_sentence
                            
                            if has_punctuation and has_enough_words:
                                # Traducir frase completa
                                translated = self.translate_text(self.sentence_buffer)
                                latency = time.time() - start_time
                                
                                if translated:
                                    self.send_to_web(translated)
                                    sys.stdout.write('\r' + ' ' * 150 + '\r')
                                    print(f"📝 {translated}")
                                    sys.stdout.flush()
                                
                                # Limpiar buffer
                                self.sentence_buffer = ""
                        else:
                            # Modo normal: traducir cada chunk
                            translated = self.translate_text(text)
                            latency = time.time() - start_time
                            
                            if translated:
                                self.send_to_web(translated)
                                sys.stdout.write('\r' + ' ' * 150 + '\r')
                                print(f"{translated}")
                                sys.stdout.flush()
                        
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
    parser.add_argument(
        '--web-display',
        action='store_true',
        help='Enviar traducciones a servidor web en localhost:5000'
    )
    parser.add_argument(
        '--glossary-id',
        type=str,
        default=None,
        help='ID del glosario de DeepL (opcional)'
    )
    parser.add_argument(
        '--sentence-mode',
        action='store_true',
        help='Traducir frases completas en vez de chunks de tiempo (mejor contexto, mayor latencia)'
    )
    parser.add_argument(
        '--transcribe-only',
        action='store_true',
        help='Solo transcribir sin traducir (útil para testing)'
    )
    
    args = parser.parse_args()
    
    # Obtener API key (solo si no es transcribe-only)
    api_key = args.api_key or os.getenv('DEEPL_API_KEY')
    if not args.transcribe_only and not api_key:
        print("❌ ERROR: DEEPL_API_KEY requerida para traducción")
        print("export DEEPL_API_KEY='your-key'")
        print("O usa --transcribe-only para solo transcribir")
        sys.exit(1)
    
    print("="*60)
    print("⚡ WHISPER LOCAL con CPU Optimizado - Apple M4")
    print("="*60)
    if args.transcribe_only:
        print(f"🎤 Modo: Solo transcripción (sin traducción)")
    else:
        print(f"🌍 {args.source_lang.upper()} → {args.target_lang.upper()}")
    print(f"🤖 Modelo: {args.model}")
    if not args.transcribe_only:
        print(f"💾 Caché: Activado")
        print(f"⏱️  Latencia esperada: 1-2 segundos")
    print(f"ℹ️  CPU M4 >> Docker CPU genérico")
    if not args.transcribe_only:
        if args.sentence_mode:
            print(f"📝 Modo: Frases completas (mejor contexto)")
        else:
            print(f"⚡ Modo: Chunks de tiempo (menor latencia)")
    if args.web_display:
        print(f"🌐 Web Display: http://localhost:5000")
    print("="*60 + "\n")
    
    try:
        client = LocalCoreMLClient(
            api_key=api_key,
            source_lang=args.source_lang,
            target_lang=args.target_lang,
            model_name=args.model,
            web_display=args.web_display,
            glossary_id=args.glossary_id,
            sentence_mode=args.sentence_mode,
            transcribe_only=args.transcribe_only
        )
        
        client.start()
        
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
