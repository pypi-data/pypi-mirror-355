// Atlas Code - Autonomer KI-Entwicklungsassistent
// VOLLSTÄNDIG WIEDERHERGESTELLT - Performance-optimiert

// Globale Referenzen - Performance-optimiert
const promptInput = document.getElementById('prompt-input');
const terminalOutput = document.getElementById('terminal-output');
const statusText = document.getElementById('status-text');
const currentTokensSpan = document.getElementById('current-tokens');
const sessionTokensSpan = document.getElementById('session-tokens');
const tokenSpeedSpan = document.getElementById('token-speed');
const timerSpan = document.getElementById('timer');
const workingDirSpan = document.getElementById('working-dir');
const autoAcceptIndicator = document.getElementById('auto-accept-indicator');
const autoAcceptStatus = document.getElementById('auto-accept-status');
const contextIndicator = document.getElementById('context-indicator');
const contextPercentage = document.getElementById('context-percentage');

// Performance-Variablen
let lastScrollTime = 0;
let scrollThrottle = 16; // ~60fps
let lastTokenUpdate = 0;
let tokenUpdateThrottle = 100; // 100ms

let isProcessing = false;
let currentTypewriterMessage = null;
let currentRawText = ''; // Roher Text-Buffer für Typewriter
let startTime = null;
let timerInterval = null;

// Erweiterte State-Verwaltung
let appState = {
    sessionId: null,
    totalSessions: 0,
    cacheSize: 0,
    performance: {
        avgResponseTime: 0,
        totalRequests: 0,
        cacheHits: 0
    },
    ui: {
        maxMessages: 1000, // Begrenzt DOM-Elemente
        autoCleanup: true,
        compactMode: false
    }
};

// Claude Code Features
let autoAcceptEdits = true;
let contextUsage = {
    used: 0,
    total: 50000, // Max context length
    percentage: 100
};

// Glüh-Effekt State
let lastGlowTime = 0;

// Token-Tracking
let tokenStats = {
    current: 0,
    session: 0,
    speed: 0,
    time: 0
};

class AtlasApp {
    constructor() {
        this.initializeApp();
        this.setupEventListeners();
        this.loadSystemInfo();
        this.startTimer();
    }
    
    initializeApp() {
        console.log('🔥 Atlas Code gestartet');
        this.updateStatus('Atlas bereit', 'ready');
        
        // Terminal-Container für bessere Performance optimieren
        if (terminalOutput) {
            terminalOutput.classList.add('scroll-optimized');
        }
    }
    
    setupEventListeners() {
        // Enter-Taste für Eingabe (vereinfacht!)
        if (promptInput) {
            promptInput.addEventListener('keydown', (event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    this.sendMessage();
                }
            });
            
            // Glüh-Effekt für User-Input
            promptInput.addEventListener('input', (event) => {
                this.addGlowToInput(event);
            });
        }
        
        // Erweiterte Keyboard-Shortcuts
        document.addEventListener('keydown', (event) => {
            // Escape zum Abbrechen
            if (event.key === 'Escape' && isProcessing) {
                this.interruptProcess();
            }
            // Ctrl+Alt+E für Notstop (Modell entladen)
            else if (event.ctrlKey && event.altKey && event.key === 'e') {
                event.preventDefault();
                this.emergencyStop();
            }
            // Shift+Tab für Auto-Accept Toggle
            else if (event.shiftKey && event.key === 'Tab') {
                event.preventDefault();
                this.toggleAutoAccept();
            }
            // Ctrl+Alt+I für Cache-Info
            else if (event.ctrlKey && event.altKey && event.key === 'i') {
                event.preventDefault();
                this.showCacheInfo();
            }
            // Ctrl+Alt+C für Cache leeren
            else if (event.ctrlKey && event.altKey && event.key === 'c') {
                event.preventDefault();
                this.clearCurrentCache();
            }
            // Ctrl+Alt+N für neue Session
            else if (event.ctrlKey && event.altKey && event.key === 'n') {
                event.preventDefault();
                this.startNewSession();
            }
            // Ctrl+Alt+R für manuelle Context-Rotation (Debug)
            else if (event.ctrlKey && event.altKey && event.key === 'r') {
                event.preventDefault();
                this.triggerManualRotation();
            }
        });
    }
    
    async sendMessage() {
        const message = promptInput.value.trim();
        if (!message || isProcessing) return;
        
        console.log('📤 Sende Nachricht:', message);
        
        // Benutzer-Nachricht anzeigen
        this.addMessageToTerminal({
            role: 'user',
            type: 'message',
            content: message
        });
        
        promptInput.value = '';
        this.setProcessing(true);
        
        try {
            // Direkt an Atlas senden - IMMER mit Typewriter
            console.log('🚀 Rufe atlas_chat auf...');
            await eel.atlas_chat(message)();
        } catch (error) {
            console.error('❌ Atlas-Fehler:', error);
            this.addMessageToTerminal({
                role: 'assistant',
                type: 'error',
                content: `❌ Atlas-Verbindungsfehler: ${error}`
            });
            this.setProcessing(false);
        }
    }
    
    addMessageToTerminal(chunk) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `terminal-message role-${chunk.role} chat-message`;
        
        // Content formatieren
        let content = this.formatContent(chunk.content);
        
        // Spezielle Behandlung für verschiedene Typen
        if (chunk.type === 'error') {
            messageDiv.classList.add('format-error');
        } else if (chunk.type === 'confirmation') {
            messageDiv.classList.add('type-confirmation');
        }
        
        messageDiv.innerHTML = content;
        terminalOutput.appendChild(messageDiv);
        
        // Performance-optimiertes Auto-scroll mit Throttling
        this.throttledScroll();
        
        // Auto-Cleanup für Performance
        if (appState.ui.autoCleanup) {
            this.cleanupOldMessages();
        }
        
        return messageDiv;
    }
    
    // Performance-optimierte Scroll-Funktion
    throttledScroll() {
        const now = performance.now();
        if (now - lastScrollTime > scrollThrottle) {
            terminalOutput.scrollTop = terminalOutput.scrollHeight;
            lastScrollTime = now;
        } else {
            // Debounced scroll für bessere Performance
            setTimeout(() => {
                terminalOutput.scrollTop = terminalOutput.scrollHeight;
            }, scrollThrottle);
        }
    }
    
    // DOM-Cleanup für bessere Performance
    cleanupOldMessages() {
        const messages = terminalOutput.children;
        if (messages.length > appState.ui.maxMessages) {
            const removeCount = messages.length - appState.ui.maxMessages;
            for (let i = 0; i < removeCount; i++) {
                if (messages[0]) {
                    messages[0].remove();
                }
            }
            console.log(`🧹 DOM cleanup: ${removeCount} alte Nachrichten entfernt`);
        }
    }
    
    formatContent(content) {
        if (!content) return '';
        
        // Code-Blöcke formatieren
        content = content.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
            return `<div class="code-block"><pre><code>${this.escapeHtml(code.trim())}</code></pre></div>`;
        });
        
        // Inline-Code formatieren
        content = content.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Zeilenumbrüche erhalten
        content = content.replace(/\n/g, '<br>');
        
        return content;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    updateStatus(status, type) {
        if (statusText) {
            statusText.innerHTML = `🔥 ${status}`;
            statusText.className = `status-${type} atlas-glow`;
        }
    }
    
    setProcessing(processing) {
        isProcessing = processing;
        if (promptInput) {
            promptInput.disabled = processing;
            
            if (processing) {
                promptInput.placeholder = "Atlas arbeitet... (ESC zum Abbrechen)";
                this.updateStatus('Atlas denkt nach', 'typewriting');
            } else {
                promptInput.placeholder = "Nachricht an Atlas eingeben...";
                this.updateStatus('Atlas bereit', 'ready');
            }
        }
    }
    
    updateTokenStats(stats) {
        const now = performance.now();
        
        // Throttle Token-Updates für bessere Performance
        if (now - lastTokenUpdate < tokenUpdateThrottle) {
            return;
        }
        
        if (stats.current !== undefined) tokenStats.current = stats.current;
        if (stats.session !== undefined) tokenStats.session = stats.session;
        if (stats.speed !== undefined) tokenStats.speed = stats.speed;
        if (stats.time !== undefined) tokenStats.time = stats.time;
        
        this.updateTokenDisplay();
        lastTokenUpdate = now;
    }
    
    updateTokenDisplay() {
        if (currentTokensSpan) currentTokensSpan.textContent = tokenStats.current;
        if (sessionTokensSpan) sessionTokensSpan.textContent = tokenStats.session;
        if (tokenSpeedSpan) tokenSpeedSpan.textContent = tokenStats.speed;
    }
    
    async loadSystemInfo() {
        try {
            const info = await eel.get_system_info()();
            const sandboxStatus = info.sandbox_mode ? 'Sandbox' : 'Vollzugriff';
            if (workingDirSpan) workingDirSpan.textContent = `📁 ${sandboxStatus}`;
            tokenStats.session = info.token_count || 0;
            this.updateTokenDisplay();
        } catch (error) {
            console.error('Fehler beim Laden der Systeminfo:', error);
        }
        
        // Performance-Monitoring initialisieren
        this.initPerformanceMonitoring();
    }
    
    initPerformanceMonitoring() {
        // Memory-Usage überwachen
        setInterval(() => {
            if (performance.memory) {
                const memoryInfo = {
                    used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024),
                    total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024),
                    limit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024)
                };
                
                // Warnung bei hohem Memory-Verbrauch
                if (memoryInfo.used > memoryInfo.limit * 0.8) {
                    console.warn('⚠️ Hoher Memory-Verbrauch:', memoryInfo);
                    if (appState.ui.autoCleanup) {
                        this.cleanupOldMessages();
                    }
                }
            }
        }, 30000); // Alle 30 Sekunden
    }
    
    startTimer() {
        startTime = Date.now();
        timerInterval = setInterval(() => {
            const elapsed = Date.now() - startTime;
            const minutes = Math.floor(elapsed / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            
            if (timerSpan) {
                timerSpan.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }
        }, 1000);
    }
    
    interruptProcess() {
        if (isProcessing) {
            this.addMessageToTerminal({
                role: 'assistant',
                type: 'message',
                content: '⚠️ Atlas-Verarbeitung abgebrochen'
            });
            this.setProcessing(false);
        }
    }
    
    async emergencyStop() {
        try {
            this.addMessageToTerminal({
                role: 'assistant',
                type: 'message',
                content: '🚨 NOTSTOP: Entlade deepseek-coder-v2:16b Modell...'
            });
            
            const result = await eel.emergency_stop()();
            
            if (result.success) {
                this.addMessageToTerminal({
                    role: 'assistant',
                    type: 'message',
                    content: `✅ ${result.message}`
                });
            } else {
                this.addMessageToTerminal({
                    role: 'assistant',
                    type: 'error',
                    content: `❌ ${result.error}`
                });
            }
            
            // Reset alles
            this.setProcessing(false);
            currentTypewriterMessage = null;
            tokenStats = { current: 0, session: 0, speed: 0, time: 0 };
            this.updateTokenDisplay();
            
        } catch (error) {
            this.addMessageToTerminal({
                role: 'assistant',
                type: 'error',
                content: `❌ Notstop-Fehler: ${error}`
            });
        }
    }
    
    toggleAutoAccept() {
        autoAcceptEdits = !autoAcceptEdits;
        
        if (autoAcceptStatus) {
            if (autoAcceptEdits) {
                autoAcceptStatus.textContent = 'on';
                autoAcceptIndicator.classList.remove('disabled');
            } else {
                autoAcceptStatus.textContent = 'off';
                autoAcceptIndicator.classList.add('disabled');
            }
        }
        
        // Visual feedback
        this.addMessageToTerminal({
            role: 'assistant',
            type: 'message',
            content: `⚙️ Auto-accept edits: ${autoAcceptEdits ? 'ON' : 'OFF'}`
        });
    }
    
    updateContextIndicator(used, total) {
        contextUsage.used = used || 0;
        contextUsage.total = total || 50000;
        contextUsage.percentage = Math.max(0, Math.round((1 - contextUsage.used / contextUsage.total) * 100));
        
        if (contextPercentage) {
            contextPercentage.textContent = contextUsage.percentage;
        }
        
        // Color coding based on context usage
        if (contextIndicator) {
            if (contextUsage.percentage < 10) {
                contextIndicator.style.color = '#ef4444'; // Red - critical
            } else if (contextUsage.percentage < 25) {
                contextIndicator.style.color = '#f59e0b'; // Orange - warning
            } else {
                contextIndicator.style.color = '#10b981'; // Green - good
            }
        }
    }
    
    addGlowToInput(event) {
        // Glüh-Effekt für User-Input beim Tippen - Performance-optimiert
        const input = event.target;
        
        // Verwende CSS-Klassen statt direkter Style-Manipulation
        input.classList.add('atlas-input-glow');
        
        // Nach 0.7s entfernen
        setTimeout(() => {
            input.classList.remove('atlas-input-glow');
        }, 700);
    }
    
    // Cache-Verwaltung UI mit Context-Rotation Info
    async showCacheInfo() {
        try {
            const cacheInfo = await eel.get_cache_info()();
            const sessions = await eel.list_available_sessions()();
            const rotationInfo = await eel.get_context_rotation_info()();
            
            let infoText = `📊 **System-Informationen:**\n\n`;
            
            // Basis-Cache-Info
            infoText += `**Aktuelle Session:** ${cacheInfo.session_id?.substring(0, 8) || 'Unbekannt'}\n`;
            infoText += `**Gesamt-Sessions:** ${cacheInfo.total_sessions || 0}\n`;
            infoText += `**Cache-Größe:** ${cacheInfo.total_cache_size_mb || 0} MB\n`;
            infoText += `**Nachrichten:** ${cacheInfo.current_conversation_length || 0}\n`;
            infoText += `**Cache-Hits:** ${cacheInfo.cache_hits || 0}\n`;
            infoText += `**Model:** ${cacheInfo.model_name || 'Unbekannt'}\n\n`;
            
            // Context-Rotation Info
            if (rotationInfo.available) {
                infoText += `**Context-Rotation:**\n`;
                infoText += `- Version: ${rotationInfo.context_version || 1}\n`;
                infoText += `- Rotationen: ${rotationInfo.total_rotations || 0}\n`;
                infoText += `- Auslastung: ${rotationInfo.current_percentage?.toFixed(1) || 0}%\n`;
                infoText += `- Threshold: ${rotationInfo.rotation_threshold || 85}%\n`;
                if (rotationInfo.avg_rotation_time_ms) {
                    infoText += `- Ø Zeit: ${rotationInfo.avg_rotation_time_ms.toFixed(0)}ms\n`;
                }
                infoText += `\n`;
            }
            
            if (sessions.sessions && sessions.sessions.length > 0) {
                infoText += `**Verfügbare Sessions:**\n`;
                sessions.sessions.slice(0, 5).forEach(session => {
                    const isActive = session.session_id === cacheInfo.session_id ? ' (aktiv)' : '';
                    infoText += `- ${session.session_id.substring(0, 8)}: ${session.message_count} Nachrichten${isActive}\n`;
                });
            }
            
            this.addMessageToTerminal({
                role: 'assistant',
                type: 'message',
                content: infoText
            });
            
        } catch (error) {
            this.addMessageToTerminal({
                role: 'assistant',
                type: 'error',
                content: `❌ System-Info-Fehler: ${error}`
            });
        }
    }
    
    // Context-Rotation UI-Management
    showContextRotationIndicator() {
        // Erstelle Rotation-Indikator
        let indicator = document.getElementById('context-rotation-indicator');
        
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'context-rotation-indicator';
            indicator.className = 'context-rotation-indicator';
            indicator.innerHTML = `
                <div class="rotation-content">
                    <span class="rotation-spinner">🔄</span>
                    <span class="rotation-text">Atlas optimiert...</span>
                </div>
            `;
            
            // Füge zu Terminal hinzu
            terminalOutput.appendChild(indicator);
            this.throttledScroll();
        }
        
        // CSS-Animation starten
        indicator.classList.add('active');
    }
    
    hideContextRotationIndicator(data) {
        const indicator = document.getElementById('context-rotation-indicator');
        
        if (indicator) {
            // Update Text basierend auf Erfolg
            const textElement = indicator.querySelector('.rotation-text');
            const spinnerElement = indicator.querySelector('.rotation-spinner');
            
            if (data.success) {
                textElement.textContent = 'Optimierung abgeschlossen';
                spinnerElement.textContent = '✅';
                indicator.classList.add('success');
            } else {
                textElement.textContent = 'Optimierung fehlgeschlagen';
                spinnerElement.textContent = '❌';
                indicator.classList.add('error');
            }
            
            // Nach 2 Sekunden entfernen
            setTimeout(() => {
                if (indicator && indicator.parentNode) {
                    indicator.parentNode.removeChild(indicator);
                }
            }, 2000);
        }
    }
    
    // Debug-Feature: Manuelle Context-Rotation
    async triggerManualRotation() {
        try {
            this.addMessageToTerminal({
                role: 'assistant',
                type: 'message',
                content: '🔧 **Debug:** Manuelle Context-Rotation gestartet...'
            });
            
            const result = await eel.trigger_manual_context_rotation()();
            
            if (result.success) {
                this.addMessageToTerminal({
                    role: 'assistant',
                    type: 'message',
                    content: `✅ Context-Rotation erfolgreich! Neue Länge: ${result.new_context_length} Nachrichten (${result.context_percentage?.toFixed(1)}%)`
                });
                
                // Update Context-Anzeige
                this.updateContextIndicator(result.context_percentage || 20, 100);
            } else {
                this.addMessageToTerminal({
                    role: 'assistant',
                    type: 'error',
                    content: `❌ Context-Rotation fehlgeschlagen: ${result.error}`
                });
            }
            
        } catch (error) {
            this.addMessageToTerminal({
                role: 'assistant',
                type: 'error',
                content: `❌ Debug-Rotation-Fehler: ${error}`
            });
        }
    }
    
    // Neue Session starten
    async startNewSession() {
        try {
            // Cache leeren
            await eel.clear_cache()();
            
            // Seite neu laden für frische Session
            window.location.reload();
            
        } catch (error) {
            this.addMessageToTerminal({
                role: 'assistant',
                type: 'error',
                content: `❌ Neue Session-Fehler: ${error}`
            });
        }
    }
    
    // Cache leeren
    async clearCurrentCache() {
        try {
            const result = await eel.clear_cache()();
            
            if (result.success) {
                this.addMessageToTerminal({
                    role: 'assistant',
                    type: 'message',
                    content: `✅ ${result.message}`
                });
                
                // Token-Stats zurücksetzen
                tokenStats = { current: 0, session: 0, speed: 0, time: 0 };
                this.updateTokenDisplay();
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            this.addMessageToTerminal({
                role: 'assistant',
                type: 'error',
                content: `❌ Cache-Löschung fehlgeschlagen: ${error}`
            });
        }
    }
}

// Atlas Typewriter-Callbacks
eel.expose(typewriter_start);
function typewriter_start(role) {
    console.log('📝 Typewriter gestartet');
    const app = window.atlasApp;
    if (app) {
        // Reset rohen Text-Buffer
        currentRawText = '';
        
        currentTypewriterMessage = app.addMessageToTerminal({
            role: 'assistant',
            type: 'message',
            content: '<span class="typewriter-cursor atlas-glow">▌</span>'
        });
    }
}

eel.expose(typewriter_chunk);
function typewriter_chunk(chunk) {
    const app = window.atlasApp;
    if (app && currentTypewriterMessage) {
        // Aktualisiere rohen Text-Buffer
        currentRawText += chunk;
        
        // EINFACH UND PERFORMANT: Normaler Text ohne Glüh-Spans
        const formattedContent = app.formatContent(currentRawText);
        
        // Update HTML mit korrekter Formatierung
        currentTypewriterMessage.innerHTML = formattedContent + '<span class="typewriter-cursor atlas-glow">▌</span>';
        
        // Performance-optimiertes Auto-scroll
        app.throttledScroll();
    }
}

eel.expose(typewriter_end);
function typewriter_end(role) {
    console.log('📝 Typewriter beendet');
    const app = window.atlasApp;
    if (app && currentTypewriterMessage) {
        // Verwende rohen Text-Buffer für finale Formatierung
        const finalFormattedContent = app.formatContent(currentRawText);
        currentTypewriterMessage.innerHTML = finalFormattedContent;
        
        // Cleanup
        currentTypewriterMessage.style.boxShadow = 'none';
        currentTypewriterMessage = null;
        currentRawText = '';
        app.setProcessing(false);
    }
}

// Token-Update-Callback
eel.expose(token_update);
function token_update(data) {
    const app = window.atlasApp;
    if (app) {
        app.updateTokenStats({
            current: data.tokens || 0,
            speed: data.tokens_per_second || 0,
            time: data.elapsed_time || 0
        });
    }
}

// Stream-Complete-Callback
eel.expose(stream_complete);
function stream_complete(data) {
    console.log('🏁 Stream complete:', data);
    const app = window.atlasApp;
    if (app) {
        if (typeof data === 'object') {
            app.updateTokenStats({ 
                current: data.total_tokens || 0,
                session: data.session_tokens || 0 
            });
        }
        app.setProcessing(false);
    }
}

// Stream-Error-Callback
eel.expose(stream_error);
function stream_error(error) {
    console.error('❌ Stream error:', error);
    const app = window.atlasApp;
    if (app) {
        app.addMessageToTerminal({
            role: 'assistant',
            type: 'error',
            content: `❌ Atlas-Fehler: ${error}`
        });
        app.setProcessing(false);
    }
}

// Action-Executed-Callback
eel.expose(action_executed);
function action_executed(data) {
    console.log('⚡ Action executed:', data);
    const app = window.atlasApp;
    if (app) {
        const iconColor = data.success ? '✅' : '❌';
        const messageType = data.success ? 'message' : 'error';
        
        app.addMessageToTerminal({
            role: 'assistant',
            type: messageType,
            content: `${iconColor} <strong>Aktion ausgeführt:</strong> ${data.message}`
        });
        
        // Auto-cleanup nach Aktionen wenn nötig
        if (appState.ui.autoCleanup) {
            setTimeout(() => app.cleanupOldMessages(), 1000);
        }
    }
}

// Context-Update-Callback
eel.expose(update_context_usage);
function update_context_usage(used, total) {
    const app = window.atlasApp;
    if (app) {
        app.updateContextIndicator(used, total);
    }
}

// Context-Rotation-Callbacks
eel.expose(context_rotation_started);
function context_rotation_started() {
    console.log('🔄 Context-Rotation gestartet');
    const app = window.atlasApp;
    if (app) {
        app.showContextRotationIndicator();
    }
}

eel.expose(context_rotation_completed);
function context_rotation_completed(data) {
    console.log('🔄 Context-Rotation abgeschlossen:', data);
    const app = window.atlasApp;
    if (app) {
        app.hideContextRotationIndicator(data);
        
        if (data.success) {
            // Update Context-Anzeige
            app.updateContextIndicator(data.context_percentage || 20, 100);
        }
    }
}

// App initialisieren
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 DOM loaded, initializing Atlas...');
    window.atlasApp = new AtlasApp();
    console.log('✅ Atlas Code bereit - Autonomer Modus aktiv');
    
    // Debug-Info
    console.log('🔍 Debug Info:');
    console.log('- promptInput:', promptInput);
    console.log('- terminalOutput:', terminalOutput);
    console.log('- eel available:', typeof eel !== 'undefined');
});