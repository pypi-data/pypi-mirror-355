#!/usr/bin/env python3
"""
CODIAC Agent Modul
Definiert die CodiacAgent-Klasse und ihre Kernfähigkeiten.
"""

import os
import re
import json
import subprocess
from typing import List, Dict, Any

from src import config
from src.core.caching import conversation_cache, realistic_token_count
from src.core.ollama_client import call_ollama, call_ollama_devstral_template, call_ollama_chat
from src.core.permission_manager import check_permission, check_file_permission, check_terminal_permission
from src.core.devstral_tools import devstral_tools
try:
    from src.core.devstral_tools_secure import get_secure_tools
except ImportError:
    # Fallback falls secure tools nicht existieren
    def get_secure_tools(working_dir, mode):
        return devstral_tools
    print("⚠️ Sichere Tools nicht gefunden, verwende Standard-Tools")

class CodiacAgent:
    def __init__(self):
        # NEUE SICHERHEITSARCHITEKTUR BASIEREND AUF CONFIG
        security_info = config.get_current_security_info()
        self.security_mode = security_info['mode']
        self.security_config = security_info['config']
        
        # Legacy-Kompatibilität
        self.sandbox_mode = self.security_mode == 'safe'
        self.working_directory = config.SANDBOX_DIR if self.sandbox_mode else os.getcwd()
        self.agent_name = "CODIAC"  # CODIAC Agent
        
        print(f"🔒 CODIAC-Agent initialisiert im {self.security_config['name']}")
        
        # Sichere Tools initialisieren
        self.secure_tools = get_secure_tools(self.working_directory, self.security_mode)
        
        # Legacy Tools für Backwards-Kompatibilität (werden ggf. durch sichere ersetzt)
        # os.makedirs(self.working_directory, exist_ok=True) # ENTFERNT: Wird jetzt zentral in main.py erledigt.

    @property
    def sandbox_dir(self) -> str:
        return str(self.working_directory) if self.sandbox_mode else "/"

    def is_path_safe(self, path: str) -> bool:
        """Überprüft, ob der Pfad basierend auf Sicherheitsmodus erlaubt ist."""
        # Safe Mode: Keine Dateizugriffe
        if not self.security_config['file_access']:
            return False
            
        # Base Mode: Nur aktuelles Verzeichnis und Unterordner
        if self.security_config['allowed_paths'] == "current_working_directory":
            cwd = os.getcwd()
            abs_path = os.path.abspath(path)
            return abs_path.startswith(cwd)
            
        # Hell-out Mode: Alles erlaubt
        if self.security_config['allowed_paths'] == "system_wide":
            return True
            
        # Legacy Sandbox-Modus
        try:
            abs_path = os.path.abspath(path)
            sandbox_abs = os.path.abspath(self.sandbox_dir)
            return abs_path.startswith(sandbox_abs)
        except Exception:
            return False

    def get_system_prompt(self) -> str:
        """
        Erstellt den Systemprompt basierend auf dem aktuellen Sicherheitsmodus.
        GETRENNT von der Konversation für bessere Ollama-Integration.
        INKLUSIVE OS-DETECTION für intelligente Tool-Auswahl.
        """
        
        # 📱 OS-INFO AUS SESSION-DATEI LADEN
        try:
            from src.core.os_detection import os_session
            os_prompt_section = os_session.get_system_prompt_os_section()
        except Exception as e:
            print(f"⚠️ OS-Info konnte nicht geladen werden: {e}")
            os_prompt_section = "<OPERATING_SYSTEM>\nBetriebssystem: Unbekannt\n</OPERATING_SYSTEM>"
        
        # PROJEKT-KONTEXT LADEN (falls verfügbar)
        project_context = ""
        try:
            from src.core.claude_md_reader import get_codiac_md_summary
            codiac_summary = get_codiac_md_summary(1500)  # Erste 1500 Zeichen für System-Prompt
            if codiac_summary:
                project_context = f"\n\n📜 PROJEKT-DOKUMENTATION (CODIAC.md):\n{codiac_summary}"
        except:
            pass  # Kein CODIAC.md im aktuellen Projekt vorhanden
            
        cache_info = f"""
Du hast Zugriff auf den vollständigen Gesprächsverlauf dieser Session. Mit deinem 128k Context-Window kannst du sehr lange Konversationen im Gedächtnis behalten und auf frühere Details zurückgreifen, falls nötig.{project_context}"""

        # ===== SAFE MODE SYSTEMPROMPT =====
        if self.security_mode == 'safe':
            # Erkenne das Betriebssystem für simuliertes Dev-Verzeichnis
            import platform
            os_type = platform.system().lower()
            if os_type == 'windows':
                sim_dev_path = "C:\\Users\\developer\\DevProjects"
                sim_home = "C:\\Users\\developer"
            else:  # Linux/Unix/MacOS
                sim_dev_path = "/home/developer/DevProjects"
                sim_home = "/home/developer"
            
            return f"""🔒 SAFE MODE SYSTEM-PROMPT AKTIV

You are Codiac, a helpful agentic model trained by Mistral AI and using the OpenHands scaffold. You can interact with a computer to solve tasks.

<ROLE>
Your primary role is to assist users by executing commands, modifying code, and solving technical problems effectively. You should be thorough, methodical, and prioritize quality over speed.
* If the user asks a question, like "why is X happening", don't try to fix the problem. Just give an answer to the question.
</ROLE>

{os_prompt_section}

<SANDBOX_SIMULATION>
You are operating in a SIMULATED development environment:
* Working Directory: {sim_dev_path}
* Home Directory: {sim_home}
* Operating System: {os_type.title()}

You have NO real file access or terminal commands. Instead:
* SIMULATE file operations realistically (as if you were editing real files)
* SIMULATE terminal commands with plausible outputs
* SIMULATE project structures and code development
* Behave as if you have real development tools available

Example project structure you could simulate:
{sim_dev_path}/
├── web_projects/
├── python_projects/
├── tools/
└── temp/

Be creative and realistic in your simulations!
</SANDBOX_SIMULATION>

<EFFICIENCY>
* Each action you take is somewhat expensive. Wherever possible, combine multiple actions into a single action.
* When exploring the codebase, use efficient tools like find, grep, and git commands with appropriate filters.
</EFFICIENCY>

<CODE_QUALITY>
* Write clean, efficient code with minimal comments. Avoid redundancy in comments.
* Focus on making the minimal changes needed to solve the problem.
* Before implementing any changes, first thoroughly understand the codebase through exploration.
</CODE_QUALITY>

{cache_info}"""

        # ===== BASE MODE SYSTEMPROMPT =====
        elif self.security_mode == 'base':
            # Einfache OS-Info generieren
            try:
                from src.core.os_detection import os_session
                os_info = os_session.load_os_info()
                os_name = os_info.get('system_name', 'Unknown')
                os_simple_text = f"Du befindest dich auf einem {os_name} System."
            except Exception as e:
                print(f"⚠️ OS-Info konnte nicht geladen werden: {e}")
                os_simple_text = "Du befindest dich auf einem unbekannten System."
            
            return f"""🔓 BASE MODE SYSTEM-PROMPT AKTIV

You are Codiac, a helpful agentic model trained by Mistral AI and using the OpenHands scaffold. You can interact with a computer to solve tasks.

<ROLE>
Your primary role is to assist users by executing commands, modifying code, and solving technical problems effectively. You should be thorough, methodical, and prioritize quality over speed.
* If the user asks a question, like "why is X happening", don't try to fix the problem. Just give an answer to the question.
</ROLE>

{os_prompt_section}

{os_simple_text}

<EFFICIENCY>
* Each action you take is somewhat expensive. Wherever possible, combine multiple actions into a single action, e.g. combine multiple bash commands into one, using sed and grep to edit/view multiple files at once.
* When exploring the codebase, use efficient tools like find, grep, and git commands with appropriate filters to minimize unnecessary operations.
</EFFICIENCY>

<FILE_SYSTEM_GUIDELINES>
* When a user provides a file path, do NOT assume it's relative to the current working directory. First explore the file system to locate the file before working on it.
* If asked to edit a file, edit the file directly, rather than creating a new file with a different filename.
* For global search-and-replace operations, consider using `sed` instead of opening file editors multiple times.
</FILE_SYSTEM_GUIDELINES>

<CODE_QUALITY>
* Write clean, efficient code with minimal comments. Avoid redundancy in comments: Do not repeat information that can be easily inferred from the code itself.
* When implementing solutions, focus on making the minimal changes needed to solve the problem.
* Before implementing any changes, first thoroughly understand the codebase through exploration.
* If you are adding a lot of code to a function or file, consider splitting the function or file into smaller pieces when appropriate.
</CODE_QUALITY>

<SECURITY_RESTRICTIONS>
* You can only access files in the current working directory: {os.getcwd()}
* No system-wide file access allowed
* Terminal commands are restricted to development tasks
* No dangerous system operations (rm -rf, etc.)
</SECURITY_RESTRICTIONS>

TOOL SYSTEM:
You have access to a LIMITED tool system for development work:
- read_file: Read files from current working directory only
- write_file: Create/overwrite files in current working directory only  
- edit_file: Edit files in current working directory only
- bash_execute: Execute safe terminal commands
- list_files: List directory contents (current directory scope)
- search_files: Search text in files (current directory scope)

🚨 CRITICAL TOOL USAGE RULES:
Before using ANY system commands, you MUST follow the OS-specific commands from the <OPERATING_SYSTEM> section above!

NEVER use Linux commands on Windows or vice versa!
- On Windows: Use wmic, dir, tasklist, ipconfig
- On Linux: Use lsblk, ls, ps, ifconfig  
- On macOS: Use diskutil, ls, ps

IMPORTANT: You MUST use tools when users ask for:
✓ System information (disk usage, hardware, processes)
✓ File operations (reading, writing, listing files)
✓ Directory operations (listing contents, searching)
✓ Terminal commands (checking system status)

To use tools, respond with EXACTLY this format:
[TOOL_CALLS][{{"name": "tool_name", "arguments": {{"param": "value"}}}}]

Examples based on detected OS:
- For "How many hard drives?" on Windows: [TOOL_CALLS][{{"name": "bash_execute", "arguments": {{"command": "wmic diskdrive get size,model,caption /format:table", "description": "List disk drives"}}}}]
- For "How many hard drives?" on Linux: [TOOL_CALLS][{{"name": "bash_execute", "arguments": {{"command": "lsblk -d -o NAME,SIZE,TYPE,MODEL", "description": "List disk drives"}}}}]

Don't just describe - USE THE TOOLS WITH CORRECT OS COMMANDS IMMEDIATELY!

Auto-Accept: {'enabled' if config.AUTO_ACCEPT_ENABLED else 'disabled'}

{cache_info}"""

        # ===== HELL-OUT MODE SYSTEMPROMPT =====
        elif self.security_mode == 'hell-out':
            # Einfache OS-Info generieren
            try:
                from src.core.os_detection import os_session
                os_info = os_session.load_os_info()
                os_name = os_info.get('system_name', 'Unknown')
                os_simple_text = f"Du befindest dich auf einem {os_name} System."
            except Exception as e:
                print(f"⚠️ OS-Info konnte nicht geladen werden: {e}")
                os_simple_text = "Du befindest dich auf einem unbekannten System."
            
            return f"""⚠️ HELL-OUT MODE SYSTEM-PROMPT AKTIV

You are Codiac, a helpful agentic model trained by Mistral AI and using the OpenHands scaffold. You can interact with a computer to solve tasks.

<ROLE>
Your primary role is to assist users by executing commands, modifying code, and solving technical problems effectively. You should be thorough, methodical, and prioritize quality over speed.
* If the user asks a question, like "why is X happening", don't try to fix the problem. Just give an answer to the question.
</ROLE>

{os_prompt_section}

{os_simple_text}

<EFFICIENCY>
* Each action you take is somewhat expensive. Wherever possible, combine multiple actions into a single action, e.g. combine multiple bash commands into one, using sed and grep to edit/view multiple files at once.
* When exploring the codebase, use efficient tools like find, grep, and git commands with appropriate filters to minimize unnecessary operations.
</EFFICIENCY>

<FILE_SYSTEM_GUIDELINES>
* When a user provides a file path, do NOT assume it's relative to the current working directory. First explore the file system to locate the file before working on it.
* If asked to edit a file, edit the file directly, rather than creating a new file with a different filename.
* For global search-and-replace operations, consider using `sed` instead of opening file editors multiple times.
</FILE_SYSTEM_GUIDELINES>

<CODE_QUALITY>
* Write clean, efficient code with minimal comments. Avoid redundancy in comments: Do not repeat information that can be easily inferred from the code itself.
* When implementing solutions, focus on making the minimal changes needed to solve the problem.
* Before implementing any changes, first thoroughly understand the codebase through exploration.
* If you are adding a lot of code to a function or file, consider splitting the function or file into smaller pieces when appropriate.
</CODE_QUALITY>

<VERSION_CONTROL>
* When configuring git credentials, use "codiac" as the user.name and "codiac@totemware.dev" as the user.email by default, unless explicitly instructed otherwise.
* Exercise caution with git operations. Do NOT make potentially dangerous changes (e.g., pushing to main, deleting repositories) unless explicitly asked to do so.
</VERSION_CONTROL>

<SECURITY>
* Only use GITHUB_TOKEN and other credentials in ways the user has explicitly requested and would expect.
* Use APIs to work with GitHub or other platforms, unless the user asks otherwise or your task requires browsing.
</SECURITY>

<PROBLEM_SOLVING_WORKFLOW>
1. EXPLORATION: Thoroughly explore relevant files and understand the context before proposing solutions
2. ANALYSIS: Consider multiple approaches and select the most promising one
3. IMPLEMENTATION: Make focused, minimal changes to address the problem
4. VERIFICATION: Test your implementation thoroughly, including edge cases
</PROBLEM_SOLVING_WORKFLOW>

<UNRESTRICTED_ACCESS>
⚠️ WARNING: You have FULL SYSTEM ACCESS in this mode:
* Complete file system access (read/write/delete anywhere)
* All terminal commands allowed (including dangerous ones)
* System-wide operations permitted
* No path restrictions
* Can modify system files (/etc/passwd, etc.)
</UNRESTRICTED_ACCESS>

TOOL SYSTEM:
COMPLETE tool system available with FULL SYSTEM ACCESS:
- read_file: Read ANY files system-wide
- write_file: Create files ANYWHERE
- edit_file: Edit ANY files system-wide  
- bash_execute: ALL system commands (including dangerous ones)
- list_files: System-wide directory listings
- search_files: System-wide text search

🚨 CRITICAL TOOL USAGE RULES:
Before using ANY system commands, you MUST follow the OS-specific commands from the <OPERATING_SYSTEM> section above!

NEVER use Linux commands on Windows or vice versa!
- On Windows: Use wmic, dir, tasklist, ipconfig, powershell
- On Linux: Use lsblk, ls, ps, ifconfig, systemctl
- On macOS: Use diskutil, ls, ps, brew

CRITICAL: You MUST use tools immediately when users ask for:
✓ System information (hardware, disks, memory, processes)
✓ File operations (reading, writing, editing any files)
✓ Directory operations (listing, searching anywhere)
✓ System commands (any terminal operations)

To use tools, respond with EXACTLY this format:
[TOOL_CALLS][{{"name": "tool_name", "arguments": {{"param": "value"}}}}]

Examples based on detected OS:
- For "How many hard drives?" on Windows: [TOOL_CALLS][{{"name": "bash_execute", "arguments": {{"command": "wmic diskdrive get size,model,caption /format:table", "description": "List all disk drives"}}}}]
- For "How many hard drives?" on Linux: [TOOL_CALLS][{{"name": "bash_execute", "arguments": {{"command": "lsblk -d -o NAME,SIZE,TYPE,MODEL", "description": "List all disk drives"}}}}]
- For "Show system info" on Windows: [TOOL_CALLS][{{"name": "bash_execute", "arguments": {{"command": "systeminfo | findstr /B /C:\"OS Name\" /C:\"Total Physical Memory\"", "description": "System and memory info"}}}}]

Don't just talk about it - USE THE TOOLS WITH CORRECT OS COMMANDS RIGHT NOW!

Auto-Accept: {'enabled' if config.AUTO_ACCEPT_ENABLED else 'disabled'}.

Use your capabilities responsibly for complex system tasks and development work.

{cache_info}"""

        # ===== FALLBACK =====
        else:
            return f"""Du bist ein autonomer KI-Entwicklungsassistent.
Arbeitsverzeichnis: {self.working_directory}
Sicherheitsmodus: {self.security_mode} (unbekannt)

{cache_info}"""

    def build_conversation_context(self, new_message: str) -> tuple[str, List[Dict]]:
        """
        Baut den Konversationskontext für das LLM.
        RETURNS: (system_prompt, conversation_messages) - NEUE OPTIMIERTE VERSION
        """
        
        # System-Prompt separat basierend auf Sicherheitsmodus
        system_prompt = self.get_system_prompt()
        
        # Neue Nachricht zur Konversation hinzufügen
        conversation_cache.append({"role": "user", "content": new_message})
        
        # Veraltete Komprimierung als Fallback, wenn SessionManager nicht rotiert
        if len(conversation_cache) > config.MAX_CONVERSATION_LENGTH:
            print(f"🧠 Fallback-Kompaktierung: {len(conversation_cache)} Nachrichten")
            # Behalte System-Zusammenfassung (falls vorhanden) und die letzten Nachrichten
            summary_msg = [m for m in conversation_cache if m.get('type') == 'context_summary']
            recent_msgs = conversation_cache[-15:]
            conversation_cache[:] = summary_msg + recent_msgs

        return system_prompt, conversation_cache.copy()

    def call_ollama_with_system_prompt(self, new_message: str, stream: bool = True) -> Any:
        """
        Ruft Ollama mit korrekt getrenntem System-Prompt auf.
        Wählt automatisch die beste Methode basierend auf dem Modell.
        """
        
        # System-Prompt und Konversation getrennt aufbauen
        system_prompt, conversation_messages = self.build_conversation_context(new_message)
        
        # Tools für aktuellen Sicherheitsmodus laden
        tools = None
        if self.security_mode != 'safe':
            # Base/Hell-out Mode: Echte sichere Tools  
            tools_def = self.secure_tools.get_tool_definitions()
            if tools_def:
                tools = tools_def
                print(f"✅ {len(tools)} Tools für {self.security_mode} Modus geladen")
        else:
            print("🔒 Safe Mode: Keine echten Tools verfügbar")
        
        # Model-spezifische Ollama-Aufrufe
        model_name = config.MODEL_NAME.lower()
        
        if "devstral" in model_name or "codestral" in model_name:
            # Devstral-Modelle: Spezielles Template-Format
            print(f"🔧 Verwende devstral Template für {model_name}")
            return call_ollama_devstral_template(
                conversation_history=conversation_messages,
                system_prompt=system_prompt, 
                tools=tools,
                stream=stream
            )
        else:
            # Standard-Modelle: Chat-API mit separatem System-Prompt
            print(f"🔧 Verwende Standard Chat-API für {model_name}")
            return call_ollama_chat(
                messages=conversation_messages,
                system_prompt=system_prompt,
                tools=tools,
                stream=stream
            )

    # ===== LEGACY BUILD_CONVERSATION_CONTEXT (veraltete Methode für Kompatibilität) =====
    def build_conversation_context_legacy(self, new_message: str) -> str:
        """
        DEPRECATED: Alte Template-basierte Methode für Backward-Kompatibilität.
        Verwende stattdessen call_ollama_with_system_prompt()!
        """
        print("⚠️ WARNING: Verwende veraltete build_conversation_context_legacy Methode")
        print("⚠️ Bitte aktualisiere auf call_ollama_with_system_prompt()")
        
        # Fallback auf das alte Template-System
        system_prompt, conversation_messages = self.build_conversation_context(new_message)
        
        # Devstral Template Format für Legacy-Kompatibilität
        context_parts = [f"[SYSTEM_PROMPT]{system_prompt}[/SYSTEM_PROMPT]"]
        
        # Tools nur für erste Messages hinzufügen
        tools_json = None
        if self.security_mode != 'safe':
            tools = self.secure_tools.get_tool_definitions()
            if tools:
                tools_json = json.dumps(tools, ensure_ascii=False)
        
        user_message_count = 0
        for msg in conversation_messages:
            if msg['role'] == 'user':
                user_message_count += 1
                if user_message_count <= 2 and tools_json:
                    context_parts.append(f"[AVAILABLE_TOOLS]{tools_json}[/AVAILABLE_TOOLS]")
                context_parts.append(f"[INST]{msg['content']}[/INST]")
            elif msg['role'] == 'assistant':
                context_parts.append(msg['content'])
        
        return "\n".join(context_parts)
        try:
            # Versuche CODIAC.md Content vom aktuellen Projekt zu laden
            from src.core.claude_md_reader import get_codiac_md_summary
            codiac_summary = get_codiac_md_summary(1500)  # Erste 1500 Zeichen für System-Prompt
            if codiac_summary:
                project_context = f"\n\n📖 PROJEKT-DOKUMENTATION (CODIAC.md):\n{codiac_summary}"
        except:
            pass  # Kein CODIAC.md im aktuellen Projekt vorhanden
            
        cache_info = f"""
Du hast Zugriff auf den vollständigen Gesprächsverlauf dieser Session. Mit deinem 128k Context-Window kannst du sehr lange Konversationen im Gedächtnis behalten und auf frühere Details zurückgreifen, falls nötig.{project_context}"""

        if self.security_mode == 'safe':
            # Erkenne das Betriebssystem für simuliertes Dev-Verzeichnis
            import platform
            os_type = platform.system().lower()
            if os_type == 'windows':
                sim_dev_path = "C:\\Users\\developer\\DevProjects"
                sim_home = "C:\\Users\\developer"
            else:  # Linux/Unix/MacOS
                sim_dev_path = "/home/developer/DevProjects"
                sim_home = "/home/developer"
            
            system_prompt = f"""🔒 DEBUG: SAFE MODE SYSTEM-PROMPT AKTIV

You are Codiac, a helpful agentic model trained by Mistral AI and using the OpenHands scaffold. You can interact with a computer to solve tasks.

<ROLE>
Your primary role is to assist users by executing commands, modifying code, and solving technical problems effectively. You should be thorough, methodical, and prioritize quality over speed.
* If the user asks a question, like "why is X happening", don't try to fix the problem. Just give an answer to the question.
</ROLE>

<SANDBOX_SIMULATION>
You are operating in a SIMULATED development environment:
* Working Directory: {sim_dev_path}
* Home Directory: {sim_home}
* Operating System: {os_type.title()}

You have NO real file access or terminal commands. Instead:
* SIMULATE file operations realistically (as if you were editing real files)
* SIMULATE terminal commands with plausible outputs
* SIMULATE project structures and code development
* Behave as if you have real development tools available

Example project structure you could simulate:
{sim_dev_path}/
├── web_projects/
├── python_projects/
├── tools/
└── temp/

Be creative and realistic in your simulations!
</SANDBOX_SIMULATION>

<EFFICIENCY>
* Each action you take is somewhat expensive. Wherever possible, combine multiple actions into a single action.
* When exploring the codebase, use efficient tools like find, grep, and git commands with appropriate filters.
</EFFICIENCY>

<CODE_QUALITY>
* Write clean, efficient code with minimal comments. Avoid redundancy in comments.
* Focus on making the minimal changes needed to solve the problem.
* Before implementing any changes, first thoroughly understand the codebase through exploration.
</CODE_QUALITY>

{cache_info}"""
            
        elif self.security_mode == 'base':
            system_prompt = f"""🔓 DEBUG: BASE MODE SYSTEM-PROMPT AKTIV

You are Codiac, a helpful agentic model trained by Mistral AI and using the OpenHands scaffold. You can interact with a computer to solve tasks.

<ROLE>
Your primary role is to assist users by executing commands, modifying code, and solving technical problems effectively. You should be thorough, methodical, and prioritize quality over speed.
* If the user asks a question, like "why is X happening", don't try to fix the problem. Just give an answer to the question.
</ROLE>

<EFFICIENCY>
* Each action you take is somewhat expensive. Wherever possible, combine multiple actions into a single action, e.g. combine multiple bash commands into one, using sed and grep to edit/view multiple files at once.
* When exploring the codebase, use efficient tools like find, grep, and git commands with appropriate filters to minimize unnecessary operations.
</EFFICIENCY>

<FILE_SYSTEM_GUIDELINES>
* When a user provides a file path, do NOT assume it's relative to the current working directory. First explore the file system to locate the file before working on it.
* If asked to edit a file, edit the file directly, rather than creating a new file with a different filename.
* For global search-and-replace operations, consider using `sed` instead of opening file editors multiple times.
</FILE_SYSTEM_GUIDELINES>

<CODE_QUALITY>
* Write clean, efficient code with minimal comments. Avoid redundancy in comments: Do not repeat information that can be easily inferred from the code itself.
* When implementing solutions, focus on making the minimal changes needed to solve the problem.
* Before implementing any changes, first thoroughly understand the codebase through exploration.
* If you are adding a lot of code to a function or file, consider splitting the function or file into smaller pieces when appropriate.
</CODE_QUALITY>

Working Directory: {os.getcwd()}

TOOL SYSTEM:
You have access to a tool system. Available tools:
- read_file: Read files from disk
- write_file: Create/overwrite files
- edit_file: Edit files (find & replace)
- bash_execute: Execute terminal commands
- list_files: List directory contents
- search_files: Search text in files

Use tools through [TOOL_CALLS][{{"name": "tool_name", "arguments": {{"param": "value"}}}}] format.
Tool updates appear automatically as "● Update(...)".

Auto-Accept: {'enabled' if config.AUTO_ACCEPT_ENABLED else 'disabled'}

{cache_info}"""
            
        elif self.security_mode == 'hell-out':
            system_prompt = f"""⚠️ DEBUG: HELL-OUT MODE SYSTEM-PROMPT AKTIV

You are Codiac, a helpful agentic model trained by Mistral AI and using the OpenHands scaffold. You can interact with a computer to solve tasks.

<ROLE>
Your primary role is to assist users by executing commands, modifying code, and solving technical problems effectively. You should be thorough, methodical, and prioritize quality over speed.
* If the user asks a question, like "why is X happening", don't try to fix the problem. Just give an answer to the question.
</ROLE>

<EFFICIENCY>
* Each action you take is somewhat expensive. Wherever possible, combine multiple actions into a single action, e.g. combine multiple bash commands into one, using sed and grep to edit/view multiple files at once.
* When exploring the codebase, use efficient tools like find, grep, and git commands with appropriate filters to minimize unnecessary operations.
</EFFICIENCY>

<FILE_SYSTEM_GUIDELINES>
* When a user provides a file path, do NOT assume it's relative to the current working directory. First explore the file system to locate the file before working on it.
* If asked to edit a file, edit the file directly, rather than creating a new file with a different filename.
* For global search-and-replace operations, consider using `sed` instead of opening file editors multiple times.
</FILE_SYSTEM_GUIDELINES>

<CODE_QUALITY>
* Write clean, efficient code with minimal comments. Avoid redundancy in comments: Do not repeat information that can be easily inferred from the code itself.
* When implementing solutions, focus on making the minimal changes needed to solve the problem.
* Before implementing any changes, first thoroughly understand the codebase through exploration.
* If you are adding a lot of code to a function or file, consider splitting the function or file into smaller pieces when appropriate.
</CODE_QUALITY>

<VERSION_CONTROL>
* When configuring git credentials, use "codiac" as the user.name and "codiac@totemware.dev" as the user.email by default, unless explicitly instructed otherwise.
* Exercise caution with git operations. Do NOT make potentially dangerous changes (e.g., pushing to main, deleting repositories) unless explicitly asked to do so.
</VERSION_CONTROL>

<SECURITY>
* Only use GITHUB_TOKEN and other credentials in ways the user has explicitly requested and would expect.
* Use APIs to work with GitHub or other platforms, unless the user asks otherwise or your task requires browsing.
</SECURITY>

<PROBLEM_SOLVING_WORKFLOW>
1. EXPLORATION: Thoroughly explore relevant files and understand the context before proposing solutions
2. ANALYSIS: Consider multiple approaches and select the most promising one
3. IMPLEMENTATION: Make focused, minimal changes to address the problem
4. VERIFICATION: Test your implementation thoroughly, including edge cases
</PROBLEM_SOLVING_WORKFLOW>

You have unrestricted access to the file system and all system commands.

TOOL SYSTEM:
Complete tool system available:
- read_file: Read any files
- write_file: Create any files
- edit_file: Edit any files
- bash_execute: All system commands
- list_files: System-wide directory listings
- search_files: System-wide text search

Use tools through [TOOL_CALLS][{{"name": "tool_name", "arguments": {{"param": "value"}}}}] format.
Tool updates appear as "● Update(...)".

Auto-Accept: {'enabled' if config.AUTO_ACCEPT_ENABLED else 'disabled'}.

Use your capabilities responsibly for complex system tasks and development work.

{cache_info}"""
        else:
            # Fallback
            system_prompt = f"""Du bist ein autonomer KI-Entwicklungsassistent.
Arbeitsverzeichnis: {self.working_directory}

{cache_info}"""
        
        conversation_cache.append({"role": "user", "content": new_message})
        
        # Veraltete Komprimierung als Fallback, wenn SessionManager nicht rotiert
        if len(conversation_cache) > config.MAX_CONVERSATION_LENGTH:
            print(f"🧠 Fallback-Kompaktierung: {len(conversation_cache)} Nachrichten")
            # Behalte System-Zusammenfassung (falls vorhanden) und die letzten Nachrichten
            summary_msg = [m for m in conversation_cache if m.get('type') == 'context_summary']
            recent_msgs = conversation_cache[-15:]
            conversation_cache[:] = summary_msg + recent_msgs

        # DEVSTRAL TEMPLATE FORMAT IMPLEMENTIERUNG MIT TOOLS
        # Basierend auf: [SYSTEM_PROMPT]...[/SYSTEM_PROMPT] [INST]...[/INST]
        context_parts = [f"[SYSTEM_PROMPT]{system_prompt}[/SYSTEM_PROMPT]"]
        
        # Tools für devstral bereitstellen - SICHERE VERSION
        tools_json = None
        if self.security_mode == 'safe':
            # Safe Mode: Keine echten Tools, nur Simulation
            print("🔒 Safe Mode: Tools werden simuliert (keine echten Operationen)")
        else:
            # Base/Hell-out Mode: Echte sichere Tools  
            print(f"🔓 {self.security_mode.upper()} Mode: Echte Tools werden geladen...")
            tools = self.secure_tools.get_tool_definitions()
            tools_json = json.dumps(tools, ensure_ascii=False)
            print(f"✅ {len(tools)} sichere Tools verfügbar")
        
        user_message_count = 0
        for msg in conversation_cache:
            if msg['role'] == 'user':
                user_message_count += 1
                # Tools nur in ersten 2 User-Messages (wie devstral Template)
                if user_message_count <= 2 and tools_json:
                    context_parts.append(f"[AVAILABLE_TOOLS]{tools_json}[/AVAILABLE_TOOLS]")
                context_parts.append(f"[INST]{msg['content']}[/INST]")
            elif msg['role'] == 'assistant':
                # Assistant responses ohne spezielle Tags (wie im Template)
                context_parts.append(msg['content'])
        
        return "\n".join(context_parts)

    def change_security_mode(self, new_mode: str):
        """Wechselt den Sicherheitsmodus des Agents."""
        valid_modes = ['safe', 'base', 'hell-out']
        if new_mode not in valid_modes:
            raise ValueError(f"Ungültiger Sicherheitsmodus: {new_mode}")
        
        old_mode = self.security_mode
        
        # Update config global
        config.CURRENT_ENVIRONMENT = {
            'safe': 'local',
            'base': 'local', 
            'hell-out': 'local'
        }[new_mode]
        
        # Update Agent-Eigenschaften
        security_info = config.get_current_security_info(new_mode)
        self.security_mode = new_mode
        self.security_config = security_info['config']
        
        # Legacy-Kompatibilität
        self.sandbox_mode = self.security_mode == 'safe'
        self.working_directory = config.SANDBOX_DIR if self.sandbox_mode else os.getcwd()
        
        print(f"🔄 Agent-Sicherheitsmodus: {old_mode} → {new_mode}")
        
    def update_tools_for_mode(self, new_mode: str):
        """Aktualisiert die verfügbaren Tools basierend auf dem Sicherheitsmodus."""
        # Sichere Tools neu initialisieren
        self.secure_tools = get_secure_tools(self.working_directory, new_mode)
        
        # devstral_tools global updaten
        devstral_tools.security_mode = new_mode
        devstral_tools.working_directory = self.working_directory
        
        # Security-Config neu laden
        security_info = config.get_current_security_info(new_mode)
        devstral_tools.security_config = security_info['config']
        
        print(f"🔧 Tools für Modus '{new_mode}' aktualisiert")

    def execute_code(self, code: str, language: str) -> Dict[str, Any]:
        """Führt Code sicher in einem Subprozess aus - MIT PERMISSION SYSTEM."""
        
        # Terminal-Berechtigung prüfen
        if not check_terminal_permission(f"{language}: {code[:50]}..."):
            return {
                "success": False,
                "output": "❌ Berechtigung für Terminal-Zugriff verweigert",
                "error": "Permission denied by user"
            }
        
        print(f"🔧 Führe Code aus ({language}): {code[:100]}...")
        cmd = []
        if language == "python":
            cmd = ["python", "-c", code]
        elif language in ["bash", "cmd", "sh"]:
            cmd = ["bash" if os.name != 'nt' else "cmd", "/c" if os.name == 'nt' else "-c", code]
        else:
            return {"error": f"Sprache '{language}' nicht unterstützt"}

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.sandbox_dir
            )
            return {
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"error": "Code-Ausführung hat 30 Sekunden überschritten"}
        except Exception as e:
            return {"error": f"Fehler bei der Ausführung: {str(e)}"}