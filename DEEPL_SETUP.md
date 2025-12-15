# DeepL API Setup

## 🆓 Obtener API Key GRATIS

1. **Ir a DeepL**: https://www.deepl.com/pro-api
2. **Sign up for free** (crear cuenta gratuita)
3. **Ir a Account** → **API Keys**
4. **Copiar tu API key**

### Plan Gratuito
- ✅ **500,000 caracteres/mes GRATIS**
- ✅ Suficiente para ~8-10 horas de transcripción continua
- ✅ Mejor calidad que Google Translate
- ✅ Sin tarjeta de crédito requerida

## 🚀 Uso

### Opción 1: Variable de entorno (recomendado)

```bash
# Establecer la API key
export DEEPL_API_KEY="tu-api-key-aqui"

# Ejecutar cliente
source venv-client/bin/activate
python client_deepl.py
```

### Opción 2: Pasar por argumento

```bash
source venv-client/bin/activate
python client_deepl.py --api-key "tu-api-key-aqui"
```

## 📋 Ejemplos

```bash
# Inglés → Español (default, modelo small)
python client_deepl.py

# Español → Inglés
python client_deepl.py --source-lang ES --target-lang EN-US

# Con modelo medium (más preciso)
python client_deepl.py --model medium

# Francés → Español
python client_deepl.py --source-lang FR --target-lang ES
```

## 🌍 Idiomas Soportados

**Origen**: EN, ES, FR, DE, IT, PT, NL, PL, RU, JA, ZH
**Destino**: ES, EN-US, EN-GB, FR, DE, IT, PT-PT, PT-BR, NL, PL, RU, JA, ZH

## 💡 Tips

1. **Modelo small** = Buen balance velocidad/calidad (default)
2. **Modelo medium** = Mejor precisión, ~50% más lento
3. **Latencia típica**: 2-4 segundos con small
4. **Consumo**: ~150 caracteres por segundo de audio transcrito

## ⚠️ Límites

Si superas 500k caracteres/mes:
- DeepL ofrece planes pagos desde $5.99/mes (1M caracteres)
- O puedes volver a usar `client_live.py` con Google Translate (ilimitado gratis)
