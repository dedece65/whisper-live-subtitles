# Interfaz Web de Whisper Live

Interfaz web moderna para transcripción de audio en tiempo real usando Whisper Live.

## 🚀 Inicio Rápido

### 1. Asegúrate de que el servidor está corriendo

```bash
cd /Users/dedece/dev/whisper_live_docker
docker-compose up -d
```

### 2. Inicia un servidor web simple

```bash
cd web
python3 -m http.server 8000
```

### 3. Abre tu navegador

Navega a: http://localhost:8000

## 🎨 Características

- ✨ Interfaz moderna con diseño dark mode
- 🎙️ Captura de audio directamente desde el navegador
- 📡 Conexión WebSocket en tiempo real
- 📊 Visualización de nivel de audio
- 🌍 Soporte multiidioma
- ⚙️ Configuración de modelo Whisper
- 💾 Descarga de transcripciones en formato SRT
- 📱 Diseño responsive

## ⚙️ Configuración

- **Servidor**: localhost (o IP del servidor Docker)
- **Puerto**: 9090 (puerto WebSocket del servidor)
- **Idioma**: Selecciona el idioma de transcripción
- **Modelo**: tiny, base, small (recomendado), medium, large

## 🔧 Uso

1. Configura el servidor y puerto (por defecto: localhost:9090)
2. Selecciona idioma y modelo
3. Presiona "Iniciar Transcripción"
4. Permite el acceso al micrófono cuando el navegador lo solicite
5. Comienza a hablar - los subtítulos aparecerán en tiempo real
6. Presiona "Detener" cuando termines
7. Usa "Descargar" para guardar la transcripción

## 🌐 Navegadores Soportados

- Chrome/Chromium (recomendado)
- Firefox
- Edge
- Safari (puede requerir permisos adicionales)

## ⚠️ Notas

- **Permisos de micrófono**: El navegador solicitará permiso para acceder al micrófono
- **HTTPS**: Para producción, se recomienda usar HTTPS (algunos navegadores restringen acceso a micrófono en HTTP)
- **Servidor corriendo**: Asegúrate de que el servidor Docker esté activo antes de usar la interfaz

## 🎯 Servidor Web Alternativo

Si no tienes Python, puedes usar:

```bash
# Con Node.js
npx http-server web -p 8000

# Con PHP
php -S localhost:8000 -t web
```
