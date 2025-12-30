# Usa una imagen base de Python ligera
FROM python:3.11-slim

# Instalar herramientas de compilación y librerías de audio necesarias.
RUN apt update && \
    apt install -y --no-install-recommends \
    # Dependencias del sistema y compilación
    build-essential \
    python3-dev \
    # Dependencias de audio (PortAudio)
    libasound-dev \
    portaudio19-dev \
    && apt autoremove -y && apt clean && rm -rf /var/lib/apt/lists/*

# Establece variables de entorno para el Entorno Virtual (venv)
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Establece el directorio de trabajo
WORKDIR /app

# 1. Crea el Entorno Virtual
RUN python -m venv $VIRTUAL_ENV

# 2. Instala las dependencias de Python (que ahora deberían compilar correctamente)
RUN pip install --upgrade pip \
    && pip install torch \
    && pip install -U openai-whisper \
    && pip install whisper-live \
    && pip install sounddevice

# Copia el script del servidor
COPY run_server.py /app/run_server.py

# Comando para iniciar el servidor de whisper-live
CMD ["/opt/venv/bin/python", "/app/run_server.py", "--port", "9090", "--backend", "faster_whisper"]