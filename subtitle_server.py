#!/usr/bin/env python3
"""
Servidor de Subtítulos en Tiempo Real.
Muestra traducciones del cliente Whisper en una página web optimizada para proyección.
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'whisper-subtitle-secret-key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Historial de subtítulos (últimos 3)
subtitle_history = []
subtitle_counter = 0


@app.route('/')
def index():
    """Página principal de subtítulos."""
    return render_template('subtitles.html')


@app.route('/subtitle', methods=['POST'])
def receive_subtitle():
    """Recibe subtítulos del cliente Whisper."""
    global subtitle_counter
    
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    subtitle_counter += 1
    
    subtitle_data = {
        'text': text,
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'id': subtitle_counter
    }
    
    # Agregar al historial (máximo 3)
    subtitle_history.append(subtitle_data)
    if len(subtitle_history) > 3:
        subtitle_history.pop(0)
    
    # Transmitir a todos los clientes conectados
    socketio.emit('new_subtitle', subtitle_data)
    
    return jsonify({'status': 'ok', 'id': subtitle_counter})


@app.route('/history', methods=['GET'])
def get_history():
    """Obtener historial de subtítulos."""
    return jsonify(subtitle_history)


@socketio.on('connect')
def handle_connect():
    """Maneja nueva conexión de cliente."""
    print(f"✅ Cliente conectado")
    # Enviar historial al nuevo cliente
    emit('history', subtitle_history)


@socketio.on('disconnect')
def handle_disconnect():
    """Maneja desconexión de cliente."""
    print(f"❌ Cliente desconectado")


def main():
    print("=" * 60)
    print("🎬 SERVIDOR DE SUBTÍTULOS EN TIEMPO REAL")
    print("=" * 60)
    print(f"🌐 URL: http://localhost:5000")
    print(f"📡 WebSocket: Activado")
    print(f"📝 Historial: Últimos 3 subtítulos")
    print("=" * 60)
    print("\n✨ Servidor iniciado. Abre http://localhost:5000 en tu navegador.")
    print("   Para pantalla completa, presiona F11\n")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)


if __name__ == '__main__':
    main()
