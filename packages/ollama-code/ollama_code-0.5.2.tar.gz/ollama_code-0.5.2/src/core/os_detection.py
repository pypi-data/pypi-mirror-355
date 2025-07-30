#!/usr/bin/env python3
"""
OS Detection und Session-OS-Info Management
Erkennt das Betriebssystem beim Start und stellt die Info für die Session bereit
"""

import os
import json
import platform
from typing import Dict, Any

class OSSessionManager:
    def __init__(self, cache_dir: str = ".atlas_cache"):
        self.cache_dir = cache_dir
        self.os_info_file = os.path.join(cache_dir, "session_os_info.json")
        self._os_info = None
        
    def detect_and_save_os_info(self) -> Dict[str, Any]:
        """Erkennt das OS beim Programmstart und speichert in Session-Datei"""
        print("🔍 Erkenne Betriebssystem für Session...")
        
        system = platform.system().lower()
        
        # Basis-OS-Erkennung
        if system == 'windows':
            os_type = 'windows'
            shell_type = 'cmd'
        elif system == 'linux':
            os_type = 'linux'
            shell_type = 'bash'
        elif system == 'darwin':
            os_type = 'macos'
            shell_type = 'bash'
        else:
            os_type = 'unknown'
            shell_type = 'bash'
        
        # OS-spezifische Befehle definieren
        if os_type == 'windows':
            commands = {
                "list_disks": "wmic diskdrive get size,model,caption /format:table",
                "list_disks_simple": "wmic diskdrive list brief", 
                "disk_usage": "wmic logicaldisk get size,freespace,caption",
                "memory_info": "wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /format:table",
                "cpu_info": "wmic cpu get name,numberofcores,numberoflogicalprocessors /format:table",
                "list_processes": "tasklist",
                "network_info": "ipconfig",
                "list_files": "dir",
                "file_content": "type",
                "search_text": "findstr"
            }
        elif os_type in ['linux', 'macos']:
            commands = {
                "list_disks": "lsblk -d -o NAME,SIZE,TYPE,MODEL" if os_type == 'linux' else "diskutil list",
                "disk_usage": "df -h",
                "memory_info": "free -h" if os_type == 'linux' else "vm_stat",
                "cpu_info": "lscpu" if os_type == 'linux' else "sysctl -n machdep.cpu.brand_string",
                "list_processes": "ps aux",
                "network_info": "ifconfig",
                "list_files": "ls -la",
                "file_content": "cat",
                "search_text": "grep"
            }
        else:
            commands = {}
        
        # Session-OS-Info zusammenstellen
        os_info = {
            "os_type": os_type,
            "system_name": system.title(),
            "shell_type": shell_type,
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "node_name": platform.node(),
            "commands": commands,
            "session_id": int(__import__('time').time() * 1000),  # Eindeutige Session-ID
            "detected_at": __import__('datetime').datetime.now().isoformat()
        }
        
        # Session-Datei speichern
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            with open(self.os_info_file, 'w', encoding='utf-8') as f:
                json.dump(os_info, f, indent=2, ensure_ascii=False)
            
            print(f"💾 OS-Session-Info gespeichert: {os_info['system_name']} ({os_type})")
            print(f"📁 Session-Datei: {self.os_info_file}")
            
        except Exception as e:
            print(f"⚠️ Konnte OS-Session-Info nicht speichern: {e}")
        
        self._os_info = os_info
        return os_info
    
    def load_os_info(self) -> Dict[str, Any]:
        """Lädt OS-Info aus Session-Datei"""
        if self._os_info:
            return self._os_info
        
        try:
            if os.path.exists(self.os_info_file):
                with open(self.os_info_file, 'r', encoding='utf-8') as f:
                    self._os_info = json.load(f)
                    print(f"📱 OS-Session-Info geladen: {self._os_info['system_name']}")
                    return self._os_info
        except Exception as e:
            print(f"⚠️ Konnte OS-Session-Info nicht laden: {e}")
        
        # Fallback: Neu erkennen
        return self.detect_and_save_os_info()
    
    def get_command_for_task(self, task: str) -> str:
        """Gibt den OS-spezifischen Befehl für eine Aufgabe zurück"""
        os_info = self.load_os_info()
        commands = os_info.get("commands", {})
        return commands.get(task, f"echo 'Task {task} not supported'")
    
    def get_system_prompt_os_section(self) -> str:
        """Erstellt OS-spezifischen System-Prompt-Abschnitt"""
        os_info = self.load_os_info()
        os_type = os_info.get("os_type", "unknown")
        system_name = os_info.get("system_name", "Unknown")
        commands = os_info.get("commands", {})
        
        if os_type == "windows":
            return f"""
<OPERATING_SYSTEM>
Erkanntes Betriebssystem: {system_name} (Windows)
Shell: Command Prompt/PowerShell

WICHTIG: Du läufst auf einem Windows-System! Verwende WINDOWS-BEFEHLE:

Hardware-Befehle:
- Festplatten auflisten: `{commands.get('list_disks', 'wmic diskdrive list brief')}`
- Speicherplatz: `{commands.get('disk_usage', 'wmic logicaldisk get size,freespace,caption')}`
- Arbeitsspeicher: `{commands.get('memory_info', 'wmic OS get TotalVisibleMemorySize,FreePhysicalMemory')}`
- CPU-Info: `{commands.get('cpu_info', 'wmic cpu get name,numberofcores')}`

System-Befehle:
- Prozesse: `{commands.get('list_processes', 'tasklist')}`
- Netzwerk: `{commands.get('network_info', 'ipconfig')}`
- Dateien: `{commands.get('list_files', 'dir')}`

NIEMALS Linux-Befehle wie lsblk, df -h, ps aux verwenden!
</OPERATING_SYSTEM>"""
        
        elif os_type in ["linux", "macos"]:
            return f"""
<OPERATING_SYSTEM>
Erkanntes Betriebssystem: {system_name} ({os_type.upper()})
Shell: Bash

Hardware-Befehle:
- Festplatten auflisten: `{commands.get('list_disks', 'lsblk -d')}`
- Speicherplatz: `{commands.get('disk_usage', 'df -h')}`
- Arbeitsspeicher: `{commands.get('memory_info', 'free -h')}`
- CPU-Info: `{commands.get('cpu_info', 'lscpu')}`

System-Befehle:
- Prozesse: `{commands.get('list_processes', 'ps aux')}`
- Netzwerk: `{commands.get('network_info', 'ifconfig')}`
- Dateien: `{commands.get('list_files', 'ls -la')}`
</OPERATING_SYSTEM>"""
        
        else:
            return f"""
<OPERATING_SYSTEM>
Betriebssystem: {system_name} (Unbekannt)
Verwende Standard-Unix-Befehle mit Vorsicht.
</OPERATING_SYSTEM>"""

# Globale Instanz
os_session = OSSessionManager()
