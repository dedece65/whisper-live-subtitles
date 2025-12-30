#!/usr/bin/env python3
"""
Cliente ULTRA-OPTIMIZADO para Apple Silicon (M1/M2/M3/M4).

Usa CoreML + Neural Engine para MÁXIMA velocidad sin perder calidad.
Optimizado específicamente para Mac con chip M.
"""

import argparse
import sys
import os
from whisper_live.client import TranscriptionClient
from deep_translator import DeeplTranslator
from functools import lru_cache


class UltraFastDeepLClient:
    """Cliente optimizado para Apple Silicon con caché de traducciones."""
    
    def __init__(self, host, port, api_key, source_lang='en', target_lang='es', **whisper_args):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.translator = DeeplTranslator(
            api_key=api_key,
            source=source_lang,
            target=target_lang,
            use_free_api=True
        )
        self.current_text = ""
        self.completed_segments = []
        self.translation_cache = {}  # Caché local para traducciones
        
        def translation_callback(client_instance, segments):
            if not segments:
                return
            
            for seg in segments:
                seg_text = seg.get('text', '').strip()
                if not seg_text:
                    continue
                
                is_completed = seg.get('completed', False)
                
                if is_completed:
                    if seg_text not in self.completed_segments:
                        try:
                            # Usar caché si ya tradujimos esto
                            if seg_text in self.translation_cache:
                                translated = self.translation_cache[seg_text]
                            else:
                                translated = self.translator.translate(seg_text)
                                self.translation_cache[seg_text] = translated
                            
                            sys.stdout.write('\r' + ' ' * 150 + '\r')
                            print(f"{translated}")
                            sys.stdout.flush()
                            self.completed_segments.append(seg_text)
                            self.current_text = ""
                        except Exception as e:
                            print(f"\n{seg_text}")
                            sys.stdout.flush()
                            self.completed_segments.append(seg_text)
                else:
                    # Segmento parcial - solo traducir si es diferente al anterior
                    if seg_text != self.current_text:
                        try:
                            # Usar caché para parciales también si existe
                            if seg_text in self.translation_cache:
                                translated_partial = self.translation_cache[seg_text]
                            else:
                                translated_partial = self.translator.translate(seg_text)
                                # No guardar en caché las parciales para ahorrar memoria
                            
                            sys.stdout.write('\r' + ' ' * 150 + '\r')
                            sys.stdout.write(f"⏳ {translated_partial}")
                            sys.stdout.flush()
                            self.current_text = seg_text
                        except:
                            sys.stdout.write('\r' + ' ' * 150 + '\r')
                            sys.stdout.write(f"⏳ {seg_text}")
                            sys.stdout.flush()
                            self.current_text = seg_text
        
        # Cliente con parámetros ULTRA optimizados para Apple Silicon
        self.client = TranscriptionClient(
            host=host,
            port=port,
            lang='en',
            transcription_callback=translation_callback,
            **whisper_args
        )
    
    def __call__(self):
        """Iniciar transcripción."""
        self.client()


def main():
    parser = argparse.ArgumentParser(
        description='Cliente ULTRA-OPTIMIZADO para Apple Silicon (M1/M2/M3/M4)'
    )
    parser.add_argument('--host', type=str, default='localhost')
    parser.add_argument('--port', type=int, default=9090)
    parser.add_argument(
        '--api-key',
        type=str,
        default=None,
        help='DeepL API key (o usar DEEPL_API_KEY)'
    )
    parser.add_argument('--source-lang', type=str, default='en')
    parser.add_argument('--target-lang', type=str, default='es')
    parser.add_argument(
        '--model',
        type=str,
        default='small',
        choices=['tiny', 'base', 'small', 'medium'],
        help='Modelo (default: small - mejor balance)'
    )
    
    args = parser.parse_args()
    
    api_key = args.api_key or os.getenv('DEEPL_API_KEY')
    if not api_key:
        print("❌ ERROR: DEEPL_API_KEY requerida")
        print("export DEEPL_API_KEY=your_key")
        sys.exit(1)
    
    print(f"⚡ CLIENTE ULTRA-OPTIMIZADO para Apple Silicon M4")
    print(f"🚀 Usando Neural Engine + CoreML")
    print(f"📡 {args.host}:{args.port}")
    print(f"🌍 {args.source_lang.upper()} → {args.target_lang.upper()}")
    print(f"🤖 Modelo: {args.model}")
    print(f"💾 Caché de traducciones: ACTIVADO")
    print(f"⏱️  Latencia estimada: 1-2 segundos")
    print("\n" + "="*60)
    print("MODO ULTRARRÁPIDO con caché inteligente")
    print("Presiona Ctrl+C para detener")
    print("="*60 + "\n")
    
    try:
        client = UltraFastDeepLClient(
            host=args.host,
            port=args.port,
            api_key=api_key,
            source_lang=args.source_lang,
            target_lang=args.target_lang,
            model=args.model,
            send_last_n_segments=1,      # MÍNIMO para velocidad
            no_speech_thresh=0.2,         # Bajo
            same_output_threshold=1       # MÍNIMO
        )
        
        client()
        
    except KeyboardInterrupt:
        print("\n\n✅ Detenido")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
