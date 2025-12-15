# Sistema de Subtítulos en Tiempo Real para Whisper

Sistema web profesional para proyectar traducciones de Whisper en tiempo real como subtítulos.

## 🎬 Características

- **Diseño profesional** optimizado para proyección
- **Subtítulos en tiempo real** vía WebSockets
- **Animaciones suaves** con efectos fade-in y slide-up
- **Historial visual** de últimos 3 subtítulos con opacidad gradual
- **Texto grande y legible** ideal para presentaciones y eventos
- **Responsive** se adapta a cualquier tamaño de pantalla
- **Pantalla completa** con F11

## 📋 Requisitos

```bash
pip install flask flask-socketio flask-cors
```

## 🚀 Uso

### 1. Iniciar el servidor de subtítulos

En una terminal:

```bash
python3 subtitle_server.py
```

El servidor se iniciará en `http://localhost:5000`

### 2. Abrir la página de subtítulos

Abre tu navegador en `http://localhost:5000`

- Presiona **F11** para pantalla completa
- Los subtítulos aparecerán automáticamente cuando se envíen traducciones

### 3. Iniciar el cliente Whisper con web display

En otra terminal:

```bash
# Con web display activado
python3 client_local_coreml.py --web-display

# O sin web display (solo consola)
python3 client_local_coreml.py
```

## 🧪 Prueba sin micrófono

Para probar el sistema sin usar el micrófono:

```bash
python3 test_subtitles.py
```

Este script enviará 6 subtítulos de prueba cada 3 segundos.

## 🎯 Workflow completo

```bash
# Terminal 1: Servidor de subtítulos
python3 subtitle_server.py

# Terminal 2: Cliente Whisper
export DEEPL_API_KEY='tu-api-key'
python3 client_local_coreml.py --web-display --model small

# Navegador: http://localhost:5000 (F11 para pantalla completa)
```

## 📁 Archivos del sistema

- **`subtitle_server.py`**: Servidor Flask con Socket.IO
- **`templates/subtitles.html`**: Interfaz web de subtítulos
- **`client_local_coreml.py`**: Cliente Whisper (modificado con soporte web)
- **`test_subtitles.py`**: Script de prueba

## 🎨 Características visuales

- Fondo degradado oscuro profesional
- Texto con sombras para máximo contraste
- Subtítulo actual: texto grande (3.5rem) con borde verde brillante
- Historial: 2 subtítulos anteriores con opacidad reducida
- Animaciones: fade-in y slide-up suaves
- Contador de subtítulos y timestamp en tiempo real

## 💡 Tips

- **Para proyección**: Usa pantalla completa (F11) y proyecta la ventana del navegador
- **Múltiples pantallas**: Los WebSockets permiten que múltiples navegadores vean los mismos subtítulos simultáneamente
- **Sin servidor**: El cliente funciona normalmente sin `--web-display` mostrando solo en consola
- **Latencia**: Los subtítulos aparecen instantáneamente (< 100ms) después de la traducción
