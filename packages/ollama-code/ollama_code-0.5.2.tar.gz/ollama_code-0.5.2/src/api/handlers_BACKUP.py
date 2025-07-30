#!/usr/bin/env python3
"""
API-Handler für die Eel-Schnittstelle.
Alle @eel.expose Funktionen sind hier definiert.
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
session_total_tokens = 0  # Gesamte Session-Tokens
token_start_time = None
last_token_update = 0
typewriter_active = False

def parse_tool_calls(text: str) -> List[Dict[str, Any]]:
    """Verbesserte Tool-Call-Erkennung für devstral mit Fallback-Strategien"""
    import re
    tool_calls = []
    
    print(f"🔍 DEBUG: Parsing Tool-Calls aus Text ({len(text)} chars)")
    print(f"🔍 DEBUG: Text-Preview: {text[:300]}...")
    
    # ERWEITERTE PATTERNS für verschiedene Formate
    patterns = [
        # Standard Format: [TOOL_CALLS][{...}]
        ("Standard", r'\[TOOL_CALLS\]\s*\[(.*?)\]'),
        # Alternative: [TOOL_CALLS] [{...}]
        ("Alternative", r'\[TOOL_CALLS\]\s+\[(.*?)\]'),
        # JSON-Block Format
        ("JSON-Block", r'```json\s*(\{[^}]*"name"[^}]*\})\s*```'),
        # Direktes JSON: {"name": "...", "arguments": {...}}
        ("Direktes JSON", r'\{[^}]*"name"[^}]*"arguments"[^}]*\}'),
        # Function-Call Format
        ("Function-Call", r'"function_call":\s*(\{[^}]*\})'),
    ]
    
    for pattern_name, pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        print(f"🔍 DEBUG: {pattern_name} Pattern: {len(matches)} matches")
        
        for match in matches:
            try:
                # Versuche JSON zu parsen
                if isinstance(match, str):
                    tool_call = json.loads(match.strip())
                else:
                    tool_call = json.loads(match)
                
                # Validiere dass es ein Tool-Call ist
                if 'name' in tool_call:
                    tool_calls.append(tool_call)
                    print(f"✅ DEBUG: Tool-Call gefunden: {tool_call.get('name')}")
                    
            except json.JSONDecodeError as e:
                print(f"❌ DEBUG: JSON-Parse-Fehler für {pattern_name}: {e}")
                continue
    
    # FALLBACK: Intelligente Keyword-basierte Tool-Erkennung
    if not tool_calls:
        print("🔍 DEBUG: Keine Tool-Calls gefunden - aktiviere Fallback-Strategien")
        
        # Erkenne Intent basierend auf Schlüsselwörtern
        intent_keywords = {
            'festplatte': {'tool': 'bash_execute', 'cmd': 'lsblk -d -o NAME,SIZE,TYPE,MODEL', 'desc': 'Liste Festplatten auf'},
            'hard drive': {'tool': 'bash_execute', 'cmd': 'lsblk -d -o NAME,SIZE,TYPE,MODEL', 'desc': 'List hard drives'},
            'disk': {'tool': 'bash_execute', 'cmd': 'df -h', 'desc': 'Show disk usage'},
            'storage': {'tool': 'bash_execute', 'cmd': 'lsblk', 'desc': 'Show storage devices'},
            'dateien': {'tool': 'list_files', 'directory': '.', 'pattern': '*'},
            'files': {'tool': 'list_files', 'directory': '.', 'pattern': '*'},
            'verzeichnis': {'tool': 'list_files', 'directory': '.', 'pattern': '*'},
            'directory': {'tool': 'list_files', 'directory': '.', 'pattern': '*'}
        }
        
        text_lower = text.lower()
        for keyword, action in intent_keywords.items():
            if keyword in text_lower:
                print(f"🔍 DEBUG: Keyword '{keyword}' erkannt - erstelle automatischen Tool-Call")
                
                if action['tool'] == 'bash_execute':
                    auto_tool_call = {
                        "name": "bash_execute",
                        "arguments": {
                            "command": action['cmd'],
                            "description": action['desc']
                        }
                    }
                elif action['tool'] == 'list_files':
                    auto_tool_call = {
                        "name": "list_files",
                        "arguments": {
                            "directory": action.get('directory', '.'),
                            "pattern": action.get('pattern', '*')
                        }
                    }
                
                tool_calls.append(auto_tool_call)
                print(f"✅ DEBUG: Automatischer Tool-Call erstellt: {auto_tool_call['name']}")
                break
    
    print(f"🔍 DEBUG: Insgesamt {len(tool_calls)} Tool-Calls gefunden")
    return tool_calls

def format_tool_update(tool_name: str, result: Dict[str, Any], args: Dict[str, Any] = None) -> str:
    """Formatiert Tool-Updates im Claude Code Style"""
    # Update Codiac Status basierend auf Tool
    try:
        status_map = {
            "read_file": "reading",
            "write_file": "writing", 
            "edit_file": "editing",
            "bash_execute": "executing",
            "list_files": "listing",
            "search_files": "searching"
        }
        
        if tool_name in status_map:
            if result.get("success"):
                eel.update_codiac_status("completed", f"{tool_name} abgeschlossen", temporary=True, duration=2000)
            else:
                eel.update_codiac_status("error", f"Fehler bei {tool_name}", temporary=True, duration=3000)
    except:
        pass  # Ignore status update errors
    
    if result.get("success"):
        if tool_name == "read_file":
            lines = result.get("lines_read", 0)
            file_path = result.get("file_path", "")
            return f"● Read({file_path})\n  ⎿  Read {file_path} ({lines} lines)"
            
        elif tool_name == "write_file":
            file_path = result.get("file_path", "")
            bytes_written = result.get("bytes_written", 0)
            return f"● Write({file_path})\n  ⎿  Created {file_path} ({bytes_written} bytes)"
            
        elif tool_name == "edit_file":
            file_path = result.get("file_path", "")
            replacements = result.get("replacements", 0)
            return f"● Update({file_path})\n  ⎿  Updated {file_path} with {replacements} replacements"
            
        elif tool_name == "bash_execute":
            command = result.get("command", "")
            description = result.get("description", "")
            return f"● Bash({command[:50]}...)\n  ⎿  {description}"
            
        elif tool_name == "list_files":
            count = result.get("count", 0)
            directory = result.get("directory", ".")
            return f"● List({directory})\n  ⎿  Found {count} files"
            
        elif tool_name == "search_files":
            matches = result.get("matches_found", 0)
            pattern = result.get("pattern", "")
            return f"● Search({pattern})\n  ⎿  Found {matches} matches"
    else:
        error = result.get("error", "Unknown error")
        return f"● ❌ Error({tool_name})\n  ⎿  {error}"
    
    return f"● {tool_name}(...)\n  ⎿  Tool executed"

def execute_tool_calls(tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Führt Tool-Calls aus und gibt Ergebnisse zurück"""
    results = []
    
    for tool_call in tool_calls:
        tool_name = tool_call.get("name")
        arguments = tool_call.get("arguments", {})
        
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                results.append({"error": f"Invalid arguments for {tool_name}"})
                continue
        
        # Tool ausführen
        # SICHERE TOOL-AUSFÜHRUNG basierend auf Security Mode
        if atlas_agent.security_mode == 'safe':
            # Safe Mode: Tools werden simuliert
            result = {"error": "Tools nicht verfügbar im Safe Mode (wird simuliert)"}
        else:
            # Base/Hell-out Mode: Echte sichere Tools
            result = atlas_agent.secure_tools.execute_tool(tool_name, arguments)
        
        result["tool_name"] = tool_name
        result["arguments"] = arguments
        result["security_mode"] = atlas_agent.security_mode
        results.append(result)
        
        # Tool-Update senden
        update_text = format_tool_update(tool_name, result, arguments)
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
    """Haupt-Chat-Funktion mit Command-System."""
    global total_tokens, session_total_tokens, token_start_time, typewriter_active, last_token_update
    
    print(f"🔥 DEBUG: atlas_chat aufgerufen mit message: '{message[:50]}...'")
    
    try:
        # COMMAND-SYSTEM: Prüfe ob Nachricht ein Befehl ist
        if command_handler.is_command(message):
            result = command_handler.handle_command(message)
            
            # Sende Command-Antwort direkt an Frontend mit korrekten Eel-Funktionen
            if "error" in result:
                # Verwende typewriter für Fehler
                eel.typewriter_start("assistant")
                eel.typewriter_chunk(f"❌ {result['error']}")
                eel.typewriter_end("assistant")
            else:
                # Verwende typewriter für normale Ausgabe
                eel.typewriter_start("assistant")
                output = result["output"]
                
                # Update Working Directory Display basierend auf Sicherheitsmodus
                if atlas_agent.security_mode == 'safe':
                    # Zeige simuliertes Verzeichnis im UI
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
                
                # System-Änderungen verarbeiten
                if result.get("system_change"):
                    try:
                        eel.update_system_status()
                    except:
                        pass  # Fallback falls Funktion nicht existiert
                if result.get("clear_chat"):
                    try:
                        eel.clear_chat_display()
                    except:
                        pass  # Fallback falls Funktion nicht existiert
                if result.get("new_session"):
                    # Neue Session starten
                    try:
                        session_manager_instance.start_new_session()
                        eel.update_system_status()
                    except:
                        pass  # Fallback
            return
        
        # NORMALE KI-VERARBEITUNG
        print(f"🔥 DEBUG: Starte normale KI-Verarbeitung")
        
        # Update Codiac Status zu "thinking"
        try:
            eel.update_codiac_status("thinking", "Codiac analysiert...")
        except:
            pass
        
        total_tokens = 0
        token_start_time = time.time()
        last_token_update = 0
        typewriter_active = False

        # NEUE OPTIMIERTE METHODE: Verwende die Atlas Agent Systemprompt-Logik
        print(f"🔥 DEBUG: Verwende NEUE call_ollama_with_system_prompt Methode")
        
        # Context-Cache für Token-Tracking beibehalten
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
        pending_tool_calls = []
        
        for line in response_stream.iter_lines():
            line_count += 1
            if line_count <= 3:  # Debug nur erste paar Lines
                print(f"🔥 DEBUG: Stream Line {line_count}: {line[:100] if line else 'Empty'}")
            
            if line:
                try:
                    data = json.loads(line.decode('utf-8'))
                    if 'response' in data:
                        chunk = data['response']
                        full_response += chunk
                        
                        # Prüfe auf Tool-Calls in der bisherigen Response
                        tool_calls = parse_tool_calls(full_response)
                        
                        if not typewriter_active:
                            eel.typewriter_start("assistant")
                            typewriter_active = True
                            # Update Status zu "working" wenn Codiac anfängt zu antworten
                            try:
                                eel.update_codiac_status("working", "Codiac antwortet...")
                            except:
                                pass
                        
                        # Sende nur den neuen Chunk (ohne bereits gesendete Tool-Updates)
                        if not tool_calls or not any(tc for tc in tool_calls if tc not in pending_tool_calls):
                            eel.typewriter_chunk(chunk)
                        
                        # Neue Tool-Calls ausführen
                        new_tool_calls = [tc for tc in tool_calls if tc not in pending_tool_calls]
                        if new_tool_calls:
                            print(f"🔧 Führe {len(new_tool_calls)} Tools aus: {[tc.get('name') for tc in new_tool_calls]}")
                            tool_results = execute_tool_calls(new_tool_calls)
                            pending_tool_calls.extend(new_tool_calls)
                            
                            # Tool-Results für devstral formatieren
                            for i, result in enumerate(tool_results):
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
                        # Finale Berechnung mit total_tokens (die während Stream aktualisiert wurden)
                        final_tokens = total_tokens  # Verwende die Stream-akkumulierten Tokens
                        elapsed = time.time() - token_start_time
                        final_speed = final_tokens / elapsed if elapsed > 0 else 0
                        
                        # AI-Antwort zum Cache hinzufügen BEVOR Token-Updates
                        caching.conversation_cache.append({"role": "assistant", "content": full_response})
                        
                        # AUCH zum Context-Cache hinzufügen
                        assistant_msg_id = f"assistant_{int(time.time() * 1000)}"
                        assistant_tokens = caching.realistic_token_count(full_response)
                        context_cache.add_message(assistant_msg_id, "assistant", full_response, full_response, assistant_tokens)
                        
                        # Live-Tokens an Frontend senden (werden dort zu Session addiert)
                        print(f"📊 Live-Tokens für Transfer: {final_tokens}")
                        
                        # Context-Usage für Frontend berechnen
                        current_context_tokens = sum(caching.realistic_token_count(msg.get('content', '')) for msg in caching.conversation_cache)
                        context_percentage = (current_context_tokens / config.MAX_CONTEXT_TOKENS) * 100
                        
                        # Sende ALLE Updates zusammen - SOFORT mit Fehlerbehandlung
                        try:
                            eel.token_update({"tokens": final_tokens, "tokens_per_second": round(final_speed, 1)})
                        except Exception as e:
                            print(f"⚠️ Token-Update-Fehler: {e}")
                        
                        try:
                            # Sende Live-Tokens an Frontend (werden dort akkumuliert)
                            eel.session_token_update(final_tokens)
                        except Exception as e:
                            print(f"⚠️ Session-Token-Update-Fehler: {e}")
                        
                        try:
                            eel.update_context_usage(current_context_tokens, config.MAX_CONTEXT_TOKENS)
                        except Exception as e:
                            print(f"⚠️ Context-Update-Fehler: {e}")
                        
                        # Kurze Pause damit Frontend Zeit hat Updates zu verarbeiten
                        time.sleep(0.05)
                        
                        # Typewriter beenden NACH Token-Updates
                        try:
                            eel.typewriter_end("assistant")
                        except Exception as e:
                            print(f"⚠️ Typewriter-End-Fehler: {e}")
                        
                        caching.save_session_cache(token_start_time, total_tokens)
                        
                        # INTELLIGENTE CONTEXT-OPTIMIERUNG
                        context_stats = context_cache.get_session_stats()
                        context_usage_percent = context_stats.get('context_usage', 0)
                        
                        # NUR bei kritischem Context-Level optimieren (90%+ statt 85%)
                        if context_usage_percent > 90:
                            print(f"🔄 Context-Optimierung bei {context_usage_percent:.1f}% Auslastung")
                            
                            try:
                                # INTELLIGENTE COLLAPSE-STRATEGIE
                                eel.start_message_collapse({
                                    "reason": f"Context bei {context_usage_percent:.1f}%",
                                    "context_usage": current_context_tokens,
                                    "max_context": config.MAX_CONTEXT_TOKENS,
                                    "should_compress": True
                                })
                                
                                # Komprimiere alte Messages im Cache (behalte letzte 50 bei 120k Context)
                                context_cache.compress_old_messages(keep_recent=50)
                                
                            except Exception as e:
                                print(f"⚠️ Context-Optimierung-Fehler: {e}")
                            
                            # Session-Tokens NICHT zurücksetzen - nur Cache optimieren
                            print("✅ Context optimiert, Session-Tokens bleiben erhalten")
                        
                        try:
                            eel.stream_complete({"response": full_response, "total_tokens": total_tokens})
                            # Status zurück zu "ready" setzen
                            eel.update_codiac_status("ready")
                        except:
                            pass  # Fallback falls JS-Funktion nicht existiert
                        break
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
    except Exception as e:
        print(f"❌ Atlas-Chat-Fehler: {e}")
        eel.stream_error(str(e))
        if typewriter_active:
            eel.typewriter_end("assistant")
        # Status auf error setzen
        try:
            eel.update_codiac_status("error", f"Fehler: {str(e)[:50]}", temporary=True, duration=5000)
        except:
            pass

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
    if os.path.getsize(full_path) > config.MAX_FILE_SIZE:
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
    # Echte Sicherheitsmodi anzeigen
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
def update_viewport_priorities(visible_message_ids: list):
    """Aktualisiert Viewport-Prioritäten für Frustum Culling"""
    try:
        context_cache.update_viewport_priorities(visible_message_ids)
        return {"success": True}
    except Exception as e:
        print(f"❌ Viewport-Update-Fehler: {e}")
        return {"success": False, "error": str(e)}

@eel.expose
def get_context_cache_stats():
    """Gibt Context-Cache-Statistiken zurück"""
    try:
        return context_cache.get_session_stats()
    except Exception as e:
        print(f"❌ Cache-Stats-Fehler: {e}")
        return {"error": str(e)}

@eel.expose
def compress_old_messages(keep_recent: int = 10):
    """Komprimiert alte Nachrichten im Cache"""
    try:
        context_cache.compress_old_messages(keep_recent)
        return {"success": True, "message": f"Alte Nachrichten komprimiert (behalte {keep_recent})"}
    except Exception as e:
        print(f"❌ Komprimierungs-Fehler: {e}")
        return {"success": False, "error": str(e)}

@eel.expose
def get_available_tools():
    """Gibt verfügbare Tools für UI-Anzeige zurück"""
    try:
        if atlas_agent.security_mode in ['base', 'hell-out']:
            tools = devstral_tools.get_tool_definitions()
            return {
                "success": True, 
                "tools": tools,
                "security_mode": atlas_agent.security_mode
            }
        else:
            return {
                "success": False,
                "message": "Tools nur in base/hell-out Modus verfügbar",
                "security_mode": atlas_agent.security_mode
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

@eel.expose
def change_security_mode(new_mode: str):
    """Wechselt den Sicherheitsmodus des Atlas Agents."""
    try:
        # Validiere Modus
        valid_modes = ['safe', 'base', 'hell-out']
        if new_mode not in valid_modes:
            return {"success": False, "error": f"Ungültiger Modus: {new_mode}"}
        
        # Wechsle den Modus im Atlas Agent
        old_mode = atlas_agent.security_mode
        atlas_agent.change_security_mode(new_mode)
        
        # Update Tools basierend auf neuem Modus
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
def debug_system_prompts():
    """
    Debug-Funktion um alle Systemprompts zu testen
    """
    try:
        modes = ['safe', 'base', 'hell-out']
        results = {}
        
        print("🔧 DEBUG: Teste alle Systemprompts...")
        
        for mode in modes:
            print(f"\n{'='*50}")
            print(f"Testing Mode: {mode}")
            print(f"{'='*50}")
            
            # Modus temporär wechseln
            original_mode = atlas_agent.security_mode
            atlas_agent.change_security_mode(mode)
            
            # System-Prompt abrufen
            system_prompt = atlas_agent.get_system_prompt()
            
            results[mode] = {
                "length": len(system_prompt),
                "preview": system_prompt[:300] + "..." if len(system_prompt) > 300 else system_prompt,
                "has_tools_section": "TOOL SYSTEM:" in system_prompt,
                "has_security_section": any(section in system_prompt for section in ["SECURITY_RESTRICTIONS", "UNRESTRICTED_ACCESS", "SANDBOX_SIMULATION"]),
                "mode_indicator": mode.upper() in system_prompt
            }
            
            print(f"System Prompt Length: {len(system_prompt)}")
            print(f"System Prompt Preview:")
            print(system_prompt[:300] + "..." if len(system_prompt) > 300 else system_prompt)
            
            # Zurück zum ursprünglichen Modus
            atlas_agent.change_security_mode(original_mode)
        
        print(f"\n✅ Systemprompt-Tests abgeschlossen")
        return {"success": True, "results": results}
        
    except Exception as e:
        print(f"❌ Fehler beim Testen der Systemprompts: {e}")
        return {"success": False, "error": str(e)}

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