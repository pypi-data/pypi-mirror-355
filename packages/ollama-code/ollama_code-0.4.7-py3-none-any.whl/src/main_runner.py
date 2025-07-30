#!/usr/bin/env python3
"""
Haupt-Einstiegspunkt für das installierte Paket.
Wird durch den 'openai-coder' Befehl aufgerufen und kann auch direkt
für die Entwicklung aus dem Projekt-Root-Verzeichnis gestartet werden.
"""

import sys
import importlib.resources
from pathlib import Path

# --- KORREKTUR FÜR DIE ENTWICKLUNG ---
# Füge das Projekt-Hauptverzeichnis zum Python-Pfad hinzu.
# Dies stellt sicher, dass "from src import ..." funktioniert, wenn das Skript
# direkt aus dem Projektordner (z.B. mit "python src/main_runner.py") gestartet wird.
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
# --- ENDE DER KORREKTUR ---

import eel
import requests

from src import config
from src.agent.atlas_agent import AtlasAgent
from src.core import caching, session_manager
from src.api import handlers

def check_dependencies():
    """Überprüft die Verbindung zu Ollama und die Modellverfügbarkeit."""
    try:
        response = requests.get(f"{config.OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code != 200:
            print(f"⚠️ Warnung: Ollama nicht erreichbar unter {config.OLLAMA_URL}")
            return False
        
        models = response.json().get("models", [])
        if not any(config.MODEL_NAME in m.get("name", "") for m in models):
            print(f"⚠️ Warnung: Modell '{config.MODEL_NAME}' nicht gefunden.")
            print(f"Installiere es mit: ollama pull {config.MODEL_NAME}")
            return False
        
        print("✅ Ollama-Verbindung und Modell sind verfügbar.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Ollama nicht erreichbar: {e}")
        print("\n🔧 Lösungsvorschläge:")
        print("   1. Starte Ollama: ollama serve")
        print("   2. Prüfe Umgebungsmodus:")
        print("      - Lokal: ollama-code local")
        print("      - VM: ollama-code vm")
        print("      - Netzwerk: ollama-code net")
        print("   3. Host-Konfiguration: ollama-code host")
        print("   4. Verbindungstest: ollama-code --test")
        return False

def main():
    """Initialisiert und startet die gesamte Anwendung."""
    print("🔥 Starte OpenAI Coder v0.4.6...")

    config.setup_directories()
    
    if not check_dependencies():
        print("❗️ Bitte behebe die oben genannten Probleme und starte erneut.")
        print(f"\n📊 Aktuelle Konfiguration:")
        print(f"   Modus: {config.CURRENT_ENVIRONMENT}")
        print(f"   URL: {config.OLLAMA_URL}")
        print(f"   Modell: {config.MODEL_NAME}")
        return

    # 1. Instanzen der Kernkomponenten erstellen
    atlas_agent = AtlasAgent()
    session_manager_instance = session_manager.SessionManager()
    
    # 2. Cache initialisieren oder laden
    if not caching.load_session_cache():
         caching.initialize_cache()
    
    # 3. Referenzen setzen (Dependency Injection)
    handlers.register_handlers(atlas_agent, session_manager_instance)
    session_manager_instance.set_conversation_cache_reference(caching.conversation_cache)
    session_manager_instance.register_session(caching.current_session_id)

    # 4. Hintergrund-Tasks starten
    session_manager_instance.cleanup_old_data()

    # 5. Eel initialisieren und starten
    try:
        # KORREKTUR FÜR PAKETIERUNG: Finde den 'web' Ordner innerhalb des Pakets
        try:
            # Der moderne und korrekte Weg für Python 3.9+
            web_dir_path = str(importlib.resources.files('src') / 'web')
        except AttributeError:
            # Fallback für ältere Python-Versionen
            with importlib.resources.path('src', 'web') as path:
                web_dir_path = str(path)

        print(f"🔎 Web-Verzeichnis gefunden unter: {web_dir_path}")
        eel.init(web_dir_path)

        print(f"📁 Arbeitsverzeichnis: {config.SANDBOX_DIR}")
        print(f"🔒 Sandbox-Modus: {'Aktiv' if atlas_agent.sandbox_mode else 'Deaktiviert'}")
        
        eel.start('index.html', size=(1200, 800), port=8080)
    except (OSError, IOError) as e:
        print(f"❌ Fehler beim Starten von Eel: {e}")
        print("Stelle sicher, dass der Port 8080 frei ist.")
    except Exception as e:
        print(f"❌ Ein unerwarteter Fehler ist aufgetreten: {e}")

if __name__ == "__main__":
    main()