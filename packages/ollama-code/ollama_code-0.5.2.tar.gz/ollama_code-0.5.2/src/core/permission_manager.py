#!/usr/bin/env python3
"""
Permission Manager für interaktive Benutzerbestätigung
Implementiert das 3-Optionen-System mit Pfeiltastennavigation
"""

import sys
import os
from typing import Tuple, List
from src import config

# Platform-spezifische Imports
try:
    import termios
    import tty
    HAS_TERMIOS = True
except ImportError:
    HAS_TERMIOS = False  # Windows

class PermissionManager:
    def __init__(self):
        self.permanent_permissions = set()  # Dauerhaft erlaubte Befehle
        
    def ask_permission(self, action_type: str, command: str = None, description: str = None) -> bool:
        """
        Fragt nach Berechtigung für eine Aktion
        
        Returns:
            True: Erlaubt
            False: Verweigert
        """
        # Auto-Accept prüfen
        if config.AUTO_ACCEPT_ENABLED:
            print(f"🤖 Auto-Accept: {action_type}")
            if command:
                print(f"   Befehl: {command}")
            return True
            
        # Dauerhafte Berechtigung prüfen
        if command and command in self.permanent_permissions:
            print(f"✅ Dauerhaft erlaubt: {command}")
            return True
            
        # Interaktive Abfrage
        return self._interactive_permission(action_type, command, description)
    
    def _interactive_permission(self, action_type: str, command: str = None, description: str = None) -> bool:
        """Interaktive Berechtigungsabfrage mit Pfeiltastennavigation"""
        
        print(f"\n🔐 Berechtigung erforderlich für: {action_type}")
        if command:
            print(f"📝 Befehl: {command}")
        if description:
            print(f"💭 Beschreibung: {description}")
        
        options = [
            "Ja - Einmalig erlauben",
            "Ja - Diesen Befehl dauerhaft erlauben",
            "Nein - Verweigern und alternative Lösung finden"
        ]
        
        selected = self._arrow_key_selection(options)
        
        if selected == 0:  # Einmalig ja
            print("✅ Berechtigung einmalig erteilt")
            return True
        elif selected == 1:  # Dauerhaft ja
            if command:
                self.permanent_permissions.add(command)
                print(f"✅ Berechtigung dauerhaft erteilt für: {command}")
            else:
                print("✅ Berechtigung einmalig erteilt (kein spezifischer Befehl)")
            return True
        else:  # Nein
            print("❌ Berechtigung verweigert")
            return False
    
    def _arrow_key_selection(self, options: List[str]) -> int:
        """
        Plattformübergreifende Pfeiltastenauswahl (Windows + Linux)
        
        Returns:
            Index der gewählten Option
        """
        selected = 0
        
        def print_menu():
            # Terminal löschen (plattformübergreifend)
            if os.name == 'nt':  # Windows
                os.system('cls')
            else:  # Linux/Unix
                os.system('clear')
                
            print("\n🎯 Wählen Sie mit ↑/↓ Pfeiltasten, bestätigen mit Enter:")
            print("   (oder Nummer eingeben + Enter)")
            for i, option in enumerate(options):
                prefix = "→ " if i == selected else "  "
                print(f"{prefix}{i+1}. {option}")
            print("\nNavigation: ↑/↓ Pfeiltasten, Enter=OK, q=Abbrechen")
        
        # Windows-spezifische Implementierung
        if os.name == 'nt' and sys.stdin.isatty():
            try:
                import msvcrt
                
                while True:
                    print_menu()
                    
                    key = msvcrt.getch()
                    
                    if key == b'\r':  # Enter
                        break
                    elif key == b'\xe0':  # Spezielle Taste (Pfeile)
                        key = msvcrt.getch()
                        if key == b'H':  # Pfeil hoch
                            selected = (selected - 1) % len(options)
                        elif key == b'P':  # Pfeil runter
                            selected = (selected + 1) % len(options)
                    elif key == b'q' or key == b'\x03':  # q oder Ctrl+C
                        selected = 2  # Nein
                        break
                    elif key.isdigit():  # Nummer eingegeben
                        num = int(key.decode()) - 1
                        if 0 <= num < len(options):
                            selected = num
                            break
                            
            except ImportError:
                # msvcrt nicht verfügbar, Fallback
                print_menu()
                try:
                    choice = input("\nGeben Sie die Nummer ein (1-3): ")
                    selected = int(choice) - 1
                    if selected < 0 or selected >= len(options):
                        selected = 2
                except (ValueError, EOFError):
                    selected = 2
                    
        # Linux/Unix-Implementierung
        elif HAS_TERMIOS and sys.stdin.isatty():
            old_settings = termios.tcgetattr(sys.stdin)
            try:
                tty.setraw(sys.stdin)
                
                while True:
                    print_menu()
                    
                    char = sys.stdin.read(1)
                    
                    if char == '\r' or char == '\n':  # Enter
                        break
                    elif char == '\x1b':  # ESC-Sequenz (Pfeiltasten)
                        char = sys.stdin.read(1)
                        if char == '[':
                            char = sys.stdin.read(1)
                            if char == 'A':  # Pfeil hoch
                                selected = (selected - 1) % len(options)
                            elif char == 'B':  # Pfeil runter
                                selected = (selected + 1) % len(options)
                    elif char == 'q' or char == '\x03':  # q oder Ctrl+C
                        selected = 2  # Nein
                        break
                    elif char.isdigit():  # Nummer eingegeben
                        num = int(char) - 1
                        if 0 <= num < len(options):
                            selected = num
                            break
                        
            finally:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        else:
            # Fallback für alle anderen Fälle
            print_menu()
            try:
                choice = input("\nGeben Sie die Nummer ein (1-3): ")
                selected = int(choice) - 1
                if selected < 0 or selected >= len(options):
                    selected = 2  # Default zu Nein
            except (ValueError, EOFError):
                selected = 2  # Default zu Nein
        
        # Terminal löschen
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')
            
        print(f"✅ Gewählt: {options[selected]}")
        return selected

# Globale Instanz
permission_manager = PermissionManager()

def check_permission(action_type: str, command: str = None, description: str = None) -> bool:
    """Convenience-Funktion für Berechtigungsprüfung"""
    return permission_manager.ask_permission(action_type, command, description)

def check_file_permission(file_path: str, operation: str) -> bool:
    """Prüft Dateiberechtigung basierend auf Sicherheitsmodus"""
    security_info = config.get_current_security_info()
    mode_config = security_info['config']
    
    # Safe Mode: Keine Dateizugriffe
    if not mode_config['file_access']:
        print(f"❌ Dateizugriff im {mode_config['name']} nicht erlaubt")
        return False
    
    # Operationsberechtigung prüfen
    if 'file_operations' in mode_config:
        if operation not in mode_config['file_operations']:
            print(f"❌ Operation '{operation}' nicht erlaubt in {mode_config['name']}")
            return False
    
    # Pfadberechtigung prüfen (vereinfacht für jetzt)
    if mode_config['allowed_paths'] == "current_working_directory":
        import os
        cwd = os.getcwd()
        if not file_path.startswith(cwd):
            print(f"❌ Zugriff außerhalb des aktuellen Verzeichnisses nicht erlaubt")
            return False
    
    # Interaktive Berechtigung
    return check_permission(
        f"Dateioperation: {operation}",
        f"Pfad: {file_path}",
        f"Operation '{operation}' auf Datei/Ordner"
    )

def check_terminal_permission(command: str) -> bool:
    """Prüft Terminal-/Befehlsberechtigung"""
    security_info = config.get_current_security_info()
    mode_config = security_info['config']
    
    # Terminal-Zugriff erlaubt?
    if not mode_config['terminal_access']:
        print(f"❌ Terminal-Zugriff im {mode_config['name']} nicht erlaubt")
        return False
    
    # Interaktive Berechtigung
    return check_permission(
        "Terminal-Befehl ausführen",
        command,
        f"Befehl '{command}' im Terminal ausführen"
    )