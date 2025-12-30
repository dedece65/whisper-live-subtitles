#!/usr/bin/env python3
"""
Cliente de Whisper Live con traducción DeepL de ALTA CALIDAD para subtítulos en directo.

Optimizado para calidad + velocidad usando DeepL API (gratis hasta 500k chars/mes).
Requiere API key de DeepL: https://www.deepl.com/pro-api
"""

import argparse
import sys
import os
from whisper_live.client import TranscriptionClient
from deep_translator import DeeplTranslator


class DeepLTranslatingClient:
    """Cliente con traducción DeepL de alta calidad."""
    
    def __init__(self, host, port, api_key, source_lang='en', target_lang='es', **whisper_args):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.translator = DeeplTranslator(
            api_key=api_key,
            source=source_lang,
            target=target_lang,
            use_free_api=True  # Usar API gratuita
        )
        self.current_text = ""
        self.completed_segments = []
        
        def translation_callback(client_instance, segments):
            if not segments:
                return
            
            # Procesar todos los segmentos
            for seg in segments:
                seg_text = seg.get('text', '').strip()
                if not seg_text:
                    continue
                
                is_completed = seg.get('completed', False)
                
                if is_completed:
                    # Segmento completo - traducir y fijar
                    if seg_text not in self.completed_segments:
                        try:
                            translated = self.translator.translate(seg_text)
                            # Limpiar y mostrar traducción final
                            sys.stdout.write('\r' + ' ' * 150 + '\r')
                            print(f"{translated}")
                            sys.stdout.flush()
                            self.completed_segments.append(seg_text)
                            self.current_text = ""
                        except Exception as e:
                            # Fallback si falla DeepL
                            print(f"\n{seg_text}")
                            sys.stdout.flush()
                            self.completed_segments.append(seg_text)
                else:
                    # Segmento parcial - traducir también
                    if seg_text != self.current_text:
                        try:
                            translated_partial = self.translator.translate(seg_text)
                            sys.stdout.write('\r' + ' ' * 150 + '\r')
                            sys.stdout.write(f"⏳ {translated_partial}")
                            sys.stdout.flush()
                            self.current_text = seg_text
                        except:
                            # Fallback
                            sys.stdout.write('\r' + ' ' * 150 + '\r')
                            sys.stdout.write(f"⏳ {seg_text}")
                            sys.stdout.flush()
                            self.current_text = seg_text
        
        # Crear cliente con modelo SMALL (buena calidad)
        self.client = TranscriptionClient(
            host=host,
            port=port,
            lang='en',  # Whisper siempre en inglés
            transcription_callback=translation_callback,
            **whisper_args
        )
    
    def __call__(self):
        """Iniciar transcripción."""
        self.client()


def main():
    parser = argparse.ArgumentParser(
        description='Transcripción con DEEPL (alta calidad) para subtítulos en directo'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='localhost',
        help='Host del servidor (default: localhost)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=9090,
        help='Puerto del servidor (default: 9090)'
    )
    parser.add_argument(
        '--api-key',
        type=str,
        default=None,
        help='DeepL API key (o usar variable DEEPL_API_KEY)'
    )
    parser.add_argument(
        '--source-lang',
        type=str,
        default='en',
        choices=['en', 'es', 'fr', 'de', 'it', 'pt', 'nl', 'pl', 'ru', 'ja', 'zh'],
        help='Idioma de origen (default: en = inglés)'
    )
    parser.add_argument(
        '--target-lang',
        type=str,
        default='es',
        choices=['es', 'en', 'fr', 'de', 'it', 'pt', 'nl', 'pl', 'ru', 'ja', 'zh'],
        help='Idioma destino (default: es = español)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='small',
        choices=['tiny', 'base', 'small', 'medium', 'large'],
        help='Modelo Whisper (default: small - buen balance)'
    )
    
    args = parser.parse_args()
    
    # Obtener API key
    api_key = args.api_key or os.getenv('DEEPL_API_KEY')
    
    if not api_key:
        print("❌ ERROR: DeepL API key requerida")
        print("\n📝 Opciones:")
        print("1. Pasar con --api-key YOUR_KEY")
        print("2. Establecer variable: export DEEPL_API_KEY=your_key")
        print("\n🔑 Obtén tu API key GRATIS (500k chars/mes):")
        print("   https://www.deepl.com/pro-api")
        print("   -> Sign up for free -> API Key")
        sys.exit(1)
    
    print(f"⚡ TRANSCRIPCIÓN con DeepL (ALTA CALIDAD)")
    print(f"📡 Servidor: {args.host}:{args.port}")
    print(f"� {args.source_lang.upper()} → {args.target_lang.upper()}")
    print(f"🤖 Modelo: {args.model}")
    print(f"✨ Traductor: DeepL (mejor calidad)")
    print(f"⏱️  Latencia: 2-4 segundos")
    print("\n" + "="*60)
    print("Verás texto temporal (⏳) que se actualiza")
    print("Cuando esté completo, se fijará la traducción final")
    print("Presiona Ctrl+C para detener")
    print("="*60 + "\n")
    
    try:
        client = DeepLTranslatingClient(
            host=args.host,
            port=args.port,
            api_key=api_key,
            source_lang=args.source_lang,
            target_lang=args.target_lang,
            model=args.model,
            send_last_n_segments=2,      # Balance velocidad/contexto
            no_speech_thresh=0.25,       # Bajo para detectar voz fácilmente
            same_output_threshold=2      # Actualiza rápido
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
