// Estado de la aplicación
let audioContext = null;
let mediaStream = null;
let websocket = null;
let audioWorkletNode = null;
let isRecording = false;
let transcriptionHistory = [];

// Elementos del DOM
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const clearBtn = document.getElementById('clearBtn');
const downloadBtn = document.getElementById('downloadBtn');
const serverHost = document.getElementById('serverHost');
const serverPort = document.getElementById('serverPort');
const language = document.getElementById('language');
const model = document.getElementById('model');
const statusIndicator = document.getElementById('statusIndicator');
const statusText = document.getElementById('statusText');
const audioLevel = document.getElementById('audioLevel');
const transcriptionDisplay = document.getElementById('transcriptionDisplay');

// Event Listeners
startBtn.addEventListener('click', startTranscription);
stopBtn.addEventListener('click', stopTranscription);
clearBtn.addEventListener('click', clearTranscription);
downloadBtn.addEventListener('click', downloadTranscription);

// Función principal para iniciar transcripción
async function startTranscription() {
    try {
        updateStatus('connecting', 'Conectando...');
        
        // Solicitar acceso al micrófono
        mediaStream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                sampleRate: 16000
            } 
        });
        
        // Crear contexto de audio
        audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
        const source = audioContext.createMediaStreamSource(mediaStream);
        
        // Conectar WebSocket
        const wsUrl = `ws://${serverHost.value}:${serverPort.value}`;
        websocket = new WebSocket(wsUrl);
        
        websocket.onopen = () => {
            console.log('WebSocket conectado');
            updateStatus('connected', 'Conectado - Escuchando...');
            isRecording = true;
            startBtn.disabled = true;
            stopBtn.disabled = false;
            
            // Enviar configuración inicial
            const config = {
                language: language.value,
                model: model.value,
                task: 'transcribe',
                use_vad: true
            };
            websocket.send(JSON.stringify(config));
            
            // Procesar audio
            processAudio(source);
        };
        
        websocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('Mensaje recibido:', data);
                
                if (data.text || data.segments) {
                    const text = data.text || (data.segments && data.segments.map(s => s.text).join(' '));
                    if (text && text.trim()) {
                        addTranscription(text, data.is_final || false);
                    }
                }
            } catch (e) {
                console.error('Error procesando mensaje:', e);
            }
        };
        
        websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            updateStatus('error', 'Error de conexión');
            stopTranscription();
        };
        
        websocket.onclose = () => {
            console.log('WebSocket cerrado');
            if (isRecording) {
                updateStatus('disconnected', 'Desconectado');
                stopTranscription();
            }
        };
        
    } catch (error) {
        console.error('Error:', error);
        updateStatus('error', `Error: ${error.message}`);
        alert(`No se pudo acceder al micrófono: ${error.message}\n\nAsegúrate de dar permisos de micrófono al navegador.`);
    }
}

// Procesar audio y enviarlo al servidor
function processAudio(source) {
    const processor = audioContext.createScriptProcessor(4096, 1, 1);
    
    source.connect(processor);
    processor.connect(audioContext.destination);
    
    processor.onaudioprocess = (e) => {
        if (!isRecording || !websocket || websocket.readyState !== WebSocket.OPEN) {
            return;
        }
        
        const inputData = e.inputBuffer.getChannelData(0);
        
        // Calcular nivel de audio para visualización
        const sum = inputData.reduce((acc, val) => acc + Math.abs(val), 0);
        const average = sum / inputData.length;
        const level = Math.min(100, average * 1000);
        audioLevel.style.width = `${level}%`;
        
        // Convertir a Int16Array para enviar al servidor
        const int16Data = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
            const s = Math.max(-1, Math.min(1, inputData[i]));
            int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        
        // Enviar audio como array buffer
        if (websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send(int16Data.buffer);
        }
    };
}

// Detener transcripción
function stopTranscription() {
    isRecording = false;
    
    if (websocket) {
        websocket.close();
        websocket = null;
    }
    
    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
        mediaStream = null;
    }
    
    if (audioContext) {
        audioContext.close();
        audioContext = null;
    }
    
    startBtn.disabled = false;
    stopBtn.disabled = true;
    audioLevel.style.width = '0%';
    updateStatus('disconnected', 'Desconectado');
}

// Añadir transcripción a la visualización
function addTranscription(text, isFinal = false) {
    // Eliminar estado vacío si existe
    const emptyState = transcriptionDisplay.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }
    
    const now = new Date();
    const timeStr = now.toLocaleTimeString('es-ES');
    
    // Si es transcripción parcial, actualizar la última entrada si existe
    const lastEntry = transcriptionDisplay.querySelector('.transcription-entry:last-child');
    
    if (!isFinal && lastEntry && !lastEntry.classList.contains('final')) {
        // Actualizar entrada existente
        lastEntry.querySelector('.transcription-text').textContent = text;
    } else {
        // Crear nueva entrada
        const entry = document.createElement('div');
        entry.className = `transcription-entry${isFinal ? ' final' : ''}`;
        entry.innerHTML = `
            <div class="transcription-time">${timeStr}</div>
            <div class="transcription-text">${text}</div>
        `;
        transcriptionDisplay.appendChild(entry);
        
        // Guardar en historial
        transcriptionHistory.push({ time: timeStr, text, isFinal });
        
        // Scroll automático
        transcriptionDisplay.scrollTop = transcriptionDisplay.scrollHeight;
    }
}

// Limpiar transcripción
function clearTranscription() {
    transcriptionDisplay.innerHTML = `
        <div class="empty-state">
            <div class="empty-icon">🎤</div>
            <p>Presiona "Iniciar Transcripción" y comienza a hablar</p>
            <p class="empty-hint">Los subtítulos aparecerán aquí en tiempo real</p>
        </div>
    `;
    transcriptionHistory = [];
}

// Descargar transcripción
function downloadTranscription() {
    if (transcriptionHistory.length === 0) {
        alert('No hay transcripciones para descargar');
        return;
    }
    
    // Crear contenido SRT
    let srtContent = '';
    let index = 1;
    
    for (const entry of transcriptionHistory.filter(e => e.isFinal)) {
        srtContent += `${index}\n`;
        srtContent += `${entry.time} --> ${entry.time}\n`;
        srtContent += `${entry.text}\n\n`;
        index++;
    }
    
    // Si no hay finales, usar todas
    if (!srtContent) {
        for (const entry of transcriptionHistory) {
            srtContent += `${index}\n`;
            srtContent += `${entry.time} --> ${entry.time}\n`;
            srtContent += `${entry.text}\n\n`;
            index++;
        }
    }
    
    // Descargar archivo
    const blob = new Blob([srtContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transcripcion_${new Date().toISOString().slice(0, 10)}.srt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Actualizar estado
function updateStatus(status, text) {
    statusIndicator.className = `status-indicator ${status}`;
    statusText.textContent = text;
}

// Inicialización
console.log('Whisper Live Web Interface cargada');
console.log('Asegúrate de que el servidor esté corriendo en el puerto configurado');
