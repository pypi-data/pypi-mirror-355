#!/usr/bin/env python3
"""
Kommandozeilen-Interface für ollama-code
Behandelt verschiedene Umgebungsmodi und Konfigurationen.
"""

import sys
import argparse
from pathlib import Path

# Füge das Projekt-Hauptverzeichnis zum Python-Pfad hinzu
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src import config
from src.main_runner import main as start_main_app

def show_host_setup_help():
    """Zeigt Hilfe für die Host-Konfiguration"""
    print("🔧 Host-Konfiguration für Ollama")
    print("=" * 50)
    print()
    print("Für die verschiedenen Umgebungsmodi muss Ollama entsprechend konfiguriert werden:")
    print()
    print("📍 LOKALES SYSTEM (local):")
    print("   - Ollama läuft direkt auf demselben System")
    print("   - Standard-Konfiguration: http://localhost:11434")
    print("   - Keine weitere Konfiguration nötig")
    print()
    print("📍 VIRTUELLE MASCHINE (vm):")
    print("   - Ollama läuft auf dem Host-System, Code in VM")
    print("   - Linux VM: Ollama muss auf allen Interfaces lauschen")
    print("     Befehl: OLLAMA_HOST=0.0.0.0 ollama serve")
    print("   - Windows Host: Firewall-Regel für Port 11434 erstellen")
    print("   - Docker: host.docker.internal:11434 verwenden")
    print()
    print("📍 NETZWERK (net):")
    print("   - Ollama läuft auf einem anderen Rechner im Netzwerk")
    print("   - Server-Konfiguration: OLLAMA_HOST=0.0.0.0 ollama serve")
    print("   - Client-Konfiguration: IP-Adresse des Servers anpassen")
    print("   - Firewall: Port 11434 freigeben")
    print()
    print("🔍 Weitere Informationen:")
    print("   - Ollama Dokumentation: https://ollama.ai/")
    print("   - Netzwerk-Troubleshooting: ollama-code --test-connection")

def test_connection():
    """Testet die Verbindung zu Ollama"""
    import requests
    
    print(f"🔍 Teste Verbindung zu Ollama...")
    print(f"   URL: {config.OLLAMA_URL}")
    print(f"   Modus: {config.CURRENT_ENVIRONMENT}")
    print()
    
    try:
        # Test der Basis-Verbindung
        response = requests.get(f"{config.OLLAMA_URL}/api/tags", timeout=10)
        
        if response.status_code == 200:
            print("✅ Ollama-Server ist erreichbar!")
            
            # Überprüfe verfügbare Modelle
            data = response.json()
            models = data.get("models", [])
            
            if models:
                print(f"📋 Verfügbare Modelle ({len(models)}):")
                for model in models:
                    name = model.get("name", "Unbekannt")
                    size = model.get("size", 0)
                    size_mb = round(size / (1024 * 1024), 1)
                    print(f"   - {name} ({size_mb} MB)")
                
                # Überprüfe ob das konfigurierte Modell verfügbar ist
                if any(config.MODEL_NAME in m.get("name", "") for m in models):
                    print(f"✅ Konfiguriertes Modell '{config.MODEL_NAME}' ist verfügbar!")
                else:
                    print(f"⚠️  Konfiguriertes Modell '{config.MODEL_NAME}' nicht gefunden!")
                    print(f"   Installiere es mit: ollama pull {config.MODEL_NAME}")
            else:
                print("⚠️  Keine Modelle installiert!")
                print(f"   Installiere ein Modell mit: ollama pull {config.MODEL_NAME}")
                
        else:
            print(f"❌ Ollama-Server antwortet mit Status {response.status_code}")
            print("   Mögliche Ursachen:")
            print("   - Ollama ist nicht gestartet")
            print("   - Falsche URL-Konfiguration")
            print("   - Netzwerk-/Firewall-Probleme")
            
    except requests.exceptions.ConnectError:
        print("❌ Verbindung fehlgeschlagen - Server nicht erreichbar!")
        print()
        print("🔧 Lösungsvorschläge:")
        print(f"   1. Prüfe ob Ollama läuft: curl {config.OLLAMA_URL}/api/tags")
        print("   2. Prüfe die Umgebungskonfiguration:")
        print("      - Lokal: ollama-code local")
        print("      - VM: ollama-code vm")  
        print("      - Netzwerk: ollama-code net")
        print("   3. Host-Setup-Hilfe: ollama-code host")
        
    except requests.exceptions.Timeout:
        print("❌ Verbindung ist zu langsam (Timeout)!")
        print("   - Prüfe die Netzwerkverbindung")
        print("   - Server könnte überlastet sein")
        
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")

def main():
    """Hauptfunktion für die Kommandozeilen-Schnittstelle"""
    parser = argparse.ArgumentParser(
        description="Ollama Code - Autonomer KI-Entwicklungsassistent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  ollama-code                 Startet die Anwendung (lokaler Modus)
  ollama-code --mode vm       Startet im VM-Modus
  ollama-code --mode net      Startet im Netzwerk-Modus
  ollama-code --host          Zeigt Host-Konfigurationshilfe
  ollama-code --test          Testet Ollama-Verbindung
  ollama-code --config        Zeigt aktuelle Konfiguration
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['local', 'vm', 'net'],
        default='local',
        help='Umgebungsmodus: local (Standard), vm (Virtuelle Maschine), net (Netzwerk)'
    )
    
    parser.add_argument(
        '--host',
        action='store_true',
        help='Zeigt Host-Konfigurationshilfe'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Testet die Verbindung zu Ollama'
    )
    
    parser.add_argument(
        '--config',
        action='store_true', 
        help='Zeigt aktuelle Konfiguration'
    )
    
    args = parser.parse_args()
    
    # Zuerst prüfen ob es Info-Befehle sind (nicht die Hauptapp starten)
    if args.host:
        show_host_setup_help()
        return
        
    if args.test:
        # Umgebungsmodus setzen für korrekten Test
        config.set_environment_mode(args.mode)
        test_connection()
        return
        
    if args.config:
        # Umgebungsmodus setzen für korrekte Anzeige
        config.set_environment_mode(args.mode)
        info = config.get_current_environment_info()
        print("📋 Aktuelle Konfiguration:")
        print(f"   Modus: {info['mode']}")
        print(f"   URL: {info['url']}")
        print(f"   Beschreibung: {info['description']}")
        print(f"   Modell: {config.MODEL_NAME}")
        return
    
    # Umgebungsmodus setzen und Hauptanwendung starten
    try:
        config.set_environment_mode(args.mode)
        if args.mode != 'local':
            print(f"🚀 Starte ollama-code im {args.mode.upper()}-Modus...")
    except ValueError as e:
        print(f"❌ {e}")
        return
    
    # Hauptanwendung starten
    start_main_app()

if __name__ == "__main__":
    main()