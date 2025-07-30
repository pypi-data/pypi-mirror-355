#!/usr/bin/env python3
"""
CODIAC.md Manager für Codiac
Automatisches Erstellen, Lesen und Aktualisieren der eigenen Projektdokumentation
"""

import os
from pathlib import Path
from typing import Optional

class CodiacMdManager:
    def __init__(self, project_root: Path = None):
        """Initialisiert den CODIAC.md Manager"""
        self.project_root = project_root or Path.cwd()
        self.codiac_md_path = None  # Wird beim ersten Zugriff auf Projekt gesetzt
        self.content = None
        self.last_modified = None
        
        # NICHT automatisch erstellen - nur bei Projektarbeit
        
    def set_project_path(self, project_path: Path):
        """Setzt aktuelles Projektverzeichnis und erstellt CODIAC.md bei Bedarf"""
        self.project_root = project_path
        self.codiac_md_path = self.project_root / "CODIAC.md"
        
        # Prüfe ob es ein Projekt ist (hat .git, package.json, pyproject.toml, etc.)
        if self.is_project_directory(project_path):
            self.ensure_codiac_md_exists()
    
    def is_project_directory(self, path: Path) -> bool:
        """Prüft ob Verzeichnis ein Entwicklungsprojekt ist"""
        project_indicators = [
            ".git",           # Git Repository
            "package.json",   # Node.js Projekt
            "pyproject.toml", # Python Projekt
            "pom.xml",        # Java Maven
            "Cargo.toml",     # Rust Projekt
            "go.mod",         # Go Projekt
            "composer.json",  # PHP Projekt
            "Gemfile",        # Ruby Projekt
            "requirements.txt", # Python Requirements
            "setup.py",       # Python Setup
            "CMakeLists.txt", # C/C++ CMake
            "Dockerfile",     # Docker Projekt
            ".vscode",        # VS Code Workspace
            ".idea",          # IntelliJ Projekt
            "src/",           # Source Verzeichnis
            "app/",           # App Verzeichnis
        ]
        
        for indicator in project_indicators:
            if (path / indicator).exists():
                return True
        return False
    
    def ensure_codiac_md_exists(self):
        """Erstellt CODIAC.md wenn sie nicht existiert (nur in Projekten)"""
        if not self.codiac_md_path or self.codiac_md_path.exists():
            return
            
        initial_content = self.get_initial_project_codiac_content()
        try:
            with open(self.codiac_md_path, 'w', encoding='utf-8') as f:
                f.write(initial_content)
            print(f"📝 CODIAC.md für Projekt erstellt: {self.codiac_md_path}")
        except Exception as e:
            print(f"❌ Fehler beim Erstellen von CODIAC.md: {e}")
    
    def get_initial_project_codiac_content(self) -> str:
        """Gibt den initialen Inhalt für Projekt-CODIAC.md zurück"""
        project_name = self.project_root.name
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        return f"""# {project_name} - Codiac Projekt-Dokumentation

## 📋 Projekt-Übersicht
Automatisch erstellt von **Codiac** am {today}

**Projektpfad**: `{self.project_root}`

## 🎯 Was Codiac hier gemacht hat
*(Wird automatisch von Codiac aktualisiert)*

### ✅ Erledigte Aufgaben
- [{today}] CODIAC.md für Projekt erstellt

### 🚧 Geplante Aufgaben
*(Füge hier Aufgaben hinzu, die noch erledigt werden müssen)*

## 📁 Projektstruktur
*(Codiac wird hier die wichtigsten Dateien und Ordner dokumentieren)*

## 🔧 Verwendete Tools
*(Codiac dokumentiert hier welche Tools er in diesem Projekt verwendet hat)*

## 📝 Notizen
*(Wichtige Erkenntnisse und Entscheidungen während der Entwicklung)*

## 🐛 Bekannte Probleme
*(Liste von Bugs oder Issues die noch behoben werden müssen)*

## 🚀 Deployment & Build
*(Informationen wie das Projekt gebaut und deployed wird)*

---
*Diese Datei wird automatisch von Codiac gepflegt und dokumentiert den Entwicklungsfortschritt.*
"""

    def read_codiac_md(self) -> Optional[str]:
        """Liest CODIAC.md und gibt Inhalt zurück"""
        if not self.codiac_md_path or not self.codiac_md_path.exists():
            return None
            
        try:
            # Prüfe ob Datei seit letztem Lesen geändert wurde
            current_modified = self.codiac_md_path.stat().st_mtime
            
            if self.content is None or current_modified != self.last_modified:
                with open(self.codiac_md_path, 'r', encoding='utf-8') as f:
                    self.content = f.read()
                self.last_modified = current_modified
                
                print(f"📖 CODIAC.md {'geladen' if self.last_modified is None else 'neu geladen'} ({len(self.content)} Zeichen)")
                
            return self.content
            
        except Exception as e:
            print(f"⚠️ Fehler beim Lesen von CODIAC.md: {e}")
            return None
    
    def update_completed_task(self, task_description: str):
        """Fügt erledigte Aufgabe zur CODIAC.md hinzu"""
        try:
            content = self.read_codiac_md()
            if not content:
                return
                
            # Aktuelles Datum
            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")
            new_task = f"- [{today}] {task_description}"
            
            # Finde "Was ich bereits gemacht habe" Sektion
            lines = content.split('\n')
            new_lines = []
            in_completed_section = False
            
            for line in lines:
                if "## ✅ Was ich bereits gemacht habe" in line:
                    in_completed_section = True
                    new_lines.append(line)
                elif in_completed_section and line.startswith("## "):
                    # Neue Sektion, füge Task vor dieser Sektion hinzu
                    new_lines.append(new_task)
                    new_lines.append(line)
                    in_completed_section = False
                else:
                    new_lines.append(line)
            
            # Schreibe aktualisierte Datei
            updated_content = '\n'.join(new_lines)
            with open(self.codiac_md_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print(f"📝 CODIAC.md aktualisiert: {task_description}")
            
        except Exception as e:
            print(f"⚠️ Fehler beim Aktualisieren von CODIAC.md: {e}")
    
    def add_todo_task(self, task_description: str):
        """Fügt neue Aufgabe zur TODO-Liste hinzu"""
        try:
            content = self.read_codiac_md()
            if not content:
                return
                
            new_todo = f"- [ ] {task_description}"
            
            # Finde "Was ich noch machen muss" Sektion
            lines = content.split('\n')
            new_lines = []
            
            for line in lines:
                new_lines.append(line)
                if "## 🚧 Was ich noch machen muss" in line:
                    new_lines.append(new_todo)
            
            # Schreibe aktualisierte Datei
            updated_content = '\n'.join(new_lines)
            with open(self.codiac_md_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print(f"📝 TODO zu CODIAC.md hinzugefügt: {task_description}")
            
        except Exception as e:
            print(f"⚠️ Fehler beim Hinzufügen von TODO: {e}")

    def get_summary(self, max_chars: int = 2000) -> Optional[str]:
        """Gibt zusammengefasste Version für System-Prompt zurück"""
        content = self.read_codiac_md()
        if not content:
            return None
            
        if len(content) <= max_chars:
            return content
        else:
            # Nimm die ersten max_chars Zeichen + "..."
            return content[:max_chars] + "..."
    
    def search_section(self, section_name: str) -> Optional[str]:
        """Sucht spezifische Sektion in CODIAC.md"""
        content = self.read_codiac_md()
        if not content:
            return None
            
        lines = content.split('\n')
        section_lines = []
        in_section = False
        
        for line in lines:
            if line.startswith('#') and section_name.lower() in line.lower():
                in_section = True
                section_lines.append(line)
            elif in_section and line.startswith('#') and not section_name.lower() in line.lower():
                # Neue Sektion gefunden, beende aktuelle
                break
            elif in_section:
                section_lines.append(line)
                
        return '\n'.join(section_lines) if section_lines else None
    
    def get_commands_info(self) -> Optional[str]:
        """Extrahiert Befehls-Informationen aus CODIAC.md"""
        return self.search_section("Befehle") or self.search_section("Commands")
    
    def get_tools_info(self) -> Optional[str]:
        """Extrahiert Tool-Informationen aus CODIAC.md"""
        return self.search_section("Tool") or self.search_section("Tools")
    
    def get_completed_tasks(self) -> Optional[str]:
        """Extrahiert erledigte Aufgaben aus CODIAC.md"""
        return self.search_section("Was ich bereits gemacht habe")
    
    def get_todo_tasks(self) -> Optional[str]:
        """Extrahiert TODO-Aufgaben aus CODIAC.md"""
        return self.search_section("Was ich noch machen muss")

# Globale Instance für das Projekt
codiac_md_manager = None

def init_codiac_md_manager(project_root: Path = None):
    """Initialisiert globalen CODIAC.md Manager"""
    global codiac_md_manager
    codiac_md_manager = CodiacMdManager(project_root)
    return codiac_md_manager

def set_current_project(project_path: Path):
    """Setzt aktuelles Projektverzeichnis und erstellt CODIAC.md bei Bedarf"""
    if codiac_md_manager:
        codiac_md_manager.set_project_path(project_path)

def get_codiac_md_content() -> Optional[str]:
    """Gibt aktuellen CODIAC.md Inhalt zurück"""
    if codiac_md_manager:
        return codiac_md_manager.read_codiac_md()
    return None

def get_codiac_md_summary(max_chars: int = 2000) -> Optional[str]:
    """Gibt zusammengefasste Version zurück"""
    if codiac_md_manager:
        return codiac_md_manager.get_summary(max_chars)
    return None

def update_completed_task(task: str):
    """Fügt erledigte Aufgabe zur CODIAC.md hinzu"""
    if codiac_md_manager:
        codiac_md_manager.update_completed_task(task)

def add_todo_task(task: str):
    """Fügt neue TODO-Aufgabe zur CODIAC.md hinzu"""
    if codiac_md_manager:
        codiac_md_manager.add_todo_task(task)

# Backward compatibility aliases (für Migration)
get_claude_md_summary = get_codiac_md_summary
init_claude_md_reader = init_codiac_md_manager