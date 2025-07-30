# 🔥 Atlas Code

**Autonomer KI-Entwicklungsassistent mit lokalem Ollama-Backend**

Atlas ist ein intelligenter, autonomer KI-Agent, der Aufgaben vollständig und selbstständig ausführt - genau wie Claude Code, aber mit lokalen Ollama-Modellen.

---

## ✨ **Was ist Atlas?**

Atlas Code ist ein minimalistisches Terminal-Interface mit einem hochintelligenten KI-Agenten, der:

- **🤖 Autonom arbeitet** - Führt Aufgaben vollständig aus ohne weitere Nachfragen
- **🖋️ Live-Typewriter** - Elegante Echtzeit-Textausgabe mit Cursor-Animation
- **🚀 Performance-optimiert** - Conversation-Caching für längere Gespräche
- **🔒 Sicher** - Sandbox-Modus standardmäßig aktiv
- **⚡ Ollama-nativ** - Funktioniert ausschließlich mit lokalen Modellen

---

## 🎯 **Hauptfeatures**

### **Autonome Ausführung**
```
Du: "Erstelle eine Python-Funktion für Fibonacci-Zahlen"
Atlas: Analysiert → Schreibt Code → Testet → Optimiert → Fertig!
```

### **Live-Typewriter-Effekt**
- Immer aktiv, kein Umschalten nötig
- Oranges Glühen (Atlas-Farbe: #E67E22)
- Blinkender Cursor ▌ während der Eingabe

### **Smart Performance**
- **Conversation-Caching**: Optimierte Kontextverwaltung
- **Token-Limiting**: Automatisches Kürzen langer Gespräche
- **Live-Metriken**: Tokens/Sekunde, Gesamt-Tokens, Timer

### **Terminal-Ästhetik**
- Glassmorphism-Design aus dem AgentSuite-Projekt
- Kompakte, minimalistische UI
- Responsive für alle Bildschirmgrößen

---

## 🚀 **Quick Start**

### **Voraussetzungen**
```bash
# 1. Ollama installieren
# https://ollama.ai

# 2. Modell herunterladen
ollama pull deepseek-coder-v2:16b

# 3. Ollama starten
ollama serve
```

### **Installation**
```bash
# Dependencies installieren
pip install -r requirements.txt

# Atlas starten
python main.py
```

**Atlas öffnet sich automatisch unter:** `http://localhost:8080`

---

## 💬 **Verwendung**

### **Einfach schreiben und Enter drücken**
```
Nachricht an Atlas eingeben...
```

**Keine Kommandos, keine Modi - einfach natürlich schreiben!**

### **Beispiel-Gespräche**
```
Du: Wie heißt du?
Atlas: Ich bin Atlas, dein Entwicklungsassistent.

Du: Erstelle eine REST API in Python
Atlas: [Schreibt vollständigen Flask-Code mit Endpunkten]

Du: Verbessere die Performance 
Atlas: [Analysiert Code, optimiert, testet Änderungen]
```

### **Shortcuts**
- `Enter` → Nachricht senden
- `ESC` → Verarbeitung abbrechen
- Auto-Scroll zu neuen Nachrichten

---

## 🔧 **Technische Details**

### **Architektur**
```
Atlas Code
├── Backend (Python + Eel)
│   ├── AtlasAgent - Konversations-Management  
│   ├── Ollama-Integration - Streaming + Tokens
│   └── Conversation-Cache - Performance
└── Frontend (Vanilla JS + CSS)
    ├── Terminal-Interface
    ├── Typewriter-Effekt
    └── Live-Token-Tracking
```

### **Performance-Optimierungen**
- **Conversation-Cache**: Begrenzt auf 50 Nachrichten
- **Token-Throttling**: Updates alle 100ms
- **Context-Limiting**: Nur relevante Historie (8 letzte Nachrichten)
- **Memory-Management**: Automatisches Cache-Cleanup

### **Sicherheit**
- **Sandbox-Standard**: Arbeitet in `workspace/` Verzeichnis
- **Kontrollierte Ausführung**: Code wird nur nach Bestätigung ausgeführt
- **Lokale Modelle**: Keine externen API-Calls

---

## ⚙️ **Konfiguration**

### **Modell ändern**
```python
# In main.py
MODEL_NAME = "dein-bevorzugtes-modell"
```

### **Performance tunen**
```python
# Konversationslänge anpassen
MAX_CONVERSATION_LENGTH = 50  # Standard

# Token-Update-Intervall
last_token_update = 0.1  # 100ms (Standard)
```

### **Sandbox deaktivieren**
Atlas kann auf Vollzugriff umgestellt werden, läuft aber standardmäßig sicher im Sandbox-Modus.

---

## 📊 **Token-Metriken**

Die Status-Bar zeigt Live-Metriken:

```
🔥 Atlas bereit | 📁 Sandbox | Live: 42T | Total: 1337T | 15/s | 02:45
```

- **Live**: Tokens der aktuellen Antwort
- **Total**: Session-Gesamt-Tokens  
- **Speed**: Tokens pro Sekunde
- **Timer**: Session-Dauer

---

## 🎨 **Design-Prinzipien**

### **Atlas-Identität**
- **Farbe**: Orange (#E67E22) mit Glüh-Effekt
- **Name**: "Atlas" - kurz, prägnant, stark
- **Verhalten**: Autonom, vollständig, hilfreich

### **Terminal-Authentizität**
- Monospace-Fonts für Code
- Glassmorphism-Effekte
- Minimalistisch und fokussiert
- Keine überflüssigen UI-Elemente

### **Performance-First**
- Kompakte Bundle-Größe (kein Tailwind)
- Optimierte DOM-Struktur
- Effiziente Event-Handling

---

## 🔄 **Unterschiede zu Claude Code**

| Feature | Claude Code | Atlas Code |
|---------|-------------|------------|
| **Backend** | Anthropic API | Lokale Ollama-Modelle |
| **Modelle** | Claude-Familie | Beliebige Ollama-Modelle |
| **UI** | Sidebar + Chat | Terminal-Interface |
| **Identität** | Claude | Atlas |
| **Performance** | Cloud-basiert | Lokal optimiert |
| **Autonomie** | ✅ Vollständig | ✅ Vollständig |

---

## 🛠️ **Erweiterte Features**

### **Conversation-Management**
```python
# Automatisches Context-Management
def build_conversation_context(self, new_message: str) -> str:
    # Intelligente Kontextverkürzung
    # Performance-optimierte Historie
    # Relevanz-basierte Filterung
```

### **Smart Token-Tracking**
```python
def realistic_token_count(text):
    # GPT-ähnliche Tokenisierung
    # Subwort-Unterstützung
    # Deutsche Sprache optimiert
```

### **Live-Updates**
```javascript
// Echtzeit Token-Updates
function token_update(data) {
    // Throttled auf 100ms
    // Smooth UI-Updates
    // Performance-Monitoring
}
```

---

## 🎯 **Roadmap**

- [ ] **Multi-Model-Support**: Wechsel zwischen verschiedenen Ollama-Modellen
- [ ] **Plugin-System**: Erweiterbare Funktionalitäten
- [ ] **Export-Features**: Chat-Verlauf und Code-Snippets exportieren
- [ ] **Themes**: Anpassbare UI-Themes
- [ ] **Mobile-App**: Native Mobile-Version

---

## 🤝 **Entwicklung**

### **Debugging**
```bash
# Backend-Logs
python main.py

# Frontend-Entwicklung  
# Browser DevTools (F12)
```

### **Testing**
```bash
# Ollama-Verbindung testen
curl http://localhost:11434/api/tags

# Modell-Status prüfen
ollama list
```

---

## 📄 **Lizenz**

MIT-Lizenz - Siehe `LICENSE` für Details.

---

## 🙏 **Credits**

- **Ollama** - Lokale LLM-Infrastruktur
- **Eel** - Python-JavaScript-Bridge
- **AgentSuite** - Terminal-Design-Inspiration
- **Claude Code** - Autonomie-Konzept-Inspiration

---

**Atlas Code - Dein autonomer Entwicklungsassistent. Lokal. Intelligent. Vollständig.** 🔥