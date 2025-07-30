#!/usr/bin/env python3
"""
Ollama Client Modul
Verwaltet die Kommunikation mit dem Ollama-Backend.
"""

import requests
from typing import Any
from src import config

def call_ollama(prompt: str, stream: bool = True) -> Any:
    """Ruft das Ollama-Modell auf"""
    try:
        payload = {
            "model": config.MODEL_NAME,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": 0.6,
                "top_p": 0.85,
                "max_tokens": 4096,
                "num_predict": -1,
                "repeat_penalty": 1.15,
                "typical_p": 1.0,
                "tfs_z": 1.0,
                "num_ctx": 8192,
                "num_batch": 512,
                "num_thread": 8
            },
            "keep_alive": "5m"
        }
        
        response = requests.post(
            f"{config.OLLAMA_URL}/api/generate",
            json=payload,
            stream=stream,
            timeout=None
        )
        
        response.raise_for_status() # Löst einen Fehler bei 4xx/5xx aus
        
        if stream:
            return response
        else:
            return response.json()
            
    except requests.exceptions.ConnectionError as e:
        error_msg = f"❌ Ollama-Server nicht erreichbar: {str(e)}\n"
        error_msg += "\n🔧 Lösungsvorschläge:\n"
        error_msg += "   1. Prüfe ob Ollama läuft: ollama serve\n"
        error_msg += "   2. Prüfe Umgebungskonfiguration:\n"
        error_msg += "      - Lokal: ollama-code local\n"
        error_msg += "      - VM: ollama-code vm\n"
        error_msg += "      - Netzwerk: ollama-code net\n"
        error_msg += "   3. Host-Setup-Hilfe: ollama-code host\n"
        error_msg += "   4. Verbindungstest: ollama-code --test\n"
        print(error_msg)
        return {"error": "Ollama-Verbindung fehlgeschlagen"}
    
    except requests.exceptions.Timeout as e:
        error_msg = f"❌ Ollama-Verbindung zu langsam (Timeout): {str(e)}\n"
        error_msg += "\n🔧 Mögliche Ursachen:\n"
        error_msg += "   - Netzwerkverbindung zu langsam\n"
        error_msg += "   - Server überlastet\n"
        error_msg += "   - Große Modelle brauchen mehr Zeit\n"
        print(error_msg)
        return {"error": "Ollama-Verbindung Timeout"}
    
    except requests.exceptions.RequestException as e:
        error_msg = f"❌ Ollama-Verbindung fehlgeschlagen: {str(e)}\n"
        error_msg += "\n🔧 Weitere Hilfe:\n"
        error_msg += "   - Konfiguration prüfen: ollama-code --show-config\n"
        error_msg += "   - Verbindung testen: ollama-code --test\n"
        error_msg += "   - Host-Setup: ollama-code host\n"
        print(error_msg)
        return {"error": f"Ollama-Verbindung fehlgeschlagen: {str(e)}"}