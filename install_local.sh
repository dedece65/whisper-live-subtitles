#!/bin/bash
set -e

echo "🚀 Instalando Whisper Local con CoreML para Apple M4..."
echo ""

# Verificar que estamos en macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo "❌ Error: Este script es solo para macOS"
    exit 1
fi

# Verificar chip Apple Silicon
if [[ "$(uname -m)" != "arm64" ]]; then
    echo "❌ Error: Este script requiere Apple Silicon (M1/M2/M3/M4)"
    exit 1
fi

echo "✅ Sistema verificado: macOS con Apple Silicon"
echo ""

# Crear entorno virtual
echo "📦 Creando entorno virtual venv-local..."
python3 -m venv venv-local

# Activar entorno virtual
source venv-local/bin/activate

echo "✅ Entorno virtual creado y activado"
echo ""

# Actualizar pip
echo "⬆️  Actualizando pip..."
pip install --upgrade pip setuptools wheel

# Instalar PyTorch con soporte MPS (Metal Performance Shaders)
echo "🔧 Instalando PyTorch optimizado para Apple Silicon..."
pip install torch torchvision torchaudio

# Instalar Whisper y dependencias
echo "🎙️  Instalando OpenAI Whisper..."
pip install openai-whisper

# Instalar faster-whisper (más rápido con CoreML)
echo "⚡ Instalando faster-whisper..."
pip install faster-whisper

# Instalar dependencias de audio
echo "🔊 Instalando dependencias de audio..."
pip install sounddevice numpy scipy

# Instalar deep-translator para DeepL
echo "🌐 Instalando deep-translator..."
pip install deep-translator

# Crear archivo de requirements
echo "📝 Creando requirements-local.txt..."
pip freeze > requirements-local.txt

echo ""
echo "✅ ¡Instalación completa!"
echo ""
echo "📋 Próximos pasos:"
echo "1. Activar entorno: source venv-local/bin/activate"
echo "2. Establecer API key: export DEEPL_API_KEY='tu-key'"
echo "3. Ejecutar cliente: python client_local_coreml.py"
echo ""
echo "⚡ El primer uso descargará el modelo (~500MB)"
echo ""
