#!/usr/bin/env python3
"""
Atlas Agent Modul
Definiert die AtlasAgent-Klasse und ihre Kernfähigkeiten.
"""

import os
import re
import subprocess
from typing import List, Dict, Any

from src.config import MODEL_NAME, SANDBOX_DIR, MAX_CONVERSATION_LENGTH
from src.core.caching import conversation_cache, realistic_token_count
from src.core.ollama_client import call_ollama

class AtlasAgent:
    def __init__(self):
        self.sandbox_mode = True
        self.working_directory = SANDBOX_DIR
        self.agent_name = "Atlas"
        # os.makedirs(self.working_directory, exist_ok=True) # ENTFERNT: Wird jetzt zentral in main.py erledigt.

    @property
    def sandbox_dir(self) -> str:
        return str(self.working_directory) if self.sandbox_mode else "/"

    def is_path_safe(self, path: str) -> bool:
        """Überprüft, ob der Pfad sicher innerhalb der Sandbox liegt."""
        if not self.sandbox_mode:
            return True
        try:
            abs_path = os.path.abspath(path)
            sandbox_abs = os.path.abspath(self.sandbox_dir)
            return abs_path.startswith(sandbox_abs)
        except Exception:
            return False

    def build_conversation_context(self, new_message: str) -> str:
        """Baut den Konversationskontext für das LLM."""
        system_prompt = f"""Du bist {self.agent_name}, ein autonomer KI-Entwicklungsassistent.
- Du arbeitest im Sandbox-Modus: {self.working_directory}
- Sei proaktiv, präzise und führe angeforderte Aktionen aus.
- Gib bei Dateipfaden immer den vollen, sauberen Pfad an."""
        
        conversation_cache.append({"role": "user", "content": new_message})
        
        # Veraltete Komprimierung als Fallback, wenn SessionManager nicht rotiert
        if len(conversation_cache) > MAX_CONVERSATION_LENGTH:
            print(f"🧠 Fallback-Kompaktierung: {len(conversation_cache)} Nachrichten")
            # Behalte System-Zusammenfassung (falls vorhanden) und die letzten Nachrichten
            summary_msg = [m for m in conversation_cache if m.get('type') == 'context_summary']
            recent_msgs = conversation_cache[-15:]
            conversation_cache[:] = summary_msg + recent_msgs

        context_parts = [system_prompt]
        for msg in conversation_cache:
            context_parts.append(f"{'Benutzer' if msg['role'] == 'user' else 'Atlas'}: {msg['content']}")
        
        return "\n\n".join(context_parts)

    def execute_code(self, code: str, language: str) -> Dict[str, Any]:
        """Führt Code sicher in einem Subprozess aus."""
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