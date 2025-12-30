# 🎙️ Whisper Live - Sistema de Transcripción y Subtítulos en Tiempo Real

Sistema completo de transcripción automática con traducción en tiempo real usando OpenAI Whisper + DeepL, optimizado para Apple Silicon (M4).

## 📋 Índice

- [Requisitos](#-requisitos)
- [Componentes del Sistema](#-componentes-del-sistema)
- [Configuración Inicial](#-configuración-inicial)
- [Instalación](#-instalación)
- [Uso del Sistema](#-uso-del-sistema)
- [Configuración Avanzada](#-configuración-avanzada)
- [Solución de Problemas](#-solución-de-problemas)

## 🎯 Requisitos

### Hardware
- **macOS con Apple Silicon** (M1/M2/M3/M4) - recomendado
- **8GB+ RAM** (16GB recomendado)
- **Micrófono** funcional

### Software
- **Python 3.8+**
- **macOS 12.3+** (para optimizaciones Metal)

## 🧩 Componentes del Sistema

El sistema consta de dos componentes principales que trabajan juntos:

### 1. `client_m4_optimized.py` - Cliente de Transcripción
- Captura audio del micrófono en tiempo real
- Transcribe usando Whisper (optimizado para M4)
- Traduce con DeepL (opcional)
- Filtra alucinaciones y ruido
- Envía subtítulos al servidor web

### 2. `subtitle_server.py` - Servidor de Visualización
- Servidor web Flask con Socket.IO
- Muestra subtítulos en tiempo real en navegador
- Optimizado para proyección en pantalla grande
- Mantiene historial de últimos 3 subtítulos

## 🔧 Configuración Inicial

### 1. Obtener API Key de DeepL (Gratis)

> **Nota**: DeepL es opcional pero mejora significativamente la calidad de traducción.

1. Ir a https://www.deepl.com/pro-api
2. Crear cuenta gratuita (sin tarjeta de crédito)
3. Plan gratuito: **500,000 caracteres/mes**
4. Copiar tu API key desde Account → API Keys

### 2. Configurar Variable de Entorno

```bash
# Añadir a ~/.zshrc para hacerlo permanente
export DEEPL_API_KEY="tu-api-key-aquí"

# O establecer temporalmente en la sesión actual
export DEEPL_API_KEY="tu-api-key-aquí"
```

## 📦 Instalación

### Instalación Automática (Recomendado)

```bash
# 1. Clonar o navegar al proyecto
cd /ruta/al/proyecto

# 2. Ejecutar script de instalación
./install_local.sh
```

El script instalará:
- ✅ Entorno virtual `venv-local`
- ✅ PyTorch optimizado para Apple Silicon
- ✅ Whisper y faster-whisper
- ✅ DeepL y deep-translator
- ✅ Flask, Flask-SocketIO, Flask-CORS
- ✅ Dependencias de audio (sounddevice, numpy)

### Instalación Manual

Si prefieres instalar manualmente:

```bash
# 1. Crear entorno virtual
python3 -m venv venv-local

# 2. Activar entorno
source venv-local/bin/activate

# 3. Actualizar pip
pip install --upgrade pip setuptools wheel

# 4. Instalar dependencias
pip install -r requirements-local.txt

# 5. Instalar dependencias del servidor
pip install flask flask-socketio flask-cors python-socketio
```

### Verificar Instalación

```bash
source venv-local/bin/activate
python -c "import whisper; import deepl; import flask; print('✅ Todo instalado correctamente')"
```

## 🚀 Uso del Sistema

### Flujo Típico de Uso

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────┐
│  Micrófono      │────────▶│  client_m4_      │────────▶│  subtitle_  │
│  (Audio input)  │         │  optimized.py    │  HTTP   │  server.py  │
└─────────────────┘         │                  │         │             │
                            │ • Whisper        │         │ • Flask     │
                            │ • DeepL          │         │ • WebSocket │
                            │ • Noise Filter   │         │             │
                            └──────────────────┘         └──────┬──────┘
                                                                 │
                                                                 ▼
                                                         ┌───────────────┐
                                                         │   Navegador   │
                                                         │ localhost:5000│
                                                         └───────────────┘
```

### Paso 1: Iniciar el Servidor de Subtítulos

En una terminal:

```bash
# Activar entorno virtual
source venv-local/bin/activate

# Iniciar servidor
python subtitle_server.py
```

Verás:

```
============================================================
🎬 SERVIDOR DE SUBTÍTULOS EN TIEMPO REAL
============================================================
🌐 URL: http://localhost:5000
📡 WebSocket: Activado
📝 Historial: Últimos 3 subtítulos
============================================================

✨ Servidor iniciado. Abre http://localhost:5000 en tu navegador.
   Para pantalla completa, presiona F11
```

### Paso 2: Abrir Interfaz Web

Abre tu navegador en: **http://localhost:5000**

- Presiona **F11** para pantalla completa
- Los subtítulos aparecerán automáticamente al llegar del cliente

### Paso 3: Iniciar Cliente de Transcripción

En **otra terminal** (manteniendo el servidor corriendo):

```bash
# Activar entorno virtual
source venv-local/bin/activate

# Configurar API key (si no está en ~/.zshrc)
export DEEPL_API_KEY="tu-api-key"

# Ejecutar cliente con visualización web
python client_m4_optimized.py --web-display
```

#### Opciones del Cliente

```bash
# Básico (inglés → español, modelo small)
python client_m4_optimized.py --web-display

# Con modelo medium (mejor precisión, más lento)
python client_m4_optimized.py --web-display --model medium

# Con modelo tiny (máxima velocidad, menor precisión)
python client_m4_optimized.py --web-display --model tiny

# Con glosario personalizado de DeepL
python client_m4_optimized.py --web-display --glossary-id "tu-glossary-id"

# Solo transcripción, sin traducción (sin DeepL)
python client_m4_optimized.py --web-display
# (No configurar DEEPL_API_KEY)

# Con API key por argumento
python client_m4_optimized.py --web-display --api-key "tu-api-key"
```

### Paso 4: Hablar al Micrófono

- El cliente transcribirá y traducirá automáticamente
- Los subtítulos aparecerán en la página web
- Los últimos 3 subtítulos se mantienen visibles

### Detener el Sistema

```bash
# En cada terminal, presionar:
Ctrl + C
```

## 🎨 Glosarios de DeepL (Opcional)

Los glosarios permiten traducciones consistentes de términos técnicos.

### 1. Crear Glosario desde CSV

```bash
# 1. Editar glosario_bob.csv con tus términos
# Formato: término_origen,término_destino,idioma_origen,idioma_destino

# 2. Subir glosario a DeepL
source venv-local/bin/activate
export DEEPL_API_KEY="tu-api-key"
python upload_glossary.py
```

El script mostrará el `glossary_id` generado.

### 2. Listar Glosarios Existentes

```bash
python list_glossaries.py
```

### 3. Usar Glosario en Cliente

```bash
python client_m4_optimized.py --web-display --glossary-id "abc123-def456"
```

> **Importante**: El glosario debe coincidir con el par de idiomas (EN→ES).

## ⚙️ Configuración Avanzada

### Modelos de Whisper Disponibles

| Modelo | Tamaño | Velocidad M4 | Calidad | RAM | Uso Recomendado |
|--------|--------|--------------|---------|-----|-----------------|
| `tiny` | 39 MB | ⚡⚡⚡ | ⭐⭐ | 500 MB | Máxima velocidad |
| `base` | 74 MB | ⚡⚡⚡ | ⭐⭐⭐ | 700 MB | Balance rápido |
| `small` | 466 MB | ⚡⚡ | ⭐⭐⭐⭐ | 1 GB | **Recomendado** |
| `medium` | 1.5 GB | ⚡ | ⭐⭐⭐⭐⭐ | 2 GB | Máxima precisión |
| `large` | 2.9 GB | ⚡ | ⭐⭐⭐⭐⭐ | 4 GB | Profesional |

### Ajustar Umbral de Ruido

Editar `client_m4_optimized.py`, línea ~59:

```python
# Valores más altos = menos sensible (ignora más ruido)
# Valores más bajos = más sensible (captura todo)
self.amplitude_threshold = 0.01  # Default: 0.01
```

### Ajustar Duración de Buffer

Editar `client_m4_optimized.py`, línea ~56:

```python
# Tiempo máximo antes de forzar traducción
self.max_buffer_duration = 7.0  # Segundos
```

### Personalizar Servidor Web

Editar `subtitle_server.py`:

```python
# Línea ~50: Cambiar número de subtítulos en historial
if len(subtitle_history) > 3:  # Cambiar 3 por el número deseado
```

```python
# Línea ~90: Cambiar puerto
socketio.run(app, host='0.0.0.0', port=5000, debug=False)
# Cambiar 5000 por otro puerto si es necesario
```

### Estilos de Subtítulos

Editar `templates/subtitles.html` para personalizar:

- Tamaños de fuente (líneas 97, 98, 169-175)
- Colores y transparencias (líneas 78, 101)
- Animaciones (líneas 107, 111, 114-132)

## 🔍 Solución de Problemas

### El servidor no inicia

**Error**: `Address already in use`

**Solución**:
```bash
# Ver qué proceso usa el puerto 5000
lsof -i :5000

# Matar proceso si es necesario
kill -9 <PID>

# O cambiar puerto en subtitle_server.py
```

### Cliente no conecta al servidor

**Error**: `Failed to send subtitle`

**Solución**:
1. Verifica que el servidor esté corriendo
2. Verifica la URL en `client_m4_optimized.py` línea ~47:
   ```python
   self.web_server_url = "http://localhost:5000/subtitle"
   ```
3. Si el servidor está en otro puerto, actualiza la URL

### DeepL falla con error de glosario

**Error**: `Glossary not found` o `Invalid glossary ID`

**Solución**:
1. Verifica que el glosario existe:
   ```bash
   python list_glossaries.py
   ```
2. Asegúrate que el ID no tenga sufijo `:fx` (el cliente lo limpia automáticamente)
3. Verifica que el glosario sea para el par EN→ES

### Audio no se captura

**Solución**:
1. Otorgar permisos de micrófono:
   - System Settings → Privacy & Security → Microphone
   - Habilitar Terminal o tu app
2. Verificar dispositivo de audio:
   ```python
   import sounddevice as sd
   print(sd.query_devices())
   ```
3. Configurar dispositivo de entrada correcto en Preferencias del Sistema

### "Thank you" o alucinaciones repetidas

El cliente ya incluye filtros anti-alucinación. Si persiste:

1. Aumentar umbral de ruido (ver Configuración Avanzada)
2. Usar modelo más grande: `--model medium`
3. Verificar que el micrófono esté en un ambiente sin ecos

### Latencia alta

**Soluciones**:
1. Usar modelo más pequeño: `--model tiny` o `--model base`
2. Cerrar aplicaciones pesadas (Chrome, etc.)
3. Conectar Mac a corriente (máximo rendimiento)
4. Reducir `max_buffer_duration` en el código

### Módulos no encontrados

**Error**: `No module named 'whisper'` o similar

**Solución**:
```bash
# Asegúrate de activar el entorno virtual
source venv-local/bin/activate

# Reinstalar dependencias
pip install -r requirements-local.txt
```

### Primera ejecución muy lenta

Es normal. Whisper descarga el modelo la primera vez (~500MB para `small`).

Los modelos se guardan en: `~/.cache/whisper/`

## 📊 Rendimiento en Apple M4

Latencia medida en MacBook Pro M4 (16GB RAM):

| Configuración | Primera Palabra | Frase Completa | CPU % | RAM |
|--------------|-----------------|----------------|-------|-----|
| tiny | 0.4s | 0.8s | 150% | 500MB |
| base | 0.6s | 1.0s | 180% | 700MB |
| **small (recomendado)** | **0.8s** | **1.5s** | **220%** | **1GB** |
| medium | 1.2s | 2.5s | 280% | 2GB |

**Mejora vs Docker**: 2-3x más rápido

## 💡 Consejos y Mejores Prácticas

### Para Presentaciones
1. Iniciar servidor y abrir navegador en modo pantalla completa (F11)
2. Probar audio antes de la presentación
3. Usar modelo `small` para balance óptimo
4. Conectar Mac a corriente

### Para Desarrollo
1. Usar `--model tiny` para pruebas rápidas
2. Monitorear salida del cliente para debugging
3. Revisar consola del navegador (F12) para errores de WebSocket

### Para Máxima Calidad
1. Usar `--model medium` o `--model large`
2. Crear glosario personalizado para términos técnicos
3. Ambiente silencioso sin eco

### Para Máxima Velocidad
1. Usar `--model tiny`
2. Reducir `max_buffer_duration`
3. Cerrar aplicaciones innecesarias

## 📁 Estructura del Proyecto

```
whisper_live_docker/
├── client_m4_optimized.py    # Cliente principal optimizado M4
├── subtitle_server.py         # Servidor web de subtítulos
├── requirements-local.txt     # Dependencias Python
├── install_local.sh          # Script de instalación
├── upload_glossary.py        # Subir glosarios a DeepL
├── list_glossaries.py        # Listar glosarios disponibles
├── glosario_bob.csv          # Ejemplo de glosario
├── templates/
│   └── subtitles.html        # Interfaz web de subtítulos
├── docs/                     # Documentación adicional
│   ├── DEEPL_SETUP.md       # Guía DeepL
│   ├── LOCAL_SETUP.md       # Setup local detallado
│   └── M4_OPTIMIZATIONS.md  # Optimizaciones M4
├── legacy/                   # Versiones antiguas
└── venv-local/              # Entorno virtual (creado por install)
```

## 🔄 Compatibilidad con Docker

Este proyecto mantiene compatibilidad con Docker para otros sistemas. Ver documentación en `docker/` para:
- Ejecutar servidor Whisper en Docker
- Usar GPU NVIDIA
- Deployar en servidores Linux

## 🌍 Idiomas Soportados

**Transcripción (Whisper)**: 99+ idiomas
- Inglés (EN), Español (ES), Francés (FR), Alemán (DE), Italiano (IT), Portugués (PT), etc.

**Traducción (DeepL)**:
- **Origen**: EN, ES, FR, DE, IT, PT, NL, PL, RU, JA, ZH
- **Destino**: ES, EN-US, EN-GB, FR, DE, IT, PT-PT, PT-BR, NL, PL, RU, JA, ZH

## 📄 Licencia

Este proyecto utiliza:
- [OpenAI Whisper](https://github.com/openai/whisper) - MIT License
- [Faster Whisper](https://github.com/guillaumekln/faster-whisper) - MIT License
- [DeepL API](https://www.deepl.com/docs-api) - API Terms
- [Flask](https://flask.palletsprojects.com/) - BSD License

## 🙏 Créditos

- OpenAI Whisper - Modelo de transcripción
- DeepL - API de traducción
- Faster Whisper - Backend optimizado
- Flask + Socket.IO - Framework web

---

**Estado**: ✅ Sistema completo y funcional

**Mantenido por**: dedece

**Última actualización**: 2025-12-30
