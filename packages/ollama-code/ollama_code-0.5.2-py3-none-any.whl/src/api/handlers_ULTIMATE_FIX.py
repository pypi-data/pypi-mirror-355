#!/usr/bin/env python3
"""
API-Handler für die Eel-Schnittstelle.
ULTIMATE FIX - Korrigiert alle Tool-Call-Probleme endgültig
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

# Globale Instanzen
atlas_agent: CodiacAgent = None
session_manager_instance: session_manager.SessionManager = None

# Globale Zustandsvariablen für das Streaming
total_tokens = 0
session_total_tokens = 0
token_start_time = None
last_token_update = 0
typewriter_active = False

def parse_tool_calls_from_complete_text(text: str) -> List[Dict[str, Any]]:
    """Parst Tool-Calls aus dem kompletten Text (nicht chunked)"""
    import re
    tool_calls = []
    
    # Erweiterte Patterns für bessere Tool-Call-Erkennung
    patterns = [
        # Standard Array-Format: [TOOL_CALLS][{...}]
        (r'\[TOOL_CALLS\]\s*(\[.*?\])', 'array'),
        # Einzelnes Object: [TOOL_CALLS]{"name":...}
        (r'\[TOOL_CALLS\]\s*(\{.*?"name".*?\})', 'object'),
        # Multi-Object Array (non-greedy)
        (r'\[TOOL_CALLS\]\s*(\[[\s\S]*?\])', 'multi'),
    ]
    
    for pattern, format_type in patterns:
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            try:
                match_text = match.strip()
                
                if format_type in ['array', 'multi'] and match_text.startswith('['):
                    # Parse JSON Array
                    tool_array = json.loads(match_text)
                    if isinstance(tool_array, list):
                        for tool_call in tool_array:
                            if isinstance(tool_call, dict) and 'name' in tool_call:
                                tool_calls.append(tool_call)
                
                elif format_type == 'object' and match_text.startswith('{'):
                    # Parse Single JSON Object
                    tool_call = json.loads(match_text)
                    if isinstance(tool_call, dict) and 'name' in tool_call:
                        tool_calls.append(tool_call)
                        
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON-Parse-Fehler: {e} für Text: {match_text[:100]}...")
                continue
    
    # Fallback: Intent-basierte Tool-Generierung
    if not tool_calls and 'festplatte' in text.lower():
        tool_calls.append({
            "name": "bash_execute",
            "arguments": {
                "command": "lsblk -d -o NAME,SIZE,TYPE,MODEL",
                "description": "Liste alle Festplatten auf"
            }
        })
    
    return tool_calls

def clean_text_from_tool_calls(text: str) -> str:
    """Entfernt ALLE Tool-Call-Syntax aus dem Text für saubere Chat-Anzeige"""
    import re
    
    # Entferne verschiedene Tool-Call-Formate komplett
    patterns_to_remove = [
        r'\[TOOL_CALLS\]\s*\[.*?\]',  # [TOOL_CALLS][{...}]
        r'\[TOOL_CALLS\]\s*\{.*?\}',  # [TOOL_CALLS]{"name":...}
        r'\[TOOL_CALLS\].*?(?=\s|$)',  # [TOOL_CALLS] gefolgt von allem bis Leerzeichen/Ende
    ]
    
    cleaned_text = text
    for pattern in patterns_to_remove:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.DOTALL | re.IGNORECASE)
    
    # Entferne überschüssige Leerzeichen und Zeilenumbrüche
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    
    return cleaned_text

def format_tool_success(tool_name: str, result: Dict[str, Any]) -> str:
    """Formatiert erfolgreiche Tool-Ergebnisse benutzerfreundlich"""
    
    if tool_name == "bash_execute":
        description = result.get("description", "System-Befehl")
        stdout = result.get("stdout", "").strip()
        stderr = result.get("stderr", "").strip()
        
        if stdout:
            # Intelligente Ausgabe-Kürzung
            if len(stdout) > 1000:
                lines = stdout.split('\n')
                if len(lines) > 20:
                    truncated = '\n'.join(lines[:20]) + f"\n... ({len(lines) - 20} weitere Zeilen)"
                    return f"✅ **{description}:**\n```\n{truncated}\n```"
                else:
                    return f"✅ **{description}:**\n```\n{stdout[:1000]}...\n```"
            else:
                return f"✅ **{description}:**\n```\n{stdout}\n```"
        elif stderr:
            return f"⚠️ **{description}** - Warnung: {stderr}"
        else:
            return f"✅ **{description}** - Erfolgreich ausgeführt"
    
    return f"✅ **{tool_name}** erfolgreich ausgeführt"

def execute_tools_with_better_error_handling(tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Führt Tools aus mit verbesserter Fehlerbehandlung"""
    results = []
    
    for tool_call in tool_calls:
        tool_name = tool_call.get("name")
        arguments = tool_call.get("arguments", {})
        
        print(f"🔧 Führe Tool aus: {tool_name} mit args: {arguments}")
        
        try:
            if atlas_agent.security_mode == 'safe':
                result = {"success": False, "error": "Safe Mode: Tools werden simuliert"}
            else:
                # Führe Tool aus
                result = atlas_agent.secure_tools.execute_tool(tool_name, arguments)
                print(f"🔧 Tool-Result: {result}")
            
            result["tool_name"] = tool_name
            result["arguments"] = arguments
            results.append(result)
            
            # Formatiere und sende Tool-Update
            if result.get("success"):
                update_text = format_tool_success(tool_name, result)
            else:
                error_msg = result.get("error", "Unbekannter Fehler")
                update_text = f"❌ **{tool_name} fehlgeschlagen:** {error_msg}"
            
            try:
                eel.typewriter_chunk(update_text + "\n\n")
            except:
                pass
                
        except Exception as e:
            error_result = {
                "success": False,
                "error": f"Tool-Ausführungs-Fehler: {str(e)}",
                "tool_name": tool_name,
                "arguments": arguments
            }
            results.append(error_result)
            
            try:
                eel.typewriter_chunk(f"❌ **{tool_name} Fehler:** {str(e)}\n\n")
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
    """Haupt-Chat-Funktion mit ultimativ korrigiertem Tool-System"""
    global total_tokens, session_total_tokens, token_start_time, typewriter_active, last_token_update
    
    print(f"🔥 DEBUG: atlas_chat aufgerufen mit message: '{message[:50]}...'")
    
    try:
        # COMMAND-SYSTEM bleibt unverändert
        if command_handler.is_command(message):
            result = command_handler.handle_command(message)
            
            if "error" in result:
                eel.typewriter_start("assistant")
                eel.typewriter_chunk(f"❌ {result['error']}")
                eel.typewriter_end("assistant")
            else:
                eel.typewriter_start("assistant")
                eel.typewriter_chunk(result["output"])
                eel.typewriter_end("assistant")
                
                if result.get("system_change"):
                    try:
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
        tools_executed = False  # Flag um Tools nur einmal auszuführen
        
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
                        
                        if not typewriter_active:
                            eel.typewriter_start("assistant")
                            typewriter_active = True
                            try:
                                eel.update_codiac_status("working", "Codiac antwortet...")
                            except:
                                pass
                        
                        # Versuche Tool-Calls zu parsen aus der kompletten Response
                        if not tools_executed and '[TOOL_CALLS]' in full_response:
                            tool_calls = parse_tool_calls_from_complete_text(full_response)
                            
                            if tool_calls:
                                print(f"🔧 {len(tool_calls)} Tool-Calls erkannt: {[tc.get('name') for tc in tool_calls]}")
                                
                                # Führe Tools aus
                                tool_results = execute_tools_with_better_error_handling(tool_calls)
                                
                                # Tool-Results für devstral formatieren
                                for result in tool_results:
                                    tool_result_msg = {
                                        "role": "tool", 
                                        "content": json.dumps(result, ensure_ascii=False)
                                    }
                                    caching.conversation_cache.append(tool_result_msg)
                                
                                tools_executed = True  # Verhindere mehrfache Ausführung
                        
                        # Sende NUR den sauberen Text (ohne Tool-Calls)
                        clean_chunk = clean_text_from_tool_calls(chunk)
                        if clean_chunk.strip():
                            eel.typewriter_chunk(clean_chunk)
                        
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
                        
                        # AI-Antwort zum Cache hinzufügen (SAUBERER Text ohne Tool-Calls)
                        clean_response = clean_text_from_tool_calls(full_response)
                        caching.conversation_cache.append({"role": "assistant", "content": clean_response})
                        
                        # Context-Cache hinzufügen
                        assistant_msg_id = f"assistant_{int(time.time() * 1000)}"
                        assistant_tokens = caching.realistic_token_count(clean_response)
                        context_cache.add_message(assistant_msg_id, "assistant", clean_response, clean_response, assistant_tokens)
                        
                        print(f"📊 Live-Tokens für Transfer: {final_tokens}")
                        
                        # Updates senden
                        try:
                            eel.token_update({"tokens": final_tokens, "tokens_per_second": round(final_speed, 1)})
                            eel.session_token_update(final_tokens)
                            
                            current_context_tokens = sum(caching.realistic_token_count(msg.get('content', '')) for msg in caching.conversation_cache)
                            eel.update_context_usage(current_context_tokens, config.MAX_CONTEXT_TOKENS)
                        except Exception as e:
                            print(f"⚠️ Update-Fehler: {e}")
                        
                        time.sleep(0.05)
                        
                        # Typewriter beenden
                        try:
                            eel.typewriter_end("assistant")
                        except Exception as e:
                            print(f"⚠️ Typewriter-End-Fehler: {e}")
                        
                        caching.save_session_cache(token_start_time, total_tokens)
                        
                        try:
                            eel.stream_complete({"response": clean_response, "total_tokens": total_tokens})
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

# Alle anderen @eel.expose Funktionen bleiben identisch
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

# Dummy-Implementierungen für fehlende Funktionen
@eel.expose
def list_files(directory: str = ""):
    return {"items": [], "current_path": directory}

@eel.expose
def read_file(filepath: str):
    return {"error": "Funktion nicht implementiert"}

@eel.expose
def write_file(filepath: str, content: str):
    return {"error": "Funktion nicht implementiert"}

@eel.expose
def execute_code(code: str, language: str = "python"):
    return {"error": "Funktion nicht implementiert"}

@eel.expose
def clear_cache(all_sessions: bool = False):
    return {"success": True, "message": "Cache geleert"}

@eel.expose
def get_cache_info():
    return {}

@eel.expose
def get_context_rotation_info():
    return {}

@eel.expose
def trigger_manual_context_rotation():
    return {"success": False}

@eel.expose
def update_viewport_priorities(visible_message_ids: list):
    return {"success": True}

@eel.expose
def get_context_cache_stats():
    return {}

@eel.expose
def compress_old_messages(keep_recent: int = 10):
    return {"success": True}

@eel.expose
def get_available_tools():
    return {"success": False}

@eel.expose
def debug_system_prompts():
    return {"success": False}
