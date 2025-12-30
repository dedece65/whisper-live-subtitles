# 📚 Resumen de Archivos Legacy y Documentación

Este documento explica los archivos históricos del proyecto y cómo evolucionó el sistema hasta la versión actual.

## 📋 Índice

- [Resumen Ejecutivo](#-resumen-ejecutivo)
- [Archivos Legacy](#-archivos-legacy)
- [Evolución del Sistema](#-evolución-del-sistema)
- [Documentación Histórica](#-documentación-histórica)
- [Comparativa: Legacy vs Actual](#-comparativa-legacy-vs-actual)
- [¿Cuándo Usar Qué?](#-cuándo-usar-qué)

## 🎯 Resumen Ejecutivo

El proyecto evolucionó desde un sistema basado en **Docker + whisper-live** hasta una solución **local optimizada para Apple M4**. Los archivos en `legacy/` representan iteraciones previas del cliente que conectaban a un servidor Whisper en Docker.

### Versión Actual (Recomendada)
- **Cliente**: `client_m4_optimized.py` - Whisper local con faster-whisper
- **Servidor**: `subtitle_server.py` - Flask + WebSocket
- **Arquitectura**: Standalone (no requiere Docker)

### Versión Legacy (Archivada)
- **Clientes**: `legacy/client_*.py` - Conectan a servidor Docker
- **Servidor**: `legacy/run_server.py` - whisper-live en Docker
- **Arquitectura**: Cliente-Servidor (requiere Docker)

## 📂 Archivos Legacy

### 1. `legacy/transcriptions.py`

**Propósito**: Cliente básico de transcripción sin traducción.

**Características**:
- Conexión a servidor whisper-live en Docker
- Solo transcripción (sin traducción)
- Basado en `whisper_live.client.TranscriptionClient`
- Opciones configurables de modelo y parámetros

**Opciones principales**:
```bash
--host localhost      # Servidor Docker
--port 9090          # Puerto WebSocket
--lang en            # Idioma de transcripción
--model small        # Modelo Whisper
--task transcribe    # O 'translate' para traducir a inglés
```

**Ejemplo de uso**:
```bash
# Conectar a Docker y transcribir
python legacy/transcriptions.py --lang en --model small
```

**Estado**: ⚠️ Obsoleto - Reemplazado por `client_m4_optimized.py`

---

### 2. `legacy/client_deepl.py`

**Propósito**: Cliente con traducción DeepL de alta calidad.

**Características**:
- ✅ Transcripción vía servidor Docker
- ✅ Traducción con DeepL API
- ✅ Mostrar traducciones parciales (⏳) y finales
- ✅ Fallback a texto original si DeepL falla

**Mejoras sobre `transcriptions.py`**:
- Añade traducción de alta calidad con DeepL
- Muestra estado de traducción en tiempo real
- Maneja segmentos completos vs parciales

**Opciones principales**:
```bash
--api-key YOUR_KEY    # DeepL API key
--source-lang en      # Idioma origen
--target-lang es      # Idioma destino
--model small         # Modelo Whisper
```

**Ejemplo de uso**:
```bash
export DEEPL_API_KEY="tu-api-key"
python legacy/client_deepl.py --source-lang en --target-lang es
```

**Latencia**: 2-4 segundos

**Estado**: ⚠️ Obsoleto - Reemplazado por `client_m4_optimized.py`

**Limitaciones**:
- Requiere servidor Docker corriendo
- No aprovecha Neural Engine del M4
- Sin filtro anti-alucinaciones
- Sin noise gate

---

### 3. `legacy/client_m4.py`

**Propósito**: Cliente optimizado para Apple Silicon con caché de traducciones.

**Características**:
- ✅ Todo lo de `client_deepl.py`
- ✅ **Caché de traducciones** (50-70% más rápido en repeticiones)
- ✅ **Parámetros ultra-agresivos** para mínima latencia
- ✅ Preparado para CoreML (aunque aún usa Docker)

**Mejoras sobre `client_deepl.py`**:
1. **Caché inteligente**: Guarda traducciones en memoria
2. **Parámetros optimizados**:
   - `send_last_n_segments=1` (mínimo para velocidad)
   - `no_speech_thresh=0.2` (bajo)
   - `same_output_threshold=1` (mínimo)

**Ejemplo de uso**:
```bash
export DEEPL_API_KEY="tu-api-key"
python legacy/client_m4.py --model small
```

**Latencia**: 1-2 segundos (mejor que `client_deepl.py`)

**Estado**: ⚠️ Obsoleto - Reemplazado por `client_m4_optimized.py`

**Limitaciones**:
- Todavía requiere servidor Docker
- No usa faster-whisper local
- No usa el Neural Engine directamente

---

### 4. `legacy/run_server.py`

**Propósito**: Script para iniciar servidor whisper-live en Docker.

**Características**:
- Inicializa `TranscriptionServer` de whisper-live
- Soporta múltiples backends:
  - `faster_whisper` (default)
  - `tensorrt` (GPU NVIDIA)
  - `openvino` (Intel)
- Configuración de puerto, modelo, threads

**Opciones principales**:
```bash
--port 9090                    # Puerto WebSocket
--backend faster_whisper       # Backend a usar
--single_model                 # Compartir modelo entre clientes
--omp_num_threads 1           # Threads OpenMP
```

**Ejemplo de uso**:
```bash
# Dentro de Docker
python legacy/run_server.py --port 9090 --backend faster_whisper
```

**Estado**: ⚠️ Obsoleto - Ya no se usa servidor Docker para Whisper

**Nota**: Este script se ejecutaba **dentro del contenedor Docker**, no en el host.

---

## 🔄 Evolución del Sistema

### Fase 1: Docker Básico (Obsoleta)
```
┌─────────────┐    WebSocket    ┌──────────────────┐
│ transcriptions│─────────────────▶│ Docker Container │
│ .py          │                  │ whisper-live     │
└─────────────┘                  └──────────────────┘
```

**Características**:
- Solo transcripción
- Sin traducción
- Latencia: 3-5s

---

### Fase 2: Docker + DeepL (Obsoleta)
```
┌──────────────┐   WebSocket   ┌──────────────────┐
│ client_deepl │────────────────▶│ Docker Container │
│ .py          │                 │ whisper-live     │
│              │                 └──────────────────┘
│ + DeepL API  │
└──────────────┘
```

**Mejoras**:
- ✅ Traducción de alta calidad con DeepL
- ✅ Mostrar traducciones parciales
- Latencia: 2-4s

---

### Fase 3: Docker + DeepL + Caché M4 (Obsoleta)
```
┌──────────────┐   WebSocket   ┌──────────────────┐
│ client_m4.py │────────────────▶│ Docker Container │
│              │                 │ whisper-live     │
│ + DeepL API  │                 └──────────────────┘
│ + Cache      │
└──────────────┘
```

**Mejoras**:
- ✅ Caché de traducciones
- ✅ Parámetros optimizados
- Latencia: 1-2s

**Limitación**: Todavía usa Docker (no aprovecha M4 directamente)

---

### Fase 4: Local + M4 Optimizado (ACTUAL) ✅
```
┌──────────────────┐        HTTP         ┌──────────────┐
│ client_m4_       │─────────────────────▶│ subtitle_    │
│ optimized.py     │                      │ server.py    │
│                  │                      │ (Flask)      │
│ • Faster-Whisper │                      └──────────────┘
│   (local int8)   │                               │
│ • DeepL API      │                               ▼
│ • Noise Gate     │                      ┌──────────────┐
│ • Anti-halluc.   │                      │  Navegador   │
│ • VAD            │                      │ (WebSocket)  │
└──────────────────┘                      └──────────────┘
```

**Ventajas**:
- ✅ Sin Docker (proceso local)
- ✅ Faster-whisper con int8 (2-3x más rápido)
- ✅ Aprovecha CPU M4 optimizado
- ✅ Noise Gate (evita procesar silencio)
- ✅ Filtros anti-alucinación ("Thank you", etc.)
- ✅ VAD (Voice Activity Detection)
- ✅ Servidor web visual con Flask
- ✅ WebSocket para actualizaciones en tiempo real
- Latencia: 0.8-1.5s (con modelo small)

---

## 📖 Documentación Histórica

### `docs/M4_OPTIMIZATIONS.md`

**Contenido**: Documenta el desarrollo de `client_m4.py` (legacy).

**Puntos clave**:
- Explicación de caché de traducciones
- Comparativa de latencias entre versiones
- Recomendaciones para usar CoreML local (que luego se implementó)

**Estado**: ⚠️ Parcialmente obsoleto
- La idea de CoreML local se implementó en `client_m4_optimized.py`
- Los benchmarks son del cliente legacy (que usaba Docker)

**Relevancia actual**: Contexto histórico del desarrollo

---

### `docs/README_SUBTITLES.md`

**Contenido**: Documenta el sistema de subtítulos web (`subtitle_server.py`).

**Puntos clave**:
- Cómo funciona el servidor Flask + WebSocket
- Características visuales de la interfaz
- Workflow completo con cliente y servidor

**Estado**: ✅ VIGENTE
- El servidor `subtitle_server.py` sigue siendo el mismo
- La documentación es precisa y actual

**Referencia**: Este documento se integró en el [README.md](file:///Users/dedece/dev/whisper_live_docker/README.md) principal

---

### `docs/DEEPL_SETUP.md`

**Contenido**: Guía para configurar DeepL API.

**Puntos clave**:
- Cómo obtener API key gratis
- Ejemplos de uso con clientes legacy
- Idiomas soportados

**Estado**: ✅ VIGENTE
- La información sigue siendo válida
- Se integró en el README principal

---

### `docs/LOCAL_SETUP.md`

**Contenido**: Guía detallada de setup local con CoreML para M4.

**Puntos clave**:
- Instalación de faster-whisper local
- Benchmarks en M4
- Optimizaciones aplicadas
- Comparativa Docker vs Local

**Estado**: ✅ VIGENTE
- Documenta la instalación que usa `client_m4_optimized.py`
- Los benchmarks son precisos
- Se integró en el README principal

---

## 📊 Comparativa: Legacy vs Actual

| Característica | Legacy (Docker) | Actual (Local) |
|----------------|-----------------|----------------|
| **Arquitectura** | Cliente → Docker Server | Cliente standalone + Web Server |
| **Whisper** | whisper-live en Docker | faster-whisper local (int8) |
| **Hardware** | CPU genérico Docker | CPU M4 optimizado |
| **Latencia** | 1-4s | 0.8-1.5s |
| **Memoria** | 2GB+ (Docker) | ~1GB (proceso local) |
| **Setup** | Docker + venv | Solo venv |
| **Portabilidad** | ✅ Cualquier OS con Docker | ⚠️ Solo macOS Apple Silicon |
| **Traducción** | DeepL API | DeepL API |
| **Caché traducciones** | Solo `client_m4.py` | ✅ |
| **Noise Gate** | ❌ | ✅ |
| **Anti-alucinación** | ❌ | ✅ |
| **VAD** | ❌ | ✅ |
| **Visualización web** | ❌ | ✅ |
| **Glosarios DeepL** | ❌ | ✅ |

## 🎯 ¿Cuándo Usar Qué?

### Usa la Versión ACTUAL (`client_m4_optimized.py` + `subtitle_server.py`)

✅ **Si tienes**:
- MacBook con Apple Silicon (M1/M2/M3/M4)
- Necesitas mínima latencia (0.8-1.5s)
- Quieres visualización web profesional
- Necesitas glosarios personalizados
- Trabajas en ambiente con ruido

✅ **Ventajas**:
- Más rápido (2-3x)
- Sin Docker
- Filtros avanzados
- Mejor UX

---

### Usa la Versión LEGACY (Docker + `legacy/client_*.py`)

⚠️ **Si tienes**:
- Linux, Windows, o Mac Intel
- No puedes instalar dependencias locales
- Necesitas portabilidad
- Múltiples usuarios compartiendo servidor

⚠️ **Limitaciones**:
- Más lento
- Sin noise gate
- Sin anti-alucinación
- Sin interfaz web

---

### Setup con Legacy (Solo si es necesario)

Si necesitas usar el sistema legacy:

#### 1. Iniciar Servidor Docker

```bash
# Construir imagen
docker build -t whisper-live-server ./docker

# Ejecutar servidor
docker run -d -p 9090:9090 whisper-live-server

# O con docker-compose
docker-compose up -d
```

#### 2. Usar Cliente Legacy

```bash
# Activar entorno
source venv-client/bin/activate

# Opción A: Transcripción simple
python legacy/transcriptions.py --model small

# Opción B: Con DeepL
export DEEPL_API_KEY="tu-key"
python legacy/client_deepl.py --source-lang en --target-lang es

# Opción C: Optimizado M4 (con Docker)
export DEEPL_API_KEY="tu-key"
python legacy/client_m4.py --model small
```

---

## 🔑 Conceptos Clave

### ¿Por qué se abandonó Docker?

1. **Overhead**: Docker añade latencia al procesar audio
2. **No aprovecha M4**: El contenedor no usa Neural Engine ni optimizaciones Apple
3. **Complejidad**: Requiere construir imagen, gestionar contenedor
4. **Recursos**: Docker consume más RAM

### ¿Por qué faster-whisper int8?

- **2-3x más rápido** que openai-whisper original
- **Uso de int8** optimizado para CPU Apple Silicon
- **Menor uso de RAM** sin perder calidad significativa

### ¿Qué es el Noise Gate?

Filtro que **ignora audio por debajo de cierto umbral** (silencio/ruido de fondo).

**Beneficios**:
- Evita procesar silencio innecesario
- Reduce alucinaciones de Whisper
- Limpia buffer automáticamente

### ¿Qué son las alucinaciones?

Whisper a veces **"inventa" texto** cuando no hay audio claro:
- "Thank you."
- "Subtitles by..."
- Repeticiones sin sentido

**Solución en `client_m4_optimized.py`**:
- Lista negra de frases comunes
- Detección y descarte automático
- Limpieza de buffer al detectar alucinación

---

## 📚 Referencias Cruzadas

- **README principal**: [README.md](file:///Users/dedece/dev/whisper_live_docker/README.md)
- **Cliente actual**: [client_m4_optimized.py](file:///Users/dedece/dev/whisper_live_docker/client_m4_optimized.py)
- **Servidor actual**: [subtitle_server.py](file:///Users/dedece/dev/whisper_live_docker/subtitle_server.py)
- **Instalación**: [install_local.sh](file:///Users/dedece/dev/whisper_live_docker/install_local.sh)

---

## 🗂️ Estructura de Archivos

```
whisper_live_docker/
├── README.md                    # ✅ Documentación principal ACTUAL
├── client_m4_optimized.py      # ✅ Cliente ACTUAL
├── subtitle_server.py          # ✅ Servidor ACTUAL
├── install_local.sh            # ✅ Script instalación ACTUAL
│
├── legacy/                     # ⚠️ Archivos LEGACY (archivados)
│   ├── transcriptions.py      # V1: Solo transcripción
│   ├── client_deepl.py        # V2: + DeepL
│   ├── client_m4.py           # V3: + Caché
│   └── run_server.py          # Servidor Docker
│
└── docs/                       # 📖 Documentación adicional
    ├── M4_OPTIMIZATIONS.md    # Historia optimizaciones
    ├── README_SUBTITLES.md    # Docs servidor web (vigente)
    ├── DEEPL_SETUP.md         # Setup DeepL (vigente)
    └── LOCAL_SETUP.md         # Setup local M4 (vigente)
```

---

## 💡 Conclusión

Los archivos en `legacy/` representan la **evolución iterativa** del sistema:

1. **V1** (`transcriptions.py`): Transcripción básica
2. **V2** (`client_deepl.py`): + Traducción DeepL
3. **V3** (`client_m4.py`): + Caché y optimizaciones
4. **V4** (`client_m4_optimized.py`): Reescritura completa local ✅

**Recomendación**: Usar siempre la **versión actual** para Apple Silicon. Los archivos legacy se mantienen solo para:
- Referencia histórica
- Compatibilidad con sistemas sin macOS
- Aprendizaje de la evolución del código

---

**Última actualización**: 2025-12-30  
**Versión actual recomendada**: `client_m4_optimized.py` + `subtitle_server.py`
