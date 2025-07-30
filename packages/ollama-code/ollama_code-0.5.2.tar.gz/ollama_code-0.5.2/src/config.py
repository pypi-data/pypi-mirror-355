#!/usr/bin/env python3
"""
Zentrale Konfigurationsdatei für CODIAC Code
"""

import os
import platform
import socket
import subprocess
from pathlib import Path

# Projekt-Root-Verzeichnis
PROJECT_DIR = Path(__file__).parent.parent 

# Ollama-Konfiguration
OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "devstral:24b"

def detect_environment():
    """Erkennt die aktuelle Umgebung (Docker, WSL, native Linux/Windows)"""
    env_info = {
        'is_docker': False,
        'is_wsl': False,
        'is_windows': False,
        'is_linux': False,
        'platform': platform.system().lower()
    }
    
    # Docker-Erkennung
    if os.path.exists('/.dockerenv') or os.path.exists('/proc/1/cgroup'):
        try:
            with open('/proc/1/cgroup', 'r') as f:
                if 'docker' in f.read():
                    env_info['is_docker'] = True
        except:
            pass
    
    # WSL-Erkennung
    if os.path.exists('/proc/version'):
        try:
            with open('/proc/version', 'r') as f:
                content = f.read().lower()
                if 'microsoft' in content or 'wsl' in content:
                    env_info['is_wsl'] = True
        except:
            pass
    
    # Platform-spezifische Erkennung
    if env_info['platform'] == 'windows':
        env_info['is_windows'] = True
    elif env_info['platform'] == 'linux':
        env_info['is_linux'] = True
    
    return env_info

def get_host_candidates():
    """Gibt eine Liste möglicher Host-Adressen basierend auf der Umgebung zurück"""
    env = detect_environment()
    candidates = []
    
    if env['is_docker']:
        # Docker-Umgebung: host.docker.internal und Gateway-IPs
        candidates.extend([
            "host.docker.internal",
            "172.17.0.1",      # Docker default bridge
            "172.18.0.1",      # Docker custom bridge
            "192.168.65.2",    # Docker Desktop Windows/Mac
            "10.0.2.2",        # VirtualBox NAT
        ])
    
    if env['is_wsl']:
        # WSL-Umgebung: Host-IP dynamisch ermitteln
        try:
            # Versuche WSL-spezifische IP-Ermittlung
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                wsl_ip = result.stdout.strip().split()[0]
                ip_parts = wsl_ip.split('.')
                if len(ip_parts) == 4:
                    # Gateway ist normalerweise .1 im selben Subnet
                    gateway_ip = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.1"
                    candidates.append(gateway_ip)
        except:
            pass
        
        # WSL-typische IPs
        candidates.extend([
            "172.16.0.1",      # Häufige WSL2-Range
            "172.20.0.1",      # Alternative WSL2-Range
            "172.24.0.1",      # Alternative WSL2-Range
            "10.0.75.1",       # WSL1-Range
            "192.168.1.1",     # Lokales Netzwerk Gateway
        ])
    
    if env['is_linux'] and not env['is_wsl'] and not env['is_docker']:
        # Native Linux: lokale und Netzwerk-IPs
        try:
            # Versuche Default-Gateway zu finden
            result = subprocess.run(['ip', 'route', 'show', 'default'], capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                # Extrahiere Gateway-IP aus "default via X.X.X.X"
                parts = result.stdout.split()
                if len(parts) >= 3 and parts[1] == 'via':
                    candidates.append(parts[2])
        except:
            pass
        
        candidates.extend([
            "192.168.1.1",     # Typisches Home-Gateway
            "192.168.0.1",     # Alternative Home-Gateway
            "10.0.0.1",        # Enterprise-Gateway
        ])
    
    if env['is_windows']:
        # Windows: lokale IPs und VM-Gateways
        candidates.extend([
            "192.168.1.1",     # Home-Router
            "192.168.0.1",     # Alternative
            "10.0.0.1",        # Enterprise
            "172.16.0.1",      # VM-Gateway
        ])
    
    # Universelle Fallbacks (immer hinzufügen)
    candidates.extend([
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
    ])
    
    # Entferne Duplikate und behalte Reihenfolge
    seen = set()
    unique_candidates = []
    for candidate in candidates:
        if candidate not in seen:
            seen.add(candidate)
            unique_candidates.append(candidate)
    
    return unique_candidates

def find_working_host(port=11434, timeout=2):
    """Findet einen funktionierenden Host durch Testen aller Kandidaten"""
    candidates = get_host_candidates()
    
    print(f"🔍 Teste {len(candidates)} mögliche Host-Adressen...")
    
    for i, host in enumerate(candidates, 1):
        try:
            print(f"   {i:2d}. Teste {host}:{port}...", end=" ")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                print("✅ Erfolg!")
                return host
            else:
                print("❌")
        except Exception as e:
            print(f"❌ ({str(e)[:30]})")
            continue
    
    print("⚠️ Kein funktionierender Host gefunden, verwende localhost als Fallback.")
    return "localhost"

# Cache für Host-Erkennung (wird nur bei Bedarf neu berechnet)
_CACHED_HOST = None
_CACHE_TIMESTAMP = 0

def get_dynamic_host(force_refresh=False):
    """Ermittelt den Host dynamisch zur Laufzeit mit Caching"""
    global _CACHED_HOST, _CACHE_TIMESTAMP
    import time
    
    # Cache 5 Minuten gültig, außer force_refresh=True
    current_time = time.time()
    cache_valid = (current_time - _CACHE_TIMESTAMP) < 300  # 5 Minuten
    
    if not force_refresh and cache_valid and _CACHED_HOST:
        return _CACHED_HOST
    
    # Host-Erkennung durchführen
    detected_host = find_working_host()
    
    # Cache aktualisieren
    _CACHED_HOST = detected_host
    _CACHE_TIMESTAMP = current_time
    
    return detected_host

# Statische Konfiguration (wird zur Laufzeit überschrieben)
ENVIRONMENT_MODES = {
    "local": {
        "url": "http://localhost:11434",
        "description": "Lokales System - Ollama läuft direkt auf dem Host"
    },
    "vm": {
        "url": "http://localhost:11434",  # Wird zur Laufzeit dynamisch ersetzt
        "description": "Virtuelle Maschine - Ollama läuft auf dem Host-System (Auto-detected)"
    },
    "net": {
        "url": "http://192.168.1.100:11434",
        "description": "Netzwerk - Ollama läuft auf einem anderen Rechner im Netzwerk" 
    }
}

# Standard-Umgebung
CURRENT_ENVIRONMENT = "local"

# Sandbox-Konfiguration
SANDBOX_DIR = PROJECT_DIR / "workspace"

# Cache-Konfiguration
CACHE_DIR = PROJECT_DIR / ".codiac_cache"
SESSIONS_DIR = CACHE_DIR / "sessions"
CONTEXT_CACHE_DIR = CACHE_DIR / "context"
MODEL_CACHE_DIR = CACHE_DIR / "models"

# Anwendungs-Konfiguration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_CONVERSATION_LENGTH = 50  # Veraltet, wird durch Session-Manager gesteuert

# Context-Management für devstral:24b - ULTRA CONTEXT 128k
MAX_CONTEXT_TOKENS = 120000  # 120k Token Limit (devstral:24b hat 128k nativ)
CONTEXT_ROTATION_THRESHOLD = 0.98  # Bei 98% = 117600 Tokens Optimierung

# Sicherheitsmodi
SECURITY_MODES = {
    "safe": {
        "name": "Sandbox Mode",
        "description": "Simulierte Entwicklungsumgebung - keine echten Systemzugriffe",
        "file_access": False,
        "directory_access": False,
        "terminal_access": False,
        "system_access": False,
        "auto_accept_default": False,
        "allowed_paths": [],
        "simulation_mode": True
    },
    "base": {
        "name": "Base Mode", 
        "description": "Aktueller Pfad + Unterordner - Dateien lesen/schreiben, keine Löschung",
        "file_access": True,
        "directory_access": "current_and_subdirs",
        "terminal_access": True,
        "system_access": False,
        "auto_accept_default": False,
        "file_operations": ["read", "write", "edit"],
        "allowed_paths": "current_working_directory"
    },
    "hell-out": {
        "name": "Let The Hell Out Mode",
        "description": "Vollzugriff auf gesamtes System - GEFÄHRLICH!",
        "file_access": True,
        "directory_access": "system_wide", 
        "terminal_access": True,
        "system_access": True,
        "auto_accept_default": False,
        "file_operations": ["read", "write", "edit", "delete"],
        "allowed_paths": "system_wide"
    }
}

# Aktueller Sicherheitsmodus
CURRENT_SECURITY_MODE = "safe"
AUTO_ACCEPT_ENABLED = False


def set_environment_mode(mode: str):
    """Setzt den Umgebungsmodus und aktualisiert die Ollama-URL DYNAMISCH"""
    global OLLAMA_URL, CURRENT_ENVIRONMENT
    
    if mode not in ENVIRONMENT_MODES:
        available_modes = ", ".join(ENVIRONMENT_MODES.keys())
        raise ValueError(f"Unbekannter Modus '{mode}'. Verfügbare Modi: {available_modes}")
    
    CURRENT_ENVIRONMENT = mode
    
    # DYNAMISCHE URL-GENERIERUNG JE NACH MODUS
    if mode == "local":
        OLLAMA_URL = "http://localhost:11434"
    elif mode == "vm":
        # ECHTE DYNAMISCHE HOST-ERKENNUNG ZUR LAUFZEIT!
        print("🔍 Führe Host-Erkennung durch...")
        detected_host = get_dynamic_host()
        OLLAMA_URL = f"http://{detected_host}:11434"
        print(f"✅ Host erkannt: {detected_host}")
    elif mode == "net":
        OLLAMA_URL = ENVIRONMENT_MODES["net"]["url"]
    
    print(f"🔄 Umgebungsmodus auf '{mode}' gesetzt: {OLLAMA_URL}")

def get_current_environment_info():
    """Gibt Informationen zum aktuellen Umgebungsmodus zurück"""
    return {
        "mode": CURRENT_ENVIRONMENT,
        "url": OLLAMA_URL,
        "description": ENVIRONMENT_MODES[CURRENT_ENVIRONMENT]["description"]
    }

def set_security_mode(mode: str):
    """Setzt den Sicherheitsmodus"""
    global CURRENT_SECURITY_MODE, AUTO_ACCEPT_ENABLED
    
    if mode not in SECURITY_MODES:
        available_modes = ", ".join(SECURITY_MODES.keys())
        raise ValueError(f"Unbekannter Sicherheitsmodus '{mode}'. Verfügbare Modi: {available_modes}")
    
    CURRENT_SECURITY_MODE = mode
    AUTO_ACCEPT_ENABLED = SECURITY_MODES[mode]["auto_accept_default"]
    
    mode_info = SECURITY_MODES[mode]
    print(f"🔒 Sicherheitsmodus auf '{mode_info['name']}' gesetzt")
    print(f"📝 {mode_info['description']}")
    print(f"🤖 Auto-Accept: {'Ein' if AUTO_ACCEPT_ENABLED else 'Aus'}")

def get_current_security_info(mode=None):
    """Gibt Informationen zum aktuellen Sicherheitsmodus zurück"""
    # Verwende übergebenen Mode oder aktuellen Mode
    target_mode = mode if mode else CURRENT_SECURITY_MODE
    
    if target_mode not in SECURITY_MODES:
        raise ValueError(f"Unbekannter Sicherheitsmodus: {target_mode}")
    
    return {
        "mode": target_mode,
        "config": SECURITY_MODES[target_mode],
        "auto_accept": AUTO_ACCEPT_ENABLED
    }

def toggle_auto_accept():
    """Schaltet Auto-Accept um"""
    global AUTO_ACCEPT_ENABLED
    AUTO_ACCEPT_ENABLED = not AUTO_ACCEPT_ENABLED
    print(f"🤖 Auto-Accept: {'Ein' if AUTO_ACCEPT_ENABLED else 'Aus'}")
    return AUTO_ACCEPT_ENABLED

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