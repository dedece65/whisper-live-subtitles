# 🎙️ Whisper Live - Transcripción en Tiempo Real con Docker

Sistema de transcripción automática en tiempo real usando OpenAI Whisper. El servidor corre en Docker y el cliente captura audio del micrófono de tu máquina.

## 📋 Requisitos

- **Docker** instalado ([Instalar Docker](https://docs.docker.com/get-docker/))
- **Python 3.8+** en el host (para el cliente)
- **Micrófono** funcional
- **8GB+ RAM** recomendado (4GB mínimo)

### Requisitos Opcionales

- **GPU NVIDIA** con CUDA (para mejor rendimiento)
- **nvidia-docker** si usas GPU

## 🚀 Inicio Rápido

### 1️⃣ Construir y ejecutar el servidor

```bash
# Opción A: Usar docker-compose (recomendado)
docker-compose up -d

# Opción B: Usar docker directamente
docker build -t whisper-live-server .
docker run -d -p 9090:9090 --name whisper-server whisper-live-server
```

El servidor tardará unos segundos en iniciar y cargar el modelo.

### 2️⃣ Instalar dependencias del cliente

#### En macOS (con entorno virtual):

```bash
# Instalar PortAudio (requerido para PyAudio)
brew install portaudio

# Crear entorno virtual
python3 -m venv venv-client

# Activar entorno virtual
source venv-client/bin/activate

# Instalar dependencias
pip install -r requirements-client.txt
```

#### En Linux/Windows:

```bash
# Linux: Instalar PortAudio del sistema
sudo apt-get install portaudio19-dev  # Debian/Ubuntu
# o
sudo dnf install portaudio-devel      # Fedora

# Windows: normalmente PyAudio viene pre-compilado, pero si falla:
# - Descargar wheel desde https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

# Crear e instalar en entorno virtual
python -m venv venv-client
source venv-client/bin/activate  # Linux/Mac
# o
venv-client\Scripts\activate     # Windows

pip install -r requirements-client.txt
```

### 3️⃣ Ejecutar el cliente

```bash
# Activar el entorno virtual si no está activado
source venv-client/bin/activate

# Ejecutar el cliente
python client.py
```

¡Habla al micrófono y verás los subtítulos en tiempo real! 🎉

## 🌐 Interfaz Web (Nueva)

Para una experiencia visual más completa, puedes usar la interfaz web:

### 1️⃣ Iniciar el servidor (si no está iniciado)

```bash
docker-compose up -d
```

### 2️⃣ Iniciar servidor web

```bash
cd web
python3 -m http.server 8000
```

### 3️⃣ Abrir en el navegador

Navega a: **http://localhost:8000**

**Características de la interfaz web:**
- ✨ Diseño moderno con dark mode
- 🎙️ Captura de audio directamente desde el navegador
- 📊 Visualización de nivel de audio en tiempo real
- 🌍 Selector de idioma y modelo
- 💾 Descarga de transcripciones en formato SRT
- 📱 Diseño responsive

Ver [web/README.md](file:///Users/dedece/dev/whisper_live_docker/web/README.md) para más detalles.

## ⚙️ Configuración Avanzada

### Opciones del Cliente

```bash
# Usar un modelo diferente (más grande = más preciso pero más lento)
python client.py --model medium

# Conectar a un servidor remoto
python client.py --host 192.168.1.100 --port 9090

# Traducir al inglés en lugar de transcribir
python client.py --task translate --lang es

# Cambiar idioma de transcripción
python client.py --lang es  # español
python client.py --lang fr  # francés
```

**Modelos disponibles:**
- `tiny` - Más rápido, menos preciso
- `base` - Balance velocidad/precisión
- `small` - Recomendado (default)
- `medium` - Mejor precisión, más lento
- `large`, `large-v2`, `large-v3` - Máxima precisión, requiere GPU

### Ver ayuda completa

```bash
python client.py --help
```

## 🐳 Comandos Docker Útiles

```bash
# Ver logs del servidor
docker logs whisper-server

# Detener el servidor
docker stop whisper-server

# Reiniciar el servidor
docker restart whisper-server

# Eliminar el contenedor
docker rm -f whisper-server

# Con docker-compose
docker-compose logs -f    # Ver logs
docker-compose down       # Detener y eliminar
docker-compose restart    # Reiniciar
```

## 🎮 Uso con GPU

Para usar GPU NVIDIA y acelerar la transcripción:

1. Instala [nvidia-docker](https://github.com/NVIDIA/nvidia-docker)

2. Edita `docker-compose.yml` y descomenta las líneas bajo `deploy`

3. Ejecuta:
```bash
docker-compose up -d
```

## 🔧 Solución de Problemas

### El cliente no puede conectar al servidor

**Error:** `ConnectionRefusedError`

**Solución:**
1. Verifica que el servidor esté ejecutándose:
   ```bash
   docker ps
   ```
2. Verifica que el puerto 9090 esté mapeado:
   ```bash
   docker port whisper-server
   ```
3. Espera unos segundos más (el servidor tarda en cargar el modelo)

### No se captura audio del micrófono

**Solución:**
1. Verifica que tu micrófono esté conectado y funcional
2. Otorga permisos de micrófono a la terminal (en macOS: Preferencias → Seguridad → Micrófono)
3. Prueba listar dispositivos de audio:
   ```python
   import sounddevice as sd
   print(sd.query_devices())
   ```

### Transcripción muy lenta

**Soluciones:**
- Usa un modelo más pequeño: `python client.py --model tiny`
- Usa GPU si está disponible (ver sección GPU)
- Cierra otras aplicaciones que consuman recursos

### El servidor se queda sin memoria

**Solución:**
- Usa un modelo más pequeño editando `docker-compose.yml`:
  ```yaml
  environment:
    - WHISPER_MODEL=tiny.en
  ```
- Aumenta la memoria disponible para Docker en configuración

## 📝 Arquitectura

```
┌─────────────┐          WebSocket          ┌──────────────┐
│   Cliente   │◄─────────(puerto 9090)─────►│   Servidor   │
│  (Host)     │                              │   (Docker)   │
│             │                              │              │
│ - Captura   │     Envía audio chunks       │ - Whisper    │
│   micrófono │ ──────────────────────────►  │   Model      │
│             │                              │              │
│ - Muestra   │  ◄────── Subtítulos ──────── │ - Faster     │
│   subtítulos│                              │   Whisper    │
└─────────────┘                              └──────────────┘
```

## 🤝 Contribuir

¿Encontraste un problema o tienes una mejora? ¡Las contribuciones son bienvenidas!

## 📄 Licencia

Este proyecto usa [Whisper Live](https://github.com/collabora/WhisperLive) y [OpenAI Whisper](https://github.com/openai/whisper).

## 🙏 Créditos

- [OpenAI Whisper](https://github.com/openai/whisper) - Modelo de transcripción
- [Whisper Live](https://github.com/collabora/WhisperLive) - Servidor/cliente en tiempo real
- [Faster Whisper](https://github.com/guillaumekln/faster-whisper) - Backend optimizado
