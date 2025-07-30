#!/usr/bin/env python3
"""
Ollama Client Modul - Optimiert für Systemprompts
Verwaltet die Kommunikation mit dem Ollama-Backend mit korrekter Systemprompt-Implementierung.
"""

import requests
import json
from typing import Any, List, Dict, Optional
from src import config

def call_ollama(prompt: str, stream: bool = True, tools: list = None) -> Any:
    """Ruft das Ollama-Modell auf mit Tool-Support für devstral"""
    print(f"🔥 DEBUG: call_ollama gestartet")
    print(f"🔥 DEBUG: URL: {config.OLLAMA_URL}")
    print(f"🔥 DEBUG: Model: {config.MODEL_NAME}")
    print(f"🔥 DEBUG: Stream: {stream}")
    print(f"🔥 DEBUG: Prompt length: {len(prompt)} chars")
    
    try:
        payload = {
            "model": config.MODEL_NAME,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": 0.6,
                "top_p": 0.85,
                "max_tokens": 8192,      # Output-Limit
                "num_predict": -1,       # CRITICAL: Unlimited prediction für Agent
                "num_keep": 128,         # CRITICAL: Keep wichtige Tokens im Context
                "repeat_penalty": 1.15,
                "typical_p": 1.0,
                "tfs_z": 1.0,
                # num_ctx entfernt - devstral:24b nutzt standardmäßig 128k
                "num_batch": 2048,      # Größere Batches
                "num_thread": -1,       # CRITICAL: AUTO CPU-Threads
                "num_gpu": -1,          # CRITICAL: AUTO GPU-Nutzung
                "num_gqa": 8,           # Grouped Query Attention für 24b Model
                "rope_frequency_base": 1000000.0,  # RoPE für 128k Sequenzen
                "rope_frequency_scale": 0.5,       # Skalierung für lange Kontexte
                "f16_kv": True,         # FIX: Python True statt JSON true
                "low_vram": False       # FIX: Python False statt JSON false
            },
            "keep_alive": "5m"
        }
        
        print(f"🔥 DEBUG: Payload erstellt, sende Request...")
        
        response = requests.post(
            f"{config.OLLAMA_URL}/api/generate",
            json=payload,
            stream=stream,
            timeout=300  # 5 Minuten Timeout statt None
        )
        
        print(f"🔥 DEBUG: Response erhalten - Status: {response.status_code}")
        
        # Verbesserte Fehlerbehandlung
        if response.status_code != 200:
            error_detail = f"HTTP {response.status_code}"
            try:
                error_json = response.json()
                error_detail += f": {error_json.get('error', 'Unbekannter Fehler')}"
                print(f"🔥 DEBUG: Error JSON: {error_json}")
            except:
                error_detail += f": {response.text[:200]}"
                print(f"🔥 DEBUG: Error Text: {response.text[:200]}")
            print(f"🔥 DEBUG: Raising RequestException: {error_detail}")
            raise requests.exceptions.RequestException(error_detail)
        
        print(f"🔥 DEBUG: Response OK, returning {'stream' if stream else 'json'}")
        
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

# === NEUE OPTIMIERTE SYSTEMPROMPT-FUNKTIONEN ===

def call_ollama_chat(messages: List[Dict], system_prompt: str = None, stream: bool = True, tools: list = None) -> Any:
    """
    Ruft Ollama /api/chat Endpunkt mit korrektem Systemprompt auf.
    Dieser Ansatz ist optimal für Chat-Konversationen mit mehreren Nachrichten.
    """
    print(f"🔥 DEBUG: call_ollama_chat gestartet")
    print(f"🔥 DEBUG: Messages count: {len(messages)}")
    print(f"🔥 DEBUG: System prompt length: {len(system_prompt) if system_prompt else 0}")
    
    try:
        # Nachrichten für Chat-Format vorbereiten
        chat_messages = []
        
        # System-Message als erste Nachricht hinzufügen (wenn vorhanden)
        if system_prompt:
            chat_messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # User/Assistant Messages hinzufügen
        for msg in messages:
            if msg['role'] in ['user', 'assistant']:
                chat_messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })
        
        payload = {
            "model": config.MODEL_NAME,
            "messages": chat_messages,
            "stream": stream,
            "options": {
                "temperature": 0.6,
                "top_p": 0.85,
                "max_tokens": 8192,
                "num_predict": -1,
                "num_keep": 128,
                "repeat_penalty": 1.15,
                "typical_p": 1.0,
                "tfs_z": 1.0,
                "num_batch": 2048,
                "num_thread": -1,
                "num_gpu": -1,
                "num_gqa": 8,
                "rope_frequency_base": 1000000.0,
                "rope_frequency_scale": 0.5,
                "f16_kv": True,
                "low_vram": False
            },
            "keep_alive": "5m"
        }
        
        # Tools hinzufügen (falls verfügbar)
        if tools:
            payload["tools"] = tools
            print(f"🔧 DEBUG: {len(tools)} Tools hinzugefügt")
        
        response = requests.post(
            f"{config.OLLAMA_URL}/api/chat",
            json=payload,
            stream=stream,
            timeout=300
        )
        
        return _handle_response(response, stream)
        
    except Exception as e:
        return _handle_error(e)

def call_ollama_devstral_template(conversation_history: List[Dict], system_prompt: str, tools: list = None, stream: bool = True) -> Any:
    """
    Spezielle Implementierung für devstral-Modelle mit dem korrekten Template-Format.
    Verwendet [SYSTEM_PROMPT]...[/SYSTEM_PROMPT] [INST]...[/INST] Format.
    """
    print(f"🔥 DEBUG: call_ollama_devstral_template gestartet")
    print(f"🔥 DEBUG: Conversation history: {len(conversation_history)} messages")
    
    try:
        # Devstral Template Format aufbauen
        template_parts = []
        
        # System prompt mit Tags
        if system_prompt:
            template_parts.append(f"[SYSTEM_PROMPT]{system_prompt}[/SYSTEM_PROMPT]")
        
        # Tools für erste User-Messages (devstral Konvention)
        tools_added = False
        user_message_count = 0
        
        for msg in conversation_history:
            if msg['role'] == 'user':
                user_message_count += 1
                
                # Tools nur in ersten 2 User-Messages hinzufügen
                if user_message_count <= 2 and tools and not tools_added:
                    tools_json = json.dumps(tools, ensure_ascii=False)
                    template_parts.append(f"[AVAILABLE_TOOLS]{tools_json}[/AVAILABLE_TOOLS]")
                    tools_added = True
                    print(f"🔧 DEBUG: Tools in Message {user_message_count} hinzugefügt")
                
                template_parts.append(f"[INST]{msg['content']}[/INST]")
                
            elif msg['role'] == 'assistant':
                # Assistant responses ohne spezielle Tags
                template_parts.append(msg['content'])
        
        # Kompletten Template-Prompt erstellen
        full_prompt = "\n".join(template_parts)
        
        print(f"🔥 DEBUG: Devstral Template erstellt ({len(full_prompt)} Zeichen)")
        
        # Standard generate-Aufruf mit Template-Prompt
        payload = {
            "model": config.MODEL_NAME,
            "prompt": full_prompt,
            "stream": stream,
            "raw": True,  # Wichtig: Kein zusätzliches Templating durch Ollama
            "options": {
                "temperature": 0.6,
                "top_p": 0.85,
                "max_tokens": 8192,
                "num_predict": -1,
                "num_keep": 128,
                "repeat_penalty": 1.15,
                "typical_p": 1.0,
                "tfs_z": 1.0,
                "num_batch": 2048,
                "num_thread": -1,
                "num_gpu": -1,
                "num_gqa": 8,
                "rope_frequency_base": 1000000.0,
                "rope_frequency_scale": 0.5,
                "f16_kv": True,
                "low_vram": False
            },
            "keep_alive": "5m"
        }
        
        response = requests.post(
            f"{config.OLLAMA_URL}/api/generate",
            json=payload,
            stream=stream,
            timeout=300
        )
        
        return _handle_response(response, stream)
        
    except Exception as e:
        return _handle_error(e)

def _handle_response(response, stream: bool):
    """Gemeinsame Response-Behandlung für alle Ollama-Aufrufe."""
    if response.status_code != 200:
        error_detail = f"HTTP {response.status_code}"
        try:
            error_json = response.json()
            error_detail += f": {error_json.get('error', 'Unbekannter Fehler')}"
        except:
            error_detail += f": {response.text[:200]}"
        raise requests.exceptions.RequestException(error_detail)
    
    if stream:
        return response
    else:
        return response.json()

def _handle_error(e):
    """Gemeinsame Fehlerbehandlung für alle Ollama-Aufrufe."""
    if isinstance(e, requests.exceptions.ConnectionError):
        error_msg = f"❌ Ollama-Server nicht erreichbar: {str(e)}\n"
        error_msg += "\n🔧 Lösungsvorschläge:\n"
        error_msg += "   1. Prüfe ob Ollama läuft: ollama serve\n"
        error_msg += "   2. Prüfe Umgebungskonfiguration\n"
        print(error_msg)
        return {"error": "Ollama-Verbindung fehlgeschlagen"}
    
    elif isinstance(e, requests.exceptions.Timeout):
        error_msg = f"❌ Ollama-Verbindung zu langsam (Timeout): {str(e)}\n"
        print(error_msg)
        return {"error": "Ollama-Verbindung Timeout"}
    
    elif isinstance(e, requests.exceptions.RequestException):
        error_msg = f"❌ Ollama-Verbindung fehlgeschlagen: {str(e)}\n"
        print(error_msg)
        return {"error": f"Ollama-Verbindung fehlgeschlagen: {str(e)}"}
    
    else:
        print(f"❌ Unbekannter Fehler: {str(e)}")
        return {"error": f"Unbekannter Fehler: {str(e)}"}