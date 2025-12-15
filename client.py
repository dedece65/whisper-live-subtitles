#!/usr/bin/env python3
"""
Cliente de Whisper Live para transcripción en tiempo real desde el micrófono.

Este script captura audio del micrófono y lo envía al servidor de whisper-live
para obtener subtítulos en tiempo real.
"""

import argparse
from whisper_live.client import TranscriptionClient


def main():
    parser = argparse.ArgumentParser(
        description='Cliente de transcripción en tiempo real con Whisper'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='localhost',
        help='Host del servidor whisper-live (default: localhost)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=9090,
        help='Puerto del servidor whisper-live (default: 9090)'
    )
    parser.add_argument(
        '--lang',
        type=str,
        default='en',
        help='Idioma de transcripción (default: en)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='small',
        choices=['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3'],
        help='Modelo de Whisper a usar (default: small)'
    )
    parser.add_argument(
        '--task',
        type=str,
        default='transcribe',
        choices=['transcribe', 'translate'],
        help='Tarea: transcribe o translate (traducir a inglés) (default: transcribe)'
    )
    
    args = parser.parse_args()
    
    print(f"🎙️  Iniciando cliente de transcripción...")
    print(f"📡 Conectando a {args.host}:{args.port}")
    print(f"🌍 Idioma: {args.lang}")
    print(f"🤖 Modelo: {args.model}")
    print(f"⚙️  Tarea: {args.task}")
    print("\n" + "="*60)
    print("Habla al micrófono para ver los subtítulos en tiempo real")
    print("Presiona Ctrl+C para detener")
    print("="*60 + "\n")
    
    try:
        # Crear cliente de transcripción
        client = TranscriptionClient(
            host=args.host,
            port=args.port,
            lang=args.lang,
            model=args.model,
            translate=(args.task == 'translate')
        )
        
        # Iniciar transcripción desde el micrófono
        # Esto bloqueará hasta que se presione Ctrl+C
        client()
        
    except KeyboardInterrupt:
        print("\n\n✅ Transcripción detenida por el usuario")
    except ConnectionRefusedError:
        print(f"\n❌ Error: No se pudo conectar al servidor en {args.host}:{args.port}")
        print("   Asegúrate de que el servidor Docker esté ejecutándose:")
        print("   docker run -p 9090:9090 whisper-live-server")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        raise


if __name__ == "__main__":
    main()
