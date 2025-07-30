#!/usr/bin/env python3
"""
Command Handler für Chat-Befehle
Verarbeitet alle Nachrichten, die mit / beginnen
"""

import os
from typing import Dict, Any, List
from src import config

class CommandHandler:
    def __init__(self):
        self.commands = {
            # Sicherheitsmodus-Befehle
            'security': self._cmd_security,
            'safe': lambda: self._set_security_mode('safe'),
            'sandbox': lambda: self._set_security_mode('safe'),
            'base': lambda: self._set_security_mode('base'),
            'hell-out': lambda: self._set_security_mode('hell-out'),
            
            # Auto-Accept Befehle
            'auto-accept': self._cmd_auto_accept,
            'autoaccept': self._cmd_auto_accept,
            
            # System-Befehle
            'status': self._cmd_status,
            'context': self._cmd_context,
            'session': self._cmd_session,
            'clear': self._cmd_clear,
            'help': self._cmd_help,
            
            # Datei-Befehle
            'ls': self._cmd_ls,
            'pwd': self._cmd_pwd,
            'cd': self._cmd_cd,
            'read': self._cmd_read,
            'edit': self._cmd_edit,
            
            # Terminal-Befehle
            'exec': self._cmd_exec,
            'shell': self._cmd_shell,
        }
    
    def is_command(self, message: str) -> bool:
        """Prüft ob eine Nachricht ein Command ist"""
        return message.strip().startswith('/')
    
    def handle_command(self, message: str) -> Dict[str, Any]:
        """Verarbeitet einen Command und gibt Antwort zurück"""
        command_line = message.strip()[1:]  # / entfernen
        parts = command_line.split()
        
        if not parts:
            return {"error": "Leerer Befehl. Gib /help für Hilfe ein."}
        
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        if command in self.commands:
            try:
                if args:
                    return self.commands[command](args)
                else:
                    return self.commands[command]()
            except Exception as e:
                return {"error": f"Fehler beim Ausführen von /{command}: {str(e)}"}
        else:
            return {"error": f"Unbekannter Befehl: /{command}. Gib /help für verfügbare Befehle ein."}
    
    # SICHERHEITSMODUS-BEFEHLE
    def _cmd_security(self, args: List[str] = None) -> Dict[str, Any]:
        """Sicherheitsmodus-Befehle"""
        if not args:
            # Status anzeigen
            info = config.get_current_security_info()
            return {
                "output": f"🔒 Aktueller Sicherheitsmodus: {info['config']['name']}\n"
                         f"📝 {info['config']['description']}\n"
                         f"🤖 Auto-Accept: {'Ein' if info['auto_accept'] else 'Aus'}"
            }
        
        subcommand = args[0].lower()
        if subcommand in ['safe', 'base', 'hell-out']:
            return self._set_security_mode(subcommand)
        elif subcommand == 'status':
            return self._cmd_security()
        else:
            return {"error": f"Unbekannter Security-Befehl: {subcommand}"}
    
    def _set_security_mode(self, mode: str) -> Dict[str, Any]:
        """Setzt den Sicherheitsmodus"""
        try:
            config.set_security_mode(mode)
            info = config.get_current_security_info()
            return {
                "output": f"✅ Sicherheitsmodus geändert zu: {info['config']['name']}\n"
                         f"📝 {info['config']['description']}\n"
                         f"🤖 Auto-Accept: {'Ein' if info['auto_accept'] else 'Aus'}",
                "system_change": True
            }
        except ValueError as e:
            return {"error": str(e)}
    
    # AUTO-ACCEPT BEFEHLE
    def _cmd_auto_accept(self, args: List[str] = None) -> Dict[str, Any]:
        """Auto-Accept Befehle"""
        if not args:
            # Status anzeigen
            status = "Ein" if config.AUTO_ACCEPT_ENABLED else "Aus"
            return {"output": f"🤖 Auto-Accept: {status}"}
        
        subcommand = args[0].lower()
        if subcommand in ['on', 'ein', 'true', '1']:
            config.AUTO_ACCEPT_ENABLED = True
            return {"output": "🤖 Auto-Accept aktiviert", "system_change": True}
        elif subcommand in ['off', 'aus', 'false', '0']:
            config.AUTO_ACCEPT_ENABLED = False
            return {"output": "🤖 Auto-Accept deaktiviert", "system_change": True}
        elif subcommand in ['toggle', 'switch']:
            config.toggle_auto_accept()
            status = "Ein" if config.AUTO_ACCEPT_ENABLED else "Aus"
            return {"output": f"🤖 Auto-Accept umgeschaltet: {status}", "system_change": True}
        elif subcommand == 'status':
            return self._cmd_auto_accept()
        else:
            return {"error": f"Unbekannter Auto-Accept-Befehl: {subcommand}"}
    
    # SYSTEM-BEFEHLE
    def _cmd_status(self) -> Dict[str, Any]:
        """Zeigt Systemstatus"""
        security_info = config.get_current_security_info()
        env_info = config.get_current_environment_info()
        
        status = f"""📊 SYSTEM STATUS
🔒 Sicherheit: {security_info['config']['name']}
🌐 Umgebung: {env_info['mode']} ({env_info['url']})
🤖 Auto-Accept: {'Ein' if security_info['auto_accept'] else 'Aus'}
📁 Arbeitsverzeichnis: {os.getcwd()}
🧠 Max Tokens: {config.MAX_CONTEXT_TOKENS}
⚡ Token Threshold: {int(config.MAX_CONTEXT_TOKENS * config.CONTEXT_ROTATION_THRESHOLD)}"""
        
        return {"output": status}
    
    def _cmd_context(self) -> Dict[str, Any]:
        """Zeigt Context-Usage"""
        # TODO: Echte Token-Zählung implementieren
        return {"output": f"🧠 Context: 0/{config.MAX_CONTEXT_TOKENS} Tokens (0%)"}
    
    def _cmd_session(self, args: List[str] = None) -> Dict[str, Any]:
        """Session-Befehle"""
        if not args:
            return {"output": "📝 Session-Befehle: new, info, clear, tokens"}
        
        subcommand = args[0].lower()
        if subcommand == 'new':
            return {"output": "🆕 Neue Session wird gestartet...", "new_session": True}
        elif subcommand == 'info':
            return {"output": "📝 Session-Info: TODO implementieren"}
        elif subcommand == 'clear':
            return {"output": "🧹 Session geleert", "clear_session": True}
        elif subcommand == 'tokens':
            # TODO: Echte Token-Info
            return {"output": "📊 Token-Info wird implementiert..."}
        else:
            return {"error": f"Unbekannter Session-Befehl: {subcommand}"}
    
    def _cmd_clear(self) -> Dict[str, Any]:
        """Löscht Chat-Verlauf"""
        return {"output": "🧹 Chat-Verlauf gelöscht", "clear_chat": True}
    
    def _cmd_help(self, args: List[str] = None) -> Dict[str, Any]:
        """Zeigt Hilfe"""
        if args and args[0].lower() == 'security':
            return {"output": """🔒 SICHERHEITSMODI:
/security safe       - Safe Mode (nur Chat)
/security base       - Base Mode (lokaler Zugriff)
/security hell-out   - Hell-Out Mode (Vollzugriff)
/security status     - Aktueller Modus"""}
        
        security_info = config.get_current_security_info()
        mode = security_info['mode']
        
        help_text = """💬 VERFÜGBARE BEFEHLE:

🔒 SICHERHEIT:
/security [safe|base|hell-out] - Sicherheitsmodus wechseln
/auto-accept [on|off|toggle]   - Auto-Accept umschalten

📊 SYSTEM:
/status      - Systemstatus anzeigen
/context     - Token-Usage anzeigen  
/session     - Session-Befehle
/clear       - Chat löschen"""

        if mode != 'safe':
            help_text += """

📁 DATEIEN:
/ls [pfad]   - Dateien auflisten
/pwd         - Aktuelles Verzeichnis
/read [datei] - Datei lesen"""
            
        if mode in ['base', 'hell-out']:
            help_text += """
/cd [pfad]   - Verzeichnis wechseln
/edit [datei] - Datei bearbeiten

💻 TERMINAL:
/exec [cmd]  - Befehl ausführen"""
            
        help_text += """

ℹ️ HILFE:
/help [topic] - Diese Hilfe anzeigen"""
        
        return {"output": help_text}
    
    # DATEI-BEFEHLE
    def _cmd_ls(self, args: List[str] = None) -> Dict[str, Any]:
        """Dateien auflisten"""
        security_info = config.get_current_security_info()
        if not security_info['config']['file_access']:
            return {"error": "❌ Dateizugriff im Safe Mode nicht erlaubt"}
        
        path = args[0] if args else '.'
        try:
            files = os.listdir(path)
            output = f"📁 Inhalt von {os.path.abspath(path)}:\n"
            for f in sorted(files):
                full_path = os.path.join(path, f)
                if os.path.isdir(full_path):
                    output += f"📂 {f}/\n"
                else:
                    output += f"📄 {f}\n"
            return {"output": output}
        except Exception as e:
            return {"error": f"Fehler beim Auflisten: {str(e)}"}
    
    def _cmd_pwd(self) -> Dict[str, Any]:
        """Aktuelles Verzeichnis"""
        return {"output": f"📁 Aktuelles Verzeichnis: {os.getcwd()}"}
    
    def _cmd_cd(self, args: List[str] = None) -> Dict[str, Any]:
        """Verzeichnis wechseln"""
        security_info = config.get_current_security_info()
        if security_info['mode'] == 'safe':
            return {"error": "❌ Verzeichniswechsel im Safe Mode nicht erlaubt"}
        
        if not args:
            return {"error": "❌ Pfad erforderlich: /cd <pfad>"}
        
        path = args[0]
        try:
            os.chdir(path)
            return {"output": f"📁 Verzeichnis gewechselt zu: {os.getcwd()}", "directory_change": True}
        except Exception as e:
            return {"error": f"Fehler beim Verzeichniswechsel: {str(e)}"}
    
    def _cmd_read(self, args: List[str] = None) -> Dict[str, Any]:
        """Datei lesen"""
        security_info = config.get_current_security_info()
        if not security_info['config']['file_access']:
            return {"error": "❌ Dateizugriff im Safe Mode nicht erlaubt"}
        
        if not args:
            return {"error": "❌ Dateiname erforderlich: /read <datei>"}
        
        filename = args[0]
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"output": f"📄 Inhalt von {filename}:\n```\n{content}\n```"}
        except Exception as e:
            return {"error": f"Fehler beim Lesen: {str(e)}"}
    
    def _cmd_edit(self, args: List[str] = None) -> Dict[str, Any]:
        """Datei bearbeiten"""
        security_info = config.get_current_security_info()
        if security_info['mode'] == 'safe':
            return {"error": "❌ Dateibearbeitung im Safe Mode nicht erlaubt"}
        
        if not args:
            return {"error": "❌ Dateiname erforderlich: /edit <datei>"}
        
        return {"output": f"📝 Dateibearbeitung für {args[0]} wird implementiert..."}
    
    # TERMINAL-BEFEHLE
    def _cmd_exec(self, args: List[str] = None) -> Dict[str, Any]:
        """Terminal-Befehl ausführen"""
        security_info = config.get_current_security_info()
        if not security_info['config']['terminal_access']:
            return {"error": "❌ Terminal-Zugriff im Safe Mode nicht erlaubt"}
        
        if not args:
            return {"error": "❌ Befehl erforderlich: /exec <befehl>"}
        
        command = ' '.join(args)
        return {"output": f"💻 Terminal-Ausführung für '{command}' wird implementiert...", "needs_permission": True}
    
    def _cmd_shell(self) -> Dict[str, Any]:
        """Interaktive Shell"""
        security_info = config.get_current_security_info()
        if not security_info['config']['terminal_access']:
            return {"error": "❌ Terminal-Zugriff im Safe Mode nicht erlaubt"}
        
        return {"output": "💻 Interaktive Shell wird implementiert..."}

# Globale Instanz
command_handler = CommandHandler()