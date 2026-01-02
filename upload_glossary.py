import deepl
import os
import csv

# Pon tu API Key aquí o asegúrate de tenerla en el entorno
API_KEY = os.getenv('DEEPL_API_KEY') 
CSV_FILE = 'glosario_deepl.csv' # Asegúrate de que este archivo está en la misma carpeta

def create_glossary():
    if not API_KEY:
        print("❌ Error: No se detecta DEEPL_API_KEY")
        return

    translator = deepl.Translator(API_KEY)
    
    entries = {}
    try:
        with open(CSV_FILE, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader) # Saltar cabecera si existe
            for row in reader:
                if len(row) >= 2:
                    # Asumiendo Columna 0 = Inglés, Columna 1 = Español
                    source = row[0].strip()
                    target = row[1].strip()
                    entries[source] = target
                    
        print(f"📖 Leídos {len(entries)} términos del CSV.")
        
        # Crear glosario
        glossary = translator.create_glossary(
            "Ingeniería Sonido",
            source_lang="en",
            target_lang="es",
            entries=entries
        )
        
        print("\n✅ ¡Glosario creado con éxito!")
        print(f"🆔 NUEVO ID: {glossary.glossary_id}")
        print("👉 Copia este ID y úsalo en el comando del cliente.")
        
    except FileNotFoundError:
        print(f"❌ No encuentro el archivo {CSV_FILE}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    create_glossary()