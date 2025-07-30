#!/usr/bin/env python3
"""
API-Handler für die Eel-Schnittstelle.
Alle @eel.expose Funktionen sind hier definiert.
"""

import eel
import json
import os
import time
from typing import Dict, Any

from src import config
from src.core import caching, ollama_client, session_manager
from src.agent.atlas_agent import AtlasAgent

# Globale Instanzen, die von main.py gesetzt werden
atlas_agent: AtlasAgent = None
session_manager_instance: session_manager.SessionManager = None

# Globale Zustandsvariablen für das Streaming
total_tokens = 0
token_start_time = None
last_token_update = 0
typewriter_active = False

def register_handlers(_atlas_agent: AtlasAgent, _session_manager: session_manager.SessionManager):
    """Registriert die globalen Instanzen für die Handler."""
    global atlas_agent, session_manager_instance
    atlas_agent = _atlas_agent
    session_manager_instance = _session_manager
    print("✅ API-Handler erfolgreich registriert.")

@eel.expose
def atlas_chat(message: str):
    """Haupt-Chat-Funktion, die das Streaming zum Frontend steuert."""
    global total_tokens, token_start_time, typewriter_active, last_token_update
    
    try:
        total_tokens = 0
        token_start_time = time.time()
        last_token_update = 0
        typewriter_active = False

        context = atlas_agent.build_conversation_context(message)
        response_stream = ollama_client.call_ollama(context, stream=True)
        
        if isinstance(response_stream, dict) and "error" in response_stream:
            eel.stream_error(response_stream["error"])
            return

        full_response = ""
        for line in response_stream.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode('utf-8'))
                    if 'response' in data:
                        chunk = data['response']
                        full_response += chunk
                        
                        if not typewriter_active:
                            eel.typewriter_start("assistant")
                            typewriter_active = True
                        
                        eel.typewriter_chunk(chunk)
                        
                        # Live-Token-Update
                        chunk_tokens = caching.realistic_token_count(chunk)
                        total_tokens += chunk_tokens
                        current_time = time.time()
                        if current_time - last_token_update > 0.1:
                            elapsed = current_time - token_start_time
                            speed = total_tokens / elapsed if elapsed > 0 else 0
                            eel.token_update({"tokens": total_tokens, "tokens_per_second": round(speed, 1)})
                            last_token_update = current_time
                            
                    if data.get('done', False):
                        eel.typewriter_end("assistant")
                        caching.conversation_cache.append({"role": "assistant", "content": full_response})
                        caching.save_session_cache(token_start_time, total_tokens)
                        
                        # Prüfe auf Context-Rotation NACH der Antwort
                        should_rotate, reason = session_manager_instance.should_rotate_context()
                        if should_rotate:
                            eel.context_rotation_started()
                            success = session_manager_instance.perform_context_rotation()
                            stats = session_manager_instance.get_session_stats()
                            eel.context_rotation_completed({
                                "success": success,
                                "new_context_length": len(caching.conversation_cache),
                                "context_percentage": stats.get('current_percentage', 100)
                            })
                        
                        eel.stream_complete({"response": full_response, "total_tokens": total_tokens})
                        break
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
    except Exception as e:
        print(f"❌ Atlas-Chat-Fehler: {e}")
        eel.stream_error(str(e))
        if typewriter_active:
            eel.typewriter_end("assistant")

@eel.expose
def list_files(directory: str = ""):
    """Listet Dateien und Ordner im Arbeitsverzeichnis auf."""
    try:
        target_dir = os.path.join(atlas_agent.sandbox_dir, directory)
        if not atlas_agent.is_path_safe(target_dir):
            return {"error": "Zugriff außerhalb des erlaubten Bereichs"}
        
        items = []
        for item in os.listdir(target_dir):
            item_path = os.path.join(target_dir, item)
            items.append({
                "name": item,
                "is_directory": os.path.isdir(item_path),
                "size": os.path.getsize(item_path)
            })
        return {"items": items, "current_path": target_dir}
    except Exception as e:
        return {"error": str(e)}

@eel.expose
def read_file(filepath: str):
    full_path = os.path.join(atlas_agent.sandbox_dir, filepath)
    if not atlas_agent.is_path_safe(full_path) or not os.path.exists(full_path):
        return {"error": "Datei nicht gefunden oder Zugriff verweigert"}
    if os.path.getsize(full_path) > MAX_FILE_SIZE:
        return {"error": "Datei zu groß"}
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            return {"content": f.read(), "filepath": full_path}
    except Exception as e:
        return {"error": str(e)}

@eel.expose
def write_file(filepath: str, content: str):
    full_path = os.path.join(atlas_agent.sandbox_dir, filepath)
    if not atlas_agent.is_path_safe(full_path):
        return {"error": "Zugriff verweigert"}
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return {"success": True, "filepath": full_path}
    except Exception as e:
        return {"error": str(e)}

@eel.expose
def execute_code(code: str, language: str = "python"):
    return atlas_agent.execute_code(code, language)

@eel.expose
def get_system_info():
    return {
        "working_directory": atlas_agent.sandbox_dir,
        "sandbox_mode": atlas_agent.sandbox_mode,
        "model_name": config.MODEL_NAME,
        "ollama_url": config.OLLAMA_URL
    }

@eel.expose
def clear_cache(all_sessions: bool = False):
    caching.clear_session_cache(all_sessions)
    session_manager_instance.register_session(caching.current_session_id) # Re-register
    return {"success": True, "message": "Cache geleert"}

@eel.expose
def get_cache_info():
    return caching.get_cache_stats()

@eel.expose
def get_context_rotation_info():
    return session_manager_instance.get_session_stats()

@eel.expose
def trigger_manual_context_rotation():
    eel.context_rotation_started()
    success = session_manager_instance.perform_context_rotation()
    stats = session_manager_instance.get_session_stats()
    result = {
        "success": success,
        "new_context_length": len(caching.conversation_cache),
        "context_percentage": stats.get('current_percentage', 100)
    }
    eel.context_rotation_completed(result)
    return result

@eel.expose
def emergency_stop():
    """Entlädt das Modell über die Ollama-API."""
    try:
        # Ein Generate-Call mit keep_alive=0 entlädt das Modell
        requests.post(
            f"{config.OLLAMA_URL}/api/generate",
            json={"model": config.MODEL_NAME, "keep_alive": 0},
            timeout=10
        )
        caching.clear_session_cache(all_sessions=False)
        return {"success": True, "message": f"Modell {config.MODEL_NAME} entladen."}
    except Exception as e:
        return {"success": False, "error": str(e)}