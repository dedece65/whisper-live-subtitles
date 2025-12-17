#!/usr/bin/env python3
"""
Script para listar glosarios disponibles en DeepL.
Usa este script para obtener el ID de tu glosario.
"""
import deepl
import os
import sys

def list_glossaries():
    """Lista todos los glosarios disponibles en tu cuenta de DeepL."""
    # Obtener API key
    api_key = os.getenv('DEEPL_API_KEY')
    if not api_key:
        print("❌ ERROR: DEEPL_API_KEY no está configurada")
        print("Ejecuta: export DEEPL_API_KEY='tu-api-key'")
        sys.exit(1)
    
    print("=" * 60)
    print("📚 GLOSARIOS DISPONIBLES EN DEEPL")
    print("=" * 60)
    print()
    
    try:
        translator = deepl.Translator(api_key)
        glossaries = translator.list_glossaries()
        
        if not glossaries:
            print("⚠️  No tienes glosarios creados aún.")
            print()
            print("Para crear un glosario:")
            print("1. Ve a https://www.deepl.com/pro-account/glossary")
            print("2. Crea un nuevo glosario")
            print("3. Vuelve a ejecutar este script")
            return
        
        for i, glossary in enumerate(glossaries, 1):
            print(f"Glosario #{i}")
            print(f"  Nombre: {glossary.name}")
            print(f"  ID: {glossary.glossary_id}")
            print(f"  Idiomas: {glossary.source_lang} → {glossary.target_lang}")
            print(f"  Entradas: {glossary.entry_count}")
            print()
            print("  Para usar este glosario, ejecuta:")
            print(f"  python client_local_coreml.py --glossary-id {glossary.glossary_id}")
            print("-" * 60)
            print()
    
    except Exception as e:
        print(f"❌ Error al listar glosarios: {e}")
        sys.exit(1)

if __name__ == "__main__":
    list_glossaries()
