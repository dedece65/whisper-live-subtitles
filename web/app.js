// Estado de la aplicación
let audioContext = null;
let mediaStream = null;
let websocket = null;
let audioWorkletNode = null;
let isRecording = false;
let serverReady = false;
let transcriptionHistory = [];
let clientUid = null;
let audioProcessor = null;

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

// Generar UUID
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Función principal para iniciar transcripción
async function startTranscription() {
    try {
        updateStatus('connecting', 'Conectando...');
        serverReady = false;
        clientUid = generateUUID();
        
        // Solicitar acceso al micrófono con configuración específica
        mediaStream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                channelCount: 1,  // Mono explícitamente
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
                sampleRate: { ideal: 16000 }
            } 
        });
        
        // Crear contexto de audio
        audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
        const source = audioContext.createMediaStreamSource(mediaStream);
        
        // Conectar WebSocket
        const wsUrl = `ws://${serverHost.value}:${serverPort.value}`;
        websocket = new WebSocket(wsUrl);
        websocket.binaryType = 'arraybuffer';
        
        websocket.onopen = () => {
            console.log('WebSocket conectado');
            isRecording = true;
            startBtn.disabled = true;
            stopBtn.disabled = false;
            
            // Enviar configuración inicial (según protocolo whisper-live)
            const config = {
                uid: clientUid,
                language: language.value || null,
                task: 'transcribe',
                model: model.value,
                use_vad: false,  // DESACTIVADO: El VAD está filtrando todo
                max_clients: 4,
                max_connection_time: 600,
                send_last_n_segments: 10,
                no_speech_thresh: 0.3,  // Menos estricto (default 0.45)
                clip_audio: false,
                same_output_threshold: 5  // Reducido de 10 para respuestas más rápidas
            };
            
            console.log('Enviando configuración:', config);
            websocket.send(JSON.stringify(config));
        };
        
        websocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('Mensaje recibido:', data);
                
                // Validar UID
                if (data.uid && data.uid !== clientUid) {
                    console.error('UID inválido');
                    return;
                }
                
                // Manejar diferentes tipos de mensajes
                if (data.message === 'SERVER_READY') {
                    serverReady = true;
                    updateStatus('connected', 'Conectado - Escuchando...');
                    console.log('Servidor listo, iniciando captura de audio');
                    processAudio(source);
                } else if (data.message === 'DISCONNECT') {
                    console.log('Servidor desconectó por tiempo excedido');
                    stopTranscription();
                } else if (data.status) {
                    handleStatusMessage(data);
                } else if (data.segments) {
                    processSegments(data.segments);
                } else if (data.language) {
                    console.log(`Idioma detectado: ${data.language} (${data.language_prob})`);
                }
            } catch (e) {
                console.error('Error procesando mensaje:', e, event.data);
            }
        };
        
        websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            updateStatus('error', 'Error de conexión');
        };
        
        websocket.onclose = (event) => {
            console.log('WebSocket cerrado', {
                code: event.code,
                reason: event.reason,
                wasClean: event.wasClean
            });
            
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

// Manejar mensajes de estado del servidor
function handleStatusMessage(data) {
    if (data.status === 'WAIT') {
        updateStatus('waiting', `En espera - ${Math.round(data.message)} min`);
        console.log(`Servidor lleno. Tiempo de espera: ${data.message} minutos`);
    } else if (data.status === 'ERROR') {
        updateStatus('error', `Error: ${data.message}`);
        console.error(`Error del servidor: ${data.message}`);
    } else if (data.status === 'WARNING') {
        console.warn(`Advertencia del servidor: ${data.message}`);
    }
}

// Procesar segmentos de transcripción
function processSegments(segments) {
    if (!segments || segments.length === 0) return;
    
    for (const segment of segments) {
        const text = segment.text;
        const isFinal = segment.completed || false;
        
        if (text && text.trim()) {
            addTranscription(text, isFinal);
        }
    }
}

// Procesar audio y enviarlo al servidor
function processAudio(source) {
    audioProcessor = audioContext.createScriptProcessor(4096, 1, 1);
    
    source.connect(audioProcessor);
    audioProcessor.connect(audioContext.destination);
    
    console.log(`Audio Context: ${audioContext.sampleRate}Hz`);
    
    audioProcessor.onaudioprocess = (e) => {
        if (!isRecording || !websocket || websocket.readyState !== WebSocket.OPEN || !serverReady) {
            return;
        }
        
        // Obtener datos de audio (ya es mono porque pedimos 1 canal)
        const inputData = e.inputBuffer.getChannelData(0);
        
        // Calcular nivel de audio para visualización
        let sum = 0;
        for (let i = 0; i < inputData.length; i++) {
            // Asegurarse de que no hay NaN o Infinity
            if (isFinite(inputData[i])) {
                sum += Math.abs(inputData[i]);
            }
        }
        const average = sum / inputData.length;
        const level = Math.min(100, average * 1000);
        audioLevel.style.width = `${level}%`;
        
        // Convertir Float32 a Int16 correctamente, validando datos
        const int16Data = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
            // Validar y clampar valores
            let s = inputData[i];
            if (!isFinite(s)) {
                s = 0; // Reemplazar NaN/Infinity con 0
            } else {
                s = Math.max(-1, Math.min(1, s));
            }
            // Convertir a Int16 con rango completo
            int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        
        // Enviar audio como array buffer (binario)
        try {
            websocket.send(int16Data.buffer);
        } catch (e) {
            console.error('Error enviando audio:', e);
        }
    };
}

// Detener transcripción
function stopTranscription() {
    isRecording = false;
    serverReady = false;
    
    if (audioProcessor) {
        audioProcessor.disconnect();
        audioProcessor = null;
    }
    
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
