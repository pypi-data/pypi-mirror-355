#!/usr/bin/env python3
"""
Devstral Tool System - Claude Code Style Tools für Agent-Coder
Implementiert Tools für devstral:24b Agent-Modell mit Cross-Platform Support
"""

import os
import json
import subprocess
import platform
from typing import Dict, List, Any, Optional
from pathlib import Path

class DevstralToolSystem:
    def __init__(self, working_directory: str = None, security_mode: str = 'safe'):
        self.working_directory = working_directory or os.getcwd()
        self.tools_enabled = True
        self.security_mode = security_mode
        
        # OS-Erkennung
        self.current_os = self._detect_os()
        
        # Security-Konfiguration laden
        from src import config
        security_info = config.get_current_security_info()
        self.security_config = security_info['config']
        
        print(f"🛠️ Tools initialisiert im {self.security_config['name']} auf {self.current_os}")
        
        # Prüfe ob wir in einem neuen Projekt arbeiten
        self._check_and_setup_project()
        
    def _detect_os(self) -> str:
        """Erkennt das aktuelle Betriebssystem"""
        system = platform.system().lower()
        if system == 'windows':
            return 'windows'
        elif system == 'linux':
            return 'linux'
        elif system == 'darwin':
            return 'macos'
        else:
            return 'unknown'
    
    def _translate_command(self, command: str) -> str:
        """Übersetzt Befehle basierend auf dem aktuellen OS"""
        # Command-Mappings für verschiedene Betriebssysteme
        command_mappings = {
            'linux': {
                # Linux-spezifische Befehle bleiben unverändert
                'lsblk -d -o NAME,SIZE,TYPE,MODEL': 'lsblk -d -o NAME,SIZE,TYPE,MODEL',
                'df -h': 'df -h',
                'ls -la': 'ls -la',
                'ps aux': 'ps aux',
                'free -h': 'free -h',
                'uname -a': 'uname -a'
            },
            'windows': {
                # Linux-zu-Windows Übersetzungen
                'lsblk -d -o NAME,SIZE,TYPE,MODEL': 'wmic diskdrive get size,model,caption /format:table',
                'lsblk': 'wmic diskdrive get size,model,caption /format:table',
                'df -h': 'wmic logicaldisk get size,freespace,caption',
                'ls -la': 'dir',
                'ls': 'dir',
                'ps aux': 'tasklist',
                'ps': 'tasklist', 
                'free -h': 'wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /format:table',
                'uname -a': 'systeminfo | findstr /B /C:"OS Name" /C:"OS Version" /C:"System Type"',
                'cat': 'type',
                'grep': 'findstr',
                'which': 'where',
                'pwd': 'cd',
                'clear': 'cls',
                'chmod': 'icacls',
                'top': 'tasklist',
                'mount': 'wmic logicaldisk get caption,description,filesystem',
                'ifconfig': 'ipconfig',
                'netstat': 'netstat'
            },
            'macos': {
                # Linux-zu-macOS Übersetzungen
                'lsblk -d -o NAME,SIZE,TYPE,MODEL': 'diskutil list',
                'lsblk': 'diskutil list',
                'df -h': 'df -h',
                'ls -la': 'ls -la',
                'ps aux': 'ps aux',
                'free -h': 'vm_stat',
                'uname -a': 'uname -a'
            }
        }
        
        # Direkte Übersetzung suchen
        if self.current_os in command_mappings:
            os_commands = command_mappings[self.current_os]
            if command in os_commands:
                translated = os_commands[command]
                print(f"🔄 Befehl übersetzt: '{command}' → '{translated}' ({self.current_os})")
                return translated
        
        # Intelligente Teil-Übersetzung für komplexere Befehle
        return self._smart_command_translation(command)
    
    def _fix_malformed_command(self, command: str) -> str:
        """Korrigiert häufige Befehlsfehler wie fehlende Leerzeichen"""
        print(f"🔧 DEBUG: _fix_malformed_command eingegangen: '{command}'")
        
        # Häufige Korrekturen für zusammengeschriebene Befehle
        fixes = {
            # lsblk Varianten
            'lsblk-d-oNAME,SIZE,TYPE,MODEL': 'lsblk -d -o NAME,SIZE,TYPE,MODEL',
            'lsblk-d': 'lsblk -d',
            'lsblk-o': 'lsblk -o NAME,SIZE,TYPE,MODEL',
            'lsblkphysical': 'lsblk -d -o NAME,SIZE,TYPE,MODEL',
            'lsblkdisks': 'lsblk -d -o NAME,SIZE,TYPE,MODEL',
            
            # df Varianten
            'df-h': 'df -h',
            'dfh': 'df -h',
            
            # ls Varianten
            'ls-la': 'ls -la',
            'ls-l': 'ls -l',
            'lsla': 'ls -la',
            'lsl': 'ls -l',
            
            # ps Varianten
            'psaux': 'ps aux',
            'ps-aux': 'ps aux',
            
            # free Varianten
            'free-h': 'free -h',
            'freeh': 'free -h',
        }
        
        # Direkte Korrektur
        if command in fixes:
            corrected = fixes[command]
            print(f"🔧 DEBUG: Direktkorrektur angewendet: '{command}' → '{corrected}'")
            return corrected
        
        # Pattern-basierte Korrekturen
        import re
        
        # Korrigiere lsblk mit zusammenhängenden Parametern
        if command.startswith('lsblk'):
            # Beispiel: lsblk-d-oNAME,SIZE,TYPE,MODEL → lsblk -d -o NAME,SIZE,TYPE,MODEL
            corrected = re.sub(r'lsblk-([do])-o([A-Z,]+)', r'lsblk -\1 -o \2', command)
            if corrected != command:
                print(f"🔧 DEBUG: lsblk Pattern-Korrektur: '{command}' → '{corrected}'")
                return corrected
            
            # Fallback für jede lsblk-Variation
            if command != 'lsblk':
                print(f"🔧 DEBUG: lsblk Fallback-Korrektur: '{command}' → 'lsblk -d -o NAME,SIZE,TYPE,MODEL'")
                return 'lsblk -d -o NAME,SIZE,TYPE,MODEL'
        
        # Fallback: Originaler Befehl
        print(f"🔧 DEBUG: Keine Korrektur nötig: '{command}'")
        return command
    
    def _smart_command_translation(self, command: str) -> str:
        """Intelligente Befehlsübersetzung für komplexere Fälle"""
        if self.current_os == 'windows':
            # Häufige Linux-Befehle für Windows anpassen
            if command.startswith('lsblk'):
                if '-d' in command and '-o' in command:
                    return 'wmic diskdrive get size,model,caption /format:table'
                else:
                    return 'wmic diskdrive get size,model,caption /format:table'
            
            elif command.startswith('ls '):
                return command.replace('ls ', 'dir ')
            
            elif command.startswith('cat '):
                return command.replace('cat ', 'type ')
            
            elif command.startswith('grep '):
                return command.replace('grep ', 'findstr ')
            
            elif command.startswith('ps '):
                return 'tasklist'
            
            elif 'df -h' in command:
                return 'wmic logicaldisk get size,freespace,caption'
            
            elif 'free' in command:
                return 'wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /format:table'
        
        elif self.current_os == 'macos':
            # macOS-spezifische Anpassungen
            if command.startswith('lsblk'):
                return 'diskutil list'
        
        # Fallback: Originalbefehl zurückgeben
        return command
    
    def _check_and_setup_project(self):
        """Prüft ob aktuelles Verzeichnis ein Projekt ist und setzt CODIAC.md auf"""
        try:
            from src.core.claude_md_reader import set_current_project
            current_path = Path(self.working_directory)
            set_current_project(current_path)
        except Exception as e:
            print(f"⚠️ Projekt-Setup-Fehler: {e}")
        
    def _check_security_permission(self, operation: str, path: str = None) -> bool:
        """Prüft Sicherheitsberechtigung für Operation"""
        # Safe Mode: Keine echten Operationen
        if self.security_mode == 'safe':
            return False
            
        # File-Access prüfen
        if operation in ['read', 'write', 'edit', 'delete'] and not self.security_config.get('file_access', False):
            return False
            
        # Terminal-Access prüfen  
        if operation == 'terminal' and not self.security_config.get('terminal_access', False):
            return False
            
        # Path-Sicherheit prüfen
        if path and operation in ['read', 'write', 'edit', 'delete']:
            return self._is_path_safe(path)
            
        # Operation gegen erlaubte Liste prüfen
        allowed_ops = self.security_config.get('file_operations', [])
        if operation in ['read', 'write', 'edit', 'delete'] and operation not in allowed_ops:
            return False
            
        return True
        
    def _is_path_safe(self, path: str) -> bool:
        """Prüft ob Pfad basierend auf Sicherheitsmodus erlaubt ist"""
        allowed_paths = self.security_config.get('allowed_paths', 'none')
        
        if allowed_paths == 'none':
            return False
        elif allowed_paths == 'current_working_directory':
            abs_path = os.path.abspath(path)
            cwd = os.path.abspath(self.working_directory)
            return abs_path.startswith(cwd)
        elif allowed_paths == 'system_wide':
            return True
        else:
            return False
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Gibt Tool-Definitionen basierend auf Sicherheitsmodus zurück"""
        tools = []
        
        # Safe Mode: Keine echten Tools, nur Simulation
        if self.security_mode == 'safe':
            return self._get_simulated_tools()
        
        # Base/Hell-out Mode: Echte Tools basierend auf Berechtigungen
        if self._check_security_permission('read'):
            tools.extend([
                {
                    "type": "function",
                    "function": {
                        "name": "read_file",
                        "description": "Liest eine Datei vom lokalen Dateisystem",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "Absoluter oder relativer Pfad zur Datei"
                                },
                                "lines": {
                                    "type": "integer", 
                                    "description": "Optionale Anzahl Zeilen (Standard: alle)"
                                }
                            },
                            "required": ["file_path"]
                        }
                    }
                },
                {
                    "type": "function", 
                    "function": {
                        "name": "write_file",
                        "description": "Schreibt oder erstellt eine Datei",
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
                },
                {
                    "type": "function",
                    "function": {
                        "name": "edit_file", 
                        "description": "Bearbeitet eine bestehende Datei (find & replace)",
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
                },
                {
                    "type": "function",
                    "function": {
                        "name": "bash_execute",
                        "description": f"Führt einen Systembefehl aus (automatische OS-Erkennung: {self.current_os})",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "command": {
                                    "type": "string",
                                    "description": "Systembefehl (wird automatisch für das aktuelle OS übersetzt)"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Kurze Beschreibung was der Befehl macht"
                                }
                            },
                            "required": ["command"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "list_files",
                        "description": "Listet Dateien in einem Verzeichnis auf",
                        "parameters": {
                            "type": "object", 
                            "properties": {
                                "directory": {
                                    "type": "string",
                                    "description": "Verzeichnispfad (Standard: aktuelles Verzeichnis)"
                                },
                                "pattern": {
                                    "type": "string",
                                    "description": "Optionales Dateimuster (z.B. '*.py')"
                                }
                            },
                            "required": []
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "search_files",
                        "description": "Sucht nach Text in Dateien (grep-ähnlich)",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "pattern": {
                                    "type": "string", 
                                    "description": "Suchpattern"
                                },
                                "file_pattern": {
                                    "type": "string",
                                    "description": "Dateimuster (z.B. '*.py')"
                                },
                                "directory": {
                                    "type": "string",
                                    "description": "Suchverzeichnis"
                                }
                            },
                            "required": ["pattern"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "system_info",
                        "description": "Zeigt Systeminformationen an (OS-spezifisch optimiert)",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "info_type": {
                                    "type": "string",
                                    "description": "Art der Information: 'disks', 'memory', 'cpu', 'network', 'all'",
                                    "enum": ["disks", "memory", "cpu", "network", "all"]
                                }
                            },
                            "required": ["info_type"]
                        }
                    }
                }
            ])
        
        return tools
    
    def _get_simulated_tools(self) -> List[Dict[str, Any]]:
        """Gibt simulierte Tools für Safe Mode zurück"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "read_file_simulation",
                    "description": "SIMULATION: Liest eine Datei (Safe Mode - nur Simulation)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Pfad zur Datei (wird nur simuliert)"
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file_simulation",
                    "description": "SIMULATION: Schreibt eine Datei (Safe Mode - nur Simulation)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Pfad zur Datei (wird nur simuliert)"
                            },
                            "content": {
                                "type": "string",
                                "description": "Dateiinhalt (wird nur simuliert)"
                            }
                        },
                        "required": ["file_path", "content"]
                    }
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Führt ein Tool aus und gibt das Ergebnis zurück"""
        try:
            if tool_name == "read_file":
                return self._read_file(arguments)
            elif tool_name == "write_file":
                return self._write_file(arguments)
            elif tool_name == "edit_file":
                return self._edit_file(arguments)
            elif tool_name == "bash_execute":
                return self._bash_execute(arguments)
            elif tool_name == "list_files":
                return self._list_files(arguments)
            elif tool_name == "search_files":
                return self._search_files(arguments)
            elif tool_name == "system_info":
                return self._system_info(arguments)
            else:
                return {"error": f"Unbekanntes Tool: {tool_name}"}
        except Exception as e:
            return {"error": f"Tool-Fehler: {str(e)}"}
    
    def _read_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Liest eine Datei"""
        file_path = args.get("file_path")
        lines = args.get("lines")
        
        if not file_path:
            return {"error": "file_path ist erforderlich"}
            
        full_path = os.path.join(self.working_directory, file_path)
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                if lines:
                    content = ''.join(f.readlines()[:lines])
                else:
                    content = f.read()
            
            return {
                "success": True,
                "content": content,
                "file_path": full_path,
                "lines_read": len(content.split('\n'))
            }
        except Exception as e:
            return {"error": f"Fehler beim Lesen von {file_path}: {str(e)}"}
    
    def _write_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Schreibt eine Datei"""
        file_path = args.get("file_path")
        content = args.get("content")
        
        if not file_path or content is None:
            return {"error": "file_path und content sind erforderlich"}
            
        full_path = os.path.join(self.working_directory, file_path)
        
        try:
            # Erstelle Verzeichnis falls nötig
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "file_path": full_path,
                "bytes_written": len(content.encode('utf-8'))
            }
        except Exception as e:
            return {"error": f"Fehler beim Schreiben von {file_path}: {str(e)}"}
    
    def _edit_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Bearbeitet eine Datei"""
        file_path = args.get("file_path")
        old_text = args.get("old_text")
        new_text = args.get("new_text")
        
        if not all([file_path, old_text is not None, new_text is not None]):
            return {"error": "file_path, old_text und new_text sind erforderlich"}
            
        full_path = os.path.join(self.working_directory, file_path)
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if old_text not in content:
                return {"error": f"Text '{old_text[:50]}...' nicht in Datei gefunden"}
            
            new_content = content.replace(old_text, new_text)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return {
                "success": True,
                "file_path": full_path,
                "replacements": content.count(old_text)
            }
        except Exception as e:
            return {"error": f"Fehler beim Bearbeiten von {file_path}: {str(e)}"}
    
    def _bash_execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Führt Systembefehl aus mit automatischer OS-Anpassung"""
        command = args.get("command")
        description = args.get("description", "Systembefehl ausführen")
        
        if not command:
            return {"error": "command ist erforderlich"}
        
        # 🔧 DEBUG: Eingehenden Befehl protokollieren
        print(f"🔧 DEBUG: Eingehender Befehl: '{command}'")
        print(f"🔧 DEBUG: Aktuelles OS: {self.current_os}")
        
        # Robuste Befehlskorrektur vor Übersetzung
        corrected_command = self._fix_malformed_command(command)
        print(f"🔧 DEBUG: Korrigierter Befehl: '{corrected_command}'")
        
        # Befehl für aktuelles OS übersetzen
        translated_command = self._translate_command(corrected_command)
        print(f"🔧 DEBUG: Übersetzter Befehl: '{translated_command}'")
        
        try:
            # Für Windows: cmd.exe verwenden, für Unix-Systeme: shell
            if self.current_os == 'windows':
                # Windows-spezifische Ausführung
                result = subprocess.run(
                    translated_command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=self.working_directory
                )
            else:
                # Unix-spezifische Ausführung
                result = subprocess.run(
                    translated_command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=self.working_directory
                )
            
            return {
                "success": result.returncode == 0,
                "original_command": command,
                "corrected_command": corrected_command,
                "translated_command": translated_command,
                "os": self.current_os,
                "description": description,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "debug_info": {
                    "os_detected": self.current_os,
                    "command_fixed": corrected_command != command,
                    "command_translated": translated_command != corrected_command
                }
            }
        except subprocess.TimeoutExpired:
            return {
                "error": "Befehl-Timeout (30s überschritten)",
                "original_command": command,
                "corrected_command": corrected_command,
                "translated_command": translated_command
            }
        except Exception as e:
            # Fallback für Hardware-Abfragen mit alternativen Befehlen
            if "festplatte" in description.lower() or "disk" in description.lower():
                print(f"🔧 DEBUG: Hardware-Abfrage fehlgeschlagen, versuche Fallback...")
                fallback_result = self._hardware_fallback()
                if fallback_result:
                    return fallback_result
            
            return {
                "error": f"Befehl-Fehler: {str(e)}",
                "original_command": command,
                "corrected_command": corrected_command,
                "translated_command": translated_command,
                "debug_info": {
                    "os_detected": self.current_os,
                    "command_fixed": corrected_command != command,
                    "command_translated": translated_command != corrected_command,
                    "error_type": type(e).__name__
                }
            }
    
    def _system_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Neue Methode für OS-spezifische Systeminformationen"""
        info_type = args.get("info_type", "all")
        
        try:
            result = {
                "success": True,
                "os": self.current_os,
                "info_type": info_type,
                "data": {}
            }
            
            if info_type in ["disks", "all"]:
                if self.current_os == 'windows':
                    disk_cmd = 'wmic diskdrive get size,model,caption /format:table'
                elif self.current_os == 'macos':
                    disk_cmd = 'diskutil list'
                else:  # Linux
                    disk_cmd = 'lsblk -d -o NAME,SIZE,TYPE,MODEL'
                
                disk_result = subprocess.run(disk_cmd, shell=True, capture_output=True, text=True, timeout=10)
                result["data"]["disks"] = {
                    "command": disk_cmd,
                    "output": disk_result.stdout,
                    "success": disk_result.returncode == 0
                }
            
            if info_type in ["memory", "all"]:
                if self.current_os == 'windows':
                    mem_cmd = 'wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /format:table'
                elif self.current_os == 'macos':
                    mem_cmd = 'vm_stat'
                else:  # Linux
                    mem_cmd = 'free -h'
                
                mem_result = subprocess.run(mem_cmd, shell=True, capture_output=True, text=True, timeout=10)
                result["data"]["memory"] = {
                    "command": mem_cmd,
                    "output": mem_result.stdout,
                    "success": mem_result.returncode == 0
                }
            
            if info_type in ["cpu", "all"]:
                if self.current_os == 'windows':
                    cpu_cmd = 'wmic cpu get name,numberofcores,numberoflogicalprocessors /format:table'
                else:  # Linux/macOS
                    cpu_cmd = 'cat /proc/cpuinfo | grep "model name" | head -1' if self.current_os == 'linux' else 'sysctl -n machdep.cpu.brand_string'
                
                cpu_result = subprocess.run(cpu_cmd, shell=True, capture_output=True, text=True, timeout=10)
                result["data"]["cpu"] = {
                    "command": cpu_cmd,
                    "output": cpu_result.stdout,
                    "success": cpu_result.returncode == 0
                }
            
            return result
            
        except Exception as e:
            return {"error": f"Systeminfo-Fehler: {str(e)}"}
    
    def _hardware_fallback(self) -> Dict[str, Any]:
        """Fallback-Methode für Hardware-Abfragen wenn normale Befehle fehlschlagen"""
        print(f"🔧 DEBUG: _hardware_fallback für {self.current_os}")
        
        try:
            if self.current_os == 'windows':
                # Windows PowerShell Fallback
                fallback_commands = [
                    'Get-PhysicalDisk | Select-Object DeviceID, Size, MediaType, FriendlyName',
                    'wmic diskdrive list brief',
                    'fsutil fsinfo drives'
                ]
                
                for cmd in fallback_commands:
                    try:
                        result = subprocess.run(
                            f'powershell -Command "{cmd}"',
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=15,
                            cwd=self.working_directory
                        )
                        
                        if result.returncode == 0 and result.stdout.strip():
                            return {
                                "success": True,
                                "original_command": "hardware_fallback",
                                "fallback_command": cmd,
                                "os": self.current_os,
                                "description": "Hardware-Fallback (PowerShell)",
                                "stdout": result.stdout,
                                "stderr": result.stderr,
                                "return_code": result.returncode
                            }
                    except:
                        continue
                        
                # Letzte Alternative: Einfache Laufwerksliste
                try:
                    result = subprocess.run(
                        'wmic logicaldisk get size,freespace,caption',
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=10,
                        cwd=self.working_directory
                    )
                    
                    if result.returncode == 0:
                        return {
                            "success": True,
                            "original_command": "hardware_fallback",
                            "fallback_command": "wmic logicaldisk",
                            "os": self.current_os,
                            "description": "Laufwerks-Info (Fallback)",
                            "stdout": result.stdout + "\n\n📝 Hinweis: Dies sind Laufwerke/Partitionen. Für physische Festplatten verwende system_info.",
                            "stderr": result.stderr,
                            "return_code": result.returncode
                        }
                except:
                    pass
                    
            else:  # Linux/macOS
                fallback_commands = [
                    'fdisk -l 2>/dev/null | grep "Disk /"',
                    'ls /dev/sd* /dev/nvme* 2>/dev/null',
                    'df -h'
                ]
                
                for cmd in fallback_commands:
                    try:
                        result = subprocess.run(
                            cmd,
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=15,
                            cwd=self.working_directory
                        )
                        
                        if result.returncode == 0 and result.stdout.strip():
                            return {
                                "success": True,
                                "original_command": "hardware_fallback",
                                "fallback_command": cmd,
                                "os": self.current_os,
                                "description": "Hardware-Fallback (Unix)",
                                "stdout": result.stdout,
                                "stderr": result.stderr,
                                "return_code": result.returncode
                            }
                    except:
                        continue
            
            return None  # Kein Fallback erfolgreich
            
        except Exception as e:
            print(f"⚠️ Hardware-Fallback-Fehler: {e}")
            return None
    
    def _list_files(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Listet Dateien auf"""
        directory = args.get("directory", ".")
        pattern = args.get("pattern", "*")
        
        full_dir = os.path.join(self.working_directory, directory)
        
        try:
            from glob import glob
            search_pattern = os.path.join(full_dir, pattern)
            files = glob(search_pattern)
            
            file_list = []
            for file_path in files:
                rel_path = os.path.relpath(file_path, self.working_directory)
                is_dir = os.path.isdir(file_path)
                size = 0 if is_dir else os.path.getsize(file_path)
                
                file_list.append({
                    "name": os.path.basename(file_path),
                    "path": rel_path,
                    "is_directory": is_dir,
                    "size": size
                })
            
            return {
                "success": True,
                "directory": directory,
                "pattern": pattern,
                "files": file_list,
                "count": len(file_list)
            }
        except Exception as e:
            return {"error": f"Fehler beim Auflisten: {str(e)}"}
    
    def _search_files(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Sucht in Dateien"""
        pattern = args.get("pattern")
        file_pattern = args.get("file_pattern", "*.py")
        directory = args.get("directory", ".")
        
        if not pattern:
            return {"error": "pattern ist erforderlich"}
            
        full_dir = os.path.join(self.working_directory, directory)
        
        try:
            import re
            from glob import glob
            
            search_files = glob(os.path.join(full_dir, "**", file_pattern), recursive=True)
            matches = []
            
            for file_path in search_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            rel_path = os.path.relpath(file_path, self.working_directory)
                            matches.append({
                                "file": rel_path,
                                "line": line_num,
                                "content": line.strip(),
                                "match": pattern
                            })
                except:
                    continue  # Ignoriere nicht-lesbare Dateien
            
            return {
                "success": True,
                "pattern": pattern,
                "matches": matches,
                "files_searched": len(search_files),
                "matches_found": len(matches)
            }
        except Exception as e:
            return {"error": f"Such-Fehler: {str(e)}"}

# Globale Tool-System Instanz
devstral_tools = DevstralToolSystem()