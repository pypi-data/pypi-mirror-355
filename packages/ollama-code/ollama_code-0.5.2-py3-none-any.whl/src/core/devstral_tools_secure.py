#!/usr/bin/env python3
"""
Secure Devstral Tool System - Echte Sicherheitsmodi
Implementiert echte Berechtigungen für /base und /hell-out Modi
"""

import os
import json
import subprocess
import shutil
from typing import Dict, List, Any, Optional
from pathlib import Path

class SecureDevstralToolSystem:
    def __init__(self, working_directory: str = None, security_mode: str = 'safe'):
        self.working_directory = working_directory or os.getcwd()
        self.security_mode = security_mode
        
        # Security-Konfiguration laden - DIREKT aus SECURITY_MODES basierend auf übergebenem Modus
        from src import config
        self.security_config = config.SECURITY_MODES[security_mode]
        
        print(f"🛠️ Secure Tools initialisiert: {self.security_config['name']}")
        print(f"   File Access: {self.security_config.get('file_access', False)}")
        print(f"   Terminal Access: {self.security_config.get('terminal_access', False)}")
        print(f"   Allowed Paths: {self.security_config.get('allowed_paths', 'none')}")
        
    def _check_security_permission(self, operation: str, path: str = None) -> bool:
        """Prüft Sicherheitsberechtigung für Operation"""
        # Safe Mode: Keine echten Operationen
        if self.security_mode == 'safe':
            return False
            
        # File-Access prüfen
        if operation in ['read', 'write', 'edit', 'delete'] and not self.security_config.get('file_access', False):
            print(f"❌ {operation} verweigert: Kein File-Access im {self.security_mode} Modus")
            return False
            
        # Terminal-Access prüfen  
        if operation == 'terminal' and not self.security_config.get('terminal_access', False):
            print(f"❌ Terminal-Access verweigert im {self.security_mode} Modus")
            return False
            
        # Path-Sicherheit prüfen
        if path and operation in ['read', 'write', 'edit', 'delete']:
            if not self._is_path_safe(path):
                print(f"❌ Path verweigert: {path} nicht in erlaubtem Bereich")
                return False
            
        # Operation gegen erlaubte Liste prüfen
        allowed_ops = self.security_config.get('file_operations', [])
        if operation in ['read', 'write', 'edit', 'delete'] and operation not in allowed_ops:
            print(f"❌ Operation {operation} nicht erlaubt. Erlaubt: {allowed_ops}")
            return False
            
        return True
        
    def _is_path_safe(self, path: str) -> bool:
        """Prüft ob Pfad basierend auf Sicherheitsmodus erlaubt ist"""
        allowed_paths = self.security_config.get('allowed_paths', 'none')
        
        try:
            if allowed_paths == 'none':
                return False
            elif allowed_paths == 'current_working_directory':
                abs_path = os.path.abspath(path)
                cwd = os.path.abspath(self.working_directory)
                is_safe = abs_path.startswith(cwd)
                if not is_safe:
                    print(f"🚫 Path außerhalb Working Directory: {abs_path} not in {cwd}")
                return is_safe
            elif allowed_paths == 'system_wide':
                return True
            else:
                return False
        except Exception as e:
            print(f"❌ Path-Check Fehler: {e}")
            return False

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Gibt Tool-Definitionen basierend auf Sicherheitsmodus zurück"""
        tools = []
        
        # Safe Mode: Keine echten Tools (werden simuliert)
        if self.security_mode == 'safe':
            print("🔒 Safe Mode: Keine echten Tools verfügbar (Simulation)")
            return []
        
        print(f"🔓 {self.security_mode.upper()} Mode: Echte Tools werden geladen...")
        
        # READ FILE TOOL
        if self._check_security_permission('read'):
            tools.append({
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": f"Liest eine Datei vom Dateisystem ({self.security_mode} mode)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Pfad zur Datei (relativ oder absolut)"
                            },
                            "lines": {
                                "type": "integer", 
                                "description": "Optionale Anzahl Zeilen (Standard: alle)"
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            })
            
        # WRITE FILE TOOL
        if self._check_security_permission('write'):
            tools.append({
                "type": "function", 
                "function": {
                    "name": "write_file",
                    "description": f"Schreibt/erstellt eine Datei ({self.security_mode} mode)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Pfad zur Datei"
                            },
                            "content": {
                                "type": "string",
                                "description": "Dateiinhalt"
                            }
                        },
                        "required": ["file_path", "content"]
                    }
                }
            })
            
        # EDIT FILE TOOL
        if self._check_security_permission('edit'):
            tools.append({
                "type": "function",
                "function": {
                    "name": "edit_file", 
                    "description": f"Bearbeitet eine Datei (find & replace) ({self.security_mode} mode)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Pfad zur Datei"
                            },
                            "old_text": {
                                "type": "string",
                                "description": "Text der ersetzt werden soll"
                            },
                            "new_text": {
                                "type": "string", 
                                "description": "Neuer Text"
                            }
                        },
                        "required": ["file_path", "old_text", "new_text"]
                    }
                }
            })
            
        # DELETE TOOL (nur für hell-out mode)
        if self._check_security_permission('delete'):
            tools.append({
                "type": "function",
                "function": {
                    "name": "delete_file",
                    "description": "GEFÄHRLICH: Löscht Dateien oder Verzeichnisse (nur hell-out mode)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Pfad zur zu löschenden Datei/Verzeichnis"
                            },
                            "recursive": {
                                "type": "boolean",
                                "description": "Für Verzeichnisse: Rekursiv löschen (Standard: false)"
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            })
            
        # TERMINAL TOOL
        if self._check_security_permission('terminal'):
            tools.append({
                "type": "function",
                "function": {
                    "name": "bash_execute",
                    "description": f"Führt Terminal-Befehle aus ({self.security_mode} mode)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Terminal-Befehl"
                            },
                            "description": {
                                "type": "string",
                                "description": "Beschreibung was der Befehl macht"
                            }
                        },
                        "required": ["command"]
                    }
                }
            })
            
        # LIST FILES TOOL (immer verfügbar wenn file_access)
        if self.security_config.get('file_access', False):
            tools.append({
                "type": "function",
                "function": {
                    "name": "list_files",
                    "description": f"Listet Dateien und Verzeichnisse auf ({self.security_mode} mode)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directory": {
                                "type": "string",
                                "description": "Verzeichnis (Standard: current)"
                            },
                            "show_hidden": {
                                "type": "boolean",
                                "description": "Versteckte Dateien anzeigen (Standard: false)"
                            }
                        }
                    }
                }
            })
            
        # SYSTEM INFO TOOL (nur hell-out)
        if self.security_mode == 'hell-out':
            tools.append({
                "type": "function",
                "function": {
                    "name": "system_info",
                    "description": "Zeigt Systeminformationen (nur hell-out mode)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "info_type": {
                                "type": "string",
                                "enum": ["basic", "hardware", "network", "processes"],
                                "description": "Art der gewünschten Informationen"
                            }
                        }
                    }
                }
            })

        print(f"✅ {len(tools)} Tools geladen für {self.security_mode} mode")
        return tools

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Führt ein Tool aus mit Sicherheitsprüfungen"""
        try:
            # Safe Mode: Keine echten Tools
            if self.security_mode == 'safe':
                return {"error": "Tools nicht verfügbar im Safe Mode (Simulation aktiv)"}
            
            print(f"🛠️ Executing {tool_name} in {self.security_mode} mode...")
            
            # Tool-spezifische Ausführung
            if tool_name == "read_file":
                return self._read_file(arguments)
            elif tool_name == "write_file":
                return self._write_file(arguments)
            elif tool_name == "edit_file":
                return self._edit_file(arguments)
            elif tool_name == "delete_file":
                return self._delete_file(arguments)
            elif tool_name == "bash_execute":
                return self._bash_execute(arguments)
            elif tool_name == "list_files":
                return self._list_files(arguments)
            elif tool_name == "system_info":
                return self._system_info(arguments)
            else:
                return {"error": f"Unbekanntes Tool: {tool_name}"}
                
        except Exception as e:
            return {"error": f"Tool-Fehler: {str(e)}"}

    def _read_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Liest eine Datei mit Sicherheitsprüfung"""
        file_path = args.get("file_path")
        lines = args.get("lines")
        
        if not file_path:
            return {"error": "file_path ist erforderlich"}
        
        # Sicherheitsprüfung
        if not self._check_security_permission('read', file_path):
            return {"error": "Berechtigung verweigert für read_file"}
            
        # Pfad auflösen
        if os.path.isabs(file_path):
            full_path = file_path
        else:
            full_path = os.path.join(self.working_directory, file_path)
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                if lines:
                    content = ''.join(f.readlines()[:lines])
                else:
                    content = f.read()
            
            print(f"✅ Datei gelesen: {full_path}")
            return {
                "success": True,
                "content": content,
                "file_path": full_path,
                "lines_read": len(content.split('\n')),
                "security_mode": self.security_mode
            }
        except Exception as e:
            return {"error": f"Fehler beim Lesen von {file_path}: {str(e)}"}

    def _write_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Schreibt eine Datei mit Sicherheitsprüfung"""
        file_path = args.get("file_path")
        content = args.get("content")
        
        if not file_path or content is None:
            return {"error": "file_path und content sind erforderlich"}
        
        # Sicherheitsprüfung
        if not self._check_security_permission('write', file_path):
            return {"error": "Berechtigung verweigert für write_file"}
            
        # Pfad auflösen
        if os.path.isabs(file_path):
            full_path = file_path
        else:
            full_path = os.path.join(self.working_directory, file_path)
            
        try:
            # Verzeichnis erstellen falls nötig
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Datei geschrieben: {full_path}")
            return {
                "success": True,
                "file_path": full_path,
                "bytes_written": len(content.encode('utf-8')),
                "security_mode": self.security_mode
            }
        except Exception as e:
            return {"error": f"Fehler beim Schreiben von {file_path}: {str(e)}"}

    def _edit_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Bearbeitet eine Datei mit Sicherheitsprüfung"""
        file_path = args.get("file_path")
        old_text = args.get("old_text")
        new_text = args.get("new_text")
        
        if not all([file_path, old_text is not None, new_text is not None]):
            return {"error": "file_path, old_text und new_text sind erforderlich"}
        
        # Sicherheitsprüfung
        if not self._check_security_permission('edit', file_path):
            return {"error": "Berechtigung verweigert für edit_file"}
            
        # Pfad auflösen
        if os.path.isabs(file_path):
            full_path = file_path
        else:
            full_path = os.path.join(self.working_directory, file_path)
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if old_text not in content:
                return {"error": f"Text '{old_text[:50]}...' nicht in Datei gefunden"}
            
            new_content = content.replace(old_text, new_text)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"✅ Datei bearbeitet: {full_path}")
            return {
                "success": True,
                "file_path": full_path,
                "replacements": content.count(old_text),
                "security_mode": self.security_mode
            }
        except Exception as e:
            return {"error": f"Fehler beim Bearbeiten von {file_path}: {str(e)}"}

    def _delete_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Löscht Datei/Verzeichnis (nur hell-out mode)"""
        file_path = args.get("file_path")
        recursive = args.get("recursive", False)
        
        if not file_path:
            return {"error": "file_path ist erforderlich"}
        
        # Nur hell-out mode
        if self.security_mode != 'hell-out':
            return {"error": "delete_file nur verfügbar im hell-out mode"}
        
        # Sicherheitsprüfung
        if not self._check_security_permission('delete', file_path):
            return {"error": "Berechtigung verweigert für delete_file"}
            
        # Pfad auflösen
        if os.path.isabs(file_path):
            full_path = file_path
        else:
            full_path = os.path.join(self.working_directory, file_path)
            
        try:
            if os.path.isfile(full_path):
                os.remove(full_path)
                print(f"🗑️ Datei gelöscht: {full_path}")
                return {
                    "success": True,
                    "deleted": full_path,
                    "type": "file",
                    "security_mode": self.security_mode
                }
            elif os.path.isdir(full_path):
                if recursive:
                    shutil.rmtree(full_path)
                    print(f"🗑️ Verzeichnis rekursiv gelöscht: {full_path}")
                else:
                    os.rmdir(full_path)
                    print(f"🗑️ Verzeichnis gelöscht: {full_path}")
                return {
                    "success": True,
                    "deleted": full_path,
                    "type": "directory",
                    "recursive": recursive,
                    "security_mode": self.security_mode
                }
            else:
                return {"error": f"Pfad nicht gefunden: {full_path}"}
        except Exception as e:
            return {"error": f"Fehler beim Löschen von {file_path}: {str(e)}"}

    def _bash_execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Führt Terminal-Befehl aus mit Sicherheitsprüfung"""
        command = args.get("command")
        description = args.get("description", "Terminal-Befehl")
        
        if not command:
            return {"error": "command ist erforderlich"}
        
        # Sicherheitsprüfung
        if not self._check_security_permission('terminal'):
            return {"error": "Terminal-Berechtigung verweigert"}
        
        # Gefährliche Befehle prüfen (nur in hell-out mode erlaubt)
        dangerous_commands = ['rm -rf /', 'format', 'del /s /q C:', 'dd if=/dev/zero', 'mkfs']
        if any(dangerous in command.lower() for dangerous in dangerous_commands):
            if self.security_mode != 'hell-out':
                return {"error": f"Gefährlicher Befehl nur im hell-out mode erlaubt: {command}"}
            print(f"⚠️ GEFÄHRLICHER BEFEHL ERKANNT: {command}")
            
        try:
            print(f"💻 Executing: {command}")
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.working_directory
            )
            
            return {
                "success": result.returncode == 0,
                "command": command,
                "description": description,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "security_mode": self.security_mode,
                "working_directory": self.working_directory
            }
        except subprocess.TimeoutExpired:
            return {"error": f"Befehl-Timeout nach 30s: {command}"}
        except Exception as e:
            return {"error": f"Fehler beim Ausführen von '{command}': {str(e)}"}

    def _list_files(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Listet Dateien mit Sicherheitsprüfung"""
        directory = args.get("directory", ".")
        show_hidden = args.get("show_hidden", False)
        
        # Sicherheitsprüfung
        if not self._check_security_permission('read', directory):
            return {"error": "Berechtigung verweigert für list_files"}
            
        # Pfad auflösen
        if os.path.isabs(directory):
            full_path = directory
        else:
            full_path = os.path.join(self.working_directory, directory)
            
        try:
            files = []
            for item in os.listdir(full_path):
                if not show_hidden and item.startswith('.'):
                    continue
                    
                item_path = os.path.join(full_path, item)
                is_dir = os.path.isdir(item_path)
                
                files.append({
                    "name": item,
                    "type": "directory" if is_dir else "file",
                    "size": os.path.getsize(item_path) if not is_dir else None
                })
            
            return {
                "success": True,
                "directory": full_path,
                "files": files,
                "count": len(files),
                "security_mode": self.security_mode
            }
        except Exception as e:
            return {"error": f"Fehler beim Auflisten von {directory}: {str(e)}"}

    def _system_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Zeigt Systeminformationen (nur hell-out mode)"""
        info_type = args.get("info_type", "basic")
        
        if self.security_mode != 'hell-out':
            return {"error": "system_info nur verfügbar im hell-out mode"}
            
        try:
            if info_type == "basic":
                import platform
                return {
                    "success": True,
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                    "python_version": platform.python_version(),
                    "security_mode": self.security_mode
                }
            else:
                return {"error": f"Info-Type '{info_type}' noch nicht implementiert"}
        except Exception as e:
            return {"error": f"Fehler beim Abrufen der Systeminfo: {str(e)}"}

# Globale Instanz für Kompatibilität
secure_devstral_tools = None

def get_secure_tools(working_directory: str = None, security_mode: str = 'safe'):
    """Factory-Funktion für sichere Tools"""
    global secure_devstral_tools
    secure_devstral_tools = SecureDevstralToolSystem(working_directory, security_mode)
    return secure_devstral_tools