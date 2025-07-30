#!/usr/bin/env python3
"""
FINAL FIX: Handlers mit korrigiertem Tool-Call-System
- Deduplizierung von Tool-Calls
- Verstecken von [TOOL_CALLS] Text im Chat
- Korrektes Tool-Result-Formatting
"""

import eel
import json
import os
import time
import requests
from typing import Dict, Any, List

from src import config
from src.core import caching, ollama_client, session_manager
from src.core.devstral_tools import devstral_tools
from src.core.context_cache import context_cache
from src.core.command_handler import command_handler
from src.agent.codiac_agent import CodiacAgent

# Globale Instanzen, die von main.py gesetzt werden
atlas_agent: CodiacAgent = None
session_manager_instance: session_manager.SessionManager = None

# Globale Zustandsvariablen für das Streaming
total_tokens = 0
session_total_tokens = 0
token_start_time = None
last_token_update = 0
typewriter_active = False

def parse_tool_calls_with_dedup(text: str, already_executed: List[str]) -> List[Dict[str, Any]]:
    """Tool-Call-Parsing mit Deduplizierung"""
    import re
    tool_calls = []
    
    # Patterns für Tool-Call-Erkennung
    patterns = [
        ("devstral Standard", r'\[TOOL_CALLS\]\s*(\[.*?\])'),
        ("devstral Single", r'\[TOOL_CALLS\]\s*(\{[^}]*"name"[^}]*\})'),
    ]
    
    for pattern_name, pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            try:
                match_text = match.strip()
                
                # Handle Array-Format [{}]
                if match_text.startswith('[') and match_text.endswith(']'):
                    tool_array = json.loads(match_text)
                    if isinstance(tool_array, list):
                        for tool_call in tool_array:
                            if isinstance(tool_call, dict) and 'name' in tool_call:
                                # Erstelle eindeutige ID für Deduplizierung
                                tool_id = f"{tool_call['name']}_{json.dumps(tool_call.get('arguments', {}), sort_keys=True)}"
                                if tool_id not in already_executed:
                                    tool_calls.append(tool_call)
                                    already_executed.append(tool_id)
                
                # Handle Single Object Format {}
                elif match_text.startswith('{') and match_text.endswith('}'):
                    tool_call = json.loads(match_text)
                    if isinstance(tool_call, dict) and 'name' in tool_call:
                        tool_id = f"{tool_call['name']}_{json.dumps(tool_call.get('arguments', {}), sort_keys=True)}"
                        if tool_id not in already_executed:
                            tool_calls.append(tool_call)
                            already_executed.append(tool_id)
                    
            except json.JSONDecodeError:
                continue
    
    return tool_calls

def filter_tool_calls_from_text(text: str) -> str:
    """Entfernt [TOOL_CALLS] aus dem Chat-Text"""
    import re
    
    # Entferne [TOOL_CALLS][...] komplett aus dem Text
    patterns = [
        r'\[TOOL_CALLS\]\s*\[.*?\]',
        r'\[TOOL_CALLS\]\s*\{[^}]*\}',
    ]
    
    filtered_text = text
    for pattern in patterns:
        filtered_text = re.sub(pattern, '', filtered_text, flags=re.DOTALL)
    
    return filtered_text.strip()

def format_tool_result_properly(tool_name: str, result: Dict[str, Any]) -> str:
    """Formatiert Tool-Ergebnisse benutzerfreundlich"""
    
    # Prüfe auf Erfolg
    if not result.get("success", False):
        error_msg = result.get("error", "Unbekannter Fehler")
        return f"❌ **{tool_name} fehlgeschlagen:** {error_msg}"
    
    # Tool-spezifische Formatierung
    if tool_name == "bash_execute":
        description = result.get("description", "System-Befehl")
        stdout = result.get("stdout", "").strip()
        stderr = result.get("stderr", "").strip()
        
        if stdout:
            # Begrenzte Ausgabe für bessere Lesbarkeit
            if len(stdout) > 500:
                return f"✅ **{description}**\n```\n{stdout[:500]}...\n(Ausgabe gekürzt)\n```"
            else:
                return f"✅ **{description}**\n```\n{stdout}\n```"
        elif stderr:
            return f"⚠️ **{description}** - Warnung: {stderr}"
        else:
            return f"✅ **{description}** - Erfolgreich ausgeführt"
    
    elif tool_name == "read_file":
        file_path = result.get("file_path", "")
        lines = result.get("lines_read", 0)
        return f"📄 **Datei gelesen:** {file_path} ({lines} Zeilen)"
    
    elif tool_name == "list_files":
        count = result.get("count", 0)
        directory = result.get("directory", ".")
        return f"📁 **{count} Dateien** in {directory} gefunden"
    
    else:
        return f"✅ **{tool_name}** erfolgreich ausgeführt"

def execute_tool_calls_secure(tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Führt Tool-Calls sicher aus"""
    results = []
    
    for tool_call in tool_calls:
        tool_name = tool_call.get("name")
        arguments = tool_call.get("arguments", {})
        
        # Sichere Tool-Ausführung
        if atlas_agent.security_mode == 'safe':
            result = {"success": False, "error": "Safe Mode: Tools werden simuliert"}
        else:
            result = atlas_agent.secure_tools.execute_tool(tool_name, arguments)
        
        result["tool_name"] = tool_name
        result["arguments"] = arguments
        results.append(result)
        
        # Saubere Tool-Update-Ausgabe
        update_text = format_tool_result_properly(tool_name, result)
        try:
            eel.typewriter_chunk(update_text + "\n\n")
        except:
            pass
    
    return results

def register_handlers(_atlas_agent: CodiacAgent, _session_manager: session_manager.SessionManager):
    """Registriert die globalen Instanzen für die Handler."""
    global atlas_agent, session_manager_instance
    atlas_agent = _atlas_agent
    session_manager_instance = _session_manager
    
    # Context-Cache initialisieren
    context_cache.set_session(caching.current_session_id)
    print("✅ API-Handler und Context-Cache erfolgreich registriert.")

@eel.expose
def atlas_chat(message: str):
    """Haupt-Chat-Funktion mit korrigiertem Tool-System"""
    global total_tokens, session_total_tokens, token_start_time, typewriter_active, last_token_update
    
    print(f"🔥 DEBUG: atlas_chat aufgerufen mit message: '{message[:50]}...'")
    
    try:
        # COMMAND-SYSTEM: Prüfe ob Nachricht ein Befehl ist
        if command_handler.is_command(message):
            result = command_handler.handle_command(message)
            
            if "error" in result:
                eel.typewriter_start("assistant")
                eel.typewriter_chunk(f"❌ {result['error']}")
                eel.typewriter_end("assistant")
            else:
                eel.typewriter_start("assistant")
                output = result["output"]
                
                if atlas_agent.security_mode == 'safe':
                    import platform
                    os_type = platform.system().lower()
                    if os_type == 'windows':
                        sim_path = "C:\\Users\\developer\\DevProjects"
                    else:
                        sim_path = "/home/developer/DevProjects"
                    try:
                        eel.update_working_directory(f"📁 {sim_path} (Simulation)")
                    except:
                        pass
                
                eel.typewriter_chunk(output)
                eel.typewriter_end("assistant")
                
                if result.get("system_change"):
                    try:
                        eel.update_system_status()
                    except:
                        pass
                if result.get("clear_chat"):
                    try:
                        eel.clear_chat_display()
                    except:
                        pass
                if result.get("new_session"):
                    try:
                        session_manager_instance.start_new_session()
                        eel.update_system_status()
                    except:
                        pass
            return
        
        # NORMALE KI-VERARBEITUNG
        print(f"🔥 DEBUG: Starte normale KI-Verarbeitung")
        
        try:
            eel.update_codiac_status("thinking", "Codiac analysiert...")
        except:
            pass
        
        total_tokens = 0
        token_start_time = time.time()
        last_token_update = 0
        typewriter_active = False

        print(f"🔥 DEBUG: Verwende NEUE call_ollama_with_system_prompt Methode")
        
        # Context-Cache für Token-Tracking
        user_msg_id = f"user_{int(time.time() * 1000)}"
        user_tokens = caching.realistic_token_count(message)
        context_cache.add_message(user_msg_id, "user", message, message, user_tokens)
        
        response_stream = atlas_agent.call_ollama_with_system_prompt(message, stream=True)
        print(f"🔥 DEBUG: Response_stream erhalten: {type(response_stream)}")
        
        if isinstance(response_stream, dict) and "error" in response_stream:
            print(f"🔥 DEBUG: Error in response_stream: {response_stream['error']}")
            eel.stream_error(response_stream["error"])
            return

        print(f"🔥 DEBUG: Starte Stream-Iteration...")
        full_response = ""
        line_count = 0
        executed_tool_ids = []  # DEDUPLIZIERUNG
        
        for line in response_stream.iter_lines():
            line_count += 1
            if line_count <= 3:
                print(f"🔥 DEBUG: Stream Line {line_count}: {line[:100] if line else 'Empty'}")
            
            if line:
                try:
                    data = json.loads(line.decode('utf-8'))
                    if 'response' in data:
                        chunk = data['response']
                        full_response += chunk
                        
                        # Tool-Calls mit Deduplizierung parsen
                        tool_calls = parse_tool_calls_with_dedup(full_response, executed_tool_ids)
                        
                        if not typewriter_active:
                            eel.typewriter_start("assistant")
                            typewriter_active = True
                            try:
                                eel.update_codiac_status("working", "Codiac antwortet...")
                            except:
                                pass
                        
                        # Chunk OHNE Tool-Calls senden
                        filtered_chunk = filter_tool_calls_from_text(chunk)
                        if filtered_chunk:
                            eel.typewriter_chunk(filtered_chunk)
                        
                        # Neue Tool-Calls ausführen
                        if tool_calls:
                            print(f"🔧 Führe {len(tool_calls)} neue Tools aus: {[tc.get('name') for tc in tool_calls]}")
                            tool_results = execute_tool_calls_secure(tool_calls)
                            
                            # Tool-Results für devstral formatieren
                            for result in tool_results:
                                tool_result_msg = {
                                    "role": "tool", 
                                    "content": json.dumps(result, ensure_ascii=False)
                                }
                                caching.conversation_cache.append(tool_result_msg)
                        
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
                        # Finale Token-Berechnung
                        final_tokens = total_tokens
                        elapsed = time.time() - token_start_time
                        final_speed = final_tokens / elapsed if elapsed > 0 else 0
                        
                        # AI-Antwort zum Cache hinzufügen
                        filtered_response = filter_tool_calls_from_text(full_response)
                        caching.conversation_cache.append({"role": "assistant", "content": filtered_response})
                        
                        # Context-Cache hinzufügen
                        assistant_msg_id = f"assistant_{int(time.time() * 1000)}"
                        assistant_tokens = caching.realistic_token_count(filtered_response)
                        context_cache.add_message(assistant_msg_id, "assistant", filtered_response, filtered_response, assistant_tokens)
                        
                        print(f"📊 Live-Tokens für Transfer: {final_tokens}")
                        
                        # Context-Usage berechnen
                        current_context_tokens = sum(caching.realistic_token_count(msg.get('content', '')) for msg in caching.conversation_cache)
                        
                        # Updates senden
                        try:
                            eel.token_update({"tokens": final_tokens, "tokens_per_second": round(final_speed, 1)})
                        except Exception as e:
                            print(f"⚠️ Token-Update-Fehler: {e}")
                        
                        try:
                            eel.session_token_update(final_tokens)
                        except Exception as e:
                            print(f"⚠️ Session-Token-Update-Fehler: {e}")
                        
                        try:
                            eel.update_context_usage(current_context_tokens, config.MAX_CONTEXT_TOKENS)
                        except Exception as e:
                            print(f"⚠️ Context-Update-Fehler: {e}")
                        
                        time.sleep(0.05)
                        
                        # Typewriter beenden
                        try:
                            eel.typewriter_end("assistant")
                        except Exception as e:
                            print(f"⚠️ Typewriter-End-Fehler: {e}")
                        
                        caching.save_session_cache(token_start_time, total_tokens)
                        
                        # Context-Optimierung
                        context_stats = context_cache.get_session_stats()
                        context_usage_percent = context_stats.get('context_usage', 0)
                        
                        if context_usage_percent > 90:
                            print(f"🔄 Context-Optimierung bei {context_usage_percent:.1f}% Auslastung")
                            
                            try:
                                eel.start_message_collapse({
                                    "reason": f"Context bei {context_usage_percent:.1f}%",
                                    "context_usage": current_context_tokens,
                                    "max_context": config.MAX_CONTEXT_TOKENS,
                                    "should_compress": True
                                })
                                
                                context_cache.compress_old_messages(keep_recent=50)
                                
                            except Exception as e:
                                print(f"⚠️ Context-Optimierung-Fehler: {e}")
                            
                            print("✅ Context optimiert, Session-Tokens bleiben erhalten")
                        
                        try:
                            eel.stream_complete({"response": filtered_response, "total_tokens": total_tokens})
                            eel.update_codiac_status("ready")
                        except:
                            pass
                        break
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
    except Exception as e:
        print(f"❌ Atlas-Chat-Fehler: {e}")
        eel.stream_error(str(e))
        if typewriter_active:
            eel.typewriter_end("assistant")
        try:
            eel.update_codiac_status("error", f"Fehler: {str(e)[:50]}", temporary=True, duration=5000)
        except:
            pass

# Alle anderen @eel.expose Funktionen bleiben unverändert...
@eel.expose
def get_system_info():
    mode_info = {
        'safe': '🔒 Safe Mode (Simulation)',
        'base': '🔓 Base Mode (Real File Access)',
        'hell-out': '⚠️ Hell-Out Mode (Full System Access)'
    }
    
    current_mode = atlas_agent.security_mode
    mode_display = mode_info.get(current_mode, f'Unknown: {current_mode}')
    
    return {
        "working_directory": atlas_agent.working_directory,
        "sandbox_mode": atlas_agent.sandbox_mode,
        "security_mode": current_mode,
        "security_display": mode_display,
        "model_name": config.MODEL_NAME,
        "ollama_url": config.OLLAMA_URL,
        "file_access": atlas_agent.security_config.get('file_access', False),
        "terminal_access": atlas_agent.security_config.get('terminal_access', False),
        "allowed_paths": atlas_agent.security_config.get('allowed_paths', 'none'),
        "file_operations": atlas_agent.security_config.get('file_operations', [])
    }

@eel.expose
def change_security_mode(new_mode: str):
    try:
        valid_modes = ['safe', 'base', 'hell-out']
        if new_mode not in valid_modes:
            return {"success": False, "error": f"Ungültiger Modus: {new_mode}"}
        
        old_mode = atlas_agent.security_mode
        atlas_agent.change_security_mode(new_mode)
        atlas_agent.update_tools_for_mode(new_mode)
        
        print(f"🔄 Sicherheitsmodus gewechselt: {old_mode} → {new_mode}")
        
        return {
            "success": True, 
            "message": f"Sicherheitsmodus gewechselt von {old_mode} zu {new_mode}",
            "old_mode": old_mode,
            "new_mode": new_mode
        }
        
    except Exception as e:
        print(f"❌ Fehler beim Wechseln des Sicherheitsmodus: {e}")
        return {"success": False, "error": str(e)}

# Weitere Standard-Funktionen...
@eel.expose
def emergency_stop():
    try:
        requests.post(
            f"{config.OLLAMA_URL}/api/generate",
            json={"model": config.MODEL_NAME, "keep_alive": 0},
            timeout=10
        )
        caching.clear_session_cache(all_sessions=False)
        return {"success": True, "message": f"Modell {config.MODEL_NAME} entladen."}
    except Exception as e:
        return {"success": False, "error": str(e)}
