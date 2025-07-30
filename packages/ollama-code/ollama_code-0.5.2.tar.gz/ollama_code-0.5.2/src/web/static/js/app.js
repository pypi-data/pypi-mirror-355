// CODIAC TERMINAL - Glassmorphism Terminal Interface
// Authentic Terminal Experience with Enhanced Visuals

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
let typewriter_active = false; // FIX: Variable war nicht definiert

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
    },
    viewport: {
        bufferSize: 5,  // Nachrichten außerhalb Viewport vollständig geladen
        lastCheck: 0,
        checkInterval: 1000, // 1s zwischen Viewport-Checks
        visible: new Set(), // Aktuell sichtbare Message-IDs
        observer: null // Intersection Observer
    }
};

// Claude Code Features - ERWEITERT FÜR NEUE MODI
let autoAcceptEdits = false; // Standardmäßig aus
let securityMode = 'safe'; // safe, base, hell-out
let contextUsage = {
    used: 0,
    total: 120000, // ULTRA: 120k Token Limit (devstral:24b 128k Kapazität)
    percentage: 100
};

// TERMINAL TYPEWRITER EFFECTS
function addTerminalGlow(text, container) {
    let charIndex = 0;
    
    function addNextChar() {
        if (charIndex < text.length) {
            const char = text[charIndex];
            const span = document.createElement('span');
            span.className = 'ai-typing-char atlas-glow';
            span.textContent = char;
            container.appendChild(span);
            charIndex++;
            
            // Terminal-like typing speed
            setTimeout(addNextChar, 25); // 25ms für authentisches Terminal-Gefühl
        }
    }
    
    addNextChar();
}

function terminalTypewriter(text, container, callback) {
    container.innerHTML = ''; // Clear terminal line
    let index = 0;
    
    function typeChar() {
        if (index < text.length) {
            const char = text[index];
            const span = document.createElement('span');
            span.className = 'ai-typing-char atlas-glow';
            span.textContent = char;
            container.appendChild(span);
            index++;
            
            // Authentic terminal typing speed
            setTimeout(typeChar, 35); // 35ms für realistisches Terminal-Typing
        } else if (callback) {
            callback();
        }
    }
    
    typeChar();
}

// Glüh-Effekt State
let lastGlowTime = 0;

// COMMAND-SYSTEM CALLBACKS
eel.expose(update_system_status);
function update_system_status() {
    // System-Status aktualisieren
    console.log("🔄 System-Status wird aktualisiert");
    // TODO: Status-Display implementieren
}

eel.expose(clear_chat_display);
function clear_chat_display() {
    // Chat-Display leeren
    if (terminalOutput) {
        terminalOutput.innerHTML = '';
    }
    console.log("🧹 Chat-Display geleert");
}

// TOKEN-UPDATE CALLBACKS - VERBESSERT MIT FEHLERBEHANDLUNG
eel.expose(token_update);
function token_update(data) {
    try {
        if (!data || typeof data !== 'object') {
            console.warn('⚠️ Ungültige Token-Daten erhalten:', data);
            return false;
        }
        
        // Live-Tokens (aktuelle Nachricht)
        if (data.tokens !== undefined && data.tokens >= 0) {
            tokenStats.current = data.tokens;
        }
        if (data.tokens_per_second !== undefined && data.tokens_per_second >= 0) {
            tokenStats.speed = data.tokens_per_second;
        }
        
        // Display über AtlasApp aktualisieren (falls verfügbar)
        const app = window.atlasApp;
        if (app && typeof app.updateTokenDisplay === 'function') {
            app.updateTokenDisplay();
        } else {
            // Fallback direkte Update mit Formatierung
            if (currentTokensSpan) currentTokensSpan.textContent = formatTokens(tokenStats.current || 0);
            if (sessionTokensSpan) sessionTokensSpan.textContent = formatTokens(tokenStats.session || 0);
            if (tokenSpeedSpan) tokenSpeedSpan.textContent = (tokenStats.speed || 0).toFixed(1);
        }
        
        return true; // Erfolg an Backend signalisieren
    } catch (error) {
        console.error('❌ Token-Update-Fehler:', error);
        return false; // Fehler an Backend signalisieren
    }
}

// SESSION-TOKEN-UPDATE - KORREKTE LIVE/TOTAL LOGIK
eel.expose(session_token_update);
function session_token_update(total_session_tokens) {
    try {
        // KORREKTE AKKUMULATION: Live-Tokens zu Session-Tokens addieren
        const previousSession = tokenStats.session || 0;
        const currentLive = tokenStats.current || 0;
        
        // Addiere Live-Tokens zu Session-Tokens (akkumulierend)
        tokenStats.session = previousSession + currentLive;
        
        console.log(`📊 Token-Akkumulation: Live=${formatTokens(currentLive)} + Session=${formatTokens(previousSession)} = Total=${formatTokens(tokenStats.session)}`);
        
        // WICHTIG: Live-Tokens NICHT resetten! 
        // Live zeigt finalen Token-Count der letzten KI-Nachricht
        // Live wird erst beim START der nächsten User-Nachricht auf 0 gesetzt
        
        // Reset Token-Speed (Stream beendet)
        tokenStats.speed = 0;
        
        // Display aktualisieren über AtlasApp (bevorzugt) oder direkt
        const app = window.atlasApp;
        if (app && typeof app.updateTokenDisplay === 'function') {
            app.updateTokenDisplay();
        } else {
            // Fallback direkte Update
            if (sessionTokensSpan) sessionTokensSpan.textContent = formatTokens(tokenStats.session);
            if (currentTokensSpan) currentTokensSpan.textContent = formatTokens(tokenStats.current);
            if (tokenSpeedSpan) tokenSpeedSpan.textContent = '0.0';
        }
        
        return true; // Erfolg an Backend signalisieren
    } catch (error) {
        console.error('❌ Session-Token-Update-Fehler:', error);
        return false;
    }
}

// Token-Tracking mit persistenter Session-Summe
let tokenStats = {
    current: 0,        // Live-Tokens der aktuellen Nachricht
    session: 0,        // Gesamte Session-Tokens (persistent)
    speed: 0,         // Tokens pro Sekunde
    time: 0          // Zeit
};

// Hilfsfunktion für k-Format (erweitert für 120k Context)
function formatTokens(tokens) {
    if (tokens >= 1000000) {
        return (tokens / 1000000).toFixed(1) + 'M';
    } else if (tokens >= 100000) {
        return (tokens / 1000).toFixed(0) + 'k'; // 120k statt 120.0k
    } else if (tokens >= 10000) {
        return (tokens / 1000).toFixed(1) + 'k';
    } else if (tokens >= 1000) {
        return (tokens / 1000).toFixed(1) + 'k';
    }
    return tokens.toString();
}

class AtlasApp {
    constructor() {
        this.initializeApp();
        this.setupEventListeners();
        this.loadSystemInfo();
        this.startTimer();
    }
    
    initializeApp() {
        console.log('🚀 CODIAC TERMINAL initialized');
        this.updateStatus('Codiac bereit', 'ready');
        
        // Terminal-Container mit Glassmorphism optimieren
        if (terminalOutput) {
            terminalOutput.classList.add('scroll-optimized');
            // Terminal prompt hinzufügen
            this.addTerminalPrompt();
        }
        
        // Terminal-Effekte initialisieren
        this.initTerminalEffects();
        
        // VIEWPORT FRUSTUM CULLING initialisieren
        this.initViewportManager();
    }
    
    addTerminalPrompt() {
        // Ersten Terminal-Prompt hinzufügen
        const welcomeMsg = document.createElement('div');
        welcomeMsg.className = 'terminal-message role-computer';
        welcomeMsg.innerHTML = 'CODIAC TERMINAL v0.5.2 - Autonomous AI Development Assistant<br/>Type your message to begin...';
        terminalOutput.appendChild(welcomeMsg);
    }
    
    initTerminalEffects() {
        // Glassmorphism-Effekte für alle relevanten Elemente
        const glassmorphElements = [
            document.getElementById('terminal-container'),
            document.getElementById('prompt-input'),
            document.getElementById('status-bar'),
            document.getElementById('codiac-status')
        ];
        
        glassmorphElements.forEach(element => {
            if (element) {
                element.style.willChange = 'backdrop-filter, background';
                element.style.backfaceVisibility = 'hidden';
            }
        });
    }
    
    initViewportManager() {
        console.log('👁️ Initialisiere Viewport-Manager...');
        
        // Intersection Observer für Frustum Culling
        appState.viewport.observer = new IntersectionObserver((entries) => {
            const now = performance.now();
            
            // Throttle Viewport-Updates
            if (now - appState.viewport.lastCheck < appState.viewport.checkInterval) {
                return;
            }
            appState.viewport.lastCheck = now;
            
            let visibilityChanged = false;
            
            entries.forEach(entry => {
                const messageId = entry.target.dataset.messageId;
                if (!messageId) return;
                
                if (entry.isIntersecting) {
                    if (!appState.viewport.visible.has(messageId)) {
                        appState.viewport.visible.add(messageId);
                        visibilityChanged = true;
                        this.ensureMessageFullyLoaded(entry.target);
                    }
                } else {
                    if (appState.viewport.visible.has(messageId)) {
                        appState.viewport.visible.delete(messageId);
                        visibilityChanged = true;
                        this.scheduleMessageCompression(entry.target);
                    }
                }
            });
            
            if (visibilityChanged) {
                this.updateViewportPriorities();
            }
        }, {
            root: terminalOutput,
            rootMargin: `${appState.viewport.bufferSize * 100}px 0px`, // Buffer-Zone
            threshold: [0, 0.1, 0.5, 0.9, 1.0] // Mehrere Threshold für smooth Updates
        });
        
        console.log('✅ Viewport-Manager aktiv');
    }
    
    ensureMessageFullyLoaded(messageElement) {
        // Stelle sicher dass Message vollständig geladen ist
        if (messageElement.classList.contains('compressed')) {
            console.log('🔄 Lade komprimierte Message vollständig...');
            this.expandMessage(messageElement.dataset.messageId, messageElement);
        }
    }
    
    scheduleMessageCompression(messageElement) {
        // Plane Komprimierung für Message außerhalb Viewport
        const messageId = messageElement.dataset.messageId;
        
        setTimeout(() => {
            // Prüfe ob Message immer noch außerhalb Viewport
            if (!appState.viewport.visible.has(messageId)) {
                console.log('🗜️ Komprimiere Message außerhalb Viewport...');
                this.compressMessage(messageElement);
            }
        }, 2000); // 2s Verzögerung
    }
    
    compressMessage(messageElement) {
        const fullContent = messageElement.innerHTML;
        const messageId = messageElement.dataset.messageId || this.generateMessageId();
        
        // Speichere Vollinhalt
        this.saveMessageToCache(messageId, fullContent);
        
        // Erstelle komprimierte Version
        const preview = this.extractPreviewText(fullContent);
        messageElement.innerHTML = `
            <div class="message-compressed" data-full-cached="true">
                <span class="compress-indicator">📄</span>
                <span class="compress-preview">${preview}</span>
            </div>
        `;
        messageElement.classList.add('compressed');
        messageElement.dataset.messageId = messageId;
    }
    
    generateMessageId() {
        return 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    async updateViewportPriorities() {
        // Sende sichtbare Message-IDs an Backend
        const visibleIds = Array.from(appState.viewport.visible);
        
        try {
            await eel.update_viewport_priorities(visibleIds)();
            console.log(`👁️ Viewport-Prioritäten aktualisiert: ${visibleIds.length} sichtbar`);
        } catch (error) {
            console.warn('⚠️ Viewport-Update-Fehler:', error);
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
        // Sichere Referenz auf das Input-Element
        const inputElement = document.getElementById('prompt-input');
        if (!inputElement) return;
        
        const message = inputElement.value.trim();
        if (!message || isProcessing) return;
        
        console.log('🔥 DEBUG: sendMessage gestartet');
        console.log('🔥 DEBUG: Message:', message);
        console.log('🔥 DEBUG: isProcessing:', isProcessing);
        
        // RESET Live-Tokens für neue Nachricht (vorherige KI-Antwort ist abgeschlossen)
        tokenStats.current = 0;
        tokenStats.speed = 0;
        this.updateTokenDisplay();
        console.log('🔄 Live-Tokens für neue Nachricht zurückgesetzt');
        
        // SOFORT Input leeren
        inputElement.value = '';
        
        // Benutzer-Nachricht anzeigen
        this.addMessageToTerminal({
            role: 'user',
            type: 'message',
            content: message
        });
        
        this.setProcessing(true);
        
        try {
            // Direkt an Atlas senden - IMMER mit Typewriter
            console.log('🔥 DEBUG: Rufe eel.atlas_chat auf...');
            console.log('🔥 DEBUG: eel object:', typeof eel, eel);
            
            const result = await eel.atlas_chat(message)();
            console.log('🔥 DEBUG: atlas_chat Result:', result);
        } catch (error) {
            console.error('🔥 DEBUG: Atlas-Fehler Details:', error);
            console.error('🔥 DEBUG: Error stack:', error.stack);
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
    
    // Auto-scroll nur während Typewriter aktiv ist
    throttledScroll() {
        if (terminalOutput && (typewriter_active || currentTypewriterMessage)) {
            terminalOutput.scrollTop = terminalOutput.scrollHeight;
        }
    }
    
    // AGGRESSIVE DOM-Cleanup für bessere Performance
    cleanupOldMessages() {
        const messages = terminalOutput.children;
        const maxMessages = 500; // Reduziert für bessere Performance
        
        if (messages.length > maxMessages) {
            const removeCount = messages.length - maxMessages;
            
            // BATCH-REMOVAL für bessere Performance
            const toRemove = [];
            for (let i = 0; i < removeCount; i++) {
                if (messages[i]) {
                    toRemove.push(messages[i]);
                }
            }
            
            // Entferne alle auf einmal
            requestAnimationFrame(() => {
                toRemove.forEach(msg => {
                    // Cleanup alle Animationen vor dem Entfernen
                    const spans = msg.querySelectorAll('.ai-typing-char');
                    spans.forEach(span => {
                        span.style.willChange = 'auto'; // GPU-Layer freigeben
                        span.style.animation = 'none';
                    });
                    msg.remove();
                });
                console.log(`🧹 DOM cleanup: ${removeCount} alte Nachrichten entfernt`);
                
                // Garbage Collection forcieren (falls verfügbar)
                if (window.gc) {
                    window.gc();
                }
            });
        }
    }
    
    formatContent(content) {
        if (!content) return '';
        
        // Code-Blöcke mit Copy-Button formatieren
        content = content.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
            const trimmedCode = code.trim();
            const langClass = lang ? ` class="language-${lang}"` : '';
            return `<div class="code-block">
                <div class="code-header">
                    <span class="code-lang">${lang || 'Code'}</span>
                    <button class="copy-btn" onclick="navigator.clipboard.writeText(\`${this.escapeForJS(trimmedCode)}\`).then(() => {this.textContent='✓ Kopiert'; setTimeout(() => this.textContent='📋 Kopieren', 1000)})">📋 Kopieren</button>
                </div>
                <pre><code${langClass}>${this.escapeHtml(trimmedCode)}</code></pre>
            </div>`;
        });
        
        // Inline-Code formatieren
        content = content.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Zeilenumbrüche erhalten
        content = content.replace(/\n/g, '<br>');
        
        return content;
    }
    
    escapeForJS(text) {
        return text.replace(/\\/g, '\\\\').replace(/`/g, '\\`').replace(/\$/g, '\\$');
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
        try {
            // Live-Tokens (grün) - aktuelle Nachricht
            if (currentTokensSpan) {
                const liveTokens = Math.max(0, tokenStats.current || 0);
                currentTokensSpan.textContent = formatTokens(liveTokens);
                currentTokensSpan.style.color = '#10b981'; // Grün für Live
            }
            
            // Session-Tokens (blau) - gesamte Session
            if (sessionTokensSpan) {
                const sessionTokens = Math.max(0, tokenStats.session || 0);
                sessionTokensSpan.textContent = formatTokens(sessionTokens);
                sessionTokensSpan.style.color = '#3b82f6'; // Blau für Total
            }
            
            // Token-Speed (orange) - aktuelle Geschwindigkeit
            if (tokenSpeedSpan) {
                const speed = Math.max(0, tokenStats.speed || 0);
                tokenSpeedSpan.textContent = speed.toFixed(1);
                tokenSpeedSpan.style.color = '#f59e0b'; // Orange für Speed
            }
        } catch (error) {
            console.error('❌ Token-Display-Update-Fehler:', error);
        }
    }
    
    async loadSystemInfo() {
        try {
            const info = await eel.get_system_info()();
            
            // Echte Sicherheitsmodi anzeigen
            const securityDisplay = info.security_display || '🔒 Safe Mode (Simulation)';
            if (workingDirSpan) {
                workingDirSpan.textContent = securityDisplay;
                
                // Farben basierend auf Sicherheitsmodus
                if (info.security_mode === 'safe') {
                    workingDirSpan.style.color = '#10b981'; // Grün für Safe
                } else if (info.security_mode === 'base') {
                    workingDirSpan.style.color = '#F39C12'; // Orange für Base
                } else if (info.security_mode === 'hell-out') {
                    workingDirSpan.style.color = '#dc2626'; // Rot für Hell-out
                }
            }
            
            // Debug-Info in Konsole
            console.log('🔒 Security Info:', {
                mode: info.security_mode,
                file_access: info.file_access,
                terminal_access: info.terminal_access,
                allowed_paths: info.allowed_paths,
                operations: info.file_operations
            });
            
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
                content: '🚨 NOTSTOP: Entlade devstral:24b Modell...'
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
        contextUsage.total = total || 120000; // ULTRA: 120k Token Limit (devstral:24b)
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
    
    // NEUE MESSAGE-COLLAPSE-FUNKTIONALITÄT
    async startMessageCollapse(data) {
        console.log('📦 Starte Message-Collapse...');
        
        // Zeige Collapse-Indikator
        this.addMessageToTerminal({
            role: 'assistant',
            type: 'message',
            content: `📦 **Context optimieren...** (${data.context_usage}/${data.max_context} Tokens)`
        });
        
        // Sammle alle Nachrichten zum Kollabieren
        const messages = Array.from(terminalOutput.querySelectorAll('.chat-message'));
        const messagesToCollapse = messages.slice(0, -5); // Behalte letzte 5 sichtbar
        
        let collapsedCount = 0;
        
        for (const message of messagesToCollapse) {
            await this.collapseMessage(message);
            collapsedCount++;
        }
        
        this.addMessageToTerminal({
            role: 'assistant',
            type: 'message',
            content: `✅ **${collapsedCount} Nachrichten komprimiert** - Zum Aufklappen anklicken`
        });
        
        // Update Context-Anzeige
        this.updateContextIndicator(20, 100); // Viel freier Context
    }
    
    async collapseMessage(messageElement) {
        const fullContent = messageElement.innerHTML;
        const messageId = 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        
        // Speichere Vollinhalt in lokalen Cache (später DB)
        await this.saveMessageToCache(messageId, fullContent);
        
        // Erstelle kollabierte Version
        const previewText = this.extractPreviewText(fullContent);
        const collapsedHTML = `
            <div class="message-collapsed" data-message-id="${messageId}" onclick="window.atlasApp.expandMessage('${messageId}', this)">
                <span class="collapse-indicator">📁</span>
                <span class="collapse-preview">${previewText}</span>
                <span class="collapse-hint">Klicken zum Aufklappen</span>
            </div>
        `;
        
        // Ersetze Nachricht durch kollabierte Version
        messageElement.innerHTML = collapsedHTML;
        messageElement.classList.add('collapsed');
    }
    
    extractPreviewText(html) {
        // Extrahiere ersten Satz als Preview
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        const text = tempDiv.textContent || tempDiv.innerText || '';
        const firstSentence = text.split(/[.!?]/)[0];
        return firstSentence.substring(0, 80) + (firstSentence.length > 80 ? '...' : '');
    }
    
    async saveMessageToCache(messageId, content) {
        // TODO: Später echte DB-Integration
        // Für jetzt: localStorage als Cache
        try {
            const cacheKey = `message_cache_${messageId}`;
            localStorage.setItem(cacheKey, content);
            console.log(`💾 Message ${messageId} cached`);
        } catch (error) {
            console.error('❌ Cache-Fehler:', error);
        }
    }
    
    async expandMessage(messageId, element) {
        console.log(`📂 Expandiere Message: ${messageId}`);
        
        try {
            // Lade aus Cache
            const cacheKey = `message_cache_${messageId}`;
            const fullContent = localStorage.getItem(cacheKey);
            
            if (fullContent) {
                // Ersetze kollabierte Version durch Vollinhalt
                const messageElement = element.closest('.chat-message');
                messageElement.innerHTML = fullContent;
                messageElement.classList.remove('collapsed');
                
                console.log(`✅ Message ${messageId} expandiert`);
            } else {
                throw new Error('Cache nicht gefunden');
            }
        } catch (error) {
            console.error('❌ Expand-Fehler:', error);
            element.innerHTML = '<span style="color: red;">❌ Fehler beim Laden</span>';
        }
    }
}

// Atlas Typewriter-Callbacks
eel.expose(typewriter_start);
function typewriter_start(role) {
    console.log('🔥 DEBUG: Typewriter gestartet');
    typewriter_active = true; // FIX: Global setzen
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
        console.log('🔥 DEBUG: typewriter_chunk:', chunk);
        
        // TOOL-UPDATE DETECTION - Claude Code Style
        if (chunk.startsWith('● ')) {
            const toolDiv = document.createElement('div');
            toolDiv.className = chunk.includes('❌') ? 'tool-update tool-error' : 'tool-update tool-success';
            toolDiv.innerHTML = chunk.replace(/\n/g, '<br>');
            
            // Tool-Update direkt hinzufügen ohne Typewriter-Effekt
            const cursor = currentTypewriterMessage.querySelector('.typewriter-cursor');
            if (cursor) {
                cursor.parentNode.insertBefore(toolDiv, cursor);
            } else {
                currentTypewriterMessage.appendChild(toolDiv);
            }
            
            app.throttledScroll();
            return; // Skip normal typewriter for tool updates
        }
        
        // Aktualisiere rohen Text-Buffer
        currentRawText += chunk;
        
        // EINFACHER ANSATZ: Erstelle DOM-Elemente für neue Buchstaben
        const cursor = currentTypewriterMessage.querySelector('.typewriter-cursor');
        
        // PERFORMANCE-OPTIMIERT: Batch DOM-Updates
        const fragment = document.createDocumentFragment();
        const spans = [];
        
        // Erstelle alle Spans in einem Fragment (weniger DOM-Updates)
        chunk.split('').forEach(char => {
            const span = document.createElement('span');
            span.className = 'ai-typing-char';
            span.textContent = char;
            
            // FORCIERE SOFORTIGE ANIMATION mit GPU-Optimierung
            span.style.color = '#FF4500';
            span.style.textShadow = '0 0 3px #FF4500, 0 0 6px #FF6500';
            span.style.willChange = 'color, text-shadow, filter';
            span.style.transform = 'translateZ(0)'; // GPU-Layer
            
            fragment.appendChild(span);
            spans.push(span);
        });
        
        // SINGLE DOM-UPDATE statt vieler einzelner
        if (cursor) {
            cursor.parentNode.insertBefore(fragment, cursor);
        } else {
            currentTypewriterMessage.appendChild(fragment);
        }
        
        // Starte alle Animationen in einem requestAnimationFrame (GPU-optimiert)
        requestAnimationFrame(() => {
            spans.forEach(span => {
                span.style.animation = 'fire-glow-fade 0.3s ease-out forwards';
                
                // AGGRESSIVE CLEANUP: Entferne Span-Wrapper nach Animation
                setTimeout(() => {
                    if (span.parentNode) {
                        // Ersetze Span durch reinen Textnode (viel performanter)
                        const textNode = document.createTextNode(span.textContent);
                        span.parentNode.replaceChild(textNode, span);
                    }
                }, 350); // 50ms nach Animation-Ende
            });
        });
        
        // Performance-optimiertes Auto-scroll
        app.throttledScroll();
        
        // PROAKTIVES CLEANUP: Entferne alte Spans während des Tippens
        const allSpans = currentTypewriterMessage.querySelectorAll('.ai-typing-char');
        if (allSpans.length > 1000) { // Bei mehr als 1000 Spans
            // Ersetze die ersten 500 durch Textnodes
            for (let i = 0; i < 500; i++) {
                const span = allSpans[i];
                if (span && span.parentNode) {
                    const textNode = document.createTextNode(span.textContent);
                    span.parentNode.replaceChild(textNode, span);
                }
            }
            console.log('🧹 Proaktives Span-Cleanup: 500 Spans zu Textnodes konvertiert');
        }
    }
}

eel.expose(typewriter_end);
function typewriter_end(role) {
    console.log('🔥 DEBUG: Typewriter beendet');
    typewriter_active = false; // FIX: Global setzen
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

// ENTFERNT: Doppelte token_update Funktion (bereits bei Zeile 129 definiert)

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
        
        // RESET Token-Speed nach Stream-Ende
        tokenStats.speed = 0;
        app.updateTokenDisplay();
        
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

// Working Directory Update Callback
eel.expose(update_working_directory);
function update_working_directory(path_text) {
    const workingDirElement = document.getElementById('working-dir');
    if (workingDirElement) {
        workingDirElement.textContent = path_text;
    }
}

// Codiac Status Update System
const CodiacStatus = {
    // Task-spezifische Emojis und Texte
    states: {
        ready: { emoji: '🔥', text: 'Codiac bereit' },
        thinking: { emoji: '🤔', text: 'Codiac denkt...' },
        working: { emoji: '⚙️', text: 'Codiac arbeitet...' },
        reading: { emoji: '📖', text: 'Datei lesen...' },
        writing: { emoji: '✍️', text: 'Datei schreiben...' },
        editing: { emoji: '📝', text: 'Code bearbeiten...' },
        executing: { emoji: '⚡', text: 'Befehl ausführen...' },
        searching: { emoji: '🔍', text: 'Dateien durchsuchen...' },
        listing: { emoji: '📂', text: 'Verzeichnis auflisten...' },
        error: { emoji: '❌', text: 'Fehler aufgetreten' },
        completed: { emoji: '✅', text: 'Aufgabe abgeschlossen' }
    },
    
    currentState: 'ready',
    
    update: function(state, customText = null) {
        if (!this.states[state]) {
            console.warn(`Unbekannter Status: ${state}`);
            return;
        }
        
        this.currentState = state;
        const statusElement = document.getElementById('codiac-status');
        const emojiElement = document.getElementById('status-emoji');
        const textElement = document.getElementById('status-text');
        
        if (!statusElement || !emojiElement || !textElement) return;
        
        // Entferne alle Status-Klassen
        statusElement.className = '';
        
        // Füge neue Status-Klasse hinzu
        statusElement.classList.add(state);
        
        // Update Emoji und Text
        const stateConfig = this.states[state];
        emojiElement.textContent = stateConfig.emoji;
        textElement.textContent = customText || stateConfig.text;
        
        console.log(`🎯 Codiac Status: ${state} - ${textElement.textContent}`);
    },
    
    // Automatisches Zurücksetzen nach Delay
    setTemporary: function(state, customText = null, duration = 3000) {
        this.update(state, customText);
        
        setTimeout(() => {
            if (this.currentState === state) {
                this.update('ready');
            }
        }, duration);
    }
};

// Expose Codiac Status für Backend
eel.expose(update_codiac_status);
function update_codiac_status(state, text = null, temporary = false, duration = 3000) {
    if (temporary) {
        CodiacStatus.setTemporary(state, text, duration);
    } else {
        CodiacStatus.update(state, text);
    }
}

// Initialisiere Status
document.addEventListener('DOMContentLoaded', function() {
    CodiacStatus.update('ready');
});

// Context-Update-Callback
eel.expose(update_context_usage);
function update_context_usage(used, total) {
    try {
        console.log(`🧠 Context-Update: ${used}/${total} Tokens`);
        const app = window.atlasApp;
        if (app && app.updateContextIndicator) {
            app.updateContextIndicator(used, total);
        }
        return true; // Expliziter Return-Wert für Eel
    } catch (error) {
        console.error('❌ Context-Update-Fehler:', error);
        return false;
    }
}

// Message-Collapse-System (ersetzt Context-Rotation)
eel.expose(start_message_collapse);
function start_message_collapse(data) {
    console.log('📦 Message-Collapse gestartet:', data);
    const app = window.atlasApp;
    if (app) {
        app.startMessageCollapse(data);
    }
}

// Legacy Context-Rotation-Callbacks (für Kompatibilität)
eel.expose(context_rotation_started);
function context_rotation_started() {
    console.log('🔄 Context-Rotation gestartet (Legacy)');
}

eel.expose(context_rotation_completed);
function context_rotation_completed(data) {
    console.log('🔄 Context-Rotation abgeschlossen (Legacy):', data);
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