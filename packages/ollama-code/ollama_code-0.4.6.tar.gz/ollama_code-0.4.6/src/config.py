#!/usr/bin/env python3
"""
Zentrale Konfigurationsdatei für Atlas Code
"""

import os
from pathlib import Path

# Projekt-Root-Verzeichnis
# Annahme: config.py ist in OpenAI_Coder_v0.4.6/src/
PROJECT_DIR = Path(__file__).parent.parent 

# Ollama-Konfiguration
OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "deepseek-coder-v2:16b"

# Sandbox-Konfiguration
SANDBOX_DIR = PROJECT_DIR / "workspace"

# Cache-Konfiguration
CACHE_DIR = PROJECT_DIR / ".atlas_cache"
SESSIONS_DIR = CACHE_DIR / "sessions"
CONTEXT_CACHE_DIR = CACHE_DIR / "context"
MODEL_CACHE_DIR = CACHE_DIR / "models"

# Anwendungs-Konfiguration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_CONVERSATION_LENGTH = 50  # Veraltet, wird durch Session-Manager gesteuert


def setup_directories():
    """
    NEU: Erstellt alle notwendigen Projektverzeichnisse, falls sie nicht existieren.
    Dies verhindert den "unable to open database file" Fehler.
    """
    print("📁 Erstelle benötigte Verzeichnisstruktur...")
    try:
        for path in [CACHE_DIR, SESSIONS_DIR, CONTEXT_CACHE_DIR, MODEL_CACHE_DIR, SANDBOX_DIR]:
            path.mkdir(parents=True, exist_ok=True)
        print("✅ Verzeichnisse erfolgreich erstellt/verifiziert.")
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Verzeichnisse: {e}")
        # Beende das Programm, da es ohne die Ordner nicht laufen kann.
        exit(1)